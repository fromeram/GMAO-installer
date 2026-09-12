# routers/helpers.py — Shared helper functions, dependencies, and role constants
import logging
from datetime import datetime, timedelta, date, time
from typing import List, Optional, Union, Literal, Any, Dict, Tuple
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from src.database import get_db
from src.auth import get_current_user
from src.models.user import User
from src.models.work_order import WorkOrder
from src.models.work_order_technician import WorkOrderTechnician
from src.models.maintenance import Maintenance
from src.models.task_list import TaskList
from src.models.task_step import TaskStep
from src.models.checklist_progress import ChecklistProgress
from src.models.shift_pattern import ShiftPattern
from src.models.shift_assignment import ShiftAssignment
from src.models.absence import Absence
from src.models.shift_override import ShiftOverride

logger = logging.getLogger(__name__)

PROXY_URL = "http://192.168.1.62:5000"

VACATION_MANAGER_ROLES = ["Administrador", "Jefe de Mantenimiento", "Jefe Sección", "Calidad"]
MANAGER_ROLES = ["Administrador", "Jefe de Mantenimiento", "Jefe Sección"]
INVENTORY_ACCESS_ROLES = ["Administrador", "Jefe de Mantenimiento", "Jefe Sección", "Calidad", "Contabilidad"]
FINANCIAL_ACCESS_ROLES = ["Administrador", "Jefe de Mantenimiento", "Calidad", "Contabilidad"]
PRODUCT_EDIT_ROLES = ["Administrador", "Jefe de Mantenimiento"]
RESTRICTED_WORKER_ROLES = ["Mecánico"]
CONSULTANT_ROLES = ["Calidad", "Contabilidad"]
CALENDAR_ACCESS_ROLES = ["Administrador", "Jefe de Mantenimiento", "Jefe Sección", "Mecánico", "Calidad", "Contabilidad"]

def get_inventory_user(current_user: User = Depends(get_current_user)):
    """Dependencia para usuarios que pueden acceder al inventario y reportes"""
    if current_user.role.nombre not in INVENTORY_ACCESS_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder al inventario"
        )
    return current_user

def get_financial_user(current_user: User = Depends(get_current_user)):
    """Dependencia para usuarios que pueden ver información financiera"""
    if current_user.role.nombre not in FINANCIAL_ACCESS_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a información financiera"
        )
    return current_user

def get_product_editor(current_user: User = Depends(get_current_user)):
    """Dependencia para usuarios que pueden crear/editar productos"""
    if current_user.role.nombre not in PRODUCT_EDIT_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para crear o editar productos"
        )
    return current_user

def get_active_order_for_maintenance(maintenance_id: int, db: Session) -> Optional['WorkOrder']:
    """
    Obtiene la orden activa (Pendiente/En Progreso) para un mantenimiento específico.
    Returns None si no hay órdenes activas.
    """
    from src.models.work_order import WorkOrder
    
    return db.query(WorkOrder).filter(
        WorkOrder.generated_from_maintenance_id == maintenance_id,
        WorkOrder.status.in_(["Pendiente", "En Progreso"])
    ).first()

def get_all_orders_for_maintenance(maintenance_id: int, db: Session) -> List['WorkOrder']:
    """
    Obtiene TODAS las órdenes generadas por un mantenimiento (historial completo).
    """
    from src.models.work_order import WorkOrder
    
    return db.query(WorkOrder).filter(
        WorkOrder.generated_from_maintenance_id == maintenance_id
    ).order_by(WorkOrder.created_at.desc()).all()

def can_generate_new_order(maintenance_id: int, db: Session) -> Tuple[bool, str]:
    """
    Determina si se puede generar una nueva orden para un mantenimiento.
    Returns (can_generate: bool, reason: str)
    """
    active_order = get_active_order_for_maintenance(maintenance_id, db)
    
    if active_order:
        return False, f"Ya existe una orden activa: {active_order.order_number} (Estado: {active_order.status})"
    
    return True, "OK"

