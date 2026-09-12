#!/usr/bin/env python
"""
Script de configuración inicial para el sistema GMAO.
Crea las tablas y el usuario administrador inicial si no existen.
"""
import os
import logging
from sqlalchemy.orm import Session

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar solo después de configurar logging
from src.database import engine, Base
from src.models.user import User
from src.models.role import Role
from src.auth import get_password_hash
from src.config import INITIAL_ADMIN_USERNAME, INITIAL_ADMIN_PASSWORD

def setup_database():
    """Crea las tablas en la base de datos si no existen."""
    logger.info("Creando tablas en la base de datos...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas creadas correctamente.")
    except Exception as e:
        logger.error(f"Error al crear las tablas: {e}")
        raise

def create_admin_role(db: Session):
    """Crea el rol de administrador si no existe."""
    logger.info("Verificando rol de administrador...")
    admin_role = db.query(Role).filter(Role.nombre == "Administrador").first()
    if not admin_role:
        logger.info("Creando rol de administrador...")
        admin_role = Role(nombre="Administrador")
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)
        logger.info(f"Rol de administrador creado con ID: {admin_role.id}")
    else:
        logger.info(f"El rol de administrador ya existe con ID: {admin_role.id}")
    return admin_role

def create_admin_user(db: Session, role_id: int):
    """Crea el usuario administrador inicial si no existe."""
    logger.info(f"Verificando usuario administrador '{INITIAL_ADMIN_USERNAME}'...")
    
    admin_user = db.query(User).filter(User.username == INITIAL_ADMIN_USERNAME).first()
    if not admin_user:
        logger.info(f"Creando usuario administrador '{INITIAL_ADMIN_USERNAME}'...")
        hashed_password = get_password_hash(INITIAL_ADMIN_PASSWORD)
        admin_user = User(
            username=INITIAL_ADMIN_USERNAME,
            password=hashed_password,
            role_id=role_id,
            active=True
        )
        db.add(admin_user)
        db.commit()
        logger.info(f"Usuario administrador '{INITIAL_ADMIN_USERNAME}' creado con ID: {admin_user.id}")
        logger.warning(f"¡IMPORTANTE! Cambie la contraseña del administrador después del primer inicio de sesión.")
    else:
        logger.info(f"El usuario administrador '{INITIAL_ADMIN_USERNAME}' ya existe con ID: {admin_user.id}")
    return admin_user

def create_other_roles(db: Session):
    """Crea otros roles básicos si no existen."""
    roles = ["Jefe de Mantenimiento", "Jefe de Sección", "Mecánico"]
    for role_name in roles:
        existing_role = db.query(Role).filter(Role.nombre == role_name).first()
        if not existing_role:
            new_role = Role(nombre=role_name)
            db.add(new_role)
            logger.info(f"Rol '{role_name}' creado.")
    db.commit()
    logger.info("Roles básicos verificados/creados.")

def main():
    """Función principal del script de configuración."""
    logger.info("Iniciando script de configuración inicial...")
    
    try:
        # Crear estructura de base de datos
        setup_database()
        
        # Crear sesión para operaciones de datos
        from src.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Crear roles y usuario administrador
            admin_role = create_admin_role(db)
            create_admin_user(db, admin_role.id)
            create_other_roles(db)
            
            logger.info("Configuración inicial completada con éxito.")
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error en la configuración inicial: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())