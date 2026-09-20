# routes.py
"""
Rutas de la API para la gestión de usuarios, roles, secciones, líneas, máquinas, mantenimiento, proveedores, inventario, almacenes, órdenes, etc.
Cada endpoint está debidamente protegido según los roles.
"""

# routes.py (Sección de importaciones actualizada)

import logging
from datetime import datetime, timedelta, date
import calendar # Necesario para calcular días del mes
import time # <-- Asegúrate de tener esta importación al principio del archivo
import json # <-- Asegúrate de tener esta importación
from decimal import Decimal # <<<--- Añadido para Pydantic con Numeric/Decimal
from dateutil.relativedelta import relativedelta
from fastapi import Request, APIRouter, HTTPException, Depends, File, UploadFile, Form, BackgroundTasks, Body, status, Query
from typing import List, Optional, Union, Literal, Any, Dict, ForwardRef
from pydantic import BaseModel, ValidationError, validator, Field # <-- Añadido Field
from src.ai.document_processor import DocumentProcessor # Asegúrate que esta ruta es correcta
import aiofiles
import os
import requests # Asegúrate que se usa o elimina si no

# Importaciones SQLAlchemy
from sqlalchemy.orm import Session, joinedload, contains_eager
from sqlalchemy import func, distinct # <<<--- Añadido para query de nombres distintos
from src.database import get_db

# Importaciones de Autenticación
from src.auth import (
    create_access_token,
    verify_password,
    get_current_user,
    get_admin_user,
    get_jefe_seccion_user, # Asegúrate si este se usa realmente
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Importaciones de Modelos SQLAlchemy
from src.models.base import Base # Asumiendo que importas Base aquí o en los modelos individuales
from src.models.role import Role
from src.models.section import Section
from src.models.line import Line
from src.models.machine import Machine
from src.models.supplier import Supplier
from src.models.inventory import Inventory
from src.models.associations import MachinePartAssociation 
from src.models.maintenance import Maintenance
from src.models.work_order import WorkOrder, FailureCode, CauseCode, RemedyCode # <-- IMPORTANTE
from src.models.warehouse import Warehouse
from src.models.user import User
from src.models.document import Document
from src.models.supplier_product_price import SupplierProductPrice # <<<--- Añadido nuevo modelo
from src.models.task_list import TaskList   # <-- AÑADIR ESTA LÍNEA
from src.models.task_step import TaskStep     # <-- AÑADIR ESTA LÍNEA
from src.models.shift_pattern import ShiftPattern     # <-- AÑADIR ESTA LÍNEA
from src.models.shift_assignment import ShiftAssignment 
from src.models.absence import Absence # <-- Añadir esta CUANDO creemos endpoints para ausencias
logging.basicConfig(level=logging.INFO) # Configuración básica (opcional pero útil)
logger = logging.getLogger(__name__)


# URL del proxy (si se sigue usando)
PROXY_URL = "http://192.168.1.62:5000"


router = APIRouter()

# =======================================================================
# === INICIO SECCIÓN MODELOS PYDANTIC (REORGANIZADA v4 - ESPEREMOS FINAL) ===
# =======================================================================

# 1. Autenticación y Usuarios
# ===========================
class LoginModel(BaseModel):
    username: str; password: str
class Token(BaseModel):
    access_token: str; token_type: str
class RoleCreate(BaseModel):
    id: int; nombre: str
class UserCreate(BaseModel):
    username: str; password: str; role_id: int; section_id: Optional[int] = None
class UserReadBasic(BaseModel):
    id: int; username: str
    class Config: orm_mode = True

# 2. Modelos Básicos Reutilizables (Definir antes de usarlos)
# =========================================================
class SectionReadBasic(BaseModel):
    id: int; nombre: str
    class Config: orm_mode = True
class LineReadBasic(BaseModel):
    id: int; nombre: str
    class Config: orm_mode = True
class MachineReadBasic(BaseModel):
    id: int; nombre: str
    class Config: orm_mode = True
class InventoryReadBasic(BaseModel):
     id: int; product_name: str
     class Config: orm_mode = True
class CodeBase(BaseModel):
    code: str = Field(..., max_length=50); description: str = Field(..., max_length=255)
class CodeRead(CodeBase):
    id: int
    class Config: orm_mode = True
class SupplierInfo(BaseModel):
     id: int; name: Optional[str] = None; company: Optional[str] = None
     class Config: orm_mode = True
class WarehouseInfo(BaseModel):
    id: int; name: Optional[str] = None
    class Config: orm_mode = True
class ShiftPatternBase(BaseModel):
    name: str; description: Optional[str] = None; pattern_sequence: str = Field(..., min_length=1)
class ShiftPatternReadBasic(ShiftPatternBase):
    id: int; cycle_length_days: int
    class Config: orm_mode = True
class TaskStepBase(BaseModel):
    step_order: int = Field(..., ge=1); description: str
    estimated_time_minutes: Optional[int] = Field(None, ge=0)
class TaskStepRead(TaskStepBase):
    id: int; task_list_id: int
    class Config: orm_mode = True

# 3. Secciones y Líneas
# =====================
class SectionCreate(BaseModel): nombre: str
class SectionUpdate(BaseModel): nombre: str
class LineCreate(BaseModel): nombre: str; section_id: int
class LineUpdate(BaseModel): nombre: str

# 4. Máquinas y BOM (Lista de Materiales)
# ========================================
class MaquinaCreate(BaseModel):
    nombre: str; modelo: str; marca: str; numero_serie: str; line_id: int; section_id: int; criticidad: Optional[str] = None
class MaquinaUpdate(BaseModel):
    nombre: Optional[str] = None; modelo: Optional[str] = None; marca: Optional[str] = None; numero_serie: Optional[str] = None
    line_id: Optional[int] = None; section_id: Optional[int] = None; criticidad: Optional[str] = None
class MaquinaRead(BaseModel):
    id: int; nombre: str; modelo: str; marca: str; numero_serie: str; line_id: int; section_id: int; criticidad: Optional[str] = None
    class Config: orm_mode = True
class MachinePartCreate(BaseModel):
    inventory_id: int; quantity: int = Field(..., ge=1)
class MachinePartRead(BaseModel):
    inventory_id: int; quantity: int; part: InventoryReadBasic # Definido en #2
    class Config: orm_mode = True
# --- Modelo para "Dónde se usa" (usa MachineReadBasic de #2) ---
class PartUsageInMachine(BaseModel):
    quantity: int
    machine: MachineReadBasic
    class Config: orm_mode = True
# ---------------------------------------------------------------

# 5. Códigos FCR
# ==============
# CodeBase y CodeRead ya definidos en #2
class CodeCreate(CodeBase): pass
class CodeUpdate(BaseModel): code: Optional[str]=Field(None,max_length=50); description: Optional[str]=Field(None,max_length=255)

# 6. Listas de Tareas y Pasos
# ===========================
# TaskStepBase y TaskStepRead ya definidos en #2
class TaskStepCreate(TaskStepBase): pass
class TaskStepUpdate(BaseModel):
    step_order: Optional[int] = Field(None, ge=1); description: Optional[str] = None
    estimated_time_minutes: Optional[int] = Field(None, ge=0)
class TaskListBase(BaseModel):
    name: str; description: Optional[str] = None; applies_to_type: Optional[str] = None
class TaskListCreate(TaskListBase):
    steps: List[TaskStepCreate] = []
class TaskListUpdate(BaseModel):
    name: Optional[str] = None; description: Optional[str] = None; applies_to_type: Optional[str] = None
class TaskListReadBasic(TaskListBase): # Redefinido aquí para claridad
    id: int
    class Config: orm_mode = True
class TaskListRead(TaskListBase): # Usa TaskStepRead definido en #2
    id: int; steps: List[TaskStepRead] = []
    class Config: orm_mode = True

# 7. Órdenes de Trabajo (Work Orders)
# ==================================
class WorkOrderBase(BaseModel):
    title: str; details: Optional[str]=None; work_type: Literal["Preventivo", "Correctivo", "Inspección", "Mejora", "Modificación", "Seguridad"]
    section_id: int; line_id: int; machine_id: int; operator: str; assigned_to_id: int
    repuesto_id: Optional[int]=None; quantity_used: Optional[int]=Field(default=0, ge=0); imagen_url: Optional[str]=None
class WorkOrderCreate(WorkOrderBase): status: Optional[Literal["Pendiente"]]="Pendiente"
class WorkOrderCompleteUpdate(BaseModel):
    status: Optional[Literal["Pendiente", "En curso", "En revisión", "Cerrada"]]=None
    failure_code_id: Optional[int]=None; cause_code_id: Optional[int]=None; remedy_code_id: Optional[int]=None
    actual_start_time: Optional[datetime]=None # Mantengo datetime
    actual_end_time: Optional[datetime]=None   # Mantengo datetime
    downtime_hours: Optional[float]=Field(default=None, ge=0)
    completion_notes: Optional[str]=None; title: Optional[str]=None; details: Optional[str]=None
    work_type: Optional[Literal["Preventivo", "Correctivo", "Inspección", "Mejora", "Modificación", "Seguridad"]]=None
    section_id: Optional[int]=None; line_id: Optional[int]=None; machine_id: Optional[int]=None
    assigned_to_id: Optional[int]=None; repuesto_id: Optional[int]=None
    quantity_used: Optional[int]=Field(default=None, ge=0); imagen_url: Optional[str]=None
    class Config: orm_mode = True
class WorkOrderRead(WorkOrderBase):
    id: int; order_number: Optional[str]=None; status: str; created_at: Optional[datetime]=None; finished_at: Optional[datetime]=None
    actual_start_time: Optional[datetime]=None; actual_end_time: Optional[datetime]=None
    downtime_hours: Optional[float]=None # Ajustado a float
    completion_notes: Optional[str]=None
    failure_code: Optional[CodeRead]=None; cause_code: Optional[CodeRead]=None; remedy_code: Optional[CodeRead]=None
    assigned_to: Optional[UserReadBasic]=None; machine: Optional[MachineReadBasic]=Field(None, alias='machine_obj')
    section: Optional[SectionReadBasic]=None; line: Optional[LineReadBasic]=None; repuesto: Optional[InventoryReadBasic]=None
    class Config: orm_mode=True; allow_population_by_field_name=True

# 8. Inventario, Almacenes
# ========================
class WarehouseCreate(BaseModel): name: str
# WarehouseInfo ya definido en #2
class InventoryBase(BaseModel):
    product_name: str; quantity: int; warehouse_id: int; price: float
    supplier_id: Optional[int]=None; discount: Optional[float]=Field(default=0.0, ge=0, le=100)
    class Config: orm_mode=True
class InventarioCreate(InventoryBase): pass
class InventarioUpdate(BaseModel):
    product_name: Optional[str]=None; quantity: Optional[int]=None; warehouse_id: Optional[int]=None
    price: Optional[float]=None; supplier_id: Optional[int]=None; discount: Optional[float]=Field(default=None, ge=0, le=100)
class InventoryReportItem(BaseModel): # Usa WarehouseInfo
    id: int; product_name: str; quantity: int # Nombres OK
    almacen: Optional[WarehouseInfo]=None; proveedor: Optional[str]=None
    price: float; discount: Optional[float]=None # Nombres OK
    class Config: orm_mode=True

# 9. Proveedores y Precios Proveedor
# ==================================
class SupplierCreate(BaseModel): name: str; company: str; phone: str
# SupplierInfo ya definido en #2
class SupplierUpdate(BaseModel): name: Optional[str]=None; company: Optional[str]=None; phone: Optional[str]=None
class SupplierPriceBase(BaseModel):
    product_name: str; supplier_id: int; warehouse_id: Optional[int]=None; price: Decimal
    discount: Optional[Decimal]=Field(default=Decimal('0.0'), ge=0, le=100)
    # Validadores...
    @validator('discount', pre=True, always=True)
    def validate_discount(cls, v): # ... (código igual) ...
        if v is None: return Decimal('0.0'); v_dec = Decimal(str(v));
        if not (Decimal('0.0') <= v_dec <= Decimal('100.0')): raise ValueError('Discount must be between 0.0 and 100.0')
        return v_dec
    @validator('price', pre=True, always=True)
    def validate_price(cls, v): # ... (código igual) ...
        v_dec = Decimal(str(v));
        if v_dec < Decimal('0.0'): raise ValueError('Price cannot be negative')
        return v_dec
    class Config: orm_mode = True; json_encoders = { Decimal: float }
class SupplierPriceCreate(SupplierPriceBase): pass
class SupplierPriceUpdate(BaseModel):
    product_name: Optional[str]=None; supplier_id: Optional[int]=None; warehouse_id: Optional[int]=None
    price: Optional[Decimal]=None; discount: Optional[Decimal]=None
    # Validadores opcionales...
    @validator('discount', pre=True, always=True)
    def validate_discount_optional(cls, v): # ... (código igual) ...
         if v is None: return v; v_dec = Decimal(str(v));
         if not (Decimal('0.0') <= v_dec <= Decimal('100.0')): raise ValueError('Discount must be between 0.0 and 100.0')
         return v_dec
    @validator('price', pre=True, always=True)
    def validate_price_optional(cls, v): # ... (código igual) ...
        if v is None: return v; v_dec = Decimal(str(v));
        if v_dec < Decimal('0.0'): raise ValueError('Price cannot be negative')
        return v_dec
    class Config: orm_mode = True; json_encoders = { Decimal: float }
class SupplierPrice(SupplierPriceBase): # Usa SupplierInfo y WarehouseInfo
    id: int; last_updated: datetime; supplier: Optional[SupplierInfo]=None; warehouse: Optional[WarehouseInfo]=None
    class Config: orm_mode=True; json_encoders = { Decimal: float }

# 10. Mantenimiento Preventivo
# ===========================
class MantenimientoPreventivoCreate(BaseModel):
    title: str; description: str; maquina_id: int; frecuencia: str; fechaInicio: str # O date
    notification_interval: int; assigned_role_id: Optional[int]=None; assigned_user_id: Optional[int]=None

# 11. Patrones de Turno
# ======================
# ShiftPatternBase y ShiftPatternReadBasic ya definidos en #2
class ShiftPatternCreate(ShiftPatternBase): pass
class ShiftPatternUpdate(BaseModel):
    name: Optional[str]=None; description: Optional[str]=None; pattern_sequence: Optional[str]=Field(None, min_length=1)
class ShiftPatternRead(ShiftPatternBase):
    id: int; cycle_length_days: int
    class Config: orm_mode = True

# 12. Asignaciones de Turno
# ==========================
class ShiftAssignmentBase(BaseModel):
    user_id: int; pattern_id: int; reference_date: date; offset_days: int = Field(..., ge=0)
class ShiftAssignmentCreate(ShiftAssignmentBase): pass
class ShiftAssignmentRead(ShiftAssignmentBase):
    id: int; user: UserReadBasic; pattern: ShiftPatternReadBasic # Usan los ReadBasic definidos antes
    class Config: orm_mode = True

# 13. Ausencias
# =============
class AbsenceBase(BaseModel):
    user_id: int; start_date: date; end_date: date
    absence_type: Literal['V', 'B', 'A', 'F']; notes: Optional[str] = None
    @validator('end_date')
    def end_date_must_be_after_start_date(cls, end_date, values):
        start_date = values.get('start_date');
        if start_date and end_date < start_date: raise ValueError('End date cannot be before start date')
        return end_date
class AbsenceCreate(AbsenceBase): pass
class AbsenceRead(AbsenceBase):
    id: int; created_at: date
    class Config: orm_mode = True

# 14. Inicialización (InitData)
# =============================
class InitData(BaseModel):
    roles: List[RoleCreate]; users: List[UserCreate]; sections: List[SectionCreate]
    lines: List[LineCreate]; machines: List[MaquinaCreate]; suppliers: List[SupplierCreate]
    warehouses: List[WarehouseCreate]; inventory: List[InventarioCreate]
    maintenances: List[MantenimientoPreventivoCreate]; work_orders: List[WorkOrderCreate]

# ================================================================
# === FIN SECCIÓN MODELOS PYDANTIC (REORGANIZADA v4) ===
# ================================================================

# ... (Aquí empiezan tus endpoints @router...) ...

# ---------------------------
# ENDPOINTS DE AUTENTICACIÓN Y USUARIOS
# ---------------------------

@router.post("/token")
async def login_for_access_token(data: LoginModel, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == data.username).first()
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Usuario no encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(data.password, user.password):
            raise HTTPException(
                status_code=401,
                detail="Contraseña incorrecta",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.username,
                "role": user.role.nombre if user.role else None
            }, 
            expires_delta=access_token_expires
        )

        # Devolvemos también los datos del usuario
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_data": {
                "id": user.id,
                "username": user.username,
                "role": user.role.nombre if user.role else None,
                "section": user.section.nombre if user.section else None
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/users")
def create_user(data: UserCreate, db: Session = Depends(get_db), _admin=Depends(get_admin_user)):
    # Validación mejorada del role_id
    if not isinstance(data.role_id, int):
        raise HTTPException(status_code=400, detail="El ID del rol debe ser un número entero")

    role = db.query(Role).filter(Role.id == data.role_id).first()
    if not role:
        raise HTTPException(status_code=400, detail=f"Rol con ID {data.role_id} no existe")

    # Resto del código sin cambios...
    hashed = get_password_hash(data.password)
    
    new_user = User(
        username=data.username,
        password=hashed,
        role_id=data.role_id,
        section_id=data.section_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "username": new_user.username,
        "role": role.nombre,
        "section": new_user.section.nombre if new_user.section else None
    }


