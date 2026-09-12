# Auto-generated router module
import json
import logging
import os
import shutil
from datetime import datetime, timedelta, date, time
from decimal import Decimal
from typing import List, Optional, Union, Literal, Any, Dict, Tuple

from fastapi import (
    APIRouter, HTTPException, Depends, File, UploadFile, Form,
    BackgroundTasks, Body, status, Query, Response, Request
)
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session, joinedload, contains_eager
from sqlalchemy import func, distinct, case, or_, text
from sqlalchemy.orm.attributes import flag_modified

from src.database import get_db, SessionLocal
from src.auth import (
    create_access_token,
    verify_password,
    get_current_user,
    get_admin_user,
    get_jefe_seccion_user,
    get_password_hash
)
from src.config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from src.schemas import *
from src.models.base import Base
from src.models.role import Role
from src.models.section import Section
from src.models.line import Line
from src.models.machine import Machine
from src.models.supplier import Supplier
from src.models.inventory import Inventory
from src.models.associations import MachinePartAssociation
from src.models.maintenance import Maintenance
from src.models.work_order import WorkOrder, FailureCode, CauseCode, RemedyCode
from src.models.warehouse import Warehouse
from src.models.user import User 
from src.models.document import Document
from src.models.supplier_product_price import SupplierProductPrice
from src.models.task_list import TaskList
from src.models.task_step import TaskStep
from src.models.shift_pattern import ShiftPattern
from src.models.shift_assignment import ShiftAssignment
from src.models.absence import Absence
from src.models.shift_override import ShiftOverride
from src.models.maintenance_backlog import MaintenanceBacklog, BacklogPriority, BacklogStatus
from src.models.document_attachment import DocumentAttachment
from src.models.alert import Alert
from src.models.audit_log import AuditLog
from src.models import absence_crud, shift_override_crud, vacation_request_crud
from src.models.format import Format
from src.models.vacation_request import VacationRequest
from src.models.checklist_progress import ChecklistProgress
from src.models.work_order_material import WorkOrderMaterial
from src.models.work_order_technician import WorkOrderTechnician
from src.models.maintenance_request import MaintenanceRequest
from src.middleware.audit_middleware import audit_manager
from src.gamification.points_engine import get_points_engine

from .helpers import (
    PROXY_URL,
    VACATION_MANAGER_ROLES, MANAGER_ROLES,
    INVENTORY_ACCESS_ROLES, FINANCIAL_ACCESS_ROLES,
    PRODUCT_EDIT_ROLES, RESTRICTED_WORKER_ROLES,
    CONSULTANT_ROLES, CALENDAR_ACCESS_ROLES,
    get_inventory_user, get_financial_user, get_product_editor,
    get_active_order_for_maintenance, get_all_orders_for_maintenance,
    can_generate_new_order, get_maintenance_statistics,
    get_current_shift_user, handle_checklist_integration,
    add_technician_to_order, get_order_technicians,
    generate_work_order_from_task_list
)

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Section lines 7193-8263 ---
# --- ENDPOINTS PATRONES DE TURNO ---

@router.post(
    "/shift-patterns",
    response_model=ShiftPatternRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo patrón de turno"
)
def create_shift_pattern(
    pattern_data: ShiftPatternCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # Requiere Admin
):
    """Crea un nuevo patrón de turnos."""
    existing = db.query(ShiftPattern).filter(ShiftPattern.name == pattern_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Ya existe un patrón con el nombre '{pattern_data.name}'")

    if not pattern_data.pattern_sequence:
         raise HTTPException(status_code=400, detail="La secuencia del patrón no puede estar vacía.")

    db_pattern = ShiftPattern(
        name=pattern_data.name,
        description=pattern_data.description,
        pattern_sequence=pattern_data.pattern_sequence
        # cycle_length_days se calcula automáticamente en __init__ del modelo
    )
    try:
        db.add(db_pattern)
        db.commit()
        db.refresh(db_pattern)
        logger.info(f"Patrón de turno '{db_pattern.name}' (ID: {db_pattern.id}) creado.")
        return db_pattern
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando ShiftPattern: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al crear patrón: {e}")


@router.get(
    "/shift-patterns",
    response_model=List[ShiftPatternReadBasic], # Devuelve lista básica
    summary="Obtener todos los patrones de turno"
)
def list_shift_patterns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Cualquier usuario logueado puede verlos
):
    """Lista la información básica de todos los patrones de turno."""
    patterns = db.query(ShiftPattern).order_by(ShiftPattern.name).all()
    return patterns


