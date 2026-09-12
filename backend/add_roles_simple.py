# add_roles_simple.py - Ejecutar desde la carpeta backend
"""
Script simple para añadir los roles Calidad y Contabilidad
Ejecutar desde: backend/
"""

import sys
import os

# Configurar el path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
sys.path.insert(0, project_dir)

# Ahora importar
try:
    from src.database import SessionLocal
    from src.models.role import Role
    print("✅ Importaciones exitosas")
except Exception as e:
    print(f"❌ Error en importaciones: {e}")
    sys.exit(1)

def add_new_roles():
    """Añade los nuevos roles Calidad y Contabilidad"""
    print("🚀 Iniciando proceso de creación de roles...")
    
    db = SessionLocal()
    
    try:
        # Verificar conexión a la base de datos
        db.execute("SELECT 1")
        print("✅ Conexión a base de datos exitosa")
        
        # Verificar si los roles ya existen
        existing_calidad = db.query(Role).filter(Role.nombre == "Calidad").first()
        existing_contabilidad = db.query(Role).filter(Role.nombre == "Contabilidad").first()
        
        roles_added = []
        
        # Crear rol Calidad si no existe
        if not existing_calidad:
            role_calidad = Role(nombre="Calidad")
            db.add(role_calidad)
            roles_added.append("Calidad")
            print("✅ Rol 'Calidad' preparado para creación")
        else:
            print("ℹ️ Rol 'Calidad' ya existe")
        
        # Crear rol Contabilidad si no existe
        if not existing_contabilidad:
            role_contabilidad = Role(nombre="Contabilidad")
            db.add(role_contabilidad)
            roles_added.append("Contabilidad")
            print("✅ Rol 'Contabilidad' preparado para creación")
        else:
            print("ℹ️ Rol 'Contabilidad' ya existe")
        
        if roles_added:
            # Hacer commit de los cambios
            db.commit()
            print(f"🎉 Roles creados exitosamente: {', '.join(roles_added)}")
        else:
            print("✨ No hay roles nuevos que crear")
            
        # Mostrar todos los roles actuales
        all_roles = db.query(Role).all()
        print("\n📋 Roles actuales en el sistema:")
        for role in all_roles:
            print(f"  - ID: {role.id}, Nombre: {role.nombre}")
            
        print("\n🎯 Proceso completado exitosamente!")
        return True
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear roles: {str(e)}")
        import traceback
        print(f"📋 Detalles del error:")
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 50)
    print("🏭 GMAO - Creador de Roles Calidad y Contabilidad")
    print("=" * 50)
    
    success = add_new_roles()
    
    if success:
        print("\n✅ ¡Script ejecutado correctamente!")
        print("📌 Ahora puedes crear usuarios con estos roles desde la interfaz web.")
    else:
        print("\n❌ Script falló. Revisa los errores arriba.")
        sys.exit(1)