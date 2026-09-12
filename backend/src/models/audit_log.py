# src/models/audit_log.py - VERSIÓN CORREGIDA

from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime # Importar DateTime explícitamente


from .base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    
    # Hemos dejado los nombres de columna como estaban en tu versión anterior
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(Integer, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_name = Column(String(255), nullable=False)
    user_role = Column(String(100))
    

    timestamp = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False, 
        index=True
    )
    # ------------------------------------

    ip_address = Column(String(45))
    user_agent = Column(Text)
    old_values = Column(JSON)
    new_values = Column(JSON)
    changes_summary = Column(Text)
    module = Column(String(100), index=True)
    severity = Column(String(20), default='MEDIUM', index=True)
    notes = Column(Text)
    session_id = Column(String(255))
    
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user={self.user_name}, timestamp={self.timestamp})>"