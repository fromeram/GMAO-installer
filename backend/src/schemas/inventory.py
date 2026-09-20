# schemas/inventory.py — Schemas de inventario, almacenes y productos
from typing import Optional, Literal
from pydantic import BaseModel, Field

from .auth import UserReadBasic


class WarehouseCreate(BaseModel):
    name: str

class WarehouseInfo(BaseModel):
    id: int; name: Optional[str] = None
    class Config: orm_mode = True

class SupplierInfo(BaseModel):
    id: int; name: Optional[str] = None; company: Optional[str] = None
    class Config: orm_mode = True

class InventoryReadBasic(BaseModel):
    id: int
    product_name: str
    quantity: int
    tipo: Optional[str] = "mecánico"
    class Config: orm_mode = True

class InventarioBase(BaseModel):
    product_name: str
    quantity: int
    warehouse_id: int
    price: float
    supplier_id: Optional[int] = None
    discount: Optional[float] = Field(default=0.0, ge=0, le=100)
    stock_minimo: Optional[int] = Field(default=0, ge=0)
    tipo: Optional[str] = Field(default="mecánico")
    class Config: orm_mode = True

class InventarioCreate(InventarioBase):
    tipo: Literal["mecánico", "eléctrico", "neumático", "limpieza"] = "mecánico"

class InventarioUpdate(BaseModel):
    product_name: Optional[str] = None
    quantity: Optional[int] = None
    warehouse_id: Optional[int] = None
    price: Optional[float] = None
    supplier_id: Optional[int] = None
    discount: Optional[float] = Field(default=None, ge=0, le=100)
    stock_minimo: Optional[int] = Field(default=None, ge=0)
    tipo: Optional[Literal["mecánico", "eléctrico", "neumático", "limpieza"]] = None
    class Config: orm_mode = True

class InventoryReportItem(BaseModel):
    id: int
    product_name: str
    quantity: int
    almacen: Optional[WarehouseInfo] = None
    proveedor: Optional[str] = None
    price: float
    discount: Optional[float] = None
    tipo: Optional[str] = "mecánico"
    class Config: orm_mode = True
