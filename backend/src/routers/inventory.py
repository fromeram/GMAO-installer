# Auto-generated router module
import json
import logging
import os
import shutil
from datetime import datetime, timedelta, date, time
from decimal import Decimal
from typing import List, Optional, Union, Literal, Any, Dict, Tuple

from fastapi import (
    APIRouter, HTTPException, Depends, File, UploadFile, Form,
    BackgroundTasks, Body, status, Query, Response, Request
)
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session, joinedload, contains_eager
from sqlalchemy import func, distinct, case, or_, text
from sqlalchemy.orm.attributes import flag_modified

from src.database import get_db, SessionLocal
from src.auth import (
    create_access_token,
    verify_password,
    get_current_user,
    get_admin_user,
    get_jefe_seccion_user,
    get_password_hash
)
from src.config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from src.schemas import *
from src.models.base import Base
from src.models.role import Role
from src.models.section import Section
from src.models.line import Line
from src.models.machine import Machine
from src.models.supplier import Supplier
from src.models.inventory import Inventory
from src.models.associations import MachinePartAssociation
from src.models.maintenance import Maintenance
from src.models.work_order import WorkOrder, FailureCode, CauseCode, RemedyCode
from src.models.warehouse import Warehouse
from src.models.user import User 
from src.models.document import Document
from src.models.supplier_product_price import SupplierProductPrice
from src.models.task_list import TaskList
from src.models.task_step import TaskStep
from src.models.shift_pattern import ShiftPattern
from src.models.shift_assignment import ShiftAssignment
from src.models.absence import Absence
from src.models.shift_override import ShiftOverride
from src.models.maintenance_backlog import MaintenanceBacklog, BacklogPriority, BacklogStatus
from src.models.document_attachment import DocumentAttachment
from src.models.alert import Alert
from src.models.audit_log import AuditLog
from src.models import absence_crud, shift_override_crud, vacation_request_crud
from src.models.format import Format
from src.models.vacation_request import VacationRequest
from src.models.checklist_progress import ChecklistProgress
from src.models.work_order_material import WorkOrderMaterial
from src.models.work_order_technician import WorkOrderTechnician
from src.models.maintenance_request import MaintenanceRequest
from src.middleware.audit_middleware import audit_manager
from src.gamification.points_engine import get_points_engine

from .helpers import (
    PROXY_URL,
    VACATION_MANAGER_ROLES, MANAGER_ROLES,
    INVENTORY_ACCESS_ROLES, FINANCIAL_ACCESS_ROLES,
    PRODUCT_EDIT_ROLES, RESTRICTED_WORKER_ROLES,
    CONSULTANT_ROLES, CALENDAR_ACCESS_ROLES,
    get_inventory_user, get_financial_user, get_product_editor,
    get_active_order_for_maintenance, get_all_orders_for_maintenance,
    can_generate_new_order, get_maintenance_statistics,
    get_current_shift_user, handle_checklist_integration,
    add_technician_to_order, get_order_technicians,
    generate_work_order_from_task_list
)

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Section lines 3793-5111 ---
# ---------------------------
# ENDPOINTS DE INVENTARIO Y ALMACENES (CORREGIDOS)
# ---------------------------

