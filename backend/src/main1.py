# backend/src/main.py - VERSIÓN CORREGIDA
from fastapi import FastAPI
from .scheduler import scheduler
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
from src.routes import router
from src.routes_scheduler import router as scheduler_router
from .routes_gamification import router as gamification_router
from src.routes_ai import router as ai_router
from src.routes_ai_dashboard import router as dashboard_ai_router
from .routers.communication_routes import router as communication_router

# ✅ IMPORTACIONES CORREGIDAS PARA PREDICCIONES
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

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
    "http://192.168.1.15",
    "http://192.168.1.15:80",
    "http://localhost:3000",
    "https://fromeram.no-ip.org"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Incluir los routers ---
app.include_router(router)
app.include_router(scheduler_router, prefix="/api")
app.include_router(gamification_router)
app.include_router(ai_router, prefix="/api/ai", tags=["AI"])
app.include_router(dashboard_ai_router, prefix="/api/ai/dashboard", tags=["AI Dashboard"])
app.include_router(communication_router, tags=["Communications"])

# --- Endpoints Raíz / Health ---
@app.get("/")
def root():
    return {"message": "API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

# ✅ FUNCIÓN CORREGIDA PARA EJECUTAR PREDICCIONES
def run_automatic_predictions():
    """Ejecuta ciclo de predicciones automáticas de forma segura"""
    try:
        logger.info("🔮 Iniciando ciclo de predicciones automáticas...")
        
        # ✅ IMPORTACIÓN CORREGIDA
        from src.ai.prediction_scheduler import run_single_real_prediction_cycle
        
        # Ejecutar en un thread separado para no bloquear
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_single_real_prediction_cycle)
            result = future.result(timeout=600)  # Timeout de 10 minutos
            
        logger.info("✅ Ciclo de predicciones automáticas completado")
        
    except Exception as e:
        logger.error(f"❌ Error en predicciones automáticas: {e}", exc_info=True)

# ✅ FUNCIÓN ASÍNCRONA PARA INICIALIZAR PREDICCIONES
async def initialize_ai_predictions():
    """Inicializa el sistema de predicciones después del startup"""
    try:
        # Esperar 60 segundos para que todo esté inicializado
        await asyncio.sleep(60)
        
        logger.info("🤖 Inicializando sistema de predicciones automáticas...")
        
        # Verificar configuración
        try:
            from src.routes_ai import AI_CONFIG_CACHE, initialize_real_models
            
            # Asegurar que los modelos estén inicializados
            await initialize_real_models()
            
            model_configured = AI_CONFIG_CACHE.get("default_prediction_model")
            auto_enabled = AI_CONFIG_CACHE.get("auto_prediction_enabled", True)
            
            logger.info(f"📊 Configuración actual:")
            logger.info(f"   - Modelo: {model_configured}")
            logger.info(f"   - Auto habilitado: {auto_enabled}")
            
            if not model_configured:
                logger.error("❌ No hay modelo configurado para predicciones")
                return
                
            if not auto_enabled:
                logger.warning("⚠️ Predicciones automáticas deshabilitadas")
                return
                
        except Exception as config_error:
            logger.error(f"❌ Error obteniendo configuración: {config_error}")
            # Usar valores por defecto
            model_configured = "deepseek-r1:8b"
        
        # Ejecutar primera predicción después de la inicialización
        logger.info("🚀 Ejecutando primera predicción en 2 minutos...")
        await asyncio.sleep(120)  # Esperar 2 minutos más
        
        # Ejecutar primera predicción
        run_automatic_predictions()
        
    except Exception as e:
        logger.error(f"❌ Error inicializando predicciones: {e}", exc_info=True)

# --- Eventos de inicio/parada ---
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting up application...")
    
    # Iniciar scheduler principal
    try:
        if not scheduler.running:
            scheduler.start()
            logger.info("✅ Scheduler started successfully")
            
            # ✅ CONFIGURAR JOB DE PREDICCIONES AUTOMÁTICAS
            try:
                # Obtener intervalo de configuración
                hours_interval = 3  # Por defecto 3 horas
                
                try:
                    from src.routes_ai import AI_CONFIG_CACHE
                    hours_interval = AI_CONFIG_CACHE.get("prediction_frequency_hours", 3)
                except:
                    logger.warning("⚠️ No se pudo cargar configuración, usando 3 horas por defecto")
                
                logger.info(f"🤖 Configurando predicciones automáticas cada {hours_interval} horas")
                
                # Añadir job recurrente
                scheduler.add_job(
                    func=run_automatic_predictions,
                    trigger=IntervalTrigger(hours=hours_interval),
                    id='auto_ai_predictions',
                    name='Predicciones IA Automáticas',
                    replace_existing=True,
                    max_instances=1,  # Solo una instancia a la vez
                    coalesce=True     # Si se pierde una ejecución, no ejecutar múltiples
                )
                
                logger.info("✅ Job de predicciones automáticas configurado")
                
            except Exception as pred_error:
                logger.error(f"❌ Error configurando job de predicciones: {pred_error}", exc_info=True)
                
        else:
            logger.warning("⚠️ Scheduler is already running")
            
    except Exception as e:
        logger.error(f"❌ Error starting scheduler: {e}", exc_info=True)
    
    # ✅ INICIALIZAR PREDICCIONES EN BACKGROUND
    asyncio.create_task(initialize_ai_predictions())
    logger.info("📋 Tarea de inicialización de predicciones programada")

@app.on_event("shutdown")
def shutdown_event():
    logger.info("🛑 Shutting down application...")
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("✅ Scheduler shutdown successfully")
    except Exception as e:
        logger.error(f"❌ Error shutting down scheduler: {e}")

# ✅ ENDPOINT MEJORADO: Estado del sistema
@app.get("/api/system/status")
def system_status():
    """Estado completo del sistema incluyendo predicciones"""
    try:
        # Información del scheduler
        scheduler_jobs = []
        ai_prediction_job = None
        
        if scheduler.running:
            for job in scheduler.get_jobs():
                job_info = {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                }
                scheduler_jobs.append(job_info)
                
                if job.id == 'auto_ai_predictions':
                    ai_prediction_job = job_info
        
        # Obtener configuración de IA
        ai_config = {}
        try:
            from src.routes_ai import AI_CONFIG_CACHE
            ai_config = {
                "model": AI_CONFIG_CACHE.get("default_prediction_model", "Not configured"),
                "threshold": AI_CONFIG_CACHE.get("prediction_confidence_threshold", 70),
                "enabled": AI_CONFIG_CACHE.get("auto_prediction_enabled", False),
                "frequency_hours": AI_CONFIG_CACHE.get("prediction_frequency_hours", 3)
            }
        except:
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
        logger.error(f"❌ Error getting system status: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ✅ NUEVO ENDPOINT: Forzar ciclo de predicciones manual
@app.post("/api/ai/predictions/force-cycle-now")
async def force_prediction_cycle():
    """Fuerza un ciclo de predicciones inmediatamente"""
    try:
        logger.info("🔄 Forzando ciclo manual de predicciones...")
        
        # Ejecutar en background
        asyncio.create_task(asyncio.to_thread(run_automatic_predictions))
        
        return {
            "status": "started",
            "message": "Ciclo de predicciones iniciado manualmente",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error forzando ciclo: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }