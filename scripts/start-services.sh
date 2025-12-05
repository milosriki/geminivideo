#!/bin/bash
# ============================================================================
# SERVICE STARTUP ORCHESTRATOR
# €5M Investment-Grade Ad Platform
# ============================================================================
# Handles correct startup order, dependencies, and health checks
# Supports both --dev and --prod modes

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default mode
MODE="dev"
DOCKER_MODE="docker"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --prod) MODE="prod" ;;
        --dev) MODE="dev" ;;
        --direct) DOCKER_MODE="direct" ;;
        --help)
            echo "Usage: $0 [--dev|--prod] [--direct]"
            echo "  --dev     Start in development mode (default)"
            echo "  --prod    Start in production mode"
            echo "  --direct  Start services directly (not in Docker)"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     SERVICE STARTUP ORCHESTRATOR - €5M Ad Platform        ║${NC}"
echo -e "${CYAN}║              Mode: ${MODE^^} | Docker: ${DOCKER_MODE^^}                ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Check if health-check script exists
if [ ! -f "$SCRIPT_DIR/health-check.sh" ]; then
    echo -e "${RED}✗ health-check.sh not found!${NC}"
    exit 1
fi

# Function to check health of a service
check_health() {
    local service=$1
    local port=$2
    local endpoint=${3:-/health}
    local max_attempts=${4:-30}
    local attempt=0

    echo -e "${BLUE}⏳ Waiting for $service on port $port...${NC}"

    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s "http://localhost:$port$endpoint" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $service is healthy${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -ne "${YELLOW}.${NC}"
        sleep 2
    done

    echo -e "${RED}✗ $service failed to start after $max_attempts attempts${NC}"
    return 1
}

# Function to wait for database
wait_for_db() {
    echo -e "${BLUE}⏳ Waiting for PostgreSQL...${NC}"
    local attempt=0
    local max_attempts=30

    while [ $attempt -lt $max_attempts ]; do
        if docker compose exec -T postgres pg_isready -U geminivideo > /dev/null 2>&1; then
            echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -ne "${YELLOW}.${NC}"
        sleep 2
    done

    echo -e "${RED}✗ PostgreSQL failed to start${NC}"
    return 1
}

# Function to wait for Redis
wait_for_redis() {
    echo -e "${BLUE}⏳ Waiting for Redis...${NC}"
    local attempt=0
    local max_attempts=30

    while [ $attempt -lt $max_attempts ]; do
        if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Redis is ready${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -ne "${YELLOW}.${NC}"
        sleep 2
    done

    echo -e "${RED}✗ Redis failed to start${NC}"
    return 1
}

# Change to root directory
cd "$ROOT_DIR"

if [ "$DOCKER_MODE" = "docker" ]; then
    # ========================================================================
    # DOCKER MODE - Start services with Docker Compose
    # ========================================================================

    echo -e "${CYAN}═══ Phase 1: Infrastructure Services ═══${NC}"
    echo ""

    # Stop any existing services
    echo -e "${YELLOW}⏹  Stopping existing services...${NC}"
    if [ "$MODE" = "prod" ]; then
        docker compose -f docker-compose.yml -f docker-compose.prod.yml down --remove-orphans
    else
        docker compose down --remove-orphans
    fi
    echo ""

    # Start infrastructure services (PostgreSQL and Redis)
    echo -e "${GREEN}▶  Starting PostgreSQL and Redis...${NC}"
    docker compose up -d postgres redis

    # Wait for databases
    wait_for_db || exit 1
    wait_for_redis || exit 1
    echo ""

    echo -e "${CYAN}═══ Phase 2: Core Backend Services ═══${NC}"
    echo ""

    # Start ML service (has no other service dependencies)
    echo -e "${GREEN}▶  Starting ML Service...${NC}"
    docker compose up -d ml-service
    check_health "ml-service" 8003 || exit 1
    echo ""

    # Start titan-core (needs Redis and API keys configured)
    echo -e "${GREEN}▶  Starting Titan Core AI Council...${NC}"
    docker compose up -d titan-core
    check_health "titan-core" 8084 || exit 1
    echo ""

    # Start video-agent (needs PostgreSQL and Redis)
    echo -e "${GREEN}▶  Starting Video Agent...${NC}"
    docker compose up -d video-agent
    check_health "video-agent" 8082 || exit 1
    echo ""

    # Start drive-intel (needs PostgreSQL and Redis)
    echo -e "${GREEN}▶  Starting Drive Intel...${NC}"
    docker compose up -d drive-intel
    check_health "drive-intel" 8081 || exit 1
    echo ""

    echo -e "${CYAN}═══ Phase 3: Publishing Services ═══${NC}"
    echo ""

    # Start meta-publisher
    echo -e "${GREEN}▶  Starting Meta Publisher...${NC}"
    docker compose up -d meta-publisher
    check_health "meta-publisher" 8083 || exit 1
    echo ""

    # Start tiktok-ads
    echo -e "${GREEN}▶  Starting TikTok Ads...${NC}"
    docker compose up -d tiktok-ads
    check_health "tiktok-ads" 8085 || exit 1
    echo ""

    echo -e "${CYAN}═══ Phase 4: Gateway & Workers ═══${NC}"
    echo ""

    # Start gateway-api (needs all backend services)
    echo -e "${GREEN}▶  Starting Gateway API...${NC}"
    docker compose up -d gateway-api
    check_health "gateway-api" 8080 "/health" || exit 1
    echo ""

    # Start background workers
    echo -e "${GREEN}▶  Starting Background Workers...${NC}"
    docker compose up -d drive-worker video-worker
    echo -e "${GREEN}✓ Workers started${NC}"
    echo ""

    echo -e "${CYAN}═══ Phase 5: Frontend ═══${NC}"
    echo ""

    # Start frontend (needs gateway-api)
    echo -e "${GREEN}▶  Starting Frontend...${NC}"
    docker compose up -d frontend
    sleep 5
    check_health "frontend" 3000 "/" 60 || echo -e "${YELLOW}⚠ Frontend may still be building...${NC}"
    echo ""

else
    # ========================================================================
    # DIRECT MODE - Start services directly (for development)
    # ========================================================================

    echo -e "${YELLOW}⚠  Direct mode - services will run in background${NC}"
    echo -e "${YELLOW}   Use 'scripts/stop-services.sh' to stop them${NC}"
    echo ""

    # This mode assumes databases are running in Docker
    echo -e "${CYAN}═══ Checking Infrastructure ═══${NC}"
    docker compose up -d postgres redis
    wait_for_db || exit 1
    wait_for_redis || exit 1
    echo ""

    # Create logs directory
    mkdir -p "$ROOT_DIR/logs"

    echo -e "${CYAN}═══ Starting Services Directly ═══${NC}"
    echo ""

    # Start ML Service
    echo -e "${GREEN}▶  Starting ML Service...${NC}"
    cd "$ROOT_DIR/services/ml-service"
    PORT=8003 python -m src.main > "$ROOT_DIR/logs/ml-service.log" 2>&1 &
    echo $! > "$ROOT_DIR/logs/ml-service.pid"
    cd "$ROOT_DIR"
    sleep 3
    check_health "ml-service" 8003 || exit 1
    echo ""

    # Start Titan Core
    echo -e "${GREEN}▶  Starting Titan Core...${NC}"
    cd "$ROOT_DIR/services/titan-core"
    PORT=8084 python main.py > "$ROOT_DIR/logs/titan-core.log" 2>&1 &
    echo $! > "$ROOT_DIR/logs/titan-core.pid"
    cd "$ROOT_DIR"
    sleep 3
    check_health "titan-core" 8084 || exit 1
    echo ""

    # Start Video Agent
    echo -e "${GREEN}▶  Starting Video Agent...${NC}"
    cd "$ROOT_DIR/services/video-agent"
    PORT=8082 python main.py > "$ROOT_DIR/logs/video-agent.log" 2>&1 &
    echo $! > "$ROOT_DIR/logs/video-agent.pid"
    cd "$ROOT_DIR"
    sleep 3
    check_health "video-agent" 8082 || exit 1
    echo ""

    # Start Gateway API
    echo -e "${GREEN}▶  Starting Gateway API...${NC}"
    cd "$ROOT_DIR/services/gateway-api"
    PORT=8080 npm start > "$ROOT_DIR/logs/gateway-api.log" 2>&1 &
    echo $! > "$ROOT_DIR/logs/gateway-api.pid"
    cd "$ROOT_DIR"
    sleep 5
    check_health "gateway-api" 8080 "/health" || exit 1
    echo ""

    # Start Meta Publisher
    echo -e "${GREEN}▶  Starting Meta Publisher...${NC}"
    cd "$ROOT_DIR/services/meta-publisher"
    PORT=8083 npm start > "$ROOT_DIR/logs/meta-publisher.log" 2>&1 &
    echo $! > "$ROOT_DIR/logs/meta-publisher.pid"
    cd "$ROOT_DIR"
    sleep 3
    check_health "meta-publisher" 8083 || exit 1
    echo ""

    # Start Frontend
    echo -e "${GREEN}▶  Starting Frontend...${NC}"
    cd "$ROOT_DIR/frontend"
    PORT=3000 npm run dev > "$ROOT_DIR/logs/frontend.log" 2>&1 &
    echo $! > "$ROOT_DIR/logs/frontend.pid"
    cd "$ROOT_DIR"
    echo -e "${GREEN}✓ Frontend started (building...)${NC}"
    echo ""
fi

# ========================================================================
# FINAL HEALTH CHECK
# ========================================================================

echo -e "${CYAN}═══ Final Health Check ═══${NC}"
echo ""

bash "$SCRIPT_DIR/health-check.sh"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              ALL SERVICES STARTED SUCCESSFULLY!            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Service URLs:${NC}"
    echo -e "  ${BLUE}Frontend:${NC}        http://localhost:3000"
    echo -e "  ${BLUE}Gateway API:${NC}     http://localhost:8080"
    echo -e "  ${BLUE}Drive Intel:${NC}     http://localhost:8081"
    echo -e "  ${BLUE}Video Agent:${NC}     http://localhost:8082"
    echo -e "  ${BLUE}Meta Publisher:${NC}  http://localhost:8083"
    echo -e "  ${BLUE}Titan Core:${NC}      http://localhost:8084"
    echo -e "  ${BLUE}TikTok Ads:${NC}      http://localhost:8085"
    echo -e "  ${BLUE}ML Service:${NC}      http://localhost:8003"
    echo -e "  ${BLUE}PostgreSQL:${NC}      localhost:5432"
    echo -e "  ${BLUE}Redis:${NC}           localhost:6379"
    echo ""
    echo -e "${CYAN}Logs:${NC}"
    if [ "$DOCKER_MODE" = "docker" ]; then
        echo -e "  ${YELLOW}docker compose logs -f [service-name]${NC}"
    else
        echo -e "  ${YELLOW}tail -f logs/[service-name].log${NC}"
    fi
    echo ""
else
    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║        SOME SERVICES FAILED TO START PROPERLY             ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Check logs for details:${NC}"
    echo -e "  docker compose logs [service-name]"
    echo ""
    exit 1
fi
