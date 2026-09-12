# backend/src/models/inventory.py
"""
Modelo de inventario.
Cada producto tiene nombre, cantidad, ubicación (relacionado con un almacén), precio y un proveedor opcional.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Numeric # Importar Numeric
from sqlalchemy.orm import relationship
from src.models.base import Base
from .associations import MachinePartAssociation
# Importar otros modelos si son necesarios para relaciones (Warehouse, Supplier ya están en las relaciones)
# from .warehouse import Warehouse
# from .supplier import Supplier

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    product_name = Column(String, nullable=False) # Alembic no reportó problemas aquí
    quantity = Column(Integer, nullable=False) # Alembic no reportó problemas aquí
    # Relación por ID. Asume que warehouse.py define Warehouse
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    # --- MODIFICADO: Usar Numeric para precios ---
    price = Column(Numeric(10, 2), nullable=False)
    # ------------------------------------------
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True) # Alembic no reportó problemas aquí
    # Mantenemos Float aquí, pero considera Numeric si necesitas precisión exacta
    discount = Column(Float, nullable=True) # Alembic no reportó problemas aquí
    stock_minimo = Column(Integer, default=0)
    tipo = Column(String, nullable=True, default='mecánico')  # ← AÑADIR ESTA LÍNEA

    # Relaciones
    # Asegúrate que Supplier y Warehouse tienen la relación inversa con back_populates="inventory_items"
    supplier = relationship("Supplier", back_populates="inventory_items")
    warehouse = relationship("Warehouse", back_populates="inventory_items")
    # Asegúrate que WorkOrder tiene la relación inversa con back_populates="repuesto"
    work_orders = relationship("WorkOrder", back_populates="repuesto")
    machine_associations = relationship(
        "MachinePartAssociation",
        back_populates="part", # 'part' es como llamamos a la relación en MachinePartAssociation
        cascade="all, delete-orphan", # Si borras un Repuesto, borra sus asociaciones a máquinas
        lazy="selectin"
    )