# src/models/alert.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

# Tabla de asociación para alertas y usuarios (muchos a muchos)
alert_user = Table('alert_user', Base.metadata,
    Column('alert_id', Integer, ForeignKey('alerts.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False, index=True)  # maintenance, stock, system, etc.
    message = Column(Text, nullable=False)
    entity_type = Column(String(50), nullable=True)  # machine, inventory, work_order, etc.
    entity_id = Column(Integer, nullable=True)
    severity = Column(String(20), nullable=False, default="info")  # info, warning, danger
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relaciones
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    users = relationship("User", secondary=alert_user, backref="alerts")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, type='{self.type}', severity='{self.severity}', resolved={self.resolved})>"