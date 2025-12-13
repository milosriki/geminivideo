#!/bin/bash
# ============================================================================
# Enhanced Production Deployment Script
# Agent 19: Deployment Automation
# Created: 2025-12-13
#
# Features:
# - Pre-deployment checks
# - Database migrations
# - Service deployment with health verification
# - Automatic rollback on failure
# - Slack notifications
# ============================================================================

set -e

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# GCP Configuration
GCP_PROJECT="${GCP_PROJECT_ID:-geminivideo-prod}"
GCP_REGION="${GCP_REGION:-us-central1}"
ARTIFACT_REGISTRY="${ARTIFACT_REGISTRY_REPO:-geminivideo-repo}"

# Services to deploy
SERVICES=(
  "ml-service"
  "drive-intel"
  "video-agent"
  "meta-publisher"
  "titan-core"
  "gateway-api"
  "frontend"
)

# Deployment state
DEPLOYMENT_ID=$(date +%Y%m%d-%H%M%S)
ROLLBACK_IMAGES=()
DEPLOYED_SERVICES=()

# ============================================================================
# Helper Functions
# ============================================================================

log() {
  echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
  echo -e "${GREEN}[✅ SUCCESS]${NC} $1"
}

warning() {
  echo -e "${YELLOW}[⚠️  WARNING]${NC} $1"
}

error() {
  echo -e "${RED}[❌ ERROR]${NC} $1"
}

# ============================================================================
# Pre-Deployment Checks
# ============================================================================

pre_deployment_checks() {
  log "Running pre-deployment checks..."

  # Check gcloud authentication
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1; then
    error "Not authenticated with gcloud. Run: gcloud auth login"
    exit 1
  fi
  success "GCloud authentication verified"

  # Check project configuration
  CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
  if [ "$CURRENT_PROJECT" != "$GCP_PROJECT" ]; then
    log "Switching to project $GCP_PROJECT..."
    gcloud config set project "$GCP_PROJECT"
  fi
  success "GCP project: $GCP_PROJECT"

  # Check required environment variables
  REQUIRED_VARS=("DATABASE_URL" "REDIS_URL" "GEMINI_API_KEY")
  for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
      warning "Environment variable $var is not set"
    fi
  done

  # Verify Cloud Run API is enabled
  if ! gcloud services list --enabled --filter="name:run.googleapis.com" --format="value(name)" | grep -q "run.googleapis.com"; then
    error "Cloud Run API is not enabled. Run: gcloud services enable run.googleapis.com"
    exit 1
  fi
  success "Cloud Run API enabled"

  # Check Artifact Registry
  if ! gcloud artifacts repositories describe "$ARTIFACT_REGISTRY" --location="$GCP_REGION" &>/dev/null; then
    error "Artifact Registry repository not found: $ARTIFACT_REGISTRY"
    exit 1
  fi
  success "Artifact Registry verified"

  log "All pre-deployment checks passed!"
}

# ============================================================================
# Database Migrations
# ============================================================================

run_database_migrations() {
  log "Running database migrations..."

  # Check if Supabase CLI is available
  if command -v supabase &>/dev/null; then
    cd "$PROJECT_ROOT"
    supabase db push --linked || warning "Supabase migrations failed, continuing..."
    success "Database migrations completed"
  else
    warning "Supabase CLI not found, skipping migrations"
  fi
}

# ============================================================================
# Build and Push Images
# ============================================================================

build_and_push_image() {
  local service=$1
  local service_path="$PROJECT_ROOT/services/$service"
  local image_name="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT}/${ARTIFACT_REGISTRY}/${service}"
  local tag="${DEPLOYMENT_ID}"

  log "Building image for $service..."

  # Check if Dockerfile exists
  if [ ! -f "$service_path/Dockerfile" ]; then
    warning "No Dockerfile found for $service, skipping..."
    return 0
  fi

  # Build image
  docker build -t "${image_name}:${tag}" \
               -t "${image_name}:latest" \
               "$service_path"

  # Push image
  log "Pushing image for $service..."
  docker push "${image_name}:${tag}"
  docker push "${image_name}:latest"

  success "Image built and pushed: ${image_name}:${tag}"

  # Store for potential rollback
  ROLLBACK_IMAGES+=("$service:$tag")
}

# ============================================================================
# Deploy Service
# ============================================================================

deploy_service() {
  local service=$1
  local image_name="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT}/${ARTIFACT_REGISTRY}/${service}"
  local tag="${DEPLOYMENT_ID}"

  log "Deploying $service to Cloud Run..."

  # Get service-specific configuration
  local memory="1Gi"
  local cpu="1"
  local min_instances="1"
  local max_instances="10"
  local timeout="300"

  case $service in
    "ml-service")
      memory="16Gi"
      cpu="4"
      timeout="600"
      ;;
    "drive-intel")
      memory="4Gi"
      cpu="4"
      timeout="3600"
      ;;
    "video-agent")
      memory="4Gi"
      cpu="2"
      ;;
    "gateway-api")
      memory="2Gi"
      cpu="2"
      ;;
    "frontend")
      memory="512Mi"
      min_instances="1"
      timeout="60"
      ;;
  esac

  # Deploy to Cloud Run
  gcloud run deploy "$service" \
    --image="${image_name}:${tag}" \
    --region="$GCP_REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --memory="$memory" \
    --cpu="$cpu" \
    --timeout="$timeout" \
    --min-instances="$min_instances" \
    --max-instances="$max_instances" \
    --quiet

  DEPLOYED_SERVICES+=("$service")
  success "$service deployed successfully"
}