@router.get("/inventario")
def get_inventario(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Obtener inventario - ACTUALIZADO CON TIPO
    Solo usuarios con acceso al inventario pueden ver esta información
    """
    # Verificar permisos manualmente en lugar de usar dependencia
    allowed_roles = ["Administrador", "Jefe de Mantenimiento", "Jefe de Sección", "Calidad", "Contabilidad"]
    
    if current_user.role.nombre not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder al inventario"
        )
    
    try:
        items = db.query(Inventory).options(joinedload(Inventory.warehouse)).all()
        res = []
        total_value = 0
        
        # Determinar si puede ver precios
        can_see_prices = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento", "Calidad", "Contabilidad"]
        
        for it in items:
            item_value = it.quantity * it.price
            total_value += item_value
            sup = db.query(Supplier).filter(Supplier.id == it.supplier_id).first()
            res.append({
                "id": it.id,
                "nombre": it.product_name,
                "cantidad": it.quantity,
                "almacen": it.warehouse.name if it.warehouse else "Sin almacén",
                "precio": it.price if can_see_prices else "****",
                "valor_total": item_value if can_see_prices else "****",
                "proveedor": sup.company if sup else None,
                "stock_minimo": it.stock_minimo or 0,
                "tipo": it.tipo or "mecánico"  # ← NUEVO CAMPO
            })
        
        return {
            "items": res,
            "total_value": total_value if can_see_prices else "****"
        }
    except Exception as e:
        logger.error(f"Error en get_inventario: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al obtener inventario")

@router.get("/inventario/reporte", response_model=List[InventoryReportItem])
def get_inventory_report_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo: mecánico, eléctrico, neumático, limpieza")  # ← NUEVO PARÁMETRO
):
    """
    Obtiene los datos detallados del inventario para reportes.
    Accesible para Calidad y Contabilidad.
    ACTUALIZADO: Incluye filtro por tipo de producto
    """
    # Verificar permisos manualmente
    allowed_roles = ["Administrador", "Jefe de Mantenimiento", "Jefe de Sección", "Calidad", "Contabilidad"]
    
    if current_user.role.nombre not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a los reportes de inventario"
        )
    
    logger.debug("Accediendo a /inventario/reporte...")
    try:
        # Construir query base
        query = db.query(Inventory).options(
            joinedload(Inventory.warehouse),
            joinedload(Inventory.supplier)
        )
        
        # Aplicar filtro por tipo si se especifica
        if tipo and tipo in ["mecánico", "eléctrico", "neumático", "limpieza"]:
            query = query.filter(Inventory.tipo == tipo)
            logger.debug(f"Aplicando filtro por tipo: {tipo}")
        
        items = query.order_by(Inventory.product_name).all()
        
        logger.debug(f"Encontrados {len(items)} items en inventario.")
        return items

    except Exception as e:
        logger.error(f"Error al obtener datos de inventario para reporte: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al obtener datos de inventario para reporte")


@router.get(
    "/inventory/{inventory_id}/usage", # O puedes usar /parts/{inventory_id}/usage si prefieres
    response_model=List[PartUsageInMachine],
    summary="Obtener máquinas que usan un repuesto específico"
)
def get_part_usage(
    inventory_id: int,
    db: Session = Depends(get_db)
    # Podrías añadir dependencia de usuario si quieres proteger esta ruta
    # current_user: User = Depends(get_current_user)
):
    """
    Dado el ID de un repuesto (inventory_id), devuelve una lista de las máquinas
    que lo utilizan y la cantidad utilizada en cada una.
    """
    # Verificar que el repuesto existe
    inventory_item = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repuesto con ID {inventory_id} no encontrado."
        )

    # Buscar todas las asociaciones para este repuesto, cargando la info de la máquina
    associations = db.query(MachinePartAssociation).options(
        joinedload(MachinePartAssociation.machine) # Carga eficiente de Máquina
    ).filter(MachinePartAssociation.inventory_id == inventory_id).all()

    # El response_model=List[PartUsageInMachine] junto con orm_mode=True
    # se encargará de convertir la lista de 'associations' al formato deseado,
    # incluyendo el objeto anidado 'machine' con los campos de MachineReadBasic.
    return associations

@router.get("/inventory/low-stock", response_model=List[InventoryReportItem])
def get_low_stock_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # ← Cambio aquí
    default_min: int = Query(5, description="Valor mínimo predeterminado si no está configurado")
):
    """
    Devuelve productos con stock bajo. Accesible para Calidad y Contabilidad.
    """
    # Verificar permisos manualmente
    allowed_roles = ["Administrador", "Jefe de Mantenimiento", "Jefe de Sección", "Calidad", "Contabilidad"]
    
    if current_user.role.nombre not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a la información de stock bajo"
        )
    
    try:
        items = db.query(Inventory).options(
            joinedload(Inventory.warehouse),
            joinedload(Inventory.supplier)
        ).filter(
            ((Inventory.stock_minimo > 0) & (Inventory.quantity <= Inventory.stock_minimo)) |
            ((Inventory.stock_minimo == 0) & (Inventory.quantity <= default_min))
        ).order_by(Inventory.product_name).all()
        
        logger.info(f"Encontrados {len(items)} productos bajo stock mínimo")
        return items
        
    except Exception as e:
        logger.error(f"Error al obtener inventario bajo mínimos: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno al obtener datos de inventario bajo mínimos"
        )


@router.get("/productos")
def get_productos(
    db: Session = Depends(get_db),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo: mecánico, eléctrico, neumático, limpieza")  # ← NUEVO PARÁMETRO
):
    """
    Obtener productos - ACTUALIZADO CON FILTRO POR TIPO
    """
    try:
        # Construir query base
        query = db.query(Inventory).options(
            joinedload(Inventory.warehouse),
            joinedload(Inventory.supplier)
        )
        
        # Aplicar filtro por tipo si se especifica
        if tipo and tipo in ["mecánico", "eléctrico", "neumático", "limpieza"]:
            query = query.filter(Inventory.tipo == tipo)
        
        items = query.all()
        
        return [{
            "id": item.id,
            "nombre": item.product_name,
            "cantidad": item.quantity,
            "precio": item.price,
            "descuento": item.discount,
            "almacen_id": item.warehouse_id,
            "almacen": item.warehouse.name if item.warehouse else "Sin almacén",
            "proveedor": item.supplier.company if item.supplier else None,
            "supplier_id": item.supplier_id,
            "stock_minimo": item.stock_minimo or 0,
            "tipo": item.tipo or "mecánico"  # ← NUEVO CAMPO
        } for item in items]
    except Exception as e:
        logger.error(f"Error al obtener productos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al obtener productos")

@router.post("/productos")
def create_producto_endpoint(
    data: InventarioCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_product_editor)  # ← Solo admin/jefe pueden crear
):
    """Crear producto - Solo administradores y jefes"""
    return _create_producto(data.dict(), db, current_user)

def _create_producto(data: Dict[str, Any], db: Session, _admin=None):
    print("DEBUG: Iniciando _create_producto...") 
    try:
        # --- Extraer datos del inventario ---
        product_name = data.get("product_name", "")
        try:
             quantity = int(data.get("quantity", 0))
             price = float(data.get("price", 0))
        except (ValueError, TypeError):
             raise ValueError("La cantidad y el precio deben ser números válidos.")

        warehouse_id = int(data.get("warehouse_id"))
        supplier_id = data.get("supplier_id")
        
        # ✅ NUEVO: Extraer y validar tipo
        tipo_input = data.get("tipo", "mecánico")
        allowed_types = ["mecánico", "eléctrico", "neumático", "limpieza"]
        
        if tipo_input not in allowed_types:
            print(f"WARN: Tipo '{tipo_input}' no válido, usando 'mecánico' por defecto.")
            tipo = "mecánico"
        else:
            tipo = tipo_input
        
        print(f"DEBUG: Tipo de producto: {tipo}")
        
        # ✅ CORRECCIÓN: Extraer stock_minimo correctamente
        stock_minimo_input = data.get("stock_minimo")
        stock_minimo = 0  # Valor por defecto
        
        if stock_minimo_input is not None and stock_minimo_input != "":
            try:
                stock_minimo_val = int(stock_minimo_input)
                if stock_minimo_val >= 0:
                    stock_minimo = stock_minimo_val
                else:
                    print(f"WARN: stock_minimo '{stock_minimo_input}' es negativo, usando 0.")
                    stock_minimo = 0
            except (ValueError, TypeError):
                print(f"WARN: stock_minimo '{stock_minimo_input}' no es un número válido, usando 0.")
                stock_minimo = 0

        # Extraer descuento (código existente)
        discount_input = data.get("discount")
        discount = None
        if discount_input is not None and discount_input != "":
            try:
                discount_val = float(discount_input)
                if 0 <= discount_val <= 100:
                    discount = discount_val
                else:
                     print(f"WARN: Descuento '{discount_input}' fuera de rango (0-100), usando 0.0.")
                     discount = 0.0
            except (ValueError, TypeError):
                print(f"WARN: Descuento '{discount_input}' no es un número válido, usando 0.0.")
                discount = 0.0
        else:
            discount = 0.0

        print(f"DEBUG: Datos extraídos - Prod: '{product_name}', Qty: {quantity}, WhID: {warehouse_id}, Price: {price}, SuppID: {supplier_id}, Disc: {discount}, StockMin: {stock_minimo}, Tipo: {tipo}")

        # Validar que price y quantity no sean negativos
        if price < 0:
             raise ValueError("El precio no puede ser negativo")
        if quantity < 0:
             raise ValueError("La cantidad no puede ser negativa")

        # --- Validar Almacén ---
        print(f"DEBUG: Validando almacén ID: {warehouse_id}")
        almacen = db.query(Warehouse).get(warehouse_id)
        if not almacen:
            print(f"ERROR: Almacén ID {warehouse_id} no encontrado.")
            raise HTTPException(status_code=400, detail="Almacén no existe")
        print("DEBUG: Almacén válido.")

        # --- Validar Proveedor (si se proporciona) ---
        valid_supplier_id = None
        if supplier_id:
             try:
                supplier_id_int = int(supplier_id)
                print(f"DEBUG: Validando proveedor ID: {supplier_id_int}")
                supplier = db.query(Supplier).get(supplier_id_int)
                if not supplier:
                    print(f"ERROR: Proveedor ID {supplier_id_int} no encontrado.")
                    raise HTTPException(status_code=400, detail="Proveedor no existe")
                valid_supplier_id = supplier_id_int
                print("DEBUG: Proveedor válido.")
             except (ValueError, TypeError):
                 print(f"ERROR: ID de proveedor '{supplier_id}' no es un entero válido.")
                 raise HTTPException(status_code=400, detail="ID de proveedor inválido.")
        else:
             print("DEBUG: No se proporcionó ID de proveedor.")
             valid_supplier_id = None

        # --- Lógica de Inventario: Buscar si ya existe ---
        # IMPORTANTE: Ahora también considerar el tipo en la búsqueda
        print(f"DEBUG: Buscando inventario existente para Prod='{product_name}', WhID={warehouse_id}, Tipo='{tipo}'")
        existing_product_inventory = db.query(Inventory).filter(
            Inventory.product_name == product_name,
            Inventory.warehouse_id == warehouse_id,
            Inventory.tipo == tipo  # ← NUEVO: También filtrar por tipo
        ).first()
        print(f"DEBUG: Inventario existente encontrado: {existing_product_inventory is not None}")

        inventory_item_to_update_prices = None
        result_message = {}

        if existing_product_inventory:
            # --- Actualizar Inventario Existente ---
            print(f"DEBUG: Actualizando cantidad para inventario ID: {existing_product_inventory.id}")
            existing_product_inventory.quantity += quantity
            
            if _admin or True:
                 print(f"DEBUG: Actualizando también precio={price}, descuento={discount}, proveedor ID={valid_supplier_id}, stock_minimo={stock_minimo}")
                 existing_product_inventory.price = price
                 existing_product_inventory.discount = discount
                 existing_product_inventory.supplier_id = valid_supplier_id
                 existing_product_inventory.stock_minimo = stock_minimo
                 # El tipo ya existe y es el mismo

            db.commit()
            db.refresh(existing_product_inventory)
            inventory_item_to_update_prices = existing_product_inventory
            result_message = {"id": existing_product_inventory.id, "message": "Cantidad de producto actualizada", "warehouse_id": existing_product_inventory.warehouse_id}

        else:
            # --- Crear Nuevo Registro en Inventario ---
            print(f"DEBUG: Creando nuevo registro en inventario para '{product_name}' tipo '{tipo}'.")
            inv = Inventory(
                product_name=product_name,
                quantity=quantity,
                warehouse_id=warehouse_id,
                price=price,
                supplier_id=valid_supplier_id,
                discount=discount,
                stock_minimo=stock_minimo,
                tipo=tipo  # ← NUEVO CAMPO
            )
            db.add(inv)
            db.commit()
            db.refresh(inv)
            inventory_item_to_update_prices = inv
            result_message = {"id": inv.id, "message": "Producto creado en inventario"}

        # --- *** LÓGICA: Actualizar/Crear en supplier_product_prices *** ---
        if inventory_item_to_update_prices and inventory_item_to_update_prices.supplier_id:
            current_supplier_id = inventory_item_to_update_prices.supplier_id
            current_product_name = inventory_item_to_update_prices.product_name
            print(f"DEBUG SPP: Iniciando lógica SPP para Prod='{current_product_name}', SuppID={current_supplier_id}")
            try:
                print(f"DEBUG SPP: Buscando precio existente para Prod='{current_product_name}', SuppID={current_supplier_id}")
                existing_supplier_price = db.query(SupplierProductPrice).filter(
                    SupplierProductPrice.product_name == current_product_name,
                    SupplierProductPrice.supplier_id == current_supplier_id
                ).first()
                print(f"DEBUG SPP: Precio existente encontrado: {existing_supplier_price is not None}")

                # Obtener los datos del inventario para actualizar/crear la oferta
                current_price = inventory_item_to_update_prices.price
                current_discount = inventory_item_to_update_prices.discount
                current_warehouse_id = inventory_item_to_update_prices.warehouse_id

                if existing_supplier_price:
                    # Actualizar la oferta existente
                    print(f"DEBUG SPP: Actualizando precio existente ID {existing_supplier_price.id} con Precio={current_price}, Descuento={current_discount}, WhID={current_warehouse_id}")
                    existing_supplier_price.price = current_price
                    existing_supplier_price.discount = current_discount
                    existing_supplier_price.warehouse_id = current_warehouse_id
                    existing_supplier_price.last_updated = datetime.utcnow()
                else:
                    # Crear nueva oferta si no existe
                    print(f"DEBUG SPP: Creando nuevo precio con Precio={current_price}, Descuento={current_discount}, WhID={current_warehouse_id}")
                    new_supplier_price = SupplierProductPrice(
                        product_name=current_product_name,
                        supplier_id=current_supplier_id,
                        warehouse_id=current_warehouse_id,
                        price=current_price,
                        discount=current_discount
                    )
                    db.add(new_supplier_price)

                print("DEBUG SPP: Intentando commit para supplier_product_prices...")
                db.commit()
                print("DEBUG SPP: Commit para supplier_product_prices EXITOSO.")

            except Exception as e_price:
                db.rollback()
                print(f"DEBUG SPP: ERROR durante commit/actualización de supplier_product_prices: {str(e_price)}")
                logging.error(f"Error al actualizar/crear SupplierProductPrice para inv ID {inventory_item_to_update_prices.id}: {str(e_price)}")

        elif inventory_item_to_update_prices:
             print(f"DEBUG SPP: OMITIDO - No hay supplier_id en inventario ID {inventory_item_to_update_prices.id}")

        # --- Devolver resultado de la operación de inventario ---
        print(f"DEBUG: _create_producto finalizado. Devolviendo: {result_message}")
        return result_message

    except ValueError as ve:
         print(f"ERROR: ValueError en _create_producto: {str(ve)}")
         logging.error(f"Error de validación en _create_producto: {str(ve)}")
         raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException as he:
        print(f"ERROR: HTTPException en _create_producto: {he.detail}")
        raise he
    except Exception as e:
        db.rollback()
        print(f"ERROR: Excepción inesperada en _create_producto: {str(e)}")
        logging.exception("Error inesperado en _create_producto:")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")




@router.put("/productos/{id}", response_model=Dict[str, Any])
def update_producto(
    id: int,
    data: InventarioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_product_editor)
):
    """Actualizar producto - ACTUALIZADO PARA INCLUIR TIPO"""
    print(f"DEBUG: Iniciando update_producto para ID: {id}")
    inv = db.query(Inventory).get(id)
    if not inv:
        print(f"ERROR: Producto con ID {id} no encontrado en inventario.")
        raise HTTPException(status_code=404, detail="Producto no encontrado en inventario")

    # Control de permisos
    can_edit_financials = current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]
    print(f"DEBUG: Usuario '{current_user.username}' (Rol: {current_user.role.nombre}). Puede editar financieros: {can_edit_financials}")
    if data.price is not None and not can_edit_financials:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar precios")
    if data.discount is not None and not can_edit_financials:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar descuentos")

    update_data = data.dict(exclude_unset=True)
    print(f"DEBUG: Datos recibidos para actualizar: {update_data}")
    supplier_price_needs_update = False
    original_supplier_id = inv.supplier_id

    # Validar y aplicar cambios al objeto 'inv'
    for key, value in update_data.items():
        print(f"DEBUG: Procesando campo '{key}' con valor '{value}'")
        if value is None and key not in ['supplier_id', 'discount', 'stock_minimo', 'tipo']:
             print(f"DEBUG: Omitiendo campo '{key}' porque el valor es None.")
             continue

        try:
            if key == "warehouse_id":
                warehouse = db.query(Warehouse).get(int(value))
                if not warehouse:
                    raise HTTPException(status_code=400, detail="Almacén no existe")
                inv.warehouse_id = int(value)
            elif key == "supplier_id":
                 if value is None:
                      inv.supplier_id = None
                      supplier_price_needs_update = True
                 else:
                     supplier = db.query(Supplier).get(int(value))
                     if not supplier:
                        raise HTTPException(status_code=400, detail="Proveedor no existe")
                     inv.supplier_id = int(value)
                     supplier_price_needs_update = True
            elif key == "price":
                 price_val = float(value)
                 if price_val < 0:
                     raise ValueError("El precio no puede ser negativo")
                 inv.price = price_val
                 supplier_price_needs_update = True
            elif key == "discount":
                 if value is None:
                     discount_val = 0.0
                 else:
                     discount_val = float(value)
                     if not (0 <= discount_val <= 100):
                         raise ValueError("El descuento debe estar entre 0 y 100")
                 inv.discount = discount_val
                 supplier_price_needs_update = True
            elif key == "stock_minimo":
                if value is None:
                    stock_minimo_val = 0
                else:
                    stock_minimo_val = int(value)
                    if stock_minimo_val < 0:
                        raise ValueError("El stock mínimo no puede ser negativo")
                inv.stock_minimo = stock_minimo_val
            elif key == "tipo":  # ← NUEVO CAMPO
                allowed_types = ["mecánico", "eléctrico", "neumático", "limpieza"]
                if value and value in allowed_types:
                    inv.tipo = value
                    print(f"DEBUG: Actualizando tipo a: {value}")
                else:
                    print(f"WARN: Tipo '{value}' no válido, manteniendo valor actual: {inv.tipo}")
            elif key == "quantity":
                  qty_val = int(value)
                  if qty_val < 0:
                       raise ValueError("La cantidad no puede ser negativa")
                  inv.quantity = qty_val
            elif hasattr(inv, key):
                setattr(inv, key, value)
            else:
                 print(f"WARN: Campo '{key}' no reconocido en el modelo Inventory.")

        except (ValueError, TypeError) as val_err:
             print(f"ERROR: Error de tipo/valor procesando campo '{key}': {val_err}")
             raise HTTPException(status_code=400, detail=f"Valor inválido para el campo '{key}': {val_err}")
        except HTTPException:
             raise
        except Exception as e:
             print(f"ERROR: Excepción inesperada procesando campo '{key}': {e}")
             logging.exception(f"Error procesando campo {key} en update_producto:")
             raise HTTPException(status_code=500, detail=f"Error procesando campo '{key}'")

    try:
        # Guardar cambios en Inventario
        print("DEBUG: Intentando commit para actualización de inventario...")
        db.commit()
        print("DEBUG: Commit de inventario EXITOSO.")
        db.refresh(inv)

        # --- *** LÓGICA SPP TRAS ACTUALIZACIÓN DE INVENTARIO *** ---
        if supplier_price_needs_update and inv.supplier_id is not None:
            # Solo actualizar si se cambiaron datos relevantes Y el item AHORA tiene proveedor
            current_supplier_id = inv.supplier_id
            current_product_name = inv.product_name
            print(f"DEBUG SPP (Update): Iniciando lógica SPP para Prod='{current_product_name}', SuppID={current_supplier_id}")
            try:
                print(f"DEBUG SPP (Update): Buscando precio existente para Prod='{current_product_name}', SuppID={current_supplier_id}")
                existing_supplier_price = db.query(SupplierProductPrice).filter(
                    SupplierProductPrice.product_name == current_product_name,
                    SupplierProductPrice.supplier_id == current_supplier_id
                ).first()
                print(f"DEBUG SPP (Update): Precio existente encontrado: {existing_supplier_price is not None}")

                current_price = inv.price
                current_discount = inv.discount
                current_warehouse_id = inv.warehouse_id

                if existing_supplier_price:
                    print(f"DEBUG SPP (Update): Actualizando precio existente ID {existing_supplier_price.id} con Precio={current_price}, Descuento={current_discount}, WhID={current_warehouse_id}")
                    existing_supplier_price.price = current_price
                    existing_supplier_price.discount = current_discount
                    existing_supplier_price.warehouse_id = current_warehouse_id
                    existing_supplier_price.last_updated = datetime.utcnow()
                else:
                    # Crear si no existía para este proveedor/producto
                    print(f"DEBUG SPP (Update): Creando nuevo precio con Precio={current_price}, Descuento={current_discount}, WhID={current_warehouse_id}")
                    new_supplier_price = SupplierProductPrice(
                        product_name=current_product_name,
                        supplier_id=current_supplier_id,
                        warehouse_id=current_warehouse_id,
                        price=current_price,
                        discount=current_discount
                    )
                    db.add(new_supplier_price)

                print("DEBUG SPP (Update): Intentando commit para supplier_product_prices...")
                db.commit()
                print("DEBUG SPP (Update): Commit para supplier_product_prices EXITOSO.")

            except Exception as e_price:
                db.rollback()
                print(f"DEBUG SPP (Update): ERROR durante commit/actualización de supplier_product_prices: {str(e_price)}")
                logging.error(f"Error al actualizar/crear SupplierProductPrice tras update de inventario ID {inv.id}: {str(e_price)}")

        elif supplier_price_needs_update and inv.supplier_id is None:
             print(f"DEBUG SPP (Update): OMITIDO - El inventario ID {inv.id} se quedó sin supplier_id tras la actualización.")

        # --- Devolver el producto de inventario actualizado ---
        response_data = {
             "id": inv.id,
             "nombre": inv.product_name,
             "cantidad": inv.quantity,
             "almacen_id": inv.warehouse_id,
             "precio": float(inv.price) if inv.price is not None else None,
             "descuento": float(inv.discount) if inv.discount is not None else None,
             "supplier_id": inv.supplier_id,
             "stock_minimo": inv.stock_minimo,
             "tipo": inv.tipo or "mecánico"  # ← NUEVO CAMPO
         }
        print(f"DEBUG: update_producto finalizado para ID: {id}. Devolviendo: {response_data}")
        return response_data

    except HTTPException as he:
         db.rollback()
         print(f"ERROR: HTTPException en update_producto: {he.detail}")
         raise he
    except Exception as e:
        db.rollback()
        print(f"ERROR: Excepción inesperada en update_producto (ID: {id}): {str(e)}")
        logging.exception(f"Error inesperado en update_producto (ID: {id}):")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al actualizar producto: {str(e)}")
    
@router.get("/productos/{id}")
def get_producto_detalle(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene detalles de un producto específico por su ID - ACTUALIZADO CON TIPO."""
    try:
        # Buscar el producto por ID
        producto = db.query(Inventory).filter(Inventory.id == id).options(
            joinedload(Inventory.warehouse),
            joinedload(Inventory.supplier)
        ).first()
        
        if not producto:
            raise HTTPException(status_code=404, detail=f"Producto con ID {id} no encontrado")
        
        # Formatear la respuesta
        response = {
            "id": producto.id,
            "nombre": producto.product_name,
            "cantidad": producto.quantity,
            "almacen_id": producto.warehouse_id,
            "almacen": producto.warehouse.name if producto.warehouse else None,
            "precio": float(producto.price) if producto.price is not None else None,
            "descuento": float(producto.discount) if producto.discount is not None else None,
            "supplier_id": producto.supplier_id,
            "proveedor": producto.supplier.company if producto.supplier else None,
            "stock_minimo": producto.stock_minimo,
            "tipo": producto.tipo or "mecánico"  # ← NUEVO CAMPO
        }
        
        return response
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error obteniendo detalle del producto {id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
    

@router.delete("/productos/{producto_id}")
def delete_producto(
    producto_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_product_editor)  # ← Solo admin/jefe pueden eliminar
):
    """Eliminar producto - Solo administradores y jefes"""
    """Elimina un producto del inventario."""
    
    # Buscar el producto
    producto = db.query(Inventory).filter(Inventory.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Comprobar si está en uso en máquinas
    machine_parts = db.query(MachinePartAssociation).filter(
        MachinePartAssociation.inventory_id == producto_id
    ).first()
    
    if machine_parts:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar el producto porque está asociado a máquinas"
        )
    
    from src.models.work_order_material import WorkOrderMaterial
    # Comprobar si está en uso en órdenes de trabajo
    work_orders = db.query(WorkOrderMaterial).filter(
        WorkOrderMaterial.inventory_id == producto_id
    ).first()
    
    if work_orders:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar el producto porque está siendo utilizado en órdenes de trabajo"
        )
    
    # Eliminar precios asociados en supplier_product_prices si existen
    try:
        supplier_prices = db.query(SupplierProductPrice).filter(
            SupplierProductPrice.product_name == producto.product_name
        ).all()
        
        for price in supplier_prices:
            db.delete(price)
        
        # Eliminar el producto
        db.delete(producto)
        db.commit()
        
        return {"success": True, "message": "Producto eliminado correctamente"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar producto {producto_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al eliminar el producto: {str(e)}")

@router.get("/inventario/estadisticas-tipo")
def get_estadisticas_por_tipo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene estadísticas del inventario agrupadas por tipo de producto
    """
    # Verificar permisos
    allowed_roles = ["Administrador", "Jefe de Mantenimiento", "Jefe de Sección", "Calidad", "Contabilidad"]
    
    if current_user.role.nombre not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a las estadísticas de inventario"
        )
    
    try:
        # Query para obtener estadísticas por tipo
        from sqlalchemy import func
        
        stats = db.query(
            Inventory.tipo,
            func.count(Inventory.id).label('total_items'),
            func.sum(Inventory.quantity).label('total_quantity'),
            func.sum(Inventory.quantity * Inventory.price).label('total_value')
        ).group_by(Inventory.tipo).all()
        
        # Formatear respuesta
        result = {
            "por_tipo": {},
            "resumen": {
                "total_items": 0,
                "total_quantity": 0,
                "total_value": 0
            }
        }
        
        for stat in stats:
            tipo = stat.tipo or "mecánico"
            result["por_tipo"][tipo] = {
                "total_items": stat.total_items,
                "total_quantity": stat.total_quantity,
                "total_value": float(stat.total_value) if stat.total_value else 0
            }
            
            # Sumar al resumen general
            result["resumen"]["total_items"] += stat.total_items
            result["resumen"]["total_quantity"] += stat.total_quantity
            result["resumen"]["total_value"] += float(stat.total_value) if stat.total_value else 0
        
        return result
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas por tipo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al obtener estadísticas por tipo")
    
@router.get("/productos/tipos")
def get_product_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene los tipos de productos disponibles y la cantidad de productos por tipo
    """
    try:
        from sqlalchemy import func
        
        # Query para contar productos por tipo
        type_counts = db.query(
            Inventory.tipo,
            func.count(Inventory.id).label('count')
        ).group_by(Inventory.tipo).all()
        
        result = {
            "tipos_disponibles": ["mecánico", "eléctrico", "neumático", "limpieza"],
            "conteo_por_tipo": {}
        }
        
        # Inicializar contadores en 0
        for tipo in result["tipos_disponibles"]:
            result["conteo_por_tipo"][tipo] = 0
        
        # Llenar con datos reales
        for tipo_count in type_counts:
            tipo = tipo_count.tipo or "mecánico"
            if tipo in result["tipos_disponibles"]:
                result["conteo_por_tipo"][tipo] = tipo_count.count
        
        return result
        
    except Exception as e:
        logger.error(f"Error al obtener tipos de productos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al obtener tipos de productos")
    
@router.post("/productos/migrate-types")
def migrate_product_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Migra productos existentes clasificándolos automáticamente por tipo
    SOLO PARA ADMINISTRADORES - Usar una sola vez después de la migración de BD
    """
    # Solo administradores pueden ejecutar esta migración
    if current_user.role.nombre != "Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden ejecutar la migración de tipos"
        )
    
    try:
        # Diccionario de palabras clave para clasificación automática
        classification_keywords = {
            'eléctrico': [
                'motor', 'cable', 'sensor', 'switch', 'relay', 'fuse', 'fusible',
                'led', 'lamp', 'light', 'wire', 'eléctrico', 'electrico', 
                'voltaje', 'amperio', 'resistencia', 'capacitor', 'transistor',
                'diodo', 'transformador', 'inversor', 'batería', 'bateria',
                'cargador', 'conector', 'enchufe', 'interruptor', 'pulsador'
            ],
            'neumático': [
                'cylinder', 'cilindro', 'valve', 'valvula', 'air', 'aire',
                'pneumatic', 'neumatico', 'neumático', 'compressor', 'compresor',
                'manguera', 'hose', 'fitting', 'conexión', 'presión', 'presion',
                'psi', 'bar', 'filtro aire', 'regulador', 'manifold', 'actuador'
            ]
        }
        
        # Obtener productos sin tipo o con tipo NULL
        products = db.query(Inventory).filter(
            (Inventory.tipo == None) | (Inventory.tipo == '')
        ).all()
        
        classified_count = {
            'eléctrico': 0,
            'neumático': 0, 
            'mecánico': 0,
            'limpieza': 0
        }
        
        for product in products:
            product_name_lower = product.product_name.lower()
            classified_type = 'mecánico'  # Tipo por defecto
            
            # Buscar coincidencias con palabras clave
            # Prioridad: eléctrico > neumático > mecánico
            for tipo, keywords in classification_keywords.items():
                for keyword in keywords:
                    if keyword in product_name_lower:
                        classified_type = tipo
                        break
                
                if classified_type != 'mecánico':
                    break
            
            # Actualizar el producto
            product.tipo = classified_type
            classified_count[classified_type] += 1
        
        # Guardar cambios
        db.commit()
        
        return {
            "success": True,
            "message": "Migración de tipos completada",
            "productos_clasificados": classified_count,
            "total_procesados": sum(classified_count.values())
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error durante la migración de tipos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error durante la migración: {str(e)}")
    
@router.get("/productos/validate-types")
def validate_product_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Valida que todos los productos tengan tipos válidos
    """
    # Verificar permisos
    allowed_roles = ["Administrador", "Jefe de Mantenimiento", "Jefe de Sección", "Calidad", "Contabilidad"]
    
    if current_user.role.nombre not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para validar tipos de productos"
        )
    
    try:
        valid_types = ['mecánico', 'eléctrico', 'neumático', 'limpieza']
        
        # Contar productos por tipo
        type_counts = {}
        for tipo in valid_types:
            count = db.query(Inventory).filter(Inventory.tipo == tipo).count()
            type_counts[tipo] = count
        
        # Buscar productos con tipos inválidos o NULL
        invalid_products = db.query(Inventory).filter(
            (Inventory.tipo == None) | 
            (Inventory.tipo == '') | 
            (~Inventory.tipo.in_(valid_types))
        ).all()
        
        result = {
            "productos_por_tipo": type_counts,
            "total_productos": sum(type_counts.values()),
            "productos_invalidos": len(invalid_products),
            "valido": len(invalid_products) == 0
        }
        
        if invalid_products:
            result["productos_con_problemas"] = [
                {
                    "id": p.id,
                    "nombre": p.product_name,
                    "tipo_actual": p.tipo
                } for p in invalid_products[:10]  # Mostrar máximo 10 ejemplos
            ]
            
            # OPCIONAL: Auto-corregir productos inválidos
            for product in invalid_products:
                product.tipo = 'mecánico'
            db.commit()
            result["mensaje"] = f"Se corrigieron {len(invalid_products)} productos con tipos inválidos a 'mecánico'"
        
        return result
        
    except Exception as e:
        logger.error(f"Error al validar tipos de productos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al validar tipos de productos")





@router.get("/products/distinct-names", response_model=List[str])
def get_distinct_product_names(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_inventory_user)  # ← Acceso para roles de inventario
):
    """
    Obtiene nombres únicos de productos - Accesible para Calidad y Contabilidad
    """
    try:
        distinct_names = db.query(distinct(SupplierProductPrice.product_name)).order_by(SupplierProductPrice.product_name).all()
        return [name[0] for name in distinct_names]
    except Exception as e:
        print(f"Error fetching distinct product names: {e}")
        raise HTTPException(status_code=500, detail="Error interno al obtener nombres de productos.")

