#!/usr/bin/env python3
"""
Script para ejecutar migraciones directamente usando SQL
sin depender de la importación de modelos.
"""
import os
import sys
from sqlalchemy import create_engine, text

# URL de la base de datos (ajusta según tu configuración)
DB_URL = "postgresql://Admin:Francisco@localhost:5432/gmao_db"

def run_migration():
    """Ejecuta SQL de migración directamente"""
    print("Conectando a la base de datos...")
    engine = create_engine(DB_URL)
    
    with engine.begin() as conn:
        print("Ejecutando migración...")
        
        # Verificar tablas existentes
        result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        existing_tables = [row[0] for row in result]
        print(f"Tablas existentes: {', '.join(existing_tables)}")
        
        # Crear tablas faltantes (migration UP)
        if 'maintenance_backlogs' not in existing_tables:
            print("Creando tabla maintenance_backlogs...")
            conn.execute(text("""
                CREATE TABLE maintenance_backlogs (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    priority VARCHAR(20) DEFAULT 'Media',
                    status VARCHAR(20) DEFAULT 'Pendiente',
                    machine_id INTEGER REFERENCES machines(id),
                    section_id INTEGER REFERENCES sections(id),
                    created_by_id INTEGER NOT NULL REFERENCES users(id),
                    assigned_to_id INTEGER REFERENCES users(id),
                    estimated_hours INTEGER,
                    estimated_downtime INTEGER,
                    notes TEXT,
                    completion_notes TEXT,
                    actual_work_order_id INTEGER REFERENCES work_orders(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """))
        
        # Verificar si inventory tiene stock_minimo
        result = conn.execute(text(
            "SELECT 1 FROM information_schema.columns WHERE table_name='inventory' AND column_name='stock_minimo'"
        ))
        if not result.fetchone():
            print("Añadiendo columna stock_minimo a inventory...")
            conn.execute(text("ALTER TABLE inventory ADD COLUMN stock_minimo INTEGER DEFAULT 0"))
        
        # Crear tabla task_lists si no existe
        if 'task_lists' not in existing_tables:
            print("Creando tabla task_lists...")
            conn.execute(text("""
                CREATE TABLE task_lists (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    description TEXT,
                    applies_to_type VARCHAR(255)
                )
            """))
        
        # Crear tabla task_steps si no existe
        if 'task_steps' not in existing_tables:
            print("Creando tabla task_steps...")
            conn.execute(text("""
                CREATE TABLE task_steps (
                    id SERIAL PRIMARY KEY,
                    task_list_id INTEGER NOT NULL REFERENCES task_lists(id) ON DELETE CASCADE,
                    step_order INTEGER NOT NULL DEFAULT 1,
                    description TEXT NOT NULL,
                    estimated_time_minutes INTEGER
                )
            """))
        
        # Crear tabla shift_patterns si no existe
        if 'shift_patterns' not in existing_tables:
            print("Creando tabla shift_patterns...")
            conn.execute(text("""
                CREATE TABLE shift_patterns (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    description TEXT,
                    pattern_sequence VARCHAR(255) NOT NULL,
                    cycle_length_days INTEGER NOT NULL
                )
            """))
        
        # Crear tabla shift_assignments si no existe
        if 'shift_assignments' not in existing_tables:
            print("Creando tabla shift_assignments...")
            conn.execute(text("""
                CREATE TABLE shift_assignments (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    pattern_id INTEGER NOT NULL REFERENCES shift_patterns(id),
                    reference_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    offset_days INTEGER NOT NULL DEFAULT 0,
                    UNIQUE (user_id)
                )
            """))
        else:
            # Verificar si reference_date existe
            result = conn.execute(text(
                "SELECT 1 FROM information_schema.columns WHERE table_name='shift_assignments' AND column_name='reference_date'"
            ))
            if not result.fetchone():
                print("Añadiendo columna reference_date a shift_assignments...")
                conn.execute(text("ALTER TABLE shift_assignments ADD COLUMN reference_date DATE"))
                conn.execute(text("UPDATE shift_assignments SET reference_date = CURRENT_DATE WHERE reference_date IS NULL"))
                conn.execute(text("ALTER TABLE shift_assignments ALTER COLUMN reference_date SET NOT NULL"))
        
        # Crear tabla shift_overrides si no existe
        if 'shift_overrides' not in existing_tables:
            print("Creando tabla shift_overrides...")
            conn.execute(text("""
                CREATE TABLE shift_overrides (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    date DATE NOT NULL,
                    actual_shift_code VARCHAR(10) NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, date)
                )
            """))
        
        # Crear tablas para códigos FCR
        for table_name in ['failure_codes', 'cause_codes', 'remedy_codes']:
            if table_name not in existing_tables:
                print(f"Creando tabla {table_name}...")
                conn.execute(text(f"""
                    CREATE TABLE {table_name} (
                        id SERIAL PRIMARY KEY,
                        code VARCHAR(50) NOT NULL UNIQUE,
                        description VARCHAR(255) NOT NULL
                    )
                """))
        
        # Añadir columnas FCR a work_orders
        for column, column_type in [
            ('failure_code_id', 'INTEGER REFERENCES failure_codes(id)'),
            ('cause_code_id', 'INTEGER REFERENCES cause_codes(id)'),
            ('remedy_code_id', 'INTEGER REFERENCES remedy_codes(id)'),
            ('actual_start_time', 'TIMESTAMP'),
            ('actual_end_time', 'TIMESTAMP'),
            ('downtime_hours', 'NUMERIC(10,2) DEFAULT 0.0'),
            ('completion_notes', 'TEXT')
        ]:
            result = conn.execute(text(
                f"SELECT 1 FROM information_schema.columns WHERE table_name='work_orders' AND column_name='{column}'"
            ))
            if not result.fetchone():
                print(f"Añadiendo columna {column} a work_orders...")
                conn.execute(text(f"ALTER TABLE work_orders ADD COLUMN {column} {column_type}"))
        
        # Registrar la migración en alembic_version
        # Verificar primero si la migración 8a72fb27622a ya está registrada
        result = conn.execute(text("SELECT 1 FROM alembic_version WHERE version_num = '8a72fb27622a'"))
        if not result.fetchone():
            print("Registrando la migración en alembic_version...")
            # Verificar si existe la tabla alembic_version
            result = conn.execute(text("SELECT 1 FROM information_schema.tables WHERE table_name='alembic_version'"))
            if not result.fetchone():
                conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
                conn.execute(text("INSERT INTO alembic_version VALUES ('8a72fb27622a')"))
            else:
                # Verificar si hay alguna versión anterior registrada
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.fetchone()
                if version:
                    print(f"Actualizando versión en alembic_version de {version[0]} a 8a72fb27622a...")
                    conn.execute(text("UPDATE alembic_version SET version_num = '8a72fb27622a'"))
                else:
                    conn.execute(text("INSERT INTO alembic_version VALUES ('8a72fb27622a')"))
        
        print("¡Migración completada con éxito!")

if __name__ == "__main__":
    run_migration()