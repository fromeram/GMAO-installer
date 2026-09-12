# scripts/add_new_roles.py
"""
Script para añadir los nuevos roles Calidad y Contabilidad
"""
import sys
import os

# Añadir el directorio padre al path para poder importar src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models.role import Role

def add_new_roles():
    """Añade los nuevos roles Calidad y Contabilidad"""
    db = SessionLocal()
    
    try:
        # Verificar si los roles ya existen
        existing_calidad = db.query(Role).filter(Role.nombre == "Calidad").first()
        existing_contabilidad = db.query(Role).filter(Role.nombre == "Contabilidad").first()
        
        roles_added = []
        
        # Crear rol Calidad si no existe
        if not existing_calidad:
            role_calidad = Role(nombre="Calidad")
            db.add(role_calidad)
            roles_added.append("Calidad")
            print("✅ Rol 'Calidad' creado")
        else:
            print("ℹ️ Rol 'Calidad' ya existe")
        
        # Crear rol Contabilidad si no existe
        if not existing_contabilidad:
            role_contabilidad = Role(nombre="Contabilidad")
            db.add(role_contabilidad)
            roles_added.append("Contabilidad")
            print("✅ Rol 'Contabilidad' creado")
        else:
            print("ℹ️ Rol 'Contabilidad' ya existe")
        
        if roles_added:
            db.commit()
            print(f"🎉 Roles creados exitosamente: {', '.join(roles_added)}")
        else:
            print("✨ No hay roles nuevos que crear")
            
        # Mostrar todos los roles actuales
        all_roles = db.query(Role).all()
        print("\n📋 Roles actuales en el sistema:")
        for role in all_roles:
            print(f"  - ID: {role.id}, Nombre: {role.nombre}")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear roles: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_new_roles()