# Endpoint principal para comparar precios de un producto
@router.get("/supplier-prices/compare", response_model=List[SupplierPrice])
def get_supplier_prices_for_product(
    product_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ← Cambio aquí
):
    """
    Comparar precios de proveedores - Accesible para Calidad y Contabilidad
    """
    # Verificar permisos manualmente
    allowed_roles = ["Administrador", "Jefe de Mantenimiento", "Calidad", "Contabilidad"]
    
    if current_user.role.nombre not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a la comparación de precios"
        )
    
    try:
        prices = db.query(SupplierProductPrice).options(
            joinedload(SupplierProductPrice.supplier),
            joinedload(SupplierProductPrice.warehouse)
        ).filter(SupplierProductPrice.product_name.ilike(f"%{product_name}%")).all()

        return prices
    except Exception as e:
        print(f"Error comparing prices for {product_name}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al comparar precios.")


# Endpoint para añadir una nueva oferta de precio
@router.post("/supplier-prices", response_model=SupplierPrice, status_code=201)
def create_supplier_price(
    price_data: SupplierPriceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # O rol adecuado (Jefe Mantenimiento?)
):
    """
    Crea una nueva entrada en el catálogo de precios de proveedores.
    Requiere rol de Administrador o Jefe de Mantenimiento.
    """
    # Verificar que el proveedor existe
    supplier = db.query(Supplier).filter(Supplier.id == price_data.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail=f"Proveedor con ID {price_data.supplier_id} no encontrado.")

    # Verificar que el almacén existe (si se proporciona)
    if price_data.warehouse_id:
        warehouse = db.query(Warehouse).filter(Warehouse.id == price_data.warehouse_id).first()
        if not warehouse:
             raise HTTPException(status_code=404, detail=f"Almacén con ID {price_data.warehouse_id} no encontrado.")

    # Opcional: Verificar si ya existe una entrada EXACTA (mismo producto, proveedor, almacén)
    # db_existing = db.query(SupplierProductPrice).filter(
    #     SupplierProductPrice.product_name == price_data.product_name,
    #     SupplierProductPrice.supplier_id == price_data.supplier_id,
    #     SupplierProductPrice.warehouse_id == price_data.warehouse_id
    # ).first()
    # if db_existing:
    #     raise HTTPException(status_code=400, detail="Ya existe una oferta para este producto, proveedor y almacén.")

    db_price = SupplierProductPrice(**price_data.dict())
    # last_updated se establece por defecto en el modelo/DB
    try:
        db.add(db_price)
        db.commit()
        db.refresh(db_price)
        # Cargar relaciones para la respuesta
        db.refresh(db_price, attribute_names=['supplier', 'warehouse'])
        return db_price
    except Exception as e:
        db.rollback()
        print(f"Error creating supplier price: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno al crear la oferta de precio: {e}")


