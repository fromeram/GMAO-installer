# schemas/tasks.py — Schemas de listas de tareas y pasos
from typing import Optional, List
from pydantic import BaseModel, Field


class TaskStepBase(BaseModel):
    step_order: int = Field(..., ge=1)
    description: str
    estimated_time_minutes: Optional[int] = Field(None, ge=0)

class TaskStepRead(TaskStepBase):
    id: int; task_list_id: int
    class Config: orm_mode = True

class TaskStepCreate(TaskStepBase):
    pass

class TaskStepUpdate(BaseModel):
    step_order: Optional[int] = Field(None, ge=1)
    description: Optional[str] = None
    estimated_time_minutes: Optional[int] = Field(None, ge=0)

class TaskListBase(BaseModel):
    name: str
    description: Optional[str] = None
    applies_to_type: Optional[str] = None

class TaskListCreate(TaskListBase):
    steps: List[TaskStepCreate] = []

class TaskListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    applies_to_type: Optional[str] = None

class TaskListReadBasic(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    applies_to_type: Optional[str] = None
    steps_count: int
    total_estimated_minutes: int
    class Config: orm_mode = True

class TaskListRead(TaskListBase):
    id: int
    steps: List[TaskStepRead] = []
    class Config: orm_mode = True

class TaskListForMaintenanceRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    applies_to_type: Optional[str] = None
    steps_count: int
    total_estimated_minutes: int
    class Config: orm_mode = True
