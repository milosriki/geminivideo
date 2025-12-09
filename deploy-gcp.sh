#!/bin/bash
# GCP Cloud Run Deployment Script
# Deploys all services to Google Cloud Run

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"geminivideo-prod"}
REGION=${GCP_REGION:-"us-central1"}

echo "🚀 Deploying to GCP Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Enable required APIs
echo "📋 Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  cloudbuild.googleapis.com \
  --project=$PROJECT_ID

# Build and push images
echo "🔨 Building Docker images..."

echo "Building gateway-api..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/gateway-api ./services/gateway-api --project=$PROJECT_ID

echo "Building ml-service..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/ml-service ./services/ml-service --project=$PROJECT_ID

echo "Building video-agent..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/video-agent ./services/video-agent --project=$PROJECT_ID

echo "Building drive-intel..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/drive-intel ./services/drive-intel --project=$PROJECT_ID

# Deploy to Cloud Run
echo "🚀 Deploying services to Cloud Run..."

# Gateway API
gcloud run deploy gateway-api \
  --image gcr.io/$PROJECT_ID/gateway-api \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=$CLOUD_SQL_URL,REDIS_URL=$MEMORYSTORE_URL,ML_SERVICE_URL=https://ml-service-$REGION-$PROJECT_ID.a.run.app,VIDEO_AGENT_URL=https://video-agent-$REGION-$PROJECT_ID.a.run.app,DRIVE_INTEL_URL=https://drive-intel-$REGION-$PROJECT_ID.a.run.app" \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --project=$PROJECT_ID

# ML Service
gcloud run deploy ml-service \
  --image gcr.io/$PROJECT_ID/ml-service \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=$CLOUD_SQL_URL,REDIS_URL=$MEMORYSTORE_URL" \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 5 \
  --project=$PROJECT_ID

# Video Agent
gcloud run deploy video-agent \
  --image gcr.io/$PROJECT_ID/video-agent \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=$CLOUD_SQL_URL,REDIS_URL=$MEMORYSTORE_URL" \
  --memory 8Gi \
  --cpu 4 \
  --timeout 600 \
  --max-instances 3 \
  --project=$PROJECT_ID

# Drive Intel
gcloud run deploy drive-intel \
  --image gcr.io/$PROJECT_ID/drive-intel \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=$CLOUD_SQL_URL,REDIS_URL=$MEMORYSTORE_URL" \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 5 \
  --project=$PROJECT_ID

# Deploy workers as Cloud Run Jobs
echo "⚙️  Deploying background workers..."

# Self-Learning Worker (runs every 5 minutes)
gcloud run jobs create self-learning-worker \
  --image gcr.io/$PROJECT_ID/gateway-api \
  --region $REGION \
  --command npm \
  --args run,worker:self-learning \
  --set-env-vars "DATABASE_URL=$CLOUD_SQL_URL,REDIS_URL=$MEMORYSTORE_URL,ML_SERVICE_URL=https://ml-service-$REGION-$PROJECT_ID.a.run.app" \
  --memory 2Gi \
  --cpu 1 \
  --max-retries 3 \
  --schedule "*/5 * * * *" \
  --project=$PROJECT_ID

# Batch Executor Worker (runs every 10 minutes)
gcloud run jobs create batch-executor-worker \
  --image gcr.io/$PROJECT_ID/gateway-api \
  --region $REGION \
  --command npm \
  --args run,worker:batch \
  --set-env-vars "DATABASE_URL=$CLOUD_SQL_URL,REDIS_URL=$MEMORYSTORE_URL" \
  --memory 2Gi \
  --cpu 1 \
  --max-retries 3 \
  --schedule "*/10 * * * *" \
  --project=$PROJECT_ID

echo "✅ Deployment complete!"
echo ""
echo "📊 Service URLs:"
gcloud run services list --region=$REGION --project=$PROJECT_ID --format="table(metadata.name,status.url)"

