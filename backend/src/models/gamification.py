# backend/src/models/gamification.py
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import Base

class AchievementType(enum.Enum):
    SPEED = "speed"          # Completar rápido
    QUALITY = "quality"      # Sin retrabajos
    CONSISTENCY = "consistency"  # Rendimiento constante
    LEARNING = "learning"    # Mejorar habilidades
    TEAMWORK = "teamwork"    # Colaboración
    INNOVATION = "innovation"  # Sugerencias/mejoras

class BadgeRarity(enum.Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    type = Column(Enum(AchievementType), nullable=False)
    rarity = Column(Enum(BadgeRarity), default=BadgeRarity.COMMON)
    icon = Column(String(50), nullable=False)  # Emoji o icono
    points = Column(Integer, default=0)
    condition_json = Column(Text)  # JSON con condiciones específicas
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user_achievements = relationship("UserAchievement", back_populates="achievement")

class UserPoints(Base):
    __tablename__ = "user_points"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_points = Column(Integer, default=0)
    weekly_points = Column(Integer, default=0)
    monthly_points = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)  # Días consecutivos trabajando
    best_streak = Column(Integer, default=0)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    last_activity = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="points")
    transactions = relationship("PointTransaction", back_populates="user_points")

class PointTransaction(Base):
    __tablename__ = "point_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_points_id = Column(Integer, ForeignKey("user_points.id"), nullable=False)
    points = Column(Integer, nullable=False)  # Puede ser negativo
    reason = Column(String(200), nullable=False)
    entity_type = Column(String(50))  # work_order, maintenance, etc.
    entity_id = Column(Integer)
    multiplier = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user_points = relationship("UserPoints", back_populates="transactions")

class UserAchievement(Base):
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)
    progress = Column(Integer, default=100)  # Porcentaje completado
    notified = Column(Boolean, default=False)
    
    # Relaciones
    user = relationship("User")
    achievement = relationship("Achievement", back_populates="user_achievements")

class Challenge(Base):
    __tablename__ = "challenges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    type = Column(Enum(AchievementType), nullable=False)
    points_reward = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    target_value = Column(Integer, nullable=False)
    condition_json = Column(Text)
    active = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    
    # Relaciones
    participations = relationship("ChallengeParticipation", back_populates="challenge")

class ChallengeParticipation(Base):
    __tablename__ = "challenge_participations"
    
    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_progress = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    challenge = relationship("Challenge", back_populates="participations")
    user = relationship("User")

# ¡NO REDEFINIR LA CLASE USER AQUÍ!
# Las relaciones se añaden en user.py