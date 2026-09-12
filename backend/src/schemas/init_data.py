# schemas/init_data.py — Schema para inicialización masiva
from typing import List
from pydantic import BaseModel

from .auth import RoleCreate, UserCreate
from .sections import SectionCreate, LineCreate
from .machines import MaquinaCreate
from .suppliers import SupplierCreate
from .inventory import WarehouseCreate, InventarioCreate
from .maintenance import MantenimientoPreventivoCreate
from .work_orders import WorkOrderCreate


class InitData(BaseModel):
    roles: List[RoleCreate]
    users: List[UserCreate]
    sections: List[SectionCreate]
    lines: List[LineCreate]
    machines: List[MaquinaCreate]
    suppliers: List[SupplierCreate]
    warehouses: List[WarehouseCreate]
    inventory: List[InventarioCreate]
    maintenances: List[MantenimientoPreventivoCreate]
    work_orders: List[WorkOrderCreate]
