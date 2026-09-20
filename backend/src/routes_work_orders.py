# src/routes_work_orders.py - Gestión de documentos para órdenes de trabajo

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
from src.models.work_order import WorkOrder
from src.models.user import User
from src.models.document_attachment import DocumentAttachment

logger = logging.getLogger(__name__)
router = APIRouter()

# Modelos Pydantic para documentos de órdenes de trabajo
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

# --- ENDPOINTS PARA DOCUMENTOS DE ÓRDENES DE TRABAJO ---

@router.post("/work-orders/{order_id}/documents/upload", response_model=DocumentAttachmentRead)
async def upload_work_order_document(
    order_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sube un documento asociado a una orden de trabajo específica.
    Tipos de documentos típicos: albaranes, certificados OCA, fotos del trabajo, partes de trabajo, etc.
    """
    # Verificar que la orden de trabajo existe
    work_order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
    
    # Validar extensión de archivo
    file_extension = ""
    if "." in file.filename:
        file_extension = file.filename.rsplit('.', 1)[1].lower()

    allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx', 'txt']
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Tipo de archivo no permitido: {file_extension}")
    
    # Verificar tamaño máximo (50MB)
    file.file.seek(0, 2)  # Ir al final del archivo
    file_size_check = file.file.tell()
    file.file.seek(0)  # Volver al inicio
    
    if file_size_check > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(status_code=400, detail="El archivo excede el tamaño máximo (50MB)")
    
    # Crear directorio específico para documentos de la orden de trabajo
    file_directory = f"src/storage/documents/attachments/work_order/{order_id}"
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
        logger.error(f"Error guardando archivo para orden {order_id}: {e}", exc_info=True)
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
        entity_type="work_order",
        entity_id=order_id
    )
    
    db.add(doc_attachment)
    db.commit()
    db.refresh(doc_attachment)
    
    logger.info(f"Documento subido para orden {order_id}: {file.filename} por usuario {current_user.id}")
    
    return doc_attachment

@router.get("/work-orders/{order_id}/documents", response_model=List[DocumentAttachmentRead])
async def get_work_order_documents(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene todos los documentos asociados a una orden de trabajo específica."""
    # Verificar que la orden de trabajo existe
    work_order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
    
    # Obtener documentos ordenados por fecha de subida (más recientes primero)
    documents = db.query(DocumentAttachment).options(
        joinedload(DocumentAttachment.uploaded_by)
    ).filter(
        DocumentAttachment.entity_type == "work_order",
        DocumentAttachment.entity_id == order_id
    ).order_by(DocumentAttachment.uploaded_at.desc()).all()
    
    return documents

@router.get("/work-orders/documents/download/{document_id}")
async def download_work_order_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Descarga un documento específico de una orden de trabajo."""
    # Buscar el documento
    doc = db.query(DocumentAttachment).filter(
        DocumentAttachment.id == document_id,
        DocumentAttachment.entity_type == "work_order"
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
            'txt': 'text/plain'
        }
        mime_type = mime_map.get(doc.file_type.lower(), 'application/octet-stream')
    
    logger.info(f"Descargando documento de orden: {doc.file_path} (Tamaño: {file_size} bytes)")
    
    return FileResponse(
        path=doc.file_path,
        filename=doc.original_file_name,
        media_type=mime_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{doc.original_file_name}\"",
            "Content-Length": str(file_size)
        }
    )

@router.get("/work-orders/documents/preview/{document_id}")
async def preview_work_order_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vista previa de un documento de orden de trabajo (solo para PDF e imágenes)."""
    # Buscar el documento
    doc = db.query(DocumentAttachment).filter(
        DocumentAttachment.id == document_id,
        DocumentAttachment.entity_type == "work_order"
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

@router.delete("/work-orders/documents/{document_id}", status_code=204)
async def delete_work_order_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina un documento específico de una orden de trabajo."""
    # Verificar permisos (solo admin, jefe de mantenimiento o quien subió el documento)
    is_admin = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
    
    doc = db.query(DocumentAttachment).filter(
        DocumentAttachment.id == document_id,
        DocumentAttachment.entity_type == "work_order"
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
    
    logger.info(f"Documento de orden eliminado: ID {document_id} por usuario {current_user.id}")
    
    return None

# --- ENDPOINTS ADICIONALES PARA AUDITORÍA Y REPORTES ---

@router.get("/work-orders/{order_id}/documents/summary")
async def get_work_order_documents_summary(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene un resumen de los documentos asociados a una orden de trabajo."""
    # Verificar que la orden de trabajo existe
    work_order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
    
    # Obtener estadísticas de documentos
    documents = db.query(DocumentAttachment).filter(
        DocumentAttachment.entity_type == "work_order",
        DocumentAttachment.entity_id == order_id
    ).all()
    
    total_documents = len(documents)
    total_size = sum(doc.file_size for doc in documents)
    
    # Agrupar por tipo de archivo
    types_summary = {}
    for doc in documents:
        file_type = doc.file_type.upper()
        if file_type not in types_summary:
            types_summary[file_type] = {'count': 0, 'size': 0}
        types_summary[file_type]['count'] += 1
        types_summary[file_type]['size'] += doc.file_size
    
    return {
        'order_id': order_id,
        'total_documents': total_documents,
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'types_summary': types_summary,
        'last_upload': max((doc.uploaded_at for doc in documents), default=None)
    }