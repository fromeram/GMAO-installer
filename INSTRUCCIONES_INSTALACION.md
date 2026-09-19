# 📖 Instrucciones de Instalación Multiplataforma — GMAO System

¡Bienvenido! Esta guía te explica cómo poner en marcha el sistema GMAO en tu servidor de fábrica, en tu ordenador personal (Windows o Mac) y en los teléfonos móviles de tus técnicos en menos de 3 minutos.

---

## 🖥️ Paso 1: Elige tu Entorno de Instalación

GMAO System está 100% contenerizado con **Docker**, lo que permite desplegarlo tanto en un servidor de planta como en tu PC o portátil para ver cómo funciona.

### Opción A: Servidor Linux / Proxmox (Recomendado para Producción en Planta)
> 💡 **Nota**: No necesitas configurar nada previamente. Este comando instala automáticamente Docker, Compose y todo lo necesario en Ubuntu, Debian o Proxmox.

En la terminal de tu servidor (como `root` o con `sudo`), ejecuta:
```bash
apt update && apt install -y curl && bash <(curl -fsSL https://raw.githubusercontent.com/fromeram/GMAO-installer/main/setup.sh)
```

---

### Opción B: Windows 10 / 11 (Ideal para Pruebas en tu Ordenador)
Si eres director de fábrica, jefe de mantenimiento o técnico y quieres probar el sistema en tu PC:

1. **Requisito**: Tener instalado y abierto **[Docker Desktop para Windows](https://www.docker.com/products/docker-desktop/)** (asegúrate de marcar *"Use WSL 2"* durante la instalación).
2. **Método 1 (PowerShell en 1 línea)**: Abre PowerShell y pega:
   ```powershell
   irm https://raw.githubusercontent.com/fromeram/GMAO-installer/main/setup.ps1 | iex
   ```
3. **Método 2 (Descarga manual ZIP)**:
   - Descarga el código: [GMAO-installer ZIP](https://github.com/fromeram/GMAO-installer/archive/refs/heads/main.zip)
   - Descomprime la carpeta y haz **doble clic en `install.bat`**.
   - Se abrirá automáticamente la aplicación en tu navegador web.

---

### Opción C: macOS (Para Mac con Procesador Apple Silicon M1-M4 o Intel)
1. **Requisito**: Tener instalado y abierto **[Docker Desktop para Mac](https://www.docker.com/products/docker-desktop/)**.
2. Abre la aplicación **Terminal** en tu Mac y pega:
   ```bash
   bash <(curl -fsSL https://raw.githubusercontent.com/fromeram/GMAO-installer/main/setup.sh)
   ```

---

## 📝 Paso 2: Responde al Asistente de Fábrica

1. **IP o Host del Servidor**:
   - En servidores de fábrica: Detectará tu IP local (ej. `192.168.1.45`). Pulsa **ENTER**.
   - En Windows o Mac para pruebas: Pulsa **ENTER** para usar `localhost`.
2. **Contraseñas**: Puedes dejar las contraseñas seguras sugeridas pulsando **ENTER** o escribir las que prefieras.
3. **Servidor de Inteligencia Artificial (Ollama)**:
   - Si tienes **Ollama** funcionando para diagnósticos automáticos, escribe su dirección (ej. `http://localhost:11434` o `http://host.docker.internal:11434` en Windows).
   - Si aún no tienes Ollama, pulsa **ENTER** y podrás conectarlo cuando quieras.
4. **Estructura de Fábrica**:
   - **Plantilla Estándar (Recomendada para empezar)**: Genera almacenes, secciones, líneas y máquinas con datos industriales realistas para ver cómo funciona el sistema de inmediato.
   - **Personalizada**: Te permite dar de alta tus secciones y máquinas una a una.

---

## 🌐 Paso 3: Acceso al Panel de Control Web

Cuando concluya la instalación, el navegador se abrirá o podrás acceder en:
- **Panel Web Seguro (HTTPS)**: `https://<IP_O_LOCALHOST>`
- **Panel Web Estándar (HTTP)**: `http://<IP_O_LOCALHOST>`
- **Usuario inicial**: `admin`
- **Contraseña**: La generada en el asistente (se muestra en pantalla al finalizar).

*(En entornos locales con HTTPS autofirmado, si el navegador muestra aviso de seguridad, pulsa en "Configuración avanzada" $\rightarrow$ "Continuar a la web").*

---

## 📱 Paso 4: Instala la App en los Teléfonos Móviles de los Mecánicos

Para que los técnicos trabajen a pie de máquina escaneando códigos QR:

1. **Descarga el instalador APK en el móvil Android**:  
   👉 **[Descargar GMAOv2.2.4.apk (Última versión oficial)](https://github.com/fromeram/GMAO-installer/raw/main/android/GMAOv2.2.4.apk)**
2. Abre el archivo en el móvil e instala la app.
3. En la pantalla inicial, pulsa en **⚙️ "Configurar Servidor"** e introduce la IP de tu servidor (ejemplo: `http://192.168.1.50:8000`).
4. Pulsa **"Probar Conexión"** y **"Guardar"**. ¡Listo! Inicia sesión con las credenciales del técnico.

---

## 🛠️ Herramientas de Mantenimiento y Backups

- **En Linux / Mac**: Entra en la carpeta del programa (`cd ~/GMAO-installer`) y ejecuta `./gmao.sh` para crear copias de seguridad de la base de datos, restaurar datos o reiniciar servicios.
- **En Windows**: Haz doble clic en `uninstall.bat` si deseas detener y limpiar los contenedores.
