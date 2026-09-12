# 🏭 GMAO System - Sistema de Gestión de Mantenimiento Industrial

[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%2017-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)

**GMAO System** es una solución integral y moderna de **Gestión de Mantenimiento Asistido por Ordenador (CMMS / GMAO)** diseñada específicamente para entornos industriales y plantas de producción. 

Incluye gestión completa de activos, órdenes de trabajo (correctivas, preventivas, predictivas), gestión de almacenes y repuestos, control de técnicos, auditoría, gamificación, scheduler de tareas automáticas y soporte para modelos de Inteligencia Artificial preventiva.

---

## 🚀 Despliegue Rápido (Autoinstalable)

Este repositorio está preparado para que cualquier operador o empresa pueda desplegarlo en su propio servidor o máquina virtual en cuestión de minutos.

### 1. Clonar el repositorio
```bash
git clone https://github.com/fromeram/gmao-installer.git
cd gmao-installer
```

### 2. Dar permisos de ejecución
```bash
chmod +x install.sh gmao.sh
```

### 3. Ejecutar el asistente de instalación
```bash
./install.sh
```

---

## 🛠️ ¿Qué hace el Instalador (`install.sh`)?

El instalador interactivo te guiará paso a paso:

1. **Comprobación del Entorno**: Verifica que Docker y Docker Compose estén presentes.
2. **Configuración de Red**: Detecta automáticamente tu IP local o te permite configurar un dominio personalizado.
3. **Credenciales Personalizadas**: Te solicita o genera contraseñas seguras para la base de datos PostgreSQL y la cuenta del Administrador principal.
4. **Asistente de Estructura de Fábrica**:
   - **Almacenes de Repuestos**: Te pregunta cuántos almacenes tienes y sus nombres (ej. *Almacén Central*, *Taller*, etc.).
   - **Secciones / Áreas de Planta**: Te pregunta las secciones de tu fábrica (ej. *Mecanizado*, *Prensas*, *Envasado*).
   - **Líneas de Producción**: Para cada sección, puedes definir sus líneas.
   - **Máquinas**: Para cada línea, puedes introducir sus máquinas con Marca, Modelo, Número de Serie y Criticidad (ALTA, MEDIA, BAJA).
   - *(Opcional)*: También puedes seleccionar la opción de cargar una **plantilla industrial estándar** de prueba con un solo clic.
5. **Seguridad y SSL**: Genera automáticamente certificados SSL autofirmados para que puedas acceder por **HTTPS** de forma segura en tu red local o intranet.
6. **Arranque Automatizado**: Construye los contenedores Docker e inicializa la base de datos completa con sus **48 tablas y 82 relaciones foráneas**.

---

## 🖥️ Panel de Control y Mantenimiento (`gmao.sh`)

Para gestionar el sistema día a día sin necesidad de recordar comandos de Docker, dispones del script de administración:

```bash
./gmao.sh
```

O directamente mediante comandos rápidos:

| Comando | Descripción |
| :--- | :--- |
| `./gmao.sh status` | Muestra el estado de salud de todos los contenedores |
| `./gmao.sh start` | Inicia todos los servicios del GMAO |
| `./gmao.sh stop` | Detiene los servicios de forma ordenada |
| `./gmao.sh restart` | Reinicia los contenedores |
| `./gmao.sh logs` | Muestra los logs en tiempo real (puedes especificar `./gmao.sh logs backend`) |
| `./gmao.sh backup` | Crea un volcado completo de la base de datos en la carpeta `backups/` |
| `./gmao.sh restore` | Restaura una copia de seguridad seleccionada |

---

## 🏗️ Arquitectura del Sistema

```
gmao-installer/
├── install.sh                  # Asistente de instalación interactivo
├── gmao.sh                     # Herramienta de gestión y backups
├── docker-compose.yml          # Orquestación de servicios Docker
├── .env.example                # Plantilla de variables de entorno
├── db/
│   ├── 01_schema.sql           # Esquema completo de la BD (48 tablas, 82 relaciones)
│   └── 02_initial_data.sql     # Roles esenciales y datos de arranque
├── backend/                    # API FastAPI modularizada
│   └── src/
│       ├── main.py             # Punto de entrada de la API
│       ├── routers/            # 15 routers modulares (máquinas, órdenes, almacén, etc.)
│       └── schemas/            # Esquemas de validación Pydantic
├── frontend/                   # Interfaz de usuario en React
└── nginx/                      # Servidor web inverso y terminación SSL (HTTPS)
    └── gmao.conf               # Configuración segura y universal de Nginx
```

---

## 🧪 Cómo Probarlo en una Máquina Virtual Linux (VM)

Si deseas probar el instalador en una máquina virtual limpia (Ubuntu 22.04 / 24.04 o Debian):

1. **Instalar Docker**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose-v2 openssl git
   sudo usermod -aG docker $USER
   newgrp docker
   ```
2. **Clonar e Instalar**:
   ```bash
   git clone https://github.com/fromeram/gmao-installer.git
   cd gmao-installer
   chmod +x install.sh gmao.sh
   ./install.sh
   ```
3. **Acceder desde el navegador**:
   Abre `https://<IP_DE_TU_VM>` en tu navegador web e inicia sesión con las credenciales que hayas configurado en el asistente.

---

## 🔒 Privacidad y Seguridad

- Este repositorio **NO contiene contraseñas reales, tokens privados ni dominios personales**.
- Todas las credenciales se generan o introducen durante la ejecución de `install.sh` y se almacenan exclusivamente en el archivo local `.env` del servidor del usuario, protegido con permisos restrictivos `600`.
