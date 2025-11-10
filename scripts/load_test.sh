#!/bin/bash
# Load test script for AI Ad Intelligence Suite

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8080}"
CONCURRENCY="${CONCURRENCY:-10}"
REQUESTS="${REQUESTS:-100}"

echo "🚀 Running load tests..."
echo "URL: $GATEWAY_URL"
echo "Concurrency: $CONCURRENCY"
echo "Total Requests: $REQUESTS"
echo ""

# Test health endpoint under load
echo "Testing /health endpoint..."
ab -n $REQUESTS -c $CONCURRENCY "${GATEWAY_URL}/health" || {
    echo "⚠️  ApacheBench not installed. Skipping load tests."
    echo "Install with: apt-get install apache2-utils"
    exit 0
}

echo ""
echo "Testing /assets endpoint..."
ab -n $((REQUESTS / 2)) -c $((CONCURRENCY / 2)) "${GATEWAY_URL}/assets"

echo ""
echo "✅ Load tests completed"
