# schemas/dashboard.py — Schemas del dashboard
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from .machines import MachineReadBasic


class DashboardStats(BaseModel):
    pendingOrders: int
    ongoingOrders: int
    completedOrders: int
    completedOrdersTrend: float
    lowStockItems: int
    mtbfAvg: float
    mttrAvg: float
    availabilityAvg: float
    class Config: orm_mode = True

class PendingTask(BaseModel):
    id: int
    title: str
    work_type: str
    status: str
    machine_obj: Optional[MachineReadBasic] = None
    class Config: orm_mode = True

class MaintenanceHistoryItem(BaseModel):
    id: int
    order_number: Optional[str] = None
    title: str
    work_type: str
    finished_at: Optional[datetime] = None
    machine_obj: Optional[MachineReadBasic] = None
    class Config: orm_mode = True

class MaintenanceByMonthItem(BaseModel):
    month: str
    preventivo: int
    correctivo: int
    inspeccion: int
    otros: int
    total: int
    class Config: orm_mode = True

class MaintenanceByTypeItem(BaseModel):
    name: str
    value: int
    class Config: orm_mode = True
