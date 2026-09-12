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

AUTO_CLEANUP_CONFIG = AutoCleanupConfig()


# --- Section lines 9210-10142 ---
# --- ENDPOINTS DE AUDIT TRAIL ---
@router.get("/audit-trail/storage-stats")
def get_audit_storage_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Obtiene estadísticas de almacenamiento del audit trail.
    """
    try:
        # Estadísticas generales
        total_records = db.query(func.count(AuditLog.id)).scalar()
        
        # Registros por antigüedad
        now = datetime.utcnow()
        last_30_days = now - timedelta(days=30)
        last_90_days = now - timedelta(days=90)
        last_365_days = now - timedelta(days=365)
        
        records_last_30 = db.query(func.count(AuditLog.id)).filter(
            AuditLog.timestamp >= last_30_days
        ).scalar()
        
        records_last_90 = db.query(func.count(AuditLog.id)).filter(
            AuditLog.timestamp >= last_90_days,
            AuditLog.timestamp < last_30_days
        ).scalar()
        
        records_last_365 = db.query(func.count(AuditLog.id)).filter(
            AuditLog.timestamp >= last_365_days,
            AuditLog.timestamp < last_90_days
        ).scalar()
        
        records_older_365 = db.query(func.count(AuditLog.id)).filter(
            AuditLog.timestamp < last_365_days
        ).scalar()
        
        # Estadísticas por acción
        stats_by_action = db.query(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.action).order_by(func.count(AuditLog.id).desc()).all()
        
        # Estadísticas por módulo
        stats_by_module = db.query(
            AuditLog.module,
            func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.module).order_by(func.count(AuditLog.id).desc()).all()
        
        return {
            "total_records": total_records,
            "age_distribution": {
                "last_30_days": records_last_30,
                "30_to_90_days": records_last_90,
                "90_to_365_days": records_last_365,
                "older_than_365_days": records_older_365
            },
            "by_action": [
                {"action": row.action, "count": row.count} 
                for row in stats_by_action
            ],
            "by_module": [
                {"module": row.module or "unknown", "count": row.count} 
                for row in stats_by_module
            ],
            "recommendations": {
                "can_clean_login_logs": records_last_90 > 1000,
                "can_clean_old_records": records_older_365 > 500,
                "suggested_cleanup": "Considera eliminar LOGIN logs más antiguos que 90 días" if records_last_90 > 1000 else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error en get_audit_storage_stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")



@router.get("/audit-trail/stats")
def get_audit_stats(
    days: int = Query(7, ge=1, le=365, description="Número de días para las estadísticas"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ← Cambiar get_admin_user por get_current_user
):
    """
    Obtiene estadísticas del audit trail para el dashboard.
    """
    try:
        # Verificar permisos básicos (cualquier usuario logueado puede ver stats básicas)
        is_admin = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
        
        # Calcular fecha de inicio
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query base para el período
        base_query = db.query(AuditLog).filter(
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        )
        
        # Si no es admin, filtrar solo sus acciones
        if not is_admin:
            base_query = base_query.filter(AuditLog.user_id == current_user.id)
        
        # Estadísticas por acción
        actions_stats = db.query(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.timestamp >= start_date
        )
        
        if not is_admin:
            actions_stats = actions_stats.filter(AuditLog.user_id == current_user.id)
        
        actions_stats = actions_stats.group_by(AuditLog.action).all()
        
        # Estadísticas por módulo
        modules_stats = db.query(
            AuditLog.module,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.timestamp >= start_date
        )
        
        if not is_admin:
            modules_stats = modules_stats.filter(AuditLog.user_id == current_user.id)
        
        modules_stats = modules_stats.group_by(AuditLog.module).all()
        
        # Actividad por día
        daily_activity = db.query(
            func.date(AuditLog.timestamp).label('date'),
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.timestamp >= start_date
        )
        
        if not is_admin:
            daily_activity = daily_activity.filter(AuditLog.user_id == current_user.id)
        
        daily_activity = daily_activity.group_by(func.date(AuditLog.timestamp)).order_by('date').all()
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "total_actions": base_query.count(),
            "actions_by_type": [{"action": row.action, "count": row.count} for row in actions_stats],
            "actions_by_module": [{"module": row.module or "unknown", "count": row.count} for row in modules_stats],
            "daily_activity": [
                {
                    "date": row.date.isoformat(),
                    "count": row.count
                } for row in daily_activity
            ]
        }
    
    except Exception as e:
        logger.error(f"Error en get_audit_stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/audit-trail/recent-activity")
def get_recent_activity(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene actividad reciente para mostrar en el dashboard.
    """
    try:
        # Los usuarios normales solo ven actividad relevante para ellos
        is_admin = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
        
        query = db.query(AuditLog)
        
        if not is_admin:
            # Para usuarios normales, mostrar solo sus propias acciones
            query = query.filter(
                db.or_(
                    AuditLog.user_id == current_user.id,
                    db.and_(
                        AuditLog.entity_type == 'WorkOrder',
                        AuditLog.metadata.contains({'assigned_to_id': current_user.id})  # ← CAMBIAR extra_data por metadata
                    )
                )
            )
        
        recent_activities = query.filter(
            AuditLog.severity.in_(['MEDIUM', 'HIGH', 'CRITICAL'])  # Solo actividades importantes
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        return [
            {
                "id": activity.id,
                "summary": activity.changes_summary or f"{activity.action} {activity.entity_type}",
                "timestamp": activity.timestamp.isoformat(),
                "severity": activity.severity,
                "user_name": activity.user_name,
                "module": activity.module or "unknown"
            } for activity in recent_activities
        ]
    
    except Exception as e:
        logger.error(f"Error en get_recent_activity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
@router.get("/audit-trail/login-activity")
def get_login_activity(
    days: int = Query(7, ge=1, le=90, description="Días de historial"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene actividad de login reciente.
    Solo administradores pueden ver todos los logins.
    """
    try:
        is_admin = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = db.query(AuditLog).filter(
            AuditLog.action.in_(["LOGIN", "LOGIN_FAILED"]),
            AuditLog.timestamp >= start_date
        )
        
        # Si no es admin, solo mostrar sus propios logins
        if not is_admin:
            query = query.filter(AuditLog.user_id == current_user.id)
        
        login_activities = query.order_by(AuditLog.timestamp.desc()).limit(100).all()
        
        return [
            {
                "id": activity.id,
                "user_name": activity.user_name,
                "action": activity.action,
                "success": activity.action == "LOGIN",
                "timestamp": activity.timestamp.isoformat(),
                "ip_address": activity.ip_address,
                "user_agent": activity.user_agent
            } for activity in login_activities
        ]
        
    except Exception as e:
        logger.error(f"Error en get_login_activity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/audit-trail/entity/{entity_type}/{entity_id}", response_model=List[AuditLogResponse])
def get_entity_audit_history(
    entity_type: str,
    entity_id: int,
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el historial completo de una entidad específica.
    Ej: /audit-trail/entity/WorkOrder/123 - Historial de la orden 123
    """
    
    # Validar que el entity_type es válido
    valid_entities = [
        'WorkOrder', 'Machine', 'User', 'Inventory', 'Maintenance', 
        'Supplier', 'FailureCode', 'CauseCode', 'RemedyCode', 'MaintenanceBacklog'
    ]
    
    if entity_type not in valid_entities:
        raise HTTPException(status_code=400, detail=f"Tipo de entidad no válido. Debe ser uno de: {', '.join(valid_entities)}")
    
    # Obtener historial
    history = db.query(AuditLog).filter(
        AuditLog.entity_type == entity_type,
        AuditLog.entity_id == entity_id
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    return history

@router.get("/audit-trail/{audit_id}", response_model=AuditLogDetailResponse)
def get_audit_detail(
    audit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene detalles completos de un registro de audit específico.
    """
    try:
        audit_log = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
        
        if not audit_log:
            raise HTTPException(status_code=404, detail="Registro de audit no encontrado")
        
        # Verificar permisos
        is_admin = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
        
        if not is_admin and audit_log.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permiso para ver este registro")
        
        # Crear respuesta manual para evitar problemas de serialización
        response = {
            "id": audit_log.id,
            "action": audit_log.action,
            "entity_type": audit_log.entity_type,
            "entity_id": audit_log.entity_id,
            "user_name": audit_log.user_name,
            "user_role": audit_log.user_role,
            "timestamp": audit_log.timestamp,
            "ip_address": audit_log.ip_address,
            "changes_summary": audit_log.changes_summary,
            "module": audit_log.module,
            "severity": audit_log.severity,
            "notes": audit_log.notes,
            "old_values": audit_log.old_values,
            "new_values": audit_log.new_values,
            "user_agent": audit_log.user_agent,
            "session_id": audit_log.session_id,
            "metadata": None  # Por ahora None hasta que arreglemos la columna
        }
        
        return response
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error en get_audit_detail para ID {audit_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")





@router.post("/test-create-audit")
def test_create_audit(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crear una entrada de prueba en audit_logs"""
    try:
        test_audit = AuditLog(
            action="TEST",
            entity_type="TestEntity",
            entity_id=999,
            user_id=current_user.id,
            user_name=current_user.username,
            user_role=current_user.role.nombre if current_user.role else "Unknown",
            changes_summary="Prueba del sistema de audit trail",
            module="test",
            severity="LOW",
            notes="Entrada de prueba creada manualmente",
            metadata={"test_timestamp": datetime.utcnow().isoformat()}  # ← CAMBIAR extra_data por metadata
        )
        
        db.add(test_audit)
        db.commit()
        db.refresh(test_audit)
        
        return {
            "success": True,
            "audit_id": test_audit.id,
            "message": "Entrada de prueba creada correctamente"
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/audit-trail-simple")
def get_audit_trail_simple(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Versión simplificada del endpoint audit-trail"""
    try:
        # Solo obtener los últimos 10 registros
        logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
        
        result = []
        for log in logs:
            result.append({
                "id": log.id,
                "action": log.action,
                "entity_type": log.entity_type,
                "user_name": log.user_name,
                "timestamp": log.timestamp.isoformat(),
                "summary": log.changes_summary or f"{log.action} {log.entity_type}"
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")







# ENDPOINT MEJORADO PARA DEBUG
# ===============================
# AÑADIR este endpoint temporal para debug

@router.get("/debug-audit-logs")
def debug_audit_logs(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint temporal para debug de audit logs"""
    try:
        logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        result = []
        for log in logs:
            try:
                log_data = {
                    "id": log.id,
                    "action": log.action,
                    "entity_type": log.entity_type,
                    "entity_id": log.entity_id,
                    "user_name": log.user_name,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "changes_summary": log.changes_summary,
                    "module": log.module,
                    "severity": log.severity,
                    "ip_address": log.ip_address,
                    "notes": log.notes
                }
                result.append(log_data)
            except Exception as e:
                logger.error(f"Error procesando log {log.id}: {e}")
                result.append({
                    "id": log.id,
                    "error": f"Error procesando: {str(e)}"
                })
        
        return {
            "success": True,
            "count": len(result),
            "logs": result
        }
        
    except Exception as e:
        logger.error(f"Error en debug_audit_logs: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

# ==============================================================================
# SISTEMA DE LIMPIEZA PARA AUDIT TRAIL
# ==============================================================================

#  ENDPOINT PARA ELIMINAR LOGS ANTIGUOS
# ========================================



@router.delete("/audit-trail/cleanup")
def cleanup_audit_logs(
    days: int = Query(365, ge=1, le=3650, description="Eliminar logs más antiguos que X días"),  # ← CAMBIO: ge=1 en lugar de ge=30
    dry_run: bool = Query(True, description="Modo prueba - no elimina realmente"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Elimina registros de audit trail más antiguos que X días.
    Ahora permite desde 1 día en adelante para mayor flexibilidad.
    """
    try:
        # Calcular fecha límite
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Contar registros que se eliminarían
        count_query = db.query(AuditLog).filter(
            AuditLog.timestamp < cutoff_date
        )
        
        total_to_delete = count_query.count()
        
        if total_to_delete == 0:
            return {
                "success": True,
                "message": f"No hay registros más antiguos que {days} días",
                "deleted_count": 0,
                "dry_run": dry_run
            }
        
        # Mostrar estadísticas por módulo
        stats_by_module = db.query(
            AuditLog.module,
            func.count(AuditLog.id).label('count')
        ).filter(
            AuditLog.timestamp < cutoff_date
        ).group_by(AuditLog.module).all()
        
        module_stats = {row.module or "unknown": row.count for row in stats_by_module}
        
        if not dry_run:
            # Eliminar realmente
            deleted_count = count_query.delete(synchronize_session=False)
            db.commit()
            
            # Registrar la limpieza en audit trail
            audit_manager.log_action(
                db=db,
                action="DELETE",
                entity=AuditLog(),
                user=current_user,
                request=None,
                notes=f"Limpieza de audit trail: eliminados {deleted_count} registros más antiguos que {days} días",
                metadata={"days": days, "deleted_count": deleted_count}
            )
            db.commit()
            
            return {
                "success": True,
                "message": f"Eliminados {deleted_count} registros más antiguos que {days} días",
                "deleted_count": deleted_count,
                "module_stats": module_stats,
                "dry_run": False
            }
        else:
            return {
                "success": True,
                "message": f"[MODO PRUEBA] Se eliminarían {total_to_delete} registros más antiguos que {days} días",
                "would_delete_count": total_to_delete,
                "module_stats": module_stats,
                "dry_run": True,
                "note": "Usa dry_run=false para eliminar realmente"
            }
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error en cleanup_audit_logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.delete("/audit-trail/cleanup-by-action")
def cleanup_audit_logs_by_action(
    actions: str = Query(..., description="Acciones separadas por coma"),
    days: int = Query(90, ge=1, description="Eliminar acciones más antiguas que X días"),  # ← CAMBIO: ge=1 en lugar de ge=7
    dry_run: bool = Query(True, description="Modo prueba"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Elimina tipos específicos de acciones del audit trail.
    Ahora permite desde 1 día en adelante.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Convertir string de acciones a lista
        actions_list = [action.strip() for action in actions.split(',')]
        
        # Validar acciones
        valid_actions = ["LOGIN", "LOGIN_FAILED", "CREATE", "UPDATE", "DELETE", "COMPLETE", "STATUS_CHANGE", "EXPORT"]
        invalid_actions = [action for action in actions_list if action not in valid_actions]
        
        if invalid_actions:
            raise HTTPException(
                status_code=400, 
                detail=f"Acciones inválidas: {invalid_actions}. Válidas: {valid_actions}"
            )
        
        # Contar registros
        count_query = db.query(AuditLog).filter(
            AuditLog.action.in_(actions_list),
            AuditLog.timestamp < cutoff_date
        )
        
        total_to_delete = count_query.count()
        
        if total_to_delete == 0:
            return {
                "success": True,
                "message": f"No hay registros de acciones {actions_list} más antiguos que {days} días",
                "deleted_count": 0
            }
        
        if not dry_run:
            deleted_count = count_query.delete(synchronize_session=False)
            db.commit()
            
            # Registrar la limpieza
            audit_manager.log_action(
                db=db,
                action="DELETE",
                entity=AuditLog(),
                user=current_user,
                request=None,
                notes=f"Limpieza selectiva: eliminados {deleted_count} registros de acciones {actions_list}",
                metadata={"actions": actions_list, "days": days, "deleted_count": deleted_count}
            )
            db.commit()
            
            return {
                "success": True,
                "message": f"Eliminados {deleted_count} registros de acciones {actions_list}",
                "deleted_count": deleted_count,
                "actions": actions_list,
                "days": days
            }
        else:
            return {
                "success": True,
                "message": f"[MODO PRUEBA] Se eliminarían {total_to_delete} registros de acciones {actions_list}",
                "would_delete_count": total_to_delete,
                "actions": actions_list,
                "dry_run": True
            }
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error en cleanup_audit_logs_by_action: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/audit-trail/auto-cleanup/config")
def get_auto_cleanup_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Obtiene la configuración actual de limpieza automática."""
    try:
        return {
            "success": True,
            "config": AUTO_CLEANUP_CONFIG.dict()
        }
    except Exception as e:
        logger.error(f"Error obteniendo configuración de auto-cleanup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/audit-trail/auto-cleanup/config")
def save_auto_cleanup_config(
    config: AutoCleanupConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Guarda la configuración de limpieza automática."""
    try:
        global AUTO_CLEANUP_CONFIG
        AUTO_CLEANUP_CONFIG = config
        
        # Aquí podrías guardar en base de datos para persistencia
        # audit_config = AuditConfig(user_id=current_user.id, config=config.dict())
        # db.add(audit_config)
        # db.commit()
        
        # Registrar el cambio de configuración
        audit_manager.log_action(
            db=db,
            action="UPDATE",
            entity=AuditLog(),  # Entidad dummy
            user=current_user,
            request=None,
            notes=f"Configuración de limpieza automática actualizada: {config.frequency}",
            metadata=config.dict()
        )
        db.commit()
        
        return {
            "success": True,
            "message": "Configuración guardada correctamente"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error guardando configuración de auto-cleanup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/audit-trail/auto-cleanup/run")
def run_manual_cleanup(
    config: AutoCleanupConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Ejecuta la limpieza manualmente con la configuración proporcionada."""
    try:
        total_deleted = 0
        operations = []
        
        # Limpieza de logs de LOGIN
        if config.loginLogsEnabled:
            cutoff_date = datetime.utcnow() - timedelta(days=config.loginLogsDays)
            
            login_deleted = db.query(AuditLog).filter(
                AuditLog.action.in_(['LOGIN', 'LOGIN_FAILED']),
                AuditLog.timestamp < cutoff_date
            ).delete(synchronize_session=False)
            
            if login_deleted > 0:
                total_deleted += login_deleted
                operations.append(f"LOGIN logs > {config.loginLogsDays} días: {login_deleted}")
        
        # Limpieza general de logs
        if config.generalLogsEnabled:
            cutoff_date = datetime.utcnow() - timedelta(days=config.generalLogsDays)
            
            # Excluir los LOGIN logs si ya se limpiaron
            query = db.query(AuditLog).filter(AuditLog.timestamp < cutoff_date)
            if config.loginLogsEnabled:
                query = query.filter(~AuditLog.action.in_(['LOGIN', 'LOGIN_FAILED']))
            
            general_deleted = query.delete(synchronize_session=False)
            
            if general_deleted > 0:
                total_deleted += general_deleted
                operations.append(f"Logs generales > {config.generalLogsDays} días: {general_deleted}")
        
        if total_deleted > 0:
            db.commit()
            
            # Registrar la limpieza manual
            audit_manager.log_action(
                db=db,
                action="UPDATE" if existing_progress else "CREATE",
                entity=checklist_progress,
                user=current_user,
                request=request,
                notes=f"Progreso de checklist {'actualizado' if existing_progress else 'creado'} para orden {work_order.order_number}",
                metadata={  # ← CORRECCIÓN: cambiar a 'metadata'
                    "progress_percent": checklist_progress.progress_percent,
                    "is_completed": checklist_progress.is_completed,
                    "total_elapsed_time": checklist_progress.total_elapsed_time
                }
            )
            db.commit()
            
            return {
                "success": True,
                "message": f"Eliminados {total_deleted} registros",
                "details": operations,
                "total_deleted": total_deleted
            }
        else:
            return {
                "success": True,
                "message": "No hay registros para eliminar con la configuración actual",
                "total_deleted": 0
            }
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error en limpieza manual: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
def execute_auto_cleanup():
    """Ejecuta la limpieza automática según la configuración guardada."""
    if not AUTO_CLEANUP_CONFIG.enabled:
        return
    
    db = SessionLocal()
    try:
        total_deleted = 0
        operations = []
        
        # Limpieza de logs de LOGIN
        if AUTO_CLEANUP_CONFIG.loginLogsEnabled:
            cutoff_date = datetime.utcnow() - timedelta(days=AUTO_CLEANUP_CONFIG.loginLogsDays)
            
            login_deleted = db.query(AuditLog).filter(
                AuditLog.action.in_(['LOGIN', 'LOGIN_FAILED']),
                AuditLog.timestamp < cutoff_date
            ).delete(synchronize_session=False)
            
            if login_deleted > 0:
                total_deleted += login_deleted
                operations.append(f"LOGIN logs > {AUTO_CLEANUP_CONFIG.loginLogsDays} días: {login_deleted}")
        
        # Limpieza general de logs
        if AUTO_CLEANUP_CONFIG.generalLogsEnabled:
            cutoff_date = datetime.utcnow() - timedelta(days=AUTO_CLEANUP_CONFIG.generalLogsDays)
            
            query = db.query(AuditLog).filter(AuditLog.timestamp < cutoff_date)
            if AUTO_CLEANUP_CONFIG.loginLogsEnabled:
                query = query.filter(~AuditLog.action.in_(['LOGIN', 'LOGIN_FAILED']))
            
            general_deleted = query.delete(synchronize_session=False)
            
            if general_deleted > 0:
                total_deleted += general_deleted
                operations.append(f"Logs generales > {AUTO_CLEANUP_CONFIG.generalLogsDays} días: {general_deleted}")
        
        if total_deleted > 0:
            db.commit()
            logger.info(f"Limpieza automática ejecutada: {total_deleted} registros eliminados - {operations}")
        else:
            logger.info("Limpieza automática: no hay registros para eliminar")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error en limpieza automática: {e}")
    finally:
        db.close()

@router.get("/audit-trail")
def get_audit_trail_fixed(
    limit: int = Query(50, le=500, description="Número máximo de registros"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir"),
    entity_type: Optional[str] = Query(None, description="Filtrar por tipo de entidad"),
    action: Optional[str] = Query(None, description="Filtrar por tipo de acción"),
    module: Optional[str] = Query(None, description="Filtrar por módulo"),
    severity: Optional[str] = Query(None, description="Filtrar por severidad"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el historial de audit trail con filtros opcionales.
    Versión simplificada para evitar errores de serialización.
    """
    try:
        # Verificar permisos
        is_admin = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
        
        # Construir query base
        query = db.query(AuditLog)
        
        # Filtrar por usuario si no es admin
        if not is_admin:
            query = query.filter(AuditLog.user_id == current_user.id)
        
        # Aplicar filtros opcionales
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if module:
            query = query.filter(AuditLog.module == module)
        
        if severity:
            query = query.filter(AuditLog.severity == severity)
        
        # Ordenar por timestamp descendente (más recientes primero)
        query = query.order_by(AuditLog.timestamp.desc())
        
        # Aplicar paginación
        results = query.offset(offset).limit(limit).all()
        
        # Construir respuesta manual para evitar errores de serialización
        formatted_results = []
        for audit_log in results:
            try:
                formatted_log = {
                    "id": audit_log.id,
                    "action": audit_log.action,
                    "entity_type": audit_log.entity_type,
                    "entity_id": audit_log.entity_id,
                    "user_name": audit_log.user_name,
                    "user_role": audit_log.user_role,
                    "timestamp": audit_log.timestamp,
                    "ip_address": audit_log.ip_address,
                    "changes_summary": audit_log.changes_summary,
                    "module": audit_log.module,
                    "severity": audit_log.severity,
                    "notes": audit_log.notes
                }
                formatted_results.append(formatted_log)
            except Exception as e:
                logger.error(f"Error formateando audit log {audit_log.id}: {e}")
                # Incluir un registro de error en lugar de fallar completamente
                formatted_results.append({
                    "id": audit_log.id,
                    "error": f"Error al formatear: {str(e)}"
                })
        
        return formatted_results
    
    except Exception as e:
        logger.error(f"Error en get_audit_trail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# === ENDPOINT PARA NOTIFICACIONES DE GAMIFICACIÓN ===

@router.get("/notifications/gamification")
def get_gamification_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene notificaciones pendientes de gamificación"""
    try:
        from src.models.gamification import UserAchievement
        
        # Logros no notificados
        unnotified_achievements = db.query(UserAchievement).options(
            joinedload(UserAchievement.achievement)
        ).filter(
            UserAchievement.user_id == current_user.id,
            UserAchievement.notified == False
        ).all()
        
        # Marcar como notificados
        for ua in unnotified_achievements:
            ua.notified = True
        
        if unnotified_achievements:
            db.commit()
        
        return {
            "new_achievements": [
                {
                    "id": ua.achievement.id,
                    "name": ua.achievement.name,
                    "description": ua.achievement.description,
                    "icon": ua.achievement.icon,
                    "points": ua.achievement.points,
                    "rarity": ua.achievement.rarity.value
                }
                for ua in unnotified_achievements
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting gamification notifications: {e}")
        return {"new_achievements": []}
    
# Añadir estos endpoints al archivo routes.py existente

# =============================================================================
