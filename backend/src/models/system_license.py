# src/models/system_license.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from .base import Base

class SystemLicense(Base):
    """
    Control de Licenciamiento y Periodo de Evaluación del GMAO.
    """
    __tablename__ = 'system_licenses'

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String(100), unique=True, nullable=False, index=True)
    installed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    trial_days = Column(Integer, default=90, nullable=False) # 3 meses (90 días de prueba)
    
    # Datos de activación si se introduce clave
    license_key = Column(Text, nullable=True)
    license_type = Column(String(50), default="trial") # 'trial', 'permanente', 'temporal'
    licensed_to = Column(String(255), nullable=True)   # Nombre de la empresa o cliente
    expires_at = Column(DateTime(timezone=True), nullable=True) # None si permanente
    activated_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<SystemLicense(machine_id='{self.machine_id}', type='{self.license_type}', active={self.is_active})>"
