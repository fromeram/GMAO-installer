# src/models/document_attachment.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class DocumentAttachment(Base):
    __tablename__ = "document_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    original_file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    entity_type = Column(String, nullable=False)  # 'machine', 'work_order', etc.
    entity_id = Column(Integer, nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])