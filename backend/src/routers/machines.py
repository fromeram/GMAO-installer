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


# --- Section lines 2024-2300 ---
# ---------------------------
# ENDPOINTS DE MAQUINAS
# ---------------------------

@router.get("/maquinas", response_model=List[MaquinaRead]) # <-- Cambiado response_model
def get_maquinas(db: Session = Depends(get_db)):
    # Devolver directamente la lista de objetos SQLAlchemy,
    # FastAPI se encargará de convertirlos usando MaquinaRead
    machines = db.query(Machine).all()
    return machines

@router.post("/maquinas", response_model=MaquinaRead)
def create_maquina(
    data: MaquinaCreate, 
    request: Request,  # ← AÑADIR Request
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_admin_user)  # ← CAMBIAR _admin por current_user
):
    # ... validaciones existentes ...
    sec = db.query(Section).filter(Section.id == data.section_id).first()
    if not sec:
        raise HTTPException(status_code=400, detail="Sección no existe.")
    ln = db.query(Line).filter(Line.id == data.line_id, Line.section_id == data.section_id).first()
    if not ln:
        raise HTTPException(status_code=400, detail="Línea no existe en esa sección.")
    existing_mach = db.query(Machine).filter(Machine.numero_serie == data.numero_serie).first()
    if existing_mach:
        raise HTTPException(status_code=400, detail="Máquina con este número de serie ya existe.")

    mach = Machine(
        nombre=data.nombre,
        modelo=data.modelo,
        marca=data.marca,
        numero_serie=data.numero_serie,
        section_id=data.section_id,
        line_id=data.line_id,
        criticidad=data.criticidad
    )
    db.add(mach)
    db.commit()
    db.refresh(mach)
    
    # *** AÑADIR AUDIT TRAIL ***
    audit_manager.log_action(
        db=db,
        action="CREATE",
        entity=mach,
        user=current_user,
        request=request,
        notes=f"Máquina creada: {mach.nombre} (S/N: {mach.numero_serie})"
    )
    db.commit()  # Commit del audit log
    # *** FIN AUDIT TRAIL ***
    
    return mach

# MODIFICAR el endpoint PUT /maquinas/{machine_id} (línea ~970)
@router.put("/maquinas/{machine_id}", response_model=MaquinaRead)
def update_maquina(
    machine_id: int,
    data: MaquinaUpdate,
    request: Request,  # ← AÑADIR Request
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # ← CAMBIAR _admin por current_user
):
    mach = db.query(Machine).filter(Machine.id == machine_id).first()
    if not mach:
        raise HTTPException(status_code=404, detail="Máquina no encontrada.")

    # *** CAPTURAR ESTADO ANTERIOR PARA AUDIT ***
    old_data = audit_manager.extract_entity_data(mach)
    # *** FIN CAPTURA ***

    update_data = data.dict(exclude_unset=True)
    
    # ... validaciones existentes ...
    if "numero_serie" in update_data and update_data["numero_serie"] != mach.numero_serie:
        existing_mach = db.query(Machine).filter(Machine.numero_serie == update_data["numero_serie"]).first()
        if existing_mach:
            raise HTTPException(status_code=400, detail="Ya existe otra máquina con ese número de serie.")

    new_section_id = update_data.get("section_id", mach.section_id)
    new_line_id = update_data.get("line_id", mach.line_id)

    if new_section_id != mach.section_id or new_line_id != mach.line_id:
         sec = db.query(Section).filter(Section.id == new_section_id).first()
         if not sec:
              raise HTTPException(status_code=400, detail="La nueva sección no existe.")
         ln = db.query(Line).filter(Line.id == new_line_id, Line.section_id == new_section_id).first()
         if not ln:
              raise HTTPException(status_code=400, detail="La nueva línea no existe en la nueva sección.")

    # Actualizar campos
    for key, value in update_data.items():
        setattr(mach, key, value)

    db.commit()
    db.refresh(mach)
    
    # *** AÑADIR AUDIT TRAIL ***
    new_data = audit_manager.extract_entity_data(mach)
    audit_manager.log_action(
        db=db,
        action="UPDATE",
        entity=mach,
        user=current_user,
        request=request,
        old_data=old_data,
        new_data=new_data,
        notes=f"Máquina actualizada: {mach.nombre}"
    )
    db.commit()  # Commit del audit log
    # *** FIN AUDIT TRAIL ***
    
    return mach

