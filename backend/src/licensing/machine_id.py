# src/licensing/machine_id.py
"""
Generador y extractor de Identificador de Máquina Único (Machine ID).
Estable, persistente e irrepetible para cada servidor o instancia.
"""

import os
import uuid
import platform
import hashlib

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
MACHINE_ID_FILE = os.path.join(STORAGE_DIR, "machine_id.key")

def get_or_create_machine_id() -> str:
    """
    Obtiene el ID de máquina almacenado o genera uno nuevo si no existe.
    Formato: GMAO-XXXX-XXXX-XXXX
    """
    os.makedirs(STORAGE_DIR, exist_ok=True)
    
    # 1. Si ya existe un ID guardado en disco, lo usamos directamente
    if os.path.exists(MACHINE_ID_FILE):
        try:
            with open(MACHINE_ID_FILE, "r", encoding="utf-8") as f:
                saved_id = f.read().strip().upper()
                if saved_id.startswith("GMAO-") and len(saved_id) >= 19:
                    return saved_id
        except Exception:
            pass
            
    # 2. Generar huella basada en hardware y red
    try:
        node_mac = uuid.getnode()
        hostname = platform.node()
        system_info = f"{node_mac}:{hostname}:{platform.machine()}"
    except Exception:
        system_info = str(uuid.uuid4())
        
    h = hashlib.sha256(system_info.encode("utf-8")).hexdigest()[:16].upper()
    generated_id = f"GMAO-{h[0:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"
    
    # 3. Guardar para garantizar persistencia
    try:
        with open(MACHINE_ID_FILE, "w", encoding="utf-8") as f:
            f.write(generated_id)
    except Exception:
        pass
        
    return generated_id
