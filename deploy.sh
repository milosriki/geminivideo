#!/bin/bash
# Automated Deployment Script
# Supports both Docker and Cloud Run deployment

set -e

DEPLOYMENT_TYPE=${1:-"docker"}

echo "🚀 GeminiVideo Deployment Script"
echo "=================================="
echo ""

if [ "$DEPLOYMENT_TYPE" == "docker" ]; then
    echo "📦 Deploying to Docker (Local)..."
    echo ""
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        echo "⚠️  No .env file found. Creating from template..."
        cat > .env << EOF
# Database
POSTGRES_USER=geminivideo
POSTGRES_PASSWORD=changeme
POSTGRES_DB=geminivideo
DATABASE_URL=postgresql://geminivideo:changeme@postgres:5432/geminivideo

# Redis
REDIS_URL=redis://redis:6379

# Service URLs (for local Docker)
ML_SERVICE_URL=http://ml-service:8003
VIDEO_AGENT_URL=http://video-agent:8004
DRIVE_INTEL_URL=http://drive-intel:8002

# API Keys (set these)
META_ACCESS_TOKEN=
GOOGLE_ADS_CLIENT_ID=
GOOGLE_ADS_CLIENT_SECRET=
GOOGLE_ADS_REFRESH_TOKEN=
GOOGLE_ADS_DEVELOPER_TOKEN=

# GCS (optional for local)
GCS_BUCKET_NAME=
GOOGLE_APPLICATION_CREDENTIALS=
EOF
        echo "✅ Created .env file. Please update with your credentials."
        echo ""
    fi
    
    # Build and start services
    echo "🔨 Building Docker images..."
    docker-compose build --parallel
    
    echo ""
    echo "🚀 Starting services..."
    docker-compose up -d
    
    echo ""
    echo "⏳ Waiting for services to be healthy..."
    sleep 10
    
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    
    echo ""
    echo "✅ Docker deployment complete!"
    echo ""
    echo "📋 Service URLs:"
    echo "  - Gateway API: http://localhost:8080"
    echo "  - ML Service: http://localhost:8003"
    echo "  - Video Agent: http://localhost:8004"
    echo "  - Drive Intel: http://localhost:8002"
    echo ""
    echo "📝 View logs: docker-compose logs -f"
    echo "🛑 Stop services: docker-compose down"
    
elif [ "$DEPLOYMENT_TYPE" == "cloud" ] || [ "$DEPLOYMENT_TYPE" == "gcp" ]; then
    echo "☁️  Deploying to Google Cloud Run..."
    echo ""
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        echo "❌ gcloud CLI not found!"
        echo ""
        echo "Please install gcloud CLI:"
        echo "  https://cloud.google.com/sdk/docs/install"
        echo ""
        echo "Or run: docker deploy to deploy locally"
        exit 1
    fi
    
    # Check if logged in
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo "⚠️  Not logged in to gcloud. Please run:"
        echo "  gcloud auth login"
        exit 1
    fi
    
    # Check for required environment variables
    if [ -z "$GCP_PROJECT_ID" ]; then
        echo "⚠️  GCP_PROJECT_ID not set. Using default: geminivideo-prod"
        export GCP_PROJECT_ID=geminivideo-prod
    fi
    
    if [ -z "$GCP_REGION" ]; then
        echo "⚠️  GCP_REGION not set. Using default: us-central1"
        export GCP_REGION=us-central1
    fi
    
    echo "Project: $GCP_PROJECT_ID"
    echo "Region: $GCP_REGION"
    echo ""
    
    # Run the GCP deployment script
    if [ -f deploy-gcp.sh ]; then
        chmod +x deploy-gcp.sh
        ./deploy-gcp.sh
    else
        echo "❌ deploy-gcp.sh not found!"
        exit 1
    fi
    
else
    echo "❌ Invalid deployment type: $DEPLOYMENT_TYPE"
    echo ""
    echo "Usage:"
    echo "  ./deploy.sh docker    # Deploy to local Docker"
    echo "  ./deploy.sh cloud     # Deploy to Google Cloud Run"
    echo "  ./deploy.sh gcp       # Deploy to Google Cloud Run (alias)"
    exit 1
fi
