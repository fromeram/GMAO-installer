# src/routers/communication_routes.py - VERSIÓN CORREGIDA Y COMPLETA
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, or_, and_

from ..database import get_db
from ..auth import get_current_user, get_admin_user
from ..models.user import User
from ..models.role import Role
from ..models.communication import Communication, CommunicationType, CommunicationStatus, CommunicationDirection, CommunicationRead as CommunicationReadModel
from ..models.machine import Machine
from ..middleware.audit_middleware import audit_manager
from pydantic import BaseModel, Field
from starlette.responses import Response

# ==========================================
# MODELOS PYDANTIC ACTUALIZADOS Y RENOMBRADOS
# ==========================================

class CommunicationBase(BaseModel):
    type: CommunicationType
    subject: str = Field(..., max_length=200, min_length=5)
    message: str = Field(..., min_length=10)
    priority: Optional[str] = Field("Normal", pattern="^(Baja|Normal|Alta|Urgente)$")
    department: Optional[str] = None
    machine_id: Optional[int] = None
    is_anonymous: Optional[bool] = False

class CommunicationCreate(CommunicationBase):
    parent_communication_id: Optional[int] = None

class CommunicationStatsResponse(BaseModel):
    total_communications: int
    pending_count: int
    in_progress_count: int
    resolved_count: int
    by_type: dict
    by_priority: dict
    avg_resolution_time_days: float
    oldest_pending_days: int

class AdminCommunicationCreate(BaseModel):
    type: CommunicationType = Field(..., description="Tipo de comunicación")
    subject: str = Field(..., max_length=200, min_length=5)
    message: str = Field(..., min_length=10)
    priority: str = Field("Normal", pattern="^(Baja|Normal|Alta|Urgente)$")
    target_user_id: Optional[int] = Field(None, description="Usuario específico destinatario")
    target_role_id: Optional[int] = Field(None, description="Rol destinatario (ej: todos los mecánicos)")
    target_department: Optional[str] = Field(None, description="Departamento destinatario")
    machine_id: Optional[int] = None
    requires_response: Optional[bool] = False
    parent_communication_id: Optional[int] = Field(None, description="Si es respuesta a otra comunicación")

class CommunicationUpdate(BaseModel):
    status: Optional[CommunicationStatus] = None
    assigned_to_id: Optional[int] = None
    admin_notes: Optional[str] = None
    admin_response: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(Baja|Normal|Alta|Urgente)$")

class CommunicationReadSchema(BaseModel):
    id: int
    type: CommunicationType
    subject: str
    message: str
    status: CommunicationStatus
    priority: str
    direction: CommunicationDirection
    created_at: datetime
    updated_at: datetime
    reviewed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    created_by_id: int
    created_by_name: Optional[str] = None
    is_anonymous: bool = False
    
    assigned_to_id: Optional[int] = None
    assigned_to_name: Optional[str] = None
    target_role_name: Optional[str] = None
    target_department: Optional[str] = None
    
    admin_response: Optional[str] = None
    requires_response: bool = False
    
    department: Optional[str] = None
    machine_id: Optional[int] = None
    machine_name: Optional[str] = None
    parent_communication_id: Optional[int] = None
    
    replies: List['CommunicationReadSchema'] = []
    
    class Config:
        orm_mode = True

class CommunicationAdminReadSchema(CommunicationReadSchema):
    admin_notes: Optional[str] = None
    read_count: Optional[int] = 0
    
    class Config:
        orm_mode = True

CommunicationReadSchema.update_forward_refs()

class AvailableUser(BaseModel):
    id: int
    username: str
    role_name: str
    department: Optional[str] = None

class AvailableRole(BaseModel):
    id: int
    nombre: str
    user_count: int

# ==========================================
# ROUTER SETUP
# ==========================================

router = APIRouter(prefix="/communications", tags=["Communications"])

def user_can_view_communication(user: User, communication: Communication) -> bool:
    """Determina si un usuario puede ver una comunicación específica"""
    # Administradores y jefes pueden ver todo
    if user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]:
        return True
    
    # Los usuarios pueden ver sus propias comunicaciones creadas
    if communication.created_by_id == user.id:
        return True
    
    # Los usuarios pueden ver comunicaciones dirigidas a ellos
    if communication.assigned_to_id == user.id:
        return True
    
    # Los usuarios pueden ver comunicaciones dirigidas a su rol
    if communication.target_role_id and communication.target_role_id == user.role_id:
        return True
    
    # Los usuarios pueden ver comunicaciones dirigidas a su departamento
    if (communication.target_department and 
        user.section and 
        communication.target_department == user.section.nombre):
        return True
    
    return False

def user_can_manage_communications(user: User) -> bool:
    """Determina si un usuario puede gestionar comunicaciones (Admin/Jefe)"""
    return user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]