def get_maintenance_statistics(maintenance_id: int, db: Session) -> Dict[str, Any]:
    """
    Obtiene estadísticas completas de un mantenimiento.
    """
    from src.models.work_order import WorkOrder
    
    all_orders = get_all_orders_for_maintenance(maintenance_id, db)
    active_order = get_active_order_for_maintenance(maintenance_id, db)
    
    completed_orders = [o for o in all_orders if o.status == "Cerrada"]
    
    # Calcular tiempo promedio de resolución
    avg_resolution_time = None
    if completed_orders:
        resolution_times = []
        for order in completed_orders:
            if order.created_at and order.finished_at:
                duration = (order.finished_at - order.created_at).total_seconds() / 3600  # horas
                resolution_times.append(duration)
        
        if resolution_times:
            avg_resolution_time = sum(resolution_times) / len(resolution_times)
    
    return {
        "total_orders": len(all_orders),
        "completed_orders": len(completed_orders),
        "pending_orders": len([o for o in all_orders if o.status == "Pendiente"]),
        "in_progress_orders": len([o for o in all_orders if o.status == "En Progreso"]),
        "has_active_order": active_order is not None,
        "active_order_id": active_order.id if active_order else None,
        "can_generate_new": can_generate_new_order(maintenance_id, db)[0],
        "avg_resolution_hours": round(avg_resolution_time, 2) if avg_resolution_time else None,
        "last_order_date": all_orders[0].created_at.isoformat() if all_orders else None
    }


