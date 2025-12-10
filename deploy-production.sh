#!/bin/bash
# deploy-production.sh - Complete Production Deployment to Cloud Run
# Deploys all 12 services with proper configuration

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"geminivideo-prod"}
REGION=${GCP_REGION:-"us-central1"}
REPOSITORY=${GCP_REPOSITORY:-"geminivideo-repo"}
SERVICE_ACCOUNT="geminivideo-sa@${PROJECT_ID}.iam.gserviceaccount.com"
VPC_CONNECTOR="geminivideo-connector"

echo "🚀 GeminiVideo Production Deployment"
echo "===================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Repository: $REPOSITORY"
echo ""

# Check prerequisites
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get secrets
echo "📋 Loading secrets..."
DB_PASSWORD=$(gcloud secrets versions access latest --secret=db-password --project=$PROJECT_ID 2>/dev/null || echo "")
REDIS_HOST=$(gcloud secrets versions access latest --secret=redis-host --project=$PROJECT_ID 2>/dev/null || echo "")
DB_CONNECTION_NAME=$(gcloud sql instances describe geminivideo-db --format="value(connectionName)" --project=$PROJECT_ID 2>/dev/null || echo "")

if [ -z "$DB_CONNECTION_NAME" ]; then
    echo "⚠️  Cloud SQL instance not found. Please run setup-infrastructure.sh first."
    exit 1
fi

# Function to deploy a service
deploy_service() {
    local SERVICE=$1
    local IMAGE=$2
    local MEMORY=$3
    local CPU=$4
    local TIMEOUT=$5
    local MIN_INSTANCES=$6
    local MAX_INSTANCES=$7
    local CONCURRENCY=$8
    local ENV_VARS=$9

    echo ""
    echo "🚀 Deploying $SERVICE..."
    echo "   Image: $IMAGE"
    echo "   Memory: $MEMORY, CPU: $CPU, Timeout: ${TIMEOUT}s"
    echo "   Scaling: $MIN_INSTANCES-$MAX_INSTANCES instances, Concurrency: $CONCURRENCY"

    gcloud run deploy $SERVICE \
        --image=$IMAGE \
        --region=$REGION \
        --platform=managed \
        --memory=$MEMORY \
        --cpu=$CPU \
        --timeout=$TIMEOUT \
        --min-instances=$MIN_INSTANCES \
        --max-instances=$MAX_INSTANCES \
        --concurrency=$CONCURRENCY \
        --service-account=$SERVICE_ACCOUNT \
        --vpc-connector=$VPC_CONNECTOR \
        --set-env-vars="$ENV_VARS" \
        --set-secrets="DATABASE_PASSWORD=db-password:latest" \
        --allow-unauthenticated \
        --project=$PROJECT_ID \
        --quiet

    echo "✅ $SERVICE deployed successfully"
}

# Build and push images first
echo ""
echo "🔨 Building and pushing Docker images..."
if [ -f cloudbuild.yaml ]; then
    gcloud builds submit --config=cloudbuild.yaml --project=$PROJECT_ID
else
    echo "⚠️  cloudbuild.yaml not found. Building images manually..."
    # Build each service
    for service in gateway-api ml-service video-agent drive-intel titan-core meta-publisher tiktok-ads google-ads frontend; do
        echo "Building $service..."
        gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$service:latest ./services/$service --project=$PROJECT_ID
    done
fi

# Deploy backend services first
echo ""
echo "📦 Deploying backend services..."

# Drive Intel
deploy_service \
    "drive-intel" \
    "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/drive-intel:latest" \
    "4Gi" "2" "300" "1" "20" "10" \
    "DATABASE_URL=postgresql://geminivideo:\$DATABASE_PASSWORD@/$DB_CONNECTION_NAME/geminivideo,REDIS_URL=redis://$REDIS_HOST:6379,PORT=8081"

# Video Agent
deploy_service \
    "video-agent" \
    "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/video-agent:latest" \
    "8Gi" "4" "600" "0" "10" "5" \
    "DATABASE_URL=postgresql://geminivideo:\$DATABASE_PASSWORD@/$DB_CONNECTION_NAME/geminivideo,REDIS_URL=redis://$REDIS_HOST:6379,GCS_BUCKET=geminivideo-assets,PORT=8082"

