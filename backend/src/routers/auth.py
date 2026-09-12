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


# --- Section lines 1379-1850 ---
# ---------------------------
# ENDPOINTS DE AUTENTICACIÓN Y USUARIOS
# ---------------------------

@router.post("/token")
async def login_for_access_token(data: LoginModel, request: Request, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == data.username).first()
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Usuario no encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # ✅ VERIFICAR SI EL USUARIO ESTÁ ACTIVO
        if not user.active:
            # Registrar intento de login de usuario inactivo
            try:
                print(f"[LOGIN] Usuario inactivo intentó hacer login: {user.username}")
                audit_manager.log_login(db, user, request, success=False)
                db.commit()
            except Exception as audit_error:
                print(f"[LOGIN ERROR] Error registrando intento de usuario inactivo: {audit_error}")
            
            raise HTTPException(
                status_code=401,
                detail="Usuario inactivo. Contacte con el administrador.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(data.password, user.password):
            # Registrar intento fallido
            try:
                print(f"[LOGIN] Registrando login fallido para usuario: {user.username}")
                audit_manager.log_login(db, user, request, success=False)
                db.commit()
                print(f"[LOGIN] Login fallido registrado correctamente")
            except Exception as audit_error:
                print(f"[LOGIN ERROR] Error registrando login fallido: {audit_error}")
                import traceback
                print(f"[LOGIN ERROR] Traceback: {traceback.format_exc()}")
            
            raise HTTPException(
                status_code=401,
                detail="Contraseña incorrecta",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Login exitoso - registrar en audit
        try:
            print(f"[LOGIN] Registrando login exitoso para usuario: {user.username}")
            audit_manager.log_login(db, user, request, success=True)
            db.commit()
            print(f"[LOGIN] Login exitoso registrado correctamente")
        except Exception as audit_error:
            print(f"[LOGIN ERROR] Error registrando login exitoso: {audit_error}")
            import traceback
            print(f"[LOGIN ERROR] Traceback: {traceback.format_exc()}")

        access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.username,
                "role": user.role.nombre if user.role else None
            }, 
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_data": {
                "id": user.id,
                "username": user.username,
                "role": user.role.nombre if user.role else None,
                "section": user.section.nombre if user.section else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[LOGIN ERROR] Error general en login: {e}")
        import traceback
        print(f"[LOGIN ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users")
def create_user(
    data: UserCreate, 
    request: Request,  # ← AÑADIR Request
    db: Session = Depends(get_db), 
    current_user=Depends(get_admin_user)
):
    if not isinstance(data.role_id, int):
        raise HTTPException(status_code=400, detail="El ID del rol debe ser un número entero")

    role = db.query(Role).filter(Role.id == data.role_id).first()
    if not role:
        raise HTTPException(status_code=400, detail=f"Rol con ID {data.role_id} no existe")

    hashed = get_password_hash(data.password)
    
    new_user = User(
        username=data.username,
        password=hashed,
        role_id=data.role_id,
        section_id=data.section_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # *** AÑADIR AUDIT TRAIL ***
    audit_manager.log_action(
        db=db,
        action="CREATE",
        entity=new_user,
        user=current_user,
        request=request,
        notes=f"Usuario creado: {new_user.username} con rol {role.nombre}"
    )
    db.commit()  # Commit del audit log
    # *** FIN AUDIT TRAIL ***

    return {
        "id": new_user.id,
        "username": new_user.username,
        "role": role.nombre,
        "section": new_user.section.nombre if new_user.section else None
    }


@router.get("/users/me")
def get_my_user(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role.nombre if current_user.role else None,  # String
        "section": current_user.section.nombre if current_user.section else None  # String
    }



@router.get("/users")
def list_users(
    include_inactive: bool = Query(False, description="Incluir usuarios inactivos"),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    try:
        # Base query
        query = db.query(User)
        
        # Filtrar por sección si es Jefe de Sección
        if (current_user.role and current_user.role.nombre == "Jefe de Sección"):
            query = query.filter(User.section_id == current_user.section_id)
        
        # ✅ CAMBIO PRINCIPAL: Aplicar filtro de activos solo si no se pide incluir inactivos
        if not include_inactive:
            query = query.filter(User.active == True)
        
        users = query.all()
        
        result = []
        for u in users:
            result.append({
                "id": u.id,
                "username": u.username,
                "role": u.role.nombre if u.role else None,
                "section": u.section.nombre if u.section else None,
                "role_id": u.role_id,
                "active": u.active  # ✅ IMPORTANTE: Incluir campo active en la respuesta
            })
        
        return result
        
    except Exception as e:
        print(f"Error en list_users: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}", summary="Actualizar un usuario")
def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,  # ← AÑADIR Request
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # *** CAPTURAR ESTADO ANTERIOR ***
    old_data = audit_manager.extract_entity_data(db_user)
    # *** FIN CAPTURA ***

    update_data = user_data.dict(exclude_unset=True)
    if not update_data:
         raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar.")

    fields_updated = []
    for key, value in update_data.items():
        if key == "role_id" and value is not None:
            role = db.query(Role).filter(Role.id == value).first()
            if not role: raise HTTPException(status_code=400, detail=f"Rol ID {value} no existe.")
        if key == "section_id" and value is not None:
            section = db.query(Section).filter(Section.id == value).first()
            if not section: raise HTTPException(status_code=400, detail=f"Sección ID {value} no existe.")
        if key == "username" and value != db_user.username:
             existing = db.query(User).filter(User.username == value).first()
             if existing: raise HTTPException(status_code=400, detail="El nombre de usuario ya existe.")

        setattr(db_user, key, value)
        fields_updated.append(key)

    try:
        db.commit()
        db.refresh(db_user)
        
        # *** AÑADIR AUDIT TRAIL ***
        new_data = audit_manager.extract_entity_data(db_user)
        audit_manager.log_action(
            db=db,
            action="UPDATE",
            entity=db_user,
            user=current_user,
            request=request,
            old_data=old_data,
            new_data=new_data,
            notes=f"Usuario actualizado: {db_user.username}. Campos: {', '.join(fields_updated)}"
        )
        db.commit()  # Commit del audit log
        # *** FIN AUDIT TRAIL ***
        
        return {
            "id": db_user.id,
            "username": db_user.username,
            "role": db_user.role.nombre if db_user.role else None,
            "section": db_user.section.nombre if db_user.section else None,
            "role_id": db_user.role_id,
            "section_id": db_user.section_id
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando usuario {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al actualizar usuario.")
    
@router.put("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if user.active:
        raise HTTPException(status_code=400, detail="El usuario ya está activo")
    
    # Capturar estado anterior
    old_data = audit_manager.extract_entity_data(user)
    
    user.active = True
    db.commit()
    
    # Audit trail
    new_data = audit_manager.extract_entity_data(user)
    audit_manager.log_action(
        db=db,
        action="UPDATE",
        entity=user,
        user=current_user,
        request=request,
        old_data=old_data,
        new_data=new_data,
        notes=f"Usuario activado: {user.username}"
    )
    db.commit()
    
    return {"success": True, "message": "Usuario activado correctamente"}




@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    request: Request,  # ← AÑADIR Request
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # *** CAPTURAR DATOS ANTES DE ELIMINAR ***
    old_data = audit_manager.extract_entity_data(user)
    username = user.username
    # *** FIN CAPTURA ***
    
    db.delete(user)
    
    # *** AÑADIR AUDIT TRAIL ***
    audit_manager.log_action(
        db=db,
        action="DELETE", 
        entity=user,
        user=current_user,
        request=request,
        old_data=old_data,
        notes=f"Usuario eliminado: {username}"
    )
    # *** FIN AUDIT TRAIL ***
    
    db.commit()
    return {"success": True, "message": "Usuario eliminado"}


@router.put("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    request: Request,  # ← AÑADIR Request
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="No puede desactivar su propio usuario")
    
    # *** CAPTURAR ESTADO ANTERIOR ***
    old_data = audit_manager.extract_entity_data(user)
    # *** FIN CAPTURA ***
    
    user.active = False
    db.commit()
    
    # *** AÑADIR AUDIT TRAIL ***
    new_data = audit_manager.extract_entity_data(user)
    audit_manager.log_action(
        db=db,
        action="UPDATE",
        entity=user,
        user=current_user,
        request=request,
        old_data=old_data,
        new_data=new_data,
        notes=f"Usuario desactivado: {user.username}"
    )
    db.commit()  # Commit del audit log
    # *** FIN AUDIT TRAIL ***
    
    return {"success": True, "message": "Usuario desactivado correctamente"}

@router.put("/users/{user_id}/change-password", response_model=PasswordChangeResponse)
def change_user_password(
    user_id: int,
    password_data: PasswordChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Solo administradores pueden cambiar contraseñas
):
    """
    Cambia la contraseña de un usuario específico.
    Solo administradores pueden usar este endpoint.
    """
    try:
        # Buscar el usuario
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=404, 
                detail=f"Usuario con ID {user_id} no encontrado"
            )
        
        # Validar que no se está intentando cambiar la contraseña del propio admin
        # (opcional - puedes comentar esto si quieres permitirlo)
        if current_user.id == user_id:
            raise HTTPException(
                status_code=400, 
                detail="No puedes cambiar tu propia contraseña desde aquí. Usa el perfil de usuario."
            )
        
        # Capturar datos anteriores para audit (sin la contraseña por seguridad)
        old_data = {
            "user_id": target_user.id,
            "username": target_user.username,
            "password_changed": False
        }
        
        # Hashear la nueva contraseña
        new_password_hash = get_password_hash(password_data.new_password)
        
        # Actualizar la contraseña
        target_user.password = new_password_hash
        
        db.commit()
        db.refresh(target_user)
        
        # Registrar en audit trail
        new_data = {
            "user_id": target_user.id,
            "username": target_user.username,
            "password_changed": True
        }
        
        audit_manager.log_action(
            db=db,
            action="UPDATE",
            entity=target_user,
            user=current_user,
            request=request,
            old_data=old_data,
            new_data=new_data,
            notes=f"Contraseña cambiada para usuario: {target_user.username}",
            metadata={
                "action_type": "password_change",
                "target_user_id": target_user.id,
                "target_username": target_user.username
            }
        )
        db.commit()
        
        logger.info(f"Administrador {current_user.username} cambió la contraseña del usuario {target_user.username}")
        
        return PasswordChangeResponse(
            success=True,
            message=f"Contraseña actualizada correctamente para {target_user.username}",
            user_id=target_user.id,
            username=target_user.username
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logger.error(f"Error cambiando contraseña para usuario {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno al cambiar contraseña: {str(e)}"
        )


# ---------------------------
# ENDPOINTS DE ROLES
# ---------------------------

@router.get("/roles")
def list_roles(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Lista todos los roles disponibles.
    Accesible para todos los usuarios autenticados.
    """
    roles = db.query(Role).all()
    return [{"id": r.id, "nombre": r.nombre} for r in roles]

#@router.get("/roles")
#def list_roles(db: Session = Depends(get_db), _admin=Depends(get_admin_user)):
#    roles = db.query(Role).all()
#    return [{"id": r.id, "nombre": r.nombre} for r in roles]

