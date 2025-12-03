#!/bin/bash
# Run integration tests for Gemini Video system
#
# Usage:
#   ./scripts/run_integration_tests.sh           # Run all integration tests
#   ./scripts/run_integration_tests.sh --fast    # Run only fast tests
#   ./scripts/run_integration_tests.sh --verify  # Run deployment verification only

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Gemini Video Integration Test Suite${NC}"
echo -e "${BLUE}============================================${NC}"

# Check if services are running
echo -e "\n${YELLOW}Checking if services are running...${NC}"
services=(
    "http://localhost:8000/health:Gateway API"
    "http://localhost:8001/health:Drive Intel"
    "http://localhost:8002/health:Video Agent"
    "http://localhost:8003/health:ML Service"
)

all_running=true
for service in "${services[@]}"; do
    IFS=':' read -r url name <<< "$service"
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is running"
    else
        echo -e "${RED}✗${NC} $name is NOT running"
        all_running=false
    fi
done

if [ "$all_running" = false ]; then
    echo -e "\n${RED}ERROR: Not all services are running!${NC}"
    echo -e "${YELLOW}Please start services with: ./scripts/start-all.sh${NC}"
    exit 1
fi

echo -e "\n${GREEN}All services are running!${NC}"

# Run deployment verification first
if [ "$1" = "--verify" ]; then
    echo -e "\n${BLUE}Running deployment verification...${NC}"
    python3 scripts/verify_deployment.py
    exit $?
fi

# Install test dependencies if needed
if [ ! -f "tests/.deps_installed" ]; then
    echo -e "\n${YELLOW}Installing test dependencies...${NC}"
    pip install -q -r tests/requirements.txt
    touch tests/.deps_installed
fi

# Run integration tests
echo -e "\n${BLUE}Running integration tests...${NC}"

cd "$(dirname "$0")/.."

if [ "$1" = "--fast" ]; then
    # Run only fast tests (exclude slow ones)
    pytest tests/integration/ -v -m "not slow" --tb=short
else
    # Run all integration tests
    pytest tests/integration/ -v --tb=short
fi

test_result=$?

echo -e "\n${BLUE}============================================${NC}"
if [ $test_result -eq 0 ]; then
    echo -e "${GREEN}✓ All integration tests passed!${NC}"
else
    echo -e "${RED}✗ Some integration tests failed${NC}"
    echo -e "${YELLOW}Review the output above for details${NC}"
fi
echo -e "${BLUE}============================================${NC}"

exit $test_result
