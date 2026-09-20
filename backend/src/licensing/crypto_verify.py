# src/licensing/crypto_verify.py
"""
Módulo de Verificación Criptográfica Asimétrica (RSA 2048-bit + SHA-256).
Utiliza exclusivamente la biblioteca estándar de Python sin dependencias externas.
La clave privada solo existe en posesión de Fran Romera para firmar licencias.
"""

import base64
import json
import hashlib
from typing import Tuple, Dict, Any, Optional

# Clave Pública RSA Oficial de Fran Romera (Modulus N y Exponente E)
PUBLIC_N = 29407280394681016658852463577282722320027853467559904295544225405316526965551693274899992139920174269838503610949730826765795388713435255789585515422662299931501066071903385212400813574656111289884864170158461112901970884221409881866834623885077085345967330211638985565690103044853353957799138248387308939034658182639203247037565529792537653933986634492311372478398868723474760662303072574988585754110987854486269777495091513283207624386188461187726732226734695479483130945776040355205134601956005214287388321904195889895652446418960762374160387550926117747802791390113723540461348890669357602074311224415291661868871
PUBLIC_E = 65537

def verify_license_signature(license_key: str, expected_machine_id: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Verifica la autenticidad matemática de una clave de activación para una máquina dada.
    Retorna (es_valido, payload, mensaje_error).
    """
    if not license_key or not isinstance(license_key, str):
        return False, None, "Clave de licencia vacía o no válida"
    
    key_clean = license_key.strip()
    if not key_clean.startswith("LIC-GMAO-"):
        return False, None, "Formato de clave no reconocido (debe comenzar con LIC-GMAO-)"
        
    try:
        raw_b64 = key_clean.replace("LIC-GMAO-", "").strip()
        data_json = json.loads(base64.b64decode(raw_b64.encode("ascii")).decode("utf-8"))
        
        if "d" not in data_json or "s" not in data_json:
            return False, None, "Estructura interna de la clave corrupta"
            
        payload_bytes = base64.b64decode(data_json["d"])
        sig_bytes = base64.b64decode(data_json["s"])
        sig_int = int.from_bytes(sig_bytes, "big")
        
        # Verificación criptográfica RSA PKCS#1 v1.5 con SHA-256
        decrypted_int = pow(sig_int, PUBLIC_E, PUBLIC_N)
        decrypted_bytes = decrypted_int.to_bytes(256, "big")
        
        expected_hash = hashlib.sha256(payload_bytes).digest()
        actual_hash = decrypted_bytes[-32:]
        
        if expected_hash != actual_hash:
            return False, None, "Firma digital de licencia inválida o manipulada"
            
        payload = json.loads(payload_bytes.decode("utf-8"))
        key_machine_id = payload.get("machine_id", "").strip().upper()
        
        if key_machine_id != expected_machine_id.strip().upper():
            return False, payload, f"Esta clave está vinculada al servidor {key_machine_id}, no coincide con {expected_machine_id}"
            
        return True, payload, "Licencia verificada con éxito"
        
    except Exception as e:
        return False, None, f"Error al procesar la clave de licencia: {str(e)}"
