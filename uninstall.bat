@echo off
chcp 65001 >nul
title GMAO System - Desinstalador para Windows
echo ==========================================================================
echo        GMAO SYSTEM - Desinstalacion Completa de Contenedores
echo ==========================================================================
echo.
set /p CONFIRM="Desea detener y eliminar todos los contenedores y datos de GMAO System? (s/n): "
if /i "%CONFIRM%" neq "s" (
    echo Desinstalacion cancelada.
    pause
    exit /b 0
)

echo Deteniendo y eliminando contenedores Docker...
docker compose down -v
echo.
echo ==========================================================================
echo   GMAO System ha sido detenido y desinstalado de su equipo.
echo ==========================================================================
echo.
pause
