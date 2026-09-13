# src/routers/license.py
"""
Router de Estado y Activación de Licencias de GMAO System.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from ..database import get_db
from ..licensing.license_manager import get_license_status, activate_license_key
from ..licensing.machine_id import get_or_create_machine_id

router = APIRouter(tags=["Licenciamiento"])

class LicenseActivateRequest(BaseModel):
    license_key: str = Field(..., description="Clave de activación proporcionada por Fran Romera")

class ContactInfoResponse(BaseModel):
    author: str = "Fran Romera Martínez"
    contact_email: str = "fromeram@gmail.com"
    support_message: str = "Para adquirir una licencia permanente, soporte industrial o extender tu periodo de evaluación, contacta directamente con el autor."

@router.get("/license/status", summary="Obtener Estado de la Licencia y Días Restantes")
def check_license(db: Session = Depends(get_db)):
    """
    Devuelve el estado de la licencia, Machine ID y días de prueba restantes.
    Accesible para informar al usuario en la cabecera o pantalla de bloqueo.
    """
    status_info = get_license_status(db)
    return status_info

@router.post("/license/activate", summary="Activar Licencia con Clave Criptográfica")
def activate_system_license(req: LicenseActivateRequest, db: Session = Depends(get_db)):
    """
    Valida y activa una clave criptográfica firmada para este servidor.
    """
    if not req.license_key or not req.license_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La clave de licencia no puede estar vacía"
        )
        
    success, message, new_status = activate_license_key(req.license_key.strip(), db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
        
    return {
        "success": True,
        "message": message,
        "license": new_status
    }

@router.get("/license/contact", summary="Información de Contacto para Licencias")
def get_license_contact():
    """Información oficial de contacto para solicitar licencias."""
    return ContactInfoResponse()
