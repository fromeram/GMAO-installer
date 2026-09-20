# src/routes_legal.py - VERSIÓN CORREGIDA PARA TABLA maintenances

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import logging

from src.database import get_db
from src.auth import get_current_user
from src.models.maintenance import Maintenance  # Asegúrate que el modelo corresponda a la tabla 'maintenances'
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
    maquina_id: int
    maquina_nombre: str
    frecuencia: str
    next_maintenance_date: Optional[date] = None
    last_maintenance_date: Optional[date] = None
    notification_interval: Optional[int] = None
    assigned_role_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    is_completed: Optional[bool] = None
    generated_order_id: Optional[int] = None
    task_list_id: Optional[int] = None
    tipo_regulacion: Optional[str] = None
    organismo_certificador: Optional[str] = None
    numero_certificado: Optional[str] = None
    normativa_aplicable: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# --- Endpoints ---
@router.get("/mantenimiento-legal", response_model=List[LegalMaintenanceRead], tags=["Mantenimiento Legal"])
def get_legal_maintenances(db: Session = Depends(get_db)):
    """Obtiene todos los planes de mantenimiento de tipo Legal."""
    maintenances = db.query(Maintenance).options(joinedload(Maintenance.machine)).filter(Maintenance.type == "Legal").order_by(Maintenance.id.desc()).all()
    
    response = []
    for m in maintenances:
        response.append(
            LegalMaintenanceRead(
                id=m.id,
                title=m.title,
                description=m.description,
                maquina_id=m.machine_id,
                maquina_nombre=m.machine.nombre if m.machine else "N/A",
                frecuencia=m.frequency,
                next_maintenance_date=m.next_maintenance_date.date() if m.next_maintenance_date else None,
                last_maintenance_date=m.last_maintenance_date.date() if m.last_maintenance_date else None,
                notification_interval=m.notification_interval,
                assigned_role_id=m.assigned_role_id,
                assigned_user_id=m.assigned_user_id,
                is_completed=m.is_completed,
                generated_order_id=m.generated_order_id,
                task_list_id=m.task_list_id,
                # ✅ Campos adicionales con manejo seguro
                tipo_regulacion=getattr(m, 'tipo_regulacion', None),
                organismo_certificador=getattr(m, 'organismo_certificador', None),
                numero_certificado=getattr(m, 'numero_certificado', None),
                normativa_aplicable=getattr(m, 'normativa_aplicable', None),
                created_at=m.created_at
            )
        )
    return response

