# src/models/shift_pattern.py
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from src.models.base import Base

class ShiftPattern(Base):
    __tablename__ = "shift_patterns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    pattern_sequence = Column(String, nullable=False)
    cycle_length_days = Column(Integer, nullable=False)

    assignments = relationship("ShiftAssignment", back_populates="pattern")

    # Autocalcular longitud al crear/actualizar
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.pattern_sequence:
            self.cycle_length_days = len(self.pattern_sequence)

    def __repr__(self):
         return f"<ShiftPattern(id={self.id}, name='{self.name}')>"