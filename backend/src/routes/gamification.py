# backend/src/routes/gamification.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from src.dependencies import get_db, get_current_user
from src.models.user import User
from src.models.gamification import (
    UserPoints, PointTransaction, Achievement, UserAchievement,
    Challenge, ChallengeParticipation, AchievementType, BadgeRarity
)
from src.gamification.points_engine import get_points_engine
from src.schemas.gamification import (
    UserStatsResponse, LeaderboardResponse, LeaderboardEntry,
    AchievementResponse, PointTransactionResponse, GamificationDashboardResponse,
    AdminAwardPointsRequest, AdminAwardPointsResponse, AdminGamificationStatsResponse,
    OrderCompletionResponse, SystemStatusResponse, SystemActionResponse,
    InitializeProfilesResponse, ToggleSystemRequest, ResetUserPointsRequest,
    LeaderboardFilters, TransactionHistoryFilters, LeaderboardPeriodEnum
)

router = APIRouter(prefix="/gamification", tags=["Gamification"])
logger = logging.getLogger(__name__)

# === ENDPOINTS PRINCIPALES ===

@router.get("/profile", response_model=UserStatsResponse)
def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene el perfil de gamificación del usuario actual"""
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
    
    return UserStatsResponse(
        user_id=current_user.id,
        username=current_user.username,
        total_points=user_points.total_points,
        weekly_points=user_points.weekly_points,
        monthly_points=user_points.monthly_points,
        level=user_points.level,
        experience=user_points.experience,
        current_streak=user_points.current_streak,
        best_streak=user_points.best_streak,
        rank_position=rank_position
    )

@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    period: LeaderboardPeriodEnum = Query(LeaderboardPeriodEnum.ALL, description="all, weekly, monthly"),
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene el ranking de usuarios"""
    try:
        # Determinar campo de ordenamiento
        order_field = UserPoints.total_points
        if period == LeaderboardPeriodEnum.WEEKLY:
            order_field = UserPoints.weekly_points
        elif period == LeaderboardPeriodEnum.MONTHLY:
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
            user_rank = db.query(func.count(UserPoints.id)).filter(
                getattr(UserPoints, order_field.name) > 
                db.query(getattr(UserPoints, order_field.name)).filter(
                    UserPoints.user_id == current_user.id
                ).scalar_subquery()
            ).scalar() + 1
            current_user_position = user_rank
        
        return LeaderboardResponse(
            leaderboard=leaderboard,
            current_user_position=current_user_position,
            period=period.value,
            total_participants=db.query(UserPoints).count()
        )
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo ranking")

@router.get("/achievements", response_model=List[AchievementResponse])
def get_user_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene todos los logros del usuario (obtenidos y disponibles)"""
    try:
        # Obtener logros del usuario
        user_achievements = db.query(UserAchievement).options(
            joinedload(UserAchievement.achievement)
        ).filter(UserAchievement.user_id == current_user.id).all()
        
        user_achievement_ids = [ua.achievement_id for ua in user_achievements]
        
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene el historial de transacciones de puntos"""
    user_points = db.query(UserPoints).filter(
        UserPoints.user_id == current_user.id
    ).first()
    
    if not user_points:
        return []
    
    transactions = db.query(PointTransaction).filter(
        PointTransaction.user_points_id == user_points.id
    ).order_by(desc(PointTransaction.created_at)).offset(offset).limit(limit).all()
    
    return transactions

