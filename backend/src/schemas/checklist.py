# schemas/checklist.py — Schemas de checklists y progreso de pasos
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ChecklistStepProgress(BaseModel):
    step_id: int
    completed: bool = False
    notes: Optional[str] = None
    actual_time_minutes: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class ChecklistProgressCreate(BaseModel):
    work_order_id: int
    task_list_id: int
    steps_progress: List[ChecklistStepProgress] = []
    total_elapsed_time: Optional[float] = 0
    progress_percent: Optional[float] = 0
    extra_data: Optional[Dict[str, Any]] = None

class ChecklistProgressUpdate(BaseModel):
    steps_progress: Optional[List[ChecklistStepProgress]] = None
    total_elapsed_time: Optional[float] = None
    progress_percent: Optional[float] = None
    extra_data: Optional[Dict[str, Any]] = None
    is_completed: Optional[bool] = False

class ChecklistProgressRead(BaseModel):
    id: int
    work_order_id: int
    task_list_id: int
    steps_progress: List[ChecklistStepProgress] = []
    total_elapsed_time: float
    progress_percent: float
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    created_by_id: int
    extra_data: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True
