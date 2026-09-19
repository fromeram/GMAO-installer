# ==============================================================================
# GMAO SYSTEM - Instalador Automático para Windows (PowerShell)
# Compatible con Windows 10, Windows 11 y Windows Server con Docker Desktop
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"

Clear-Host
Write-Host "==========================================================================" -ForegroundColor Blue
Write-Host "    ██████╗ ███╗   ███╗ █████╗  ██████╗     ███████╗██╗   ██╗███████╗" -ForegroundColor Blue
Write-Host "   ██╔════╝ ████╗ ████║██╔══██╗██╔═══██╗    ██╔════╝╚██╗ ██╔╝██╔════╝" -ForegroundColor Blue
Write-Host "   ██║  ███╗██╔████╔██║███████║██║   ██║    ███████╗ ╚████╔╝ ███████╗" -ForegroundColor Blue
Write-Host "   ██║   ██║██║╚██╔╝██║██╔══██║██║   ██║    ╚════██║  ╚██╔╝  ╚════██║" -ForegroundColor Blue
Write-Host "   ╚██████╔╝██║ ╚═╝ ██║██║  ██║╚██████╔╝    ███████║   ██║   ███████║" -ForegroundColor Blue
Write-Host "    ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝     ╚══════╝   ╚═╝   ╚══════╝" -ForegroundColor Blue
Write-Host "==========================================================================" -ForegroundColor Blue
Write-Host "         Asistente de Instalación y Despliegue en Windows" -ForegroundColor Cyan
Write-Host "==========================================================================`n" -ForegroundColor Blue

# 1. Comprobación de Docker Desktop
Write-Host "[1/5] Verificando Docker Desktop en Windows..." -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Error: Docker no está instalado en este equipo con Windows." -ForegroundColor Red
    Write-Host "👉 Por favor, descarga e instala Docker Desktop para Windows desde:" -ForegroundColor Yellow
    Write-Host "   https://www.docker.com/products/docker-desktop/`n" -ForegroundColor Cyan
    Write-Host "Durante la instalación, asegúrate de marcar 'Use WSL 2 instead of Hyper-V'." -ForegroundColor Gray
    Write-Host "Una vez instalado y abierto, vuelve a ejecutar este instalador." -ForegroundColor Gray
    Read-Host "Presiona ENTER para salir..."
    Exit 1
}

$dockerRunning = $false
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dockerRunning = $true
    }
} catch {
    $dockerRunning = $false
}

if (-not $dockerRunning) {
    Write-Host "⚠️  Docker Desktop está instalado pero no se encuentra en ejecución." -ForegroundColor Yellow
    Write-Host "👉 Por favor, abre la aplicación Docker Desktop desde tu Menú Inicio de Windows." -ForegroundColor Cyan
    Write-Host "   Espera a que el icono de la ballena en la barra de tareas esté activo y reintenta.`n" -ForegroundColor Gray
    Read-Host "Presiona ENTER para salir..."
    Exit 1
}

Write-Host "  ✓ Docker Desktop detectado y operativo." -ForegroundColor Green

# 2. Configuración de Parámetros
Write-Host "`n[2/5] Configuración de Red y Seguridad" -ForegroundColor Cyan
Write-Host "Pulsa ENTER para aceptar los valores sugeridos por defecto [ ].`n" -ForegroundColor Yellow

$SERVER_HOST = Read-Host "  🌐 Dirección IP o dominio [localhost]"
if ([string]::IsNullOrWhiteSpace($SERVER_HOST)) { $SERVER_HOST = "localhost" }

$POSTGRES_DB = "gmao_db"
$POSTGRES_USER = "gmao_user"
$rndPass = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 10 | ForEach-Object {[char]$_})
$POSTGRES_PASSWORD = "Gmao_" + $rndPass

$INITIAL_ADMIN_USERNAME = "admin"
$rndAdmin = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 8 | ForEach-Object {[char]$_})
$INITIAL_ADMIN_PASSWORD = "Adm_" + $rndAdmin

$JWT_SECRET_KEY = [System.Guid]::NewGuid().ToString("N") + [System.Guid]::NewGuid().ToString("N")
$OLLAMA_URL = "http://host.docker.internal:11434"

# 3. Estructura de Fábrica Inicial
Write-Host "`n[3/5] Configuración de la Estructura de Fábrica" -ForegroundColor Cyan
Write-Host "  1) Cargar plantilla industrial estándar de ejemplo (Recomendado para pruebas)"
Write-Host "  2) Empezar con estructura mínima"
$opt = Read-Host "  Selecciona una opción [1-2, por defecto 1]"

$SQL_SETUP = "db/03_factory_setup.sql"
New-Item -ItemType Directory -Force -Path "db" | Out-Null

