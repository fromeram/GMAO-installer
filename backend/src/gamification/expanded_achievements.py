# backend/src/gamification/expanded_achievements.py
"""
Sistema de logros expandido con 100+ logros categorizados
Para reemplazar o complementar achievements_setup.py
"""

from sqlalchemy.orm import Session
from ..models.gamification import Achievement, AchievementType, BadgeRarity
import json

def setup_expanded_achievements(db: Session):
    """Configura un sistema masivo de logros (100+ logros)"""
    
    achievements = [
        # ========================================
        # 🚀 LOGROS DE VELOCIDAD Y PRODUCTIVIDAD
        # ========================================
        {
            'name': '⚡ Rayo McQueen',
            'description': 'Completa una orden en menos de 1 hora',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.COMMON,
            'icon': '⚡',
            'points': 25,
            'condition_json': json.dumps({'type': 'fast_completion', 'max_hours': 1})
        },
        {
            'name': '💨 Velocista',
            'description': 'Completa una orden en menos de 30 minutos',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.RARE,
            'icon': '💨',
            'points': 50,
            'condition_json': json.dumps({'type': 'fast_completion', 'max_hours': 0.5})
        },
        {
            'name': '🏃 Flash',
            'description': 'Completa una orden en menos de 15 minutos',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.EPIC,
            'icon': '🏃',
            'points': 100,
            'condition_json': json.dumps({'type': 'fast_completion', 'max_hours': 0.25})
        },
        {
            'name': '🚀 Productivo',
            'description': 'Completa 5 órdenes en un día',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.RARE,
            'icon': '🚀',
            'points': 75,
            'condition_json': json.dumps({'type': 'orders_per_day', 'target': 5})
        },
        {
            'name': '🌟 Súper Productivo',
            'description': 'Completa 10 órdenes en un día',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.EPIC,
            'icon': '🌟',
            'points': 150,
            'condition_json': json.dumps({'type': 'orders_per_day', 'target': 10})
        },
        {
            'name': '💫 Hiper Productivo',
            'description': 'Completa 15 órdenes en un día',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '💫',
            'points': 300,
            'condition_json': json.dumps({'type': 'orders_per_day', 'target': 15})
        },
        {
            'name': '🔥 Máquina Imparable',
            'description': 'Completa 20 órdenes en un día',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🔥',
            'points': 500,
            'condition_json': json.dumps({'type': 'orders_per_day', 'target': 20})
        },
        {
            'name': '⏰ Madrugador',
            'description': 'Completa 5 órdenes antes de las 8:00 AM',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.RARE,
            'icon': '⏰',
            'points': 80,
            'condition_json': json.dumps({'type': 'early_bird_orders', 'target': 5, 'before_hour': 8})
        },
        {
            'name': '📈 Acelerador',
            'description': 'Completa órdenes 50% más rápido que el promedio por 5 días',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.EPIC,
            'icon': '📈',
            'points': 200,
            'condition_json': json.dumps({'type': 'speed_improvement', 'improvement_percent': 50, 'days': 5})
        },

        # ========================================
        # 🎯 LOGROS DE CALIDAD Y PRECISIÓN
        # ========================================
        {
            'name': '🎯 Precisión',
            'description': '10 órdenes consecutivas sin retrabajo',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.COMMON,
            'icon': '🎯',
            'points': 50,
            'condition_json': json.dumps({'type': 'no_rework_streak', 'target': 10})
        },
        {
            'name': '💎 Perfeccionista',
            'description': '25 órdenes consecutivas sin retrabajo',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.RARE,
            'icon': '💎',
            'points': 125,
            'condition_json': json.dumps({'type': 'no_rework_streak', 'target': 25})
        },
        {
            'name': '🏆 Maestro Artesano',
            'description': '50 órdenes consecutivas sin retrabajo',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🏆',
            'points': 300,
            'condition_json': json.dumps({'type': 'no_rework_streak', 'target': 50})
        },
        {
            'name': '👑 Leyenda Viviente',
            'description': '100 órdenes consecutivas sin retrabajo',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '👑',
            'points': 1000,
            'condition_json': json.dumps({'type': 'no_rework_streak', 'target': 100})
        },
        {
            'name': '✨ Trabajo Impecable',
            'description': 'Completa 50 órdenes con calificación perfecta',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.EPIC,
            'icon': '✨',
            'points': 250,
            'condition_json': json.dumps({'type': 'perfect_rating_count', 'target': 50})
        },
        {
            'name': '🔍 Inspector',
            'description': 'Detecta 10 problemas potenciales antes de que se conviertan en fallas',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.RARE,
            'icon': '🔍',
            'points': 100,
            'condition_json': json.dumps({'type': 'preventive_detection', 'target': 10})
        },
        {
            'name': '🛡️ Guardián de la Calidad',
            'description': 'Mantén 95% de calidad durante 30 días',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.EPIC,
            'icon': '🛡️',
            'points': 200,
            'condition_json': json.dumps({'type': 'quality_percentage', 'target': 95, 'days': 30})
        },

        # ========================================
        # 📅 LOGROS DE CONSISTENCIA Y DISCIPLINA
        # ========================================
        {
            'name': '📅 Constante',
            'description': 'Trabaja 7 días consecutivos',
            'type': AchievementType.CONSISTENCY,
            'rarity': BadgeRarity.COMMON,
            'icon': '📅',
            'points': 35,
            'condition_json': json.dumps({'type': 'daily_streak', 'target_days': 7})
        },
        {
            'name': '🔥 En Llamas',
            'description': 'Trabaja 30 días consecutivos',
            'type': AchievementType.CONSISTENCY,
            'rarity': BadgeRarity.EPIC,
            'icon': '🔥',
            'points': 200,
            'condition_json': json.dumps({'type': 'daily_streak', 'target_days': 30})
        },
        {
            'name': '🌪️ Vendaval',
            'description': 'Trabaja 60 días consecutivos',
            'type': AchievementType.CONSISTENCY,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🌪️',
            'points': 500,
            'condition_json': json.dumps({'type': 'daily_streak', 'target_days': 60})
        },
        {
            'name': '⚡ Indestructible',
            'description': 'Trabaja 100 días consecutivos',
            'type': AchievementType.CONSISTENCY,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '⚡',
            'points': 1000,
            'condition_json': json.dumps({'type': 'daily_streak', 'target_days': 100})
        },
        {
            'name': '🎯 Disciplinado',
            'description': 'Completa al menos 1 orden cada día por 14 días',
            'type': AchievementType.CONSISTENCY,
            'rarity': BadgeRarity.RARE,
            'icon': '🎯',
            'points': 100,
            'condition_json': json.dumps({'type': 'min_orders_streak', 'min_orders': 1, 'days': 14})
        },
        {
            'name': '📊 Estable',
            'description': 'Mantén una productividad constante (±10%) por 30 días',
            'type': AchievementType.CONSISTENCY,
            'rarity': BadgeRarity.EPIC,
            'icon': '📊',
            'points': 180,
            'condition_json': json.dumps({'type': 'stable_productivity', 'variance': 10, 'days': 30})
        },

        # ========================================
        # 🏅 LOGROS DE APRENDIZAJE Y EXPERIENCIA
        # ========================================
        {
            'name': '🎓 Novato',
            'description': 'Completa tu primera orden de trabajo',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.COMMON,
            'icon': '🎓',
            'points': 10,
            'condition_json': json.dumps({'type': 'order_count', 'target': 1})
        },
        {
            'name': '⚙️ Aprendiz',
            'description': 'Completa 10 órdenes de trabajo',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.COMMON,
            'icon': '⚙️',
            'points': 25,
            'condition_json': json.dumps({'type': 'order_count', 'target': 10})
        },
        {
            'name': '🔧 Técnico',
            'description': 'Completa 50 órdenes de trabajo',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '🔧',
            'points': 75,
            'condition_json': json.dumps({'type': 'order_count', 'target': 50})
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
            'name': '🌟 Leyenda',
            'description': 'Completa 1000 órdenes de trabajo',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🌟',
            'points': 1000,
            'condition_json': json.dumps({'type': 'order_count', 'target': 1000})
        },
        {
            'name': '🔧 Mecánico Experto',
            'description': 'Completa 100 órdenes correctivas',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '🔧',
            'points': 150,
            'condition_json': json.dumps({'type': 'order_type_count', 'work_type': 'Correctivo', 'target': 100})
        },
        {
            'name': '🛡️ Guardián Preventivo',
            'description': 'Completa 50 mantenimientos preventivos',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '🛡️',
            'points': 125,
            'condition_json': json.dumps({'type': 'order_type_count', 'work_type': 'Preventivo', 'target': 50})
        },
        {
            'name': '🔍 Detective de Fallas',
            'description': 'Resuelve 25 problemas complejos',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.EPIC,
            'icon': '🔍',
            'points': 200,
            'condition_json': json.dumps({'type': 'complex_problems_solved', 'target': 25})
        },
        {
            'name': '📚 Estudiante Eterno',
            'description': 'Trabaja en 10 tipos diferentes de máquinas',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '📚',
            'points': 120,
            'condition_json': json.dumps({'type': 'machine_variety', 'target': 10})
        },

        # ========================================
        # 🤝 LOGROS DE TRABAJO EN EQUIPO
        # ========================================
        {
            'name': '🌙 Búho Nocturno',
            'description': 'Completa 5 órdenes después de las 20:00',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.RARE,
            'icon': '🌙',
            'points': 80,
            'condition_json': json.dumps({'type': 'night_shift_orders', 'target': 5, 'after_hour': 20})
        },
        {
            'name': '🦉 Vigilante Nocturno',
            'description': 'Completa 15 órdenes después de las 22:00',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.EPIC,
            'icon': '🦉',
            'points': 150,
            'condition_json': json.dumps({'type': 'night_shift_orders', 'target': 15, 'after_hour': 22})
        },
        {
            'name': '🚨 Héroe de Emergencia',
            'description': 'Resuelve 3 emergencias en una semana',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.EPIC,
            'icon': '🚨',
            'points': 150,
            'condition_json': json.dumps({'type': 'emergency_orders', 'target': 3, 'timeframe_days': 7})
        },
        {
            'name': '🚑 Bombero Industrial',
            'description': 'Resuelve 10 emergencias en un mes',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🚑',
            'points': 400,
            'condition_json': json.dumps({'type': 'emergency_orders', 'target': 10, 'timeframe_days': 30})
        },
        {
            'name': '🎯 Colaborador',
            'description': 'Ayuda en 10 órdenes de otros técnicos',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.RARE,
            'icon': '🎯',
            'points': 100,
            'condition_json': json.dumps({'type': 'assistance_count', 'target': 10})
        },
        {
            'name': '🤝 Mentor',
            'description': 'Entrena a 3 técnicos nuevos',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.EPIC,
            'icon': '🤝',
            'points': 200,
            'condition_json': json.dumps({'type': 'mentoring_count', 'target': 3})
        },
        {
            'name': '🔀 Multitarea',
            'description': 'Trabaja en 5 órdenes simultáneamente',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.RARE,
            'icon': '🔀',
            'points': 90,
            'condition_json': json.dumps({'type': 'simultaneous_orders', 'target': 5})
        },
        {
            'name': '📞 Disponible 24/7',
            'description': 'Responde a llamadas de emergencia fuera de horario 10 veces',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.EPIC,
            'icon': '📞',
            'points': 180,
            'condition_json': json.dumps({'type': 'after_hours_calls', 'target': 10})
        },

        # ========================================
        # 💡 LOGROS DE INNOVACIÓN Y MEJORA
        # ========================================
        {
            'name': '💡 Innovador',
            'description': 'Sugiere 5 mejoras implementadas',
            'type': AchievementType.INNOVATION,
            'rarity': BadgeRarity.RARE,
            'icon': '💡',
            'points': 120,
            'condition_json': json.dumps({'type': 'suggestions_implemented', 'target': 5})
        },
        {
            'name': '🧠 Genio',
            'description': 'Encuentra una solución que ahorra 50+ horas al mes',
            'type': AchievementType.INNOVATION,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🧠',
            'points': 500,
            'condition_json': json.dumps({'type': 'time_saving_solution', 'hours_saved': 50})
        },
        {
            'name': '🔬 Investigador',
            'description': 'Documenta 10 procedimientos nuevos',
            'type': AchievementType.INNOVATION,
            'rarity': BadgeRarity.EPIC,
            'icon': '🔬',
            'points': 200,
            'condition_json': json.dumps({'type': 'procedures_documented', 'target': 10})
        },
        {
            'name': '⚡ Optimizador',
            'description': 'Mejora la eficiencia de un proceso en 30%',
            'type': AchievementType.INNOVATION,
            'rarity': BadgeRarity.EPIC,
            'icon': '⚡',
            'points': 250,
            'condition_json': json.dumps({'type': 'process_improvement', 'improvement_percent': 30})
        },
        {
            'name': '🎨 Creativo',
            'description': 'Desarrolla una herramienta casera útil',
            'type': AchievementType.INNOVATION,
            'rarity': BadgeRarity.RARE,
            'icon': '🎨',
            'points': 150,
            'condition_json': json.dumps({'type': 'custom_tool_created', 'target': 1})
        },

        # ========================================
        # 🏭 LOGROS ESPECÍFICOS POR EQUIPOS
        # ========================================
        {
            'name': '🔨 Especialista en Prensas',
            'description': 'Completa 50 órdenes en prensas hidráulicas',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '🔨',
            'points': 100,
            'condition_json': json.dumps({'type': 'machine_type_orders', 'machine_type': 'Prensa', 'target': 50})
        },
        {
            'name': '⚙️ Experto en Tornos',
            'description': 'Completa 50 órdenes en tornos CNC',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '⚙️',
            'points': 100,
            'condition_json': json.dumps({'type': 'machine_type_orders', 'machine_type': 'Torno', 'target': 50})
        },
        {
            'name': '🔧 Maestro de Soldadura',
            'description': 'Completa 50 órdenes de soldadura',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '🔧',
            'points': 100,
            'condition_json': json.dumps({'type': 'machine_type_orders', 'machine_type': 'Soldadora', 'target': 50})
        },
        {
            'name': '💡 Electricista Experto',
            'description': 'Resuelve 25 problemas eléctricos',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '💡',
            'points': 120,
            'condition_json': json.dumps({'type': 'electrical_problems_solved', 'target': 25})
        },
        {
            'name': '🌡️ Especialista en Temperatura',
            'description': 'Mantén sistemas de climatización por 90 días sin fallas',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.EPIC,
            'icon': '🌡️',
            'points': 200,
            'condition_json': json.dumps({'type': 'hvac_uptime', 'days': 90})
        },
        {
            'name': '🔩 Rey de los Rodamientos',
            'description': 'Cambia 100 rodamientos perfectamente',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.EPIC,
            'icon': '🔩',
            'points': 180,
            'condition_json': json.dumps({'type': 'bearing_replacements', 'target': 100})
        },

        # ========================================
        # 🎲 LOGROS ESPECIALES Y TEMPORADAS
        # ========================================
        {
            'name': '🎃 Trabajador de Halloween',
            'description': 'Trabaja el 31 de octubre',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.RARE,
            'icon': '🎃',
            'points': 100,
            'condition_json': json.dumps({'type': 'holiday_worker', 'date': '10-31'})
        },
        {
            'name': '🎄 Héroe Navideño',
            'description': 'Trabaja el 25 de diciembre',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.EPIC,
            'icon': '🎄',
            'points': 200,
            'condition_json': json.dumps({'type': 'holiday_worker', 'date': '12-25'})
        },
        {
            'name': '🎆 Guerrero de Año Nuevo',
            'description': 'Trabaja el 1 de enero',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.EPIC,
            'icon': '🎆',
            'points': 200,
            'condition_json': json.dumps({'type': 'holiday_worker', 'date': '01-01'})
        },
        {
            'name': '☀️ Verano Productivo',
            'description': 'Completa 100 órdenes en verano',
            'type': AchievementType.CONSISTENCY,
            'rarity': BadgeRarity.RARE,
            'icon': '☀️',
            'points': 150,
            'condition_json': json.dumps({'type': 'seasonal_orders', 'season': 'summer', 'target': 100})
        },
        {
            'name': '❄️ Guerrero del Invierno',
            'description': 'Trabaja bajo condiciones extremas de frío 10 veces',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.EPIC,
            'icon': '❄️',
            'points': 180,
            'condition_json': json.dumps({'type': 'extreme_conditions', 'condition': 'cold', 'target': 10})
        },
        {
            'name': '🌈 Después de la Tormenta',
            'description': 'Restaura servicios después de un corte de energía',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.EPIC,
            'icon': '🌈',
            'points': 250,
            'condition_json': json.dumps({'type': 'power_restoration', 'target': 1})
        },

        # ========================================
        # 🏃‍♂️ LOGROS DE EFICIENCIA Y TIEMPO
        # ========================================
        {
            'name': '⏱️ Cronometrado',
            'description': 'Completa 20 órdenes en tiempo exacto estimado',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.RARE,
            'icon': '⏱️',
            'points': 100,
            'condition_json': json.dumps({'type': 'exact_timing', 'target': 20, 'variance': 5})
        },
        {
            'name': '🎯 Calculadora Humana',
            'description': 'Estima tiempos con 95% de precisión en 50 órdenes',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.EPIC,
            'icon': '🎯',
            'points': 200,
            'condition_json': json.dumps({'type': 'time_estimation_accuracy', 'target': 50, 'accuracy': 95})
        },
        {
            'name': '🔄 Reciclador',
            'description': 'Reutiliza materiales en 25 reparaciones',
            'type': AchievementType.INNOVATION,
            'rarity': BadgeRarity.RARE,
            'icon': '🔄',
            'points': 120,
            'condition_json': json.dumps({'type': 'material_reuse', 'target': 25})
        },
        {
            'name': '💰 Ahorrador',
            'description': 'Ahorra $5000 en costos de reparación',
            'type': AchievementType.INNOVATION,
            'rarity': BadgeRarity.EPIC,
            'icon': '💰',
            'points': 300,
            'condition_json': json.dumps({'type': 'cost_savings', 'target': 5000})
        },
        {
            'name': '📊 Analista',
            'description': 'Registra datos de rendimiento por 60 días consecutivos',
            'type': AchievementType.CONSISTENCY,
            'rarity': BadgeRarity.RARE,
            'icon': '📊',
            'points': 150,
            'condition_json': json.dumps({'type': 'data_logging_streak', 'target_days': 60})
        },

        # ========================================
        # 🎖️ LOGROS DE LIDERAZGO Y RECONOCIMIENTO
        # ========================================
        {
            'name': '👥 Líder del Turno',
            'description': 'Dirige un equipo de 5+ técnicos exitosamente',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.EPIC,
            'icon': '👥',
            'points': 250,
            'condition_json': json.dumps({'type': 'team_leadership', 'team_size': 5})
        },
        {
            'name': '🎓 Instructor',
            'description': 'Entrena a 10 técnicos nuevos',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🎓',
            'points': 400,
            'condition_json': json.dumps({'type': 'training_sessions', 'target': 10})
        },
        {
            'name': '📝 Documentalista',
            'description': 'Crea 20 manuales de procedimientos',
            'type': AchievementType.INNOVATION,
            'rarity': BadgeRarity.EPIC,
            'icon': '📝',
            'points': 300,
            'condition_json': json.dumps({'type': 'manuals_created', 'target': 20})
        },
        {
            'name': '🎙️ Comunicador',
            'description': 'Presenta 5 informes técnicos a la gerencia',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.RARE,
            'icon': '🎙️',
            'points': 150,
            'condition_json': json.dumps({'type': 'technical_presentations', 'target': 5})
        },
        {
            'name': '🏅 Empleado del Mes',
            'description': 'Recibe reconocimiento formal por excelencia',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.EPIC,
            'icon': '🏅',
            'points': 500,
            'condition_json': json.dumps({'type': 'formal_recognition', 'target': 1})
        },

        # ========================================
        # 🌟 LOGROS ÉPICOS Y LEGENDARIOS
        # ========================================
        {
            'name': '🦸‍♂️ Superhéroe Industrial',
            'description': 'Completa 50 emergencias exitosamente',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🦸‍♂️',
            'points': 1000,
            'condition_json': json.dumps({'type': 'emergency_orders', 'target': 50, 'timeframe_days': 365})
        },
        {
            'name': '🎯 100% Perfecto',
            'description': 'Mantén 100% de eficiencia por 30 días',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🎯',
            'points': 750,
            'condition_json': json.dumps({'type': 'perfect_efficiency', 'days': 30})
        },
        {
            'name': '🌍 Salvador de la Planta',
            'description': 'Previene una parada total de producción',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🌍',
            'points': 1500,
            'condition_json': json.dumps({'type': 'production_save', 'target': 1})
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
            'name': '👑 Rey del Mantenimiento',
            'description': 'Lidera el ranking por 6 meses consecutivos',
            'type': AchievementType.CONSISTENCY,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '👑',
            'points': 2000,
            'condition_json': json.dumps({'type': 'leaderboard_dominance', 'months': 6})
        },

        # ========================================
        # 🎲 LOGROS DIVERTIDOS Y ÚNICOS
        # ========================================
        {
            'name': '☕ Adicto al Café',
            'description': 'Repara la máquina de café 5 veces',
            'type': AchievementType.TEAMWORK,
            'rarity': BadgeRarity.COMMON,
            'icon': '☕',
            'points': 50,
            'condition_json': json.dumps({'type': 'coffee_machine_repairs', 'target': 5})
        },
        {
            'name': '🔧 MacGyver',
            'description': 'Repara algo usando solo clips y cinta adhesiva',
            'type': AchievementType.INNOVATION,
            'rarity': BadgeRarity.EPIC,
            'icon': '🔧',
            'points': 200,
            'condition_json': json.dumps({'type': 'creative_repair', 'target': 1})
        },
        {
            'name': '🎵 Mecánico Musical',
            'description': 'Identifica problemas por el sonido 10 veces',
            'type': AchievementType.LEARNING,
            'rarity': BadgeRarity.RARE,
            'icon': '🎵',
            'points': 100,
            'condition_json': json.dumps({'type': 'sound_diagnosis', 'target': 10})
        },
        {
            'name': '🧩 Solucionador de Puzzles',
            'description': 'Resuelve 5 problemas que otros no pudieron',
            'type': AchievementType.INNOVATION,
            'rarity': BadgeRarity.EPIC,
            'icon': '🧩',
            'points': 250,
            'condition_json': json.dumps({'type': 'unsolved_problems', 'target': 5})
        },
        {
            'name': '🎪 Malabarista',
            'description': 'Gestiona 10 órdenes urgentes simultáneamente',
            'type': AchievementType.SPEED,
            'rarity': BadgeRarity.EPIC,
            'icon': '🎪',
            'points': 300,
            'condition_json': json.dumps({'type': 'urgent_multitasking', 'target': 10})
        },
        {
            'name': '🔮 Adivino Técnico',
            'description': 'Predice 5 fallas antes de que ocurran',
            'type': AchievementType.QUALITY,
            'rarity': BadgeRarity.LEGENDARY,
            'icon': '🔮',
            'points': 500,
            'condition_json': json.dumps({'type': 'failure_prediction', 'target': 5})
        }
    ]
    
    # Insertar logros en la base de datos
    inserted_count = 0
    for ach_data in achievements:
        existing = db.query(Achievement).filter(
            Achievement.name == ach_data['name']
        ).first()
        
        if not existing:
            achievement = Achievement(**ach_data)
            db.add(achievement)
            inserted_count += 1
    
    db.commit()
    print(f"✅ Configurados {inserted_count} nuevos logros ({len(achievements)} total en el sistema)")
    return inserted_count

