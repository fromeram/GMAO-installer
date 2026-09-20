# schemas/sections.py — Schemas de secciones y líneas
from pydantic import BaseModel


class SectionReadBasic(BaseModel):
    id: int; nombre: str
    class Config: orm_mode = True

class SectionCreate(BaseModel):
    nombre: str

class SectionUpdate(BaseModel):
    nombre: str

class LineReadBasic(BaseModel):
    id: int; nombre: str
    class Config: orm_mode = True

class LineCreate(BaseModel):
    nombre: str; section_id: int

class LineUpdate(BaseModel):
    nombre: str