@router.get("/users/me")
def get_my_user(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role.nombre if current_user.role else None,  # String
        "section": current_user.section.nombre if current_user.section else None  # String
    }



@router.get("/users")
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # ... (lógica existente)
    if (current_user.role and current_user.role.nombre == "Jefe de Sección"):
        users = db.query(User).filter(User.section_id == current_user.section_id).all()
    else:
        users = db.query(User).all()
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "username": u.username,
            "role": u.role.nombre if u.role else None,  # Cambiado a string
            "section": u.section.nombre if u.section else None,
            "role_id": u.role_id  # Mantenemos el ID para edición
        })
    return result


@router.put("/users/{user_id}", summary="Actualizar un usuario")
def update_user(
    user_id: int,
    user_data: UserUpdate, # Usa el nuevo modelo
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # Solo Admin puede editar por ahora?
):
    """Actualiza el rol o sección de un usuario existente."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    update_data = user_data.dict(exclude_unset=True)
    if not update_data:
         raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar.")

    fields_updated = []
    for key, value in update_data.items():
        # Validar IDs si se proporcionan
        if key == "role_id" and value is not None:
            role = db.query(Role).filter(Role.id == value).first()
            if not role: raise HTTPException(status_code=400, detail=f"Rol ID {value} no existe.")
        if key == "section_id" and value is not None:
            section = db.query(Section).filter(Section.id == value).first()
            if not section: raise HTTPException(status_code=400, detail=f"Sección ID {value} no existe.")
        # Validar unicidad de username si cambia
        if key == "username" and value != db_user.username:
             existing = db.query(User).filter(User.username == value).first()
             if existing: raise HTTPException(status_code=400, detail="El nombre de usuario ya existe.")

        setattr(db_user, key, value)
        fields_updated.append(key)

    try:
        db.commit()
        db.refresh(db_user)
        # Devolver datos consistentes con GET /users
        return {
            "id": db_user.id,
            "username": db_user.username,
            "role": db_user.role.nombre if db_user.role else None,
            "section": db_user.section.nombre if db_user.section else None,
            "role_id": db_user.role_id,
            "section_id": db_user.section_id # Añadir section_id para consistencia
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando usuario {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al actualizar usuario.")



@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Solo administradores pueden eliminar
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db.delete(user)
    db.commit()
    return {"success": True, "message": "Usuario eliminado"}


# ---------------------------
# ENDPOINTS DE ROLES
# ---------------------------

@router.get("/roles")
def list_roles(db: Session = Depends(get_db), _admin=Depends(get_admin_user)):
    roles = db.query(Role).all()
    return [{"id": r.id, "nombre": r.nombre} for r in roles]

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

# ---------------------------
# ENDPOINTS DE MAQUINAS
# ---------------------------

@router.get("/maquinas", response_model=List[MaquinaRead]) # <-- Cambiado response_model
def get_maquinas(db: Session = Depends(get_db)):
    # Devolver directamente la lista de objetos SQLAlchemy,
    # FastAPI se encargará de convertirlos usando MaquinaRead
    machines = db.query(Machine).all()
    return machines

@router.post("/maquinas", response_model=MaquinaRead) # <-- Cambiado response_model
def create_maquina(data: MaquinaCreate, db: Session = Depends(get_db), _admin=Depends(get_admin_user)):
    # ... (validaciones de sección, línea, numero_serie igual que antes) ...
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
        criticidad=data.criticidad # <-- AÑADIDO: Guardar criticidad
    )
    db.add(mach)
    db.commit()
    db.refresh(mach)
    # FastAPI convierte mach a MaquinaRead automáticamente
    return mach

@router.put("/maquinas/{machine_id}", response_model=MaquinaRead) # <-- Cambiado response_model
def update_maquina(
    machine_id: int,
    data: MaquinaUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin_user)
):
    mach = db.query(Machine).filter(Machine.id == machine_id).first()
    if not mach:
        raise HTTPException(status_code=404, detail="Máquina no encontrada.")

    update_data = data.dict(exclude_unset=True) # Obtener solo campos enviados

    # Validar número de serie único si se cambia
    if "numero_serie" in update_data and update_data["numero_serie"] != mach.numero_serie:
        existing_mach = db.query(Machine).filter(Machine.numero_serie == update_data["numero_serie"]).first()
        if existing_mach:
            raise HTTPException(status_code=400, detail="Ya existe otra máquina con ese número de serie.")

    # Validar línea y sección si se cambian
    # (la lógica que tenías estaba bien, solo ajustada para usar update_data)
    new_section_id = update_data.get("section_id", mach.section_id)
    new_line_id = update_data.get("line_id", mach.line_id)

    if new_section_id != mach.section_id or new_line_id != mach.line_id:
         sec = db.query(Section).filter(Section.id == new_section_id).first()
         if not sec:
              raise HTTPException(status_code=400, detail="La nueva sección no existe.")
         ln = db.query(Line).filter(Line.id == new_line_id, Line.section_id == new_section_id).first()
         if not ln:
              raise HTTPException(status_code=400, detail="La nueva línea no existe en la nueva sección.")

    # Actualizar todos los campos proporcionados usando setattr
    for key, value in update_data.items():
        setattr(mach, key, value) # Actualiza nombre, modelo, marca, numero_serie, line_id, section_id, criticidad si vienen en update_data

    db.commit()
    db.refresh(mach)
    # FastAPI convierte mach a MaquinaRead automáticamente
    return mach

@router.delete("/maquinas/{machine_id}")
def delete_maquina(
    machine_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin_user) # O el rol que deba poder eliminar
):
    mach = db.query(Machine).options(
        joinedload(Machine.maintenances), # Cargar relaciones para comprobar
        joinedload(Machine.work_orders)
    ).filter(Machine.id == machine_id).first()

    if not mach:
        raise HTTPException(status_code=404, detail="Máquina no encontrada.")

    # --- ¡IMPORTANTE! Comprobar dependencias ---
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
    # --------------------------------------------
    # Si quieres permitir el borrado en cascada (peligroso), necesitarías configurar
    # la relación en machine.py con cascade="all, delete-orphan" y/o configurar
    # ON DELETE CASCADE en la base de datos. Por defecto, es más seguro prevenirlo.
    # Alternativamente, podrías eliminar manualmente las dependencias aquí antes de
    # eliminar la máquina, o permitir poner la máquina en estado "inactivo".

    db.delete(mach)
    db.commit()
    return {"message": "Máquina eliminada correctamente."}

@router.get(
    "/maquinas/{machine_id}/history",
    response_model=List[WorkOrderRead], # Devuelve una lista de OTs detalladas
    summary="Obtener historial de órdenes de trabajo para una máquina"
)
def get_machine_history(
    machine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Requiere login
):
    """
    Obtiene la lista completa de órdenes de trabajo asociadas a una
    máquina específica, ordenada por fecha de creación descendente.
    Incluye detalles anidados gracias a WorkOrderRead.
    """
    # Verificar primero que la máquina existe
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Máquina con ID {machine_id} no encontrada."
        )

    # Consultar órdenes de trabajo filtrando por machine_id
    # Usar joinedload para cargar relaciones eficientemente y evitar N+1 queries
    # Cargar todas las relaciones que necesita el modelo WorkOrderRead
    history = db.query(WorkOrder).options(
        joinedload(WorkOrder.assigned_to),
        joinedload(WorkOrder.machine_obj), # Alias 'machine' en Pydantic
        joinedload(WorkOrder.section),
        joinedload(WorkOrder.line),
        joinedload(WorkOrder.repuesto),
        joinedload(WorkOrder.failure_code),
        joinedload(WorkOrder.cause_code),
        joinedload(WorkOrder.remedy_code)
    ).filter(WorkOrder.machine_id == machine_id)\
     .order_by(WorkOrder.created_at.desc())\
     .all()

    logger.info(f"Encontradas {len(history)} órdenes para historial de máquina ID {machine_id}")
    # FastAPI se encarga de la conversión usando response_model=List[WorkOrderRead]
    return history



@router.get(
    "/maquinas/{machine_id}/parts",
    response_model=List[MachinePartRead], # <- Usa el modelo definido en este archivo
    summary="Obtener lista de repuestos (BOM) para una máquina"
)
def get_machine_parts(machine_id: int, db: Session = Depends(get_db)):
    """Obtiene la lista de repuestos asociados a una máquina específica."""
    # Verificar si la máquina existe primero
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")

    # Consultar las asociaciones cargando la información del repuesto relacionado
    associations = db.query(MachinePartAssociation).options(
        joinedload(MachinePartAssociation.part) # Carga eficiente de Inventory
    ).filter(MachinePartAssociation.machine_id == machine_id).all()

    # FastAPI/Pydantic convertirán 'associations' a List[MachinePartRead]
    # Siempre que la relación 'part' en MachinePartAssociation y el modelo
    # InventoryReadBasic estén definidos correctamente.
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




# ---------------------------
# ENDPOINTS DE MANTENIMIENTO
# ---------------------------

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
def get_all_maintenance(start: str = None, end: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Maintenance)
    if current_user.role.nombre == "Jefe de Sección":
        query = query.join(Machine).filter(Machine.section_id == current_user.section_id)
    if start and end:
        try:
            sdt = datetime.strptime(start, "%Y-%m-%d")
            edt = datetime.strptime(end, "%Y-%m-%d")
            query = query.filter(Maintenance.created_at >= sdt, Maintenance.created_at <= edt)
        except:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")
    maints = query.all()
    result = []
    for m in maints:
        machineName = db.query(Machine).filter(Machine.id == m.machine_id).first()
        result.append({
            "id": m.id,
            "title": m.title,
            "type": m.type,
            "description": m.description,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "machineName": machineName.nombre if machineName else "Desconocida"
        })
    return result

@router.get("/mantenimiento-preventivo")
def get_mantenimiento_preventivo(db: Session = Depends(get_db)):
    try:
        maintenances = db.query(Maintenance).filter(Maintenance.type == "Preventivo").all()
        result = []

        for m in maintenances:
            try:
                # Obtener la máquina
                machine = db.query(Machine).filter(Machine.id == m.machine_id).first()
                
                # Obtener línea y sección si existe la máquina
                line = None
                section = None
                if machine:
                    line = db.query(Line).filter(Line.id == machine.line_id).first()
                    if line:
                        section = db.query(Section).filter(Section.id == line.section_id).first()

                # Obtener usuario o rol asignado
                assigned_user = None
                assigned_role = None
                if m.assigned_user_id:
                    assigned_user = db.query(User).filter(User.id == m.assigned_user_id).first()
                if m.assigned_role_id:
                    assigned_role = db.query(Role).filter(Role.id == m.assigned_role_id).first()

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
                    "assigned_user": {
                        "id": assigned_user.id,
                        "username": assigned_user.username
                    } if assigned_user else None,
                    "assigned_role": {
                        "id": assigned_role.id,
                        "nombre": assigned_role.nombre
                    } if assigned_role else None
                }
                result.append(maintenance_data)
            except Exception as e:
                print(f"Error procesando mantenimiento {m.id}: {str(e)}")
                continue

        return result
    except Exception as e:
        print(f"Error general en get_mantenimiento_preventivo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
        assigned_user_id=data.assigned_user_id
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
    days_ahead: int = 1,  # Por defecto alertas para próximos 1 días
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = datetime.utcnow().date()
    end_date = today + timedelta(days=days_ahead)
    
    alerts = db.query(Maintenance).filter(
        Maintenance.next_maintenance_date.between(today, end_date),
        Maintenance.generated_order_id.is_(None)
    ).all()
    
    return [
        {
            "id": m.id,
            "title": m.title,
            "machine": m.machine.nombre,
            "due_date": m.next_maintenance_date.isoformat(),
            "assigned_to": m.assigned_user.username if m.assigned_user else m.assigned_role.nombre
        } for m in alerts
    ]



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



# --- FIN ENDPOINTS LISTAS DE TAREAS ---


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



# ---------------------------
# ENDPOINTS DE INVENTARIO Y ALMACENES (CORREGIDOS)
# ---------------------------

@router.get("/inventario")
def get_inventario(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.query(Inventory).options(joinedload(Inventory.warehouse)).all()
    res = []
    total_value = 0
    for it in items:
        item_value = it.quantity * it.price
        total_value += item_value
        sup = db.query(Supplier).filter(Supplier.id == it.supplier_id).first()
        res.append({
            "id": it.id,
            "nombre": it.product_name,
            "cantidad": it.quantity,
            "almacen": it.warehouse.name if it.warehouse else "Sin almacén",  # Cambiado a warehouse
            "precio": it.price if current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"] else "****",
            "valor_total": item_value if current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"] else "****",
            "proveedor": sup.company if sup else None
        })
    
    return {
        "items": res,
        "total_value": total_value if current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"] else "****"
    }

@router.get("/inventario/reporte", response_model=List[InventoryReportItem])
def get_inventory_report_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Asegurar login
):
    """
    Obtiene los datos detallados del inventario para reportes.
    """
    logger.debug("Accediendo a /inventario/reporte...") # Usar logger en lugar de print
    try:
        items = db.query(Inventory).options(
            joinedload(Inventory.warehouse), # Carga almacén
            joinedload(Inventory.supplier)   # Carga proveedor
        ).order_by(Inventory.product_name).all()
        logger.debug(f"Encontrados {len(items)} items en inventario.")

        # FastAPI/Pydantic con orm_mode=True puede convertir directamente
        # la lista de objetos SQLAlchemy 'items' a List[InventoryReportItem]
        # si las relaciones y los modelos Pydantic (InventoryReportItem, WarehouseInfo)
        # están correctamente definidos.
        # No necesitamos construir la lista manualmente.

        logger.debug(f"Devolviendo {len(items)} items para el reporte (conversión Pydantic automática).")
        return items # <-- Devolver directamente la lista de objetos SQLAlchemy

    except Exception as e:
        logger.error(f"Error al obtener datos de inventario para reporte: {e}", exc_info=True) # exc_info=True da más detalle
        raise HTTPException(status_code=500, detail="Error interno al obtener datos de inventario para reporte")



@router.get(
    "/inventory/{inventory_id}/usage", # O puedes usar /parts/{inventory_id}/usage si prefieres
    response_model=List[PartUsageInMachine],
    summary="Obtener máquinas que usan un repuesto específico"
)
def get_part_usage(
    inventory_id: int,
    db: Session = Depends(get_db)
    # Podrías añadir dependencia de usuario si quieres proteger esta ruta
    # current_user: User = Depends(get_current_user)
):
    """
    Dado el ID de un repuesto (inventory_id), devuelve una lista de las máquinas
    que lo utilizan y la cantidad utilizada en cada una.
    """
    # Verificar que el repuesto existe
    inventory_item = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repuesto con ID {inventory_id} no encontrado."
        )

    # Buscar todas las asociaciones para este repuesto, cargando la info de la máquina
    associations = db.query(MachinePartAssociation).options(
        joinedload(MachinePartAssociation.machine) # Carga eficiente de Máquina
    ).filter(MachinePartAssociation.inventory_id == inventory_id).all()

    # El response_model=List[PartUsageInMachine] junto con orm_mode=True
    # se encargará de convertir la lista de 'associations' al formato deseado,
    # incluyendo el objeto anidado 'machine' con los campos de MachineReadBasic.
    return associations


@router.get("/productos")
def get_productos(db: Session = Depends(get_db)):
    items = db.query(Inventory).options(
        joinedload(Inventory.warehouse),
        joinedload(Inventory.supplier)
    ).all()
    
    return [{
        "id": item.id,
        "nombre": item.product_name,
        "cantidad": item.quantity,
        "precio": item.price,
        "descuento": item.discount,  # Incluir descuento
        "almacen_id": item.warehouse_id,  # Nuevo campo
        "almacen": item.warehouse.name if item.warehouse else "Sin almacén",
        "proveedor": item.supplier.company if item.supplier else None
    } for item in items]

@router.post("/productos")
def create_producto_endpoint(data: InventarioCreate, db: Session = Depends(get_db), _admin=Depends(get_admin_user)):
    return _create_producto(data.dict(), db, _admin)

def _create_producto(data: Dict[str, Any], db: Session, _admin=None):
    """
    Crea un nuevo producto en inventario o actualiza la cantidad si ya existe.
    ADEMÁS: Actualiza o crea la entrada correspondiente en supplier_product_prices.
    """
    print("DEBUG: Iniciando _create_producto...") # Debug inicio función
    try:
        # --- Extraer datos del inventario ---
        product_name = data.get("product_name", "")
        # Asegurar que quantity y price se tratan como números desde el principio
        try:
             quantity = int(data.get("quantity", 0))
             price = float(data.get("price", 0))
        except (ValueError, TypeError):
             raise ValueError("La cantidad y el precio deben ser números válidos.")

        warehouse_id = int(data.get("warehouse_id")) # Asume que siempre viene
        supplier_id = data.get("supplier_id") # Puede ser None
        discount_input = data.get("discount")
        discount = None

        if discount_input is not None and discount_input != "":
            try:
                discount_val = float(discount_input)
                if 0 <= discount_val <= 100:
                    discount = discount_val
                else:
                     print(f"WARN: Descuento '{discount_input}' fuera de rango (0-100), usando 0.0.")
                     discount = 0.0
            except (ValueError, TypeError):
                print(f"WARN: Descuento '{discount_input}' no es un número válido, usando 0.0.")
                discount = 0.0 # Default a 0 si el valor no es válido
        else:
            discount = 0.0 # Default a 0 si no se proporciona o es None/""

        print(f"DEBUG: Datos extraídos - Prod: '{product_name}', Qty: {quantity}, WhID: {warehouse_id}, Price: {price}, SuppID: {supplier_id}, Disc: {discount}")

        # Validar que price y quantity no sean negativos
        if price < 0:
             raise ValueError("El precio no puede ser negativo")
        if quantity < 0:
             raise ValueError("La cantidad no puede ser negativa")

        # --- Validar Almacén ---
        print(f"DEBUG: Validando almacén ID: {warehouse_id}")
        almacen = db.query(Warehouse).get(warehouse_id)
        if not almacen:
            print(f"ERROR: Almacén ID {warehouse_id} no encontrado.")
            raise HTTPException(status_code=400, detail="Almacén no existe")
        print("DEBUG: Almacén válido.")

        # --- Validar Proveedor (si se proporciona) ---
        valid_supplier_id = None # Usar esta variable para la lógica posterior
        if supplier_id:
             # Intentar convertir a entero por si viene como string
             try:
                supplier_id_int = int(supplier_id)
                print(f"DEBUG: Validando proveedor ID: {supplier_id_int}")
                supplier = db.query(Supplier).get(supplier_id_int)
                if not supplier:
                    print(f"ERROR: Proveedor ID {supplier_id_int} no encontrado.")
                    raise HTTPException(status_code=400, detail="Proveedor no existe")
                valid_supplier_id = supplier_id_int # Guardar el ID válido
                print("DEBUG: Proveedor válido.")
             except (ValueError, TypeError):
                 print(f"ERROR: ID de proveedor '{supplier_id}' no es un entero válido.")
                 raise HTTPException(status_code=400, detail="ID de proveedor inválido.")
        else:
             print("DEBUG: No se proporcionó ID de proveedor.")
             valid_supplier_id = None # Asegurarse que es None

        # --- Lógica de Inventario: Buscar si ya existe ---
        print(f"DEBUG: Buscando inventario existente para Prod='{product_name}', WhID={warehouse_id}")
        existing_product_inventory = db.query(Inventory).filter(
            Inventory.product_name == product_name,
            Inventory.warehouse_id == warehouse_id,
        ).first()
        print(f"DEBUG: Inventario existente encontrado: {existing_product_inventory is not None}")

        inventory_item_to_update_prices = None
        result_message = {}

        if existing_product_inventory:
            # --- Actualizar Inventario Existente ---
            print(f"DEBUG: Actualizando cantidad para inventario ID: {existing_product_inventory.id}. Qty actual: {existing_product_inventory.quantity}, Añadiendo: {quantity}")
            existing_product_inventory.quantity += quantity
            # Decidir si actualizar otros campos al añadir stock
            if _admin or True: # Ajustar permiso si es necesario
                 print(f"DEBUG: Actualizando también precio={price}, descuento={discount}, proveedor ID={valid_supplier_id}")
                 existing_product_inventory.price = price
                 existing_product_inventory.discount = discount
                 existing_product_inventory.supplier_id = valid_supplier_id # Actualizar con el ID validado

            print("DEBUG: Intentando commit para actualización de inventario...")
            db.commit()
            print("DEBUG: Commit de inventario EXITOSO.")
            db.refresh(existing_product_inventory)
            inventory_item_to_update_prices = existing_product_inventory
            result_message = {"id": existing_product_inventory.id, "message": "Cantidad de producto actualizada", "warehouse_id": existing_product_inventory.warehouse_id}

        else:
            # --- Crear Nuevo Registro en Inventario ---
            print(f"DEBUG: Creando nuevo registro en inventario para '{product_name}'.")
            inv = Inventory(
                product_name=product_name,
                quantity=quantity,
                warehouse_id=warehouse_id,
                price=price,
                supplier_id=valid_supplier_id, # Usar el ID validado (puede ser None)
                discount=discount
            )
            db.add(inv)
            print("DEBUG: Intentando commit para nuevo registro de inventario...")
            db.commit()
            print("DEBUG: Commit de inventario EXITOSO.")
            db.refresh(inv)
            inventory_item_to_update_prices = inv
            result_message = {"id": inv.id, "message": "Producto creado en inventario"}


        # --- *** NUEVA LÓGICA: Actualizar/Crear en supplier_product_prices *** ---
        if inventory_item_to_update_prices and inventory_item_to_update_prices.supplier_id:
            current_supplier_id = inventory_item_to_update_prices.supplier_id
            current_product_name = inventory_item_to_update_prices.product_name
            print(f"DEBUG SPP: Iniciando lógica SPP para Prod='{current_product_name}', SuppID={current_supplier_id}")
            try:
                print(f"DEBUG SPP: Buscando precio existente para Prod='{current_product_name}', SuppID={current_supplier_id}")
                existing_supplier_price = db.query(SupplierProductPrice).filter(
                    SupplierProductPrice.product_name == current_product_name,
                    SupplierProductPrice.supplier_id == current_supplier_id
                ).first()
                print(f"DEBUG SPP: Precio existente encontrado: {existing_supplier_price is not None}")

                # Obtener los datos del inventario para actualizar/crear la oferta
                current_price = inventory_item_to_update_prices.price
                current_discount = inventory_item_to_update_prices.discount
                current_warehouse_id = inventory_item_to_update_prices.warehouse_id

                if existing_supplier_price:
                    # Actualizar la oferta existente
                    print(f"DEBUG SPP: Actualizando precio existente ID {existing_supplier_price.id} con Precio={current_price}, Descuento={current_discount}, WhID={current_warehouse_id}")
                    existing_supplier_price.price = current_price
                    existing_supplier_price.discount = current_discount
                    existing_supplier_price.warehouse_id = current_warehouse_id
                    existing_supplier_price.last_updated = datetime.utcnow() # Actualizar fecha explícitamente
                else:
                    # Crear nueva oferta si no existe
                    print(f"DEBUG SPP: Creando nuevo precio con Precio={current_price}, Descuento={current_discount}, WhID={current_warehouse_id}")
                    new_supplier_price = SupplierProductPrice(
                        product_name=current_product_name,
                        supplier_id=current_supplier_id,
                        warehouse_id=current_warehouse_id,
                        price=current_price,
                        discount=current_discount
                        # last_updated tiene valor por defecto al crear
                    )
                    db.add(new_supplier_price)

                print("DEBUG SPP: Intentando commit para supplier_product_prices...")
                db.commit() # Guardar los cambios en supplier_product_prices
                print("DEBUG SPP: Commit para supplier_product_prices EXITOSO.")

            except Exception as e_price:
                db.rollback() # Revertir si falla la actualización de precios
                print(f"DEBUG SPP: ERROR durante commit/actualización de supplier_product_prices: {str(e_price)}")
                logging.error(f"Error al actualizar/crear SupplierProductPrice para inv ID {inventory_item_to_update_prices.id}: {str(e_price)}")
                # result_message["warning"] = "No se pudo actualizar el catálogo de precios del proveedor." # Opcional

        elif inventory_item_to_update_prices:
             print(f"DEBUG SPP: OMITIDO - No hay supplier_id en inventario ID {inventory_item_to_update_prices.id}")


        # --- Devolver resultado de la operación de inventario ---
        print(f"DEBUG: _create_producto finalizado. Devolviendo: {result_message}")
        return result_message

    except ValueError as ve: # Capturar errores de validación propios
         # No necesita rollback si ocurre antes de la lógica de DB
         print(f"ERROR: ValueError en _create_producto: {str(ve)}")
         logging.error(f"Error de validación en _create_producto: {str(ve)}")
         raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException as he: # Re-lanzar HTTPExceptions (proveedor/almacén no existe)
        print(f"ERROR: HTTPException en _create_producto: {he.detail}")
        # No necesita rollback si ocurre antes del commit de inventario
        raise he
    except Exception as e:
        db.rollback() # Revertir cambios en inventario si ocurre otro error
        print(f"ERROR: Excepción inesperada en _create_producto: {str(e)}")
        logging.exception("Error inesperado en _create_producto:") # Log completo con traceback
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")




@router.put("/productos/{id}", response_model=Dict[str, Any])
def update_producto(
    id: int,
    data: InventarioUpdate, # Usa el modelo Pydantic adecuado
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Ajustar permisos si es necesario
):
    """
    Actualiza un registro de inventario existente.
    ADEMÁS: Actualiza o crea la entrada correspondiente en supplier_product_prices
    si se modifica información relevante (proveedor, precio, descuento).
    """
    print(f"DEBUG: Iniciando update_producto para ID: {id}")
    inv = db.query(Inventory).get(id)
    if not inv:
        print(f"ERROR: Producto con ID {id} no encontrado en inventario.")
        raise HTTPException(status_code=404, detail="Producto no encontrado en inventario")

    # Control de permisos (Ejemplo)
    can_edit_financials = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
    print(f"DEBUG: Usuario '{current_user.username}' (Rol: {current_user.role.nombre}). Puede editar financieros: {can_edit_financials}")
    if data.price is not None and not can_edit_financials:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar precios")
    if data.discount is not None and not can_edit_financials:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar descuentos")

    update_data = data.dict(exclude_unset=True) # Obtener solo los campos enviados
    print(f"DEBUG: Datos recibidos para actualizar: {update_data}")
    supplier_price_needs_update = False # Bandera para saber si actualizar precios proveedor
    original_supplier_id = inv.supplier_id # Guardar ID original por si cambia

    # Validar y aplicar cambios al objeto 'inv'
    for key, value in update_data.items():
        print(f"DEBUG: Procesando campo '{key}' con valor '{value}'")
        if value is None and key not in ['supplier_id', 'discount']: # Permitir establecer supplier y discount a None/0 explícitamente si se desea
             print(f"DEBUG: Omitiendo campo '{key}' porque el valor es None.")
             continue # Saltar campos None a menos que sea supplier_id o discount

        try:
            if key == "warehouse_id":
                warehouse = db.query(Warehouse).get(int(value))
                if not warehouse:
                    raise HTTPException(status_code=400, detail="Almacén no existe")
                inv.warehouse_id = int(value)
            elif key == "supplier_id":
                 if value is None: # Permitir desasignar proveedor
                      inv.supplier_id = None
                      supplier_price_needs_update = True # Aún necesita actualizarse si antes tenía proveedor
                 else:
                     supplier = db.query(Supplier).get(int(value))
                     if not supplier:
                        raise HTTPException(status_code=400, detail="Proveedor no existe")
                     inv.supplier_id = int(value)
                     supplier_price_needs_update = True
            elif key == "price":
                 price_val = float(value)
                 if price_val < 0:
                     raise ValueError("El precio no puede ser negativo")
                 inv.price = price_val
                 supplier_price_needs_update = True
            elif key == "discount":
                 if value is None: # Si se envía null explícitamente
                     discount_val = 0.0
                 else:
                     discount_val = float(value)
                     if not (0 <= discount_val <= 100):
                         raise ValueError("El descuento debe estar entre 0 y 100")
                 inv.discount = discount_val
                 supplier_price_needs_update = True
            elif key == "quantity":
                  qty_val = int(value)
                  if qty_val < 0:
                       raise ValueError("La cantidad no puede ser negativa")
                  inv.quantity = qty_val
            elif hasattr(inv, key): # Actualizar otros campos como product_name
                setattr(inv, key, value)
            else:
                 print(f"WARN: Campo '{key}' no reconocido en el modelo Inventory.")

        except (ValueError, TypeError) as val_err:
             print(f"ERROR: Error de tipo/valor procesando campo '{key}': {val_err}")
             raise HTTPException(status_code=400, detail=f"Valor inválido para el campo '{key}': {val_err}")
        except HTTPException: # Re-lanzar excepciones de validación de FK
             raise
        except Exception as e:
             print(f"ERROR: Excepción inesperada procesando campo '{key}': {e}")
             logging.exception(f"Error procesando campo {key} en update_producto:")
             raise HTTPException(status_code=500, detail=f"Error procesando campo '{key}'")


    try:
        # Guardar cambios en Inventario
        print("DEBUG: Intentando commit para actualización de inventario...")
        db.commit()
        print("DEBUG: Commit de inventario EXITOSO.")
        db.refresh(inv)

        # --- *** LÓGICA SPP TRAS ACTUALIZACIÓN DE INVENTARIO *** ---
        if supplier_price_needs_update and inv.supplier_id is not None:
            # Solo actualizar si se cambiaron datos relevantes Y el item AHORA tiene proveedor
            current_supplier_id = inv.supplier_id
            current_product_name = inv.product_name
            print(f"DEBUG SPP (Update): Iniciando lógica SPP para Prod='{current_product_name}', SuppID={current_supplier_id}")
            try:
                print(f"DEBUG SPP (Update): Buscando precio existente para Prod='{current_product_name}', SuppID={current_supplier_id}")
                existing_supplier_price = db.query(SupplierProductPrice).filter(
                    SupplierProductPrice.product_name == current_product_name,
                    SupplierProductPrice.supplier_id == current_supplier_id
                ).first()
                print(f"DEBUG SPP (Update): Precio existente encontrado: {existing_supplier_price is not None}")

                current_price = inv.price
                current_discount = inv.discount
                current_warehouse_id = inv.warehouse_id

                if existing_supplier_price:
                    print(f"DEBUG SPP (Update): Actualizando precio existente ID {existing_supplier_price.id} con Precio={current_price}, Descuento={current_discount}, WhID={current_warehouse_id}")
                    existing_supplier_price.price = current_price
                    existing_supplier_price.discount = current_discount
                    existing_supplier_price.warehouse_id = current_warehouse_id
                    existing_supplier_price.last_updated = datetime.utcnow()
                else:
                    # Crear si no existía para este proveedor/producto
                    print(f"DEBUG SPP (Update): Creando nuevo precio con Precio={current_price}, Descuento={current_discount}, WhID={current_warehouse_id}")
                    new_supplier_price = SupplierProductPrice(
                        product_name=current_product_name,
                        supplier_id=current_supplier_id,
                        warehouse_id=current_warehouse_id,
                        price=current_price,
                        discount=current_discount
                    )
                    db.add(new_supplier_price)

                print("DEBUG SPP (Update): Intentando commit para supplier_product_prices...")
                db.commit() # Commit específico para los cambios en SPP
                print("DEBUG SPP (Update): Commit para supplier_product_prices EXITOSO.")

            except Exception as e_price:
                db.rollback() # Revertir solo la parte de supplier_price si falla
                print(f"DEBUG SPP (Update): ERROR durante commit/actualización de supplier_product_prices: {str(e_price)}")
                logging.error(f"Error al actualizar/crear SupplierProductPrice tras update de inventario ID {inv.id}: {str(e_price)}")
                # Decidir si lanzar error o continuar

        elif supplier_price_needs_update and inv.supplier_id is None:
             print(f"DEBUG SPP (Update): OMITIDO - El inventario ID {inv.id} se quedó sin supplier_id tras la actualización.")
             # NOTA: Aquí NO borramos la entrada antigua de supplier_product_prices.
             # Si se quisiera borrar la oferta cuando se quita el proveedor del inventario,
             # se necesitaría buscar usando el 'original_supplier_id' y borrarla aquí.

        # --- Devolver el producto de inventario actualizado ---
        response_data = {
             "id": inv.id,
             "nombre": inv.product_name,
             "cantidad": inv.quantity,
             "almacen_id": inv.warehouse_id,
             "precio": float(inv.price) if inv.price is not None else None,
             "descuento": float(inv.discount) if inv.discount is not None else None,
             "supplier_id": inv.supplier_id
         }
        print(f"DEBUG: update_producto finalizado para ID: {id}. Devolviendo: {response_data}")
        return response_data

    except HTTPException as he:
         db.rollback() # Revertir si falla validación durante la actualización
         print(f"ERROR: HTTPException en update_producto: {he.detail}")
         raise he
    except Exception as e:
        db.rollback() # Revertir si falla el commit final
        print(f"ERROR: Excepción inesperada en update_producto (ID: {id}): {str(e)}")
        logging.exception(f"Error inesperado en update_producto (ID: {id}):")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al actualizar producto: {str(e)}")

@router.get("/products/distinct-names", response_model=List[str])
def get_distinct_product_names(db: Session = Depends(get_db)):
    """
    Obtiene una lista de nombres de productos únicos disponibles
    en el catálogo de precios de proveedores.
    """
    try:
        distinct_names = db.query(distinct(SupplierProductPrice.product_name)).order_by(SupplierProductPrice.product_name).all()
        # El resultado es una lista de tuplas [(name1,), (name2,)...], extraer el primer elemento
        return [name[0] for name in distinct_names]
    except Exception as e:
        print(f"Error fetching distinct product names: {e}")
        raise HTTPException(status_code=500, detail="Error interno al obtener nombres de productos.")

# Endpoint principal para comparar precios de un producto
@router.get("/supplier-prices/compare", response_model=List[SupplierPrice])
def get_supplier_prices_for_product(
    product_name: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las ofertas de precios de diferentes proveedores
    para un nombre de producto específico.
    """
    try:
        prices = db.query(SupplierProductPrice).options(
            joinedload(SupplierProductPrice.supplier), # Carga eficiente del proveedor
            joinedload(SupplierProductPrice.warehouse) # Carga eficiente del almacén
        ).filter(SupplierProductPrice.product_name.ilike(f"%{product_name}%")).all() # Usar ilike para búsqueda flexible (o == si quieres exacto)

        if not prices:
             print(f"No prices found for product name containing: {product_name}")
             # Devolver lista vacía es válido, no necesariamente un 404
             # raise HTTPException(status_code=404, detail="No se encontraron precios para este producto.")

        return prices
    except Exception as e:
        print(f"Error comparing prices for {product_name}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al comparar precios.")


