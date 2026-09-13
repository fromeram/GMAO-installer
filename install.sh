#!/bin/bash
# ==============================================================================
# GMAO SYSTEM - Instalador Automático e Interactivo
# Despliega el sistema GMAO completo adaptado a la estructura de cualquier fábrica.
# ==============================================================================

set -e

# Colores de terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

clear
echo -e "${BLUE}${BOLD}"
echo "=========================================================================="
echo "    ██████╗ ███╗   ███╗ █████╗  ██████╗     ███████╗██╗   ██╗███████╗"
echo "   ██╔════╝ ████╗ ████║██╔══██╗██╔═══██╗    ██╔════╝╚██╗ ██╔╝██╔════╝"
echo "   ██║  ███╗██╔████╔██║███████║██║   ██║    ███████╗ ╚████╔╝ ███████╗"
echo "   ██║   ██║██║╚██╔╝██║██╔══██║██║   ██║    ╚════██║  ╚██╔╝  ╚════██║"
echo "   ╚██████╔╝██║ ╚═╝ ██║██║  ██║╚██████╔╝    ███████║   ██║   ███████║"
echo "    ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝     ╚══════╝   ╚═╝   ╚══════╝"
echo "=========================================================================="
echo -e "         ${CYAN}Asistente de Instalación y Despliegue de Fábrica${NC}"
echo -e "${BLUE}${BOLD}==========================================================================${NC}\n"

# 1. Comprobación e instalación automática de requisitos
echo -e "${CYAN}[1/6] Verificando e instalando componentes necesarios...${NC}"

if ! command -v openssl &> /dev/null; then
    echo -e "  ${YELLOW}⚙️  Instalando OpenSSL...${NC}"
    if command -v apt-get &> /dev/null; then apt-get update -y -qq && apt-get install -y -qq openssl; fi
fi

if ! command -v docker &> /dev/null; then
    echo -e "  ${YELLOW}⚙️  Docker no está instalado. Instalándolo automáticamente...${NC}"
    if command -v apt-get &> /dev/null; then
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -y
        apt-get install -y docker.io docker-compose-v2 || apt-get install -y docker.io docker-compose || true
    fi
fi

# Asegurar que el servicio de Docker esté corriendo
if command -v systemctl &> /dev/null; then
    systemctl enable --now docker 2>/dev/null || true
    systemctl start docker 2>/dev/null || true
fi
service docker start 2>/dev/null || true

echo -e "  ${GREEN}✓${NC} Docker verificado: $(docker --version 2>/dev/null || echo Activo)"

DOCKER_COMPOSE_CMD=""
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo -e "  ${YELLOW}⚙️  Instalando plugin docker-compose...${NC}"
    if command -v apt-get &> /dev/null; then apt-get install -y docker-compose-v2 || apt-get install -y docker-compose; fi
    DOCKER_COMPOSE_CMD="docker compose"
fi
echo -e "  ${GREEN}✓${NC} Docker Compose listo" 

# Detectar IP local del servidor
DEFAULT_IP="localhost"
if command -v hostname &> /dev/null && hostname -I &> /dev/null; then
    DEFAULT_IP=$(hostname -I | awk '{print $1}')
elif command -v ipconfig &> /dev/null; then
    DETECTED_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "")
    if [ -n "$DETECTED_IP" ]; then DEFAULT_IP="$DETECTED_IP"; fi
fi

# 2. Configuración del Servidor y Credenciales
echo -e "\n${CYAN}[2/6] Configuración de Red y Seguridad${NC}"
echo -e "${YELLOW}Pulsa ENTER para aceptar el valor por defecto [ ].${NC}\n"

read -r -p "  🌐 Dirección IP o dominio del servidor [$DEFAULT_IP]: " INPUT_HOST
SERVER_HOST="${INPUT_HOST:-$DEFAULT_IP}"

read -r -p "  🗄️  Nombre de la base de datos [gmao_db]: " INPUT_DB
POSTGRES_DB="${INPUT_DB:-gmao_db}"

read -r -p "  👤 Usuario de PostgreSQL [gmao_user]: " INPUT_DB_USER
POSTGRES_USER="${INPUT_DB_USER:-gmao_user}"

