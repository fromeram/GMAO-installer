# 🏭 GMAO System — Plataforma Integral de Mantenimiento Industrial

[![License: Proprietary](https://img.shields.io/badge/Licencia-Prueba_Gratuita_3_Meses-blue.svg)](https://github.com/fromeram/GMAO-installer)
[![Docker: Pre-built](https://img.shields.io/badge/Docker-Imágenes_Listas_(GHCR)-success.svg)](https://github.com/fromeram/GMAO-installer/pkgs/container/gmao-backend)
[![Seguridad: RSA-2048](https://img.shields.io/badge/Seguridad-RSA_2048_Machine_ID-orange.svg)](https://github.com/fromeram/GMAO-installer)
[![AI: Ollama Ready](https://img.shields.io/badge/IA-Ollama_Local_&_Privada-purple.svg)](https://ollama.com)

**GMAO System** es una solución profesional de **Gestión de Mantenimiento Asistido por Ordenador (GMAO / CMMS)** diseñada para fábricas, plantas industriales e instalaciones técnicas. 

Permite controlar todo el ciclo de vida de los activos industriales: órdenes de trabajo correctivas y preventivas, gamificación para técnicos, gestión de almacén con control de stock de repuestos, matriz de criticidad, mantenimiento legal con certificados, códigos QR para máquinas y asistencia con **Inteligencia Artificial local**.

---

## ⚡ Instalación en 1 Solo Paso (No necesitas instalar nada previamente)

> 💡 **No hace falta que instales Docker, ni Git, ni nada antes.**  
> El instalador automático se encarga de instalar todas las herramientas necesarias por ti.

En cualquier servidor Linux, máquina virtual (Ubuntu / Debian) o contenedor Proxmox limpio, ejecuta como usuario **root** (o con `sudo`):

```bash
apt update && apt install -y curl && bash <(curl -fsSL https://raw.githubusercontent.com/fromeram/GMAO-installer/main/setup.sh)
```

### ¿Qué hace este comando automáticamente?
1. ⚙️ Detecta tu sistema e instala **Docker**, **Docker Compose**, **Git** y herramientas de seguridad.
2. 📥 Descarga los scripts de arranque y orquestación.
3. 🚀 Descarga las imágenes del sistema pre-compiladas y listas para usar.
4. 📋 Abre un **asistente visual interactivo en pantalla** que te hace preguntas sencillas para dejar la fábrica lista.

---

## 📋 ¿Qué te preguntará el Asistente de Configuración?

El instalador te guiará paso a paso en español con preguntas muy sencillas:

1. **Dirección IP del Servidor**: Detecta la IP local de tu máquina (por ejemplo `192.168.1.50`). Solo pulsas `ENTER` para aceptarla.
2. **Contraseña de Base de Datos y Administrador**: Te propone contraseñas seguras automáticamente o puedes escribir las que tú quieras.
3. **Servidor de Inteligencia Artificial (Ollama)**:
   - Te preguntará la dirección IP del servidor donde tengas instalado Ollama.
   - Si aún no tienes IA o prefieres probar el programa primero, simplemente pulsas `ENTER` y podrás configurarla en cualquier momento más adelante.
4. **Estructura de tu Fábrica**:
   - **Opción rápida**: Cargar una plantilla industrial completa con máquinas, secciones y almacenes de ejemplo listos para probar en 1 segundo.
   - **Opción guiada**: Escribir tus propios almacenes, secciones (ej. *Línea 1, Envasado, Calderas*) y las máquinas de cada línea.

Al terminar, el sistema arrancará de inmediato y te mostrará la dirección web para entrar desde cualquier navegador.

---

## 🤖 Inteligencia Artificial Industrial (Mantenimiento Predictivo y Asistente)

El sistema integra un asistente de Inteligencia Artificial capaz de analizar el histórico de averías, diagnosticar fallos mecánicos/eléctricos y sugerir los repuestos necesarios en lenguaje natural.

### 🔒 100% Privada y Local (Tus datos no salen a Internet)
La IA funciona mediante **[Ollama](https://ollama.com)**, lo que garantiza que ningún dato industrial, fallo o documento de tu fábrica viaje a servidores externos.

### 📌 ¿Dónde se instala Ollama?
Puedes tener Ollama instalado en dos sitios según la potencia de tus equipos:
- **En el mismo servidor que el GMAO**: Si tu servidor tiene suficiente memoria RAM (8GB - 16GB o más).
- **En otro PC o servidor dedicado**: Si tienes otro ordenador en la red de la fábrica con tarjeta gráfica (GPU) o más potencia, puedes instalar Ollama allí y el GMAO se conectará a través de la red local introduciendo su dirección IP (ejemplo: `http://192.168.1.100:11434`).

#### Para instalar Ollama en 1 minuto:
```bash
# 1. Instalar Ollama en Linux
curl -fsSL https://ollama.com/install.sh | sh

# 2. Descargar el modelo recomendado (bueno, rápido y preciso)
ollama run qwen2.5:7b
# O para equipos con muchos recursos:
ollama run qwen2.5-coder:14b
```

---

## 🌍 ¿Cómo acceder al GMAO desde fuera de la Fábrica (Internet / Móvil)?

Si los técnicos o responsables necesitan consultar el GMAO desde su teléfono móvil, desde casa o desde otra delegación fuera de la red local, dispones de **3 formas seguras**:

### 🥇 Opción 1: Cloudflare Tunnel (Recomendada — Gratis, fácil y sin abrir puertos)
Es la opción más moderna y segura de la industria:
- **No necesitas tocar el router de la fábrica ni abrir ningún puerto**.
- Te proporciona un enlace web seguro con candado verde (`https://mantenimiento.tudominio.com`).
- Protege el servidor contra ataques informáticos.

**Pasos rápidos:**
1. Crea una cuenta gratuita en [Cloudflare.com](https://cloudflare.com).
2. Ve a **Zero Trust** $\rightarrow$ **Networks** $\rightarrow$ **Tunnels** $\rightarrow$ **Create a Tunnel**.
3. Elige **Cloudflared (Linux)** y copia el comando que te da Cloudflare en la consola de tu servidor GMAO.
4. En la configuración del túnel, apunta a `http://localhost:80` (o `https://localhost:443`). ¡Listo! Ya puedes acceder desde cualquier parte del mundo.

### 🥈 Opción 2: VPN Privada (Tailscale o WireGuard — Máxima privacidad)
Si solo quieres que entren personas autorizadas sin exponer nada a Internet:
1. Instala **[Tailscale](https://tailscale.com)** en el servidor del GMAO y en los móviles/portátiles de los técnicos.
2. Cada dispositivo recibe una IP segura privada.
3. Podrás entrar al GMAO desde el móvil en la calle escribiendo esa IP en el navegador como si estuvieras dentro de la fábrica.

### 🥉 Opción 3: Apertura de Puertos en el Router (Port Forwarding clásico)
1. Entra al router de tu operador de Internet.
2. Abre y redirige los puertos **80** (HTTP) y **443** (HTTPS) hacia la dirección IP local de tu servidor GMAO.
3. Si no tienes IP pública fija, utiliza un servicio gratuito de DNS dinámico como **DuckDNS** o **No-IP**.

---

## 🎁 Periodo de Prueba Gratuito de 3 Meses (100% Funcional)

Para que puedas implantar el software en tu empresa con total tranquilidad, cargues tus máquinas y compruebes el ahorro de tiempo y costes:

- ✅ **90 días de prueba gratuita** desde el momento de la instalación.
- ✅ **Todas las funciones desbloqueadas**: Sin límites de máquinas, usuarios, órdenes de trabajo, técnicos ni almacenes.
- ✅ **Sin tarjeta de crédito ni compromisos**: Al terminar los 3 meses, el sistema se pausa a la espera de una clave de activación. Tus datos quedan guardados y protegidos intactos en tu base de datos.

### 🔑 Activación de Licencia Permanente
En cualquier momento puedes pulsar en el distintivo de licencia en la barra superior del programa:
1. Te mostrará el **ID Único de tu Máquina (Machine ID)**.
2. Escríbenos a través de GitHub o correo electrónico para solicitar tu clave de licencia.
3. Pega la clave recibida en la ventana y el sistema quedará activado de por vida.

---

## 🛠️ Comandos de Administración del Sistema (`gmao.sh`)

En la carpeta donde se instaló el programa dispones de un centro de control muy fácil de usar:

```bash
./gmao.sh
```

Abre un menú interactivo para gestionar el programa, o puedes usar comandos rápidos directos:

| Comando | Para qué sirve |
| :--- | :--- |
| `./gmao.sh status` | Comprueba si todos los servicios están funcionando correctamente |
| `./gmao.sh start` | Enciende el programa |
| `./gmao.sh stop` | Apaga el programa de forma limpia |
| `./gmao.sh restart` | Reinicia todos los servicios |
| `./gmao.sh logs` | Muestra en pantalla lo que está ocurriendo (útil para diagnósticos) |
| `./gmao.sh backup` | **Crea una copia de seguridad completa** de todos tus datos en la carpeta `backups/` |
| `./gmao.sh restore` | Restaura una copia de seguridad anterior en caso de emergencia |
| `./gmao.sh build` | Actualiza los contenedores a la última versión disponible |

---

## 📦 Arquitectura del Software (Listo para Producción)

El software se distribuye mediante imágenes Docker pre-compiladas y optimizadas alojadas en **GitHub Container Registry (GHCR)**:

```
GMAO-installer/
├── setup.sh                  # Instalador 1-click automático
├── install.sh                # Asistente de configuración de fábrica
├── gmao.sh                   # Panel de administración y copias de seguridad
├── docker-compose.yml        # Orquestación con imágenes oficiales de GHCR
├── .env.example              # Plantilla de variables de entorno
├── nginx/                    # Proxy inverso seguro Nginx con soporte SSL
└── db/                       # Estructura de base de datos industrial (48 tablas, 82 relaciones)
```

- **Backend**: API modular de alto rendimiento (FastAPI, Python 3.10) con firma criptográfica RSA-2048.
- **Frontend**: Panel de control interactivo para técnicos y jefes de planta (React, Ant Design).
- **Base de Datos**: PostgreSQL 17 optimizado para entornos industriales.
- **Servidor Web**: Nginx con compresión gzip, terminación SSL y cabeceras de seguridad.

---

## 💬 Soporte y Contacto

¿Tienes dudas durante la instalación, necesitas una adaptación a medida para tu planta o deseas solicitar una licencia permanente?
- **Autor**: Fran Romera
- **GitHub**: [github.com/fromeram](https://github.com/fromeram)
