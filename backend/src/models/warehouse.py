# warehouse.py
"""
Modelo de almacén.
Cada almacén tiene un nombre único y se relaciona con inventario.
"""
# backend/src/models/warehouse.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.models.base import Base

class Warehouse(Base):
    __tablename__ = "warehouses"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    # Relación con inventario
    inventory_items = relationship("Inventory", back_populates="warehouse", cascade="all, delete-orphan")
