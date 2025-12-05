#!/bin/bash
# ============================================================================
# HEALTH CHECK SCRIPT
# €5M Investment-Grade Ad Platform
# ============================================================================
# Checks all services and returns JSON health report
# Exit 1 if any service is down

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Track overall health
ALL_HEALTHY=true

# Output format (json or text)
OUTPUT_FORMAT=${1:-text}

# Service configurations
declare -A SERVICES=(
    ["postgres"]="5432::pg_isready"
    ["redis"]="6379::redis"
    ["ml-service"]="8003:/health:http"
    ["titan-core"]="8084:/health:http"
    ["video-agent"]="8082:/health:http"
    ["drive-intel"]="8081:/health:http"
    ["meta-publisher"]="8083:/health:http"
    ["tiktok-ads"]="8085:/health:http"
    ["gateway-api"]="8080:/health:http"
    ["frontend"]="3000:/:http"
)

# JSON output array
JSON_OUTPUT="{"
JSON_OUTPUT+="\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
JSON_OUTPUT+="\"services\":{"

FIRST=true

check_service() {
    local service=$1
    local port=$2
    local endpoint=$3
    local type=$4

    local status="down"
    local message=""
    local response_time=""

    case $type in
        "http")
            start_time=$(date +%s%N)
            if response=$(curl -f -s -m 5 "http://localhost:$port$endpoint" 2>&1); then
                end_time=$(date +%s%N)
                response_time=$(( (end_time - start_time) / 1000000 ))
                status="healthy"
                message="OK"

                # Try to extract service info from response
                if echo "$response" | jq -e . >/dev/null 2>&1; then
                    service_name=$(echo "$response" | jq -r '.service // ""')
                    if [ -n "$service_name" ]; then
                        message="$service_name - OK"
                    fi
                fi
            else
                status="down"
                message="HTTP request failed"
                ALL_HEALTHY=false
            fi
            ;;
        "pg_isready")
            if docker compose exec -T postgres pg_isready -U geminivideo > /dev/null 2>&1; then
                status="healthy"
                message="Database ready"
            else
                status="down"
                message="Database not responding"
                ALL_HEALTHY=false
            fi
            ;;
        "redis")
            if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
                status="healthy"
                message="Redis ready"
            else
                status="down"
                message="Redis not responding"
                ALL_HEALTHY=false
            fi
            ;;
    esac

    # Output based on format
    if [ "$OUTPUT_FORMAT" = "json" ]; then
        if [ "$FIRST" = false ]; then
            JSON_OUTPUT+=","
        fi
        FIRST=false

        JSON_OUTPUT+="\"$service\":{"
        JSON_OUTPUT+="\"status\":\"$status\","
        JSON_OUTPUT+="\"port\":$port,"
        JSON_OUTPUT+="\"endpoint\":\"$endpoint\","
        JSON_OUTPUT+="\"message\":\"$message\""
        if [ -n "$response_time" ]; then
            JSON_OUTPUT+=",\"response_time_ms\":$response_time"
        fi
        JSON_OUTPUT+="}"
    else
        # Text output
        if [ "$status" = "healthy" ]; then
            printf "${GREEN}✓${NC} %-20s ${BLUE}%s${NC} - %s" "$service" "http://localhost:$port$endpoint" "$message"
            if [ -n "$response_time" ]; then
                printf " ${YELLOW}(${response_time}ms)${NC}"
            fi
            printf "\n"
        else
            printf "${RED}✗${NC} %-20s ${BLUE}%s${NC} - ${RED}%s${NC}\n" "$service" "http://localhost:$port$endpoint" "$message"
        fi
    fi
}

if [ "$OUTPUT_FORMAT" = "text" ]; then
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}             HEALTH CHECK - All Services                    ${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo ""
fi

# Check each service
for service in "${!SERVICES[@]}"; do
    config="${SERVICES[$service]}"
    IFS=':' read -r port endpoint type <<< "$config"

    check_service "$service" "$port" "$endpoint" "$type"
done

# Close JSON output
if [ "$OUTPUT_FORMAT" = "json" ]; then
    JSON_OUTPUT+="},"
    if [ "$ALL_HEALTHY" = true ]; then
        JSON_OUTPUT+="\"overall_status\":\"healthy\""
    else
        JSON_OUTPUT+="\"overall_status\":\"unhealthy\""
    fi
    JSON_OUTPUT+="}"
    echo "$JSON_OUTPUT" | jq '.'
else
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    if [ "$ALL_HEALTHY" = true ]; then
        echo -e "${GREEN}Overall Status: HEALTHY ✓${NC}"
    else
        echo -e "${RED}Overall Status: UNHEALTHY ✗${NC}"
    fi
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
fi

# Exit with appropriate code
if [ "$ALL_HEALTHY" = true ]; then
    exit 0
else
    exit 1
fi