# Endpoint para actualizar una oferta de precio existente
@router.put("/supplier-prices/{price_id}", response_model=SupplierPrice)
def update_supplier_price(
    price_id: int,
    price_data: SupplierPriceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # O rol adecuado
):
    """
    Actualiza una oferta de precio existente en el catálogo.
    Requiere rol de Administrador o Jefe de Mantenimiento.
    """
    db_price = db.query(SupplierProductPrice).filter(SupplierProductPrice.id == price_id).first()
    if not db_price:
        raise HTTPException(status_code=404, detail="Oferta de precio no encontrada.")

    # Validar proveedor/almacén si se cambian
    if price_data.supplier_id is not None and price_data.supplier_id != db_price.supplier_id:
         supplier = db.query(Supplier).filter(Supplier.id == price_data.supplier_id).first()
         if not supplier:
             raise HTTPException(status_code=404, detail=f"Proveedor con ID {price_data.supplier_id} no encontrado.")
         db_price.supplier_id = price_data.supplier_id # Actualizar solo si es válido

    if price_data.warehouse_id is not None and price_data.warehouse_id != db_price.warehouse_id:
         warehouse = db.query(Warehouse).filter(Warehouse.id == price_data.warehouse_id).first()
         if not warehouse:
             raise HTTPException(status_code=404, detail=f"Almacén con ID {price_data.warehouse_id} no encontrado.")
         db_price.warehouse_id = price_data.warehouse_id # Actualizar solo si es válido
    elif price_data.warehouse_id is None and 'warehouse_id' in price_data.dict(exclude_unset=True):
         # Permitir quitar el almacén estableciéndolo a None explícitamente
         db_price.warehouse_id = None


    update_data = price_data.dict(exclude_unset=True) # Obtener solo los campos enviados

    for key, value in update_data.items():
         # Actualizar solo si el campo existe en el modelo y el valor no es None (excepto warehouse_id)
         if hasattr(db_price, key) and (key == 'warehouse_id' or value is not None):
             setattr(db_price, key, value)

    # last_updated se actualiza automáticamente por onupdate en el modelo/DB
    # Si no, añadir: db_price.last_updated = datetime.datetime.utcnow()

    try:
        db.commit()
        db.refresh(db_price)
        db.refresh(db_price, attribute_names=['supplier', 'warehouse'])
        return db_price
    except Exception as e:
        db.rollback()
        print(f"Error updating supplier price {price_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno al actualizar la oferta: {e}")


