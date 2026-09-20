# schemas/suppliers.py — Schemas de proveedores y precios
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, validator

from .inventory import SupplierInfo, WarehouseInfo


class SupplierCreate(BaseModel):
    name: str; company: str; phone: str

class SupplierUpdate(BaseModel):
    name: Optional[str] = None; company: Optional[str] = None; phone: Optional[str] = None

class SupplierPriceBase(BaseModel):
    product_name: str
    supplier_id: int
    warehouse_id: Optional[int] = None
    price: Decimal
    discount: Optional[Decimal] = Field(default=Decimal('0.0'), ge=0, le=100)

    @validator('discount', pre=True, always=True)
    def validate_discount(cls, v):
        if v is None:
            return Decimal('0.0')
        try:
            v_dec = Decimal(str(v))
        except Exception:
            raise ValueError(f"Valor inválido para descuento: '{v}'")
        if not (Decimal('0.0') <= v_dec <= Decimal('100.0')):
            raise ValueError('El descuento debe estar entre 0.0 y 100.0')
        return v_dec

    @validator('price', pre=True, always=True)
    def validate_price(cls, v):
        if v is None:
            raise ValueError('El precio no puede ser nulo')
        try:
            v_dec = Decimal(str(v))
        except Exception:
            raise ValueError(f"Valor inválido para precio: '{v}'")
        if v_dec < Decimal('0.0'):
            raise ValueError('El precio no puede ser negativo')
        return v_dec

    class Config:
        orm_mode = True
        json_encoders = {Decimal: float}

class SupplierPriceCreate(SupplierPriceBase):
    pass

class SupplierPriceUpdate(BaseModel):
    product_name: Optional[str] = None
    supplier_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    price: Optional[Decimal] = None
    discount: Optional[Decimal] = None

    @validator('discount', pre=True, always=True)
    def validate_discount_optional(cls, v):
        if v is None: return v
        v_dec = Decimal(str(v))
        if not (Decimal('0.0') <= v_dec <= Decimal('100.0')):
            raise ValueError('Discount must be between 0.0 and 100.0')
        return v_dec

    @validator('price', pre=True, always=True)
    def validate_price_optional(cls, v):
        if v is None: return v
        v_dec = Decimal(str(v))
        if v_dec < Decimal('0.0'):
            raise ValueError('Price cannot be negative')
        return v_dec

    class Config:
        orm_mode = True
        json_encoders = {Decimal: float}

class SupplierPrice(SupplierPriceBase):
    id: int
    last_updated: datetime
    supplier: Optional[SupplierInfo] = None
    warehouse: Optional[WarehouseInfo] = None
    class Config:
        orm_mode = True
        json_encoders = {Decimal: float}
