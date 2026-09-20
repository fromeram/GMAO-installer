# routes_ai_dashboard.py

# --- Imports Estándar ---
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# --- Imports de FastAPI ---
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

# --- Imports de SQLAlchemy ---
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

# --- Dependencias de la Aplicación ---
from src.auth import get_admin_user, get_current_user
from src.database import get_db

# --- Modelos de la Base de Datos ---
from src.models.ai_prediction import AIModelPerformance, MachinePrediction
from src.models.machine import Machine
from src.models.user import User
from src.models.work_order import WorkOrder

# --- Servicios de IA ---
from src.ai.predictive_service import PredictiveMaintenanceService

# --- Definición del Logger ---
logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Dashboard"])


# --- Funciones Auxiliares (Helpers) ---

def get_ai_config():
    """✅ Obtiene la configuración REAL actual de IA desde routes_ai."""
    try:
        from .routes_ai import AI_CONFIG_CACHE
        config = AI_CONFIG_CACHE.copy()
        
        # ✅ VERIFICAR QUE HAY MODELO CONFIGURADO
        if not config.get("default_prediction_model"):
            logger.warning("⚠️ No hay modelo de predicción configurado")
            config["default_prediction_model"] = "Not Configured"
        
        return config
    except ImportError:
        logger.error("❌ No se pudo importar configuración real desde routes_ai")
        return {
            "default_prediction_model": "Import Error",
            "prediction_confidence_threshold": 70,
            "default_chat_model": "Not Available"
        }


async def perform_machine_analysis(machine_id: int, user_id: int, db_session: Session):
    """✅ ANÁLISIS REAL DE MÁQUINA usando configuración y modelo REAL"""
    try:
        # ✅ OBTENER CONFIGURACIÓN REAL desde routes_ai
        try:
            from .routes_ai import AI_CONFIG_CACHE
            ai_config = AI_CONFIG_CACHE.copy()
        except ImportError:
            logger.error("❌ No se pudo importar configuración real")
            ai_config = {
                "default_prediction_model": None,
                "prediction_confidence_threshold": 70
            }
        
        prediction_model = ai_config.get("default_prediction_model")
        confidence_threshold = ai_config.get("prediction_confidence_threshold", 70)
        
        if not prediction_model:
            logger.error("❌ No hay modelo real configurado para análisis")
            return
        
        logger.info(f"🔮 Realizando análisis REAL con modelo: {prediction_model}, umbral: {confidence_threshold}%")
        
        # ✅ VERIFICAR QUE LA MÁQUINA EXISTE
        machine = db_session.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            logger.error(f"❌ Máquina {machine_id} no encontrada para análisis")
            return
        
        # ✅ VERIFICAR QUE TIENE DATOS SUFICIENTES
        order_count = db_session.query(func.count(WorkOrder.id)).filter(
            WorkOrder.machine_id == machine_id,
            WorkOrder.created_at >= datetime.utcnow() - timedelta(days=90)
        ).scalar()
        
        if order_count < 2:
            logger.warning(f"⚠️ Máquina {machine.nombre} tiene insuficientes datos ({order_count} órdenes en 90 días)")
            return
        
        # ✅ PREPARAR DATOS REALES de la máquina
        machine_data = {
            "id": machine.id,
            "nombre": machine.nombre,
            "modelo": machine.modelo,
            "marca": machine.marca,
            "criticidad": machine.criticidad,
            "section": machine.section.nombre if machine.section else None,
        }
        
        # ✅ OBTENER HISTORIAL REAL de órdenes
        historical_orders = (
            db_session.query(WorkOrder)
            .filter(WorkOrder.machine_id == machine_id, WorkOrder.status == "Cerrada")
            .order_by(desc(WorkOrder.created_at))
            .limit(50)
            .all()
        )
        
        historical_data = []
        for order in historical_orders:
            historical_data.append({
                "date": order.created_at.isoformat(),
                "work_type": order.work_type,
                "downtime_hours": order.downtime_hours,
                "failure_code": order.failure_code.code if order.failure_code else None,
                "cause_code": order.cause_code.code if order.cause_code else None,
            })
        
        logger.info(f"📊 Analizando {len(historical_data)} órdenes históricas reales de {machine.nombre}")
        
        # ✅ USAR SERVICIO REAL DE IA
        ai_service = PredictiveMaintenanceService()
        
        # ✅ GENERAR PREDICCIÓN con modelo REAL configurado
        prediction_result = await ai_service.predict_machine_failure(
            machine_data=machine_data,
            historical_data=historical_data,
            days_ahead=30,
            model_override=prediction_model,  # ✅ MODELO REAL
            confidence_threshold=confidence_threshold,  # ✅ UMBRAL REAL
        )
        
        # ✅ AÑADIR METADATOS REALES
        prediction_result["model_used"] = prediction_model
        prediction_result["confidence_threshold_used"] = confidence_threshold
        prediction_result["analysis_type"] = "real_model_analysis"
        prediction_result["data_points_analyzed"] = len(historical_data)
        
        # ✅ VALIDAR RESULTADO
        confidence = prediction_result.get("confidence", 0)
        probability = prediction_result.get("probability", 0)
        
        logger.info(f"📈 Resultado REAL para {machine.nombre}: Probabilidad {probability}%, Confianza {confidence}%")
        
        # ✅ GUARDAR SOLO SI CUMPLE CRITERIOS REALES
        if confidence >= confidence_threshold and probability > 5:
            
            predicted_date = None
            if prediction_result.get("predicted_date"):
                try:
                    predicted_date = datetime.strptime(prediction_result["predicted_date"], "%Y-%m-%d").date()
                except Exception as e:
                    logger.warning(f"⚠️ Error parseando fecha predicha: {e}")
            
            # ✅ DESACTIVAR predicciones anteriores
            db_session.query(MachinePrediction).filter(
                MachinePrediction.machine_id == machine_id,
                MachinePrediction.status == "active"
            ).update({"status": "superseded"})
            
            # ✅ CREAR PREDICCIÓN REAL
            prediction = MachinePrediction(
                machine_id=machine_id,
                prediction_type="failure",
                probability=probability,
                confidence=confidence,
                predicted_date=predicted_date,
                prediction_data=prediction_result,
                components_at_risk=prediction_result.get("components_at_risk", []),
                recommended_actions=prediction_result.get("recommended_actions", []),
                model_used=prediction_model,  # ✅ MODELO REAL USADO
                data_points_used=len(historical_data),
                status="active",
                created_at=datetime.utcnow()
            )
            
            db_session.add(prediction)
            db_session.commit()
            
            logger.info(f"✅ Análisis REAL completado y guardado para {machine.nombre} usando modelo {prediction_model}")
        else:
            logger.info(f"⚠️ Análisis para {machine.nombre} no cumple criterios: confianza {confidence}% < {confidence_threshold}%")
        
    except Exception as e:
        logger.error(f"❌ Error en análisis REAL para máquina {machine_id}: {e}", exc_info=True)
        db_session.rollback()