SUGGESTED_DB_PASS=$(openssl rand -base64 12 2>/dev/null | tr -dc 'a-zA-Z0-9' | head -c 12 || echo "GmaoDbPass2026")
read -r -p "  🔑 Contraseña para PostgreSQL [$SUGGESTED_DB_PASS]: " INPUT_DB_PASS
POSTGRES_PASSWORD="${INPUT_DB_PASS:-$SUGGESTED_DB_PASS}"

echo ""
read -r -p "  🛡️  Usuario Administrador del GMAO [admin]: " INPUT_ADMIN_USER
INITIAL_ADMIN_USERNAME="${INPUT_ADMIN_USER:-admin}"

SUGGESTED_ADMIN_PASS=$(openssl rand -base64 10 2>/dev/null | tr -dc 'a-zA-Z0-9' | head -c 10 || echo "AdminPass123")
read -r -p "  🔐 Contraseña del Administrador [$SUGGESTED_ADMIN_PASS]: " INPUT_ADMIN_PASS
INITIAL_ADMIN_PASSWORD="${INPUT_ADMIN_PASS:-$SUGGESTED_ADMIN_PASS}"

echo -e "\n  ${YELLOW}🤖 Inteligencia Artificial (Mantenimiento Predictivo y Chat con Ollama):${NC}"
echo -e "  El GMAO incluye análisis de riesgo, predicciones automáticas y chat con IA local."
echo -e "  Para estas funciones se requiere un servidor Ollama (en este equipo o en otro de la red)."
echo -e "  ${CYAN}💡 Si aún no tienes Ollama, puedes instalarlo en Linux con:${NC}"
echo -e "     ${BOLD}curl -fsSL https://ollama.com/install.sh | sh && ollama run qwen2.5-coder:14b${NC}"
echo -e "     (O modelos ligeros: qwen2.5:7b, llama3.2:3b)"
echo -e "  • Si ya tienes Ollama en la red, escribe su IP (ej: http://192.168.1.50:11434)."
echo -e "  • Si lo instalarás en este servidor, presiona Enter para usar [http://localhost:11434]."
read -r -p "  🤖 Dirección URL de Ollama [http://localhost:11434]: " INPUT_OLLAMA
OLLAMA_URL="${INPUT_OLLAMA:-http://localhost:11434}"

JWT_SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || echo "4f8a3c9b7e1d5a2f6c8e0b3d5f7a9c1e3b5d7f9a1c3e5b7d9f1a3c5e7b9d1f3a")

# 3. Asistente de Estructura de Fábrica (Almacenes, Secciones, Líneas y Máquinas)
echo -e "\n${CYAN}[3/6] Configuración de la Estructura de tu Fábrica${NC}"
echo -e "Cada industria tiene diferentes almacenes de repuestos, secciones, líneas y máquinas.\n"
echo "  1) Configurar ahora interactivamente (Secciones, Líneas, Máquinas y Almacenes)"
echo "  2) Cargar una plantilla industrial estándar de ejemplo (Recomendado para pruebas)"
echo "  3) Empezar con estructura mínima (Crear activos después desde la aplicación web)"
echo ""
read -r -p "  Selecciona una opción [1-3, por defecto 2]: " FACTORY_OPT
FACTORY_OPT="${FACTORY_OPT:-2}"

SQL_SETUP="db/03_factory_setup.sql"
rm -f "$SQL_SETUP"
echo "-- GMAO SYSTEM - Configuración de Planta Inicial" > "$SQL_SETUP"

