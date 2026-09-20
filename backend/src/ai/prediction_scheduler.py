# src/ai/prediction_scheduler.py - CORRECCIÓN DE IMPORTS

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from src.database import SessionLocal
from src.models.machine import Machine
from src.models.work_order import WorkOrder
from src.models.ai_prediction import MachinePrediction
from src.ai.predictive_service import PredictiveMaintenanceService
from src.models.user import User

logger = logging.getLogger(__name__)

class RealPredictionScheduler:
    """Programador automático de predicciones REALES - SIN DATOS FICTICIOS"""
    
    def __init__(self):
        self.prediction_service = PredictiveMaintenanceService()
        self.is_running = False
    
    def get_real_ai_configuration(self):
        """✅ OBTIENE CONFIGURACIÓN REAL - CORRECCIÓN DE IMPORTS"""
        try:
            # ✅ MÉTODO SIMPLIFICADO: importar directamente
            config = None
            
            # Intentar desde diferentes rutas posibles
            import sys
            import importlib.util
            
            # Método 1: Buscar en módulos ya cargados
            for module_name in sys.modules:
                if 'routes_ai' in module_name:
                    try:
                        module = sys.modules[module_name]
                        if hasattr(module, 'AI_CONFIG_CACHE'):
                            config = module.AI_CONFIG_CACHE.copy()
                            logger.info(f"✅ Configuración cargada desde {module_name}")
                            break
                    except Exception as e:
                        logger.warning(f"Error accediendo a {module_name}: {e}")
                        continue
            
            # Método 2: Si no se encontró, detectar automáticamente
            if not config or not config.get("default_prediction_model"):
                logger.warning("⚠️ No se encontró configuración, detectando modelo automáticamente...")
                config = self.detect_available_model()
            
            # ✅ VERIFICAR QUE TENEMOS MODELO VÁLIDO
            if config and config.get("default_prediction_model"):
                logger.info(f"✅ Configuración válida: {config.get('default_prediction_model')}")
                return config
            else:
                logger.error("❌ No se pudo obtener configuración válida")
                return self.get_fallback_config()
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo configuración: {e}")
            return self.get_fallback_config()
    
    def get_fallback_config(self):
        """Configuración de respaldo cuando falla la detección"""
        return {
            "default_prediction_model": None,
            "prediction_confidence_threshold": 60,
            "auto_prediction_enabled": False,
            "prediction_frequency_hours": 3
        }
    
    def detect_available_model(self):
        """✅ DETECTA AUTOMÁTICAMENTE UN MODELO DISPONIBLE"""
        try:
            from src.ai.ollama_client import OllamaClient
            
            # Crear loop si no existe
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Obtener modelos disponibles
            ollama_client = OllamaClient()
            
            async def get_models():
                return await ollama_client.list_models()
            
            models = loop.run_until_complete(get_models())
            
            if not models:
                logger.error("❌ No se encontraron modelos en Ollama")
                return self.get_fallback_config()
            
            # ✅ BUSCAR MODELO PREFERIDO
            model_preferences = [
                "gemma3n:latest",  # Última versión de Gemma3
                "gemma3:12b",
                "deepseek-r1:8b",
                "qwen2.5:7b", 
                "llama3.2:3b",
                
            ]
            
            selected_model = None
            for preferred in model_preferences:
                for model in models:
                    if model.get('name') == preferred:
                        selected_model = preferred
                        break
                if selected_model:
                    break
            
            # Si no encuentra preferido, usar el primero disponible
            if not selected_model and models:
                selected_model = models[0].get('name')
            
            logger.info(f"🤖 Modelo detectado automáticamente: {selected_model}")
            
            return {
                "default_prediction_model": selected_model,
                "prediction_confidence_threshold": 60,
                "auto_prediction_enabled": True,
                "prediction_frequency_hours": 3
            }
            
        except Exception as e:
            logger.error(f"❌ Error detectando modelo: {e}")
            return self.get_fallback_config()
        

