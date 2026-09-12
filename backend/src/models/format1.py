# src/models/format.py - Modelo para Formatos Maestros CORREGIDO
from sqlalchemy import Column, Integer, String, Text, Float, JSON, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Format(Base):
    """
    Modelo para gestión de formatos maestros en cambios de formato.
    Permite definir formatos estándar con sus características y tiempos estimados.
    """
    __tablename__ = "formats"
    
    # Campos principales
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Tiempos y configuración
    estimated_setup_time = Column(Float, nullable=True, comment="Tiempo estimado de setup en horas")
    
    # Configuración avanzada (JSON para flexibilidad)
    machines_requiring_adjustment = Column(JSON, nullable=True, comment="Lista de IDs de máquinas que requieren ajuste")
    tools_materials_needed = Column(JSON, nullable=True, comment="Lista de herramientas/materiales necesarios")
    
    # Estado y control
    active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # RELACIONES CORREGIDAS: Sin back_populates problemáticos
    # Estas relaciones permiten acceder a las órdenes que usan este formato
    work_orders_as_from = relationship(
        "WorkOrder", 
        primaryjoin="Format.id == WorkOrder.format_from_id",
        back_populates="format_from_obj" 
    )
    work_orders_as_to = relationship(
        "WorkOrder", 
        primaryjoin="Format.id == WorkOrder.format_to_id",
        back_populates="format_to_obj"
    )

    def __repr__(self):
        return f"<Format(id={self.id}, name='{self.name}', active={self.active})>"
    
    @property
    def machines_count(self):
        """Retorna el número de máquinas que requieren ajuste para este formato"""
        if self.machines_requiring_adjustment and isinstance(self.machines_requiring_adjustment, list):
            return len(self.machines_requiring_adjustment)
        return 0
    
    @property
    def tools_count(self):
        """Retorna el número de herramientas/materiales necesarios"""
        if self.tools_materials_needed and isinstance(self.tools_materials_needed, list):
            return len(self.tools_materials_needed)
        return 0