# supplier.py
"""
Modelo de proveedor.
Cada proveedor tiene nombre, compañía y teléfono.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, doc="Nombre del proveedor")
    company = Column(String, nullable=False, doc="Compañía del proveedor")
    phone = Column(String, nullable=False, doc="Teléfono del proveedor")

    inventory_items = relationship("Inventory", back_populates="supplier")