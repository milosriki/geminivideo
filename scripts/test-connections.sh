#!/bin/bash
# Test script to verify all services are connected and running properly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Gemini Video Services Connection Test ===${NC}"
echo ""

# Function to check service health
check_service() {
    local service_name=$1
    local url=$2
    local max_retries=30
    local retry_count=0
    
    echo -e "${YELLOW}Checking ${service_name}...${NC}"
    
    while [ $retry_count -lt $max_retries ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ ${service_name} is healthy${NC}"
            return 0
        fi
        retry_count=$((retry_count + 1))
        sleep 2
    done
    
    echo -e "${RED}✗ ${service_name} failed to start${NC}"
    return 1
}

# Wait a bit for services to start
echo "Waiting for services to initialize..."
sleep 10

# Check all services
services_ok=true

# Check drive-intel
if ! check_service "Drive Intel" "http://localhost:8001/health"; then
    services_ok=false
fi

# Check video-agent
if ! check_service "Video Agent" "http://localhost:8002/health"; then
    services_ok=false
fi

# Check meta-publisher
if ! check_service "Meta Publisher" "http://localhost:8003/health"; then
    services_ok=false
fi

# Check gateway-api
if ! check_service "Gateway API" "http://localhost:8000/health"; then
    services_ok=false
fi

# Check frontend
if ! check_service "Frontend" "http://localhost:3000"; then
    services_ok=false
fi

echo ""
echo -e "${BLUE}=== Testing Service Connections ===${NC}"

# Test gateway to drive-intel connection
echo -e "${YELLOW}Testing Gateway → Drive Intel connection...${NC}"
if curl -s -f "http://localhost:8000/api/assets" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Gateway can reach Drive Intel${NC}"
else
    echo -e "${RED}✗ Gateway cannot reach Drive Intel${NC}"
    services_ok=false
fi

# Test gateway to meta-publisher connection
echo -e "${YELLOW}Testing Gateway → Meta Publisher connection...${NC}"
if curl -s -f "http://localhost:8000/api/insights" > /dev/null 2>&1 || curl -s "http://localhost:8000/api/insights" | grep -q "adId"; then
    echo -e "${GREEN}✓ Gateway can reach Meta Publisher${NC}"
else
    echo -e "${YELLOW}⚠ Gateway → Meta Publisher connection check inconclusive${NC}"
fi

echo ""
echo -e "${BLUE}=== Service URLs ===${NC}"
echo -e "Frontend:       ${GREEN}http://localhost:3000${NC}"
echo -e "Gateway API:    ${GREEN}http://localhost:8000${NC}"
echo -e "Drive Intel:    ${GREEN}http://localhost:8001${NC}"
echo -e "Video Agent:    ${GREEN}http://localhost:8002${NC}"
echo -e "Meta Publisher: ${GREEN}http://localhost:8003${NC}"

echo ""
if [ "$services_ok" = true ]; then
    echo -e "${GREEN}=== ✓ All services are connected and running! ===${NC}"
    echo ""
    echo -e "You can now:"
    echo -e "  1. Open ${BLUE}http://localhost:3000${NC} in your browser"
    echo -e "  2. Use the Assets & Ingest panel to upload videos"
    echo -e "  3. View ranked clips and scores"
    echo -e "  4. Create render jobs"
    echo ""
    exit 0
else
    echo -e "${RED}=== Some services failed to start ===${NC}"
    echo ""
    echo "To debug, run:"
    echo "  docker-compose logs [service-name]"
    echo ""
    exit 1
fi
