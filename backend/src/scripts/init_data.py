from sqlalchemy.orm import Session
from src.models.role import Role
from src.models.user import User
from src.auth import get_password_hash

def init_db(db: Session):
    try:
        # Crear rol de administrador si no existe
        admin_role = db.query(Role).filter(Role.nombre == "Administrador").first()
        if not admin_role:
            admin_role = Role(
                id=1,
                nombre="Administrador"
            )
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            
        # Crear usuario Admin si no existe
        admin_user = db.query(User).filter(User.username == "Admin").first()
        if not admin_user:
            hashed_password = get_password_hash(os.getenv("INITIAL_ADMIN_PASSWORD", "admin123"))
            admin_user = User(
                username="Admin",
                password=hashed_password,
                role_id=admin_role.id
            )
            db.add(admin_user)
            db.commit()
            
        return True
    except Exception as e:
        print(f"Error en la inicialización: {e}")
        db.rollback()
        return False