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


# --- Section lines 3363-3689 ---
# ---------------------------------
# ENDPOINTS PARA LISTAS DE TAREAS
# ---------------------------------

@router.post(
    "/task-lists",
    response_model=TaskListRead, # Devuelve la lista completa con pasos creados
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva Lista de Tareas Estándar (con sus pasos)"
)
def create_task_list(
    task_list_data: TaskListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # O un rol con permisos adecuados
):
    """
    Crea una nueva lista de tareas estándar, incluyendo los pasos iniciales.
    """
    # Verificar si ya existe una lista con el mismo nombre
    existing_list = db.query(TaskList).filter(TaskList.name == task_list_data.name).first()
    if existing_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una lista de tareas con el nombre '{task_list_data.name}'"
        )

    # Crear la lista principal
    db_task_list = TaskList(
        name=task_list_data.name,
        description=task_list_data.description,
        applies_to_type=task_list_data.applies_to_type
    )
    # Crear los pasos asociados
    if task_list_data.steps:
        for step_data in task_list_data.steps:
            db_step = TaskStep(
                step_order=step_data.step_order,
                description=step_data.description,
                estimated_time_minutes=step_data.estimated_time_minutes
                # La relación se establecerá al añadir a db_task_list.steps
            )
            db_task_list.steps.append(db_step) # Añadir paso a la lista

    try:
        db.add(db_task_list)
        db.commit()
        # --- COMENTAR O ELIMINAR LAS SIGUIENTES LÍNEAS ---
        # db.refresh(db_task_list)
        # db.refresh(db_task_list, attribute_names=['steps'])
        # ----------------------------------------------
        logger.info(f"Lista de Tareas '{db_task_list.name}' (ID: {db_task_list.id}) creada.")
        # Devolver directamente el objeto, Pydantic/FastAPI intentarán serializarlo
        return db_task_list
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear TaskList: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al crear la lista de tareas: {e}")



@router.get(
    "/task-lists",
    response_model=List[TaskListReadBasic], # Usar el modelo básico para la lista
    summary="Obtener todas las Listas de Tareas Estándar"
)
def list_task_lists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Permitir a usuarios logueados ver las listas
):
    """Devuelve una lista con la información básica de todas las listas de tareas."""
    lists = db.query(TaskList).order_by(TaskList.name).all()
    return lists



