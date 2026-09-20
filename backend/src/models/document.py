# backend/src/models/document.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB # Importar JSONB
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
# from .user import User # Asegurar importación
# from .work_order import WorkOrder

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True) # index=True está bien
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    content = Column(Text, nullable=True) # Usar Text es más flexible que String
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    supplier_name = Column(String, nullable=True)
    total_amount = Column(Float, nullable=True) # Considerar Numeric aquí también si es monetario
    # --- MODIFICADO: Usar JSONB ---
    processed_data = Column(JSONB, nullable=True)
    # ------------------------------

    # Relaciones
    # Asegúrate que WorkOrder tiene back_populates="source_document"
    work_orders = relationship("WorkOrder", back_populates="source_document") # Quitar foreign_keys si no es ambiguo
    # Asegúrate que User tiene back_populates="documents"
    created_by = relationship("User", back_populates="documents")