# schemas/auth.py — Schemas de autenticación y usuarios
from typing import Optional
from pydantic import BaseModel, Field, validator


class LoginModel(BaseModel):
    username: str; password: str

class Token(BaseModel):
    access_token: str; token_type: str

class RoleCreate(BaseModel):
    id: int; nombre: str

class UserCreate(BaseModel):
    username: str; password: str; role_id: int; section_id: Optional[int] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    role_id: Optional[int] = None
    section_id: Optional[int] = None

class UserReadBasic(BaseModel):
    id: int; username: str
    class Config: orm_mode = True

class PasswordChangeRequest(BaseModel):
    new_password: str = Field(..., min_length=6, description="Nueva contraseña (mínimo 6 caracteres)")
    confirm_password: str = Field(..., description="Confirmación de la nueva contraseña")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Las contraseñas no coinciden')
        return v

class PasswordChangeResponse(BaseModel):
    success: bool
    message: str
    user_id: int
    username: str
