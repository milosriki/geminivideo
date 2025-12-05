#!/bin/bash
# ============================================================================
# SERVICE STOP SCRIPT
# €5M Investment-Grade Ad Platform
# ============================================================================
# Gracefully stops all services in reverse order of dependencies
# Ensures proper cleanup and data persistence

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Default mode
MODE="graceful"
DOCKER_MODE="docker"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --force) MODE="force" ;;
        --direct) DOCKER_MODE="direct" ;;
        --help)
            echo "Usage: $0 [--force] [--direct]"
            echo "  --force   Force stop without graceful shutdown"
            echo "  --direct  Stop direct processes (not Docker)"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         SERVICE SHUTDOWN - €5M Ad Platform                ║${NC}"
echo -e "${CYAN}║                Mode: ${MODE^^}                              ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to root directory
cd "$ROOT_DIR"

if [ "$DOCKER_MODE" = "docker" ]; then
    # ========================================================================
    # DOCKER MODE - Stop Docker Compose services
    # ========================================================================

    echo -e "${CYAN}═══ Phase 1: Frontend Shutdown ═══${NC}"
    echo ""

    echo -e "${YELLOW}⏹  Stopping frontend...${NC}"
    docker compose stop frontend
    echo -e "${GREEN}✓ Frontend stopped${NC}"
    echo ""

    echo -e "${CYAN}═══ Phase 2: Gateway Shutdown ═══${NC}"
    echo ""

    echo -e "${YELLOW}⏹  Stopping gateway-api...${NC}"
    docker compose stop gateway-api
    echo -e "${GREEN}✓ Gateway API stopped${NC}"
    echo ""

    echo -e "${CYAN}═══ Phase 3: Workers Shutdown ═══${NC}"
    echo ""

    echo -e "${YELLOW}⏹  Stopping background workers...${NC}"
    docker compose stop drive-worker video-worker
    echo -e "${GREEN}✓ Workers stopped${NC}"
    echo ""

    echo -e "${CYAN}═══ Phase 4: Publishing Services Shutdown ═══${NC}"
    echo ""

    echo -e "${YELLOW}⏹  Stopping meta-publisher and tiktok-ads...${NC}"
    docker compose stop meta-publisher tiktok-ads
    echo -e "${GREEN}✓ Publishing services stopped${NC}"
    echo ""

    echo -e "${CYAN}═══ Phase 5: Core Backend Services Shutdown ═══${NC}"
    echo ""

    echo -e "${YELLOW}⏹  Stopping drive-intel, video-agent, titan-core, ml-service...${NC}"
    docker compose stop drive-intel video-agent titan-core ml-service
    echo -e "${GREEN}✓ Backend services stopped${NC}"
    echo ""

    echo -e "${CYAN}═══ Phase 6: Infrastructure Shutdown ═══${NC}"
    echo ""

    # Wait a bit for connections to close
    echo -e "${BLUE}⏳ Waiting for connections to close...${NC}"
    sleep 3

    echo -e "${YELLOW}⏹  Stopping redis and postgres...${NC}"
    docker compose stop redis postgres
    echo -e "${GREEN}✓ Infrastructure stopped${NC}"
    echo ""

    if [ "$MODE" = "force" ]; then
        echo -e "${RED}⚠  Force mode: Removing containers...${NC}"
        docker compose down
    fi

else
    # ========================================================================
    # DIRECT MODE - Stop direct processes
    # ========================================================================

    echo -e "${CYAN}═══ Stopping Direct Processes ═══${NC}"
    echo ""

    # Kill processes in reverse order
    SERVICES=("frontend" "meta-publisher" "gateway-api" "video-agent" "titan-core" "ml-service")

    for service in "${SERVICES[@]}"; do
        PID_FILE="$ROOT_DIR/logs/${service}.pid"
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo -e "${YELLOW}⏹  Stopping $service (PID: $PID)...${NC}"
                if [ "$MODE" = "force" ]; then
                    kill -9 $PID 2>/dev/null || true
                else
                    kill -TERM $PID 2>/dev/null || true
                    # Wait up to 10 seconds for graceful shutdown
                    for i in {1..10}; do
                        if ! ps -p $PID > /dev/null 2>&1; then
                            break
                        fi
                        sleep 1
                    done
                    # Force kill if still running
                    if ps -p $PID > /dev/null 2>&1; then
                        kill -9 $PID 2>/dev/null || true
                    fi
                fi
                echo -e "${GREEN}✓ $service stopped${NC}"
            else
                echo -e "${BLUE}ℹ  $service not running${NC}"
            fi
            rm -f "$PID_FILE"
        else
            echo -e "${BLUE}ℹ  No PID file for $service${NC}"
        fi
    done

    echo ""
    echo -e "${CYAN}═══ Stopping Infrastructure ═══${NC}"
    echo ""

    # Keep databases running in Docker
    echo -e "${BLUE}ℹ  Databases (postgres, redis) left running in Docker${NC}"
    echo -e "${BLUE}   Use 'docker compose down' to stop them${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ALL SERVICES STOPPED SUCCESSFULLY!            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$DOCKER_MODE" = "docker" ]; then
    echo -e "${CYAN}Status:${NC}"
    docker compose ps
    echo ""
    echo -e "${YELLOW}To completely remove containers and volumes:${NC}"
    echo -e "  docker compose down -v"
    echo ""
    echo -e "${YELLOW}To start again:${NC}"
    echo -e "  ./scripts/start-services.sh"
else
    echo -e "${YELLOW}To start again:${NC}"
    echo -e "  ./scripts/start-services.sh --direct"
fi
echo ""
