# backend/src/setup_gamification.py
"""
Script para inicializar el sistema de gamificación
Ejecutar una vez después de crear las tablas
"""

from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.gamification.achievements_setup import setup_default_achievements
from src.models.gamification import UserPoints
from src.models.user import User

def initialize_gamification():
    """Inicializa el sistema de gamificación"""
    db = SessionLocal()
    
    try:
        print("🎮 Inicializando sistema de gamificación...")
        
        # 1. Configurar logros predeterminados
        setup_default_achievements(db)
        
        # 2. Crear registros de puntos para usuarios existentes
        users_without_points = db.query(User).outerjoin(UserPoints).filter(
            UserPoints.id.is_(None),
            User.active == True
        ).all()
        
        for user in users_without_points:
            user_points = UserPoints(user_id=user.id)
            db.add(user_points)
            print(f"✅ Creado perfil de puntos para {user.username}")
        
        db.commit()
        
        print("🎉 Sistema de gamificación inicializado correctamente!")
        print(f"📊 Usuarios con perfil: {db.query(UserPoints).count()}")
        print(f"🏆 Logros disponibles: {db.query(Achievement).count()}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error inicializando gamificación: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    initialize_gamification()