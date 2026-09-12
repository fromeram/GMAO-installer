# src/scheduler.py - VERSIÓN COMPLETA CON CONFIGURACIÓN DINÁMICA DE IA

# ================================================
# 1. Importaciones
# ================================================

# Importaciones estándar de Python
import logging
import os
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Importaciones de terceros
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import func, and_, or_, text
from sqlalchemy.orm import joinedload, Session

# Importaciones de modelos y base de datos locales
from src.database import SessionLocal
from src.models.maintenance import Maintenance
from src.models.work_order import WorkOrder
from src.models.machine import Machine
from src.models.user import User
from src.models.inventory import Inventory
from src.models.maintenance_backlog import MaintenanceBacklog, BacklogStatus
from src.models.section import Section
from src.models.line import Line
from src.auth import create_access_token
from datetime import timedelta

# ================================================
# 2. Configuración e Inicialización de Logger
# ================================================

# Crear logger específico para el scheduler
logger = logging.getLogger("scheduler")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Intentar cargar configuración desde archivo
CONFIG_FILE = "scheduler_config.json"
DEFAULT_CONFIG = {
    "email": {
        "enabled": False,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "your_email@gmail.com",
        "password": "your_app_password",
        "sender": "GMAO System <your_email@gmail.com>"
    },
    "tasks": {
        "generate_orders": {
            "enabled": True,
            "cron": "0 0 * * *",  # Diariamente a las 00:00
            "advance_days": 0,    # Generar órdenes para hoy
            "description": "Generación automática de órdenes de trabajo"
        },
        "check_upcoming": {
            "enabled": True,
            "cron": "0 8 * * *",  # Diariamente a las 08:00
            "advance_days": 7,    # Alertar sobre mantenimientos en los próximos 7 días
            "description": "Verificación de mantenimientos próximos"
        },
        "check_stock": {
            "enabled": True,
            "cron": "0 9 * * *",  # Diariamente a las 09:00
            "description": "Verificación de stock mínimo"
        },
        "check_overdue": {
            "enabled": True,
            "cron": "0 10 * * *",  # Diariamente a las 10:00
            "description": "Verificación de órdenes vencidas"
        },
        "generate_metrics": {
            "enabled": True,
            "cron": "0 1 * * 1",    # Semanalmente los lunes a la 01:00
            "description": "Generación de métricas semanales"
        },
        "maintenance_backup": {
            "enabled": True,
            "cron": "0 23 * * 6",  # Sábados a las 23:00
            "description": "Actualización de backlog de mantenimiento"
        },
        "ai_predictions": {
            "enabled": True,
            "cron": "*/10 * * * *",  # ✅ CADA 10 MINUTOS POR DEFECTO
            "description": "Predicciones automáticas de IA basadas en datos reales"
        }
    },
    "ai_predictions": {
        "max_machines_per_cycle": 1,
        "cooldown_minutes": 5,
        "analysis_depth": "standard",
        "confidence_threshold": 70,
        "auto_retry_failed": True,
        "priority_sections": "1,4,7"
    }
}

# Cargar o crear configuración
config = DEFAULT_CONFIG
try:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            loaded_config = json.load(f)
            # Actualizar recursivamente para mantener valores predeterminados para claves faltantes
            def update_dict(d, u):
                for k, v in u.items():
                    if isinstance(v, dict) and k in d:
                        d[k] = update_dict(d.get(k, {}), v)
                    else:
                        d[k] = v
                return d
            config = update_dict(DEFAULT_CONFIG, loaded_config)
            logger.info(f"✅ Configuración cargada desde {CONFIG_FILE}")
    else:
        # Guardar configuración predeterminada
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
            logger.info(f"✅ Configuración predeterminada guardada en {CONFIG_FILE}")
except Exception as e:
    logger.error(f"❌ Error al cargar/guardar configuración: {e}")

# Inicializar scheduler
scheduler = BackgroundScheduler()

# ================================================
# 3. Funciones de Utilidad
# ================================================