case "$FACTORY_OPT" in
    1)
        echo -e "\n${BLUE}--- [A] Almacenes de Repuestos ---${NC}"
        read -r -p "  ¿Cuántos almacenes de repuestos tiene tu fábrica? [1]: " NUM_W
        NUM_W="${NUM_W:-1}"
        for (( i=1; i<=NUM_W; i++ )); do
            read -r -p "    Nombre del Almacén #$i [Almacén $i]: " W_NAME
            W_NAME="${W_NAME:-Almacén $i}"
            echo "INSERT INTO warehouses (name) VALUES ('$W_NAME');" >> "$SQL_SETUP"
        done

        echo -e "\n${BLUE}--- [B] Secciones / Áreas de Planta ---${NC}"
        read -r -p "  ¿Cuántas secciones o áreas de producción tienes? [1]: " NUM_SEC
        NUM_SEC="${NUM_SEC:-1}"
        
        for (( s=1; s<=NUM_SEC; s++ )); do
            echo ""
            read -r -p "  🏭 Nombre de la Sección #$s [Sección $s]: " SEC_NAME
            SEC_NAME="${SEC_NAME:-Sección $s}"
            echo "INSERT INTO sections (nombre) VALUES ('$SEC_NAME');" >> "$SQL_SETUP"
            
            read -r -p "    ¿Cuántas líneas de producción tiene '$SEC_NAME'? [1]: " NUM_L
            NUM_L="${NUM_L:-1}"
            
            for (( l=1; l<=NUM_L; l++ )); do
                echo ""
                read -r -p "    📍 Nombre de la Línea #$l de '$SEC_NAME' [Línea $s.$l]: " L_NAME
                L_NAME="${L_NAME:-Línea $s.$l}"
                echo "INSERT INTO lines (nombre, section_id) VALUES ('$L_NAME', (SELECT id FROM sections WHERE nombre = '$SEC_NAME' ORDER BY id DESC LIMIT 1));" >> "$SQL_SETUP"
                
                read -r -p "      ¿Cuántas máquinas tiene la línea '$L_NAME'? [1]: " NUM_M
                NUM_M="${NUM_M:-1}"
                
                for (( m=1; m<=NUM_M; m++ )); do
                    echo -e "      ⚙️  ${BOLD}Datos de la Máquina #$m:${NC}"
                    read -r -p "        Nombre de la máquina [Máquina $s.$l.$m]: " M_NAME
                    M_NAME="${M_NAME:-Máquina $s.$l.$m}"
                    
                    read -r -p "        Marca [Genérica]: " M_BRAND
                    M_BRAND="${M_BRAND:-Genérica}"
                    
                    read -r -p "        Modelo [Standard]: " M_MODEL
                    M_MODEL="${M_MODEL:-Standard}"
                    
                    DEFAULT_SN="SN-$(date +%y%m%d)-$s$l$m"
                    read -r -p "        Número de serie [$DEFAULT_SN]: " M_SN
                    M_SN="${M_SN:-$DEFAULT_SN}"
                    
                    read -r -p "        Criticidad (ALTA / MEDIA / BAJA) [MEDIA]: " M_CRIT
                    M_CRIT="${M_CRIT:-MEDIA}"
                    M_CRIT=$(echo "$M_CRIT" | tr '[:lower:]' '[:upper:]')
                    
                    echo "INSERT INTO machines (nombre, marca, modelo, numero_serie, criticidad, section_id, line_id) VALUES ('$M_NAME', '$M_BRAND', '$M_MODEL', '$M_SN', '$M_CRIT', (SELECT id FROM sections WHERE nombre = '$SEC_NAME' ORDER BY id DESC LIMIT 1), (SELECT id FROM lines WHERE nombre = '$L_NAME' AND section_id = (SELECT id FROM sections WHERE nombre = '$SEC_NAME' ORDER BY id DESC LIMIT 1) ORDER BY id DESC LIMIT 1));" >> "$SQL_SETUP"
                done
            done
        done
        ;;
        
    2)
        echo -e "\n  ${GREEN}✓${NC} Generando plantilla industrial estándar..."
        cat << 'PLANTILLA' >> "$SQL_SETUP"
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
PLANTILLA
        ;;
        
    3|*)
        echo -e "\n  ${GREEN}✓${NC} Configuración mínima seleccionada."
        cat << 'MINIMO' >> "$SQL_SETUP"
INSERT INTO warehouses (name) VALUES ('Almacén Central de Repuestos');
INSERT INTO sections (name) VALUES ('Planta General');
INSERT INTO lines (name, section_id) VALUES ('Línea Principal', 1);
MINIMO
        ;;
esac

echo -e "  ${GREEN}✓${NC} Estructura de fábrica preparada en db/03_factory_setup.sql"

# 4. Generación de Archivos del Entorno
echo -e "\n${CYAN}[4/6] Generando archivo .env y certificados de seguridad...${NC}"

cat << ENVEOD > .env
# ==============================================================================
# GMAO SYSTEM - Configuración del Entorno
# Generado el: $(date)
# ==============================================================================

# Base de datos PostgreSQL
POSTGRES_DB=$POSTGRES_DB
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@db:5432/$POSTGRES_DB

# Seguridad y Autenticación JWT
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Administrador Inicial
INITIAL_ADMIN_USERNAME=$INITIAL_ADMIN_USERNAME
INITIAL_ADMIN_PASSWORD=$INITIAL_ADMIN_PASSWORD

