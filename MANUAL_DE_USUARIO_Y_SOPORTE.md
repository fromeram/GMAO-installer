# 📖 MANUAL INTEGRAL DE USUARIO, INSTALACIÓN Y RESOLUCIÓN DE PROBLEMAS
## Sistema GMAO — Gestión de Mantenimiento Asistido por Ordenador
**Edición Industrial — Adaptado a Plantas de Producción, Cartón y Envases, Cerámica y Manufactura**  
**Autor y Titular de Derechos:** Fran Romera  
**Copyright:** © 2024–2026 Fran Romera. Todos los derechos reservados. Prohibida su copia o distribución ilegal.  
**Versión del Sistema:** 2.2.3  
**Fecha de Publicación:** Septiembre 2026  

---

## 📑 ÍNDICE GENERAL

1. [Introducción y Arquitectura del Sistema](#1-introducción-y-arquitectura-del-sistema)
2. [Guía de Instalación y Puesta en Marcha](#2-guía-de-instalación-y-puesta-en-marcha)
   - 2.1 [Requisitos del Servidor y Entorno](#21-requisitos-del-servidor-y-entorno)
   - 2.2 [Instalación Automática del Servidor (install.sh)](#22-instalación-automática-del-servidor-installsh)
   - 2.3 [Instalación y Configuración de la App Android](#23-instalación-y-configuración-de-la-app-android)
   - 2.4 [Verificación de Servicios y Salud del Sistema](#24-verificación-de-servicios-y-salud-del-sistema)
3. [Roles de Usuario y Matriz de Permisos](#3-roles-de-usuario-y-matriz-de-permisos)
4. [Manual de Uso Operativo por Módulos](#4-manual-de-uso-operativo-por-módulos)
   - 4.1 [Estructura de Planta, Líneas y Máquinas (Info Planta)](#41-estructura-de-planta-líneas-y-máquinas-info-planta)
   - 4.2 [Catálogo de Máquinas, Historial, BOM y Códigos QR](#42-catálogo-de-máquinas-historial-bom-y-códigos-qr)
   - 4.3 [Órdenes de Trabajo (OTs) y Partes de Mantenimiento](#43-órdenes-de-trabajo-ots-y-partes-de-mantenimiento)
   - 4.4 [Mantenimiento Preventivo, Tareas Periódicas y Plan Anual](#44-mantenimiento-preventivo-tareas-periódicas-y-plan-anual)
   - 4.5 [Mantenimiento Legal y Normativo (Inspecciones Oficiales)](#45-mantenimiento-legal-y-normativo-inspecciones-oficiales)
   - 4.6 [Gestión de Inventario, Repuestos, Almacenes y Proveedores](#46-gestión-de-inventario-repuestos-almacenes-y-proveedores)
   - 4.7 [Gestión de Turnos, Cuadrantes y Solicitudes de Vacaciones](#47-gestión-de-turnos-cuadrantes-y-solicitudes-de-vacaciones)
   - 4.8 [Módulo de Comunicaciones Internas (Buzón Operario-Admin)](#48-módulo-de-comunicaciones-internas-buzón-operario-admin)
   - 4.9 [Gamificación, Puntos y Logros de Personal](#49-gamificación-puntos-y-logros-de-personal)
   - 4.10 [Inteligencia Artificial: Predicción, Chat Técnico y Procesamiento Documental](#410-inteligencia-artificial-predicción-chat-técnico-y-procesamiento-documental)
5. [Administración del Sistema y Automatización](#5-administración-del-sistema-y-automatización)
   - 5.1 [Motor de Tareas Programadas (Scheduler)](#51-motor-de-tareas-programadas-scheduler)
   - 5.2 [Notificaciones por Correo Electrónico (SMTP)](#52-notificaciones-por-correo-electrónico-smtp)
   - 5.3 [Copias de Seguridad (Backup) y Restauración de Base de Datos](#53-copias-de-seguridad-backup-y-restauración-de-base-de-datos)
6. [Guía Exhaustiva de Resolución de Problemas (Troubleshooting)](#6-guía-exhaustiva-de-resolución-de-problemas-troubleshooting)

---

## 1. INTRODUCCIÓN Y ARQUITECTURA DEL SISTEMA

El **Sistema GMAO** es una plataforma integral de mantenimiento asistido por ordenador diseñada para maximizar la fiabilidad, disponibilidad y vida útil de los equipos en plantas industriales de proceso continuo y manufactura: fábricas de cajas de cartón ondulado y packaging, plantas cerámicas, líneas de envasado, inyección de plástico y manufactura pesada (formadoras automáticas de cartón, trenes de rodillos transportadores, robots de paletizado, enfardadoras de film, prensas hidráulicas, hornos industriales, secaderos y centros de transformación).

### Arquitectura Técnica
```
       ┌─────────────────────────────────────────────────────────┐
       │                    USUARIOS / CLIENTES                  │
       │     Navegador Web (React)   /   App Android Nativa      │
       └───────────┬─────────────────────────────────┬───────────┘
                   │ HTTPS (443)                     │ HTTPS (443) / API (8000)
       ┌───────────▼─────────────────────────────────▼───────────┐
       │                 NGINX REVERSE PROXY                     │
       │    Terminación SSL (Certificados) + Servidor Estático   │
       └───────────────────────────┬─────────────────────────────┘
                                   │ Proxy HTTP interna
       ┌───────────────────────────▼─────────────────────────────┐
       │             FASTAPI BACKEND (Python 3.10)               │
       │  • Lógica de Negocio   • Autenticación JWT              │
       │  • Motor de Tareas     • Auditoría de Cambios           │
       └─────────────┬─────────────────────────────┬─────────────┘
                     │                             │
       ┌─────────────▼─────────────┐ ┌─────────────▼─────────────┐
       │  POSTGRESQL 17 (Database) │ │ OLLAMA (Servidor de IA)   │
       │   Datos, Relaciones, OTs  │ │ Predicción + Chat Técnico │
       └───────────────────────────┘ └───────────────────────────┘
```

---

## 2. GUÍA DE INSTALACIÓN Y PUESTA EN MARCHA

### 2.1 Requisitos del Servidor y Entorno

* **Servidor Físico / Máquina Virtual / Contenedor Proxmox (LXC):**
  * **Sistema Operativo:** Ubuntu 22.04 / 24.04 LTS o Debian 12 (Linux 64-bit).
  * **CPU:** 2 núcleos mínimo (4 núcleos recomendados si se procesan documentos).
  * **Memoria RAM:** 4 GB mínimo (8 GB recomendados).
  * **Almacenamiento:** 25 GB de espacio libre en disco (SSD preferible).
  * **Puertos de red libres:** `80` (HTTP), `443` (HTTPS), `8000` (API Backend opcional para app móvil directa), `5432` (PostgreSQL interno).
  * **Software base necesario:** Docker Engine y Docker Compose v2 (el instalador los descarga si no existen).

### 2.2 Instalación Automática del Servidor (`install.sh`)

El instalador automatizado permite desplegar el sistema desde cero en pocos minutos.

#### Paso 1: Clonar o descargar el instalador
En la consola del servidor (como usuario `root` o con privilegios `sudo`):
```bash
cd /root
git clone https://github.com/fromeram/GMAO-installer.git gmao-installer
cd gmao-installer
chmod +x install.sh
```

#### Paso 2: Ejecutar el script interactivo
```bash
./install.sh
```

#### Paso 3: Asistente interactivo paso a paso
El instalador solicitará los siguientes datos:
1. **Detección de IP:** Mostrará las interfaces de red detectadas (por ejemplo, `192.168.1.16`). Acepta la IP sugerida o introduce la IP estática deseada.
2. **Nombre de la Fábrica / Base de Datos:** Introduce el nombre de la instalación (ejemplo: `mimas`). Solo letras, números y guiones bajos.
3. **Estructura Inicial de Planta:**
   * ¿Deseas inicializar la planta con secciones de prueba? Si respondes que sí, te preguntará:
     * *Número de secciones* (ejemplo: `3`).
     * *Número de líneas por sección* (ejemplo: `1`).
     * *Número de máquinas por línea* (ejemplo: `1`).
   * *Validación de seguridad:* El instalador valida estrictamente que solo se introduzcan números enteros positivos.
4. **Credenciales de Administrador:**
   * Usuario administrador inicial (por defecto: `Admin`).
   * Contraseña de acceso (por defecto: `Francisco`).
5. **Configuración de Ollama (IA):**
   * Introduce la IP del servidor de modelos IA (por ejemplo: `192.168.1.62:11434`) o pulsa Enter para omitir.

#### Paso 4: Finalización del Despliegue
El instalador creará el directorio `/root/gmao-project`, generará los certificados SSL, descargará las imágenes oficiales de Docker (`ghcr.io/fromeram/gmao-backend` y `ghcr.io/fromeram/gmao-frontend`), creará la base de datos PostgreSQL 17 y dejará el sistema arrancado.

### 2.3 Instalación y Configuración de la App Android

1. **Descargar la APK:**
   * Accede desde el navegador móvil a la página de bienvenida de tu servidor:  
     `https://<IP-DEL-SERVIDOR>/`  
     O descarga directamente **`GMAOv2.2.3.apk`** desde el repositorio oficial de GitHub:  
     `https://github.com/fromeram/GMAO-installer/raw/main/android/GMAOv2.2.3.apk`
2. **Habilitar orígenes desconocidos:**
   * En los Ajustes de Android, autoriza a Chrome o al explorador de archivos a «Instalar aplicaciones desconocidas».
3. **Instalar y Abrir la App:**
   * Abre `GMAOv2.2.3.apk` y confirma la instalación.
4. **Configurar la Conexión en la Pantalla de Login:**
   * En la parte inferior de la pantalla de acceso, pulsa en **«Configuración de Servidor»** (icono de engranaje).
   * Selecciona o escribe la URL del servidor:  
     * Para red local con API directa: `http://192.168.1.16:8000/` o `https://192.168.1.16/`
   * Pulsa **«Probar Conexión»** para verificar el estado de la red.
   * La app cuenta con soporte integrado para certificados SSL autofirmados, garantizando la conexión en redes locales seguras.
5. **Iniciar Sesión:**
   * Introduce usuario y contraseña (por ejemplo, `Admin` / `Francisco`).

### 2.4 Verificación de Servicios y Salud del Sistema

Desde el terminal del servidor, puedes verificar el estado de los contenedores con:
```bash
docker ps
```
Deberás ver los tres contenedores principales:
* `gmao-project-nginx`: Estado `Up` (puertos 80 y 443).
* `gmao-project-backend`: Estado `Up (healthy)` (puerto 8000).
* `gmao-project-db`: Estado `Up (healthy)` (puerto 5432).

Para comprobar el endpoint de salud de la API:
```bash
curl -s http://localhost:8000/health
# Respuesta esperada: {"status":"ok"}
```

---

## 3. ROLES DE USUARIO Y MATRIZ DE PERMISOS

El sistema implementa un modelo de seguridad basado en roles (RBAC) con visibilidad segregada:

| Rol | Alcance de Visualización | Acceso a OTs | Inventario y Compras | Turnos y Personal | Módulo IA y Ajustes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Administrador** | Toda la fábrica | Total (Crear, Asignar, Cerrar, Borrar) | Total (Modificar precios, Crear repuestos) | Total (Aprobar vacaciones, Asignar cuadrantes) | Total |
| **Jefe de Mantenimiento** | Toda la fábrica | Total (Planificación, Validación) | Consulta y solicitud | Gestión de turnos y validación de vacaciones | Total |
| **Jefe de Sección** | Su sección asignada | Crear avisos, validar trabajos de su sección | Consulta de stock | Consulta de cuadrante de su sección | Consulta |
| **Mecánico / Operario** | Tareas asignadas | Ejecutar OTs, imputar horas y repuestos | Consulta y consumo de stock en OT | Solicitud de vacaciones personales | Chat Asistente |
| **Calidad** | Procesos y normativas | Verificación de estándares y formatos | Consulta | Consulta | Consulta |
| **Contabilidad** | Costes y proveedores | Auditoría de costes por máquina y sección | Precios, proveedores y facturación | Consulta | Sin acceso |

---

## 4. MANUAL DE USO OPERATIVO POR MÓDULOS

### 4.1 Estructura de Planta, Líneas y Máquinas (`/info-planta`)
La fábrica se estructura de forma jerárquica en tres niveles:
1. **Secciones:** Áreas principales de la planta (ej.: *Prensas*, *Hornos*, *Esmaltadoras*, *Rectificado y Pulido*, *Clasificación*, *Servicios Generales*).
2. **Líneas:** Divisiones operativas dentro de cada sección (ej.: *Línea 1*, *Línea 2*, *Compresores*, *Grupos Electrógenos*).
3. **Máquinas:** Equipos físicos individuales con número de serie, marca, modelo y estado operativo.

* **Cómo agregar una Sección/Línea:**  
  Accede a `Configuración de Planta` -> `Añadir Sección`. Introduce el nombre descriptivo y pulsa guardar. Dentro de la sección, añade las líneas correspondientes.

### 4.2 Catálogo de Máquinas, Documentación Técnica, BOM y Códigos QR (`/maquinas`)
Cada máquina de la planta cuenta con un perfil maestro integral diseñado para facilitar el trabajo tanto del Responsable de Mantenimiento desde el ordenador como del técnico a pie de máquina.

#### A. Generación e Impresión de Códigos QR (Desde la Web)
* Accede al menú **«Generador QR»** o pulsa el botón **«Código QR»** en cualquier máquina.
* El sistema genera una etiqueta física normalizada que incluye:
  * Nombre de la máquina y modelo.
  * Número de serie y sección.
  * Código QR de alta resolución con URL directa a la ficha técnica del equipo (`/maquinas/:machineId/detail`).
* **Impresión:** Puedes imprimir la etiqueta directamente en impresora de etiquetas adhesivas o láser y plastificarla para adherirla al cuadro eléctrico o chasis de la máquina.

#### B. Escaneo con Cámara desde la App Android (A Pie de Planta)
El mecánico ya no necesita llevar pesadas carpetas de planos ni desplazarse al taller para consultar manuales:
1. Abre la aplicación móvil **GMAO** en su teléfono o tablet industrial.
2. Toca el botón **«Escanear QR»** disponible directamente en el **Dashboard** o en la pestaña **Máquinas** (también dispone de botón de linterna/flash para zonas oscuras de la fábrica).
3. Apunta la cámara al código QR de la máquina. En menos de 0,5 segundos, la app vibra, reconoce el equipo y abre automáticamente su ficha completa.

#### C. Las 4 Áreas de Trabajo a Pie de Máquina:
1. **📄 Documentación Técnica y Planos (¡Acceso Inmediato!):**
   * **Manuales de usuario y mantenimiento (PDF):** El mecánico puede consultar el manual original del fabricante directamente en pantalla.
   * **Esquemas eléctricos y neumáticos:** Visualización de diagramas para rastrear cableados, relés, fusibles y electroválvulas en plena avería.
   * **Planos mecánicos y guías de ajuste:** Planos de despiece, tolerancias y pares de apriete.
2. **⚙️ Lista de Materiales (BOM) y Consulta de Stock:**
   * Despiece de todos los repuestos asignados al equipo (rodamientos, retenes, correas, fotocélulas, cilindros, contactores).
   * **Stock disponible en almacén en tiempo real:** El mecánico comprueba al instante si hay repuestos en stock físico antes de desmontar la pieza defectuosa.
3. **🛠️ Historial de Averías e Intervenciones:**
   * Registro histórico de todas las averías correctivas y mantenimientos preventivos previos.
   * Permite ver qué ocurrió la última vez que falló el equipo, qué operario intervino y qué solución se aplicó (Códigos FCR).
4. **📊 Indicadores de Fiabilidad y Apertura Rápida de OT:**
   * Consulta de métricas MTBF (tiempo medio entre fallos), MTTR (tiempo medio de reparación) y disponibilidad real.
   * Botón directo para **«Abrir Parte de Trabajo / OT»** vinculada automáticamente a la máquina escaneada sin tener que buscarla en listas.

### 4.3 Órdenes de Trabajo (OTs) y Partes de Mantenimiento (`/ordenes`)
El flujo de vida de una orden de trabajo garantiza trazabilidad total:
1. **Apertura de Avería:**
   * Puede abrirla cualquier operario o jefe de equipo indicando máquina afectada, descripción de la incidencia y nivel de prioridad (*Baja*, *Media*, *Alta*, *Urgente*).
2. **Asignación:**
   * El Jefe de Mantenimiento asigna la OT a un mecánico específico o a un rol (ej. *Mecánico de Turno*).
3. **Ejecución y Partes de Trabajo:**
   * El mecánico pone la OT en estado **«En curso»**.
   * Registra las horas de mano de obra invertidas.
   * Selecciona los repuestos utilizados del inventario (se descuentan automáticamente del stock).
   * Asigna los **Códigos FCR**:
     * **Fallo (Failure Code):** Qué falló (ej.: *Rotura mecánica*, *Fallo eléctrico*, *Atasco de material*).
     * **Causa (Cause Code):** Por qué falló (ej.: *Desgaste por uso*, *Falta de lubricación*, *Sobrecarga*).
     * **Remedio (Remedy Code):** Cómo se resolvió (ej.: *Sustitución de pieza*, *Ajuste y calibración*, *Reparación en taller*).
4. **Cierre:**
   * Una vez resuelto, se marca como **«Cerrada»** y pasa al histórico con cálculo de tiempos (MTTR - Tiempo Medio de Reparación).

### 4.4 Mantenimiento Preventivo, Tareas Periódicas y Plan Anual (`/mantenimiento-preventivo`, `/plan-anual`)
* **Creación de Planes Preventivos:**
  * Define la periodicidad (*Diaria*, *Semanal*, *Quincenal*, *Mensual*, *Trimestral*, *Semestral*, *Anual*).
  * Asocia una **Lista de Tareas (Checklist)** con los pasos numerados obligatorios y tiempos estimados.
* **Generación Automática:**
  * El **Scheduler** del sistema comprueba cada noche los preventivos que vencen y genera automáticamente la Orden de Trabajo correspondiente para el equipo técnico.
* **Plan Anual Visual:**  
  Una matriz interactiva de 12 meses donde se observan los preventivos programados, completados en verde o pendientes en naranja.

### 4.5 Mantenimiento Legal y Normativo (`/mantenimiento-legal`)
Módulo específico para inspecciones oficiales y cumplimiento reglamentario:
* Registro de equipos sometidos a normativa industrial: depósitos de aire comprimido (R.D. 2060/2008), centros de transformación eléctrica (RAT), instalaciones de protección contra incendios (RIPCI), climatización (RITE).
* Fechas de última y próxima inspección oficial (OCA / Organismo de Control Autorizado).
* Registro de número de certificado y adjuntos de actas oficiales.

### 4.6 Gestión de Inventario, Repuestos, Almacenes y Proveedores (`/inventario`, `/proveedores`)
* **Ficha de Repuesto:** Referencia interna, código del fabricante, ubicación física (Almacén, Estantería, Cajón), stock actual y stock mínimo de seguridad.
* **Precios Reales Cobrados por Proveedor:** El sistema no utiliza precios teóricos ni precios máximos arbitrarios; el precio unitario de cada repuesto es exactamente el precio real cobrado y facturado por el proveedor en compras anteriores.
* **Reporte y Exportación a Medida para Ajustes Contables (`/reporte-inventario`):**
  * Permite marcar mediante casillas de verificación (checkboxes) los repuestos específicos que se deseen incluir.
  * **Suma acumulada en vivo:** El sistema calcula y muestra en la cabecera la cantidad total de artículos y el valor monetario exacto (€) acumulado a medida que se seleccionan productos.
  * **Ajustes de Contabilidad:** Permite seleccionar un conjunto de productos hasta cuadrar el valor o importe determinado que la empresa necesite para sus balances o cierres contables.
  * **Exportación a Excel (.xlsx):** Genera el archivo Excel agrupado por tipos (mecánico, eléctrico, neumático, limpieza) con fórmulas nativas de suma para totales automáticos.
* **Alertas de Stock Bajo (`/inventario/bajo-stock`):** Cuando el consumo en una OT sitúa el stock por debajo del mínimo, el sistema genera avisos visuales para tramitar la reposición.
* **Comparador de Proveedores por Precio (`/comparar-precios`):** Historial comparativo de cotizaciones para cada repuesto que permite comprar al proveedor más económico.

### 4.7 Gestión de Turnos, Cuadrantes y Solicitudes de Vacaciones (`/turnos`, `/vacaciones`)
* **Patrones Rotativos:** Configuración de secuencias de turnos (ejemplo: 6x2, rotación Mañana-Tarde-Noche).
* **Calendario de Personal:** Vista mensual donde se visualizan los técnicos disponibles en cada turno y posibles descubiertos.
* **Módulo de Vacaciones:** El trabajador solicita días de permiso desde la web o app móvil; los administradores reciben la solicitud y la aprueban o rechazan con un clic.

### 4.8 Módulo de Comunicaciones Internas (`/communications`)
Canal formal de comunicación integrado en el GMAO:
* **Operario a Administración:** Envío de sugerencias de mejora, pedidos urgentes de herramienta o quejas técnicas (con opción de anonimato).
* **Administración a Operarios:** Envío de circulares, normas de seguridad o asignación de tareas extraordinarias.
* **Acuse de Recibo:** Trazabilidad de qué usuarios han abierto y leído el comunicado.

### 4.9 Gamificación, Puntos y Logros de Personal (`/gamification`)
Diseñado para fomentar la proactividad del equipo de mantenimiento:
* **Puntos por Acción:** Los mecánicos acumulan puntos al cerrar OTs preventivas en plazo, reportar averías detalladas con códigos FCR o realizar checklists exhaustivos.
* **Insignias y Retos:** Reconocimientos virtuales (ej.: *«Maestro del Engrase»*, *«Técnico Rápido»*, *«Cero Reincidencias»*).
* **Ranking de Mantenimiento:** Cuadro de honor mensual por puntos de calidad.

### 4.10 Inteligencia Artificial: Predicción, Chat Técnico y Procesamiento Documental
El sistema se integra de forma nativa con **Ollama** (servidores locales privados, sin enviar datos a la nube externa):
1. **Mantenimiento Predictivo:**  
   Algoritmos que analizan el historial de fallos pasados y horas de trabajo de cada máquina para predecir cuándo va a volver a fallar un componente (cálculo de probabilidad a 30 días y matriz de criticidad).
2. **Chat Asistente Técnico (AIChat):**  
   Los mecánicos pueden conversar con el modelo de lenguaje configurado como experto industrial. Ejemplo:  
   *«Tengo alarma de sobrepresión en la bomba de esmalte de la Línea 2, ¿qué debo revisar primero?»*
3. **Análisis Multimodal de Imágenes Técnicas:**  
   Permite adjuntar fotografías de piezas dañadas o placas de características de motores tomadas desde la app móvil para apoyar el diagnóstico y la identificación de componentes.

> [!IMPORTANT]
> **Criterio de Elección del Modelo de IA (Ollama):**  
> El servidor Ollama se ejecuta de forma 100% privada dentro de la infraestructura local del cliente. La profundidad del diagnóstico, el razonamiento técnico y la calidad de las respuestas dependen directamente de la capacidad del modelo que decida instalar cada empresa:
> - **Modelos ligeros (1B a 3B en CPU estándar):** Adecuados para consultas sencillas y clasificación básica. No pueden garantizar el razonamiento técnico profundo de un ingeniero de mantenimiento sénior.
> - **Modelos recomendados (8B a 14B con GPU o buena RAM, ej. *Llama 3.1 8B, Qwen 2.5 14B, Mistral*):** Nivel óptimo para diagnóstico de averías, detección de síntomas y consulta de manuales.
> - **Modelos avanzados (32B a 70B en servidores dedicados con GPU):** Capacidad analítica equivalente al criterio de un ingeniero especialista en fiabilidad industrial.
> Cada empresa debe instalar el modelo más potente que su hardware (memoria RAM o tarjeta gráfica GPU) le permita para maximizar el valor del asistente.


---

## 5. ADMINISTRACIÓN DEL SISTEMA Y AUTOMATIZACIÓN

### 5.1 Motor de Tareas Programadas (Scheduler)
En el backend se ejecuta un planificador en segundo plano (`scheduler.py`) que realiza las siguientes rutinas periódicas:
* **00:00 h diaria:** Generación automática de OTs para los mantenimientos preventivos que cumplen fecha hoy.
* **08:00 h diaria:** Verificación de preventivos que vencen en los próximos 7 días (aviso previo).
* **09:00 h diaria:** Verificación de artículos que han caído por debajo del stock mínimo.
* **10:00 h diaria:** Revisión de órdenes de trabajo vencidas pendientes de cierre.
* **Cada 10 minutos:** Ciclo de cálculo de predicciones de averías mediante IA.
* **Lunes a la 01:00 h:** Cálculo de métricas semanales de fiabilidad (MTBF, MTTR, Disponibilidad).

### 5.2 Notificaciones por Correo Electrónico (SMTP)
En el archivo de configuración `scheduler_config.json` se pueden activar las alertas por email:
```json
{
    "email": {
        "enabled": true,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "tu_correo@gmail.com",
        "password": "tu_app_password_de_16_caracteres",
        "sender": "GMAO Cerámica <tu_correo@gmail.com>"
    }
}
```
*(Nota: Para cuentas de Gmail, debes generar una «Contraseña de Aplicación» desde los ajustes de seguridad de Google).*

### 5.3 Copias de Seguridad (Backup) y Restauración de Base de Datos

#### Cómo generar una copia de seguridad manual:
Desde el servidor host donde corre Docker:
```bash
# Copia en formato comprimido de PostgreSQL
docker exec gmao-project-db pg_dump -U Admin -d mimas -F c -f /tmp/backup_gmao.dump
docker cp gmao-project-db:/tmp/backup_gmao.dump /root/backups/backup_$(date +%Y%m%d_%H%M%S).dump

# O copia en SQL plano:
docker exec gmao-project-db pg_dump -U Admin -d mimas --clean --if-exists > /root/backups/backup_$(date +%Y%m%d).sql
```

#### Cómo restaurar una copia de seguridad en caso de caída o migración:
1. Copia el archivo `.dump` al servidor.
2. Introduce el archivo en el contenedor:
   ```bash
   docker cp backup_gmao.dump gmao-project-db:/tmp/backup.dump
   ```
3. Detén el backend para evitar bloqueos:
   ```bash
   docker stop gmao-project-backend
   ```
4. Limpia el esquema y restaura los datos:
   ```bash
   docker exec gmao-project-db psql -U Admin -d mimas -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO \"Admin\";"
   docker exec gmao-project-db pg_restore -U Admin -d mimas /tmp/backup.dump
   ```
5. Vuelve a arrancar el backend:
   ```bash
   docker start gmao-project-backend
   ```

---

## 6. GUÍA EXHAUSTIVA DE RESOLUCIÓN DE PROBLEMAS (TROUBLESHOOTING)

A continuación se recopilan los problemas más habituales identificados durante el despliegue y uso en planta, acompañados de su solución técnica probada:

---

### Problema 1: Error en Android al iniciar sesión o cargar el Dashboard  
**Mensaje en pantalla:** `Error en tareas: Unknown error during API call: Required value 'title' (JSON name 'titulo') missing at $[1]` o error de tipo `ClassCastException`.

* **Causa:**
  1. En versiones anteriores de la app móvil (v2.2.1 o v2.2.2), el deserializador JSON (Moshi) exigía que los campos `title` vinieran estrictamente etiquetados como `titulo` en español sin admitir valores nulos o nombres en inglés.
  2. En compilaciones de Release anteriores, la optimización R8 eliminaba las firmas de tipos genéricos de Retrofit (`Continuation<Response<LoginResponse>>`).
* **Solución:**
  1. **Actualización del Backend:** Ya se han añadido alias bilingües (`title`/`titulo`, `type`/`tipo`, `description`/`descripcion`) en el router `/maintenance` del backend para que la app nunca encuentre campos ausentes.
  2. **Actualización de la App:** Instala la versión corregida **`GMAOv2.2.3.apk`** disponible en GitHub y en el instalador. Esta versión es completamente tolerante a fallos y tiene valores por defecto de seguridad.

---

### Problema 2: Error de Certificado SSL en Navegador o Móvil  
**Mensaje:** `NET::ERR_CERT_AUTHORITY_INVALID` o `Trust anchor for certification path not found`.

* **Causa:** El instalador genera certificados SSL autofirmados válidos para la IP local del servidor (`https://192.168.1.X`).
* **Solución:**
  * **En el Navegador Web:** Haz clic en *«Avanzado»* y luego en *«Continuar a 192.168.1.X (no seguro)»*. Esto solo debe hacerse la primera vez.
  * **En la App Android:** La versión v2.2.2 y v2.2.3 ya incorpora un gestor de confianza SSL específico (`TrustAllCertsSocketFactory`) en `ApiConfig.kt` y `RepositoryModule.kt` que permite operar en redes locales con IPs privadas sin bloquear la conexión.

---

### Problema 3: Los contenedores no arrancan o la base de datos da error de conexión  
**Mensaje en logs:** `could not translate host name "db" to address` o `Connection refused (port 5432)`.

* **Causa:** La red de Docker no está enlazada o el contenedor `gmao-project-db` no ha completado su arranque inicial antes que el backend.
* **Solución:**
  1. Verifica el estado de los contenedores:
     ```bash
     docker ps -a
     ```
  2. Si `gmao-project-db` está reiniciándose, comprueba sus logs:
     ```bash
     docker logs gmao-project-db
     ```
  3. Asegúrate de que el volumen de datos tiene permisos adecuados:
     ```bash
     cd /root/gmao-project
     docker compose restart db
     sleep 5
     docker compose restart backend
     ```

---

### Problema 4: El instalador interactivo da error al introducir letras en lugar de números  
**Síntoma:** Durante la instalación, al preguntar por número de secciones o máquinas, se introdujo una letra y la instalación falló al crear la base de datos.

* **Causa:** Falta de validación estricta de tipo en versiones antiguas de `install.sh`.
* **Solución:**
  * Se ha incorporado la función `ask_positive_int` en el instalador oficial. Si introduces un valor no numérico, el script te avisará inmediatamente con un mensaje en rojo y volverá a solicitar el número sin romper la instalación.
  * Para limpiar y reinstalar desde cero:
    ```bash
    cd /root/gmao-installer
    git pull origin main
    # Detener y borrar contenedores previos
    cd /root/gmao-project && docker compose down -v
    cd /root/gmao-installer && ./install.sh
    ```

---

### Problema 5: La Inteligencia Artificial no responde o devuelve error 503  
**Mensaje:** `Servicio de IA no disponible: Error: No se encontraron modelos en el servidor de Ollama`.

* **Causa:** El backend no puede comunicarse con la IP de Ollama (`192.168.1.62:11434`) o el servidor Ollama está apagado.
* **Solución:**
  1. Comprueba desde el servidor GMAO si hay visibilidad de red hacia Ollama:
     ```bash
     curl -s http://192.168.1.62:11434/api/tags
     ```
  2. Si responde un JSON con la lista de modelos, la red funciona. Si da `Connection refused` o timeout:
     * Asegúrate de que Ollama está escuchando en todas las interfaces (`OLLAMA_HOST=0.0.0.0:11434`).
     * Revisa que el firewall del servidor Windows/Linux que aloja Ollama permite el puerto `11434` entrante.
  3. En la web del GMAO, ve a `Administración IA` -> `Probar Conexión` para forzar la rediscovery de modelos.

---

### Problema 6: No se envían los correos de aviso de stock bajo o preventivos  
* **Causa:** Las credenciales de Gmail en `scheduler_config.json` son incorrectas o Google bloqueó el acceso.
* **Solución:**
  1. Google ya no permite usar tu contraseña personal en programas externos.
  2. Entra en tu cuenta de Google -> `Seguridad` -> `Verificación en 2 pasos` -> `Contraseñas de aplicaciones`.
  3. Crea una nueva contraseña llamada "GMAO" (es una clave de 16 letras como `abcd efgh ijkl mnop`).
  4. Configura esa clave en `scheduler_config.json` y reinicia el backend:
     ```bash
     docker restart gmao-project-backend
     ```

---

### Problema 7: El mecánico no ve las órdenes de trabajo de otra sección  
* **Causa:** Comportamiento normal de seguridad del sistema.
* **Solución:** Los usuarios con rol `Jefe de Sección` o `Mecánico` tienen el acceso limitado por defecto a los equipos de su sección asignada para evitar confusiones en planta. Si un técnico debe intervenir en toda la fábrica, su usuario debe crearse o editarse con el rol `Jefe de Mantenimiento` o asociarse a la sección general `Mantenimiento`.

---

### Problema 8: Cómo hacer una copia de seguridad rápida antes de una intervención en planta  
Ejecuta en un solo comando:
```bash
docker exec gmao-project-db pg_dump -U Admin -d mimas -F c -f /tmp/backup_seguridad.dump && docker cp gmao-project-db:/tmp/backup_seguridad.dump /root/backup_seguridad_$(date +%Y%m%d_%H%M).dump
```
El archivo generado en `/root/` contendrá todos los datos exactos del sistema listos para ser recuperados en segundos en caso de necesidad.

---
---

## ⚖️ PROPIEDAD INTELECTUAL Y DERECHOS DE AUTOR

© 2024–2026 **Fran Romera**. Todos los derechos reservados.

El software **GMAO System**, su código fuente, arquitectura técnica, esquema de base de datos, interfaz gráfica web, app nativa Android, algoritmos de cálculo predictivo mediante IA y la presente documentación técnica constituyen una obra original y propiedad intelectual exclusiva de **Fran Romera**.

**Aviso Legal y Prohibición Expresa:**  
Queda terminantemente prohibida la copia ilegal, reproducción total o parcial, ingeniería inversa, decompilación, distribución comercial, cesión, sublicenciamiento o explotación no autorizada por cualquier medio físico o digital sin el consentimiento expreso, previo y por escrito de su autor y titular, **Fran Romera**.

*Manual elaborado y verificado para la versión GMAO 2.2.3. Sistema operativo en planta industrial.*
EOF
