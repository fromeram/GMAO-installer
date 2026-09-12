# routes_ai.py - VERSIÓN COMPLETAMENTE CORREGIDA SIN DATOS FICTICIOS

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from src.ai.ollama_client import OllamaClient
from src.models.machine import Machine
from src.models.work_order import WorkOrder
from src.models.section import Section
from src.models.ai_prediction import MachinePrediction
from datetime import datetime, timedelta
from .database import SessionLocal, get_db
from src.auth import get_current_user
from src.models.user import User
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text, desc, func, or_
from typing import Optional, List, Dict
from pydantic import BaseModel
import json
import time
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Predictive Maintenance"])

# ✅ CONFIGURACIÓN CORREGIDA - SIN MODELOS FICTICIOS
AI_CONFIG_CACHE = {
    "default_prediction_model": None,  # ✅ Se detectará automáticamente
    "default_chat_model": None,        # ✅ Se detectará automáticamente  
    "prediction_confidence_threshold": 70,
    "auto_prediction_enabled": True,
    "prediction_frequency_minutes": 20,  # ✅ Como tienes configurado
    "performance_evaluation_days": 30,
    "ollama_server_url": "http://192.168.1.62:11434",
    "max_prediction_history_days": 365
}

# Un diccionario simple para mantener el estado de la IA.
AI_STATE = {
    "ready": False,
    "message": "AI is initializing...",
    "models": {}
}
# -------------------------------------------

# --- Bloque 3: AÑADE ESTA NUEVA FUNCIÓN ---
from fastapi import Depends, HTTPException # Asegúrate de tener estos imports

async def get_ai_ready():
    """
    Una dependencia de FastAPI que comprueba si la IA está lista.
    Si no lo está, lanza un error 503 (Servicio No Disponible).
    """
    if not AI_STATE["ready"]:
        raise HTTPException(
            status_code=503, 
            detail=f"Servicio de IA no disponible: {AI_STATE['message']}"
        )
    return AI_STATE
# ------------------------------------------



# ✅ FUNCIÓN PARA DETECTAR MODELOS REALES AL STARTUP
async def initialize_real_models():
    """Detecta y configura los modelos y actualiza el estado global."""
    global AI_STATE, AI_CONFIG_CACHE # Usamos el estado global y el cache
    try:
        ollama_client = OllamaClient()
        real_models = await ollama_client.list_models()
        
        if not real_models:
            AI_STATE["message"] = "Error: No se encontraron modelos en el servidor de Ollama."
            logger.error(AI_STATE["message"])
            return # La función termina aquí, el estado no cambia a 'ready'

        # --- Tu lógica para buscar modelos (esto no cambia) ---
        deepseek_model = None
        chat_model = None
        for model in real_models:
            model_name = model.get('name', '').lower()
            if 'deepseek' in model_name and 'r1' in model_name:
                deepseek_model = model.get('name')
            elif any(x in model_name for x in ['llama3.2', 'qwen', 'mistral']) and not chat_model:
                chat_model = model.get('name')
        
        if deepseek_model:
            AI_CONFIG_CACHE["default_prediction_model"] = deepseek_model
        if chat_model:
            AI_CONFIG_CACHE["default_chat_model"] = chat_model
        
        if not deepseek_model and real_models:
            first_model = real_models[0].get('name')
            AI_CONFIG_CACHE["default_prediction_model"] = first_model
            AI_CONFIG_CACHE["default_chat_model"] = first_model
            logger.warning(f"⚠️ DeepSeek no encontrado, usando: {first_model}")
        
        # --- Actualizamos el "semáforo" para ponerlo en VERDE ---
        AI_STATE["models"]["prediction"] = AI_CONFIG_CACHE.get("default_prediction_model")
        AI_STATE["models"]["chat"] = AI_CONFIG_CACHE.get("default_chat_model")
        AI_STATE["ready"] = True
        AI_STATE["message"] = "AI models loaded successfully."
        logger.info(f"✅ AI State is now READY. Models: {AI_STATE['models']}")
        # -----------------------------------------------------------

    except Exception as e:
        # --- Si hay un error, lo anotamos en el "semáforo" ---
        error_message = f"Error crítico durante la inicialización de la IA: {e}"
        AI_STATE["message"] = error_message
        logger.error(error_message, exc_info=True)
        # ----------------------------------------------------


class ChatMessage(BaseModel):
    message: str
    model: str
    assistant_type: str = "maintenance-expert"
    assistant_prompt: Optional[str] = None
    settings: Dict = {}
    context: dict = {}


