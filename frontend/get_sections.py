from sqlalchemy import create_engine, MetaData, Table, select

# Configuración para conectarse a la base de datos
DATABASE_URL = "postgresql://Admin:Francisco@localhost:5432/gmao_db"
engine = create_engine(DATABASE_URL)
connection = engine.connect()
metadata = MetaData()

# Reflejar la tabla 'sections'
sections_table = Table('sections', metadata, autoload_with=engine)

# Consultar todas las secciones de la base de datos
query = select(sections_table)  # Cambiado de select([table]) a select(table)
result = connection.execute(query)
sections = result.fetchall()

# Imprimir las secciones
for section in sections:
    print(section)

# Cerrar la conexión
connection.close()
