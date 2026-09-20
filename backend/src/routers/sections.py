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


# --- Section lines 1851-2023 ---
# ---------------------------
# ENDPOINTS DE SECCIONES Y LÍNEAS
# ---------------------------

from sqlalchemy.orm import joinedload


@router.get("/secciones")
async def get_secciones(db: Session = Depends(get_db)):
    try:
        print("Iniciando consulta de secciones...")  # Debug
        secs = db.query(Section).options(
            joinedload(Section.lines).joinedload(Line.machines)
        ).all()
        
        result = []
        for s in secs:
            section_data = {
                "id": s.id,
                "nombre": s.nombre,
                "lines": []
            }
            print(f"Procesando sección {s.nombre} con {len(s.lines)} líneas")  # Debug
            
            for ln in s.lines:
                line_data = {
                    "id": ln.id,
                    "nombre": ln.nombre,
                    "machines": []
                }
                print(f"Procesando línea {ln.nombre} con {len(ln.machines)} máquinas")  # Debug
                
                for m in ln.machines:
                    machine_data = {
                        "id": m.id,
                        "nombre": m.nombre,
                        "modelo": m.modelo,
                        "marca": m.marca,
                        "numero_serie": m.numero_serie
                    }
                    line_data["machines"].append(machine_data)
                section_data["lines"].append(line_data)
            result.append(section_data)
        
        print("Resultado final:", result)  # Debug
        return result
    except Exception as e:
        print(f"Error en get_secciones: {str(e)}")  # Debug
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/secciones")
async def create_seccion(data: SectionCreate, db: Session = Depends(get_db), _admin=Depends(get_admin_user)):
    exist = db.query(Section).filter(Section.nombre == data.nombre).first()
    if exist:
        raise HTTPException(status_code=400, detail="La sección ya existe.")
    sec = Section(nombre=data.nombre)
    db.add(sec)
    db.commit()
    db.refresh(sec)
    return {"id": sec.id, "nombre": sec.nombre}

@router.put("/secciones/{seccion_id}")
def update_seccion(seccion_id: int, data: SectionUpdate, db: Session = Depends(get_db), _admin=Depends(get_admin_user)):
    sec = db.query(Section).filter(Section.id == seccion_id).first()
    if not sec:
        raise HTTPException(status_code=404, detail="Sección no encontrada.")
    sec.nombre = data.nombre
    db.commit()
    db.refresh(sec)
    return {"id": sec.id, "nombre": sec.nombre}

@router.delete("/secciones/{seccion_id}")
def delete_seccion(seccion_id: int, db: Session = Depends(get_db), _admin=Depends(get_admin_user)):
    sec = db.query(Section).filter(Section.id == seccion_id).first()
    if not sec:
        raise HTTPException(status_code=404, detail="Sección no encontrada.")
    db.delete(sec)
    db.commit()
    return {"message": "Sección eliminada correctamente."}

@router.get("/lines/section/{section_id}")
def get_lines_for_section(
    section_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene todas las líneas asociadas a una sección específica.
    """
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Sección no encontrada.")
    
    lines = db.query(Line).filter(Line.section_id == section_id).all()
    
    return [
        {
            "id": line.id, 
            "nombre": line.nombre
        } 
        for line in lines
    ]

@router.post("/secciones/line")
def create_line(data: LineCreate, db: Session = Depends(get_db), _admin=Depends(get_admin_user)):
    sec = db.query(Section).filter(Section.id == data.section_id).first()
    if not sec:
        raise HTTPException(status_code=404, detail="Sección no encontrada.")
    existing_line = db.query(Line).filter(Line.nombre.ilike(data.nombre), Line.section_id == data.section_id).first()
    if existing_line:
        raise HTTPException(status_code=400, detail="La línea ya existe en esta sección.")
    ln = Line(nombre=data.nombre, section_id=data.section_id)
    db.add(ln)
    db.commit()
    db.refresh(ln)
    return {"id": ln.id, "nombre": ln.nombre, "section_id": ln.section_id}

@router.put("/secciones/line/{line_id}")
def update_line(line_id: int, data: LineUpdate, db: Session = Depends(get_db), _admin=Depends(get_admin_user)):
    ln = db.query(Line).filter(Line.id == line_id).first()
    if not ln:
        raise HTTPException(status_code=404, detail="Línea no encontrada.")
    existing_line = db.query(Line).filter(Line.nombre.ilike(data.nombre), Line.section_id == ln.section_id, Line.id != line_id).first()
    if existing_line:
        raise HTTPException(status_code=400, detail="La línea ya existe en esta sección.")
    ln.nombre = data.nombre
    db.commit()
    db.refresh(ln)
    return {"id": ln.id, "nombre": ln.nombre, "section_id": ln.section_id}

@router.delete("/secciones/line/{line_id}")
def delete_line(line_id: int, db: Session = Depends(get_db), _admin=Depends(get_admin_user)):
    ln = db.query(Line).filter(Line.id == line_id).first()
    if not ln:
        raise HTTPException(status_code=404, detail="Línea no encontrada.")
    db.delete(ln)
    db.commit()
    return {"message": "Línea eliminada correctamente."}

# ---------------------------
# ENDPOINT DE INFO PLANTA
# ---------------------------

@router.get("/infoplanta")
def get_info_planta(db: Session = Depends(get_db)):
    sections = db.query(Section).all()
    result = []
    for s in sections:
        lines_data = []
        for ln in s.lines:
            machines_data = []
            for mach in ln.machines:
                machines_data.append({
                    "id": mach.id,
                    "nombre": mach.nombre,
                    "modelo": mach.modelo,
                    "marca": mach.marca,
                    "numero_serie": mach.numero_serie
                })
            lines_data.append({
                "id": ln.id,
                "nombre": ln.nombre,
                "machines": machines_data
            })
        result.append({
            "id": s.id,
            "nombre": s.nombre,
            "lines": lines_data
        })
    return result