# ✅ MÉTODO ÚNICO CORREGIDO
async def run_real_prediction_cycle_corrected(self):
    """✅ MÉTODO ÚNICO - Ejecuta ciclo completo de predicciones REALES"""
    db = SessionLocal()
    try:
        logger.info("🔄 Iniciando ciclo de predicciones REALES...")
        
        # ✅ OBTENER CONFIGURACIÓN REAL
        ai_config = self.get_real_ai_configuration()
        
        real_model = ai_config.get("default_prediction_model")
        if not real_model:
            logger.error("❌ No hay modelo real configurado")
            return {"status": "error", "message": "No hay modelo configurado"}
        
        logger.info(f"🤖 Modelo REAL configurado: {real_model}")
        
        # ✅ OBTENER CONFIGURACIÓN DEL SCHEDULER
        try:
            import os
            import json
            CONFIG_FILE = "scheduler_config.json"
            scheduler_ai_config = {}
            
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
                    scheduler_ai_config = config_data.get("ai_predictions", {})
                    logger.info(f"📋 Config del scheduler: {scheduler_ai_config}")
                    
                    # Combinar configuraciones
                    ai_config.update(scheduler_ai_config)
                    logger.info(f"📊 Configuración FINAL: {ai_config}")
                    
        except Exception as e:
            logger.warning(f"⚠️ No se pudo cargar config del scheduler: {e}")
        
        # ✅ ENCONTRAR MÁQUINAS QUE NECESITAN ANÁLISIS
        machines_to_analyze = self.get_real_machines_needing_analysis(db, ai_config)
        
        if not machines_to_analyze:
            logger.info("ℹ️ No hay máquinas que necesiten análisis en este momento")
            return {"status": "success", "message": "No hay máquinas para analizar"}
        
        logger.info(f"📊 Analizando {len(machines_to_analyze)} máquinas REALES")
        
        # ✅ GENERAR PREDICCIONES PARA CADA MÁQUINA
        successful_predictions = 0
        errors = []
        
        for machine in machines_to_analyze:
            try:
                logger.info(f"🔮 Analizando máquina: {machine.nombre}")
                
                prediction_result = await self.generate_real_machine_prediction(
                    machine, db, ai_config
                )
                
                if prediction_result:
                    successful_predictions += 1
                    logger.info(f"✅ Predicción REAL generada para {machine.nombre}")
                else:
                    logger.info(f"⚠️ Predicción para {machine.nombre} no cumplió criterios de confianza")
                
            except Exception as e:
                error_msg = f"❌ Error predicción para {machine.nombre}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        
        # ✅ RESULTADO FINAL
        result_message = f"🎯 Ciclo REAL completado: {successful_predictions}/{len(machines_to_analyze)} predicciones exitosas"
        logger.info(result_message)
        
        status = "success" if successful_predictions > 0 else "partial" if len(errors) < len(machines_to_analyze) else "error"
        
        return {
            "status": status,
            "message": result_message,
            "successful_predictions": successful_predictions,
            "total_machines": len(machines_to_analyze),
            "errors": errors,
            "config_used": ai_config
        }
        
    except Exception as e:
        error_msg = f"❌ Error general en ciclo de predicciones REALES: {e}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}
    finally:
        db.close()

        
    
    async def generate_real_machine_prediction(self, machine: Machine, db: Session, ai_config: dict):
        """Genera predicción REAL para una máquina específica usando SOLO datos reales"""
        
        try:
            logger.info(f"🔮 Generando predicción REAL para {machine.nombre} (ID: {machine.id})")
            
            # Preparar datos REALES de la máquina
            machine_data = {
                "id": machine.id,
                "nombre": machine.nombre,
                "modelo": machine.modelo,
                "marca": machine.marca,
                "criticidad": machine.criticidad,
                "section": machine.section.nombre if machine.section else None,
            }
            
            # Obtener historial REAL de órdenes de trabajo
            historical_orders = db.query(WorkOrder).filter(
                WorkOrder.machine_id == machine.id,
                WorkOrder.status == "Cerrada"
            ).order_by(desc(WorkOrder.created_at)).limit(50).all()
            
            if len(historical_orders) < 2:
                logger.info(f"⚠️ Máquina {machine.nombre} tiene insuficientes datos históricos ({len(historical_orders)} órdenes)")
                return None
            
            historical_data = []
            for order in historical_orders:
                historical_data.append({
                    "date": order.created_at.isoformat(),
                    "work_type": order.work_type,
                    "downtime_hours": float(order.downtime_hours) if order.downtime_hours is not None else 0.0,
                    "failure_code": order.failure_code.code if order.failure_code else None,
                    "cause_code": order.cause_code.code if order.cause_code else None,
                })
            
            # Usar modelo REAL configurado
            model_to_use = ai_config.get("default_prediction_model")
            confidence_threshold = ai_config.get("prediction_confidence_threshold", 70)
            
            if not model_to_use:
                logger.error(f"❌ No hay modelo real configurado para predicción")
                return None
            
            logger.info(f"🤖 Usando modelo REAL: {model_to_use}, umbral: {confidence_threshold}%")
            
            # Generar predicción con IA REAL
            prediction_result = await self.prediction_service.predict_machine_failure(
                machine_data=machine_data,
                historical_data=historical_data,
                days_ahead=30,
                model_override=model_to_use,
                confidence_threshold=confidence_threshold
            )
            
            # Validar resultado
            confidence = prediction_result.get("confidence", 0)
            probability = prediction_result.get("probability", 0)
            
            logger.info(f"📊 Resultado REAL para {machine.nombre}: "
                       f"Probabilidad: {probability}%, Confianza: {confidence}%")
            
            # ✅ OBTENER USUARIO DEL SISTEMA PARA created_by_id
            system_user = db.query(User).filter(User.role_id == 1).first()
            if not system_user:
                system_user = db.query(User).first()
            creator_id = system_user.id if system_user else 1
            
            # Validar y guardar predicción
            if confidence is None or probability is None:
                logger.info(f"⚠️ Predicción para {machine.nombre} no se generó correctamente (confianza o probabilidad es None)")
                return None
            
            if confidence < confidence_threshold:
                logger.info(f"⚠️ Predicción para {machine.nombre} NO cumple umbral: confianza {confidence}% < {confidence_threshold}%")
                return None
                
            if probability <= 10:
                logger.info(f"⚠️ Predicción para {machine.nombre} tiene probabilidad muy baja: {probability}%")
                return None
            
            logger.info(f"✅ Predicción para {machine.nombre} ACEPTADA: confianza {confidence}% >= {confidence_threshold}%, probabilidad {probability}%")
            
            # Continuar con el código de guardado de predicción...
            predicted_date = None
            if prediction_result.get("predicted_date"):
                try:
                    predicted_date = datetime.strptime(
                        prediction_result["predicted_date"], "%Y-%m-%d"
                    ).date()
                except Exception as e:
                    logger.warning(f"⚠️ Error parseando fecha: {e}")
            
            # Desactivar predicciones anteriores
            db.query(MachinePrediction).filter(
                MachinePrediction.machine_id == machine.id,
                MachinePrediction.status == "active"
            ).update({"status": "expired"})
            
            # Crear predicción REAL
            new_prediction = MachinePrediction(
                machine_id=machine.id,
                prediction_type="failure",
                probability=probability,
                confidence=confidence,
                predicted_date=predicted_date,
                prediction_data=prediction_result,
                components_at_risk=prediction_result.get("components_at_risk", []),
                recommended_actions=prediction_result.get("recommended_actions", []),
                model_used=model_to_use,
                data_points_used=len(historical_data),
                status="active",
                created_at=datetime.utcnow(),
                created_by_id=creator_id
            )
            
            db.add(new_prediction)
            db.commit()
            
            logger.info(f"✅ Predicción REAL guardada para {machine.nombre}: {probability}% probabilidad, {confidence}% confianza")
            return new_prediction
            
                
        except Exception as e:
            logger.error(f"❌ Error generando predicción REAL para {machine.nombre}: {e}")
            db.rollback()
            return None

