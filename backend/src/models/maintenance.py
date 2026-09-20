# backend/src/models/maintenance.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class Maintenance(Base):
    __tablename__ = "maintenances"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    assigned_role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    frequency = Column(String, nullable=True)
    next_maintenance_date = Column(DateTime, nullable=True)
    last_maintenance_date = Column(DateTime, nullable=True)
    
    # ✅ ELIMINADO: generated_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=True)
    
    notification_interval = Column(Integer, nullable=True)
    task_list_id = Column(Integer, ForeignKey("task_lists.id"), nullable=True)
    is_completed = Column(Boolean, default=False)
    
    # Campos para mantenimiento legal
    tipo_regulacion = Column(String(255))
    organismo_certificador = Column(String(255))
    numero_certificado = Column(String(255))
    normativa_aplicable = Column(Text)

    # Relaciones
    machine = relationship("Machine", back_populates="maintenances")
    assigned_role = relationship("Role")
    assigned_user = relationship("User")
    task_list = relationship("TaskList", back_populates="maintenances")
    
    # ✅ NUEVA RELACIÓN: Un mantenimiento puede tener MUCHAS órdenes de trabajo
    generated_work_orders = relationship(
        "WorkOrder", 
        foreign_keys="WorkOrder.generated_from_maintenance_id", 
        back_populates="generated_from_maintenance"
    )
