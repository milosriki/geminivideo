#!/bin/bash
# ============================================================================
# Fix Port Mismatches in GeminiVideo Configuration
# ============================================================================
# This script fixes the service URL port mismatches identified in the audit

set -e

echo "Fixing port mismatches in docker-compose files..."

# Fix TITAN_CORE_URL (should be 8084, not 8000)
if grep -q "TITAN_CORE_URL.*:8000" docker-compose.yml 2>/dev/null; then
    sed -i 's/TITAN_CORE_URL=http:\/\/titan-core:8000/TITAN_CORE_URL=http:\/\/titan-core:8084/g' docker-compose.yml
    echo "  Fixed TITAN_CORE_URL in docker-compose.yml"
fi

if grep -q "TITAN_CORE_URL.*:8000" docker-compose.production.yml 2>/dev/null; then
    sed -i 's/TITAN_CORE_URL=http:\/\/titan-core:8000/TITAN_CORE_URL=http:\/\/titan-core:8084/g' docker-compose.production.yml
    echo "  Fixed TITAN_CORE_URL in docker-compose.production.yml"
fi

# Fix GOOGLE_ADS_URL (should be 8086)
if grep -q "GOOGLE_ADS_URL.*:8084" docker-compose.yml 2>/dev/null; then
    sed -i 's/GOOGLE_ADS_URL=http:\/\/google-ads:8084/GOOGLE_ADS_URL=http:\/\/google-ads:8086/g' docker-compose.yml
    echo "  Fixed GOOGLE_ADS_URL in docker-compose.yml"
fi

echo ""
echo "Checking .env.example files..."

# Update .env.example with correct ports
if [ -f ".env.example" ]; then
    if ! grep -q "TITAN_CORE_URL" .env.example; then
        echo "" >> .env.example
        echo "# Service URLs (Internal)" >> .env.example
        echo "DRIVE_INTEL_URL=http://drive-intel:8001" >> .env.example
        echo "VIDEO_AGENT_URL=http://video-agent:8002" >> .env.example
        echo "ML_SERVICE_URL=http://ml-service:8003" >> .env.example
        echo "TITAN_CORE_URL=http://titan-core:8084" >> .env.example
        echo "META_PUBLISHER_URL=http://meta-publisher:8083" >> .env.example
        echo "GOOGLE_ADS_URL=http://google-ads:8086" >> .env.example
        echo "TIKTOK_ADS_URL=http://tiktok-ads:8085" >> .env.example
        echo "  Added service URLs to .env.example"
    fi
fi

echo ""
echo "Port mismatch fixes complete!"
echo ""
echo "Service Port Reference:"
echo "  - drive-intel:    8001"
echo "  - video-agent:    8002"
echo "  - ml-service:     8003"
echo "  - gateway-api:    8080"
echo "  - meta-publisher: 8083"
echo "  - titan-core:     8084"
echo "  - tiktok-ads:     8085"
echo "  - google-ads:     8086"
echo ""
