# src/models/vacation_request_crud.py
from sqlalchemy.orm import Session, joinedload, load_only
from fastapi import HTTPException, status
from datetime import date, datetime, timedelta # Añadido timedelta
from typing import Optional, List

# --- Ajusta rutas de importación ---
from src.models.vacation_request import VacationRequest
from src.models.user import User
from src.models.absence import Absence
# Importar absence_crud para crear la ausencia
from src.models import absence_crud
# Asumiendo schemas en routes.py
try:
    from routes import VacationRequestCreate, VacationRequestUpdate, AbsenceCreate
except ImportError:
    from pydantic import BaseModel
    class VacationRequestCreate(BaseModel): pass
    class VacationRequestUpdate(BaseModel): pass
    class AbsenceCreate(BaseModel): pass # Necesario para crear Ausencia
import logging # Añadir logging
logger = logging.getLogger(__name__)
# --- Fin Ajustes ---

def get_request_by_id(db: Session, request_id: int) -> Optional[VacationRequest]:
    """Obtiene una solicitud por ID, cargando relaciones de usuario."""
    return db.query(VacationRequest).options(
        joinedload(VacationRequest.user).load_only(User.id, User.username),
        joinedload(VacationRequest.reviewed_by).load_only(User.id, User.username)
    ).filter(VacationRequest.id == request_id).first()

def get_requests(
    db: Session,
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[VacationRequest]:
    """Obtiene una lista de solicitudes con filtros opcionales."""
    query = db.query(VacationRequest).options(
        joinedload(VacationRequest.user).load_only(User.id, User.username),
        joinedload(VacationRequest.reviewed_by).load_only(User.id, User.username)
    )
    if user_id is not None: query = query.filter(VacationRequest.user_id == user_id)
    if status is not None: query = query.filter(VacationRequest.status == status)
    # Filtrar por solapamiento de fechas
    if start_date: query = query.filter(VacationRequest.end_date >= start_date)
    if end_date: query = query.filter(VacationRequest.start_date <= end_date)

    return query.order_by(VacationRequest.created_at.desc()).all()


def create_request(db: Session, request_data: VacationRequestCreate) -> VacationRequest:
    """Crea una nueva solicitud de vacaciones."""
    try: db_request = VacationRequest(**request_data.dict()) # Pydantic v1
    except AttributeError: db_request = VacationRequest(**request_data.model_dump()) # Pydantic v2+
    db_request.status = 'Solicitado' # Asegurar estado inicial

    db.add(db_request)
    db.commit()
    db.refresh(db_request)  # Quitamos el parámetro ['user'] que causaba el error
    
    return db_request

def update_request_status(
    db: Session,
    request_id: int,
    status_update: VacationRequestUpdate,
    reviewer_id: int
) -> Optional[VacationRequest]:
    """Actualiza el estado y notas de una solicitud (Aprobar/Rechazar)."""
    db_request = get_request_by_id(db, request_id)
    if not db_request: return None # 404

    if db_request.status != 'Solicitado':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se pueden procesar solicitudes pendientes.")

    db_request.status = status_update.status
    db_request.manager_notes = status_update.manager_notes
    db_request.reviewed_by_id = reviewer_id
    # Nota: updated_at se actualiza automáticamente por onupdate=func.now() si lo tienes en el modelo
    # Si no, descomenta la línea de abajo y asegúrate de importar datetime
    # db_request.updated_at = datetime.utcnow()

    # --- Crear Ausencia si se aprueba ---
    if db_request.status == 'Aprobado':
        logger.info(f"Solicitud {request_id} aprobada. Intentando crear ausencia...")
        try:
            # Preparar datos para crear la ausencia (UNA por cada día del rango)
            # Esto asegura que el calendario base la muestre correctamente
            current_d = db_request.start_date
            while current_d <= db_request.end_date:
                # Crear diccionario directamente en lugar de usar el modelo AbsenceCreate
                absence_data = {
                    "user_id": db_request.user_id,
                    "start_date": current_d,
                    "end_date": current_d,  # Ausencia por día individual
                    "absence_type": "V",
                    "notes": f"Vacaciones aprobadas (Solicitud ID: {db_request.id}). {db_request.manager_notes or ''}".strip()
                }
                
                # Crear la ausencia directamente sin validación Pydantic
                try:
                    absence = Absence(
                        user_id=absence_data["user_id"],
                        start_date=absence_data["start_date"],
                        end_date=absence_data["end_date"],
                        absence_type=absence_data["absence_type"],
                        notes=absence_data["notes"]
                    )
                    db.add(absence)
                    db.flush()  # Flush para detectar errores antes del commit final
                    logger.info(f"Creada Ausencia 'V' para usuario {db_request.user_id} en fecha {current_d} (Solicitud {request_id})")
                except Exception as e_absence_create:
                    logger.error(f"Error creando ausencia para fecha {current_d}: {e_absence_create}")
                    raise e_absence_create
                
                # Prevenir bucle infinito
                if db_request.start_date > db_request.end_date:
                    break
                current_d += timedelta(days=1)

        except Exception as e_absence:
            db.rollback() # DESHACER la aprobación si falla la creación de ausencias
            logger.error(f"Error al crear Absence para VacationRequest ID {request_id}: {e_absence}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear el registro de ausencia. La aprobación fue cancelada."
            ) from e_absence

    # Confirmar cambios en la solicitud (y ausencias si se aprobaron)
    db.commit()
    db.refresh(db_request)
    db.refresh(db_request, ['user', 'reviewed_by']) # Cargar relaciones para respuesta
    return db_request


def delete_request(db: Session, request_id: int, requesting_user_id: int, is_manager: bool) -> bool:
    """Elimina una solicitud. Solo si está 'Solicitado'."""
    db_request = get_request_by_id(db, request_id)
    if not db_request: return False # 404

    # Verificar permisos: Solo el creador o un manager pueden borrar
    can_delete = (requesting_user_id == db_request.user_id or is_manager)
    if not can_delete:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para eliminar esta solicitud.")

    if db_request.status != 'Solicitado':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se pueden eliminar solicitudes pendientes.")

    db.delete(db_request)
    db.commit()
    return True