# ==========================================
# ENDPOINTS DE ADMINISTRACIÓN (ACTUALIZADOS)
# ==========================================

@router.get("/admin/available-users", response_model=List[AvailableUser])
def get_available_users(
    role_filter: Optional[str] = Query(None, description="Filtrar por rol"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    query = db.query(User).options(joinedload(User.role), joinedload(User.section))
    if role_filter:
        query = query.join(Role).filter(Role.nombre == role_filter)
    query = query.join(Role).filter(Role.nombre != "Administrador")
    users = query.order_by(User.username).all()
    result = []
    for user in users:
        result.append(AvailableUser(
            id=user.id,
            username=user.username,
            role_name=user.role.nombre if user.role else "Sin rol",
            department=user.section.nombre if user.section else None
        ))
    return result

@router.get("/admin/available-roles", response_model=List[AvailableRole])
def get_available_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    role_counts = db.query(
        Role.id,
        Role.nombre,
        func.count(User.id).label('user_count')
    ).outerjoin(User).group_by(Role.id, Role.nombre).all()
    result = []
    for role_id, role_name, user_count in role_counts:
        if role_name != "Administrador":
            result.append(AvailableRole(
                id=role_id,
                nombre=role_name,
                user_count=user_count or 0
            ))
    return result

@router.post("/admin/send-message", response_model=CommunicationAdminReadSchema, status_code=status.HTTP_201_CREATED)
def send_admin_message(
    message_data: AdminCommunicationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    targets = [message_data.target_user_id, message_data.target_role_id, message_data.target_department]
    if sum(t is not None for t in targets) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe especificar exactamente un destinatario: usuario, rol o departamento"
        )

    target_user, target_role = None, None
    if message_data.machine_id and not db.query(Machine).filter(Machine.id == message_data.machine_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Máquina no encontrada")
    if message_data.target_user_id:
        target_user = db.query(User).filter(User.id == message_data.target_user_id).first()
        if not target_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario destinatario no encontrado")
    if message_data.target_role_id:
        target_role = db.query(Role).filter(Role.id == message_data.target_role_id).first()
        if not target_role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol destinatario no encontrado")

    direction = CommunicationDirection.BROADCAST if message_data.target_role_id or message_data.target_department else CommunicationDirection.DOWNWARD
    
    communication = Communication(
        type=message_data.type, subject=message_data.subject, message=message_data.message,
        priority=message_data.priority, direction=direction, created_by_id=current_user.id,
        assigned_to_id=message_data.target_user_id, target_role_id=message_data.target_role_id,
        target_department=message_data.target_department, machine_id=message_data.machine_id,
        requires_response=message_data.requires_response, parent_communication_id=message_data.parent_communication_id,
        status=CommunicationStatus.PENDING, department=current_user.section.nombre if current_user.section else None
    )
    db.add(communication)
    db.commit()
    db.refresh(communication)

    try:
        target_info = f"a departamento {message_data.target_department}" if message_data.target_department else (f"a rol {target_role.nombre}" if target_role else f"a usuario {target_user.username}")
        audit_manager.log_action(db=db, action="CREATE", entity=communication, user=current_user, request=request,
                                 notes=f"Mensaje administrativo enviado {target_info}: {communication.subject}")
        db.commit()
    except Exception as e:
        print(f"Warning: Audit trail failed: {e}")

    return CommunicationAdminReadSchema.from_orm(communication)

@router.get("/unread-count", response_model=dict)
def get_unread_count(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Obtener cantidad de mensajes no leídos para el usuario actual"""
    
    unread_condition = or_(
        and_(
            Communication.assigned_to_id == current_user.id,
            Communication.read_at.is_(None)
        ),
        and_(
            Communication.target_role_id == current_user.role_id,
            Communication.target_role_id.isnot(None),
            ~Communication.read_receipts.any(CommunicationReadModel.user_id == current_user.id)
        ),
        and_(
            Communication.target_department == (current_user.section.nombre if current_user.section else None),
            Communication.target_department.isnot(None),
            ~Communication.read_receipts.any(CommunicationReadModel.user_id == current_user.id)
        )
    )

    unread_count = db.query(Communication).filter(
        unread_condition,
        Communication.direction.in_([CommunicationDirection.DOWNWARD, CommunicationDirection.BROADCAST]),
        Communication.status != CommunicationStatus.RESOLVED
    ).count()
    
    return {"unread_count": unread_count}

# ==========================================
# ENDPOINTS PARA OPERARIOS (ACTUALIZADOS)
# ==========================================

@router.get("/my-messages", response_model=List[CommunicationReadSchema])
def get_my_messages(
    status_filter: Optional[CommunicationStatus] = Query(None, description="Filtrar por estado"),
    type_filter: Optional[CommunicationType] = Query(None, description="Filtrar por tipo"),
    direction_filter: Optional[CommunicationDirection] = Query(None, description="Filtrar por dirección"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener TODOS los hilos de mensajes del usuario (enviados y recibidos)."""
    
    base_condition = Communication.parent_communication_id.is_(None)

    sent_query = db.query(Communication).filter(
        Communication.created_by_id == current_user.id,
        base_condition
    )
    
    received_query = db.query(Communication).filter(
        or_(
            Communication.assigned_to_id == current_user.id,
            and_(Communication.target_role_id == current_user.role_id, Communication.target_role_id.isnot(None)),
            and_(Communication.target_department == (current_user.section.nombre if current_user.section else None), Communication.target_department.isnot(None))
        ),
        base_condition
    )
    
    query = sent_query.union(received_query).options(
        joinedload(Communication.machine),
        joinedload(Communication.created_by),
        joinedload(Communication.assigned_to),
        joinedload(Communication.target_role),
        joinedload(Communication.replies).options(
            joinedload(Communication.created_by)
        )
    )
    
    if status_filter: query = query.filter(Communication.status == status_filter)
    if type_filter: query = query.filter(Communication.type == type_filter)
    if direction_filter: query = query.filter(Communication.direction == direction_filter)
    
    communications = query.order_by(desc(Communication.created_at)).limit(limit).all()
    
    result = []
    for comm in communications:
        is_recipient = (comm.assigned_to_id == current_user.id or 
                        comm.target_role_id == current_user.role_id or
                        (comm.target_department and current_user.section and comm.target_department == current_user.section.nombre))

        if is_recipient:
            if comm.direction == CommunicationDirection.BROADCAST:
                existing_read = db.query(CommunicationReadModel).filter(
                    CommunicationReadModel.communication_id == comm.id,
                    CommunicationReadModel.user_id == current_user.id
                ).first()
                if not existing_read:
                    read_record = CommunicationReadModel(communication_id=comm.id, user_id=current_user.id)
                    db.add(read_record)
                    db.commit()
            elif comm.read_at is None:
                comm.read_at = datetime.now(timezone.utc)
                db.add(comm)
                db.commit()
        
        result.append(CommunicationReadSchema.from_orm(comm))
    
    return result

@router.post("/", response_model=CommunicationReadSchema, status_code=status.HTTP_201_CREATED)
def create_communication(
    communication_data: CommunicationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if communication_data.machine_id and not db.query(Machine).filter(Machine.id == communication_data.machine_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Máquina no encontrada")
    
    data = communication_data.dict()
    
    if data.get("parent_communication_id"):
        parent = db.query(Communication).filter(Communication.id == data["parent_communication_id"]).first()
        if parent:
            if not data.get("subject"):
                data["subject"] = f"Re: {parent.subject}"
            if not data.get("type"):
                 data["type"] = parent.type
    
    # 🔥 AGREGAR ESTA LÍNEA AQUÍ:
    data.pop('department', None)
    
    communication = Communication(
        **data,
        created_by_id=current_user.id,
        department=current_user.section.nombre if current_user.section else None,
        direction=CommunicationDirection.UPWARD
    )
    db.add(communication)
    db.commit()
    db.refresh(communication)
    
    try:
        notes = f"Nueva comunicación creada: {communication.type.value} - {communication.subject}"
        if communication.parent_communication_id:
            notes = f"Respuesta creada para la comunicación ID {communication.parent_communication_id}"
        audit_manager.log_action(db=db, action="CREATE", entity=communication, user=current_user, request=request, notes=notes)
        db.commit()
    except Exception as e:
        print(f"Warning: Audit trail failed: {e}")
    
    return CommunicationReadSchema.from_orm(communication)

@router.get("/my-communications", response_model=List[CommunicationReadSchema])
def get_my_communications(
    status_filter: Optional[CommunicationStatus] = Query(None),
    type_filter: Optional[CommunicationType] = Query(None),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Communication).options(
        joinedload(Communication.machine),
        joinedload(Communication.assigned_to)
    ).filter(Communication.created_by_id == current_user.id, Communication.parent_communication_id.is_(None))
    
    if status_filter: query = query.filter(Communication.status == status_filter)
    if type_filter: query = query.filter(Communication.type == type_filter)
    
    communications = query.order_by(desc(Communication.created_at)).limit(limit).all()
    
    return [CommunicationReadSchema.from_orm(comm) for comm in communications]

@router.get("/admin/all", response_model=List[CommunicationAdminReadSchema])
def get_all_communications_admin(
    status_filter: Optional[CommunicationStatus] = Query(None),
    type_filter: Optional[CommunicationType] = Query(None),
    priority_filter: Optional[str] = Query(None),
    pending_only: bool = Query(False),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    query = db.query(Communication).options(
        joinedload(Communication.created_by),
        joinedload(Communication.assigned_to),
        joinedload(Communication.machine),
        joinedload(Communication.target_role),
        joinedload(Communication.replies).options(
            joinedload(Communication.created_by)
        )
    ).filter(Communication.parent_communication_id.is_(None))
    
    if pending_only: query = query.filter(Communication.status == CommunicationStatus.PENDING)
    elif status_filter: query = query.filter(Communication.status == status_filter)
    if type_filter: query = query.filter(Communication.type == type_filter)
    if priority_filter: query = query.filter(Communication.priority == priority_filter)
    
    communications = query.order_by(
        desc(Communication.priority == "Urgente"),
        desc(Communication.priority == "Alta"),
        desc(Communication.created_at)
    ).offset(offset).limit(limit).all()
    
    return [CommunicationAdminReadSchema.from_orm(comm) for comm in communications]


@router.put("/{communication_id}", response_model=CommunicationAdminReadSchema)
def update_communication(
    communication_id: int,
    update_data: CommunicationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    communication = db.query(Communication).filter(Communication.id == communication_id).first()
    if not communication:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comunicación no encontrada")
    
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        if hasattr(communication, key):
            setattr(communication, key, value)
    
    if 'status' in update_dict:
        communication.updated_at = datetime.now(timezone.utc)
        if update_dict['status'] == CommunicationStatus.REVIEWED and not communication.reviewed_at:
            communication.reviewed_at = datetime.now(timezone.utc)
        elif update_dict['status'] == CommunicationStatus.RESOLVED and not communication.resolved_at:
            communication.resolved_at = datetime.now(timezone.utc)
            
    db.commit()
    db.refresh(communication)
    
    try:
        audit_manager.log_action(db=db, action="UPDATE", entity=communication, user=current_user, request=request,
                                 notes=f"Comunicación actualizada: {communication.subject}")
        db.commit()
    except Exception as e:
        print(f"Warning: Audit trail failed: {e}")
    
    return CommunicationAdminReadSchema.from_orm(communication)


@router.get("/admin/stats", response_model=CommunicationStatsResponse)
def get_communication_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    total_count = db.query(func.count(Communication.id)).filter(Communication.created_at >= start_date).scalar() or 0
    pending_count = db.query(func.count(Communication.id)).filter(Communication.status == CommunicationStatus.PENDING, Communication.created_at >= start_date).scalar() or 0
    in_progress_count = db.query(func.count(Communication.id)).filter(Communication.status == CommunicationStatus.IN_PROGRESS, Communication.created_at >= start_date).scalar() or 0
    resolved_count = db.query(func.count(Communication.id)).filter(Communication.status == CommunicationStatus.RESOLVED, Communication.created_at >= start_date).scalar() or 0
    
    by_type = {comm_type.value: db.query(func.count(Communication.id)).filter(Communication.type == comm_type, Communication.created_at >= start_date).scalar() or 0 for comm_type in CommunicationType}
    by_priority = {priority: db.query(func.count(Communication.id)).filter(Communication.priority == priority, Communication.created_at >= start_date).scalar() or 0 for priority in ["Baja", "Normal", "Alta", "Urgente"]}
    
    resolved_comms = db.query(Communication.resolved_at, Communication.created_at).filter(
        Communication.status == CommunicationStatus.RESOLVED,
        Communication.created_at >= start_date,
        Communication.resolved_at.isnot(None)
    ).all()
    
    avg_resolution_time = 0.0
    if resolved_comms:
        total_seconds = sum((comm.resolved_at - comm.created_at).total_seconds() for comm in resolved_comms)
        avg_resolution_time = (total_seconds / len(resolved_comms)) / (24 * 3600)

    oldest_pending = db.query(Communication.created_at).filter(Communication.status == CommunicationStatus.PENDING).order_by(Communication.created_at.asc()).first()
    oldest_pending_days = (datetime.now(timezone.utc) - oldest_pending[0]).days if oldest_pending else 0
    
    return CommunicationStatsResponse(
        total_communications=total_count, pending_count=pending_count, in_progress_count=in_progress_count, resolved_count=resolved_count,
        by_type=by_type, by_priority=by_priority, avg_resolution_time_days=round(avg_resolution_time, 1), oldest_pending_days=oldest_pending_days
    )

@router.delete("/{communication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_communication(
    communication_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    communication = db.query(Communication).filter(Communication.id == communication_id).first()
    if not communication:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comunicación no encontrada")
    
    audit_notes = f"Comunicación eliminada: ID={communication.id}, Asunto='{communication.subject}'"
    db.delete(communication)
    
    try:
        # La auditoría debe registrarse antes del commit final de la eliminación
        audit_manager.log_action(db=db, action="DELETE", entity_type="Communication", entity_id=communication_id, user=current_user, request=request, notes=audit_notes)
    except Exception as e:
        print(f"Warning: Audit trail for DELETE failed: {e}")
        
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)