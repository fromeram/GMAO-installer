# backend/src/routes_notifications.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
from datetime import datetime, timedelta
from .database import get_db
from .auth import get_current_user
from .models import User  # Añadir este import también
print("🚀 DEBUG: routes_notifications.py cargado correctamente")

router = APIRouter()

@router.get("/mantenimiento-preventivo/pending")
async def get_pending_maintenances(
    current_user: User = Depends(get_current_user),  # ✅ User, no Dict
    db: Session = Depends(get_db)
):
    print("🔥 DEBUG: Función get_pending_maintenances EJECUTÁNDOSE (VERSIÓN CORREGIDA)")
    """
    Obtiene los mantenimientos preventivos pendientes para el usuario actual
    utilizando el intervalo de notificación dinámico.
    """
    try:
        # MODIFICADO: Añadimos m.notification_interval a la consulta
        query = text("""
            SELECT 
                m.id,
                m.title,
                m.frequency,
                m.next_maintenance_date,
                m.notification_interval,
                maq.nombre as machine_name,
                u.username as assigned_username,
                r.nombre as assigned_role_name
            FROM maintenances m
            LEFT JOIN machines maq ON m.machine_id = maq.id
            LEFT JOIN users u ON m.assigned_user_id = u.id
            LEFT JOIN roles r ON m.assigned_role_id = r.id
            WHERE m.is_completed = false 
            AND m.next_maintenance_date IS NOT NULL
            AND (
                :is_admin = true 
                OR m.assigned_user_id = :user_id 
                OR m.assigned_role_id = :role_id
            )
        """)
        
        is_admin = hasattr(current_user, 'role') and current_user.role and current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento", "Calidad"]
        
        result = db.execute(query, {
            'is_admin': is_admin,
            'user_id': current_user.id,      # ✅ Sin .get()
            'role_id': current_user.role_id  # ✅ Sin .get()
        })
        
        pending_maintenances = []
        now = datetime.now() # Usamos datetime para comparar con más precisión
        
        for row in result:
            if row.next_maintenance_date:
                # NUEVA LÓGICA: Usar el intervalo de notificación de la base de datos
                # El intervalo se guarda en horas. Si no existe, usamos 24h por defecto.
                notification_interval_hours = row.notification_interval or 24
                
                # Calculamos la fecha límite para la notificación
                notification_deadline = row.next_maintenance_date - timedelta(hours=notification_interval_hours)
                
                # Si la fecha y hora actual ya ha pasado la fecha límite de notificación, lo añadimos
                if now >= notification_deadline:
                    pending_maintenances.append({
                        "id": row.id,
                        "title": row.title,
                        "machine_name": row.machine_name or "N/A",
                        "maquina_nombre": row.machine_name or "N/A",
                        "next_maintenance_date": row.next_maintenance_date.isoformat(),
                        "frecuencia": row.frequency,
                        "assigned_user": {
                            "username": row.assigned_username
                        } if row.assigned_username else None,
                        "assigned_role": {
                            "nombre": row.assigned_role_name
                        } if row.assigned_role_name else None
                    })
        
        return pending_maintenances
        
    except Exception as e:
        print(f"Error en pending maintenances: {e}")
        return []

# NUEVA FUNCIÓN PARA VACACIONES PENDIENTES
@router.get("/vacaciones/pending")
async def get_pending_vacations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print("🔥🔥🔥 DEBUG: FUNCIÓN VACACIONES/PENDING EJECUTÁNDOSE (REAL) 🔥🔥🔥")
    print(f"🔍 Usuario: {current_user.username}, Rol: {current_user.role.nombre if current_user.role else 'Sin rol'}")
    
    try:
        # ✅ CONSULTA REAL: Solo solicitudes 'Solicitado' para administradores
        query = text("""
            SELECT 
                vr.id,
                vr.start_date as fecha_inicio,
                vr.end_date as fecha_fin,
                vr.notes as motivo,
                vr.status as estado,
                vr.created_at as fecha_solicitud,
                vr.manager_notes as observaciones,
                vr.user_id,
                u.username as solicitante_username
            FROM vacation_requests vr
            LEFT JOIN users u ON vr.user_id = u.id
            WHERE vr.status = 'Solicitado' AND :is_admin = true
            ORDER BY vr.created_at DESC
        """)
        
        # Determinar si es admin
        is_admin = hasattr(current_user, 'role') and current_user.role and current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento", "Calidad"]
        print(f"🔍 DEBUG: Es admin: {is_admin}")
        
        result = db.execute(query, {
            'is_admin': is_admin
        })
        
        pending_vacations = []
        
        for row in result:
            print(f"🔍 DEBUG: Procesando solicitud ID {row.id}, Estado: {row.estado}")
            if row.estado == 'Solicitado' and is_admin:
                vacation_data = {
                    "id": row.id,
                    "fecha_inicio": row.fecha_inicio.isoformat(),
                    "fecha_fin": row.fecha_fin.isoformat(),
                    "motivo": row.motivo or "Sin motivo especificado",
                    "estado": row.estado,
                    "fecha_solicitud": row.fecha_solicitud.isoformat(),
                    "observaciones": row.observaciones,
                    "solicitante": {
                        "username": row.solicitante_username,
                        "nombre": row.solicitante_username,
                        "apellidos": ""
                    },
                    "notification_type": "nueva_solicitud"
                }
                pending_vacations.append(vacation_data)
                print(f"✅ DEBUG: Añadida solicitud ID {row.id}")
        
        print(f"🔍 DEBUG: Total solicitudes devueltas: {len(pending_vacations)}")
        return pending_vacations
        
    except Exception as e:
        print(f"❌ ERROR en pending vacations: {e}")
        import traceback
        traceback.print_exc()
        return []

# NUEVA FUNCIÓN PARA MARCAR NOTIFICACIÓN DE VACACIONES COMO VISTA
@router.post("/vacaciones/{vacation_id}/mark-notified")
async def mark_vacation_as_notified(
    vacation_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marca una notificación de vacaciones como vista/notificada
    """
    try:
        # Aquí podrías agregar lógica para marcar como vista si tienes una tabla de notificaciones
        # Por ahora solo retornamos success
        return {"success": True, "message": "Notificación marcada como vista"}
    except Exception as e:
        print(f"Error marking vacation notification: {e}")
        return {"success": False, "message": "Error al marcar notificación"}