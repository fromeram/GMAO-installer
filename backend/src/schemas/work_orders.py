# schemas/work_orders.py — Schemas de órdenes de trabajo, técnicos y materiales
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

from .auth import UserReadBasic
from .sections import SectionReadBasic, LineReadBasic
from .machines import MachineReadBasic, InventoryReadBasic
from .codes import CodeRead


class WorkOrderMaterialCreate(BaseModel):
    inventory_id: int
    quantity_used: int = Field(..., gt=0)

class WorkOrderBase(BaseModel):
    title: str
    details: Optional[str] = Field(None, description="Detalles del trabajo")
    work_type: Literal[
        "Preventivo", "Correctivo", "Inspección", "Mejora", "Modificación", "Seguridad",
        "Cambio de Formato", "Setup de Línea", "Cambio Global de Planta"
    ]
    section_id: int
    line_id: int
    machine_id: Optional[int] = None
    operator: str
    assigned_to_id: Optional[int] = None
    imagen_url: Optional[str] = None
    
    class Config:
        str_strip_whitespace = False
        validate_all = True

class WorkOrderCreate(WorkOrderBase):
    status: Optional[Literal["Pendiente"]] = "Pendiente"
    task_list_id: Optional[int] = None
    checklist_data: Optional[Dict[str, Any]] = None
    materials: Optional[List[WorkOrderMaterialCreate]] = []

class WorkOrderCompleteUpdate(BaseModel):
    status: Optional[Literal["Pendiente", "En curso", "En revisión", "Cerrada"]] = None
    failure_code_id: Optional[int] = None
    cause_code_id: Optional[int] = None
    remedy_code_id: Optional[int] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    downtime_hours: Optional[float] = Field(default=None, ge=0)
    completion_notes: Optional[str] = None
    title: Optional[str] = None
    details: Optional[str] = None
    work_type: Optional[Literal[
        "Preventivo", "Correctivo", "Inspección", "Mejora", "Modificación", "Seguridad",
        "Cambio de Formato", "Setup de Línea", "Cambio Global de Planta"
    ]] = None
    machine_id: Optional[int] = None
    line_id: Optional[int] = None
    section_id: Optional[int] = None
    operator: Optional[str] = None
    assigned_to_id: Optional[int] = None
    imagen_url: Optional[str] = None
    task_list_id: Optional[int] = None
    checklist_data: Optional[Dict[str, Any]] = None
    materials: Optional[List[WorkOrderMaterialCreate]] = None

class WorkOrderTechnicianBase(BaseModel):
    user_id: int
    role: Literal["principal", "apoyo", "supervisor"] = "apoyo"
    hours_worked: Optional[float] = Field(0.0, ge=0)
    notes: Optional[str] = None

class WorkOrderTechnicianCreate(WorkOrderTechnicianBase):
    pass

class WorkOrderTechnicianRead(WorkOrderTechnicianBase):
    id: int
    work_order_id: int
    assigned_at: datetime
    assigned_by_id: Optional[int]
    is_active: bool
    technician: Optional[UserReadBasic] = None
    class Config: orm_mode = True

class WorkOrderTechnicianUpdate(BaseModel):
    role: Optional[Literal["principal", "apoyo", "supervisor"]] = None
    hours_worked: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class WorkOrderMaterialRead(BaseModel):
    id: int
    inventory_id: int
    quantity_used: int
    unit_cost_at_use: float
    inventory: Optional[InventoryReadBasic] = None
    class Config: orm_mode = True

class WorkOrderRead(BaseModel):
    # Campos básicos
    id: int
    order_number: Optional[str] = None
    title: str
    details: Optional[str] = None
    work_type: str
    section_id: int
    line_id: Optional[int] = None
    machine_id: Optional[int] = None
    operator: str
    assigned_to_id: int
    status: str
    created_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    imagen_url: Optional[str] = None
    # Campos TCO
    total_material_cost: Optional[float] = 0.0
    total_labor_cost: Optional[float] = 0.0
    total_external_cost: Optional[float] = 0.0
    total_cost: Optional[float] = 0.0
    # Campos FCR
    failure_code_id: Optional[int] = None
    cause_code_id: Optional[int] = None
    remedy_code_id: Optional[int] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    downtime_hours: Optional[float] = None
    completion_notes: Optional[str] = None
    # Campos de cambio de formato
    format_change_type: Optional[str] = None
    affected_machines: Optional[List[int]] = None
    format_from_id: Optional[int] = None
    format_to_id: Optional[int] = None
    format_from_name: Optional[str] = None
    format_to_name: Optional[str] = None
    estimated_setup_duration: Optional[float] = None
    setup_duration: Optional[float] = None
    production_loss_hours: Optional[float] = None
    setup_team: Optional[List[int]] = None
    setup_notes: Optional[str] = None
    # Objetos anidados
    failure_code: Optional[CodeRead] = None
    cause_code: Optional[CodeRead] = None
    remedy_code: Optional[CodeRead] = None
    assigned_to: Optional[UserReadBasic] = None
    machine: Optional[MachineReadBasic] = Field(None, alias='machine_obj')
    section: Optional[SectionReadBasic] = None
    line: Optional[LineReadBasic] = None
    technicians: Optional[List[WorkOrderTechnicianRead]] = []
    materials: Optional[List[WorkOrderMaterialRead]] = []
    
    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class FormatChangeOrderUpdate(BaseModel):
    status: Optional[Literal["Pendiente", "En curso", "En revisión", "Cerrada"]] = None
    setup_duration: Optional[float] = Field(None, ge=0)
    production_loss_hours: Optional[float] = Field(None, ge=0)
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    completion_notes: Optional[str] = None
    setup_notes: Optional[str] = None
    failure_code_id: Optional[int] = None
    cause_code_id: Optional[int] = None
    remedy_code_id: Optional[int] = None
