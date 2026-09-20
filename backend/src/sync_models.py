from sqlalchemy import create_engine
from models import Machine, Section, Line, Supplier, Inventory, WorkOrder, User, Role
from database import engine, Base

# Crear todas las tablas en la base de datos
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas con éxito.")
