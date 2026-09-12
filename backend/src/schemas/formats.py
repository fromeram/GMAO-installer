# schemas/formats.py — Schemas de formatos de producción y cambios de formato
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, validator

from .work_orders import FormatChangeOrderUpdate


class FormatBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    estimated_setup_time: Optional[float] = Field(None, ge=0, description="Tiempo estimado en horas")
    machines_requiring_adjustment: Optional[List[int]] = Field(None, description="IDs de máquinas que requieren ajuste")
    tools_materials_needed: Optional[List[str]] = Field(None, description="Lista de herramientas/materiales")

class FormatCreate(FormatBase):
    pass

class FormatUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    estimated_setup_time: Optional[float] = Field(None, ge=0)
    machines_requiring_adjustment: Optional[List[int]] = None
    tools_materials_needed: Optional[List[str]] = None
    active: Optional[bool] = None

class FormatRead(FormatBase):
    id: int
    active: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

class FormatChangeOrderCreate(BaseModel):
    title: str
    details: Optional[str] = None
    work_type: Literal["Cambio de Formato", "Setup de Línea", "Cambio Global de Planta"]
    format_change_type: Literal["Individual", "Línea", "Global"]
    
    section_id: Optional[int] = None
    line_id: Optional[int] = None
    
    machine_id: Optional[int] = None
    affected_machines: Optional[List[int]] = []
    setup_team: Optional[List[int]] = []
    
    format_from_id: Optional[int] = None
    format_to_id: Optional[int] = None
    format_from_name: Optional[str] = None
    format_to_name: Optional[str] = None
    
    estimated_setup_duration: Optional[float] = Field(None, ge=0)
    assigned_to_id: int
    operator: str
    setup_notes: Optional[str] = None
    
    @validator('section_id')
    def validate_section_requirements(cls, v, values):
        format_type = values.get('format_change_type')
        if format_type in ['Individual', 'Línea'] and not v:
            raise ValueError('section_id es requerido para cambios individuales y de línea')
        return v
    
    @validator('affected_machines')
    def validate_machine_requirements(cls, v, values):
        format_type = values.get('format_change_type')
        machine_id = values.get('machine_id')
        if format_type == 'Individual':
            if not machine_id:
                raise ValueError('machine_id es requerido para cambios individuales')
        else:
            if not v or len(v) == 0:
                raise ValueError('affected_machines es requerido para cambios de línea/globales')
        return v
