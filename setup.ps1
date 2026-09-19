# ==============================================================================
# GMAO SYSTEM - Script de Arranque en Windows (Bootstrap)
# Descarga automáticamente el repositorio y ejecuta el instalador.
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

Write-Host "`n==========================================================================" -ForegroundColor Blue
Write-Host "       GMAO SYSTEM - Descarga y Despliegue Automático en Windows          " -ForegroundColor Cyan
Write-Host "==========================================================================`n" -ForegroundColor Blue

$INSTALL_DIR = "$HOME\GMAO-installer"

if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "📥 Descargando GMAO System mediante Git..." -ForegroundColor Cyan
    if (Test-Path "$INSTALL_DIR\.git") {
        Set-Location $INSTALL_DIR
        git pull origin main
    } else {
        if (Test-Path $INSTALL_DIR) { Remove-Item -Recurse -Force $INSTALL_DIR }
        git clone https://github.com/fromeram/GMAO-installer.git $INSTALL_DIR
        Set-Location $INSTALL_DIR
    }
} else {
    Write-Host "📥 Descargando paquete oficial de GMAO System desde GitHub..." -ForegroundColor Cyan
    $zipPath = "$HOME\gmao_installer.zip"
    $tempDir = "$HOME\gmao_temp"
    
    Invoke-WebRequest -Uri "https://github.com/fromeram/GMAO-installer/archive/refs/heads/main.zip" -OutFile $zipPath
    if (Test-Path $tempDir) { Remove-Item -Recurse -Force $tempDir }
    Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force
    
    if (Test-Path $INSTALL_DIR) { Remove-Item -Recurse -Force $INSTALL_DIR }
    Move-Item -Path "$tempDir\GMAO-installer-main" -Destination $INSTALL_DIR -Force
    Remove-Item $zipPath -Force
    Remove-Item $tempDir -Recurse -Force
    Set-Location $INSTALL_DIR
}

Write-Host "✓ Archivos preparados en $INSTALL_DIR`n" -ForegroundColor Green
& "$INSTALL_DIR\install.ps1"
