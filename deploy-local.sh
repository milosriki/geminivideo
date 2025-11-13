#!/bin/bash
# Local Docker Deployment - Quick Start
# Run this to deploy locally with Docker Compose

set -e

echo "🚀 Deploying Geminivideo Locally with Docker Compose"
echo "===================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose not found. Please install it first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://geminivideo:geminivideo@postgres:5432/geminivideo

# Service URLs (internal Docker network)
DRIVE_INTEL_URL=http://drive-intel:8081
VIDEO_AGENT_URL=http://video-agent:8082
ML_SERVICE_URL=http://ml-service:8003
META_PUBLISHER_URL=http://meta-publisher:8083
GATEWAY_URL=http://gateway-api:8080

# Meta Credentials (replace with your actual credentials)
META_ACCESS_TOKEN=
META_AD_ACCOUNT_ID=
META_PAGE_ID=
META_API_VERSION=v18.0

# Frontend
VITE_GATEWAY_URL=http://localhost:8080
VITE_DRIVE_INTEL_URL=http://localhost:8081
EOF
    echo "✅ .env file created (please configure Meta credentials)"
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose down 2>/dev/null || true

# Build images (disable BuildKit due to npm compatibility issue)
echo ""
echo "🔨 Building Docker images..."
DOCKER_BUILDKIT=0 docker compose build

# Start database first
echo ""
echo "🗄️  Starting PostgreSQL..."
docker-compose up -d postgres

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 5

# Initialize database
echo ""
echo "📊 Initializing database..."
docker-compose exec -T postgres psql -U geminivideo -d geminivideo -c "SELECT 1;" > /dev/null 2>&1 || {
    echo "⚠️  Database not ready yet, waiting longer..."
    sleep 5
}

# Start all services
echo ""
echo "🚀 Starting all services..."
docker compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo ""
echo "🏥 Checking service health..."
echo ""

services=(
    "gateway-api:8080"
    "drive-intel:8081"
    "video-agent:8082"
    "ml-service:8003"
    "meta-publisher:8083"
)

for service in "${services[@]}"; do
    name="${service%:*}"
    port="${service#*:}"

    if curl -s "http://localhost:$port/health" > /dev/null 2>&1 || \
       curl -s "http://localhost:$port/" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name (port $port) - Healthy${NC}"
    else
        echo -e "${YELLOW}⚠️  $name (port $port) - Starting...${NC}"
    fi
done

# Show logs
echo ""
echo "📋 Recent logs:"
echo "=============="
docker compose logs --tail=5

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "🌐 Access your services:"
echo "  Frontend:        http://localhost"
echo "  Gateway API:     http://localhost:8080"
echo "  Drive Intel:     http://localhost:8081"
echo "  Video Agent:     http://localhost:8082"
echo "  ML Service:      http://localhost:8003"
echo "  Meta Publisher:  http://localhost:8083"
echo ""
echo "📊 View logs:"
echo "  docker compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "  docker compose down"
echo ""
echo "📝 Next steps:"
echo "  1. Configure Meta credentials in .env"
echo "  2. Test ML service: curl http://localhost:8003/health"
echo "  3. Train XGBoost model: curl -X POST http://localhost:8003/api/ml/train -H 'Content-Type: application/json' -d '{\"use_synthetic_data\": true}'"
echo "  4. Open frontend at http://localhost"
echo ""
