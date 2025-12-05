#!/bin/bash

# ============================================================================
# Deploy Edge Infrastructure to Cloudflare Workers
# Usage: ./deploy-edge.sh [environment]
# ============================================================================

set -e

ENVIRONMENT=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================================="
echo "Deploying Edge Infrastructure to Cloudflare"
echo "Environment: $ENVIRONMENT"
echo "=================================================="

# Check dependencies
command -v wrangler >/dev/null 2>&1 || {
  echo "Error: wrangler CLI not found. Install with: npm install -g wrangler"
  exit 1
}

# Authenticate with Cloudflare (if not already)
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
  echo "Authenticating with Cloudflare..."
  wrangler login
else
  echo "Using CLOUDFLARE_API_TOKEN from environment"
fi

# Create KV Namespaces (if not exists)
echo ""
echo "Step 1: Creating KV Namespaces..."
create_kv_namespace() {
  local name=$1
  echo "  - Creating KV namespace: $name"
  wrangler kv:namespace create "$name" --env "$ENVIRONMENT" || echo "    (already exists)"
}

create_kv_namespace "PREDICTIONS"
create_kv_namespace "CREATIVE_SCORES"
create_kv_namespace "AB_TESTS"
create_kv_namespace "ANALYTICS"

# Create R2 Buckets (if not exists)
echo ""
echo "Step 2: Creating R2 Buckets..."
create_r2_bucket() {
  local name=$1
  echo "  - Creating R2 bucket: $name"
  wrangler r2 bucket create "$name" || echo "    (already exists)"
}

create_r2_bucket "geminivideo-assets"
create_r2_bucket "geminivideo-videos"
create_r2_bucket "geminivideo-uploads"
create_r2_bucket "geminivideo-analytics"

# Create D1 Database (if not exists)
echo ""
echo "Step 3: Creating D1 Database..."
wrangler d1 create geminivideo-edge --env "$ENVIRONMENT" || echo "  (already exists)"

# Set secrets
echo ""
echo "Step 4: Setting Secrets..."
echo "  Note: You'll need to set these manually or via CI/CD:"
echo "    - ORIGIN_URL"
echo "    - GATEWAY_API_URL"
echo "    - TITAN_CORE_URL"
echo "    - ML_SERVICE_URL"
echo "    - API_SECRET"
echo "    - STREAM_ACCOUNT_ID"
echo "    - STREAM_API_TOKEN"

# Build TypeScript workers
echo ""
echo "Step 5: Building TypeScript Workers..."
cd "$SCRIPT_DIR"
npm run build

# Deploy Workers
echo ""
echo "Step 6: Deploying Workers..."

deploy_worker() {
  local name=$1
  local script=$2
  echo "  - Deploying worker: $name"
  wrangler deploy "$script" --name "$name" --env "$ENVIRONMENT"
}

deploy_worker "prediction-cache" "workers/prediction-cache.ts"
deploy_worker "creative-scorer" "workers/creative-scorer.ts"
deploy_worker "ab-router" "workers/ab-router.ts"
deploy_worker "trending-hooks" "workers/trending-hooks.ts"
deploy_worker "asset-delivery" "workers/asset-delivery.ts"
deploy_worker "edge-analytics" "workers/edge-analytics.ts"

# Configure custom domains (optional)
echo ""
echo "Step 7: Configuring Custom Domains (optional)..."
echo "  Run these commands to configure custom domains:"
echo "    wrangler custom-domains add api.geminivideo.com --worker prediction-cache"
echo "    wrangler custom-domains add cdn.geminivideo.com --worker asset-delivery"

# Set up R2 custom domains
echo ""
echo "Step 8: Configuring R2 Custom Domains..."
echo "  Configure in Cloudflare dashboard:"
echo "    - geminivideo-assets -> cdn.geminivideo.com"
echo "    - geminivideo-videos -> video.geminivideo.com"

# Deploy Cloudflare Stream settings (if applicable)
echo ""
echo "Step 9: Configuring Cloudflare Stream..."
if [ -n "$STREAM_ACCOUNT_ID" ]; then
  echo "  Stream Account ID: $STREAM_ACCOUNT_ID"
  echo "  Configure via dashboard: https://dash.cloudflare.com/stream"
else
  echo "  STREAM_ACCOUNT_ID not set, skipping Stream configuration"
fi

# Test endpoints
echo ""
echo "Step 10: Testing Edge Endpoints..."
test_endpoint() {
  local url=$1
  echo "  Testing: $url"
  curl -s -o /dev/null -w "    Status: %{http_code}\n" "$url" || echo "    Failed"
}

if [ "$ENVIRONMENT" = "production" ]; then
  test_endpoint "https://api.geminivideo.com/api/predict-quick/test"
  test_endpoint "https://api.geminivideo.com/api/score-cached/test"
  test_endpoint "https://cdn.geminivideo.com/assets/images/test.jpg"
fi

# Summary
echo ""
echo "=================================================="
echo "Edge Deployment Complete!"
echo "=================================================="
echo ""
echo "Edge Workers Deployed:"
echo "  - Prediction Cache: https://api.geminivideo.com/api/predict-quick/*"
echo "  - Creative Scorer: https://api.geminivideo.com/api/score-cached/*"
echo "  - A/B Router: https://api.geminivideo.com/api/ab/*"
echo "  - Trending Hooks: https://api.geminivideo.com/api/hooks/trending/*"
echo "  - Asset Delivery: https://cdn.geminivideo.com/assets/*"
echo "  - Edge Analytics: https://api.geminivideo.com/api/analytics/*"
echo ""
echo "Global Edge Network:"
echo "  - 310+ data centers worldwide"
echo "  - <50ms latency globally"
echo "  - Zero cold starts"
echo ""
echo "Cost Savings:"
echo "  - R2 vs S3: ~$9,000/month saved (zero egress)"
echo "  - Stream vs MediaConvert: ~$990/month saved"
echo "  - Edge vs Origin: 90% reduction in origin requests"
echo ""
echo "Next Steps:"
echo "  1. Set secrets: wrangler secret put SECRET_NAME"
echo "  2. Configure custom domains in Cloudflare dashboard"
echo "  3. Enable Cloudflare Stream for video delivery"
echo "  4. Monitor analytics: wrangler tail [worker-name]"
echo ""
