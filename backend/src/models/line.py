# backend/src/models/line.py
"""
Modelo de línea.
Cada línea pertenece a una sección y se relaciona con máquinas.
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import Base
# from .section import Section # Asegúrate que Section está importado si es necesario
# from .machine import Machine

class Line(Base):
    __tablename__ = "lines"

    id = Column(Integer, primary_key=True)
    # --- MODIFICADO: Ajustar a lo detectado ---
    nombre = Column(String(255), nullable=False)
    # ------------------------------------------
    section_id = Column(Integer, ForeignKey('sections.id'), nullable=False) # Mantenido nullable=False

    # Relaciones
    # Asegúrate que Section tiene back_populates="lines"
    section = relationship("Section", back_populates="lines")
    # Asegúrate que Machine tiene back_populates="line"
    machines = relationship("Machine", back_populates="line")