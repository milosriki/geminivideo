#!/bin/bash
# =============================================================================
# Gemini Video - Cloud Run Deployment Script
# =============================================================================
# Automated deployment script for all backend services
# Usage: ./scripts/deploy-cloud-run.sh [service-name]
#        ./scripts/deploy-cloud-run.sh              # Deploy all services
#        ./scripts/deploy-cloud-run.sh titan-core   # Deploy specific service
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# Configuration
# =============================================================================

# Get project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables from .env.production or .env
ENV_FILE="${PROJECT_ROOT}/.env.production"
if [ ! -f "$ENV_FILE" ]; then
    ENV_FILE="${PROJECT_ROOT}/.env"
fi

if [ ! -f "$ENV_FILE" ]; then
    log_error "No .env file found. Please create .env or .env.production"
    exit 1
fi

log_info "Loading environment from: $ENV_FILE"

# Parse .env file
export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)

# GCP Configuration
PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${CLOUD_RUN_REGION:-us-central1}"
REPOSITORY="${ARTIFACT_REGISTRY_REPO:-geminivideo-repo}"
SERVICE_ACCOUNT="${CLOUD_RUN_SERVICE_ACCOUNT:-geminivideo-cloud-run@${PROJECT_ID}.iam.gserviceaccount.com}"

# Validate required variables
if [ -z "$PROJECT_ID" ]; then
    log_error "GCP_PROJECT_ID not set in .env file"
    exit 1
fi

log_info "Project ID: $PROJECT_ID"
log_info "Region: $REGION"
log_info "Repository: $REPOSITORY"
log_info "Service Account: $SERVICE_ACCOUNT"

# Docker image tag (use git SHA or 'latest')
if command -v git &> /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
    IMAGE_TAG=$(git rev-parse --short HEAD)
else
    IMAGE_TAG="latest"
fi

log_info "Image tag: $IMAGE_TAG"

# =============================================================================
# Service Definitions
# =============================================================================

# Define services with their configurations
declare -A SERVICES=(
    ["drive-intel"]="1Gi:1:300:10"
    ["video-agent"]="2Gi:2:600:10"
    ["ml-service"]="4Gi:2:900:5"
    ["meta-publisher"]="1Gi:1:300:5"
    ["titan-core"]="4Gi:2:900:10"
    ["gateway-api"]="1Gi:1:300:20"
)

# Service order (dependencies first)
SERVICE_ORDER=("drive-intel" "video-agent" "ml-service" "meta-publisher" "titan-core" "gateway-api")

# =============================================================================
# Helper Functions
# =============================================================================

# Check if gcloud is installed and authenticated
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI not found. Please install: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install: https://docs.docker.com/get-docker/"
        exit 1
    fi

    # Check gcloud authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Not authenticated with gcloud. Run: gcloud auth login"
        exit 1
    fi

    # Set project
    gcloud config set project "$PROJECT_ID" --quiet

    log_success "Prerequisites check passed"
}

# Setup Artifact Registry
setup_artifact_registry() {
    log_info "Setting up Artifact Registry..."

    # Check if repository exists
    if gcloud artifacts repositories describe "$REPOSITORY" \
        --location="$REGION" &>/dev/null; then
        log_success "Artifact Registry repository already exists"
    else
        log_info "Creating Artifact Registry repository..."
        gcloud artifacts repositories create "$REPOSITORY" \
            --repository-format=docker \
            --location="$REGION" \
            --description="Gemini Video Docker images"
        log_success "Artifact Registry repository created"
    fi

    # Configure Docker authentication
    gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
}

# Store secrets in Secret Manager
setup_secrets() {
    log_info "Setting up secrets in Secret Manager..."

    # Define secrets to create from environment variables
    declare -A SECRETS=(
        ["gemini-api-key"]="$GEMINI_API_KEY"
        ["anthropic-api-key"]="$ANTHROPIC_API_KEY"
        ["openai-api-key"]="$OPENAI_API_KEY"
        ["database-url"]="$DATABASE_URL"
        ["redis-url"]="$REDIS_URL"
        ["meta-access-token"]="$META_ACCESS_TOKEN"
    )

    for secret_name in "${!SECRETS[@]}"; do
        secret_value="${SECRETS[$secret_name]}"

        # Skip if value is empty
        if [ -z "$secret_value" ]; then
            log_warning "Skipping $secret_name (not set in .env)"
            continue
        fi

        # Check if secret exists
        if gcloud secrets describe "$secret_name" &>/dev/null; then
            log_info "Updating secret: $secret_name"
            echo -n "$secret_value" | gcloud secrets versions add "$secret_name" --data-file=-
        else
            log_info "Creating secret: $secret_name"
            echo -n "$secret_value" | gcloud secrets create "$secret_name" --data-file=-
        fi

        # Grant service account access
        gcloud secrets add-iam-policy-binding "$secret_name" \
            --member="serviceAccount:${SERVICE_ACCOUNT}" \
            --role="roles/secretmanager.secretAccessor" \
            --quiet 2>/dev/null || true
    done

    log_success "Secrets configured"
}

