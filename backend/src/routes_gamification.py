# backend/src/routes_gamification.py - CORREGIDO
from fastapi import APIRouter, Depends, HTTPException, Query
# ### CAMBIO: Mover 'case' a la importación correcta ###
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_, case
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from src.database import get_db
from src.auth import get_current_user, get_admin_user
from src.models.user import User
from src.models.gamification import (
    UserPoints, PointTransaction, Achievement, UserAchievement,
    Challenge, ChallengeParticipation, AchievementType, BadgeRarity
)
from src.gamification.points_engine import get_points_engine
from pydantic import BaseModel, Field

router = APIRouter(prefix="/gamification", tags=["Gamification"])
logger = logging.getLogger(__name__)

# === MODELOS PYDANTIC ===

class AwardPointsRequest(BaseModel):
    user_id: int = Field(..., description="ID del usuario a premiar")
    points: int = Field(..., description="Cantidad de puntos a otorgar (puede ser negativo)")
    reason: str = Field(..., min_length=3, max_length=200, description="Motivo de la premiación")

class UserStatsResponse(BaseModel):
    user_id: int
    username: str
    total_points: int
    weekly_points: int
    monthly_points: int
    level: int
    experience: int
    current_streak: int
    best_streak: int
    rank_position: Optional[int] = None
    
    class Config:
        orm_mode = True

class AchievementResponse(BaseModel):
    id: int
    name: str
    description: str
    type: str
    rarity: str
    icon: str
    points: int
    earned_at: Optional[datetime] = None
    progress: int = 0
    
    class Config:
        orm_mode = True

class LeaderboardEntry(BaseModel):
    position: int
    user_id: int
    username: str
    points: int
    level: int
    avatar: Optional[str] = None

class PointTransactionResponse(BaseModel):
    id: int
    points: int
    reason: str
    created_at: datetime
    multiplier: float
    
    class Config:
        orm_mode = True

# === ENDPOINTS PRINCIPALES (ACCESIBLES PARA TODOS) ===

@router.get("/profile", response_model=UserStatsResponse)
def get_user_profile(
    current_user: User = Depends(get_current_user),  # ← TODOS los usuarios pueden acceder
    db: Session = Depends(get_db)
):
    """Obtiene el perfil de gamificación del usuario actual - ACCESIBLE PARA TODOS"""
    user_points = db.query(UserPoints).filter(
        UserPoints.user_id == current_user.id
    ).first()
    
    if not user_points:
        # Crear perfil si no existe
        user_points = UserPoints(user_id=current_user.id)
        db.add(user_points)
        db.commit()
        db.refresh(user_points)
    
    # Calcular posición en el ranking
    rank_position = db.query(func.count(UserPoints.id)).filter(
        UserPoints.total_points > user_points.total_points
    ).scalar() + 1
    
    response = UserStatsResponse.from_orm(user_points)
    response.user_id = current_user.id
    response.username = current_user.username
    response.rank_position = rank_position
    return response

@router.get("/leaderboard")
def get_leaderboard(
    period: str = Query("all", description="all, weekly, monthly"),
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_user),  # ← TODOS los usuarios pueden acceder
    db: Session = Depends(get_db)
):
    """Obtiene el ranking de usuarios - ACCESIBLE PARA TODOS"""
    try:
        # Determinar campo de ordenamiento
        order_field = UserPoints.total_points
        if period == "weekly":
            order_field = UserPoints.weekly_points
        elif period == "monthly":
            order_field = UserPoints.monthly_points
        
        # Consulta base con información del usuario
        leaderboard_query = db.query(
            UserPoints,
            User.username
        ).join(
            User, UserPoints.user_id == User.id
        ).filter(
            User.active == True
        ).order_by(desc(order_field)).limit(limit)
        
        results = leaderboard_query.all()
        
        # Formatear respuesta
        leaderboard = []
        current_user_position = None
        
        for idx, (user_points, username) in enumerate(results, 1):
            points = getattr(user_points, order_field.name)
            
            entry = LeaderboardEntry(
                position=idx,
                user_id=user_points.user_id,
                username=username,
                points=points,
                level=user_points.level
            )
            leaderboard.append(entry)
            
            # Marcar posición del usuario actual
            if user_points.user_id == current_user.id:
                current_user_position = idx
        
        # Si el usuario actual no está en el top, obtener su posición
        if current_user_position is None:
            user_rank_query = db.query(getattr(UserPoints, order_field.name)).filter(UserPoints.user_id == current_user.id).scalar_subquery()
            current_user_position = db.query(func.count(UserPoints.id)).filter(getattr(UserPoints, order_field.name) > user_rank_query).scalar() + 1
        
        return {
            "leaderboard": leaderboard,
            "current_user_position": current_user_position,
            "period": period,
            "total_participants": db.query(UserPoints).count()
        }
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo ranking")

