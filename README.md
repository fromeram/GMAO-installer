# 🏭 GMAO System — Software de Gestión de Mantenimiento Industrial (CMMS)

[![License: Proprietary](https://img.shields.io/badge/Licencia-Prueba_Gratuita_3_Meses-blue.svg)](https://github.com/fromeram/GMAO-installer)
[![Docker: Pre-built](https://img.shields.io/badge/Docker-Imágenes_Listas_(GHCR)-success.svg)](https://github.com/fromeram/GMAO-installer/pkgs/container/gmao-backend)
[![Android App](https://img.shields.io/badge/📲_Android_App-v2.2.1_(Descarga_Directa)-brightgreen.svg)](https://github.com/fromeram/GMAO-installer/raw/main/android/GMAOv2.2.1.apk)
[![Seguridad: RSA-2048](https://img.shields.io/badge/Seguridad-RSA_2048_Machine_ID-orange.svg)](https://github.com/fromeram/GMAO-installer)
[![AI: Ollama Ready](https://img.shields.io/badge/IA-Ollama_Local_&_Privada-purple.svg)](https://ollama.com)

**GMAO System** es una plataforma integral de **Gestión de Mantenimiento Asistido por Ordenador (GMAO / CMMS)** diseñada para plantas de producción, fábricas e instalaciones técnicas industriales. 

Permite digitalizar y optimizar el ciclo de vida completo de los activos de fábrica:
- 📋 **Órdenes de Trabajo**: Correctivas, preventivas, predictivas y de mejora con asignación de técnicos y tiempos.
- 📱 **App Móvil Android Nativa**: Para que los técnicos operen a pie de máquina escaneando códigos QR, reportando averías y adjuntando fotografías.
- 📦 **Gestión de Repuestos y Almacenes**: Control de stock mínimo, alertas de rotura de inventario y trazabilidad de piezas por máquina.
- 🏆 **Gamificación Técnica**: Sistema de puntos, niveles, logros y ranking para motivar al equipo de mantenimiento.
- 🤖 **Inteligencia Artificial Predictiva (Ollama)**: Diagnóstico automático de fallos, estimación de probabilidad de averías y asistente técnico local privado.
- ⚖️ **Mantenimiento Legal y Preventivo**: Calendario anual, checklist normativo y registro de auditorías.

---

## 📲 App Móvil Android para Técnicos (Descarga Directa)

Para que los mecánicos y electricistas trabajen directamente en planta desde su teléfono móvil o tablet:

[![Descargar APK Android](https://img.shields.io/badge/📲_DESCARGAR_APP_ANDROID_(APK)-VERSIÓN_2.2.1-success?style=for-the-badge&logo=android)](https://github.com/fromeram/GMAO-installer/raw/main/android/GMAOv2.2.1.apk)

> 👉 **Enlace directo de descarga**: [Descargar GMAOv2.2.1.apk](https://github.com/fromeram/GMAO-installer/raw/main/android/GMAOv2.2.1.apk) *(Solo 9.2 MB)*

### Cómo ponerla en marcha en 30 segundos:
1. Descarga e instala el archivo `.apk` en cualquier móvil o tablet Android (permite la instalación de aplicaciones de origen desconocido si el móvil te lo pide).
2. Abre la aplicación y pulsa en **⚙️ "Configurar Servidor"** en la pantalla de inicio.
3. Escribe la dirección IP o dominio de tu servidor GMAO (ejemplo: `http://192.168.1.50:8000` o `https://gmao.tuempresa.com`).
4. Pulsa **"Probar Conexión"** para verificar que conecta y luego **"Guardar y Usar"**.
5. Inicia sesión con tu usuario técnico. ¡Ya puedes escanear códigos QR en las máquinas y gestionar órdenes desde cualquier rincón de la fábrica!

---

## ⚡ Instalación del Servidor en 1 Solo Paso (Automática)

> 💡 **No necesitas instalar Docker, Git ni configurar nada previamente.**  
> El instalador automático se encarga de instalar todas las dependencias del sistema por ti.

En cualquier servidor Linux, máquina virtual (Ubuntu 22.04 / 24.04 o Debian) o contenedor Proxmox limpio, ejecuta como usuario **root** (o con `sudo`):

```bash
apt update && apt install -y curl && bash <(curl -fsSL https://raw.githubusercontent.com/fromeram/GMAO-installer/main/setup.sh)
```

### ¿Qué hace este comando automáticamente?
1. ⚙️ Instala **Docker**, **Docker Compose**, **Git** y utilidades criptográficas.
2. 📥 Descarga la estructura del sistema y los scripts de gestión.
3. 🚀 Descarga las imágenes oficiales de producción desde **GitHub Container Registry (GHCR)**.
4. 📋 Abre un **asistente interactivo en español** que te hace preguntas sencillas para dejar tu fábrica configurada en 2 minutos.

---

## 📋 ¿Qué te preguntará el Asistente de Instalación?

1. **Dirección IP del Servidor**: Detecta la IP local de tu servidor (ej. `192.168.1.50`). Pulsa `ENTER` para confirmarla.
2. **Contraseñas**: Genera contraseñas seguras automáticamente o puedes introducir las que prefieras.
3. **Servidor de Inteligencia Artificial (Ollama)**:
   - Te pide la IP donde corre Ollama (ej. `http://localhost:11434` o `http://192.168.1.100:11434`).
   - Si aún no tienes IA o quieres probar el sistema primero, pulsa `ENTER` y podrás activarla en cualquier momento posterior.
4. **Estructura de Fábrica**:
   - **Plantilla estándar industrial**: Crea máquinas, secciones y almacenes de ejemplo en 1 segundo para probar el programa de inmediato.
   - **Estructura personalizada**: Puedes escribir tus almacenes reales, secciones de producción (ej. *Línea 1, Envasado, Calderas*) y las máquinas de cada línea.

---

## 🤖 Módulo de Inteligencia Artificial Local (Ollama)

El sistema incorpora un asistente de IA especializado en mantenimiento industrial capaz de diagnosticar fallos, sugerir repuestos y estimar la probabilidad de rotura de cada activo según su histórico.

- **100% Privada y Local**: Funciona con **[Ollama](https://ollama.com)**. Ningún dato técnico ni documento de tu empresa se envía a servidores externos en la nube.
- **Flexibilidad de despliegue**: Puede estar instalado en el **mismo servidor** del GMAO o en **otro ordenador/servidor de la red** que disponga de mayor potencia o tarjeta gráfica (GPU).

```bash
# 1. Instalar Ollama en Linux
curl -fsSL https://ollama.com/install.sh | sh

# 2. Descargar el modelo de IA recomendado (muy rápido y preciso)
ollama run qwen2.5:7b
```

---

## 🌍 Acceso Remoto desde Fuera de la Fábrica (Móvil / Internet)

Si los técnicos o directores necesitan acceder al GMAO desde fuera de la red local o desde su casa:

1. **Cloudflare Tunnel (Recomendada — Gratis y sin abrir puertos)**:
   - Conecta el GMAO a un dominio seguro con candado verde (`https://mantenimiento.tudominio.com`).
   - No requiere tocar el router de la fábrica ni abrir ningún puerto.
   - Protege el servidor contra accesos no autorizados.
2. **VPN Privada (Tailscale / WireGuard)**:
   - Instala la app gratuita [Tailscale](https://tailscale.com) en el servidor y en los teléfonos de los técnicos para acceder de forma segura y privada.
3. **Redirección de Puertos (Port Forwarding)**:
   - Redirigir los puertos 80 y 443 del router hacia la IP local del servidor con un servicio de DNS dinámico (DuckDNS / No-IP).

---

## 🎁 Periodo de Prueba Gratuito de 3 Meses (100% Funcional)

- ✅ **90 días de evaluación completa** desde el momento de la instalación.
- ✅ **Sin limitaciones**: Máquinas ilimitadas, usuarios ilimitados, órdenes de trabajo, almacén y módulo de IA activados al 100%.
- ✅ **Sin tarjeta de crédito**: Al terminar los 3 meses, el sistema se pausa a la espera de una clave de activación. Tus datos quedan intactos y guardados con seguridad en la base de datos PostgreSQL.

### Activación Permanente
En cualquier momento puedes pulsar en el distintivo de licencia en la barra superior de la aplicación para ver el **ID Único de tu Servidor (Machine ID)** y solicitar tu clave de activación permanente.

---

## 🛠️ Panel de Mantenimiento Diario (`gmao.sh`)

En la carpeta donde se instala el programa dispones de un menú de control rápido:

```bash
./gmao.sh
```

| Comando | Acción |
| :--- | :--- |
| `./gmao.sh status` | Comprueba la salud y estado de los contenedores |
| `./gmao.sh start` | Inicia los servicios del GMAO |
| `./gmao.sh stop` | Detiene el sistema de forma limpia |
| `./gmao.sh restart` | Reinicia todos los servicios |
| `./gmao.sh logs` | Muestra los registros y eventos en tiempo real |
| `./gmao.sh backup` | **Crea una copia de seguridad completa** de la base de datos en la carpeta `backups/` |
| `./gmao.sh restore` | Restaura una copia de seguridad anterior |
| `./gmao.sh build` | Actualiza el sistema a la última versión disponible |

---

## 💬 Contacto y Soporte

¿Deseas solicitar una licencia comercial permanente, soporte para la implantación en tu planta o adaptaciones a medida?
- **Desarrollador**: Fran Romera
- **GitHub**: [github.com/fromeram](https://github.com/fromeram)
