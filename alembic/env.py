# alembic/env.py
import os
import sys
import socket
from logging.config import fileConfig
from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool
from alembic import context

# --- INICIO DE MODIFICACIONES (Adaptado para Contenedor /app) ---
# Dentro del contenedor, el WORKDIR suele ser /app donde se monta el código.
# Añadimos /app directamente al path, ya que 'src' estará ahí.
app_path = '/app'  # Ruta base dentro del contenedor
sys.path.insert(0, app_path)
# También agrega la ruta actual (del proyecto)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("-" * 50)
print(f"DEBUG: Running inside container presumably.")
print(f"DEBUG: Added app_path to sys.path: {app_path}")
print(f"DEBUG: Current sys.path: {sys.path}")
print("-" * 50)

# --- Importar CON el prefijo 'src.' ---
# Python buscará en /app y encontrará el paquete 'src'
print("DEBUG: Attempting to import Base from src.models.base...")
try:
    from src.models.base import Base  # Importa tu Base (CON 'src.')
    print("DEBUG: Imported Base successfully.")
except ImportError as e:
    print(f"ERROR: Failed to import Base: {e}")
    print(f"ERROR: Check if '{app_path}/src/models/base.py' exists and '{app_path}/src/__init__.py' exists inside the container.")
    
    # Intenta alternativa sin 'src'
    try:
        print("DEBUG: Attempting fallback import without 'src' prefix...")
        from models.base import Base
        print("DEBUG: Imported Base successfully using fallback method.")
    except ImportError as e2:
        print(f"ERROR: Fallback import also failed: {e2}")
        raise e  # Raise original error

print("DEBUG: Attempting to import models...")
try:
    # Importa todos los modelos CON el prefijo 'src.'
    from src.models.role import Role
    from src.models.user import User
    from src.models.section import Section
    from src.models.line import Line
    from src.models.machine import Machine
    from src.models.supplier import Supplier
    from src.models.warehouse import Warehouse
    from src.models.inventory import Inventory
    from src.models.maintenance import Maintenance
    from src.models.document import Document
    from src.models.menu import Menu
    from src.models.supplier_product_price import SupplierProductPrice
    from src.models.work_order import WorkOrder, FailureCode, CauseCode, RemedyCode
    # Añadir los nuevos modelos
    try:
        from src.models.maintenance_backlog import MaintenanceBacklog
        from src.models.task_list import TaskList
        from src.models.task_step import TaskStep
        from src.models.shift_pattern import ShiftPattern
        from src.models.shift_assignment import ShiftAssignment
        from src.models.shift_override import ShiftOverride
        from src.models.absence import Absence
        print("DEBUG: New models also imported successfully.")
    except ImportError as e:
        print(f"WARNING: Could not import some new models: {e}. They will be created in the migration.")
    
    print("DEBUG: Models imported successfully.")
except ImportError as e:
    print(f"ERROR: Failed to import one or more models: {e}. Check paths and file names inside '{app_path}/src/models/'.")
    
    # Intenta alternativa sin 'src'
    try:
        print("DEBUG: Attempting fallback imports without 'src' prefix...")
        from models.role import Role
        from models.user import User
        # ... resto de imports
        print("DEBUG: Models imported successfully using fallback method.")
    except ImportError as e2:
        print(f"ERROR: Fallback model imports also failed: {e2}")
        raise e  # Raise original error

# Configuración
config = context.config

# MODIFICACIÓN: Determinar si estamos dentro o fuera del contenedor Docker
def is_docker():
    try:
        # Comprueba si existe el archivo .dockerenv que indica entorno Docker
        return os.path.exists('/.dockerenv')
    except:
        return False

# Determinar la URL de la base de datos
if is_docker():
    # Dentro del contenedor Docker
    db_url = "os.getenv("DATABASE_URL", "postgresql+psycopg2://gmao_user:gmao_pass@db:5432/gmao_db")"
    print(f"DEBUG: Running inside Docker container, using URL: {db_url}")
else:
    # Fuera del contenedor Docker (en la máquina host)
    db_url = "os.getenv("DATABASE_URL", "postgresql+psycopg2://gmao_user:gmao_pass@localhost:5432/gmao_db")"
    print(f"DEBUG: Running on host machine, using URL: {db_url}")

# Sobrescribir la URL de conexión en la configuración
config.set_main_option('sqlalchemy.url', db_url)

if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
# --- FIN DE MODIFICACIONES ---

def run_migrations_offline() -> None:
    # Esta parte usará la URL que configuramos arriba
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    # MODIFICACIÓN: Usar directamente la URL desde la variable db_url
    # en lugar de obtenerla de la configuración
    connectable = create_engine(db_url)
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()