# ✅ INSTANCIA GLOBAL REAL
real_prediction_scheduler = RealPredictionScheduler()

# ✅ FUNCIÓN ÚNICA DE CICLO REAL
def run_single_real_prediction_cycle():
    """✅ FUNCIÓN ÚNICA - Ejecuta UN ciclo completo de predicciones REALES"""
    
    logger.info("🚀 INICIANDO CICLO REAL DE PREDICCIONES...")
    
    loop = None
    try:
        # Crear nuevo loop asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Ejecutar ciclo async
        result = loop.run_until_complete(real_prediction_scheduler.run_real_prediction_cycle())
        
        logger.info(f"✅ CICLO REAL COMPLETADO: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ ERROR EN CICLO REAL: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if loop:
            try:
                loop.close()
            except:
                pass


# ✅ FUNCIÓN DE COMPATIBILIDAD (para código existente)
def run_single_prediction_cycle():
    """Función de compatibilidad que ejecuta el ciclo REAL"""
    return run_single_real_prediction_cycle()

# ✅ ALIASES para compatibilidad
prediction_scheduler = real_prediction_scheduler

def run_real_prediction_cycle_with_config(ai_config: dict):
    """
    ✅ EJECUTA CICLO REAL CON CONFIGURACIÓN PERSONALIZADA
    """
    loop = None
    try:
        # Crear nuevo loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info(f"🔄 Ejecutando ciclo REAL con configuración personalizada:")
        logger.info(f"   - Máquinas por ciclo: {ai_config.get('max_machines_per_cycle', 5)}")
        logger.info(f"   - Cooldown: {ai_config.get('cooldown_minutes', 30)} min")
        logger.info(f"   - Umbral confianza: {ai_config.get('confidence_threshold', 70)}%")
        
        # Ejecutar ciclo usando la configuración personalizada
        result = loop.run_until_complete(real_prediction_scheduler.run_real_prediction_cycle())
        
        logger.info(f"✅ Ciclo REAL con configuración personalizada completado: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error en ciclo REAL con configuración: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if loop:
            try:
                loop.close()
            except:
                pass


def get_real_machines_needing_analysis(self, db: Session, ai_config: dict):
    """✅ FUNCIÓN ÚNICA - Identifica máquinas que necesitan análisis REAL"""
    
    now = datetime.utcnow()
    cooldown_hours = ai_config.get("cooldown_minutes", 30) / 60
    analysis_threshold = now - timedelta(hours=cooldown_hours)
    max_machines = ai_config.get("max_machines_per_cycle", 3)
    
    logger.info(f"🔍 Buscando máquinas (máx: {max_machines}) sin análisis desde: {analysis_threshold}")
    
    try:
        # Usar configuración de secciones prioritarias
        priority_sections = ai_config.get("priority_sections", "1,4,7")
        if isinstance(priority_sections, str):
            priority_section_ids = [int(x.strip()) for x in priority_sections.split(",") if x.strip().isdigit()]
        else:
            priority_section_ids = [1, 4, 7]  # Fallback
        
        logger.info(f"📊 Secciones prioritarias: {priority_section_ids}")
        
        # ✅ CONSULTA OPTIMIZADA para encontrar máquinas con fallos recientes
        from sqlalchemy import text
        
        machines_query = text("""
            SELECT DISTINCT m.id, m.nombre, m.section_id,
                   COUNT(wo.id) as total_ordenes,
                   COUNT(CASE WHEN wo.work_type = 'Correctivo' THEN 1 END) as total_fallos
            FROM machines m
            INNER JOIN work_orders wo ON m.id = wo.machine_id
            WHERE wo.status = 'Cerrada'
            AND m.section_id IN :section_ids
            GROUP BY m.id, m.nombre, m.section_id
            HAVING COUNT(wo.id) >= 2 
            AND COUNT(CASE WHEN wo.work_type = 'Correctivo' THEN 1 END) >= 1
            ORDER BY COUNT(CASE WHEN wo.work_type = 'Correctivo' THEN 1 END) DESC
            LIMIT :max_machines
        """)
        
        machines_data = db.execute(machines_query, {
            "section_ids": tuple(priority_section_ids),
            "max_machines": max_machines
        }).fetchall()
        
        logger.info(f"📊 Máquinas candidatas encontradas: {len(machines_data)}")
        
        # Filtrar máquinas sin análisis reciente
        final_machines = []
        for machine_data in machines_data:
            machine_id = machine_data.id
            
            # Verificar si tiene predicción reciente
            recent_prediction = db.query(MachinePrediction).filter(
                MachinePrediction.machine_id == machine_id,
                MachinePrediction.created_at >= analysis_threshold,
                MachinePrediction.status == "active"
            ).first()
            
            if not recent_prediction:
                # Obtener objeto máquina completo
                machine = db.query(Machine).filter(Machine.id == machine_id).first()
                if machine:
                    final_machines.append(machine)
                    logger.info(f"  ✅ {machine.nombre} (ID: {machine_id}, Fallos: {machine_data.total_fallos})")
            else:
                logger.info(f"  ⚠️ {machine_data.nombre} ya tiene predicción reciente")
        
        logger.info(f"📈 Máquinas finales para análisis: {len(final_machines)}")
        return final_machines
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo máquinas: {e}")
        return []




# ✅ Y AL FINAL DEL TODO, ESTAS LÍNEAS:
RealPredictionScheduler.get_real_machines_needing_analysis = get_real_machines_needing_analysis
RealPredictionScheduler.run_real_prediction_cycle = run_real_prediction_cycle_corrected
# ✅ ALIASES para compatibilidad (si existen)
prediction_scheduler = real_prediction_scheduler