# ML Service
deploy_service \
    "ml-service" \
    "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/ml-service:latest" \
    "4Gi" "2" "300" "1" "20" "10" \
    "DATABASE_URL=postgresql://geminivideo:\$DATABASE_PASSWORD@/$DB_CONNECTION_NAME/geminivideo,REDIS_URL=redis://$REDIS_HOST:6379,GCS_BUCKET=geminivideo-models,PORT=8003"

# Titan Core
deploy_service \
    "titan-core" \
    "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/titan-core:latest" \
    "4Gi" "2" "900" "1" "10" "5" \
    "REDIS_URL=redis://$REDIS_HOST:6379,ML_SERVICE_URL=https://ml-service-$REGION-$PROJECT_ID.a.run.app,PORT=8084"

# Meta Publisher
deploy_service \
    "meta-publisher" \
    "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/meta-publisher:latest" \
    "1Gi" "1" "300" "1" "20" "20" \
    "DATABASE_URL=postgresql://geminivideo:\$DATABASE_PASSWORD@/$DB_CONNECTION_NAME/geminivideo,GATEWAY_URL=https://gateway-api-$REGION-$PROJECT_ID.a.run.app,PORT=8083"

# TikTok Ads
deploy_service \
    "tiktok-ads" \
    "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/tiktok-ads:latest" \
    "1Gi" "1" "300" "0" "10" "20" \
    "DATABASE_URL=postgresql://geminivideo:\$DATABASE_PASSWORD@/$DB_CONNECTION_NAME/geminivideo,PORT=8085"

# Google Ads
deploy_service \
    "google-ads" \
    "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/google-ads:latest" \
    "1Gi" "1" "300" "0" "10" "20" \
    "DATABASE_URL=postgresql://geminivideo:\$DATABASE_PASSWORD@/$DB_CONNECTION_NAME/geminivideo,PORT=8086"

# Get service URLs
echo ""
echo "📡 Getting service URLs..."
DRIVE_INTEL_URL=$(gcloud run services describe drive-intel --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)
VIDEO_AGENT_URL=$(gcloud run services describe video-agent --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)
ML_SERVICE_URL=$(gcloud run services describe ml-service --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)
TITAN_CORE_URL=$(gcloud run services describe titan-core --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)
META_PUBLISHER_URL=$(gcloud run services describe meta-publisher --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)
TIKTOK_ADS_URL=$(gcloud run services describe tiktok-ads --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)
GOOGLE_ADS_URL=$(gcloud run services describe google-ads --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)

# Deploy Gateway API (depends on all services)
echo ""
echo "🌐 Deploying Gateway API..."
deploy_service \
    "gateway-api" \
    "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/gateway-api:latest" \
    "2Gi" "2" "300" "1" "100" "80" \
    "DATABASE_URL=postgresql://geminivideo:\$DATABASE_PASSWORD@/$DB_CONNECTION_NAME/geminivideo,REDIS_URL=redis://$REDIS_HOST:6379,DRIVE_INTEL_URL=$DRIVE_INTEL_URL,VIDEO_AGENT_URL=$VIDEO_AGENT_URL,ML_SERVICE_URL=$ML_SERVICE_URL,TITAN_CORE_URL=$TITAN_CORE_URL,META_PUBLISHER_URL=$META_PUBLISHER_URL,TIKTOK_ADS_URL=$TIKTOK_ADS_URL,GOOGLE_ADS_URL=$GOOGLE_ADS_URL,PORT=8080"

# Get Gateway URL
GATEWAY_URL=$(gcloud run services describe gateway-api --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)

# Deploy Frontend
echo ""
echo "🎨 Deploying Frontend..."
deploy_service \
    "frontend" \
    "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/frontend:latest" \
    "512Mi" "1" "60" "1" "10" "80" \
    "VITE_API_BASE_URL=$GATEWAY_URL"

echo ""
echo "✅ All services deployed successfully!"
echo ""
echo "📊 Service URLs:"
echo "  Gateway API: $GATEWAY_URL"
echo "  Frontend: $(gcloud run services describe frontend --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)"
echo "  Drive Intel: $DRIVE_INTEL_URL"
echo "  Video Agent: $VIDEO_AGENT_URL"
echo "  ML Service: $ML_SERVICE_URL"
echo "  Titan Core: $TITAN_CORE_URL"
echo "  Meta Publisher: $META_PUBLISHER_URL"
echo ""
echo "📝 Next steps:"
echo "  1. Run ./deploy-workers.sh to deploy background workers"
echo "  2. Set up monitoring and alerting"
echo "  3. Run health checks: ./health-check.sh"
echo ""

