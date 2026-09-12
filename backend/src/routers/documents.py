# Auto-generated router module
import json
import logging
import os
import shutil
from datetime import datetime, timedelta, date, time
from decimal import Decimal
from typing import List, Optional, Union, Literal, Any, Dict, Tuple

from fastapi import (
    APIRouter, HTTPException, Depends, File, UploadFile, Form,
    BackgroundTasks, Body, status, Query, Response, Request
)
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session, joinedload, contains_eager
from sqlalchemy import func, distinct, case, or_, text
from sqlalchemy.orm.attributes import flag_modified

from src.database import get_db, SessionLocal
from src.auth import (
    create_access_token,
    verify_password,
    get_current_user,
    get_admin_user,
    get_jefe_seccion_user,
    get_password_hash
)
from src.config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from src.schemas import *
from src.models.base import Base
from src.models.role import Role
from src.models.section import Section
from src.models.line import Line
from src.models.machine import Machine
from src.models.supplier import Supplier
from src.models.inventory import Inventory
from src.models.associations import MachinePartAssociation
from src.models.maintenance import Maintenance
from src.models.work_order import WorkOrder, FailureCode, CauseCode, RemedyCode
from src.models.warehouse import Warehouse
from src.models.user import User 
from src.models.document import Document
from src.models.supplier_product_price import SupplierProductPrice
from src.models.task_list import TaskList
from src.models.task_step import TaskStep
from src.models.shift_pattern import ShiftPattern
from src.models.shift_assignment import ShiftAssignment
from src.models.absence import Absence
from src.models.shift_override import ShiftOverride
from src.models.maintenance_backlog import MaintenanceBacklog, BacklogPriority, BacklogStatus
from src.models.document_attachment import DocumentAttachment
from src.models.alert import Alert
from src.models.audit_log import AuditLog
from src.models import absence_crud, shift_override_crud, vacation_request_crud
from src.models.format import Format
from src.models.vacation_request import VacationRequest
from src.models.checklist_progress import ChecklistProgress
from src.models.work_order_material import WorkOrderMaterial
from src.models.work_order_technician import WorkOrderTechnician
from src.models.maintenance_request import MaintenanceRequest
from src.middleware.audit_middleware import audit_manager
from src.gamification.points_engine import get_points_engine

from .helpers import (
    PROXY_URL,
    VACATION_MANAGER_ROLES, MANAGER_ROLES,
    INVENTORY_ACCESS_ROLES, FINANCIAL_ACCESS_ROLES,
    PRODUCT_EDIT_ROLES, RESTRICTED_WORKER_ROLES,
    CONSULTANT_ROLES, CALENDAR_ACCESS_ROLES,
    get_inventory_user, get_financial_user, get_product_editor,
    get_active_order_for_maintenance, get_all_orders_for_maintenance,
    can_generate_new_order, get_maintenance_statistics,
    get_current_shift_user, handle_checklist_integration,
    add_technician_to_order, get_order_technicians,
    generate_work_order_from_task_list
)

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Section lines 8264-8430 ---
# --- ENDPOINTS NUEVOS PARA DOCUMENTOS  ---

