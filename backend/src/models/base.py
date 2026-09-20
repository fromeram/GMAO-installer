# models/base.py
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Configuración adicional del Base si es necesaria
def as_dict(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}

Base.as_dict = as_dict
