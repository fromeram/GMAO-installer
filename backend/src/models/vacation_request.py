# src/models/vacation_request.py
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Enum as SQLEnum, DateTime # Renombrado Enum para evitar conflicto
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
# Asegúrate que la ruta a Base y User es correcta
from src.models.base import Base
from src.models.user import User

# Definir el Enum directamente aquí para la base de datos y el modelo
vacation_status_enum_sql = SQLEnum('Solicitado', 'Aprobado', 'Rechazado', name='vacation_status_enum')

class VacationRequest(Base):
    __tablename__ = "vacation_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    status = Column(vacation_status_enum_sql, nullable=False, default='Solicitado', index=True)
    notes = Column(Text, nullable=True) # Notas del solicitante
    manager_notes = Column(Text, nullable=True) # Notas del responsable
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now()) # Añadir server_default
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Quién aprobó/rechazó

    # Relaciones
    # Recordatorio: Añadir 'vacation_requests = relationship("VacationRequest", ...)' en models/user.py
    user = relationship("User", back_populates="vacation_requests", foreign_keys=[user_id]) # USAR ESTA LÍNEA
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])

    def __repr__(self):
        return f"<VacationRequest(id={self.id}, user={self.user_id}, status='{self.status}', start={self.start_date}, end={self.end_date})>"