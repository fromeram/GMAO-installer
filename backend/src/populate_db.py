from sqlalchemy.orm import Session
from models import Role
from database import engine

session = Session(bind=engine)
admin_role = Role(nombre="Administrador")
session.add(admin_role)
session.commit()
session.close()
