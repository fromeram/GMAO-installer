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


# --- Section lines 3690-3792 ---
# ---------------------------
# ENDPOINTS DE PROVEEDORES
# ---------------------------

@router.get("/suppliers")
def get_suppliers(db: Session = Depends(get_db)):
    """Endpoint para obtener lista de proveedores"""
    try:
        sups = db.query(Supplier).all()
        return [
            {
                "id": s.id,
                "company": s.company,
                # --- CAMBIO AQUÍ ---
                "name": s.name,  # Cambiado de "nombre" a "name"
                # --------------------
                "phone": s.phone
            }
            for s in sups
        ]
    except Exception as e:
        # Es buena práctica loggear el error también
        logging.error(f"Error en get_suppliers: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al obtener proveedores")

@router.post("/suppliers")
def create_supplier_endpoint(data: SupplierCreate, db: Session = Depends(get_db), _admin=Depends(get_admin_user)):
    """
    Endpoint para crear proveedores
    """
    # Pasa data.model_dump() en lugar de data.dict() si usas Pydantic v2+
    return _create_supplier(data.dict(), db, _admin)
    #return _create_supplier(data.model_dump(), db, _admin) # Usar model_dump() para Pydantic v2

def _create_supplier(data: Dict[str, Any], db: Session, _admin=None):
    """
    Implementación interna para crear proveedor
    """
    try:
        # No necesitas .get con Pydantic, si el campo es obligatorio dará error antes
        # name = data.get("name", "")
        # company = data.get("company", "")
        # phone = data.get("phone", "")

        sup = Supplier(name=data["name"], company=data["company"], phone=data["phone"])
        db.add(sup)
        db.commit()
        db.refresh(sup)

        # --- CAMBIO AQUÍ (por consistencia) ---
        return {"id": sup.id, "name": sup.name, "company": sup.company, "phone": sup.phone} # Cambiado "nombre" a "name"
        # -------------------------------------
    except Exception as e:
        db.rollback()
        logging.error(f"Error en _create_supplier: {str(e)}")
        # Evita exponer detalles internos del error al cliente si no es necesario
        # raise HTTPException(status_code=500, detail=str(e))
        raise HTTPException(status_code=500, detail="Error interno al crear el proveedor")
    


@router.put("/suppliers/{supplier_id}")
def update_supplier_endpoint(
    supplier_id: int,
    data: SupplierUpdate, # Usa el modelo de actualización
    db: Session = Depends(get_db),
    _admin=Depends(get_admin_user)
):
    """
    Endpoint para actualizar un proveedor existente.
    """
    try:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")

        # Actualiza solo los campos proporcionados en `data`
        #update_data = data.model_dump(exclude_unset=True) # Pydantic v2
        update_data = data.dict(exclude_unset=True) # Pydantic v1  <-- CORRECTO PARA TU CASO

        for key, value in update_data.items():
            setattr(supplier, key, value)

        db.commit()
        db.refresh(supplier)

        # Devuelve el proveedor actualizado (consistente con GET)
        return {
            "id": supplier.id,
            "name": supplier.name,
            "company": supplier.company,
            "phone": supplier.phone
        }
    except HTTPException as http_exc:
        # Re-lanzar excepciones HTTP para que FastAPI las maneje
        raise http_exc
    except Exception as e:
        db.rollback()
        logging.error(f"Error en update_supplier_endpoint (ID: {supplier_id}): {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al actualizar el proveedor")



