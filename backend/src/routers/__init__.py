# routers/__init__.py — Router principal que agrupa todos los sub-routers
from fastapi import APIRouter

from .auth import router as auth_router
from .sections import router as sections_router
from .machines import router as machines_router
from .work_orders import router as work_orders_router
from .maintenance import router as maintenance_router
from .inventory import router as inventory_router
from .suppliers import router as suppliers_router
from .shifts import router as shifts_router
from .codes import router as codes_router
from .tasks import router as tasks_router
from .documents import router as documents_router
from .dashboard import router as dashboard_router
from .alerts import router as alerts_router
from .audit import router as audit_router, execute_auto_cleanup, AUTO_CLEANUP_CONFIG
from .formats import router as formats_router
from .communication_routes import router as communication_router

# Router principal unificado
router = APIRouter()

# Incluir todos los sub-routers con sus respectivos tags
router.include_router(auth_router, tags=["Autenticación"])
router.include_router(sections_router, tags=["Secciones y Líneas"])
router.include_router(machines_router, tags=["Máquinas"])
router.include_router(work_orders_router, tags=["Órdenes de Trabajo"])
router.include_router(maintenance_router, tags=["Mantenimiento"])
router.include_router(inventory_router, tags=["Inventario"])
router.include_router(suppliers_router, tags=["Proveedores"])
router.include_router(shifts_router, tags=["Turnos y Calendario"])
router.include_router(codes_router, tags=["Códigos FCR"])
router.include_router(tasks_router, tags=["Listas de Tareas"])
router.include_router(documents_router, tags=["Documentos"])
router.include_router(dashboard_router, tags=["Dashboard"])
router.include_router(alerts_router, tags=["Alertas"])
router.include_router(audit_router, tags=["Auditoría"])
router.include_router(formats_router, tags=["Formatos"])

# Alias main_router para compatibilidad
main_router = router

__all__ = [
    "router",
    "main_router",
    "auth_router",
    "sections_router",
    "machines_router",
    "work_orders_router",
    "maintenance_router",
    "inventory_router",
    "suppliers_router",
    "shifts_router",
    "codes_router",
    "tasks_router",
    "documents_router",
    "dashboard_router",
    "alerts_router",
    "audit_router",
    "formats_router",
    "communication_router",
    "execute_auto_cleanup",
    "AUTO_CLEANUP_CONFIG"
]
