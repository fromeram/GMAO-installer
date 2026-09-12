# backend/src/schemas/gamification.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# === ENUMERACIONES ===
class AchievementTypeEnum(str, Enum):
    SPEED = "speed"
    QUALITY = "quality"
    CONSISTENCY = "consistency"
    LEARNING = "learning"
    TEAMWORK = "teamwork"
    INNOVATION = "innovation"
    # Valores adicionales para compatibilidad
    WORK_ORDER = "work_order"
    MAINTENANCE = "maintenance"
    SAFETY = "safety"
    EFFICIENCY = "efficiency"
    TRAINING = "training"
    MILESTONE = "milestone"

class BadgeRarityEnum(str, Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    # Valor adicional para compatibilidad
    UNCOMMON = "uncommon"

class LeaderboardPeriodEnum(str, Enum):
    ALL = "all"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

# === ESQUEMAS BASE ===
class UserStatsBase(BaseModel):
    user_id: int
    username: str
    total_points: int
    weekly_points: int
    monthly_points: int
    level: int
    experience: int
    current_streak: int
    best_streak: int

class UserStatsResponse(UserStatsBase):
    rank_position: Optional[int] = None
    
    class Config:
        orm_mode = True

class LeaderboardEntry(BaseModel):
    position: int
    user_id: int
    username: str
    points: int
    level: int
    avatar: Optional[str] = None

class LeaderboardResponse(BaseModel):
    leaderboard: List[LeaderboardEntry]
    current_user_position: int
    period: str
    total_participants: int

# === ESQUEMAS DE LOGROS ===
class AchievementBase(BaseModel):
    name: str
    description: str
    type: AchievementTypeEnum
    rarity: BadgeRarityEnum
    icon: str
    points: int

class AchievementResponse(AchievementBase):
    id: int
    earned_at: Optional[datetime] = None
    progress: int = 0
    
    class Config:
        orm_mode = True

class UserAchievementResponse(BaseModel):
    id: int
    achievement_id: int
    user_id: int
    earned_at: datetime
    progress: int
    achievement: AchievementResponse
    
    class Config:
        orm_mode = True

# === ESQUEMAS DE TRANSACCIONES ===
class PointTransactionBase(BaseModel):
    points: int
    reason: str
    multiplier: float = 1.0

class PointTransactionResponse(PointTransactionBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class PointTransactionCreate(PointTransactionBase):
    user_id: int
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None

# === ESQUEMAS DE DASHBOARD ===
class WeeklyStatsResponse(BaseModel):
    points_earned: int
    activities: int

class RecentAchievementResponse(BaseModel):
    name: str
    icon: str
    points: int
    earned_at: str
    rarity: str

class RecentActivityResponse(BaseModel):
    points: int
    reason: str
    created_at: str
    type: str  # "gain" or "loss"

class UserDashboardStats(BaseModel):
    total_points: int
    level: int
    experience: int
    rank_position: int
    current_streak: int
    next_level_xp: int
    xp_to_next_level: int

class GamificationDashboardResponse(BaseModel):
    user_stats: UserDashboardStats
    weekly_stats: WeeklyStatsResponse
    recent_achievements: List[RecentAchievementResponse]
    recent_activities: List[RecentActivityResponse]

# === ESQUEMAS ADMINISTRATIVOS ===
class AdminAwardPointsRequest(BaseModel):
    user_id: int
    points: int
    reason: str

class AdminAwardPointsResponse(BaseModel):
    success: bool
    message: str
    new_total: int

class AdminStatsOverview(BaseModel):
    total_users: int
    total_points_awarded: int
    total_achievements_earned: int

class TopUserStats(BaseModel):
    username: str
    points: int

class PopularAchievementStats(BaseModel):
    name: str
    earned_count: int

class MonthlyActivityStats(BaseModel):
    month: str
    points: int
    transactions: int

class AdminGamificationStatsResponse(BaseModel):
    overview: AdminStatsOverview
    top_users: List[TopUserStats]
    popular_achievements: List[PopularAchievementStats]
    monthly_activity: List[MonthlyActivityStats]

# === ESQUEMAS DE ÓRDENES DE TRABAJO ===
class OrderCompletionResponse(BaseModel):
    success: bool
    points_awarded: int
    bonuses: Dict[str, Any]
    new_achievements: List[str]
    level_up: bool

# === ESQUEMAS DE SISTEMA ===
class SystemStatusResponse(BaseModel):
    initialized: bool
    enabled: bool
    total_users: int
    users_with_profile: int
    total_achievements: int
    total_points_awarded: int

class SystemActionResponse(BaseModel):
    success: bool
    message: str

class InitializeProfilesResponse(SystemActionResponse):
    pass

class ToggleSystemRequest(BaseModel):
    enabled: bool

class ResetUserPointsRequest(BaseModel):
    user_id: int

# === ESQUEMAS DE FILTROS Y PARÁMETROS ===
class LeaderboardFilters(BaseModel):
    period: LeaderboardPeriodEnum = LeaderboardPeriodEnum.ALL
    limit: int = Field(default=20, le=100, ge=1)

class TransactionHistoryFilters(BaseModel):
    limit: int = Field(default=50, le=200, ge=1)
    offset: int = Field(default=0, ge=0)

# === ESQUEMAS DE DESAFÍOS (FUTURO) ===
class ChallengeBase(BaseModel):
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    reward_points: int
    active: bool = True

class ChallengeResponse(ChallengeBase):
    id: int
    participants_count: int = 0
    
    class Config:
        orm_mode = True

class ChallengeParticipationResponse(BaseModel):
    id: int
    challenge_id: int
    user_id: int
    progress: int
    completed: bool
    completed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