# Build Docker image
build_image() {
    local service=$1
    local service_dir="${PROJECT_ROOT}/services/${service}"
    local image_name="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${service}"

    log_info "Building $service..."

    if [ ! -d "$service_dir" ]; then
        log_error "Service directory not found: $service_dir"
        return 1
    fi

    if [ ! -f "${service_dir}/Dockerfile" ]; then
        log_error "Dockerfile not found for $service"
        return 1
    fi

    # Build with both specific tag and latest
    docker build \
        --tag "${image_name}:${IMAGE_TAG}" \
        --tag "${image_name}:latest" \
        --platform linux/amd64 \
        "$service_dir"

    log_success "Built $service"
}

# Push Docker image
push_image() {
    local service=$1
    local image_name="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${service}"

    log_info "Pushing $service..."

    docker push "${image_name}:${IMAGE_TAG}"
    docker push "${image_name}:latest"

    log_success "Pushed $service"
}

# Get service URL
get_service_url() {
    local service=$1
    local service_name="geminivideo-${service}"

    gcloud run services describe "$service_name" \
        --region="$REGION" \
        --format='value(status.url)' 2>/dev/null || echo ""
}

# Deploy service to Cloud Run
deploy_service() {
    local service=$1
    local config=${SERVICES[$service]}

    # Parse configuration: memory:cpu:timeout:max_instances
    IFS=':' read -r memory cpu timeout max_instances <<< "$config"

    local service_name="geminivideo-${service}"
    local image_name="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${service}:${IMAGE_TAG}"

    log_info "Deploying $service to Cloud Run..."

    # Build base deployment command
    local deploy_cmd=(
        gcloud run deploy "$service_name"
        --image="$image_name"
        --region="$REGION"
        --platform=managed
        --service-account="$SERVICE_ACCOUNT"
        --memory="$memory"
        --cpu="$cpu"
        --timeout="${timeout}s"
        --max-instances="$max_instances"
        --min-instances=0
        --allow-unauthenticated
        --quiet
    )

    # Add service-specific environment variables and secrets
    case $service in
        "gateway-api")
            # Get URLs of backend services
            local titan_url=$(get_service_url "titan-core")
            local video_url=$(get_service_url "video-agent")
            local ml_url=$(get_service_url "ml-service")
            local drive_url=$(get_service_url "drive-intel")
            local meta_url=$(get_service_url "meta-publisher")

            deploy_cmd+=(
                --set-env-vars="NODE_ENV=production,GCP_PROJECT_ID=${PROJECT_ID}"
            )

            # Add service URLs if available
            [ -n "$titan_url" ] && deploy_cmd+=(--set-env-vars="TITAN_CORE_URL=${titan_url}")
            [ -n "$video_url" ] && deploy_cmd+=(--set-env-vars="VIDEO_AGENT_URL=${video_url}")
            [ -n "$ml_url" ] && deploy_cmd+=(--set-env-vars="ML_SERVICE_URL=${ml_url}")
            [ -n "$drive_url" ] && deploy_cmd+=(--set-env-vars="DRIVE_INTEL_URL=${drive_url}")
            [ -n "$meta_url" ] && deploy_cmd+=(--set-env-vars="META_PUBLISHER_URL=${meta_url}")

            deploy_cmd+=(
                --set-secrets="DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest"
            )
            ;;

        "titan-core")
            local video_url=$(get_service_url "video-agent")
            local ml_url=$(get_service_url "ml-service")

            deploy_cmd+=(
                --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID},GCS_BUCKET_NAME=${GCS_BUCKET_NAME:-geminivideo-storage}"
            )

            [ -n "$video_url" ] && deploy_cmd+=(--set-env-vars="VIDEO_AGENT_URL=${video_url}")
            [ -n "$ml_url" ] && deploy_cmd+=(--set-env-vars="ML_SERVICE_URL=${ml_url}")

            deploy_cmd+=(
                --set-secrets="GEMINI_API_KEY=gemini-api-key:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest,OPENAI_API_KEY=openai-api-key:latest,DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest"
            )
            ;;

        "video-agent")
            deploy_cmd+=(
                --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID},TEMP_STORAGE_PATH=/tmp/video,MAX_VIDEO_SIZE_MB=500"
                --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"
            )
            ;;

        "ml-service")
            deploy_cmd+=(
                --set-env-vars="MIN_SAMPLES_FOR_UPDATE=50,LEARNING_RATE=0.01"
                --set-secrets="DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest"
            )
            ;;

        "drive-intel")
            deploy_cmd+=(
                --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID}"
                --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"
            )
            ;;

        "meta-publisher")
            deploy_cmd+=(
                --set-secrets="META_ACCESS_TOKEN=meta-access-token:latest"
            )
            ;;
    esac

    # Execute deployment
    "${deploy_cmd[@]}"

    log_success "Deployed $service"

    # Get and display service URL
    local service_url=$(get_service_url "$service")
    log_info "Service URL: $service_url"
}