# MODIFICAR el endpoint DELETE /maquinas/{machine_id} (línea ~1020)
@router.delete("/maquinas/{machine_id}")
def delete_maquina(
    machine_id: int,
    request: Request,  # ← AÑADIR Request
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # ← CAMBIAR _admin por current_user
):
    mach = db.query(Machine).options(
        joinedload(Machine.maintenances),
        joinedload(Machine.work_orders)
    ).filter(Machine.id == machine_id).first()

    if not mach:
        raise HTTPException(status_code=404, detail="Máquina no encontrada.")

    # Validaciones de dependencias existentes...
    if mach.maintenances:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar la máquina porque tiene {len(mach.maintenances)} mantenimientos asociados."
        )
    if mach.work_orders:
         raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar la máquina porque tiene {len(mach.work_orders)} órdenes de trabajo asociadas."
        )

    # *** CAPTURAR DATOS ANTES DE ELIMINAR ***
    old_data = audit_manager.extract_entity_data(mach)
    machine_name = mach.nombre
    machine_serial = mach.numero_serie
    # *** FIN CAPTURA ***

    db.delete(mach)
    
    # *** AÑADIR AUDIT TRAIL ***
    audit_manager.log_action(
        db=db,
        action="DELETE",
        entity=mach,
        user=current_user,
        request=request,
        old_data=old_data,
        notes=f"Máquina eliminada: {machine_name} (S/N: {machine_serial})"
    )
    # *** FIN AUDIT TRAIL ***
    
    db.commit()
    return {"message": "Máquina eliminada correctamente."}


@router.get(
    "/maquinas/{machine_id}/parts",
    response_model=List[MachinePartRead],
    summary="Obtener lista de repuestos (BOM) para una máquina"
)
def get_machine_parts(
    machine_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user) # Añadimos 'current_user' para asegurar que el usuario está logueado
):
    """
    Obtiene la lista de repuestos asociados a una máquina específica.
    Permite el acceso a cualquier usuario autenticado.
    """
    # Verificar que la máquina existe
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")

    # Obtener las asociaciones de repuestos sin filtrar por rol
    associations = db.query(MachinePartAssociation).options(
        joinedload(MachinePartAssociation.part)
    ).filter(MachinePartAssociation.machine_id == machine_id).all()

    return associations

@router.post(
    "/maquinas/{machine_id}/parts",
    response_model=MachinePartRead, # <- Usa el modelo definido en este archivo
    status_code=status.HTTP_201_CREATED,
    summary="Añadir un repuesto al BOM de una máquina"
)
def add_part_to_machine(
    machine_id: int,
    part_data: MachinePartCreate, # <- Usa el modelo definido en este archivo
    db: Session = Depends(get_db),
    _admin=Depends(get_admin_user) # Permiso de Admin por ahora
):
    """Añade una asociación entre una máquina y un repuesto."""
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")

    inventory_item = db.query(Inventory).filter(Inventory.id == part_data.inventory_id).first()
    if not inventory_item:
        raise HTTPException(status_code=404, detail="Repuesto (Inventory ID) no encontrado")

    existing_assoc = db.query(MachinePartAssociation).filter(
        MachinePartAssociation.machine_id == machine_id,
        MachinePartAssociation.inventory_id == part_data.inventory_id
    ).first()

    if existing_assoc:
        raise HTTPException(
            status_code=409, # Conflict
            detail=f"El repuesto '{inventory_item.product_name}' ya está asociado a esta máquina."
        )

    new_assoc = MachinePartAssociation(
        machine_id=machine_id,
        inventory_id=part_data.inventory_id,
        quantity=part_data.quantity
    )
    db.add(new_assoc)
    try:
        db.commit()
        db.refresh(new_assoc)
        # Necesitamos cargar manualmente la relación 'part' para la respuesta,
        # ya que 'new_assoc' recién creada podría no tenerla cargada aún.
        db.refresh(new_assoc.part) # O db.refresh(inventory_item) si usamos ese objeto
        logger.info(f"Asociado repuesto ID {new_assoc.inventory_id} a máquina ID {new_assoc.machine_id}")
        return new_assoc
    except Exception as e:
        db.rollback()
        logger.error(f"Error al añadir repuesto a máquina: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al guardar asociación: {e}")


@router.delete(
    "/maquinas/{machine_id}/parts/{inventory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un repuesto del BOM de una máquina"
)
def remove_part_from_machine(
    machine_id: int,
    inventory_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin_user) # Permiso de Admin por ahora
):
    """Elimina la asociación entre una máquina y un repuesto."""
    assoc = db.query(MachinePartAssociation).filter(
        MachinePartAssociation.machine_id == machine_id,
        MachinePartAssociation.inventory_id == inventory_id
    ).first()

    if not assoc:
        raise HTTPException(status_code=404, detail="Asociación máquina-repuesto no encontrada.")

    db.delete(assoc)
    try:
        db.commit()
        logger.info(f"Eliminada asociación repuesto ID {inventory_id} de máquina ID {machine_id}")
        return None # No devolver cuerpo para 204 No Content
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar repuesto de máquina: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al eliminar asociación: {e}")