@router.post("/mantenimiento-legal", response_model=LegalMaintenanceRead, tags=["Mantenimiento Legal"])
def create_legal_maintenance(data: LegalMaintenanceCreate, db: Session = Depends(get_db)):
    """Crea un nuevo plan de mantenimiento de tipo Legal."""
    try:
        fecha_inicio = datetime.strptime(data.fechaInicio, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")
    
    # Mapeo de frecuencias mejorado para mantenimiento legal
    step = None
    if data.frecuencia == "Diario": step = relativedelta(days=1)
    elif data.frecuencia == "Semanal": step = relativedelta(weeks=1)
    elif data.frecuencia == "Mensual": step = relativedelta(months=1)
    elif data.frecuencia == "Trimestral": step = relativedelta(months=3)
    elif data.frecuencia == "Semestral": step = relativedelta(months=6)
    elif data.frecuencia == "Anual": step = relativedelta(years=1)
    elif data.frecuencia == "Bianual": step = relativedelta(years=2)
    elif data.frecuencia == "Trienal": step = relativedelta(years=3)
    elif data.frecuencia == "Cada 4 años": step = relativedelta(years=4)
    elif data.frecuencia == "Quinquenal": step = relativedelta(years=5)
    elif data.frecuencia == "Cada 8 años": step = relativedelta(years=8)
    elif data.frecuencia == "Cada 16 años": step = relativedelta(years=16)
    
    next_date = fecha_inicio + step if step else fecha_inicio

    new_maintenance = Maintenance(
        title=data.title,
        description=data.description,
        type="Legal",
        machine_id=data.maquina_id,
        frequency=data.frecuencia,
        created_at=datetime.combine(fecha_inicio, datetime.min.time()),
        next_maintenance_date=datetime.combine(next_date, datetime.min.time()),
        notification_interval=data.notification_interval,
        assigned_role_id=data.assigned_role_id,
        assigned_user_id=data.assigned_user_id
    )
    
    # ✅ Agregar campos adicionales usando setattr para compatibilidad
    if data.tipo_regulacion:
        setattr(new_maintenance, 'tipo_regulacion', data.tipo_regulacion)
    if data.organismo_certificador:
        setattr(new_maintenance, 'organismo_certificador', data.organismo_certificador)
    if data.numero_certificado:
        setattr(new_maintenance, 'numero_certificado', data.numero_certificado)
    if data.normativa_aplicable:
        setattr(new_maintenance, 'normativa_aplicable', data.normativa_aplicable)
    
    db.add(new_maintenance)
    db.commit()
    db.refresh(new_maintenance)
    
    response = LegalMaintenanceRead(
        id=new_maintenance.id,
        title=new_maintenance.title,
        description=new_maintenance.description,
        maquina_id=new_maintenance.machine_id,
        maquina_nombre=new_maintenance.machine.nombre if new_maintenance.machine else "N/A",
        frecuencia=new_maintenance.frequency,
        next_maintenance_date=new_maintenance.next_maintenance_date.date() if new_maintenance.next_maintenance_date else None,
        last_maintenance_date=new_maintenance.last_maintenance_date.date() if new_maintenance.last_maintenance_date else None,
        notification_interval=new_maintenance.notification_interval,
        assigned_role_id=new_maintenance.assigned_role_id,
        assigned_user_id=new_maintenance.assigned_user_id,
        is_completed=new_maintenance.is_completed,
        generated_order_id=new_maintenance.generated_order_id,
        task_list_id=new_maintenance.task_list_id,
        tipo_regulacion=getattr(new_maintenance, 'tipo_regulacion', None),
        organismo_certificador=getattr(new_maintenance, 'organismo_certificador', None),
        numero_certificado=getattr(new_maintenance, 'numero_certificado', None),
        normativa_aplicable=getattr(new_maintenance, 'normativa_aplicable', None),
        created_at=new_maintenance.created_at
    )
    return response

@router.put("/mantenimiento-legal/{maintenance_id}", response_model=LegalMaintenanceRead, tags=["Mantenimiento Legal"])
def update_legal_maintenance(maintenance_id: int, data: LegalMaintenanceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Actualiza un plan de mantenimiento legal."""
    maintenance = db.query(Maintenance).filter(Maintenance.id == maintenance_id, Maintenance.type == "Legal").first()
    if not maintenance:
        raise HTTPException(status_code=404, detail="Mantenimiento legal no encontrado")
    
    try:
        fecha_inicio = datetime.strptime(data.fechaInicio, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")
    
    # Calcular próxima fecha basada en la frecuencia
    step = None
    if data.frecuencia == "Diario": step = relativedelta(days=1)
    elif data.frecuencia == "Semanal": step = relativedelta(weeks=1)
    elif data.frecuencia == "Mensual": step = relativedelta(months=1)
    elif data.frecuencia == "Trimestral": step = relativedelta(months=3)
    elif data.frecuencia == "Semestral": step = relativedelta(months=6)
    elif data.frecuencia == "Anual": step = relativedelta(years=1)
    elif data.frecuencia == "Bianual": step = relativedelta(years=2)
    elif data.frecuencia == "Trienal": step = relativedelta(years=3)
    elif data.frecuencia == "Cada 4 años": step = relativedelta(years=4)
    elif data.frecuencia == "Quinquenal": step = relativedelta(years=5)
    elif data.frecuencia == "Cada 8 años": step = relativedelta(years=8)
    elif data.frecuencia == "Cada 16 años": step = relativedelta(years=16)
    
    next_date = fecha_inicio + step if step else fecha_inicio
    
    # Actualizar campos básicos
    maintenance.title = data.title
    maintenance.description = data.description
    maintenance.machine_id = data.maquina_id
    maintenance.frequency = data.frecuencia
    maintenance.next_maintenance_date = datetime.combine(next_date, datetime.min.time())
    maintenance.notification_interval = data.notification_interval
    maintenance.assigned_role_id = data.assigned_role_id
    maintenance.assigned_user_id = data.assigned_user_id
    
    # ✅ Actualizar campos adicionales usando setattr
    setattr(maintenance, 'tipo_regulacion', data.tipo_regulacion)
    setattr(maintenance, 'organismo_certificador', data.organismo_certificador)
    setattr(maintenance, 'numero_certificado', data.numero_certificado)
    setattr(maintenance, 'normativa_aplicable', data.normativa_aplicable)
    
    try:
        db.commit()
        db.refresh(maintenance)
        
        response = LegalMaintenanceRead(
            id=maintenance.id,
            title=maintenance.title,
            description=maintenance.description,
            maquina_id=maintenance.machine_id,
            maquina_nombre=maintenance.machine.nombre if maintenance.machine else "N/A",
            frecuencia=maintenance.frequency,
            next_maintenance_date=maintenance.next_maintenance_date.date() if maintenance.next_maintenance_date else None,
            last_maintenance_date=maintenance.last_maintenance_date.date() if maintenance.last_maintenance_date else None,
            notification_interval=maintenance.notification_interval,
            assigned_role_id=maintenance.assigned_role_id,
            assigned_user_id=maintenance.assigned_user_id,
            is_completed=maintenance.is_completed,
            generated_order_id=maintenance.generated_order_id,
            task_list_id=maintenance.task_list_id,
            tipo_regulacion=getattr(maintenance, 'tipo_regulacion', None),
            organismo_certificador=getattr(maintenance, 'organismo_certificador', None),
            numero_certificado=getattr(maintenance, 'numero_certificado', None),
            normativa_aplicable=getattr(maintenance, 'normativa_aplicable', None),
            created_at=maintenance.created_at
        )
        return response
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando mantenimiento legal {maintenance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.delete("/mantenimiento-legal/{maintenance_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Mantenimiento Legal"])
def delete_legal_maintenance(maintenance_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Elimina un plan de mantenimiento legal."""
    maintenance = db.query(Maintenance).filter(Maintenance.id == maintenance_id, Maintenance.type == "Legal").first()
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