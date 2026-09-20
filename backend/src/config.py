# backend/src/config.py
"""
Archivo de configuración central para el backend de GMAO.
Gestiona todas las variables de configuración desde variables de entorno.
"""
import os
from datetime import timedelta

# Cargar dotenv si está disponible (opcional para desarrollo)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # No falla si python-dotenv no está instalado

# Configuración de Base de Datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://Admin:postgres@localhost/gmao_db")

# Configuración de JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "insecure_key_for_development_only")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Tiempo de expiración como timedelta
JWT_ACCESS_TOKEN_EXPIRE_DELTA = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

# Configuración de API externa (Ollama)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Configuración inicial de Admin
INITIAL_ADMIN_USERNAME = os.getenv("INITIAL_ADMIN_USERNAME", "admin")
INITIAL_ADMIN_PASSWORD = os.getenv("INITIAL_ADMIN_PASSWORD", "changeThisPassword!")

# Configuración de almacenamiento
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "storage/uploads")
DOCUMENT_FOLDER = os.getenv("DOCUMENT_FOLDER", "storage/documents")