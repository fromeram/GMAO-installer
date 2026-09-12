# schemas/common.py — Enums, constantes de roles y dependencias compartidas
from enum import Enum
from fastapi import Depends, HTTPException, status
from src.auth import get_current_user
from src.models.user import User

# --- Enums ---
class ProductType(str, Enum):
    MECANICO = "mecánico"
    ELECTRICO = "eléctrico"
    NEUMATICO = "neumático"
    LIMPIEZA = "limpieza"

# --- Constantes de Roles ---
PROXY_URL = "http://192.168.1.62:5000"

VACATION_MANAGER_ROLES = ["Administrador", "Jefe de Mantenimiento", "Jefe Sección", "Calidad"]
MANAGER_ROLES = ["Administrador", "Jefe de Mantenimiento", "Jefe Sección"]
INVENTORY_ACCESS_ROLES = ["Administrador", "Jefe de Mantenimiento", "Jefe Sección", "Calidad", "Contabilidad"]
FINANCIAL_ACCESS_ROLES = ["Administrador", "Jefe de Mantenimiento", "Calidad", "Contabilidad"]
PRODUCT_EDIT_ROLES = ["Administrador", "Jefe de Mantenimiento"]
RESTRICTED_WORKER_ROLES = ["Mecánico"]
CONSULTANT_ROLES = ["Calidad", "Contabilidad"]
CALENDAR_ACCESS_ROLES = ["Administrador", "Jefe de Mantenimiento", "Jefe Sección", "Mecánico", "Calidad", "Contabilidad"]

# --- Dependencias de permisos ---
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
