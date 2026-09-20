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


# --- Section lines 10242-12029 ---
# --- ENDPOINTS PARA GESTIÓN DE FORMATOS ---

@router.post("/formats", response_model=FormatRead, status_code=status.HTTP_201_CREATED)
def create_format(
    format_data: FormatCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Solo admin puede crear formatos
):
    """Crea un nuevo formato maestro"""
    # Verificar nombre único
    existing = db.query(Format).filter(Format.name == format_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Ya existe un formato con el nombre '{format_data.name}'")
    
    new_format = Format(**format_data.dict())
    
    try:
        db.add(new_format)
        db.commit()
        db.refresh(new_format)
        
        # Audit trail
        audit_manager.log_action(
            db=db,
            action="CREATE",
            entity=new_format,
            user=current_user,
            request=request,
            notes=f"Formato creado: {new_format.name}"
        )
        db.commit()
        
        return new_format
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando formato: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al crear formato")

@router.get("/formats", response_model=List[FormatRead])
def list_formats(
    active_only: bool = Query(True, description="Solo formatos activos"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista todos los formatos disponibles"""
    query = db.query(Format)
    
    if active_only:
        query = query.filter(Format.active == True)
    
    formats = query.order_by(Format.name).all()
    return formats

@router.get("/formats/global-templates")
def get_global_format_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene formatos que pueden usarse como plantillas para cambios globales"""
    try:
        # Buscar formatos que tengan máquinas asociadas (potenciales plantillas globales)
        formats = db.query(Format).filter(
            Format.active == True,
            Format.machines_requiring_adjustment.isnot(None)
        ).all()
        
        # Filtrar solo los que tienen al menos 2 máquinas (para ser considerados "globales")
        global_templates = []
        for format_obj in formats:
            if (format_obj.machines_requiring_adjustment and 
                isinstance(format_obj.machines_requiring_adjustment, list) and 
                len(format_obj.machines_requiring_adjustment) >= 2):
                
                # Obtener información de las máquinas
                machine_info = []
                for machine_id in format_obj.machines_requiring_adjustment:
                    machine = db.query(Machine).options(
                        joinedload(Machine.line).joinedload(Line.section)
                    ).filter(Machine.id == machine_id).first()
                    
                    if machine:
                        machine_info.append({
                            'id': machine.id,
                            'nombre': machine.nombre,
                            'section': machine.line.section.nombre if machine.line and machine.line.section else 'N/A',
                            'line': machine.line.nombre if machine.line else 'N/A'
                        })
                
                global_templates.append({
                    'id': format_obj.id,
                    'name': format_obj.name,
                    'description': format_obj.description,
                    'estimated_setup_time': format_obj.estimated_setup_time,
                    'machines_count': len(machine_info),
                    'machines_info': machine_info,
                    'sections_involved': len(set(m['section'] for m in machine_info if m['section'] != 'N/A')),
                    'is_truly_global': len(set(m['section'] for m in machine_info if m['section'] != 'N/A')) > 1
                })
        
        return {
            'templates': global_templates,
            'summary': {
                'total_templates': len(global_templates),
                'truly_global_templates': len([t for t in global_templates if t['is_truly_global']])
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo plantillas globales: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener plantillas")

@router.get("/formats/{format_id}", response_model=FormatRead)
def get_format(
    format_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene un formato específico"""
    format_obj = db.query(Format).filter(Format.id == format_id).first()
    if not format_obj:
        raise HTTPException(status_code=404, detail="Formato no encontrado")
    return format_obj

@router.put("/formats/{format_id}", response_model=FormatRead)
def update_format(
    format_id: int,
    format_data: FormatUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Actualiza un formato existente"""
    format_obj = db.query(Format).filter(Format.id == format_id).first()
    if not format_obj:
        raise HTTPException(status_code=404, detail="Formato no encontrado")
    
    # Capturar estado anterior
    old_data = audit_manager.extract_entity_data(format_obj)
    
    update_data = format_data.dict(exclude_unset=True)
    
    # Verificar nombre único si se cambia
    if 'name' in update_data and update_data['name'] != format_obj.name:
        existing = db.query(Format).filter(Format.name == update_data['name']).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Ya existe un formato con el nombre '{update_data['name']}'")
    
    for key, value in update_data.items():
        setattr(format_obj, key, value)
    
    try:
        db.commit()
        db.refresh(format_obj)
        
        # Audit trail
        new_data = audit_manager.extract_entity_data(format_obj)
        audit_manager.log_action(
            db=db,
            action="UPDATE",
            entity=format_obj,
            user=current_user,
            request=request,
            old_data=old_data,
            new_data=new_data,
            notes=f"Formato actualizado: {format_obj.name}"
        )
        db.commit()
        
        return format_obj
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando formato {format_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al actualizar formato")

@router.delete("/formats/{format_id}", status_code=204)
def delete_format(
    format_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Elimina (desactiva) un formato"""
    format_obj = db.query(Format).filter(Format.id == format_id).first()
    if not format_obj:
        raise HTTPException(status_code=404, detail="Formato no encontrado")
    
    # Verificar si está en uso
    orders_using_format = db.query(WorkOrder).filter(
        db.or_(
            WorkOrder.format_from_id == format_id,
            WorkOrder.format_to_id == format_id
        )
    ).first()
    
    if orders_using_format:
        # No eliminar, solo desactivar
        format_obj.active = False
        message = f"Formato desactivado (en uso): {format_obj.name}"
    else:
        # Eliminar completamente
        old_data = audit_manager.extract_entity_data(format_obj)
        format_name = format_obj.name
        db.delete(format_obj)
        message = f"Formato eliminado: {format_name}"
        
        # Audit trail para eliminación
        audit_manager.log_action(
            db=db,
            action="DELETE",
            entity=format_obj,
            user=current_user,
            request=request,
            old_data=old_data,
            notes=message
        )
    
    db.commit()
    return None

# --- ENDPOINTS PARA ÓRDENES DE CAMBIO DE FORMATO ---

@router.post("/work-orders/format-change", response_model=WorkOrderRead)
def create_format_change_order(
    order_data: FormatChangeOrderCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea una orden de trabajo específica para cambio de formato"""
    
    # --- Lógica de validación (ya la tienes, la mantenemos) ---
    if order_data.format_change_type == 'Individual' and not order_data.machine_id:
        raise HTTPException(status_code=400, detail="machine_id es requerido para cambios individuales")
    
    if order_data.format_change_type in ['Línea', 'Global'] and not order_data.affected_machines:
        raise HTTPException(status_code=400, detail="affected_machines es requerido para cambios multi-máquina")

    # --- Creación del diccionario de datos para la BD ---
    # Este diccionario DEBE incluir todos los campos que queremos guardar
    work_order_data = {
        'title': order_data.title,
        'details': order_data.details,
        'work_type': order_data.work_type,
        'section_id': order_data.section_id,
        'line_id': order_data.line_id,
        'machine_id': order_data.machine_id,
        'operator': order_data.operator,
        'assigned_to_id': order_data.assigned_to_id,
        'status': 'Pendiente',
        
        # ✅ Campos de formato que ahora se guardarán correctamente
        'format_change_type': order_data.format_change_type,
        'affected_machines': order_data.affected_machines, # <-- Clave
        'setup_team': order_data.setup_team,             # <-- Clave
        'format_from_id': order_data.format_from_id,
        'format_to_id': order_data.format_to_id,
        'format_from_name': order_data.format_from_name,
        'format_to_name': order_data.format_to_name,
        'estimated_setup_duration': order_data.estimated_setup_duration,
        'setup_notes': order_data.setup_notes
    }
    
    new_order = WorkOrder(**work_order_data)
    
    # Generar número de orden
    latest_order = db.query(WorkOrder).order_by(WorkOrder.id.desc()).first()
    next_number = 1 if not latest_order else latest_order.id + 1
    new_order.order_number = f"FC-{datetime.now().year}-{next_number:05d}"
    
    try:
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        
        # Audit trail
        audit_manager.log_action(
            db=db,
            action="CREATE",
            entity=new_order,
            user=current_user,
            request=request,
            notes=f"Orden de cambio de formato creada: {new_order.title}",
            metadata={
                'format_change_type': order_data.format_change_type,
                'machines_count': len(order_data.affected_machines) if order_data.affected_machines else 1,
                'format_from': order_data.format_from_name,
                'format_to': order_data.format_to_name,
                #'format_from': order.format_from_name,
                #'format_to': order.format_to_name,
                'is_global': order_data.format_change_type == 'Global'
            }
        )
        db.commit()
        
        return new_order
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando orden de cambio de formato: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al crear orden de cambio de formato")

@router.put("/work-orders/{order_id}/format-change")
def update_format_change_order(
    order_id: int,
    update_data: FormatChangeOrderUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza una orden de cambio de formato con datos específicos de setup"""
    
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    if not order.is_format_change:
        raise HTTPException(status_code=400, detail="Esta orden no es un cambio de formato")
    
    # Verificar permisos (similar a órdenes normales)
    can_edit = (
        current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"] or
        (current_user.role.nombre == "Jefe de Sección" and order.section_id == current_user.section_id) or
        (order.assigned_to_id == current_user.id)
    )
    
    if not can_edit:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar esta orden")
    
    # Capturar estado anterior
    old_data = audit_manager.extract_entity_data(order)
    
    update_dict = update_data.dict(exclude_unset=True)
    
    for key, value in update_dict.items():
        setattr(order, key, value)
    
    # Auto-completar finished_at si se cierra
    if update_data.status == "Cerrada" and order.finished_at is None:
        order.finished_at = datetime.utcnow()
    
    try:
        # Commit de los cambios en la orden
        db.commit() 
        
        # Lógica de Audit Trail (esto ya lo tienes)
        new_data = audit_manager.extract_entity_data(order)
        audit_manager.log_action(
            db=db,
            action="UPDATE" if update_data.status != "Cerrada" else "COMPLETE",
            entity=order,
            user=current_user,
            request=request,
            old_data=old_data,
            new_data=new_data,
            notes=f"Orden de cambio de formato actualizada: {order.title}",
            metadata={
                'setup_duration': order.setup_duration,
                'production_loss': order.production_loss_hours,
                'efficiency': order.setup_efficiency
            }
        )
        db.commit() # Commit final para el log de auditoría

        # === SOLUCIÓN FINAL: Re-consultar y construir la respuesta manualmente ===
        
        # 1. Re-consultamos para obtener un objeto limpio con todas las relaciones cargadas
        fresh_order = db.query(WorkOrder).options(
            joinedload(WorkOrder.technicians).joinedload(WorkOrderTechnician.technician),
            joinedload(WorkOrder.assigned_to),
            joinedload(WorkOrder.machine_obj),
            joinedload(WorkOrder.section),
            joinedload(WorkOrder.line),
            joinedload(WorkOrder.repuesto),
            joinedload(WorkOrder.failure_code),
            joinedload(WorkOrder.cause_code),
            joinedload(WorkOrder.remedy_code),
            joinedload(WorkOrder.format_from_obj),
            joinedload(WorkOrder.format_to_obj)
        ).filter(WorkOrder.id == order_id).one()

        # 2. Construimos la lista de técnicos "a mano"
        technicians_list = []
        if fresh_order.technicians:
            for tech_assignment in fresh_order.technicians:
                technician_info = None
                if tech_assignment.technician:
                    technician_info = {
                        "id": tech_assignment.technician.id,
                        "username": tech_assignment.technician.username
                    }
                
                technicians_list.append({
                    "id": tech_assignment.id,
                    "work_order_id": tech_assignment.work_order_id,
                    "user_id": tech_assignment.user_id,
                    "role": tech_assignment.role,
                    "hours_worked": tech_assignment.hours_worked,
                    "notes": tech_assignment.notes,
                    "is_active": tech_assignment.is_active,
                    "assigned_at": tech_assignment.assigned_at,
                    "assigned_by_id": tech_assignment.assigned_by_id,
                    "technician": technician_info
                })

        # 3. Construimos el diccionario de respuesta completo
        response_dict = {
            "id": fresh_order.id,
            "order_number": fresh_order.order_number,
            "title": fresh_order.title,
            "details": fresh_order.details,
            "work_type": fresh_order.work_type,
            "status": fresh_order.status,
            "operator": fresh_order.operator,
            "created_at": fresh_order.created_at,
            "finished_at": fresh_order.finished_at,
            "section_id": fresh_order.section_id,
            "line_id": fresh_order.line_id,
            "machine_id": fresh_order.machine_id,
            "assigned_to_id": fresh_order.assigned_to_id,
            "format_change_type": fresh_order.format_change_type,
            "affected_machines": fresh_order.affected_machines,
            "setup_team": fresh_order.setup_team,
            "format_from_id": fresh_order.format_from_id,
            "format_to_id": fresh_order.format_to_id,
            "format_from_name": fresh_order.format_from_name,
            "format_to_name": fresh_order.format_to_name,
            "estimated_setup_duration": fresh_order.estimated_setup_duration,
            "setup_duration": fresh_order.setup_duration,
            "production_loss_hours": fresh_order.production_loss_hours,
            "setup_notes": fresh_order.setup_notes,
            # Relaciones
            "assigned_to": {"id": fresh_order.assigned_to.id, "username": fresh_order.assigned_to.username} if fresh_order.assigned_to else None,
            "machine": {"id": fresh_order.machine_obj.id, "nombre": fresh_order.machine_obj.nombre} if fresh_order.machine_obj else None,
            "machine_obj": {"id": fresh_order.machine_obj.id, "nombre": fresh_order.machine_obj.nombre} if fresh_order.machine_obj else None,
            "section": {"id": fresh_order.section.id, "nombre": fresh_order.section.nombre} if fresh_order.section else None,
            "line": {"id": fresh_order.line.id, "nombre": fresh_order.line.nombre} if fresh_order.line else None,
            "repuesto": {"id": fresh_order.repuesto.id, "product_name": fresh_order.repuesto.product_name} if fresh_order.repuesto else None,
            # Lista de técnicos construida manualmente
            "technicians": technicians_list
        }
        
        # 4. Devolvemos el diccionario, que FastAPI puede convertir a JSON sin problemas
        return response_dict

    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando orden de cambio de formato {order_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al procesar la actualización: {str(e)}")







# --- ENDPOINTS PARA REPORTES DE CAMBIOS DE FORMATO ---

@router.get("/reports/format-changes/summary")
def get_format_changes_summary(
    start_date: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    format_change_type: Optional[str] = Query(None, description="Tipo de cambio"),
    section_id: Optional[int] = Query(None, description="Filtrar por sección"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reporte resumen de cambios de formato"""
    
    # Filtros por rol
    query = db.query(WorkOrder).filter(
        WorkOrder.work_type.in_(['Cambio de Formato', 'Setup de Línea', 'Cambio Global de Planta'])
    )
    
    if current_user.role.nombre == "Jefe de Sección":
        query = query.filter(WorkOrder.section_id == current_user.section_id)
    elif section_id:
        query = query.filter(WorkOrder.section_id == section_id)
    
    # Filtros de fecha
    if start_date:
        query = query.filter(WorkOrder.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(WorkOrder.created_at <= datetime.combine(end_date, datetime.max.time()))
    
    # Filtro por tipo
    if format_change_type:
        query = query.filter(WorkOrder.format_change_type == format_change_type)
    
    orders = query.all()
    
    # Calcular métricas
    total_orders = len(orders)
    completed_orders = [o for o in orders if o.status == 'Cerrada']
    
    total_setup_time = sum(o.setup_duration for o in completed_orders if o.setup_duration)
    total_estimated_time = sum(o.estimated_setup_duration for o in completed_orders if o.estimated_setup_duration)
    total_production_loss = sum(o.production_loss_hours for o in completed_orders if o.production_loss_hours)
    
    avg_efficiency = None
    if completed_orders:
        efficiencies = [o.setup_efficiency for o in completed_orders if o.setup_efficiency]
        if efficiencies:
            avg_efficiency = sum(efficiencies) / len(efficiencies)
    
    # Agrupar por tipo de cambio
    by_type = {}
    for order in orders:
        change_type = order.format_change_type or 'Sin especificar'
        if change_type not in by_type:
            by_type[change_type] = {'count': 0, 'completed': 0, 'avg_duration': 0}
        
        by_type[change_type]['count'] += 1
        if order.status == 'Cerrada':
            by_type[change_type]['completed'] += 1
            if order.setup_duration:
                current_avg = by_type[change_type]['avg_duration']
                by_type[change_type]['avg_duration'] = (current_avg + order.setup_duration) / 2
    
    # Top cambios más frecuentes
    format_combinations = {}
    for order in completed_orders:
        if order.format_from_name and order.format_to_name:
            key = f"{order.format_from_name} → {order.format_to_name}"
            if key not in format_combinations:
                format_combinations[key] = {'count': 0, 'avg_duration': 0, 'total_duration': 0}
            
            format_combinations[key]['count'] += 1
            if order.setup_duration:
                format_combinations[key]['total_duration'] += order.setup_duration
                format_combinations[key]['avg_duration'] = format_combinations[key]['total_duration'] / format_combinations[key]['count']
    
    top_combinations = sorted(
        format_combinations.items(), 
        key=lambda x: x[1]['count'], 
        reverse=True
    )[:10]
    
    return {
        'period': {
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None
        },
        'summary': {
            'total_orders': total_orders,
            'completed_orders': len(completed_orders),
            'completion_rate': len(completed_orders) / total_orders * 100 if total_orders > 0 else 0,
            'total_setup_hours': round(total_setup_time, 2),
            'total_estimated_hours': round(total_estimated_time, 2),
            'total_production_loss_hours': round(total_production_loss, 2),
            'average_efficiency': round(avg_efficiency, 2) if avg_efficiency else None
        },
        'by_type': by_type,
        'top_format_combinations': [
            {
                'combination': combination,
                'count': data['count'],
                'avg_duration_hours': round(data['avg_duration'], 2)
            }
            for combination, data in top_combinations
        ]
    }

@router.get("/reports/format-changes/efficiency")
def get_format_changes_efficiency(
    limit: int = Query(20, le=100, description="Número máximo de registros"),
    sort_by: str = Query("efficiency", description="Ordenar por: efficiency, duration, date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reporte de eficiencia de cambios de formato"""
    
    query = db.query(WorkOrder).filter(
        WorkOrder.work_type.in_(['Cambio de Formato', 'Setup de Línea', 'Cambio Global de Planta']),
        WorkOrder.status == 'Cerrada',
        WorkOrder.setup_duration.isnot(None),
        WorkOrder.estimated_setup_duration.isnot(None)
    )
    
    if current_user.role.nombre == "Jefe de Sección":
        query = query.filter(WorkOrder.section_id == current_user.section_id)
    
    orders = query.all()
    
    # Calcular eficiencias y preparar datos
    efficiency_data = []
    for order in orders:
        if order.setup_efficiency:
            efficiency_data.append({
                'order_id': order.id,
                'order_number': order.order_number,
                'title': order.title,
                'format_change_type': order.format_change_type,
                'format_from': order.format_from_name or (order.format_from_obj.name if order.format_from_obj else None),
                'format_to': order.format_to_name or (order.format_to_obj.name if order.format_to_obj else None),
                'estimated_duration': order.estimated_setup_duration,
                'actual_duration': order.setup_duration,
                'efficiency': round(order.setup_efficiency, 2),
                'production_loss': order.production_loss_hours,
                'finished_at': order.finished_at.isoformat() if order.finished_at else None,
                'section': order.section.nombre if order.section else None,
                'assigned_to': order.assigned_to.username if order.assigned_to else None
            })
    
    # Ordenar según parámetro
    if sort_by == "efficiency":
        efficiency_data.sort(key=lambda x: x['efficiency'], reverse=True)
    elif sort_by == "duration":
        efficiency_data.sort(key=lambda x: x['actual_duration'])
    elif sort_by == "date":
        efficiency_data.sort(key=lambda x: x['finished_at'] or '', reverse=True)
    
    return {
        'data': efficiency_data[:limit],
        'statistics': {
            'total_analyzed': len(efficiency_data),
            'avg_efficiency': round(sum(d['efficiency'] for d in efficiency_data) / len(efficiency_data), 2) if efficiency_data else 0,
            'best_efficiency': max(efficiency_data, key=lambda x: x['efficiency']) if efficiency_data else None,
            'worst_efficiency': min(efficiency_data, key=lambda x: x['efficiency']) if efficiency_data else None,
            'total_time_saved': sum(d['estimated_duration'] - d['actual_duration'] for d in efficiency_data if d['efficiency'] > 100),
            'total_time_lost': sum(d['actual_duration'] - d['estimated_duration'] for d in efficiency_data if d['efficiency'] < 100)
        }
    }

@router.get("/dashboard/format-changes")
def get_format_changes_dashboard(
    days: int = Query(30, ge=1, le=365, description="Días hacia atrás para análisis"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dashboard específico para cambios de formato"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(WorkOrder).filter(
        WorkOrder.work_type.in_(['Cambio de Formato', 'Setup de Línea', 'Cambio Global de Planta']),
        WorkOrder.created_at >= start_date
    )
    
    if current_user.role.nombre == "Jefe de Sección":
        query = query.filter(WorkOrder.section_id == current_user.section_id)
    
    orders = query.all()
    completed_orders = [o for o in orders if o.status == 'Cerrada']
    
    # KPIs principales
    total_changes = len(orders)
    global_changes = len([o for o in orders if o.format_change_type == 'Global'])
    line_changes = len([o for o in orders if o.format_change_type == 'Línea'])
    individual_changes = len([o for o in orders if o.format_change_type == 'Individual'])
    
    # Métricas de tiempo
    avg_setup_time = {}
    for change_type in ['Global', 'Línea', 'Individual']:
        type_orders = [o for o in completed_orders if o.format_change_type == change_type and o.setup_duration]
        if type_orders:
            avg_setup_time[change_type] = sum(o.setup_duration for o in type_orders) / len(type_orders)
        else:
            avg_setup_time[change_type] = 0
    
    # Eficiencia general
    efficiency_orders = [o for o in completed_orders if o.setup_efficiency]
    avg_efficiency = sum(o.setup_efficiency for o in efficiency_orders) / len(efficiency_orders) if efficiency_orders else 0
    
    # Tendencia por semana
    weekly_data = {}
    for order in orders:
        week_start = order.created_at.date() - timedelta(days=order.created_at.weekday())
        week_key = week_start.isoformat()
        
        if week_key not in weekly_data:
            weekly_data[week_key] = {'total': 0, 'completed': 0, 'setup_hours': 0}
        
        weekly_data[week_key]['total'] += 1
        if order.status == 'Cerrada':
            weekly_data[week_key]['completed'] += 1
            if order.setup_duration:
                weekly_data[week_key]['setup_hours'] += order.setup_duration
    
    # Convertir a lista ordenada
    weekly_trend = []
    for week, data in sorted(weekly_data.items()):
        weekly_trend.append({
            'week': week,
            'total_changes': data['total'],
            'completed_changes': data['completed'],
            'total_setup_hours': round(data['setup_hours'], 2)
        })
    
    return {
        'period_days': days,
        'kpis': {
            'total_changes': total_changes,
            'global_changes': global_changes,
            'line_changes': line_changes,
            'individual_changes': individual_changes,
            'completion_rate': round(len(completed_orders) / total_changes * 100, 1) if total_changes > 0 else 0,
            'average_efficiency': round(avg_efficiency, 1)
        },
        'average_setup_times': {
            'global_hours': round(avg_setup_time['Global'], 2),
            'line_hours': round(avg_setup_time['Línea'], 2),
            'individual_hours': round(avg_setup_time['Individual'], 2)
        },
        'weekly_trend': weekly_trend[-8:],  # Últimas 8 semanas
        'total_production_loss': round(sum(o.production_loss_hours for o in completed_orders if o.production_loss_hours), 2),
        'most_frequent_changes': [
            {
                'combination': f"{o.format_from_name} → {o.format_to_name}",
                'count': len([x for x in completed_orders if x.format_from_name == o.format_from_name and x.format_to_name == o.format_to_name])
            }
            for o in completed_orders if o.format_from_name and o.format_to_name
        ][:5]
    }

@router.get("/work-orders/{work_order_id}/checklist-data")
def get_work_order_checklist_data(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene los datos necesarios para mostrar el checklist de una orden de trabajo.
    Incluye la TaskList y el progreso guardado si existe.
    """
    try:
        # Buscar la orden de trabajo
        work_order = db.query(WorkOrder).options(
            joinedload(WorkOrder.machine_obj),
            joinedload(WorkOrder.assigned_to)
        ).filter(WorkOrder.id == work_order_id).first()
        
        if not work_order:
            raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
        
        # Verificar permisos
        can_access = (
            current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"] or
            (current_user.role.nombre == "Jefe de Sección" and work_order.section_id == current_user.section_id) or
            work_order.assigned_to_id == current_user.id
        )
        
        if not can_access:
            raise HTTPException(status_code=403, detail="No tienes permisos para acceder a esta orden")
        
        response_data = {
            "work_order": {
                "id": work_order.id,
                "order_number": work_order.order_number,
                "title": work_order.title,
                "status": work_order.status,
                "work_type": work_order.work_type,
                "machine_name": work_order.machine_obj.nombre if work_order.machine_obj else None,
                "assigned_to": work_order.assigned_to.username if work_order.assigned_to else None
            },
            "task_list": None,
            "has_checklist": False,
            "existing_progress": None
        }
        
        # Buscar TaskList asociada
        task_list = None
        
        # Método 1: Si es preventivo, buscar por mantenimiento
        if work_order.work_type == "Preventivo":
            maintenance = db.query(Maintenance).filter(
                Maintenance.generated_order_id == work_order_id
            ).first()
            
            if maintenance and maintenance.task_list_id:
                task_list = db.query(TaskList).options(
                    joinedload(TaskList.steps)
                ).filter(TaskList.id == maintenance.task_list_id).first()
        
        if task_list:
            response_data["has_checklist"] = True
            response_data["task_list"] = {
                "id": task_list.id,
                "name": task_list.name,
                "description": task_list.description,
                "applies_to_type": task_list.applies_to_type,
                "steps": [
                    {
                        "id": step.id,
                        "step_order": step.step_order,
                        "description": step.description,
                        "estimated_time_minutes": step.estimated_time_minutes
                    }
                    for step in sorted(task_list.steps, key=lambda x: x.step_order)
                ]
            }
            
            # Buscar progreso existente
            from src.models.checklist_progress import ChecklistProgress
            existing_progress = db.query(ChecklistProgress).filter(
                ChecklistProgress.work_order_id == work_order_id,
                ChecklistProgress.task_list_id == task_list.id
            ).first()
            
            if existing_progress:
                response_data["existing_progress"] = {
                    "id": existing_progress.id,
                    "steps_progress": existing_progress.steps_progress,
                    "total_elapsed_time": existing_progress.total_elapsed_time,
                    "progress_percent": existing_progress.progress_percent,
                    "is_completed": existing_progress.is_completed,
                    "updated_at": existing_progress.updated_at.isoformat()
                }
        
        return response_data
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error obteniendo datos de checklist para orden {work_order_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/work-orders/{work_order_id}/checklist-progress", response_model=ChecklistProgressRead)
def create_checklist_progress(
    work_order_id: int,
    progress_data: ChecklistProgressCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea o actualiza el progreso del checklist para una orden de trabajo."""
    try:
        # Verificar que la orden existe
        work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not work_order:
            raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
        
        # Verificar permisos de edición
        can_edit = (
            current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"] or
            (current_user.role.nombre == "Jefe de Sección" and work_order.section_id == current_user.section_id) or
            work_order.assigned_to_id == current_user.id
        )
        
        if not can_edit:
            raise HTTPException(status_code=403, detail="No tienes permisos para editar esta orden")
        
        # Verificar que la TaskList existe
        task_list = db.query(TaskList).filter(TaskList.id == progress_data.task_list_id).first()
        if not task_list:
            raise HTTPException(status_code=404, detail="Lista de tareas no encontrada")
        
        from src.models.checklist_progress import ChecklistProgress
        
        # Buscar progreso existente
        existing_progress = db.query(ChecklistProgress).filter(
            ChecklistProgress.work_order_id == work_order_id,
            ChecklistProgress.task_list_id == progress_data.task_list_id
        ).first()
        
        if existing_progress:
            # Actualizar existente
            existing_progress.steps_progress = [step.dict() for step in progress_data.steps_progress]
            existing_progress.total_elapsed_time = progress_data.total_elapsed_time
            existing_progress.progress_percent = progress_data.progress_percent
            existing_progress.extra_data = progress_data.extra_data
            existing_progress.updated_at = datetime.utcnow()
            
            # Verificar si está completado
            completed_steps = sum(1 for step in progress_data.steps_progress if step.completed)
            total_steps = len(progress_data.steps_progress)
            existing_progress.is_completed = completed_steps == total_steps and total_steps > 0
            
            checklist_progress = existing_progress
        else:
            # Crear nuevo
            checklist_progress = ChecklistProgress(
                work_order_id=work_order_id,
                task_list_id=progress_data.task_list_id,
                steps_progress=[step.dict() for step in progress_data.steps_progress],
                total_elapsed_time=progress_data.total_elapsed_time,
                progress_percent=progress_data.progress_percent,
                extra_data=progress_data.extra_data,
                created_by_id=current_user.id
            )
            
            # Verificar si está completado
            completed_steps = sum(1 for step in progress_data.steps_progress if step.completed)
            total_steps = len(progress_data.steps_progress)
            checklist_progress.is_completed = completed_steps == total_steps and total_steps > 0
            
            db.add(checklist_progress)
        
        db.commit()
        db.refresh(checklist_progress)
        """
        # 🔧 ASIGNAR AL USUARIO DEL TURNO ACTUAL SI NO ESTÁ ASIGNADA
        if not work_order.assigned_to_id:
            # Obtener usuario del turno actual
            current_shift_user = get_current_shift_user(db, work_order.section_id)
            if current_shift_user:
                work_order.assigned_to_id = current_shift_user.id
                logger.info(f"Orden {work_order.order_number} asignada automáticamente al usuario del turno: {current_shift_user.username}")
        """
        
        # Audit trail
        audit_manager.log_action(
            db=db,
            action="UPDATE" if existing_progress else "CREATE",
            entity=checklist_progress,
            user=current_user,
            request=request,
            notes=f"Progreso de checklist {'actualizado' if existing_progress else 'creado'} para orden {work_order.order_number}",
            metadata={
                "progress_percent": checklist_progress.progress_percent,
                "is_completed": checklist_progress.is_completed,
                "total_elapsed_time": checklist_progress.total_elapsed_time
            }
        )
        db.commit()
        
        return checklist_progress
        
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logger.error(f"Error guardando progreso de checklist: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.put("/checklist-progress/{progress_id}", response_model=ChecklistProgressRead)
def update_checklist_progress(
    progress_id: int,
    progress_data: ChecklistProgressUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza el progreso de un checklist específico."""
    try:
        from src.models.checklist_progress import ChecklistProgress
        
        checklist_progress = db.query(ChecklistProgress).filter(
            ChecklistProgress.id == progress_id
        ).first()
        
        if not checklist_progress:
            raise HTTPException(status_code=404, detail="Progreso de checklist no encontrado")
        
        # Verificar permisos
        work_order = db.query(WorkOrder).filter(WorkOrder.id == checklist_progress.work_order_id).first()
        can_edit = (
            current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"] or
            (current_user.role.nombre == "Jefe de Sección" and work_order.section_id == current_user.section_id) or
            work_order.assigned_to_id == current_user.id
        )
        
        if not can_edit:
            raise HTTPException(status_code=403, detail="No tienes permisos para editar este checklist")
        
        # Actualizar campos
        update_data = progress_data.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            if key == "steps_progress" and value is not None:
                setattr(checklist_progress, key, [step.dict() if hasattr(step, 'dict') else step for step in value])
            else:
                setattr(checklist_progress, key, value)
        
        checklist_progress.updated_at = datetime.utcnow()
        
        # Auto-detectar completado si no se especifica
        if "is_completed" not in update_data and checklist_progress.steps_progress:
            completed_steps = sum(1 for step in checklist_progress.steps_progress if step.get('completed', False))
            total_steps = len(checklist_progress.steps_progress)
            checklist_progress.is_completed = completed_steps == total_steps and total_steps > 0
        
        db.commit()
        db.refresh(checklist_progress)
        
        # Audit trail
        audit_manager.log_action(
            db=db,
            action="UPDATE" if existing_progress else "CREATE",
            entity=checklist_progress,
            user=current_user,
            request=request,
            notes=f"Progreso de checklist {'actualizado' if existing_progress else 'creado'} para orden {work_order.order_number}",
            metadata={  # ← A ESTO
                "progress_percent": checklist_progress.progress_percent,
                "is_completed": checklist_progress.is_completed,
                "total_elapsed_time": checklist_progress.total_elapsed_time
            }
        )
        db.commit()
        
        return checklist_progress
        
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando progreso de checklist {progress_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/checklist-progress/{progress_id}", response_model=ChecklistProgressRead)
def get_checklist_progress(
    progress_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene el progreso de un checklist específico."""
    try:
        from src.models.checklist_progress import ChecklistProgress
        
        checklist_progress = db.query(ChecklistProgress).filter(
            ChecklistProgress.id == progress_id
        ).first()
        
        if not checklist_progress:
            raise HTTPException(status_code=404, detail="Progreso de checklist no encontrado")
        
        # Verificar permisos de lectura
        work_order = db.query(WorkOrder).filter(WorkOrder.id == checklist_progress.work_order_id).first()
        can_view = (
            current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"] or
            (current_user.role.nombre == "Jefe de Sección" and work_order.section_id == current_user.section_id) or
            work_order.assigned_to_id == current_user.id
        )
        
        if not can_view:
            raise HTTPException(status_code=403, detail="No tienes permisos para ver este checklist")
        
        return checklist_progress
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error obteniendo progreso de checklist {progress_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.delete("/checklist-progress/{progress_id}", status_code=204)
def delete_checklist_progress(
    progress_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Solo admin puede eliminar
):
    """Elimina el progreso de un checklist."""
    try:
        from src.models.checklist_progress import ChecklistProgress
        
        checklist_progress = db.query(ChecklistProgress).filter(
            ChecklistProgress.id == progress_id
        ).first()
        
        if not checklist_progress:
            raise HTTPException(status_code=404, detail="Progreso de checklist no encontrado")
        
        # Capturar datos para audit
        work_order = db.query(WorkOrder).filter(WorkOrder.id == checklist_progress.work_order_id).first()
        old_data = {
            "progress_id": checklist_progress.id,
            "work_order_id": checklist_progress.work_order_id,
            "progress_percent": checklist_progress.progress_percent,
            "is_completed": checklist_progress.is_completed
        }
        
        db.delete(checklist_progress)
        
        # Audit trail
        audit_manager.log_action(
            db=db,
            action="DELETE",
            entity=checklist_progress,
            user=current_user,
            request=request,
            old_data=old_data,
            notes=f"Progreso de checklist eliminado para orden {work_order.order_number if work_order else 'N/A'}"
        )
        
        db.commit()
        return None
        
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando progreso de checklist {progress_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/work-orders/{work_order_id}/checklist-export")
def export_checklist_data(
    work_order_id: int,
    format: str = Query("json", description="Formato de exportación: json, pdf"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Exporta los datos del checklist en diferentes formatos."""
    try:
        # Verificar que la orden existe y permisos
        work_order = db.query(WorkOrder).options(
            joinedload(WorkOrder.machine_obj),
            joinedload(WorkOrder.assigned_to)
        ).filter(WorkOrder.id == work_order_id).first()
        
        if not work_order:
            raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
        
        can_access = (
            current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"] or
            (current_user.role.nombre == "Jefe de Sección" and work_order.section_id == current_user.section_id) or
            work_order.assigned_to_id == current_user.id
        )
        
        if not can_access:
            raise HTTPException(status_code=403, detail="No tienes permisos para exportar este checklist")
        
        # Buscar progreso del checklist
        from src.models.checklist_progress import ChecklistProgress
        checklist_progress = db.query(ChecklistProgress).filter(
            ChecklistProgress.work_order_id == work_order_id
        ).first()
        
        if not checklist_progress:
            raise HTTPException(status_code=404, detail="No hay progreso de checklist para esta orden")
        
        # Obtener TaskList
        task_list = db.query(TaskList).options(
            joinedload(TaskList.steps)
        ).filter(TaskList.id == checklist_progress.task_list_id).first()
        
        # Construir datos de exportación
        export_data = {
            "export_info": {
                "generated_at": datetime.utcnow().isoformat(),
                "generated_by": current_user.username,
                "format": format
            },
            "work_order": {
                "id": work_order.id,
                "order_number": work_order.order_number,
                "title": work_order.title,
                "status": work_order.status,
                "work_type": work_order.work_type,
                "machine_name": work_order.machine_obj.nombre if work_order.machine_obj else None,
                "assigned_to": work_order.assigned_to.username if work_order.assigned_to else None,
                "created_at": work_order.created_at.isoformat()
            },
            "task_list": {
                "id": task_list.id,
                "name": task_list.name,
                "description": task_list.description
            } if task_list else None,
            "checklist_progress": {
                "total_elapsed_time": checklist_progress.total_elapsed_time,
                "progress_percent": checklist_progress.progress_percent,
                "is_completed": checklist_progress.is_completed,
                "started_at": checklist_progress.created_at.isoformat(),
                "last_updated": checklist_progress.updated_at.isoformat()
            },
            "steps": []
        }
        
        # Añadir detalles de pasos
        if task_list and task_list.steps:
            steps_progress_dict = {sp['step_id']: sp for sp in checklist_progress.steps_progress}
            
            for step in sorted(task_list.steps, key=lambda x: x.step_order):
                step_progress = steps_progress_dict.get(step.id, {})
                
                export_data["steps"].append({
                    "step_order": step.step_order,
                    "description": step.description,
                    "estimated_time_minutes": step.estimated_time_minutes,
                    "actual_time_minutes": step_progress.get('actual_time_minutes'),
                    "completed": step_progress.get('completed', False),
                    "notes": step_progress.get('notes'),
                    "started_at": step_progress.get('started_at'),
                    "completed_at": step_progress.get('completed_at')
                })
        
        if format == "json":
            return export_data
        else:
            # Para futuros formatos (PDF, Excel, etc.)
            raise HTTPException(status_code=400, detail=f"Formato '{format}' no soportado")
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error exportando checklist para orden {work_order_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# =============================================================================
# ENDPOINT PARA ESTADÍSTICAS DE CHECKLIST (opcional)
# =============================================================================

@router.get("/checklist-progress/stats")
def get_checklist_stats(
    days: int = Query(30, ge=1, le=365, description="Días hacia atrás para estadísticas"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene estadísticas de uso del sistema de checklist."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        from src.models.checklist_progress import ChecklistProgress
        
        # Filtro por rol
        query = db.query(ChecklistProgress).filter(
            ChecklistProgress.created_at >= start_date
        )
        
        if current_user.role.nombre == "Jefe de Sección":
            # Solo checklists de su sección
            query = query.join(WorkOrder).filter(WorkOrder.section_id == current_user.section_id)
        elif current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
            # Solo sus propios checklists
            query = query.filter(ChecklistProgress.created_by_id == current_user.id)
        
        all_progress = query.all()
        
        # Calcular estadísticas
        total_checklists = len(all_progress)
        completed_checklists = len([p for p in all_progress if p.is_completed])
        completion_rate = (completed_checklists / total_checklists * 100) if total_checklists > 0 else 0
        
        # Tiempo promedio
        completed_with_time = [p for p in all_progress if p.is_completed and p.total_elapsed_time > 0]
        avg_completion_time = (
            sum(p.total_elapsed_time for p in completed_with_time) / len(completed_with_time)
        ) if completed_with_time else 0
        
        # Distribución por progreso
        progress_distribution = {
            "0-25%": len([p for p in all_progress if 0 <= p.progress_percent < 25]),
            "25-50%": len([p for p in all_progress if 25 <= p.progress_percent < 50]),
            "50-75%": len([p for p in all_progress if 50 <= p.progress_percent < 75]),
            "75-100%": len([p for p in all_progress if 75 <= p.progress_percent < 100]),
            "100%": completed_checklists
        }
        
        return {
            "period_days": days,
            "total_checklists": total_checklists,
            "completed_checklists": completed_checklists,
            "completion_rate": round(completion_rate, 1),
            "average_completion_time_minutes": round(avg_completion_time, 1),
            "progress_distribution": progress_distribution,
            "summary": {
                "most_active_day": "Por implementar",
                "efficiency_trend": "Por implementar"
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de checklist: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/audit-trail-fixed", response_model=List[AuditLogResponse])
def get_audit_trail_fixed(
    limit: int = Query(50, le=500, description="Número máximo de registros"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir"),
    entity_type: Optional[str] = Query(None, description="Filtrar por tipo de entidad"),
    action: Optional[str] = Query(None, description="Filtrar por tipo de acción"),
    module: Optional[str] = Query(None, description="Filtrar por módulo"),
    severity: Optional[str] = Query(None, description="Filtrar por severidad"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el historial de audit trail con timestamps corregidos para zona horaria.
    """
    try:
        # Verificar permisos
        is_admin = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
        
        # Construir query base
        query = db.query(AuditLog)
        
        # Filtrar por usuario si no es admin
        if not is_admin:
            query = query.filter(AuditLog.user_id == current_user.id)
        
        # Aplicar filtros opcionales
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if module:
            query = query.filter(AuditLog.module == module)
        
        if severity:
            query = query.filter(AuditLog.severity == severity)
        
        # Ordenar por timestamp descendente (más recientes primero)
        query = query.order_by(AuditLog.timestamp.desc())
        
        # Aplicar paginación
        results = query.offset(offset).limit(limit).all()
        
        # Convertir usando nuestro serializador personalizado
        formatted_results = [
            AuditLogResponse.from_orm_audit_log(audit_log)
            for audit_log in results
        ]
        
        return formatted_results
    
    except Exception as e:
        logger.error(f"Error en get_audit_trail_fixed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    

# AGREGAR ESTE ENDPOINT TEMPORAL AL FINAL DE routes.py PARA DEBUG

@router.get("/debug/current-shift-user")
def debug_current_shift_user(
    section_id: Optional[int] = Query(None, description="ID de la sección"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint de debug para ver qué usuario devuelve get_current_shift_user()"""
    try:
        logger.info("🔍 INICIANDO DEBUG DE TURNO ACTUAL")
        
        # Probar la función
        shift_user = get_current_shift_user(db, section_id)
        
        if shift_user:
            return {
                "success": True,
                "current_shift_user": {
                    "id": shift_user.id,
                    "username": shift_user.username,
                    "section_id": shift_user.section_id
                },
                "debug_info": {
                    "section_filter": section_id,
                    "current_time": datetime.now().strftime("%H:%M:%S"),
                    "current_date": datetime.now().date().isoformat()
                }
            }
        else:
            return {
                "success": False,
                "current_shift_user": None,
                "message": "No se encontró usuario en turno actual",
                "debug_info": {
                    "section_filter": section_id,
                    "current_time": datetime.now().strftime("%H:%M:%S"),
                    "current_date": datetime.now().date().isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"💥 Error en debug: {e}")
        return {
            "success": False,
            "error": str(e),
            "debug_info": {
                "section_filter": section_id,
                "current_time": datetime.now().strftime("%H:%M:%S"),
                "current_date": datetime.now().date().isoformat()
            }
        }

@router.post("/vacaciones/{vacation_id}/mark-notified")
async def mark_vacation_as_notified(
    vacation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return {"success": True, "message": "Notificación marcada como vista"}
    except Exception as e:
        logger.error(f"Error marking vacation notification: {e}")
        return {"success": False, "message": "Error al marcar notificación"}
    

@router.post("/ordenes/{order_id}/technicians")
def add_technician_to_work_order(
    order_id: int,
    technician_data: WorkOrderTechnicianCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Añade un técnico a una orden de trabajo"""
    
    # Verificar que la orden existe
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    # ✅ NUEVA LÓGICA DE PERMISOS EXPANDIDA
    can_edit = False
    
    # Admin y Jefe de Mantenimiento siempre pueden
    if current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]:
        can_edit = True
    
    # Jefe de Sección puede en su sección
    elif current_user.role.nombre == "Jefe de Sección" and order.section_id == current_user.section_id:
        can_edit = True
    
    # ✅ MECÁNICOS: Pueden gestionar técnicos SI son técnico principal de la orden
    elif current_user.role.nombre == "Mecánico":
        # Verificar si es técnico principal en la orden
        principal_assignment = db.query(WorkOrderTechnician).filter(
            WorkOrderTechnician.work_order_id == order_id,
            WorkOrderTechnician.user_id == current_user.id,
            WorkOrderTechnician.role == "principal",
            WorkOrderTechnician.is_active == True
        ).first()
        
        # También verificar si es el técnico asignado en el campo legacy
        is_assigned_legacy = order.assigned_to_id == current_user.id
        
        can_edit = principal_assignment is not None or is_assigned_legacy
    
    if not can_edit:
        raise HTTPException(
            status_code=403, 
            detail="No tienes permisos para gestionar técnicos en esta orden. Los mecánicos deben ser técnico principal para gestionar el equipo."
        )
    
    # ⭐ VALIDAR QUE YA NO ESTÉ ASIGNADO
    existing = db.query(WorkOrderTechnician).filter(
        WorkOrderTechnician.work_order_id == order_id,
        WorkOrderTechnician.user_id == technician_data.user_id,
        WorkOrderTechnician.is_active == True
    ).first()
    
    if existing:
        return {
            "message": "El técnico ya está asignado",
            "assignment": {
                "id": existing.id,
                "user_id": existing.user_id,
                "role": existing.role,
                "technician": {
                    "id": existing.technician.id,
                    "username": existing.technician.username
                } if existing.technician else None
            },
            "technicians": get_order_technicians(db, order_id)
        }
    
    # ⭐ CREAR NUEVA ASIGNACIÓN SI NO EXISTE
    # Verificar que el usuario existe y está activo
    user = db.query(User).filter(User.id == technician_data.user_id, User.active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o inactivo")
    
    # Si es principal, cambiar el principal anterior a apoyo
    if technician_data.role == "principal":
        existing_principal = db.query(WorkOrderTechnician).filter(
            WorkOrderTechnician.work_order_id == order_id,
            WorkOrderTechnician.role == "principal",
            WorkOrderTechnician.is_active == True
        ).first()
        
        if existing_principal:
            existing_principal.role = "apoyo"
    
    # Crear la nueva asignación
    assignment = WorkOrderTechnician(
        work_order_id=order_id,
        user_id=technician_data.user_id,
        role=technician_data.role,
        assigned_at=datetime.utcnow(),
        assigned_by_id=current_user.id,
        notes=technician_data.notes,
        hours_worked=0.0,
        is_active=True
    )
    
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    # Cargar la relación del técnico
    assignment = db.query(WorkOrderTechnician).options(
        joinedload(WorkOrderTechnician.technician)
    ).filter(WorkOrderTechnician.id == assignment.id).first()
    
    return {
        "message": "Técnico añadido correctamente",
        "assignment": {
            "id": assignment.id,
            "user_id": assignment.user_id,
            "role": assignment.role,
            "assigned_at": assignment.assigned_at,
            "technician": {
                "id": assignment.technician.id,
                "username": assignment.technician.username
            } if assignment.technician else None
        },
        "technicians": get_order_technicians(db, order_id)
    }


# ✅ TAMBIÉN MODIFICAR LA FUNCIÓN DE REMOVER TÉCNICO
@router.delete("/ordenes/{order_id}/technicians/{user_id}")
def remove_technician_from_work_order(
    order_id: int,
    user_id: int,
    soft_delete: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remueve un técnico de una orden de trabajo"""
    
    # Verificar que la orden existe
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    # ✅ NUEVA LÓGICA DE PERMISOS EXPANDIDA (IGUAL QUE EN ADD)
    can_edit = False
    
    # Admin y Jefe de Mantenimiento siempre pueden
    if current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]:
        can_edit = True
    
    # Jefe de Sección puede en su sección
    elif current_user.role.nombre == "Jefe de Sección" and order.section_id == current_user.section_id:
        can_edit = True
    
    # ✅ MECÁNICOS: Pueden gestionar técnicos SI son técnico principal de la orden
    elif current_user.role.nombre == "Mecánico":
        # Verificar si es técnico principal en la orden
        principal_assignment = db.query(WorkOrderTechnician).filter(
            WorkOrderTechnician.work_order_id == order_id,
            WorkOrderTechnician.user_id == current_user.id,
            WorkOrderTechnician.role == "principal",
            WorkOrderTechnician.is_active == True
        ).first()
        
        # También verificar si es el técnico asignado en el campo legacy
        is_assigned_legacy = order.assigned_to_id == current_user.id
        
        can_edit = principal_assignment is not None or is_assigned_legacy
    
    if not can_edit:
        raise HTTPException(
            status_code=403, 
            detail="No tienes permisos para gestionar técnicos en esta orden"
        )
    
    assignment = db.query(WorkOrderTechnician).filter(
        WorkOrderTechnician.work_order_id == order_id,
        WorkOrderTechnician.user_id == user_id,
        WorkOrderTechnician.is_active == True
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    
    if soft_delete:
        assignment.is_active = False
    else:
        db.delete(assignment)
    
    # Si era principal, promover a otro técnico
    if assignment.role == "principal":
        next_technician = db.query(WorkOrderTechnician).filter(
            WorkOrderTechnician.work_order_id == order_id,
            WorkOrderTechnician.role == "apoyo",
            WorkOrderTechnician.is_active == True
        ).order_by(WorkOrderTechnician.assigned_at.asc()).first()
        
        if next_technician:
            next_technician.role = "principal"
    
    db.commit()
    
    return {
        "message": "Técnico removido correctamente",
        "technicians": get_order_technicians(db, order_id)
    }

# ENDPOINT: Obtener técnicos de una orden
@router.get("/ordenes/{order_id}/technicians")
def get_work_order_technicians(
    order_id: int,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene la lista de técnicos asignados a una orden"""
    
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    # Verificar acceso
    #can_access = (
    #    current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"] or
    #    (current_user.role.nombre == "Jefe de Sección" and order.section_id == current_user.section_id) or
    #    order.assigned_to_id == current_user.id  # Técnico principal legacy
    #)
    
    # También verificar si es técnico asignado en la nueva tabla
    #if not can_access:
    #    technician_assignment = db.query(WorkOrderTechnician).filter(
    #        WorkOrderTechnician.work_order_id == order_id,
    #        WorkOrderTechnician.user_id == current_user.id,
    #        WorkOrderTechnician.is_active == True
    #    ).first()
    #    can_access = technician_assignment is not None
    
    #if not can_access:
    #    raise HTTPException(status_code=403, detail="No tienes permisos para ver esta orden")
    
    return {
        "order_id": order_id,
        "order_title": order.title,
        "technicians": get_order_technicians(db, order_id, include_inactive)
    }

# ENDPOINT: Actualizar horas trabajadas
@router.put("/ordenes/{order_id}/technicians/{user_id}/hours")
def update_technician_hours(
    order_id: int,
    user_id: int,
    hours_data: dict,  # {"hours_worked": 4.5}
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza las horas trabajadas de un técnico"""
    
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    # ✅ PERMISOS EXPANDIDOS PARA ACTUALIZAR HORAS
    can_edit = False
    
    # Admin y Jefe de Mantenimiento siempre pueden
    if current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]:
        can_edit = True
    
    # Jefe de Sección puede en su sección
    elif current_user.role.nombre == "Jefe de Sección" and order.section_id == current_user.section_id:
        can_edit = True
    
    # Cualquier técnico puede actualizar sus propias horas
    elif current_user.id == user_id:
        can_edit = True
    
    # ✅ MECÁNICOS PRINCIPALES: Pueden actualizar horas de otros técnicos del equipo
    elif current_user.role.nombre == "Mecánico":
        # Verificar si es técnico principal en la orden
        principal_assignment = db.query(WorkOrderTechnician).filter(
            WorkOrderTechnician.work_order_id == order_id,
            WorkOrderTechnician.user_id == current_user.id,
            WorkOrderTechnician.role == "principal",
            WorkOrderTechnician.is_active == True
        ).first()
        
        # También verificar si es el técnico asignado en el campo legacy
        is_assigned_legacy = order.assigned_to_id == current_user.id
        
        can_edit = principal_assignment is not None or is_assigned_legacy
    
    if not can_edit:
        raise HTTPException(status_code=403, detail="No tienes permisos para actualizar estas horas")
    
    assignment = db.query(WorkOrderTechnician).filter(
        WorkOrderTechnician.work_order_id == order_id,
        WorkOrderTechnician.user_id == user_id,
        WorkOrderTechnician.is_active == True
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    
    hours_worked = hours_data.get("hours_worked", 0)
    if hours_worked < 0:
        raise HTTPException(status_code=400, detail="Las horas trabajadas no pueden ser negativas")
    
    assignment.hours_worked = hours_worked
    db.commit()
    db.refresh(assignment)
    
    return {
        "message": "Horas actualizadas correctamente",
        "hours_worked": float(assignment.hours_worked),
        "technician": assignment.technician.username if assignment.technician else None
    }
# ENDPOINT: Técnicos disponibles
@router.get("/technicians/available")
def get_available_technicians_for_assignment(
    max_load: int = 3,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene técnicos disponibles para asignar"""
    
    query = text("""
        SELECT 
            u.id,
            u.username,
            r.nombre as role_name,
            COUNT(CASE WHEN wo.status IN ('Pendiente', 'En curso', 'En revisión') THEN 1 END) as current_load
        FROM users u
        INNER JOIN roles r ON u.role_id = r.id
        LEFT JOIN work_order_technicians wot ON u.id = wot.user_id AND wot.is_active = TRUE
        LEFT JOIN work_orders wo ON wot.work_order_id = wo.id
        WHERE u.active = TRUE 
          AND r.nombre IN ('Mecánico', 'Jefe de Mantenimiento', 'Jefe de Sección', 'Administrador')
        GROUP BY u.id, u.username, r.nombre
        HAVING COUNT(CASE WHEN wo.status IN ('Pendiente', 'En curso', 'En revisión') THEN 1 END) < :max_load
        ORDER BY 
            CASE r.nombre 
                WHEN 'Mecánico' THEN 1 
                WHEN 'Jefe de Sección' THEN 2
                WHEN 'Jefe de Mantenimiento' THEN 3
                WHEN 'Administrador' THEN 4
                ELSE 5 
            END,
            current_load ASC, 
            u.username ASC
    """)
    
    result = db.execute(query, {"max_load": max_load}).fetchall()
    
    available_technicians = []
    for row in result:
        available_technicians.append({
            "user_id": row.id,
            "username": f"{row.username} ({row.role_name})",  # Mostrar el rol
            "current_load": row.current_load,
            "availability": "high" if row.current_load == 0 else "medium" if row.current_load <= 1 else "low"
        })
    
    return {
        "available_technicians": available_technicians,
        "criteria": f"Personal técnico con menos de {max_load} órdenes activas"
    }


