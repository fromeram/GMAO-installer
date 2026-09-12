# src/storage/__init__.py
import os

STORAGE_BASE = "storage"
DOCUMENT_TYPES = {
    'albaran': 'albaranes',
    'parte_trabajo': 'partes',
    'otros': 'otros'
}

def init_storage():
    """Inicializa la estructura de carpetas"""
    for doc_type in DOCUMENT_TYPES.values():
        path = os.path.join(STORAGE_BASE, doc_type)
        os.makedirs(path, exist_ok=True)