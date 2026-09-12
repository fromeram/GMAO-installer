from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from src.utils.timezone_utils import serialize_datetime_with_timezone

class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    user_name: str
    user_role: Optional[str] = None
    timestamp: str  # Será un string ISO con zona horaria
    ip_address: Optional[str] = None
    changes_summary: Optional[str] = None
    module: Optional[str] = None
    severity: str = 'MEDIUM'
    notes: Optional[str] = None
    
    @classmethod
    def from_orm_audit_log(cls, audit_log):
        """Convierte un AuditLog de SQLAlchemy a respuesta con timezone"""
        return cls(
            id=audit_log.id,
            action=audit_log.action,
            entity_type=audit_log.entity_type,
            entity_id=audit_log.entity_id,
            user_name=audit_log.user_name,
            user_role=audit_log.user_role,
            timestamp=serialize_datetime_with_timezone(audit_log.timestamp),
            ip_address=audit_log.ip_address,
            changes_summary=audit_log.changes_summary,
            module=audit_log.module,
            severity=audit_log.severity,
            notes=audit_log.notes
        )
    
    class Config:
        orm_mode = True