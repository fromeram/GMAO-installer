# backend/src/models/work_order.py
"""
Modelo de orden de trabajo.
Modificado para añadir códigos de cierre (falla, causa, remedio),
campos detallados de finalización Y nuevos campos para cambios de formato.
"""

from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, CheckConstraint, Text, Float, JSON, Boolean, Numeric
)
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class FailureCode(Base):
    __tablename__ = "failure_codes"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    work_orders = relationship("WorkOrder", back_populates="failure_code")

class CauseCode(Base):
    __tablename__ = "cause_codes"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    work_orders = relationship("WorkOrder", back_populates="cause_code")

class RemedyCode(Base):
    __tablename__ = "remedy_codes"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    work_orders = relationship("WorkOrder", back_populates="remedy_code")


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True)
    title = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    work_type = Column(String, nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    line_id = Column(Integer, ForeignKey("lines.id"), nullable=False)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=True)
    operator = Column(String, nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False, default="Pendiente")
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    
    # ✅ LÍNEAS CORREGIDAS Y AÑADIDAS
    task_list_id = Column(Integer, ForeignKey("task_lists.id"), nullable=True)
    generated_from_maintenance_id = Column(Integer, ForeignKey("maintenances.id"), nullable=True, index=True)
    # repuesto_id = Column(Integer, ForeignKey("inventory.id"), nullable=True) # DEPRECADO: Usar materials
    failure_code_id = Column(Integer, ForeignKey("failure_codes.id"), nullable=True)
    cause_code_id = Column(Integer, ForeignKey("cause_codes.id"), nullable=True)
    remedy_code_id = Column(Integer, ForeignKey("remedy_codes.id"), nullable=True)
    source_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    format_from_id = Column(Integer, ForeignKey("formats.id"), nullable=True)
    format_to_id = Column(Integer, ForeignKey("formats.id"), nullable=True)
    
    # --- GESTIÓN ECONÓMICA (TCO) ---
    total_material_cost = Column(Numeric(10, 2), default=0.0)
    total_labor_cost = Column(Numeric(10, 2), default=0.0)
    total_external_cost = Column(Numeric(10, 2), default=0.0)
    
    # Campos adicionales
    # quantity_used = Column(Integer, default=0) # DEPRECADO: Usar materials
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)
    downtime_hours = Column(Float, nullable=True)
    completion_notes = Column(Text, nullable=True)
    imagen_url = Column(String, nullable=True)
    format_change_type = Column(String, nullable=True)
    affected_machines = Column(JSON, nullable=True)
    format_from_name = Column(String, nullable=True)
    format_to_name = Column(String, nullable=True)
    estimated_setup_duration = Column(Float, nullable=True)
    setup_duration = Column(Float, nullable=True)
    production_loss_hours = Column(Float, nullable=True)
    setup_team = Column(JSON, nullable=True)
    setup_notes = Column(Text, nullable=True)

    # Relaciones
    section = relationship("Section")
    line = relationship("Line")
    machine_obj = relationship("Machine", foreign_keys=[machine_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    # repuesto = relationship("Inventory") # DEPRECADO
    failure_code = relationship("FailureCode", back_populates="work_orders")
    cause_code = relationship("CauseCode", back_populates="work_orders")
    remedy_code = relationship("RemedyCode", back_populates="work_orders")
    source_document = relationship("Document", back_populates="work_orders")
    format_from_obj = relationship("Format", foreign_keys=[format_from_id], back_populates="work_orders_as_from")
    format_to_obj = relationship("Format", foreign_keys=[format_to_id], back_populates="work_orders_as_to")
    technicians = relationship("WorkOrderTechnician", back_populates="work_order", cascade="all, delete-orphan")
    checklist_progress = relationship("ChecklistProgress", back_populates="work_order", cascade="all, delete-orphan")
    materials = relationship("WorkOrderMaterial", back_populates="work_order", cascade="all, delete-orphan")
    maintenance_request_origin = relationship("MaintenanceRequest", back_populates="work_order", uselist=False)

    generated_from_maintenance = relationship(
        "Maintenance",
        foreign_keys=[generated_from_maintenance_id],
        back_populates="generated_work_orders"
    )
    
    # ✅ Esta es la relación que estaba dando el error. Ahora tiene su columna `task_list_id` para funcionar.
    task_list = relationship("TaskList", back_populates="work_orders")

    # --- MÉTODOS AUXILIARES PARA CAMBIOS DE FORMATO ---
    @property
    def has_checklist(self):
        """Determina si esta orden tiene un checklist asociado"""
        return self.task_list_id is not None or len(self.checklist_progress) > 0

    def __repr__(self):
        return f"<WorkOrder(id={self.id}, title='{self.title}', status='{self.status}')>"

    @property
    def setup_efficiency(self):
        """Calcula la eficiencia del setup (tiempo estimado / tiempo real * 100)"""
        if self.estimated_setup_duration and self.setup_duration and self.setup_duration > 0:
            return (self.estimated_setup_duration / self.setup_duration) * 100
        return None

    @property
    def total_cost(self):
        """Calcula el coste total de la orden de trabajo"""
        mat = float(self.total_material_cost or 0.0)
        lab = float(self.total_labor_cost or 0.0)
        ext = float(self.total_external_cost or 0.0)
        return mat + lab + ext

    @property
    def affected_machines_count(self):
        """Retorna el número de máquinas afectadas en el cambio"""
        if self.affected_machines and isinstance(self.affected_machines, list):
            return len(self.affected_machines)
        elif self.machine_id:
            return 1
        return 0

    @property
    def setup_team_count(self):
        """Retorna el número de miembros del equipo de setup"""
        if self.setup_team and isinstance(self.setup_team, list):
            return len(self.setup_team)
        return 0

    @property
    def is_format_change(self):
        """Determina si esta orden es un cambio de formato"""
        return self.work_type in ['Cambio de Formato', 'Setup de Línea', 'Cambio Global de Planta']
    
    def __repr__(self):
        return f"<WorkOrder(id={self.id}, order_number='{self.order_number}', title='{self.title}', status='{self.status}')>"

    def get_principal_technician(self):
        """Retorna el técnico principal de esta orden"""
        for tech in self.technicians:
            if tech.role == "principal" and tech.is_active:
                return tech
        return None
    
    def get_active_technicians(self):
        """Retorna lista de técnicos activos"""
        return [tech for tech in self.technicians if tech.is_active]



    # Constraints ACTUALIZADOS
    __table_args__ = (
    CheckConstraint(
        status.in_(['Pendiente', 'En curso', 'En revisión', 'Cerrada']),
        name='valid_status'
    ),
    CheckConstraint(
        work_type.in_([
            'Preventivo', 'Correctivo', 'Inspección', 'Mejora', 'Modificación', 'Seguridad',
            'Cambio de Formato', 'Setup de Línea', 'Cambio Global de Planta'  # ✅ AGREGAR ESTOS
        ]),
        name='valid_work_type'
    ),
    CheckConstraint(
        format_change_type.in_(['Individual', 'Línea', 'Global']) | (format_change_type.is_(None)),
        name='valid_format_change_type'
    ),
)