@router.get(
    "/shift-patterns/{pattern_id}",
    response_model=ShiftPatternRead, # Devuelve detalles completos
    summary="Obtener detalles de un patrón de turno específico"
)
def get_shift_pattern(
    pattern_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene los detalles de un patrón de turno por su ID."""
    pattern = db.query(ShiftPattern).filter(ShiftPattern.id == pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Patrón de turno no encontrado.")
    return pattern


@router.put(
    "/shift-patterns/{pattern_id}",
    response_model=ShiftPatternRead, # Devuelve el patrón actualizado completo
    summary="Actualizar un patrón de turno"
)
def update_shift_pattern(
    pattern_id: int,
    pattern_data: ShiftPatternUpdate, # Usa el modelo Update
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # Requiere Admin
):
    """Actualiza nombre, descripción o secuencia de un patrón existente."""
    db_pattern = db.query(ShiftPattern).filter(ShiftPattern.id == pattern_id).first()
    if not db_pattern:
        raise HTTPException(status_code=404, detail="Patrón de turno no encontrado.")

    update_data = pattern_data.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar.")

    # Validar nombre único si se cambia
    if 'name' in update_data and update_data['name'] != db_pattern.name:
        existing = db.query(ShiftPattern).filter(ShiftPattern.name == update_data['name']).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Ya existe un patrón con el nombre '{update_data['name']}'")

    # Actualizar campos y recalcular longitud si cambia la secuencia
    for key, value in update_data.items():
        setattr(db_pattern, key, value)
        if key == 'pattern_sequence':
            if not value: # Validar que no sea vacía
                 raise HTTPException(status_code=400, detail="La secuencia del patrón no puede quedar vacía.")
            db_pattern.cycle_length_days = len(value) # Recalcular longitud

    try:
        db.commit()
        db.refresh(db_pattern)
        logger.info(f"Patrón de turno ID {pattern_id} actualizado.")
        return db_pattern
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando ShiftPattern {pattern_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al actualizar patrón: {e}")


@router.delete(
    "/shift-patterns/{pattern_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un patrón de turno"
)
def delete_shift_pattern(
    pattern_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # Requiere Admin
):
    """Elimina un patrón de turno si no está asignado a ningún usuario."""
    db_pattern = db.query(ShiftPattern).filter(ShiftPattern.id == pattern_id).first()
    if not db_pattern:
        raise HTTPException(status_code=404, detail="Patrón de turno no encontrado.")

    # Comprobar si está en uso por alguna asignación
    assignment = db.query(ShiftAssignment).filter(ShiftAssignment.pattern_id == pattern_id).first()
    if assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # O 409 Conflict
            detail=f"No se puede eliminar: el patrón '{db_pattern.name}' está asignado al menos a un usuario."
        )

    try:
        db.delete(db_pattern)
        db.commit()
        logger.info(f"Patrón de turno ID {pattern_id} ('{db_pattern.name}') eliminado.")
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando ShiftPattern {pattern_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al eliminar patrón: {e}")

# --- FIN ENDPOINTS PATRONES DE TURNO ---

# 12. ASIGNACIONES DE TURNOS ...
# =============================

@router.post(
    "/shift-assignments",
    response_model=ShiftAssignmentRead,
    status_code=status.HTTP_201_CREATED, # O 200 si actualiza
    summary="Crear o actualizar la asignación de turno para un usuario"
)
def create_or_update_assignment(
    assignment_data: ShiftAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # Solo Admin puede asignar turnos? Ajustar si es necesario
):
    """
    Crea una nueva asignación de turno para un usuario o actualiza la existente.
    Un usuario solo puede tener una asignación activa.
    """
    # Verificar que el usuario existe
    user = db.query(User).filter(User.id == assignment_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuario con ID {assignment_data.user_id} no encontrado.")

    # Verificar que el patrón existe
    pattern = db.query(ShiftPattern).filter(ShiftPattern.id == assignment_data.pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail=f"Patrón de turno con ID {assignment_data.pattern_id} no encontrado.")

    # Validar offset_days contra la longitud del ciclo del patrón
    if assignment_data.offset_days >= pattern.cycle_length_days:
        raise HTTPException(
            status_code=400,
            detail=f"El offset ({assignment_data.offset_days}) no puede ser mayor o igual a la longitud del ciclo ({pattern.cycle_length_days}). Debe ser de 0 a {pattern.cycle_length_days - 1}."
        )

    # Buscar si ya existe una asignación para este usuario
    db_assignment = db.query(ShiftAssignment).filter(ShiftAssignment.user_id == assignment_data.user_id).first()

    if db_assignment:
        # Actualizar asignación existente
        logger.info(f"Actualizando asignación existente para usuario ID {assignment_data.user_id}")
        db_assignment.pattern_id = assignment_data.pattern_id
        db_assignment.reference_date = assignment_data.reference_date
        db_assignment.offset_days = assignment_data.offset_days
        http_status_code = status.HTTP_200_OK
    else:
        # Crear nueva asignación
        logger.info(f"Creando nueva asignación para usuario ID {assignment_data.user_id}")
        db_assignment = ShiftAssignment(**assignment_data.dict())
        db.add(db_assignment)
        http_status_code = status.HTTP_201_CREATED

    try:
        db.commit()
        # --- COMENTAR O ELIMINAR LAS SIGUIENTES LÍNEAS ---
        # db.refresh(db_assignment)
        # # Cargar relaciones para la respuesta
        # db.refresh(db_assignment, attribute_names=['user', 'pattern'])
        # ----------------------------------------------
        logger.info(f"Asignación para usuario {assignment_data.user_id} guardada/actualizada.")
        # Devolver directamente el objeto db_assignment. FastAPI/Pydantic deberían poder serializarlo.
        return db_assignment
    except Exception as e:
        db.rollback()
        logger.error(f"Error al guardar asignación de turno para usuario {assignment_data.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al guardar asignación: {e}")


@router.get(
    "/shift-assignments",
    response_model=List[ShiftAssignmentRead],
    summary="Obtener todas las asignaciones de turno"
)
def list_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # Solo Admin/Jefe Mant.?
):
    """Devuelve una lista de todas las asignaciones de turno de usuarios."""
    assignments = db.query(ShiftAssignment).options(
        joinedload(ShiftAssignment.user), # Cargar usuario
        joinedload(ShiftAssignment.pattern) # Cargar patrón
    ).all()
    return assignments


@router.get(
    "/users/{user_id}/shift-assignment",
    response_model=ShiftAssignmentRead,
    summary="Obtener la asignación de turno de un usuario específico"
)
def get_user_assignment(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Permitir verse a sí mismo o Admin/Jefe ver otros?
):
    """Obtiene la asignación de turno para un usuario dado su ID."""
    # Lógica de Permiso Ejemplo: Admin/Jefe puede ver cualquiera, usuario normal solo a sí mismo
    can_view = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"] or current_user.id == user_id
    if not can_view:
         raise HTTPException(status_code=403, detail="No tienes permiso para ver esta asignación.")

    assignment = db.query(ShiftAssignment).options(
        joinedload(ShiftAssignment.user),
        joinedload(ShiftAssignment.pattern)
    ).filter(ShiftAssignment.user_id == user_id).first()

    if not assignment:
        raise HTTPException(status_code=404, detail=f"No se encontró asignación de turno para el usuario ID {user_id}.")
    return assignment


@router.delete(
    "/shift-assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una asignación de turno"
)
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # Solo Admin/Jefe Mant.?
):
    """Elimina una asignación de turno existente."""
    db_assignment = db.query(ShiftAssignment).filter(ShiftAssignment.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Asignación de turno no encontrada.")

    try:
        user_id_deleted = db_assignment.user_id # Guardar para log
        db.delete(db_assignment)
        db.commit()
        logger.info(f"Eliminada asignación de turno ID {assignment_id} para usuario ID {user_id_deleted}.")
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando ShiftAssignment {assignment_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al eliminar asignación: {e}")
    

@router.delete("/shift-assignments/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_shift_assignment(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # Solo administradores
):
    """Elimina la asignación de turno de un usuario específico."""
    # Verificar que el usuario existe
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado"
        )
    
    # Buscar la asignación de turno del usuario
    assignment = db.query(ShiftAssignment).filter(ShiftAssignment.user_id == user_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró asignación de turno para el usuario {user_id}"
        )
    
    try:
        # Eliminar la asignación
        db.delete(assignment)
        db.commit()
        logger.info(f"Asignación de turno eliminada para usuario ID {user_id}")
        return None  # No devuelve cuerpo para 204 NO CONTENT
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar asignación de turno para usuario {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al eliminar asignación de turno: {str(e)}"
        )


# --- FIN ENDPOINTS ASIGNACIONES DE TURNO ---

# ---  ENDPOINTS ASIGNACIONES DE AUSENCIAS---


ALLOWED_ROLES_MANAGE_ABSENCES = ["Administrador", "Jefe de Mantenimiento", "Jefe de Sección"]

@router.post("/absences", response_model=AbsenceRead, status_code=status.HTTP_201_CREATED)
def create_absence_route(absence_data: AbsenceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): # Usa : User
    # ... (Tu lógica original) ...
    user_to_register = db.query(User).filter(User.id == absence_data.user_id).first()
    if not user_to_register: raise HTTPException(status_code=404, detail=f"Usuario ID {absence_data.user_id} no encontrado.")
    is_manager = hasattr(current_user, 'role') and current_user.role and current_user.role.nombre in ALLOWED_ROLES_MANAGE_ABSENCES
    is_own_absence = current_user.id == absence_data.user_id
    if not (is_manager or is_own_absence): raise HTTPException(status_code=403, detail="Permiso denegado.")
    try:
        try: db_absence_sqla = Absence(**absence_data.model_dump()) # Pydantic V2+
        except AttributeError: db_absence_sqla = Absence(**absence_data.dict()) # Pydantic V1
        # Llama a CRUD create si lo tienes, o hazlo aquí
        db.add(db_absence_sqla); db.commit(); db.refresh(db_absence_sqla)
        logger.info(f"Ausencia registrada ID {db_absence_sqla.id}...")
        return db_absence_sqla
    except HTTPException as http_exc: raise http_exc
    except Exception as e: db.rollback(); logger.error(f"Error registrando ausencia: {e}", exc_info=True); raise HTTPException(status_code=500, detail="Error interno.")


@router.get("/absences", response_model=List[AbsenceRead])
def list_absences_route(user_id: Optional[int] = Query(None), start_date: Optional[date] = Query(None), end_date: Optional[date] = Query(None), absence_type: Optional[Literal['V', 'B', 'A', 'F']] = Query(None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): # Usa : User
    # ... (Tu lógica original) ...
    query = db.query(Absence)
    is_manager = hasattr(current_user, 'role') and current_user.role and current_user.role.nombre in ALLOWED_ROLES_MANAGE_ABSENCES
    if not is_manager:
        if user_id is not None and user_id != current_user.id: raise HTTPException(status_code=403, detail="Permiso denegado.")
        query = query.filter(Absence.user_id == current_user.id)
    elif user_id is not None: query = query.filter(Absence.user_id == user_id)
    if start_date: query = query.filter(Absence.end_date >= start_date)
    if end_date: query = query.filter(Absence.start_date <= end_date)
    if absence_type:
         if absence_type not in ['V', 'B', 'A', 'F']: raise HTTPException(status_code=400, detail="Tipo inválido.")
         query = query.filter(Absence.absence_type == absence_type)
    absences = query.order_by(Absence.start_date.desc(), Absence.user_id).all()
    return absences


@router.put("/absences/{absence_id}", response_model=AbsenceRead)
async def update_existing_absence_route(absence_id: int, absence_data: AbsenceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): # Usa : User
    if not hasattr(current_user, 'role') or not current_user.role or current_user.role.nombre not in ALLOWED_ROLES_MANAGE_ABSENCES: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permiso denegado.")
    existing_absence = absence_crud.get_absence_by_id(db, absence_id)
    if not existing_absence: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ausencia no encontrada")
    try:
        updated_absence = absence_crud.update_absence(db=db, absence_id=absence_id, absence_data=absence_data)
        if updated_absence is None: raise HTTPException(status_code=404, detail="Error al actualizar")
        return updated_absence
    except HTTPException as http_exc: raise http_exc
    except Exception as e: logger.error(f"Error actualizando Absence {absence_id}: {e}", exc_info=True); raise HTTPException(status_code=500, detail="Error interno.")


@router.delete("/absences/{absence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_absence(absence_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)): # Usa : User, tu nombre original
    # ... (Tu lógica original) ...
    db_absence = db.query(Absence).filter(Absence.id == absence_id).first()
    if not db_absence: raise HTTPException(status_code=404, detail="Ausencia no encontrada.")
    can_delete = hasattr(current_user, 'role') and current_user.role and current_user.role.nombre in ALLOWED_ROLES_MANAGE_ABSENCES # Simplificado
    if not can_delete: raise HTTPException(status_code=403, detail="Permiso denegado.")
    try:
        user_id_deleted = db_absence.user_id; type_deleted = db_absence.absence_type
        db.delete(db_absence); db.commit()
        logger.info(f"Eliminada ausencia ID {absence_id} (Tipo: {type_deleted}) por usuario ID {current_user.id}.")
        return None
    except Exception as e: db.rollback(); logger.error(f"Error eliminando Absence {absence_id}: {e}", exc_info=True); raise HTTPException(status_code=500, detail=f"Error interno: {e}")

# --- FIN ENDPOINTS AUSENCIAS ---


# --- ENDPOINTS NUEVOS PARA SHIFT OVERRIDES (SIN TAGS, Usa : User) ---
@router.post("/shift-overrides", response_model=ShiftOverrideRead, status_code=status.HTTP_201_CREATED)
def create_new_shift_override(
    override_data: ShiftOverrideCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registra o actualiza cobertura/cambio turno con código directo."""
    # Verificar permisos
    ALLOWED_ROLES_MANAGE_ABSENCES = ["Administrador", "Jefe de Mantenimiento", "Jefe de Sección"]
    
    if not hasattr(current_user, 'role') or not current_user.role or current_user.role.nombre not in ALLOWED_ROLES_MANAGE_ABSENCES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Permiso denegado para registrar cambios de turno."
        )
    
    # Verificar usuario
    user_exists = db.query(User).filter(User.id == override_data.user_id, User.active == True).first()
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Usuario ID {override_data.user_id} no encontrado o inactivo."
        )
    
    try:
        # Verificar si ya existe un override para este usuario y fecha
        existing = db.query(ShiftOverride).filter(
            ShiftOverride.user_id == override_data.user_id,
            ShiftOverride.date == override_data.date
        ).first()
        
        # Verificar código de turno
        valid_shift_codes = ['M', 'T', 'N']
        if override_data.actual_shift_code not in valid_shift_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Código de turno '{override_data.actual_shift_code}' no válido. Debe ser uno de: {', '.join(valid_shift_codes)}"
            )
        
        # Crear o actualizar el override
        if existing:
            # ACTUALIZAR el override existente
            logger.info(f"Actualizando override existente ID {existing.id} para usuario {override_data.user_id} en fecha {override_data.date}")
            
            # Actualizar el código de turno
            existing.actual_shift_code = override_data.actual_shift_code
            
            # Actualizar notas si se proporcionan
            if override_data.notes is not None:
                existing.notes = override_data.notes
                
            new_override = existing
        else:
            # Crear nuevo override
            try:
                # Intentar con model_dump() primero (Pydantic v2)
                dict_data = override_data.model_dump()
            except AttributeError:
                # Fallback a dict() (Pydantic v1)
                dict_data = override_data.dict()
            
            new_override = ShiftOverride(**dict_data)
            db.add(new_override)
        
        db.commit()
        db.refresh(new_override)
        
        # IMPORTANTE: Ya no intentamos cargar la relación user con attribute_names
        # En su lugar, obtenemos el override completo con una consulta que incluye joinedload
        result_override = db.query(ShiftOverride).options(
            joinedload(ShiftOverride.user)
        ).filter(ShiftOverride.id == new_override.id).first()
        
        if not result_override:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se pudo recuperar el override creado/actualizado"
            )
        
        logger.info(f"ShiftOverride ID {result_override.id} creado/actualizado para usuario {override_data.user_id}")
        return result_override
    
    except HTTPException as http_exc:
        logger.warning(f"HTTPException al crear/actualizar ShiftOverride: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado creando/actualizando ShiftOverride: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error interno al registrar/actualizar cambio: {str(e)}"
        )

