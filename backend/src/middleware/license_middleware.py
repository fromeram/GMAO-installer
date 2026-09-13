# src/middleware/license_middleware.py
"""
Middleware de Control de Acceso por Licencia y Periodo de Evaluación.
Bloquea el acceso operacional cuando el trial de 3 meses ha finalizado.
"""

import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..database import SessionLocal
from ..licensing.license_manager import get_license_status

# Rutas permitidas incluso con licencia expirada
EXEMPT_PATHS = {
    "/license/status",
    "/license/activate",
    "/license/contact",
    "/health",
    "/token",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/favicon.ico"
}

class LicenseEnforcementMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # 1. Rutas exentas y preflight CORS siempre permitidos
        if request.method == "OPTIONS":
            return await call_next(request)
            
        for exempt in EXEMPT_PATHS:
            if path == exempt or path.startswith("/static/") or path.startswith("/api/license/"):
                return await call_next(request)
                
        # 2. Comprobar estado de la licencia en la base de datos
        db = SessionLocal()
        try:
            status_info = get_license_status(db)
            if status_info.get("is_locked", False):
                return JSONResponse(
                    status_code=402, # Payment Required / License Expired
                    content={
                        "detail": "LICENSE_EXPIRED",
                        "message": "El periodo de prueba de 3 meses de GMAO System ha finalizado.",
                        "machine_id": status_info.get("machine_id"),
                        "days_remaining": 0,
                        "contact": "franromeramartinez@... / GitHub: fromeram"
                    }
                )
        except Exception:
            # En caso de error de BD momentáneo, permitir la petición para no interrumpir
            pass
        finally:
            db.close()
            
        return await call_next(request)
