# src/routes_scheduler.py - VERSIÓN COMPLETA CORREGIDA - PARTE 1

# ================================================
# 1. Importaciones
# ================================================

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
import json
import os
import logging
from datetime import datetime, timedelta

from src.database import get_db
from src.auth import get_admin_user, get_current_user
from src.models.user import User
from .scheduler import scheduler, config, schedule_tasks

logger = logging.getLogger("scheduler_admin")

router = APIRouter()

# ================================================
# 2. Modelos Pydantic Flexibles
# ================================================

class SchedulerStatus(BaseModel):
    running: bool
    job_count: int
    next_run_times: Dict[str, Optional[str]]
    config: Dict[str, Any]

class SchedulerConfig(BaseModel):
    email: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tasks: Optional[Dict[str, Dict[str, Any]]] = Field(default_factory=dict)
    ai_predictions: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"

class SchedulerTaskRun(BaseModel):
    task_name: str
    
    class Config:
        extra = "ignore"

# ================================================
# 3. Funciones Auxiliares
# ================================================

def get_task_display_name(task_id):
    """✅ Mapeo seguro de nombres de tareas en español"""
    safe_task_id = str(task_id or '').lower()
    
    task_names = {
        'generate_daily_orders': 'Generar Órdenes Diarias',
        'generate_orders': 'Generar Órdenes Diarias',
        'check_upcoming_maintenance': 'Verificar Mantenimientos Próximos',
        'check_upcoming': 'Verificar Mantenimientos Próximos',
        'check_low_stock': 'Verificar Stock Bajo',
        'check_stock': 'Verificar Stock Bajo',
        'check_overdue_tasks': 'Verificar Órdenes Vencidas',
        'check_overdue': 'Verificar Órdenes Vencidas',
        'generate_weekly_metrics': 'Generar Métricas Semanales',
        'generate_metrics': 'Generar Métricas Semanales',
        'update_maintenance_backlog': 'Actualizar Backlog de Mantenimiento',
        'maintenance_backup': 'Actualizar Backlog de Mantenimiento',
        'run_ai_predictions': 'Predicciones de IA',
        'ai_predictions': 'Predicciones de IA',
        'cleanup_old_audit_logs': 'Limpiar Logs de Auditoría',
        'cleanup_audit_logs': 'Limpiar Auditoría'
    }
    
    if task_names.get(safe_task_id):
        return task_names[safe_task_id]
    
    try:
        return safe_task_id.replace('_', ' ').title()
    except:
        return 'Tarea Desconocida'

