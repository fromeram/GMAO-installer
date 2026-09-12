# backend/src/main.py - VERSIÓN DEFINITIVA BASADA EN ANÁLISIS DE LOGS

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import text
from src.database import SessionLocal
from src.auth import get_password_hash

# Routers de la aplicación
from src.routers import router
from src.routes_scheduler import router as scheduler_router
from .routes_gamification import router as gamification_router
from src.routes_ai import router as ai_router
from src.routes_ai_dashboard import router as dashboard_ai_router
from .routers.communication_routes import router as communication_router
from src.routes_ai import initialize_real_models, AI_STATE
from .routes_notifications import router as notifications_router
from .routes_plan_anual import router as plan_anual_router 
from .routes_legal import router as legal_router 

# ✅ USAR SOLO EL SCHEDULER DE scheduler.py, NO CREAR UNO NUEVO
from .scheduler import scheduler, schedule_tasks

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("app.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

app = FastAPI(title="GMAO API", version="0.1.0")

# --- Configuración de CORS ---
origins = [
    "http://localhost",
    "http://localhost:80",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:80",
    "http://127.0.0.1:3000",
]

cors_env = os.getenv("CORS_ORIGINS", "")
if cors_env:
    for orig in cors_env.split(","):
        if orig.strip() and orig.strip() not in origins:
            origins.append(orig.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://.*$",  # Permite despliegues locales, intranets y dominios personalizados
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ CONFIGURACIÓN CORREGIDA BASADA EN NGINX ANÁLISIS:
# Nginx elimina "/api/" de TODAS las rutas con "proxy_pass http://backend:8000/;"
# Algunos endpoints del frontend tienen /api/ duplicado, así que registramos ambas versiones

# 1. Routers de IA (SIN /api/ porque Nginx lo elimina)
app.include_router(dashboard_ai_router, prefix="/ai/dashboard", tags=["AI Dashboard"])
app.include_router(ai_router, prefix="/ai", tags=["AI"])

# 2. Otros routers - DOBLE REGISTRO para compatibilidad con frontend
# Versión sin /api/ (para URLs correctas)
app.include_router(legal_router, prefix="", tags=["Mantenimiento Legal"])
app.include_router(notifications_router, prefix="", tags=["notifications"])
app.include_router(scheduler_router, prefix="", tags=["Scheduler"])

# Versión con /api/ (para URLs duplicadas del frontend como /api/api/vacaciones/pending)
# Esto permite que ambos tipos de URL funcionen hasta que se corrija el frontend
app.include_router(legal_router, prefix="/api", tags=["Legal - Compat /api/api/*"])
app.include_router(notifications_router, prefix="/api", tags=["Notifications - Compat /api/api/*"])
app.include_router(scheduler_router, prefix="/api", tags=["Scheduler - Compat /api/api/*"])

# 3. Routers sin prefijo (funcionan igual)
app.include_router(plan_anual_router, tags=["Plan Anual"])  # SIN PREFIX (correcto)
app.include_router(gamification_router, tags=["Gamification"])
app.include_router(communication_router, tags=["Communications"])

# 4. ✅ Router principal SIN PREFIX (DEBE IR AL FINAL PARA NO INTERFERIR)
app.include_router(router)

# --- Endpoints Raíz / Health ---
@app.get("/")
def root():
    return {"message": "API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

# --- Función para ejecutar el ciclo de predicciones ---
def run_automatic_predictions():
    """Ejecuta un ciclo de predicciones automáticas de forma segura en un thread."""
    try:
        logger.info("🔮 Iniciando ciclo de predicciones automáticas programado...")
        from src.ai.prediction_scheduler import run_single_real_prediction_cycle
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_single_real_prediction_cycle)
            future.result(timeout=1800)  # Timeout de 30 minutos para el ciclo completo
            
        logger.info("✅ Ciclo de predicciones automáticas programado completado.")
        
    except Exception as e:
        logger.error(f"❌ Error en el ciclo de predicciones automáticas programado: {e}", exc_info=True)

def ensure_database_initialized():
    """
    Verifica que la base de datos esté lista, que los roles esenciales existan,
    y que el usuario administrador inicial esté creado según las variables de entorno.
    """
    try:
        admin_username = os.getenv("INITIAL_ADMIN_USERNAME", "admin")
        admin_password = os.getenv("INITIAL_ADMIN_PASSWORD", "admin")

        db = SessionLocal()
        try:
            # 1. Verificar si las tablas principales existen
            table_check = db.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users');"
            )).scalar()

            if not table_check:
                logger.warning("⚠️ La tabla 'users' aún no existe en la base de datos (esperando inicialización).")
                return

            # 2. Asegurar que los roles básicos existan
            roles = [
                (1, 'Administrador'),
                (2, 'Jefe de Mantenimiento'),
                (3, 'Jefe de Sección'),
                (4, 'Mecánico'),
                (6, 'Calidad'),
                (7, 'Contabilidad')
            ]
            for role_id, role_name in roles:
                db.execute(
                    text("INSERT INTO roles (id, nombre) VALUES (:id, :name) ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre;"),
                    {"id": role_id, "name": role_name}
                )
            db.commit()

            # 3. Verificar / Crear usuario administrador inicial
            user_exists = db.execute(
                text("SELECT id FROM users WHERE username = :username;"),
                {"username": admin_username}
            ).fetchone()

            if not user_exists:
                hashed_pw = get_password_hash(admin_password)
                db.execute(
                    text("""
                        INSERT INTO users (username, password, role_id, active, hourly_rate)
                        VALUES (:username, :password, 1, true, 0.0);
                    """),
                    {"username": admin_username, "password": hashed_pw}
                )
                db.commit()
                logger.info(f"✅ Usuario administrador inicial '{admin_username}' creado con éxito.")
            else:
                logger.info(f"ℹ️ Usuario administrador '{admin_username}' ya presente en la base de datos.")

        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Error durante la verificación de base de datos: {e}", exc_info=True)

