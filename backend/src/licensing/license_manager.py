# src/licensing/license_manager.py
"""
Gestor del Ciclo de Vida de Licencia y Periodo de Evaluación de 3 Meses.
"""

from datetime import datetime, timezone, timedelta
from typing import Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from .machine_id import get_or_create_machine_id
from .crypto_verify import verify_license_signature
from ..models.system_license import SystemLicense

TRIAL_DAYS_DEFAULT = 90 # 3 Meses completos de evaluación

def ensure_license_record(db: Session) -> SystemLicense:
    """Asegura que exista un registro de licencia en la base de datos."""
    machine_id = get_or_create_machine_id()
    record = db.query(SystemLicense).first()
    
    if not record:
        record = SystemLicense(
            machine_id=machine_id,
            trial_days=TRIAL_DAYS_DEFAULT,
            license_type="trial",
            installed_at=datetime.now(timezone.utc),
            is_active=True
        )
        db.add(record)
        db.commit()
        db.refresh(record)
    elif not record.machine_id:
        record.machine_id = machine_id
        db.commit()
        
    return record

def get_license_status(db: Session) -> Dict[str, Any]:
    """
    Retorna el estado detallado de la licencia del sistema.
    """
    try:
        record = ensure_license_record(db)
        now = datetime.now(timezone.utc)
        
        # 1. Si está activado con licencia permanente o temporal
        if record.license_key and record.license_type != "trial":
            # Verificar validez matemática de la clave almacenada
            valid, payload, msg = verify_license_signature(record.license_key, record.machine_id)
            if valid and payload:
                # Comprobar si es permanente
                if payload.get("type") == "permanente" or not payload.get("expires_at"):
                    return {
                        "status": "licensed",
                        "machine_id": record.machine_id,
                        "license_type": "permanente",
                        "licensed_to": payload.get("client", record.licensed_to or "Licencia Oficial"),
                        "days_remaining": None,
                        "expires_at": None,
                        "installed_at": record.installed_at.isoformat() if record.installed_at else None,
                        "is_locked": False,
                        "message": "Licencia permanente activa"
                    }
                else:
                    # Licencia con fecha de caducidad
                    try:
                        exp_dt = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
                        if now <= exp_dt:
                            days_left = max(0, (exp_dt - now).days)
                            return {
                                "status": "licensed",
                                "machine_id": record.machine_id,
                                "license_type": "temporal",
                                "licensed_to": payload.get("client", record.licensed_to),
                                "days_remaining": days_left,
                                "expires_at": exp_dt.isoformat(),
                                "installed_at": record.installed_at.isoformat() if record.installed_at else None,
                                "is_locked": False,
                                "message": f"Licencia válida por {days_left} días"
                            }
                        else:
                            return {
                                "status": "expired",
                                "machine_id": record.machine_id,
                                "license_type": "temporal_expirada",
                                "licensed_to": payload.get("client", record.licensed_to),
                                "days_remaining": 0,
                                "expires_at": exp_dt.isoformat(),
                                "installed_at": record.installed_at.isoformat() if record.installed_at else None,
                                "is_locked": True,
                                "message": "Tu licencia comercial ha expirado. Contacta para renovarla."
                            }
                    except Exception:
                        pass

        # 2. Evaluación del Periodo de Prueba (Trial de 90 días)
        installed_at = record.installed_at
        if installed_at.tzinfo is None:
            installed_at = installed_at.replace(tzinfo=timezone.utc)
            
        trial_limit = installed_at + timedelta(days=record.trial_days or TRIAL_DAYS_DEFAULT)
        days_remaining = max(0, (trial_limit - now).days)
        
        if now > trial_limit:
            return {
                "status": "expired",
                "machine_id": record.machine_id,
                "license_type": "trial_expirado",
                "licensed_to": "Evaluación no activada",
                "days_remaining": 0,
                "expires_at": trial_limit.isoformat(),
                "installed_at": installed_at.isoformat(),
                "is_locked": True,
                "message": "El periodo de prueba de 3 meses ha finalizado. Por favor activa tu licencia."
            }
        else:
            return {
                "status": "trial",
                "machine_id": record.machine_id,
                "license_type": "trial",
                "licensed_to": "Versión de Evaluación",
                "days_remaining": days_remaining,
                "expires_at": trial_limit.isoformat(),
                "installed_at": installed_at.isoformat(),
                "is_locked": False,
                "message": f"Periodo de prueba activo: {days_remaining} días restantes"
            }
            
    except Exception as e:
        machine_id = get_or_create_machine_id()
        return {
            "status": "trial",
            "machine_id": machine_id,
            "license_type": "trial",
            "licensed_to": "Versión de Evaluación",
            "days_remaining": TRIAL_DAYS_DEFAULT,
            "expires_at": None,
            "installed_at": None,
            "is_locked": False,
            "message": f"Periodo de prueba: {TRIAL_DAYS_DEFAULT} días"
        }

def activate_license_key(license_key: str, db: Session) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Intenta activar una clave de licencia criptográfica.
    """
    record = ensure_license_record(db)
    valid, payload, error_msg = verify_license_signature(license_key, record.machine_id)
    
    if not valid or not payload:
        return False, error_msg, {}
        
    try:
        now = datetime.now(timezone.utc)
        record.license_key = license_key.strip()
        record.license_type = payload.get("type", "permanente")
        record.licensed_to = payload.get("client", "Cliente Oficial")
        record.activated_at = now
        
        if payload.get("expires_at"):
            record.expires_at = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
        else:
            record.expires_at = None
            
        record.is_active = True
        db.commit()
        db.refresh(record)
        
        status_info = get_license_status(db)
        return True, "¡Licencia activada con éxito!", status_info
        
    except Exception as e:
        db.rollback()
        return False, f"Error guardando la licencia: {str(e)}", {}
