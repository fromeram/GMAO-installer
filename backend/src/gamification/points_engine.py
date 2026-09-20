# backend/src/gamification/points_engine.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, List, Optional
import json
import logging

from ..models.gamification import (
    UserPoints, PointTransaction, Achievement, UserAchievement, 
    AchievementType, BadgeRarity
)
from ..models.work_order import WorkOrder
from ..models.user import User

logger = logging.getLogger(__name__)

class PointsEngine:
    """Motor de puntos que calcula recompensas basadas en rendimiento"""
    
    # Configuración base de puntos
    BASE_POINTS = {
        'complete_order': 50,
        'preventive_order': 75,
        'corrective_order': 60,
        'inspection_order': 40,
        'emergency_order': 100,
        'first_time_fix': 25,  # Bonus por arreglar sin retrabajo
        'speed_bonus': 30,     # Completar antes de tiempo
        'quality_bonus': 40,   # Sin defectos reportados
        'daily_streak': 10,    # Por cada día consecutivo
        'weekly_streak': 50,   # Semana completa trabajando
    }
    
    # Multiplicadores por rendimiento
    MULTIPLIERS = {
        'excellent': 1.5,    # >95% eficiencia
        'good': 1.2,         # 85-95% eficiencia
        'average': 1.0,      # 70-85% eficiencia
        'below_average': 0.8, # <70% eficiencia
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_user_points(self, user_id: int) -> UserPoints:
        """Obtiene o crea el registro de puntos del usuario"""
        user_points = self.db.query(UserPoints).filter(
            UserPoints.user_id == user_id
        ).first()
        
        if not user_points:
            user_points = UserPoints(user_id=user_id)
            self.db.add(user_points)
            self.db.flush()
        
        return user_points
    
    def award_points_for_order(self, work_order: WorkOrder, user_id: int) -> Dict:
        """Otorga puntos por completar una orden de trabajo"""
        try:
            user_points = self.get_or_create_user_points(user_id)
            
            # Calcular puntos base según tipo de orden
            work_type_key = f"{work_order.work_type.lower()}_order"
            base_points = self.BASE_POINTS.get(work_type_key, self.BASE_POINTS['complete_order'])
            
            # Calcular bonificaciones
            bonuses = self._calculate_bonuses(work_order, user_id)
            
            # Calcular multiplicador por rendimiento del técnico
            multiplier = self._get_performance_multiplier(user_id)
            
            # Total de puntos
            total_points = int((base_points + sum(bonuses.values())) * multiplier)
            
            # Registrar transacción
            transaction = PointTransaction(
                user_points_id=user_points.id,
                points=total_points,
                reason=f"Completar OT #{work_order.order_number}: {work_order.title}",
                entity_type="work_order",
                entity_id=work_order.id,
                multiplier=multiplier
            )
            
            # Actualizar puntos del usuario
            user_points.total_points += total_points
            user_points.weekly_points += total_points
            user_points.monthly_points += total_points
            user_points.last_activity = datetime.utcnow()
            
            # Actualizar experiencia y nivel
            user_points.experience += total_points
            new_level = self._calculate_level(user_points.experience)
            level_up = new_level > user_points.level
            user_points.level = new_level
            
            self.db.add(transaction)
            self.db.commit()
            
            # Verificar logros después de otorgar puntos
            new_achievements = self._check_achievements(user_id, work_order)
            
            return {
                'points_awarded': total_points,
                'base_points': base_points,
                'bonuses': bonuses,
                'multiplier': multiplier,
                'new_total': user_points.total_points,
                'level_up': level_up,
                'new_level': user_points.level if level_up else None,
                'new_achievements': new_achievements
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error awarding points for order {work_order.id}: {e}")
            return {'error': str(e)}
    
    def _calculate_bonuses(self, work_order: WorkOrder, user_id: int) -> Dict[str, int]:
        """Calcula bonificaciones específicas para una orden"""
        bonuses = {}
        
        # Bonus por velocidad (completar antes del tiempo estimado)
        if work_order.actual_start_time and work_order.actual_end_time:
            actual_duration = (work_order.actual_end_time - work_order.actual_start_time).total_seconds() / 3600
            if hasattr(work_order, 'estimated_hours') and work_order.estimated_hours:
                if actual_duration < work_order.estimated_hours * 0.8:  # 20% más rápido
                    bonuses['speed_bonus'] = self.BASE_POINTS['speed_bonus']
        
        # Bonus por calidad (sin órdenes relacionadas posteriores)
        days_since = (datetime.utcnow() - work_order.finished_at).days if work_order.finished_at else 0
        if days_since >= 7:  # Una semana sin retrabajos
            related_orders = self.db.query(WorkOrder).filter(
                WorkOrder.machine_id == work_order.machine_id,
                WorkOrder.work_type == "Correctivo",
                WorkOrder.created_at > work_order.finished_at,
                WorkOrder.created_at < work_order.finished_at + timedelta(days=7)
            ).count()
            
            if related_orders == 0:
                bonuses['quality_bonus'] = self.BASE_POINTS['quality_bonus']
        
        # Bonus por racha diaria
        streak = self._calculate_daily_streak(user_id)
        if streak > 0:
            bonuses['streak_bonus'] = min(streak * self.BASE_POINTS['daily_streak'], 100)
        
        return bonuses
    
    def _get_performance_multiplier(self, user_id: int) -> float:
        """Calcula multiplicador basado en rendimiento histórico del técnico"""
        # Obtener órdenes completadas en los últimos 30 días
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        orders = self.db.query(WorkOrder).filter(
            WorkOrder.assigned_to_id == user_id,
            WorkOrder.status == "Cerrada",
            WorkOrder.finished_at >= thirty_days_ago
        ).all()
        
        if len(orders) < 5:  # Mínimo 5 órdenes para evaluar
            return 1.0
        
        # Calcular métricas de eficiencia
        on_time_count = 0
        quality_count = 0
        
        for order in orders:
            # Verificar si se completó a tiempo (simplificado)
            if order.actual_end_time and order.actual_start_time:
                # Aquí puedes implementar lógica más sofisticada
                on_time_count += 1
            
            # Verificar calidad (sin retrabajos)
            # Implementar lógica según tus criterios
            quality_count += 1
        
        efficiency = (on_time_count / len(orders)) * 100
        
        # Devolver multiplicador según eficiencia
        if efficiency >= 95:
            return self.MULTIPLIERS['excellent']
        elif efficiency >= 85:
            return self.MULTIPLIERS['good']
        elif efficiency >= 70:
            return self.MULTIPLIERS['average']
        else:
            return self.MULTIPLIERS['below_average']
    
    def _calculate_level(self, experience: int) -> int:
        """Calcula el nivel basado en experiencia total"""
        # Fórmula progresiva: cada nivel requiere más XP
        # Nivel 1: 0-100 XP, Nivel 2: 100-250 XP, etc.
        if experience < 100:
            return 1
        
        # Fórmula: XP requerida = 100 * level^1.5
        level = 1
        xp_required = 0
        
        while xp_required < experience:
            level += 1
            xp_required += int(100 * (level ** 1.5))
        
        return max(1, level - 1)
    
    def _calculate_daily_streak(self, user_id: int) -> int:
        """Calcula la racha de días consecutivos trabajando"""
        today = datetime.utcnow().date()
        streak = 0
        current_date = today
        
        # Verificar hacia atrás día por día
        for i in range(30):  # Máximo 30 días
            orders_on_date = self.db.query(WorkOrder).filter(
                WorkOrder.assigned_to_id == user_id,
                WorkOrder.status == "Cerrada",
                func.date(WorkOrder.finished_at) == current_date
            ).count()
            
            if orders_on_date > 0:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def _check_achievements(self, user_id: int, work_order: WorkOrder) -> List[Dict]:
        """Verifica si el usuario ha desbloqueado nuevos logros"""
        new_achievements = []
        
        try:
            # Obtener logros que el usuario aún no tiene
            user_achievement_ids = self.db.query(UserAchievement.achievement_id).filter(
                UserAchievement.user_id == user_id
            ).subquery()
            
            available_achievements = self.db.query(Achievement).filter(
                ~Achievement.id.in_(user_achievement_ids),
                Achievement.active == True
            ).all()
            
            logger.info(f"Checking {len(available_achievements)} achievements for user {user_id}")
            
            for achievement in available_achievements:
                if self._check_achievement_condition(user_id, achievement, work_order):
                    logger.info(f"Achievement unlocked: {achievement.name} for user {user_id}")
                    
                    # Otorgar logro
                    user_achievement = UserAchievement(
                        user_id=user_id,
                        achievement_id=achievement.id
                    )
                    self.db.add(user_achievement)
                    
                    # Otorgar puntos del logro
                    if achievement.points > 0:
                        user_points = self.get_or_create_user_points(user_id)
                        user_points.total_points += achievement.points
                        
                        transaction = PointTransaction(
                            user_points_id=user_points.id,
                            points=achievement.points,
                            reason=f"Logro desbloqueado: {achievement.name}",
                            entity_type="achievement",
                            entity_id=achievement.id
                        )
                        self.db.add(transaction)
                    
                    new_achievements.append({
                        'id': achievement.id,
                        'name': achievement.name,
                        'description': achievement.description,
                        'points': achievement.points,
                        'rarity': achievement.rarity.value,
                        'icon': achievement.icon
                    })
            
            if new_achievements:
                self.db.commit()
                logger.info(f"Awarded {len(new_achievements)} new achievements to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error checking achievements for user {user_id}: {e}")
            self.db.rollback()
        
        return new_achievements
    
    def _check_achievement_condition(self, user_id: int, achievement: Achievement, 
                                   work_order: WorkOrder = None) -> bool:
        """Verifica si se cumple la condición para un logro específico"""
        try:
            # Parsear condiciones JSON
            conditions = json.loads(achievement.condition_json) if achievement.condition_json else {}
            
            # Implementar verificaciones según tipo de logro
            if achievement.type == AchievementType.SPEED:
                return self._check_speed_achievement(user_id, conditions, work_order)
            elif achievement.type == AchievementType.QUALITY:
                return self._check_quality_achievement(user_id, conditions, work_order)
            elif achievement.type == AchievementType.CONSISTENCY:
                return self._check_consistency_achievement(user_id, conditions)
            elif achievement.type == AchievementType.LEARNING:
                return self._check_learning_achievement(user_id, conditions)
            elif achievement.type == AchievementType.TEAMWORK:
                return self._check_teamwork_achievement(user_id, conditions, work_order)
            elif achievement.type == AchievementType.INNOVATION:
                return self._check_innovation_achievement(user_id, conditions)
            
            return False
        except Exception as e:
            logger.error(f"Error checking achievement {achievement.id}: {e}")
            return False
    
    def _check_speed_achievement(self, user_id: int, conditions: Dict, 
                               work_order: WorkOrder = None) -> bool:
        """Verifica logros relacionados con velocidad"""
        # Ejemplo: "Completar 10 órdenes en un día"
        if conditions.get('type') == 'orders_per_day':
            today = datetime.utcnow().date()
            orders_today = self.db.query(WorkOrder).filter(
                WorkOrder.assigned_to_id == user_id,
                WorkOrder.status == "Cerrada",
                func.date(WorkOrder.finished_at) == today
            ).count()
            
            return orders_today >= conditions.get('target', 10)
        
        # Ejemplo: "Completar orden en menos de 2 horas"
        if conditions.get('type') == 'fast_completion' and work_order:
            if work_order.actual_start_time and work_order.actual_end_time:
                duration = (work_order.actual_end_time - work_order.actual_start_time).total_seconds() / 3600
                return duration <= conditions.get('max_hours', 2)
        
        return False
    
    def _check_quality_achievement(self, user_id: int, conditions: Dict, 
                                 work_order: WorkOrder = None) -> bool:
        """Verifica logros relacionados con calidad"""
        # Ejemplo: "50 órdenes sin retrabajo"
        if conditions.get('type') == 'no_rework_streak':
            # Implementar lógica específica para tu sistema
            pass
        
        return False
    
    def _check_consistency_achievement(self, user_id: int, conditions: Dict) -> bool:
        """Verifica logros relacionados con consistencia"""
        # Ejemplo: "30 días consecutivos trabajando"
        if conditions.get('type') == 'daily_streak':
            streak = self._calculate_daily_streak(user_id)
            return streak >= conditions.get('target_days', 30)
        
        return False
    
    def _check_learning_achievement(self, user_id: int, conditions: Dict) -> bool:
        """Verifica logros relacionados con aprendizaje"""
        if conditions.get('type') == 'order_count':
            # Contar órdenes completadas por el usuario
            order_count = self.db.query(WorkOrder).filter(
                WorkOrder.assigned_to_id == user_id,
                WorkOrder.status == "Cerrada"
            ).count()
            
            logger.info(f"User {user_id} has completed {order_count} orders, target: {conditions.get('target', 1)}")
            return order_count >= conditions.get('target', 1)
        
        return False
    
    def _check_teamwork_achievement(self, user_id: int, conditions: Dict, 
                                  work_order: WorkOrder = None) -> bool:
        """Verifica logros relacionados con trabajo en equipo"""
        if conditions.get('type') == 'night_shift_orders':
            # Contar órdenes completadas después de cierta hora
            after_hour = conditions.get('after_hour', 20)
            target = conditions.get('target', 5)
            
            night_orders = self.db.query(WorkOrder).filter(
                WorkOrder.assigned_to_id == user_id,
                WorkOrder.status == "Cerrada",
                func.extract('hour', WorkOrder.finished_at) >= after_hour
            ).count()
            
            return night_orders >= target
        
        if conditions.get('type') == 'emergency_orders':
            # Contar órdenes de emergencia en un periodo
            timeframe_days = conditions.get('timeframe_days', 7)
            target = conditions.get('target', 3)
            since_date = datetime.utcnow() - timedelta(days=timeframe_days)
            
            emergency_orders = self.db.query(WorkOrder).filter(
                WorkOrder.assigned_to_id == user_id,
                WorkOrder.status == "Cerrada",
                WorkOrder.work_type == "Correctivo",  # Asumiendo que correctivo = emergencia
                WorkOrder.finished_at >= since_date
            ).count()
            
            return emergency_orders >= target
        
        return False
    
    def _check_innovation_achievement(self, user_id: int, conditions: Dict) -> bool:
        """Verifica logros relacionados con innovación"""
        # Implementar cuando tengas sistema de sugerencias/mejoras
        return False

# Instancia global
def get_points_engine(db: Session) -> PointsEngine:
    return PointsEngine(db)