@router.get("/shift-overrides", response_model=List[ShiftOverrideRead])
def list_shift_overrides(user_id: Optional[int] = Query(None), start_date: Optional[date] = Query(None), end_date: Optional[date] = Query(None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """ Lista overrides registrados. Restringido a Admin/Jefes. """
    # ... (Lógica de autorización y query usando shift_override_crud.get...) ...
    if not hasattr(current_user, 'role') or not current_user.role or current_user.role.nombre not in ALLOWED_ROLES_MANAGE_ABSENCES: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permiso denegado.")
    from src.models import shift_override_crud # Importar crud
    # Mover query a CRUD idealmente
    query = db.query(ShiftOverride).options(joinedload(ShiftOverride.user))
    if user_id: query = query.filter(ShiftOverride.user_id == user_id)
    if start_date: query = query.filter(ShiftOverride.date >= start_date)
    if end_date: query = query.filter(ShiftOverride.date <= end_date)
    overrides = query.order_by(ShiftOverride.date.desc(), ShiftOverride.user_id).all()
    return overrides


@router.delete("/shift-overrides/{override_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shift_override_endpoint(override_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """ Elimina un override por ID. Requiere rol Admin/Jefe. """
    # ... (Lógica de autorización y llamada a shift_override_crud.delete...) ...
    if not hasattr(current_user, 'role') or not current_user.role or current_user.role.nombre not in ALLOWED_ROLES_MANAGE_ABSENCES: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permiso denegado.")
    from src.models import shift_override_crud # Importar crud
    # Verificar existencia primero
    existing = shift_override_crud.get_override_by_id(db, override_id)
    if not existing: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Override no encontrado.")
    success = shift_override_crud.delete_shift_override(db=db, override_id=override_id)
    if not success: raise HTTPException(status_code=500, detail="Error al eliminar.")
    logger.info(f"Eliminado ShiftOverride ID {override_id} por usuario ID {current_user.id}.")
    return None


# --- FIN ENDPOINTS SHIFT OVERRIDES ---


# --- ENDPOINT CALENDARIO (MODIFICADO para usar shift_code de override y : User) ---
@router.get("/calendar-data", response_model=Dict[str, Dict[str, Any]])
def get_calendar_data(
    year: int = Query(..., description="Año"), 
    month: int = Query(..., ge=1, le=12, description="Mes"), 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    show_all_users: bool = Query(False, description="Mostrar todos los usuarios aunque no tengan asignación")
):
    logger.info(f"[Calendar Data] Solicitando para {year}-{month:02d}")
    try:
        start_date = date(year, month, 1)
        days_in_month = calendar.monthrange(year, month)[1]
        end_date = date(year, month, days_in_month)
        
        # Obtener usuarios activos
        users_query = db.query(User).options(
            joinedload(User.section), 
            joinedload(User.role)
        ).filter(User.active == True)
        
        users = users_query.all()
        all_user_ids = [u.id for u in users]
        
        if not all_user_ids:
            return {}
            
        # Obtener asignaciones de turno
        assignments = db.query(ShiftAssignment).options(
            joinedload(ShiftAssignment.user).load_only(User.id, User.username),
            joinedload(ShiftAssignment.pattern)
        ).filter(ShiftAssignment.user_id.in_(all_user_ids)).all()
        
        # MODIFICACIÓN: Filtrar solo usuarios con asignación o ausencias, o override
        # Identificar qué usuarios tienen asignación de turno
        users_with_assignment = {assign.user_id for assign in assignments if assign.user and assign.pattern}
        
        # Obtener ausencias para el periodo
        absences = absence_crud.get_absences_for_period_and_users(db, start_date, end_date, all_user_ids)
        
        # Identificar qué usuarios tienen ausencias
        users_with_absence = {ab.user_id for ab in absences}
        
        # Obtener overrides para el periodo
        from src.models import shift_override_crud
        overrides = db.query(ShiftOverride).filter(
            ShiftOverride.user_id.in_(all_user_ids),
            ShiftOverride.date >= start_date,
            ShiftOverride.date <= end_date
        ).all()
        
        # Identificar qué usuarios tienen overrides
        users_with_override = {ov.user_id for ov in overrides}
        
        # Combinar todos los usuarios que deben mostrarse
        users_to_show = users_with_assignment.union(users_with_absence).union(users_with_override)
        
        # Si se solicita, mostrar todos los usuarios
        if show_all_users:
            users_to_show = set(all_user_ids)
        
        # Filtrar users_to_fetch para incluir solo los que tienen asignación, ausencia u override
        user_ids_to_fetch = list(users_to_show)
        
        if not user_ids_to_fetch:
            return {}
        
        # Mapeo de ausencias
        absence_lookup: Dict[int, Dict[date, Dict]] = {}
        for ab in absences:
            current_d = ab.start_date
            while current_d <= ab.end_date:
                if ab.user_id not in absence_lookup:
                    absence_lookup[ab.user_id] = {}
                absence_details = {
                    "type": "absence",
                    "id": ab.id,
                    "absence_type": ab.absence_type,
                    "notes": ab.notes,
                    "start_date": ab.start_date.isoformat(),
                    "end_date": ab.end_date.isoformat(),
                    "user_id": ab.user_id
                }
                absence_lookup[ab.user_id][current_d] = absence_details
                current_d += timedelta(days=1)
        
        # Mapeo de asignaciones
        assignment_lookup = {assign.user_id: assign for assign in assignments if assign.user and assign.pattern}
        
        # Mapeo de nombres de usuario (solo para los usuarios a mostrar)
        user_lookup = {user.id: user.username for user in users if user.id in user_ids_to_fetch}
        
        # Mapeo de overrides
        override_lookup: Dict[int, Dict[date, Dict]] = {}
        for ov in overrides:
            if ov.user_id not in override_lookup:
                override_lookup[ov.user_id] = {}
                
            override_details = {
                "type": "override",
                "id": ov.id,
                "code": ov.actual_shift_code,
                "notes": ov.notes,
                "date": ov.date.isoformat(),
                "user_id": ov.user_id
            }
            override_lookup[ov.user_id][ov.date] = override_details
        
        # Generar datos del calendario
        calendar_data: Dict[str, Dict[str, Any]] = {}
        current_day = start_date
        
        while current_day <= end_date:
            day_str = current_day.isoformat()
            calendar_data[day_str] = {}
            
            for user_id in user_ids_to_fetch:
                username = user_lookup.get(user_id, f"User_{user_id}")
                
                # ORDEN CORRECTO DE PRIORIDAD: Override > Ausencia > Patrón
                user_overrides = override_lookup.get(user_id, {})
                if current_day in user_overrides:
                    calendar_data[day_str][username] = user_overrides[current_day]
                    continue
                
                user_absences = absence_lookup.get(user_id, {})
                if current_day in user_absences:
                    calendar_data[day_str][username] = user_absences[current_day]
                    continue
                
                # Si no hay override ni ausencia, usar el patrón
                assign = assignment_lookup.get(user_id)
                if assign and assign.pattern and assign.pattern.pattern_sequence:
                    try:
                        ref_date_assign = assign.reference_date
                        days_difference = (current_day - ref_date_assign).days
                        total_offset_days = days_difference + assign.offset_days
                        cycle_len = assign.pattern.cycle_length_days
                        
                        if cycle_len <= 0:
                            raise ValueError("Cycle length must be positive")
                            
                        day_index = (total_offset_days % cycle_len + cycle_len) % cycle_len
                        shift_code = assign.pattern.pattern_sequence[day_index]
                        
                        calendar_data[day_str][username] = {
                            "type": "shift",
                            "code": shift_code,
                            "pattern_name": assign.pattern.name
                        }
                    except Exception as e_calc:
                        logger.error(f"Error cálculo turno user {user_id}: {e_calc}", exc_info=True)
                        continue  # CAMBIO: Ignorar usuario si hay error en vez de mostrar tipo "error"
                # CAMBIO: Ya no incluimos usuarios sin asignación (quitado el código que mostraba "type": "no_assignment")
            
            current_day += timedelta(days=1)
        
        logger.info(f"[Calendar Data] Datos generados para {year}-{month:02d}")
        return calendar_data
        
    except Exception as e:
        logger.error(f"[Calendar Data] Error general: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno al generar datos del calendario"
        )
# --- FIN ENDPOINT CALENDARIO ---

# --- ENDPOINTS NUEVOS PARA SOLICITUDES DE VACACIONES ---

@router.post("/vacation-requests", response_model=VacationRequestRead, status_code=status.HTTP_201_CREATED, tags=["Vacation Requests"])
def request_vacation(
    request_data: VacationRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea una nueva solicitud de vacaciones para un usuario."""
    # Validar que el user_id de la solicitud existe
    user_exists = db.query(User).filter(User.id == request_data.user_id).first()
    if not user_exists: raise HTTPException(status_code=404, detail=f"Usuario ID {request_data.user_id} no encontrado.")

    # Permisos: ¿Puede un admin solicitar por otro? ¿O solo el propio usuario?
    is_manager = hasattr(current_user, 'role') and current_user.role and current_user.role.nombre in VACATION_MANAGER_ROLES
    is_own_request = current_user.id == request_data.user_id

    if not (is_manager or is_own_request):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes crear solicitudes para otros usuarios.")

    try:
        # Asegúrate de importar vacation_request_crud
        from src.models import vacation_request_crud
        new_request = vacation_request_crud.create_request(db=db, request_data=request_data)
        return new_request
    except Exception as e:
        logger.error(f"Error creando VacationRequest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al crear solicitud.")

@router.get("/vacation-requests", response_model=List[VacationRequestRead], tags=["Vacation Requests"])
def list_vacation_requests(
    user_id: Optional[int] = Query(None, description="Filtrar por ID de usuario"),
    status: Optional[Literal['Solicitado', 'Aprobado', 'Rechazado']] = Query(None, description="Filtrar por estado"),
    start_date: Optional[date] = Query(None, description="Fecha inicio del rango"),
    end_date: Optional[date] = Query(None, description="Fecha fin del rango"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista solicitudes de vacaciones. Managers ven todas (o filtradas), usuarios normales solo las suyas."""
    is_manager = hasattr(current_user, 'role') and current_user.role and current_user.role.nombre in VACATION_MANAGER_ROLES
    effective_user_id = user_id
    if not is_manager:
        if user_id is not None and user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes ver solicitudes de otros usuarios.")
        effective_user_id = current_user.id # Forzar ver solo las propias

    try:
        # Asegúrate de importar vacation_request_crud
        from src.models import vacation_request_crud
        requests = vacation_request_crud.get_requests(
            db=db,
            user_id=effective_user_id,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
        return requests
    except Exception as e:
        logger.error(f"Error listando VacationRequests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al listar solicitudes.")


@router.put("/vacation-requests/{request_id}/status", response_model=VacationRequestRead, tags=["Vacation Requests"])
def update_vacation_request_status(
    request_id: int,
    status_update: VacationRequestUpdate, # Schema con {status: 'Aprobado'|'Rechazado', notes: ...}
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Quien aprueba/rechaza
):
    """Aprueba o rechaza una solicitud de vacaciones. Requiere rol de Manager."""
    is_manager = hasattr(current_user, 'role') and current_user.role and current_user.role.nombre in VACATION_MANAGER_ROLES
    if not is_manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para aprobar/rechazar solicitudes.")

    try:
        # Asegúrate de importar vacation_request_crud
        from src.models import vacation_request_crud
        updated_request = vacation_request_crud.update_request_status(
            db=db,
            request_id=request_id,
            status_update=status_update,
            reviewer_id=current_user.id
        )
        if not updated_request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")
        return updated_request
    except HTTPException as http_exc: # Capturar 400 si no está pendiente o 500 si falla crear ausencia
        raise http_exc
    except Exception as e:
        logger.error(f"Error actualizando estado de VacationRequest {request_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al actualizar estado.")

@router.delete("/vacation-requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Vacation Requests"])
def delete_vacation_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina una solicitud de vacaciones PENDIENTE. Puede hacerlo el solicitante o un manager."""
    is_manager = hasattr(current_user, 'role') and current_user.role and current_user.role.nombre in VACATION_MANAGER_ROLES
    try:
        # Asegúrate de importar vacation_request_crud
        from src.models import vacation_request_crud
        success = vacation_request_crud.delete_request(
            db=db,
            request_id=request_id,
            requesting_user_id=current_user.id,
            is_manager=is_manager
        )
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.") # O fallo de permiso desde CRUD
        return None
    except HTTPException as http_exc: # Capturar 403 o 400 del CRUD
        raise http_exc
    except Exception as e:
        logger.error(f"Error eliminando VacationRequest {request_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al eliminar solicitud.")

@router.get("/vacation-requests/inactive-users", tags=["Vacation Requests"])
def get_vacation_requests_from_inactive_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Solo administradores
):
    """Obtiene solicitudes de vacaciones de usuarios inactivos para limpieza."""
    try:
        # Buscar solicitudes de usuarios inactivos
        inactive_user_requests = db.query(VacationRequest).join(User).filter(
            User.active == False,
            VacationRequest.status == 'Solicitado'  # Solo pendientes
        ).all()
        
        result = []
        for request in inactive_user_requests:
            result.append({
                "id": request.id,
                "user_id": request.user_id,
                "username": request.user.username,
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
                "status": request.status,
                "created_at": request.created_at.isoformat(),
                "user_active": request.user.active
            })
        
        return {
            "inactive_user_requests": result,
            "count": len(result)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo solicitudes de usuarios inactivos: {e}")
        raise HTTPException(status_code=500, detail="Error interno")

# 4. Endpoint para limpiar solicitudes de usuarios inactivos
@router.delete("/vacation-requests/cleanup-inactive-users", tags=["Vacation Requests"])
def cleanup_vacation_requests_from_inactive_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Elimina todas las solicitudes pendientes de usuarios inactivos."""
    try:
        # Buscar y eliminar solicitudes de usuarios inactivos
        deleted_count = db.query(VacationRequest).join(User).filter(
            User.active == False,
            VacationRequest.status == 'Solicitado'
        ).delete(synchronize_session=False)
        
        db.commit()
        
        # Log de auditoría
        audit_manager.log_action(
            db=db,
            action="DELETE",
            entity=None,  # No hay entidad específica
            user=current_user,
            request=None,
            notes=f"Limpieza masiva: {deleted_count} solicitudes de vacaciones de usuarios inactivos eliminadas"
        )
        db.commit()
        
        return {
            "success": True,
            "message": f"Se eliminaron {deleted_count} solicitudes de usuarios inactivos",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error en limpieza de solicitudes: {e}")
        raise HTTPException(status_code=500, detail="Error interno en limpieza")
    

@router.get("/vacation-requests/all-pending", tags=["Vacation Requests"])
def get_all_pending_vacation_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene TODAS las solicitudes de vacaciones pendientes, independientemente del mes."""
    try:
        # Determinar si es manager para filtrar permisos si es necesario
        is_manager = hasattr(current_user, 'role') and current_user.role and current_user.role.nombre in VACATION_MANAGER_ROLES        
        # Base query para solicitudes pendientes
        query = db.query(VacationRequest).join(User, VacationRequest.user_id == User.id).filter(
            VacationRequest.status == 'Solicitado',
            User.active == True  # Solo usuarios activos
        )
        
        # Si no es manager, solo ver sus propias solicitudes
        if not is_manager:
            query = query.filter(VacationRequest.user_id == current_user.id)
        
        # Obtener todas las solicitudes pendientes
        pending_requests = query.all()
        
        result = []
        for request in pending_requests:
            result.append({
                "id": request.id,
                "user_id": request.user_id,
                "username": request.user.username,  # Nombre real del usuario
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
                "status": request.status,
                "notes": request.notes,
                "created_at": request.created_at.isoformat(),
                "type": "vacation_request"  # Para compatibilidad con frontend
            })
        
        logger.info(f"Encontradas {len(result)} solicitudes pendientes globales para usuario {current_user.username}")
        
        return {
            "pending_requests": result,
            "count": len(result)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo solicitudes pendientes globales: {e}")
        raise HTTPException(status_code=500, detail="Error interno al obtener solicitudes pendientes")


# --- NUEVO ENDPOINT PARA CALENDARIO DE VACACIONES ---
@router.post("/vacation-requests", response_model=VacationRequestRead, status_code=status.HTTP_201_CREATED, tags=["Vacation Requests"])
def request_vacation(
    request_data: VacationRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea una nueva solicitud de vacaciones."""
    # Valida que el usuario existe
    user_exists = db.query(User).filter(User.id == request_data.user_id).first()
    if not user_exists: raise HTTPException(status_code=404, detail=f"Usuario ID {request_data.user_id} no encontrado.")
    # Valida permisos
    is_manager = hasattr(current_user, 'role') and current_user.role and current_user.role.nombre in VACATION_MANAGER_ROLES
    is_own_request = current_user.id == request_data.user_id
    if not (is_manager or is_own_request): raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes crear solicitudes para otros.")
    try:
        # Llama al CRUD (asegúrate que vacation_request_crud está importado arriba)
        new_request = vacation_request_crud.create_request(db=db, request_data=request_data)
        return new_request
    except HTTPException as http_exc: raise http_exc
    except Exception as e: logger.error(f"Error creando VacationRequest: {e}", exc_info=True); raise HTTPException(status_code=500, detail="Error interno.")

@router.get("/vacation-requests", response_model=List[VacationRequestRead], tags=["Vacation Requests"])
def list_vacation_requests(
    user_id: Optional[int] = Query(None), status: Optional[Literal['Solicitado', 'Aprobado', 'Rechazado']] = Query(None),
    start_date: Optional[date] = Query(None), end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Lista solicitudes de vacaciones. Managers ven todas, usuarios normales solo las suyas."""
    is_manager = hasattr(current_user, 'role') and current_user.role and current_user.role.nombre in VACATION_MANAGER_ROLES
    effective_user_id = user_id
    if not is_manager:
        if user_id is not None and user_id != current_user.id: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes ver solicitudes de otros.")
        effective_user_id = current_user.id
    try:
        # Llama al CRUD (asegúrate que vacation_request_crud está importado arriba)
        requests = vacation_request_crud.get_requests(db=db, user_id=effective_user_id, status=status, start_date=start_date, end_date=end_date)
        return requests
    except Exception as e: logger.error(f"Error listando VacationRequests: {e}", exc_info=True); raise HTTPException(status_code=500, detail="Error interno.")

@router.put("/vacation-requests/{request_id}/status", response_model=VacationRequestRead, tags=["Vacation Requests"])
def update_vacation_request_status(
    request_id: int, status_update: VacationRequestUpdate, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aprueba o rechaza una solicitud. Requiere rol de Manager."""
    is_manager = hasattr(current_user, 'role') and current_user.role and current_user.role.nombre in VACATION_MANAGER_ROLES
    if not is_manager: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permiso denegado.")
    try:
        # Llama al CRUD (asegúrate que vacation_request_crud está importado arriba)
        updated_request = vacation_request_crud.update_request_status(db=db, request_id=request_id, status_update=status_update, reviewer_id=current_user.id)
        if not updated_request: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")
        return updated_request
    except HTTPException as http_exc: raise http_exc
    except Exception as e: logger.error(f"Error actualizando estado VacReq {request_id}: {e}", exc_info=True); raise HTTPException(status_code=500, detail="Error interno.")

@router.delete("/vacation-requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Vacation Requests"])
def delete_vacation_request(request_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Elimina una solicitud PENDIENTE. Puede hacerlo el solicitante o un manager."""
    is_manager = hasattr(current_user, 'role') and current_user.role and current_user.role.nombre in VACATION_MANAGER_ROLES
    try:
        # Llama al CRUD (asegúrate que vacation_request_crud está importado arriba)
        success = vacation_request_crud.delete_request(db=db, request_id=request_id, requesting_user_id=current_user.id, is_manager=is_manager)
        if not success: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")
        return None
    except HTTPException as http_exc: raise http_exc
    except Exception as e: logger.error(f"Error eliminando VacReq {request_id}: {e}", exc_info=True); raise HTTPException(status_code=500, detail="Error interno.")

# --- NUEVO ENDPOINT PARA DATOS DEL CALENDARIO DE VACACIONES ---
@router.get("/vacation-requests/calendar", response_model=Dict[str, Dict[str, Any]], tags=["Vacation Requests", "Calendar"])
def get_vacation_calendar_data_only( # Nombre claro para indicar que solo devuelve solicitudes
    year: int = Query(..., description="Año"), month: int = Query(..., ge=1, le=12, description="Mes"),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Devuelve SOLAMENTE datos de SOLICITUDES de vacaciones para visualización."""
    logger.info(f"[Vacation Calendar ONLY] Solicitando para {year}-{month:02d}")
    try:
        start_date = date(year, month, 1); days_in_month = calendar.monthrange(year, month)[1]; end_date = date(year, month, days_in_month)
        # Obtener usuarios para lookup (¿filtrar por permisos?)
        users = db.query(User).filter(User.active == True).all()
        user_lookup = {user.id: user.username for user in users}
        # Obtener solicitudes relevantes (usando CRUD)
        # Llama al CRUD (asegúrate que vacation_request_crud está importado arriba)
        requests = vacation_request_crud.get_requests(db=db, start_date=start_date, end_date=end_date) # Trae todas las que solapan
        # Filtrar por permisos si es necesario (ej. usuario normal solo ve las suyas)
        is_manager = hasattr(current_user, 'role') and current_user.role and current_user.role.nombre in VACATION_MANAGER_ROLES
        if not is_manager:
            requests = [req for req in requests if req.user_id == current_user.id]

        # Procesar para formato de calendario
        calendar_data: Dict[str, Dict[str, Any]] = {}
        current_day_iter = start_date
        while current_day_iter <= end_date: day_str = current_day_iter.isoformat(); calendar_data[day_str] = {}; current_day_iter += timedelta(days=1)

        for req in requests:
            username = user_lookup.get(req.user_id, f"User_{req.user_id}")
            current_d = req.start_date
            while current_d <= req.end_date:
                if start_date <= current_d <= end_date:
                    day_str = current_d.isoformat()
                    # Validar con schema Pydantic antes de añadir
                    try:
                        event_data = VacationCalendarEvent(
                             id=req.id, status=req.status, user_id=req.user_id,
                             start_date=req.start_date, end_date=req.end_date,
                             notes=req.notes, manager_notes=req.manager_notes,
                             username=username
                         ).dict() # Pydantic V1
                    except AttributeError:
                         event_data = VacationCalendarEvent( # Pydantic V2 fallback
                             id=req.id, status=req.status, user_id=req.user_id,
                             start_date=req.start_date, end_date=req.end_date,
                             notes=req.notes, manager_notes=req.manager_notes,
                             username=username
                         ).model_dump()
                    # Usar lista para permitir múltiples eventos por día/usuario
                    if username not in calendar_data[day_str]: calendar_data[day_str][username] = []
                    calendar_data[day_str][username].append(event_data)
                if req.start_date > req.end_date: break
                current_d += timedelta(days=1)

        # Convertir listas de un solo elemento en objeto directo para mantener formato anterior
        final_calendar_data = {}
        for day, users in calendar_data.items():
            final_calendar_data[day] = {}
            for user, events in users.items():
                if events: final_calendar_data[day][user] = events[0] # Tomar solo el primero

        logger.info(f"[Vacation Calendar ONLY] Datos generados para {year}-{month:02d}")
        return final_calendar_data
    except Exception as e:
        logger.error(f"[Vacation Calendar ONLY] Error general: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al generar datos del calendario de vacaciones")

# --- FIN ENDPOINTS VACACIONES ---

