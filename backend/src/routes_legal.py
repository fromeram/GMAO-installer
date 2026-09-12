# src/routes_legal.py - VERSIÓN CORREGIDA

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import logging

from src.database import get_db
from src.auth import get_current_user
from src.models.maintenance import Maintenance
from src.models.machine import Machine
from src.models.user import User
from src.models.role import Role

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Modelos Pydantic ---
class LegalMaintenanceCreate(BaseModel):
    title: str
    description: str
    maquina_id: int
    frecuencia: str
    fechaInicio: str
    notification_interval: int
    assigned_role_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    # ✅ Campos adicionales para el formulario profesional
    tipo_regulacion: Optional[str] = None
    organismo_certificador: Optional[str] = None
    numero_certificado: Optional[str] = None
    normativa_aplicable: Optional[str] = None

class LegalMaintenanceUpdate(BaseModel):
    title: str
    description: str
    maquina_id: int
    frecuencia: str
    fechaInicio: str
    notification_interval: int
    assigned_role_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    tipo_regulacion: Optional[str] = None
    organismo_certificador: Optional[str] = None
    numero_certificado: Optional[str] = None
    normativa_aplicable: Optional[str] = None

class LegalMaintenanceRead(BaseModel):
    id: int
    title: str
    description: str
    maquina_nombre: str
    frecuencia: str
    next_maintenance_date: Optional[date] = None
    notification_interval: Optional[int] = None
    assigned_role_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    tipo_regulacion: Optional[str] = None
    organismo_certificador: Optional[str] = None
    numero_certificado: Optional[str] = None
    normativa_aplicable: Optional[str] = None
    # ✅ CAMPO SEGURO: Solo incluir si existe en el modelo
    generated_order_id: Optional[int] = None
    
    class Config:
        from_attributes = True

# --- Endpoints ---
@router.get("/mantenimiento-legal", response_model=List[LegalMaintenanceRead], tags=["Mantenimiento Legal"])
def get_legal_maintenances(db: Session = Depends(get_db)):
    """Obtiene todos los planes de mantenimiento de tipo Legal."""
    try:
        maintenances = db.query(Maintenance).options(
            joinedload(Maintenance.machine)
        ).filter(Maintenance.type == "Legal").order_by(Maintenance.id.desc()).all()
        
        response = []
        for m in maintenances:
            # ✅ SOLUCIÓN SEGURA: usar getattr para evitar AttributeError
            maintenance_data = {
                "id": m.id,
                "title": m.title,
                "description": m.description,
                "maquina_nombre": m.machine.nombre if m.machine else "N/A",
                "frecuencia": m.frequency,
                "next_maintenance_date": m.next_maintenance_date.date() if m.next_maintenance_date else None,
                "notification_interval": m.notification_interval,
                "assigned_role_id": m.assigned_role_id,
                "assigned_user_id": m.assigned_user_id,
                "tipo_regulacion": getattr(m, 'tipo_regulacion', None),
                "organismo_certificador": getattr(m, 'organismo_certificador', None),
                "numero_certificado": getattr(m, 'numero_certificado', None),
                "normativa_aplicable": getattr(m, 'normativa_aplicable', None),
                # ✅ CAMPO PROBLEMÁTICO RESUELTO: Solo incluir si existe
                "generated_order_id": getattr(m, 'generated_order_id', None),
            }
            response.append(LegalMaintenanceRead(**maintenance_data))
        
        return response
        
    except Exception as e:
        logger.error(f"Error obteniendo mantenimientos legales: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/mantenimiento-legal", response_model=LegalMaintenanceRead, tags=["Mantenimiento Legal"])