if ($opt -eq "2") {
    $sqlContent = @"
INSERT INTO warehouses (name) VALUES ('Almacén Central de Repuestos');
INSERT INTO sections (name) VALUES ('Planta General');
INSERT INTO lines (name, section_id) VALUES ('Línea Principal', 1);
"@
    Set-Content -Path $SQL_SETUP -Value $sqlContent -Encoding UTF8
    Write-Host "  ✓ Configuración mínima seleccionada." -ForegroundColor Green
} else {
    $sqlContent = @"
-- Almacenes
INSERT INTO warehouses (name) VALUES 
    ('Almacén Central de Repuestos'),
    ('Taller de Mantenimiento y Herramientas');

-- Secciones
INSERT INTO sections (id, nombre) VALUES 
    (1, 'Mecanizado y Mecánica General'),
    (2, 'Línea de Envasado y Packaging'),
    (3, 'Servicios Auxiliares e Infraestructura');

-- Líneas
INSERT INTO lines (id, nombre, section_id) VALUES 
    (1, 'Línea de Tornos y Fresadoras', 1),
    (2, 'Línea de Embotellado Automático', 2),
    (3, 'Sala de Calderas y Compresores', 3);

-- Máquinas
INSERT INTO machines (nombre, marca, modelo, numero_serie, criticidad, section_id, line_id) VALUES 
    ('Torno CNC Multieje', 'Haas Automation', 'ST-20Y', 'SN-HAA-2024-01', 'ALTA', 1, 1),
    ('Centro de Mecanizado Vertical', 'Mazak', 'VCN-530C', 'SN-MAZ-2023-88', 'ALTA', 1, 1),
    ('Llenadora Rotativa Isométrica', 'Krones', 'Modulfill', 'SN-KRO-2022-12', 'ALTA', 2, 2),
    ('Etiquetadora Automática', 'PackLab', 'Wing-12', 'SN-PKL-2021-05', 'MEDIA', 2, 2),
    ('Compresor Rotativo de Tornillo', 'Atlas Copco', 'GA-37-VSD', 'SN-ATC-2020-43', 'ALTA', 3, 3);

SELECT setval('sections_id_seq', (SELECT COALESCE(MAX(id), 1) FROM sections));
SELECT setval('lines_id_seq', (SELECT COALESCE(MAX(id), 1) FROM lines));
SELECT setval('machines_id_seq', (SELECT COALESCE(MAX(id), 1) FROM machines));
SELECT setval('warehouses_id_seq', (SELECT COALESCE(MAX(id), 1) FROM warehouses));
"@
    Set-Content -Path $SQL_SETUP -Value $sqlContent -Encoding UTF8
    Write-Host "  ✓ Plantilla industrial estándar preparada." -ForegroundColor Green
}

# 4. Generación de Archivos del Entorno y Certificados
Write-Host "`n[4/5] Generando configuración de entorno y carpetas..." -ForegroundColor Cyan

New-Item -ItemType Directory -Force -Path "backend/src/storage/documents/attachments" | Out-Null
New-Item -ItemType Directory -Force -Path "nginx/certs" | Out-Null
New-Item -ItemType Directory -Force -Path "backups" | Out-Null

$envContent = @"
# GMAO SYSTEM - Configuración del Entorno Windows
POSTGRES_DB=$POSTGRES_DB
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
INITIAL_ADMIN_USERNAME=$INITIAL_ADMIN_USERNAME
INITIAL_ADMIN_PASSWORD=$INITIAL_ADMIN_PASSWORD
OLLAMA_URL=$OLLAMA_URL
SERVER_HOST=$SERVER_HOST
CORS_ORIGINS=http://$SERVER_HOST,http://${SERVER_HOST}:80,https://$SERVER_HOST,http://localhost,http://localhost:3000
"@

Set-Content -Path ".env" -Value $envContent -Encoding UTF8
Write-Host "  ✓ Archivo .env generado." -ForegroundColor Green

# 5. Despliegue de Contenedores Docker
Write-Host "`n[5/5] Iniciando contenedores de GMAO System..." -ForegroundColor Cyan
Write-Host "  Descargando imágenes oficiales de Docker (esto solo tarda la primera vez)..." -ForegroundColor Gray

docker compose down -v --remove-orphans 2>$null
docker compose pull
docker compose up -d

Write-Host "`n  Verificando que los servicios respondan correctamente..." -ForegroundColor Gray
$ready = $false
for ($i=1; $i -le 35; $i++) {
    Start-Sleep -Seconds 2
    $state = docker ps --filter "name=gmao-project-backend" --filter "health=healthy" -q
    if ($state) {
        $ready = $true
        break
    }
    Write-Host -NoNewline "."
}

Write-Host ""
if ($ready) {
    Write-Host "  ✓ Todos los servicios se han iniciado con éxito." -ForegroundColor Green
    if (Test-Path $SQL_SETUP) {
        Get-Content $SQL_SETUP | docker exec -i gmao-project-db psql -U $POSTGRES_USER -d $POSTGRES_DB 2>$null
    }
} else {
    Write-Host "  ℹ️  Los contenedores están iniciando en segundo plano." -ForegroundColor Yellow
}

# Resumen de Instalación
Write-Host "`n==========================================================================" -ForegroundColor Green
Write-Host "         🎉 ¡GMAO SYSTEM ESTÁ LISTO EN TU EQUIPO WINDOWS!                 " -ForegroundColor Green
Write-Host "==========================================================================`n" -ForegroundColor Green
Write-Host "  🌐 Acceso Web Seguro (HTTPS):   https://$SERVER_HOST" -ForegroundColor White
Write-Host "  🌐 Acceso Web (HTTP):          http://$SERVER_HOST" -ForegroundColor White
Write-Host "  📡 Documentación API (Swagger): https://$SERVER_HOST/api/docs" -ForegroundColor White
Write-Host ""
Write-Host "  🛡️  Credenciales de Acceso Inicial:" -ForegroundColor White
Write-Host "     Usuario:    $INITIAL_ADMIN_USERNAME" -ForegroundColor Cyan
Write-Host "     Contraseña: $INITIAL_ADMIN_PASSWORD" -ForegroundColor Cyan
Write-Host ""
Write-Host "==========================================================================`n" -ForegroundColor Blue

# Abrir el navegador automáticamente
Start-Process "http://$SERVER_HOST"

Write-Host "Para detener el sistema más adelante, ejecuta el archivo 'uninstall.bat' o 'docker compose down'." -ForegroundColor Gray
