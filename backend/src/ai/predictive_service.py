# ai/predictive_service.py - VERSIÓN FINAL CORREGIDA Y OPTIMIZADA
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from .ollama_client import OllamaClient
import logging
import asyncio

logger = logging.getLogger(__name__)

class PredictiveMaintenanceService:
    """Servicio principal para mantenimiento predictivo con IA"""
    
    def __init__(self, ollama_url: str = "http://192.168.1.62:11434"):
        self.ollama_client = OllamaClient(ollama_url)
        self.models = None
    
    def _get_models_config(self):
        """Obtiene la configuración actual de modelos"""
        try:
            from src.routes_ai import AI_CONFIG_CACHE
            # Usamos un modelo por defecto razonable si no está en la caché
            default_model = "gemma3n:latest" 
            return {
                "failure_prediction": AI_CONFIG_CACHE.get("default_prediction_model", default_model),
                "pattern_analysis": AI_CONFIG_CACHE.get("default_prediction_model", default_model),
                "optimization": AI_CONFIG_CACHE.get("default_prediction_model", default_model), 
                "text_analysis": AI_CONFIG_CACHE.get("default_chat_model", default_model)
            }
        except ImportError:
            # Fallback si no se puede importar
            default_model = "gemma3n:latest"
            return {
                "failure_prediction": default_model,
                "pattern_analysis": default_model,
                "optimization": default_model,
                "text_analysis": default_model
            }

    # ✅ --- FUNCIÓN COMPLETAMENTE REESCRITA PARA USAR /api/chat ---
    async def predict_machine_failure(
        self,
        machine_data: Dict,
        historical_data: List[Dict],
        days_ahead: int = 30,
        model_override: str = None,
        confidence_threshold: float = None
    ) -> Dict:
        """
        Genera una predicción de fallo usando el endpoint de CHAT para mayor fiabilidad en el formato.
        """
        try:
            metrics = self._calculate_machine_metrics(historical_data)
            models_config = self._get_models_config()
            model_to_use = model_override or models_config["failure_prediction"]

            if confidence_threshold is None:
                try:
                    from src.routes_ai import AI_CONFIG_CACHE
                    confidence_threshold = AI_CONFIG_CACHE.get("prediction_confidence_threshold", 70)
                except ImportError:
                    confidence_threshold = 70

            print(f"🤖 Usando modelo REAL (modo CHAT): {model_to_use}")
            print(f"📊 Umbral de confianza: {confidence_threshold}%")

            # 1. Definimos las instrucciones del sistema (las reglas del juego)
            system_prompt = f"""
            REGLA MÁS IMPORTANTE: RESPONDE ÚNICA Y EXCLUSIVAMENTE CON UN OBJETO JSON. TODO EL CONTENIDO DE ESE JSON DEBE ESTAR EN ESPAÑOL.

            Eres un analista experto en mantenimiento predictivo y preventivo para maquinaria industrial azulejera.
            Tu tarea es analizar los datos y responder con un objeto JSON válido.
            No incluyas explicaciones, texto introductorio, o cualquier texto fuera de la estructura JSON.
            Tu respuesta completa debe empezar con `{{` y terminar con `}}`.

            La estructura JSON y los nombres de las claves deben ser exactamente estos, y los valores deben estar en español:
            {{
                "probability": <numero_0_a_100>,
                "confidence": <numero_0_a_100>,
                "predicted_date": "<YYYY-MM-DD>" | null,
                "days_until_failure": <numero> | null,
                "components_at_risk": ["<componente en riesgo 1>", "<componente en riesgo 2>"],
                "failure_type": "<tipo de fallo en español>",
                "severity": "<baja|media|alta|critica>",
                "recommended_actions": ["<acción recomendada en español 1>", "<acción recomendada en español 2>"],
                "analysis_summary": "<resumen del análisis en español>"
            }}

            ## REGLAS OBLIGATORIAS:
            1.  El campo "recommended_actions" es OBLIGATORIO y NO PUEDE ser un array vacío.
            2.  DEBES proporcionar al menos dos recomendaciones específicas en español.
            3.  Si el riesgo es bajo, recomienda acciones preventivas generales como "Inspección visual de la máquina" o "Verificar parámetros de operación, lubricación y limpieza de las zonas mas vulnerables a enganchones".
            4.  RECUERDA: La totalidad de tu respuesta, incluyendo cada palabra en el resumen y en las acciones, debe estar en perfecto español.
            """
            # 2. Definimos los datos específicos para esta máquina (la petición del usuario)
            recent_failures = [o for o in historical_data[-10:] if o.get("work_type") == "Correctivo"]
            user_prompt = f"""
            Analiza los siguientes datos de la máquina y proporciona la salida JSON según las instrucciones, en español.
            
            CONTEXTO DE LA MÁQUINA:
            - Nombre: {machine_data.get('nombre')}
            - Modelo: {machine_data.get('modelo')}
            - Criticidad: {machine_data.get('criticidad', 'Media')}

            MÉTRICAS DE RENDIMIENTO:
            - MTBF (Tiempo Medio Entre Fallos): {metrics['mtbf']} horas
            - MTTR (Tiempo Medio de Reparación): {metrics['mttr']} horas
            - Nº de Fallos Recientes: {metrics['failure_rate']}

            HISTORIAL DE FALLOS RECIENTES:
            {json.dumps(recent_failures, indent=2, ensure_ascii=False)}

            PERIODO DE PREDICCIÓN: {days_ahead} días.
            """


            # 3. Creamos la lista de mensajes para la API de chat
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # 4. Llamamos a la función generate_with_chat con timeout
            response = None
            try:
                timeout_seconds = 300.0
                logger.info(f"💬 Llamando al modelo '{model_to_use}' (modo CHAT) para {machine_data.get('nombre', 'N/A')}. Timeout: {timeout_seconds}s.")
                
                # Usamos la función del cliente para el endpoint /api/chat
                generation_task = self.ollama_client.generate_with_chat(
                    model=model_to_use,
                    messages=messages,
                    temperature=0.1 # Temperatura muy baja para forzar el formato
                )
                response = await asyncio.wait_for(generation_task, timeout=timeout_seconds)

            except asyncio.TimeoutError:
                logger.error(f"❌ TIMEOUT! El modelo '{model_to_use}' (modo CHAT) tardó más de {timeout_seconds}s en responder.")
                return self._generate_fallback_prediction(machine_data, metrics, model_to_use)
            
            except Exception as ollama_error:
                logger.error(f"❌ Error directo de Ollama (modo CHAT) para {machine_data.get('nombre', 'N/A')}: {ollama_error}")
                return self._generate_fallback_prediction(machine_data, metrics, model_to_use)

            if not response:
                logger.warning(f"⚠️ La respuesta de Ollama (modo CHAT) fue vacía. Usando fallback.")
                return self._generate_fallback_prediction(machine_data, metrics, model_to_use)

            # 5. Procesamos la respuesta
            prediction = self._parse_ai_response(response, "failure_prediction")
            
            prediction.update({
                "machine_id": machine_data["id"],
                "prediction_type": "failure",
                "model_used": model_to_use,
                "data_points_used": len(historical_data),
                "generated_at": datetime.utcnow().isoformat(),
                "metrics_used": metrics,
                "confidence_threshold": confidence_threshold
            })

            return prediction

        except Exception as e:
            logger.error(f"Error general en predicción de fallo para {machine_data.get('nombre', 'N/A')}: {e}")
            model_name_for_fallback = locals().get('model_to_use', 'unknown')
            metrics_for_fallback = locals().get('metrics', {"mtbf": 0, "mttr": 0, "failure_rate": 0})
            return self._generate_fallback_prediction(machine_data, metrics_for_fallback, model_name_for_fallback)

    
    async def analyze_failure_patterns(
        self, 
        failures_data: List[Dict],
        time_window_days: int = 90
    ) -> Dict:
        # ... (esta función no necesita cambios)
        try:
            patterns = self._group_failures_by_patterns(failures_data)
            models_config = self._get_models_config()
            model_to_use = models_config["pattern_analysis"]
            prompt = f"""
            TASK: Analyze industrial equipment failure patterns.
            DATA: {json.dumps(patterns, indent=2)}
            TIME WINDOW: {time_window_days} days
            TOTAL FAILURES: {len(failures_data)}
            INSTRUCTIONS: Identify significant recurring patterns, correlations, and root causes. Provide specific preventive actions.
            OUTPUT FORMAT: Respond exclusively with a structured JSON object.
            """
            response = await self.ollama_client.generate(model=model_to_use, prompt=prompt)
            return self._parse_ai_response(response, "pattern_analysis")
        except Exception as e:
            logger.error(f"Error en análisis de patrones: {e}")
            return {"error": str(e), "patterns": []}
    
    async def optimize_maintenance_schedule(
        self,
        machines_data: List[Dict],
        constraints: Dict,
        optimization_goals: List[str]
    ) -> Dict:
        # ... (esta función no necesita cambios)
        try:
            models_config = self._get_models_config()
            model_to_use = models_config["optimization"]
            prompt = f"""
            TASK: Optimize a maintenance schedule.
            MACHINES: {json.dumps(machines_data, indent=2)}
            CONSTRAINTS: {json.dumps(constraints, indent=2)}
            GOALS: {json.dumps(optimization_goals, indent=2)}
            INSTRUCTIONS: Propose an optimized schedule that minimizes downtime and balances workload, respecting all constraints.
            OUTPUT FORMAT: Respond exclusively with a detailed JSON object for the schedule.
            """
            response = await self.ollama_client.generate(model=model_to_use, prompt=prompt)
            optimization = self._parse_ai_response(response, "optimization")
            improvement_metrics = self._calculate_optimization_metrics(machines_data, optimization)
            optimization["improvement_metrics"] = improvement_metrics
            return optimization
        except Exception as e:
            logger.error(f"Error en optimización de cronograma: {e}")
            return {"error": str(e), "optimized_schedule": []}
    
    async def generate_maintenance_insights(
        self,
        section_data: Dict,
        performance_data: Dict,
        period_days: int = 30
    ) -> Dict:
        # ... (esta función no necesita cambios)
        try:
            models_config = self._get_models_config()
            model_to_use = models_config["text_analysis"]
            prompt = f"""
            TASK: Generate maintenance insights for a specific section.
            SECTION DATA: {json.dumps(section_data, indent=2)}
            PERFORMANCE DATA ({period_days} days): {json.dumps(performance_data, indent=2)}
            INSTRUCTIONS: Analyze KPIs, identify problems, find improvement opportunities, and provide strategic recommendations.
            OUTPUT FORMAT: Respond exclusively with a structured JSON object.
            """
            response = await self.ollama_client.generate(model=model_to_use, prompt=prompt)
            return self._parse_ai_response(response, "insights")
        except Exception as e:
            logger.error(f"Error generando insights: {e}")
            return {"error": str(e), "insights": {}}
    
    # --- Métodos auxiliares privados ---
    
    def _calculate_machine_metrics(self, historical_data: List[Dict]) -> Dict:
        # ... (esta función no necesita cambios)
        if not historical_data:
            return {"mtbf": 0, "mttr": 0, "failure_rate": 0, "total_orders": 0, "preventive_ratio": 0}
        
        failure_intervals, repair_times, corrective_orders = [], [], []
        
        # Ordenar por fecha para un cálculo de MTBF correcto
        sorted_orders = sorted(historical_data, key=lambda x: x['date'])

        for i, order in enumerate(sorted_orders):
            if order.get("work_type") == "Correctivo":
                corrective_orders.append(order)
                if order.get("downtime_hours"):
                    repair_times.append(float(order["downtime_hours"]))

        for i in range(1, len(corrective_orders)):
            time_diff = self._calculate_time_difference(
                corrective_orders[i]["date"], corrective_orders[i-1]["date"]
            )
            if time_diff > 0:
                failure_intervals.append(time_diff)

        mtbf = np.mean(failure_intervals) if failure_intervals else 0
        mttr = np.mean(repair_times) if repair_times else 0
        total_orders = len(historical_data)
        preventive_ratio = len([o for o in historical_data if o.get("work_type") == "Preventivo"]) / total_orders if total_orders > 0 else 0
        
        return {
            "mtbf": round(mtbf, 2),
            "mttr": round(mttr, 2),
            "failure_rate": len(corrective_orders),
            "total_orders": total_orders,
            "preventive_ratio": round(preventive_ratio, 2)
        }
    
    def _build_failure_prediction_prompt(
        self, 
        machine_data: Dict, 
        metrics: Dict, 
        historical_data: List[Dict], 
        days_ahead: int,
        confidence_threshold: float = 70
    ) -> str:
        """
        ✅ PROMPT MEJORADO para forzar la respuesta en formato JSON.
        """
        recent_failures = [
            order for order in historical_data[-10:] 
            if order.get("work_type") == "Correctivo"
        ]
        
        return f"""
        TASK: Perform a failure prediction analysis for an industrial machine and respond EXCLUSIVELY with a single JSON object.

        MACHINE CONTEXT:
        - Name: {machine_data.get('nombre')}
        - Model: {machine_data.get('modelo')}
        - Criticality: {machine_data.get('criticidad', 'Media')}

        PERFORMANCE METRICS:
        - MTBF (Mean Time Between Failures): {metrics['mtbf']} hours
        - MTTR (Mean Time To Repair): {metrics['mttr']} hours
        - Recent Failure Count: {metrics['failure_rate']}

        RECENT FAILURE HISTORY:
        {json.dumps(recent_failures, indent=2)}

        INSTRUCTIONS:
        1. Analyze all provided data.
        2. Calculate the failure probability (%) for the next {days_ahead} days.
        3. Estimate the failure date if probability is over 10%.
        4. Identify components at highest risk.
        5. State your confidence in this prediction (0-100%).
        6. Provide a very brief analysis summary.

        OUTPUT FORMAT:
        Respond ONLY and EXCLUSIVELY with a valid JSON object. Do not include any explanation, introductory text, or markdown formatting. Your entire response must start with `{{` and end with `}}`.

        JSON STRUCTURE:
        {{
            "probability": <number_0_to_100>,
            "confidence": <number_0_to_100>,
            "predicted_date": "<YYYY-MM-DD>" | null,
            "days_until_failure": <number> | null,
            "components_at_risk": ["<string>", "<string>"],
            "failure_type": "<string_mechanical_electrical_etc>",
            "severity": "<low|medium|high|critical>",
            "recommended_actions": ["<string_action_1>", "<string_action_2>"],
            "analysis_summary": "<string_very_short_summary>"
        }}

        JSON OUTPUT:
        """

    def _parse_ai_response(self, response: str, response_type: str) -> Dict:
        # ... (esta función no necesita cambios)
        try:
            # Limpiar la respuesta para extraer solo el JSON
            json_part = response[response.find('{'):response.rfind('}')+1]
            if json_part:
                return json.loads(json_part)
            
            logger.warning(f"No se encontró un objeto JSON en la respuesta: {response[:200]}...")
            return self._extract_structured_info(response, response_type)
            
        except (json.JSONDecodeError, IndexError):
            logger.warning(f"Respuesta de IA no es JSON válido: {response[:200]}...")
            return self._extract_structured_info(response, response_type)
    
    def _extract_structured_info(self, response: str, response_type: str) -> Dict:
        # ... (esta función no necesita cambios)
        if response_type == "failure_prediction":
            return {
                "probability": self._extract_number(response, ["probabilidad", "probability"]),
                "confidence": self._extract_number(response, ["confianza", "confidence"]),
                "predicted_date": self._extract_date(response),
                "components_at_risk": self._extract_components(response),
                "failure_type": self._extract_failure_type(response),
                "severity": self._extract_severity(response),
                "recommended_actions": self._extract_actions(response),
                "analysis_summary": response[:500]
            }
        return {"raw_response": response, "type": response_type}

    def _extract_number(self, text: str, keywords: List[str]) -> Optional[float]:
        # ... (esta función no necesita cambios)
        import re
        for keyword in keywords:
            pattern = rf'"{keyword}"\s*:\s*(\d+(?:\.\d+)?)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
    
    # ... (el resto de los métodos _extract, _generate_fallback, etc. no necesitan cambios)
    
    def _extract_date(self, text: str) -> Optional[str]:
        import re
        date_pattern = r"(\d{4}-\d{2}-\d{2})"
        match = re.search(date_pattern, text)
        if match: return match.group(1)
        return None

    def _extract_components(self, text: str) -> List[str]:
        return [] # Simplificado, la extracción desde texto libre es poco fiable

    def _extract_failure_type(self, text: str) -> str:
        return "general"

    def _extract_severity(self, text: str) -> str:
        text_lower = text.lower()
        if any(word in text_lower for word in ["crítico", "critical"]): return "critical"
        if any(word in text_lower for word in ["alto", "high"]): return "high"
        if any(word in text_lower for word in ["medio", "medium"]): return "medium"
        return "low"

    def _extract_actions(self, text: str) -> List[str]:
        """
        ✅ Extrae una lista de acciones recomendadas desde una cadena de texto,
        incluso si no es un JSON perfecto.
        """
        import re
        import json
        try:
            # Intenta encontrar un bloque JSON que contenga "recommended_actions"
            match = re.search(r'["\']recommended_actions["\']\s*:\s*(\[.*?\])', text, re.DOTALL)
            if match:
                actions_str = match.group(1)
                # Limpiar y parsear el string del array
                actions = json.loads(actions_str)
                return [str(action) for action in actions] # Asegurarse de que todos los elementos son strings
        except (json.JSONDecodeError, IndexError):
            # Si el JSON parcial falla, buscar líneas que parezcan acciones
            pass

        # Fallback: buscar líneas que empiecen con guiones, asteriscos o números (listas)
        lines = text.split('\n')
        actions = []
        for line in lines:
            cleaned_line = line.strip()
            if re.match(r'^\s*[-*]\s*|\d+\.\s*', cleaned_line):
                # Quitar el marcador de lista y comillas
                action = re.sub(r'^\s*[-*]\s*|\d+\.\s*', '', cleaned_line).strip('", ')
                if action:
                    actions.append(action)
        
        # Si encontramos algo, lo devolvemos. Si no, la lista vacía.
        return actions

    def _generate_fallback_prediction(self, machine_data: Dict, metrics: Dict, model_used: str = "fallback") -> Dict:
        criticality = machine_data.get('criticidad', 'Media')
        mtbf = metrics.get('mtbf', 0)
        failure_rate = metrics.get('failure_rate', 0)

        probability = 20
        if mtbf > 0 and mtbf < 720: probability = min(85, (720 / mtbf) * 10)
        elif failure_rate > 3: probability = 65
        
        if criticality == 'Alta': probability = min(95, probability * 1.2)
        elif criticality == 'Baja': probability *= 0.8
        
        days_until = max(7, int(mtbf / 24)) if mtbf > 0 else 30
        
        return {
            "probability": round(probability, 1), "confidence": 60,
            "predicted_date": (datetime.utcnow() + timedelta(days=days_until)).strftime("%Y-%m-%d"),
            "days_until_failure": days_until, "components_at_risk": ["Sistema general"],
            "failure_type": "general", "severity": "medium",
            "recommended_actions": ["Inspección visual", "Verificar parámetros operacionales"],
            "analysis_summary": "Predicción de respaldo generada por fallo o timeout en el modelo de IA.",
            "model_used": model_used, "fallback_used": True, "meets_confidence_threshold": False
        }

    def _calculate_time_difference(self, date1: str, date2: str) -> float:
        try:
            dt1 = datetime.fromisoformat(date1.replace('Z', '+00:00'))
            dt2 = datetime.fromisoformat(date2.replace('Z', '+00:00'))
            return abs((dt1 - dt2).total_seconds() / 3600)
        except:
            return 0

    def _group_failures_by_patterns(self, failures_data: List[Dict]) -> Dict:
        return {} # Implementación simplificada

    def _calculate_optimization_metrics(self, original_data: List[Dict], optimization: Dict) -> Dict:
        return {} # Implementación simplificada