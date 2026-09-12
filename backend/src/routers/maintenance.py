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


# --- Section lines 2301-3362 ---
# ---------------------------
# ENDPOINTS DE MANTENIMIENTO
# ---------------------------

def generate_work_order_from_task_list(maintenance: Maintenance, db: Session) -> WorkOrder:
    """Genera una orden de trabajo detallada usando TaskList"""
    
    # --- Tu lógica para buscar el técnico asignado (INTACTA) ---
    logger.info(f"🔧 GENERANDO ORDEN PARA MANTENIMIENTO {maintenance.id}")
    logger.info(f"   📋 Usuario asignado en mantenimiento: {maintenance.assigned_user_id} (SERÁ IGNORADO)")
    logger.info(f"   👥 Rol asignado en mantenimiento: {maintenance.assigned_role_id} (SERÁ IGNORADO)")
    
    section_id = maintenance.machine.section_id if maintenance.machine else None
    logger.info(f"   🏭 Sección de la máquina: {section_id}")
    
    current_shift_user = get_current_shift_user(db, section_id)
    
    if current_shift_user:
        assigned_to_id = current_shift_user.id
        logger.info(f"   ✅ FORZANDO ASIGNACIÓN AL TURNO ACTUAL: {current_shift_user.username} (ID: {assigned_to_id})")
    else:
        logger.warning(f"   ❌ NO se encontró usuario en turno actual")
        assigned_to_id = maintenance.assigned_user_id
        if assigned_to_id:
            logger.info(f"   🔄 Fallback 1 - Usuario del mantenimiento: {assigned_to_id}")
        elif maintenance.assigned_role_id:
            user_with_role = db.query(User).filter(User.role_id == maintenance.assigned_role_id).first()
            assigned_to_id = user_with_role.id if user_with_role else None
            logger.info(f"   🔄 Fallback 2 - Usuario por rol: {assigned_to_id}")
        else:
            default_user = db.query(User).filter(User.active == True).first()
            assigned_to_id = default_user.id if default_user else 1
            logger.info(f"   🔄 Fallback 3 - Usuario por defecto: {assigned_to_id}")
    
    logger.info(f"   🎯 USUARIO FINAL ASIGNADO: {assigned_to_id}")
    
    # --- Tu lógica para crear el objeto work_order (INTACTA) ---
    if not maintenance.task_list_id:
        work_order = WorkOrder(
            title=maintenance.title,
            details=maintenance.description,
            work_type="Preventivo",
            machine_id=maintenance.machine_id,
            operator="Sistema Automático",
            assigned_to_id=assigned_to_id,
            section_id=maintenance.machine.section_id if maintenance.machine else None,
            line_id=maintenance.machine.line_id if maintenance.machine else None,
            status="Pendiente",
            created_at=datetime.utcnow()
        )
    else:
        task_list = db.query(TaskList).options(joinedload(TaskList.steps)).filter(TaskList.id == maintenance.task_list_id).first()

        if not task_list:
            logger.warning(f"TaskList {maintenance.task_list_id} no encontrada para mantenimiento {maintenance.id}")
            work_order = WorkOrder(
                title=maintenance.title,
                details=maintenance.description + "\n\n⚠️ Lista de tareas no encontrada",
                work_type="Preventivo",
                machine_id=maintenance.machine_id,
                operator="Sistema Automático",
                assigned_to_id=assigned_to_id,
                section_id=maintenance.machine.section_id if maintenance.machine else None,
                line_id=maintenance.machine.line_id if maintenance.machine else None,
                status="Pendiente",
                created_at=datetime.utcnow()
            )
        else:
            machine_name = maintenance.machine.nombre if maintenance.machine else "Máquina desconocida"
            title = f"[Preventivo] {task_list.name} - {machine_name}"
            
            # --- Tu construcción de detalles (INTACTA Y COMPLETA) ---
            details = f"🔧 MANTENIMIENTO PREVENTIVO\n"
            details += f"Máquina: {machine_name}\n"
            details += f"Frecuencia: {maintenance.frequency}\n"
            details += f"Lista de tareas: {task_list.name}\n\n"
            if task_list.description:
                details += f"Descripción: {task_list.description}\n\n"
            details += "📋 PASOS A SEGUIR:\n"
            details += "=" * 50 + "\n\n"
            total_estimated_time = 0
            step_count = 0
            for step in sorted(task_list.steps, key=lambda x: x.step_order):
                step_count += 1
                details += f"Paso {step.step_order}: {step.description}\n"
                if step.estimated_time_minutes:
                    details += f"    ⏱️ Tiempo estimado: {step.estimated_time_minutes} minutos\n"
                    total_estimated_time += step.estimated_time_minutes
                details += f"    ✅ Completado: [ ]\n"
                details += f"    📝 Observaciones: ________________________________\n\n"
            details += "=" * 50 + "\n"
            details += f"📊 RESUMEN:\n"
            details += f"    • Total de pasos: {step_count}\n"
            details += f"    • Tiempo total estimado: {total_estimated_time} minutos ({total_estimated_time/60:.1f} horas)\n"
            details += f"    • Fecha de generación: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}\n\n"
            details += "✅ VERIFICACIÓN FINAL:\n"
            details += "[ ] Todos los pasos completados\n"
            details += "[ ] Máquina en condiciones óptimas\n"
            details += "[ ] Herramientas recogidas\n"
            details += "[ ] Área de trabajo limpia\n\n"
            details += "👤 Técnico responsable: ________________\n"
            details += "📅 Fecha de ejecución: ________________\n"
            details += "🕐 Hora inicio: _______ Hora fin: _______\n"
            details += "✍️ Observaciones generales:\n"
            details += "_" * 50 + "\n" * 3
            # --- FIN de tu construcción de detalles ---
            
            work_order = WorkOrder(
                title=title,
                details=details,
                work_type="Preventivo",
                machine_id=maintenance.machine_id,
                section_id=maintenance.machine.section_id if maintenance.machine else None,
                line_id=maintenance.machine.line_id if maintenance.machine else None,
                assigned_to_id=assigned_to_id,
                status="Pendiente",
                created_at=datetime.utcnow(),
                operator="Sistema Automático",
                generated_from_maintenance_id=maintenance.id
            )

    # ✅ --- ÚNICO BLOQUE AÑADIDO: Asignación del técnico en el nuevo sistema ---
    db.add(work_order)
    db.flush()  # Crucial para obtener el work_order.id

    if assigned_to_id:
        logger.info(f"   ➕ Añadiendo asignación al sistema de técnicos para la nueva orden {work_order.id}")
        tech_assignment = WorkOrderTechnician(
            work_order_id=work_order.id,
            user_id=assigned_to_id,
            role='principal',
            assigned_by_id=1,
            notes='Asignado automáticamente por el sistema preventivo.'
        )
        db.add(tech_assignment)
    # --- FIN DEL BLOQUE AÑADIDO ---

    return work_order



