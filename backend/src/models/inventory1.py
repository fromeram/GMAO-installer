# inventory.py
"""
Modelo de inventario.
Cada producto tiene nombre, cantidad, ubicación (relacionado con un almacén), precio y un proveedor opcional.
"""
# backend/src/models/inventory.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import Base

class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    location = Column(String, ForeignKey("warehouses.name"), nullable=False)
    price = Column(Float, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)  # ✅ Cambiado a ID

    # Relaciones
    supplier = relationship("Supplier", back_populates="inventory_items")
    warehouse = relationship("Warehouse", back_populates="inventory_items")
    work_orders = relationship("WorkOrder", back_populates="repuesto")