# Endpoint para añadir una nueva oferta de precio
@router.post("/supplier-prices", response_model=SupplierPrice, status_code=201)
def create_supplier_price(
    price_data: SupplierPriceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # O rol adecuado (Jefe Mantenimiento?)
):
    """
    Crea una nueva entrada en el catálogo de precios de proveedores.
    Requiere rol de Administrador o Jefe de Mantenimiento.
    """
    # Verificar que el proveedor existe
    supplier = db.query(Supplier).filter(Supplier.id == price_data.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail=f"Proveedor con ID {price_data.supplier_id} no encontrado.")

    # Verificar que el almacén existe (si se proporciona)
    if price_data.warehouse_id:
        warehouse = db.query(Warehouse).filter(Warehouse.id == price_data.warehouse_id).first()
        if not warehouse:
             raise HTTPException(status_code=404, detail=f"Almacén con ID {price_data.warehouse_id} no encontrado.")

    # Opcional: Verificar si ya existe una entrada EXACTA (mismo producto, proveedor, almacén)
    # db_existing = db.query(SupplierProductPrice).filter(
    #     SupplierProductPrice.product_name == price_data.product_name,
    #     SupplierProductPrice.supplier_id == price_data.supplier_id,
    #     SupplierProductPrice.warehouse_id == price_data.warehouse_id
    # ).first()
    # if db_existing:
    #     raise HTTPException(status_code=400, detail="Ya existe una oferta para este producto, proveedor y almacén.")

    db_price = SupplierProductPrice(**price_data.dict())
    # last_updated se establece por defecto en el modelo/DB
    try:
        db.add(db_price)
        db.commit()
        db.refresh(db_price)
        # Cargar relaciones para la respuesta
        db.refresh(db_price, attribute_names=['supplier', 'warehouse'])
        return db_price
    except Exception as e:
        db.rollback()
        print(f"Error creating supplier price: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno al crear la oferta de precio: {e}")


