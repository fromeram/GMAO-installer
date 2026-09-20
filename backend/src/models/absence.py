# src/models/absence.py
from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import Base
from datetime import date

class Absence(Base):
    __tablename__ = "absences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    # Tipo: 'V'(Vacaciones), 'B'(Baja), 'A'(Asuntos Propios), 'F'(Festivo asignado), etc.
    absence_type = Column(String(10), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(Date, default=date.today)

    # Relación opcional a usuario (no estrictamente necesaria si no listas ausencias desde User)
    # user = relationship("User")

    def __repr__(self):
        return f"<Absence(id={self.id}, user={self.user_id}, type='{self.absence_type}', start={self.start_date}, end={self.end_date})>"