async def calculate_current_ai_performance(db: Session, days: int) -> Dict:
    """Calcula métricas de rendimiento actuales."""
    # Implementación de la función
    pass


async def generate_ai_improvement_recommendations(model_performance: Dict) -> List[str]:
    """Genera recomendaciones para mejorar el rendimiento de IA."""
    # Implementación de la función
    pass


# --- Endpoints del Router ---

@router.get("/overview")
async def get_ai_dashboard_overview(
    section_id: Optional[int] = Query(None),
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard principal de IA con métricas y predicciones."""
    try:
        # Obtener máquinas del ámbito del usuario
        machines_query = db.query(Machine)
        if current_user.role.nombre == "Jefe de Sección":
            machines_query = machines_query.filter(Machine.section_id == current_user.section_id)
        elif section_id:
            machines_query = machines_query.filter(Machine.section_id == section_id)
        machines = machines_query.all()

        # Predicciones recientes
        recent_predictions = (
            db.query(MachinePrediction)
            .filter(
                MachinePrediction.created_at >= datetime.utcnow() - timedelta(days=days),
                MachinePrediction.status == "active",
            )
            .order_by(desc(MachinePrediction.probability))
            .limit(10)
            .all()
        )

        # Máquinas en riesgo
        high_risk_machines = [
            pred for pred in recent_predictions if pred.probability and pred.probability > 70
        ]

        # Predicciones por máquina crítica
        critical_machines = [m for m in machines if m.criticidad == "Alta"]
        critical_predictions = []
        for machine in critical_machines[:5]:  # Top 5
            latest_prediction = (
                db.query(MachinePrediction)
                .filter(
                    MachinePrediction.machine_id == machine.id,
                    MachinePrediction.status == "active",
                )
                .order_by(desc(MachinePrediction.created_at))
                .first()
            )
            if latest_prediction:
                critical_predictions.append({
                    "machine": {
                        "id": machine.id,
                        "name": machine.nombre,
                        "section": machine.section.nombre if machine.section else None,
                    },
                    "prediction": {
                        "probability": latest_prediction.probability,
                        "predicted_date": latest_prediction.predicted_date.isoformat()
                        if latest_prediction.predicted_date
                        else None,
                        "confidence": latest_prediction.confidence,
                        "components_at_risk": latest_prediction.components_at_risk,
                    },
                })

        # Estadísticas de rendimiento de IA
        total_predictions = db.query(func.count(MachinePrediction.id)).scalar()
        accurate_predictions = (
            db.query(func.count(MachinePrediction.id))
            .filter(MachinePrediction.actual_outcome == "correct")
            .scalar()
        )
        ai_accuracy = (accurate_predictions / total_predictions * 100) if total_predictions > 0 else 0

        # Tendencia de predicciones por día
        daily_predictions = []
        for i in range(days):
            day = datetime.utcnow().date() - timedelta(days=i)
            day_count = (
                db.query(func.count(MachinePrediction.id))
                .filter(func.date(MachinePrediction.created_at) == day)
                .scalar()
            )
            daily_predictions.append({"date": day.isoformat(), "predictions_count": day_count})

        # Próximas acciones recomendadas
        upcoming_actions = []
        for pred in recent_predictions[:5]:
            if pred.recommended_actions:
                upcoming_actions.append({
                    "machine_id": pred.machine_id,
                    "machine_name": pred.machine.nombre if pred.machine else "N/A",
                    "actions": pred.recommended_actions,
                    "priority": pred.prediction_data.get("severity", "medium")
                    if pred.prediction_data
                    else "medium",
                    "due_date": pred.predicted_date.isoformat() if pred.predicted_date else None,
                })

        return {
            "overview": {
                "total_machines_monitored": len(machines),
                "high_risk_machines": len(high_risk_machines),
                "critical_machines_monitored": len(critical_machines),
                "ai_accuracy_percent": round(ai_accuracy, 1),
                "predictions_last_week": len(recent_predictions),
                "generated_at": datetime.utcnow().isoformat(),
            },
            "high_risk_alerts": [
                {
                    "machine_id": pred.machine_id,
                    "machine_name": pred.machine.nombre if pred.machine else "N/A",
                    "probability": pred.probability,
                    "predicted_date": pred.predicted_date.isoformat()
                    if pred.predicted_date
                    else None,
                    "confidence": pred.confidence,
                    "days_until_failure": (pred.predicted_date.date() - datetime.utcnow().date()).days
                    if pred.predicted_date
                    else None,
                }
                for pred in high_risk_machines
            ],
            "critical_machines_status": critical_predictions,
            "prediction_trends": {
                "daily_predictions": list(reversed(daily_predictions)),
                "accuracy_trend": "Por implementar",
                "pattern_detection": "Por implementar",
            },
            "recommended_actions": upcoming_actions,
            "ai_performance": {
                "total_predictions": total_predictions,
                "accurate_predictions": accurate_predictions,
                "accuracy_rate": ai_accuracy,
                "models_active": ["llama3"],
                "last_model_update": "2024-01-01",
            },
        }

    except Exception as e:
        logger.error(f"Error en AI dashboard overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/machine-risk-matrix")
async def get_machine_risk_matrix(
    section_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Matriz de riesgo de máquinas basada en predicciones de IA."""
    try:
        machines_query = db.query(Machine).options(joinedload(Machine.section))
        if current_user.role.nombre == "Jefe de Sección":
            machines_query = machines_query.filter(Machine.section_id == current_user.section_id)
        elif section_id:
            machines_query = machines_query.filter(Machine.section_id == section_id)
        machines = machines_query.all()

        risk_matrix = []
        for machine in machines:
            latest_prediction = (
                db.query(MachinePrediction)
                .filter(
                    MachinePrediction.machine_id == machine.id,
                    MachinePrediction.status == "active",
                )
                .order_by(desc(MachinePrediction.created_at))
                .first()
            )

            recent_orders = (
                db.query(WorkOrder)
                .filter(
                    WorkOrder.machine_id == machine.id,
                    WorkOrder.created_at >= datetime.utcnow() - timedelta(days=90),
                )
                .all()
            )

            failure_count = len([o for o in recent_orders if o.work_type == "Correctivo"])
            avg_downtime = (
                sum(o.downtime_hours or 0 for o in recent_orders) / len(recent_orders)
                if recent_orders
                else 0
            )

            if latest_prediction and latest_prediction.probability:
                probability = latest_prediction.probability
                if probability >= 80:
                    risk_level = "critical"
                elif probability >= 60:
                    risk_level = "high"
                elif probability >= 40:
                    risk_level = "medium"
                else:
                    risk_level = "low"
            else:
                if failure_count >= 3:
                    risk_level = "high"
                elif failure_count >= 1:
                    risk_level = "medium"
                else:
                    risk_level = "low"

            risk_matrix.append({
                "machine_id": machine.id,
                "machine_name": machine.nombre,
                "section": machine.section.nombre if machine.section else "N/A",
                "criticality": machine.criticidad or "Media",
                "risk_level": risk_level,
                "failure_probability": latest_prediction.probability if latest_prediction else None,
                "confidence": latest_prediction.confidence if latest_prediction else None,
                "predicted_date": latest_prediction.predicted_date.isoformat()
                if latest_prediction and latest_prediction.predicted_date
                else None,
                "recent_failures": failure_count,
                "avg_downtime_hours": round(avg_downtime, 2),
                "components_at_risk": latest_prediction.components_at_risk if latest_prediction else [],
                "last_prediction": latest_prediction.created_at.isoformat() if latest_prediction else None,
            })

        risk_stats = {
            "critical": len([m for m in risk_matrix if m["risk_level"] == "critical"]),
            "high": len([m for m in risk_matrix if m["risk_level"] == "high"]),
            "medium": len([m for m in risk_matrix if m["risk_level"] == "medium"]),
            "low": len([m for m in risk_matrix if m["risk_level"] == "low"]),
        }

        return {
            "risk_matrix": sorted(
                risk_matrix, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}[x["risk_level"]]
            ),
            "risk_statistics": risk_stats,
            "total_machines": len(risk_matrix),
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error en machine risk matrix: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/predictions/history")
async def get_predictions_history(
    machine_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    prediction_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Historial de predicciones de IA con validación de precisión."""
    try:
        ai_config = get_ai_config()
        query = (
            db.query(MachinePrediction)
            .options(
                joinedload(MachinePrediction.machine),
                joinedload(MachinePrediction.created_by),
            )
            .filter(MachinePrediction.created_at >= datetime.utcnow() - timedelta(days=days))
        )

        if machine_id:
            query = query.filter(MachinePrediction.machine_id == machine_id)
        if prediction_type:
            query = query.filter(MachinePrediction.prediction_type == prediction_type)
        if current_user.role.nombre == "Jefe de Sección":
            query = query.join(Machine).filter(Machine.section_id == current_user.section_id)

        predictions = query.order_by(desc(MachinePrediction.created_at)).all()
        
        history = []
        needs_commit = False
        for pred in predictions:
            actual_outcome = pred.actual_outcome
            if pred.predicted_date and pred.predicted_date.date() < datetime.utcnow().date() and not actual_outcome:
                start_check = pred.predicted_date.date() - timedelta(days=3)
                end_check = pred.predicted_date.date() + timedelta(days=3)
                
                actual_failure = db.query(WorkOrder).filter(
                    WorkOrder.machine_id == pred.machine_id,
                    WorkOrder.work_type == "Correctivo",
                    func.date(WorkOrder.created_at).between(start_check, end_check),
                ).first()
                
                actual_outcome = "correct" if actual_failure else "false_positive"
                pred.actual_outcome = actual_outcome
                pred.outcome_date = actual_failure.created_at if actual_failure else datetime.utcnow()
                needs_commit = True

            history.append({
                "id": pred.id,
                "machine": {
                    "id": pred.machine.id,
                    "name": pred.machine.nombre,
                    "section": pred.machine.section.nombre if pred.machine.section else None,
                } if pred.machine else None,
                "prediction_type": pred.prediction_type,
                "probability": pred.probability,
                "confidence": pred.confidence,
                "predicted_date": pred.predicted_date.isoformat() if pred.predicted_date else None,
                "components_at_risk": pred.components_at_risk,
                "recommended_actions": pred.recommended_actions if isinstance(pred.recommended_actions, list) else [],
                "model_used": pred.model_used or ai_config.get("default_prediction_model", "N/A"),
                "created_at": pred.created_at.isoformat(),
                "created_by": pred.created_by.username if pred.created_by else None,
                "actual_outcome": actual_outcome,
                "outcome_date": pred.outcome_date.isoformat() if pred.outcome_date else None,
                "status": pred.status,
            })

        completed_predictions = [h for h in history if h["actual_outcome"]]
        correct_predictions = [h for h in completed_predictions if h["actual_outcome"] == "correct"]
        accuracy_stats = {
            "total_predictions": len(history),
            "completed_predictions": len(completed_predictions),
            "correct_predictions": len(correct_predictions),
            "accuracy_rate": (len(correct_predictions) / len(completed_predictions) * 100) if completed_predictions else 0,
            "false_positives": len([h for h in completed_predictions if h["actual_outcome"] == "false_positive"]),
            "pending_validation": len(history) - len(completed_predictions),
        }

        if needs_commit:
            db.commit()

        return {
            "predictions_history": history,
            "accuracy_statistics": accuracy_stats,
            "current_model_config": ai_config.get("default_prediction_model", "N/A"),
            "period_analyzed": f"{days} días",
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error en predictions history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/trigger-analysis/{machine_id}")
async def trigger_machine_analysis(
    machine_id: int,
    background_tasks: BackgroundTasks,
    force_refresh: bool = Query(False, description="Forzar nuevo análisis"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dispara análisis de IA para una máquina específica."""
    try:
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail="Máquina no encontrada")

        can_analyze = (
            current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
            or (current_user.role.nombre == "Jefe de Sección" and machine.section_id == current_user.section_id)
        )
        if not can_analyze:
            raise HTTPException(status_code=403, detail="No tienes permisos para analizar esta máquina")

        ai_config = get_ai_config()
        prediction_model = ai_config.get("default_prediction_model", "deepseek-r1:8b")
        
        recent_analysis = db.query(MachinePrediction).filter(
            MachinePrediction.machine_id == machine_id,
            MachinePrediction.created_at >= datetime.utcnow() - timedelta(hours=4),
        ).first()

        if recent_analysis and not force_refresh:
            return {
                "message": "Análisis reciente encontrado",
                "existing_prediction": {
                    "id": recent_analysis.id,
                    "probability": recent_analysis.probability,
                    "confidence": recent_analysis.confidence,
                    "model_used": recent_analysis.model_used,
                    "created_at": recent_analysis.created_at.isoformat(),
                },
                "use_force_refresh": "Usa force_refresh=true para generar nuevo análisis",
                "current_model_config": prediction_model,
            }

        background_tasks.add_task(
            perform_machine_analysis,
            machine_id=machine_id,
            user_id=current_user.id,
            db_session=db,
        )

        return {
            "message": f"Análisis de IA iniciado para máquina {machine.nombre}",
            "machine_id": machine_id,
            "model_to_use": prediction_model,
            "estimated_completion": "2-3 minutos",
            "check_status_url": f"/api/ai/dashboard/analysis-status/{machine_id}",
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error iniciando análisis para máquina {machine_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/analysis-status/{machine_id}")
async def get_analysis_status(
    machine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtiene el estado del análisis más reciente de una máquina."""
    try:
        latest_prediction = (
            db.query(MachinePrediction)
            .filter(MachinePrediction.machine_id == machine_id)
            .order_by(desc(MachinePrediction.created_at))
            .first()
        )

        if not latest_prediction:
            return {
                "status": "no_analysis",
                "message": "No se ha realizado análisis para esta máquina",
            }

        time_since_analysis = datetime.utcnow() - latest_prediction.created_at
        
        if time_since_analysis.total_seconds() < 300:
            status = "recent"
        elif time_since_analysis.total_seconds() < 3600:
            status = "current"
        elif time_since_analysis.total_seconds() < 86400:
            status = "valid"
        else:
            status = "outdated"

        return {
            "status": status,
            "prediction": {
                "id": latest_prediction.id,
                "probability": latest_prediction.probability,
                "confidence": latest_prediction.confidence,
                "predicted_date": latest_prediction.predicted_date.isoformat()
                if latest_prediction.predicted_date
                else None,
                "components_at_risk": latest_prediction.components_at_risk,
                "recommended_actions": latest_prediction.recommended_actions,
                "created_at": latest_prediction.created_at.isoformat(),
                "age_minutes": int(time_since_analysis.total_seconds() / 60),
            },
            "machine_id": machine_id,
        }

    except Exception as e:
        logger.error(f"Error obteniendo estado de análisis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/ai-performance")
async def get_ai_performance_metrics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Métricas detalladas de rendimiento de los modelos de IA."""
    try:
        performance_records = (
            db.query(AIModelPerformance)
            .filter(AIModelPerformance.evaluation_period_end >= datetime.utcnow() - timedelta(days=days))
            .order_by(desc(AIModelPerformance.last_updated))
            .all()
        )

        if not performance_records:
            current_metrics = await calculate_current_ai_performance(db, days)
        else:
            current_metrics = {
                "accuracy": performance_records[0].accuracy,
                "precision": performance_records[0].precision_score,
                "recall": performance_records[0].recall_score,
                "f1_score": performance_records[0].f1_score,
            }

        all_predictions = db.query(MachinePrediction).filter(
            MachinePrediction.created_at >= datetime.utcnow() - timedelta(days=days)
        ).all()

        model_performance = {}
        for pred in all_predictions:
            model = pred.model_used or "unknown"
            if model not in model_performance:
                model_performance[model] = {
                    "total_predictions": 0,
                    "correct_predictions": 0,
                    "false_positives": 0,
                    "confidence_sum": 0,
                    "high_confidence_predictions": 0,
                }
            
            model_performance[model]["total_predictions"] += 1
            model_performance[model]["confidence_sum"] += pred.confidence or 0
            
            if pred.confidence and pred.confidence > 80:
                model_performance[model]["high_confidence_predictions"] += 1
            
            if pred.actual_outcome == "correct":
                model_performance[model]["correct_predictions"] += 1
            elif pred.actual_outcome == "false_positive":
                model_performance[model]["false_positives"] += 1

        for model, stats in model_performance.items():
            total = stats["total_predictions"]
            stats["accuracy_rate"] = (stats["correct_predictions"] / total * 100) if total > 0 else 0
            stats["false_positive_rate"] = (stats["false_positives"] / total * 100) if total > 0 else 0
            stats["avg_confidence"] = (stats["confidence_sum"] / total) if total > 0 else 0
            stats["high_confidence_rate"] = (
                stats["high_confidence_predictions"] / total * 100
            ) if total > 0 else 0

        daily_performance = []
        for i in range(min(days, 30)):
            day = datetime.utcnow().date() - timedelta(days=i)
            day_predictions = [p for p in all_predictions if p.created_at.date() == day]
            
            day_correct = len([p for p in day_predictions if p.actual_outcome == "correct"])
            day_total = len(day_predictions)
            day_accuracy = (day_correct / day_total * 100) if day_total > 0 else 0
            
            daily_performance.append({
                "date": day.isoformat(),
                "total_predictions": day_total,
                "correct_predictions": day_correct,
                "accuracy": round(day_accuracy, 1),
            })

        return {
            "current_metrics": {
                "overall_accuracy": round(current_metrics.get("accuracy", 0), 2),
                "precision": round(current_metrics.get("precision", 0), 2),
                "recall": round(current_metrics.get("recall", 0), 2),
                "f1_score": round(current_metrics.get("f1_score", 0), 2),
            },
            "model_performance": model_performance,
            "daily_trends": list(reversed(daily_performance)),
            "summary": {
                "total_predictions_analyzed": len(all_predictions),
                "predictions_with_outcome": len([p for p in all_predictions if p.actual_outcome]),
                "evaluation_period_days": days,
                "last_updated": datetime.utcnow().isoformat(),
            },
            "recommendations": await generate_ai_improvement_recommendations(model_performance),
        }

    except Exception as e:
        logger.error(f"Error obteniendo métricas de IA: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")