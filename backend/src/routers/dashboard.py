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


# --- Section lines 8842-9116 ---
# --- ENDPOINTS DE DASHBOARD ---

@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Obtener estadísticas generales para el dashboard."""
    today = datetime.utcnow()
    first_day_current_month = datetime(today.year, today.month, 1)
    first_day_previous_month = (first_day_current_month - timedelta(days=1)).replace(day=1)
    
    # Filtrado según rol del usuario
    role_filter = True  # Sin filtro por defecto (admin)
    if current_user.role.nombre == "Jefe de Sección" and current_user.section_id:
        role_filter = WorkOrder.section_id == current_user.section_id
    
    # Contar órdenes pendientes
    pending_orders = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.status.in_(["Pendiente", "En revisión"]),
        role_filter
    ).scalar()
    
    # Contar órdenes en curso
    ongoing_orders = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.status == "En curso",
        role_filter
    ).scalar()
    
    # Contar órdenes completadas este mes
    completed_orders_current = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.status == "Cerrada",
        WorkOrder.finished_at >= first_day_current_month,
        role_filter
    ).scalar()
    
    # Contar órdenes completadas mes anterior (para calcular tendencia)
    completed_orders_previous = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.status == "Cerrada",
        WorkOrder.finished_at >= first_day_previous_month,
        WorkOrder.finished_at < first_day_current_month,
        role_filter
    ).scalar()
    
    # Calcular tendencia (% de cambio)
    if completed_orders_previous > 0:
        completed_orders_trend = ((completed_orders_current - completed_orders_previous) / completed_orders_previous) * 100
    else:
        completed_orders_trend = 100 if completed_orders_current > 0 else 0
    
    # Contar productos bajo stock mínimo
    low_stock_count = db.query(func.count(Inventory.id)).filter(
        Inventory.quantity <= Inventory.stock_minimo
    ).scalar()
    
    # Calcular promedios de métricas (MTBF, MTTR, disponibilidad)
    machines_query = db.query(Machine)
    if current_user.role.nombre == "Jefe de Sección" and current_user.section_id:
        machines_query = machines_query.filter(Machine.section_id == current_user.section_id)
    
    machines = machines_query.all()
    
    mtbf_values = []
    mttr_values = []
    availability_values = []
    
    for machine in machines:
        # Obtener métricas solo para máquinas con órdenes
        orders_count = db.query(func.count(WorkOrder.id)).filter(
            WorkOrder.machine_id == machine.id,
            WorkOrder.status == "Cerrada"
        ).scalar()
        
        if orders_count > 0:
            try:
                # Versión simplificada para calcular métricas
                metrics = get_machine_metrics(machine.id, "last_year", db, current_user)
                
                if metrics["mtbf"] > 0:
                    mtbf_values.append(metrics["mtbf"])
                if metrics["mttr"] > 0:
                    mttr_values.append(metrics["mttr"])
                if metrics["disponibilidad"] > 0:
                    availability_values.append(metrics["disponibilidad"])
            except Exception as e:
                # Ignorar errores en cálculos individuales
                logger.error(f"Error calculando métricas para máquina {machine.id}: {e}")
                continue
    
    # Calcular promedios
    mtbf_avg = statistics.mean(mtbf_values) if mtbf_values else 0
    mttr_avg = statistics.mean(mttr_values) if mttr_values else 0
    availability_avg = statistics.mean(availability_values) if availability_values else 0
    
    return {
        "pendingOrders": pending_orders,
        "ongoingOrders": ongoing_orders,
        "completedOrders": completed_orders_current,
        "completedOrdersTrend": round(completed_orders_trend, 1),
        "lowStockItems": low_stock_count,
        "mtbfAvg": round(mtbf_avg, 1),
        "mttrAvg": round(mttr_avg, 1),
        "availabilityAvg": round(availability_avg, 1)
    }

@router.get("/dashboard/pending-tasks", response_model=List[PendingTask])
def get_pending_tasks(
    limit: int = Query(10, description="Número máximo de tareas a devolver"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener lista de tareas pendientes para el dashboard."""
    try:
        # Filtrado según rol del usuario
        query = db.query(WorkOrder).options(
            joinedload(WorkOrder.machine_obj),
            joinedload(WorkOrder.assigned_to)
        ).filter(
            WorkOrder.status.in_(["Pendiente", "En curso", "En revisión"])
        )
        
        if current_user.role.nombre == "Jefe de Sección" and current_user.section_id:
            query = query.filter(WorkOrder.section_id == current_user.section_id)
        elif current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
            query = query.filter(WorkOrder.assigned_to_id == current_user.id)
        
        # Ordenar por estado y fecha de creación
        orders = query.order_by(
            case(
                (WorkOrder.status == "En curso", 1),
                (WorkOrder.status == "En revisión", 2),
                (WorkOrder.status == "Pendiente", 3),
                else_=4
            ),
            WorkOrder.created_at.asc()
        ).limit(limit).all()
        
        return orders
    except Exception as e:
        logger.error(f"Error en get_pending_tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/dashboard/maintenance-history", response_model=List[MaintenanceHistoryItem])