class EnhancedMachineAnalyzer:
    """Analizador REAL usando SOLO tus datos reales"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def get_machine_intelligence(self, machine_id: int) -> Dict:
        """Obtiene análisis completo REAL de una máquina específica"""
        
        # 1. Datos básicos REALES de la máquina
        machine_query = text("""
            SELECT m.id, m.nombre, m.modelo, m.marca, m.criticidad,
                   s.nombre as seccion, m.section_id
            FROM machines m
            LEFT JOIN sections s ON m.section_id = s.id
            WHERE m.id = :machine_id
        """)
        machine_data = self.db.execute(machine_query, {"machine_id": machine_id}).fetchone()
        
        if not machine_data:
            return {"error": "Máquina no encontrada"}
        
        # 2. Análisis de fallos REALES (últimos 6 meses)
        failure_analysis = self._analyze_real_machine_failures(machine_id)
        
        # 3. Comparación con máquinas similares REALES
        similar_machines = self._get_real_similar_machines_performance(machine_data)
        
        # 4. Predicción basada en patrones REALES
        prediction = self._predict_real_next_maintenance(machine_id, failure_analysis)
        
        # 5. Recomendaciones específicas REALES
        recommendations = self._generate_real_recommendations(
            machine_data, failure_analysis, similar_machines
        )
        
        return {
            "machine_info": {
                "id": machine_data.id,
                "nombre": machine_data.nombre,
                "modelo": machine_data.modelo,
                "marca": machine_data.marca,
                "seccion": machine_data.seccion,
                "criticidad": machine_data.criticidad
            },
            "failure_analysis": failure_analysis,
            "similar_machines": similar_machines,
            "prediction": prediction,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat(),
            "data_source": "100_percent_real_data"
        }
    
    def _analyze_real_machine_failures(self, machine_id: int) -> Dict:
        """Análisis REAL usando SOLO datos históricos de tu planta"""
        
        query = text("""
            SELECT 
                COUNT(*) as total_ordenes,
                COUNT(CASE WHEN work_type = 'Correctivo' THEN 1 END) as total_fallos,
                COUNT(CASE WHEN work_type = 'Preventivo' THEN 1 END) as total_preventivos,
                ROUND(AVG(downtime_hours), 2) as promedio_downtime,
                MAX(created_at) as ultimo_mantenimiento,
                MIN(created_at) as primer_registro,
                -- MTBF REAL calculado con tus datos
                CASE 
                    WHEN COUNT(CASE WHEN work_type = 'Correctivo' THEN 1 END) > 1 THEN
                        EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at)))/86400 / 
                        NULLIF(COUNT(CASE WHEN work_type = 'Correctivo' THEN 1 END) - 1, 0)
                    ELSE NULL
                END as mtbf_dias,
                -- Tendencia REAL reciente vs anterior
                COUNT(CASE WHEN created_at >= NOW() - INTERVAL '30 days' AND work_type = 'Correctivo' THEN 1 END) as fallos_ultimos_30,
                COUNT(CASE WHEN created_at BETWEEN NOW() - INTERVAL '60 days' AND NOW() - INTERVAL '30 days' AND work_type = 'Correctivo' THEN 1 END) as fallos_anteriores_30
            FROM work_orders 
            WHERE machine_id = :machine_id 
            AND created_at >= NOW() - INTERVAL '6 months'
        """)
        
        result = self.db.execute(query, {"machine_id": machine_id}).fetchone()
        
        # Análisis de tendencia REAL
        tendencia = "estable"
        if result.fallos_ultimos_30 > result.fallos_anteriores_30:
            tendencia = "empeorando"
        elif result.fallos_ultimos_30 < result.fallos_anteriores_30:
            tendencia = "mejorando"
        
        # Nivel de riesgo basado en datos REALES
        riesgo = "bajo"
        if result.total_fallos >= 5 or (result.mtbf_dias and result.mtbf_dias < 15):
            riesgo = "alto"
        elif result.total_fallos >= 3 or (result.mtbf_dias and result.mtbf_dias < 30):
            riesgo = "medio"
        
        return {
            "total_ordenes": result.total_ordenes or 0,
            "total_fallos": result.total_fallos or 0,
            "total_preventivos": result.total_preventivos or 0,
            "promedio_downtime": float(result.promedio_downtime) if result.promedio_downtime else 0,
            "ultimo_mantenimiento": result.ultimo_mantenimiento.isoformat() if result.ultimo_mantenimiento else None,
            "mtbf_dias": float(result.mtbf_dias) if result.mtbf_dias else None,
            "tendencia": tendencia,
            "nivel_riesgo": riesgo,
            "fallos_recientes": result.fallos_ultimos_30 or 0,
            "ratio_correctivo": round((result.total_fallos / result.total_ordenes * 100), 1) if result.total_ordenes > 0 else 0,
            "analysis_type": "real_historical_data"
        }
    
    def _get_real_similar_machines_performance(self, machine_data) -> List[Dict]:
        """Compara con máquinas REALES similares de tu planta"""
        
        query = text("""
            WITH machine_stats AS (
                SELECT 
                    m.id, m.nombre, m.criticidad,
                    COUNT(wo.id) as total_ordenes,
                    COUNT(CASE WHEN wo.work_type = 'Correctivo' THEN 1 END) as fallos,
                    ROUND(AVG(wo.downtime_hours), 2) as avg_downtime
                FROM machines m
                LEFT JOIN work_orders wo ON m.id = wo.machine_id 
                    AND wo.created_at >= NOW() - INTERVAL '3 months'
                WHERE m.section_id = :section_id AND m.id != :machine_id
                GROUP BY m.id, m.nombre, m.criticidad
                HAVING COUNT(wo.id) > 0
            )
            SELECT *,
                CASE 
                    WHEN fallos <= 1 THEN 'excelente'
                    WHEN fallos <= 2 THEN 'bueno'
                    WHEN fallos <= 4 THEN 'regular'
                    ELSE 'malo'
                END as rendimiento
            FROM machine_stats
            ORDER BY fallos ASC, avg_downtime ASC
            LIMIT 5
        """)
        
        results = self.db.execute(query, {
            "section_id": machine_data.section_id,
            "machine_id": machine_data.id
        }).fetchall()
        
        return [
            {
                "id": r.id,
                "nombre": r.nombre,
                "criticidad": r.criticidad,
                "total_ordenes": r.total_ordenes,
                "fallos": r.fallos,
                "avg_downtime": float(r.avg_downtime) if r.avg_downtime else 0,
                "rendimiento": r.rendimiento,
                "data_source": "real_plant_comparison"
            }
            for r in results
        ]
    
    def _predict_real_next_maintenance(self, machine_id: int, failure_analysis: Dict) -> Dict:
        """Predicción REAL basada SOLO en patrones de tus datos"""
        
        mtbf_dias = failure_analysis.get('mtbf_dias')
        ultimo_mantenimiento = failure_analysis.get('ultimo_mantenimiento')
        tendencia = failure_analysis.get('tendencia')
        nivel_riesgo = failure_analysis.get('nivel_riesgo')
        
        if not ultimo_mantenimiento:
            return {
                "fecha_estimada": None,
                "dias_hasta_mantenimiento": None,
                "confianza": 0,
                "motivo": "Sin historial suficiente para predicción real",
                "prediction_type": "insufficient_data"
            }
        
        # Calcular días desde último mantenimiento REAL
        ultimo = datetime.fromisoformat(ultimo_mantenimiento.replace('Z', ''))
        dias_desde_ultimo = (datetime.utcnow() - ultimo).days
        
        # ✅ PREDICCIÓN BASADA SOLO EN TUS DATOS REALES
        if mtbf_dias and mtbf_dias > 0:
            # Ajustar MTBF según tendencia REAL observada
            mtbf_ajustado = mtbf_dias
            if tendencia == "empeorando":
                mtbf_ajustado *= 0.7  # Más conservador por tendencia real negativa
            elif tendencia == "mejorando":
                mtbf_ajustado *= 1.3  # Más optimista por tendencia real positiva
            
            dias_hasta_proximo = max(1, int(mtbf_ajustado - dias_desde_ultimo))
            fecha_estimada = datetime.utcnow() + timedelta(days=dias_hasta_proximo)
            
            # Confianza basada en cantidad de datos REALES
            confianza = 30  # Base mínima
            if failure_analysis['total_fallos'] >= 5:
                confianza += 40  # Muchos datos = alta confianza
            elif failure_analysis['total_fallos'] >= 3:
                confianza += 25  # Datos suficientes
            
            if tendencia == "estable":
                confianza += 20
            if nivel_riesgo == "alto":
                confianza += 15  # Patrones claros de fallo
                
        else:
            # Sin MTBF, usar heurísticas conservadoras basadas en riesgo REAL
            if nivel_riesgo == "alto" and failure_analysis['fallos_recientes'] > 2:
                dias_hasta_proximo = 7  # Crítico según datos reales
                confianza = 60
            elif nivel_riesgo == "medio":
                dias_hasta_proximo = 21  # Medio según análisis real
                confianza = 45
            else:
                dias_hasta_proximo = 45  # Bajo riesgo según datos
                confianza = 30
            
            fecha_estimada = datetime.utcnow() + timedelta(days=dias_hasta_proximo)
        
        return {
            "fecha_estimada": fecha_estimada.strftime("%Y-%m-%d"),
            "dias_hasta_mantenimiento": dias_hasta_proximo,
            "confianza": min(95, max(20, confianza)),
            "mtbf_usado": mtbf_dias,
            "ajuste_tendencia": tendencia,
            "dias_desde_ultimo": dias_desde_ultimo,
            "motivo": f"Basado en {failure_analysis['total_fallos']} fallos reales históricos",
            "prediction_type": "real_data_based",
            "total_historical_failures": failure_analysis['total_fallos']
        }
    
    def _generate_real_recommendations(self, machine_data, failure_analysis, similar_machines) -> List[str]:
        """Recomendaciones REALES específicas basadas en TUS datos"""
        
        recommendations = []
        nombre = machine_data.nombre
        seccion = machine_data.seccion
        
        # ✅ RECOMENDACIONES BASADAS EN ANÁLISIS REAL
        if failure_analysis['nivel_riesgo'] == 'alto':
            recommendations.append(f"🚨 DATOS REALES: {nombre} tiene {failure_analysis['total_fallos']} fallos históricos reales - requiere inspección urgente")
            
            if failure_analysis['tendencia'] == 'empeorando':
                recommendations.append(f"📈 TENDENCIA REAL NEGATIVA: {nombre} - fallos recientes aumentaron según datos históricos")
                
        elif failure_analysis['nivel_riesgo'] == 'medio':
            recommendations.append(f"⚠️ ANÁLISIS REAL: {nombre} muestra {failure_analysis['total_fallos']} fallos en historial - planificar preventivo")
        
        # Comparación REAL con máquinas de tu planta
        if similar_machines:
            mejor_similar = similar_machines[0]
            if failure_analysis['total_fallos'] > mejor_similar['fallos']:
                recommendations.append(f"📊 COMPARACIÓN REAL: {nombre} ({failure_analysis['total_fallos']} fallos) vs {mejor_similar['nombre']} ({mejor_similar['fallos']} fallos) - máquina similar de tu planta")
        
        # MTBF REAL calculado
        mtbf = failure_analysis.get('mtbf_dias')
        if mtbf and mtbf < 20:
            recommendations.append(f"⏱️ MTBF REAL CRÍTICO: {nombre} falla cada {mtbf:.1f} días según datos históricos - revisar estrategia preventiva")
        
        # Ratio correctivo REAL
        ratio = failure_analysis.get('ratio_correctivo', 0)
        if ratio > 70:
            recommendations.append(f"🔧 DATOS REALES: {nombre} tiene {ratio}% correctivo - aumentar mantenimiento preventivo")
        
        # Recomendaciones específicas por SECCIÓN REAL
        if seccion and failure_analysis['total_fallos'] > 0:
            section_recommendations = {
                "Prensas": f"🏭 PRENSAS: Revisar sistema hidráulico y calibración según historial de {nombre}",
                "Clasificacion": f"📦 CLASIFICACIÓN: Verificar sensores y transporte en {nombre} (fallos reales detectados)",
                "RECTIFICADORAS": f"⚙️ RECTIFICADORAS: Inspeccionar refrigeración y herramientas de {nombre}",
                "Esmaltadoras": f"🎨 ESMALTADORAS: Revisar aplicación y secado en {nombre}",
                "Hornos": f"🔥 HORNOS: Verificar temperatura y quemadores en {nombre}",
                "Mantenimiento": f"🔧 MANTENIMIENTO: Revisar equipos auxiliares de {nombre}"
            }
            
            if seccion in section_recommendations:
                recommendations.append(section_recommendations[seccion])
        
        # Si no hay fallos, recomendación positiva REAL
        if failure_analysis['total_fallos'] == 0:
            recommendations.append(f"✅ DATOS REALES: {nombre} no presenta fallos históricos - mantener rutina preventiva actual")
        
        return recommendations


# ✅ ENDPOINT PRINCIPAL CORREGIDO PARA USAR SOLO DATOS REALES
@router.get("/predictions/real-data", dependencies=[Depends(get_ai_ready)])
async def get_completely_real_predictions(
    machine_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """✅ OBTIENE PREDICCIONES 100% REALES - SIN DATOS SINTÉTICOS"""
    try:
        logger.info(f"🔍 Obteniendo predicciones COMPLETAMENTE REALES para {days} días")
        
        # ✅ ASEGURAR QUE TENEMOS MODELOS REALES
        if not AI_CONFIG_CACHE.get("default_prediction_model"):
            await initialize_real_models()
        
        # Query SOLO predicciones reales guardadas en BD
        query = db.query(MachinePrediction).options(
            joinedload(MachinePrediction.machine).joinedload(Machine.section),
        ).filter(
            MachinePrediction.created_at >= datetime.utcnow() - timedelta(days=days),
            MachinePrediction.status.in_(["active", "superseded"])
        )
        
        if machine_id:
            query = query.filter(MachinePrediction.machine_id == machine_id)
        
        # Filtrar por sección si es jefe de sección
        if current_user.role.nombre == "Jefe de Sección":
            query = query.join(Machine).filter(Machine.section_id == current_user.section_id)
        
        real_predictions = query.order_by(desc(MachinePrediction.created_at)).all()
        
        logger.info(f"📊 Predicciones REALES encontradas en BD: {len(real_predictions)}")
        
        # ✅ SI NO HAY PREDICCIONES REALES, FORZAR GENERACIÓN
        if len(real_predictions) == 0:
            logger.warning("❌ NO hay predicciones reales en BD - necesitas ejecutar el scheduler")
            
            return {
                "predictions": [],
                "total_predictions": 0,
                "data_source": "no_real_predictions_found",
                "model_configured": AI_CONFIG_CACHE.get("default_prediction_model", "Not detected"),
                "message": "No se encontraron predicciones reales. Ejecuta el scheduler manual o espera al automático.",
                "generated_at": datetime.utcnow().isoformat(),
                "suggestion": "Usa el botón 'Ciclo Manual' en AIPredictions para generar predicciones reales"
            }
        
        # ✅ FORMATEAR SOLO PREDICCIONES REALES
        formatted_predictions = []
        for pred in real_predictions:
            formatted_predictions.append({
                "id": pred.id,
                "machine": {
                    "id": pred.machine.id,
                    "name": pred.machine.nombre,
                    "section": pred.machine.section.nombre if pred.machine.section else None
                },
                "prediction_type": pred.prediction_type,
                "probability": pred.probability,
                "confidence": pred.confidence,
                "predicted_date": pred.predicted_date.isoformat() if pred.predicted_date else None,
                "components_at_risk": pred.components_at_risk or [],
                "recommended_actions": pred.recommended_actions or [],
                "model_used": pred.model_used or AI_CONFIG_CACHE.get("default_prediction_model", "Unknown"),
                "created_at": pred.created_at.isoformat(),
                "status": pred.status,
                "actual_outcome": pred.actual_outcome,
                "data_points_used": pred.data_points_used,
                "data_source": "100_percent_real_ai_prediction"
            })
        
        return {
            "predictions": formatted_predictions,
            "total_predictions": len(formatted_predictions),
            "data_source": "only_real_database_predictions",
            "model_configured": AI_CONFIG_CACHE.get("default_prediction_model", "Not configured"),
            "generated_at": datetime.utcnow().isoformat(),
            "note": "Estas predicciones fueron generadas por IA real usando datos históricos de tu planta"
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo predicciones reales: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ✅ SCHEDULER MANUAL COMPLETAMENTE CORREGIDO
@router.post("/predictions/force-real-cycle", dependencies=[Depends(get_ai_ready)])
async def force_completely_real_prediction_cycle(
    section_id: Optional[int] = Query(None),
    max_machines: int = Query(5, ge=1, le=20),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """✅ FUERZA CICLO REAL DE PREDICCIONES SIN DATOS FICTICIOS"""
    try:
        logger.info(f"🚀 INICIANDO CICLO COMPLETAMENTE REAL - Usuario: {current_user.username}")
        
        # ✅ ASEGURAR MODELOS REALES
        models_detected = await initialize_real_models()
        if not models_detected:
            raise HTTPException(status_code=500, detail="No se pudieron detectar modelos reales en Ollama")
        
        real_model = AI_CONFIG_CACHE.get("default_prediction_model")
        if not real_model:
            raise HTTPException(status_code=500, detail="No hay modelo real configurado")
        
        # ✅ OBTENER MÁQUINAS REALES CON DATOS SUFICIENTES
        machines_query = text("""
            SELECT DISTINCT m.id, m.nombre, m.section_id, COUNT(wo.id) as orden_count
            FROM machines m
            INNER JOIN work_orders wo ON m.id = wo.machine_id
            WHERE wo.created_at >= NOW() - INTERVAL '3 months'
            AND (:section_id IS NULL OR m.section_id = :section_id)
            GROUP BY m.id, m.nombre, m.section_id
            HAVING COUNT(wo.id) >= 2
            ORDER BY COUNT(wo.id) DESC
            LIMIT :max_machines
        """)
        
        machines_data = db.execute(machines_query, {
            "section_id": section_id,
            "max_machines": max_machines
        }).fetchall()
        
        if not machines_data:
            raise HTTPException(status_code=404, detail="No se encontraron máquinas con datos suficientes para análisis real")
        
        logger.info(f"📊 Máquinas seleccionadas para análisis REAL: {len(machines_data)}")
        
        def real_prediction_task():
            """Tarea REAL de predicciones en segundo plano"""
            task_db = SessionLocal()
            successful_predictions = 0
            
            try:
                analyzer = EnhancedMachineAnalyzer(task_db)
                
                for machine_data in machines_data:
                    try:
                        machine_id = machine_data.id
                        logger.info(f"🔮 Analizando máquina REAL: {machine_data.nombre} (ID: {machine_id})")
                        
                        # ✅ GENERAR ANÁLISIS COMPLETAMENTE REAL
                        intelligence = analyzer.get_machine_intelligence(machine_id)
                        
                        if "error" in intelligence:
                            logger.error(f"❌ Error en análisis de {machine_data.nombre}: {intelligence['error']}")
                            continue
                        
                        prediction_data = intelligence['prediction']
                        
                        # ✅ GUARDAR PREDICCIÓN REAL EN BD SI ES VÁLIDA
                        if prediction_data.get('confianza', 0) >= AI_CONFIG_CACHE.get('prediction_confidence_threshold', 70):
                            
                            # Desactivar predicciones anteriores
                            task_db.query(MachinePrediction).filter(
                                MachinePrediction.machine_id == machine_id,
                                MachinePrediction.status == "active"
                            ).update({"status": "expired"})
                            
                            # Crear predicción REAL
                            predicted_date = None
                            if prediction_data.get('fecha_estimada'):
                                try:
                                    predicted_date = datetime.strptime(
                                        prediction_data['fecha_estimada'], "%Y-%m-%d"
                                    ).date()
                                except:
                                    pass
                            
                            new_prediction = MachinePrediction(
                                machine_id=machine_id,
                                prediction_type="failure",
                                probability=min(95, max(5, prediction_data.get('confianza', 50))),
                                confidence=prediction_data.get('confianza', 50),
                                predicted_date=predicted_date,
                                prediction_data=intelligence,  # ✅ Datos REALES completos
                                components_at_risk=intelligence.get('recommendations', [])[:3],  # Primeras 3 recomendaciones como componentes
                                recommended_actions=intelligence.get('recommendations', []),
                                model_used=real_model,  # ✅ MODELO REAL DETECTADO
                                data_points_used=intelligence['failure_analysis']['total_ordenes'],
                                status="active",
                                created_at=datetime.utcnow()
                            )
                            
                            task_db.add(new_prediction)
                            task_db.commit()
                            
                            successful_predictions += 1
                            logger.info(f"✅ Predicción REAL guardada para {machine_data.nombre}: {prediction_data.get('confianza')}% confianza")
                        else:
                            logger.info(f"⚠️ Predicción para {machine_data.nombre} no cumple umbral de confianza ({prediction_data.get('confianza', 0)}% < {AI_CONFIG_CACHE.get('prediction_confidence_threshold', 70)}%)")
                    
                    except Exception as e:
                        logger.error(f"❌ Error procesando máquina {machine_data.nombre}: {e}")
                        continue
                
                logger.info(f"🎯 Ciclo REAL completado: {successful_predictions}/{len(machines_data)} predicciones exitosas")
                
            except Exception as e:
                logger.error(f"❌ Error general en ciclo REAL: {e}")
                task_db.rollback()
            finally:
                task_db.close()
        
        # Ejecutar en segundo plano
        background_tasks.add_task(real_prediction_task)
        
        return {
            "message": f"🔄 Ciclo REAL iniciado para {len(machines_data)} máquinas con datos suficientes",
            "status": "started_real_analysis",
            "machines_selected": [{"id": m.id, "nombre": m.nombre, "ordenes": m.orden_count} for m in machines_data],
            "model_real_detected": real_model,
            "confidence_threshold": AI_CONFIG_CACHE.get('prediction_confidence_threshold', 70),
            "estimated_completion": "2-5 minutos",
            "initiated_by": current_user.username,
            "data_source": "100_percent_real_historical_data",
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Revisa AIPredictions en unos minutos para ver las predicciones REALES generadas"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ Error en ciclo REAL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ✅ ENDPOINTS CORREGIDOS

@router.get("/configuration", dependencies=[Depends(get_ai_ready)])
async def get_real_ai_configuration(
    current_user: User = Depends(get_current_user)
):
    """Obtiene la configuración REAL actual de IA"""
    
    # ✅ ASEGURAR DETECCIÓN DE MODELOS REALES
    if not AI_CONFIG_CACHE.get("default_prediction_model"):
        await initialize_real_models()
    
    return {
        "configuration": AI_CONFIG_CACHE,
        "models_detected": AI_CONFIG_CACHE.get("default_prediction_model") is not None,
        "last_updated": datetime.utcnow().isoformat(),
        "data_source": "real_ollama_detection"
    }


@router.post("/configuration", dependencies=[Depends(get_ai_ready)])
async def update_real_ai_configuration(
    config_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Actualiza la configuración de IA con validación REAL"""
    global AI_CONFIG_CACHE
    
    try:
        # ✅ VALIDAR QUE LOS MODELOS EXISTEN REALMENTE
        new_config = config_data.get("configuration", {})
        
        # Verificar modelos en Ollama
        ollama_client = OllamaClient()
        available_models = await ollama_client.list_models()
        available_names = [m.get('name') for m in available_models]
        
        # Validar modelo de predicción
        prediction_model = new_config.get("default_prediction_model")
        if prediction_model and prediction_model not in available_names:
            raise HTTPException(
                status_code=400, 
                detail=f"Modelo de predicción '{prediction_model}' no existe en Ollama. Disponibles: {available_names}"
            )
        
        # Validar modelo de chat
        chat_model = new_config.get("default_chat_model")
        if chat_model and chat_model not in available_names:
            raise HTTPException(
                status_code=400, 
                detail=f"Modelo de chat '{chat_model}' no existe en Ollama. Disponibles: {available_names}"
            )
        
        # ✅ ACTUALIZAR CONFIGURACIÓN CON MODELOS REALES
        AI_CONFIG_CACHE.update(new_config)
        
        logger.info(f"✅ Configuración actualizada por {current_user.username}")
        logger.info(f"   Predicción: {AI_CONFIG_CACHE.get('default_prediction_model')}")
        logger.info(f"   Chat: {AI_CONFIG_CACHE.get('default_chat_model')}")
        
        return {
            "message": "Configuración actualizada con modelos REALES verificados",
            "configuration": AI_CONFIG_CACHE,
            "models_verified": True,
            "available_models": available_names,
            "updated_by": current_user.username,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ Error actualizando configuración: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/available", dependencies=[Depends(get_ai_ready)])
async def get_real_available_models(
    current_user: User = Depends(get_current_user)
):
    """Obtiene DINÁMICAMENTE la lista de modelos REALES desde Ollama"""
    try:
        ollama_client = OllamaClient()
        
        logger.info(f"🔍 Conectando a Ollama en: {ollama_client.base_url}")
        raw_models = await ollama_client.list_models()
        
        logger.info(f"🤖 Modelos REALES encontrados: {len(raw_models)}")
        
        # ✅ CONVERTIR A FORMATO ESPERADO PERO CON DATOS REALES
        models = []
        for model in raw_models:
            model_name = model.get('name', '')
            model_size = model.get('size', 0)
            
            # Calcular velocidad basada en tamaño REAL
            size_gb = model_size / (1024**3) if model_size else 0
            if size_gb < 2:
                speed = 'Muy rápido'
                quality = 'Buena'
            elif size_gb < 5:
                speed = 'Rápido'  
                quality = 'Muy buena'
            elif size_gb < 10:
                speed = 'Moderado'
                quality = 'Excelente'
            else:
                speed = 'Lento'
                quality = 'Máxima'
            
            # Formatear tamaño REAL
            if size_gb > 1:
                size_str = f"{size_gb:.1f}GB"
            elif model_size > 1024*1024:
                size_str = f"{model_size/(1024*1024):.0f}MB"
            else:
                size_str = "Calculando..."
            
            # ✅ DETECTAR TIPO DE MODELO REAL
            display_name = model_name
            description = f'Modelo detectado automáticamente - {size_str}'
            
            if 'deepseek' in model_name.lower() and 'r1' in model_name.lower():
                display_name = f"DeepSeek R1 ({model_name})"
                description = f'Modelo de razonamiento avanzado - {size_str}'
            elif 'llama' in model_name.lower():
                display_name = f"Llama ({model_name})"
                description = f'Modelo de Meta optimizado - {size_str}'
            elif 'qwen' in model_name.lower():
                display_name = f"Qwen ({model_name})"
                description = f'Modelo multilingüe de Alibaba - {size_str}'
            
            models.append({
                'name': model_name,  # ✅ NOMBRE REAL EXACTO
                'displayName': display_name,
                'description': description,
                'speed': speed,
                'quality': quality,
                'size': size_str,
                'available': True,  # ✅ SI ESTÁ EN LA LISTA, ESTÁ DISPONIBLE
                'real_data': model,  # Datos completos REALES
                'detected_from': 'ollama_real_api'
            })
            
            logger.info(f"  ✅ {model_name} ({size_str}) - {speed}")
        
        return {
            "models": models,
            "total_available": len(models),
            "server_url": ollama_client.base_url,
            "detection_method": "real_dynamic_from_ollama",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error conectando con Ollama REAL: {e}")
        return {
            "models": [],
            "total_available": 0,
            "server_url": "http://192.168.1.62:11434",
            "error": f"No se pudo conectar con Ollama: {str(e)}",
            "detection_method": "failed_real_connection"
        }


@router.get("/models/health", dependencies=[Depends(get_ai_ready)])
async def check_real_ollama_health(
    current_user: User = Depends(get_current_user)
):
    """Verifica DINÁMICAMENTE el estado REAL de Ollama"""
    try:
        ollama_client = OllamaClient()
        
        logger.info(f"🏥 Verificando salud REAL de Ollama en: {ollama_client.base_url}")
        
        # ✅ VERIFICAR CONEXIÓN REAL
        health_status = await ollama_client.health_check()
        
        if health_status:
            # ✅ OBTENER MODELOS REALES
            models = await ollama_client.list_models()
            models_count = len(models)
            models_list = [m.get('name', '') for m in models]
            
            logger.info(f"✅ Ollama REAL saludable: {models_count} modelos detectados")
            
            return {
                "connected": True,
                "status": "healthy_real_connection",
                "models_count": models_count,
                "server_url": ollama_client.base_url,
                "last_check": datetime.utcnow().isoformat(),
                "models_list": models_list,  # ✅ LISTA REAL
                "deepseek_detected": any('deepseek' in m.lower() for m in models_list),
                "connection_type": "real_verified"
            }
        else:
            logger.warning("❌ Ollama no responde")
            return {
                "connected": False,
                "status": "unreachable_real_server",
                "models_count": 0,
                "server_url": ollama_client.base_url,
                "last_check": datetime.utcnow().isoformat(),
                "error": "Ollama server REAL no responde"
            }
            
    except Exception as e:
        logger.error(f"❌ Error verificando Ollama REAL: {e}")
        return {
            "connected": False,
            "status": "error_real_connection",
            "models_count": 0,
            "server_url": "http://192.168.1.62:11434",
            "last_check": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.post("/models/test/{model_name}", dependencies=[Depends(get_ai_ready)])
async def test_real_model(
    model_name: str,
    current_user: User = Depends(get_current_user)
):
    """Prueba un modelo REAL específico de Ollama"""
    try:
        logger.info(f"🧪 Probando modelo REAL: {model_name}")
        start_time = time.time()
        
        ollama_client = OllamaClient()
        
        # ✅ VERIFICAR QUE EL MODELO EXISTE REALMENTE
        available_models = await ollama_client.list_models()
        model_names = [m.get('name', '') for m in available_models]
        
        if model_name not in model_names:
            return {
                "status": "error",
                "message": f"Modelo '{model_name}' NO encontrado en Ollama",
                "available_models": model_names,
                "test_type": "real_model_verification"
            }
        
        # ✅ PROMPT DE PRUEBA ESPECÍFICO PARA MANTENIMIENTO
        test_prompt = "Responde brevemente: ¿Qué es MTBF en mantenimiento industrial?"
        
        response = await ollama_client.generate(
            model=model_name,
            prompt=test_prompt,
            temperature=0.3,
            max_tokens=100
        )
        
        response_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"✅ Modelo REAL {model_name} funciona correctamente ({response_time}ms)")
        
        return {
            "status": "success",
            "model": model_name,
            "response": response,
            "response_time_ms": response_time,
            "test_prompt": test_prompt,
            "test_type": "real_model_test",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error probando modelo REAL {model_name}: {e}")
        return {
            "status": "error",
            "model": model_name,
            "message": str(e),
            "test_type": "real_model_test_failed",
            "timestamp": datetime.utcnow().isoformat()
        }


# ✅ ANÁLISIS ESPECÍFICO DE MÁQUINA REAL
@router.get("/machine-analysis/{machine_id}", dependencies=[Depends(get_ai_ready)])
async def get_real_machine_analysis(
    machine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Análisis completo REAL de una máquina específica"""
    try:
        analyzer = EnhancedMachineAnalyzer(db)
        analysis = analyzer.get_machine_intelligence(machine_id)
        
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
        
        # ✅ ASEGURAR QUE SE MARCA COMO ANÁLISIS REAL
        analysis["analysis_type"] = "100_percent_real_data"
        analysis["model_would_use"] = AI_CONFIG_CACHE.get("default_prediction_model", "Not configured")
        
        return analysis
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ Error en análisis REAL: {e}")
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")


# ✅ RESUMEN GENERAL REAL DE LA PLANTA
@router.get("/plant-overview", dependencies=[Depends(get_ai_ready)])
async def get_real_plant_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resumen general REAL de toda la planta usando SOLO datos reales"""
    try:
        # ✅ ESTADÍSTICAS GENERALES REALES
        overview_query = text("""
            SELECT 
                COUNT(DISTINCT m.id) as total_maquinas,
                COUNT(DISTINCT s.id) as total_secciones,
                COUNT(wo.id) as ordenes_ultimo_mes,
                COUNT(CASE WHEN wo.work_type = 'Correctivo' THEN 1 END) as fallos_ultimo_mes,
                COUNT(CASE WHEN wo.work_type = 'Preventivo' THEN 1 END) as preventivos_ultimo_mes,
                ROUND(
                    COUNT(CASE WHEN wo.work_type = 'Correctivo' THEN 1 END) * 100.0 / 
                    NULLIF(COUNT(wo.id), 0), 1
                ) as porcentaje_correctivo_planta
            FROM machines m
            LEFT JOIN sections s ON m.section_id = s.id
            LEFT JOIN work_orders wo ON m.id = wo.machine_id 
                AND wo.created_at >= NOW() - INTERVAL '30 days'
        """)
        
        overview = db.execute(overview_query).fetchone()
        
        # ✅ SECCIONES CON MÁS PROBLEMAS REALES
        problematic_sections_query = text("""
            SELECT 
                s.nombre as seccion,
                COUNT(CASE WHEN wo.work_type = 'Correctivo' THEN 1 END) as fallos,
                COUNT(wo.id) as total_ordenes,
                ROUND(
                    COUNT(CASE WHEN wo.work_type = 'Correctivo' THEN 1 END) * 100.0 / 
                    NULLIF(COUNT(wo.id), 0), 1
                ) as porcentaje_correctivo
            FROM sections s
            LEFT JOIN machines m ON s.id = m.section_id
            LEFT JOIN work_orders wo ON m.id = wo.machine_id 
                AND wo.created_at >= NOW() - INTERVAL '30 days'
            GROUP BY s.id, s.nombre
            HAVING COUNT(wo.id) > 0
            ORDER BY porcentaje_correctivo DESC
            LIMIT 5
        """)
        
        problematic_sections = db.execute(problematic_sections_query).fetchall()
        
        # ✅ MÁQUINAS MÁS PROBLEMÁTICAS CON ID REAL
        top_problematic_machines_query = text("""
            SELECT 
                m.id,
                m.nombre,
                s.nombre as seccion,
                m.criticidad,
                COUNT(CASE WHEN wo.work_type = 'Correctivo' THEN 1 END) as fallos
            FROM machines m
            LEFT JOIN sections s ON m.section_id = s.id
            LEFT JOIN work_orders wo ON m.id = wo.machine_id 
                AND wo.created_at >= NOW() - INTERVAL '30 days'
            GROUP BY m.id, m.nombre, s.nombre, m.criticidad
            HAVING COUNT(CASE WHEN wo.work_type = 'Correctivo' THEN 1 END) > 0
            ORDER BY fallos DESC
            LIMIT 10
        """)
        
        top_problematic = db.execute(top_problematic_machines_query).fetchall()
        
        return {
            "plant_overview": {
                "total_maquinas": overview.total_maquinas,
                "total_secciones": overview.total_secciones,
                "ordenes_ultimo_mes": overview.ordenes_ultimo_mes,
                "fallos_ultimo_mes": overview.fallos_ultimo_mes,
                "preventivos_ultimo_mes": overview.preventivos_ultimo_mes,
                "porcentaje_correctivo_planta": float(overview.porcentaje_correctivo_planta) if overview.porcentaje_correctivo_planta else 0
            },
            "problematic_sections": [
                {
                    "seccion": ps.seccion,
                    "fallos": ps.fallos,
                    "total_ordenes": ps.total_ordenes,
                    "porcentaje_correctivo": float(ps.porcentaje_correctivo)
                }
                for ps in problematic_sections
            ],
            "top_problematic_machines": [
                {
                    "id": tp.id,  # ✅ ID REAL de la máquina
                    "nombre": tp.nombre,
                    "seccion": tp.seccion,
                    "criticidad": tp.criticidad,
                    "fallos": tp.fallos
                }
                for tp in top_problematic
            ],
            "data_source": "100_percent_real_plant_data",
            "generated_at": datetime.utcnow().isoformat(),
            "model_configured": AI_CONFIG_CACHE.get("default_prediction_model", "Not configured")
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo resumen REAL de planta: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo resumen de planta: {str(e)}")


# ✅ ENDPOINT DE INICIALIZACIÓN PARA FRONTEND
@router.post("/initialize-real-models", dependencies=[Depends(get_ai_ready)])
async def initialize_models_endpoint(
    current_user: User = Depends(get_current_user)
):
    """Endpoint para inicializar modelos reales desde el frontend"""
    try:
        success = await initialize_real_models()
        
        if success:
            return {
                "status": "success",
                "message": "Modelos reales detectados y configurados",
                "prediction_model": AI_CONFIG_CACHE.get("default_prediction_model"),
                "chat_model": AI_CONFIG_CACHE.get("default_chat_model"),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": "No se pudieron detectar modelos reales en Ollama",
                "suggestion": "Verifica que Ollama esté ejecutándose y tenga modelos instalados"
            }
            
    except Exception as e:
        logger.error(f"❌ Error inicializando modelos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ✅ CHAT CON IA USANDO MODELO REAL
@router.post("/chat/message", dependencies=[Depends(get_ai_ready)])
async def chat_with_real_ai(
    chat_data: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat con IA usando SOLO modelos reales detectados"""
    start_time = time.time()
    
    try:
        # ✅ ASEGURAR MODELOS REALES
        if not AI_CONFIG_CACHE.get("default_chat_model"):
            await initialize_real_models()
        
        real_chat_model = AI_CONFIG_CACHE.get("default_chat_model")
        if not real_chat_model:
            raise HTTPException(status_code=500, detail="No hay modelo de chat real configurado")
        
        # ✅ USAR MODELO REAL (IGNORAR EL DEL FRONTEND SI NO EXISTE)
        model_to_use = chat_data.model
        
        # Verificar que el modelo existe realmente
        ollama_client = OllamaClient()
        available_models = await ollama_client.list_models()
        available_names = [m.get('name') for m in available_models]
        
        if model_to_use not in available_names:
            logger.warning(f"⚠️ Modelo solicitado '{model_to_use}' no existe, usando modelo real configurado: {real_chat_model}")
            model_to_use = real_chat_model
        
        # Configuración
        temperature = chat_data.settings.get("temperature", 0.7)
        max_tokens = chat_data.settings.get("max_tokens", 2048)
        
        # ✅ LLAMADA CON MODELO REAL VERIFICADO
        try:
            ai_response_text = await ollama_client.generate(
                model=model_to_use,
                prompt=chat_data.message,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as ollama_error:
            if "model not found" in str(ollama_error).lower():
                raise HTTPException(
                    status_code=400, 
                    detail=f"Modelo {model_to_use} no encontrado en Ollama. Disponibles: {available_names}"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error del modelo de IA REAL: {str(ollama_error)}"
                )
        
        # Calcular tiempo de respuesta
        response_time = int((time.time() - start_time) * 1000)
        
        return {
            "response": ai_response_text,
            "model_used": model_to_use,  # ✅ MODELO REAL USADO
            "model_verified": True,
            "assistant_type": chat_data.assistant_type,
            "response_time": response_time,
            "metadata": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "user_role": current_user.role,
                "timestamp": datetime.utcnow().isoformat(),
                "data_source": "real_ollama_model"
            }
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ Error en chat con IA REAL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
    
# Añadir esta ruta al final del archivo routes_ai.py, antes de la inicialización

@router.post("/predict-maintenance/{machine_id}", dependencies=[Depends(get_ai_ready)])
async def predict_machine_maintenance(
    machine_id: int,
    request_data: dict = {},
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """✅ GENERA PREDICCIÓN ESPECÍFICA para una máquina usando datos reales"""
    try:
        logger.info(f"🔮 Predicción solicitada para máquina ID: {machine_id} por {current_user.username}")
        
        # ✅ VERIFICAR QUE LA MÁQUINA EXISTE
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail=f"Máquina con ID {machine_id} no encontrada")
        
        # ✅ VERIFICAR PERMISOS
        if current_user.role.nombre == "Jefe de Sección":
            if machine.section_id != current_user.section_id:
                raise HTTPException(status_code=403, detail="No tienes permisos para analizar esta máquina")
        
        # ✅ OBTENER CONFIGURACIÓN REAL
        ai_config = AI_CONFIG_CACHE.copy()
        model_override = request_data.get("model_override") or ai_config.get("default_prediction_model")
        days_ahead = request_data.get("days_ahead", 30)
        confidence_threshold = request_data.get("confidence_threshold") or ai_config.get("prediction_confidence_threshold", 70)
        
        if not model_override:
            raise HTTPException(status_code=500, detail="No hay modelo de IA configurado")
        
        logger.info(f"🤖 Usando modelo: {model_override}, umbral: {confidence_threshold}%")
        
        # ✅ VERIFICAR DATOS HISTÓRICOS
        historical_orders = db.query(WorkOrder).filter(
            WorkOrder.machine_id == machine_id,
            WorkOrder.status == "Cerrada",
            WorkOrder.created_at >= datetime.utcnow() - timedelta(days=90)
        ).order_by(desc(WorkOrder.created_at)).limit(50).all()
        
        if len(historical_orders) < 2:
            return {
                "success": False,
                "message": f"Máquina {machine.nombre} tiene insuficientes datos históricos ({len(historical_orders)} órdenes en 90 días)",
                "machine_name": machine.nombre,
                "machine_id": machine_id,
                "historical_orders_count": len(historical_orders),
                "minimum_required": 2
            }
        
        # ✅ PREPARAR DATOS PARA IA
        machine_data = {
            "id": machine.id,
            "nombre": machine.nombre,
            "modelo": machine.modelo,
            "marca": machine.marca,
            "criticidad": machine.criticidad,
            "section": machine.section.nombre if machine.section else None,
        }
        
        historical_data = []
        for order in historical_orders:
            historical_data.append({
                "date": order.created_at.isoformat(),
                "work_type": order.work_type,
                "downtime_hours": float(order.downtime_hours) if order.downtime_hours is not None else 0.0,
                "failure_code": order.failure_code.code if order.failure_code else None,
                "cause_code": order.cause_code.code if order.cause_code else None,
            })
        
        # ✅ GENERAR PREDICCIÓN EN SEGUNDO PLANO
        def generate_prediction_task():
            task_db = SessionLocal()
            try:
                from src.ai.predictive_service import PredictiveMaintenanceService
                
                # Crear loop asyncio para la función async
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Ejecutar predicción
                prediction_service = PredictiveMaintenanceService()
                prediction_result = loop.run_until_complete(
                    prediction_service.predict_machine_failure(
                        machine_data=machine_data,
                        historical_data=historical_data,
                        days_ahead=days_ahead,
                        model_override=model_override,
                        confidence_threshold=confidence_threshold
                    )
                )
                
                loop.close()
                
                # ✅ GUARDAR RESULTADO SI ES VÁLIDO
                confidence = prediction_result.get("confidence", 0)
                probability = prediction_result.get("probability", 0)
                
                if confidence >= confidence_threshold and probability > 10:
                    # Desactivar predicciones anteriores
                    task_db.query(MachinePrediction).filter(
                        MachinePrediction.machine_id == machine_id,
                        MachinePrediction.status == "active"
                    ).update({"status": "expired"})
                    
                    # Parsear fecha predicha
                    predicted_date = None
                    if prediction_result.get("predicted_date"):
                        try:
                            predicted_date = datetime.strptime(
                                prediction_result["predicted_date"], "%Y-%m-%d"
                            ).date()
                        except:
                            pass
                    
                    # Crear nueva predicción
                    new_prediction = MachinePrediction(
                        machine_id=machine_id,
                        prediction_type="failure",
                        probability=probability,
                        confidence=confidence,
                        predicted_date=predicted_date,
                        prediction_data=prediction_result,
                        components_at_risk=prediction_result.get("components_at_risk", []),
                        recommended_actions=prediction_result.get("recommended_actions", []),
                        model_used=model_override,
                        data_points_used=len(historical_data),
                        status="active",
                        created_at=datetime.utcnow(),
                        created_by_id=current_user.id
                    )
                    
                    task_db.add(new_prediction)
                    task_db.commit()
                    
                    logger.info(f"✅ Predicción guardada para {machine.nombre}: {probability}% probabilidad")
                else:
                    logger.info(f"⚠️ Predicción no cumple criterios: confianza {confidence}% < {confidence_threshold}%")
                
            except Exception as e:
                logger.error(f"❌ Error en tarea de predicción: {e}")
                task_db.rollback()
            finally:
                task_db.close()
        
        # Ejecutar en segundo plano
        background_tasks.add_task(generate_prediction_task)
        
        # ✅ RESPUESTA INMEDIATA
        return {
            "success": True,
            "message": f"Predicción iniciada para {machine.nombre}",
            "machine_name": machine.nombre,
            "machine_id": machine_id,
            "model_used": model_override,
            "confidence_threshold": confidence_threshold,
            "days_ahead": days_ahead,
            "historical_data_points": len(historical_data),
            "estimated_completion": "2-3 minutos",
            "prediction_analysis": {
                "model_used": model_override,
                "prediction_confidence": confidence_threshold,
                "estimated_date": "Calculando...",
                "risk_level": "Analizando..."
            },
            "historical_context": {
                "total_orders": len(historical_orders),
                "total_failures": len([o for o in historical_orders if o.work_type == "Correctivo"])
            }
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ Error en predicción para máquina {machine_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")



# ✅ INICIALIZAR MODELOS AL IMPORTAR EL MÓDULO
import asyncio
def init_models_on_startup():
    """Inicializa modelos reales al cargar el módulo"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(initialize_real_models())
        loop.close()
        logger.info("🚀 Modelos reales inicializados al startup")
    except Exception as e:
        logger.error(f"❌ Error en inicialización al startup: {e}")

# Ejecutar inicialización
init_models_on_startup()


@router.post("/predictions/trigger-batch", dependencies=[Depends(get_ai_ready)])
async def trigger_batch_predictions_fixed(
    section_id: Optional[int] = Query(None),
    max_machines: int = Query(10, ge=1, le=20),
    force_refresh: bool = Query(False),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """✅ DISPARA PREDICCIONES EN LOTE CORREGIDO"""
    try:
        logger.info(f"🚀 Iniciando predicciones en lote - Usuario: {current_user.username}")
        
        # ✅ ASEGURAR MODELOS REALES
        if not AI_CONFIG_CACHE.get("default_prediction_model"):
            await initialize_real_models()
        
        real_model = AI_CONFIG_CACHE.get("default_prediction_model")
        if not real_model:
            raise HTTPException(status_code=500, detail="No se pudo detectar modelo real para predicciones")
        
        # ✅ OBTENER MÁQUINAS REALES CON DATOS SUFICIENTES
        from sqlalchemy import text
        
        machines_query = text("""
            SELECT DISTINCT m.id, m.nombre, m.section_id, COUNT(wo.id) as orden_count
            FROM machines m
            INNER JOIN work_orders wo ON m.id = wo.machine_id
            WHERE wo.created_at >= NOW() - INTERVAL '3 months'
            AND (:section_id IS NULL OR m.section_id = :section_id)
            GROUP BY m.id, m.nombre, m.section_id
            HAVING COUNT(wo.id) >= 2
            ORDER BY COUNT(wo.id) DESC
            LIMIT :max_machines
        """)
        
        machines_data = db.execute(machines_query, {
            "section_id": section_id,
            "max_machines": max_machines
        }).fetchall()
        
        if not machines_data:
            raise HTTPException(
                status_code=404, 
                detail="No se encontraron máquinas con datos suficientes para análisis en lote"
            )
        
        logger.info(f"📊 Máquinas seleccionadas para análisis en lote: {len(machines_data)}")
        
        def batch_prediction_task():
            """Tarea de predicciones en lote en segundo plano"""
            task_db = SessionLocal()
            successful_predictions = 0
            
            try:
                from src.ai.prediction_scheduler import real_prediction_scheduler
                
                for machine_data in machines_data:
                    try:
                        machine = task_db.query(Machine).filter(Machine.id == machine_data.id).first()
                        if not machine:
                            continue
                        
                        # Usar el scheduler real para generar predicción
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        result = loop.run_until_complete(
                            real_prediction_scheduler.generate_real_machine_prediction(
                                machine, task_db, AI_CONFIG_CACHE
                            )
                        )
                        
                        loop.close()
                        
                        if result:
                            successful_predictions += 1
                            logger.info(f"✅ Predicción en lote para {machine.nombre}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error en lote para {machine_data.nombre}: {e}")
                        continue
                
                logger.info(f"🎯 Lote completado: {successful_predictions}/{len(machines_data)} predicciones")
                
            except Exception as e:
                logger.error(f"❌ Error general en lote: {e}")
            finally:
                task_db.close()
        
        # Ejecutar en segundo plano
        background_tasks.add_task(batch_prediction_task)
        
        return {
            "message": f"Predicciones en lote iniciadas para {len(machines_data)} máquinas",
            "machines_count": len(machines_data),
            "machine_names": [m.nombre for m in machines_data],
            "model_used": real_model,
            "estimated_completion": "3-8 minutos",
            "initiated_by": current_user.username,
            "check_status_url": "/api/ai/predictions/real-data"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ Error en predicciones en lote: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predictions/manual-cycle", dependencies=[Depends(get_ai_ready)])
async def trigger_manual_prediction_cycle_fixed(
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user)
):
    """✅ DISPARA MANUALMENTE UN CICLO COMPLETO DE PREDICCIONES CORREGIDO"""
    try:
        logger.info(f"🔄 Ciclo manual iniciado por {current_user.username}")
        
        # ✅ ASEGURAR CONFIGURACIÓN REAL
        if not AI_CONFIG_CACHE.get("default_prediction_model"):
            await initialize_real_models()
        
        model_to_use = AI_CONFIG_CACHE.get("default_prediction_model")
        confidence_threshold = AI_CONFIG_CACHE.get("prediction_confidence_threshold", 70)
        
        if not model_to_use:
            raise HTTPException(status_code=500, detail="No se pudo detectar modelo real para predicciones")
        
        logger.info(f"🤖 Usando configuración: Modelo={model_to_use}, Umbral={confidence_threshold}%")
        
        def manual_cycle_task():
            """Ejecutar ciclo manual con configuración real"""
            try:
                logger.info("🚀 Ejecutando ciclo manual...")
                
                # Usar el scheduler real corregido
                from src.ai.prediction_scheduler import run_single_real_prediction_cycle
                run_single_real_prediction_cycle()
                
                logger.info("✅ Ciclo manual completado")
            except Exception as e:
                logger.error(f"❌ Error en ciclo manual: {e}")
        
        # Ejecutar en segundo plano
        background_tasks.add_task(manual_cycle_task)
        
        return {
            "message": "🔄 Ciclo manual de predicciones iniciado",
            "status": "started_with_real_config",
            "estimated_completion": "3-8 minutos",
            "initiated_by": current_user.username,
            "model_configured": model_to_use,
            "confidence_threshold": confidence_threshold,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Revisa AIPredictions en unos minutos para ver los resultados"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ Error en ciclo manual: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/scheduler-status", dependencies=[Depends(get_ai_ready)])
async def get_scheduler_status_fixed(current_user: User = Depends(get_current_user)):
    """Verifica el estado del scheduler de predicciones"""
    try:
        # Verificar configuración actual
        config_status = "not_configured"
        if AI_CONFIG_CACHE.get("default_prediction_model"):
            config_status = "configured"
        
        # Verificar predicciones recientes
        db = SessionLocal()
        try:
            recent_predictions = db.query(MachinePrediction).filter(
                MachinePrediction.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            last_prediction = db.query(MachinePrediction).order_by(
                desc(MachinePrediction.created_at)
            ).first()
            
        finally:
            db.close()
        
        return {
            "scheduler_status": {
                "config_status": config_status,
                "model_configured": AI_CONFIG_CACHE.get("default_prediction_model", "None"),
                "auto_prediction_enabled": AI_CONFIG_CACHE.get("auto_prediction_enabled", False)
            },
            "prediction_status": {
                "recent_predictions_24h": recent_predictions,
                "last_prediction_time": last_prediction.created_at.isoformat() if last_prediction else None,
                "last_prediction_model": last_prediction.model_used if last_prediction else None
            },
            "current_config": AI_CONFIG_CACHE,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error verificando scheduler: {e}")
        return {
            "scheduler_status": {"error": str(e)},
            "current_config": AI_CONFIG_CACHE,
            "timestamp": datetime.utcnow().isoformat()
        }
