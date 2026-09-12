# src/models/checklist_progress.py
"""Modelo para el progreso de checklist de órdenes de trabajo"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from src.models.base import Base  # ← IMPORT AGREGADO

class ChecklistProgress(Base):
    __tablename__ = "checklist_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=False)
    task_list_id = Column(Integer, ForeignKey("task_lists.id"), nullable=False)
    
    # Progreso de pasos (JSON con estructura de ChecklistStepProgress)
    steps_progress = Column(JSON, nullable=False, default=[])
    
    # Métricas generales
    total_elapsed_time = Column(Float, default=0.0)  # minutos
    progress_percent = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    
    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Metadatos adicionales (JSON libre)
    extra_data = Column(JSON, nullable=True)
    
    # Relaciones
    work_order = relationship("WorkOrder")
    task_list = relationship("TaskList")
    created_by = relationship("User")
    
    def __repr__(self):
        return f"<ChecklistProgress(id={self.id}, work_order_id={self.work_order_id}, progress={self.progress_percent}%)>"