#!/bin/bash
# ==============================================================================
# GMAO SYSTEM - Script de Arranque Todo en Uno (Bootstrap)
# Instala automáticamente todas las dependencias del sistema y lanza el asistente.
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BLUE}${BOLD}==========================================================================${NC}"
echo -e "${CYAN}${BOLD}       GMAO SYSTEM - Preparando el Sistema Operativo (Automático)         ${NC}"
echo -e "${BLUE}${BOLD}==========================================================================${NC}\n"

# Forzar preferencia IPv4 para evitar fallos de conectividad en redes sin enrutamiento IPv6
sed -i 's/^#precedence ::ffff:0:0\/96  100/precedence ::ffff:0:0\/96  100/' /etc/gai.conf 2>/dev/null || true

echo -e "${YELLOW}⚙️  Instalando dependencias necesarias (Git, Docker, Compose, OpenSSL)...${NC}"

if command -v apt-get &> /dev/null; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y git curl openssl docker.io
    apt-get install -y docker-compose-v2 || apt-get install -y docker-compose || true
elif command -v dnf &> /dev/null; then
    dnf install -y git curl openssl docker docker-compose
elif command -v yum &> /dev/null; then
    yum install -y git curl openssl docker docker-compose
fi

echo -e "  ${GREEN}✓${NC} Paquetes del sistema instalados."

# Asegurar servicio Docker iniciado
if command -v systemctl &> /dev/null; then
    systemctl enable --now docker 2>/dev/null || true
    systemctl start docker 2>/dev/null || true
fi
service docker start 2>/dev/null || true

# Verificar Docker
if ! docker ps &> /dev/null; then
    echo -e "${YELLOW}⚠️  Aviso: Docker está iniciando...${NC}"
    sleep 3
fi

# Asegurar directorio de trabajo valido en el host
cd "$HOME" 2>/dev/null || cd /root 2>/dev/null || cd /

INSTALL_DIR="$HOME/GMAO-installer"
if [ -d "$INSTALL_DIR/.git" ]; then
    echo -e "  ${GREEN}✓${NC} Repositorio detectado en $INSTALL_DIR. Actualizando última versión..."
    cd "$INSTALL_DIR"
    git fetch origin main 2>/dev/null || true
    git reset --hard origin/main 2>/dev/null || git pull || true
else
    echo -e "${CYAN}📥 Descargando GMAO System desde GitHub...${NC}"
    rm -rf "$INSTALL_DIR"
    git clone https://github.com/fromeram/GMAO-installer.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

chmod +x install.sh gmao.sh

echo -e "\n${GREEN}✓ Todo listo. Iniciando el asistente de configuración de fábrica...${NC}\n"
sleep 1

exec ./install.sh
