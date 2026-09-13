# 📖 Instrucciones de Instalación — GMAO System

¡Bienvenido! Esta guía te explica cómo poner en marcha el sistema GMAO en tu fábrica y en los teléfonos móviles de tus técnicos en menos de 3 minutos.

---

## 🚀 Paso 1: Instalación del Servidor (Comando Todo en Uno)

> 💡 **Nota**: No te preocupes por instalar Docker ni configurar nada manualmente en Linux. Este comando instala automáticamente todo lo necesario.

En la consola de tu servidor Linux, máquina virtual o contenedor Proxmox (como usuario `root` o con `sudo`), pega esta única línea:

```bash
apt update && apt install -y curl && bash <(curl -fsSL https://raw.githubusercontent.com/fromeram/GMAO-installer/main/setup.sh)
```

El instalador preparará el sistema y abrirá el asistente interactivo de configuración.

---

## 📝 Paso 2: Responde al Asistente de Fábrica

1. **IP del Servidor**: El programa detecta la IP de tu máquina (ej. `192.168.1.45`). Pulsa **ENTER**.
2. **Contraseñas**: Puedes dejar las contraseñas seguras automáticas pulsando **ENTER** o escribir las tuyas.
3. **Servidor de Inteligencia Artificial (Ollama)**:
   - Si tienes **Ollama** funcionando para diagnósticos automáticos, escribe su dirección (ej. `http://localhost:11434` o la IP de tu equipo con IA).
   - Si todavía no tienes Ollama instalado, pulsa **ENTER** y podrás añadirlo más adelante cuando quieras.
4. **Estructura de Fábrica**:
   - **Plantilla Estándar (Recomendada para empezar)**: Te crea máquinas, almacenes y áreas industriales listas para usar y probar el programa al instante.
   - **Personalizada**: Puedes introducir tus secciones y máquinas reales una a una.

---

## 🌐 Paso 3: Accede desde el Navegador

Cuando termine la instalación:
- **Panel Web (HTTPS)**: `https://<IP_DE_TU_SERVIDOR>`
- **Usuario inicial**: `admin`
- **Contraseña**: La que hayas introducido en el asistente.

*(Si el navegador muestra advertencia de certificado autofirmado en la red local, pulsa en "Configuración avanzada" $\rightarrow$ "Continuar a la web").*

---

## 📱 Paso 4: Instala la App en los Móviles de los Técnicos

Para que los mecánicos y electricistas trabajen a pie de máquina escaneando códigos QR:

1. **Descarga el archivo APK en el teléfono**:  
   👉 [Descargar GMAOv2.2.2.apk](https://github.com/fromeram/GMAO-installer/raw/main/android/GMAOv2.2.2.apk)
2. Instala la aplicación en el móvil Android.
3. Pulsa en **⚙️ "Configurar Servidor"** en la pantalla de inicio y escribe la IP de tu servidor GMAO (ejemplo: `http://192.168.1.50:8000`).
4. Pulsa **"Probar Conexión"** y **"Guardar"**. ¡Listo! Inicia sesión con tu usuario.

---

## ⚙️ Mantenimiento Diario y Backups (`./gmao.sh`)

Dentro de la carpeta del programa (`cd GMAO-installer`), ejecuta:

```bash
./gmao.sh
```

- **Opción 6**: Crea una copia de seguridad (backup) completa de todos tus datos en la carpeta `backups/`.
- **Opción 7**: Restaura una copia de seguridad anterior.
- **Opción 1**: Comprueba que todos los servicios estén activos.
