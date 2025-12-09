#!/bin/bash
echo "=== GROUP A MISSING ITEMS CHECK ==="
echo ""

# Check route registration
echo "1. Route Registration:"
TOTAL_ROUTES=$(grep -c "app.use('/api" services/gateway-api/src/index.ts 2>/dev/null || echo "0")
echo "Total routes registered: $TOTAL_ROUTES"

# Check for credits/roas/knowledge
echo ""
echo "2. Credits/ROAS/Knowledge Routes:"
if grep -qE "registerCreditsEndpoints|app.use.*credits|creditsRouter" services/gateway-api/src/index.ts 2>/dev/null; then
  echo "✅ Credits route registered"
else
  echo "❌ MISSING: Credits route not registered"
fi

if grep -qE "app.use.*roas|roasRouter" services/gateway-api/src/index.ts 2>/dev/null; then
  echo "✅ ROAS route registered"
else
  echo "❌ MISSING: ROAS route not registered"
fi

if grep -qE "app.use.*knowledge|knowledgeRouter" services/gateway-api/src/index.ts 2>/dev/null; then
  echo "✅ Knowledge route registered"
else
  echo "❌ MISSING: Knowledge route not registered"
fi

# Check campaigns endpoints
echo ""
echo "3. Campaigns Endpoints:"
CAMPAIGN_ENDPOINTS=$(grep -c "router\.\(get\|post\|put\|delete\)" services/gateway-api/src/routes/campaigns.ts 2>/dev/null || echo "0")
echo "Total endpoints: $CAMPAIGN_ENDPOINTS"

# Check for activate/pause endpoints
if grep -q ":id/activate\|:id/pause" services/gateway-api/src/routes/campaigns.ts 2>/dev/null; then
  echo "✅ Activate/pause endpoints exist"
else
  echo "⚠️  Check: Activate/pause endpoints may be missing"
fi

# Check ads endpoints
echo ""
echo "4. Ads Endpoints:"
ADS_ENDPOINTS=$(grep -c "router\.\(get\|post\|put\|delete\)" services/gateway-api/src/routes/ads.ts 2>/dev/null || echo "0")
echo "Total endpoints: $ADS_ENDPOINTS"

# Check for approve/reject endpoints
if grep -q ":id/approve\|:id/reject" services/gateway-api/src/routes/ads.ts 2>/dev/null; then
  echo "✅ Approve/reject endpoints exist"
else
  echo "⚠️  Check: Approve/reject endpoints may be missing"
fi

# Check frontend API methods
echo ""
echo "5. Frontend API Methods:"
if [ -f "frontend/src/lib/api.ts" ]; then
  API_METHODS=$(grep -c "export const" frontend/src/lib/api.ts 2>/dev/null || echo "0")
  echo "Total methods: $API_METHODS"
  
  if grep -q "activateCampaign\|pauseCampaign" frontend/src/lib/api.ts 2>/dev/null; then
    echo "✅ Campaign methods exist"
  else
    echo "⚠️  Check: Campaign methods may be missing"
  fi
else
  echo "⚠️  frontend/src/lib/api.ts not found"
fi

# Check self-learning cycle
echo ""
echo "6. Self-Learning Cycle:"
if [ -f "services/gateway-api/src/workers/self-learning-cycle.ts" ]; then
  LOOPS=$(grep -c "async function execute" services/gateway-api/src/workers/self-learning-cycle.ts 2>/dev/null || echo "0")
  echo "Loops implemented: $LOOPS"
  
  if [ "$LOOPS" -ge 7 ]; then
    echo "✅ All 7 loops implemented"
  else
    echo "⚠️  Only $LOOPS/7 loops implemented"
  fi
else
  echo "⚠️  self-learning-cycle.ts not found"
fi

echo ""
echo "=== CHECK COMPLETE ==="
