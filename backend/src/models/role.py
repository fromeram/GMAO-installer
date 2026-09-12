"""
Modelo Role.
Define los roles del sistema y la relación con usuarios.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    
    # Relación con usuarios
    users = relationship("User", back_populates="role", lazy="dynamic")
