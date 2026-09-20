# backend/src/routers/notifications.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from ..database import get_db
from ..auth import get_current_user
from ..models import User, Maintenance, Alert, Communication

router = APIRouter()

@router.get("/mantenimiento-preventivo/pending")
async def get_pending_maintenances(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene los mantenimientos preventivos pendientes para el usuario actual
    """
    # Obtener fecha actual
    today = datetime.now().date()
    
    # Buscar mantenimientos asignados al usuario o su rol
    query = db.query(Maintenance).filter(
        Maintenance.is_completed == False,
        Maintenance.next_maintenance_date != None
    )
    
    # Filtrar por usuario o rol
    if current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento", "Calidad"]:
        # Los admins ven todos los mantenimientos pendientes
        maintenances = query.all()
    else:
        # Los demás usuarios solo ven los asignados a ellos o su rol
        maintenances = query.filter(
            db.or_(
                Maintenance.assigned_user_id == current_user.id,
                Maintenance.assigned_role_id == current_user.role_id
            )
        ).all()
    
    # Filtrar solo los que están próximos o vencidos
    pending_maintenances = []
    for maintenance in maintenances:
        if maintenance.next_maintenance_date:
            days_until = (maintenance.next_maintenance_date - today).days
            
            # Incluir si está dentro del intervalo de notificación
            notification_days = (maintenance.notification_interval or 24) / 24  # convertir horas a días
            if days_until <= notification_days:
                pending_maintenances.append({
                    "id": maintenance.id,
                    "title": maintenance.title,
                    "machine_name": maintenance.machine.nombre if maintenance.machine else "N/A",
                    "maquina_nombre": maintenance.machine.nombre if maintenance.machine else "N/A",
                    "next_maintenance_date": maintenance.next_maintenance_date.isoformat(),
                    "frecuencia": maintenance.frequency,
                    "assigned_user": {
                        "username": maintenance.assigned_user.username
                    } if maintenance.assigned_user else None,
                    "assigned_role": {
                        "nombre": maintenance.assigned_role.nombre
                    } if maintenance.assigned_role else None
                })
    
    return pending_maintenances

@router.get("/communications/unread")
async def get_unread_communications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene las comunicaciones no leídas del usuario
    """
    # Este endpoint depende de cómo esté implementado tu sistema de comunicaciones
    # Aquí un ejemplo básico:
    communications = []
    
    # Si tienes una tabla de comunicaciones, podrías hacer algo así:
    # unread_comms = db.query(Communication).filter(
    #     Communication.recipient_id == current_user.id,
    #     Communication.is_read == False
    # ).all()
    
    # Por ahora retornamos un array vacío o datos de prueba
    return communications

@router.get("/alerts/active")
async def get_active_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene las alertas activas del sistema
    """
    # Buscar alertas no resueltas
    query = db.query(Alert).filter(Alert.resolved == False)
    
    # Filtrar según el rol del usuario
    if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
        # Los usuarios normales solo ven alertas asignadas a ellos
        alerts = query.join(Alert.users).filter(
            User.id == current_user.id
        ).all()
    else:
        # Los admins ven todas las alertas
        alerts = query.all()
    
    # Formatear respuesta
    active_alerts = []
    for alert in alerts:
        active_alerts.append({
            "id": alert.id,
            "type": alert.type,
            "message": alert.message,
            "severity": alert.severity,
            "created_at": alert.created_at.isoformat(),
            "entity_type": alert.entity_type,
            "entity_id": alert.entity_id
        })
    
    return active_alerts

@router.post("/maintenance/generate-order/{maintenance_id}")
async def generate_maintenance_order(
    maintenance_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Genera una orden de trabajo desde un mantenimiento preventivo
    """
    # Verificar permisos
    if current_user.role.nombre not in ["Administrador", "Jefe de Mantenimiento"]:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Buscar el mantenimiento
    maintenance = db.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    if not maintenance:
        raise HTTPException(status_code=404, detail="Mantenimiento no encontrado")
    
    # Aquí iría la lógica para generar la orden de trabajo
    # Por ahora solo retornamos success
    return {
        "success": True,
        "message": "Orden de trabajo generada correctamente"
    }

@router.post("/communications/{comm_id}/read")
async def mark_communication_as_read(
    comm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marca una comunicación como leída
    """
    # Implementar según tu modelo de comunicaciones
    return {"success": True}

# Agregar las rutas al main.py:
# from .routers import notifications
# app.include_router(notifications.router, prefix="/api", tags=["notifications"])