# --- Section lines 8431-8841 ---
# --- ENDPOINTS DE MÉTRICAS E HISTORIA DE MÁQUINAS ---
@router.get("/machines/line/{line_id}", response_model=List[MaquinaRead])
def get_machines_for_line(
    line_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene todas las máquinas asociadas a una línea de producción específica.
    """
    line = db.query(Line).filter(Line.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Línea no encontrada.")
    
    # Usamos joinedload para optimizar, aunque aquí no sea estrictamente necesario
    # es una buena práctica.
    machines = db.query(Machine).options(
        joinedload(Machine.line),
        joinedload(Machine.section)
    ).filter(Machine.line_id == line_id).all()
    
    return machines

@router.get("/maquinas/line/{line_id}", response_model=List[MaquinaRead])
def get_machines_for_line(
    line_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene todas las máquinas asociadas a una línea de producción específica.
    """
    line = db.query(Line).filter(Line.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Línea no encontrada.")
    
    machines = db.query(Machine).filter(Machine.line_id == line_id).all()
    return machines


@router.get("/maquinas/{machine_id}/metrics", response_model=MachineMetricsResponse)
def get_machine_metrics(
    machine_id: int,
    period: Optional[str] = Query("last_year", description="Periodo de tiempo: last_month, last_year, all"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calcula métricas de mantenimiento para una máquina específica:
    - MTBF (Mean Time Between Failures)
    - MTTR (Mean Time To Repair)
    - Disponibilidad
    - Conteo de mantenimientos por tipo
    """
    # Verificar existencia de la máquina
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Máquina con ID {machine_id} no encontrada")
    
    # Determinar fechas según periodo seleccionado
    now = datetime.utcnow()
    
    if period == "last_month":
        start_date = now - timedelta(days=30)
    elif period == "last_year":
        start_date = now - timedelta(days=365)
    else:  # "all"
        # Usar la fecha más antigua en la base de datos
        oldest_order = db.query(WorkOrder).filter(
            WorkOrder.machine_id == machine_id
        ).order_by(WorkOrder.created_at.asc()).first()
        
        if oldest_order:
            start_date = oldest_order.created_at
        else:
            # Si no hay órdenes, usar un año atrás como default
            start_date = now - timedelta(days=365)
    
    # Consultar órdenes de trabajo cerradas para esta máquina en el periodo
    orders = db.query(WorkOrder).filter(
        WorkOrder.machine_id == machine_id,
        WorkOrder.status == "Cerrada",
        WorkOrder.created_at >= start_date,
        WorkOrder.finished_at.isnot(None)
    ).order_by(WorkOrder.created_at.asc()).all()
    
    # Si no hay órdenes, devolver métricas vacías
    if not orders:
        return {
            "mtbf": 0,
            "mttr": 0,
            "disponibilidad": 0,
            "total_downtime_hours": 0,
            "total_uptime_hours": 0,
            "total_orders": 0,
            "orders_by_type": {
                "Preventivo": 0,
                "Correctivo": 0,
                "Inspección": 0,
                "Mejora": 0,
                "Modificación": 0,
                "Seguridad": 0
            },
            "lastYear": {
                "preventivas": 0,
                "correctivas": 0,
                "total": 0
            },
            "period": period
        }
    
    # Inicializar contadores
    total_orders = len(orders)
    total_downtime_hours = 0
    total_uptime_hours = 0
    orders_by_type = {
        "Preventivo": 0,
        "Correctivo": 0,
        "Inspección": 0,
        "Mejora": 0,
        "Modificación": 0,
        "Seguridad": 0
    }
    
    # Calcular tiempos de reparación y entre fallos
    repair_times = []  # Lista de tiempos de reparación
    between_failure_times = []  # Lista de tiempos entre fallos
    
    for i, order in enumerate(orders):
        # Contar por tipo
        order_type = order.work_type
        if order_type in orders_by_type:
            orders_by_type[order_type] += 1
        
        # Tiempo de reparación
        if order.actual_start_time and order.actual_end_time:
            # Si tenemos tiempos exactos de inicio y fin
            repair_time = (order.actual_end_time - order.actual_start_time).total_seconds() / 3600  # en horas
        elif order.downtime_hours:
            # Si tenemos horas de inactividad registradas
            repair_time = order.downtime_hours
        elif order.finished_at and order.created_at:
            # Como fallback, usar diferencia entre creación y cierre
            repair_time = (order.finished_at - order.created_at).total_seconds() / 3600
        else:
            # Default si no hay información
            repair_time = 0
        
        repair_times.append(repair_time)
        total_downtime_hours += repair_time
        
        # Tiempo entre fallos (solo para correctivas)
        if order.work_type == "Correctivo" and i > 0 and orders[i-1].work_type == "Correctivo":
            # Tiempo entre el fin de la última correctiva y el inicio de esta
            previous_end = orders[i-1].finished_at
            current_start = order.created_at
            
            between_failure = (current_start - previous_end).total_seconds() / 3600  # en horas
            between_failure_times.append(between_failure)
            total_uptime_hours += between_failure
    
    # Calcular MTTR (Mean Time To Repair) - promedio de tiempos de reparación
    mttr = sum(repair_times) / len(repair_times) if repair_times else 0
    
    # Calcular MTBF (Mean Time Between Failures) - promedio de tiempos entre fallos
    mtbf = sum(between_failure_times) / len(between_failure_times) if between_failure_times else 0
    
    # Si no hay datos suficientes para MTBF, usar una estimación basada en la ventana de tiempo
    if mtbf == 0 and orders_by_type["Correctivo"] > 0:
        # Estimar MTBF como tiempo total / número de fallos correctivos
        total_period_hours = (now - start_date).total_seconds() / 3600
        corrective_count = orders_by_type["Correctivo"]
        mtbf = total_period_hours / corrective_count if corrective_count > 0 else total_period_hours
    
    # Calcular disponibilidad
    total_time = total_uptime_hours + total_downtime_hours
    disponibilidad = (total_uptime_hours / total_time * 100) if total_time > 0 else 0
    
    # Si la disponibilidad parece incorrecta, usar fórmula alternativa
    if disponibilidad == 0 or total_time < 24:  # Si hay muy poco tiempo registrado
        # Fórmula alternativa: MTBF / (MTBF + MTTR) * 100
        if mtbf + mttr > 0:
            disponibilidad = (mtbf / (mtbf + mttr)) * 100
    
    # Datos adicionales para el último año/mes
    last_period_data = {
        "preventivas": 0,
        "correctivas": 0,
        "total": 0
    }
    
    last_period_start = now - timedelta(days=365 if period != "last_month" else 30)
    
    for order in orders:
        if order.created_at >= last_period_start:
            last_period_data["total"] += 1
            if order.work_type == "Preventivo":
                last_period_data["preventivas"] += 1
            elif order.work_type == "Correctivo":
                last_period_data["correctivas"] += 1
    
    return {
        "mtbf": round(mtbf, 2),
        "mttr": round(mttr, 2),
        "disponibilidad": round(disponibilidad, 2),
        "total_downtime_hours": round(total_downtime_hours, 2),
        "total_uptime_hours": round(total_uptime_hours, 2),
        "total_orders": total_orders,
        "orders_by_type": orders_by_type,
        "lastYear": last_period_data,
        "period": period
    }

@router.get(
    "/maquinas/{machine_id}/history",
    response_model=List[WorkOrderRead],
    summary="Obtener historial de órdenes de trabajo para una máquina"
)
def get_machine_history(
    machine_id: int,
    limit: Optional[int] = Query(None, description="Límite de resultados a devolver"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene la lista de órdenes de trabajo asociadas a una máquina específica,
    ordenada por fecha de creación descendente.
    """
    # Verificar primero que la máquina existe
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Máquina con ID {machine_id} no encontrada."
        )

    try:
        # Consultar órdenes de trabajo filtrando por machine_id
        query = db.query(WorkOrder).options(
            joinedload(WorkOrder.assigned_to),
            joinedload(WorkOrder.machine_obj),
            joinedload(WorkOrder.section),
            joinedload(WorkOrder.line),
            joinedload(WorkOrder.failure_code),
            joinedload(WorkOrder.cause_code),
            joinedload(WorkOrder.remedy_code)
            # TEMPORALMENTE COMENTADO: joinedload(WorkOrder.technicians).joinedload(WorkOrderTechnician.technician)
        ).filter(WorkOrder.machine_id == machine_id)\
         .order_by(WorkOrder.created_at.desc())
        
        # Aplicar límite si se especifica
        if limit is not None:
            query = query.limit(limit)
        
        orders = query.all()
        logger.info(f"Encontradas {len(orders)} órdenes para historial de máquina ID {machine_id}")
        
        # Crear respuesta manual sin technicians para evitar el error
        result = []
        for order in orders:
            # Convertir a diccionario manualmente para controlar el campo technicians
            order_dict = {
                "id": order.id,
                "order_number": order.order_number,
                "title": order.title,
                "details": order.details,
                "work_type": order.work_type,
                "section_id": order.section_id,
                "line_id": order.line_id,
                "machine_id": order.machine_id,
                "operator": order.operator,
                "assigned_to_id": order.assigned_to_id,
                "status": order.status,
                "created_at": order.created_at,
                "finished_at": order.finished_at,
                "imagen_url": order.imagen_url,
                "failure_code_id": order.failure_code_id,
                "cause_code_id": order.cause_code_id,
                "remedy_code_id": order.remedy_code_id,
                "actual_start_time": order.actual_start_time,
                "actual_end_time": order.actual_end_time,
                "downtime_hours": order.downtime_hours,
                "completion_notes": order.completion_notes,
                "format_change_type": order.format_change_type,
                "affected_machines": order.affected_machines,
                "format_from_id": order.format_from_id,
                "format_to_id": order.format_to_id,
                "format_from_name": order.format_from_name,
                "format_to_name": order.format_to_name,
                "estimated_setup_duration": order.estimated_setup_duration,
                "setup_duration": order.setup_duration,
                "production_loss_hours": order.production_loss_hours,
                "setup_team": order.setup_team,
                "setup_notes": order.setup_notes,
                
                # ✅ LÍNEA AÑADIDA
                "setup_efficiency": order.setup_efficiency,
                
                # Relaciones
                "failure_code": {
                    "id": order.failure_code.id,
                    "code": order.failure_code.code,
                    "description": order.failure_code.description
                } if order.failure_code else None,
                
                "cause_code": {
                    "id": order.cause_code.id,
                    "code": order.cause_code.code,
                    "description": order.cause_code.description
                } if order.cause_code else None,
                
                "remedy_code": {
                    "id": order.remedy_code.id,
                    "code": order.remedy_code.code,
                    "description": order.remedy_code.description
                } if order.remedy_code else None,
                
                "assigned_to": {
                    "id": order.assigned_to.id,
                    "username": order.assigned_to.username
                } if order.assigned_to else None,
                
                "machine": {
                    "id": order.machine_obj.id,
                    "nombre": order.machine_obj.nombre
                } if order.machine_obj else None,
                
                "section": {
                    "id": order.section.id,
                    "nombre": order.section.nombre
                } if order.section else None,
                
                "line": {
                    "id": order.line.id,
                    "nombre": order.line.nombre
                } if order.line else None,
                
                # TECHNICIANS VACÍO TEMPORALMENTE
                "technicians": []
            }
            result.append(order_dict)
        
        return result
        
    except Exception as e:
        logger.error(f"Error al obtener historial de máquina {machine_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener el historial: {str(e)}"
        )

@router.get("/maquinas/{machine_id}", response_model=MaquinaRead)
def get_machine(
    machine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene los detalles de una máquina específica."""
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Máquina con ID {machine_id} no encontrada")
    return machine
@router.get("/maquinas/{machine_id}")
def get_machine(
    machine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene los detalles de una máquina específica."""
    # Cargar la máquina con todas sus relaciones
    machine = db.query(Machine).options(
        joinedload(Machine.section),
        joinedload(Machine.line)
    ).filter(Machine.id == machine_id).first()
    
    if not machine:
        raise HTTPException(status_code=404, detail=f"Máquina con ID {machine_id} no encontrada")
    
    # Cargar los repuestos asociados
    parts = db.query(MachinePartAssociation).options(
        joinedload(MachinePartAssociation.part)
    ).filter(MachinePartAssociation.machine_id == machine_id).all()
    
    # Crear una respuesta con los datos de la máquina y sus repuestos
    response = {
        "id": machine.id,
        "nombre": machine.nombre,
        "modelo": machine.modelo,
        "marca": machine.marca,
        "numero_serie": machine.numero_serie,
        "line_id": machine.line_id,
        "section_id": machine.section_id,
        "criticidad": machine.criticidad,
        "section": {"id": machine.section.id, "nombre": machine.section.nombre} if machine.section else None,
        "line": {"id": machine.line.id, "nombre": machine.line.nombre} if machine.line else None,
        "parts": [
            {
                "inventory_id": part.inventory_id,
                "quantity": part.quantity,
                "part": {
                    "id": part.part.id,
                    "product_name": part.part.product_name,
                    "quantity": part.part.quantity
                } if part.part else None
            } 
            for part in parts
        ]
    }
    
    return response

