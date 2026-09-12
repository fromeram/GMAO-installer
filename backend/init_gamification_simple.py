#!/usr/bin/env python3
"""
Script simple para inicializar logros de gamificación
Evita problemas de importaciones circulares
"""

import json
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configurar conexión directa a la base de datos
# Ajusta estos valores según tu configuración
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gmao_user:gmao_pass@db:5432/gmao_db")

def get_db_connection():
    """Crear conexión directa a la base de datos"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal(), engine

def create_achievements_direct():
    """Crear logros usando SQL directo para evitar problemas de importación"""
    
    achievements = [
        {
            'name': '⚡ Rayo McQueen',
            'description': 'Completa una orden en menos de 1 hora',
            'type': 'SPEED',
            'rarity': 'COMMON',
            'icon': '⚡',
            'points': 25,
            'condition_json': '{"type": "fast_completion", "max_hours": 1}',
            'active': True
        },
        {
            'name': '🚀 Productivo',
            'description': 'Completa 5 órdenes en un día',
            'type': 'SPEED',
            'rarity': 'RARE',
            'icon': '🚀',
            'points': 75,
            'condition_json': '{"type": "orders_per_day", "target": 5}',
            'active': True
        },
        {
            'name': '🌟 Súper Productivo',
            'description': 'Completa 10 órdenes en un día',
            'type': 'SPEED',
            'rarity': 'EPIC',
            'icon': '🌟',
            'points': 150,
            'condition_json': '{"type": "orders_per_day", "target": 10}',
            'active': True
        },
        {
            'name': '🎯 Precisión',
            'description': '10 órdenes consecutivas sin retrabajo',
            'type': 'QUALITY',
            'rarity': 'COMMON',
            'icon': '🎯',
            'points': 50,
            'condition_json': '{"type": "no_rework_streak", "target": 10}',
            'active': True
        },
        {
            'name': '💎 Perfeccionista',
            'description': '25 órdenes consecutivas sin retrabajo',
            'type': 'QUALITY',
            'rarity': 'RARE',
            'icon': '💎',
            'points': 125,
            'condition_json': '{"type": "no_rework_streak", "target": 25}',
            'active': True
        },
        {
            'name': '🏆 Maestro Artesano',
            'description': '50 órdenes consecutivas sin retrabajo',
            'type': 'QUALITY',
            'rarity': 'LEGENDARY',
            'icon': '🏆',
            'points': 300,
            'condition_json': '{"type": "no_rework_streak", "target": 50}',
            'active': True
        },
        {
            'name': '📅 Constante',
            'description': 'Trabaja 7 días consecutivos',
            'type': 'CONSISTENCY',
            'rarity': 'COMMON',
            'icon': '📅',
            'points': 35,
            'condition_json': '{"type": "daily_streak", "target_days": 7}',
            'active': True
        },
        {
            'name': '🔥 En Llamas',
            'description': 'Trabaja 30 días consecutivos',
            'type': 'CONSISTENCY',
            'rarity': 'EPIC',
            'icon': '🔥',
            'points': 200,
            'condition_json': '{"type": "daily_streak", "target_days": 30}',
            'active': True
        },
        {
            'name': '🌙 Búho Nocturno',
            'description': 'Completa 5 órdenes después de las 20:00',
            'type': 'TEAMWORK',
            'rarity': 'RARE',
            'icon': '🌙',
            'points': 80,
            'condition_json': '{"type": "night_shift_orders", "target": 5, "after_hour": 20}',
            'active': True
        },
        {
            'name': '🚨 Héroe de Emergencia',
            'description': 'Resuelve 3 emergencias en una semana',
            'type': 'TEAMWORK',
            'rarity': 'EPIC',
            'icon': '🚨',
            'points': 150,
            'condition_json': '{"type": "emergency_orders", "target": 3, "timeframe_days": 7}',
            'active': True
        },
        {
            'name': '🔧 Primera Reparación',
            'description': 'Completa tu primera orden de trabajo',
            'type': 'LEARNING',
            'rarity': 'COMMON',
            'icon': '🔧',
            'points': 10,
            'condition_json': '{"type": "order_count", "target": 1}',
            'active': True
        },
        {
            'name': '🛠️ Mecánico Experimentado',
            'description': 'Completa 50 órdenes de trabajo',
            'type': 'LEARNING',
            'rarity': 'RARE',
            'icon': '🛠️',
            'points': 100,
            'condition_json': '{"type": "order_count", "target": 50}',
            'active': True
        },
        {
            'name': '⭐ Centurión',
            'description': 'Completa 100 órdenes de trabajo',
            'type': 'LEARNING',
            'rarity': 'EPIC',
            'icon': '⭐',
            'points': 200,
            'condition_json': '{"type": "order_count", "target": 100}',
            'active': True
        }
    ]
    
    db, engine = get_db_connection()
    
    try:
        created_count = 0
        updated_count = 0
        
        for ach in achievements:
            # Verificar si existe
            result = db.execute(
                text("SELECT id FROM achievements WHERE name = :name"),
                {"name": ach['name']}
            ).fetchone()
            
            if not result:
                # Crear nuevo
                db.execute(
                    text("""
                    INSERT INTO achievements 
                    (name, description, type, rarity, icon, points, condition_json, active, created_at)
                    VALUES (:name, :description, :type, :rarity, :icon, :points, :condition_json, :active, NOW())
                    """),
                    ach
                )
                created_count += 1
            else:
                # Actualizar existente
                db.execute(
                    text("""
                    UPDATE achievements SET 
                        description = :description,
                        type = :type,
                        rarity = :rarity,
                        icon = :icon,
                        points = :points,
                        condition_json = :condition_json,
                        active = :active
                    WHERE name = :name
                    """),
                    ach
                )
                updated_count += 1
        
        db.commit()
        return created_count, updated_count
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def create_missing_user_points():
    """Crear perfiles de puntos para usuarios que no los tengan"""
    
    db, engine = get_db_connection()
    
    try:
        # Encontrar usuarios sin perfil de puntos
        result = db.execute(
            text("""
            SELECT u.id, u.username 
            FROM users u 
            LEFT JOIN user_points up ON u.id = up.user_id 
            WHERE up.id IS NULL AND u.active = true
            """)
        ).fetchall()
        
        created_count = 0
        for user in result:
            db.execute(
                text("""
                INSERT INTO user_points 
                (user_id, total_points, weekly_points, monthly_points, current_streak, best_streak, level, experience, last_activity, updated_at)
                VALUES (:user_id, 0, 0, 0, 0, 0, 1, 0, NOW(), NOW())
                """),
                {"user_id": user.id}
            )
            created_count += 1
            print(f"   ✅ Creado perfil para {user.username}")
        
        if created_count > 0:
            db.commit()
        
        return created_count
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def verify_system_status():
    """Verificar el estado del sistema de gamificación"""
    
    db, engine = get_db_connection()
    
    try:
        # Contar logros
        achievements_count = db.execute(text("SELECT COUNT(*) FROM achievements")).scalar()
        
        # Contar usuarios con puntos
        user_points_count = db.execute(text("SELECT COUNT(*) FROM user_points")).scalar()
        
        # Contar usuarios activos
        active_users_count = db.execute(text("SELECT COUNT(*) FROM users WHERE active = true")).scalar()
        
        # Contar logros ganados
        earned_achievements = db.execute(text("SELECT COUNT(*) FROM user_achievements")).scalar()
        
        # Top usuarios
        top_users = db.execute(
            text("""
            SELECT u.username, up.total_points, up.level,
                   (SELECT COUNT(*) FROM user_achievements ua WHERE ua.user_id = u.id) as achievements_count
            FROM user_points up 
            JOIN users u ON up.user_id = u.id 
            WHERE u.active = true
            ORDER BY up.total_points DESC 
            LIMIT 5
            """)
        ).fetchall()
        
        return {
            'achievements_count': achievements_count,
            'user_points_count': user_points_count,
            'active_users_count': active_users_count,
            'earned_achievements': earned_achievements,
            'top_users': top_users
        }
        
    finally:
        db.close()

def main():
    """Función principal"""
    print("🎮 INICIALIZANDO SISTEMA DE GAMIFICACIÓN")
    print("=" * 50)
    
    try:
        # 1. Verificar estado inicial
        print("0. Verificando estado inicial...")
        initial_status = verify_system_status()
        print(f"   📊 Logros definidos: {initial_status['achievements_count']}")
        print(f"   🏆 Logros ganados: {initial_status['earned_achievements']}")
        print(f"   👥 Usuarios con puntos: {initial_status['user_points_count']}")
        print(f"   👤 Usuarios activos: {initial_status['active_users_count']}")
        
        # 2. Crear logros
        print("\n1. Creando/actualizando logros predeterminados...")
        created_achievements, updated_achievements = create_achievements_direct()
        print(f"   ✅ Logros creados: {created_achievements}")
        print(f"   🔄 Logros actualizados: {updated_achievements}")
        
        # 3. Crear perfiles de usuario
        print("\n2. Creando perfiles de puntos para usuarios...")
        created_profiles = create_missing_user_points()
        print(f"   ✅ Perfiles creados: {created_profiles}")
        
        # 4. Verificar estado final
        print("\n3. Verificando estado final...")
        final_status = verify_system_status()
        print(f"   📊 Total de logros en el sistema: {final_status['achievements_count']}")
        print(f"   🏆 Logros ganados por usuarios: {final_status['earned_achievements']}")
        print(f"   👥 Usuarios con perfil de puntos: {final_status['user_points_count']}")
        print(f"   👤 Usuarios activos: {final_status['active_users_count']}")
        
        # 5. Mostrar top usuarios
        print("\n4. Top usuarios por puntos:")
        for i, user in enumerate(final_status['top_users'], 1):
            print(f"   {i}. {user.username}: {user.total_points} puntos, "
                  f"{user.achievements_count} logros, nivel {user.level}")
        
        print("\n" + "=" * 50)
        print("🎉 INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
        print("\nEl sistema de gamificación está listo.")
        print("Los logros deberían aparecer desbloqueados en el frontend.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR durante la inicialización: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)