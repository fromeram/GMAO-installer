# src/models/absence_crud.py (COMPLETO y Corregido)

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import date, timedelta
from typing import Optional, List

# --- Importación del modelo Absence (Corregida) ---
from .absence import Absence

# --- Schemas (Intenta importar o usa placeholders) ---
try:
    # Asumiendo que están en routes.py y no hay importación circular grave
    from routes import AbsenceCreate, AbsenceUpdate
except ImportError:
    from pydantic import BaseModel
    class AbsenceCreate(BaseModel): pass
    class AbsenceUpdate(BaseModel): pass
# --- Fin Schemas ---


def get_absence_by_id(db: Session, absence_id: int) -> Optional[Absence]:
    """Obtiene una ausencia específica por su ID."""
    return db.query(Absence).filter(Absence.id == absence_id).first()

def create_absence(db: Session, absence: AbsenceCreate) -> Absence:
    """Crea un nuevo registro de ausencia."""
    # Validar fechas
    if absence.start_date > absence.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin no puede ser anterior a la fecha de inicio."
        )
    # Crear instancia SQLAlchemy
    try: db_absence = Absence(**absence.model_dump()) # Pydantic V2+
    except AttributeError: db_absence = Absence(**absence.dict()) # Pydantic V1

    db.add(db_absence)
    db.commit()
    db.refresh(db_absence)
    return db_absence

# <<< --- FUNCIÓN QUE FALTABA --- >>>
def get_absences_for_period_and_users(db: Session, start: date, end: date, user_ids: List[int]) -> List[Absence]:
    """
    Obtiene todas las ausencias para una lista de usuarios que se solapan
    con el rango de fechas proporcionado.
    """
    if not user_ids:
        return [] # Devuelve lista vacía si no hay IDs de usuario
    return db.query(Absence).filter(
        Absence.user_id.in_(user_ids),
        Absence.start_date <= end, # La ausencia empieza antes o durante el fin del rango
        Absence.end_date >= start  # La ausencia termina después o durante el inicio del rango
    ).order_by(Absence.start_date).all()
# <<< --- FIN FUNCIÓN QUE FALTABA --- >>>

def update_absence(db: Session, absence_id: int, absence_data: AbsenceUpdate) -> Optional[Absence]:
    """Actualiza una ausencia existente."""
    db_absence = get_absence_by_id(db, absence_id)
    if not db_absence: return None # El endpoint manejará el 404

    try: update_data = absence_data.model_dump(exclude_unset=True) # Pydantic V2+
    except AttributeError: update_data = absence_data.dict(exclude_unset=True) # Pydantic V1

    for key, value in update_data.items(): setattr(db_absence, key, value)

    if isinstance(db_absence.start_date, date) and isinstance(db_absence.end_date, date) and \
       db_absence.start_date > db_absence.end_date:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La fecha de fin no puede ser anterior a la fecha de inicio.")
    db.commit(); db.refresh(db_absence)
    return db_absence

def delete_absence(db: Session, absence_id: int) -> bool:
    """Elimina una ausencia."""
    db_absence = get_absence_by_id(db, absence_id)
    if not db_absence: return False
    db.delete(db_absence); db.commit()
    return True