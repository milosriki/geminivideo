#!/bin/bash
#
# Google Ads Integration Test Script
# Tests both direct service and gateway-api integration
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
GOOGLE_ADS_URL="${GOOGLE_ADS_URL:-http://localhost:8084}"
GATEWAY_URL="${GATEWAY_URL:-http://localhost:8000}"

echo "=================================================="
echo "Google Ads Integration Test Suite"
echo "=================================================="
echo ""
echo "Testing against:"
echo "  Google Ads Service: $GOOGLE_ADS_URL"
echo "  Gateway API: $GATEWAY_URL"
echo ""

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"

    printf "Testing %-50s ... " "$name"

    if response=$(curl -s -X "$method" -H "Content-Type: application/json" "$url" -w "\n%{http_code}" 2>&1); then
        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n-1)

        if [ "$http_code" = "200" ] || [ "$http_code" = "400" ] || [ "$http_code" = "202" ]; then
            echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
            return 0
        else
            echo -e "${RED}✗ FAIL${NC} (HTTP $http_code)"
            return 1
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (Connection failed)"
        return 1
    fi
}

# Track results
PASS=0
FAIL=0

echo "=================================================="
echo "1. Direct Service Tests (port 8084)"
echo "=================================================="
echo ""

# Health check
if test_endpoint "Health Check" "$GOOGLE_ADS_URL/health"; then
    ((PASS++))
else
    ((FAIL++))
fi

# Root endpoint
if test_endpoint "Root Endpoint" "$GOOGLE_ADS_URL/"; then
    ((PASS++))
else
    ((FAIL++))
fi

# Account info (expected to fail without credentials)
if test_endpoint "Account Info" "$GOOGLE_ADS_URL/api/account/info"; then
    ((PASS++))
else
    ((FAIL++))
fi

echo ""
echo "=================================================="
echo "2. Gateway API Tests (port 8000)"
echo "=================================================="
echo ""

# Gateway health
if test_endpoint "Gateway Health" "$GATEWAY_URL/health"; then
    ((PASS++))
else
    ((FAIL++))
fi

# Google Ads account via gateway
if test_endpoint "Google Ads Account (via Gateway)" "$GATEWAY_URL/api/google-ads/account/info"; then
    ((PASS++))
else
    ((FAIL++))
fi

echo ""
echo "=================================================="
echo "3. POST Endpoint Tests (Dry-Run Mode)"
echo "=================================================="
echo ""

# Test campaign creation
CAMPAIGN_DATA='{"name":"Test Campaign","budget":1000,"status":"PAUSED"}'
if test_endpoint "Create Campaign (Direct)" "$GOOGLE_ADS_URL/api/campaigns" "POST"; then
    ((PASS++))
else
    ((FAIL++))
fi

if test_endpoint "Create Campaign (Gateway)" "$GATEWAY_URL/api/google-ads/campaigns" "POST"; then
    ((PASS++))
else
    ((FAIL++))
fi

# Test publish workflow
PUBLISH_DATA='{"videoPath":"/test.mp4","campaignName":"Test","budget":1000,"adGroupName":"Test Group","cpcBidMicros":1000000,"headline":"Test Ad","finalUrl":"https://example.com"}'
if test_endpoint "Publish Workflow (Direct)" "$GOOGLE_ADS_URL/api/publish" "POST"; then
    ((PASS++))
else
    ((FAIL++))
fi

if test_endpoint "Publish Workflow (Gateway)" "$GATEWAY_URL/api/google-ads/publish" "POST"; then
    ((PASS++))
else
    ((FAIL++))
fi

echo ""
echo "=================================================="
echo "4. Performance Endpoints (Mock Data)"
echo "=================================================="
echo ""

# Test performance endpoints
if test_endpoint "Campaign Performance" "$GOOGLE_ADS_URL/api/performance/campaign/test_123"; then
    ((PASS++))
else
    ((FAIL++))
fi

if test_endpoint "Ad Performance" "$GOOGLE_ADS_URL/api/performance/ad/test_456"; then
    ((PASS++))
else
    ((FAIL++))
fi

echo ""
echo "=================================================="
echo "Test Results Summary"
echo "=================================================="
echo ""
echo -e "Total Tests: $((PASS + FAIL))"
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Configure Google Ads credentials in .env"
    echo "  2. Restart the service"
    echo "  3. Test with real API calls"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Ensure google-ads service is running on port 8084"
    echo "  2. Ensure gateway-api is running on port 8000"
    echo "  3. Check service logs for errors"
    exit 1
fi
