# schemas/machines.py — Schemas de máquinas y BOM
from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class MachineReadBasic(BaseModel):
    id: int; nombre: str
    class Config: orm_mode = True

class MaquinaCreate(BaseModel):
    nombre: str; modelo: str; marca: str; numero_serie: str; line_id: int; section_id: int; criticidad: Optional[str] = None

class MaquinaUpdate(BaseModel):
    nombre: Optional[str] = None; modelo: Optional[str] = None; marca: Optional[str] = None; numero_serie: Optional[str] = None
    line_id: Optional[int] = None; section_id: Optional[int] = None; criticidad: Optional[str] = None

class MaquinaRead(BaseModel):
    id: int; nombre: str; modelo: str; marca: str; numero_serie: str; line_id: int; section_id: int; criticidad: Optional[str] = None
    class Config: orm_mode = True

class InventoryReadBasic(BaseModel):
    id: int
    product_name: str
    quantity: Optional[int] = None
    class Config: orm_mode = True

class MachinePartCreate(BaseModel):
    inventory_id: int; quantity: int = Field(..., ge=1)

class MachinePartRead(BaseModel):
    inventory_id: int; quantity: int; part: InventoryReadBasic
    class Config: orm_mode = True

class PartUsageInMachine(BaseModel):
    quantity: int
    machine: MachineReadBasic
    class Config: orm_mode = True

class MachineMetricsResponse(BaseModel):
    mtbf: float
    mttr: float
    disponibilidad: float
    total_downtime_hours: float
    total_uptime_hours: float
    total_orders: int
    orders_by_type: Dict[str, int]
    lastYear: Dict[str, int]
    period: str