@router.get("/achievements", response_model=List[AchievementResponse])
def get_user_achievements(
    current_user: User = Depends(get_current_user),  # ← TODOS los usuarios pueden acceder
    db: Session = Depends(get_db)
):
    """Obtiene todos los logros del usuario (obtenidos y disponibles) - ACCESIBLE PARA TODOS"""
    try:
        # Obtener logros del usuario
        user_achievements = db.query(UserAchievement).options(
            joinedload(UserAchievement.achievement)
        ).filter(UserAchievement.user_id == current_user.id).all()
        
        # Obtener todos los logros disponibles
        all_achievements = db.query(Achievement).filter(
            Achievement.active == True
        ).all()
        
        result = []
        for achievement in all_achievements:
            user_ach = next((ua for ua in user_achievements 
                           if ua.achievement_id == achievement.id), None)
            
            result.append(AchievementResponse(
                id=achievement.id,
                name=achievement.name,
                description=achievement.description,
                type=achievement.type.value,
                rarity=achievement.rarity.value,
                icon=achievement.icon,
                points=achievement.points,
                earned_at=user_ach.earned_at if user_ach else None,
                progress=user_ach.progress if user_ach else 0
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting achievements: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo logros")

@router.get("/transactions", response_model=List[PointTransactionResponse])
def get_point_history(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),  # ← TODOS los usuarios pueden acceder
    db: Session = Depends(get_db)
):
    """Obtiene el historial de transacciones de puntos - ACCESIBLE PARA TODOS"""
    user_points = db.query(UserPoints).filter(
        UserPoints.user_id == current_user.id
    ).first()
    
    if not user_points:
        return []
    
    transactions = db.query(PointTransaction).filter(
        PointTransaction.user_points_id == user_points.id
    ).order_by(desc(PointTransaction.created_at)).offset(offset).limit(limit).all()
    
    return transactions

@router.get("/stats/dashboard")
def get_gamification_dashboard(
    current_user: User = Depends(get_current_user),  # ← TODOS los usuarios pueden acceder
    db: Session = Depends(get_db)
):
    """Dashboard completo de gamificación para el usuario - ACCESIBLE PARA TODOS"""
    try:
        # Obtener estadísticas del usuario
        user_points = db.query(UserPoints).filter(
            UserPoints.user_id == current_user.id
        ).first()
        
        if not user_points:
            user_points = UserPoints(user_id=current_user.id)
            db.add(user_points)
            db.commit()
        
        # Logros recientes (últimos 5)
        recent_achievements = db.query(UserAchievement).options(
            joinedload(UserAchievement.achievement)
        ).filter(
            UserAchievement.user_id == current_user.id
        ).order_by(desc(UserAchievement.earned_at)).limit(5).all()
        
        # Transacciones recientes
        recent_transactions = db.query(PointTransaction).filter(
            PointTransaction.user_points_id == user_points.id
        ).order_by(desc(PointTransaction.created_at)).limit(10).all()
        
        # Estadísticas de la semana
        week_start = datetime.utcnow() - timedelta(days=7)
        weekly_stats = db.query(
            func.sum(PointTransaction.points).label('points'),
            func.count(PointTransaction.id).label('transactions')
        ).filter(
            PointTransaction.user_points_id == user_points.id,
            PointTransaction.created_at >= week_start
        ).first()
        
        # Posición en ranking
        rank_position = db.query(func.count(UserPoints.id)).filter(
            UserPoints.total_points > user_points.total_points
        ).scalar() + 1
        
        # Próximo nivel
        next_level_xp = int(100 * ((user_points.level + 1) ** 1.5))
        xp_to_next_level = next_level_xp - user_points.experience
        
        return {
            "user_stats": {
                "total_points": user_points.total_points,
                "level": user_points.level,
                "experience": user_points.experience,
                "rank_position": rank_position,
                "current_streak": user_points.current_streak,
                "next_level_xp": next_level_xp,
                "xp_to_next_level": max(0, xp_to_next_level)
            },
            "weekly_stats": {
                "points_earned": weekly_stats.points or 0,
                "activities": weekly_stats.transactions or 0
            },
            "recent_achievements": [
                {
                    "name": ua.achievement.name,
                    "icon": ua.achievement.icon,
                    "points": ua.achievement.points,
                    "earned_at": ua.earned_at.isoformat(),
                    "rarity": ua.achievement.rarity.value
                }
                for ua in recent_achievements
            ],
            "recent_activities": [
                {
                    "points": tx.points,
                    "reason": tx.reason,
                    "created_at": tx.created_at.isoformat(),
                    "type": "gain" if tx.points > 0 else "loss"
                }
                for tx in recent_transactions
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo dashboard")

# === ENDPOINTS ADMINISTRATIVOS (SOLO PARA ADMINS) ===

@router.post("/admin/award-points")
def admin_award_points(
    award_data: AwardPointsRequest,  # <-- Usar el modelo para recibir un JSON
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Permite a administradores otorgar puntos manualmente - SOLO ADMINS"""
    try:
        if award_data.points == 0:
            raise HTTPException(status_code=400, detail="Los puntos no pueden ser cero.")

        points_engine = get_points_engine(db)
        user_points = points_engine.get_or_create_user_points(award_data.user_id)
        
        # Crear transacción
        transaction = PointTransaction(
            user_points_id=user_points.id,
            points=award_data.points,
            reason=f"[ADMIN] {award_data.reason}",
            entity_type="manual",
            entity_id=current_user.id
        )
        
        # Actualizar puntos
        user_points.total_points += award_data.points
        if award_data.points > 0:
            user_points.experience += award_data.points
        
        user_points.level = points_engine._calculate_level(user_points.experience)
        
        db.add(transaction)
        db.commit()
        
        return {
            "success": True,
            "message": f"Otorgados {award_data.points} puntos a usuario {award_data.user_id}",
            "new_total": user_points.total_points
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error awarding manual points: {e}")
        raise HTTPException(status_code=500, detail="Error otorgando puntos")


@router.get("/admin/stats")
def get_admin_gamification_stats(
    current_user: User = Depends(get_admin_user),  # ← SOLO ADMINS
    db: Session = Depends(get_db)
):
    """Estadísticas generales de gamificación para administradores - SOLO ADMINS"""
    try:
        # Estadísticas generales
        total_users = db.query(UserPoints).count()
        total_points_awarded = db.query(func.sum(UserPoints.total_points)).scalar() or 0
        total_achievements_earned = db.query(UserAchievement).count()
        
        # Top 10 usuarios más activos
        top_users = db.query(
            UserPoints.total_points,
            User.username
        ).join(User).order_by(desc(UserPoints.total_points)).limit(10).all()
        
        # Logros más populares
        popular_achievements = db.query(
            Achievement.name,
            func.count(UserAchievement.id).label('earned_count')
        ).join(UserAchievement).group_by(Achievement.id).order_by(
            desc('earned_count')
        ).limit(10).all()
        
        # Actividad por mes
        monthly_activity = db.query(
            func.date_trunc('month', PointTransaction.created_at).label('month'),
            func.sum(PointTransaction.points).label('points'),
            func.count(PointTransaction.id).label('transactions')
        ).group_by('month').order_by('month').limit(12).all()
        
        return {
            "overview": {
                "total_users": total_users,
                "total_points_awarded": total_points_awarded,
                "total_achievements_earned": total_achievements_earned
            },
            "top_users": [
                {"username": username, "points": points}
                for points, username in top_users
            ],
            "popular_achievements": [
                {"name": name, "earned_count": count}
                for name, count in popular_achievements
            ],
            "monthly_activity": [
                {
                    "month": activity.month.isoformat(),
                    "points": activity.points,
                    "transactions": activity.transactions
                }
                for activity in monthly_activity
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas")

@router.get("/admin/system-status")
def get_system_status(
    current_user: User = Depends(get_admin_user),  # ← SOLO ADMINS
    db: Session = Depends(get_db)
):
    """Obtiene el estado del sistema de gamificación - SOLO ADMINS"""
    try:
        # Verificar si hay logros en el sistema
        total_achievements = db.query(Achievement).count()
        
        # Verificar usuarios con perfil
        users_with_profile = db.query(UserPoints).count()
        total_users = db.query(User).filter(User.active == True).count()
        
        # Calcular puntos totales otorgados
        total_points_awarded = db.query(func.sum(UserPoints.total_points)).scalar() or 0
        
        # Sistema inicializado si hay logros y al menos un perfil de usuario
        initialized = total_achievements > 0 and users_with_profile > 0
        
        return {
            "initialized": initialized,
            "enabled": True,  # Por ahora siempre activo
            "total_users": total_users,
            "users_with_profile": users_with_profile,
            "total_achievements": total_achievements,
            "total_points_awarded": total_points_awarded
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "initialized": False,
            "enabled": False,
            "total_users": 0,
            "users_with_profile": 0,
            "total_achievements": 0,
            "total_points_awarded": 0
        }

@router.post("/admin/initialize-achievements")
def initialize_achievements(
    current_user: User = Depends(get_admin_user),  # ← SOLO ADMINS
    db: Session = Depends(get_db)
):
    """Inicializa los logros predeterminados - SOLO ADMINS"""
    try:
        from src.gamification.achievements_setup import setup_default_achievements
        setup_default_achievements(db)
        
        return {"success": True, "message": "Logros inicializados correctamente"}
    except Exception as e:
        logger.error(f"Error initializing achievements: {e}")
        raise HTTPException(status_code=500, detail="Error inicializando logros")

@router.post("/admin/initialize-user-profiles")
def initialize_user_profiles(
    current_user: User = Depends(get_admin_user),  # ← SOLO ADMINS
    db: Session = Depends(get_db)
):
    """Crea perfiles de gamificación para todos los usuarios - SOLO ADMINS"""
    try:
        users_created = 0
        
        # Obtener usuarios sin perfil de gamificación
        users_without_points = db.query(User).outerjoin(UserPoints).filter(
            UserPoints.id.is_(None),
            User.active == True
        ).all()
        
        for user in users_without_points:
            user_points = UserPoints(user_id=user.id)
            db.add(user_points)
            users_created += 1
        
        db.commit()
        
        return {
            "success": True, 
            "message": f"Perfiles creados para {users_created} usuarios"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing user profiles: {e}")
        raise HTTPException(status_code=500, detail="Error creando perfiles")

# === INTEGRACIÓN CON ÓRDENES DE TRABAJO ===

@router.post("/award-order-completion")
def award_points_for_order_completion(
    work_order_id: int,
    current_user: User = Depends(get_current_user),  # ← TODOS pueden usar esto
    db: Session = Depends(get_db)
):
    """Endpoint para otorgar puntos al completar una orden - TODOS PUEDEN USARLO"""
    try:
        from src.models.work_order import WorkOrder
        
        work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not work_order:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        
        if work_order.status != "Cerrada":
            raise HTTPException(status_code=400, detail="La orden no está cerrada")
        
        # Verificar que el usuario actual sea el asignado o admin
        if (work_order.assigned_to_id != current_user.id and 
            current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]):
            raise HTTPException(status_code=403, detail="Sin permisos")
        
        # Otorgar puntos
        points_engine = get_points_engine(db)
        result = points_engine.award_points_for_order(
            work_order, 
            work_order.assigned_to_id or current_user.id
        )
        
        return {
            "success": True,
            "points_awarded": result.get('points_awarded', 0),
            "bonuses": result.get('bonuses', {}),
            "new_achievements": result.get('new_achievements', []),
            "level_up": result.get('level_up', False)
        }
        
    except Exception as e:
        logger.error(f"Error awarding points for order {work_order_id}: {e}")
        raise HTTPException(status_code=500, detail="Error otorgando puntos")

# === NOTIFICACIONES ===

@router.get("/notifications")
def get_gamification_notifications(
    current_user: User = Depends(get_current_user),  # ← TODOS pueden acceder
    db: Session = Depends(get_db)
):
    """Obtiene notificaciones pendientes de gamificación - TODOS PUEDEN ACCEDER"""
    try:
        # Logros no notificados
        unnotified_achievements = db.query(UserAchievement).options(
            joinedload(UserAchievement.achievement)
        ).filter(
            UserAchievement.user_id == current_user.id,
            UserAchievement.notified == False
        ).all()
        
        # Marcar como notificados
        for ua in unnotified_achievements:
            ua.notified = True
        
        if unnotified_achievements:
            db.commit()
        
        return {
            "new_achievements": [
                {
                    "id": ua.achievement.id,
                    "name": ua.achievement.name,
                    "description": ua.achievement.description,
                    "icon": ua.achievement.icon,
                    "points": ua.achievement.points,
                    "rarity": ua.achievement.rarity.value
                }
                for ua in unnotified_achievements
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting gamification notifications: {e}")
        return {"new_achievements": []}
    
# backend/src/routes_gamification.py - NUEVOS ENDPOINTS AÑADIR

@router.get("/leaderboard/enhanced")
def get_enhanced_leaderboard(
    period: str = Query("all", description="all, weekly, monthly"),
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el ranking mejorado con logros visibles
    Incluye los logros más raros de cada usuario
    """
    try:
        # Determinar campo de ordenamiento
        order_field = UserPoints.total_points
        if period == "weekly":
            order_field = UserPoints.weekly_points
        elif period == "monthly":
            order_field = UserPoints.monthly_points
        
        # Consulta principal con joins optimizados
        leaderboard_query = db.query(
            UserPoints,
            User.username,
            User.id.label('user_id')
        ).join(
            User, UserPoints.user_id == User.id
        ).filter(
            User.active == True
        ).order_by(desc(order_field)).limit(limit)
        
        results = leaderboard_query.all()
        
        # Para cada usuario, obtener sus logros más raros
        leaderboard = []
        current_user_position = None
        
        for idx, (user_points, username, user_id) in enumerate(results, 1):
            # Obtener logros del usuario ordenados por rareza
            user_achievements = db.query(UserAchievement).options(
                joinedload(UserAchievement.achievement)
            ).join(Achievement).filter(
                UserAchievement.user_id == user_id
            ).order_by(
                # Ordenar por rareza: legendary > epic > rare > common
                case(
                    (Achievement.rarity == BadgeRarity.LEGENDARY, 4),
                    (Achievement.rarity == BadgeRarity.EPIC, 3),
                    (Achievement.rarity == BadgeRarity.RARE, 2),
                    (Achievement.rarity == BadgeRarity.COMMON, 1),
                    else_=0
                ).desc(),
                Achievement.points.desc()
            ).limit(5).all()
            
            # Contar total de logros
            total_achievements = db.query(UserAchievement).filter(
                UserAchievement.user_id == user_id
            ).count()
            
            # Calcular racha actual
            current_streak = user_points.current_streak or 0
            
            # Formatear logros para respuesta
            achievements_data = []
            for ua in user_achievements:
                achievements_data.append({
                    'id': ua.achievement.id,
                    'name': ua.achievement.name,
                    'icon': ua.achievement.icon,
                    'rarity': ua.achievement.rarity.value,
                    'points': ua.achievement.points,
                    'description': ua.achievement.description,
                    'earned_at': ua.earned_at.isoformat() if ua.earned_at else None
                })
            
            points = getattr(user_points, order_field.name)
            
            entry = {
                'position': idx,
                'user_id': user_id,
                'username': username,
                'points': points,
                'level': user_points.level,
                'achievements': achievements_data,
                'total_achievements': total_achievements,
                'current_streak': current_streak,
                'best_streak': user_points.best_streak or 0,
                'weekly_points': user_points.weekly_points,
                'monthly_points': user_points.monthly_points
            }
            
            leaderboard.append(entry)
            
            # Marcar posición del usuario actual
            if user_id == current_user.id:
                current_user_position = idx
        
        # Si el usuario actual no está en el top, obtener su posición
        if current_user_position is None:
            user_rank_query = db.query(getattr(UserPoints, order_field.name)).filter(UserPoints.user_id == current_user.id).scalar_subquery()
            current_user_position = db.query(func.count(UserPoints.id)).filter(getattr(UserPoints, order_field.name) > user_rank_query).scalar() + 1
        
        total_available = db.query(Achievement).filter(Achievement.active == True).count()
        return {
            "leaderboard": leaderboard,
            "current_user_position": current_user_position,
            "period": period,
            "total_participants": db.query(UserPoints).count(),
            "achievement_stats": {
                "total_achievements_available": total_available,
                "rarity_distribution": {
                    "legendary": db.query(Achievement).filter(Achievement.rarity == BadgeRarity.LEGENDARY).count(),
                    "epic": db.query(Achievement).filter(Achievement.rarity == BadgeRarity.EPIC).count(),
                    "rare": db.query(Achievement).filter(Achievement.rarity == BadgeRarity.RARE).count(),
                    "common": db.query(Achievement).filter(Achievement.rarity == BadgeRarity.COMMON).count()
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting enhanced leaderboard: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo ranking mejorado")

@router.get("/achievements/showcase/{user_id}")
def get_user_achievement_showcase(
    user_id: int,
    limit: int = Query(10, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene los logros más destacados de un usuario específico
    Útil para mostrar en perfiles o modales
    """
    try:
        # Verificar que el usuario existe
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Obtener logros del usuario ordenados por rareza y puntos
        user_achievements = db.query(UserAchievement).options(
            joinedload(UserAchievement.achievement)
        ).join(Achievement).filter(
            UserAchievement.user_id == user_id
        ).order_by(
            case(
                (Achievement.rarity == BadgeRarity.LEGENDARY, 4),
                (Achievement.rarity == BadgeRarity.EPIC, 3),
                (Achievement.rarity == BadgeRarity.RARE, 2),
                (Achievement.rarity == BadgeRarity.COMMON, 1),
                else_=0
            ).desc(),
            Achievement.points.desc(),
            UserAchievement.earned_at.desc()
        ).limit(limit).all()
        
        # Estadísticas del usuario
        user_stats = db.query(UserPoints).filter(UserPoints.user_id == user_id).first()
        total_achievements = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id
        ).count()
        
        # Contar por rareza
        rarity_counts = {}
        for rarity in BadgeRarity:
            count = db.query(UserAchievement).join(Achievement).filter(
                UserAchievement.user_id == user_id,
                Achievement.rarity == rarity
            ).count()
            rarity_counts[rarity.value] = count
        
        # Formatear logros
        achievements_data = []
        for ua in user_achievements:
            achievements_data.append({
                'id': ua.achievement.id,
                'name': ua.achievement.name,
                'description': ua.achievement.description,
                'icon': ua.achievement.icon,
                'rarity': ua.achievement.rarity.value,
                'points': ua.achievement.points,
                'type': ua.achievement.type.value,
                'earned_at': ua.earned_at.isoformat() if ua.earned_at else None,
                'progress': ua.progress
            })
        
        total_available = db.query(Achievement).filter(Achievement.active == True).count()
        return {
            "user": {
                "id": target_user.id,
                "username": target_user.username,
                "level": user_stats.level if user_stats else 1,
                "total_points": user_stats.total_points if user_stats else 0
            },
            "achievements": achievements_data,
            "stats": {
                "total_achievements": total_achievements,
                "rarity_breakdown": rarity_counts,
                "completion_rate": round(
                    (total_achievements / total_available) * 100, 1
                ) if total_available > 0 else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user achievement showcase: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo logros del usuario")

@router.get("/achievements/categories")
def get_achievement_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los logros organizados por categorías
    """
    try:
        from src.gamification.expanded_achievements import get_achievements_by_category
        
        # Obtener todos los logros activos
        all_achievements = db.query(Achievement).filter(Achievement.active == True).all()
        
        # Organizar por tipo
        categories = {}
        for achievement in all_achievements:
            category = achievement.type.value
            if category not in categories:
                categories[category] = []
            
            categories[category].append({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'rarity': achievement.rarity.value,
                'points': achievement.points
            })
        
        # Estadísticas por categoría
        category_stats = {}
        for category, achievements in categories.items():
            category_stats[category] = {
                'total': len(achievements),
                'by_rarity': {
                    'legendary': len([a for a in achievements if a['rarity'] == 'legendary']),
                    'epic': len([a for a in achievements if a['rarity'] == 'epic']),
                    'rare': len([a for a in achievements if a['rarity'] == 'rare']),
                    'common': len([a for a in achievements if a['rarity'] == 'common'])
                }
            }
        
        return {
            "categories": categories,
            "stats": category_stats,
            "total_achievements": len(all_achievements)
        }
        
    except Exception as e:
        logger.error(f"Error getting achievement categories: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo categorías de logros")

@router.post("/admin/bulk-create-achievements")
def bulk_create_achievements(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Crea masivamente los logros expandidos - SOLO ADMINS
    """
    try:
        from src.gamification.expanded_achievements import setup_expanded_achievements
        
        # Ejecutar setup de logros expandidos
        created_count = setup_expanded_achievements(db)
        
        return {
            "success": True,
            "message": f"Se crearon {created_count} nuevos logros",
            "total_achievements": db.query(Achievement).filter(Achievement.active == True).count()
        }
        
    except Exception as e:
        logger.error(f"Error creating bulk achievements: {e}")
        raise HTTPException(status_code=500, detail="Error creando logros masivamente")