# backend/src/middleware/audit_middleware.py
"""
Middleware para capturar automáticamente cambios en el sistema
y registrarlos en el Audit Trail.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect
from fastapi import Request

from src.models.audit_log import AuditLog
from src.models.user import User
import logging
logger = logging.getLogger(__name__) 

class AuditTrailManager:
    """
    Gestor principal del sistema de Audit Trail.
    Se integra con tus endpoints existentes sin modificar su lógica.
    """
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        
        # Entidades que queremos auditar
        self.tracked_entities = {
            'WorkOrder': {'severity': 'HIGH', 'module': 'maintenance'},
            'Machine': {'severity': 'MEDIUM', 'module': 'assets'},
            'User': {'severity': 'HIGH', 'module': 'users'},
            'Inventory': {'severity': 'MEDIUM', 'module': 'inventory'},
            'Maintenance': {'severity': 'MEDIUM', 'module': 'maintenance'},
            'Supplier': {'severity': 'LOW', 'module': 'inventory'},
            'FailureCode': {'severity': 'LOW', 'module': 'maintenance'},
            'CauseCode': {'severity': 'LOW', 'module': 'maintenance'},
            'RemedyCode': {'severity': 'LOW', 'module': 'maintenance'},
            'MaintenanceBacklog': {'severity': 'MEDIUM', 'module': 'maintenance'},
            'DocumentAttachment': {'severity': 'LOW', 'module': 'documents'},
        }
        
        # Campos sensibles que queremos ofuscar en los logs
        self.sensitive_fields = ['password', 'password_hash', 'token', 'secret']
    
    def should_audit(self, entity: Any) -> bool:
        """Determina si una entidad debe ser auditada"""
        entity_name = entity.__class__.__name__
        return entity_name in self.tracked_entities
    
    def extract_entity_data(self, entity: Any) -> Dict[str, Any]:
        """Extrae datos relevantes de una entidad para el audit"""
        if not entity:
            return {}
        
        # Usar SQLAlchemy inspection para obtener los datos
        mapper = inspect(entity.__class__)
        data = {}
        
        for column in mapper.columns:
            value = getattr(entity, column.name, None)
            
            # Ofuscar campos sensibles
            if column.name in self.sensitive_fields:
                data[column.name] = "***HIDDEN***"
            # Convertir datetime a string para JSON
            elif isinstance(value, datetime):
                data[column.name] = value.isoformat() if value else None
            # Convertir otros tipos no serializables
            elif value is not None:
                try:
                    json.dumps(value)  # Test si es serializable
                    data[column.name] = value
                except (TypeError, ValueError):
                    data[column.name] = str(value)
            else:
                data[column.name] = None
        
        return data
    
    def generate_changes_summary(self, old_data: Dict, new_data: Dict, entity_type: str) -> str:
        """Genera un resumen legible de los cambios"""
        if not old_data:
            return f"Creado nuevo {entity_type}"
        
        if not new_data:
            return f"Eliminado {entity_type}"
        
        changes = []
        for key, new_value in new_data.items():
            old_value = old_data.get(key)
            if old_value != new_value and key not in self.sensitive_fields:
                # Formatear cambios específicos por tipo
                if key == 'status':
                    changes.append(f"Estado: {old_value} → {new_value}")
                elif key == 'quantity':
                    changes.append(f"Cantidad: {old_value} → {new_value}")
                elif key == 'assigned_to_id':
                    changes.append(f"Asignado a: ID {old_value} → ID {new_value}")
                elif 'date' in key.lower() or 'time' in key.lower():
                    changes.append(f"{key}: {old_value} → {new_value}")
                else:
                    # Para otros campos, mostrar cambio genérico
                    old_str = str(old_value)[:50] + "..." if len(str(old_value)) > 50 else str(old_value)
                    new_str = str(new_value)[:50] + "..." if len(str(new_value)) > 50 else str(new_value)
                    changes.append(f"{key}: {old_str} → {new_str}")
        
        if not changes:
            return f"Actualizado {entity_type} (sin cambios significativos)"
        
        return f"Actualizado {entity_type}: " + ", ".join(changes[:3])  # Máximo 3 cambios en resumen
    
    def log_action(
        self,
        db: Session,
        action: str,
        entity: Any,
        user: User,
        request: Request = None,
        old_data: Dict = None,
        new_data: Dict = None,
        notes: str = None,
        metadata: Dict = None
    ):
        """
        Registra una acción en el audit trail.
        
        Args:
            db: Sesión de base de datos
            action: Tipo de acción (CREATE, UPDATE, DELETE, etc.)
            entity: Objeto sobre el que se realizó la acción
            user: Usuario que realizó la acción
            request: Request HTTP (opcional, para obtener IP y user-agent)
            old_data: Estado anterior del objeto (para UPDATE/DELETE)
            new_data: Nuevo estado del objeto (para CREATE/UPDATE)
            notes: Notas adicionales
            metadata: Metadatos específicos de la acción
        """
        
        if not self.should_audit(entity):
            return
        
        entity_type = entity.__class__.__name__
        entity_config = self.tracked_entities[entity_type]
        
        # Obtener datos del request si está disponible
        ip_address = None
        user_agent = None
        if request:
            # Obtener IP real considerando proxies
            ip_address = (
                request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
                request.headers.get("X-Real-IP") or
                request.client.host if request.client else None
            )
            user_agent = request.headers.get("User-Agent")
        
        # Si no tenemos old_data/new_data, extraerlos del entity actual
        if action == "CREATE" and not new_data:
            new_data = self.extract_entity_data(entity)
        elif action == "DELETE" and not old_data:
            old_data = self.extract_entity_data(entity)
        elif action == "UPDATE":
            if not new_data:
                new_data = self.extract_entity_data(entity)
        
        # Generar resumen de cambios
        changes_summary = self.generate_changes_summary(old_data or {}, new_data or {}, entity_type)
        
        # Crear registro de audit
        audit_entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=getattr(entity, 'id', None),
            user_id=user.id,
            user_name=user.username,
            user_role=user.role.nombre if user.role else None,
            #timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            old_values=old_data,
            new_values=new_data,
            changes_summary=changes_summary,
            module=entity_config['module'],
            severity=entity_config['severity'],
            notes=notes,
            session_id=self.session_id,
            #extra_metadata=metadata or {}  # ← CAMBIAR extra_data por metadata
        )
        
        try:
            db.add(audit_entry)
            # NO hacer commit aquí - dejar que lo haga el endpoint principal
            print(f"[AUDIT] {changes_summary} por {user.username}")
        except Exception as e:
            print(f"[AUDIT ERROR] No se pudo registrar audit log: {e}")
            # No fallar la operación principal por un error de audit
    
    def log_login(self, db: Session, user: User, request: Request, success: bool = True):
        """Registra intentos de login"""
        try:
            logger.info(f"[AUDIT] Iniciando log_login para usuario: {user.username}, success: {success}")
            
            action = "LOGIN" if success else "LOGIN_FAILED"
            
            # Obtener datos del request si está disponible
            ip_address = None
            user_agent = None
            if request:
                # Obtener IP real considerando proxies
                ip_address = (
                    request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
                    request.headers.get("X-Real-IP") or
                    request.client.host if request.client else "unknown"
                )
                user_agent = request.headers.get("User-Agent", "unknown")
                logger.debug(f"[AUDIT] IP: {ip_address}, User-Agent: {user_agent[:50]}...")
            
            # Crear el registro de audit log
            logger.debug(f"[AUDIT] Creando AuditLog con action: {action}")
            
            audit_entry = AuditLog(
                action=action,
                entity_type="User",
                entity_id=user.id,
                user_id=user.id,
                user_name=user.username,
                user_role=user.role.nombre if user.role else "Unknown",
                #timestamp=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                old_values=None,
                new_values=None,
                changes_summary=f"Login {'exitoso' if success else 'fallido'} para usuario {user.username}",
                module="authentication",
                severity="MEDIUM" if success else "HIGH",
                notes=f"Login {'exitoso' if success else 'fallido'} desde IP: {ip_address}",
                session_id=self.session_id
            )
            
            logger.debug(f"[AUDIT] AuditLog creado, añadiendo a DB...")
            db.add(audit_entry)
            
            # NO hacer commit aquí - dejar que lo haga el endpoint principal
            logger.info(f"[AUDIT] Login {'exitoso' if success else 'fallido'} registrado para {user.username}")
            
        except Exception as e:
            logger.error(f"[AUDIT ERROR] No se pudo registrar login audit: {e}", exc_info=True)
            # No fallar la operación principal por un error de audit
    
    def log_export(self, db: Session, user: User, export_type: str, entity_count: int, request: Request = None):
        """Registra exportaciones de datos"""
        class ExportAction:
            def __init__(self):
                self.id = None
                self.__class__.__name__ = "Export"
        
        pseudo_entity = ExportAction()
        
        metadata = {
            'export_type': export_type,
            'entity_count': entity_count,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.log_action(
            db=db,
            action="EXPORT",
            entity=pseudo_entity,
            user=user,
            request=request,
            metadata=metadata,
            notes=f"Exportó {entity_count} registros de {export_type}"
        )

# Instancia global del audit manager
audit_manager = AuditTrailManager()