#!/bin/bash
# Comprehensive script to start all services and verify connections

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Gemini Video - Start All Services ===${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose not found. Please install it first.${NC}"
    exit 1
fi

# Stop any existing services
echo -e "${YELLOW}Stopping any existing services...${NC}"
docker-compose down > /dev/null 2>&1 || true

# Clean up old containers
echo -e "${YELLOW}Cleaning up old containers...${NC}"
docker-compose rm -f > /dev/null 2>&1 || true

# Build and start all services
echo -e "${YELLOW}Building and starting all services...${NC}"
echo -e "${YELLOW}This may take a few minutes on first run...${NC}"
echo ""

docker-compose up -d --build

# Wait for services to be ready
echo ""
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 5

# Run connection test
echo ""
if [ -f "./scripts/test-connections.sh" ]; then
    chmod +x ./scripts/test-connections.sh
    ./scripts/test-connections.sh
else
    echo -e "${GREEN}All services started!${NC}"
    echo ""
    echo -e "Service URLs:"
    echo -e "  Frontend:       ${BLUE}http://localhost:3000${NC}"
    echo -e "  Gateway API:    ${BLUE}http://localhost:8000${NC}"
    echo -e "  Drive Intel:    ${BLUE}http://localhost:8001${NC}"
    echo -e "  Video Agent:    ${BLUE}http://localhost:8002${NC}"
    echo -e "  Meta Publisher: ${BLUE}http://localhost:8003${NC}"
    echo ""
    echo -e "To view logs: ${YELLOW}docker-compose logs -f${NC}"
    echo -e "To stop: ${YELLOW}docker-compose down${NC}"
fi
