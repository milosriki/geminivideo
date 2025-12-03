#!/bin/bash
# Load Testing Script for GeminiVideo
# Simulates concurrent video generations and measures performance

set -e

API_BASE_URL="${API_BASE_URL:-http://localhost:8080}"
CONCURRENT_USERS="${CONCURRENT_USERS:-10}"
DURATION_SECONDS="${DURATION_SECONDS:-60}"
OUTPUT_DIR="./load-test-results"

echo "🔥 GeminiVideo Load Test"
echo "========================="
echo "API: $API_BASE_URL"
echo "Concurrent Users: $CONCURRENT_USERS"
echo "Duration: ${DURATION_SECONDS}s"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check dependencies
if ! command -v hey &> /dev/null && ! command -v ab &> /dev/null; then
    echo "❌ Error: 'hey' or 'ab' (Apache Bench) is required"
    echo "Install hey: brew install hey"
    exit 1
fi

# Test endpoints
ENDPOINTS=(
    "/health"
    "/api/avatars"
    "/api/assets"
)

# Load test function using hey
load_test_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    local name=$(echo "$endpoint" | tr '/' '_')
    local output_file="$OUTPUT_DIR/${name}_results.txt"
    
    echo "Testing $endpoint..."
    
    if command -v hey &> /dev/null; then
        hey -n 1000 -c $CONCURRENT_USERS -m $method "$API_BASE_URL$endpoint" > "$output_file"
    else
        ab -n 1000 -c $CONCURRENT_USERS "$API_BASE_URL$endpoint" > "$output_file"
    fi
    
    echo "✅ Results saved to $output_file"
}

# Health check first
echo "1. Testing /health endpoint..."
load_test_endpoint "/health" "GET"

# Test read endpoints
echo "2. Testing read endpoints..."
load_test_endpoint "/api/avatars" "GET"
load_test_endpoint "/api/assets" "GET"

# Test CTR prediction (ML service)
echo "3. Testing ML service..."
cat > "$OUTPUT_DIR/ctr_request.json" << 'EOF'
{
  "clip_data": {
    "hook": "Transform your body in 90 days",
    "script": "Dubai's #1 fitness transformation program",
    "duration": 30,
    "platform": "meta"
  }
}
EOF

if command -v hey &> /dev/null; then
    hey -n 100 -c 5 -m POST \
        -H "Content-Type: application/json" \
        -D "$OUTPUT_DIR/ctr_request.json" \
        "$API_BASE_URL/api/ml/predict-ctr" > "$OUTPUT_DIR/ml_prediction_results.txt"
fi

# Stress test: Generate requests
echo "4. Simulating video generation load..."
cat > "$OUTPUT_DIR/generate_request.json" << 'EOF'
{
  "product_name": "Fitness Program",
  "offer": "90-day transformation",
  "target_avatar": "fitness-enthusiast",
  "pain_points": ["lack of time", "no results"],
  "desires": ["six-pack abs", "energy"],
  "variant": "reels",
  "hook": "Transform your body in 90 days",
  "cta": "Start Today"
}
EOF

if command -v hey &> /dev/null; then
    hey -n 50 -c 5 -m POST \
        -H "Content-Type: application/json" \
        -D "$OUTPUT_DIR/generate_request.json" \
        "$API_BASE_URL/api/generate" > "$OUTPUT_DIR/generation_results.txt"
fi

# Summary
echo ""
echo "📊 Load Test Complete!"
echo "======================"
echo "Results saved to: $OUTPUT_DIR"
echo ""

# Parse and display key metrics
if [ -f "$OUTPUT_DIR/_health_results.txt" ]; then
    echo "Health Endpoint Performance:"
    grep -E "Requests/sec|Total:" "$OUTPUT_DIR/_health_results.txt" || true
fi

echo ""
echo "View detailed results with:"
echo "  cat $OUTPUT_DIR/*.txt"