@router.get("/stats/dashboard", response_model=GamificationDashboardResponse)
def get_gamification_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dashboard completo de gamificación para el usuario"""
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
        
        return GamificationDashboardResponse(
            user_stats={
                "total_points": user_points.total_points,
                "level": user_points.level,
                "experience": user_points.experience,
                "rank_position": rank_position,
                "current_streak": user_points.current_streak,
                "next_level_xp": next_level_xp,
                "xp_to_next_level": max(0, xp_to_next_level)
            },
            weekly_stats={
                "points_earned": weekly_stats.points or 0,
                "activities": weekly_stats.transactions or 0
            },
            recent_achievements=[
                {
                    "name": ua.achievement.name,
                    "icon": ua.achievement.icon,
                    "points": ua.achievement.points,
                    "earned_at": ua.earned_at.isoformat(),
                    "rarity": ua.achievement.rarity.value
                }
                for ua in recent_achievements
            ],
            recent_activities=[
                {
                    "points": tx.points,
                    "reason": tx.reason,
                    "created_at": tx.created_at.isoformat(),
                    "type": "gain" if tx.points > 0 else "loss"
                }
                for tx in recent_transactions
            ]
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo dashboard")

# === ENDPOINTS ADMINISTRATIVOS ===

@router.post("/admin/award-points", response_model=AdminAwardPointsResponse)
def admin_award_points(
    request: AdminAwardPointsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Permite a administradores otorgar puntos manualmente"""
    # Verificar permisos de administrador
    if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
        raise HTTPException(status_code=403, detail="Sin permisos de administrador")
    
    try:
        points_engine = get_points_engine(db)
        user_points = points_engine.get_or_create_user_points(request.user_id)
        
        # Crear transacción
        transaction = PointTransaction(
            user_points_id=user_points.id,
            points=request.points,
            reason=f"[ADMIN] {request.reason}",
            entity_type="manual",
            entity_id=current_user.id
        )
        
        # Actualizar puntos
        user_points.total_points += request.points
        user_points.experience += request.points if request.points > 0 else 0
        user_points.level = points_engine._calculate_level(user_points.experience)
        
        db.add(transaction)
        db.commit()
        
        return AdminAwardPointsResponse(
            success=True,
            message=f"Otorgados {request.points} puntos a usuario {request.user_id}",
            new_total=user_points.total_points
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error awarding manual points: {e}")
        raise HTTPException(status_code=500, detail="Error otorgando puntos")

@router.get("/admin/stats", response_model=AdminGamificationStatsResponse)
def get_admin_gamification_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Estadísticas generales de gamificación para administradores"""
    if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
        raise HTTPException(status_code=403, detail="Sin permisos")
    
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
        
        return AdminGamificationStatsResponse(
            overview={
                "total_users": total_users,
                "total_points_awarded": total_points_awarded,
                "total_achievements_earned": total_achievements_earned
            },
            top_users=[
                {"username": username, "points": points}
                for points, username in top_users
            ],
            popular_achievements=[
                {"name": name, "earned_count": count}
                for name, count in popular_achievements
            ],
            monthly_activity=[
                {
                    "month": activity.month.isoformat(),
                    "points": activity.points,
                    "transactions": activity.transactions
                }
                for activity in monthly_activity
            ]
        )
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas")

# === INTEGRACIÓN CON ÓRDENES DE TRABAJO ===

@router.post("/award-order-completion", response_model=OrderCompletionResponse)
def award_points_for_order_completion(
    work_order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Endpoint para otorgar puntos al completar una orden (llamado automáticamente)"""
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
        
        return OrderCompletionResponse(
            success=True,
            points_awarded=result.get('points_awarded', 0),
            bonuses=result.get('bonuses', {}),
            new_achievements=result.get('new_achievements', []),
            level_up=result.get('level_up', False)
        )
        
    except Exception as e:
        logger.error(f"Error awarding points for order {work_order_id}: {e}")
        raise HTTPException(status_code=500, detail="Error otorgando puntos")

# === ENDPOINTS DE SISTEMA ===

@router.get("/admin/system-status", response_model=SystemStatusResponse)
def get_system_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene el estado del sistema de gamificación"""
    if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
        raise HTTPException(status_code=403, detail="Sin permisos")
    
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
        
        return SystemStatusResponse(
            initialized=initialized,
            enabled=True,  # Por ahora siempre activo, puedes implementar un switch
            total_users=total_users,
            users_with_profile=users_with_profile,
            total_achievements=total_achievements,
            total_points_awarded=total_points_awarded
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return SystemStatusResponse(
            initialized=False,
            enabled=False,
            total_users=0,
            users_with_profile=0,
            total_achievements=0,
            total_points_awarded=0
        )

@router.post("/admin/initialize-achievements", response_model=SystemActionResponse)
def initialize_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Inicializa los logros predeterminados"""
    if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
        raise HTTPException(status_code=403, detail="Sin permisos")
    
    try:
        from src.gamification.achievements_setup import setup_default_achievements
        setup_default_achievements(db)
        
        return SystemActionResponse(
            success=True, 
            message="Logros inicializados correctamente"
        )
    except Exception as e:
        logger.error(f"Error initializing achievements: {e}")
        raise HTTPException(status_code=500, detail="Error inicializando logros")

@router.post("/admin/initialize-user-profiles", response_model=InitializeProfilesResponse)
def initialize_user_profiles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea perfiles de gamificación para todos los usuarios"""
    if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
        raise HTTPException(status_code=403, detail="Sin permisos")
    
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
        
        return InitializeProfilesResponse(
            success=True, 
            message=f"Perfiles creados para {users_created} usuarios"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing user profiles: {e}")
        raise HTTPException(status_code=500, detail="Error creando perfiles")

@router.post("/admin/enable-system", response_model=SystemActionResponse)
def enable_system(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activa el sistema de gamificación"""
    if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
        raise HTTPException(status_code=403, detail="Sin permisos")
    
    # Aquí puedes implementar lógica para activar/desactivar
    # Por ejemplo, guardar en una tabla de configuración
    
    return SystemActionResponse(
        success=True, 
        message="Sistema activado correctamente"
    )

@router.post("/admin/toggle-system", response_model=SystemActionResponse)
def toggle_system(
    request: ToggleSystemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activa o desactiva el sistema de gamificación"""
    if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
        raise HTTPException(status_code=403, detail="Sin permisos")
    
    # Implementar lógica para guardar estado en BD
    return SystemActionResponse(
        success=True, 
        message=f"Sistema {'activado' if request.enabled else 'desactivado'} correctamente"
    )

@router.post("/admin/reset-user-points", response_model=SystemActionResponse)
def reset_user_points(
    request: ResetUserPointsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reinicia los puntos de un usuario"""
    if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
        raise HTTPException(status_code=403, detail="Sin permisos")
    
    try:
        user_points = db.query(UserPoints).filter(UserPoints.user_id == request.user_id).first()
        if user_points:
            user_points.total_points = 0
            user_points.weekly_points = 0
            user_points.monthly_points = 0
            user_points.experience = 0
            user_points.level = 1
            user_points.current_streak = 0
            db.commit()
            
        return SystemActionResponse(
            success=True, 
            message="Puntos reiniciados correctamente"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error resetting user points: {e}")
        raise HTTPException(status_code=500, detail="Error reiniciando puntos")
