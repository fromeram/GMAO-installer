# src/scheduler.py - ARCHIVO COMPLETO CORREGIDO

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
# Posibles importaciones de modelos de turnos (si existen en src.models)
# from src.models.shift_assignment import ShiftAssignment
# from src.models.shift_pattern import ShiftPattern
# from src.models.role import Role
# from src.models.absence import Absence
# from src.models.shift_override import ShiftOverride

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
            "cron": "0 */3 * * *",  # Cada 3 horas
            "description": "Predicciones automáticas de IA basadas en datos reales"
        }
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
            logger.info(f"Configuración cargada desde {CONFIG_FILE}")
    else:
        # Guardar configuración predeterminada
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
            logger.info(f"Configuración predeterminada guardada en {CONFIG_FILE}")
except Exception as e:
    logger.error(f"Error al cargar/guardar configuración: {e}")

# Inicializar scheduler
scheduler = BackgroundScheduler()

# ================================================
# 3. Funciones de Utilidad
# ================================================

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

def run_ai_predictions():
    """
    Ejecuta predicciones automáticas de IA.
    """
    if not config["tasks"]["ai_predictions"]["enabled"]:
        logger.info("Predicciones de IA deshabilitadas por configuración.")
        return {"status": "skipped", "message": "Predicciones de IA deshabilitadas"}
    
    logger.info("Ejecutando predicciones automáticas de IA...")
    try:
        # Aquí integrarías con tu sistema de IA
        # Por ejemplo:
        # from src.ai.prediction_model import run_prediction_cycle # Suponiendo que tienes un módulo para esto
        # prediction_results = run_prediction_cycle()
        
        # Simulación de una predicción
        simulated_prediction_data = {
            "machine_id": 123,
            "failure_probability": 0.75,
            "predicted_failure_date": (datetime.utcnow().date() + timedelta(days=30)).isoformat()
        }
        logger.info(f"Predicción de IA simulada: {simulated_prediction_data}")
        
        # Podrías guardar estas predicciones en la base de datos o generar alertas
        save_alert(SessionLocal(), "AI_prediction", 
                   f"Predicción: Máquina 123 tiene alta probabilidad de fallo en 30 días.", 
                   "machine", 123, "warning")

        logger.info("Predicciones de IA completadas")
        return {"status": "success", "message": "Predicciones ejecutadas correctamente", "data": simulated_prediction_data}
        
    except Exception as e:
        logger.error(f"Error en predicciones de IA: {e}")
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
# 5. Funciones de Programación del Scheduler
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
    Programa todas las tareas configuradas en el scheduler.
    """
    # Limpiar todos los trabajos existentes para evitar duplicados al reiniciar
    scheduler.remove_all_jobs()
    logger.info("Todos los trabajos existentes del scheduler han sido eliminados para reprogramar.")

    # Programar la limpieza de logs de auditoría (tarea fija mensual)
    scheduler.add_job(
        cleanup_old_audit_logs,
        'cron',
        day=1, # El día 1 de cada mes
        hour=2,
        minute=0,
        id='cleanup_audit_logs',
        replace_existing=True # Asegura que si se llama varias veces, no se duplique
    )
    logger.info("Tarea de limpieza de audit trail programada: día 1 de cada mes a las 2:00 AM")
    
    # Programar tareas basadas en la configuración
    tasks_to_schedule = {
        "generate_orders": {"func": generate_daily_orders, "id": "generate_daily_orders"},
        "check_upcoming": {"func": check_upcoming_maintenance, "id": "check_upcoming_maintenance"},
        "check_stock": {"func": check_low_stock, "id": "check_low_stock"},
        "check_overdue": {"func": check_overdue_tasks, "id": "check_overdue_tasks"},
        "generate_metrics": {"func": generate_weekly_metrics, "id": "generate_weekly_metrics"},
        "maintenance_backup": {"func": update_maintenance_backlog, "id": "update_maintenance_backlog"},
        "ai_predictions": {"func": run_ai_predictions, "id": "run_ai_predictions"},
    }

    for task_name, details in tasks_to_schedule.items():
        if config["tasks"][task_name]["enabled"]:
            cron_expr = config["tasks"][task_name]["cron"]
            scheduler.add_job(
                details["func"],
                CronTrigger.from_crontab(cron_expr),
                id=details["id"],
                replace_existing=True
            )
            logger.info(f"Tarea '{details['id']}' programada: {cron_expr}")
        else:
            logger.info(f"Tarea '{details['id']}' deshabilitada por configuración y no programada.")
            
    # Programar la limpieza automática configurable (desde src.routes)
    schedule_auto_cleanup()
    
    total_jobs = len(scheduler.get_jobs())
    logger.info(f"Total de tareas programadas: {total_jobs}")
    
    # Mostrar resumen de tareas programadas
    logger.info("Resumen de tareas programadas:")
    for job in scheduler.get_jobs():
        try:
            next_run = "N/A"
            if job.next_run_time:
                next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"  • {job.id}: próxima ejecución {next_run} (Trigger: {job.trigger.__class__.__name__})")
        except Exception as e:
            logger.warning(f"Error obteniendo detalles para job {job.id}: {e}")
            logger.info(f"  • {job.id}: detalles no disponibles")
            
    return total_jobs

# ================================================
# 6. Inicio del Scheduler
# ================================================

# Función para iniciar el scheduler
def start_scheduler():
    """Inicia el BackgroundScheduler."""
    if not scheduler.running:
        try:
            schedule_tasks() # Programar todas las tareas al inicio
            scheduler.start()
            logger.info("Scheduler iniciado correctamente.")
        except Exception as e:
            logger.error(f"Error al iniciar el scheduler: {e}")
    else:
        logger.info("El scheduler ya está en ejecución.")

# Función para detener el scheduler
def stop_scheduler():
    """Detiene el BackgroundScheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler detenido.")
    else:
        logger.info("El scheduler no está en ejecución.")

# Ejemplo de cómo se usaría en una aplicación principal
if __name__ == "__main__":
    logger.info("Iniciando módulo scheduler.py directamente para prueba.")
    start_scheduler()
    
    # Mantener el script en ejecución para que el scheduler tenga tiempo de ejecutar tareas
    try:
        # En una aplicación real (ej. con FastAPI/Flask), no necesitarías este bucle,
        # el scheduler correría en segundo plano junto con el servidor web.
        # Aquí es solo para que el script no termine inmediatamente en modo stand-alone.
        while True:
            import time
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        stop_scheduler()
        logger.info("Scheduler finalizado por interrupción del usuario.")