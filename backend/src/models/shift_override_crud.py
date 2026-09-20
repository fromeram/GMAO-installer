# src/models/shift_override_crud.py (Versión corregida)

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from datetime import date
from typing import Optional, List

# --- Ajusta rutas de importación ---
from src.models.shift_override import ShiftOverride
from src.models.user import User # Para cargar relación user

# Asumiendo schemas en routes.py
try:
    from routes import ShiftOverrideCreate
except ImportError:
    from pydantic import BaseModel
    class ShiftOverrideCreate(BaseModel): pass
# --- Fin Ajustes ---


def get_override_by_id(db: Session, override_id: int) -> Optional[ShiftOverride]:
    """Obtiene un override por su ID."""
    return db.query(ShiftOverride).filter(ShiftOverride.id == override_id).first()

def get_override_for_user_and_date(db: Session, user_id: int, target_date: date) -> Optional[ShiftOverride]:
    """Obtiene el override para un usuario y fecha específicos (si existe)."""
    return db.query(ShiftOverride).filter(
        ShiftOverride.user_id == user_id,
        ShiftOverride.date == target_date
    ).first()

def get_overrides_for_period_and_users(db: Session, start: date, end: date, user_ids: List[int]) -> List[ShiftOverride]:
    """Obtiene todos los overrides para una lista de usuarios en un rango de fechas."""
    if not user_ids:
        return []
    
    return db.query(ShiftOverride).options(
        joinedload(ShiftOverride.user).load_only(User.id, User.username) # Solo cargar usuario
    ).filter(
        ShiftOverride.user_id.in_(user_ids),
        ShiftOverride.date >= start,
        ShiftOverride.date <= end
    ).order_by(ShiftOverride.date, ShiftOverride.user_id).all()

# Modifica esta función en src/models/shift_override_crud.py

def create_or_update_shift_override(db: Session, override_data: ShiftOverrideCreate) -> ShiftOverride:
    """
    Crea un nuevo override o actualiza uno existente si ya existe para ese usuario y fecha.
    Esto permite cambiar el turno para un día específico aunque ya tenga un override.
    """
    # Verificar que el usuario existe
    user = db.query(User).filter(User.id == override_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Usuario con ID {override_data.user_id} no encontrado"
        )
    
    # Verificar que el código de turno es válido
    valid_shift_codes = ['M', 'T', 'N']
    if override_data.actual_shift_code not in valid_shift_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Código de turno '{override_data.actual_shift_code}' no válido. Debe ser uno de: {', '.join(valid_shift_codes)}"
        )
    
    # Buscar si ya existe un override para este usuario y fecha
    existing = get_override_for_user_and_date(db, override_data.user_id, override_data.date)
    
    try:
        if existing:
            # ACTUALIZAR el override existente
            import logging
            logging.info(f"Actualizando override existente ID {existing.id} para usuario {override_data.user_id} en fecha {override_data.date}")
            
            # Actualizar el código de turno
            existing.actual_shift_code = override_data.actual_shift_code
            
            # Actualizar notas si se proporcionan
            if override_data.notes is not None:
                existing.notes = override_data.notes
                
            db_override = existing
        else:
            # Crear un nuevo override
            try: 
                # Intentar con Pydantic v2
                db_override = ShiftOverride(**override_data.model_dump())
            except AttributeError:
                # Fallback a Pydantic v1
                db_override = ShiftOverride(**override_data.dict())
                
            db.add(db_override)
            
        db.commit()
        db.refresh(db_override)
        return db_override
    except Exception as e:
        db.rollback()
        # Loggear el error para diagnóstico
        import logging
        logging.error(f"Error al crear/actualizar ShiftOverride: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al crear/actualizar override: {str(e)}"
        )
    
    # Verificar que el usuario existe
    user = db.query(User).filter(User.id == override_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Usuario con ID {override_data.user_id} no encontrado"
        )
    
    # Verificar que el código de turno es válido
    valid_shift_codes = ['M', 'T', 'N']
    if override_data.actual_shift_code not in valid_shift_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Código de turno '{override_data.actual_shift_code}' no válido. Debe ser uno de: {', '.join(valid_shift_codes)}"
        )
    
    # Crear el objeto ShiftOverride
    try: 
        # Intentar con Pydantic v2
        db_override = ShiftOverride(**override_data.model_dump())
    except AttributeError:
        # Fallback a Pydantic v1
        db_override = ShiftOverride(**override_data.dict())
    
    try:
        db.add(db_override)
        db.commit()
        db.refresh(db_override)
        return db_override
    except Exception as e:
        db.rollback()
        # Loggear el error para diagnóstico
        import logging
        logging.error(f"Error al crear ShiftOverride: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al crear override: {str(e)}"
        )

def delete_shift_override(db: Session, override_id: int) -> bool:
    """Elimina un override."""
    db_override = get_override_by_id(db, override_id)
    if not db_override: return False
    
    try:
        db.delete(db_override)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        import logging
        logging.error(f"Error al eliminar ShiftOverride {override_id}: {str(e)}", exc_info=True)
        return False
