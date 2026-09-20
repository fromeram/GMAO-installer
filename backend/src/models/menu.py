# menu.py
"""
Modelo de menú (opcional, para la administración de rutas o secciones de la UI en el backend).
"""

from sqlalchemy import Column, Integer, String
from src.database import Base

class Menu(Base):
    __tablename__ = "menu"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    url = Column(String, nullable=False)
    # Se pueden agregar más campos (por ejemplo, descripción o icono)