# Endpoint para eliminar una oferta de precio
@router.delete("/supplier-prices/{price_id}", status_code=200)
def delete_supplier_price(
    price_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user) # O rol adecuado
):
    """
    Elimina una oferta de precio del catálogo.
    Requiere rol de Administrador o Jefe de Mantenimiento.
    """
    db_price = db.query(SupplierProductPrice).filter(SupplierProductPrice.id == price_id).first()
    if not db_price:
        raise HTTPException(status_code=404, detail="Oferta de precio no encontrada.")

    try:
        db.delete(db_price)
        db.commit()
        return {"message": "Oferta de precio eliminada correctamente"}
    except Exception as e:
        db.rollback()
        print(f"Error deleting supplier price {price_id}: {e}")
        # Podría fallar por restricciones si algo más depende de esta tabla (poco probable)
        raise HTTPException(status_code=500, detail=f"Error interno al eliminar la oferta: {e}")


@router.get("/supplier-prices/all", response_model=List[SupplierPrice])
def get_all_supplier_prices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Cambio aquí también
):
    """
    Obtiene TODOS los precios de proveedores para análisis de comparación
    Accesible para roles con permisos de inventario
    """
    # Verificar permisos manualmente
    allowed_roles = ["Administrador", "Jefe de Mantenimiento", "Calidad", "Contabilidad"]
    
    if current_user.role.nombre not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a los precios de proveedores"
        )
    
    try:
        # Obtener todos los precios con sus relaciones
        all_prices = db.query(SupplierProductPrice).options(
            joinedload(SupplierProductPrice.supplier),
            joinedload(SupplierProductPrice.warehouse)
        ).order_by(
            SupplierProductPrice.product_name,
            SupplierProductPrice.price
        ).all()

        logger.info(f"Obtenidos {len(all_prices)} precios de proveedores para comparación")
        return all_prices

    except Exception as e:
        logger.error(f"Error al obtener todos los precios de proveedores: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al obtener precios de proveedores")

