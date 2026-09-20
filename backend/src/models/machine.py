# src/models/machine.py
"""
Modelo de máquina.
Cada máquina pertenece a una línea y una sección, y se relaciona con mantenimientos y órdenes de trabajo.
"""

# Asegúrate de importar String si no estaba ya
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from .associations import MachinePartAssociation

class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    modelo = Column(String, nullable=False)
    marca = Column(String, nullable=False)
    numero_serie = Column(String, unique=True, nullable=False)
    line_id = Column(Integer, ForeignKey("lines.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)

    # --- NUEVO CAMPO ---
    criticidad = Column(String(50), nullable=True) # Ej: 'Alta', 'Media', 'Baja'
    # -------------------

    line = relationship("Line", back_populates="machines")
    section = relationship("Section", back_populates="machines")
    maintenances = relationship("Maintenance", back_populates="machine")
    #predictions = relationship("MachinePrediction", back_populates="machine", cascade="all, delete-orphan")

    work_orders = relationship("WorkOrder", back_populates="machine_obj") # Relación con WorkOrder
    part_associations = relationship(
        "MachinePartAssociation",
        back_populates="machine",
        cascade="all, delete-orphan", # Si borras Machine, borra sus asociaciones
        lazy="selectin" # Carga eficiente de asociaciones y partes relacionadas
    )
