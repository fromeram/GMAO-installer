# src/storage/paths.py
import os
from datetime import datetime

STORAGE_BASE = "storage"
DOCUMENT_TYPES = {
    'albaran': 'albaranes',
    'parte_trabajo': 'partes',
    'otros': 'otros'
}

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf', '.txt', '.rtf', '.pages'}  # Añadido .pages para Mac

def init_storage():
    """Inicializa la estructura de carpetas"""
    for doc_type in DOCUMENT_TYPES.values():
        path = os.path.join(STORAGE_BASE, doc_type)
        os.makedirs(path, exist_ok=True)

def get_storage_path(filename: str, doc_type: str) -> str:
    """Genera ruta de almacenamiento con estructura por año/mes"""
    now = datetime.now()
    type_folder = DOCUMENT_TYPES.get(doc_type, 'otros')
    year_month = now.strftime('%Y/%m')
    
    # Crear estructura año/mes si no existe
    full_path = os.path.join(STORAGE_BASE, type_folder, year_month)
    os.makedirs(full_path, exist_ok=True)
    
    # Generar nombre único
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    ext = os.path.splitext(filename)[1].lower()
    new_filename = f"{timestamp}_{filename}"
    
    return os.path.join(full_path, new_filename)