# Subir documento
@router.post("/documents/{entity_type}/{entity_id}/upload", response_model=DocumentAttachmentRead)
async def upload_document(
    entity_type: str,
    entity_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sube un documento asociado a una entidad específica.
    VERSIÓN FINAL Y ROBUSTA.
    """
    if entity_type not in ["machine", "work_order", "inventory", "maintenance", "legal"]:
        raise HTTPException(status_code=400, detail="Tipo de entidad no válido")

    file_extension = ""
    if "." in file.filename:
        file_extension = file.filename.rsplit('.', 1)[1].lower()

    allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx', 'txt']
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Tipo de archivo no permitido: {file_extension}")
    
    file_directory = f"src/storage/documents/attachments/{entity_type}/{entity_id}"
    os.makedirs(file_directory, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Usamos secure_filename para limpiar el nombre del archivo de caracteres problemáticos
    safe_filename = secure_filename(file.filename)
    new_filename = f"{timestamp}_{safe_filename}"
    file_path = os.path.join(file_directory, new_filename)
    
    file_size = 0
    try:
        # Guardamos el archivo en disco en bloques para manejar archivos grandes de forma eficiente.
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Obtenemos el tamaño real del archivo una vez guardado en disco.
        file_size = os.path.getsize(file_path)

    except Exception as e:
        logger.error(f"Error crítico al guardar el archivo en disco: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="No se pudo guardar el archivo en el servidor.")
    finally:
        # Es una buena práctica cerrar siempre el objeto de archivo.
        file.file.close()

    # Creamos el registro en la base de datos con la información correcta.
    doc_attachment = DocumentAttachment(
        file_name=new_filename,
        original_file_name=file.filename,
        file_path=file_path,
        file_type=file_extension, # Guardamos la extensión para la lógica de vista previa del frontend.
        file_size=file_size,
        description=description,
        uploaded_by_id=current_user.id,
        entity_type=entity_type,
        entity_id=entity_id
    )
    
    db.add(doc_attachment)
    db.commit()
    db.refresh(doc_attachment)
    
    return doc_attachment


@router.delete("/documents/attachment/{document_id}", status_code=204)
async def delete_document_attachment(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina un documento adjunto específico."""
    # Mismo código que el delete actual pero con ruta específica
    is_admin = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
    
    doc = db.query(DocumentAttachment).filter(DocumentAttachment.id == document_id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    if not is_admin and doc.uploaded_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tiene permisos para eliminar este documento")
    
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    db.delete(doc)
    db.commit()
    
    return None


    """
    Endpoint específico para vista previa (inline, no descarga)
    """
    from fastapi.responses import FileResponse
    import os
    
    # Buscar el documento
    doc = db.query(DocumentAttachment).filter(DocumentAttachment.id == document_id).first()
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

@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina un documento específico."""
    # Verificar si solo admin o jefe puede eliminar
    is_admin = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
    
    doc = db.query(DocumentAttachment).filter(DocumentAttachment.id == document_id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Solo el admin o quien subió el documento puede eliminarlo
    if not is_admin and doc.uploaded_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tiene permisos para eliminar este documento")
    
    # Eliminar archivo físico
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    # Eliminar registro de BD
    db.delete(doc)
    db.commit()
    
    return None
# --- FIN ENDPOINTS DOCUMENTOS ---


# --- Section lines 12030-12141 ---
# --- ALIAS PARA COMPATIBILIDAD CON FRONTEND EXISTENTE ---
@router.get("/documents/list/{entity_type}/{entity_id}", response_model=List[DocumentAttachmentRead])
async def get_entity_documents(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene la lista de documentos asociados a una entidad específica."""
    documents = db.query(DocumentAttachment).options(
        joinedload(DocumentAttachment.uploaded_by)
    ).filter(
        DocumentAttachment.entity_type == entity_type,
        DocumentAttachment.entity_id == entity_id
    ).order_by(DocumentAttachment.uploaded_at.desc()).all()
    
    return documents

# --- ALIAS CON PREFIX /api PARA COMPATIBILIDAD CON FRONTEND ---
@router.get("/documents/preview/{document_id}")
async def preview_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint específico para vista previa (inline, no descarga)"""
    from fastapi.responses import FileResponse
    import os
    
    # Buscar el documento
    doc = db.query(DocumentAttachment).filter(DocumentAttachment.id == document_id).first()
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
            "Content-Disposition": f"inline; filename=\"{doc.file_name}\""
        }
    )

@router.get("/documents/download/{document_id}")
async def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ENDPOINT DE DESCARGA CORREGIDO - Versión completa"""
    from fastapi.responses import FileResponse
    import os
    
    # Buscar el documento
    doc = db.query(DocumentAttachment).filter(DocumentAttachment.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    
    # Verificar que el archivo existe físicamente
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor.")
    
    # Verificar que el archivo no está vacío
    file_size = os.path.getsize(doc.file_path)
    if file_size == 0:
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
    
    # Devolver el archivo con el tipo MIME correcto
    return FileResponse(
        path=doc.file_path,
        filename=doc.original_file_name,
        media_type=mime_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{doc.file_name}\"",
            "Content-Length": str(file_size)
        }
    )

