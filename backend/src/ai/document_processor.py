# document_processor.py (Versión Simplificada)
import os
import io
import json
import logging
import base64
import shutil
import asyncio
import re
from datetime import datetime
from PIL import Image, ImageEnhance, ImageFilter
import aiohttp
import requests # Mantenemos requests para la llamada síncrona al proxy
from sqlalchemy.orm import Session
from src.models.document import Document
from src.models.work_order import WorkOrder
from src.models.machine import Machine

# Configurar logger (si no está configurado globalmente)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DocumentProcessor:
    def __init__(self, base_url: str = "http://192.168.1.62:11434", model: str = "gemma3:27b"):
        # base_url (Ollama directo) no se usa si siempre vamos por el proxy
        # self.base_url = base_url
        self.model = model # Modelo a solicitar al proxy
        # Añadimos URL del proxy
        self.proxy_url = "http://192.168.1.62:5000" # Dirección del servidor Windows
        # Timeout más largo para llamadas al proxy IA (25 minutos)
        self.timeout_seconds = 1500

    # --- Se mantiene la función de preprocesamiento de imagen ---
    def preprocess_image(self, image_data: bytes, doc_type: str = "albaran") -> bytes:
        """
        Preprocesa la imagen para mejorar el reconocimiento de texto según el tipo de documento.
        Los documentos manuscritos (partes de trabajo) reciben un tratamiento especial.

        Args:
            image_data: Datos de la imagen en bytes
            doc_type: Tipo de documento ("albaran" o "parte_trabajo")

        Returns:
            Imagen preprocesada en bytes
        """
        try:
            # Abrir la imagen desde bytes
            image = Image.open(io.BytesIO(image_data))

            # Convertir a RGB si no lo está ya
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Redimensionar si la imagen es muy grande (manteniendo la proporción)
            max_dim = 2000
            width, height = image.size
            if width > max_dim or height > max_dim:
                if width > height:
                    new_width = max_dim
                    new_height = int(height * (max_dim / width))
                else:
                    new_height = max_dim
                    new_width = int(width * (max_dim / height))
                # Corrección: usar los nuevos width y height
                image = image.resize((new_width, new_height), Image.LANCZOS)
                # Actualizar width y height para el procesamiento posterior
                width, height = new_width, new_height

            # Aplicar preprocesamiento específico según tipo de documento
            if doc_type == "parte_trabajo":
                # Para manuscritos: procesamiento más agresivo para texto escrito a mano
                logger.info("Aplicando preprocesamiento intensivo para parte_trabajo")

                # 1. Aumentar el contraste significativamente
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2.8)

                # 2. Aumentar la nitidez
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(2.5)

                # 3. Ajustar el brillo
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(1.2)

                # --- Eliminado el bloque complejo de FIND_EDGES que podía ser problemático ---
                # Ahora nos quedamos con los ajustes de contraste, nitidez y brillo.
                # ---

            else: # albaran
                # Para albaranes impresos: ajustes estándar
                logger.info("Aplicando preprocesamiento estándar para albaran")
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.9)

                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(1.8)

            # Convertir de vuelta a bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG', optimize=True, quality=95)
            preprocessed_bytes = img_byte_arr.getvalue()
            logger.info(f"Preprocesamiento completado. Tamaño original: {len(image_data)} bytes, preprocesado: {len(preprocessed_bytes)} bytes")
            return preprocessed_bytes

        except Exception as e:
            logger.warning(f"Error en preprocesamiento de imagen: {str(e)}. Usando imagen original.")
            import traceback
            logger.debug(traceback.format_exc())
            return image_data

    # --- ELIMINADAS FUNCIONES DE POST-PROCESAMIENTO LOCAL ---
    # _extract_pattern, _extract_supplier_name, _extract_total_amount,
    # _extract_products_from_text, _post_process_work_order, _post_process_json,
    # _fallback_extraction, _extract_structured_data, _normalize_numeric_values
    # ---

    # --- ELIMINADA LA CLASE ManuscriptPostProcessor ---
    # class ManuscriptPostProcessor: ...
    # ---

    async def process_document(self, file_path: str, doc_type: str, db: Session = None, doc_id: int = None):
        """
        Procesa un documento llamando al proxy IA y maneja la respuesta.
        VERSIÓN SIMPLIFICADA: Confía en los datos refinados por el RAG del proxy.
        """
        logger.info(f"Iniciando process_document (simplificado) para ID:{doc_id or 'N/A'} ({os.path.basename(file_path)}), tipo: {doc_type}")

        try:
            # Verificar si el archivo existe
            if not os.path.exists(file_path):
                logger.error(f"El archivo {file_path} no existe.")
                raise FileNotFoundError(f"El archivo {file_path} no existe")

            # Leer archivo
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                if not file_content:
                     raise ValueError(f"El archivo {file_path} está vacío.")
                logger.info(f"Archivo '{os.path.basename(file_path)}' leído ({len(file_content)} bytes).")
            except Exception as e:
                logger.error(f"Error leyendo archivo {file_path}: {e}", exc_info=True)
                raise IOError(f"Error leyendo archivo: {e}") from e

            # Preprocesar imagen ANTES de codificar
            logger.info(f"Iniciando preprocesamiento para tipo: {doc_type}")
            preprocessed_content = self.preprocess_image(file_content, doc_type)

            # Codificar a base64 el contenido preprocesado
            try:
                base64_content = base64.b64encode(preprocessed_content).decode('utf-8')
                logger.info(f"Imagen preprocesada codificada ({len(base64_content)} chars base64).")
            except Exception as e:
                logger.error(f"Error codificando imagen preprocesada {file_path}: {e}", exc_info=True)
                raise ValueError(f"Error codificando imagen: {e}") from e

            # Preparar payload y URL para el proxy
            payload = {
                "file_base64": base64_content,
                "file_path": file_path.replace('/', '\\'), # Ruta original para referencia del proxy
                "filename": os.path.basename(file_path),
                "model": self.model, # El modelo que queremos que use el proxy (si lo soporta)
                "doc_type": doc_type
            }
            # Endpoint del proxy que realiza la extracción completa (Ollama + RAG)
            url = f"{self.proxy_url}/extract" # Asumiendo que /extract hace todo

            logger.info(f"Enviando solicitud al proxy IA: {url} con timeout {self.timeout_seconds}s")
            logger.debug(f"Payload (sin base64): modelo={self.model}, tipo={doc_type}, archivo={payload['filename']}")

            # --- Llamada al Proxy y Manejo de Respuesta ---
            try:
                # Usamos requests síncrono aquí como estaba antes
                response = requests.post(url, json=payload, timeout=self.timeout_seconds)

                # --- Logs de Diagnóstico de Respuesta ---
                logger.info(f"Respuesta recibida del Proxy IA. Status Code: {response.status_code}")
                proxy_response_text = ""
                result = {}
                extracted_data_from_proxy = None # Inicializar
                try:
                    proxy_response_text = response.text
                    logger.info(f"Proxy Raw Response Text (primeros 500 chars): {proxy_response_text[:500]}")
                    if response.ok:
                         # Intentamos parsear como JSON
                         result = response.json()
                         # Verificamos la estructura esperada devuelta por el proxy
                         if isinstance(result, dict):
                             extracted_data_from_proxy = result.get('extracted_data') # Extraemos el campo clave
                             logger.info(f"Proxy Parsed JSON Response. Success: {result.get('success')}. Error: {result.get('error')}. Extracted Data: {str(extracted_data_from_proxy)[:300]}...")
                         else:
                              logger.error(f"Proxy devolvió JSON pero no es un diccionario: {type(result)}")
                              extracted_data_from_proxy = {"error": "Formato JSON inesperado del proxy"}

                    else:
                         logger.warning(f"Status code {response.status_code} no es OK, no se parsea JSON.")

                except json.JSONDecodeError as json_err:
                    logger.error(f"FALLO al parsear JSON recibido del proxy (Status: {response.status_code}): {json_err}")
                    raise ValueError(f'Respuesta inválida (no JSON) del proxy: {proxy_response_text[:500]}') from json_err
                except Exception as read_err:
                    logger.error(f"Error leyendo/parseando respuesta del proxy: {read_err}", exc_info=True)
                    raise IOError(f'Error leyendo respuesta del proxy: {read_err}') from read_err
                # --- Fin Logs ---

                # Verificar status code HTTP
                if not response.ok:
                    error_msg = f"Error del proxy: HTTP {response.status_code}"
                    logger.error(f"{error_msg}. Raw text: {proxy_response_text[:500]}")
                    raise requests.exceptions.HTTPError(error_msg, response=response)

                # Verificar el campo 'success' dentro del JSON recibido del proxy
                # (Asumiendo que tu proxy devuelve {'success': True/False, 'extracted_data': ..., 'error': ...})
                if not result.get('success', False):
                    error_msg = result.get('error', 'Error desconocido reportado por el proxy (success=false)')
                    logger.error(f"Proxy reportó error interno: {error_msg}")
                    raise ValueError(f"Error reportado por el proxy: {error_msg}")

                # Extraer los datos ya refinados por el RAG del proxy
                # Si extracted_data_from_proxy es None o no es dict, lo convertimos a dict vacío
                extracted_data = extracted_data_from_proxy if isinstance(extracted_data_from_proxy, dict) else {}

                if not extracted_data:
                     logger.warning(f"Campo 'extracted_data' del proxy vacío o ausente/inválido (era: {extracted_data_from_proxy}). Usando dict vacío.")

                # --- YA NO HAY POST-PROCESAMIENTO LOCAL AQUÍ ---
                # Los datos en 'extracted_data' son los que se guardarán.

                # Guardar debug file (opcional, si todavía lo quieres)
                debug_file = None
                # ... tu lógica para guardar si es necesario ...

                logger.info(f"process_document (simplificado) para ID:{doc_id or 'N/A'} finalizado con éxito. Devolviendo datos recibidos del proxy.")
                return {
                    'success': True,
                    # Devolvemos directamente los datos del proxy
                    'extracted_data': extracted_data,
                    'debug_file': debug_file, # Puede ser None
                    'processing_method': 'proxy_rag_refined' # Indicamos que son datos del proxy
                }

            # Manejar errores específicos de la llamada al proxy
            except requests.exceptions.Timeout as e:
                error_msg = f"Timeout ({self.timeout_seconds}s) esperando respuesta del proxy: {e}"
                logger.error(error_msg)
                raise TimeoutError(error_msg) from e
            except requests.exceptions.RequestException as e:
                 error_msg = f"Error de conexión/red al contactar al proxy: {e}"
                 logger.error(error_msg, exc_info=True)
                 raise ConnectionError(error_msg) from e
            # Capturamos también los errores lanzados por validación (HTTPError, ValueError)
            except (requests.exceptions.HTTPError, ValueError, IOError) as e_comm_validation:
                 logger.error(f"Error de comunicación o validación con proxy: {e_comm_validation}", exc_info=False) # No necesitamos toda la traza aquí
                 raise e_comm_validation # Relanzamos para que la tarea de fondo lo maneje
            except Exception as e_proxy:
                error_msg = f"Error inesperado durante comunicación/procesamiento con proxy: {e_proxy}"
                logger.error(error_msg, exc_info=True)
                raise RuntimeError(error_msg) from e_proxy

        # Manejar errores generales (archivo no existe, error leyendo/codificando)
        except (FileNotFoundError, IOError, ValueError) as e_main:
            # Estos errores ya fueron logueados donde ocurrieron.
            error_msg = f"Error general procesando documento ANTES de llamar al proxy: {e_main}"
            logger.error(error_msg, exc_info=False)
            raise e_main # Relanzar la excepción original para que la background task la capture

    # --- Se mantiene _create_work_orders por si se usa en otro lado, ---
    # --- pero NO se llama desde el flujo principal de process_document ---
    async def _create_work_orders(self, doc: Document, work_orders: list, db: Session):
        """
        Crea órdenes de trabajo en base a la información extraída.
        (Esta función se mantiene pero no se llama en el flujo principal post-proxy)

        Args:
            doc: Documento origen
            work_orders: Lista de órdenes de trabajo a crear (recibida del proxy)
            db: Sesión de base de datos
        """
        orders_created = 0
        errors = 0

        logger.info(f"(Función _create_work_orders NO LLAMADA EN FLUJO PRINCIPAL) - Recibidas {len(work_orders)} tareas para posible creación de órdenes")

        for wo_data in work_orders:
            # ... (resto del código de _create_work_orders sin cambios) ...
             try:
                # Buscar la máquina de manera más flexible
                machine_name = wo_data.get('machine_name', wo_data.get('machine', '')).strip() # Usar machine_name si existe
                details = wo_data.get('details', '')
                operator = wo_data.get('operator', 'Sin asignar')
                work_type = wo_data.get('work_type', 'Correctivo') # Tomar tipo del RAG si existe
                title = wo_data.get('action', f"Trabajo en {machine_name}")[:50] # Usar acción como título si existe

                if not machine_name:
                    # Si no hay nombre de máquina, intentar extraerlo de los detalles
                    logger.warning("No se encontró 'machine_name' o 'machine', intentando inferir de 'details'.")
                    # ... (lógica para inferir machine_name de details) ...
                    # Por simplicidad, si no hay, la marcamos como desconocida
                    if not machine_name:
                         logger.warning("No se pudo determinar la máquina desde details, usando 'Máquina sin identificar'")
                         machine_name = "Máquina sin identificar"

                # Buscar la máquina en la base de datos
                # ... (lógica de búsqueda flexible de máquina) ...
                machines_query = db.query(Machine)
                machine = machines_query.filter(Machine.nombre == machine_name).first()
                if not machine:
                    machine = machines_query.filter(Machine.nombre.ilike(f"%{machine_name}%")).first()
                # ... (más lógica de búsqueda si es necesario) ...

                if not machine:
                    logger.warning(f"Máquina no encontrada en BD para nombre: '{machine_name}'")
                    errors += 1
                    continue

                # Buscar usuario/operario asignado
                assigned_user = db.query(User).filter(User.username == operator).first()
                assigned_to_id = assigned_user.id if assigned_user else None
                if not assigned_to_id:
                     logger.warning(f"Operario '{operator}' no encontrado, orden sin asignar a usuario específico.")
                     # Podríamos asignar a un usuario/rol por defecto aquí si es necesario

                # Crear la orden de trabajo
                order = WorkOrder(
                    title=title,
                    details=details,
                    work_type=work_type,
                    machine_id=machine.id,
                    section_id=machine.section_id,
                    line_id=machine.line_id,
                    operator=operator, # Guardar el nombre original extraído
                    status='Pendiente', # Estado inicial
                    source_document_id=doc.id,
                    assigned_to_id=assigned_to_id, # ID del usuario si se encontró
                    created_at=datetime.utcnow()
                    # 'repuesto_id' y 'quantity_used' se manejarían en la confirmación
                )

                # Agregar la orden a la base de datos
                db.add(order)
                orders_created += 1

             except Exception as e:
                logger.error(f"Error creando orden de trabajo desde datos {wo_data}: {str(e)}")
                errors += 1

        # Confirmar los cambios en la base de datos (si hubo órdenes creadas)
        if orders_created > 0:
            try:
                db.commit()
                logger.info(f"Se crearon {orders_created} órdenes de trabajo automáticamente desde {doc.id} (errores: {errors})")
            except Exception as e_commit:
                 logger.error(f"Error al hacer commit de las órdenes de trabajo creadas: {e_commit}")
                 db.rollback()
        elif errors > 0:
             logger.warning(f"No se crearon órdenes, pero hubo {errors} errores durante el intento.")
        else:
            logger.info(f"No se crearon órdenes automáticamente (quizás no había datos válidos o no se llamó a la función).")


    # --- Funciones auxiliares _get_expected_fields, _validate_extracted_data ---
    # --- (Se mantienen por si se usan en validaciones futuras, pero no en post-proc) ---
    def _get_expected_fields(self, doc_type: str) -> dict:
        """
        Devuelve los campos esperados según el tipo de documento
        """
        if doc_type == "albaran":
            return {
                "document": ["number", "date"],
                "supplier": ["name"],
                "products": ["description", "quantity", "unit_price"],
                "totals": ["total_amount"]
            }
        else:  # parte_trabajo
            # Campos clave que esperamos del ManuscriptRAGSystem
            return {
                "date": [], # Campo opcional
                "shift": [], # Campo opcional
                "operator": [], # Campo opcional
                "work_orders": ["machine_name", "line_name", "section_name", "action", "details"] # Campos clave por orden
            }

    def _validate_extracted_data(self, data: dict, expected_fields: dict) -> dict:
        """
        Valida que los datos extraídos tengan la estructura esperada
        (Simplificado para chequear existencia básica)
        """
        validation = {'is_valid': True, 'missing_fields': {}, 'warnings': []}
        if not isinstance(data, dict):
             validation['is_valid'] = False
             validation['warnings'].append("Los datos extraídos no son un diccionario.")
             return validation

        for section, fields in expected_fields.items():
            if section not in data:
                validation['is_valid'] = False
                validation['missing_fields'][section] = fields
                continue

            section_data = data[section]

            # Para listas como work_orders o products
            if isinstance(section_data, list):
                if not section_data: # Lista vacía es válida si la sección existe
                     continue
                # Validar estructura del primer elemento como ejemplo
                if fields and isinstance(section_data[0], dict):
                     item_missing = [f for f in fields if f not in section_data[0]]
                     if item_missing:
                          validation['is_valid'] = False
                          # No marcamos como missing toda la sección, sino que avisamos
                          validation['warnings'].append(f"Primer item en '{section}' no tiene campos: {', '.join(item_missing)}")
                elif fields and not isinstance(section_data[0], dict):
                     validation['is_valid'] = False
                     validation['warnings'].append(f"Items en '{section}' no son diccionarios.")

            # Para diccionarios como supplier o document
            elif isinstance(section_data, dict):
                 dict_missing = [f for f in fields if f not in section_data]
                 if dict_missing:
                      validation['is_valid'] = False
                      validation['missing_fields'][section] = dict_missing
            # Para campos simples que no son listas ni dicts (date, shift, operator)
            elif not fields: # Si no se esperan subcampos, solo la existencia de la clave es suficiente
                 pass
            else: # Si se esperan subcampos pero no es lista ni dict
                 validation['is_valid'] = False
                 validation['missing_fields'][section] = fields

        return validation