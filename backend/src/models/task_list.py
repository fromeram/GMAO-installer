# src/models/task_list.py
# Archivo corregido con el import correcto

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.models.base import Base  # ← IMPORT AGREGADO

class TaskList(Base):
    __tablename__ = "task_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    applies_to_type = Column(String, nullable=True)  # 'Preventivo', 'Correctivo', etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relaciones
    steps = relationship("TaskStep", back_populates="task_list", cascade="all, delete-orphan")
    created_by = relationship("User")
    
    # NUEVA: Relación inversa con WorkOrder
    work_orders = relationship("WorkOrder", back_populates="task_list")
    
    # NUEVA: Relación con ChecklistProgress
    checklist_progress = relationship("ChecklistProgress", back_populates="task_list")
    maintenances = relationship("Maintenance", back_populates="task_list")
    
    # Propiedades computadas
    @property
    def steps_count(self):
        return len(self.steps)
    
    @property
    def total_estimated_minutes(self):
        return sum(step.estimated_time_minutes or 0 for step in self.steps)
    
    def __repr__(self):
        return f"<TaskList(id={self.id}, name='{self.name}', steps={self.steps_count})>"