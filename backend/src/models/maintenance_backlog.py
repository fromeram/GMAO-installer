# backend/src/models/maintenance_backlog.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
import enum

class BacklogPriority(str, enum.Enum):  # Cambiado a str, enum.Enum
    LOW = "Baja"
    MEDIUM = "Media"
    HIGH = "Alta"
    CRITICAL = "Crítica"

class BacklogStatus(str, enum.Enum):  # Cambiado a str, enum.Enum
    PENDING = "Pendiente"
    PLANNED = "Planificado"
    IN_PROGRESS = "En Progreso"
    COMPLETED = "Completado"
    CANCELLED = "Cancelado"

class MaintenanceBacklog(Base):
    __tablename__ = 'maintenance_backlogs'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    priority = Column(Enum(BacklogPriority), default=BacklogPriority.MEDIUM)
    status = Column(Enum(BacklogStatus), default=BacklogStatus.PENDING)
    
    # Relaciones
    machine_id = Column(Integer, ForeignKey('machines.id'))
    section_id = Column(Integer, ForeignKey('sections.id'))
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey('users.id'))
    
    # Estimaciones
    estimated_hours = Column(Integer)  # Horas estimadas
    estimated_downtime = Column(Integer)  # Tiempo de parada requerido
    
    # Seguimiento
    notes = Column(Text)  # Notas adicionales
    completion_notes = Column(Text)
    actual_work_order_id = Column(Integer, ForeignKey('work_orders.id'))  # Si se convierte en OT
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relaciones
    machine = relationship("Machine", backref="backlog_items")
    section = relationship("Section", backref="backlog_items")
    created_by = relationship("User", foreign_keys=[created_by_id], backref="created_backlog_items")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], backref="assigned_backlog_items")
    work_order = relationship("WorkOrder", backref="backlog_source")