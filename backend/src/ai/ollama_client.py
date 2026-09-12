# src/ai/ollama_client.py - Versión actualizada con soporte para parámetros
import aiohttp
import json
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str = "http://192.168.1.62:11434"):
        self.base_url = base_url
        # ✅ Timeout ajustado a 5 minutos (300s), un valor razonable para modelos grandes.
        self.timeout = aiohttp.ClientTimeout(total=300)
        
    async def generate(
        self, 
        model: str, 
        prompt: str, 
        images: Optional[List] = None,
        # --- ✅ PARÁMETROS OPTIMIZADOS POR DEFECTO ---
        temperature: float = 0.2,   # Baja creatividad para que se ciña al formato JSON
        max_tokens: int = 4096,     # Aumentamos por si el JSON es largo
        top_p: float = 0.9,
        top_k: int = 40,
        num_gpu: int = 0,           # IMPORTANTÍSIMO: 0 para forzar el uso de CPU y evitar errores
        num_threads: int = 10,      # Un buen número de hilos para tu i7 Ultra sin saturarlo
        stream: bool = False
    ) -> str:
        """
        Genera respuesta usando Ollama con parámetros optimizados.
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # ✅ PAYLOAD CORREGIDO: ahora usa los parámetros pasados a la función
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_p": top_p,
                    "top_k": top_k,
                    "num_ctx": 4096,
                    "num_gpu": num_gpu,
                    "num_thread": num_threads
                }
            }
            
            if images:
                payload["images"] = images

            try:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '')

                    # Si el status no es 200, manejamos el error
                    error_text = await response.text()
                    logger.error(f"Error from Ollama (status {response.status}): {error_text}")
                    if "model not found" in error_text:
                        raise Exception(f"Model '{model}' not found in Ollama.")
                    raise Exception(f"Ollama server failed with status {response.status}: {error_text}")

            except aiohttp.ClientError as e:
                logger.error(f"Connection error to Ollama: {e}")
                raise Exception(f"Cannot connect to Ollama server at {self.base_url}.")
            except Exception as e:
                logger.error(f"Unexpected error in Ollama client: {e}")
                raise

    async def list_models(self) -> List[Dict]:
        """
        Obtiene la lista de modelos disponibles en Ollama
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                print(f"🔍 DEBUG: Conectando a {self.base_url}/api/tags")
                async with session.get(f"{self.base_url}/api/tags") as response:
                    print(f"🔍 DEBUG: Status HTTP: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"🔍 DEBUG: Respuesta JSON completa: {result}")
                        
                        models = result.get('models', [])
                        print(f"🔍 DEBUG: Modelos encontrados: {len(models)}")
                        
                        for i, model in enumerate(models):
                            print(f"🔍 DEBUG: Modelo {i+1}: {model.get('name', 'sin_nombre')}")
                        
                        return models
                    else:
                        error_text = await response.text()
                        print(f"🔍 DEBUG: Error HTTP {response.status}: {error_text}")
                        return []
                        
            except aiohttp.ClientError as e:
                print(f"🔍 DEBUG: Error de conexión: {e}")
                return []
            except Exception as e:
                print(f"🔍 DEBUG: Error inesperado: {e}")
                import traceback
                traceback.print_exc()
                return []

    async def pull_model(self, model_name: str) -> bool:
        """
        Descarga un modelo en Ollama
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            payload = {"name": model_name}
            
            try:
                async with session.post(
                    f"{self.base_url}/api/pull",
                    json=payload
                ) as response:
                    if response.status == 200:
                        # El pull puede tardar mucho, así que solo verificamos que empezó
                        logger.info(f"Model pull started for {model_name}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Error pulling model {model_name}: {error_text}")
                        return False
                        
            except Exception as e:
                logger.error(f"Error pulling model {model_name}: {e}")
                return False

    async def check_model_exists(self, model_name: str) -> bool:
        """
        Verifica si un modelo existe en Ollama
        """
        models = await self.list_models()
        model_names = [model.get('name', '') for model in models]
        return model_name in model_names

    async def get_model_info(self, model_name: str) -> Optional[Dict]:
        """
        Obtiene información detallada de un modelo
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            payload = {"name": model_name}
            
            try:
                async with session.post(
                    f"{self.base_url}/api/show",
                    json=payload
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return None
                        
            except Exception as e:
                logger.error(f"Error getting model info for {model_name}: {e}")
                return None

    async def health_check(self) -> bool:
        """
        Verifica si Ollama está funcionando correctamente
        """
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            try:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
                    
            except Exception:
                return False

    async def generate_with_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Genera respuesta usando el formato de chat de Ollama
        
        Args:
            model: Nombre del modelo
            messages: Lista de mensajes en formato [{"role": "user", "content": "..."}]
            temperature: Temperatura del modelo
            max_tokens: Máximo tokens a generar
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "num_ctx": 4096
                }
            }

            try:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('message', {}).get('content', '')
                    else:
                        error_text = await response.text()
                        logger.error(f"Error in chat API: {error_text}")
                        raise Exception(f"Chat API error: {error_text}")
                        
            except aiohttp.ClientError as e:
                logger.error(f"Connection error in chat API: {e}")
                raise Exception(f"Cannot connect to Ollama chat API")
            except Exception as e:
                logger.error(f"Unexpected error in chat API: {e}")
                raise

    def get_model_recommendations(self, use_case: str = "chat") -> List[str]:
        """
        Recomienda modelos según el caso de uso
        """
        recommendations = {
            "chat": ["llama3.2:3b", "llama3.2:1b", "mistral:7b"],
            "technical": ["gemma2:9b", "llama3:8b", "qwen2.5:7b"],
            "analysis": ["gemma3:27b", "llama3:8b", "gemma2:9b"],
            "fast": ["llama3.2:1b", "llama3.2:3b"],
            "quality": ["gemma3:27b", "gemma2:9b", "llama3:8b"]
        }
        
        return recommendations.get(use_case, recommendations["chat"])