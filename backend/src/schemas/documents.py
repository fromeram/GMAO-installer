# schemas/documents.py — Schemas de documentos adjuntos
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DocumentAttachmentBase(BaseModel):
    file_name: str
    original_file_name: str
    file_path: str
    file_type: str
    file_size: int
    description: Optional[str] = None
    entity_type: str
    entity_id: int

class DocumentAttachmentCreate(DocumentAttachmentBase):
    pass

class DocumentAttachmentRead(DocumentAttachmentBase):
    id: int
    uploaded_by_id: int
    uploaded_at: datetime
    class Config: orm_mode = True