def get_current_shift_user(db: Session, section_id: Optional[int] = None) -> Optional[User]:
    """
    Obtiene el usuario que está actualmente en turno considerando la hora actual.
    VERSION CON DEBUG DETALLADO
    """
    try:
        from datetime import datetime, date, time
        
        current_datetime = datetime.now()
        current_date = current_datetime.date()
        current_time = current_datetime.time()
        
        # 🔍 DEBUG: Mostrar información actual
        logger.info(f"🕐 BUSCANDO USUARIO TURNO ACTUAL:")
        logger.info(f"   📅 Fecha actual: {current_date}")
        logger.info(f"   🕐 Hora actual: {current_time.strftime('%H:%M:%S')}")
        logger.info(f"   🏭 Sección filtro: {section_id}")
        
        # Configuración de horarios de turno
        shift_schedules = {
            'M': {'start': time(6, 0), 'end': time(14, 0)},    # Mañana: 06:00-14:00
            'T': {'start': time(14, 0), 'end': time(22, 0)},   # Tarde: 14:00-22:00
            'N': {'start': time(22, 0), 'end': time(6, 0)}     # Noche: 22:00-06:00
        }
        
        def is_time_in_shift(current_time: time, shift_code: str) -> bool:
            """Verifica si la hora actual está dentro del rango del turno"""
            if shift_code not in shift_schedules:
                logger.warning(f"❌ Código de turno desconocido: {shift_code}")
                return False
                
            start_time = shift_schedules[shift_code]['start']
            end_time = shift_schedules[shift_code]['end']
            
            # Turno normal (no cruza medianoche)
            if start_time <= end_time:
                result = start_time <= current_time < end_time
                logger.debug(f"   🔍 Turno {shift_code}: {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')} -> {'✅' if result else '❌'}")
                return result
            
            # Turno nocturno (cruza medianoche)
            else:
                result = current_time >= start_time or current_time < end_time
                logger.debug(f"   🔍 Turno {shift_code} (nocturno): {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')} -> {'✅' if result else '❌'}")
                return result
        
        # 1. Buscar todos los usuarios activos con asignación de turno
        query = db.query(ShiftAssignment).options(
            joinedload(ShiftAssignment.user),
            joinedload(ShiftAssignment.pattern)
        ).join(User).filter(
            User.active == True
        )
        
        # Filtrar por sección si se especifica
        if section_id:
            query = query.filter(User.section_id == section_id)
        
        assignments = query.all()
        
        logger.info(f"📋 Encontradas {len(assignments)} asignaciones de turno")
        
        if not assignments:
            logger.warning("❌ No se encontraron asignaciones de turno activas")
            return None
        
        # 2. Analizar cada asignación
        candidates = []
        
        for i, assignment in enumerate(assignments):
            logger.info(f"\n🔍 ANALIZANDO ASIGNACIÓN #{i+1}:")
            logger.info(f"   👤 Usuario: {assignment.user.username if assignment.user else 'None'}")
            logger.info(f"   🏭 Sección: {assignment.user.section_id if assignment.user else 'None'}")
            
            if not assignment.pattern or not assignment.pattern.pattern_sequence:
                logger.warning(f"   ❌ Sin patrón de turno válido")
                continue
            
            logger.info(f"   📋 Patrón: {assignment.pattern.name}")
            logger.info(f"   🔄 Secuencia: {assignment.pattern.pattern_sequence}")
            logger.info(f"   📅 Fecha referencia: {assignment.reference_date}")
            logger.info(f"   ➕ Offset: {assignment.offset_days}")
                
            # Calcular días desde la fecha de referencia
            days_since_reference = (current_date - assignment.reference_date).days
            logger.info(f"   📊 Días desde referencia: {days_since_reference}")
            
            # Aplicar offset y calcular posición en el ciclo
            cycle_position = (days_since_reference + assignment.offset_days) % assignment.pattern.cycle_length_days
            logger.info(f"   🎯 Posición en ciclo: {cycle_position}")
            
            # Obtener el código de turno para hoy
            today_shift_code = assignment.pattern.pattern_sequence[cycle_position]
            logger.info(f"   🕐 Turno programado HOY: {today_shift_code}")
            
            # 3. Verificar si hay override para este usuario en esta fecha
            override = db.query(ShiftOverride).filter(
                ShiftOverride.user_id == assignment.user_id,
                ShiftOverride.date == current_date
            ).first()
            
            if override:
                logger.info(f"   🔄 Override encontrado: {today_shift_code} -> {override.actual_shift_code}")
                today_shift_code = override.actual_shift_code
            
            # 4. Verificar si el usuario está ausente
            absence = db.query(Absence).filter(
                Absence.user_id == assignment.user_id,
                Absence.start_date <= current_date,
                Absence.end_date >= current_date
            ).first()
            
            if absence:
                logger.info(f"   🚫 Usuario ausente: {absence.absence_type}")
                continue
            
            # 5. Verificar si el turno está activo (no es descanso)
            if today_shift_code in ['D', 'F', 'L']:
                logger.info(f"   💤 Usuario en descanso/franco: {today_shift_code}")
                continue
            
            # 6. Verificar horario
            in_schedule = is_time_in_shift(current_time, today_shift_code)
            logger.info(f"   ⏰ ¿En horario activo? {'✅ SÍ' if in_schedule else '❌ NO'}")
            
            if in_schedule:
                candidates.append({
                    'user': assignment.user,
                    'shift_code': today_shift_code,
                    'assignment': assignment
                })
                logger.info(f"   ⭐ CANDIDATO VÁLIDO")
            else:
                logger.info(f"   ⏸️  Fuera de horario")
        
        # Mostrar resumen de candidatos
        logger.info(f"\n📊 RESUMEN:")
        logger.info(f"   🎯 Candidatos válidos: {len(candidates)}")
        
        if candidates:
            selected = candidates[0]  # Tomar el primero
            logger.info(f"   ✅ SELECCIONADO: {selected['user'].username} (Turno: {selected['shift_code']})")
            return selected['user']
        else:
            logger.warning(f"   ❌ No hay usuarios en turno activo ahora")
            return None
        
    except Exception as e:
        logger.error(f"💥 Error obteniendo usuario del turno actual: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        return None


def handle_checklist_integration(
    work_order_id: int,
    checklist_data: Dict[str, Any],
    current_user: User,
    db: Session
):
    """
    Maneja la creación o actualización del progreso de checklist integrado
    """
    if not checklist_data:
        return None
    
    try:
        from src.models.checklist_progress import ChecklistProgress
        
        # Buscar progreso existente
        existing_progress = db.query(ChecklistProgress).filter(
            ChecklistProgress.work_order_id == work_order_id,
            ChecklistProgress.task_list_id == checklist_data['task_list_id']
        ).first()
        
        if existing_progress:
            # Actualizar progreso existente
            existing_progress.steps_progress = checklist_data['steps_progress']
            existing_progress.progress_percent = checklist_data['progress_percent']
            existing_progress.is_completed = checklist_data['is_completed']
            existing_progress.total_elapsed_time = checklist_data['total_elapsed_time']
            existing_progress.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(existing_progress)
            return existing_progress
        else:
            # Crear nuevo progreso
            new_progress = ChecklistProgress(
                work_order_id=work_order_id,
                task_list_id=checklist_data['task_list_id'],
                steps_progress=checklist_data['steps_progress'],
                progress_percent=checklist_data['progress_percent'],
                is_completed=checklist_data['is_completed'],
                total_elapsed_time=checklist_data['total_elapsed_time'],
                created_by_id=current_user.id
            )
            
            db.add(new_progress)
            db.commit()
            db.refresh(new_progress)
            return new_progress
            
    except Exception as e:
        print(f"Error manejando checklist integrado: {e}")
        db.rollback()
        return None


def add_technician_to_order(
    db: Session, 
    work_order_id: int, 
    user_id: int, 
    role: str = "apoyo",
    assigned_by_id: Optional[int] = None,
    notes: Optional[str] = None
) -> WorkOrderTechnician:
    """Añade un técnico a una orden de trabajo"""
    
    # Verificar que la orden existe
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
    
    # Verificar que el usuario existe y está activo
    user = db.query(User).filter(User.id == user_id, User.active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o inactivo")
    
    # Verificar que no esté ya asignado
    existing = db.query(WorkOrderTechnician).filter(
        WorkOrderTechnician.work_order_id == work_order_id,
        WorkOrderTechnician.user_id == user_id,
        WorkOrderTechnician.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="El técnico ya está asignado a esta orden")
    
    # Si es principal, cambiar el principal anterior a apoyo
    if role == "principal":
        existing_principal = db.query(WorkOrderTechnician).filter(
            WorkOrderTechnician.work_order_id == work_order_id,
            WorkOrderTechnician.role == "principal",
            WorkOrderTechnician.is_active == True
        ).first()
        
        if existing_principal:
            existing_principal.role = "apoyo"
    
    # Crear la asignación
    assignment = WorkOrderTechnician(
        work_order_id=work_order_id,
        user_id=user_id,
        role=role,
        assigned_by_id=assigned_by_id,
        notes=notes
    )
    
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    return assignment

def get_order_technicians(db: Session, work_order_id: int, include_inactive: bool = False) -> List[dict]:
    """Obtiene todos los técnicos de una orden con sus detalles"""
    
    query = db.query(WorkOrderTechnician).options(
        joinedload(WorkOrderTechnician.technician)
    ).filter(WorkOrderTechnician.work_order_id == work_order_id)
    
    if not include_inactive:
        query = query.filter(WorkOrderTechnician.is_active == True)
    
    assignments = query.all()
    
    result = []
    for assignment in assignments:
        result.append({
            "assignment_id": assignment.id,
            "user_id": assignment.user_id,
            "username": assignment.technician.username if assignment.technician else None,
            "role": assignment.role,
            "hours_worked": float(assignment.hours_worked) if assignment.hours_worked else 0.0,
            "assigned_at": assignment.assigned_at,
            "is_active": assignment.is_active,
            "notes": assignment.notes
        })
    
    return sorted(result, key=lambda x: (x["role"] != "principal", x["assigned_at"]))


def generate_work_order_from_task_list(maintenance: Maintenance, db: Session) -> WorkOrder:
    """Genera una orden de trabajo detallada usando TaskList"""
    
    # --- Tu lógica para buscar el técnico asignado (INTACTA) ---
    logger.info(f"🔧 GENERANDO ORDEN PARA MANTENIMIENTO {maintenance.id}")
    logger.info(f"   📋 Usuario asignado en mantenimiento: {maintenance.assigned_user_id} (SERÁ IGNORADO)")
    logger.info(f"   👥 Rol asignado en mantenimiento: {maintenance.assigned_role_id} (SERÁ IGNORADO)")
    
    section_id = maintenance.machine.section_id if maintenance.machine else None
    logger.info(f"   🏭 Sección de la máquina: {section_id}")
    
    current_shift_user = get_current_shift_user(db, section_id)
    
    if current_shift_user:
        assigned_to_id = current_shift_user.id
        logger.info(f"   ✅ FORZANDO ASIGNACIÓN AL TURNO ACTUAL: {current_shift_user.username} (ID: {assigned_to_id})")
    else:
        logger.warning(f"   ❌ NO se encontró usuario en turno actual")
        assigned_to_id = maintenance.assigned_user_id
        if assigned_to_id:
            logger.info(f"   🔄 Fallback 1 - Usuario del mantenimiento: {assigned_to_id}")
        elif maintenance.assigned_role_id:
            user_with_role = db.query(User).filter(User.role_id == maintenance.assigned_role_id).first()
            assigned_to_id = user_with_role.id if user_with_role else None
            logger.info(f"   🔄 Fallback 2 - Usuario por rol: {assigned_to_id}")
        else:
            default_user = db.query(User).filter(User.active == True).first()
            assigned_to_id = default_user.id if default_user else 1
            logger.info(f"   🔄 Fallback 3 - Usuario por defecto: {assigned_to_id}")
    
    logger.info(f"   🎯 USUARIO FINAL ASIGNADO: {assigned_to_id}")
    
    # --- Tu lógica para crear el objeto work_order (INTACTA) ---
    if not maintenance.task_list_id:
        work_order = WorkOrder(
            title=maintenance.title,
            details=maintenance.description,
            work_type="Preventivo",
            machine_id=maintenance.machine_id,
            operator="Sistema Automático",
            assigned_to_id=assigned_to_id,
            section_id=maintenance.machine.section_id if maintenance.machine else None,
            line_id=maintenance.machine.line_id if maintenance.machine else None,
            status="Pendiente",
            created_at=datetime.utcnow()
        )
    else:
        task_list = db.query(TaskList).options(joinedload(TaskList.steps)).filter(TaskList.id == maintenance.task_list_id).first()

        if not task_list:
            logger.warning(f"TaskList {maintenance.task_list_id} no encontrada para mantenimiento {maintenance.id}")
            work_order = WorkOrder(
                title=maintenance.title,
                details=maintenance.description + "\n\n⚠️ Lista de tareas no encontrada",
                work_type="Preventivo",
                machine_id=maintenance.machine_id,
                operator="Sistema Automático",
                assigned_to_id=assigned_to_id,
                section_id=maintenance.machine.section_id if maintenance.machine else None,
                line_id=maintenance.machine.line_id if maintenance.machine else None,
                status="Pendiente",
                created_at=datetime.utcnow()
            )
        else:
            machine_name = maintenance.machine.nombre if maintenance.machine else "Máquina desconocida"
            title = f"[Preventivo] {task_list.name} - {machine_name}"
            
            # --- Tu construcción de detalles (INTACTA Y COMPLETA) ---
            details = f"🔧 MANTENIMIENTO PREVENTIVO\n"
            details += f"Máquina: {machine_name}\n"
            details += f"Frecuencia: {maintenance.frequency}\n"
            details += f"Lista de tareas: {task_list.name}\n\n"
            if task_list.description:
                details += f"Descripción: {task_list.description}\n\n"
            details += "📋 PASOS A SEGUIR:\n"
            details += "=" * 50 + "\n\n"
            total_estimated_time = 0
            step_count = 0
            for step in sorted(task_list.steps, key=lambda x: x.step_order):
                step_count += 1
                details += f"Paso {step.step_order}: {step.description}\n"
                if step.estimated_time_minutes:
                    details += f"    ⏱️ Tiempo estimado: {step.estimated_time_minutes} minutos\n"
                    total_estimated_time += step.estimated_time_minutes
                details += f"    ✅ Completado: [ ]\n"
                details += f"    📝 Observaciones: ________________________________\n\n"
            details += "=" * 50 + "\n"
            details += f"📊 RESUMEN:\n"
            details += f"    • Total de pasos: {step_count}\n"
            details += f"    • Tiempo total estimado: {total_estimated_time} minutos ({total_estimated_time/60:.1f} horas)\n"
            details += f"    • Fecha de generación: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}\n\n"
            details += "✅ VERIFICACIÓN FINAL:\n"
            details += "[ ] Todos los pasos completados\n"
            details += "[ ] Máquina en condiciones óptimas\n"
            details += "[ ] Herramientas recogidas\n"
            details += "[ ] Área de trabajo limpia\n\n"
            details += "👤 Técnico responsable: ________________\n"
            details += "📅 Fecha de ejecución: ________________\n"
            details += "🕐 Hora inicio: _______ Hora fin: _______\n"
            details += "✍️ Observaciones generales:\n"
            details += "_" * 50 + "\n" * 3
            # --- FIN de tu construcción de detalles ---
            
            work_order = WorkOrder(
                title=title,
                details=details,
                work_type="Preventivo",
                machine_id=maintenance.machine_id,
                section_id=maintenance.machine.section_id if maintenance.machine else None,
                line_id=maintenance.machine.line_id if maintenance.machine else None,
                assigned_to_id=assigned_to_id,
                status="Pendiente",
                created_at=datetime.utcnow(),
                operator="Sistema Automático",
                generated_from_maintenance_id=maintenance.id
            )

    # ✅ --- ÚNICO BLOQUE AÑADIDO: Asignación del técnico en el nuevo sistema ---
    db.add(work_order)
    db.flush()  # Crucial para obtener el work_order.id

    if assigned_to_id:
        logger.info(f"   ➕ Añadiendo asignación al sistema de técnicos para la nueva orden {work_order.id}")
        tech_assignment = WorkOrderTechnician(
            work_order_id=work_order.id,
            user_id=assigned_to_id,
            role='principal',
            assigned_by_id=1,
            notes='Asignado automáticamente por el sistema preventivo.'
        )
        db.add(tech_assignment)
    # --- FIN DEL BLOQUE AÑADIDO ---

    return work_order

