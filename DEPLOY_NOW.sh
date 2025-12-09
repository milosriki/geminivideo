#!/bin/bash
# 🚀 PRODUCTION DEPLOYMENT SCRIPT - FULL PRO-GRADE SYSTEM
# Deploys complete system with all features ready for market domination

set -e

echo "🚀 GEMINIVIDEO PRODUCTION DEPLOYMENT"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker found${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose found${NC}"

# Check environment variables
echo ""
echo "🔐 Checking environment variables..."

REQUIRED_VARS=(
    "GEMINI_API_KEY"
    "OPENAI_API_KEY"
    "META_APP_ID"
    "META_ACCESS_TOKEN"
    "META_AD_ACCOUNT_ID"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Missing environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Set them with:"
    echo "  export GEMINI_API_KEY='your-key'"
    echo "  export OPENAI_API_KEY='your-key'"
    echo "  export META_APP_ID='your-id'"
    echo "  export META_ACCESS_TOKEN='your-token'"
    echo "  export META_AD_ACCOUNT_ID='your-account-id'"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ All required environment variables set${NC}"
fi

# Check Google Drive credentials (optional but recommended)
if [ -z "$GOOGLE_DRIVE_CREDENTIALS" ]; then
    echo -e "${YELLOW}⚠️  GOOGLE_DRIVE_CREDENTIALS not set (optional)${NC}"
    echo "   Set it to enable Google Drive integration:"
    echo "   export GOOGLE_DRIVE_CREDENTIALS=/path/to/credentials.json"
else
    if [ -f "$GOOGLE_DRIVE_CREDENTIALS" ]; then
        echo -e "${GREEN}✅ Google Drive credentials found${NC}"
    else
        echo -e "${YELLOW}⚠️  Google Drive credentials file not found: $GOOGLE_DRIVE_CREDENTIALS${NC}"
    fi
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file..."
    cat > .env << EOF
# AI Services
GEMINI_API_KEY=${GEMINI_API_KEY:-}
OPENAI_API_KEY=${OPENAI_API_KEY:-}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}

# Meta Integration
META_APP_ID=${META_APP_ID:-}
META_ACCESS_TOKEN=${META_ACCESS_TOKEN:-}
META_AD_ACCOUNT_ID=${META_AD_ACCOUNT_ID:-}
META_CLIENT_TOKEN=${META_CLIENT_TOKEN:-}
META_APP_SECRET=${META_APP_SECRET:-}

# Google Drive
GOOGLE_DRIVE_CREDENTIALS=${GOOGLE_DRIVE_CREDENTIALS:-}

# Database
DATABASE_URL=postgresql://geminivideo:geminivideo@postgres:5432/geminivideo

# Redis
REDIS_URL=redis://redis:6379
EOF
    echo -e "${GREEN}✅ .env file created${NC}"
else
    echo -e "${GREEN}✅ .env file exists${NC}"
fi

# Build and start services
echo ""
echo "🏗️  Building and starting services..."
echo ""

# Disable BuildKit for compatibility
export DOCKER_BUILDKIT=0

# Build and start
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "🏥 Checking service health..."

SERVICES=(
    "postgres:5432"
    "redis:6379"
    "gateway-api:8000"
    "drive-intel:8001"
    "video-agent:8002"
    "ml-service:8003"
    "titan-core:8084"
)

ALL_HEALTHY=true
for service in "${SERVICES[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if docker-compose ps | grep -q "$name.*Up"; then
        echo -e "${GREEN}✅ $name is running${NC}"
    else
        echo -e "${RED}❌ $name is not running${NC}"
        ALL_HEALTHY=false
    fi
done

if [ "$ALL_HEALTHY" = true ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL SERVICES ARE HEALTHY!${NC}"
    echo ""
    echo "📊 Service URLs:"
    echo "   Frontend:      http://localhost:3000"
    echo "   Gateway API:   http://localhost:8000"
    echo "   Drive Intel:   http://localhost:8001"
    echo "   Video Agent:   http://localhost:8002"
    echo "   ML Service:    http://localhost:8003"
    echo "   Titan-Core:    http://localhost:8084"
    echo ""
    echo "🚀 SYSTEM READY FOR MARKET DOMINATION!"
    echo ""
    echo "Next steps:"
    echo "1. Connect Google Drive (if credentials set)"
    echo "2. Generate your first winning ad"
    echo "3. Publish to Meta"
    echo ""
    echo "See PRODUCTION_DEPLOYMENT_COMPLETE.md for details"
else
    echo ""
    echo -e "${RED}❌ Some services are not healthy. Check logs with:${NC}"
    echo "   docker-compose logs"
    exit 1
fi

