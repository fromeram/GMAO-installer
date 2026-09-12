# 🚀 Guía Rápida de Instalación - GMAO System

## ⚡ Comando Todo en Uno (Instalación 100% Automática)

En una máquina virtual o contenedor Proxmox recién creado y completamente limpio, **solo tienes que pegar esta única línea en la consola**:

```bash
apt update && apt install -y curl && bash <(curl -fsSL https://raw.githubusercontent.com/fromeram/GMAO-installer/main/setup.sh)
```

Este comando se encarga de **TODO automáticamente**:
1. Instala `curl`, `git`, `docker`, `docker-compose` y `openssl`.
2. Inicia los servicios del sistema operativo.
3. Descarga el repositorio de GitHub.
4. Abre inmediatamente el **menú interactivo** para que tú solo tengas que responder las preguntas.

---

## 📋 ¿Qué te preguntará el instalador durante el proceso?

1. **Dirección IP o Dominio del Servidor**:
   - Detecta automáticamente la IP de la máquina (por ejemplo `192.168.1.50`). Puedes pulsar `ENTER` para aceptarla o escribir un dominio/IP personalizado.
2. **Base de Datos PostgreSQL**:
   - Nombre de la base de datos (por defecto `gmao_db`).
   - Usuario (por defecto `gmao_user`).
   - Contraseña (te sugiere una segura aleatoria o puedes escribir la que quieras).
3. **Usuario Administrador del GMAO**:
   - Usuario de acceso al panel (por defecto `admin`).
   - Contraseña de acceso (te sugiere una o puedes escribir la que prefieras).
4. **Asistente de Fábrica Personalizada (Estructura de Planta)**:
   - **Opción 1**: Configurar interactivamente:
     - Te pregunta cuántos **almacenes de repuestos** tienes y sus nombres.
     - Te pregunta las **secciones o áreas de producción** de tu fábrica.
     - Para cada sección, te pregunta las **líneas de producción**.
     - Para cada línea, te pregunta las **máquinas** (Nombre, Marca, Modelo, Número de Serie y Criticidad).
   - **Opción 2** *(Recomendada para pruebas rápidas)*: Carga una plantilla estándar industrial de ejemplo con secciones, líneas y máquinas ya listas.
   - **Opción 3**: Estructura mínima para dar de alta los activos más tarde desde la aplicación web.

---

## 🌐 Acceso al Sistema

Una vez finalizado el instalador:
- **Panel Web (HTTPS)**: `https://<IP_DE_TU_SERVIDOR>`
- **Documentación API**: `https://<IP_DE_TU_SERVIDOR>/api/docs`
- **Login Inicial**: Con el usuario y contraseña que configuraste en el paso 3.

---

## 🛠️ Panel de Mantenimiento (`gmao.sh`)

Para gestionar el sistema día a día:
```bash
./gmao.sh
```
O con comandos directos:
- `./gmao.sh status`  $\rightarrow$ Ver salud de los contenedores
- `./gmao.sh logs`    $\rightarrow$ Ver registros en tiempo real
- `./gmao.sh backup`  $\rightarrow$ Crear copia de seguridad completa de la BD
- `./gmao.sh restore` $\rightarrow$ Restaurar una copia de seguridad
- `./gmao.sh restart` $\rightarrow$ Reiniciar el sistema
