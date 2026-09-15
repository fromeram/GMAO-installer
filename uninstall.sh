#!/bin/bash
# ==============================================================================
# GMAO SYSTEM - Script de Desinstalación Automática
# Elimina contenedores, volúmenes de datos y el directorio de instalación.
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "\n${YELLOW}${BOLD}⚠️  Desinstalando GMAO System de su servidor...${NC}"

INSTALL_DIR="$HOME/GMAO-installer"

if [ -d "$INSTALL_DIR" ]; then
    cd "$INSTALL_DIR"
    if docker compose version &> /dev/null; then
        docker compose down -v --rmi all 2>/dev/null || docker compose down -v 2>/dev/null || true
    elif command -v docker-compose &> /dev/null; then
        docker-compose down -v --rmi all 2>/dev/null || docker-compose down -v 2>/dev/null || true
    fi
    cd "$HOME"
    rm -rf "$INSTALL_DIR"
fi

echo -e "${GREEN}${BOLD}✓ GMAO System ha sido desinstalado por completo del sistema.${NC}\n"
