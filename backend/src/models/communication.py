# src/models/communication.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from typing import Optional

from .base import Base

class CommunicationType(enum.Enum):
    SUGGESTION = "Sugerencia"
    MATERIAL_REQUEST = "Pedido de Material"
    COMPLAINT = "Queja/Problema"
    QUESTION = "Consulta"
    OTHER = "Otro"
    # NUEVOS TIPOS PARA ADMIN
    ADMIN_MESSAGE = "Mensaje Administrativo"
    TASK_ASSIGNMENT = "Asignación de Tarea"
    ANNOUNCEMENT = "Comunicado"

class CommunicationStatus(enum.Enum):
    PENDING = "Pendiente"
    REVIEWED = "Revisado"
    IN_PROGRESS = "En Proceso"
    RESOLVED = "Resuelto"
    REJECTED = "Rechazado"
    READ = "Leído"  # Nuevo estado para mensajes de admin

class CommunicationDirection(enum.Enum):
    """Dirección de la comunicación"""
    UPWARD = "Operario a Admin"      # Operario -> Admin (como antes)
    DOWNWARD = "Admin a Operario"    # Admin -> Operario (nuevo)
    BROADCAST = "Difusión"           # Admin -> Múltiples usuarios (nuevo)

class Communication(Base):
    __tablename__ = "communications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Información básica
    type = Column(SQLEnum(CommunicationType, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=CommunicationType.SUGGESTION)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Estado y seguimiento
    status = Column(SQLEnum(CommunicationStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=CommunicationStatus.PENDING)
    priority = Column(String(20), default="Normal")  # Baja, Normal, Alta, Urgente
    
    # NUEVO: Dirección de la comunicación
    direction = Column(SQLEnum(CommunicationDirection, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=CommunicationDirection.UPWARD)
    
    # Relaciones
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin/Jefe que revisa O usuario destinatario
    
    # NUEVO: Para mensajes dirigidos a roles específicos
    target_role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)  # Rol destinatario
    target_department = Column(String(100), nullable=True)  # Departamento destinatario
    
    # Fechas
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)  # NUEVO: Cuándo fue leído
    
    # Campos adicionales
    admin_notes = Column(Text, nullable=True)  # Notas privadas del admin
    admin_response = Column(Text, nullable=True)  # Respuesta visible para el operario
    is_anonymous = Column(Boolean, default=False)  # Por si quieren hacer sugerencias anónimas
    
    # NUEVO: Para respuestas
    parent_communication_id = Column(Integer, ForeignKey("communications.id"), nullable=True)  # Si es respuesta a otra comunicación
    requires_response = Column(Boolean, default=False)  # Si requiere respuesta
    
    # Metadatos
    department = Column(String(100), nullable=True)  # Departamento relacionado
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=True)  # Máquina relacionada si aplica
    
    # Relaciones ORM
    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="communications_created")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], back_populates="communications_assigned")
    target_role = relationship("Role", foreign_keys=[target_role_id])
    machine = relationship("Machine", backref="communications")
    
    # NUEVO: Relación para respuestas
    parent_communication = relationship("Communication", remote_side=[id], backref="replies")
    
    # NUEVO: Relación para tracking de lecturas
    read_receipts = relationship("CommunicationRead", back_populates="communication", cascade="all, delete-orphan")
    
    @property
    def created_by_name(self) -> Optional[str]:
        """Devuelve el nombre de usuario del creador o 'Anónimo'."""
        if self.is_anonymous:
            return "Anónimo"
        if self.created_by:
            return self.created_by.username
        return None

    @property
    def assigned_to_name(self) -> Optional[str]:
        """Devuelve el nombre de usuario de la persona asignada."""
        if self.assigned_to:
            return self.assigned_to.username
        return None
        
    @property
    def target_role_name(self) -> Optional[str]:
        """Devuelve el nombre del rol destinatario."""
        if self.target_role:
            return self.target_role.nombre
        return None

    @property
    def machine_name(self) -> Optional[str]:
        """Devuelve el nombre de la máquina relacionada."""
        if self.machine:
            return self.machine.nombre
        return None

    def __repr__(self):
        return f"<Communication {self.id}: {self.type.value} - {self.subject[:50]}>"
    
    @property
    def is_pending(self):
        return self.status == CommunicationStatus.PENDING
    
    @property
    def is_resolved(self):
        return self.status == CommunicationStatus.RESOLVED
    
    @property
    def is_from_admin(self):
        """Verifica si el mensaje fue enviado por un admin"""
        return self.direction == CommunicationDirection.DOWNWARD
    
    @property
    def is_broadcast(self):
        """Verifica si es un mensaje de difusión"""
        return self.direction == CommunicationDirection.BROADCAST
    
    @property
    def age_in_days(self):
        return (datetime.utcnow() - self.created_at).days


# Tabla para tracking de lecturas en mensajes broadcast
class CommunicationRead(Base):
    __tablename__ = "communication_reads"
    
    id = Column(Integer, primary_key=True)
    communication_id = Column(Integer, ForeignKey("communications.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    read_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones - ESPECIFICAR back_populates para evitar conflictos
    communication = relationship("Communication", back_populates="read_receipts")
    user = relationship("User", back_populates="communication_reads")
    
    def __repr__(self):
        return f"<CommunicationRead {self.communication_id} by {self.user_id}>"