@router.get("/supplier-prices/products-with-multiple-suppliers")
def get_products_with_multiple_suppliers(
    min_suppliers: int = Query(2, ge=2, description="Mínimo número de proveedores"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene productos que tienen múltiples proveedores con estadísticas de ahorro
    """
    # Verificar permisos
    allowed_roles = ["Administrador", "Jefe de Mantenimiento", "Calidad", "Contabilidad"]
    
    if current_user.role.nombre not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a esta información"
        )
    
    try:
        # Subconsulta para contar proveedores por producto
        supplier_count_subquery = db.query(
            SupplierProductPrice.product_name,
            func.count(func.distinct(SupplierProductPrice.supplier_id)).label('supplier_count')
        ).group_by(SupplierProductPrice.product_name).subquery()

        # Productos con múltiples proveedores
        products_with_multiple = db.query(supplier_count_subquery).filter(
            supplier_count_subquery.c.supplier_count >= min_suppliers
        ).all()

        result = []
        for product_row in products_with_multiple:
            product_name = product_row.product_name
            supplier_count = product_row.supplier_count

            # Obtener todos los precios para este producto
            prices = db.query(SupplierProductPrice).options(
                joinedload(SupplierProductPrice.supplier),
                joinedload(SupplierProductPrice.warehouse)
            ).filter(SupplierProductPrice.product_name == product_name).all()

            # Calcular precios finales (con descuentos)
            final_prices = []
            for price in prices:
                final_price = float(price.price) * (1 - float(price.discount) / 100)
                final_prices.append({
                    'supplier_id': price.supplier_id,
                    'supplier_name': price.supplier.company if price.supplier else 'N/A',
                    'original_price': float(price.price),
                    'discount': float(price.discount),
                    'final_price': final_price,
                    'warehouse': price.warehouse.name if price.warehouse else None
                })

            # Ordenar por precio final
            final_prices.sort(key=lambda x: x['final_price'])

            # Calcular estadísticas
            lowest_price = final_prices[0]['final_price']
            highest_price = final_prices[-1]['final_price']
            savings_amount = highest_price - lowest_price
            savings_percentage = (savings_amount / highest_price * 100) if highest_price > 0 else 0

            result.append({
                'product_name': product_name,
                'supplier_count': supplier_count,
                'lowest_price': lowest_price,
                'highest_price': highest_price,
                'savings_amount': savings_amount,
                'savings_percentage': round(savings_percentage, 2),
                'best_supplier': final_prices[0]['supplier_name'],
                'price_details': final_prices
            })

        # Ordenar por mayor potencial de ahorro
        result.sort(key=lambda x: x['savings_percentage'], reverse=True)

        return {
            'total_products': len(result),
            'products': result,
            'summary': {
                'total_potential_savings': sum(p['savings_amount'] for p in result),
                'average_savings_percentage': sum(p['savings_percentage'] for p in result) / len(result) if result else 0,
                'top_saving_opportunity': result[0] if result else None
            }
        }

    except Exception as e:
        logger.error(f"Error obteniendo productos con múltiples proveedores: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al procesar datos")


@router.get("/almacenes")  # <--- Añadir este endpoint GET
def list_almacenes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    whs = db.query(Warehouse).all()
    return [{"id": w.id, "name": w.name} for w in whs]

@router.post("/almacenes")
async def create_almacen(
    request: Request, 
    data: WarehouseCreate, 
    db: Session = Depends(get_db), 
    _admin=Depends(get_admin_user)
):
    try:
        # Validación de nombre único
        exist = db.query(Warehouse).filter(Warehouse.name == data.name).first()
        if exist:
            raise HTTPException(400, "Ese almacén ya existe")
            
        # Crear almacén
        w = Warehouse(name=data.name)
        db.add(w)
        db.commit()
        
        return {"id": w.id, "name": w.name}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logging.error(f"Error creando almacén: {str(e)}")
        raise HTTPException(500, "Error interno del servidor")

@router.delete("/almacenes/{almacen_id}")
def delete_almacen(
    almacen_id: int, 
    db: Session = Depends(get_db), 
    _admin=Depends(get_admin_user)
):
    almacen = db.query(Warehouse).get(almacen_id)
    if not almacen:
        raise HTTPException(404, "Almacén no encontrado")
    
    # Verificar productos asociados
    if db.query(Inventory).filter(Inventory.warehouse_id == almacen_id).first():
        raise HTTPException(400, "El almacén tiene productos asignados")
    
    db.delete(almacen)
    db.commit()
    return {"message": "Almacén eliminado"}
@router.get("/partes")
def get_partes(fecha: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not fecha:
        fecha = datetime.utcnow().strftime("%Y-%m-%d")
    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
    except:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")

    inicio = datetime(fecha_dt.year, fecha_dt.month, fecha_dt.day)
    fin = inicio + timedelta(days=1)

    query = db.query(WorkOrder).filter(WorkOrder.created_at >= inicio, WorkOrder.created_at < fin)
    if current_user.role.nombre == "Jefe de Sección":
        query = query.filter(WorkOrder.section_id == current_user.section_id)
    
    orders = query.all()
    res = []
    for o in orders:
        res.append({
            "id": o.id,
            "title": o.title,
            "work_type": o.work_type,
            "section": o.section.nombre if o.section else None,
            "line": o.line.nombre if o.line else None,
            "machine": o.machine_obj.nombre if o.machine_obj else None,  # Corregido aquí
            "operator": o.operator,
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None
        })
    return res
