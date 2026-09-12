#!/usr/bin/env python3
"""
Script para otorgar logros retroactivamente a usuarios que ya tienen puntos
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configurar conexión directa a la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gmao_user:gmao_pass@db:5432/gmao_db")

def get_db_connection():
    """Crear conexión directa a la base de datos"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal(), engine

def award_retroactive_achievements():
    """Otorgar logros retroactivamente basado en órdenes completadas"""
    
    db, engine = get_db_connection()
    
    try:
        # Obtener usuarios con puntos pero sin logros
        users_query = """
        SELECT up.user_id, u.username, up.total_points,
               (SELECT COUNT(*) FROM work_orders wo WHERE wo.assigned_to_id = up.user_id AND wo.status = 'Cerrada') as completed_orders,
               (SELECT COUNT(*) FROM user_achievements ua WHERE ua.user_id = up.user_id) as current_achievements
        FROM user_points up
        JOIN users u ON up.user_id = u.id
        WHERE up.total_points > 0
        ORDER BY up.total_points DESC;
        """
        
        users = db.execute(text(users_query)).fetchall()
        
        print(f"Procesando {len(users)} usuarios con puntos...")
        
        for user in users:
            user_id = user[0]
            username = user[1]
            total_points = user[2]
            completed_orders = user[3]
            current_achievements = user[4]
            
            print(f"\n--- Usuario: {username} (ID: {user_id}) ---")
            print(f"Puntos: {total_points}, Órdenes: {completed_orders}, Logros actuales: {current_achievements}")
            
            achievements_awarded = 0
            
            # Logro: Primera Reparación (1 orden)
            if completed_orders >= 1:
                achievement_id = db.execute(text("SELECT id FROM achievements WHERE name = '🔧 Primera Reparación'")).scalar()
                if achievement_id:
                    existing = db.execute(text("SELECT id FROM user_achievements WHERE user_id = :user_id AND achievement_id = :ach_id"), 
                                        {"user_id": user_id, "ach_id": achievement_id}).scalar()
                    if not existing:
                        db.execute(text("""
                            INSERT INTO user_achievements (user_id, achievement_id, earned_at, progress, notified)
                            VALUES (:user_id, :ach_id, NOW(), 100, false)
                        """), {"user_id": user_id, "ach_id": achievement_id})
                        achievements_awarded += 1
                        print(f"  ✅ Otorgado: 🔧 Primera Reparación")
            
            # Logro: Mecánico Experimentado (50 órdenes)
            if completed_orders >= 50:
                achievement_id = db.execute(text("SELECT id FROM achievements WHERE name = '🛠️ Mecánico Experimentado'")).scalar()
                if achievement_id:
                    existing = db.execute(text("SELECT id FROM user_achievements WHERE user_id = :user_id AND achievement_id = :ach_id"), 
                                        {"user_id": user_id, "ach_id": achievement_id}).scalar()
                    if not existing:
                        db.execute(text("""
                            INSERT INTO user_achievements (user_id, achievement_id, earned_at, progress, notified)
                            VALUES (:user_id, :ach_id, NOW(), 100, false)
                        """), {"user_id": user_id, "ach_id": achievement_id})
                        achievements_awarded += 1
                        print(f"  ✅ Otorgado: 🛠️ Mecánico Experimentado")
            
            # Logro: Centurión (100 órdenes)
            if completed_orders >= 100:
                achievement_id = db.execute(text("SELECT id FROM achievements WHERE name = '⭐ Centurión'")).scalar()
                if achievement_id:
                    existing = db.execute(text("SELECT id FROM user_achievements WHERE user_id = :user_id AND achievement_id = :ach_id"), 
                                        {"user_id": user_id, "ach_id": achievement_id}).scalar()
                    if not existing:
                        db.execute(text("""
                            INSERT INTO user_achievements (user_id, achievement_id, earned_at, progress, notified)
                            VALUES (:user_id, :ach_id, NOW(), 100, false)
                        """), {"user_id": user_id, "ach_id": achievement_id})
                        achievements_awarded += 1
                        print(f"  ✅ Otorgado: ⭐ Centurión")
            
            if achievements_awarded > 0:
                print(f"  🎉 Total logros otorgados: {achievements_awarded}")
            else:
                print(f"  ℹ️  No se otorgaron nuevos logros")
        
        db.commit()
        print(f"\n🎉 Proceso completado. Logros otorgados retroactivamente.")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

def main():
    print("🏆 OTORGANDO LOGROS RETROACTIVAMENTE")
    print("=" * 50)
    
    success = award_retroactive_achievements()
    
    if success:
        print("\n✅ Proceso completado exitosamente.")
        print("Los usuarios deberían ver sus logros en el frontend ahora.")
    else:
        print("\n❌ Error durante el proceso.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)