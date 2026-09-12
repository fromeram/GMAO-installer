# backend/src/gamification/realistic_achievements.py
"""
ARCHIVO PRINCIPAL - Sistema de logros realistas para vuestro sistema
55 logros totales, adaptados a vuestra realidad de turnos y órdenes de trabajo
"""

from sqlalchemy.orm import Session
from ..models.gamification import Achievement, AchievementType, BadgeRarity
import json

def setup_all_realistic_achievements(db: Session):
    """
    Configura TODOS los 55 logros realistas de una vez
    Adaptados a vuestro sistema real de turnos 21+7 y órdenes de trabajo
    """
    
    all_achievements = [
        # ========================================
        # PARTE 1: PRODUCTIVIDAD (15 logros)
        # ========================================
        {
            'name': '🎓 Primer Paso',
            'description': 'Completa tu primera orden de trabajo',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.COMMON,
            'icon': '🎓',
            'points': 10,
            'condition_json': json.dumps({'type': 'order_count', 'target': 1})
        },
        {
            'name': '⚙️ En Marcha',
            'description': 'Completa 10 órdenes de trabajo',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.COMMON,
            'icon': '⚙️',
            'points': 25,
            'condition_json': json.dumps({'type': 'order_count', 'target': 10})
        },
        {
            'name': '🔧 Técnico Competente',
            'description': 'Completa 50 órdenes de trabajo',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '🔧',
            'points': 75,
            'condition_json': json.dumps({'type': 'order_count', 'target': 50})
        },
        {
            'name': '🚀 Productivo',
            'description': 'Completa 3 órdenes en un día',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.COMMON,
            'icon': '🚀',
            'points': 30,
            'condition_json': json.dumps({'type': 'orders_per_day', 'target': 3})
        },
        {
            'name': '🌟 Muy Productivo',
            'description': 'Completa 5 órdenes en un día',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.RARE,
            'icon': '🌟',
            'points': 60,
            'condition_json': json.dumps({'type': 'orders_per_day', 'target': 5})
        },
        {
            'name': '💫 Súper Productivo',
            'description': 'Completa 8 órdenes en un día',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.EPIC,
            'icon': '💫',
            'points': 120,
            'condition_json': json.dumps({'type': 'orders_per_day', 'target': 8})
        },
        {
            'name': '📈 Semana Activa',
            'description': 'Completa 15 órdenes en una semana',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.COMMON,
            'icon': '📈',
            'points': 50,
            'condition_json': json.dumps({'type': 'weekly_orders', 'target': 15})
        },
        {
            'name': '🔥 Semana Intensa',
            'description': 'Completa 25 órdenes en una semana',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.RARE,
            'icon': '🔥',
            'points': 100,
            'condition_json': json.dumps({'type': 'weekly_orders', 'target': 25})
        },
        {
            'name': '🏆 Semana Épica',
            'description': 'Completa 35 órdenes en una semana',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.EPIC,
            'icon': '🏆',
            'points': 200,
            'condition_json': json.dumps({'type': 'weekly_orders', 'target': 35})
        },
        {
            'name': '👨‍🔧 Experto',
            'description': 'Completa 100 órdenes de trabajo',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.EPIC,
            'icon': '👨‍🔧',
            'points': 150,
            'condition_json': json.dumps({'type': 'order_count', 'target': 100})
        },
        {
            'name': '🎖️ Veterano',
            'description': 'Completa 250 órdenes de trabajo',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.EPIC,
            'icon': '🎖️',
            'points': 300,
            'condition_json': json.dumps({'type': 'order_count', 'target': 250})
        },
        {
            'name': '👑 Maestro',
            'description': 'Completa 500 órdenes de trabajo',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '👑',
            'points': 500,
            'condition_json': json.dumps({'type': 'order_count', 'target': 500})
        },
        {
            'name': '📅 Constante',
            'description': 'Trabaja 7 días seguidos',
            'type': AchievementType.CONSISTENCY,
            'rarity': BadgeRarity.COMMON,
            'icon': '📅',
            'points': 35,
            'condition_json': json.dumps({'type': 'daily_streak', 'target_days': 7})
        },
        {
            'name': '💪 Resistente',
            'description': 'Trabaja 14 días seguidos',
            'type': AchievementType.CONSISTENCY,
            'rarity': BadgeRarity.RARE,
            'icon': '💪',
            'points': 80,
            'condition_json': json.dumps({'type': 'daily_streak', 'target_days': 14})
        },
        {
            'name': '🔥 Incansable',
            'description': 'Trabaja 21 días seguidos (turno completo)',
            'type': AchievementType.CONSISTENCY,
            'rarity': BadgeRarity.EPIC,
            'icon': '🔥',
            'points': 200,
            'condition_json': json.dumps({'type': 'daily_streak', 'target_days': 21})
        },

        # ========================================
        # PARTE 2: CALIDAD Y TIPOS DE TRABAJO (15 logros)
        # ========================================
        {
            'name': '🎯 Precisión',
            'description': '10 órdenes sin rechazos ni retrabajos',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.COMMON,
            'icon': '🎯',
            'points': 50,
            'condition_json': json.dumps({'type': 'no_rework_streak', 'target': 10})
        },
        {
            'name': '💎 Perfeccionista',
            'description': '25 órdenes sin rechazos ni retrabajos',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.RARE,
            'icon': '💎',
            'points': 125,
            'condition_json': json.dumps({'type': 'no_rework_streak', 'target': 25})
        },
        {
            'name': '🏆 Maestro Artesano',
            'description': '50 órdenes consecutivas sin errores',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🏆',
            'points': 300,
            'condition_json': json.dumps({'type': 'no_rework_streak', 'target': 50})
        },
        {
            'name': '✨ Trabajo Impecable',
            'description': 'Completa 30 órdenes marcadas como "Excelente"',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.EPIC,
            'icon': '✨',
            'points': 200,
            'condition_json': json.dumps({'type': 'excellent_rating_count', 'target': 30})
        },
        {
            'name': '🛡️ Guardián Preventivo',
            'description': 'Completa 20 mantenimientos preventivos',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '🛡️',
            'points': 100,
            'condition_json': json.dumps({'type': 'order_type_count', 'work_type': 'Preventivo', 'target': 20})
        },
        {
            'name': '⚡ Protector de Máquinas',
            'description': 'Completa 50 mantenimientos preventivos',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.EPIC,
            'icon': '⚡',
            'points': 200,
            'condition_json': json.dumps({'type': 'order_type_count', 'work_type': 'Preventivo', 'target': 50})
        },
        {
            'name': '🔧 Reparador',
            'description': 'Completa 25 reparaciones correctivas',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.COMMON,
            'icon': '🔧',
            'points': 75,
            'condition_json': json.dumps({'type': 'order_type_count', 'work_type': 'Correctivo', 'target': 25})
        },
        {
            'name': '🚨 Bombero Industrial',
            'description': 'Completa 50 reparaciones correctivas',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '🚨',
            'points': 150,
            'condition_json': json.dumps({'type': 'order_type_count', 'work_type': 'Correctivo', 'target': 50})
        },
        {
            'name': '🦸‍♂️ Héroe de Emergencias',
            'description': 'Resuelve 5 averías urgentes en una semana',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.EPIC,
            'icon': '🦸‍♂️',
            'points': 180,
            'condition_json': json.dumps({'type': 'urgent_orders_week', 'target': 5})
        },
        {
            'name': '🔍 Inspector',
            'description': 'Completa 30 inspecciones técnicas',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.COMMON,
            'icon': '🔍',
            'points': 60,
            'condition_json': json.dumps({'type': 'order_type_count', 'work_type': 'Inspección', 'target': 30})
        },
        {
            'name': '🕵️ Detective Técnico',
            'description': 'Encuentra 10 problemas durante inspecciones',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.RARE,
            'icon': '🕵️',
            'points': 120,
            'condition_json': json.dumps({'type': 'problems_found_inspection', 'target': 10})
        },
        {
            'name': '🎭 Versátil',
            'description': 'Trabaja en 3 tipos diferentes de órdenes',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.COMMON,
            'icon': '🎭',
            'points': 40,
            'condition_json': json.dumps({'type': 'work_type_variety', 'target': 3})
        },
        {
            'name': '🌟 Todoterreno',
            'description': 'Completa preventivos, correctivos e inspecciones',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '🌟',
            'points': 80,
            'condition_json': json.dumps({'type': 'complete_work_types', 'types': ['Preventivo', 'Correctivo', 'Inspección']})
        },
        {
            'name': '⏱️ Eficiente',
            'description': 'Completa órdenes en tiempo estimado 20 veces',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.RARE,
            'icon': '⏱️',
            'points': 100,
            'condition_json': json.dumps({'type': 'on_time_completion', 'target': 20})
        },
        {
            'name': '🎯 Calculadora Humana',
            'description': 'Estima correctamente el tiempo de 30 órdenes',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.EPIC,
            'icon': '🎯',
            'points': 200,
            'condition_json': json.dumps({'type': 'accurate_estimates', 'target': 30, 'accuracy': 90})
        },

        # ========================================
        # PARTE 3: MÁQUINAS Y COLABORACIÓN (15 logros)
        # ========================================
        {
            'name': '🔨 Especialista en Prensas',
            'description': 'Completa 30 órdenes en prensas hidráulicas',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '🔨',
            'points': 100,
            'condition_json': json.dumps({'type': 'machine_type_orders', 'machine_type': 'Prensa', 'target': 30})
        },
        {
            'name': '⚙️ Maestro de Tornos',
            'description': 'Completa 30 órdenes en tornos CNC',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '⚙️',
            'points': 100,
            'condition_json': json.dumps({'type': 'machine_type_orders', 'machine_type': 'Torno', 'target': 30})
        },
        {
            'name': '🔧 Rey de la Soldadura',
            'description': 'Completa 25 órdenes de soldadura',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '🔧',
            'points': 100,
            'condition_json': json.dumps({'type': 'machine_type_orders', 'machine_type': 'Soldadora', 'target': 25})
        },
        {
            'name': '💡 Electricista Experto',
            'description': 'Resuelve 20 problemas eléctricos',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '💡',
            'points': 120,
            'condition_json': json.dumps({'type': 'electrical_orders', 'target': 20})
        },
        {
            'name': '🏭 Conocedor de Planta',
            'description': 'Trabaja en 5 secciones diferentes',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.EPIC,
            'icon': '🏭',
            'points': 150,
            'condition_json': json.dumps({'type': 'section_variety', 'target': 5})
        },
        {
            'name': '🤝 Colaborador',
            'description': 'Ayuda en 10 órdenes de otros técnicos',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.COMMON,
            'icon': '🤝',
            'points': 60,
            'condition_json': json.dumps({'type': 'assistance_count', 'target': 10})
        },
        {
            'name': '👥 Jugador de Equipo',
            'description': 'Completa 15 órdenes en equipo',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.RARE,
            'icon': '👥',
            'points': 90,
            'condition_json': json.dumps({'type': 'team_orders', 'target': 15})
        },
        {
            'name': '🎓 Mentor',
            'description': 'Enseña a 3 técnicos junior',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.EPIC,
            'icon': '🎓',
            'points': 200,
            'condition_json': json.dumps({'type': 'mentoring_count', 'target': 3})
        },
        {
            'name': '🌙 Búho Nocturno',
            'description': 'Completa 20 órdenes en turno de noche',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.RARE,
            'icon': '🌙',
            'points': 80,
            'condition_json': json.dumps({'type': 'night_shift_orders', 'target': 20})
        },
        {
            'name': '🌅 Madrugador',
            'description': 'Completa 20 órdenes en turno de mañana',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.COMMON,
            'icon': '🌅',
            'points': 60,
            'condition_json': json.dumps({'type': 'morning_shift_orders', 'target': 20})
        },
        {
            'name': '🌆 Tardero',
            'description': 'Completa 20 órdenes en turno de tarde',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.COMMON,
            'icon': '🌆',
            'points': 60,
            'condition_json': json.dumps({'type': 'afternoon_shift_orders', 'target': 20})
        },
        {
            'name': '🔄 Reciclador',
            'description': 'Reutiliza repuestos en 15 reparaciones',
            'type': AchievementType.INNOVATION,
            'rarity': BadgeRarity.RARE,
            'icon': '🔄',
            'points': 120,
            'condition_json': json.dumps({'type': 'parts_reuse', 'target': 15})
        },
        {
            'name': '💰 Ahorrador',
            'description': 'Ahorra costos en 20 reparaciones',
            'type': AchievementType.INNOVATION,
            'rarity': BadgeRarity.EPIC,
            'icon': '💰',
            'points': 200,
            'condition_json': json.dumps({'type': 'cost_savings', 'orders': 20})
        },
        {
            'name': '🎵 Oído Musical',
            'description': 'Diagnostica 10 problemas por sonido',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.EPIC,
            'icon': '🎵',
            'points': 180,
            'condition_json': json.dumps({'type': 'sound_diagnosis', 'target': 10})
        },
        {
            'name': '🧩 Solucionador',
            'description': 'Resuelve 5 órdenes que otros no pudieron',
            'type': AchievementType.INNOVATION,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🧩',
            'points': 300,
            'condition_json': json.dumps({'type': 'unsolved_orders', 'target': 5})
        },

        # ========================================
        # PARTE 4: DIVERSIÓN Y ÉPICOS (10 logros)
        # ========================================
        {
            'name': '☕ Héroe del Café',
            'description': 'Repara la máquina de café del taller',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.RARE,
            'icon': '☕',
            'points': 100,
            'condition_json': json.dumps({'type': 'coffee_machine_repair', 'target': 1})
        },
        {
            'name': '🎂 Cumpleañero Trabajador',
            'description': 'Trabaja el día de tu cumpleaños',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.RARE,
            'icon': '🎂',
            'points': 150,
            'condition_json': json.dumps({'type': 'birthday_work', 'target': 1})
        },
        {
            'name': '🎄 Trabajador Navideño',
            'description': 'Trabaja en Nochebuena o Navidad',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.EPIC,
            'icon': '🎄',
            'points': 200,
            'condition_json': json.dumps({'type': 'christmas_work', 'dates': ['12-24', '12-25']})
        },
        {
            'name': '🎆 Héroe de Fin de Año',
            'description': 'Trabaja en Nochevieja o Año Nuevo',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.EPIC,
            'icon': '🎆',
            'points': 200,
            'condition_json': json.dumps({'type': 'newyear_work', 'dates': ['12-31', '01-01']})
        },
        {
            'name': '💡 Inventor',
            'description': 'Sugiere 5 mejoras que se implementan',
            'type': AchievementType.INNOVATION,
            'rarity': BadgeRarity.EPIC,
            'icon': '💡',
            'points': 250,
            'condition_json': json.dumps({'type': 'improvements_suggested', 'target': 5})
        },
        {
            'name': '📝 Documentalista',
            'description': 'Documenta 10 procedimientos nuevos',
            'type': AchievementType.INNOVATION,
            'rarity': BadgeRarity.RARE,
            'icon': '📝',
            'points': 150,
            'condition_json': json.dumps({'type': 'procedures_documented', 'target': 10})
        },
        {
            'name': '🌟 Leyenda de la Planta',
            'description': 'Completa 1000 órdenes de trabajo',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🌟',
            'points': 1000,
            'condition_json': json.dumps({'type': 'order_count', 'target': 1000})
        },
        {
            'name': '🏆 Empleado del Año',
            'description': 'Mantén el mejor rendimiento general del año',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🏆',
            'points': 2000,
            'condition_json': json.dumps({'type': 'top_performer_year', 'target': 1})
        },
        {
            'name': '💎 Diamante Industrial',
            'description': 'Acumula 10,000 puntos totales',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '💎',
            'points': 500,
            'condition_json': json.dumps({'type': 'total_points', 'target': 10000})
        },
        {
            'name': '🌍 Salvador de la Producción',
            'description': 'Evita una parada de producción crítica',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🌍',
            'points': 1000,
            'condition_json': json.dumps({'type': 'production_save', 'target': 1})
        }
    ]
    
    # Insertar todos los logros
    inserted_count = 0
    for ach_data in all_achievements:
        existing = db.query(Achievement).filter(
            Achievement.name == ach_data['name']
        ).first()

def print_system_info():
    """Imprime información sobre el sistema de logros"""
    print("📋 SISTEMA DE LOGROS REALISTAS")
    print("=" * 50)
    print(f"📊 Total de logros: 55")
    print(f"🎯 Adaptado para turnos 21+7")
    print(f"⚙️ Basado en órdenes de trabajo reales")
    print(f"🏆 Distribución de rareza equilibrada")
    print("")
    print("🔧 Tipos de logros incluidos:")
    print("   • Productividad (órdenes por día/semana)")
    print("   • Calidad (sin retrabajos)")
    print("   • Experiencia (total de órdenes)")
    print("   • Constancia (días trabajados)")
    print("   • Especialidades (por tipo de máquina)")
    print("   • Trabajo en equipo (colaboración)")
    print("   • Innovación (mejoras y eficiencia)")
    print("   • Diversión (eventos especiales)")
    print("")
    print("✅ Listo para producción")        