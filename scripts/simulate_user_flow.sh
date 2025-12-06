#!/bin/bash

echo "🚀 Starting Local Simulation..."

# 1. Health Checks
echo "\n🏥 Checking Service Health..."
SERVICES=("frontend:3000" "gateway-api:8080" "titan-core:8084" "postgres:5432" "redis:6379")

for service in "${SERVICES[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if curl -s "http://localhost:$port" > /dev/null || nc -z localhost "$port"; then
        echo "✅ $name is UP (Port $port)"
    else
        echo "❌ $name is DOWN (Port $port)"
    fi
done

# 2. API Endpoint Simulation
echo "\n🔌 Simulating API Calls..."

# Test /api/experiments (AB Testing)
echo -n "Testing /api/experiments... "
EXP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/experiments)
if [ "$EXP_STATUS" -eq 200 ]; then
    echo "✅ OK (200)"
else
    echo "❌ FAILED ($EXP_STATUS)"
fi

# Test /api/ads/trending (Ad Spy)
echo -n "Testing /api/ads/trending... "
ADS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/ads/trending)
if [ "$ADS_STATUS" -eq 200 ]; then
    echo "✅ OK (200)"
else
    echo "❌ FAILED ($ADS_STATUS)"
fi

# Test /api/insights/ai (AI Insights)
echo -n "Testing /api/insights/ai... "
INSIGHTS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/insights/ai)
if [ "$INSIGHTS_STATUS" -eq 200 ]; then
    echo "✅ OK (200)"
else
    echo "❌ FAILED ($INSIGHTS_STATUS)"
fi

# Test /avatars (Studio)
echo -n "Testing /avatars... "
AVATAR_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/avatars)
if [ "$AVATAR_STATUS" -eq 200 ]; then
    echo "✅ OK (200)"
else
    echo "❌ FAILED ($AVATAR_STATUS)"
fi

# 3. Frontend Route Check
echo "\n🌐 Checking Frontend Routes..."
# We expect index.html for all routes in SPA, but we want to make sure the server responds
ROUTES=("/assets" "/studio" "/spy" "/analytics")
for route in "${ROUTES[@]}"; do
    echo -n "Checking route $route... "
    ROUTE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000$route")
    if [ "$ROUTE_STATUS" -eq 200 ]; then
        echo "✅ OK (200)"
    else
        echo "❌ FAILED ($ROUTE_STATUS)"
    fi
done

echo "\n✨ Simulation Complete!"
