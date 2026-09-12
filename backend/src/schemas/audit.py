# schemas/audit.py — Schemas de auditoría
from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: Optional[int]
    user_name: str
    user_role: Optional[str]
    timestamp: datetime
    ip_address: Optional[str]
    changes_summary: Optional[str]
    module: str
    severity: str
    notes: Optional[str]
    class Config: orm_mode = True

class AuditLogDetailResponse(AuditLogResponse):
    old_values: Optional[Dict] = None
    new_values: Optional[Dict] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict] = None

class AutoCleanupConfig(BaseModel):
    enabled: bool = False
    loginLogsEnabled: bool = True
    loginLogsDays: int = 7
    generalLogsEnabled: bool = False
    generalLogsDays: int = 30
    frequency: str = "daily"