def execute_task_by_name(name: str):
    """✅ Ejecuta una tarea específica por nombre"""
    try:
        logger.info(f"🔄 Intentando ejecutar tarea: {name}")
        
        if name in ["generate_orders", "generate_daily_orders"]:
            from src.scheduler import generate_daily_orders
            logger.info("📋 Ejecutando generación de órdenes diarias...")
            return generate_daily_orders()
            
        elif name in ["check_upcoming", "check_upcoming_maintenance"]:
            from src.scheduler import check_upcoming_maintenance
            logger.info("🔍 Ejecutando verificación de mantenimientos próximos...")
            return check_upcoming_maintenance()
            
        elif name in ["check_stock", "check_low_stock"]:
            from src.scheduler import check_low_stock
            logger.info("📦 Ejecutando verificación de stock bajo...")
            return check_low_stock()
            
        elif name in ["check_overdue", "check_overdue_tasks"]:
            from src.scheduler import check_overdue_tasks
            logger.info("⏰ Ejecutando verificación de órdenes vencidas...")
            return check_overdue_tasks()
            
        elif name in ["generate_metrics", "generate_weekly_metrics"]:
            from src.scheduler import generate_weekly_metrics
            logger.info("📊 Ejecutando generación de métricas semanales...")
            return generate_weekly_metrics()
            
        elif name in ["maintenance_backup", "update_maintenance_backlog"]:
            from src.scheduler import update_maintenance_backlog
            logger.info("🔧 Ejecutando actualización de backlog de mantenimiento...")
            return update_maintenance_backlog()
            
        elif name in ["ai_predictions", "run_ai_predictions"]:
            try:
                from src.scheduler import run_ai_predictions
                logger.info("🤖 Ejecutando predicciones de IA...")
                result = run_ai_predictions()
                logger.info(f"✅ Predicciones de IA completadas: {result}")
                return result
            except ImportError as e:
                error_msg = f"❌ Error de importación en AI predictions: {e}"
                logger.error(error_msg)
                return {"status": "error", "message": error_msg}
            except Exception as e:
                error_msg = f"❌ Error ejecutando AI predictions: {e}"
                logger.error(error_msg, exc_info=True)
                return {"status": "error", "message": error_msg}
        
        elif name in ["cleanup_audit_logs", "cleanup_old_audit_logs"]:
            from src.scheduler import cleanup_old_audit_logs
            logger.info("🧹 Ejecutando limpieza de logs de auditoría...")
            return cleanup_old_audit_logs()
        
        else:
            available_tasks = [
                "generate_orders", "check_upcoming", "check_stock", 
                "check_overdue", "generate_metrics", "maintenance_backup", 
                "ai_predictions", "cleanup_audit_logs"
            ]
            error_msg = f"Tarea '{name}' no reconocida. Disponibles: {available_tasks}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"❌ Error ejecutando tarea {name}: {e}"
        logger.error(error_msg, exc_info=True)
        return {"status": "error", "message": error_msg}
# ================================================
# 4. Endpoints del Router - SEGUNDA PARTE
# ================================================

