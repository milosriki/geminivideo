#!/bin/bash
# Smoke test script for AI Ad Intelligence Suite

set -e

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8080}"
DRIVE_INTEL_URL="${DRIVE_INTEL_URL:-http://localhost:8001}"
VIDEO_AGENT_URL="${VIDEO_AGENT_URL:-http://localhost:8002}"
META_PUBLISHER_URL="${META_PUBLISHER_URL:-http://localhost:8003}"

echo "🧪 Running smoke tests..."
echo ""

# Test Gateway API health
echo "Testing Gateway API..."
curl -sf "${GATEWAY_URL}/health" | jq . || { echo "❌ Gateway API failed"; exit 1; }
echo "✅ Gateway API OK"
echo ""

# Test Drive Intel health
echo "Testing Drive Intel..."
curl -sf "${DRIVE_INTEL_URL}/health" | jq . || { echo "❌ Drive Intel failed"; exit 1; }
echo "✅ Drive Intel OK"
echo ""

# Test Video Agent health
echo "Testing Video Agent..."
curl -sf "${VIDEO_AGENT_URL}/health" | jq . || { echo "❌ Video Agent failed"; exit 1; }
echo "✅ Video Agent OK"
echo ""

# Test Meta Publisher health
echo "Testing Meta Publisher..."
curl -sf "${META_PUBLISHER_URL}/health" | jq . || { echo "❌ Meta Publisher failed"; exit 1; }
echo "✅ Meta Publisher OK"
echo ""

# Test Assets endpoint
echo "Testing Assets endpoint..."
curl -sf "${GATEWAY_URL}/assets" | jq . > /dev/null || { echo "❌ Assets endpoint failed"; exit 1; }
echo "✅ Assets endpoint OK"
echo ""

# Test config endpoint
echo "Testing Config endpoint..."
curl -sf "${DRIVE_INTEL_URL}/config/ranking" | jq . > /dev/null || { echo "❌ Config endpoint failed"; exit 1; }
echo "✅ Config endpoint OK"
echo ""

# Test reliability endpoint
echo "Testing Reliability endpoint..."
curl -sf "${GATEWAY_URL}/predict/reliability" | jq . > /dev/null || { echo "❌ Reliability endpoint failed"; exit 1; }
echo "✅ Reliability endpoint OK"
echo ""

echo "🎉 All smoke tests passed!"
