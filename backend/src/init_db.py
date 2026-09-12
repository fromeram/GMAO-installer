# backend/src/init_db.py
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.database import Base, DATABASE_URL

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_db():
    try:
        logger.info("Creando engine...")
        engine = create_engine(DATABASE_URL, echo=True)
        
        # Creamos una sesión
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Primero eliminamos todas las tablas existentes
            logger.info("Eliminando tablas existentes...")
            session.execute(text("DROP TABLE IF EXISTS work_orders CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS maintenances CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS inventory CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS machines CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS lines CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS roles CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS sections CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS suppliers CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS warehouses CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS menu CASCADE"))
            session.commit()
            logger.info("Tablas eliminadas exitosamente")
            
            # Crear tablas en orden específico
            logger.info("Creando tablas base...")
            
            # 1. Roles
            session.execute(text("""
                CREATE TABLE roles (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(50) UNIQUE NOT NULL
                );
            """))
            
            # 2. Sections
            session.execute(text("""
                CREATE TABLE sections (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(50) UNIQUE NOT NULL
                );
            """))
            
            # 3. Suppliers
            session.execute(text("""
                CREATE TABLE suppliers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    company VARCHAR(100) NOT NULL,
                    phone VARCHAR(20) NOT NULL
                );
            """))
            
            # 4. Warehouses
            session.execute(text("""
                CREATE TABLE warehouses (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL
                );
            """))
            
            # 5. Users
            session.execute(text("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(200) NOT NULL,
                    role_id INTEGER REFERENCES roles(id),
                    section_id INTEGER REFERENCES sections(id)
                );
            """))
            
            # 6. Lines
            session.execute(text("""
                CREATE TABLE lines (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(50) NOT NULL,
                    section_id INTEGER REFERENCES sections(id) NOT NULL,
                    UNIQUE(nombre, section_id)
                );
            """))
            
            # 7. Machines
            session.execute(text("""
                CREATE TABLE machines (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    modelo VARCHAR(100) NOT NULL,
                    marca VARCHAR(100) NOT NULL,
                    numero_serie VARCHAR(100) UNIQUE NOT NULL,
                    line_id INTEGER REFERENCES lines(id) NOT NULL,
                    section_id INTEGER REFERENCES sections(id) NOT NULL
                );
            """))
            
            # 8. Inventory
            session.execute(text("""
                CREATE TABLE inventory (
                    id SERIAL PRIMARY KEY,
                    product_name VARCHAR(100) NOT NULL,
                    quantity INTEGER NOT NULL CHECK (quantity >= 0),
                    location VARCHAR(50) REFERENCES warehouses(name) NOT NULL,
                    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
                    supplier_id INTEGER REFERENCES suppliers(id)
                );
            """))
            
            # 9. Maintenances
            session.execute(text("""
                CREATE TABLE maintenances (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(100) NOT NULL,
                    type VARCHAR(20) NOT NULL CHECK (type IN ('Preventivo', 'Correctivo')),
                    description TEXT NOT NULL,
                    machine_id INTEGER REFERENCES machines(id) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # 10. Work Orders
            session.execute(text("""
                CREATE TABLE work_orders (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(100) NOT NULL,
                    work_type VARCHAR(20) NOT NULL CHECK (work_type IN ('Preventivo', 'Correctivo')),
                    section_id INTEGER REFERENCES sections(id) NOT NULL,
                    line_id INTEGER REFERENCES lines(id) NOT NULL,
                    machine_id INTEGER REFERENCES machines(id) NOT NULL,
                    operator VARCHAR(100) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'Pendiente' CHECK (status IN ('Pendiente', 'En curso', 'Finalizada', 'Cerrada')),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    finished_at TIMESTAMP WITH TIME ZONE,
                    imagen_url TEXT,
                    repuesto_id INTEGER REFERENCES inventory(id),
                    quantity_used INTEGER DEFAULT 0 CHECK (quantity_used >= 0)
                );
            """))
            
            # Insertar datos iniciales
            logger.info("Insertando datos iniciales...")
            
            # Roles
            session.execute(text("""
                INSERT INTO roles (id, nombre) VALUES 
                (1, 'Administrador'),
                (2, 'Jefe de Sección'),
                (3, 'Mecánico'),
                (4, 'Jefe de Mantenimiento')
                ON CONFLICT DO NOTHING;
            """))
            
            # Usuario Admin
            session.execute(text("""
                INSERT INTO users (username, password, role_id) VALUES 
                ('admin', '$2b$12$n3axm.ZTKh89NBhruQGtUeGVcSZYQ2QrTLYGG1SCy8.AKKT6.CDAm', 1)
                ON CONFLICT DO NOTHING;
            """))
            
            # Almacén principal
            session.execute(text("""
                INSERT INTO warehouses (name) VALUES 
                ('Almacén Principal')
                ON CONFLICT DO NOTHING;
            """))
            
            session.commit()
            logger.info("Inicialización completada exitosamente")
            
        except Exception as e:
            logger.error(f"Error en la creación de datos: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error en la inicialización: {str(e)}")
        raise

if __name__ == "__main__":
    init_db()