def get_maintenance_history(
    limit: int = Query(10, description="Número máximo de registros a devolver"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener historial de mantenimientos recientes para el dashboard."""
    # Filtrado según rol del usuario
    query = db.query(WorkOrder).options(
        joinedload(WorkOrder.machine_obj)
    ).filter(
        WorkOrder.status == "Cerrada",
        WorkOrder.finished_at.isnot(None)
    )
    
    if current_user.role.nombre == "Jefe de Sección" and current_user.section_id:
        query = query.filter(WorkOrder.section_id == current_user.section_id)
    elif current_user.role.nombre == "Mecánico":
        query = query.filter(WorkOrder.assigned_to_id == current_user.id)
    
    # Ordenar por fecha de cierre (más recientes primero)
    orders = query.order_by(WorkOrder.finished_at.desc()).limit(limit).all()
    
    return orders

@router.get("/dashboard/maintenance-by-month", response_model=List[MaintenanceByMonthItem])
def get_maintenance_by_month(
    months: int = Query(12, description="Número de meses a incluir"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener datos de mantenimientos agrupados por mes."""
    today = datetime.utcnow()
    start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    
    # Retroceder en el tiempo el número de meses especificado
    for _ in range(months - 1):
        start_date = (start_date.replace(day=1) - timedelta(days=1)).replace(day=1)
    
    # Filtrado según rol del usuario
    role_filter = True  # Sin filtro por defecto (admin)
    if current_user.role.nombre == "Jefe de Sección" and current_user.section_id:
        role_filter = WorkOrder.section_id == current_user.section_id
    
    # Obtener órdenes de trabajo en el rango de fechas
    orders = db.query(WorkOrder).filter(
        WorkOrder.created_at >= start_date,
        role_filter
    ).all()
    
    # Agrupar por mes y tipo de mantenimiento
    result = []
    current_date = start_date
    
    while current_date <= today:
        month_name = current_date.strftime("%b %Y")
        month_start = current_date
        month_end = current_date.replace(day=28) + timedelta(days=4)  # Asegurar que llegamos al siguiente mes
        month_end = month_end.replace(day=1) - timedelta(days=1)  # Último día del mes actual
        
        # Contar órdenes de cada tipo para este mes
        preventivo_count = 0
        correctivo_count = 0
        inspeccion_count = 0
        otros_count = 0
        
        for order in orders:
            if month_start <= order.created_at <= month_end:
                if order.work_type == "Preventivo":
                    preventivo_count += 1
                elif order.work_type == "Correctivo":
                    correctivo_count += 1
                elif order.work_type == "Inspección":
                    inspeccion_count += 1
                else:
                    otros_count += 1
        
        result.append({
            "month": month_name,
            "preventivo": preventivo_count,
            "correctivo": correctivo_count,
            "inspeccion": inspeccion_count,
            "otros": otros_count,
            "total": preventivo_count + correctivo_count + inspeccion_count + otros_count
        })
        
        # Avanzar al siguiente mes
        current_date = month_end + timedelta(days=1)
    
    return result

@router.get("/dashboard/maintenance-by-type", response_model=List[MaintenanceByTypeItem])
def get_maintenance_by_type(
    period: str = Query("all", description="Periodo a considerar: all, year, month"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener distribución de mantenimientos por tipo."""
    today = datetime.utcnow()
    
    # Determinar fecha de inicio según periodo
    if period == "month":
        start_date = today.replace(day=1)
    elif period == "year":
        start_date = today.replace(month=1, day=1)
    else:  # "all"
        start_date = datetime(2000, 1, 1)  # Fecha muy antigua para incluir todo
    
    # Filtrado según rol del usuario
    role_filter = True  # Sin filtro por defecto (admin)
    if current_user.role.nombre == "Jefe de Sección" and current_user.section_id:
        role_filter = WorkOrder.section_id == current_user.section_id
    
    # Obtener todas las órdenes en el periodo
    query = db.query(
        WorkOrder.work_type,
        func.count(WorkOrder.id).label('count')
    ).filter(
        WorkOrder.created_at >= start_date,
        role_filter
    ).group_by(WorkOrder.work_type)
    
    orders_by_type = query.all()
    
    # Formatear resultado para gráfico de pastel
    result = []
    for work_type, count in orders_by_type:
        result.append({
            "name": work_type,
            "value": count
        })
    
    return result

# --- FIN ENDPOINTS DE DASHBOARD ---

