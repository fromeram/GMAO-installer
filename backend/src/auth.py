"""
Módulo de autenticación.
Incluye funciones para verificar contraseñas, crear tokens JWT y obtener el usuario actual.
"""
# backend/src/auth.py
from datetime import datetime, timedelta  # <-- CORREGIDO: importar timedelta directamente
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.user import User
from src.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_DELTA

# Configuración de autenticación usando variables de config.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):  # <-- CORREGIDO: usar timedelta
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + JWT_ACCESS_TOKEN_EXPIRE_DELTA
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role and current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento"]:
        return current_user
    raise HTTPException(status_code=403, detail="No tienes permisos de administrador")

async def get_jefe_seccion_user(current_user: User = Depends(get_current_user)):
    if current_user.role and current_user.role.nombre in ["Administrador", "Jefe de Mantenimiento", "Jefe de Sección"]:
        return current_user
    raise HTTPException(status_code=403, detail="No tienes permisos suficientes")