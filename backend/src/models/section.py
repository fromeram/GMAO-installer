# src/models/section.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base

class Section(Base):
    __tablename__ = "sections"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)

    lines = relationship("Line", back_populates="section", cascade="all, delete-orphan", lazy="joined")
    machines = relationship("Machine", back_populates="section", cascade="all, delete-orphan", lazy="joined")
    users = relationship("User", back_populates="section")