# --- Eventos de Inicio/Parada de la Aplicación ---
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Iniciando aplicación...")

    # 0. Verificar e inicializar base de datos
    ensure_database_initialized()

    # 1. Lanza la inicialización de la IA como una tarea en segundo plano
    logger.info("🤖 Lanzando tarea de inicialización de IA en segundo plano...")
    asyncio.create_task(initialize_real_models())

    # 2. ✅ USAR EL SCHEDULER EXISTENTE DE scheduler.py EN LUGAR DE CREAR UNO NUEVO
    try:
        # Solo programar las tareas si el scheduler no está ya corriendo
        if not scheduler.running:
            logger.info("⚙️ Programando tareas del scheduler...")
            
            # Programar todas las tareas usando la función existente
            task_count = schedule_tasks()
            logger.info(f"✅ {task_count} tareas programadas correctamente")
            
            # Iniciar el scheduler
            scheduler.start()
            logger.info("✅ Scheduler principal iniciado correctamente.")
        else:
            logger.warning("⚠️ El Scheduler ya estaba en ejecución.")

    except Exception as e:
        logger.error(f"❌ Error al iniciar o configurar el scheduler: {e}", exc_info=True)

@app.on_event("shutdown")
def shutdown_event():
    logger.info("🛑 Apagando la aplicación...")
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("✅ Scheduler detenido correctamente.")
    except Exception as e:
        logger.error(f"❌ Error deteniendo el scheduler: {e}")