@router.get("/mantenimiento-preventivo/pending")
def get_pending_maintenance(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        # Obtener fecha actual
        current_date = datetime.utcnow()

        # Construir la consulta base
        query = db.query(Maintenance).filter(
            Maintenance.type == "Preventivo",
            Maintenance.is_completed == False,
            Maintenance.next_maintenance_date <= current_date
        )

        # Si el usuario no es admin, filtrar por su rol
        if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
            query = query.filter(Maintenance.assigned_role_id == current_user.role.id)

        maintenances = query.all()
        
        result = []
        for m in maintenances:
            machine = db.query(Machine).filter(Machine.id == m.machine_id).first()
            result.append({
                "id": m.id,
                "title": m.title,
                "description": m.description,
                "machine_id": m.machine_id,
                "machine_name": machine.nombre if machine else "Desconocida",
                "frequency": m.frequency,
                "next_maintenance_date": m.next_maintenance_date.isoformat() if m.next_maintenance_date else None,
                "notification_interval": m.notification_interval
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/mantenimiento-preventivo/{maintenance_id}/complete")
def complete_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        maintenance = db.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
        if not maintenance:
            raise HTTPException(status_code=404, detail="Mantenimiento no encontrado")

        # Verificar permisos
        if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
            if maintenance.assigned_role_id != current_user.role.id:
                raise HTTPException(status_code=403, detail="No tienes permiso para completar este mantenimiento")

        # Actualizar fechas y estado
        maintenance.last_maintenance_date = datetime.utcnow()
        
        # Calcular próxima fecha de mantenimiento según la frecuencia
        next_date = maintenance.last_maintenance_date
        if maintenance.frequency == "Diario":
            next_date = next_date + timedelta(days=1)
        elif maintenance.frequency == "Semanal":
            next_date = next_date + timedelta(weeks=1)
        elif maintenance.frequency == "Mensual":
            next_date = next_date + timedelta(days=30)
        elif maintenance.frequency == "Trimestral":
            next_date = next_date + timedelta(days=90)
        elif maintenance.frequency == "Semestral":
            next_date = next_date + timedelta(days=180)
        elif maintenance.frequency == "Anual":
            next_date = next_date + timedelta(days=365)

        maintenance.next_maintenance_date = next_date
        maintenance.is_completed = True

        db.commit()
        
        return {"success": True, "message": "Mantenimiento completado correctamente"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/maintenance")
def get_all_maintenance(
    start: Optional[str] = None,
    end: Optional[str] = None,
    machine_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """HISTORIAL DE MANTENIMIENTO - VERSIÓN FINAL QUE FUNCIONA"""
    try:
        # ✅ Buscar órdenes cerradas vinculadas a mantenimientos
        query = db.query(WorkOrder).filter(
            WorkOrder.status == 'Cerrada',
            WorkOrder.generated_from_maintenance_id.isnot(None)
        ).options(
            joinedload(WorkOrder.machine_obj)
        )

        # Filtros por rol
        if current_user.role.nombre == "Jefe de Sección":
            query = query.filter(WorkOrder.section_id == current_user.section_id)
        
        if machine_id:
            query = query.filter(WorkOrder.machine_id == machine_id)

        if start and end:
            try:
                sdt = datetime.strptime(start, "%Y-%m-%d")
                edt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(WorkOrder.finished_at >= sdt, WorkOrder.finished_at < edt)
            except:
                raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")
                
        orders = query.order_by(WorkOrder.finished_at.desc()).all()
        
        response_data = []
        for order in orders:
            # Buscar mantenimiento vinculado
            maintenance = db.query(Maintenance).filter(
                Maintenance.id == order.generated_from_maintenance_id
            ).first()
            
            if maintenance:
                response_data.append({
                    "id": maintenance.id,
                    "title": maintenance.title,
                    "type": maintenance.type,
                    "machineName": order.machine_obj.nombre if order.machine_obj else "Desconocida",
                    "finished_at": order.finished_at.isoformat() if order.finished_at else None,
                    "work_order_id": order.id
                })
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error en get_all_maintenance: {e}", exc_info=True)
        return []



@router.get("/mantenimiento-preventivo")
def get_mantenimiento_preventivo(
    include_task_list_details: bool = Query(False, description="Incluir detalles completos de TaskList"),
    db: Session = Depends(get_db)
):
    try:
        # CORRECCIÓN: Usar joinedload para cargar TaskList con sus pasos
        query = db.query(Maintenance).filter(Maintenance.type == "Preventivo")
        
        if include_task_list_details:
            query = query.options(
                joinedload(Maintenance.task_list).joinedload(TaskList.steps),
                joinedload(Maintenance.machine),
                joinedload(Maintenance.assigned_user),
                joinedload(Maintenance.assigned_role)
            )
        else:
            query = query.options(
                joinedload(Maintenance.task_list),  # Solo TaskList básica
                joinedload(Maintenance.machine),
                joinedload(Maintenance.assigned_user),
                joinedload(Maintenance.assigned_role)
            )
        
        maintenances = query.all()
        result = []

        for m in maintenances:
            try:
                # Obtener la máquina
                machine = m.machine
                
                # Obtener línea y sección
                line = None
                section = None
                if machine:
                    line = db.query(Line).filter(Line.id == machine.line_id).first()
                    if line:
                        section = db.query(Section).filter(Section.id == line.section_id).first()

                # Preparar información de TaskList
                task_list_info = None
                if m.task_list:
                    task_list_info = {
                        "id": m.task_list.id,
                        "name": m.task_list.name,
                        "description": m.task_list.description,
                        "applies_to_type": m.task_list.applies_to_type
                    }
                    
                    # Si se solicitan detalles completos, incluir pasos
                    if include_task_list_details:
                        steps_count = len(m.task_list.steps) if m.task_list.steps else 0
                        total_time = sum(
                            step.estimated_time_minutes or 0 
                            for step in m.task_list.steps
                        ) if m.task_list.steps else 0
                        
                        task_list_info.update({
                            "steps_count": steps_count,
                            "total_estimated_minutes": total_time,
                            "steps": [
                                {
                                    "id": step.id,
                                    "step_order": step.step_order,
                                    "description": step.description,
                                    "estimated_time_minutes": step.estimated_time_minutes
                                }
                                for step in sorted(m.task_list.steps, key=lambda x: x.step_order)
                            ] if m.task_list.steps else []
                        })

                maintenance_data = {
                    "id": m.id,
                    "title": m.title,
                    "description": m.description,
                    "maquina_id": m.machine_id,
                    "maquina_nombre": machine.nombre if machine else "Máquina no encontrada",
                    "linea_nombre": line.nombre if line else "Línea no encontrada",
                    "seccion_nombre": section.nombre if section else "Sección no encontrada",
                    "frecuencia": m.frequency,
                    "fechaInicio": m.created_at.isoformat() if m.created_at else None,
                    "next_maintenance_date": m.next_maintenance_date.isoformat() if m.next_maintenance_date else None,
                    
                    # CORRECCIÓN: Incluir task_list_id y task_list
                    "task_list_id": m.task_list_id,
                    "task_list": task_list_info,  # ← ESTO FALTABA
                    
                    "assigned_user": {
                        "id": m.assigned_user.id,
                        "username": m.assigned_user.username
                    } if m.assigned_user else None,
                    "assigned_role": {
                        "id": m.assigned_role.id,
                        "nombre": m.assigned_role.nombre
                    } if m.assigned_role else None
                }
                result.append(maintenance_data)
            except Exception as e:
                print(f"Error procesando mantenimiento {m.id}: {str(e)}")
                continue

        return result
    except Exception as e:
        print(f"Error general en get_mantenimiento_preventivo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mantenimiento-preventivo/{maintenance_id}")
def get_maintenance_with_tasklist(
    maintenance_id: int,
    include_task_list: bool = Query(True, description="Incluir TaskList completa"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene un mantenimiento específico con su TaskList completa"""
    try:
        query = db.query(Maintenance).filter(
            Maintenance.id == maintenance_id,
            Maintenance.type == "Preventivo"
        )
        
        if include_task_list:
            query = query.options(
                joinedload(Maintenance.task_list).joinedload(TaskList.steps),
                joinedload(Maintenance.machine),
                joinedload(Maintenance.assigned_user),
                joinedload(Maintenance.assigned_role)
            )
        
        maintenance = query.first()
        if not maintenance:
            raise HTTPException(status_code=404, detail="Mantenimiento no encontrado")
        
        # Construir respuesta similar al endpoint principal
        task_list_info = None
        if maintenance.task_list:
            steps_count = len(maintenance.task_list.steps) if maintenance.task_list.steps else 0
            total_time = sum(
                step.estimated_time_minutes or 0 
                for step in maintenance.task_list.steps
            ) if maintenance.task_list.steps else 0
            
            task_list_info = {
                "id": maintenance.task_list.id,
                "name": maintenance.task_list.name,
                "description": maintenance.task_list.description,
                "applies_to_type": maintenance.task_list.applies_to_type,
                "steps_count": steps_count,
                "total_estimated_minutes": total_time,
                "steps": [
                    {
                        "id": step.id,
                        "step_order": step.step_order,
                        "description": step.description,
                        "estimated_time_minutes": step.estimated_time_minutes
                    }
                    for step in sorted(maintenance.task_list.steps, key=lambda x: x.step_order)
                ] if maintenance.task_list.steps else []
            }
        
        return {
            "id": maintenance.id,
            "title": maintenance.title,
            "description": maintenance.description,
            "task_list_id": maintenance.task_list_id,
            "task_list": task_list_info,
            "machine": {
                "id": maintenance.machine.id,
                "nombre": maintenance.machine.nombre
            } if maintenance.machine else None
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error obteniendo mantenimiento {maintenance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/mantenimiento-preventivo")
def create_mantenimiento_preventivo(data: MantenimientoPreventivoCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verificar la máquina
    machine = db.query(Machine).filter(Machine.id == data.maquina_id).first()
    if not machine:
        raise HTTPException(status_code=400, detail="La máquina no existe")

    # Verificar usuario asignado si existe
    if data.assigned_user_id:
        assigned_user = db.query(User).filter(User.id == data.assigned_user_id).first()
        if not assigned_user:
            raise HTTPException(status_code=400, detail="Usuario asignado no existe")

    # Verificar rol asignado si existe
    if data.assigned_role_id:
        assigned_role = db.query(Role).filter(Role.id == data.assigned_role_id).first()
        if not assigned_role:
            raise HTTPException(status_code=400, detail="Rol asignado no existe")
        
    # ✅ NUEVA VALIDACIÓN: TaskList
        if data.task_list_id:
            task_list = db.query(TaskList).filter(TaskList.id == data.task_list_id).first()
            if not task_list:
                raise HTTPException(status_code=400, detail="Lista de tareas no existe")    

    # Verificar fechas
    try:
        fecha_inicio = datetime.strptime(data.fechaInicio, "%Y-%m-%d")
    except:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")

    # Calcular próxima fecha de mantenimiento
    next_date = fecha_inicio
    if data.frecuencia == "Diario":
        next_date = fecha_inicio + timedelta(days=1)
    elif data.frecuencia == "Semanal":
        next_date = fecha_inicio + timedelta(weeks=1)
    elif data.frecuencia == "Mensual":
        next_date = fecha_inicio + timedelta(days=30)
    elif data.frecuencia == "Trimestral":
        next_date = fecha_inicio + timedelta(days=90)
    elif data.frecuencia == "Semestral":
        next_date = fecha_inicio + timedelta(days=180)
    elif data.frecuencia == "Anual":
        next_date = fecha_inicio + timedelta(days=365)

    m = Maintenance(
            title=data.title,
            type="Preventivo",
            description=data.description,
            machine_id=data.maquina_id,
            created_at=fecha_inicio,
            next_maintenance_date=next_date,
            frequency=data.frecuencia,
            notification_interval=data.notification_interval,
            assigned_role_id=data.assigned_role_id,
            assigned_user_id=data.assigned_user_id,
            task_list_id=data.task_list_id  # ✅ AÑADIR ESTA LÍNEA
        )

    try:
        db.add(m)
        db.commit()
        db.refresh(m)

        # Obtener datos relacionados
        machine = db.query(Machine).filter(Machine.id == m.machine_id).first()
        line = db.query(Line).filter(Line.id == machine.line_id).first() if machine else None
        section = db.query(Section).filter(Section.id == line.section_id).first() if line else None
        assigned_user = db.query(User).filter(User.id == m.assigned_user_id).first() if m.assigned_user_id else None
        assigned_role = db.query(Role).filter(Role.id == m.assigned_role_id).first() if m.assigned_role_id else None

        return {
            "success": True,
            "data": {
                "id": m.id,
                "title": m.title,
                "description": m.description,
                "maquina_id": m.machine_id,
                "maquina_nombre": machine.nombre if machine else "Desconocida",
                "linea_nombre": line.nombre if line else "Desconocida",
                "seccion_nombre": section.nombre if section else "Desconocida",
                "frecuencia": m.frequency,
                "fechaInicio": m.created_at.isoformat() if m.created_at else None,
                "next_maintenance_date": m.next_maintenance_date.isoformat() if m.next_maintenance_date else None,
                "assigned_user": {
                    "id": assigned_user.id,
                    "username": assigned_user.username
                } if assigned_user else None,
                "assigned_role": {
                    "id": assigned_role.id,
                    "nombre": assigned_role.nombre
                } if assigned_role else None
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/mantenimiento-preventivo/{id}")
def update_mantenimiento_preventivo(
    id: int,
    data: MantenimientoPreventivoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verificar permisos
    if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar.")

    m = db.query(Maintenance).filter(Maintenance.id == id, Maintenance.type == "Preventivo").first()
    if not m:
        raise HTTPException(status_code=404, detail="Tarea preventiva no encontrada")

    update_data = data.dict(exclude_unset=True)
    recalculate_next_date = False

    for key, value in update_data.items():
        if key == "fechaInicio":
            try:
                fecha_inicio = datetime.strptime(value, "%Y-%m-%d")
                setattr(m, 'created_at', fecha_inicio) # El campo de la DB es created_at
                recalculate_next_date = True
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")
        elif key == "frecuencia":
            setattr(m, key, value)
            recalculate_next_date = True
        else:
            setattr(m, key, value)
            
    # Recalcular la próxima fecha si la frecuencia o la fecha de inicio cambiaron
    if recalculate_next_date:
        start_date = m.created_at
        freq = m.frecuencia
        next_date = start_date # Inicia con la fecha de inicio
        
        if freq == "Diario": next_date += timedelta(days=1)
        elif freq == "Semanal": next_date += timedelta(weeks=1)
        elif freq == "Mensual": next_date += relativedelta(months=1)
        elif freq == "Trimestral": next_date += relativedelta(months=3)
        elif freq == "Semestral": next_date += relativedelta(months=6)
        elif freq == "Anual": next_date += relativedelta(years=1)
        
        m.next_maintenance_date = next_date

    try:
        db.commit()
        db.refresh(m)
        return {"success": True, "message": "Mantenimiento actualizado correctamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/mantenimiento-preventivo/{id}")
def delete_mantenimiento_preventivo(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    m = db.query(Maintenance).filter(Maintenance.id == id, Maintenance.type == "Preventivo").first()
    if not m:
        raise HTTPException(status_code=404, detail="Tarea preventiva no encontrada")

    # Verificar permisos
    if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar tareas preventivas")

    try:
        db.delete(m)
        db.commit()
        return {"success": True, "message": "Tarea preventiva eliminada correctamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mantenimiento-preventivo/alerts")
def get_maintenance_alerts(
    days_ahead: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene alertas de mantenimientos que necesitan órdenes de trabajo.
    ARQUITECTURA CORREGIDA: Sin dependencia de generated_order_id.
    """
    today = datetime.utcnow().date()
    end_date = today + timedelta(days=days_ahead)
    
    # Obtener todos los mantenimientos que vencen
    due_maintenances = db.query(Maintenance).filter(
        Maintenance.next_maintenance_date.between(today, end_date),
        Maintenance.type == "Preventivo"
    ).all()
    
    alerts = []
    for m in due_maintenances:
        # ✅ USAR LA FUNCIÓN HELPER
        active_order = get_active_order_for_maintenance(m.id, db)
        
        # Solo mostrar alerta si NO hay orden activa
        if not active_order:
            stats = get_maintenance_statistics(m.id, db)
            alerts.append({
                "id": m.id,
                "title": m.title,
                "machine": m.machine.nombre,
                "due_date": m.next_maintenance_date.isoformat(),
                "assigned_to": m.assigned_user.username if m.assigned_user else m.assigned_role.nombre,
                "frequency": m.frequency,
                "stats": stats
            })
    
    return alerts

# ✅ NUEVA RUTA PARA HISTORIAL
@router.get("/mantenimiento-preventivo/{maintenance_id}/orders")
def get_maintenance_order_history(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el historial completo de órdenes generadas por un mantenimiento.
    """
    maintenance = db.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    if not maintenance:
        raise HTTPException(status_code=404, detail="Mantenimiento no encontrado")
    
    # ✅ USAR LAS FUNCIONES HELPER
    orders = get_all_orders_for_maintenance(maintenance_id, db)
    active_order = get_active_order_for_maintenance(maintenance_id, db)
    stats = get_maintenance_statistics(maintenance_id, db)
    
    return {
        "maintenance": {
            "id": maintenance.id,
            "title": maintenance.title,
            "frequency": maintenance.frequency,
            "next_date": maintenance.next_maintenance_date.isoformat() if maintenance.next_maintenance_date else None
        },
        "active_order": {
            "id": active_order.id,
            "order_number": active_order.order_number,
            "status": active_order.status,
            "created_at": active_order.created_at.isoformat()
        } if active_order else None,
        "order_history": [
            {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "finished_at": order.finished_at.isoformat() if order.finished_at else None
            } for order in orders
        ],
        "stats": stats
    }



@router.post("/maintenance/generate-order/{maintenance_id}")
def generate_order_from_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Genera una nueva orden de trabajo desde un mantenimiento preventivo.
    ARQUITECTURA CORREGIDA: Sin dependencia de generated_order_id.
    """
    try:
        # Verificar permisos
        if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
            raise HTTPException(status_code=403, detail="No tienes permisos para generar órdenes")

        # Buscar mantenimiento
        maintenance = db.query(Maintenance).options(
            joinedload(Maintenance.machine),
            joinedload(Maintenance.task_list)
        ).filter(Maintenance.id == maintenance_id).first()

        if not maintenance:
            raise HTTPException(status_code=404, detail="Mantenimiento no encontrado")

        # ✅ USAR LAS FUNCIONES HELPER
        can_generate, reason = can_generate_new_order(maintenance_id, db)
        if not can_generate:
            raise HTTPException(status_code=400, detail=reason)

        # Generar nueva orden
        work_order = generate_work_order_from_task_list(maintenance, db)

        # Añadir a la base de datos
        db.add(work_order)
        db.flush()  # Para obtener el ID

        # Generar número de orden
        work_order.order_number = f"OT-P-{work_order.id:04d}"

        db.commit()

        # Obtener estadísticas actualizadas
        stats = get_maintenance_statistics(maintenance_id, db)

        return {
            "success": True,
            "message": f"Orden {work_order.order_number} generada correctamente",
            "work_order": {
                "id": work_order.id,
                "order_number": work_order.order_number,
                "title": work_order.title,
                "status": work_order.status,
                "has_task_list": maintenance.task_list_id is not None,
                "task_list_name": maintenance.task_list.name if maintenance.task_list else None
            },
            "maintenance_stats": stats
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logger.error(f"Error generando orden para mantenimiento {maintenance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/maintenance/{maintenance_id}/preview-order")
def preview_order_from_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Previsualiza cómo se vería la orden de trabajo que se generaría
    desde un mantenimiento con TaskList.
    """
    try:
        maintenance = db.query(Maintenance).options(
            joinedload(Maintenance.machine),
            joinedload(Maintenance.task_list).joinedload(TaskList.steps)
        ).filter(Maintenance.id == maintenance_id).first()
        if not maintenance:
            raise HTTPException(status_code=404, detail="Mantenimiento no encontrado")

        # Generar orden (sin guardar en DB)
        preview_order = generate_work_order_from_task_list(maintenance, db)

        # Obtener información adicional de TaskList si existe
        task_list_info = None
        if maintenance.task_list:
            steps_count = len(maintenance.task_list.steps)
            total_time = sum(step.estimated_time_minutes or 0 for step in maintenance.task_list.steps)

            task_list_info = {
                "id": maintenance.task_list.id,
                "name": maintenance.task_list.name,
                "description": maintenance.task_list.description,
                "steps_count": steps_count,
                "total_estimated_minutes": total_time,
                "steps": [
                    {
                        "order": step.step_order,
                        "description": step.description,
                        "estimated_minutes": step.estimated_time_minutes
                    }
                    for step in sorted(maintenance.task_list.steps, key=lambda x: x.step_order)
                ]
            }

        return {
            "maintenance": {
                "id": maintenance.id,
                "title": maintenance.title,
                "frequency": maintenance.frequency,
                "machine_name": maintenance.machine.nombre if maintenance.machine else "Desconocida"
            },
            "preview_order": {
                "title": preview_order.title,
                "work_type": preview_order.work_type,
                "details": preview_order.details,
                "estimated_creation_date": preview_order.created_at.isoformat()
            },
            "task_list": task_list_info,
            "has_task_list": maintenance.task_list_id is not None
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error previsualizando orden para mantenimiento {maintenance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# backend/src/routes.py - Añadir estos endpoints

@router.get("/maintenance-backlog", response_model=List[BacklogRead])
def get_backlog_items(
    status: Optional[str] = None,
    machine_id: Optional[int] = None,
    section_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        logger.info(f"Getting backlog items with filters: status={status}, machine_id={machine_id}, section_id={section_id}")
        
        from src.models.maintenance_backlog import MaintenanceBacklog, BacklogStatus
        
        query = db.query(MaintenanceBacklog).options(
            joinedload(MaintenanceBacklog.machine),
            joinedload(MaintenanceBacklog.section),
            joinedload(MaintenanceBacklog.created_by),
            joinedload(MaintenanceBacklog.assigned_to)
        )
        
        if status:
            try:
                # Para debug
                logger.info(f"Attempting to filter by status: {status}")
                status_enum = BacklogStatus(status)
                query = query.filter(MaintenanceBacklog.status == status_enum)
            except ValueError as e:
                logger.warning(f"Invalid status value: {status}. Error: {e}")
        
        if machine_id:
            query = query.filter(MaintenanceBacklog.machine_id == machine_id)
        if section_id:
            query = query.filter(MaintenanceBacklog.section_id == section_id)
        
        items = query.order_by(MaintenanceBacklog.created_at.desc()).all()
        logger.info(f"Found {len(items)} backlog items")
        return items
    except Exception as e:
        logger.error(f"Error in get_backlog_items: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/maintenance-backlog")
def create_backlog_item(
    data: BacklogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = MaintenanceBacklog(
        **data.dict(),
        created_by_id=current_user.id
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.post("/maintenance-backlog/{item_id}/convert")
def convert_to_work_order(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Convierte un item del backlog en una orden de trabajo"""
    item = db.query(MaintenanceBacklog).filter(MaintenanceBacklog.id == item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    
    # Crear orden de trabajo
    work_order = WorkOrder(
        title=item.title,
        details=item.description,
        work_type="Mejora",  # O el tipo que prefieras
        machine_id=item.machine_id,
        section_id=item.section_id,
        assigned_to_id=item.assigned_to_id,
        status="Pendiente",
        operator=current_user.username
    )
    
    db.add(work_order)
    db.flush()
    
    # Actualizar el item del backlog
    item.status = BacklogStatus.PLANNED
    item.actual_work_order_id = work_order.id
    
    db.commit()
    return {"success": True, "work_order_id": work_order.id}


# Añadir este endpoint a routes.py si no existe

@router.put("/maintenance-backlog/{item_id}", response_model=BacklogRead)
def update_backlog_item(
    item_id: int,
    data: BacklogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza un elemento del backlog de mantenimiento"""
    try:
        logger.info(f"Actualizando backlog item {item_id} por usuario {current_user.username}")
        
        # Buscar el item
        item = db.query(MaintenanceBacklog).filter(MaintenanceBacklog.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item del backlog no encontrado")
        
        # Verificar permisos (opcional: solo el creador o admin puede editar)
        can_edit = (
            current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"] or
            item.created_by_id == current_user.id
        )
        
        if not can_edit:
            raise HTTPException(status_code=403, detail="No tienes permisos para editar este item")
        
        # Actualizar solo los campos proporcionados
        update_data = data.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        # Actualizar timestamp
        item.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(item)
        
        logger.info(f"Backlog item {item_id} actualizado correctamente")
        return item
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando backlog item {item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/maintenance-backlog/{item_id}", response_model=BacklogRead)
def get_backlog_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene un elemento específico del backlog"""
    try:
        item = db.query(MaintenanceBacklog).options(
            joinedload(MaintenanceBacklog.machine),
            joinedload(MaintenanceBacklog.section),
            joinedload(MaintenanceBacklog.created_by),
            joinedload(MaintenanceBacklog.assigned_to)
        ).filter(MaintenanceBacklog.id == item_id).first()
        
        if not item:
            raise HTTPException(status_code=404, detail="Item del backlog no encontrado")
        
        return item
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error obteniendo backlog item {item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.delete("/maintenance-backlog/{item_id}", status_code=204)
def delete_backlog_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina un elemento del backlog de mantenimiento"""
    try:
        item = db.query(MaintenanceBacklog).filter(MaintenanceBacklog.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item del backlog no encontrado")
        
        # Verificar permisos
        can_delete = (
            current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"] or
            item.created_by_id == current_user.id
        )
        
        if not can_delete:
            raise HTTPException(status_code=403, detail="No tienes permisos para eliminar este item")
        
        # No eliminar si ya está convertido en orden de trabajo
        if item.actual_work_order_id:
            raise HTTPException(
                status_code=400, 
                detail="No se puede eliminar: ya se ha convertido en orden de trabajo"
            )
        
        db.delete(item)
        db.commit()
        
        logger.info(f"Backlog item {item_id} eliminado por usuario {current_user.username}")
        return None
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando backlog item {item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")



# --- Section lines 5940-6076 ---
# ---------------------------
# ENDPOINTS DE SOLICITUDES DE MANTENIMIENTO (TRIAGE)
# ---------------------------

@router.post("/maintenance-requests", response_model=MaintenanceRequestRead, status_code=201, summary="Crear Solicitud de Mantenimiento")
def create_maintenance_request(
    data: MaintenanceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crea una nueva solicitud de mantenimiento (Triage).
    """
    try:
        new_request = MaintenanceRequest(
            title=data.title,
            description=data.description,
            machine_id=data.machine_id,
            priority=data.priority,
            reported_by_id=current_user.id,
            status="Pendiente"
        )
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        
        # Cargar relaciones
        db.refresh(new_request, attribute_names=['reported_by', 'machine'])
        return new_request
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear solicitud de mantenimiento: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/maintenance-requests", response_model=List[MaintenanceRequestRead], summary="Listar Solicitudes de Mantenimiento")
def list_maintenance_requests(
    status: Optional[str] = Query(None, description="Filtrar por estado (Pendiente, Aprobada, Rechazada)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista las solicitudes de mantenimiento.
    """
    try:
        query = db.query(MaintenanceRequest).options(
            joinedload(MaintenanceRequest.reported_by),
            joinedload(MaintenanceRequest.machine)
        )
        
        if status:
            query = query.filter(MaintenanceRequest.status == status)
            
        return query.order_by(MaintenanceRequest.created_at.desc()).all()
    except Exception as e:
        logger.error(f"Error listeando solicitudes de mantenimiento: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.put("/maintenance-requests/{request_id}/review", response_model=MaintenanceRequestRead, summary="Revisar Solicitud (Aprobar/Rechazar)")
def review_maintenance_request(
    request_id: int,
    data: MaintenanceRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Revisa una solicitud. Si se aprueba, genera automáticamente una Orden de Trabajo.
    Requiere permisos de Jefe de Mantenimiento o Administrador.
    """
    allowed_roles = ["Administrador", "Jefe de Mantenimiento"]
    if current_user.role.nombre not in allowed_roles:
        raise HTTPException(status_code=403, detail="No tienes permisos para revisar solicitudes de mantenimiento.")
        
    try:
        m_req = db.query(MaintenanceRequest).options(
            joinedload(MaintenanceRequest.machine)
        ).filter(MaintenanceRequest.id == request_id).first()
        
        if not m_req:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
            
        if m_req.status != "Pendiente":
            raise HTTPException(status_code=400, detail="La solicitud ya ha sido revisada")

        m_req.status = data.status
        m_req.review_notes = data.review_notes
        if data.priority:
            m_req.priority = data.priority
        m_req.reviewed_at = datetime.utcnow()
        m_req.reviewed_by_id = current_user.id
        
        # Generar Orden de Trabajo si es Aprobada
        if data.status == "Aprobada":
            # Asignar a una sección por defecto si el usuario actual tiene una, sino requiere configuración adicional
            # Para este MVP se asume que se asigna a la sección del usuario que la aprueba o una por defecto
            section_id = current_user.section_id or 1 # Ajustar según modelo de negocio
            
            # Obtener línea de la máquina si existe
            line_id = m_req.machine.line_id if m_req.machine else 1 # Ajustar según modelo de negocio
            
            new_work_order = WorkOrder(
                title=f"[Triage] {m_req.title}",
                details=f"Solicitud original: {m_req.description}\n\nNotas de revisión: {data.review_notes or ''}",
                work_type="Correctivo", # Por defecto es un correctivo si viene de un operario
                section_id=section_id,
                line_id=line_id,
                machine_id=m_req.machine_id,
                operator=current_user.username,
                assigned_to_id=current_user.id, # Opcional: Asignar al que reportó o dejar vacío
                status="Pendiente",
                created_at=datetime.utcnow()
            )
            
            latest_order = db.query(WorkOrder).order_by(WorkOrder.id.desc()).first()
            next_id = (latest_order.id + 1) if latest_order else 1
            new_work_order.order_number = f"OT-{datetime.now().year}-{next_id:04d}"
            
            db.add(new_work_order)
            db.flush() # Para obtener el ID de la nueva OT
            
            m_req.work_order_id = new_work_order.id

        db.commit()
        db.refresh(m_req)
        db.refresh(m_req, attribute_names=['reported_by', 'machine'])
        
        return m_req

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error al revisar solicitud: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")



# --- Section lines 12142-12232 ---
@router.post("/maintenance/generate-automatic-orders")
def generate_automatic_maintenance_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Genera automáticamente órdenes de mantenimiento preventivo pendientes"""
    try:
        current_date = datetime.utcnow()
        
        # Buscar mantenimientos que necesitan generar órdenes
        pending_maintenances = db.query(Maintenance).filter(
            Maintenance.type == "Preventivo",
            Maintenance.is_completed == False,
            Maintenance.next_maintenance_date <= current_date
        ).all()
        
        orders_created = 0
        
        for maintenance in pending_maintenances:
            # Verificar si ya hay una orden generada reciente
            existing_order = db.query(WorkOrder).filter(
                WorkOrder.generated_from_maintenance_id == maintenance.id,
                WorkOrder.created_at >= (current_date - timedelta(days=30))
            ).first()
            
            if existing_order:
                continue  # Ya tiene una orden reciente
            
            # Obtener usuario asignado
            assigned_user_id = maintenance.assigned_user_id
            if not assigned_user_id:
                # Buscar usuario por rol
                if maintenance.assigned_role_id:
                    user_with_role = db.query(User).filter(
                        User.role_id == maintenance.assigned_role_id,
                        User.active == True
                    ).first()
                    assigned_user_id = user_with_role.id if user_with_role else None
                
                if not assigned_user_id:
                    # Usuario por defecto
                    default_user = db.query(User).filter(User.active == True).first()
                    assigned_user_id = default_user.id if default_user else 1
            
            # Crear orden vinculada correctamente
            work_order = WorkOrder(
                title=maintenance.title,
                details=maintenance.description,
                work_type="Preventivo",
                machine_id=maintenance.machine_id,
                operator="Sistema Automático",
                assigned_to_id=assigned_user_id,
                section_id=maintenance.machine.section_id if maintenance.machine else None,
                line_id=maintenance.machine.line_id if maintenance.machine else None,
                status="Pendiente",
                created_at=current_date,
                generated_from_maintenance_id=maintenance.id  # ✅ VINCULACIÓN CORRECTA
            )
            
            db.add(work_order)
            db.flush()
            
            # Generar número de orden
            work_order.order_number = f"OT-P-{work_order.id:04d}"
            
            # Actualizar próxima fecha de mantenimiento
            if maintenance.frequency == "Mensual":
                maintenance.next_maintenance_date = current_date + timedelta(days=30)
            elif maintenance.frequency == "Semanal":
                maintenance.next_maintenance_date = current_date + timedelta(days=7)
            elif maintenance.frequency == "Trimestral":
                maintenance.next_maintenance_date = current_date + timedelta(days=90)
            elif maintenance.frequency == "Semestral":
                maintenance.next_maintenance_date = current_date + timedelta(days=180)
            elif maintenance.frequency == "Anual":
                maintenance.next_maintenance_date = current_date + timedelta(days=365)
            
            orders_created += 1
        
        db.commit()
        
        return {
            "success": True,
            "orders_created": orders_created,
            "message": f"Se generaron {orders_created} órdenes de mantenimiento automáticamente"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error generando órdenes automáticas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
