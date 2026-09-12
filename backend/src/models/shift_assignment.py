# src/models/shift_assignment.py
from sqlalchemy import Column, Integer, Date, ForeignKey # <-- Asegúrate que Date está importado
from sqlalchemy.orm import relationship
from src.models.base import Base
# Quitado import date de datetime, no se usa si usamos Date de SQLAlchemy

# Puedes quitar la constante GLOBAL_REFERENCE_DATE si guardamos la fecha aquí
# GLOBAL_REFERENCE_DATE = date(2024, 1, 1)

class ShiftAssignment(Base):
    __tablename__ = "shift_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), unique=True, nullable=False)
    pattern_id = Column(Integer, ForeignKey("shift_patterns.id"), nullable=False)
    offset_days = Column(Integer, nullable=False, default=0)
    # --- AÑADIR ESTA LÍNEA ---
    reference_date = Column(Date, nullable=False) # <-- La columna que faltaba
    # -------------------------

    # Relaciones (sin cambios)
    user = relationship("User", back_populates="shift_assignment")
    pattern = relationship("ShiftPattern", back_populates="assignments")

    def __repr__(self):
         # Añadir reference_date al repr si quieres
         return f"<ShiftAssignment(id={self.id}, user={self.user_id}, pattern={self.pattern_id}, offset={self.offset_days}, ref={self.reference_date})>"