# --- Endpoints de Administración y Estado ---
@app.get("/api/system/status")
def system_status():
    """Estado completo del sistema incluyendo predicciones."""
    try:
        scheduler_jobs = []
        ai_prediction_job = None
        
        if scheduler.running:
            for job in scheduler.get_jobs():
                try:
                    # ✅ MANEJO SEGURO DE next_run_time
                    next_run = None
                    if hasattr(job, 'next_run_time'):
                        next_run = job.next_run_time
                    elif hasattr(job, '_next_run_time'):
                        next_run = job._next_run_time
                    
                    job_info = {
                        "id": job.id,
                        "name": getattr(job, 'name', job.id),
                        "next_run": next_run.isoformat() if next_run else None,
                        "trigger": str(job.trigger) if hasattr(job, 'trigger') else "No trigger"
                    }
                    scheduler_jobs.append(job_info)
                    
                    # Buscar job de predicciones AI (puede tener diferentes nombres)
                    if job.id in ['auto_ai_predictions', 'run_ai_predictions']:
                        ai_prediction_job = job_info
                        
                except Exception as e:
                    logger.warning(f"Error procesando job {getattr(job, 'id', 'unknown')}: {e}")
        
        ai_config = {}
        try:
            from src.routes_ai import AI_CONFIG_CACHE
            ai_config = {
                "model": AI_CONFIG_CACHE.get("default_prediction_model", "Not configured"),
                "threshold": AI_CONFIG_CACHE.get("prediction_confidence_threshold", 70),
                "enabled": AI_CONFIG_CACHE.get("auto_prediction_enabled", False),
                "frequency_minutes": AI_CONFIG_CACHE.get("prediction_frequency_minutes", 30)
            }
        except Exception:
            ai_config = {"error": "Could not load AI configuration"}
        
        return {
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "scheduler": {
                "running": scheduler.running,
                "jobs_count": len(scheduler_jobs),
                "jobs": scheduler_jobs
            },
            "ai_predictions": {
                "configured": ai_prediction_job is not None,
                "job_details": ai_prediction_job,
                "configuration": ai_config
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo el estado del sistema: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}

@app.post("/api/ai/predictions/force-cycle-now")
async def force_prediction_cycle():
    """Fuerza un ciclo de predicciones inmediatamente en segundo plano."""
    try:
        logger.info("🔄 Forzando ciclo manual de predicciones...")
        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, run_automatic_predictions)
        
        return {
            "status": "started",
            "message": "Ciclo de predicciones iniciado manualmente. Revisa los logs para ver el progreso.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error forzando ciclo: {e}")
        return {"status": "error", "error": str(e)}

# ✅ ENDPOINT DE DEBUG PARA VERIFICAR RUTAS REGISTRADAS
@app.get("/debug/routes")
def debug_routes():
    """Endpoint de debug para verificar todas las rutas registradas"""
    routes_info = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes_info.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": getattr(route, 'name', 'unnamed')
            })
    
    # Filtrar rutas de IA para verificar
    ai_routes = [r for r in routes_info if '/ai' in r['path']]
    
    return {
        "total_routes": len(routes_info),
        "ai_routes_count": len(ai_routes),
        "ai_routes": ai_routes,
        "analysis": {
            "nginx_config": "proxy_pass http://backend:8000/; elimina /api/ de TODAS las rutas",
            "expected_routes": [
                "/ai/configuration (sin /api/)",
                "/vacaciones/pending (sin /api/)",
                "/scheduler/* (sin /api/)",
                "/legal/* (sin /api/)"
            ],
            "nginx_rule": "location /api/ { proxy_pass http://backend:8000/; } elimina el prefijo"
        },
        "status": "debug_info"
    }

# ✅ LOGGING DE STARTUP PARA VERIFICAR CONFIGURACIÓN
@app.on_event("startup")
async def log_router_configuration():
    """Log de configuración de routers al startup"""
    logger.info("📋 Configuración DOBLE de routers (compatibilidad con frontend):")
    logger.info("   - IA: /ai/* (funcionan correctamente)")
    logger.info("   - Legal: / Y /api/ (compatibilidad con URLs duplicadas)")
    logger.info("   - Notifications: / Y /api/ (compatibilidad con URLs duplicadas)")
    logger.info("   - Scheduler: / Y /api/ (compatibilidad con URLs duplicadas)")
    logger.info("⚠️ NOTA: Frontend tiene algunas URLs con /api/ duplicado (/api/api/*)")
    logger.info("📊 Nginx: location /api/ { proxy_pass http://backend:8000/; } elimina /api/")