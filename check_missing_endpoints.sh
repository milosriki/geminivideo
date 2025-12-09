#!/bin/bash
# Check for missing or unwired API endpoints
# Compares frontend API calls with gateway-api endpoints

echo "======================================"
echo "ENDPOINT WIRING VERIFICATION"
echo "======================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "📡 GATEWAY API ROUTES"
echo "─────────────────────────────────────"

# Count routes in gateway-api
ROUTE_FILES=$(find services/gateway-api/src/routes -name "*.ts" 2>/dev/null | wc -l)
echo "Route files: $ROUTE_FILES"

# List route modules
echo ""
echo "Route modules:"
ls -1 services/gateway-api/src/routes/*.ts 2>/dev/null | while read f; do
    basename "$f" .ts | sed 's/^/  - /'
done

echo ""
echo "📱 FRONTEND HOOKS"
echo "─────────────────────────────────────"

# Count hooks
HOOK_FILES=$(find frontend/src/hooks -name "*.ts" -o -name "*.tsx" 2>/dev/null | wc -l)
echo "Hook files: $HOOK_FILES"

echo ""
echo "Hooks:"
ls -1 frontend/src/hooks/*.ts 2>/dev/null | while read f; do
    basename "$f" .ts | sed 's/^/  - /'
done

echo ""
echo "🔗 API BASE URL CHECK"
echo "─────────────────────────────────────"

# Check if API_BASE_URL is configured
if grep -r "VITE_API_BASE_URL\|API_BASE_URL" frontend/src --include="*.ts" --include="*.tsx" -l 2>/dev/null | head -1 > /dev/null; then
    echo -e "${GREEN}✓${NC} API base URL configured in frontend"
else
    echo -e "${RED}✗${NC} API base URL configuration not found"
fi

echo ""
echo "🌐 CRITICAL ENDPOINTS"
echo "─────────────────────────────────────"

# Check for key endpoints in gateway-api
check_endpoint() {
    if grep -rq "$1" services/gateway-api/src --include="*.ts" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2 - pattern: $1"
    fi
}

check_endpoint "/api/campaigns" "Campaigns endpoint"
check_endpoint "/api/analytics" "Analytics endpoint"
check_endpoint "/api/ads" "Ads endpoint"
check_endpoint "/api/ml" "ML proxy endpoints"
check_endpoint "/webhook/hubspot" "HubSpot webhook"
check_endpoint "/api/predictions" "Predictions endpoint"
check_endpoint "/api/ab-tests" "A/B Tests endpoint"
check_endpoint "/health" "Health check endpoint"

echo ""
echo "🔄 REALTIME ENDPOINTS"
echo "─────────────────────────────────────"

check_endpoint "SSE\|EventSource\|server-sent" "SSE support"
check_endpoint "WebSocket\|socket" "WebSocket support"

echo ""
echo "======================================"
echo "ENDPOINT CHECK COMPLETE"
echo "======================================"
