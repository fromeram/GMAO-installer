# backend/src/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
from src.config import DATABASE_URL

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear engine con configuración desde variables de entorno
engine = create_engine(
    DATABASE_URL,
    pool_size=30,
    max_overflow=60
)

# Creación de sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        # Asegurarse de que siempre se cierra es crucial
        try:
            db.close()
        except Exception as e_close:
             # Loguear si falla el cierre
             logger.error(f"Error cerrando la sesión de DB: {e_close}", exc_info=True)