# Función auxiliar para categorizar logros
def get_achievements_by_category():
    """Devuelve logros organizados por categorías para mejor visualización"""
    return {
        'Velocidad y Productividad': [
            '⚡ Rayo McQueen', '💨 Velocista', '🏃 Flash', '🚀 Productivo', 
            '🌟 Súper Productivo', '💫 Hiper Productivo', '🔥 Máquina Imparable'
        ],
        'Calidad y Precisión': [
            '🎯 Precisión', '💎 Perfeccionista', '🏆 Maestro Artesano', 
            '👑 Leyenda Viviente', '✨ Trabajo Impecable'
        ],
        'Consistencia': [
            '📅 Constante', '🔥 En Llamas', '🌪️ Vendaval', '⚡ Indestructible'
        ],
        'Aprendizaje y Experiencia': [
            '🎓 Novato', '⚙️ Aprendiz', '🔧 Técnico', '👨‍🔧 Experto', 
            '🎖️ Veterano', '👑 Maestro', '🌟 Leyenda'
        ],
        'Trabajo en Equipo': [
            '🌙 Búho Nocturno', '🚨 Héroe de Emergencia', '🤝 Mentor', 
            '👥 Líder del Turno', '🦸‍♂️ Superhéroe Industrial'
        ],
        'Innovación': [
            '💡 Innovador', '🧠 Genio', '🔬 Investigador', '⚡ Optimizador'
        ],
        'Especialidades': [
            '🔨 Especialista en Prensas', '⚙️ Experto en Tornos', 
            '🔧 Maestro de Soldadura', '💡 Electricista Experto'
        ],
        'Logros Épicos': [
            '🌍 Salvador de la Planta', '💎 Diamante Industrial', 
            '👑 Rey del Mantenimiento', '🔮 Adivino Técnico'
        ],
        'Diversión': [
            '☕ Adicto al Café', '🔧 MacGyver', '🎵 Mecánico Musical', 
            '🧩 Solucionador de Puzzles', '🎪 Malabarista'
        ]
    }