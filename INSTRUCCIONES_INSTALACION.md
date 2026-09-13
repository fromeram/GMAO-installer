# 📖 Instrucciones de Instalación — GMAO System

¡Bienvenido! Esta guía te explica de forma muy sencilla cómo poner en marcha el sistema GMAO en tu empresa en solo 3 minutos.

---

## 🚀 Paso 1: El Comando Mágico (No necesitas instalar nada antes)

> 💡 **Nota importante**: No te preocupes por instalar Docker ni configurar nada manualmente en Linux. Este comando se encarga de todo el trabajo sucio por ti.

Abre la consola (terminal) de tu servidor Linux, máquina virtual o contenedor Proxmox (como usuario `root` o con permisos `sudo`) y pega esta línea:

```bash
apt update && apt install -y curl && bash <(curl -fsSL https://raw.githubusercontent.com/fromeram/GMAO-installer/main/setup.sh)
```

El instalador comprobará tu sistema, instalará Docker y descargará todo lo necesario en menos de un minuto.

---

## 📝 Paso 2: Responde a las Preguntas del Asistente

Aparecerá en tu pantalla un asistente en español muy claro:

1. **IP de la máquina**: El programa detecta la IP de tu servidor (ej. `192.168.1.45`). Solo tienes que pulsar la tecla **ENTER**.
2. **Contraseñas**: Puedes dejar que el asistente genere contraseñas seguras automáticamente pulsando **ENTER**, o escribir las tuyas personales.
3. **Servidor de Inteligencia Artificial (Ollama)**:
   - Si tienes **Ollama** funcionando para diagnósticos automáticos, escribe su dirección (ej. `http://localhost:11434` o la IP del ordenador donde esté instalado, ej. `http://192.168.1.100:11434`).
   - Si todavía no tienes Ollama instalado o quieres probar el programa sin IA por ahora, pulsa **ENTER** y podrás añadirlo más adelante cuando quieras.
4. **Estructura de Fábrica**:
   - **Opción recomendada para empezar**: Elige la **Plantilla estándar**. En un segundo te creará máquinas, almacenes y áreas industriales listas para usar y probar el programa.
   - **Opción personalizada**: Si prefieres configurarlo ya con los datos reales de tu planta, el asistente te irá pidiendo los nombres de tus almacenes, secciones y máquinas.

---

## 🌐 Paso 3: ¡Listo! Abre el Programa en tu Navegador

Cuando el instalador termine de arrancar, verás un mensaje verde de felicitación indicándote la dirección web:

- **Dirección Web (HTTPS)**: `https://<IP_DE_TU_SERVIDOR>`
- **Usuario**: `admin` (o el que hayas configurado)
- **Contraseña**: La que hayas introducido en el asistente.

> 🔒 *Al entrar por primera vez, el navegador te avisará de que el certificado de seguridad es autofirmado. Es totalmente normal en redes locales: simplemente pulsa en "Configuración avanzada" $\rightarrow$ "Continuar a la web".*

---

## 🤖 ¿Cómo añadir la Inteligencia Artificial (Ollama)?

Si quieres que el GMAO te dé diagnósticos de averías, recomiende soluciones técnicas y prediga cuándo puede fallar una máquina:

1. Instala Ollama en tu servidor o en otro ordenador de la fábrica:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
2. Descarga el modelo de inteligencia artificial:
   ```bash
   ollama run qwen2.5:7b
   ```
3. En el GMAO ya estará conectado y listo para ayudarte en cada orden de trabajo.

---

## 🌍 ¿Cómo entrar desde fuera de la fábrica (Internet o Móvil)?

Para que los técnicos puedan usar el GMAO desde su móvil o tú puedas consultarlo desde casa:

- **La mejor opción (Cloudflare Tunnel - Gratis)**:
  1. Entra en [Cloudflare.com](https://cloudflare.com) y crea un túnel gratuito en el apartado Zero Trust.
  2. Apunta el túnel al puerto `80` de tu servidor.
  3. Tendrás una dirección web pública y protegida (ej: `https://gmao.tuempresa.com`) sin tener que abrir ningún puerto en el router de tu fábrica.
- **Opción VPN (Tailscale)**:
  Instala la aplicación gratuita [Tailscale](https://tailscale.com) en el servidor y en los teléfonos móviles de los técnicos para conectaros de forma privada.

---

## ⚙️ Mantenimiento Diario (`./gmao.sh`)

Dentro de la carpeta del programa (`cd GMAO-installer`), dispones de un menú de control:

```bash
./gmao.sh
```

Desde ahí puedes hacer **copias de seguridad (backups)** de toda tu base de datos con un clic, ver si todo está funcionando o reiniciar el sistema.
