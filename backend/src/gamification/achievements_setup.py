# backend/src/gamification/achievements_setup.py
from sqlalchemy.orm import Session
from ..models.gamification import Achievement, AchievementType, BadgeRarity, UserPoints
from ..models.user import User
import json

ALL_DEFAULT_ACHIEVEMENTS = [
    {
        "name": "⚡ Rayo McQueen",
        "description": "Completa una orden en menos de 1 hora",
        "type": "SPEED",
        "rarity": "COMMON",
        "icon": "⚡",
        "points": 25,
        "condition_json": "{\"type\": \"fast_completion\", \"max_hours\": 1}"
    },
    {
        "name": "🚀 Productivo",
        "description": "Completa 5 órdenes en un día",
        "type": "SPEED",
        "rarity": "RARE",
        "icon": "🚀",
        "points": 75,
        "condition_json": "{\"type\": \"orders_per_day\", \"target\": 5}"
    },
    {
        "name": "🌟 Súper Productivo",
        "description": "Completa 10 órdenes en un día",
        "type": "SPEED",
        "rarity": "EPIC",
        "icon": "🌟",
        "points": 150,
        "condition_json": "{\"type\": \"orders_per_day\", \"target\": 10}"
    },
    {
        "name": "🎯 Precisión",
        "description": "10 órdenes consecutivas sin retrabajo",
        "type": "QUALITY",
        "rarity": "COMMON",
        "icon": "🎯",
        "points": 50,
        "condition_json": "{\"type\": \"no_rework_streak\", \"target\": 10}"
    },
    {
        "name": "💎 Perfeccionista",
        "description": "25 órdenes consecutivas sin retrabajo",
        "type": "QUALITY",
        "rarity": "RARE",
        "icon": "💎",
        "points": 125,
        "condition_json": "{\"type\": \"no_rework_streak\", \"target\": 25}"
    },
    {
        "name": "🏆 Maestro Artesano",
        "description": "50 órdenes consecutivas sin retrabajo",
        "type": "QUALITY",
        "rarity": "LEGENDARY",
        "icon": "🏆",
        "points": 300,
        "condition_json": "{\"type\": \"no_rework_streak\", \"target\": 50}"
    },
    {
        "name": "📅 Constante",
        "description": "Trabaja 7 días consecutivos",
        "type": "CONSISTENCY",
        "rarity": "COMMON",
        "icon": "📅",
        "points": 35,
        "condition_json": "{\"type\": \"daily_streak\", \"target_days\": 7}"
    },
    {
        "name": "🔥 En Llamas",
        "description": "Trabaja 30 días consecutivos",
        "type": "CONSISTENCY",
        "rarity": "EPIC",
        "icon": "🔥",
        "points": 200,
        "condition_json": "{\"type\": \"daily_streak\", \"target_days\": 30}"
    },
    {
        "name": "🌙 Búho Nocturno",
        "description": "Completa 5 órdenes después de las 20:00",
        "type": "TEAMWORK",
        "rarity": "RARE",
        "icon": "🌙",
        "points": 80,
        "condition_json": "{\"type\": \"night_shift_orders\", \"target\": 5, \"after_hour\": 20}"
    },
    {
        "name": "🚨 Héroe de Emergencia",
        "description": "Resuelve 3 emergencias en una semana",
        "type": "TEAMWORK",
        "rarity": "EPIC",
        "icon": "🚨",
        "points": 150,
        "condition_json": "{\"type\": \"emergency_orders\", \"target\": 3, \"timeframe_days\": 7}"
    },
    {
        "name": "🔧 Mecánico Experto",
        "description": "Completa 100 órdenes correctivas",
        "type": "LEARNING",
        "rarity": "RARE",
        "icon": "🔧",
        "points": 150,
        "condition_json": "{\"type\": \"order_type_count\", \"work_type\": \"Correctivo\", \"target\": 100}"
    },
    {
        "name": "🛡️ Guardián Preventivo",
        "description": "Completa 50 mantenimientos preventivos",
        "type": "LEARNING",
        "rarity": "RARE",
        "icon": "🛡️",
        "points": 125,
        "condition_json": "{\"type\": \"order_type_count\", \"work_type\": \"Preventivo\", \"target\": 50}"
    },
    {
        "name": "🔧 Primera Reparación",
        "description": "Completa tu primera orden de trabajo",
        "type": "LEARNING",
        "rarity": "COMMON",
        "icon": "🔧",
        "points": 10,
        "condition_json": "{\"type\": \"order_count\", \"target\": 1}"
    },
    {
        "name": "🛠️ Mecánico Experimentado",
        "description": "Completa 50 órdenes de trabajo",
        "type": "LEARNING",
        "rarity": "RARE",
        "icon": "🛠️",
        "points": 100,
        "condition_json": "{\"type\": \"order_count\", \"target\": 50}"
    },
    {
        "name": "⭐ Centurión",
        "description": "Completa 100 órdenes de trabajo",
        "type": "LEARNING",
        "rarity": "EPIC",
        "icon": "⭐",
        "points": 200,
        "condition_json": "{\"type\": \"order_count\", \"target\": 100}"
    },
    {
        "name": "🎓 Primer Paso",
        "description": "Completa tu primera orden de trabajo",
        "type": "LEARNING",
        "rarity": "COMMON",
        "icon": "🎓",
        "points": 10,
        "condition_json": "{\"type\": \"order_count\", \"target\": 1}"
    },
    {
        "name": "⚙️ En Marcha",
        "description": "Completa 10 órdenes de trabajo",
        "type": "LEARNING",
        "rarity": "COMMON",
        "icon": "⚙️",
        "points": 25,
        "condition_json": "{\"type\": \"order_count\", \"target\": 10}"
    },
    {
        "name": "🔧 Técnico Competente",
        "description": "Completa 50 órdenes de trabajo",
        "type": "LEARNING",
        "rarity": "RARE",
        "icon": "🔧",
        "points": 75,
        "condition_json": "{\"type\": \"order_count\", \"target\": 50}"
    },
    {
        "name": "👨‍🔧 Experto",
        "description": "Completa 100 órdenes de trabajo",
        "type": "LEARNING",
        "rarity": "EPIC",
        "icon": "👨‍🔧",
        "points": 150,
        "condition_json": "{\"type\": \"order_count\", \"target\": 100}"
    },
    {
        "name": "🌟 Leyenda de la Planta",
        "description": "Completa 1000 órdenes de trabajo",
        "type": "LEARNING",
        "rarity": "LEGENDARY",
        "icon": "🌟",
        "points": 1000,
        "condition_json": "{\"type\": \"order_count\", \"target\": 1000}"
    },
    {
        "name": "🚀 Productivo",
        "description": "Completa 3 órdenes en un día",
        "type": "SPEED",
        "rarity": "COMMON",
        "icon": "🚀",
        "points": 30,
        "condition_json": "{\"type\": \"orders_per_day\", \"target\": 3}"
    },
    {
        "name": "🌟 Muy Productivo",
        "description": "Completa 5 órdenes en un día",
        "type": "SPEED",
        "rarity": "RARE",
        "icon": "🌟",
        "points": 60,
        "condition_json": "{\"type\": \"orders_per_day\", \"target\": 5}"
    },
    {
        "name": "💫 Súper Productivo",
        "description": "Completa 8 órdenes en un día",
        "type": "SPEED",
        "rarity": "EPIC",
        "icon": "💫",
        "points": 120,
        "condition_json": "{\"type\": \"orders_per_day\", \"target\": 8}"
    },
    {
        "name": "🎯 Precisión",
        "description": "10 órdenes sin rechazos ni retrabajos",
        "type": "QUALITY",
        "rarity": "COMMON",
        "icon": "🎯",
        "points": 50,
        "condition_json": "{\"type\": \"no_rework_streak\", \"target\": 10}"
    },
    {
        "name": "💎 Perfeccionista",
        "description": "25 órdenes sin rechazos ni retrabajos",
        "type": "QUALITY",
        "rarity": "RARE",
        "icon": "💎",
        "points": 125,
        "condition_json": "{\"type\": \"no_rework_streak\", \"target\": 25}"
    },
    {
        "name": "🏆 Maestro Artesano",
        "description": "50 órdenes consecutivas sin errores",
        "type": "QUALITY",
        "rarity": "LEGENDARY",
        "icon": "🏆",
        "points": 300,
        "condition_json": "{\"type\": \"no_rework_streak\", \"target\": 50}"
    },
    {
        "name": "📅 Constante",
        "description": "Trabaja 7 días seguidos",
        "type": "CONSISTENCY",
        "rarity": "COMMON",
        "icon": "📅",
        "points": 35,
        "condition_json": "{\"type\": \"daily_streak\", \"target_days\": 7}"
    },
    {
        "name": "💪 Resistente",
        "description": "Trabaja 14 días seguidos",
        "type": "CONSISTENCY",
        "rarity": "RARE",
        "icon": "💪",
        "points": 80,
        "condition_json": "{\"type\": \"daily_streak\", \"target_days\": 14}"
    },
    {
        "name": "🔥 Incansable",
        "description": "Trabaja 21 días seguidos (turno completo)",
        "type": "CONSISTENCY",
        "rarity": "EPIC",
        "icon": "🔥",
        "points": 200,
        "condition_json": "{\"type\": \"daily_streak\", \"target_days\": 21}"
    },
    {
        "name": "🤝 Colaborador",
        "description": "Ayuda en 10 órdenes de otros técnicos",
        "type": "TEAMWORK",
        "rarity": "COMMON",
        "icon": "🤝",
        "points": 60,
        "condition_json": "{\"type\": \"assistance_count\", \"target\": 10}"
    },
    {
        "name": "🌙 Búho Nocturno",
        "description": "Completa 20 órdenes en turno de noche",
        "type": "TEAMWORK",
        "rarity": "RARE",
        "icon": "🌙",
        "points": 80,
        "condition_json": "{\"type\": \"night_shift_orders\", \"target\": 20}"
    }
]

