#!/usr/bin/env python3
"""
Script para inicializar el sistema de logros de gamificación
Ubicación: backend/init_achievements.py
Ejecutar desde backend/: python init_achievements.py
"""

from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models.gamification import Achievement, UserPoints, AchievementType, BadgeRarity
from src.models.user import User
import json

def create_achievements(db: Session):
    """Crea los logros predeterminados del sistema"""
    
    achievements = [
        # === LOGROS DE VELOCIDAD ===
        {
            'name': '⚡ Rayo McQueen',
            'description': 'Completa una orden en menos de 1 hora',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.COMMON,
            'icon': '⚡',
            'points': 25,
            'condition_json': json.dumps({
                'type': 'fast_completion',
                'max_hours': 1
            })
        },
        {
            'name': '🚀 Productivo',
            'description': 'Completa 5 órdenes en un día',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.RARE,
            'icon': '🚀',
            'points': 75,
            'condition_json': json.dumps({
                'type': 'orders_per_day',
                'target': 5
            })
        },
        {
            'name': '🌟 Súper Productivo',
            'description': 'Completa 10 órdenes en un día',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.EPIC,
            'icon': '🌟',
            'points': 150,
            'condition_json': json.dumps({
                'type': 'orders_per_day',
                'target': 10
            })
        },
        
        # === LOGROS DE CALIDAD ===
        {
            'name': '🎯 Precisión',
            'description': '10 órdenes consecutivas sin retrabajo',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.COMMON,
            'icon': '🎯',
            'points': 50,
            'condition_json': json.dumps({
                'type': 'no_rework_streak',
                'target': 10
            })
        },
        {
            'name': '💎 Perfeccionista',
            'description': '25 órdenes consecutivas sin retrabajo',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.RARE,
            'icon': '💎',
            'points': 125,
            'condition_json': json.dumps({
                'type': 'no_rework_streak',
                'target': 25
            })
        },
        {
            'name': '🏆 Maestro Artesano',
            'description': '50 órdenes consecutivas sin retrabajo',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🏆',
            'points': 300,
            'condition_json': json.dumps({
                'type': 'no_rework_streak',
                'target': 50
            })
        },
        
        # === LOGROS DE CONSISTENCIA ===
        {
            'name': '📅 Constante',
            'description': 'Trabaja 7 días consecutivos',
            'type': AchievementType.CONSISTENCY,
            'rarity': BadgeRarity.COMMON,
            'icon': '📅',
            'points': 35,
            'condition_json': json.dumps({
                'type': 'daily_streak',
                'target_days': 7
            })
        },
        {
            'name': '🔥 En Llamas',
            'description': 'Trabaja 30 días consecutivos',
            'type': AchievementType.CONSISTENCY,
            'rarity': BadgeRarity.EPIC,
            'icon': '🔥',
            'points': 200,
            'condition_json': json.dumps({
                'type': 'daily_streak',
                'target_days': 30
            })
        },
        
        # === LOGROS ESPECIALES ===
        {
            'name': '🌙 Búho Nocturno',
            'description': 'Completa 5 órdenes después de las 20:00',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.RARE,
            'icon': '🌙',
            'points': 80,
            'condition_json': json.dumps({
                'type': 'night_shift_orders',
                'target': 5,
                'after_hour': 20
            })
        },
        {
            'name': '🚨 Héroe de Emergencia',
            'description': 'Resuelve 3 emergencias en una semana',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.EPIC,
            'icon': '🚨',
            'points': 150,
            'condition_json': json.dumps({
                'type': 'emergency_orders',
                'target': 3,
                'timeframe_days': 7
            })
        },
        
        # === LOGROS BÁSICOS ===
        {
            'name': '🔧 Primera Reparación',
            'description': 'Completa tu primera orden de trabajo',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.COMMON,
            'icon': '🔧',
            'points': 10,
            'condition_json': json.dumps({
                'type': 'order_count',
                'target': 1
            })
        },
        {
            'name': '🛠️ Mecánico Experimentado',
            'description': 'Completa 50 órdenes de trabajo',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '🛠️',
            'points': 100,
            'condition_json': json.dumps({
                'type': 'order_count',
                'target': 50
            })
        },
        {
            'name': '⭐ Centurión',
            'description': 'Completa 100 órdenes de trabajo',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.EPIC,
            'icon': '⭐',
            'points': 200,
            'condition_json': json.dumps({
                'type': 'order_count',
                'target': 100
            })
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for ach_data in achievements:
        existing = db.query(Achievement).filter(
            Achievement.name == ach_data['name']
        ).first()
        
        if not existing:
            achievement = Achievement(**ach_data)
            db.add(achievement)
            created_count += 1
        else:
            # Actualizar si es necesario
            for key, value in ach_data.items():
                if key != 'name':  # No cambiar el nombre
                    setattr(existing, key, value)
            updated_count += 1
    
    db.commit()
    return created_count, updated_count

def create_user_points_profiles(db: Session):
    """Crea perfiles de puntos para usuarios que no los tengan"""
    
    users_without_points = db.query(User).outerjoin(UserPoints).filter(
        UserPoints.id.is_(None),
        User.active == True
    ).all()
    
    created_count = 0
    for user in users_without_points:
        user_points = UserPoints(user_id=user.id)
        db.add(user_points)
        created_count += 1
    
    if created_count > 0:
        db.commit()
    
    return created_count

def main():
    """Función principal"""
    print("🎮 INICIALIZANDO SISTEMA DE GAMIFICACIÓN")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # 1. Crear logros
        print("1. Creando logros predeterminados...")
        created_achievements, updated_achievements = create_achievements(db)
        print(f"   ✅ Logros creados: {created_achievements}")
        print(f"   🔄 Logros actualizados: {updated_achievements}")
        
        # 2. Crear perfiles de usuario
        print("\n2. Creando perfiles de puntos para usuarios...")
        created_profiles = create_user_points_profiles(db)
        print(f"   ✅ Perfiles creados: {created_profiles}")
        
        # 3. Verificar estado final
        print("\n3. Verificando estado final...")
        total_achievements = db.query(Achievement).count()
        total_user_points = db.query(UserPoints).count()
        active_users = db.query(User).filter(User.active == True).count()
        
        print(f"   📊 Total de logros en el sistema: {total_achievements}")
        print(f"   👥 Usuarios con perfil de puntos: {total_user_points}")
        print(f"   👤 Usuarios activos: {active_users}")
        
        # 4. Mostrar algunos logros de ejemplo
        print("\n4. Logros disponibles (muestra):")
        sample_achievements = db.query(Achievement).limit(5).all()
        for ach in sample_achievements:
            print(f"   🏆 {ach.name} ({ach.rarity.value}) - {ach.points} puntos")
        
        print("\n" + "=" * 50)
        print("🎉 INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
        print("\nEl sistema de gamificación está listo.")
        print("Los logros se otorgarán automáticamente al completar órdenes de trabajo.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR durante la inicialización: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)