def get_ai_config_from_json():
    """✅ Obtiene configuración de IA desde el JSON"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                loaded_config = json.load(f)
                ai_config = loaded_config.get("ai_predictions", {})
                
                # ✅ ASEGURAR VALORES POR DEFECTO
                defaults = {
                    "max_machines_per_cycle": 1,
                    "cooldown_minutes": 4,
                    "analysis_depth": "standard",
                    "confidence_threshold": 60,
                    "auto_retry_failed": True,
                    "priority_sections": "1,2,4,5,6,7,8"
                }

                for key, default_value in defaults.items():
                    if key not in ai_config:
                        ai_config[key] = default_value
                
                logger.info(f"📊 Configuración de IA cargada: {ai_config}")
                return ai_config
                
    except Exception as e:
        logger.error(f"❌ Error leyendo configuración de IA: {e}")
    
    # Fallback por defecto
    return {
        "max_machines_per_cycle": 1,
        "cooldown_minutes": 3,
        "analysis_depth": "standard",
        "confidence_threshold": 60,
        "auto_retry_failed": True,
        "priority_sections": "1,2,4,5,6,7,8"
    }

def send_email(recipients, subject, html_content, plain_content=None):
    """
    Envía un correo electrónico a uno o varios destinatarios.
    
    Args:
        recipients: Lista de direcciones o una sola dirección
        subject: Asunto del correo
        html_content: Contenido HTML del correo
        plain_content: Contenido alternativo en texto plano (opcional)
    """
    if not config["email"]["enabled"]:
        logger.info(f"Envío de correo desactivado. Asunto: {subject}")
        return False
    
    # Convertir destinatario único a lista
    if isinstance(recipients, str):
        recipients = [recipients]
    
    # Crear mensaje
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = config["email"]["sender"]
    msg['To'] = ', '.join(recipients)
    
    # Añadir contenido en texto plano si se proporciona
    if plain_content:
        msg.attach(MIMEText(plain_content, 'plain'))
    
    # Añadir contenido HTML
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        # Conectar al servidor SMTP
        server = smtplib.SMTP(config["email"]["smtp_server"], config["email"]["smtp_port"])
        server.starttls()
        server.login(config["email"]["username"], config["email"]["password"])
        
        # Enviar correo
        server.sendmail(config["email"]["sender"], recipients, msg.as_string())
        server.quit()
        logger.info(f"Correo enviado a {len(recipients)} destinatarios. Asunto: {subject}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar correo: {e}")
        return False

def save_alert(db, alert_type, message, entity_type=None, entity_id=None, severity="info", users=None):
    """
    Guarda una alerta en la base de datos.
    
    Args:
        db: Sesión de base de datos
        alert_type: Tipo de alerta (ej: 'maintenance', 'stock', 'system')
        message: Mensaje de la alerta
        entity_type: Tipo de entidad relacionada (ej: 'machine', 'inventory')
        entity_id: ID de la entidad relacionada
        severity: Gravedad ('info', 'warning', 'danger')
        users: Lista de IDs de usuarios a los que está dirigida (None = todos)
    """
    try:
        # Deberías tener un modelo Alert definido en tu sistema
        # Si no lo tienes, esta función actuará como placeholder para implementación futura
        
        # Por ahora, solo loguear la alerta
        logger.info(f"ALERTA [{alert_type}] [{severity}]: {message} " +
                            f"(Entity: {entity_type or 'N/A'}/{entity_id or 'N/A'}, " +
                            f"Users: {users or 'ALL'})")
        
        return True
    except Exception as e:
        logger.error(f"Error al guardar alerta: {e}")
        return False

def get_available_mechanic_for_shift(db: Session, target_date: datetime.date, role_id: int = 4):
    """
    Encuentra el mecánico disponible según el turno actual.
    
    Args:
        db: Sesión de base de datos
        target_date: Fecha para la cual buscar (date object)
        role_id: ID del rol (4 = Mecánico)
        
    Returns:
        user_id del mecánico asignado o None
    """
    try:
        # Importaciones internas que solo se usan en esta función (para evitar importaciones circulares si es un módulo grande)
        from src.models.shift_assignment import ShiftAssignment
        from src.models.shift_pattern import ShiftPattern
        from src.models.user import User
        from src.models.role import Role
        from src.models.absence import Absence
        from src.models.shift_override import ShiftOverride
        
        # 1. Obtener todos los mecánicos activos
        mechanics = db.query(User).filter(
            User.role_id == role_id,
            User.active == True
        ).all()
        
        if not mechanics:
            logger.warning("No hay mecánicos activos disponibles")
            return None
        
        # 2. Crear lista de candidatos con su turno
        candidates = []
        
        for mechanic in mechanics:
            # Verificar si tiene ausencia
            absence = db.query(Absence).filter(
                Absence.user_id == mechanic.id,
                Absence.start_date <= target_date,
                Absence.end_date >= target_date
            ).first()
            
            if absence:
                continue  # Saltar si está ausente
            
            # Verificar override
            override = db.query(ShiftOverride).filter(
                ShiftOverride.user_id == mechanic.id,
                ShiftOverride.date == target_date
            ).first()
            
            if override:
                # Usar turno override
                shift_code = override.actual_shift_code
                candidates.append({
                    'user_id': mechanic.id,
                    'username': mechanic.username,
                    'shift_code': shift_code,
                    'source': 'override'
                })
                continue
            
            # Calcular turno según patrón
            assignment = db.query(ShiftAssignment).filter(
                ShiftAssignment.user_id == mechanic.id
            ).first()
            
            if assignment and assignment.pattern:
                try:
                    days_difference = (target_date - assignment.reference_date).days
                    total_offset_days = days_difference + assignment.offset_days
                    cycle_len = assignment.pattern.cycle_length_days
                    
                    if cycle_len > 0:
                        day_index = (total_offset_days % cycle_len + cycle_len) % cycle_len
                        shift_code = assignment.pattern.pattern_sequence[day_index]
                        
                        candidates.append({
                            'user_id': mechanic.id,
                            'username': mechanic.username,
                            'shift_code': shift_code,
                            'source': 'pattern'
                        })
                except Exception as e:
                    logger.error(f"Error calculando turno para {mechanic.username}: {e}")
                    continue
        
        # 3. Filtrar por turnos laborales (excluir L=libre)
        working_candidates = [c for c in candidates if c['shift_code'] != 'L']
        
        if not working_candidates:
            # Si nadie está trabajando, usar cualquier mecánico como fallback (podrías querer otra lógica aquí, como no asignar)
            logger.info(f"Ningún mecánico en turno laboral para {target_date}, usando fallback (primer mecánico activo)")
            return mechanics[0].id if mechanics else None
            
        # 4. Priorizar por tipo de turno según la hora actual
        current_hour = datetime.now().hour
        
        # Determinar turno preferido según la hora
        if 6 <= current_hour < 14:
            preferred_shift = 'M'  # Mañana
        elif 14 <= current_hour < 22:
            preferred_shift = 'T'  # Tarde
        else:
            preferred_shift = 'N'  # Noche
        
        # Buscar mecánico en turno preferido
        preferred_candidates = [c for c in working_candidates if c['shift_code'] == preferred_shift]
        
        if preferred_candidates:
            selected = preferred_candidates[0]
            logger.info(f"Mecánico asignado por turno {preferred_shift}: {selected['username']} (ID: {selected['user_id']})")
            return selected['user_id']
        
        # Si no hay nadie en turno preferido, usar cualquier trabajador disponible
        selected = working_candidates[0]
        logger.info(f"Mecánico asignado (sin turno preferido): {selected['username']} (ID: {selected['user_id']}) - Turno: {selected['shift_code']}")
        return selected['user_id']
        
    except Exception as e:
        logger.error(f"Error en get_available_mechanic_for_shift: {e}")
        # Fallback: usar el primer mecánico activo si todo falla
        mechanic = db.query(User).filter(
            User.role_id == role_id,
            User.active == True
        ).first()
        return mechanic.id if mechanic else None

# ================================================
# 4. Tareas Programadas Principales
# ================================================

def generate_daily_orders():
    """
    Tarea programada que genera órdenes de trabajo para mantenimientos preventivos.
    Genera órdenes para los próximos días según configuración, asignando mecánicos.
    """
    if not config["tasks"]["generate_orders"]["enabled"]:
        logger.info("Generación de órdenes diarias deshabilitada por configuración.")
        return
    
    logger.info("Ejecutando generación de órdenes de trabajo preventivas...")
    db = SessionLocal()
    orders_created = 0
    
    try:
        # Fecha para generar órdenes (hoy + días de adelanto configurados)
        target_date = datetime.utcnow().date() + timedelta(days=config["tasks"]["generate_orders"]["advance_days"])
        
        # Buscar mantenimientos con fecha = fecha objetivo y sin orden generada
        maintenances = db.query(Maintenance).options(
            joinedload(Maintenance.machine).joinedload(Machine.line),
            joinedload(Maintenance.assigned_user),
            joinedload(Maintenance.assigned_role)
        ).filter(
            Maintenance.next_maintenance_date == target_date,
            Maintenance.generated_order_id.is_(None),
            Maintenance.type == "Preventivo"
        ).all()
        
        for m in maintenances:
            try:
                machine = m.machine
                if not machine:
                    logger.warning(f"Mantenimiento ID {m.id}: Máquina no encontrada")
                    continue

                # Determinar usuario asignado, usando la lógica de turnos para mecánicos
                assigned_to_id = m.assigned_user_id
                
                if not assigned_to_id and m.assigned_role_id:
                    if m.assigned_role_id == 4:  # Asumimos 4 es el ID del rol 'Mecánico'
                        assigned_to_id = get_available_mechanic_for_shift(db, target_date, m.assigned_role_id)
                    else:
                        # Para otros roles, buscar un usuario activo con ese rol
                        role_user = db.query(User).filter(
                            User.role_id == m.assigned_role_id,
                            User.active == True
                        ).first()
                        if role_user:
                            assigned_to_id = role_user.id

                if not assigned_to_id:
                    logger.warning(f"No se pudo asignar técnico para mantenimiento {m.id} (no user_id ni rol asignado, o no se encontró mecánico disponible en turno).")
                    continue

                # Determinar sección y línea
                line = machine.line
                section_id = line.section_id if line else None
                line_id = machine.line_id

                # Crear orden de trabajo
                new_order = WorkOrder(
                    title=f"[Preventivo] {m.title}",
                    details=m.description,
                    work_type="Preventivo",
                    machine_id=machine.id,
                    operator="Sistema Automático",
                    assigned_to_id=assigned_to_id,
                    section_id=section_id,
                    line_id=line_id,
                    status="Pendiente",
                    created_at=datetime.utcnow()
                )
                db.add(new_order)
                db.flush() # Para obtener el ID de la nueva orden
                
                # Generar número de orden
                new_order.order_number = f"OT-{new_order.id:04d}"
                
                # Vincular orden al mantenimiento
                m.generated_order_id = new_order.id
                db.commit()
                
                orders_created += 1
                logger.info(f"Orden #{new_order.order_number} generada para mantenimiento {m.id} ({m.title}) - Asignada a usuario {assigned_to_id}")
                
            except Exception as e:
                db.rollback()
                logger.error(f"Error generando orden para mantenimiento {m.id}: {e}")
                continue
        
        logger.info(f"Proceso completado: {orders_created} órdenes creadas para fecha {target_date}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error general en generación de órdenes: {e}")
    finally:
        db.close()

def check_upcoming_maintenance():
    """
    Verifica mantenimientos preventivos próximos a vencer y genera alertas.
    """
    if not config["tasks"]["check_upcoming"]["enabled"]:
        logger.info("Verificación de mantenimientos próximos deshabilitada por configuración.")
        return
    
    logger.info("Verificando mantenimientos preventivos próximos...")
    db = SessionLocal()
    try:
        # Fecha actual + días de margen configurados
        today = datetime.utcnow().date()
        alert_date = today + timedelta(days=config["tasks"]["check_upcoming"]["advance_days"])
        
        # Buscar mantenimientos próximos a vencer
        maintenances = db.query(Maintenance).options(
            joinedload(Maintenance.machine),
            joinedload(Maintenance.assigned_user),
            joinedload(Maintenance.assigned_role)
        ).filter(
            Maintenance.type == "Preventivo",
            Maintenance.is_completed == False,
            Maintenance.next_maintenance_date > today,
            Maintenance.next_maintenance_date <= alert_date,
            Maintenance.generated_order_id.is_(None)  # Sin OT generada aún
        ).all()
        
        if not maintenances:
            logger.info("No hay mantenimientos preventivos próximos en el período configurado.")
            return
        
        logger.info(f"Encontrados {len(maintenances)} mantenimientos preventivos próximos")
        # Aquí podrías añadir lógica para enviar correos o guardar alertas
        for m in maintenances:
            message = (f"El mantenimiento preventivo '{m.title}' de la máquina '{m.machine.name}' "
                       f"está programado para el {m.next_maintenance_date.strftime('%Y-%m-%d')}.")
            save_alert(db, "maintenance", message, "machine", m.machine.id, "warning", 
                       users=[m.assigned_user_id] if m.assigned_user_id else None)
            
            if m.assigned_user and m.assigned_user.email:
                subject = f"Recordatorio: Mantenimiento Próximo para {m.machine.name}"
                html_content = (f"<p>Hola {m.assigned_user.username},</p>"
                                f"<p>Este es un recordatorio de que el mantenimiento preventivo "
                                f"<strong>'{m.title}'</strong> para la máquina <strong>'{m.machine.name}'</strong> "
                                f"está programado para el <strong>{m.next_maintenance_date.strftime('%Y-%m-%d')}</strong>.</p>"
                                f"<p>Por favor, asegúrate de que se genere la orden de trabajo si aún no lo ha hecho, "
                                f"o de que la tarea sea atendida.</p>"
                                f"<p>Gracias.</p>")
                send_email(m.assigned_user.email, subject, html_content)

    except Exception as e:
        logger.error(f"Error en verificación de mantenimientos próximos: {e}")
    finally:
        db.close()

def check_low_stock():
    """
    Verifica productos bajo el stock mínimo y genera alertas.
    """
    if not config["tasks"]["check_stock"]["enabled"]:
        logger.info("Verificación de stock mínimo deshabilitada por configuración.")
        return
    
    logger.info("Verificando productos con stock bajo mínimos...")
    db = SessionLocal()
    try:
        # Buscar productos bajo mínimos
        low_stock_items = db.query(Inventory).options(
            joinedload(Inventory.warehouse),
            joinedload(Inventory.supplier)
        ).filter(
            Inventory.quantity <= Inventory.stock_minimo,
            Inventory.stock_minimo > 0  # Filtrar los que tienen mínimo configurado
        ).all()
        
        if not low_stock_items:
            logger.info("No hay productos bajo stock mínimo.")
            return
        
        logger.info(f"Encontrados {len(low_stock_items)} productos bajo stock mínimo")

        # Generar alertas y enviar correos a usuarios relevantes (ej: jefe de almacén)
        admin_emails = [user.email for user in db.query(User).filter(User.role_id == 1, User.active == True).all() if user.email] # Suponiendo rol 1 es admin
        
        if not admin_emails:
            logger.warning("No se encontraron administradores con correo para notificaciones de stock.")
        
        for item in low_stock_items:
            message = (f"ALERTA DE STOCK: El producto '{item.name}' ({item.item_code}) "
                       f"en el almacén '{item.warehouse.name if item.warehouse else 'N/A'}' "
                       f"está bajo el stock mínimo. Cantidad actual: {item.quantity}, Mínimo: {item.stock_minimo}.")
            save_alert(db, "stock", message, "inventory", item.id, "danger")

            if admin_emails:
                subject = f"ALERTA CRÍTICA: Stock Bajo para {item.name}"
                html_content = (f"<p>Estimado administrador,</p>"
                                f"<p>Se ha detectado que el stock del producto <strong>'{item.name}' ({item.item_code})</strong> "
                                f"está por debajo de su mínimo establecido en el almacén "
                                f"<strong>'{item.warehouse.name if item.warehouse else 'N/A'}'</strong>.</p>"
                                f"<p><strong>Detalles:</strong></p>"
                                f"<ul>"
                                f"<li>Cantidad Actual: {item.quantity}</li>"
                                f"<li>Stock Mínimo: {item.stock_minimo}</li>"
                                f"<li>Proveedor Sugerido: {item.supplier.name if item.supplier else 'N/A'}</li>"
                                f"</ul>"
                                f"<p>Por favor, tome las acciones necesarias para reponer este artículo.</p>"
                                f"<p>Gracias.</p>")
                send_email(admin_emails, subject, html_content)
                
    except Exception as e:
        logger.error(f"Error en verificación de stock mínimo: {e}")
    finally:
        db.close()

def check_overdue_tasks():
    """
    Verifica órdenes de trabajo vencidas y genera alertas.
    """
    if not config["tasks"]["check_overdue"]["enabled"]:
        logger.info("Verificación de órdenes vencidas deshabilitada por configuración.")
        return
    
    logger.info("Verificando órdenes de trabajo vencidas...")
    db = SessionLocal()
    try:
        # Fecha actual menos margen de días (ej: 3 días vencida)
        today = datetime.utcnow().date()
        overdue_threshold = today - timedelta(days=3) # Considerar vencidas las creadas hace más de 3 días

        # Buscar órdenes vencidas (creadas hace más de X días y aún pendientes/en curso)
        overdue_orders = db.query(WorkOrder).options(
            joinedload(WorkOrder.machine_obj),
            joinedload(WorkOrder.assigned_to),
            joinedload(WorkOrder.section)
        ).filter(
            WorkOrder.status.in_(["Pendiente", "En curso"]),
            func.date(WorkOrder.created_at) <= overdue_threshold
        ).all()
        
        if not overdue_orders:
            logger.info("No hay órdenes de trabajo vencidas.")
            return
        
        logger.info(f"Encontradas {len(overdue_orders)} órdenes de trabajo vencidas")

        for order in overdue_orders:
            message = (f"ORDEN VENCIDA: La orden '{order.order_number}' ({order.title}) "
                       f"para la máquina '{order.machine_obj.name if order.machine_obj else 'N/A'}' "
                       f"está vencida. Fue creada el {order.created_at.strftime('%Y-%m-%d')}.")
            save_alert(db, "work_order", message, "work_order", order.id, "danger", 
                       users=[order.assigned_to_id] if order.assigned_to_id else None)
            
            # Notificar al asignado y/o a un supervisor
            recipients_emails = []
            if order.assigned_to and order.assigned_to.email:
                recipients_emails.append(order.assigned_to.email)
            
            # Podrías añadir lógica para encontrar supervisores de la sección/línea y notificarlos también
            # Ejemplo: supervisor_emails = [user.email for user in db.query(User).filter(User.role_id == ROL_SUPERVISOR, User.active == True).all() if user.email]
            
            if recipients_emails: # or supervisor_emails:
                subject = f"ALERTA: Orden de Trabajo Vencida - {order.order_number}"
                html_content = (f"<p>Hola,</p>"
                                f"<p>La orden de trabajo <strong>'{order.order_number}' - '{order.title}'</strong> "
                                f"para la máquina <strong>'{order.machine_obj.name if order.machine_obj else 'N/A'}'</strong> "
                                f"está vencida.</p>"
                                f"<p><strong>Detalles:</strong></p>"
                                f"<ul>"
                                f"<li>Fecha de Creación: {order.created_at.strftime('%Y-%m-%d %H:%M')}</li>"
                                f"<li>Asignada a: {order.assigned_to.username if order.assigned_to else 'N/A'}</li>"
                                f"<li>Estado Actual: {order.status}</li>"
                                f"</ul>"
                                f"<p>Por favor, prioriza la resolución de esta tarea.</p>")
                send_email(recipients_emails, subject, html_content) # Combine recipients_emails and supervisor_emails if needed
                
    except Exception as e:
        logger.error(f"Error en verificación de órdenes vencidas: {e}")
    finally:
        db.close()

def generate_weekly_metrics():
    """
    Genera métricas semanales de rendimiento e informes.
    """
    if not config["tasks"]["generate_metrics"]["enabled"]:
        logger.info("Generación de métricas semanales deshabilitada por configuración.")
        return
    
    logger.info("Generando métricas semanales de rendimiento...")
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        # Calcula el inicio y fin de la semana anterior (ej. de Lunes a Domingo)
        week_start = today - timedelta(days=today.weekday() + 7)  # Lunes de la semana anterior
        week_end = week_start + timedelta(days=6)  # Domingo de la semana anterior
        
        logger.info(f"Métricas generadas para período: {week_start} - {week_end}")
        
        # Aquí iría la lógica real para calcular métricas:
        # - Número de órdenes completadas
        # - Tiempo medio de resolución
        # - Costos de mantenimiento (si se registran)
        # - Disponibilidad de máquinas
        # - etc.
        # Estas métricas se guardarían en un modelo de 'Reporte' o 'Métrica'
        
        # Ejemplo: Contar órdenes completadas en la semana
        completed_orders_count = db.query(WorkOrder).filter(
            WorkOrder.status == "Completada",
            func.date(WorkOrder.completion_date) >= week_start,
            func.date(WorkOrder.completion_date) <= week_end
        ).count()
        logger.info(f"Órdenes completadas la semana pasada ({week_start} - {week_end}): {completed_orders_count}")

        # Podrías generar un informe y enviarlo por correo
        # report_content = f"<h1>Informe Semanal de Mantenimiento ({week_start} - {week_end})</h1><p>...</p>"
        # send_email(admin_emails, "Informe Semanal de Mantenimiento", report_content)
        
    except Exception as e:
        logger.error(f"Error generando métricas semanales: {e}")
    finally:
        db.close()

def update_maintenance_backlog():
    """
    Revisa el backlog de mantenimiento y actualiza prioridades o convierte ítems en órdenes automáticamente.
    """
    if not config["tasks"]["maintenance_backup"]["enabled"]:
        logger.info("Actualización de backlog de mantenimiento deshabilitada por configuración.")
        return
    
    logger.info("Actualizando backlog de mantenimiento...")
    db = SessionLocal()
    try:
        # Buscar elementos pendientes del backlog
        pending_items = db.query(MaintenanceBacklog).filter(
            MaintenanceBacklog.status == BacklogStatus.pending
        ).all()
        
        logger.info(f"Elementos en backlog pendientes: {len(pending_items)}")

        for item in pending_items:
            # Ejemplo de lógica: si la prioridad es alta y no tiene OT asociada, crear una
            if item.priority == "Alta" and item.work_order_id is None:
                logger.info(f"Backlog Item '{item.description}' (ID: {item.id}) tiene prioridad Alta. Evaluando creación de OT.")
                # Aquí replicarías parte de la lógica de generate_daily_orders para crear una WorkOrder
                # Necesitarías información de máquina, usuario/rol, etc. que debería estar en el item de backlog o ser derivable
                # Por simplicidad, solo loguearemos la intención por ahora.
                # Puedes considerar añadir un campo 'machine_id' al modelo MaintenanceBacklog si es necesario.
                
                # new_order = WorkOrder(...)
                # db.add(new_order)
                # item.work_order_id = new_order.id
                # item.status = BacklogStatus.converted # O un nuevo estado
                # db.commit()
                logger.info(f"Podría generarse una orden de trabajo para el backlog item {item.id}.")
            
            # Podrías tener lógica para ajustar prioridades con el tiempo
            # item.priority = "Muy Alta" if (datetime.utcnow().date() - item.created_at.date()).days > 30 else item.priority
            # db.commit()

    except Exception as e:
        logger.error(f"Error actualizando backlog de mantenimiento: {e}")
        db.rollback()
    finally:
        db.close()

# ================================================
# 5. FUNCIÓN DE PREDICCIONES DE IA CON CONFIGURACIÓN DINÁMICA
# ================================================

def run_ai_predictions():
    """
    ✅ FUNCIÓN CORREGIDA - Usando el endpoint CORRECTO con /api/ai/
    """
    if not config["tasks"]["ai_predictions"]["enabled"]:
        logger.info("❌ Predicciones de IA deshabilitadas por configuración.")
        return {"status": "skipped", "message": "Predicciones de IA deshabilitadas"}
    
    logger.info("🚀 INICIANDO PREDICCIONES AUTOMÁTICAS (endpoint correcto)...")
    
    try:
        # ✅ OBTENER CONFIGURACIÓN
        ai_config = get_ai_config_from_json()
        max_machines = ai_config.get("max_machines_per_cycle", 3)
        confidence_threshold = ai_config.get("confidence_threshold", 60)
        priority_sections = ai_config.get("priority_sections", "1,4,7")
        
        logger.info(f"📊 Configuración: max_machines={max_machines}, umbral={confidence_threshold}%, secciones={priority_sections}")
        
        # ✅ OBTENER MÁQUINAS CON DATOS SUFICIENTES
        db = SessionLocal()
        try:
            # Convertir priority_sections a lista
            if isinstance(priority_sections, str):
                section_ids = [int(x.strip()) for x in priority_sections.split(",") if x.strip().isdigit()]
            else:
                section_ids = [1, 4, 7]
            
            # Consulta para encontrar máquinas con fallos recientes
            from sqlalchemy import text
            machines_query = text("""
                SELECT DISTINCT m.id, m.nombre, m.section_id,
                       COUNT(wo.id) as total_ordenes,
                       COUNT(CASE WHEN wo.work_type = 'Correctivo' THEN 1 END) as total_fallos
                FROM machines m
                INNER JOIN work_orders wo ON m.id = wo.machine_id
                WHERE wo.created_at >= NOW() - INTERVAL '90 days'
                AND wo.status = 'Cerrada'
                AND m.section_id IN :section_ids
                GROUP BY m.id, m.nombre, m.section_id
                HAVING COUNT(wo.id) >= 2 
                AND COUNT(CASE WHEN wo.work_type = 'Correctivo' THEN 1 END) >= 1
                ORDER BY COUNT(CASE WHEN wo.work_type = 'Correctivo' THEN 1 END) DESC
                LIMIT :max_machines
            """)
            
            machines_data = db.execute(machines_query, {
                "section_ids": tuple(section_ids),
                "max_machines": max_machines
            }).fetchall()
            
            if not machines_data:
                logger.info("ℹ️ No se encontraron máquinas para analizar")
                return {"status": "success", "message": "No hay máquinas para analizar"}
            
            logger.info(f"📊 Máquinas encontradas para análisis: {len(machines_data)}")
            
            # ✅ EJECUTAR PREDICCIÓN PARA CADA MÁQUINA CON EL ENDPOINT CORRECTO
            import requests
            
            successful_predictions = 0
            errors = []
            
            for machine_data in machines_data:
                try:
                    machine_id = machine_data.id
                    machine_name = machine_data.nombre
                    
                    logger.info(f"🔮 Ejecutando predicción para: {machine_name} (ID: {machine_id})")
                    
                    # ✅ USAR EL ENDPOINT CORRECTO CON /api/ai/
                    url = f"http://127.0.0.1:8000/api/ai/predict-maintenance/{machine_id}"
                    
                    # Parámetros que usa el frontend
                    payload = {
                        "days_ahead": 30,
                        "confidence_threshold": confidence_threshold
                    }
                    
                    # ✅ GENERAR TOKEN DE AUTENTICACIÓN
                    system_user = db.query(User).filter(User.role_id == 1).first()
                    if not system_user:
                        logger.error("❌ No se encontró usuario del sistema para autenticación")
                        errors.append(f"No se pudo autenticar para {machine_name}")
                        continue
                    
                    # Crear token de acceso
                    access_token = create_access_token(
                        data={"sub": system_user.username},
                        expires_delta=timedelta(hours=1)
                    )
                    
                    headers = {
                        "Content-Type": "application/json",
                        "User-Agent": "Scheduler-Automatic",
                        "Accept": "application/json",
                        "Authorization": f"Bearer {access_token}"  # ✅ Token añadido
                    }
                    
                    logger.info(f"🌐 Llamando a: {url} con usuario: {system_user.username}")
                    
                    # Hacer la llamada HTTP
                    response = requests.post(url, json=payload, headers=headers, timeout=120)
                    
                    logger.info(f"📊 Response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Verificar si la predicción fue exitosa
                        if result.get("success", False):
                            successful_predictions += 1
                            logger.info(f"✅ Predicción exitosa para {machine_name}: {result.get('message', 'Predicción completada')}")
                        else:
                            logger.warning(f"⚠️ Predicción no exitosa para {machine_name}: {result.get('message', 'Sin mensaje')}")
                            
                    elif response.status_code == 401:
                        error_msg = f"No autorizado para {machine_name} - Se requiere autenticación"
                        logger.error(f"❌ {error_msg}")
                        errors.append(error_msg)
                        # Problema de autenticación, salir del bucle
                        break
                        
                    elif response.status_code == 404:
                        error_msg = f"Endpoint no encontrado para {machine_name}"
                        logger.error(f"❌ {error_msg}")
                        errors.append(error_msg)
                        
                    elif response.status_code == 503:
                        error_msg = f"Servicio de IA no disponible para {machine_name}"
                        logger.error(f"❌ {error_msg}")
                        errors.append(error_msg)
                        
                    else:
                        error_msg = f"HTTP {response.status_code} para {machine_name}: {response.text[:100]}"
                        logger.error(f"❌ {error_msg}")
                        errors.append(error_msg)
                        
                except requests.exceptions.Timeout:
                    error_msg = f"Timeout para {machine_data.nombre}"
                    logger.error(f"❌ {error_msg}")
                    errors.append(error_msg)
                    
                except Exception as e:
                    error_msg = f"Error en {machine_data.nombre}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    errors.append(error_msg)
            
            # ✅ RESULTADO FINAL
            result_message = f"🎯 Predicciones automáticas completadas: {successful_predictions}/{len(machines_data)} exitosas"
            logger.info(result_message)
            
            if successful_predictions > 0:
                return {
                    "status": "success", 
                    "message": result_message,
                    "successful_predictions": successful_predictions,
                    "total_machines": len(machines_data),
                    "errors": errors
                }
            elif len(errors) == 0:
                return {
                    "status": "warning",
                    "message": "No se generaron predicciones exitosas",
                    "total_machines": len(machines_data)
                }
            else:
                return {
                    "status": "partial",
                    "message": f"Errores en predicciones: {len(errors)}",
                    "errors": errors
                }
        
        finally:
            db.close()
        
    except Exception as e:
        error_msg = f"❌ ERROR GENERAL EN PREDICCIONES AUTOMÁTICAS: {e}"
        logger.error(error_msg)
        return {"status": "error", "message": str(e)}

def cleanup_old_audit_logs():
    """
    Limpia logs de auditoría antiguos. Esta tarea se ejecuta mensualmente.
    """
    logger.info("Ejecutando limpieza de logs de auditoría...")
    db = SessionLocal()
    try:
        # Aquí implementarías la lógica de limpieza real para tu tabla de auditoría
        # Por ejemplo, eliminar logs más antiguos de 90 días
        # Asumiendo que tienes un modelo `AuditLog`
        # from src.models.audit_log import AuditLog
        
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        # Ejemplo: delete_count = db.query(AuditLog).filter(AuditLog.timestamp < cutoff_date).delete()
        # db.commit()
        # logger.info(f"Se eliminaron {delete_count} registros de auditoría anteriores a {cutoff_date.strftime('%Y-%m-%d')}")
        
        logger.info(f"Simulación de limpieza de auditoría: se eliminarían logs anteriores a {cutoff_date.strftime('%Y-%m-%d')}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error en limpieza de auditoría: {e}")
    finally:
        db.close()

# ================================================
# 6. Funciones de Programación del Scheduler CON CONFIGURACIÓN DINÁMICA
# ================================================

def schedule_auto_cleanup():
    """
    Programa la limpieza automática de otros tipos de datos (configurada desde src.routes).
    """
    try:
        # Importar la función y configuración desde routes si existen
        # Esto podría ser un punto de acoplamiento fuerte, considera si es lo ideal.
        # Si 'execute_auto_cleanup' es una función de dominio, debería estar aquí o en un módulo de servicios.
        from src.routes import execute_auto_cleanup, AUTO_CLEANUP_CONFIG
        
        # Remover trabajos existentes de limpieza para evitar duplicados al reprogramar
        for job_id in ['auto_cleanup_daily', 'auto_cleanup_every3days', 'auto_cleanup_weekly']:
            try:
                scheduler.remove_job(job_id)
            except Exception:
                pass  # El trabajo no existía, no hay problema
        
        if not AUTO_CLEANUP_CONFIG.enabled:
            logger.info("Limpieza automática (desde routes) desactivada por configuración.")
            return
        
        # Programar según la frecuencia configurada
        if AUTO_CLEANUP_CONFIG.frequency == 'daily':
            scheduler.add_job(
                execute_auto_cleanup,
                'cron',
                hour=3,
                minute=0,
                id='auto_cleanup_daily',
                replace_existing=True
            )
            logger.info("Limpieza automática (desde routes) programada: diariamente a las 3:00 AM")
            
        elif AUTO_CLEANUP_CONFIG.frequency == 'every3days':
            scheduler.add_job(
                execute_auto_cleanup,
                'cron',
                day='*/3',
                hour=3,
                minute=0,
                id='auto_cleanup_every3days',
                replace_existing=True
            )
            logger.info("Limpieza automática (desde routes) programada: cada 3 días a las 3:00 AM")
            
        elif AUTO_CLEANUP_CONFIG.frequency == 'weekly':
            scheduler.add_job(
                execute_auto_cleanup,
                'cron',
                day_of_week=0,  # Lunes (0=Lunes, 6=Domingo)
                hour=3,
                minute=0,
                id='auto_cleanup_weekly',
                replace_existing=True
            )
            logger.info("Limpieza automática (desde routes) programada: semanalmente los lunes a las 3:00 AM")
            
    except ImportError:
        logger.warning("No se pudo importar 'execute_auto_cleanup' o 'AUTO_CLEANUP_CONFIG' desde src.routes. "
                       "La limpieza automática configurable no se programará.")
    except Exception as e:
        logger.error(f"Error al programar limpieza automática desde routes: {e}")

def trigger_ai_predictions_manually():
    """
    Función trigger manual para predicciones de IA, útil para endpoints API.
    """
    logger.info("🔄 Predicciones de IA ejecutadas manualmente")
    try:
        result = run_ai_predictions()
        return result
    except Exception as e:
        logger.error(f"Error en predicciones manuales: {e}")
        return {"status": "error", "message": str(e)}

def schedule_tasks():
    """
    ✅ Programa todas las tareas configuradas en el scheduler - VERSIÓN DEFINITIVA
    """
    global config
    
    # Limpiar todos los trabajos existentes
    scheduler.remove_all_jobs()
    logger.info("🧹 Trabajos existentes del scheduler eliminados")

    # ✅ RECARGAR CONFIGURACIÓN DESDE ARCHIVO
    try:
        CONFIG_FILE = "scheduler_config.json"
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                loaded_config = json.load(f)
                
                # Actualizar configuración global
                def update_dict(d, u):
                    for k, v in u.items():
                        if isinstance(v, dict) and k in d:
                            d[k] = update_dict(d.get(k, {}), v)
                        else:
                            d[k] = v
                    return d
                
                config = update_dict(config, loaded_config)
                logger.info(f"✅ Configuración recargada desde {CONFIG_FILE}")
                
                # Log específico para IA
                ai_cron = config.get("tasks", {}).get("ai_predictions", {}).get("cron", "No configurado")
                ai_enabled = config.get("tasks", {}).get("ai_predictions", {}).get("enabled", False)
                logger.info(f"🤖 IA - Habilitada: {ai_enabled}, CRON: {ai_cron}")
                
    except Exception as e:
        logger.error(f"❌ Error recargando configuración: {e}")
    
    # ✅ PROGRAMAR TAREA DE LIMPIEZA (FIJA)
    try:
        scheduler.add_job(
            cleanup_old_audit_logs,
            'cron',
            day=1,
            hour=2,
            minute=0,
            id='cleanup_audit_logs',
            replace_existing=True
        )
        logger.info("✅ Tarea de limpieza programada: día 1 cada mes a las 2:00 AM")
    except Exception as e:
        logger.error(f"❌ Error programando limpieza: {e}")
    
    # ✅ PROGRAMAR TAREAS DINÁMICAS
    tasks_to_schedule = {
        "generate_orders": {"func": generate_daily_orders, "id": "generate_daily_orders"},
        "check_upcoming": {"func": check_upcoming_maintenance, "id": "check_upcoming_maintenance"},
        "check_stock": {"func": check_low_stock, "id": "check_low_stock"},
        "check_overdue": {"func": check_overdue_tasks, "id": "check_overdue_tasks"},
        "generate_metrics": {"func": generate_weekly_metrics, "id": "generate_weekly_metrics"},
        "maintenance_backup": {"func": update_maintenance_backlog, "id": "update_maintenance_backlog"},
        "ai_predictions": {"func": run_ai_predictions, "id": "run_ai_predictions"},  # ✅ FUNCIÓN CORREGIDA
    }

    scheduled_count = 0
    
    for task_name, details in tasks_to_schedule.items():
        task_config = config.get("tasks", {}).get(task_name, {})
        
        if task_config.get("enabled", False):
            cron_expr = task_config.get("cron", "0 8 * * *")
            
            try:
                # ✅ USAR CronTrigger.from_crontab PARA COMPATIBILIDAD
                from apscheduler.triggers.cron import CronTrigger
                
                scheduler.add_job(
                    details["func"],
                    CronTrigger.from_crontab(cron_expr),
                    id=details["id"],
                    replace_existing=True,
                    max_instances=1,  # ✅ EVITAR MÚLTIPLES INSTANCIAS
                    misfire_grace_time=300  # ✅ 5 MINUTOS DE GRACIA
                )
                
                logger.info(f"✅ Tarea '{details['id']}' programada con CRON: {cron_expr}")
                scheduled_count += 1
                
                # Log especial para IA
                if task_name == "ai_predictions":
                    logger.info(f"🤖 PREDICCIONES IA PROGRAMADAS CADA: {cron_expr}")
                
            except Exception as e:
                logger.error(f"❌ Error programando '{task_name}' con CRON '{cron_expr}': {e}")
                
                # Intentar con CRON por defecto
                try:
                    default_cron = "0 8 * * *"
                    scheduler.add_job(
                        details["func"],
                        CronTrigger.from_crontab(default_cron),
                        id=details["id"],
                        replace_existing=True,
                        max_instances=1
                    )
                    logger.info(f"⚠️ Tarea '{details['id']}' programada con CRON por defecto: {default_cron}")
                    scheduled_count += 1
                except Exception as e2:
                    logger.error(f"❌ Error fatal programando '{task_name}': {e2}")
        else:
            logger.info(f"⚠️ Tarea '{details['id']}' DESHABILITADA")
    
    # ✅ PROGRAMAR LIMPIEZA AUTOMÁTICA (si existe)
    try:
        schedule_auto_cleanup()
    except Exception as e:
        logger.warning(f"⚠️ No se pudo programar limpieza automática: {e}")
    
    total_jobs = len(scheduler.get_jobs())
    logger.info(f"✅ TOTAL TAREAS PROGRAMADAS: {total_jobs}")
    
    # ✅ MOSTRAR RESUMEN DETALLADO
    logger.info("📋 RESUMEN DE TAREAS PROGRAMADAS:")
    for job in scheduler.get_jobs():
        try:
            next_run = "N/A"
            if hasattr(job, 'next_run_time') and job.next_run_time:
                next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
            
            logger.info(f"  📌 {job.id}: próxima ejecución {next_run}")
            
            # Log especial para IA
            if job.id == "run_ai_predictions":
                logger.info(f"  🤖 PREDICCIONES IA: {next_run}")
                
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo detalles para job {job.id}: {e}")
    
    return total_jobs

# ================================================
# 7. Inicio del Scheduler
# ================================================

# ✅ FUNCIÓN PARA INICIAR SCHEDULER CORRECTAMENTE
def start_scheduler():
    """Inicia el BackgroundScheduler de forma segura."""
    if not scheduler.running:
        try:
            # Programar tareas ANTES de iniciar
            task_count = schedule_tasks()
            
            # Iniciar scheduler
            scheduler.start()
            
            logger.info(f"✅ SCHEDULER INICIADO CORRECTAMENTE con {task_count} tareas")
            
            # ✅ VERIFICAR QUE LAS TAREAS ESTÁN PROGRAMADAS
            jobs = scheduler.get_jobs()
            ai_job = None
            for job in jobs:
                if job.id == "run_ai_predictions":
                    ai_job = job
                    break
            
            if ai_job:
                next_ai = ai_job.next_run_time.strftime("%H:%M:%S") if ai_job.next_run_time else "N/A"
                logger.info(f"🤖 PRÓXIMA PREDICCIÓN IA: {next_ai}")
            else:
                logger.error("❌ TAREA DE IA NO ENCONTRADA EN SCHEDULER")
            
        except Exception as e:
            logger.error(f"❌ Error al iniciar scheduler: {e}")
    else:
        logger.info("ℹ️ El scheduler ya está en ejecución")
        
        # Verificar tareas IA
        jobs = scheduler.get_jobs()
        ai_jobs = [job for job in jobs if "ai" in job.id.lower() or "prediction" in job.id.lower()]
        logger.info(f"🤖 Tareas de IA encontradas: {len(ai_jobs)}")
        for job in ai_jobs:
            next_run = job.next_run_time.strftime("%H:%M:%S") if job.next_run_time else "N/A"
            logger.info(f"  - {job.id}: {next_run}")

# ✅ FUNCIÓN PARA STOP SCHEDULER
def stop_scheduler():
    """Detiene el BackgroundScheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("✅ Scheduler detenido")
    else:
        logger.info("ℹ️ El scheduler no está en ejecución")

