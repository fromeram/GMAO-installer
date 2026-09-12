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


# --- Section lines 9117-9209 ---
# ---  ENDPOINTS ALERTAS --- 
@router.get("/alerts", response_model=List[Dict[str, Any]])
def get_alerts(
    user_id: Optional[int] = None,
    unresolved_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene alertas recientes para un usuario o para todos."""
    try:
        query = db.query(Alert)
        
        # Filtrar por estado de resolución
        if unresolved_only:
            query = query.filter(Alert.resolved == False)
        
        # Si se solicitan alertas de un usuario específico
        if user_id:
            # Asegurarse de que quien solicita las alertas de otro usuario tiene permisos
            is_admin = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
            if user_id != current_user.id and not is_admin:
                raise HTTPException(status_code=403, detail="No tiene permisos para ver alertas de otros usuarios")
            
            query = query.filter(Alert.users.any(User.id == user_id))
        else:
            # Si no es administrador, solo mostrar alertas para el usuario actual
            if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
                query = query.filter(Alert.users.any(User.id == current_user.id))
        
        # Ordenar por fecha (más recientes primero)
        alerts = query.order_by(Alert.created_at.desc()).all()
        
        # Formatear resultados
        result = []
        for alert in alerts:
            formatted_alert = {
                "id": alert.id,
                "type": alert.type,
                "message": alert.message,
                "entity_type": alert.entity_type,
                "entity_id": alert.entity_id,
                "severity": alert.severity,
                "created_at": alert.created_at.isoformat(),
                "resolved": alert.resolved,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                "resolved_by": {
                    "id": alert.resolved_by.id,
                    "username": alert.resolved_by.username
                } if alert.resolved_by else None
            }
            result.append(formatted_alert)
        
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error al obtener alertas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.put("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marca una alerta como resuelta."""
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
        
        # Comprobar si el usuario puede resolver esta alerta
        is_admin = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
        is_for_user = any(user.id == current_user.id for user in alert.users)
        
        if not (is_admin or is_for_user):
            raise HTTPException(status_code=403, detail="No tiene permisos para resolver esta alerta")
        
        # Marcar como resuelta
        alert.resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by_id = current_user.id
        
        db.commit()
        
        return {"success": True, "message": "Alerta marcada como resuelta"}
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logger.error(f"Error al resolver alerta {alert_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
