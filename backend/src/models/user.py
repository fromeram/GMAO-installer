# backend/src/models/user.py
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship # <-- Necesario para relationship
from .base import Base
from .communication import Communication # ¡Importante añadir esto!

# Quitar import no usado: from .role import Role
# Quitar import no usado: from .document import Document
# Asegúrate que Section y WorkOrder se importan si se usan en relaciones o métodos
# from .section import Section
# from .work_order import WorkOrder

# Importar ShiftAssignment si se usa como tipo directo (no necesario para relationship con string)
# from .shift_assignment import ShiftAssignment

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    email = Column(String(255), nullable=True)
    
    # Relaciones
    role = relationship("Role", back_populates="users")
    section = relationship("Section", back_populates="users")
    # Asumiendo que WorkOrder tiene 'assigned_to' con back_populates="orders_assigned"
    orders_assigned = relationship("WorkOrder", back_populates="assigned_to", foreign_keys="[WorkOrder.assigned_to_id]")
    # Asumiendo que Document tiene 'created_by' con back_populates="documents"
    documents = relationship("Document", back_populates="created_by")

    # --- RELACIÓN CON ASIGNACIÓN DE TURNO (YA ESTABA CORRECTA EN TU CÓDIGO) ---
    shift_assignment = relationship("ShiftAssignment", back_populates="user", uselist=False, cascade="all, delete-orphan")
    # ------------------------------------------------------------------------
    vacation_requests = relationship("VacationRequest", back_populates="user", foreign_keys="[VacationRequest.user_id]", cascade="all, delete-orphan")
    # ------------------------------------------------------------------------
    #ai_predictions = relationship("MachinePrediction", back_populates="created_by")
    work_assignments = relationship("WorkOrderTechnician", foreign_keys="WorkOrderTechnician.user_id", back_populates="technician")

    audit_logs = relationship("AuditLog", back_populates="user")
    points = relationship("UserPoints", back_populates="user", uselist=False)
    achievements = relationship("UserAchievement", back_populates="user")
    #checklist_progress = relationship("ChecklistProgress", back_populates="created_by")
    communications_created = relationship("Communication", foreign_keys="Communication.created_by_id", back_populates="created_by")
    communications_assigned = relationship("Communication", foreign_keys="Communication.assigned_to_id", back_populates="assigned_to")
    communication_reads = relationship(
       "CommunicationRead",
       back_populates="user",
       cascade="all, delete-orphan"
)

    @property
    def is_admin(self):
        # Es más seguro comprobar si role existe antes de acceder a nombre
        return self.role and self.role.nombre == "Administrador"

    @property
    def is_maintenance_chief(self):
        return self.role and self.role.nombre == "Jefe de Mantenimiento"

    @property
    def is_section_chief(self):
        return self.role and self.role.nombre == "Jefe de Sección"
    
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    @property
    def can_send_admin_messages(self):
        """Verifica si el usuario puede enviar mensajes administrativos"""
        return self.role and self.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
    
    @property
    def can_manage_communications(self):
        """Verifica si el usuario puede gestionar todas las comunicaciones"""
        return self.can_send_admin_messages
    
    def get_active_work_orders(self):
        """Retorna órdenes de trabajo activas del usuario"""
        return [assignment.work_order for assignment in self.work_assignments 
                if assignment.is_active and assignment.work_order.status in ['Pendiente', 'En curso', 'En revisión']]

    
    # ===== NUEVOS MÉTODOS PARA COMUNICACIONES =====
    def get_unread_communications(self, db_session):
        """Obtiene comunicaciones no leídas dirigidas a este usuario"""
        from sqlalchemy import or_, and_
        from .communication import Communication, CommunicationDirection, CommunicationRead
        
        # Mensajes directos no leídos (dirigidos específicamente a este usuario)
        direct_query = db_session.query(Communication).filter(
            Communication.assigned_to_id == self.id,
            Communication.direction == CommunicationDirection.DOWNWARD,
            Communication.read_at.is_(None)
        )
        
        # Mensajes broadcast no leídos (dirigidos a su rol o departamento)
        broadcast_query = db_session.query(Communication).filter(
            or_(
                # Dirigidos a su rol
                and_(
                    Communication.target_role_id == self.role_id,
                    Communication.target_role_id.isnot(None)
                ),
                # Dirigidos a su departamento
                and_(
                    Communication.target_department == (self.section.nombre if self.section else None),
                    Communication.target_department.isnot(None),
                    self.section.isnot(None)  # Solo si tiene sección asignada
                )
            ),
            Communication.direction == CommunicationDirection.BROADCAST,
            # No existe registro de lectura para este usuario
            ~Communication.read_receipts.any(CommunicationRead.user_id == self.id)
        )
        
        # Unir ambas consultas
        try:
            all_unread = direct_query.union(broadcast_query).all()
            return all_unread
        except Exception:
            # Fallback en caso de error
            return direct_query.all()

    def get_unread_count(self, db_session):
        """Cuenta comunicaciones no leídas"""
        try:
            return len(self.get_unread_communications(db_session))
        except Exception:
            return 0
    
    def mark_communication_as_read(self, communication_id, db_session):
        """Marca una comunicación como leída"""
        from datetime import datetime, timezone
        from .communication import Communication, CommunicationDirection, CommunicationRead
        
        communication = db_session.query(Communication).filter(
            Communication.id == communication_id
        ).first()
        
        if not communication:
            return False
        
        # Si es un mensaje directo, actualizar read_at
        if communication.direction == CommunicationDirection.DOWNWARD and communication.assigned_to_id == self.id:
            communication.read_at = datetime.now(timezone.utc)
            db_session.commit()
            return True
        
        # Si es un mensaje broadcast, crear registro de lectura
        elif communication.direction == CommunicationDirection.BROADCAST:
            # Verificar si el usuario puede leer este mensaje
            can_read = (
                (communication.target_role_id == self.role_id) or
                (communication.target_department and self.section and 
                 communication.target_department == self.section.nombre)
            )
            
            if can_read:
                # Verificar si ya existe registro de lectura
                existing_read = db_session.query(CommunicationRead).filter(
                    CommunicationRead.communication_id == communication_id,
                    CommunicationRead.user_id == self.id
                ).first()
                
                if not existing_read:
                    read_record = CommunicationRead(
                        communication_id=communication_id,
                        user_id=self.id
                    )
                    db_session.add(read_record)
                    db_session.commit()
                    return True
        
        return False
    
    def get_my_communications(self, db_session, limit=50):
        """Obtiene todas las comunicaciones del usuario (enviadas y recibidas)"""
        from sqlalchemy import or_, and_, desc
        from .communication import Communication
        
        # Mensajes enviados por el usuario
        sent_query = db_session.query(Communication).filter(
            Communication.created_by_id == self.id
        )
        
        # Mensajes recibidos por el usuario
        received_query = db_session.query(Communication).filter(
            or_(
                # Dirigidos específicamente a él
                Communication.assigned_to_id == self.id,
                # Dirigidos a su rol
                and_(
                    Communication.target_role_id == self.role_id,
                    Communication.target_role_id.isnot(None)
                ),
                # Dirigidos a su departamento
                and_(
                    Communication.target_department == (self.section.nombre if self.section else None),
                    Communication.target_department.isnot(None),
                    self.section.isnot(None)
                )
            )
        )
        
        # Unir y ordenar por fecha
        try:
            all_communications = sent_query.union(received_query).order_by(
                desc(Communication.created_at)
            ).limit(limit).all()
            return all_communications
        except Exception:
            # Fallback: solo mensajes enviados
            return sent_query.order_by(desc(Communication.created_at)).limit(limit).all()
    
    def has_unread_urgent_messages(self, db_session):
        """Verifica si tiene mensajes urgentes no leídos"""
        try:
            unread = self.get_unread_communications(db_session)
            return any(comm.priority == "Urgente" for comm in unread)
        except Exception:
            return False