def create_legal_maintenance(data: LegalMaintenanceCreate, db: Session = Depends(get_db)):
    """Crea un nuevo plan de mantenimiento de tipo Legal."""
    try:
        fecha_inicio = datetime.strptime(data.fechaInicio, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")
    
    step = None
    if data.frecuencia == "Diario": step = relativedelta(days=1)
    elif data.frecuencia == "Semanal": step = relativedelta(weeks=1)
    elif data.frecuencia == "Mensual": step = relativedelta(months=1)
    elif data.frecuencia == "Trimestral": step = relativedelta(months=3)
    elif data.frecuencia == "Semestral": step = relativedelta(months=6)
    elif data.frecuencia == "Anual": step = relativedelta(years=1)
    elif data.frecuencia == "Bianual": step = relativedelta(years=2)
    elif data.frecuencia == "Trienal": step = relativedelta(years=3)
    elif data.frecuencia == "Quinquenal": step = relativedelta(years=5)
    
    next_date = fecha_inicio + step if step else fecha_inicio

    # ✅ CREAR MANTENIMIENTO CON CAMPOS SEGUROS
    maintenance_data = {
        "title": data.title,
        "description": data.description,
        "type": "Legal",
        "machine_id": data.maquina_id,
        "frequency": data.frecuencia,
        "created_at": datetime.combine(fecha_inicio, datetime.min.time()),
        "next_maintenance_date": datetime.combine(next_date, datetime.min.time()),
        "notification_interval": data.notification_interval,
        "assigned_role_id": data.assigned_role_id,
        "assigned_user_id": data.assigned_user_id,
    }
    
    # ✅ AÑADIR CAMPOS LEGALES SOLO SI ESTÁN DISPONIBLES EN EL MODELO
    legal_fields = ['tipo_regulacion', 'organismo_certificador', 'numero_certificado', 'normativa_aplicable']
    for field in legal_fields:
        value = getattr(data, field, None)
        if value is not None:
            maintenance_data[field] = value

    new_maintenance = Maintenance(**maintenance_data)
    
    try:
        db.add(new_maintenance)
        db.commit()
        db.refresh(new_maintenance)
        
        # ✅ RESPUESTA SEGURA
        response_data = {
            "id": new_maintenance.id,
            "title": new_maintenance.title,
            "description": new_maintenance.description,
            "maquina_nombre": new_maintenance.machine.nombre if new_maintenance.machine else "N/A",
            "frecuencia": new_maintenance.frequency,
            "next_maintenance_date": new_maintenance.next_maintenance_date.date() if new_maintenance.next_maintenance_date else None,
            "notification_interval": new_maintenance.notification_interval,
            "assigned_role_id": new_maintenance.assigned_role_id,
            "assigned_user_id": new_maintenance.assigned_user_id,
            "tipo_regulacion": getattr(new_maintenance, 'tipo_regulacion', None),
            "organismo_certificador": getattr(new_maintenance, 'organismo_certificador', None),
            "numero_certificado": getattr(new_maintenance, 'numero_certificado', None),
            "normativa_aplicable": getattr(new_maintenance, 'normativa_aplicable', None),
            "generated_order_id": getattr(new_maintenance, 'generated_order_id', None),
        }
        
        return LegalMaintenanceRead(**response_data)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando mantenimiento legal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.put("/mantenimiento-legal/{maintenance_id}", response_model=LegalMaintenanceRead, tags=["Mantenimiento Legal"])
def update_legal_maintenance(maintenance_id: int, data: LegalMaintenanceUpdate, db: Session = Depends(get_db)):
    """Actualiza un plan de mantenimiento legal existente."""
    try:
        maintenance = db.query(Maintenance).filter(
            Maintenance.id == maintenance_id, 
            Maintenance.type == "Legal"
        ).first()
        
        if not maintenance:
            raise HTTPException(status_code=404, detail="Mantenimiento legal no encontrado")

        # Actualizar fecha
        try:
            fecha_inicio = datetime.strptime(data.fechaInicio, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")
        
        # Calcular nueva fecha
        step = None
        if data.frecuencia == "Diario": step = relativedelta(days=1)
        elif data.frecuencia == "Semanal": step = relativedelta(weeks=1)
        elif data.frecuencia == "Mensual": step = relativedelta(months=1)
        elif data.frecuencia == "Trimestral": step = relativedelta(months=3)
        elif data.frecuencia == "Semestral": step = relativedelta(months=6)
        elif data.frecuencia == "Anual": step = relativedelta(years=1)
        elif data.frecuencia == "Bianual": step = relativedelta(years=2)
        elif data.frecuencia == "Trienal": step = relativedelta(years=3)
        elif data.frecuencia == "Quinquenal": step = relativedelta(years=5)
        
        next_date = fecha_inicio + step if step else fecha_inicio

        # ✅ ACTUALIZAR CAMPOS BÁSICOS
        maintenance.title = data.title
        maintenance.description = data.description
        maintenance.machine_id = data.maquina_id
        maintenance.frequency = data.frecuencia
        maintenance.next_maintenance_date = datetime.combine(next_date, datetime.min.time())
        maintenance.notification_interval = data.notification_interval
        maintenance.assigned_role_id = data.assigned_role_id
        maintenance.assigned_user_id = data.assigned_user_id
        
        # ✅ ACTUALIZAR CAMPOS LEGALES SOLO SI EXISTEN
        legal_fields = ['tipo_regulacion', 'organismo_certificador', 'numero_certificado', 'normativa_aplicable']
        for field in legal_fields:
            value = getattr(data, field, None)
            if hasattr(maintenance, field):
                setattr(maintenance, field, value)

        db.commit()
        db.refresh(maintenance)

        # ✅ RESPUESTA SEGURA
        response_data = {
            "id": maintenance.id,
            "title": maintenance.title,
            "description": maintenance.description,
            "maquina_nombre": maintenance.machine.nombre if maintenance.machine else "N/A",
            "frecuencia": maintenance.frequency,
            "next_maintenance_date": maintenance.next_maintenance_date.date() if maintenance.next_maintenance_date else None,
            "notification_interval": maintenance.notification_interval,
            "assigned_role_id": maintenance.assigned_role_id,
            "assigned_user_id": maintenance.assigned_user_id,
            "tipo_regulacion": getattr(maintenance, 'tipo_regulacion', None),
            "organismo_certificador": getattr(maintenance, 'organismo_certificador', None),
            "numero_certificado": getattr(maintenance, 'numero_certificado', None),
            "normativa_aplicable": getattr(maintenance, 'normativa_aplicable', None),
            "generated_order_id": getattr(maintenance, 'generated_order_id', None),
        }
        
        return LegalMaintenanceRead(**response_data)

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando mantenimiento legal {maintenance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.delete("/mantenimiento-legal/{maintenance_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Mantenimiento Legal"])
def delete_legal_maintenance(maintenance_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Elimina un plan de mantenimiento legal."""
    maintenance = db.query(Maintenance).filter(
        Maintenance.id == maintenance_id, 
        Maintenance.type == "Legal"
    ).first()
    
    if not maintenance:
        raise HTTPException(status_code=404, detail="Mantenimiento legal no encontrado")
        
    try:
        db.delete(maintenance)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando mantenimiento legal {maintenance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")