from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Numeric, Boolean, Text
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class WorkOrderTechnician(Base):
    __tablename__ = "work_order_technicians"
    
    id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="apoyo", index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, index=True)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    hours_worked = Column(Numeric(5, 2), default=0.00)
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text, nullable=True)
    
    # Relaciones
    work_order = relationship("WorkOrder", back_populates="technicians")
    technician = relationship("User", foreign_keys=[user_id], back_populates="work_assignments")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
    
    def __repr__(self):
        return f"<WorkOrderTechnician(order_id={self.work_order_id}, user_id={self.user_id}, role='{self.role}')>"