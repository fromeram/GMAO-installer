# src/models/associations.py
"""
Define las tablas y modelos de asociación para relaciones Muchos-a-Muchos
que necesiten datos adicionales.
"""
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import Base # Asegúrate que la ruta a Base es correcta

class MachinePartAssociation(Base):
    """
    Tabla de asociación entre Machine e Inventory (Repuestos).
    Guarda la cantidad de cada repuesto necesario para una máquina específica.
    """
    __tablename__ = 'machine_parts_association'

    # Claves foráneas que forman la clave primaria compuesta
    machine_id = Column(Integer, ForeignKey('machines.id', ondelete='CASCADE'), primary_key=True)
    inventory_id = Column(Integer, ForeignKey('inventory.id', ondelete='CASCADE'), primary_key=True)

    # Columna adicional en la tabla de asociación
    quantity = Column(Integer, default=1, nullable=False)

    # Relaciones inversas hacia los modelos 'padre'
    # El back_populates debe coincidir con el nombre de la relación en Machine e Inventory
    machine = relationship("Machine", back_populates="part_associations")
    part = relationship("Inventory", back_populates="machine_associations") # 'part' se refiere al Inventory item

    def __repr__(self):
        return f"<MachinePartAssociation(machine_id={self.machine_id}, inventory_id={self.inventory_id}, quantity={self.quantity})>"