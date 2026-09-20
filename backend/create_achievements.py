#!/usr/bin/env python3
# backend/create_achievements.py
"""
Script para crear todos los logros realistas del sistema de gamificación
Ejecutar desde la raíz del proyecto backend: python create_achievements.py
"""

import sys
import os

# Añadir el directorio src al path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database import SessionLocal
from src.gamification.realistic_achievements import setup_all_realistic_achievements, print_system_info
from src.models.gamification import Achievement

def main():
    """Función principal para crear todos los logros"""
    
    print("🎮 CONFIGURADOR DE LOGROS REALISTAS")
    print("=" * 50)
    
    # Mostrar información del sistema
    print_system_info()
    print("")
    
    # Confirmar ejecución
    response = input("¿Continuar con la creación de logros? (s/N): ").lower().strip()
    if response not in ['s', 'si', 'y', 'yes']:
        print("❌ Operación cancelada")
        return
    
    print("\n🚀 Iniciando creación de logros...")
    
    db = SessionLocal()
    try:
        # Verificar logros existentes
        existing_count = db.query(Achievement).filter(Achievement.active == True).count()
        print(f"📊 Logros existentes en BD: {existing_count}")
        
        if existing_count > 0:
            response = input(f"Ya hay {existing_count} logros. ¿Continuar añadiendo más? (s/N): ").lower().strip()
            if response not in ['s', 'si', 'y', 'yes']:
                print("❌ Operación cancelada")
                return
        
        # Crear todos los logros realistas
        created_count = setup_all_realistic_achievements(db)
        
        # Verificar resultado
        total_count = db.query(Achievement).filter(Achievement.active == True).count()
        
        print(f"\n🎉 ¡CONFIGURACIÓN COMPLETADA!")
        print(f"✅ Logros nuevos creados: {created_count}")
        print(f"📊 Total de logros en sistema: {total_count}")
        
        if created_count > 0:
            print(f"\n🚀 Próximos pasos:")
            print(f"   1. Reinicia tu servidor backend")
            print(f"   2. Actualiza el frontend si es necesario")
            print(f"   3. ¡El sistema de gamificación está listo!")
        else:
            print(f"\n📌 Todos los logros ya estaban configurados")
            print(f"🔄 No se requiere ninguna acción adicional")
        
    except Exception as e:
        print(f"\n❌ ERROR durante la configuración:")
        print(f"   {str(e)}")
        print(f"\n🔧 Posibles soluciones:")
        print(f"   • Verifica que la base de datos esté funcionando")
        print(f"   • Ejecuta las migraciones de Alembic si es necesario")
        print(f"   • Revisa que los modelos de gamificación estén importados")
        
        db.rollback()
        return 1
        
    finally:
        db.close()
    
    return 0

def show_statistics():
    """Muestra estadísticas de logros sin crear ninguno"""
    
    print("📊 ESTADÍSTICAS DE LOGROS")
    print("=" * 40)
    
    db = SessionLocal()
    try:
        total_achievements = db.query(Achievement).filter(Achievement.active == True).count()
        print(f"🏆 Total de logros activos: {total_achievements}")
        
        if total_achievements > 0:
            # Contar por rareza
            from src.models.gamification import BadgeRarity
            
            print(f"\n📈 Distribución por rareza:")
            for rarity in BadgeRarity:
                count = db.query(Achievement).filter(
                    Achievement.rarity == rarity,
                    Achievement.active == True
                ).count()
                print(f"   • {rarity.value.title()}: {count} logros")
            
            # Contar por tipo
            from src.models.gamification import AchievementType
            
            print(f"\n🎯 Distribución por tipo:")
            for ach_type in AchievementType:
                count = db.query(Achievement).filter(
                    Achievement.type == ach_type,
                    Achievement.active == True
                ).count()
                print(f"   • {ach_type.value.title()}: {count} logros")
        else:
            print(f"\n⚠️ No hay logros configurados en el sistema")
            print(f"   Ejecuta este script sin parámetros para crearlos")
            
    except Exception as e:
        print(f"❌ Error consultando estadísticas: {e}")
    finally:
        db.close()

def reset_achievements():
    """CUIDADO: Elimina todos los logros - Solo para desarrollo"""
    
    print("⚠️ RESET DE LOGROS - OPERACIÓN PELIGROSA")
    print("=" * 50)
    print("Esta operación eliminará TODOS los logros existentes")
    print("Solo usar en entorno de desarrollo")
    
    response = input("¿Estás SEGURO de que quieres eliminar todos los logros? (escribir 'RESET'): ").strip()
    if response != 'RESET':
        print("❌ Operación cancelada por seguridad")
        return
    
    db = SessionLocal()
    try:
        # Contar logros antes
        before_count = db.query(Achievement).count()
        
        # Eliminar todos los logros
        db.query(Achievement).delete()
        db.commit()
        
        print(f"✅ Eliminados {before_count} logros")
        print(f"🗑️ Base de datos de logros reiniciada")
        
    except Exception as e:
        print(f"❌ Error durante el reset: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Verificar argumentos de línea de comandos
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command in ['stats', 'statistics', 'info']:
            show_statistics()
        elif command in ['reset', 'clear']:
            reset_achievements()
        elif command in ['help', '-h', '--help']:
            print("📋 COMANDOS DISPONIBLES:")
            print("   python create_achievements.py          # Crear logros")
            print("   python create_achievements.py stats    # Ver estadísticas")
            print("   python create_achievements.py reset    # Eliminar todos (PELIGROSO)")
            print("   python create_achievements.py help     # Mostrar esta ayuda")
        else:
            print(f"❌ Comando desconocido: {command}")
            print("   Usa 'python create_achievements.py help' para ver comandos")
    else:
        # Ejecución normal: crear logros
        exit_code = main()
        sys.exit(exit_code)