@router.get("/scheduler/status")
def get_scheduler_status(current_user: User = Depends(get_current_user)):
    """✅ Obtiene el estado actual del scheduler con configuración completa."""
    try:
        from src.scheduler import scheduler, config
        
        # Determinar si está corriendo
        running = scheduler.running if scheduler else False
        
        # Obtener trabajos programados
        jobs = scheduler.get_jobs() if scheduler else []
        job_count = len(jobs)
        
        # ✅ MANEJO SEGURO DE next_run_time
        next_run_times = {}
        for job in jobs:
            try:
                if hasattr(job, 'next_run_time'):
                    next_run = job.next_run_time
                elif hasattr(job, '_next_run_time'):
                    next_run = job._next_run_time
                else:
                    next_run = None
                    if hasattr(job, 'trigger') and hasattr(job.trigger, 'get_next_fire_time'):
                        try:
                            next_run = job.trigger.get_next_fire_time(None, datetime.now())
                        except:
                            pass
                
                next_run_times[job.id] = next_run.strftime("%Y-%m-%d %H:%M:%S") if next_run else "No programado"
            except Exception as e:
                logger.warning(f"Error obteniendo next_run_time para job {job.id}: {e}")
                next_run_times[job.id] = "Error al obtener"
        
        # ✅ TAREAS DISPONIBLES
        available_tasks = [
            {"id": "generate_orders", "name": "Generar Órdenes Diarias", "description": "Genera automáticamente órdenes de trabajo para mantenimientos preventivos"},
            {"id": "check_upcoming", "name": "Verificar Mantenimientos Próximos", "description": "Verifica mantenimientos que están próximos a vencer"},
            {"id": "check_stock", "name": "Verificar Stock Bajo", "description": "Verifica productos del inventario con stock bajo mínimo"},
            {"id": "check_overdue", "name": "Verificar Órdenes Vencidas", "description": "Verifica órdenes de trabajo que están vencidas"},
            {"id": "generate_metrics", "name": "Generar Métricas Semanales", "description": "Genera reportes y métricas semanales de rendimiento"},
            {"id": "maintenance_backup", "name": "Actualizar Backlog de Mantenimiento", "description": "Actualiza el backlog de mantenimientos pendientes"},
            {"id": "ai_predictions", "name": "Predicciones de IA", "description": "Ejecuta ciclos automáticos de predicciones de inteligencia artificial"},
            {"id": "cleanup_audit_logs", "name": "Limpiar Logs de Auditoría", "description": "Limpia logs de auditoría antiguos del sistema"}
        ]
        
        return {
            "running": running,
            "job_count": job_count,
            "next_run_times": next_run_times,
            "config": config if 'config' in locals() and config else {},
            "available_tasks": available_tasks,
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error al obtener estado del scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/scheduler/start")
def start_scheduler(current_user: User = Depends(get_admin_user)):
    """Inicia el scheduler si está detenido."""
    try:
        if scheduler.running:
            return {"message": "El scheduler ya está en ejecución."}
        
        scheduler.start()
        logger.info(f"✅ Scheduler iniciado por {current_user.username}")
        return {"message": "Scheduler iniciado correctamente."}
    except Exception as e:
        logger.error(f"Error al iniciar scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Error al iniciar scheduler: {str(e)}")

@router.post("/scheduler/stop")
def stop_scheduler(current_user: User = Depends(get_admin_user)):
    """Detiene el scheduler si está en ejecución."""
    try:
        if not scheduler.running:
            return {"message": "El scheduler ya está detenido."}
        
        scheduler.shutdown()
        logger.info(f"✅ Scheduler detenido por {current_user.username}")
        return {"message": "Scheduler detenido correctamente."}
    except Exception as e:
        logger.error(f"Error al detener scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Error al detener scheduler: {str(e)}")

@router.post("/scheduler/reload")
def reload_scheduler(current_user: User = Depends(get_admin_user)):
    """✅ Recarga la configuración y reprograma las tareas."""
    try:
        logger.info(f"🔄 Iniciando reload del scheduler por {current_user.username}")
        
        was_running = False
        try:
            was_running = scheduler.running
            if was_running:
                scheduler.shutdown()
                logger.info("Scheduler detenido para reload")
        except Exception as e:
            logger.warning(f"Error al detener scheduler durante reload: {e}")
        
        # Recargar configuración
        try:
            CONFIG_FILE = "scheduler_config.json"
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    loaded_config = json.load(f)
                    logger.info(f"✅ Configuración recargada desde {CONFIG_FILE}")
            else:
                logger.info("No existe archivo de configuración, usando configuración por defecto")
        except Exception as e:
            logger.error(f"Error al recargar configuración: {e}")
        
        # Reprogramar tareas
        try:
            scheduler.remove_all_jobs()
            logger.info("Trabajos anteriores eliminados")
            
            task_count = schedule_tasks()
            logger.info(f"✅ Tareas reprogramadas: {task_count}")
            
        except Exception as e:
            logger.error(f"Error reprogramando tareas: {e}")
        
        # Reiniciar si estaba corriendo
        if was_running:
            try:
                scheduler.start()
                logger.info("✅ Scheduler reiniciado después del reload")
            except Exception as e:
                logger.error(f"Error reiniciando scheduler: {e}")
        
        return {
            "message": "Scheduler recargado correctamente.",
            "running": scheduler.running,
            "job_count": len(scheduler.get_jobs()) if scheduler else 0,
            "reloaded_by": current_user.username
        }
    except Exception as e:
        logger.error(f"Error al recargar scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Error al recargar scheduler: {str(e)}")

@router.put("/scheduler/config")
def update_scheduler_config(config_data: Union[SchedulerConfig, Dict[str, Any]], current_user: User = Depends(get_admin_user)):
    """✅ Actualiza la configuración del scheduler Y RECARGA AUTOMÁTICAMENTE."""
    try:
        logger.info(f"📝 Actualizando configuración del scheduler por {current_user.username}")
        
        # Manejo flexible de datos
        if isinstance(config_data, SchedulerConfig):
            config_dict = config_data.dict()
        elif isinstance(config_data, dict):
            config_dict = config_data
        else:
            try:
                config_dict = config_data.dict()
            except AttributeError:
                config_dict = dict(config_data)
        
        # Validar y limpiar datos
        clean_config = {}
        
        # Procesar configuración de email
        if 'email' in config_dict and config_dict['email']:
            clean_config['email'] = {}
            email_config = config_dict['email']
            
            valid_email_fields = ['enabled', 'smtp_server', 'smtp_port', 'username', 'password', 'sender']
            for field in valid_email_fields:
                if field in email_config and email_config[field] is not None:
                    clean_config['email'][field] = email_config[field]
        
        # Procesar configuración de tareas
        if 'tasks' in config_dict and config_dict['tasks']:
            clean_config['tasks'] = {}
            tasks_config = config_dict['tasks']
            
            valid_task_fields = ['enabled', 'cron', 'description', 'advance_days']
            for task_name, task_config in tasks_config.items():
                if isinstance(task_config, dict):
                    clean_config['tasks'][task_name] = {}
                    for field in valid_task_fields:
                        if field in task_config and task_config[field] is not None:
                            clean_config['tasks'][task_name][field] = task_config[field]
        
        # ✅ PROCESAR CONFIGURACIÓN DE IA
        if 'ai_predictions' in config_dict and config_dict['ai_predictions']:
            clean_config['ai_predictions'] = config_dict['ai_predictions']
        
        logger.info(f"🧹 Configuración limpia para guardar: {clean_config}")
        
        # Guardar nueva configuración
        CONFIG_FILE = "scheduler_config.json"
        
        # ✅ IMPORTANTE: Cargar configuración existente y mezclar
        existing_config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                existing_config = json.load(f)
        
        # Actualizar recursivamente
        def update_dict(d, u):
            for k, v in u.items():
                if isinstance(v, dict) and k in d:
                    d[k] = update_dict(d.get(k, {}), v)
                else:
                    d[k] = v
            return d
        
        final_config = update_dict(existing_config, clean_config)
        
        # Guardar configuración actualizada
        with open(CONFIG_FILE, 'w') as f:
            json.dump(final_config, f, indent=4)
        
        logger.info("✅ Configuración guardada correctamente")
        
        # ✅ RECARGAR SCHEDULER AUTOMÁTICAMENTE
        reload_result = reload_scheduler(current_user)
        
        # ✅ ACTUALIZAR TAMBIÉN LA CONFIGURACIÓN EN MEMORIA DEL SCHEDULER
        from src.scheduler import config as scheduler_config, scheduler
        scheduler_config.update(final_config)
        
        return {
            "message": "Configuración actualizada y scheduler recargado correctamente",
            "reload_result": reload_result,
            "updated_by": current_user.username,
            "updated_at": datetime.utcnow().isoformat(),
            "config_applied": final_config
        }
        
    except Exception as e:
        logger.error(f"Error al actualizar configuración: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar configuración: {str(e)}")

@router.post("/scheduler/run-task")
def run_task_now(task_data: SchedulerTaskRun, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    """✅ Ejecuta una tarea programada inmediatamente."""
    try:
        task_name = task_data.task_name
        
        logger.info(f"🔄 Solicitud de ejecución manual: {task_name} por {current_user.username}")
        
        # Función de ejecución en segundo plano
        def background_task_execution():
            try:
                logger.info(f"🚀 Iniciando ejecución en segundo plano de: {task_name}")
                result = execute_task_by_name(task_name)
                logger.info(f"✅ Tarea {task_name} completada. Resultado: {result}")
                return result
            except Exception as e:
                error_msg = f"❌ Error en ejecución en segundo plano de {task_name}: {e}"
                logger.error(error_msg, exc_info=True)
                return {"status": "error", "message": str(e)}
            
        # Añadir tarea al background
        background_tasks.add_task(background_task_execution)
        
        return {
            "message": f"Tarea '{get_task_display_name(task_name)}' iniciada correctamente",
            "task_name": task_name,
            "executed_by": current_user.username,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando tarea {task_data.task_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/scheduler/logs", response_model=List[str])
def get_scheduler_logs(
    lines: int = 100,
    current_user: User = Depends(get_admin_user)
):
    """Obtiene las últimas líneas del log del scheduler."""
    try:
        log_file = "scheduler.log"
        
        if not os.path.exists(log_file):
            return ["No hay archivo de log disponible."]
        
        # Leer últimas líneas
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            return all_lines[-lines:] if len(all_lines) > lines else all_lines
            
    except Exception as e:
        logger.error(f"Error al obtener logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener logs: {str(e)}")

@router.get("/scheduler/debug")
def debug_scheduler(current_user: User = Depends(get_admin_user)):
    """✅ Debug del estado del scheduler."""
    try:
        from src.scheduler import scheduler, config
        
        debug_info = {
            "scheduler_exists": scheduler is not None,
            "scheduler_running": scheduler.running if scheduler else False,
            "scheduler_type": str(type(scheduler)) if scheduler else "None",
            "jobs_count": len(scheduler.get_jobs()) if scheduler else 0,
            "jobs_info": [],
            "config_file_exists": os.path.exists("scheduler_config.json")
        }
        
        if scheduler:
            for job in scheduler.get_jobs():
                job_info = {
                    "id": job.id,
                    "name": getattr(job, 'name', 'Sin nombre'),
                    "func": str(job.func) if hasattr(job, 'func') else 'Sin función',
                    "trigger": str(job.trigger) if hasattr(job, 'trigger') else 'Sin trigger',
                }
                
                try:
                    if hasattr(job, 'next_run_time'):
                        job_info["next_run_time"] = str(job.next_run_time)
                    elif hasattr(job, '_next_run_time'):
                        job_info["next_run_time"] = str(job._next_run_time)
                    else:
                        job_info["next_run_time"] = "No disponible"
                except Exception as e:
                    job_info["next_run_time"] = f"Error: {str(e)}"
                
                debug_info["jobs_info"].append(job_info)
        
        return debug_info
        
    except Exception as e:
        logger.error(f"Error en debug del scheduler: {e}")
        return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}

@router.get("/scheduler/health-check")
def scheduler_health_check():
    """✅ Endpoint de health check para monitoring."""
    try:
        health_status = {
            "status": "healthy" if scheduler and scheduler.running else "unhealthy",
            "scheduler_running": scheduler.running if scheduler else False,
            "jobs_count": len(scheduler.get_jobs()) if scheduler else 0,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "scheduler_exists": scheduler is not None,
                "has_jobs": len(scheduler.get_jobs()) > 0 if scheduler else False,
                "config_file_exists": os.path.exists("scheduler_config.json")
            }
        }
        
        return health_status
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/scheduler/metrics")
def get_scheduler_metrics():
    """✅ Endpoint de métricas básicas."""
    try:
        metrics = []
        
        metrics.append(f"scheduler_running {1 if scheduler and scheduler.running else 0}")
        metrics.append(f"scheduler_jobs_total {len(scheduler.get_jobs()) if scheduler else 0}")
        
        config_exists = 1 if os.path.exists("scheduler_config.json") else 0
        metrics.append(f"scheduler_config_file_exists {config_exists}")
        
        if config_exists:
            config_size = os.path.getsize("scheduler_config.json")
            metrics.append(f"scheduler_config_file_size_bytes {config_size}")
        
        metrics_text = "\n".join(metrics)
        
        return Response(
            content=metrics_text,
            media_type="text/plain"
        )
        
    except Exception as e:
        return Response(
            content=f"# Error generating metrics: {str(e)}",
            media_type="text/plain",
            status_code=500
        )
    