# Endpoint para actualizar una oferta de precio existente
@router.put("/supplier-prices/{price_id}", response_model=SupplierPrice)
def update_supplier_price(
    price_id: int,
    price_data: SupplierPriceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # O rol adecuado
):
    """
    Actualiza una oferta de precio existente en el catálogo.
    Requiere rol de Administrador o Jefe de Mantenimiento.
    """
    db_price = db.query(SupplierProductPrice).filter(SupplierProductPrice.id == price_id).first()
    if not db_price:
        raise HTTPException(status_code=404, detail="Oferta de precio no encontrada.")

    # Validar proveedor/almacén si se cambian
    if price_data.supplier_id is not None and price_data.supplier_id != db_price.supplier_id:
         supplier = db.query(Supplier).filter(Supplier.id == price_data.supplier_id).first()
         if not supplier:
             raise HTTPException(status_code=404, detail=f"Proveedor con ID {price_data.supplier_id} no encontrado.")
         db_price.supplier_id = price_data.supplier_id # Actualizar solo si es válido

    if price_data.warehouse_id is not None and price_data.warehouse_id != db_price.warehouse_id:
         warehouse = db.query(Warehouse).filter(Warehouse.id == price_data.warehouse_id).first()
         if not warehouse:
             raise HTTPException(status_code=404, detail=f"Almacén con ID {price_data.warehouse_id} no encontrado.")
         db_price.warehouse_id = price_data.warehouse_id # Actualizar solo si es válido
    elif price_data.warehouse_id is None and 'warehouse_id' in price_data.dict(exclude_unset=True):
         # Permitir quitar el almacén estableciéndolo a None explícitamente
         db_price.warehouse_id = None


    update_data = price_data.dict(exclude_unset=True) # Obtener solo los campos enviados

    for key, value in update_data.items():
         # Actualizar solo si el campo existe en el modelo y el valor no es None (excepto warehouse_id)
         if hasattr(db_price, key) and (key == 'warehouse_id' or value is not None):
             setattr(db_price, key, value)

    # last_updated se actualiza automáticamente por onupdate en el modelo/DB
    # Si no, añadir: db_price.last_updated = datetime.datetime.utcnow()

    try:
        db.commit()
        db.refresh(db_price)
        db.refresh(db_price, attribute_names=['supplier', 'warehouse'])
        return db_price
    except Exception as e:
        db.rollback()
        print(f"Error updating supplier price {price_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno al actualizar la oferta: {e}")


