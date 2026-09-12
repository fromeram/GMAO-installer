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


# --- Section lines 5112-5939 ---
# ---------------------------
# ENDPOINTS DE ORDENES
# ---------------------------

@router.get("/ordenes", summary="Listar Órdenes de Trabajo")
def get_ordenes(
    start: Optional[str] = None,
    end: Optional[str] = None,
    status: Optional[str] = None,
    machine_id: Optional[int] = None,
    include_technicians: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene órdenes de trabajo con filtros según el rol del usuario
    ⭐ CORREGIDO PARA INCLUIR REPUESTOS SIEMPRE Y ARREGLAR has_checklist
    """
    try:
        query = db.query(WorkOrder).options(
            joinedload(WorkOrder.assigned_to),
            joinedload(WorkOrder.machine_obj),
            joinedload(WorkOrder.section),
            joinedload(WorkOrder.line),
            # joinedload(WorkOrder.repuesto),  # ⭐ DEPRECADO
            joinedload(WorkOrder.materials).joinedload(WorkOrderMaterial.inventory), # ⭐ AÑADIR MATERIALES
            joinedload(WorkOrder.failure_code),
            joinedload(WorkOrder.cause_code),
            joinedload(WorkOrder.remedy_code)
        )
        
        # ⭐ INCLUIR TÉCNICOS SOLO SI SE SOLICITA
        if include_technicians:
            query = query.options(
                joinedload(WorkOrder.technicians).joinedload(WorkOrderTechnician.technician)
            )

        # Filtros por rol
        #if current_user.role.nombre == "Jefe de Sección":
        #    query = query.filter(WorkOrder.section_id == current_user.section_id)
        #elif current_user.role.nombre in ["Mecánico", "Calidad", "Contabilidad"]:
        #    pass  # Ven todas
        
        # Aplicar filtros adicionales
        if start and end:
            try:
                start_date = datetime.strptime(start, "%Y-%m-%d")
                end_date = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(WorkOrder.created_at >= start_date, WorkOrder.created_at < end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")

        if status:
            query = query.filter(WorkOrder.status == status)
        if machine_id:
            query = query.filter(WorkOrder.machine_id == machine_id)

        orders = query.order_by(WorkOrder.created_at.desc()).all()
        
        # ⭐ SERIALIZAR MANUALMENTE PARA INCLUIR REPUESTOS
        result = []
        for order in orders:
            # ⭐ DETERMINAR SI TIENE CHECKLIST - NUEVA LÓGICA
            has_checklist = False
            if order.work_type == "Preventivo" and order.generated_from_maintenance_id:
                # ✅ USAR LA RELACIÓN DIRECTA (ya no usar generated_order_id)
                maintenance = db.query(Maintenance).filter(
                    Maintenance.id == order.generated_from_maintenance_id
                ).first()
                
                if maintenance and maintenance.task_list_id:
                    has_checklist = True
            
            order_data = {
                "id": order.id,
                "title": order.title,
                "details": order.details,
                "work_type": order.work_type,
                "status": order.status,
                "operator": order.operator,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "finished_at": order.finished_at.isoformat() if order.finished_at else None,
                "order_number": order.order_number,
                "format_change_type": order.format_change_type,
                "affected_machines": order.affected_machines, # <-- CLAVE: Incluir la lista de máquinas
                "setup_team": order.setup_team,             # <-- CLAVE: Incluir el equipo de setup
                'is_format_change': order.is_format_change, 

                
                # IDs para el frontend
                "section_id": order.section_id,
                "line_id": order.line_id,
                "machine_id": order.machine_id,
                "assigned_to_id": order.assigned_to_id,
                
                # Relaciones
                "section": {
                    "id": order.section.id,
                    "nombre": order.section.nombre
                } if order.section else None,
                
                "line": {
                    "id": order.line.id,
                    "nombre": order.line.nombre
                } if order.line else None,
                
                "machine": {
                    "id": order.machine_obj.id,
                    "nombre": order.machine_obj.nombre
                } if order.machine_obj else None,
                
                "machine_obj": {  # Alias para compatibilidad
                    "id": order.machine_obj.id,
                    "nombre": order.machine_obj.nombre
                } if order.machine_obj else None,
                
                "assigned_to": {
                    "id": order.assigned_to.id,
                    "username": order.assigned_to.username
                } if order.assigned_to else None,
                
                # ⭐ MATERIALES TCO
                "materials": [
                    {
                        "id": mat.id,
                        "inventory_id": mat.inventory_id,
                        "quantity_used": mat.quantity_used,
                        "unit_cost_at_use": float(mat.unit_cost_at_use),
                        "inventory": {
                            "id": mat.inventory.id,
                            "product_name": mat.inventory.product_name
                        } if mat.inventory else None
                    } for mat in order.materials
                ] if order.materials else [],
                
                "total_material_cost": float(order.total_material_cost or 0),
                "total_labor_cost": float(order.total_labor_cost or 0),
                "total_external_cost": float(order.total_external_cost or 0),
                "total_cost": float(order.total_cost or 0),
                
                # Códigos FCR
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
                
                # Información adicional
                "has_checklist": has_checklist,  # ⭐ CORREGIDO - NO USAR order.task_list_id
                "downtime_hours": float(order.downtime_hours) if order.downtime_hours else None,
                "completion_notes": order.completion_notes,
                "actual_start_time": order.actual_start_time.isoformat() if order.actual_start_time else None,
                "actual_end_time": order.actual_end_time.isoformat() if order.actual_end_time else None,
            }
            
            # ⭐ INCLUIR TÉCNICOS SI SE SOLICITA
            if include_technicians:
                technicians_data = []
                for tech_assignment in order.technicians:
                    if tech_assignment.technician and tech_assignment.is_active:
                        technicians_data.append({
                            "id": tech_assignment.id,
                            "user_id": tech_assignment.user_id,
                            "username": tech_assignment.technician.username,
                            "role": tech_assignment.role,
                            "hours_worked": float(tech_assignment.hours_worked) if tech_assignment.hours_worked else 0.0,
                            "assigned_at": tech_assignment.assigned_at.isoformat() if tech_assignment.assigned_at else None,
                            "is_active": tech_assignment.is_active,
                            "notes": tech_assignment.notes,
                            "work_order_id": tech_assignment.work_order_id,
                            "assigned_by_id": tech_assignment.assigned_by_id,
                            "technician": {
                                "id": tech_assignment.technician.id,
                                "username": tech_assignment.technician.username
                            }
                        })
                order_data["technicians"] = technicians_data
            else:
                order_data["technicians"] = []
            
            result.append(order_data)
        
        return result

    except Exception as e:
        print(f"Error en get_ordenes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/ordenes/{order_id}")
def get_orden_by_id(
    order_id: int,
    include_technicians: bool = Query(False),  # ⭐ NUEVO PARÁMETRO
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene una orden de trabajo específica por ID"""
    
    # Buscar la orden con todas las relaciones
    query = db.query(WorkOrder).options(
        joinedload(WorkOrder.assigned_to),
        joinedload(WorkOrder.machine_obj),
        joinedload(WorkOrder.section),
        joinedload(WorkOrder.line),
        joinedload(WorkOrder.materials).joinedload(WorkOrderMaterial.inventory),
        joinedload(WorkOrder.failure_code),
        joinedload(WorkOrder.cause_code),
        joinedload(WorkOrder.remedy_code)
    )
    
    # ⭐ INCLUIR TÉCNICOS SI SE SOLICITA
    if include_technicians:
        query = query.options(
            joinedload(WorkOrder.technicians).joinedload(WorkOrderTechnician.technician)
        )
    
    order = query.filter(WorkOrder.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
    
    # Verificar permisos de acceso
    #can_access = (
    #    current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"] or
    #    (current_user.role.nombre == "Jefe de Sección" and order.section_id == current_user.section_id) or
    #    order.assigned_to_id == current_user.id
    #)
    
    # También verificar si es técnico asignado en la nueva tabla
    #if not can_access and include_technicians:
    #    technician_assignment = db.query(WorkOrderTechnician).filter(
    #        WorkOrderTechnician.work_order_id == order_id,
    #        WorkOrderTechnician.user_id == current_user.id,
    #        WorkOrderTechnician.is_active == True
    #    ).first()
    #    can_access = technician_assignment is not None
    
    #if not can_access:
    #    raise HTTPException(status_code=403, detail="No tienes permisos para ver esta orden")
    
    # ⭐ CONSTRUIR RESPUESTA CON TÉCNICOS SI SE SOLICITA
    response_data = {
        "id": order.id,
        "title": order.title,
        "details": order.details,
        "work_type": order.work_type,
        "status": order.status,
        "operator": order.operator,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "finished_at": order.finished_at.isoformat() if order.finished_at else None,
        "order_number": order.order_number,
        
        # Relaciones
        "section": {
            "id": order.section.id,
            "nombre": order.section.nombre
        } if order.section else None,
        
        "line": {
            "id": order.line.id,
            "nombre": order.line.nombre
        } if order.line else None,
        
        "machine": {
            "id": order.machine_obj.id,
            "nombre": order.machine_obj.nombre
        } if order.machine_obj else None,
        
        "assigned_to": {
            "id": order.assigned_to.id,
            "username": order.assigned_to.username
        } if order.assigned_to else None,
        
        # Códigos FCR
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
        
        # Materiales TCO
        "materials": [
            {
                "id": mat.id,
                "inventory_id": mat.inventory_id,
                "quantity_used": mat.quantity_used,
                "unit_cost_at_use": float(mat.unit_cost_at_use),
                "inventory": {
                    "id": mat.inventory.id,
                    "product_name": mat.inventory.product_name
                } if mat.inventory else None
            } for mat in order.materials
        ] if order.materials else [],
        
        "total_material_cost": float(order.total_material_cost or 0),
        "total_labor_cost": float(order.total_labor_cost or 0),
        "total_external_cost": float(order.total_external_cost or 0),
        "total_cost": float(order.total_cost or 0),
        
        "actual_start_time": order.actual_start_time.isoformat() if order.actual_start_time else None,
        "actual_end_time": order.actual_end_time.isoformat() if order.actual_end_time else None,
        "downtime_hours": float(order.downtime_hours) if order.downtime_hours else None,
        "completion_notes": order.completion_notes,
        
        # Campos adicionales
        "section_id": order.section_id,
        "line_id": order.line_id,
        "machine_id": order.machine_id,
        "machine_name": order.machine_obj.nombre if order.machine_obj else None
    }
    
    # ⭐ INCLUIR TÉCNICOS SI SE SOLICITA
    if include_technicians:
        technicians_data = []
        for tech_assignment in order.technicians:
            if tech_assignment.technician and tech_assignment.is_active:
                technicians_data.append({
                    "user_id": tech_assignment.user_id,
                    "username": tech_assignment.technician.username,
                    "role": tech_assignment.role,
                    "hours_worked": float(tech_assignment.hours_worked) if tech_assignment.hours_worked else 0.0,
                    "assigned_at": tech_assignment.assigned_at.isoformat() if tech_assignment.assigned_at else None,
                    "is_active": tech_assignment.is_active,
                    "notes": tech_assignment.notes
                })
        response_data["technicians"] = technicians_data
    
    return response_data


@router.post("/ordenes")
def create_orden(data: WorkOrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        print(f"***** DEBUG CREATE ORDEN *****")
        print(f"Usuario actual: {current_user.username} ({current_user.role.nombre})")
        print(f"Datos recibidos: {data.dict()}")
        print("***** END DEBUG *****")
        
        # Validación para machine_id
        is_format_change = data.work_type in ['Cambio de Formato', 'Setup de Línea', 'Cambio Global de Planta']
        
        if not is_format_change and not data.machine_id:
            raise HTTPException(status_code=400, detail="machine_id es requerido para este tipo de orden")
        
        # Validar que la sección existe
        section = db.query(Section).filter(Section.id == data.section_id).first()
        if not section:
            raise HTTPException(status_code=404, detail="Sección no encontrada")
        
        # Validar que la línea existe y pertenece a la sección
        line = db.query(Line).filter(Line.id == data.line_id).first()
        if not line:
            raise HTTPException(status_code=404, detail="Línea no encontrada")
        if line.section_id != data.section_id:
            raise HTTPException(status_code=400, detail="La línea no pertenece a la sección seleccionada")
        
        # Para órdenes no de formato, validar máquina
        if not is_format_change:
            machine = db.query(Machine).filter(Machine.id == data.machine_id).first()
            if not machine:
                raise HTTPException(status_code=404, detail="Máquina no encontrada")
            if machine.line_id != data.line_id:
                raise HTTPException(status_code=400, detail="La máquina no pertenece a la línea seleccionada")
        
        # Validar task_list_id si se proporciona
        if data.task_list_id:
            task_list = db.query(TaskList).filter(TaskList.id == data.task_list_id).first()
            if not task_list:
                raise HTTPException(status_code=404, detail="Lista de tareas no encontrada")
        
        # Determinar assigned_to_id
        assigned_to_id = data.assigned_to_id or current_user.id
        
        # Validar el usuario asignado
        assigned_user = db.query(User).filter(User.id == assigned_to_id).first()
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Usuario asignado no encontrado")
        
        # ⭐ NUEVA LÓGICA DE MATERIALES MULTIPLES (TCO)
        total_material_cost = Decimal('0.0')
        materials_to_add = []
        
        if data.materials:
            for mat_data in data.materials:
                inv = db.query(Inventory).filter(Inventory.id == mat_data.inventory_id).first()
                if not inv:
                    raise HTTPException(status_code=404, detail=f"Repuesto ID {mat_data.inventory_id} no encontrado")
                if inv.quantity < mat_data.quantity_used:
                    raise HTTPException(status_code=400, detail=f"Stock insuficiente para '{inv.product_name}'")
                
                # Descontar stock
                inv.quantity -= mat_data.quantity_used
                
                # Tomar precio histórico
                current_price = inv.price if inv.price is not None else 0.0
                total_material_cost += Decimal(str(current_price * mat_data.quantity_used))
                
                # Crear la asociación
                new_material = WorkOrderMaterial(
                    inventory_id=mat_data.inventory_id,
                    quantity_used=mat_data.quantity_used,
                    unit_cost_at_use=current_price
                )
                materials_to_add.append(new_material)

        # ⭐ CREAR LA ORDEN CON VALORES FLEXIBLES
        order_dict = data.dict(exclude={'checklist_data', 'materials'})  # Excluir de base
        order_dict.update({
            'title': data.title or f"Orden de {data.work_type}",
            'details': data.details or f"Orden creada por {current_user.username}",
            'operator': data.operator or current_user.username,
            'assigned_to_id': assigned_to_id,
            'status': data.status or "Pendiente",
            'total_material_cost': total_material_cost,
            'created_at': datetime.utcnow()
        })

        order = WorkOrder(**order_dict)
        if materials_to_add:
            order.materials = materials_to_add

        # Generar número de orden
        latest_order = db.query(WorkOrder).order_by(WorkOrder.id.desc()).first()
        next_id = (latest_order.id + 1) if latest_order else 1
        order.order_number = f"OT-{datetime.now().year}-{next_id:04d}"

        db.add(order)
        db.commit()
        db.refresh(order)
        
        print(f"✅ Orden creada exitosamente: ID {order.id}, Número: {order.order_number}")
        
        # Manejar checklist integrado si existe (SIN await)
        if data.checklist_data:
            checklist_progress = handle_checklist_integration(
                work_order_id=order.id,
                checklist_data=data.checklist_data,
                current_user=current_user,
                db=db
            )
            
            if checklist_progress:
                print(f"✅ Checklist creado para orden {order.id} con {len(data.checklist_data['steps_progress'])} pasos")
        
        # Devolver respuesta compatible
        return {
            "id": order.id,
            "order_number": order.order_number,
            "title": order.title,
            "status": order.status,
            "message": "Orden creada exitosamente"
        }
        
    except HTTPException as he:
        print(f"❌ HTTPException: {he.detail}")
        raise he
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    
@router.delete("/ordenes/{orden_id}")
async def delete_orden(
    orden_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina una orden de trabajo - VERSIÓN CORREGIDA"""
    order = db.query(WorkOrder).filter(WorkOrder.id == orden_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    # Verificar permisos
    if current_user.role.nombre == "Jefe de Sección" and order.section_id != current_user.section_id:
        raise HTTPException(
            status_code=403, 
            detail="Solo puedes eliminar órdenes de tu sección"
        )

    try:
        # Capturar datos para audit trail
        order_data = {
            "order_number": order.order_number,
            "title": order.title,
            "work_type": order.work_type,
            "status": order.status,
            "machine_id": order.machine_id,
            "generated_from_maintenance_id": order.generated_from_maintenance_id
        }
        
        # ✅ ELIMINADA la referencia a Maintenance.generated_order_id (no existe)
        # Simplemente eliminar la orden
        db.delete(order)
        db.commit()
        
        # Audit trail
        audit_manager.log_action(
            db=db,
            action="DELETE",
            entity=order,
            user=current_user,
            request=request,
            old_data=order_data,
            notes=f"Orden eliminada: {order_data['order_number']} - {order_data['title']}"
        )
        db.commit()
        
        return {"success": True, "message": "Orden eliminada correctamente"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar orden {orden_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error al eliminar la orden: {str(e)}"
        )
        

@router.put("/ordenes/{orden_id}", response_model=WorkOrderRead, summary="Actualizar o Completar Orden de Trabajo")
async def update_complete_orden(
    orden_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza una orden de trabajo con validación de permisos corregida
    """
    # --- AUDIT: Capturar estado ANTES del cambio ---
    order = db.query(WorkOrder).options(
        joinedload(WorkOrder.assigned_to),
        joinedload(WorkOrder.machine_obj),
        joinedload(WorkOrder.section),
        joinedload(WorkOrder.line),
        joinedload(WorkOrder.materials).joinedload(WorkOrderMaterial.inventory),
        joinedload(WorkOrder.failure_code),
        joinedload(WorkOrder.cause_code),
        joinedload(WorkOrder.remedy_code)
    ).filter(WorkOrder.id == orden_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    # IMPORTANTE: Capturar estado anterior para audit
    old_data = audit_manager.extract_entity_data(order)
    
    # ⭐ VALIDACIÓN DE PERMISOS CORREGIDA
    print(f"🔐 DEBUG PERMISOS - Usuario: {current_user.username} (Rol: {current_user.role.nombre})")
    print(f"🔐 DEBUG PERMISOS - Orden: {orden_id} (Estado: {order.status})")
    print(f"🔐 DEBUG PERMISOS - Asignado a: {order.assigned_to_id}")
    print(f"🔐 DEBUG PERMISOS - Sección orden: {order.section_id}, Sección usuario: {getattr(current_user, 'section_id', None)}")
    
    # Admin y Jefe de Mantenimiento pueden cerrar cualquier orden
    can_close = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
    
    # Permisos para actualizar (incluyendo cambios de estado que no sean cerrar)
    can_update_progress = (
        can_close or  # Admin y Jefe de Mantenimiento pueden todo
        (current_user.role.nombre == "Jefe de Sección" and order.section_id == current_user.section_id) or
        (order.assigned_to_id == current_user.id) or  # Técnico asignado principal
        # ⭐ TAMBIÉN VERIFICAR SI ES TÉCNICO ASIGNADO EN LA NUEVA TABLA
        db.query(WorkOrderTechnician).filter(
            WorkOrderTechnician.work_order_id == orden_id,
            WorkOrderTechnician.user_id == current_user.id,
            WorkOrderTechnician.is_active == True
        ).first() is not None
    )
    
    print(f"🔐 DEBUG PERMISOS - Puede cerrar: {can_close}")
    print(f"🔐 DEBUG PERMISOS - Puede actualizar: {can_update_progress}")
    
    if not can_update_progress:
        raise HTTPException(
            status_code=403, 
            detail="No tienes permiso para actualizar esta orden."
        )

    # Parsing y validación de datos
    try:
        body_json = await request.json()
        print(f"***** DEBUG UPDATE ORDEN {orden_id} *****")
        print(f"Raw body: {body_json}")
        if 'details' in body_json:
            print(f"Details length in raw: {len(body_json['details']) if body_json['details'] else 0}")
        print("***** END DEBUG UPDATE *****")
        data = WorkOrderCompleteUpdate(**body_json)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e_parse:
        raise HTTPException(status_code=400, detail=f"Error procesando datos: {e_parse}")

    # Validación de datos
    update_data = data.dict(exclude_unset=True)
    fields_updated = []
    
    # ⭐ VALIDAR ESTADO PERMITIDO ANTES DE APLICARLO
    if data.status is not None:
        if data.status not in ["Pendiente", "En curso", "En revisión", "Cerrada"]:
            raise HTTPException(status_code=400, detail="Valor de estado proporcionado no es válido.")
        
        # ⭐ SOLO VALIDAR PERMISOS DE CIERRE SI REALMENTE SE ESTÁ INTENTANDO CERRAR
        if data.status == "Cerrada" and not can_close:
            raise HTTPException(
                status_code=403, 
                detail="No tienes permiso para cerrar esta orden. Solo administradores y jefes de mantenimiento pueden cerrar órdenes."
            )

    # Aplicar cambios al objeto order
    exclude_fields = {'materials'} # Ignoramos materials aquí para manejarlos manualmente
    for key, value in update_data.items():
        if key in exclude_fields:
            continue
        if hasattr(order, key) and value is not None:
            old_value = getattr(order, key)
            if old_value != value:
                print(f"🔄 Actualizando {key}: {old_value} -> {value}")
                setattr(order, key, value)
                fields_updated.append(key)

    # ⭐ GESTIÓN DE MÚLTIPLES MATERIALES (TCO)
    if data.materials is not None: # Si mandan una lista (incluso vacía), la procesamos
        print("🔧 DEBUG MATERIALES: Recibida actualización de materiales")
        # 1. Devolver el stock actual de lo que se usó previamente
        for old_mat in order.materials:
            if old_mat.inventory:
                old_mat.inventory.quantity += old_mat.quantity_used
        
        # 2. Borrar materiales actuales (cascade="all, delete-orphan" lo maneja con order.materials.clear())
        order.materials.clear()
        
        total_mat_cost = Decimal('0.0')
        new_materials = []
        
        # 3. Procesar y añadir los nuevos
        for mat_data in data.materials:
            inv = db.query(Inventory).filter(Inventory.id == mat_data.inventory_id).first()
            if not inv:
                raise HTTPException(status_code=404, detail=f"Repuesto ID {mat_data.inventory_id} no encontrado")
            if inv.quantity < mat_data.quantity_used:
                raise HTTPException(status_code=400, detail=f"Stock insuficiente para '{inv.product_name}'")
            
            # Descontar stock
            inv.quantity -= mat_data.quantity_used
            
            # Calcular costo
            current_price = inv.price if inv.price is not None else 0.0
            total_mat_cost += Decimal(str(current_price * mat_data.quantity_used))
            
            # Crear nueva asociación
            new_mat = WorkOrderMaterial(
                inventory_id=mat_data.inventory_id,
                quantity_used=mat_data.quantity_used,
                unit_cost_at_use=current_price
            )
            new_materials.append(new_mat)
        
        order.materials = new_materials
        order.total_material_cost = total_mat_cost
        fields_updated.append("materials")
        fields_updated.append("total_material_cost")

    # ⭐ GESTIÓN AUTOMÁTICA DE COSTOS LABORALES
    # Calcular costes laborales basados en los técnicos asignados
    if data.status == "Cerrada" or "technicians" in fields_updated or data.status == "En revisión":
        total_labor = Decimal('0.0')
        for tech in order.technicians:
            if tech.is_active and tech.hours_worked and tech.technician:
                hourly = tech.technician.hourly_rate or 0.0
                total_labor += Decimal(str(tech.hours_worked * hourly))
        order.total_labor_cost = total_labor
        if "total_labor_cost" not in fields_updated:
            fields_updated.append("total_labor_cost")

    # ⭐ GESTIÓN AUTOMÁTICA DE FECHAS
    if data.status == "En curso" and not order.actual_start_time:
        order.actual_start_time = datetime.utcnow()
        fields_updated.append("actual_start_time")
    
    if data.status == "Cerrada" and not order.actual_end_time:
        order.actual_end_time = datetime.utcnow()
        fields_updated.append("actual_end_time")

    # --- AUDIT TRAIL ---
    new_data = audit_manager.extract_entity_data(order)
    
    # Determinar el tipo de acción para el audit
    audit_action = "UPDATE"
    if data.status == "Cerrada":
        audit_action = "CLOSE"
        audit_notes = f"Orden cerrada. Campos actualizados: {', '.join(fields_updated)}"
    elif "status" in fields_updated:
        audit_action = "STATUS_CHANGE"
        audit_notes = f"Estado cambiado a '{data.status}'. Otros campos: {', '.join([f for f in fields_updated if f != 'status'])}"
    else:
        audit_notes = f"Campos actualizados: {', '.join(fields_updated)}"
    
    # Registrar en audit trail ANTES del commit
    audit_manager.log_action(
        db=db,
        action=audit_action,
        entity=order,
        user=current_user,
        request=request,
        old_data=old_data,
        new_data=new_data,
        notes=audit_notes,
        metadata={
            'fields_updated': fields_updated,
            'order_number': order.order_number,
            'work_type': order.work_type,
            'machine_id': order.machine_id
        }
    )
    # --- FIN AUDIT TRAIL ---

    # Guardar cambios
    try:
        db.commit()
        db.refresh(order)
        if hasattr(data, 'checklist_data') and data.checklist_data:
            checklist_progress = await handle_checklist_integration(
                work_order_id=order.id,
                checklist_data=data.checklist_data,
                current_user=current_user,
                db=db
            )
            
            if checklist_progress:
                print(f"✅ Checklist actualizado para orden {order.id}")
        
        # ⭐ RECARGAR TODAS LAS RELACIONES PARA LA RESPUESTA
        db.refresh(order, attribute_names=[
            'assigned_to', 'machine_obj', 'section', 'line',
            'materials', 'failure_code', 'cause_code', 'remedy_code'
        ])
        
        # Gamificación si se cierra la orden
        gamification_result = None
        if data.status == "Cerrada" and order.assigned_to_id:
            try:
                points_engine = get_points_engine(db)
                gamification_result = points_engine.award_points_for_order(
                    order, 
                    order.assigned_to_id
                )
                logger.info(f"Puntos otorgados para orden {orden_id}: {gamification_result}")
            except Exception as e:
                logger.error(f"Error en gamificación para orden {orden_id}: {e}")
                # No fallar la orden por error de gamificación

        print(f"✅ Orden {orden_id} actualizada correctamente")
        return order

    except Exception as e:
        db.rollback()
        logger.error(f"Error al actualizar orden {orden_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al guardar la orden: {e}")
