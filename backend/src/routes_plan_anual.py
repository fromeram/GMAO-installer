# src/routes_plan_anual.py (Versión híbrida: usa tanto generated_order_id como detección por similitud)

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import logging
from difflib import SequenceMatcher

from .database import get_db
from .auth import get_current_user
from .models import Maintenance, Machine, User, WorkOrder

logger = logging.getLogger(__name__)

class PlanAnualItem(BaseModel):
    id: int
    title: str
    machine_id: int
    maquina_nombre: str
    scheduled_date: date
    status: str
    work_order_id: Optional[int] = None
    class Config:
        from_attributes = True

router = APIRouter()

def text_similarity(a, b):
    """Calcula similitud entre dos textos (0-1)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

@router.get("/plan-anual", response_model=List[PlanAnualItem], tags=["Plan Anual"])
def get_plan_anual(year: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        start_of_year = date(year, 1, 1)
        end_of_year = date(year, 12, 31)

        all_plans = db.query(Maintenance).options(joinedload(Maintenance.machine)).filter(
            Maintenance.type == 'Preventivo', Maintenance.is_completed == False
        ).all()
        
        plan_ids = [p.id for p in all_plans]
        logger.info(f"📋 Planes de mantenimiento encontrados: {len(all_plans)} planes")
        
        if not plan_ids: return []

        # 🔍 MÉTODO 1: Órdenes directamente vinculadas (generated_from_maintenance_id)
        directly_linked_orders = db.query(WorkOrder).filter(
            WorkOrder.status == 'Cerrada',
            WorkOrder.work_type == 'Preventivo',
            WorkOrder.generated_from_maintenance_id.in_(plan_ids),
            WorkOrder.finished_at.between(start_of_year, end_of_year)
        ).all()
        
        logger.info(f"🔗 Órdenes directamente vinculadas: {len(directly_linked_orders)}")

        # 🔍 MÉTODO 2: Órdenes vinculadas por generated_order_id (método clásico)
        classic_linked_orders = db.query(WorkOrder).filter(
            WorkOrder.status == 'Cerrada',
            WorkOrder.work_type == 'Preventivo',
            WorkOrder.generated_from_maintenance_id.in_(plan_ids),  # ✅ USAR EL CAMPO CORRECTO
            WorkOrder.finished_at.between(start_of_year, end_of_year)
        ).all()
            
        logger.info(f"🏛️ Órdenes vinculadas clásicamente: {len(classic_linked_orders)}")

        # 🔍 MÉTODO 3: Todas las órdenes para detección por similitud
        all_completed_orders = db.query(WorkOrder).options(
            joinedload(WorkOrder.machine_obj)
        ).filter(
            WorkOrder.status == 'Cerrada',
            WorkOrder.work_type == 'Preventivo',
            WorkOrder.finished_at.between(start_of_year, end_of_year)
        ).all()
        
        logger.info(f"📊 Total órdenes preventivas en {year}: {len(all_completed_orders)}")

        # Crear mapas de órdenes vinculadas
        linked_orders_map = {}
        
        # Mapear órdenes directamente vinculadas
        for wo in directly_linked_orders:
            if wo.generated_from_maintenance_id and wo.finished_at:
                plan_id = wo.generated_from_maintenance_id
                if plan_id not in linked_orders_map:
                    linked_orders_map[plan_id] = []
                linked_orders_map[plan_id].append({
                    'work_order_id': wo.id,
                    'finished_date': wo.finished_at.date(),
                    'method': 'direct_link'
                })

        # Mapear órdenes clásicas
        for wo in classic_linked_orders:
            # Encontrar el maintenance_id correspondiente
            maintenance = db.query(Maintenance).filter(Maintenance.id == wo.generated_from_maintenance_id).first()
            if maintenance and wo.finished_at:
                plan_id = maintenance.id
                if plan_id not in linked_orders_map:
                    linked_orders_map[plan_id] = []
                linked_orders_map[plan_id].append({
                    'work_order_id': wo.id,
                    'finished_date': wo.finished_at.date(),
                    'method': 'classic_link'
                })

        def find_order_for_date(plan, target_date, tolerance_days=60):
            """Encuentra la mejor orden para una fecha específica"""
            plan_id = plan.id
            
            # 1. Primero buscar en órdenes directamente vinculadas
            if plan_id in linked_orders_map:
                for order_info in linked_orders_map[plan_id]:
                    finished_date = order_info['finished_date']
                    distance = abs((finished_date - target_date).days)
                    if distance <= tolerance_days:
                        logger.debug(f"✅ Plan {plan_id} → Orden vinculada {order_info['work_order_id']} ({order_info['method']})")
                        return order_info['work_order_id'], order_info
            
            # 2. Si no hay vinculación directa, buscar por similitud
            best_match = None
            best_score = 0
            
            for order in all_completed_orders:
                # Verificar máquina
                if order.machine_id != plan.machine_id:
                    continue
                
                # Verificar similitud de título
                title_similarity = text_similarity(plan.title, order.title)
                if title_similarity < 0.3:  # Mínimo 30% similitud
                    continue
                
                # Verificar distancia temporal
                finished_date = order.finished_at.date()
                distance_days = abs((finished_date - target_date).days)
                if distance_days > tolerance_days:
                    continue
                
                # Puntaje combinado
                temporal_score = max(0, 1 - (distance_days / tolerance_days))
                combined_score = (title_similarity * 0.7) + (temporal_score * 0.3)
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_match = {
                        'work_order_id': order.id,
                        'finished_date': finished_date,
                        'method': 'similarity',
                        'score': combined_score,
                        'title_similarity': title_similarity
                    }
            
            if best_match and best_score > 0.4:
                logger.debug(f"✅ Plan '{plan.title}' → Orden similar '{order.title}' (score: {best_score:.2f})")
                return best_match['work_order_id'], best_match
            
            return None, None

        projected_events = []
        realizados_count = 0
        
        for plan in all_plans:
            if not all([plan.machine, plan.created_at, plan.frequency]): 
                continue

            # Determinar el incremento según la frecuencia
            if plan.frequency == "Diario": step = relativedelta(days=1)
            elif plan.frequency == "Semanal": step = relativedelta(weeks=1)
            elif plan.frequency == "Mensual": step = relativedelta(months=1)
            elif plan.frequency == "Trimestral": step = relativedelta(months=3)
            elif plan.frequency == "Semestral": step = relativedelta(months=6)
            elif plan.frequency == "Anual": step = relativedelta(years=1)
            else: continue

            # Generar fechas proyectadas para el año
            current_date = plan.created_at.date()
            while current_date < start_of_year:
                current_date += step
            
            while current_date <= end_of_year:
                status = "Programado"
                work_order_id = None
                
                # Buscar orden (vinculada o por similitud)
                found_order_id, order_info = find_order_for_date(plan, current_date, 60)
                
                if found_order_id:
                    status = "Realizado"
                    work_order_id = found_order_id
                    realizados_count += 1
                
                projected_events.append(PlanAnualItem(
                    id=plan.id, 
                    title=plan.title, 
                    machine_id=plan.machine_id,
                    maquina_nombre=plan.machine.nombre, 
                    scheduled_date=current_date,
                    status=status, 
                    work_order_id=work_order_id
                ))
                current_date += step

        programados_count = len(projected_events) - realizados_count
        logger.info(f"📊 Resultado híbrido: {realizados_count} realizados, {programados_count} programados")

        return projected_events
        
    except Exception as e:
        import traceback
        logger.error(f"❌ ERROR CRÍTICO en get_plan_anual: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno en el servidor: {str(e)}")