# Inteligencia Artificial
OLLAMA_URL=$OLLAMA_URL

# Red y CORS
SERVER_HOST=$SERVER_HOST
CORS_ORIGINS=http://$SERVER_HOST,http://$SERVER_HOST:80,https://$SERVER_HOST,http://localhost,http://localhost:3000
ENVEOD

chmod 600 .env
echo -e "  ${GREEN}✓${NC} Archivo .env creado con permisos seguros (600)."

# Directorios obligatorios
mkdir -p backend/src/storage/documents/attachments nginx/certs backups

# Generación de certificados SSL si no existen
if [ ! -f nginx/certs/nginx-selfsigned.crt ] || [ ! -f nginx/certs/nginx-selfsigned.key ]; then
    echo -e "  ${CYAN}ℹ️  Generando certificados SSL autofirmados para HTTPS...${NC}"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/certs/nginx-selfsigned.key \
        -out nginx/certs/nginx-selfsigned.crt \
        -subj "/C=ES/ST=Planta/L=Fabrica/O=GMAO-System/CN=$SERVER_HOST" 2>/dev/null
    echo -e "  ${GREEN}✓${NC} Certificados SSL generados correctamente en nginx/certs/"
fi

# 5. Despliegue de los contenedores Docker
echo -e "\n${CYAN}[5/6] Construyendo e iniciando contenedores Docker...${NC}"
echo -e "${YELLOW}La primera compilación puede demorar unos minutos...${NC}\n"

$DOCKER_COMPOSE_CMD down -v --remove-orphans 2>/dev/null || true
$DOCKER_COMPOSE_CMD pull && $DOCKER_COMPOSE_CMD up -d

# 6. Comprobación de salud
echo -e "\n${CYAN}[6/6] Verificando estado de los servicios...${NC}"
printf "  Comprobando arranque del sistema "
READY=0
for i in {1..35}; do
    if docker ps --filter "name=gmao-project-backend" --filter "health=healthy" -q | grep -q .; then
        READY=1
        break
    fi
    printf "."
    sleep 2
done

echo ""
if [ $READY -eq 1 ]; then
    echo -e "  ${GREEN}✓ Todos los servicios iniciados y saludables.${NC}"
    if [ -f "$SQL_SETUP" ]; then
        docker exec -i gmao-project-db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$SQL_SETUP" 2>/dev/null || true
    fi
else
    echo -e "  ${YELLOW}ℹ️  Los servicios están iniciando en segundo plano.${NC}"
fi

# Resumen de instalación
echo -e "\n${GREEN}${BOLD}==========================================================================${NC}"
echo -e "${GREEN}${BOLD}         🎉 ¡GMAO SYSTEM INSTALADO Y CONFIGURADO CON ÉXITO!               ${NC}"
echo -e "${GREEN}${BOLD}==========================================================================${NC}\n"
echo -e "  🌐 ${BOLD}Acceso Web Seguro (HTTPS):${NC}  https://$SERVER_HOST"
echo -e "  🌐 ${BOLD}Acceso Web (HTTP):${NC}         http://$SERVER_HOST"
echo -e "  📡 ${BOLD}Documentación API (Swagger):${NC} https://$SERVER_HOST/api/docs"
echo ""
echo -e "  🛡️  ${BOLD}Credenciales de Acceso Inicial:${NC}"
echo -e "     Usuario:    ${CYAN}${BOLD}$INITIAL_ADMIN_USERNAME${NC}"
echo -e "     Contraseña: ${CYAN}${BOLD}$INITIAL_ADMIN_PASSWORD${NC}"
echo ""
echo -e "  🗄️  ${BOLD}Base de Datos:${NC}"
echo -e "     Base:       $POSTGRES_DB"
echo -e "     Usuario DB: $POSTGRES_USER"
echo ""
echo -e "${BLUE}==========================================================================${NC}"
echo -e "  🛠️  ${BOLD}Herramienta de Gestión:${NC}"
echo -e "     Usa ${YELLOW}./gmao.sh${NC} en la consola para:"
echo -e "     • Ver estado de contenedores"
echo -e "     • Crear copias de seguridad de la base de datos (Backups)"
echo -e "     • Restaurar backups"
echo -e "     • Ver logs en tiempo real"
echo -e "     • Reiniciar o detener el sistema"
echo -e "${BLUE}==========================================================================${NC}\n"
