#!/bin/bash
echo "=== CHECKING FOR MISSING ENDPOINTS ==="
echo ""

# Check campaigns.ts for common endpoints
echo "Campaigns Endpoints:"
grep -o "router\.\(get\|post\|put\|delete\|patch\)" services/gateway-api/src/routes/campaigns.ts | sort | uniq -c

echo ""
echo "Ads Endpoints:"
grep -o "router\.\(get\|post\|put\|delete\|patch\)" services/gateway-api/src/routes/ads.ts | sort | uniq -c

echo ""
echo "Analytics Endpoints:"
grep -o "router\.\(get\|post\|put\|delete\|patch\)" services/gateway-api/src/routes/analytics.ts | sort | uniq -c

echo ""
echo "=== CHECKING FOR MISSING FUNCTIONALITY ==="
echo ""

# Check for error handling
echo "Error Handling Check:"
MISSING_ERROR_HANDLING=$(grep -L "catch.*error" services/gateway-api/src/routes/campaigns.ts services/gateway-api/src/routes/ads.ts 2>/dev/null | wc -l)
if [ $MISSING_ERROR_HANDLING -gt 0 ]; then
  echo "⚠️  Some routes may be missing error handling"
else
  echo "✅ Error handling present"
fi

# Check for rate limiting
echo ""
echo "Rate Limiting Check:"
MISSING_RATE_LIMIT=$(grep -L "RateLimiter\|rateLimiter" services/gateway-api/src/routes/campaigns.ts services/gateway-api/src/routes/ads.ts 2>/dev/null | wc -l)
if [ $MISSING_RATE_LIMIT -gt 0 ]; then
  echo "⚠️  Some routes may be missing rate limiting"
else
  echo "✅ Rate limiting present"
fi

# Check for input validation
echo ""
echo "Input Validation Check:"
MISSING_VALIDATION=$(grep -L "validateInput" services/gateway-api/src/routes/campaigns.ts services/gateway-api/src/routes/ads.ts 2>/dev/null | wc -l)
if [ $MISSING_VALIDATION -gt 0 ]; then
  echo "⚠️  Some routes may be missing input validation"
else
  echo "✅ Input validation present"
fi

echo ""
echo "=== CHECK COMPLETE ==="
