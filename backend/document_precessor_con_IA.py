# src/ai/document_processor.py
import aiohttp
import json
import base64
import os
from PIL import Image
from surya import Surya  # Importamos Surya
import io
import shutil
import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from src.models.document import Document
from src.models.work_order import WorkOrder
from src.models.machine import Machine

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, base_url: str = "http://192.168.1.62:11434"):
        self.base_url = base_url
        self.models = {
            'vision': 'llava:34b',
            'text': 'codellama:70b',
            'backup': 'qwen2.5:72b'
        }
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5 minutos de timeout

    async def process_document(self, doc_id: int, file_path: str, doc_type: str, db: Session):
        try:
            # Actualizar estado
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if not doc:
                raise ValueError(f"Documento {doc_id} no encontrado")
            
            doc.status = "processing"
            db.commit()

            # Procesar según tipo de archivo
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                result = await self._process_image(file_path, doc_type)
            elif ext in ['.pdf']:
                result = await self._process_pdf(file_path, doc_type)
            else:
                result = await self._process_text(file_path, doc_type)

            # Actualizar documento con resultados
            doc.processed_data = result
            doc.status = "completed"
            doc.processed_at = datetime.utcnow()

            if doc_type == 'albaran':
                doc.supplier_name = result.get('supplier', {}).get('name')
                doc.total_amount = result.get('total_amount')
            
            # Crear órdenes de trabajo si es necesario
            if doc_type == 'parte_trabajo' and result.get('work_orders'):
                await self._create_work_orders(doc, result['work_orders'], db)

            db.commit()
            logger.info(f"Documento {doc_id} procesado correctamente")

        except Exception as e:
            logger.error(f"Error procesando documento {doc_id}: {str(e)}")
            doc.status = "error"
            doc.error_message = str(e)
            db.commit()

    async def _process_image(self, file_path: str, doc_type: str) -> dict:
        try:
            # Leemos la imagen como bytes, sin ninguna manipulación
            with open(file_path, 'rb') as f:
                image_bytes = f.read()
        
            # Creamos el base64 de la imagen
            base64_str = base64.b64encode(image_bytes).decode('utf-8')
        
            # Prompt específico según el tipo de documento
            if doc_type == "albaran":
                prompt = """Analiza con detalle este albarán comercial y extrae la siguiente información:
            
                1. Nombre de la empresa o proveedor
                2. Datos de contacto del proveedor (si están disponibles)
                3. Lista de todos los productos o materiales que aparecen, con:
                   - Nombre o descripción del producto
                   - Cantidad
                   - Precio unitario
                   - Importe total por producto
                4. Importe total del albarán
            
                Responde de manera estructurada, empezando con el proveedor, luego listando cada producto individualmente, y finalmente el total.
               """
            else:  # parte_trabajo
                prompt = """Analiza este parte de trabajo y extrae la siguiente información:
            
                1. Máquina o equipo intervenido
                2. Descripción detallada del trabajo realizado
                3. Nombre del operario que realizó el trabajo
                4. Tiempo empleado
                5. Materiales o repuestos utilizados con sus cantidades
            
                Responde de manera estructurada y detallada.
                """
        
            payload = {
                "model": "llava:34b",
                "prompt": prompt,
                "images": [base64_str],
                "stream": False
            }
        
            logging.info(f"Enviando solicitud para análisis de {doc_type}")
        
            # Realizamos la petición con un timeout mayor pero manejamos excepciones
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=500)) as session:
                    start_time = datetime.now()
                    logging.info(f"Iniciando solicitud a Ollama a las {start_time}")
                
                    try:
                        async with session.post(
                            f"{self.base_url}/api/generate",
                            json=payload,
                            headers={'Content-Type': 'application/json'}
                        ) as response:
                            end_time = datetime.now()
                            duration = (end_time - start_time).total_seconds()
                            logging.info(f"Respuesta recibida en {duration} segundos")
                        
                            status = response.status
                            text = await response.text()
                            logging.info(f"Status: {status}, Respuesta inicial: {text[:200]}...")

                            if status != 200:
                                return {"error": f"Error {status}: {text}"}
                        
                            try:
                                result = json.loads(text)
                                response_text = result.get("response", "")
                            
                                # Guardar respuesta para análisis
                                debug_dir = os.path.join("storage", "debug")
                                os.makedirs(debug_dir, exist_ok=True)
                                with open(os.path.join(debug_dir, f"{os.path.basename(file_path)}.response.txt"), "w") as f:
                                    f.write(response_text)
                            
                                # Procesar la respuesta para extraer información estructurada
                                if doc_type == "albaran":
                                    supplier_name = self._extract_supplier_name(response_text)
                                    total_amount = self._extract_total_amount(response_text)
                                
                                    return {
                                        "supplier": {"name": supplier_name, "details": ""},
                                        "total_amount": total_amount,
                                        "raw_response": response_text
                                   }
                                else:  # parte_trabajo
                                    return {"raw_response": response_text}
                            except Exception as json_error:
                                logging.error(f"Error al procesar JSON: {json_error}")
                                return {"error": str(json_error), "raw_text": text}
                    except asyncio.TimeoutError:
                        logging.error("Timeout al esperar respuesta de Ollama")
                        return {"error": "Timeout al esperar respuesta"}
            except Exception as request_error:
                logging.error(f"Error en la solicitud: {str(request_error)}")
                return {"error": f"Error en la solicitud: {str(request_error)}"}
                
        except Exception as e:
            logging.error(f"Error general: {str(e)}")
            raise

    # Funciones auxiliares para extraer información de la respuesta
    def _extract_supplier_name(self, text):
        # Búsqueda simple del nombre del proveedor
        lines = text.split('\n')
        for line in lines:
            if "proveedor:" in line.lower() or "empresa:" in line.lower():
                parts = line.split(":", 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return "Proveedor no identificado"

    def _extract_total_amount(self, text):
        # Búsqueda simple del importe total
        lines = text.split('\n')
        for line in lines:
            if "total:" in line.lower() or "importe total:" in line.lower():
                # Intentar extraer solo la parte numérica
                parts = line.split(":", 1)
                if len(parts) > 1:
                    number_part = parts[1].strip()
                    # Buscar números con posibles decimales
                    import re
                    matches = re.findall(r'\d+[.,]\d+|\d+', number_part)
                    if matches:
                        try:
                            # Convertir a float, reemplazando coma por punto si es necesario
                            return float(matches[0].replace(',', '.'))
                        except:
                            pass
        return 0.0
    
    async def _call_llava(self, image_base64: str, prompt: str) -> str:
        async with aiohttp.ClientSession() as session:
            try:
                payload = {
                    "model": "llava:34b",
                    "prompt": """Tu tarea es extraer información de un albarán que te mostraré.
                    Necesito que identifiques:
                    1. El nombre y datos de la empresa proveedora
                    2. Los productos listados, con sus cantidades y precios
                    3. El total del albarán

                    Devuelve la información en este formato JSON exacto (rellena los valores con la información que veas):
                    {
                        "supplier": {
                            "name": "NOMBRE_EMPRESA",
                            "details": "OTROS_DATOS"
                        },
                        "products": [
                            {
                                "name": "NOMBRE_PRODUCTO",
                                "quantity": CANTIDAD,
                                "price": PRECIO_UNIDAD,
                                "total": PRECIO_TOTAL
                            }
                        ],
                        "total_amount": TOTAL_ALBARAN
                    }""",
                    "images": [image_base64],
                    "stream": False,
                    "temperature": 0.1,  # Hacer la respuesta más determinista
                    "top_p": 0.1        # Reducir la creatividad
                }
            
                logging.info("Llamando a Llava API")
            
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    status = response.status
                    text = await response.text()
                    logging.info(f"Status: {status}, Respuesta: {text}")
                
                    if status == 200:
                        result = json.loads(text)
                        if "response" in result:
                            return result["response"]
                        return text
                    else:
                        raise Exception(f"Error de Llava: {text}")

            except Exception as e:
                logging.error(f"Error en llamada a Llava: {str(e)}")
                raise

    async def _structure_data(self, text: str, doc_type: str) -> dict:
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                prompt = self._get_structure_prompt(text, doc_type)
                payload = {
                    "model": self.models['text'],
                    "prompt": prompt,
                    "stream": False
                }
                
                async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        try:
                            return json.loads(result.get('response', '{}'))
                        except json.JSONDecodeError:
                            return {"error": "No se pudo estructurar la respuesta"}
                    else:
                        error_text = await response.text()
                        raise Exception(f"Error en estructuración de datos: {error_text}")
            except Exception as e:
                logger.error(f"Error en estructuración de datos: {str(e)}")
                raise

    def _get_prompt(self, doc_type: str) -> str:
        if doc_type == 'albaran':
            return """Analiza esta imagen de albarán y extrae:
                     - Nombre y datos del proveedor
                     - Lista de productos con cantidades y precios
                     - Total del albarán
                     Responde en formato JSON."""
        else:
            return """Analiza esta imagen de parte de trabajo y extrae:
                     - Máquina o equipo intervenido
                     - Descripción del trabajo realizado
                     - Operario que realizó el trabajo
                     - Tiempo empleado
                     - Materiales utilizados
                     Responde en formato JSON."""

    def _get_structure_prompt(self, text: str, doc_type: str) -> str:
        if doc_type == 'albaran':
            return f"""
            Convierte el siguiente texto de albarán en un JSON con este formato:
            {{
                "supplier": {{
                    "name": "nombre del proveedor",
                    "details": "otros datos del proveedor"
                }},
                "products": [
                    {{
                        "name": "nombre del producto",
                        "quantity": número,
                        "price": precio por unidad,
                        "total": precio total
                    }}
                ],
                "total_amount": número
            }}

            Texto a procesar: {text}
            """
        else:
            return f"""
            Convierte el siguiente texto de parte de trabajo en un JSON con este formato:
            {{
                "work_orders": [
                    {{
                        "machine": "nombre o identificador de la máquina",
                        "title": "resumen del trabajo",
                        "details": "descripción detallada",
                        "operator": "nombre del operario",
                        "time_spent": "tiempo empleado",
                        "materials": [
                            {{
                                "name": "nombre del material",
                                "quantity": cantidad
                            }}
                        ]
                    }}
                ]
            }}

            Texto a procesar: {text}
            """

    async def _create_work_orders(self, doc: Document, work_orders: list, db: Session):
        for wo_data in work_orders:
            try:
                # Buscar la máquina por nombre
                machine = db.query(Machine).filter(
                    Machine.nombre.ilike(f"%{wo_data.get('machine')}%")
                ).first()

                if not machine:
                    logger.warning(f"Máquina no encontrada: {wo_data.get('machine')}")
                    continue

                order = WorkOrder(
                    title=wo_data.get('title'),
                    details=wo_data.get('details'),
                    work_type='Correctivo',
                    machine_id=machine.id,
                    section_id=machine.section_id,
                    line_id=machine.line_id,
                    operator=wo_data.get('operator'),
                    status='Pendiente',
                    source_document_id=doc.id,
                    created_at=datetime.utcnow()
                )
                db.add(order)
            except Exception as e:
                logger.error(f"Error creando orden de trabajo: {str(e)}")

        db.commit()