#!/bin/bash
# ==============================================================================
# GMAO SYSTEM - Script de Control y Mantenimiento
# Proporciona herramientas rápidas para gestionar el ciclo de vida del GMAO.
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Detección de docker compose
if docker compose version &> /dev/null; then
    COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE="docker-compose"
else
    echo -e "${RED}Error: docker compose no está instalado.${NC}"
    exit 1
fi

status_cmd() {
    echo -e "\n${CYAN}📊 Estado de los contenedores GMAO:${NC}"
    $COMPOSE ps
    echo ""
}

start_cmd() {
    echo -e "\n${GREEN}🚀 Iniciando servicios del GMAO...${NC}"
    $COMPOSE up -d
    echo -e "${GREEN}✓ Servicios iniciados.${NC}\n"
}

stop_cmd() {
    echo -e "\n${YELLOW}🛑 Deteniendo servicios del GMAO...${NC}"
    $COMPOSE down
    echo -e "${YELLOW}✓ Servicios detenidos.${NC}\n"
}

restart_cmd() {
    echo -e "\n${BLUE}🔄 Reiniciando servicios...${NC}"
    $COMPOSE restart
    echo -e "${GREEN}✓ Servicios reiniciados.${NC}\n"
}

logs_cmd() {
    SERVICE="${1:-}"
    if [ -n "$SERVICE" ]; then
        echo -e "\n${CYAN}📋 Mostrando logs de $SERVICE (Ctrl+C para salir):${NC}"
        $COMPOSE logs -f "$SERVICE"
    else
        echo -e "\n${CYAN}📋 Mostrando logs de todos los servicios (Ctrl+C para salir):${NC}"
        $COMPOSE logs -f
    fi
}

backup_cmd() {
    mkdir -p backups
    TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
    BACKUP_FILE="backups/gmao_backup_${TIMESTAMP}.sql"
    
    echo -e "\n${CYAN}💾 Creando copia de seguridad de la base de datos...${NC}"
    
    # Cargar variables de entorno si existen
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    DB_USER="${POSTGRES_USER:-gmao_user}"
    DB_NAME="${POSTGRES_DB:-gmao_db}"
    
    docker exec gmao-project-db pg_dump -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"
    
    if [ -s "$BACKUP_FILE" ]; then
        SIZE=$(du -h "$BACKUP_FILE" | awk '{print $1}')
        echo -e "${GREEN}✓ Copia de seguridad creada con éxito:${NC} $BACKUP_FILE ($SIZE)\n"
    else
        echo -e "${RED}❌ Error creando la copia de seguridad.${NC}\n"
        rm -f "$BACKUP_FILE"
    fi
}

restore_cmd() {
    mkdir -p backups
    BACKUP_FILE="${1:-}"
    
    if [ -z "$BACKUP_FILE" ]; then
        echo -e "\n${YELLOW}Archivos de backup disponibles:${NC}"
        ls -lh backups/*.sql 2>/dev/null || { echo "No se encontraron backups en ./backups"; return 1; }
        echo ""
        read -r -p "Introduce la ruta del archivo de backup a restaurar: " BACKUP_FILE
    fi
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo -e "${RED}Error: El archivo $BACKUP_FILE no existe.${NC}\n"
        return 1
    fi
    
    echo -e "${RED}${BOLD}⚠️  ATENCIÓN: La restauración sobreescribirá los datos actuales.${NC}"
    read -r -p "¿Estás seguro de continuar? (s/N): " CONFIRM
    if [[ "$CONFIRM" =~ ^[sSyY]$ ]]; then
        if [ -f .env ]; then
            export $(grep -v '^#' .env | xargs)
        fi
        DB_USER="${POSTGRES_USER:-gmao_user}"
        DB_NAME="${POSTGRES_DB:-gmao_db}"
        
        echo -e "\n${CYAN}Restaurando base de datos desde $BACKUP_FILE...${NC}"
        cat "$BACKUP_FILE" | docker exec -i gmao-project-db psql -U "$DB_USER" -d "$DB_NAME"
        echo -e "${GREEN}✓ Restauración completada.${NC}\n"
    else
        echo -e "Operación cancelada.\n"
    fi
}

interactive_menu() {
    while true; do
        echo -e "${BLUE}${BOLD}====================================================${NC}"
        echo -e "${BLUE}${BOLD}       GMAO SYSTEM - Panel de Administración        ${NC}"
        echo -e "${BLUE}${BOLD}====================================================${NC}"
        echo -e "  1) ${CYAN}Estado de los servicios (status)${NC}"
        echo -e "  2) ${GREEN}Iniciar servicios (start)${NC}"
        echo -e "  3) ${YELLOW}Detener servicios (stop)${NC}"
        echo -e "  4) ${BLUE}Reiniciar servicios (restart)${NC}"
        echo -e "  5) ${CYAN}Ver logs en tiempo real (logs)${NC}"
        echo -e "  6) ${GREEN}Crear copia de seguridad (backup)${NC}"
        echo -e "  7) ${RED}Restaurar copia de seguridad (restore)${NC}"
        echo -e "  8) ${YELLOW}Reconstruir contenedores (build)${NC}"
        echo -e "  0) Salir"
        echo -e "${BLUE}----------------------------------------------------${NC}"
        read -r -p "Selecciona una opción [0-8]: " OPTION
        
        case "$OPTION" in
            1) status_cmd ;;
            2) start_cmd ;;
            3) stop_cmd ;;
            4) restart_cmd ;;
            5) logs_cmd ;;
            6) backup_cmd ;;
            7) restore_cmd ;;
            8) $COMPOSE up -d --build ;;
            0) echo "Hasta pronto."; exit 0 ;;
            *) echo -e "${RED}Opción no válida.${NC}\n" ;;
        esac
    done
}

# Ejecución según argumentos o menú
case "${1:-}" in
    status) status_cmd ;;
    start) start_cmd ;;
    stop) stop_cmd ;;
    restart) restart_cmd ;;
    logs) logs_cmd "${2:-}" ;;
    backup) backup_cmd ;;
    restore) restore_cmd "${2:-}" ;;
    build) $COMPOSE up -d --build ;;
    *) interactive_menu ;;
esac
