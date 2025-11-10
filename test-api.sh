#!/bin/bash
# API Test Script for AI Ad Intelligence Suite

set -e

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8080}"

echo "🧪 Testing AI Ad Intelligence Suite APIs"
echo "Gateway URL: $GATEWAY_URL"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo -e "\n${BLUE}Testing: $name${NC}"
    echo "  $method $endpoint"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$GATEWAY_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$GATEWAY_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "202" ]; then
        echo -e "  ${GREEN}✓ Success ($http_code)${NC}"
        echo "  Response: $(echo $body | jq -c . 2>/dev/null || echo $body)"
    else
        echo -e "  ${RED}✗ Failed ($http_code)${NC}"
        echo "  Response: $body"
    fi
}

# 1. Health check
test_endpoint "Health Check" "GET" "/health" ""

# 2. Get assets (should be empty initially)
test_endpoint "List Assets" "GET" "/assets" ""

# 3. Sync from local drive
test_endpoint "Sync Local Assets" "POST" "/ingest/drive/sync" '{"source":"local"}'

# 4. Get assets again (should have assets if test videos exist)
test_endpoint "List Assets After Sync" "GET" "/assets" ""

# 5. Test learning endpoint
test_endpoint "Update Learning Weights" "POST" "/internal/learning/update" ""

# 6. Get performance metrics
test_endpoint "Get Performance Metrics" "GET" "/performance/metrics?days=7" ""

echo -e "\n${GREEN}=========================================="
echo "Test completed!"
echo -e "==========================================${NC}"
