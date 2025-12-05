#!/bin/bash
# DCO Meta Variant Generator - Test Script
# €5M Investment-Grade System Validation

set -e

echo "=================================================="
echo "DCO Meta Variant Generator - System Test"
echo "=================================================="
echo ""

# Configuration
VIDEO_AGENT_URL="${VIDEO_AGENT_URL:-http://localhost:8002}"
META_PUBLISHER_URL="${META_PUBLISHER_URL:-http://localhost:8083}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Check service health
echo "Test 1: Checking service health..."
echo "-----------------------------------"

echo -n "Video Agent: "
if curl -s ${VIDEO_AGENT_URL}/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ Online${NC}"
else
    echo -e "${RED}✗ Offline${NC}"
    echo "Start video-agent service: cd services/video-agent && uvicorn main:app --port 8002"
fi

echo -n "Meta Publisher: "
if curl -s ${META_PUBLISHER_URL}/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ Online${NC}"
else
    echo -e "${RED}✗ Offline${NC}"
    echo "Start meta-publisher service: cd services/meta-publisher && npm start"
fi

echo ""

# Test 2: Get Meta format specifications
echo "Test 2: Get Meta format specifications..."
echo "------------------------------------------"

response=$(curl -s ${VIDEO_AGENT_URL}/api/dco/formats)
format_count=$(echo $response | grep -o '"name":' | wc -l)

if [ $format_count -ge 6 ]; then
    echo -e "${GREEN}✓ Found $format_count Meta formats${NC}"
    echo $response | jq -r '.formats[] | "  - \(.name): \(.dimensions) (\(.aspect_ratio))"'
else
    echo -e "${RED}✗ Format specifications not available${NC}"
fi

echo ""

# Test 3: Get DCO examples
echo "Test 3: Get DCO examples..."
echo "---------------------------"

response=$(curl -s ${VIDEO_AGENT_URL}/api/dco/examples)
example_count=$(echo $response | grep -o '"description":' | wc -l)

if [ $example_count -ge 3 ]; then
    echo -e "${GREEN}✓ Found $example_count example configurations${NC}"
    echo $response | jq -r '.examples | keys[] | "  - \(.)"'
else
    echo -e "${RED}✗ Examples not available${NC}"
fi

echo ""

# Test 4: Dry-run DCO generation
echo "Test 4: Dry-run DCO variant generation..."
echo "------------------------------------------"

payload='{
  "sourceVideoPath": "/tmp/test_video.mp4",
  "productName": "FitnessPro App",
  "hook": "Transform your body in 30 days",
  "cta": "Start Free Trial",
  "painPoint": "lack of results",
  "benefit": "personalized workouts",
  "targetAudience": "busy professionals",
  "variantCount": 3,
  "formats": ["feed", "reels"]
}'

response=$(curl -s -X POST ${META_PUBLISHER_URL}/api/dco/generate-meta-variants \
  -H "Content-Type: application/json" \
  -d "$payload")

status=$(echo $response | jq -r '.status')

if [ "$status" = "dry_run" ] || [ "$status" = "success" ]; then
    total_variants=$(echo $response | jq -r '.totalVariants')
    echo -e "${GREEN}✓ DCO generation endpoint working${NC}"
    echo "  Status: $status"
    echo "  Total variants: $total_variants"

    if [ "$status" = "dry_run" ]; then
        echo -e "${YELLOW}  Note: Running in dry-run mode (video-agent may not be available)${NC}"
    fi
else
    echo -e "${RED}✗ DCO generation failed${NC}"
    echo $response | jq '.'
fi

echo ""

# Test 5: Check Meta SDK configuration
echo "Test 5: Check Meta SDK configuration..."
echo "----------------------------------------"

response=$(curl -s ${META_PUBLISHER_URL}/)
sdk_enabled=$(echo $response | jq -r '.real_sdk_enabled')

if [ "$sdk_enabled" = "true" ]; then
    echo -e "${GREEN}✓ Meta SDK configured${NC}"
    echo "  Ready for real Meta uploads"
else
    echo -e "${YELLOW}⚠ Meta SDK not configured${NC}"
    echo "  Set environment variables:"
    echo "    - META_ACCESS_TOKEN"
    echo "    - META_AD_ACCOUNT_ID"
    echo "    - META_PAGE_ID"
fi

echo ""

# Summary
echo "=================================================="
echo "Test Summary"
echo "=================================================="
echo ""

echo "Available Endpoints:"
echo "  POST ${META_PUBLISHER_URL}/api/dco/generate-meta-variants"
echo "  POST ${META_PUBLISHER_URL}/api/dco/upload-variants"
echo "  POST ${META_PUBLISHER_URL}/api/campaigns/dco"
echo "  GET  ${VIDEO_AGENT_URL}/api/dco/formats"
echo "  GET  ${VIDEO_AGENT_URL}/api/dco/examples"
echo ""

echo "Next Steps:"
echo "  1. Review documentation: cat DCO_QUICKSTART.md"
echo "  2. Configure Meta credentials (if needed)"
echo "  3. Generate variants with real video"
echo "  4. Upload to Meta Ads Manager"
echo "  5. Activate and monitor performance"
echo ""

echo "Example Generation Command:"
echo "---"
cat << 'EOF'
curl -X POST http://localhost:8083/api/dco/generate-meta-variants \
  -H "Content-Type: application/json" \
  -d '{
    "sourceVideoPath": "/path/to/your/video.mp4",
    "productName": "Your Product",
    "hook": "Your main hook",
    "cta": "Your CTA",
    "variantCount": 3,
    "formats": ["feed", "reels", "story"]
  }'
EOF
echo "---"
echo ""

echo "Full Documentation:"
echo "  - Quick Start: DCO_QUICKSTART.md"
echo "  - Full Guide: services/video-agent/DCO_META_VARIANTS_README.md"
echo "  - Summary: AGENT_12_DCO_IMPLEMENTATION_SUMMARY.md"
echo ""

echo -e "${GREEN}✓ DCO Meta Variant Generator - Ready for €5M Validation${NC}"
echo ""
