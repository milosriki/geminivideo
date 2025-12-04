#!/bin/bash
set -e

# Load .env
if [ -f .env ]; then
  echo "Loading secrets from .env..."
  export $(grep -v '^#' .env | xargs)
else
  echo ".env file not found!"
  exit 1
fi

PROJECT_ID="ptd-fitness-demo"
REGION="us-central1"
REPO="geminivideo-repo"

echo "========================================================"
echo "Starting Manual Cloud Run Deployment"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "========================================================"

# Get Short SHA
SHORT_SHA=$(git rev-parse --short HEAD)
echo "Commit SHA: $SHORT_SHA"

# Step 1: Build Images
echo "Building Docker images on Cloud Build..."
gcloud builds submit --config cloudbuild-images.yaml --project $PROJECT_ID --substitutions=_SHORT_SHA=$SHORT_SHA .

# Step 2: Deploy Services
echo "Deploying services to Cloud Run..."

# Drive Intel
echo "Deploying drive-intel..."
gcloud run deploy drive-intel \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/drive-intel:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},OPENAI_API_KEY=${OPENAI_API_KEY},SUPABASE_URL=${SUPABASE_URL},SUPABASE_KEY=${SUPABASE_KEY}"

# Video Agent
echo "Deploying video-agent..."
gcloud run deploy video-agent \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/video-agent:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=4Gi \
  --cpu=2 \
  --timeout=600 \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},OPENAI_API_KEY=${OPENAI_API_KEY},SUPABASE_URL=${SUPABASE_URL},SUPABASE_KEY=${SUPABASE_KEY}"

# Meta Publisher
echo "Deploying meta-publisher..."
gcloud run deploy meta-publisher \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/meta-publisher:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},META_ACCESS_TOKEN=${META_ACCESS_TOKEN},META_AD_ACCOUNT_ID=${META_AD_ACCOUNT_ID},META_PAGE_ID=${META_PAGE_ID},SUPABASE_URL=${SUPABASE_URL},SUPABASE_KEY=${SUPABASE_KEY}"

# Titan Core (Missing from GitHub Action, adding here)
echo "Deploying titan-core..."
gcloud run deploy titan-core \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/titan-core:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},OPENAI_API_KEY=${OPENAI_API_KEY},ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY},GEMINI_API_KEY=${GEMINI_API_KEY},SUPABASE_URL=${SUPABASE_URL},SUPABASE_KEY=${SUPABASE_KEY}"

# Gateway API
echo "Deploying gateway-api..."
gcloud run deploy gateway-api \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/gateway-api:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},GEMINI_API_KEY=${GEMINI_API_KEY},OPENAI_API_KEY=${OPENAI_API_KEY},ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY},SUPABASE_URL=${SUPABASE_URL},SUPABASE_KEY=${SUPABASE_KEY}"

# Frontend
echo "Deploying frontend..."
gcloud run deploy frontend \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/frontend:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1

echo "========================================================"
echo "Deployment Complete! 🚀"
echo "========================================================"
