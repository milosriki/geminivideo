#!/bin/bash

# Configuration
REGION="us-central1"
REPO_NAME="geminivideo-repo"

echo "🚀 Starting Cloud Run Deployment..."
echo "⚠️  Make sure you have run 'gcloud auth login' and 'gcloud config set project YOUR_PROJECT_ID' first."

# 1. Load Environment Variables
if [ -f .env ]; then
  export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
  echo "✅ Loaded environment variables from .env"
else
  echo "⚠️  .env file not found. Please ensure environment variables are set."
fi

# 2. Database Setup
# Extract Project ID from VITE_SUPABASE_URL if not set
if [ -z "$SUPABASE_PROJECT_ID" ] && [ ! -z "$VITE_SUPABASE_URL" ]; then
  # Extract subdomain from URL (e.g., https://xyz.supabase.co -> xyz)
  SUPABASE_PROJECT_ID=$(echo $VITE_SUPABASE_URL | sed 's|https://||' | cut -d. -f1)
fi

if [ -z "$SUPABASE_DB_PASSWORD" ]; then
  echo -n "Enter your Supabase Database Password: "
  read -s SUPABASE_DB_PASSWORD
  echo
fi

DATABASE_URL="postgresql://postgres:${SUPABASE_DB_PASSWORD}@db.${SUPABASE_PROJECT_ID}.supabase.co:5432/postgres"

# 3. Enable APIs
echo "Enable APIs..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com

# 2. Create Artifact Registry
echo "Creating Artifact Registry..."
gcloud artifacts repositories create $REPO_NAME --repository-format=docker --location=$REGION --description="Geminivideo Repository" || true

# 3. Build and Push Images
echo "Building and Pushing Images..."
# Helper function to build
build_and_push() {
  SERVICE=$1
  DIR=$2
  echo "Building $SERVICE..."
  gcloud builds submit --tag $REGION-docker.pkg.dev/$(gcloud config get-value project)/$REPO_NAME/$SERVICE $DIR
}

build_and_push "titan-core" "./services/titan-core"
build_and_push "meta-publisher" "./services/meta-publisher"
build_and_push "gateway-api" "./services/gateway-api"
build_and_push "drive-intel" "./services/drive-intel"
build_and_push "video-agent" "./services/video-agent"
build_and_push "ml-service" "./services/ml-service"

# 4. Initial Deployment (to generate URLs)
echo "Deploying Services (Round 1 - Generating URLs)..."

deploy_service() {
  SERVICE=$1
  IMAGE=$REGION-docker.pkg.dev/$(gcloud config get-value project)/$REPO_NAME/$SERVICE
  echo "Deploying $SERVICE..."
  gcloud run deploy $SERVICE --image $IMAGE --region $REGION --allow-unauthenticated --port 8080 --set-env-vars="dummy=val"
}

# Note: We use port 8080 for all Cloud Run services internally, mapping to their container ports
# Adjusting container ports if necessary or assuming Dockerfiles expose correct ports.
# Cloud Run expects the container to listen on $PORT env var (default 8080).
# We will pass PORT=8080 to all services.

# Deploy independent services first
gcloud run deploy titan-core --image $REGION-docker.pkg.dev/$(gcloud config get-value project)/$REPO_NAME/titan-core --region $REGION --allow-unauthenticated --set-env-vars "GEMINI_API_KEY=${GEMINI_API_KEY},META_APP_ID=${META_APP_ID},META_ACCESS_TOKEN=${META_ACCESS_TOKEN},META_AD_ACCOUNT_ID=${META_AD_ACCOUNT_ID},META_CLIENT_TOKEN=${META_CLIENT_TOKEN},META_APP_SECRET=${META_APP_SECRET}"

gcloud run deploy ml-service --image $REGION-docker.pkg.dev/$(gcloud config get-value project)/$REPO_NAME/ml-service --region $REGION --allow-unauthenticated

gcloud run deploy drive-intel --image $REGION-docker.pkg.dev/$(gcloud config get-value project)/$REPO_NAME/drive-intel --region $REGION --allow-unauthenticated

gcloud run deploy video-agent --image $REGION-docker.pkg.dev/$(gcloud config get-value project)/$REPO_NAME/video-agent --region $REGION --allow-unauthenticated

# Deploy Meta Publisher (needs Gateway URL, but we don't have it yet, deploy with placeholder)
gcloud run deploy meta-publisher --image $REGION-docker.pkg.dev/$(gcloud config get-value project)/$REPO_NAME/meta-publisher --region $REGION --allow-unauthenticated --set-env-vars "META_ACCESS_TOKEN=${META_ACCESS_TOKEN},META_AD_ACCOUNT_ID=${META_AD_ACCOUNT_ID},META_PAGE_ID=${META_PAGE_ID},META_APP_ID=${META_APP_ID},META_CLIENT_TOKEN=${META_CLIENT_TOKEN},META_APP_SECRET=${META_APP_SECRET},GATEWAY_URL=placeholder"

# Deploy Gateway (needs other URLs)
# Fetch URLs
TITAN_URL=$(gcloud run services describe titan-core --region $REGION --format 'value(status.url)')
ML_URL=$(gcloud run services describe ml-service --region $REGION --format 'value(status.url)')
DRIVE_URL=$(gcloud run services describe drive-intel --region $REGION --format 'value(status.url)')
VIDEO_URL=$(gcloud run services describe video-agent --region $REGION --format 'value(status.url)')
META_URL=$(gcloud run services describe meta-publisher --region $REGION --format 'value(status.url)')

echo "Deploying Gateway API with Service URLs..."
gcloud run deploy gateway-api --image $REGION-docker.pkg.dev/$(gcloud config get-value project)/$REPO_NAME/gateway-api --region $REGION --allow-unauthenticated \
  --set-env-vars "DRIVE_INTEL_URL=$DRIVE_URL,VIDEO_AGENT_URL=$VIDEO_URL,ML_SERVICE_URL=$ML_URL,META_PUBLISHER_URL=$META_URL,DATABASE_URL=postgresql://postgres:${SUPABASE_DB_PASSWORD}@db.${SUPABASE_PROJECT_ID}.supabase.co:5432/postgres"

# 5. Update Circular Dependencies
echo "Updating Meta Publisher with Gateway URL..."
GATEWAY_URL=$(gcloud run services describe gateway-api --region $REGION --format 'value(status.url)')

gcloud run services update meta-publisher --region $REGION --update-env-vars "GATEWAY_URL=$GATEWAY_URL"

echo "✅ Deployment Complete!"
echo "Gateway API URL: $GATEWAY_URL"
echo "Update your Frontend .env VITE_API_BASE_URL to this URL."