# Build, push, and deploy a single service
deploy_single_service() {
    local service=$1

    if [ -z "${SERVICES[$service]}" ]; then
        log_error "Unknown service: $service"
        log_info "Available services: ${!SERVICES[@]}"
        return 1
    fi

    log_info "Deploying service: $service"
    echo "=========================================="

    build_image "$service"
    push_image "$service"
    deploy_service "$service"

    log_success "Service $service deployed successfully!"
}

# Deploy all services
deploy_all_services() {
    log_info "Deploying all services..."
    echo "=========================================="

    # Build all images first (can be parallelized)
    log_info "Building all images..."
    for service in "${SERVICE_ORDER[@]}"; do
        build_image "$service"
    done

    # Push all images (can be parallelized)
    log_info "Pushing all images..."
    for service in "${SERVICE_ORDER[@]}"; do
        push_image "$service"
    done

    # Deploy services in order (sequential due to dependencies)
    log_info "Deploying services in order..."
    for service in "${SERVICE_ORDER[@]}"; do
        deploy_service "$service"
    done

    log_success "All services deployed successfully!"
    echo "=========================================="

    # Display all service URLs
    log_info "Service URLs:"
    for service in "${SERVICE_ORDER[@]}"; do
        local url=$(get_service_url "$service")
        echo "  - $service: $url"
    done
}

# Test deployed services
test_services() {
    log_info "Testing deployed services..."
    echo "=========================================="

    for service in "${SERVICE_ORDER[@]}"; do
        local url=$(get_service_url "$service")
        if [ -n "$url" ]; then
            log_info "Testing $service at $url"

            # Try health endpoint first, fallback to root
            if curl -sf "${url}/health" > /dev/null 2>&1; then
                log_success "$service health check passed"
            elif curl -sf "$url" > /dev/null 2>&1; then
                log_success "$service is reachable"
            else
                log_warning "$service may not be ready yet"
            fi
        else
            log_warning "$service is not deployed"
        fi
    done

    log_info "Test complete!"
}

# =============================================================================
# Main Script
# =============================================================================

main() {
    echo ""
    echo "=========================================="
    echo "  Gemini Video - Cloud Run Deployment"
    echo "=========================================="
    echo ""

    # Check prerequisites
    check_prerequisites

    # Setup infrastructure
    setup_artifact_registry
    setup_secrets

    # Deploy service(s)
    if [ $# -eq 0 ]; then
        # No arguments: deploy all services
        deploy_all_services
    else
        # Specific service provided
        deploy_single_service "$1"
    fi

    # Test services
    echo ""
    test_services

    echo ""
    log_success "Deployment complete!"
    echo ""
    log_info "Next steps:"
    echo "  1. Verify services are running: gcloud run services list --region=$REGION"
    echo "  2. Check logs: gcloud run services logs read SERVICE_NAME --region=$REGION"
    echo "  3. Set up custom domain: See DEPLOY_CLOUD_RUN.md"
    echo "  4. Configure monitoring: Cloud Console > Monitoring"
    echo ""
}

# Run main function
main "$@"
