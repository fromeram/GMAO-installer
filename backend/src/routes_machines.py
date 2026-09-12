# src/routes_machines.py - Gestión de documentos para máquinas

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
import os
import shutil
import logging
from werkzeug.utils import secure_filename

from src.database import get_db
from src.auth import get_current_user
from src.models.machine import Machine
from src.models.user import User
from src.models.document_attachment import DocumentAttachment

logger = logging.getLogger(__name__)
router = APIRouter()

# Modelos Pydantic para documentos de máquinas
from pydantic import BaseModel

class DocumentAttachmentRead(BaseModel):
    id: int
    file_name: str
    original_file_name: str
    file_type: str
    file_size: int
    description: Optional[str] = None
    uploaded_by_id: int
    uploaded_at: datetime
    entity_type: str
    entity_id: int
    
    class Config:
        from_attributes = True

# --- ENDPOINTS PARA DOCUMENTOS DE MÁQUINAS ---

@router.post("/machines/{machine_id}/documents/upload", response_model=DocumentAttachmentRead)
async def upload_machine_document(
    machine_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sube un documento asociado a una máquina específica.
    Tipos de documentos típicos: manuales, certificados, hojas de datos, planos, etc.
    """
    # Verificar que la máquina existe
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")
    
    # Validar extensión de archivo
    file_extension = ""
    if "." in file.filename:
        file_extension = file.filename.rsplit('.', 1)[1].lower()

    allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'dwg']
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Tipo de archivo no permitido: {file_extension}")
    
    # Crear directorio específico para documentos de la máquina
    file_directory = f"src/storage/documents/attachments/machine/{machine_id}"
    os.makedirs(file_directory, exist_ok=True)
    
    # Generar nombre único para el archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = secure_filename(file.filename)
    new_filename = f"{timestamp}_{safe_filename}"
    file_path = os.path.join(file_directory, new_filename)
    
    file_size = 0
    try:
        # Guardar archivo en disco
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="El archivo está vacío")

    except Exception as e:
        logger.error(f"Error guardando archivo para máquina {machine_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="No se pudo guardar el archivo en el servidor.")
    finally:
        file.file.close()

    # Crear registro en base de datos
    doc_attachment = DocumentAttachment(
        file_name=new_filename,
        original_file_name=file.filename,
        file_path=file_path,
        file_type=file_extension,
        file_size=file_size,
        description=description,
        uploaded_by_id=current_user.id,
        entity_type="machine",
        entity_id=machine_id
    )
    
    db.add(doc_attachment)
    db.commit()
    db.refresh(doc_attachment)
    
    logger.info(f"Documento subido para máquina {machine_id}: {file.filename} por usuario {current_user.id}")
    
    return doc_attachment

@router.get("/machines/{machine_id}/documents", response_model=List[DocumentAttachmentRead])
async def get_machine_documents(
    machine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene todos los documentos asociados a una máquina específica."""
    # Verificar que la máquina existe
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")
    
    # Obtener documentos ordenados por fecha de subida (más recientes primero)
    documents = db.query(DocumentAttachment).options(
        joinedload(DocumentAttachment.uploaded_by)
    ).filter(
        DocumentAttachment.entity_type == "machine",
        DocumentAttachment.entity_id == machine_id
    ).order_by(DocumentAttachment.uploaded_at.desc()).all()
    
    return documents

@router.get("/machines/documents/download/{document_id}")
async def download_machine_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Descarga un documento específico de una máquina."""
    # Buscar el documento
    doc = db.query(DocumentAttachment).filter(
        DocumentAttachment.id == document_id,
        DocumentAttachment.entity_type == "machine"
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    
    # Verificar que el archivo existe físicamente
    if not os.path.exists(doc.file_path):
        logger.error(f"Archivo no encontrado en disco: {doc.file_path}")
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor.")
    
    # Verificar que el archivo no está vacío
    file_size = os.path.getsize(doc.file_path)
    if file_size == 0:
        logger.error(f"Archivo vacío: {doc.file_path}")
        raise HTTPException(status_code=400, detail="El archivo está vacío.")
    
    # Determinar el tipo MIME correcto
    mime_type = 'application/octet-stream'
    if doc.file_type:
        mime_map = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'txt': 'text/plain',
            'dwg': 'application/acad'
        }
        mime_type = mime_map.get(doc.file_type.lower(), 'application/octet-stream')
    
    logger.info(f"Descargando documento de máquina: {doc.file_path} (Tamaño: {file_size} bytes)")
    
    return FileResponse(
        path=doc.file_path,
        filename=doc.original_file_name,
        media_type=mime_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{doc.original_file_name}\"",
            "Content-Length": str(file_size)
        }
    )

@router.get("/machines/documents/preview/{document_id}")
async def preview_machine_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vista previa de un documento de máquina (solo para PDF e imágenes)."""
    # Buscar el documento
    doc = db.query(DocumentAttachment).filter(
        DocumentAttachment.id == document_id,
        DocumentAttachment.entity_type == "machine"
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    
    # Verificar que el archivo existe
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor.")
    
    # Solo permitir vista previa para ciertos tipos
    if doc.file_type.lower() not in ['pdf', 'jpg', 'jpeg', 'png']:
        raise HTTPException(status_code=400, detail="Vista previa no disponible para este tipo de archivo.")
    
    # Determinar tipo MIME
    mime_map = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png'
    }
    mime_type = mime_map.get(doc.file_type.lower(), 'application/octet-stream')
    
    # Devolver para vista previa (inline)
    return FileResponse(
        path=doc.file_path,
        filename=doc.original_file_name,
        media_type=mime_type,
        headers={
            "Content-Disposition": f"inline; filename=\"{doc.original_file_name}\""
        }
    )

@router.delete("/machines/documents/{document_id}", status_code=204)
async def delete_machine_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina un documento específico de una máquina."""
    # Verificar permisos (solo admin, jefe de mantenimiento o quien subió el documento)
    is_admin = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
    
    doc = db.query(DocumentAttachment).filter(
        DocumentAttachment.id == document_id,
        DocumentAttachment.entity_type == "machine"
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Solo el admin o quien subió el documento puede eliminarlo
    if not is_admin and doc.uploaded_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tiene permisos para eliminar este documento")
    
    # Eliminar archivo físico
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
            logger.info(f"Archivo físico eliminado: {doc.file_path}")
        except Exception as e:
            logger.error(f"Error eliminando archivo físico {doc.file_path}: {e}")
    
    # Eliminar registro de BD
    db.delete(doc)
    db.commit()
    
    logger.info(f"Documento de máquina eliminado: ID {document_id} por usuario {current_user.id}")
    
    return None