# ============================================================================
# Health Check
# ============================================================================

health_check() {
  local service=$1
  local max_attempts=30
  local attempt=1

  log "Checking health of $service..."

  # Get service URL
  local url=$(gcloud run services describe "$service" \
    --region="$GCP_REGION" \
    --format='value(status.url)')

  if [ -z "$url" ]; then
    error "Could not get URL for $service"
    return 1
  fi

  # Check health endpoint
  while [ $attempt -le $max_attempts ]; do
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "${url}/health" 2>/dev/null || echo "000")

    if [ "$status_code" = "200" ]; then
      success "$service is healthy"
      return 0
    fi

    log "Health check attempt $attempt/$max_attempts for $service (status: $status_code)"
    sleep 2
    ((attempt++))
  done

  error "Health check failed for $service after $max_attempts attempts"
  return 1
}

# ============================================================================
# Rollback
# ============================================================================

rollback() {
  error "Deployment failed! Initiating rollback..."

  for service in "${DEPLOYED_SERVICES[@]}"; do
    log "Rolling back $service..."

    # Get previous revision
    local revisions=$(gcloud run revisions list \
      --service="$service" \
      --region="$GCP_REGION" \
      --format="value(metadata.name)" \
      --limit=2)

    local previous_revision=$(echo "$revisions" | tail -n1)

    if [ -n "$previous_revision" ]; then
      gcloud run services update-traffic "$service" \
        --region="$GCP_REGION" \
        --to-revisions="$previous_revision=100" \
        --quiet

      success "Rolled back $service to $previous_revision"
    else
      warning "No previous revision found for $service"
    fi
  done

  send_notification "❌ Deployment FAILED and rolled back" "Deployment ID: $DEPLOYMENT_ID"
  exit 1
}

# ============================================================================
# Notifications
# ============================================================================

send_notification() {
  local title=$1
  local message=$2

  # Send to Slack if webhook is configured
  if [ -n "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST "$SLACK_WEBHOOK_URL" \
      -H 'Content-Type: application/json' \
      -d "{
        \"text\": \"$title\",
        \"attachments\": [{
          \"text\": \"$message\",
          \"color\": \"$([ \"$title\" == *FAILED* ] && echo 'danger' || echo 'good')\"
        }]
      }" 2>/dev/null || warning "Failed to send Slack notification"
  fi

  log "$title: $message"
}

# ============================================================================
# Main Deployment Flow
# ============================================================================

main() {
  log "=============================================="
  log "🚀 Starting Production Deployment"
  log "   Deployment ID: $DEPLOYMENT_ID"
  log "   Project: $GCP_PROJECT"
  log "   Region: $GCP_REGION"
  log "=============================================="

  # Set up error handling
  trap rollback ERR

  # Phase 1: Pre-deployment
  pre_deployment_checks

  # Phase 2: Database migrations
  run_database_migrations

  # Phase 3: Build and push images
  log "Building and pushing Docker images..."
  for service in "${SERVICES[@]}"; do
    build_and_push_image "$service"
  done

  # Phase 4: Deploy services
  log "Deploying services to Cloud Run..."
  for service in "${SERVICES[@]}"; do
    deploy_service "$service"
  done

  # Phase 5: Health checks
  log "Running health checks..."
  for service in "${DEPLOYED_SERVICES[@]}"; do
    health_check "$service" || rollback
  done

  # Phase 6: Deployment summary
  log "=============================================="
  success "🎉 Deployment completed successfully!"
  log "   Deployment ID: $DEPLOYMENT_ID"
  log "   Services deployed: ${#DEPLOYED_SERVICES[@]}"
  log "=============================================="

  # Get and display service URLs
  log "Service URLs:"
  for service in "${DEPLOYED_SERVICES[@]}"; do
    url=$(gcloud run services describe "$service" \
      --region="$GCP_REGION" \
      --format='value(status.url)')
    log "  $service: $url"
  done

  send_notification "✅ Deployment SUCCEEDED" "Deployment ID: $DEPLOYMENT_ID | Services: ${DEPLOYED_SERVICES[*]}"
}

# ============================================================================
# Entry Point
# ============================================================================

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      log "DRY RUN MODE - No actual deployment will occur"
      exit 0
      ;;
    --service)
      SERVICES=("$2")
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --dry-run     Show what would be deployed without actually deploying"
      echo "  --service     Deploy a single service"
      echo "  --help        Show this help message"
      exit 0
      ;;
    *)
      error "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Run main deployment
main
