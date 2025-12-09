#!/bin/bash
# Group A Verification Script
# Checks: Gateway API, Frontend, Docker, Config

echo "======================================"
echo "GROUP A VERIFICATION CHECKLIST"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
        return 0
    else
        echo -e "${RED}✗${NC} $2 - MISSING: $1"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
        return 0
    else
        echo -e "${RED}✗${NC} $2 - MISSING: $1"
        return 1
    fi
}

echo "📁 GATEWAY API"
echo "─────────────────────────────────────"
check_file "services/gateway-api/src/index.ts" "Main server file"
check_dir "services/gateway-api/src/routes" "Routes directory"
check_file "services/gateway-api/src/webhooks/hubspot.ts" "HubSpot webhook"
check_dir "services/gateway-api/src/realtime" "Realtime infrastructure"
check_file "services/gateway-api/Dockerfile" "Dockerfile"
echo ""

echo "🎨 FRONTEND"
echo "─────────────────────────────────────"
check_file "frontend/src/App.tsx" "Main App component"
check_dir "frontend/src/pages" "Pages directory"
check_dir "frontend/src/components" "Components directory"
check_dir "frontend/src/hooks" "Hooks directory"
check_file "frontend/src/components/ErrorBoundary.tsx" "Error boundary"
check_file "frontend/src/components/LoadingScreen.tsx" "Loading screen"
check_file "frontend/Dockerfile" "Dockerfile"
echo ""

echo "🐳 DOCKER"
echo "─────────────────────────────────────"
check_file "docker-compose.yml" "Docker Compose main"
check_file "docker-compose.production.yml" "Docker Compose production"

# Check for Celery services in docker-compose
if grep -q "celery-worker" docker-compose.yml 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Celery worker service configured"
else
    echo -e "${RED}✗${NC} Celery worker service MISSING"
fi

if grep -q "celery-beat" docker-compose.yml 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Celery beat service configured"
else
    echo -e "${RED}✗${NC} Celery beat service MISSING"
fi
echo ""

echo "⚙️ CONFIG"
echo "─────────────────────────────────────"
check_dir "shared/config" "Config directory"
check_file ".env.example" "Environment example"
echo ""

echo "🔌 ASYNC PROCESSING (Agent 5 & 13)"
echo "─────────────────────────────────────"
if grep -q "ASYNC_MODE" services/gateway-api/src/webhooks/hubspot.ts 2>/dev/null; then
    echo -e "${GREEN}✓${NC} HubSpot async mode implemented"
else
    echo -e "${YELLOW}⚠${NC} HubSpot async mode not found"
fi

if grep -q "queueCeleryTask" services/gateway-api/src/webhooks/hubspot.ts 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Celery task queueing implemented"
else
    echo -e "${YELLOW}⚠${NC} Celery task queueing not found"
fi
echo ""

echo "======================================"
echo "VERIFICATION COMPLETE"
echo "======================================"
