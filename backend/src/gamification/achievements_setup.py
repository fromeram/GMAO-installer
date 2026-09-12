# backend/src/gamification/achievements_setup.py
from sqlalchemy.orm import Session
from ..models.gamification import Achievement, AchievementType, BadgeRarity
import json

def setup_default_achievements(db: Session):
    """Configura los logros predeterminados del sistema"""
    
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
        
        # === LOGROS DE HABILIDADES ===
        {
            'name': '🔧 Mecánico Experto',
            'description': 'Completa 100 órdenes correctivas',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '🔧',
            'points': 150,
            'condition_json': json.dumps({
                'type': 'order_type_count',
                'work_type': 'Correctivo',
                'target': 100
            })
        },
        {
            'name': '🛡️ Guardián Preventivo',
            'description': 'Completa 50 mantenimientos preventivos',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '🛡️',
            'points': 125,
            'condition_json': json.dumps({
                'type': 'order_type_count',
                'work_type': 'Preventivo',
                'target': 50
            })
        }
    ]
    
    # Insertar logros en la base de datos
    for ach_data in achievements:
        existing = db.query(Achievement).filter(
            Achievement.name == ach_data['name']
        ).first()
        
        if not existing:
            achievement = Achievement(**ach_data)
            db.add(achievement)
    
    db.commit()
    print(f"✅ Configurados {len(achievements)} logros predeterminados")