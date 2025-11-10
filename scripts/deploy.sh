#!/bin/bash
# Deploy script for Gemini Video services to GCP Cloud Run

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"
REGISTRY_NAME="${REGISTRY_NAME:-geminivideo}"
IMAGE_PREFIX="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REGISTRY_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Gemini Video Deployment Script ===${NC}"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with gcloud. Run 'gcloud auth login'${NC}"
    exit 1
fi

# Function to deploy service
deploy_service() {
    local service_name=$1
    local memory=$2
    local cpu=$3
    local env_vars=$4
    
    echo -e "${YELLOW}Deploying ${service_name}...${NC}"
    
    gcloud run deploy ${service_name} \
        --image=${IMAGE_PREFIX}/${service_name}:latest \
        --region=${REGION} \
        --platform=managed \
        --allow-unauthenticated \
        --memory=${memory} \
        --cpu=${cpu} \
        ${env_vars} \
        --quiet
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ${service_name} deployed successfully${NC}"
    else
        echo -e "${RED}✗ Failed to deploy ${service_name}${NC}"
        exit 1
    fi
}

echo -e "${YELLOW}Step 1: Deploying drive-intel...${NC}"
deploy_service "drive-intel" "2Gi" "2" "--set-env-vars=CONFIG_PATH=/app/config,DATA_DIR=/app/data"

echo -e "${YELLOW}Step 2: Deploying video-agent...${NC}"
deploy_service "video-agent" "2Gi" "2" "--set-env-vars=CONFIG_PATH=/app/config,OUTPUT_DIR=/app/data/outputs"

echo -e "${YELLOW}Step 3: Deploying meta-publisher...${NC}"
deploy_service "meta-publisher" "512Mi" "1" ""

echo -e "${YELLOW}Step 4: Getting service URLs...${NC}"
DRIVE_INTEL_URL=$(gcloud run services describe drive-intel --region=${REGION} --format='value(status.url)')
VIDEO_AGENT_URL=$(gcloud run services describe video-agent --region=${REGION} --format='value(status.url)')
META_PUBLISHER_URL=$(gcloud run services describe meta-publisher --region=${REGION} --format='value(status.url)')

echo "Drive Intel URL: ${DRIVE_INTEL_URL}"
echo "Video Agent URL: ${VIDEO_AGENT_URL}"
echo "Meta Publisher URL: ${META_PUBLISHER_URL}"

echo -e "${YELLOW}Step 5: Deploying gateway-api...${NC}"
deploy_service "gateway-api" "1Gi" "1" \
    "--set-env-vars=CONFIG_PATH=/app/config,DRIVE_INTEL_URL=${DRIVE_INTEL_URL},VIDEO_AGENT_URL=${VIDEO_AGENT_URL},META_PUBLISHER_URL=${META_PUBLISHER_URL}"

GATEWAY_URL=$(gcloud run services describe gateway-api --region=${REGION} --format='value(status.url)')
echo "Gateway URL: ${GATEWAY_URL}"

echo -e "${YELLOW}Step 6: Deploying frontend...${NC}"
deploy_service "frontend" "512Mi" "1" "--set-env-vars=VITE_API_URL=${GATEWAY_URL}"

FRONTEND_URL=$(gcloud run services describe frontend --region=${REGION} --format='value(status.url)')

echo ""
echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo ""
echo "Service URLs:"
echo "  Frontend:       ${FRONTEND_URL}"
echo "  Gateway API:    ${GATEWAY_URL}"
echo "  Drive Intel:    ${DRIVE_INTEL_URL}"
echo "  Video Agent:    ${VIDEO_AGENT_URL}"
echo "  Meta Publisher: ${META_PUBLISHER_URL}"
echo ""
echo -e "${GREEN}Access your application at: ${FRONTEND_URL}${NC}"
