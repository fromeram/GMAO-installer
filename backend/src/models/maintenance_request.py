# backend/src/models/maintenance_request.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class MaintenanceRequest(Base):
    """
    Modelo para gestionar Solicitudes de Mantenimiento (Triage).
    Iniciadas por operadores de producción. Solo se convierten en 
    Órdenes de Trabajo si son aprobadas.
    """
    __tablename__ = 'maintenance_requests'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    reported_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=True)
    
    status = Column(String, nullable=False, default="Pendiente") # 'Pendiente', 'Aprobada', 'Rechazada'
    priority = Column(String, nullable=True) # 'Baja', 'Media', 'Alta'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Campo para enlazar con la Orden de Trabajo resultante si se aprueba
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=True)

    # Relaciones
    reported_by = relationship("User", foreign_keys=[reported_by_id], back_populates="maintenance_requests")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    machine = relationship("Machine", back_populates="maintenance_requests")
    work_order = relationship("WorkOrder", back_populates="maintenance_request_origin")

    def __repr__(self):
        return f"<MaintenanceRequest(id={self.id}, title='{self.title}', status='{self.status}')>"
