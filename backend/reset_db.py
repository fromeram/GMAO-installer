# reset_db.py

from sqlalchemy.orm import Session
from database import engine, Base
import models.menu        # Asegúrate de importar el modelo de menu
import models.role        # Asegúrate de importar el modelo de role
import models.user        # Asegúrate de importar el modelo de user
import models.section     # Asegúrate de importar el modelo de section
# Importa otros modelos según tu estructura

def reset_database():
    # Eliminar todas las tablas existentes
    Base.metadata.drop_all(bind=engine)
    
    # Crear todas las tablas definidas en los modelos
    Base.metadata.create_all(bind=engine)
    
    # Crear una sesión para insertar datos
    session = Session(bind=engine)
    
    # Insertar roles
    roles = [
        models.role.Role(id=1, nombre="Administrador"),
        models.role.Role(id=2, nombre="Mecanico"),
        models.role.Role(id=3, nombre="Usuario"),
        models.role.Role(id=4, nombre="Supervisor")
    ]
    session.add_all(roles)
    
    # Insertar secciones
    sections = [
        models.section.Section(id=1, nombre="Prensas"),
        models.section.Section(id=2, nombre="Mantenimiento")
    ]
    session.add_all(sections)
    
    # Insertar usuarios
    admin_user = models.user.User(
        id=1,
        username="admin",
        password="$2b$12$fajMNHjElPmT9zv7jABmouNRsNUNN1TZMbuGvXwIaXAfYMJ3ZmGsi",  # Contraseña hasheada
        role_id=1,
        section=None  # Asumiendo que 'section' es opcional para administradores
    )
    session.add(admin_user)
    
    # Insertar elementos del menú
    menu_items = [
        models.menu.Menu(nombre="Inicio", url="/home"),
        models.menu.Menu(nombre="Dashboard", url="/dashboard"),
        models.menu.Menu(nombre="Configuración", url="/settings"),
        # Agrega más elementos según tus necesidades
    ]
    session.add_all(menu_items)
    
    # Confirmar los cambios y cerrar la sesión
    session.commit()
    session.close()

if __name__ == "__main__":
    print("Creando tablas...")
    reset_database()
    print("Tablas creadas y datos iniciales insertados correctamente.")
