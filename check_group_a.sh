#!/bin/bash
echo "=== GROUP A VERIFICATION CHECK ==="
echo ""

echo "1. Route Files:"
ls -1 services/gateway-api/src/routes/*.ts | wc -l
echo "Route files found"

echo ""
echo "2. Routes Registered in index.ts:"
grep -c "app.use('/api" services/gateway-api/src/index.ts
echo "routes registered"

echo ""
echo "3. Workers Started:"
grep -c "startSelfLearningCycleWorker\|start.*worker" services/gateway-api/src/index.ts
echo "workers started"

echo ""
echo "4. Services Exist:"
ls -1 services/gateway-api/src/services/*.ts 2>/dev/null | wc -l
echo "service files found"

echo ""
echo "5. Workers Exist:"
ls -1 services/gateway-api/src/workers/*.ts 2>/dev/null | wc -l
echo "worker files found"

echo ""
echo "6. Jobs Exist:"
ls -1 services/gateway-api/src/jobs/*.ts 2>/dev/null | wc -l
echo "job files found"

echo ""
echo "7. Multi-Platform Files:"
ls -1 services/gateway-api/src/multi-platform/*.ts 2>/dev/null | wc -l
echo "multi-platform files found"

echo ""
echo "=== CHECKING FOR MISSING ITEMS ==="
echo ""

# Check if all expected routes are registered
echo "Checking route registrations..."
MISSING_ROUTES=0

if ! grep -q "app.use('/api/campaigns'" services/gateway-api/src/index.ts; then
  echo "❌ MISSING: /api/campaigns route"
  MISSING_ROUTES=$((MISSING_ROUTES+1))
fi

if ! grep -q "app.use('/api/ads'" services/gateway-api/src/index.ts; then
  echo "❌ MISSING: /api/ads route"
  MISSING_ROUTES=$((MISSING_ROUTES+1))
fi

if ! grep -q "app.use('/api/analytics'" services/gateway-api/src/index.ts; then
  echo "❌ MISSING: /api/analytics route"
  MISSING_ROUTES=$((MISSING_ROUTES+1))
fi

if [ $MISSING_ROUTES -eq 0 ]; then
  echo "✅ All main routes registered"
fi

# Check if workers are started
if ! grep -q "startSelfLearningCycleWorker" services/gateway-api/src/index.ts; then
  echo "❌ MISSING: Self-learning cycle worker not started"
else
  echo "✅ Self-learning cycle worker started"
fi

echo ""
echo "=== VERIFICATION COMPLETE ==="
