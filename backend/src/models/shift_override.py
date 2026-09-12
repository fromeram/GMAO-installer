# src/models/shift_override.py
from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import Base
from src.models.user import User

class ShiftOverride(Base):
    __tablename__ = "shift_overrides"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    actual_shift_code = Column(String(10), nullable=False) # M, T, N...
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User")