# src/models/work_order_material.py
from sqlalchemy import Column, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from .base import Base

class WorkOrderMaterial(Base):
    """
    Tabla intermedia para registrar los múltiples repuestos/materiales 
    consumidos en una Orden de Trabajo.
    Guarda la cantidad consumida y el precio unitario en el momento del uso 
    para mantener el histórico económico (TCO) aunque el precio del inventario cambie.
    """
    __tablename__ = 'work_order_materials'

    id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(Integer, ForeignKey('work_orders.id', ondelete='CASCADE'), nullable=False)
    inventory_id = Column(Integer, ForeignKey('inventory.id', ondelete='RESTRICT'), nullable=False)
    
    quantity_used = Column(Integer, default=1, nullable=False)
    unit_cost_at_use = Column(Numeric(10, 2), nullable=False) # Precio histórico

    # Relaciones inversas
    work_order = relationship("WorkOrder", back_populates="materials")
    inventory = relationship("Inventory", back_populates="work_order_materials")

    def __repr__(self):
        return f"<WorkOrderMaterial(wo_id={self.work_order_id}, item_id={self.inventory_id}, qty={self.quantity_used})>"
