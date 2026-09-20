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


# --- Section lines 6077-7192 ---
# --- Failure Codes ---
@router.post("/failure-codes", response_model=CodeRead, status_code=201, summary="Crear Código de Falla")
def create_failure_code(
    code_data: CodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Crea un nuevo código de falla."""
    existing_code = db.query(FailureCode).filter(FailureCode.code == code_data.code).first()
    if existing_code:
        raise HTTPException(status_code=400, detail=f"El código de falla '{code_data.code}' ya existe.")
    db_code = FailureCode(**code_data.dict())
    try:
        db.add(db_code)
        db.commit()
        db.refresh(db_code)
        return db_code
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando código de falla: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al crear código de falla.")

@router.get("/failure-codes", response_model=List[CodeRead], summary="Listar Códigos de Falla")
def list_failure_codes(
    db: Session = Depends(get_db), 
    _user=Depends(get_current_user),
    active_only: bool = False
):
    """Lista todos los códigos de falla disponibles."""
    query = db.query(FailureCode).order_by(FailureCode.code)
    if active_only:
        query = query.filter(FailureCode.active == True)
    return query.all()

@router.put("/failure-codes/{code_id}", response_model=CodeRead, summary="Actualizar Código de Falla")
def update_failure_code(
    code_id: int,
    code_data: CodeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Actualiza un código de falla existente."""
    db_code = db.query(FailureCode).filter(FailureCode.id == code_id).first()
    if not db_code:
        raise HTTPException(status_code=404, detail="Código de falla no encontrado.")

    update_data = code_data.dict(exclude_unset=True)
    if not update_data:
         raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar.")

    if 'code' in update_data and update_data['code'] != db_code.code:
        existing_code = db.query(FailureCode).filter(FailureCode.code == update_data['code'], FailureCode.id != code_id).first()
        if existing_code:
            raise HTTPException(status_code=400, detail=f"El código de falla '{update_data['code']}' ya existe.")

    for key, value in update_data.items():
        setattr(db_code, key, value)
    try:
        db.commit()
        db.refresh(db_code)
        return db_code
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando código de falla {code_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al actualizar código de falla.")

@router.delete("/failure-codes/{code_id}", status_code=200, summary="Eliminar Código de Falla")
def delete_failure_code(
    code_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Elimina un código de falla."""
    db_code = db.query(FailureCode).filter(FailureCode.id == code_id).first()
    if not db_code:
        raise HTTPException(status_code=404, detail="Código de falla no encontrado.")
    # Opcional: Verificar si está en uso
    # if db.query(WorkOrder).filter(WorkOrder.failure_code_id == code_id).first():
    #    raise HTTPException(status_code=400, detail="El código está en uso y no puede ser eliminado.")
    try:
        db.delete(db_code)
        db.commit()
        return {"success": True, "message": "Código de falla eliminado."}
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando código de falla {code_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al eliminar código de falla.")

# Nuevo endpoint específico para activar/desactivar
@router.post("/failure-codes/{code_id}/set-active", response_model=CodeRead, summary="Activar/Desactivar Código de Falla")
def set_failure_code_active(
    code_id: int,
    active_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Activa o desactiva un código de falla."""
    db_code = db.query(FailureCode).filter(FailureCode.id == code_id).first()
    if not db_code:
        raise HTTPException(status_code=404, detail="Código de falla no encontrado.")
    
    if 'active' not in active_data:
        raise HTTPException(status_code=400, detail="Se requiere el campo 'active'.")
    
    db_code.active = active_data['active']
    try:
        db.commit()
        db.refresh(db_code)
        return db_code
    except Exception as e:
        db.rollback()
        logger.error(f"Error cambiando estado activo para código de falla {code_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al cambiar estado de código de falla.")

# --- Cause Codes ---
@router.post("/cause-codes", response_model=CodeRead, status_code=201, summary="Crear Código de Causa")
def create_cause_code(
    code_data: CodeCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_admin_user)
):
    """Crea un nuevo código de causa."""
    existing_code = db.query(CauseCode).filter(CauseCode.code == code_data.code).first()
    if existing_code: 
        raise HTTPException(status_code=400, detail=f"Código de causa '{code_data.code}' ya existe.")
    db_code = CauseCode(**code_data.dict())
    try:
        db.add(db_code)
        db.commit()
        db.refresh(db_code)
        return db_code
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando código de causa: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al crear código de causa.")

@router.get("/cause-codes", response_model=List[CodeRead], summary="Listar Códigos de Causa")
def list_cause_codes(
    db: Session = Depends(get_db), 
    _user=Depends(get_current_user),
    active_only: bool = False
):
    """Lista todos los códigos de causa disponibles."""
    query = db.query(CauseCode).order_by(CauseCode.code)
    if active_only:
        query = query.filter(CauseCode.active == True)
    return query.all()

@router.put("/cause-codes/{code_id}", response_model=CodeRead, summary="Actualizar Código de Causa")
def update_cause_code(
    code_id: int, 
    code_data: CodeUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_admin_user)
):
    """Actualiza un código de causa existente."""
    db_code = db.query(CauseCode).filter(CauseCode.id == code_id).first()
    if not db_code: 
        raise HTTPException(status_code=404, detail="Código causa no encontrado.")
    
    update_data = code_data.dict(exclude_unset=True)
    if not update_data: 
        raise HTTPException(status_code=400, detail="No hay datos.")
    
    if 'code' in update_data and update_data['code'] != db_code.code:
        if db.query(CauseCode).filter(CauseCode.code == update_data['code'], CauseCode.id != code_id).first():
            raise HTTPException(status_code=400, detail=f"Código causa '{update_data['code']}' ya existe.")
    
    for k, v in update_data.items(): 
        setattr(db_code, k, v)
    
    try:
        db.commit()
        db.refresh(db_code)
        return db_code
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando código de causa {code_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al actualizar código de causa.")

@router.delete("/cause-codes/{code_id}", status_code=200, summary="Eliminar Código de Causa")
def delete_cause_code(
    code_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_admin_user)
):
    """Elimina un código de causa."""
    db_code = db.query(CauseCode).filter(CauseCode.id == code_id).first()
    if not db_code: 
        raise HTTPException(status_code=404, detail="Código causa no encontrado.")
    
    try:
        db.delete(db_code)
        db.commit()
        return {"success": True, "message": "Código de causa eliminado."}
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando código de causa {code_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al eliminar código de causa.")

# Nuevo endpoint específico para activar/desactivar
@router.post("/cause-codes/{code_id}/set-active", response_model=CodeRead, summary="Activar/Desactivar Código de Causa")
def set_cause_code_active(
    code_id: int,
    active_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Activa o desactiva un código de causa."""
    db_code = db.query(CauseCode).filter(CauseCode.id == code_id).first()
    if not db_code:
        raise HTTPException(status_code=404, detail="Código de causa no encontrado.")
    
    if 'active' not in active_data:
        raise HTTPException(status_code=400, detail="Se requiere el campo 'active'.")
    
    db_code.active = active_data['active']
    try:
        db.commit()
        db.refresh(db_code)
        return db_code
    except Exception as e:
        db.rollback()
        logger.error(f"Error cambiando estado activo para código de causa {code_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al cambiar estado de código de causa.")

# --- Remedy Codes ---
@router.post("/remedy-codes", response_model=CodeRead, status_code=201, summary="Crear Código de Remedio")
def create_remedy_code(
    code_data: CodeCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_admin_user)
):
    """Crea un nuevo código de remedio."""
    existing_code = db.query(RemedyCode).filter(RemedyCode.code == code_data.code).first()
    if existing_code: 
        raise HTTPException(status_code=400, detail=f"Código remedio '{code_data.code}' ya existe.")
    
    db_code = RemedyCode(**code_data.dict())
    try:
        db.add(db_code)
        db.commit()
        db.refresh(db_code)
        return db_code
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando código de remedio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al crear código de remedio.")

@router.get("/remedy-codes", response_model=List[CodeRead], summary="Listar Códigos de Remedio")
def list_remedy_codes(
    db: Session = Depends(get_db), 
    _user=Depends(get_current_user),
    active_only: bool = False
):
    """Lista todos los códigos de remedio disponibles."""
    query = db.query(RemedyCode).order_by(RemedyCode.code)
    if active_only:
        query = query.filter(RemedyCode.active == True)
    return query.all()

@router.put("/remedy-codes/{code_id}", response_model=CodeRead, summary="Actualizar Código de Remedio")
def update_remedy_code(
    code_id: int, 
    code_data: CodeUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_admin_user)
):
    """Actualiza un código de remedio existente."""
    db_code = db.query(RemedyCode).filter(RemedyCode.id == code_id).first()
    if not db_code: 
        raise HTTPException(status_code=404, detail="Código remedio no encontrado.")
    
    update_data = code_data.dict(exclude_unset=True)
    if not update_data: 
        raise HTTPException(status_code=400, detail="No hay datos.")
    
    if 'code' in update_data and update_data['code'] != db_code.code:
        if db.query(RemedyCode).filter(RemedyCode.code == update_data['code'], RemedyCode.id != code_id).first():
            raise HTTPException(status_code=400, detail=f"Código remedio '{update_data['code']}' ya existe.")
    
    for k, v in update_data.items(): 
        setattr(db_code, k, v)
    
    try:
        db.commit()
        db.refresh(db_code)
        return db_code
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando código de remedio {code_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al actualizar código de remedio.")

@router.delete("/remedy-codes/{code_id}", status_code=200, summary="Eliminar Código de Remedio")
def delete_remedy_code(
    code_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_admin_user)
):
    """Elimina un código de remedio."""
    db_code = db.query(RemedyCode).filter(RemedyCode.id == code_id).first()
    if not db_code: 
        raise HTTPException(status_code=404, detail="Código remedio no encontrado.")
    
    try:
        db.delete(db_code)
        db.commit()
        return {"success": True, "message": "Código de remedio eliminado."}
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando código de remedio {code_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al eliminar código de remedio.")

# Nuevo endpoint específico para activar/desactivar
@router.post("/remedy-codes/{code_id}/set-active", response_model=CodeRead, summary="Activar/Desactivar Código de Remedio")
def set_remedy_code_active(
    code_id: int,
    active_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Activa o desactiva un código de remedio."""
    db_code = db.query(RemedyCode).filter(RemedyCode.id == code_id).first()
    if not db_code:
        raise HTTPException(status_code=404, detail="Código de remedio no encontrado.")
    
    if 'active' not in active_data:
        raise HTTPException(status_code=400, detail="Se requiere el campo 'active'.")
    
    db_code.active = active_data['active']
    try:
        db.commit()
        db.refresh(db_code)
        return db_code
    except Exception as e:
        db.rollback()
        logger.error(f"Error cambiando estado activo para código de remedio {code_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al cambiar estado de código de remedio.")


@router.get("/sections-data")
def get_sections_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Obtiene datos agregados por sección para el Dashboard, contando ÓRDENES DE TRABAJO REALES.
    """
    logger.info(f"Accediendo a /sections-data por usuario {current_user.username}")
    try:
        # Obtener todas las secciones relevantes para el usuario
        section_query = db.query(Section)
        if current_user.role.nombre == "Jefe de Sección":
            logger.debug(f"Filtrando secciones por section_id = {current_user.section_id}")
            section_query = section_query.filter(Section.id == current_user.section_id)
        sections = section_query.all()
        logger.debug(f"Secciones obtenidas: {[s.nombre for s in sections]}")

        result = []
        for s in sections:
            try:
                # Contar OTs Preventivas para esta sección
                preventive_count = db.query(WorkOrder).filter(
                    WorkOrder.section_id == s.id,
                    WorkOrder.work_type == "Preventivo"
                ).count()

                # Contar OTs Correctivas para esta sección
                corrective_count = db.query(WorkOrder).filter(
                    WorkOrder.section_id == s.id,
                    WorkOrder.work_type == "Correctivo"
                    # Podrías añadir otros tipos aquí si los quieres sumar en algún sitio
                ).count()

                # Contar OTs Pendientes para esta sección
                pending_count = db.query(WorkOrder).filter(
                    WorkOrder.section_id == s.id,
                    WorkOrder.status == "Pendiente"
                    # O incluir 'En curso': WorkOrder.status.in_(['Pendiente', 'En curso'])
                ).count()

                # Calcular total (suma de preventivas y correctivas para el gráfico)
                # Si tienes más tipos de OT, este total puede no ser el "Total OTs" real
                total_section_maintenance = preventive_count + corrective_count

                logger.debug(f"Resultados para Sección {s.nombre}: P={preventive_count}, C={corrective_count}, Pend={pending_count}")

                result.append({
                    "nombre": s.nombre,
                    "preventive": preventive_count, # <-- Ahora cuenta WorkOrder
                    "corrective": corrective_count, # <-- Ahora cuenta WorkOrder
                    "pending": pending_count,       # <-- Añadido para el Stat
                    # "total": total_section_maintenance # Podrías añadirlo si lo necesitas
                })
            except Exception as e_sec:
                logger.error(f"Error procesando datos para sección {s.id} ({s.nombre}): {e_sec}", exc_info=True)
                # Añadir un marcador de error o valores 0 para esta sección
                result.append({ "nombre": s.nombre, "preventive": 0, "corrective": 0, "pending": 0, "error": True })

        logger.info(f"Devolviendo datos agregados para {len(result)} secciones.")
        return result
    except Exception as e:
        logger.error(f"Error general en get_sections_data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al obtener datos para el dashboard")



@router.post("/init")
def initialize_database(data: InitData, db: Session = Depends(get_db), _admin=Depends(get_admin_user)):
    # Roles
    for role in data.roles:
        db_role = db.query(Role).filter(Role.id == role.id).first()
        if not db_role:
            db_role = Role(id=role.id, nombre=role.nombre)
            db.add(db_role)
    db.commit()
    # Usuarios
    for user in data.users:
        db_user = db.query(User).filter(User.username == user.username).first()
        if not db_user:
            db_user = User(
                username=user.username,
                password=user.password,  # En producción, hashear antes
                role_id=user.role_id,
                section=user.section
            )
            db.add(db_user)
    db.commit()
    # Secciones
    for section in data.sections:
        db_section = db.query(Section).filter(Section.nombre == section.nombre).first()
        if not db_section:
            db_section = Section(nombre=section.nombre)
            db.add(db_section)
    db.commit()
    secciones = db.query(Section).all()
    section_map = {s.nombre: s.id for s in secciones}
    # Líneas
    for line in data.lines:
        db_line = db.query(Line).filter(Line.nombre == line.nombre, Line.section_id == line.section_id).first()
        if not db_line:
            db_line = Line(nombre=line.nombre, section_id=line.section_id)
            db.add(db_line)
    db.commit()
    # Máquinas
    for machine in data.machines:
        db_machine = db.query(Machine).filter(Machine.numero_serie == machine.numero_serie).first()
        if not db_machine:
            db_machine = Machine(
                nombre=machine.nombre,
                modelo=machine.modelo,
                marca=machine.marca,
                numero_serie=machine.numero_serie,
                section_id=machine.section_id,
                line_id=machine.line_id
            )
            db.add(db_machine)
    db.commit()
    # Proveedores
    for supplier in data.suppliers:
        db_supplier = db.query(Supplier).filter(Supplier.name == supplier.nombre).first()
        if not db_supplier:
            db_supplier = Supplier(name=supplier.nombre, company=supplier.company, phone=supplier.phone)
            db.add(db_supplier)
    db.commit()
    # Almacenes
    for warehouse in data.warehouses:
        db_warehouse = db.query(Warehouse).filter(Warehouse.name == warehouse.name).first()
        if not db_warehouse:
            db_warehouse = Warehouse(name=warehouse.name)
            db.add(db_warehouse)
    db.commit()
    # Inventario
    for inv in data.inventory:
        db_inventory = db.query(Inventory).filter(Inventory.product_name == inv.product_name, Inventory.location == inv.location).first()
        if not db_inventory:
            db_inventory = Inventory(
                product_name=inv.product_name,
                quantity=inv.quantity,
                location=inv.location,
                price=inv.price,
                supplier_id=inv.supplier_id
            )
            db.add(db_inventory)
    db.commit()
    # Mantenimientos
    for m in data.maintenances:
        db_maintenance = db.query(Maintenance).filter(Maintenance.title == m.frecuencia, Maintenance.machine_id == m.maquina_id).first()
        if not db_maintenance:
            maintenance_type = "Preventivo"
            try:
                fecha_inicio = datetime.strptime(m.fechaInicio, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Formato de fecha inválido para mantenimiento en máquina ID {m.maquina_id}. Usa YYYY-MM-DD.")
            db_maintenance = Maintenance(
                title=m.frecuencia,
                type=maintenance_type,
                description=m.frecuencia,
                machine_id=m.maquina_id,
                created_at=fecha_inicio
            )
            db.add(db_maintenance)
    db.commit()
    # Órdenes de Trabajo
    for order in data.work_orders:
        db_order = db.query(WorkOrder).filter(WorkOrder.title == order.title, WorkOrder.machine_id == order.machine_id).first()
        if not db_order:
            try:
                created_at = datetime.strptime(order.created_at, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Formato de fecha inválido para la orden '{order.title}'. Usa YYYY-MM-DDTHH:MM:SS.")
            db_order = WorkOrder(
                title=order.title,
                work_type=order.work_type,
                section_id=order.section_id,
                line_id=order.line_id,
                machine_id=order.machine_id,
                operator=order.operator,
                status=order.status,
                created_at=created_at,
                imagen_url=order.imagen_url
            )
            db.add(db_order)
    db.commit()
    return {"message": "Base de datos inicializada correctamente."}



@router.post("/documents/upload")
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),  # Asegúrate de importar 'File' y 'UploadFile' de FastAPI
    doc_type: str = Form(...),     # Asegúrate de importar 'Form' de FastAPI
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Validar permisos
        if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
            raise HTTPException(status_code=403, detail="No tienes permisos para esta operación")
        
        # Validar tipo de documento
        if doc_type not in ["albaran", "parte_trabajo"]:
            raise HTTPException(status_code=400, detail="Tipo de documento no válido")

        # Loguear información para depuración
        logging.info(f"Headers recibidos: {dict(request.headers)}")
        logging.info(f"Content-Type: {request.headers.get('content-type')}")
        logging.info(f"Tipo de archivo recibido: {file.content_type}")
        logging.info(f"Nombre del archivo: {file.filename}")
        logging.info(f"Tipo de documento: {doc_type}")

        file_content = await file.read()
        await file.seek(0)  # Rebobinar
        file_size = len(file_content)
        
        if file_size > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(status_code=400, detail="El archivo excede el tamaño máximo (50MB)")
        
        
        # Generar ruta de almacenamiento
        file_path = f"storage/documents/{datetime.now().timestamp()}_{file.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Guardar archivo
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        # Crear registro en BD
        doc = Document(
            filename=os.path.basename(file_path),
            original_filename=file.filename,
            type=doc_type,
            status="pending",
            file_path=file_path,
            created_at=datetime.utcnow(),
            created_by_id=current_user.id
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Crear instancia del procesador
        doc_processor = DocumentProcessor()

        # Procesar documento en segundo plano
        async def process_and_update():
            try:
                # Procesar documento
                result = await doc_processor.process_document(
                    file_path=file_path,
                    doc_type=doc_type,
                    db=db,
                    doc_id=doc.id
                )
                
                # Actualizar documento con resultado
                doc.processed_at = datetime.utcnow()
                
                if result.get('success'):
                    doc.status = "completed"
                    extracted_data = result.get('extracted_data', {})
                    
                    # Guardar datos extraídos
                    doc.processed_data = extracted_data
                    
                    if doc_type == 'albaran':
                        supplier_data = extracted_data.get('supplier', {})
                        doc.supplier_name = supplier_data.get('name')
                        doc.total_amount = extracted_data.get('totals', {}).get('total_amount')
                    
                    logging.info(f"Documento {doc.id} procesado correctamente")
                else:
                    doc.status = "error"
                    doc.error_message = result.get('error', 'Error desconocido en el procesamiento')
                    logging.error(f"Error procesando documento {doc.id}: {doc.error_message}")
                
                db.commit()
                
            except Exception as e:
                logging.error(f"Error en el procesamiento del documento {doc.id}: {str(e)}")
                doc.status = "error"
                doc.error_message = str(e)
                db.commit()

        # Agregar tarea en segundo plano
        background_tasks.add_task(process_and_update)

        return {
            "success": True,
            "message": "Documento subido y en proceso",
            "document": {
                "id": doc.id,
                "filename": doc.filename,
                "type": doc.type,
                "status": doc.status
            }
        }
    except Exception as e:
        logging.error(f"Error en upload_document: {str(e)}")
        # Incluir traza completa para mejor depuración
        import traceback
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/documents")
async def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ordenar por fecha de creación descendente puede ser útil
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "type": doc.type,
            "status": doc.status,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
            # ----- Línea Añadida/Modificada -----
            # Incluye el mensaje de error SOLO si el estado es 'error'
            "error_message": doc.error_message if doc.status == 'error' else None
            # ------------------------------------
        }
        for doc in documents
    ]
@router.delete("/documents/{doc_id}")
    
@router.get("/documents/{doc_id}/data")
async def get_document_data(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Asegúrate que get_current_user funciona
):
    """
    Obtiene los datos extraídos y la información básica de un documento (VERSIÓN CORREGIDA)
    """
    t_start = time.time()
    print(f"***** ({doc_id}) ENTERING get_document_data *****")

    # 1. Buscar el documento PRIMERO
    t_query_doc_start = time.time()
    doc = db.query(Document).filter(Document.id == doc_id).first()
    t_query_doc_end = time.time()
    print(f"(DEBUG-TIME) ({doc_id}) Consulta Documento tardó: {t_query_doc_end - t_query_doc_start:.4f}s")

    # 2. Comprobar si se encontró el documento (¡IMPORTANTE!)
    if not doc:
        print(f"ERROR: ({doc_id}) Documento con ID {doc_id} NO encontrado en la BD.")
        raise HTTPException(status_code=404, detail=f"Documento con ID {doc_id} no encontrado")

    # 3. Comprobar estado (Opcional - si sólo quieres datos de docs 'completed')
    #    Si quieres permitir ver datos aunque el estado sea 'error' o 'pending',
    #    deja comentado o elimina este bloque 'if'.
    # if doc.status != "completed":
    #     print(f"WARNING: ({doc_id}) Documento encontrado pero estado es '{doc.status}', no 'completed'.")
    #     raise HTTPException(status_code=400, detail=f"El documento está en estado '{doc.status}', no ha sido procesado completamente.")

    # --- Ahora que sabemos que 'doc' existe, continuamos ---
    try:
        # 4. Obtener Almacenes
        t_query_wh_start = time.time()
        warehouses = []
        warehouses_list = []
        try:
            warehouses = db.query(Warehouse).all()
            warehouses_list = [{"id": w.id, "name": w.name} for w in warehouses]
        except Exception as e_wh:
             print(f"ERROR: ({doc_id}) Error consultando almacenes: {e_wh}")
        t_query_wh_end = time.time()
        print(f"(DEBUG-TIME) ({doc_id}) Consulta Almacenes ({len(warehouses_list)}) tardó: {t_query_wh_end - t_query_wh_start:.4f}s")

        # 5. Obtener y validar datos procesados
        extracted_data_size = 0
        processed_data_content = None
        t_read_data_start = time.time()
        try:
            # Accedemos a los datos procesados (sabemos que 'doc' no es None)
            processed_data_content = doc.processed_data
            t_read_data_end = time.time()
            print(f"(DEBUG-TIME) ({doc_id}) Acceso/lectura de doc.processed_data tardó: {t_read_data_end - t_read_data_start:.4f}s")

            # Aseguramos que sea un diccionario si es None en la BD
            if processed_data_content is None:
                 print(f"WARNING: ({doc_id}) doc.processed_data es None en la BD.")
                 processed_data_content = {}

            # Prints de debug de tamaño y tipo (opcionales)
            print(f"(DEBUG-TYPE) ({doc_id}) Tipo de doc.processed_data leído: {type(processed_data_content)}")
            try:
                extracted_data_json_string = json.dumps(processed_data_content)
                extracted_data_size = len(extracted_data_json_string)
                print(f"(DEBUG-SIZE) ({doc_id}) Tamaño de doc.processed_data (bytes aprox. JSON): {extracted_data_size}")
            except Exception as e_dump_size:
                print(f"ERROR: ({doc_id}) Error al calcular tamaño con json.dumps: {e_dump_size}")
                extracted_data_size = -1
            # (Puedes añadir el print del tiempo de cálculo de tamaño si quieres)

        except Exception as e_read:
            print(f"ERROR: ({doc_id}) Error al acceder/leer doc.processed_data: {e_read}")
            # Decidimos devolver un error en los datos extraídos si falla la lectura
            processed_data_content = {"error": "Fallo al leer datos procesados"}

        # 6. Construir la respuesta (sabemos que 'doc' no es None aquí)
        # Asegúrate que los nombres doc.id, doc.filename, etc. coinciden con tu modelo
        document_info = {
            "id": doc.id,
            "filename": doc.filename,
            "original_filename": doc.original_filename, # <-- Corregido
            "type": doc.type,                           # <-- Corregido
            "status": doc.status,                       # <-- Corregido (útil)
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "processed_at": doc.processed_at.isoformat() if doc.processed_at else None
        }

        response_payload = {
            "document": document_info,
            "extracted_data": processed_data_content,
            "warehouses": warehouses_list
        }

        t_end = time.time()
        print(f"(DEBUG-TIME) ({doc_id}) get_document_data completado (lógica interna) en {t_end - t_start:.4f}s. Preparado para devolver respuesta.")
        print(f"(DEBUG-DATA) ({doc_id}) Devolviendo document.original_filename: {document_info.get('original_filename')}")

        return response_payload

    # Manejo de excepciones generales que puedan ocurrir *después* de encontrar 'doc'
    except HTTPException as http_exc: # Si alguna lógica interna lanza HTTPException
        print(f"ERROR: ({doc_id}) HTTPException interna en get_document_data: {http_exc.detail}")
        raise http_exc
    except Exception as e_general:
         print(f"ERROR: ({doc_id}) Error inesperado general en get_document_data: {e_general}")
         import traceback
         print(traceback.format_exc()) # Imprime traza completa del error
         raise HTTPException(status_code=500, detail="Error interno del servidor al obtener datos del documento.")

@router.post("/documents/{doc_id}/confirm-item")
async def confirm_item(
    doc_id: int,
    item_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Confirma un elemento individual (producto u orden de trabajo)"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    try:
        if doc.type == "albaran":
            # Procesar producto
            product_name = item_data.get("description")
            quantity = item_data.get("quantity", 0)
            price = item_data.get("unit_price", 0)
            warehouse_id = item_data.get("warehouse_id")
            
            # Verificar almacén
            warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
            if not warehouse:
                raise HTTPException(status_code=404, detail="Almacén no encontrado")
            
            # Buscar si el producto ya existe
            product = db.query(Inventory).filter(
                Inventory.product_name == product_name,
                Inventory.warehouse_id == warehouse_id
            ).first()
            
            if product:
                # Actualizar producto existente
                product.quantity += quantity
                product.price = price
            else:
                # Crear nuevo producto
                product = Inventory(
                    product_name=product_name,
                    quantity=quantity,
                    price=price,
                    warehouse_id=warehouse_id,
                    supplier_id=None  # Se puede añadir lógica para buscar/crear proveedor
                )
                db.add(product)
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Producto '{product_name}' añadido/actualizado en almacén"
            }
            
        elif doc.type == "parte_trabajo":
            # Procesar orden de trabajo
            machine_name = item_data.get("machine")
            details = item_data.get("details")
            operator = item_data.get("operator")
            
            # Buscar máquina
            machine = db.query(Machine).filter(Machine.nombre.ilike(f"%{machine_name}%")).first()
            if not machine:
                return {
                    "success": False,
                    "message": f"Máquina '{machine_name}' no encontrada"
                }
            
            # Crear orden de trabajo
            work_order = WorkOrder(
                title=f"Trabajo en {machine_name}",
                details=details,
                work_type="Correctivo",
                machine_id=machine.id,
                section_id=machine.section_id,
                line_id=machine.line_id,
                operator=operator,
                status="Pendiente",
                source_document_id=doc.id,
                created_at=datetime.utcnow()
            )
            
            db.add(work_order)
            db.commit()
            
            return {
                "success": True,
                "message": f"Orden de trabajo creada para máquina '{machine_name}'"
            }
            
        else:
            raise HTTPException(status_code=400, detail="Tipo de documento no soportado")
            
    except Exception as e:
        db.rollback()
        logging.error(f"Error procesando elemento: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error procesando elemento: {str(e)}")

@router.post("/documents/{doc_id}/complete")
async def complete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marca un documento como completamente procesado"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    doc.status = "confirmed"
    doc.processed_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Documento marcado como completamente procesado"
    }


@router.post("/debug-request")
async def debug_request(request: Request):
    """Endpoint para depurar peticiones"""
    try:
        # Mostrar headers
        print("Headers:", request.headers)
        
        # Mostrar body
        body = await request.body()
        print("Body raw:", body)
        
        # Intentar parsear como JSON
        try:
            body_json = await request.json()
            print("Body JSON:", body_json)
        except:
            print("No es JSON válido")
            
        return {"success": True, "headers": dict(request.headers), "body": str(body)}
    except Exception as e:
        print("Error:", str(e))
        return {"error": str(e)}

@router.get("/documents/{doc_id}/data")
async def get_document_data(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene los datos extraídos de un documento"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    if doc.status != "completed":
        raise HTTPException(status_code=400, detail="El documento no ha sido procesado completamente")
    
    # Obtener almacenes disponibles para selección
    warehouses = db.query(Warehouse).all()
    warehouses_list = [{"id": w.id, "name": w.name} for w in warehouses]
    
    return {
        "document": {
            "id": doc.id,
            "filename": doc.filename,
            "original_filename": doc.original_filename,
            "type": doc.type,
            "status": doc.status,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "processed_at": doc.processed_at.isoformat() if doc.processed_at else None
        },
        "extracted_data": doc.processed_data,
        "warehouses": warehouses_list
    }

@router.post("/documents/{doc_id}/complete")
async def complete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marca un documento como completamente procesado"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    doc.status = "confirmed"
    doc.processed_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Documento marcado como completamente procesado"
    }

@router.post("/documents/{doc_id}/feedback")
async def send_feedback(
    doc_id: int,
    feedback_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Envía feedback al servicio Donut para mejorar la extracción"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    try:
        # Añadir información del documento al feedback
        feedback_data["document_id"] = doc_id
        feedback_data["original_filename"] = doc.original_filename
        feedback_data["document_type"] = doc.type
        feedback_data["feedback_by"] = current_user.username
        
        # Enviar feedback al servidor Donut
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://192.168.1.62:8001/feedback",
                json=feedback_data,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status != 200:
                    response_text = await response.text()
                    raise HTTPException(
                        status_code=response.status, 
                        detail=f"Error enviando feedback: {response_text}"
                    )
                
                result = await response.json()
        
        return {
            "success": True,
            "message": "Feedback enviado correctamente"
        }
        
    except Exception as e:
        logging.error(f"Error enviando feedback: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error enviando feedback: {str(e)}")
    
# URL del proxy
#PROXY_URL = "http://192.168.1.62:5000"

@router.post("/documents/{doc_id}/process-with-ai")
async def process_document_with_ai(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Procesa un documento usando el proxy de extracción de IA"""
    logging.info(f"======= INICIANDO PROCESAMIENTO DEL DOCUMENTO {doc_id} =======")
    logging.info(f"Usuario: {current_user.username}, Rol: {current_user.role.nombre if current_user.role else 'Sin rol'}")
    
    try:
        # Obtener el documento
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            logging.error(f"Documento {doc_id} no encontrado")
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        logging.info(f"Documento encontrado: {doc.id}, tipo: {doc.type}, archivo: {doc.file_path}")
        
        # Crear instancia del procesador de documentos
        doc_processor = DocumentProcessor()
        
        # Procesar el documento con el método que ya funciona
        result = await doc_processor.process_document(
            file_path=doc.file_path,
            doc_type=doc.type,
            db=db,
            doc_id=doc.id
        )
        
        # Actualizar el documento con el resultado
        if result.get('success', False):
            extracted_data = result.get('extracted_data', {})
            
            # Asegurar estructura mínima necesaria para la UI
            if "supplier" not in extracted_data:
                extracted_data["supplier"] = {"name": ""}
            
            if "products" not in extracted_data:
                extracted_data["products"] = []
            else:
                # Asegurar que cada producto tenga los campos necesarios
                for product in extracted_data["products"]:
                    if "description" not in product:
                        product["description"] = ""
                    if "quantity" not in product:
                        product["quantity"] = 0
                    if "unit_price" not in product:
                        product["unit_price"] = 0
                    # Añadimos campo discount con valor predeterminado 0 si no existe
                    if "discount" not in product:
                        product["discount"] = 0
            
            if "totals" not in extracted_data:
                extracted_data["totals"] = {"total_amount": 0}
            
            doc.processed_data = extracted_data
            doc.processed_at = datetime.utcnow()
            doc.status = "completed"
            
            if doc.type == 'albaran':
                supplier_data = extracted_data.get('supplier', {})
                doc.supplier_name = supplier_data.get('name', "")
                doc.total_amount = extracted_data.get('totals', {}).get('total_amount', 0)
            
            # Añadir log explícito para ver lo que estamos guardando
            logging.info(f"Actualizando documento {doc.id} a estado 'completed' con datos: {json.dumps(extracted_data, indent=2)[:500]}...")
            
            db.commit()
            
            return {
                 "success": True,
                 "document": {
                     "id": doc.id,
                     "status": doc.status,
                     "processed_at": doc.processed_at.isoformat() if doc.processed_at else None
                 },
                  "extracted_data": extracted_data  # Usamos el extracted_data modificado
       }
        else:
            error_msg = result.get('error', 'Error desconocido en el procesamiento')
            
            doc.status = "error"
            doc.error_message = error_msg
            db.commit()
            
            return {"success": False, "error": error_msg}
            
    except Exception as e:
        logging.error(f"Error general: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"success": False, "error": f"Error general: {str(e)}"}
    