def setup_default_achievements(db: Session):
    """Configura los 31 logros predeterminados del sistema y asegura perfiles de usuario"""
    created_count = 0
    for ach_data in ALL_DEFAULT_ACHIEVEMENTS:
        existing = db.query(Achievement).filter(
            Achievement.name == ach_data['name']
        ).first()
        
        if not existing:
            ach_type = getattr(AchievementType, ach_data['type'], ach_data['type'])
            rarity = getattr(BadgeRarity, ach_data['rarity'], ach_data['rarity'])
            
            achievement = Achievement(
                name=ach_data['name'],
                description=ach_data['description'],
                type=ach_type,
                rarity=rarity,
                icon=ach_data['icon'],
                points=ach_data['points'],
                condition_json=ach_data['condition_json'],
                active=True
            )
            db.add(achievement)
            created_count += 1
    
    if created_count > 0:
        db.commit()
        print(f"✅ Configurados {created_count} logros predeterminados en la base de datos.")

    # Asegurar perfiles de usuario en user_points
    users_without_profile = db.query(User).outerjoin(UserPoints).filter(
        UserPoints.id.is_(None),
        User.active == True
    ).all()
    
    profiles_created = 0
    for u in users_without_profile:
        up = UserPoints(
            user_id=u.id,
            total_points=0,
            weekly_points=0,
            monthly_points=0,
            current_streak=0,
            best_streak=0,
            level=1,
            experience=0
        )
        db.add(up)
        profiles_created += 1
        
    if profiles_created > 0:
        db.commit()
        print(f"✅ Perfiles de gamificación creados para {profiles_created} usuario(s).")
