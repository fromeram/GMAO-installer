@echo off
chcp 65001 >nul
title GMAO System - Instalador para Windows
echo ==========================================================================
echo        GMAO SYSTEM - Asistente de Instalacion en Windows
echo ==========================================================================
echo.
echo Iniciando el asistente automatico en PowerShell...
echo.

where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker no esta instalado en este equipo con Windows.
    echo.
    echo Para probar GMAO System en Windows necesitas Docker Desktop:
    echo 1. Descarga Docker Desktop desde: https://www.docker.com/products/docker-desktop/
    echo 2. Instala marcando la casilla "Use WSL 2 instead of Hyper-V".
    echo 3. Abre Docker Desktop y luego vuelve a hacer doble clic en este archivo.
    echo.
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [AVISO] La instalacion se interrumpio o detecto un inconveniente.
    pause
)
