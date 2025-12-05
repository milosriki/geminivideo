#!/bin/bash
# =============================================================================
# Health Check Script
# =============================================================================
# Comprehensive health check for all services
# =============================================================================

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
declare -A SERVICES=(
    ["gateway-api"]="http://localhost:8080/health"
    ["titan-core"]="http://localhost:8084/health"
    ["ml-service"]="http://localhost:8003/health"
    ["video-agent"]="http://localhost:8082/health"
    ["meta-publisher"]="http://localhost:8083/health"
    ["drive-intel"]="http://localhost:8081/health"
)

declare -A INFRASTRUCTURE=(
    ["postgres"]="localhost:5432"
    ["redis"]="localhost:6379"
)

# Check service health
check_service() {
    local name=$1
    local url=$2

    if curl -f -s -o /dev/null "$url"; then
        echo -e "${GREEN}✓${NC} $name is healthy"
        return 0
    else
        echo -e "${RED}✗${NC} $name is unhealthy"
        return 1
    fi
}

# Check database
check_postgres() {
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} PostgreSQL is healthy"
        return 0
    else
        echo -e "${RED}✗${NC} PostgreSQL is unhealthy"
        return 1
    fi
}

# Check Redis
check_redis() {
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Redis is healthy"
        return 0
    else
        echo -e "${RED}✗${NC} Redis is unhealthy"
        return 1
    fi
}

# Main health check
main() {
    echo "==================================================================="
    echo "GeminiVideo Health Check"
    echo "==================================================================="
    echo ""

    local all_healthy=true

    # Check services
    echo "Checking Services..."
    for service in "${!SERVICES[@]}"; do
        if ! check_service "$service" "${SERVICES[$service]}"; then
            all_healthy=false
        fi
    done

    echo ""

    # Check infrastructure
    echo "Checking Infrastructure..."
    if ! check_postgres; then
        all_healthy=false
    fi
    if ! check_redis; then
        all_healthy=false
    fi

    echo ""
    echo "==================================================================="

    if [ "$all_healthy" = true ]; then
        echo -e "${GREEN}All systems operational${NC}"
        exit 0
    else
        echo -e "${RED}Some systems are unhealthy${NC}"
        exit 1
    fi
}

main "$@"
