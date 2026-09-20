# models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from database import Base

class Line(Base):
    __tablename__ = 'lines'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    section_id = Column(Integer, ForeignKey('sections.id', ondelete='CASCADE'))

    section = relationship('Section', back_populates='lines')
    machines = relationship('Machine', back_populates='line')

class Section(Base):
    __tablename__ = 'sections'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)

    lines = relationship('Line', back_populates='section')
    machines = relationship('Machine', back_populates='section')
    users = relationship('User', back_populates='section')  # Relación bidireccional

class Machine(Base):
    __tablename__ = 'machines'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    marca = Column(String(255), nullable=False)
    modelo = Column(String(255), nullable=False)
    numero_serie = Column(String(255), nullable=False, unique=True)
    line_id = Column(Integer, ForeignKey('lines.id', ondelete='CASCADE'))
    section_id = Column(Integer, ForeignKey('sections.id', ondelete='SET NULL'), nullable=True)

    line = relationship('Line', back_populates='machines')
    section = relationship('Section', back_populates='machines')
    maintenances = relationship('Maintenance', back_populates='machine')  # Relación bidireccional

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False, unique=True)

    users = relationship('User', back_populates='role')

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'))
    section_id = Column(Integer, ForeignKey('sections.id', ondelete='SET NULL'), nullable=True)  # Cambio aquí

    role = relationship('Role', back_populates='users')
    section = relationship('Section', back_populates='users')  # Relación bidireccional

class WorkOrder(Base):
    __tablename__ = 'work_orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    work_type = Column(String(50), nullable=False)
    section_id = Column(Integer, ForeignKey('sections.id', ondelete='CASCADE'))  # Cambio aquí
    line_id = Column(Integer, ForeignKey('lines.id', ondelete='CASCADE'))        # Cambio aquí
    machine_id = Column(Integer, ForeignKey('machines.id', ondelete='CASCADE'))  # Cambio aquí
    operator = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)

    section = relationship('Section')
    line = relationship('Line')
    machine = relationship('Machine')

class Supplier(Base):
    __tablename__ = 'suppliers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=False)
    empresa = Column(String(255), nullable=False)

    inventory = relationship('Inventory', back_populates='supplier')

class Inventory(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    location = Column(String(255))
    price = Column(DECIMAL(10, 2), nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id', ondelete='SET NULL'), nullable=True)  # Asegurar nullable

    supplier = relationship('Supplier', back_populates='inventory')

class Maintenance(Base):
    __tablename__ = 'maintenances'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    machine_id = Column(Integer, ForeignKey('machines.id', ondelete='CASCADE'))

    machine = relationship('Machine', back_populates='maintenances')  # Relación bidireccional