# Endpoint para eliminar una oferta de precio
@router.delete("/supplier-prices/{price_id}", status_code=200)
def delete_supplier_price(
    price_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # O rol adecuado
):
    """
    Elimina una oferta de precio del catálogo.
    Requiere rol de Administrador o Jefe de Mantenimiento.
    """
    db_price = db.query(SupplierProductPrice).filter(SupplierProductPrice.id == price_id).first()
    if not db_price:
        raise HTTPException(status_code=404, detail="Oferta de precio no encontrada.")

    try:
        db.delete(db_price)
        db.commit()
        return {"message": "Oferta de precio eliminada correctamente"}
    except Exception as e:
        db.rollback()
        print(f"Error deleting supplier price {price_id}: {e}")
        # Podría fallar por restricciones si algo más depende de esta tabla (poco probable)
        raise HTTPException(status_code=500, detail=f"Error interno al eliminar la oferta: {e}")



@router.get("/almacenes")  # <--- Añadir este endpoint GET
def list_almacenes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    whs = db.query(Warehouse).all()
    return [{"id": w.id, "name": w.name} for w in whs]

@router.post("/almacenes")
async def create_almacen(
    request: Request, 
    data: WarehouseCreate, 
    db: Session = Depends(get_db), 
    _admin=Depends(get_admin_user)
):
    try:
        # Validación de nombre único
        exist = db.query(Warehouse).filter(Warehouse.name == data.name).first()
        if exist:
            raise HTTPException(400, "Ese almacén ya existe")
            
        # Crear almacén
        w = Warehouse(name=data.name)
        db.add(w)
        db.commit()
        
        return {"id": w.id, "name": w.name}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logging.error(f"Error creando almacén: {str(e)}")
        raise HTTPException(500, "Error interno del servidor")

@router.delete("/almacenes/{almacen_id}")
def delete_almacen(
    almacen_id: int, 
    db: Session = Depends(get_db), 
    _admin=Depends(get_admin_user)
):
    almacen = db.query(Warehouse).get(almacen_id)
    if not almacen:
        raise HTTPException(404, "Almacén no encontrado")
    
    # Verificar productos asociados
    if db.query(Inventory).filter(Inventory.warehouse_id == almacen_id).first():
        raise HTTPException(400, "El almacén tiene productos asignados")
    
    db.delete(almacen)
    db.commit()
    return {"message": "Almacén eliminado"}
