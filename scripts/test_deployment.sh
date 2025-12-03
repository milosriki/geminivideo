#!/bin/bash
set -e

echo "🧪 Running deployment validation tests..."

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get service URLs
GATEWAY_URL=${GATEWAY_URL:-$(gcloud run services describe gateway-api --region=us-west1 --format='value(status.url)' 2>/dev/null)}
ML_SERVICE_URL=$(gcloud run services describe ml-service --region=us-west1 --format='value(status.url)' 2>/dev/null || echo "")
META_PUBLISHER_URL=$(gcloud run services describe meta-publisher --region=us-west1 --format='value(status.url)' 2>/dev/null || echo "")
FRONTEND_URL=$(gcloud run services describe frontend --region=us-west1 --format='value(status.url)' 2>/dev/null || echo "")

echo ""
echo "📡 Service URLs:"
echo "  Gateway API:    $GATEWAY_URL"
echo "  ML Service:     $ML_SERVICE_URL"
echo "  Meta Publisher: $META_PUBLISHER_URL"
echo "  Frontend:       $FRONTEND_URL"
echo ""

# Test counter
PASSED=0
FAILED=0

# Helper function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}

    echo -n "Testing $name... "

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response, expected $expected_status)"
        ((FAILED++))
    fi
}

# Test health endpoints
echo "🏥 Health Checks:"
test_endpoint "Gateway Health" "$GATEWAY_URL/health"
test_endpoint "ML Service Health" "$ML_SERVICE_URL/health"
test_endpoint "Meta Publisher Health" "$META_PUBLISHER_URL/health"
echo ""

# Test API endpoints
echo "🔌 API Endpoints:"
test_endpoint "List Assets" "$GATEWAY_URL/api/assets"
test_endpoint "ML Model Info" "$ML_SERVICE_URL/api/ml/model-info"
test_endpoint "Meta Publisher Root" "$META_PUBLISHER_URL/"
echo ""

# Test scoring endpoint with sample data
echo "🧮 Scoring Engine:"
echo -n "Testing scoring with sample data... "
score_response=$(curl -s -X POST "$GATEWAY_URL/api/score/storyboard" \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": [
      {
        "features": {
          "text_detected": ["Transform your body", "Join now"],
          "objects": ["person", "gym"],
          "motion_score": 0.8,
          "duration": 15
        }
      }
    ],
    "metadata": {
      "target_persona": "fitness_beginner",
      "variant": "reels"
    }
  }' 2>/dev/null)

if echo "$score_response" | grep -q "prediction_id"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Response: $score_response"
    ((FAILED++))
fi
echo ""

# Test ML prediction
echo "🤖 ML Service:"
echo -n "Testing CTR prediction... "
ml_response=$(curl -s -X POST "$ML_SERVICE_URL/api/ml/predict-ctr" \
  -H "Content-Type: application/json" \
  -d '{
    "clip_data": {
      "scene_count": 3,
      "total_duration": 30,
      "text_detected": ["Transform", "Now"],
      "objects": ["person"],
      "motion_score": 0.7
    }
  }' 2>/dev/null)

if echo "$ml_response" | grep -q "predicted_ctr"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Response: $ml_response"
    ((FAILED++))
fi
echo ""

# Test frontend
echo "🎨 Frontend:"
test_endpoint "Frontend Homepage" "$FRONTEND_URL"
echo ""

# Summary
echo "========================================="
echo "📊 Test Summary:"
echo "  Passed: ${GREEN}$PASSED${NC}"
echo "  Failed: ${RED}$FAILED${NC}"
echo "========================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please review.${NC}"
    exit 1
fi
