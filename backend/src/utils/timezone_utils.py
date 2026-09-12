# src/utils/timezone_utils.py - UTILIDAD PARA ZONA HORARIA

from datetime import datetime
import pytz
import os

# Obtener zona horaria del entorno o usar Madrid por defecto
TIMEZONE_NAME = os.getenv('TZ', 'Europe/Madrid')
LOCAL_TZ = pytz.timezone(TIMEZONE_NAME)

def get_local_time():
    """Devuelve la hora actual en la zona horaria local configurada"""
    return datetime.now(LOCAL_TZ)

def get_local_time_naive():
    """Devuelve la hora actual local pero sin timezone info (para SQLAlchemy)"""
    return datetime.now(LOCAL_TZ).replace(tzinfo=None)

def now_local():
    """Alias para get_local_time_naive() - más fácil de usar"""
    return get_local_time_naive()

def utc_to_local(utc_datetime):
    """Convierte un datetime UTC a la zona horaria local"""
    if utc_datetime.tzinfo is None:
        utc_datetime = pytz.utc.localize(utc_datetime)
    elif utc_datetime.tzinfo != pytz.utc:
        utc_datetime = utc_datetime.astimezone(pytz.utc)
    return utc_datetime.astimezone(LOCAL_TZ)

def format_local_time(dt, format_str="%Y-%m-%d %H:%M:%S"):
    """Formatea un datetime en la zona horaria local"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.strftime(format_str)
    else:
        local_dt = dt.astimezone(LOCAL_TZ)
        return local_dt.strftime(format_str)
    
def serialize_datetime_with_timezone(dt):
    """Convierte un datetime naive a ISO string con zona horaria de Madrid"""
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # Asumir que el datetime naive está en hora de Madrid
        dt_with_tz = LOCAL_TZ.localize(dt)
        return dt_with_tz.isoformat()
    else:
        # Ya tiene zona horaria
        return dt.isoformat()
    
    