@router.get("/partes")
def get_partes(fecha: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not fecha:
        fecha = datetime.utcnow().strftime("%Y-%m-%d")
    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
    except:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")

    inicio = datetime(fecha_dt.year, fecha_dt.month, fecha_dt.day)
    fin = inicio + timedelta(days=1)

    query = db.query(WorkOrder).filter(WorkOrder.created_at >= inicio, WorkOrder.created_at < fin)
    if current_user.role.nombre == "Jefe de Sección":
        query = query.filter(WorkOrder.section_id == current_user.section_id)
    
    orders = query.all()
    res = []
    for o in orders:
        res.append({
            "id": o.id,
            "title": o.title,
            "work_type": o.work_type,
            "section": o.section.nombre if o.section else None,
            "line": o.line.nombre if o.line else None,
            "machine": o.machine_obj.nombre if o.machine_obj else None,  # Corregido aquí
            "operator": o.operator,
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None
        })
    return res
# ---------------------------
# ENDPOINTS DE ORDENES
# ---------------------------

@router.get("/ordenes", response_model=List[WorkOrderRead], summary="Listar Órdenes de Trabajo")
def get_ordenes(
    start: Optional[str] = None,
    end: Optional[str] = None,
    status: Optional[str] = None, # Nuevo filtro por estado
    machine_id: Optional[int] = None, # Nuevo filtro por máquina
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene una lista de órdenes de trabajo, opcionalmente filtrada.
    Incluye datos relacionados como códigos, máquina, usuario asignado, etc.
    """
    try:
        # Carga ansiosa (eager loading) de relaciones para eficiencia
        query = db.query(WorkOrder).options(
            joinedload(WorkOrder.assigned_to),
            joinedload(WorkOrder.machine_obj),
            joinedload(WorkOrder.section),
            joinedload(WorkOrder.line),
            joinedload(WorkOrder.repuesto),
            joinedload(WorkOrder.failure_code), # <-- Cargar nuevo código
            joinedload(WorkOrder.cause_code),   # <-- Cargar nuevo código
            joinedload(WorkOrder.remedy_code)    # <-- Cargar nuevo código
        )

        # Filtros existentes y nuevos
        if current_user.role.nombre == "Jefe de Sección":
            query = query.filter(WorkOrder.section_id == current_user.section_id)
        # Podrías añadir más filtros por rol aquí si es necesario

        if start and end:
            try:
                sdt = datetime.strptime(start, "%Y-%m-%d")
                # Ajuste para incluir todo el día final
                edt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(WorkOrder.created_at >= sdt, WorkOrder.created_at < edt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")

        if status:
            # Validar status aquí si es necesario, aunque el modelo Pydantic ya lo hará en PUT
            if status not in ['Pendiente', 'En curso', 'En revisión', 'Cerrada']:
                 raise HTTPException(status_code=400, detail="Valor de estado inválido.")
            query = query.filter(WorkOrder.status == status)

        if machine_id:
            query = query.filter(WorkOrder.machine_id == machine_id)

        # Ordenar, por ejemplo por fecha de creación descendente
        orders = query.order_by(WorkOrder.created_at.desc()).all()

        # Pydantic se encargará de la conversión usando WorkOrderRead
        return orders
    except HTTPException as http_exc:
         raise http_exc # Re-lanzar excepciones HTTP
    except Exception as e:
         logger.error(f"Error en get_ordenes: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail="Error interno del servidor al obtener órdenes.")




@router.post("/ordenes")
def create_orden(data: WorkOrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        print("[DEBUG] Datos recibidos:", data.dict())
        
        # Validación del técnico
        print("[DEBUG] Validando técnico ID:", data.assigned_to_id)
        tecnico = db.query(User).filter(User.id == data.assigned_to_id).first()
        print("[DEBUG] Técnico encontrado:", tecnico)
        if tecnico:
            print("[DEBUG] Rol del técnico:", tecnico.role_id)

        # Validación de stock
        if data.repuesto_id:
            print("[DEBUG] Validando repuesto ID:", data.repuesto_id)
            inv = db.query(Inventory).filter(Inventory.id == data.repuesto_id).first()
            print("[DEBUG] Repuesto encontrado:", inv)
            if inv:
                print("[DEBUG] Stock actual:", inv.quantity)
                if inv.quantity < (data.quantity_used or 0):
                    print("[DEBUG] Stock insuficiente")
                    raise HTTPException(status_code=400, detail="Stock insuficiente")
                inv.quantity -= (data.quantity_used or 0)
                print("[DEBUG] Nuevo stock:", inv.quantity)

        # Crear la orden
        print("[DEBUG] Creando orden...")
        order = WorkOrder(
            title=data.title,
            details=data.details,
            work_type=data.work_type,
            section_id=data.section_id,
            line_id=data.line_id,
            machine_id=data.machine_id,
            operator=data.operator,
            assigned_to_id=data.assigned_to_id,
            status=data.status or "Pendiente",
            repuesto_id=data.repuesto_id,
            quantity_used=data.quantity_used or 0,
            imagen_url=data.imagen_url,
            created_at=datetime.utcnow()
        )

        # Obtener objetos relacionados
        sec = db.query(Section).filter(Section.id == data.section_id).first()
        if not sec:
            raise HTTPException(status_code=400, detail="Sección no encontrada")

        line = db.query(Line).filter(Line.id == data.line_id).first()
        if not line:
            raise HTTPException(status_code=400, detail="Línea no encontrada")

        machine = db.query(Machine).filter(Machine.id == data.machine_id).first()
        if not machine:
            raise HTTPException(status_code=400, detail="Máquina no encontrada")

        # Generar número de orden
        latest_order = db.query(WorkOrder).order_by(WorkOrder.id.desc()).first()
        next_number = 1 if not latest_order else latest_order.id + 1
        order.order_number = f"OT-{next_number:04d}"

        print("[DEBUG] Guardando orden en la base de datos...")
        db.add(order)
        db.commit()
        db.refresh(order)

        return {
            "success": True,
            "data": {
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
                "created_at": order.created_at.isoformat(),
                "finished_at": order.finished_at.isoformat() if order.finished_at else None,
                "imagen_url": order.imagen_url,
                "section": {"id": sec.id, "nombre": sec.nombre},
                "line": {"id": line.id, "nombre": line.nombre},
                "machine": {"id": machine.id, "nombre": machine.nombre},
                "assigned_to": {"id": tecnico.id, "username": tecnico.username} if tecnico else None,
                "repuesto_id": order.repuesto_id,
                "quantity_used": order.quantity_used
            }
        }

    except HTTPException as e:
        db.rollback()
        print("[ERROR] HTTPException:", str(e))
        raise e
    except Exception as e:
        db.rollback()
        print("[ERROR] Excepción no manejada:", str(e))
        raise HTTPException(status_code=500, detail=f"Error al crear la orden: {str(e)}")
    
    
    
    
@router.delete("/ordenes/{orden_id}")
def delete_orden(
    orden_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Verificar permisos del usuario
    if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
        raise HTTPException(
            status_code=403, 
            detail="No tienes permiso para eliminar órdenes"
        )
    
    # Buscar la orden
    order = db.query(WorkOrder).filter(WorkOrder.id == orden_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    # Si el usuario es Jefe de Sección, solo puede eliminar órdenes de su sección
    if current_user.role.nombre == "Jefe de Sección" and order.section_id != current_user.section_id:
        raise HTTPException(
            status_code=403, 
            detail="Solo puedes eliminar órdenes de tu sección"
        )

    try:
        # Eliminar la orden
        db.delete(order)
        db.commit()
        return {"success": True, "message": "Orden eliminada correctamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error al eliminar la orden: {str(e)}"
        )

@router.put("/ordenes/{orden_id}", response_model=WorkOrderRead, summary="Actualizar o Completar Orden de Trabajo")
async def update_complete_orden( # <-- Cambiado a async def para poder usar await request.json()
    orden_id: int,
    request: Request, # <-- Cambiado: Recibe Request en lugar de 'data' directamente
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza el estado y/o los detalles de cierre de una orden de trabajo...
    """
    # --- NUEVO: Parseo y Validación Manual con Try/Except ---
    try:
        body_json = await request.json() # Obtener el cuerpo JSON de la petición
        logger.info(f"Recibido JSON para PUT /ordenes/{orden_id}: {json.dumps(body_json)}") # Loggear lo recibido
        # Intentar validar con el modelo Pydantic
        data = WorkOrderCompleteUpdate(**body_json)
        logger.info("Validación Pydantic inicial del cuerpo OK.")
    except ValidationError as e:
        # ¡Si falla la validación, loggeamos el error detallado!
        logger.error(f"!!! Error de Validación Pydantic en PUT /ordenes/{orden_id} !!!")
        logger.error(e.json()) # Loggear los errores de Pydantic como JSON
        # Re-lanzamos como un error HTTP 422 (más estándar para validación) con los detalles
        raise HTTPException(status_code=422, detail=e.errors())
    except json.JSONDecodeError:
        logger.error(f"Error: Cuerpo de PUT /ordenes/{orden_id} no es JSON válido.")
        raise HTTPException(status_code=400, detail="Cuerpo de la petición no es JSON válido.")
    except Exception as e_parse:
         logger.error(f"Error inesperado al parsear/validar PUT /ordenes/{orden_id}: {e_parse}")
         raise HTTPException(status_code=400, detail=f"Error procesando datos: {e_parse}")
    # --- FIN NUEVO ---

    # Ahora podemos usar 'data' sabiendo que pasó la validación Pydantic
    logger.info(f"Actualizando/Completando OT {orden_id} por usuario {current_user.username}")
    logger.debug(f"Datos validados (modelo Pydantic): {data.dict()}")

    # Obtener la orden (sin cambios aquí)
    order = db.query(WorkOrder).options(
        joinedload(WorkOrder.assigned_to),
    ).filter(WorkOrder.id == orden_id).first()

    if not order:
        logger.warning(f"OT {orden_id} no encontrada.")
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    # --- Lógica de Permisos (sin cambios) ---
    can_close = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
    # ... (resto de la lógica de permisos igual) ...
    can_update_progress = (
         can_close or
         (current_user.role.nombre == "Jefe de Sección" and order.section_id == current_user.section_id) or
         (order.assigned_to_id == current_user.id)
    )
    if not can_update_progress:
        logger.warning(f"Usuario {current_user.username} sin permisos para actualizar OT {orden_id}.")
        raise HTTPException(status_code=403, detail="No tienes permiso para actualizar esta orden.")

    # --- Actualizar Campos (IMPORTANTE: Ahora usa 'data', no 'request') ---
    # Usar data.dict() porque 'data' ahora es el objeto Pydantic validado
    update_data = data.dict(exclude_unset=True) # Solo campos enviados y validados
    fields_updated = []
    logger.info(f"Campos a actualizar detectados: {list(update_data.keys())}")

    # Validar estado permitido ANTES de aplicarlo (si se envió)
    if data.status is not None: # Comprobar si 'status' vino en los datos
         if data.status not in ["Pendiente", "En curso", "En revisión", "Cerrada"]: # <- Movido aquí
             raise HTTPException(status_code=400, detail="Valor de estado proporcionado no es válido.")
         if data.status == "Cerrada" and not can_close:
             logger.warning(f"Usuario {current_user.username} sin permisos para cerrar OT {orden_id}.")
             raise HTTPException(status_code=403, detail="No tienes permiso para cerrar esta orden.")

    # Impedir modificar órdenes ya cerradas (excepto por Admin/Jefe Mant?)
    if order.status == "Cerrada" and not can_close:
         # Quizás permitir actualizar notas o códigos incluso si está cerrada? O bloquear todo?
         # Por ahora, bloqueamos si no es Admin/Jefe Mant y la orden YA está cerrada.
         # Podríamos permitir la actualización si el nuevo estado enviado NO es 'Cerrada'.
         # if 'status' in update_data and data.status != 'Cerrada': -> Permitir reabrir?
         logger.warning(f"Usuario {current_user.username} intentando modificar OT cerrada {orden_id}.")
         raise HTTPException(status_code=403, detail="No puedes modificar una orden ya cerrada.")


    for key, value in update_data.items():
        # Ya no necesitamos hasattr, Pydantic se aseguró que los campos existen en el modelo
        # Solo necesitamos aplicar los que vinieron en update_data

        # Validaciones específicas para IDs (sin cambios)
        if key == "failure_code_id" and value is not None and not db.query(FailureCode).get(value):
             raise HTTPException(status_code=400, detail=f"Código de Falla ID {value} no existe.")
        if key == "cause_code_id" and value is not None and not db.query(CauseCode).get(value):
             raise HTTPException(status_code=400, detail=f"Código de Causa ID {value} no existe.")
        if key == "remedy_code_id" and value is not None and not db.query(RemedyCode).get(value):
             raise HTTPException(status_code=400, detail=f"Código de Remedio ID {value} no existe.")
        if key == "repuesto_id" and value is not None and not db.query(Inventory).get(value):
             raise HTTPException(status_code=400, detail=f"Repuesto ID {value} no existe.")
        if key == "quantity_used" and value is not None and value < 0: # Validar cantidad
             raise HTTPException(status_code=400, detail="Cantidad usada no puede ser negativa.")
        # Añadir validación para otros IDs si es necesario (section, line, machine, assigned_to)

        # Aplicar el cambio al objeto SQLAlchemy 'order'
        setattr(order, key, value)
        fields_updated.append(key)


    logger.info(f"Campos actualizados para OT {orden_id}: {fields_updated}")

    # --- Lógica de Cierre/Reprogramación (sin cambios, pero ahora usa 'data.status') ---
    if data.status == "Cerrada" and order.finished_at is None:
        order.finished_at = datetime.utcnow()
        # ... (resto de la lógica de reprogramación igual) ...
        if order.work_type == "Preventivo":
            maintenance = db.query(Maintenance).filter(Maintenance.generated_order_id == orden_id).first()
            if maintenance:
                # ... (cálculo de next_date y delta igual) ...
                next_date = order.finished_at
                delta = None
                freq = maintenance.frequency
                # ... (if/elif para freq) ...
                if freq == "Diario": delta = timedelta(days=1)
                elif freq == "Semanal": delta = timedelta(weeks=1)
                elif freq == "Mensual": delta = relativedelta(months=1)
                elif freq == "Trimestral": delta = relativedelta(months=3)
                elif freq == "Semestral": delta = relativedelta(months=6)
                elif freq == "Anual": delta = relativedelta(years=1)

                if delta:
                     maintenance.next_maintenance_date = next_date + delta
                     maintenance.last_maintenance_date = order.finished_at
                     maintenance.generated_order_id = None
                     logger.info(f"Próximo mantenimiento {maintenance.id} programado para: {maintenance.next_maintenance_date}")
                else:
                     logger.warning(f"No se pudo calcular next_date para Maint ID {maintenance.id} con frecuencia '{freq}'")
            else:
                logger.warning(f"No se encontró el Mantenimiento Preventivo asociado a la OT {orden_id} para reprogramar.")

    elif data.status is not None and data.status != "Cerrada" and order.finished_at is not None:
         # Si se cambia estado a uno NO cerrado, y antes SÍ estaba cerrada, limpiar fecha fin? (Opcional)
         order.finished_at = None
         logger.info(f"OT {orden_id} reabierta (estado: {data.status}). Se limpió finished_at.")


    # --- Guardar cambios (sin cambios) ---
    try:
        db.commit()
        db.refresh(order)
        db.refresh(order, attribute_names=[
            'assigned_to', 'machine_obj', 'section', 'line',
            'repuesto', 'failure_code', 'cause_code', 'remedy_code'
        ])
        logger.info(f"OT {orden_id} actualizada/completada exitosamente.")
        return order

    except Exception as e:
        db.rollback()
        logger.error(f"Error al guardar cambios para OT {orden_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al guardar la orden: {e}")



# --- Failure Codes ---
@router.post("/failure-codes", response_model=CodeRead, status_code=201, summary="Crear Código de Falla")
def create_failure_code(
    code_data: CodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # O rol Jefe Mantenimiento?
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
def list_failure_codes(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Lista todos los códigos de falla disponibles."""
    return db.query(FailureCode).order_by(FailureCode.code).all()

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

# --- Cause Codes (Implementación análoga a Failure Codes) ---
@router.post("/cause-codes", response_model=CodeRead, status_code=201, summary="Crear Código de Causa")
def create_cause_code(code_data: CodeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    # (Lógica similar a create_failure_code, usando CauseCode)
    existing_code = db.query(CauseCode).filter(CauseCode.code == code_data.code).first()
    if existing_code: raise HTTPException(status_code=400, detail=f"Código de causa '{code_data.code}' ya existe.")
    db_code = CauseCode(**code_data.dict()); db.add(db_code); db.commit(); db.refresh(db_code); return db_code

@router.get("/cause-codes", response_model=List[CodeRead], summary="Listar Códigos de Causa")
def list_cause_codes(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(CauseCode).order_by(CauseCode.code).all()

@router.put("/cause-codes/{code_id}", response_model=CodeRead, summary="Actualizar Código de Causa")
def update_cause_code(code_id: int, code_data: CodeUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    # (Lógica similar a update_failure_code, usando CauseCode)
    db_code = db.query(CauseCode).filter(CauseCode.id == code_id).first();
    if not db_code: raise HTTPException(status_code=404, detail="Código causa no encontrado.");
    update_data = code_data.dict(exclude_unset=True);
    if not update_data: raise HTTPException(status_code=400, detail="No hay datos.");
    if 'code' in update_data and update_data['code'] != db_code.code:
        if db.query(CauseCode).filter(CauseCode.code == update_data['code'], CauseCode.id != code_id).first():
            raise HTTPException(status_code=400, detail=f"Código causa '{update_data['code']}' ya existe.");
    for k,v in update_data.items(): setattr(db_code,k,v);
    db.commit(); db.refresh(db_code); return db_code

@router.delete("/cause-codes/{code_id}", status_code=200, summary="Eliminar Código de Causa")
def delete_cause_code(code_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    # (Lógica similar a delete_failure_code, usando CauseCode)
    db_code = db.query(CauseCode).filter(CauseCode.id == code_id).first();
    if not db_code: raise HTTPException(status_code=404, detail="Código causa no encontrado.");
    db.delete(db_code); db.commit(); return {"success": True, "message": "Código de causa eliminado."}


# --- Remedy Codes (Implementación análoga a Failure Codes) ---
@router.post("/remedy-codes", response_model=CodeRead, status_code=201, summary="Crear Código de Remedio")
def create_remedy_code(code_data: CodeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    # (Lógica similar a create_failure_code, usando RemedyCode)
    existing_code = db.query(RemedyCode).filter(RemedyCode.code == code_data.code).first()
    if existing_code: raise HTTPException(status_code=400, detail=f"Código remedio '{code_data.code}' ya existe.")
    db_code = RemedyCode(**code_data.dict()); db.add(db_code); db.commit(); db.refresh(db_code); return db_code

@router.get("/remedy-codes", response_model=List[CodeRead], summary="Listar Códigos de Remedio")
def list_remedy_codes(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(RemedyCode).order_by(RemedyCode.code).all()

@router.put("/remedy-codes/{code_id}", response_model=CodeRead, summary="Actualizar Código de Remedio")
def update_remedy_code(code_id: int, code_data: CodeUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    # (Lógica similar a update_failure_code, usando RemedyCode)
    db_code = db.query(RemedyCode).filter(RemedyCode.id == code_id).first();
    if not db_code: raise HTTPException(status_code=404, detail="Código remedio no encontrado.");
    update_data = code_data.dict(exclude_unset=True);
    if not update_data: raise HTTPException(status_code=400, detail="No hay datos.");
    if 'code' in update_data and update_data['code'] != db_code.code:
         if db.query(RemedyCode).filter(RemedyCode.code == update_data['code'], RemedyCode.id != code_id).first():
             raise HTTPException(status_code=400, detail=f"Código remedio '{update_data['code']}' ya existe.");
    for k,v in update_data.items(): setattr(db_code,k,v);
    db.commit(); db.refresh(db_code); return db_code

@router.delete("/remedy-codes/{code_id}", status_code=200, summary="Eliminar Código de Remedio")
def delete_remedy_code(code_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    # (Lógica similar a delete_failure_code, usando RemedyCode)
    db_code = db.query(RemedyCode).filter(RemedyCode.id == code_id).first();
    if not db_code: raise HTTPException(status_code=404, detail="Código remedio no encontrado.");
    db.delete(db_code); db.commit(); return {"success": True, "message": "Código de remedio eliminado."}




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
            if order.repuesto_id:
                repuesto = db.query(Inventory).filter(Inventory.id == order.repuesto_id).first()
                if not repuesto:
                    raise HTTPException(status_code=400, detail=f"Repuesto con ID {order.repuesto_id} no existe.")
                if repuesto.quantity < order.quantity_used:
                    raise HTTPException(status_code=400, detail=f"No hay suficiente stock para el repuesto {repuesto.product_name}.")
                repuesto.quantity -= order.quantity_used
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


# Añadir estas rutas al final del archivo routes.py
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
async def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Verificar permisos
        if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
            raise HTTPException(status_code=403, detail="No tienes permisos para esta operación")
        
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        # Eliminar archivo físico
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
            
        # Eliminar registro de la BD
        db.delete(doc)
        db.commit()
        
        return {"success": True, "message": "Documento eliminado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
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
    

# --- ENDPOINTS PATRONES DE TURNO ---

@router.post(
    "/shift-patterns",
    response_model=ShiftPatternRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo patrón de turno"
)
def create_shift_pattern(
    pattern_data: ShiftPatternCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # Requiere Admin
):
    """Crea un nuevo patrón de turnos."""
    existing = db.query(ShiftPattern).filter(ShiftPattern.name == pattern_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Ya existe un patrón con el nombre '{pattern_data.name}'")

    if not pattern_data.pattern_sequence:
         raise HTTPException(status_code=400, detail="La secuencia del patrón no puede estar vacía.")

    db_pattern = ShiftPattern(
        name=pattern_data.name,
        description=pattern_data.description,
        pattern_sequence=pattern_data.pattern_sequence
        # cycle_length_days se calcula automáticamente en __init__ del modelo
    )
    try:
        db.add(db_pattern)
        db.commit()
        db.refresh(db_pattern)
        logger.info(f"Patrón de turno '{db_pattern.name}' (ID: {db_pattern.id}) creado.")
        return db_pattern
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando ShiftPattern: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al crear patrón: {e}")


@router.get(
    "/shift-patterns",
    response_model=List[ShiftPatternReadBasic], # Devuelve lista básica
    summary="Obtener todos los patrones de turno"
)
def list_shift_patterns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Cualquier usuario logueado puede verlos
):
    """Lista la información básica de todos los patrones de turno."""
    patterns = db.query(ShiftPattern).order_by(ShiftPattern.name).all()
    return patterns


@router.get(
    "/shift-patterns/{pattern_id}",
    response_model=ShiftPatternRead, # Devuelve detalles completos
    summary="Obtener detalles de un patrón de turno específico"
)
def get_shift_pattern(
    pattern_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene los detalles de un patrón de turno por su ID."""
    pattern = db.query(ShiftPattern).filter(ShiftPattern.id == pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail="Patrón de turno no encontrado.")
    return pattern


@router.put(
    "/shift-patterns/{pattern_id}",
    response_model=ShiftPatternRead, # Devuelve el patrón actualizado completo
    summary="Actualizar un patrón de turno"
)
def update_shift_pattern(
    pattern_id: int,
    pattern_data: ShiftPatternUpdate, # Usa el modelo Update
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # Requiere Admin
):
    """Actualiza nombre, descripción o secuencia de un patrón existente."""
    db_pattern = db.query(ShiftPattern).filter(ShiftPattern.id == pattern_id).first()
    if not db_pattern:
        raise HTTPException(status_code=404, detail="Patrón de turno no encontrado.")

    update_data = pattern_data.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar.")

    # Validar nombre único si se cambia
    if 'name' in update_data and update_data['name'] != db_pattern.name:
        existing = db.query(ShiftPattern).filter(ShiftPattern.name == update_data['name']).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Ya existe un patrón con el nombre '{update_data['name']}'")

    # Actualizar campos y recalcular longitud si cambia la secuencia
    for key, value in update_data.items():
        setattr(db_pattern, key, value)
        if key == 'pattern_sequence':
            if not value: # Validar que no sea vacía
                 raise HTTPException(status_code=400, detail="La secuencia del patrón no puede quedar vacía.")
            db_pattern.cycle_length_days = len(value) # Recalcular longitud

    try:
        db.commit()
        db.refresh(db_pattern)
        logger.info(f"Patrón de turno ID {pattern_id} actualizado.")
        return db_pattern
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando ShiftPattern {pattern_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al actualizar patrón: {e}")


@router.delete(
    "/shift-patterns/{pattern_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un patrón de turno"
)
def delete_shift_pattern(
    pattern_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # Requiere Admin
):
    """Elimina un patrón de turno si no está asignado a ningún usuario."""
    db_pattern = db.query(ShiftPattern).filter(ShiftPattern.id == pattern_id).first()
    if not db_pattern:
        raise HTTPException(status_code=404, detail="Patrón de turno no encontrado.")

    # Comprobar si está en uso por alguna asignación
    assignment = db.query(ShiftAssignment).filter(ShiftAssignment.pattern_id == pattern_id).first()
    if assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # O 409 Conflict
            detail=f"No se puede eliminar: el patrón '{db_pattern.name}' está asignado al menos a un usuario."
        )

    try:
        db.delete(db_pattern)
        db.commit()
        logger.info(f"Patrón de turno ID {pattern_id} ('{db_pattern.name}') eliminado.")
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando ShiftPattern {pattern_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al eliminar patrón: {e}")

# --- FIN ENDPOINTS PATRONES DE TURNO ---

# 12. ASIGNACIONES DE TURNOS ...
# =============================

@router.post(
    "/shift-assignments",
    response_model=ShiftAssignmentRead,
    status_code=status.HTTP_201_CREATED, # O 200 si actualiza
    summary="Crear o actualizar la asignación de turno para un usuario"
)
def create_or_update_assignment(
    assignment_data: ShiftAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # Solo Admin puede asignar turnos? Ajustar si es necesario
):
    """
    Crea una nueva asignación de turno para un usuario o actualiza la existente.
    Un usuario solo puede tener una asignación activa.
    """
    # Verificar que el usuario existe
    user = db.query(User).filter(User.id == assignment_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuario con ID {assignment_data.user_id} no encontrado.")

    # Verificar que el patrón existe
    pattern = db.query(ShiftPattern).filter(ShiftPattern.id == assignment_data.pattern_id).first()
    if not pattern:
        raise HTTPException(status_code=404, detail=f"Patrón de turno con ID {assignment_data.pattern_id} no encontrado.")

    # Validar offset_days contra la longitud del ciclo del patrón
    if assignment_data.offset_days >= pattern.cycle_length_days:
        raise HTTPException(
            status_code=400,
            detail=f"El offset ({assignment_data.offset_days}) no puede ser mayor o igual a la longitud del ciclo ({pattern.cycle_length_days}). Debe ser de 0 a {pattern.cycle_length_days - 1}."
        )

    # Buscar si ya existe una asignación para este usuario
    db_assignment = db.query(ShiftAssignment).filter(ShiftAssignment.user_id == assignment_data.user_id).first()

    if db_assignment:
        # Actualizar asignación existente
        logger.info(f"Actualizando asignación existente para usuario ID {assignment_data.user_id}")
        db_assignment.pattern_id = assignment_data.pattern_id
        db_assignment.reference_date = assignment_data.reference_date
        db_assignment.offset_days = assignment_data.offset_days
        http_status_code = status.HTTP_200_OK
    else:
        # Crear nueva asignación
        logger.info(f"Creando nueva asignación para usuario ID {assignment_data.user_id}")
        db_assignment = ShiftAssignment(**assignment_data.dict())
        db.add(db_assignment)
        http_status_code = status.HTTP_201_CREATED

    try:
        db.commit()
        # --- COMENTAR O ELIMINAR LAS SIGUIENTES LÍNEAS ---
        # db.refresh(db_assignment)
        # # Cargar relaciones para la respuesta
        # db.refresh(db_assignment, attribute_names=['user', 'pattern'])
        # ----------------------------------------------
        logger.info(f"Asignación para usuario {assignment_data.user_id} guardada/actualizada.")
        # Devolver directamente el objeto db_assignment. FastAPI/Pydantic deberían poder serializarlo.
        return db_assignment
    except Exception as e:
        db.rollback()
        logger.error(f"Error al guardar asignación de turno para usuario {assignment_data.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al guardar asignación: {e}")


@router.get(
    "/shift-assignments",
    response_model=List[ShiftAssignmentRead],
    summary="Obtener todas las asignaciones de turno"
)
def list_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # Solo Admin/Jefe Mant.?
):
    """Devuelve una lista de todas las asignaciones de turno de usuarios."""
    assignments = db.query(ShiftAssignment).options(
        joinedload(ShiftAssignment.user), # Cargar usuario
        joinedload(ShiftAssignment.pattern) # Cargar patrón
    ).all()
    return assignments


@router.get(
    "/users/{user_id}/shift-assignment",
    response_model=ShiftAssignmentRead,
    summary="Obtener la asignación de turno de un usuario específico"
)
def get_user_assignment(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Permitir verse a sí mismo o Admin/Jefe ver otros?
):
    """Obtiene la asignación de turno para un usuario dado su ID."""
    # Lógica de Permiso Ejemplo: Admin/Jefe puede ver cualquiera, usuario normal solo a sí mismo
    can_view = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"] or current_user.id == user_id
    if not can_view:
         raise HTTPException(status_code=403, detail="No tienes permiso para ver esta asignación.")

    assignment = db.query(ShiftAssignment).options(
        joinedload(ShiftAssignment.user),
        joinedload(ShiftAssignment.pattern)
    ).filter(ShiftAssignment.user_id == user_id).first()

    if not assignment:
        raise HTTPException(status_code=404, detail=f"No se encontró asignación de turno para el usuario ID {user_id}.")
    return assignment


@router.delete(
    "/shift-assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una asignación de turno"
)
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # Solo Admin/Jefe Mant.?
):
    """Elimina una asignación de turno existente."""
    db_assignment = db.query(ShiftAssignment).filter(ShiftAssignment.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Asignación de turno no encontrada.")

    try:
        user_id_deleted = db_assignment.user_id # Guardar para log
        db.delete(db_assignment)
        db.commit()
        logger.info(f"Eliminada asignación de turno ID {assignment_id} para usuario ID {user_id_deleted}.")
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando ShiftAssignment {assignment_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al eliminar asignación: {e}")

# --- FIN ENDPOINTS ASIGNACIONES DE TURNO ---


# --- ENDPOINT PARA OBTENER DATOS DEL CALENDARIO ---

@router.get(
    "/calendar-data",
    response_model=Dict[str, Dict[str, str]], # { "YYYY-MM-DD": { "Username": "ShiftCode", ... } }
    summary="Obtener datos de turno/ausencia para el calendario mensual"
)
def get_calendar_data(
    year: int = Query(..., description="Año para el calendario"),
    month: int = Query(..., ge=1, le=12, description="Mes para el calendario (1-12)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calcula y devuelve los códigos de turno o ausencia para cada usuario asignado
    y cada día del mes/año especificado.
    TODO: Implementar filtrado por sección para Jefe de Sección.
    """
    logger.info(f"Solicitando datos de calendario para {year}-{month:02d}")
    try:
        # 1. Determinar rango de fechas del mes
        start_date = date(year, month, 1)
        days_in_month = calendar.monthrange(year, month)[1]
        end_date = date(year, month, days_in_month)
        logger.debug(f"Rango de fechas: {start_date} a {end_date}")

        # 2. Obtener TODAS las asignaciones relevantes (con usuario y patrón)
        # TODO: Filtrar por sección si current_user es Jefe de Sección
        assignments = db.query(ShiftAssignment).options(
            joinedload(ShiftAssignment.user).load_only(User.id, User.username), # Cargar solo lo necesario del user
            joinedload(ShiftAssignment.pattern) # Cargar patrón completo
        ).all()
        logger.debug(f"Encontradas {len(assignments)} asignaciones de turno.")

        # 3. Obtener TODAS las ausencias que solapen con el mes
        absences = db.query(Absence).filter(
            Absence.start_date <= end_date,
            Absence.end_date >= start_date
        ).all()
        # Crear un lookup rápido para ausencias: {user_id: {date: absence_type}}
        absence_lookup = {}
        for ab in absences:
            current_d = ab.start_date
            while current_d <= ab.end_date:
                if ab.user_id not in absence_lookup:
                    absence_lookup[ab.user_id] = {}
                absence_lookup[ab.user_id][current_d] = ab.absence_type
                current_d += timedelta(days=1)
        logger.debug(f"Procesadas {len(absences)} ausencias en el periodo.")

        # 4. Calcular el calendario día a día
        calendar_data: Dict[str, Dict[str, str]] = {}
        # Fecha de referencia global (ajusta si es necesario)
        # IMPORTANTE: Debe ser la misma usada al crear la asignación
        global_reference_date = date(2024, 1, 1) # Lunes

        current_day = start_date
        while current_day <= end_date:
            day_str = current_day.isoformat() # "YYYY-MM-DD"
            calendar_data[day_str] = {}

            for assign in assignments:
                if not assign.user or not assign.pattern or not assign.pattern.pattern_sequence:
                    logger.warning(f"Asignación ID {assign.id} incompleta (sin usuario o patrón), saltando.")
                    continue

                user_id = assign.user.id
                username = assign.user.username

                # Comprobar si hay ausencia para este usuario y día
                if user_id in absence_lookup and current_day in absence_lookup[user_id]:
                    shift_code = absence_lookup[user_id][current_day]
                else:
                    # Calcular turno normal
                    try:
                        # Días desde la fecha de referencia global HASTA la fecha de referencia de la asignación
                        # ¡OJO! Si 'reference_date' es la misma para todos, este cálculo se simplifica.
                        # Asumiendo que 'assign.reference_date' es la fecha base para el offset de ESE usuario.
                        ref_date_assign = assign.reference_date # La fecha guardada en la asignación

                        # Días entre la fecha de referencia de la asignación y el día actual
                        days_difference = (current_day - ref_date_assign).days

                        # Sumar el offset inicial y calcular índice en el ciclo
                        total_offset_days = days_difference + assign.offset_days
                        cycle_len = assign.pattern.cycle_length_days

                        # Calcular índice asegurando que sea positivo con el módulo
                        day_index = (total_offset_days % cycle_len + cycle_len) % cycle_len

                        shift_code = assign.pattern.pattern_sequence[day_index]

                        # Manejo especial de Festivos para Jornada Partida
                        # Asumiendo que el patrón 'PPPPPLL' es para Jornada Partida
                        # Y que los festivos (F) solo se aplican si el día es L-V (P)
                        # Necesitaríamos una lista de festivos reales para el año/mes
                        # O marcar 'F' como un tipo de ausencia manual para esos usuarios
                        # Por simplicidad, de momento no sobrescribimos 'P' con 'F' automáticamente
                        # if shift_code == 'P' and es_festivo(current_day):
                        #     shift_code = 'F'

                    except IndexError:
                        logger.error(f"Error de índice calculando turno para user {user_id} en {day_str}. Índice={day_index}, Secuencia='{assign.pattern.pattern_sequence}'")
                        shift_code = "?" # Código de error
                    except Exception as e_calc:
                         logger.error(f"Error calculando turno para user {user_id} en {day_str}: {e_calc}", exc_info=True)
                         shift_code = "?"

                calendar_data[day_str][username] = shift_code

            current_day += timedelta(days=1)

        logger.info(f"Datos de calendario generados para {year}-{month:02d}")
        return calendar_data

    except Exception as e:
        logger.error(f"Error general en get_calendar_data para {year}-{month}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al generar datos del calendario")

# --- FIN ENDPOINT CALENDARIO ---