@router.put(
    "/task-lists/{list_id}",
    response_model=TaskListReadBasic, # Devolver solo la info básica actualizada
    summary="Actualizar información de una Lista de Tareas (sin pasos)"
)
def update_task_list(
    list_id: int,
    task_list_data: TaskListUpdate, # Modelo solo para campos de TaskList
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # Permiso admin
):
    """Actualiza el nombre, descripción o tipo de una lista de tareas."""
    db_task_list = db.query(TaskList).filter(TaskList.id == list_id).first()
    if not db_task_list:
        raise HTTPException(status_code=404, detail="Lista de tareas no encontrada.")

    update_data = task_list_data.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar.")

    # Verificar nombre único si se cambia
    if 'name' in update_data and update_data['name'] != db_task_list.name:
        existing_list = db.query(TaskList).filter(TaskList.name == update_data['name']).first()
        if existing_list:
             raise HTTPException(status_code=400, detail=f"Ya existe lista con nombre '{update_data['name']}'")

    for key, value in update_data.items():
        setattr(db_task_list, key, value)

    try:
        db.commit()
        db.refresh(db_task_list)
        logger.info(f"Lista de Tareas ID {list_id} actualizada.")
        return db_task_list
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando TaskList {list_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al actualizar lista: {e}")


@router.delete(
    "/task-lists/{list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una Lista de Tareas Estándar (y sus pasos)"
)
def delete_task_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # Permiso admin
):
    """Elimina una lista de tareas y todos sus pasos asociados."""
    db_task_list = db.query(TaskList).filter(TaskList.id == list_id).first()
    if not db_task_list:
        raise HTTPException(status_code=404, detail="Lista de tareas no encontrada.")

    # Opcional: Comprobar si la lista está en uso en algún Mantenimiento Preventivo
    # linked_maintenance = db.query(Maintenance).filter(Maintenance.task_list_id == list_id).first()
    # if linked_maintenance:
    #     raise HTTPException(status_code=400, detail="No se puede eliminar: la lista está asociada a un plan de mantenimiento preventivo.")

    try:
        db.delete(db_task_list) # El 'cascade' en el modelo debería borrar los TaskStep
        db.commit()
        logger.info(f"Lista de Tareas ID {list_id} eliminada.")
        return None # No devolver cuerpo para 204
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando TaskList {list_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al eliminar lista: {e}")
    


@router.post(
    "/task-lists/{list_id}/steps",
    response_model=TaskStepRead, # Devuelve el paso creado
    status_code=status.HTTP_201_CREATED,
    summary="Añadir un nuevo paso a una lista de tareas existente"
)
def create_task_step_for_list(
    list_id: int,
    step_data: TaskStepCreate, # Recibe datos del nuevo paso
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # O permiso adecuado
):
    """Crea un nuevo paso y lo asocia a una lista de tareas existente."""
    # Verificar que la lista de tareas existe
    db_task_list = db.query(TaskList).filter(TaskList.id == list_id).first()
    if not db_task_list:
        raise HTTPException(status_code=404, detail="Lista de tareas no encontrada.")

    # Crear el nuevo paso, asociándolo a la lista
    db_step = TaskStep(
        **step_data.dict(), # Pasa los datos validados (step_order, description, etc.)
        task_list_id=list_id # Asegura la asociación
    )

    try:
        db.add(db_step)
        db.commit()
        db.refresh(db_step)
        logger.info(f"Nuevo paso (ID: {db_step.id}) añadido a TaskList ID {list_id}")
        return db_step
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando TaskStep para TaskList {list_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al crear paso: {e}")


@router.put(
    "/task-lists/{list_id}/steps/{step_id}",
    response_model=TaskStepRead,
    summary="Actualizar un paso específico de una lista de tareas"
)
def update_task_step(
    list_id: int,
    step_id: int,
    step_data: TaskStepUpdate, # Modelo para actualizar pasos
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # O permiso adecuado
):
    """Actualiza la información de un paso de tarea existente."""
    # Buscar el paso específico asegurándose que pertenece a la lista correcta
    db_step = db.query(TaskStep).filter(
        TaskStep.id == step_id,
        TaskStep.task_list_id == list_id # Importante verificar pertenencia
    ).first()

    if not db_step:
        raise HTTPException(status_code=404, detail=f"Paso con ID {step_id} no encontrado en la lista ID {list_id}.")

    update_data = step_data.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar.")

    for key, value in update_data.items():
        setattr(db_step, key, value)

    try:
        db.commit()
        db.refresh(db_step)
        logger.info(f"Paso ID {step_id} (TaskList ID {list_id}) actualizado.")
        return db_step
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando TaskStep {step_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al actualizar paso: {e}")


@router.delete(
    "/task-lists/{list_id}/steps/{step_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un paso específico de una lista de tareas"
)
def delete_task_step(
    list_id: int,
    step_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # O permiso adecuado
):
    """Elimina un paso específico de una lista de tareas."""
    db_step = db.query(TaskStep).filter(
        TaskStep.id == step_id,
        TaskStep.task_list_id == list_id
    ).first()

    if not db_step:
        raise HTTPException(status_code=404, detail=f"Paso con ID {step_id} no encontrado en la lista ID {list_id}.")

    try:
        db.delete(db_step)
        db.commit()
        logger.info(f"Paso ID {step_id} (TaskList ID {list_id}) eliminado.")
        return None # No devolver cuerpo para 204
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando TaskStep {step_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al eliminar paso: {e}")


@router.get("/task-lists/for-maintenance", response_model=List[TaskListForMaintenanceRead])
def get_task_lists_for_maintenance(
    machine_type: Optional[str] = Query(None, description="Tipo de máquina para filtrar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene TaskLists disponibles para asignar a mantenimiento preventivo"""
    try:
        query = db.query(TaskList).order_by(TaskList.name)
        
        if machine_type:
            query = query.filter(
                or_(
                    TaskList.applies_to_type.is_(None),
                    TaskList.applies_to_type.ilike(f"%{machine_type}%")
                )
            )
        
        task_lists = query.all()
        
        result = []
        for tl in task_lists:
            steps_count = db.query(func.count(TaskStep.id)).filter(
                TaskStep.task_list_id == tl.id
            ).scalar() or 0
            
            total_time = db.query(func.sum(TaskStep.estimated_time_minutes)).filter(
                TaskStep.task_list_id == tl.id
            ).scalar() or 0
            
            result.append({
                "id": tl.id,
                "name": tl.name,
                "description": tl.description,
                "applies_to_type": tl.applies_to_type,
                "steps_count": steps_count,
                "total_estimated_minutes": int(total_time)
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo task lists: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
@router.get(
    "/task-lists/{list_id}",
    response_model=TaskListRead, # Usar el modelo completo con pasos
    summary="Obtener detalles de una Lista de Tareas (con sus pasos)"
)
def get_task_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Devuelve los detalles de una lista de tareas específica, incluyendo sus pasos ordenados."""
    # Usar joinedload para cargar los pasos eficientemente
    task_list = db.query(TaskList).options(
        joinedload(TaskList.steps)
    ).filter(TaskList.id == list_id).first()

    if not task_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lista de tareas con ID {list_id} no encontrada."
        )
    # Los pasos ya vienen ordenados por la definición de la relación
    return task_list


# --- FIN ENDPOINTS LISTAS DE TAREAS ---


