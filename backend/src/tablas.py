from models import Base

print("Tablas registradas:")
for table_name in Base.metadata.tables.keys():
    print(table_name)
