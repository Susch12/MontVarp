#!/bin/bash
# ============================================
# start.sh - Sistema VarP Monte Carlo
# Versión mejorada con construcción manual
# ============================================

set -e

# ============================================
# Colores
# ============================================
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================
# Funciones auxiliares
# ============================================

print_header() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

show_help() {
    cat << EOF
Sistema VarP Monte Carlo - Start Script

USO:
    ./start.sh [OPCIONES] [CONSUMIDORES]

OPCIONES:
    --build         Reconstruir imágenes de Docker antes de iniciar
    --no-cache      Construir sin usar cache
    --help          Mostrar esta ayuda

ARGUMENTOS:
    CONSUMIDORES    Número de consumidores a iniciar (default: 1)

EJEMPLOS:
    ./start.sh                    # Iniciar con 1 consumidor
    ./start.sh 5                  # Iniciar con 5 consumidores
    ./start.sh --build            # Reconstruir e iniciar
    ./start.sh --build 3          # Reconstruir e iniciar con 3 consumidores
    ./start.sh --no-cache 5       # Construir sin cache + 5 consumidores

URLS:
    Dashboard:        http://localhost:8050
    RabbitMQ Admin:   http://localhost:15672 (admin/password)

EOF
    exit 0
}

# ============================================
# Parsear argumentos
# ============================================

BUILD=false
NO_CACHE=false
NUM_CONSUMERS=1

while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            BUILD=true
            shift
            ;;
        --no-cache)
            BUILD=true
            NO_CACHE=true
            shift
            ;;
        --help|-h)
            show_help
            ;;
        [0-9]*)
            NUM_CONSUMERS=$1
            shift
            ;;
        *)
            print_error "Argumento desconocido: $1"
            echo "Usar --help para ver opciones"
            exit 1
            ;;
    esac
done

# ============================================
# Validaciones
# ============================================

print_header "INICIANDO SISTEMA VarP"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker no está instalado"
    exit 1
fi

print_success "Docker encontrado: $(docker --version | head -n1 | cut -d',' -f1)"

# Verificar Docker Compose
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
    print_success "docker compose encontrado: v$(docker compose version --short 2>/dev/null || echo 'installed')"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    print_success "docker-compose encontrado"
else
    print_error "docker compose no está instalado"
    exit 1
fi

# Verificar .env
if [ ! -f .env ]; then
    print_warning "Archivo .env no encontrado"
    print_info "Copiando .env.example a .env..."
    cp .env.example .env
    print_success ".env creado desde .env.example"
fi

# Verificar Docker daemon
if ! docker info &> /dev/null; then
    print_error "Docker daemon no está corriendo"
    exit 1
fi

print_success "Docker daemon corriendo"

# ============================================
# Build (construcción manual para evitar buildx)
# ============================================

if [ "$BUILD" = true ]; then
    print_header "CONSTRUYENDO IMÁGENES"
    
    # Habilitar BuildKit
    export DOCKER_BUILDKIT=1
    
    BUILD_ARGS=""
    if [ "$NO_CACHE" = true ]; then
        BUILD_ARGS="--no-cache"
        print_info "Construyendo sin cache..."
    fi
    
    # Construir Producer
    print_info "Construyendo varp-producer..."
    docker build $BUILD_ARGS -f Dockerfile.producer -t varp-producer . || {
        print_error "Error construyendo producer"
        exit 1
    }
    print_success "Producer construido"
    
    # Construir Consumer
    print_info "Construyendo varp-consumer..."
    docker build $BUILD_ARGS -f Dockerfile.consumer -t varp-consumer . || {
        print_error "Error construyendo consumer"
        exit 1
    }
    print_success "Consumer construido"
    
    # Construir Dashboard
    print_info "Construyendo varp-dashboard..."
    docker build $BUILD_ARGS -f Dockerfile.dashboard -t varp-dashboard . || {
        print_error "Error construyendo dashboard"
        exit 1
    }
    print_success "Dashboard construido"
    
    print_success "Todas las imágenes construidas exitosamente"
fi

# ============================================
# Verificar que las imágenes existen
# ============================================

print_header "VERIFICANDO IMÁGENES"

IMAGES_OK=true
for img in varp-producer varp-consumer varp-dashboard; do
    if docker image inspect $img &> /dev/null; then
        print_success "Imagen $img encontrada"
    else
        print_error "Imagen $img no encontrada"
        IMAGES_OK=false
    fi
done

if [ "$IMAGES_OK" = false ]; then
    print_warning "Algunas imágenes no existen. Construyendo..."
    
    # Construir automáticamente
    export DOCKER_BUILDKIT=1
    
    docker build -f Dockerfile.producer -t varp-producer . && print_success "Producer construido"
    docker build -f Dockerfile.consumer -t varp-consumer . && print_success "Consumer construido"
    docker build -f Dockerfile.dashboard -t varp-dashboard . && print_success "Dashboard construido"
fi

# ============================================
# Iniciar servicios
# ============================================

print_header "INICIANDO SERVICIOS"

print_info "Iniciando servicios con Docker Compose..."

if [ "$NUM_CONSUMERS" -eq 1 ]; then
    $DOCKER_COMPOSE up -d
else
    print_info "Escalando a $NUM_CONSUMERS consumidores..."
    $DOCKER_COMPOSE up -d --scale consumer=$NUM_CONSUMERS
fi

print_success "Servicios iniciados"

# ============================================
# Esperar a RabbitMQ
# ============================================

print_header "ESPERANDO SERVICIOS"

print_info "Esperando a RabbitMQ..."
sleep 5

# Verificar RabbitMQ
MAX_RETRIES=12
RETRY_COUNT=0
RABBITMQ_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -u admin:password http://localhost:15672/api/overview > /dev/null 2>&1; then
        RABBITMQ_READY=true
        break
    fi
    
    sleep 5
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
done

echo ""

if [ "$RABBITMQ_READY" = true ]; then
    print_success "RabbitMQ está listo"
else
    print_warning "RabbitMQ tardó en iniciar, pero continuamos..."
fi

# ============================================
# Estado de servicios
# ============================================

print_header "ESTADO DE SERVICIOS"

$DOCKER_COMPOSE ps

# ============================================
# Información de acceso
# ============================================

print_header "SISTEMA INICIADO"

print_success "Sistema VarP corriendo exitosamente"
echo ""
print_info "URLs de acceso:"
echo "  Dashboard:      ${GREEN}http://localhost:8050${NC}"
echo "  RabbitMQ Admin: ${GREEN}http://localhost:15672${NC}"
echo "    Usuario:      admin"
echo "    Password:     password"
echo ""
print_info "Servicios corriendo:"
echo "  - RabbitMQ:     1 instancia"
echo "  - Producer:     1 instancia"
echo "  - Consumer:     $NUM_CONSUMERS instancia(s)"
echo "  - Dashboard:    1 instancia"
echo ""
print_info "Comandos útiles:"
echo "  Ver logs:       ${YELLOW}${DOCKER_COMPOSE} logs -f${NC}"
echo "  Ver producer:   ${YELLOW}${DOCKER_COMPOSE} logs -f producer${NC}"
echo "  Ver consumers:  ${YELLOW}${DOCKER_COMPOSE} logs -f consumer${NC}"
echo "  Ver dashboard:  ${YELLOW}${DOCKER_COMPOSE} logs -f dashboard${NC}"
echo "  Detener:        ${YELLOW}./stop.sh${NC}"
echo "  Limpiar colas:  ${YELLOW}./clean_queues.sh${NC}"
echo ""
