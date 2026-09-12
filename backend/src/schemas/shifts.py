# schemas/shifts.py — Schemas de turnos, ausencias, overrides y vacaciones
from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator

from .auth import UserReadBasic


# --- Patrones de Turno ---
class ShiftPatternBase(BaseModel):
    name: str; description: Optional[str] = None; pattern_sequence: str = Field(..., min_length=1)

class ShiftPatternReadBasic(ShiftPatternBase):
    id: int; cycle_length_days: int
    class Config: orm_mode = True

class ShiftPatternCreate(ShiftPatternBase):
    pass

class ShiftPatternUpdate(BaseModel):
    name: Optional[str] = None; description: Optional[str] = None
    pattern_sequence: Optional[str] = Field(None, min_length=1)

class ShiftPatternRead(ShiftPatternBase):
    id: int; cycle_length_days: int
    class Config: orm_mode = True

# --- Asignaciones de Turno ---
class ShiftAssignmentBase(BaseModel):
    user_id: int; pattern_id: int; reference_date: date; offset_days: int = Field(..., ge=0)

class ShiftAssignmentCreate(ShiftAssignmentBase):
    pass

class ShiftAssignmentRead(ShiftAssignmentBase):
    id: int; user: UserReadBasic; pattern: ShiftPatternReadBasic
    class Config: orm_mode = True

# --- Ausencias ---
class AbsenceBase(BaseModel):
    user_id: int; start_date: date; end_date: date
    absence_type: Literal['V', 'B', 'A', 'F']; notes: Optional[str] = None
    @validator('end_date')
    def end_date_must_be_after_start_date(cls, end_date, values):
        start_date = values.get('start_date')
        if start_date and end_date < start_date:
            raise ValueError('End date cannot be before start date')
        return end_date

class AbsenceCreate(AbsenceBase):
    pass

class AbsenceRead(AbsenceBase):
    id: int; created_at: date
    class Config: orm_mode = True

class AbsenceUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    absence_type: Optional[Literal['V', 'B', 'A', 'F']] = None
    notes: Optional[str] = None
    @validator('end_date')
    def validate_end_date_update(cls, end_date, values):
        if 'start_date' in values and values['start_date'] is not None and end_date is not None:
            if end_date < values['start_date']:
                raise ValueError('End date cannot be before start date')
        return end_date

# --- Overrides de Turno ---
class ShiftOverrideBase(BaseModel):
    user_id: int
    date: date
    actual_shift_code: str = Field(..., max_length=10)
    notes: Optional[str] = None

class ShiftOverrideCreate(ShiftOverrideBase):
    @validator('actual_shift_code')
    def validate_shift_code(cls, v):
        valid_codes = ['M', 'T', 'N']
        if v not in valid_codes:
            raise ValueError(f"Código de turno inválido. Usar: {', '.join(valid_codes)}")
        return v

class ShiftOverrideRead(ShiftOverrideBase):
    id: int
    created_at: datetime
    user: Optional[UserReadBasic] = None
    class Config: orm_mode = True

# --- Vacaciones ---
class VacationRequestBase(BaseModel):
    start_date: date
    end_date: date
    notes: Optional[str] = None
    @validator('end_date')
    def end_date_must_be_after_start_date(cls, end_date, values):
        start_date = values.get('start_date')
        if start_date and isinstance(end_date, date) and end_date < start_date:
            raise ValueError('La fecha de fin no puede ser anterior a la fecha de inicio')
        return end_date

class VacationRequestCreate(VacationRequestBase):
    user_id: int

class VacationRequestUpdate(BaseModel):
    status: Literal['Aprobado', 'Rechazado']
    manager_notes: Optional[str] = None

class VacationRequestRead(VacationRequestBase):
    id: int
    user_id: int
    status: str
    manager_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    reviewed_by_id: Optional[int] = None
    user: Optional[UserReadBasic] = None
    reviewed_by: Optional[UserReadBasic] = None
    class Config: orm_mode = True

class VacationCalendarEvent(BaseModel):
    type: Literal['vacation_request'] = "vacation_request"
    id: int
    status: str
    user_id: int
    start_date: date
    end_date: date
    notes: Optional[str] = None
    manager_notes: Optional[str] = None
    username: Optional[str] = None
    class Config: orm_mode = True
