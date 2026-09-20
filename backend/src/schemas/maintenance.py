# schemas/maintenance.py — Schemas de mantenimiento preventivo, backlog y solicitudes
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

from .auth import UserReadBasic
from .sections import SectionReadBasic
from .machines import MachineReadBasic


class MantenimientoPreventivoCreate(BaseModel):
    title: str
    description: str
    maquina_id: int
    frecuencia: str
    fechaInicio: str
    notification_interval: int
    assigned_role_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    task_list_id: Optional[int] = None

class MantenimientoPreventivoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    maquina_id: Optional[int] = None
    frecuencia: Optional[str] = None
    fechaInicio: Optional[str] = None
    notification_interval: Optional[int] = None
    assigned_role_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    task_list_id: Optional[int] = None

# --- Backlog ---
class BacklogBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    priority: Optional[Literal['Baja', 'Media', 'Alta', 'Crítica']] = Field(default='Media')
    status: Optional[Literal['Pendiente', 'Planificado', 'En Progreso', 'Completado', 'Cancelado']] = Field(default='Pendiente')
    machine_id: Optional[int] = None
    section_id: Optional[int] = None
    estimated_hours: Optional[int] = Field(None, ge=0)
    estimated_downtime: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None

class BacklogCreate(BacklogBase):
    pass

class BacklogUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    priority: Optional[Literal['Baja', 'Media', 'Alta', 'Crítica']] = None
    status: Optional[Literal['Pendiente', 'Planificado', 'En Progreso', 'Completado', 'Cancelado']] = None
    machine_id: Optional[int] = None
    section_id: Optional[int] = None
    assigned_to_id: Optional[int] = None
    estimated_hours: Optional[int] = Field(None, ge=0)
    estimated_downtime: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None
    completion_notes: Optional[str] = None

class BacklogRead(BacklogBase):
    id: int
    created_by_id: int
    assigned_to_id: Optional[int] = None
    actual_work_order_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    machine: Optional[MachineReadBasic] = None
    section: Optional[SectionReadBasic] = None
    created_by: Optional[UserReadBasic] = None
    assigned_to: Optional[UserReadBasic] = None
    class Config: orm_mode = True

# --- Solicitudes de Mantenimiento ---
class MaintenanceRequestBase(BaseModel):
    title: str
    description: Optional[str] = None
    machine_id: Optional[int] = None
    priority: Optional[Literal["Baja", "Media", "Alta"]] = None

class MaintenanceRequestCreate(MaintenanceRequestBase):
    pass

class MaintenanceRequestUpdate(BaseModel):
    status: Literal["Pendiente", "Aprobada", "Rechazada"]
    review_notes: Optional[str] = None
    priority: Optional[Literal["Baja", "Media", "Alta"]] = None

class MaintenanceRequestRead(MaintenanceRequestBase):
    id: int
    reported_by_id: int
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by_id: Optional[int] = None
    review_notes: Optional[str] = None
    work_order_id: Optional[int] = None
    reported_by: Optional[UserReadBasic] = None
    machine: Optional[MachineReadBasic] = None
    class Config: orm_mode = True
