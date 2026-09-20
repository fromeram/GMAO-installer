# schemas/codes.py — Schemas de códigos de fallo, causa y remedio
from typing import Optional
from pydantic import BaseModel, Field


class CodeBase(BaseModel):
    code: str = Field(..., max_length=50)
    description: str = Field(..., max_length=255)

class CodeRead(CodeBase):
    id: int
    active: Optional[bool] = True
    class Config: orm_mode = True

class CodeCreate(CodeBase):
    active: bool = True

class CodeUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    active: Optional[bool] = None
