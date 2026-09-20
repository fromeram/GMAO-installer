# src/models/task_step.py
"""Modelo para los Pasos dentro de una Lista de Tareas Estándar"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import Base # Ajusta la ruta si Base está en otro sitio

class TaskStep(Base):
    __tablename__ = "task_steps"

    id = Column(Integer, primary_key=True, index=True)
    task_list_id = Column(Integer, ForeignKey("task_lists.id", ondelete='CASCADE'), nullable=False) # Vinculado a TaskList
    step_order = Column(Integer, nullable=False, default=1) # Orden del paso dentro de la lista
    description = Column(Text, nullable=False) # Descripción de la tarea a realizar
    estimated_time_minutes = Column(Integer, nullable=True) # Tiempo estimado para este paso (opcional)

    # Relación con la lista de tareas a la que pertenece
    task_list = relationship("TaskList", back_populates="steps")

    def __repr__(self):
        return f"<TaskStep(id={self.id}, list_id={self.task_list_id}, order={self.step_order}, desc='{self.description[:20]}...')>"