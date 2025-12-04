#!/bin/bash
# =============================================================================
# Gemini Video - Production Deployment Script
# =============================================================================
# This script handles:
# - Building Docker images for all services
# - Pushing images to container registry
# - Deploying to production environment (Cloud Run or Docker Compose)
# - Health check verification
# - Rollback capability
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${ENV_FILE:-.env.production}"

# Load environment variables
if [ -f "$PROJECT_ROOT/$ENV_FILE" ]; then
    echo -e "${CYAN}Loading environment from $ENV_FILE${NC}"
    set -a
    source "$PROJECT_ROOT/$ENV_FILE"
    set +a
else
    echo -e "${YELLOW}Warning: $ENV_FILE not found. Using environment variables.${NC}"
fi

# Required configuration
PROJECT_ID="${GCP_PROJECT_ID}"
REGION="${CLOUD_RUN_REGION:-us-central1}"
REGISTRY_URL="${REGISTRY_URL:-${REGION}-docker.pkg.dev/${PROJECT_ID}/geminivideo-repo}"
IMAGE_TAG="${IMAGE_TAG:-$(date +%Y%m%d-%H%M%S)}"
DEPLOYMENT_TARGET="${DEPLOYMENT_TARGET:-cloud-run}" # cloud-run or docker-compose

# Services to deploy
SERVICES=(
    "gateway-api:2Gi:2"
    "drive-intel:4Gi:4"
    "video-agent:4Gi:2"
    "ml-service:16Gi:4"
    "meta-publisher:1Gi:1"
    "titan-core:2Gi:1"
    "frontend:512Mi:1"
)

# Backup for rollback
BACKUP_DIR="$PROJECT_ROOT/.deployments"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/deployment-$(date +%Y%m%d-%H%M%S).txt"

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
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

log_step() {
    echo -e "\n${MAGENTA}===${NC} $1 ${MAGENTA}===${NC}\n"
}

# =============================================================================
# Validation Functions
# =============================================================================

validate_prerequisites() {
    log_step "Validating Prerequisites"

    local missing_tools=()

    # Check required tools
    command -v docker >/dev/null 2>&1 || missing_tools+=("docker")

    if [ "$DEPLOYMENT_TARGET" == "cloud-run" ]; then
        command -v gcloud >/dev/null 2>&1 || missing_tools+=("gcloud")
    fi

    if [ "$DEPLOYMENT_TARGET" == "docker-compose" ]; then
        command -v docker-compose >/dev/null 2>&1 || missing_tools+=("docker-compose")
    fi

    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi

    # Validate GCP authentication (if deploying to Cloud Run)
    if [ "$DEPLOYMENT_TARGET" == "cloud-run" ]; then
        if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
            log_error "Not authenticated with gcloud. Run 'gcloud auth login'"
            exit 1
        fi

        if [ -z "$PROJECT_ID" ]; then
            log_error "GCP_PROJECT_ID is not set"
            exit 1
        fi

        gcloud config set project "$PROJECT_ID"
    fi

    # Validate required environment variables
    local required_vars=(
        "GEMINI_API_KEY"
        "DATABASE_URL"
    )

    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi

    log_success "All prerequisites validated"
}

# =============================================================================
# Build Functions
# =============================================================================

build_images() {
    log_step "Building Docker Images"

    local services=(
        "gateway-api"
        "drive-intel"
        "video-agent"
        "ml-service"
        "meta-publisher"
        "titan-core"
        "frontend"
    )

    for service in "${services[@]}"; do
        log_info "Building $service..."

        local context_dir="$PROJECT_ROOT/services/$service"
        if [ "$service" == "frontend" ]; then
            context_dir="$PROJECT_ROOT/frontend"
        fi

        if [ ! -d "$context_dir" ]; then
            log_warning "Service directory not found: $context_dir (skipping)"
            continue
        fi

        local image_name="$REGISTRY_URL/$service:$IMAGE_TAG"
        local latest_image="$REGISTRY_URL/$service:latest"

        # Build with BuildKit disabled for npm compatibility
        DOCKER_BUILDKIT=0 docker build \
            --tag "$image_name" \
            --tag "$latest_image" \
            "$context_dir"

        if [ $? -eq 0 ]; then
            log_success "Built $service"
        else
            log_error "Failed to build $service"
            exit 1
        fi
    done

    log_success "All images built successfully"
}

# =============================================================================
# Push Functions
# =============================================================================

push_images() {
    log_step "Pushing Images to Registry"

    if [ "$DEPLOYMENT_TARGET" == "cloud-run" ]; then
        # Configure Docker for Artifact Registry
        gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
    fi

    local services=(
        "gateway-api"
        "drive-intel"
        "video-agent"
        "ml-service"
        "meta-publisher"
        "titan-core"
        "frontend"
    )

    for service in "${services[@]}"; do
        log_info "Pushing $service..."

        local image_name="$REGISTRY_URL/$service:$IMAGE_TAG"
        local latest_image="$REGISTRY_URL/$service:latest"

        docker push "$image_name"
        docker push "$latest_image"

        if [ $? -eq 0 ]; then
            log_success "Pushed $service"
        else
            log_error "Failed to push $service"
            exit 1
        fi
    done

    log_success "All images pushed successfully"
}

# =============================================================================
# Deploy Functions - Cloud Run
# =============================================================================

deploy_to_cloud_run() {
    log_step "Deploying to GCP Cloud Run"

    # Save current deployment state for rollback
    save_deployment_state

    # Deploy services in dependency order
    deploy_cloud_run_service "ml-service" "16Gi" "4" "DATABASE_URL=$DATABASE_URL"
    deploy_cloud_run_service "drive-intel" "4Gi" "4" "DATABASE_URL=$DATABASE_URL,REDIS_URL=$REDIS_URL,GEMINI_API_KEY=$GEMINI_API_KEY,GCP_PROJECT_ID=$PROJECT_ID"
    deploy_cloud_run_service "video-agent" "4Gi" "2" "DATABASE_URL=$DATABASE_URL,REDIS_URL=$REDIS_URL"
    deploy_cloud_run_service "meta-publisher" "1Gi" "1" "META_ACCESS_TOKEN=$META_ACCESS_TOKEN,META_AD_ACCOUNT_ID=$META_AD_ACCOUNT_ID,META_APP_ID=$META_APP_ID,META_APP_SECRET=$META_APP_SECRET"
    deploy_cloud_run_service "titan-core" "2Gi" "1" "GEMINI_API_KEY=$GEMINI_API_KEY,META_ACCESS_TOKEN=$META_ACCESS_TOKEN"

    # Get service URLs for gateway
    local drive_url=$(gcloud run services describe drive-intel --region="$REGION" --format='value(status.url)' 2>/dev/null || echo "")
    local video_url=$(gcloud run services describe video-agent --region="$REGION" --format='value(status.url)' 2>/dev/null || echo "")
    local ml_url=$(gcloud run services describe ml-service --region="$REGION" --format='value(status.url)' 2>/dev/null || echo "")
    local meta_url=$(gcloud run services describe meta-publisher --region="$REGION" --format='value(status.url)' 2>/dev/null || echo "")
    local titan_url=$(gcloud run services describe titan-core --region="$REGION" --format='value(status.url)' 2>/dev/null || echo "")

    # Deploy gateway with all service URLs
    deploy_cloud_run_service "gateway-api" "2Gi" "2" \
        "DATABASE_URL=$DATABASE_URL,REDIS_URL=$REDIS_URL,DRIVE_INTEL_URL=$drive_url,VIDEO_AGENT_URL=$video_url,ML_SERVICE_URL=$ml_url,META_PUBLISHER_URL=$meta_url,TITAN_CORE_URL=$titan_url,GEMINI_API_KEY=$GEMINI_API_KEY,JWT_SECRET=$JWT_SECRET,CORS_ORIGINS=$CORS_ORIGINS"

    # Get gateway URL for frontend
    local gateway_url=$(gcloud run services describe gateway-api --region="$REGION" --format='value(status.url)' 2>/dev/null || echo "")

    # Deploy frontend
    deploy_cloud_run_service "frontend" "512Mi" "1" "VITE_GATEWAY_URL=$gateway_url,VITE_ENV=production"

    log_success "All services deployed to Cloud Run"

    # Display service URLs
    display_service_urls
}

deploy_cloud_run_service() {
    local service_name=$1
    local memory=$2
    local cpu=$3
    local env_vars=$4

    log_info "Deploying $service_name to Cloud Run..."

    local image="$REGISTRY_URL/$service_name:$IMAGE_TAG"
    local timeout="${CLOUD_RUN_TIMEOUT:-600}"
    local min_instances="${CLOUD_RUN_MIN_INSTANCES:-0}"
    local max_instances="${CLOUD_RUN_MAX_INSTANCES:-10}"

    gcloud run deploy "$service_name" \
        --image="$image" \
        --region="$REGION" \
        --platform=managed \
        --allow-unauthenticated \
        --memory="$memory" \
        --cpu="$cpu" \
        --timeout="$timeout" \
        --min-instances="$min_instances" \
        --max-instances="$max_instances" \
        --set-env-vars="$env_vars" \
        --quiet

    if [ $? -eq 0 ]; then
        log_success "Deployed $service_name"
    else
        log_error "Failed to deploy $service_name"
        exit 1
    fi
}

# =============================================================================
# Deploy Functions - Docker Compose
# =============================================================================

deploy_to_docker_compose() {
    log_step "Deploying with Docker Compose"

    cd "$PROJECT_ROOT"

    # Pull latest images (if using registry)
    if [ -n "$REGISTRY_URL" ]; then
        log_info "Pulling latest images..."
        docker-compose -f docker-compose.production.yml pull
    fi

    # Stop existing containers
    log_info "Stopping existing containers..."
    docker-compose -f docker-compose.production.yml down

    # Start services
    log_info "Starting services..."
    docker-compose -f docker-compose.production.yml up -d

    if [ $? -eq 0 ]; then
        log_success "Services started successfully"
    else
        log_error "Failed to start services"
        exit 1
    fi

    # Wait for services to be healthy
    verify_health_docker_compose
}

# =============================================================================
# Health Check Functions
# =============================================================================

verify_health_cloud_run() {
    log_step "Verifying Service Health (Cloud Run)"

    local services=(
        "gateway-api"
        "drive-intel"
        "video-agent"
        "ml-service"
        "meta-publisher"
        "titan-core"
        "frontend"
    )

    for service in "${services[@]}"; do
        log_info "Checking $service..."

        local url=$(gcloud run services describe "$service" --region="$REGION" --format='value(status.url)' 2>/dev/null)

        if [ -z "$url" ]; then
            log_warning "$service not deployed"
            continue
        fi

        # Try to access health endpoint
        local max_retries=5
        local retry=0
        local healthy=false

        while [ $retry -lt $max_retries ]; do
            if curl -sf "${url}/health" > /dev/null 2>&1; then
                healthy=true
                break
            fi
            retry=$((retry + 1))
            sleep 5
        done

        if [ "$healthy" = true ]; then
            log_success "$service is healthy"
        else
            log_warning "$service health check failed (this may be normal if /health endpoint is not implemented)"
        fi
    done
}

verify_health_docker_compose() {
    log_step "Verifying Service Health (Docker Compose)"

    local max_wait=120
    local waited=0

    log_info "Waiting for services to become healthy..."

    while [ $waited -lt $max_wait ]; do
        local unhealthy=$(docker-compose -f docker-compose.production.yml ps --format json | jq -r '.[] | select(.Health != "healthy") | .Service' 2>/dev/null)

        if [ -z "$unhealthy" ]; then
            log_success "All services are healthy"
            return 0
        fi

        sleep 5
        waited=$((waited + 5))
    done

    log_warning "Some services may not be healthy yet. Check: docker-compose ps"
}

# =============================================================================
# Rollback Functions
# =============================================================================

save_deployment_state() {
    log_info "Saving deployment state for rollback..."

    if [ "$DEPLOYMENT_TARGET" == "cloud-run" ]; then
        gcloud run services list --region="$REGION" --format=json > "$BACKUP_FILE"
        log_success "Deployment state saved to $BACKUP_FILE"
    fi
}

rollback_deployment() {
    log_step "Rolling Back Deployment"

    if [ "$DEPLOYMENT_TARGET" == "cloud-run" ]; then
        log_error "Rollback for Cloud Run requires manual intervention"
        log_info "To rollback a service, use:"
        log_info "  gcloud run services update-traffic SERVICE_NAME --to-revisions PREVIOUS_REVISION=100 --region=$REGION"
        log_info "Previous deployment state saved in: $BACKUP_FILE"
    elif [ "$DEPLOYMENT_TARGET" == "docker-compose" ]; then
        log_info "Rolling back Docker Compose deployment..."
        cd "$PROJECT_ROOT"
        docker-compose -f docker-compose.production.yml down
        # User should manually specify the previous image tags
        log_warning "Please update IMAGE_TAG in .env.production to the previous version and redeploy"
    fi
}

# =============================================================================
# Display Functions
# =============================================================================

display_service_urls() {
    log_step "Deployment Summary"

    if [ "$DEPLOYMENT_TARGET" == "cloud-run" ]; then
        echo -e "${GREEN}Service URLs:${NC}\n"

        local services=(
            "frontend"
            "gateway-api"
            "drive-intel"
            "video-agent"
            "ml-service"
            "meta-publisher"
            "titan-core"
        )

        for service in "${services[@]}"; do
            local url=$(gcloud run services describe "$service" --region="$REGION" --format='value(status.url)' 2>/dev/null)
            if [ -n "$url" ]; then
                printf "  ${CYAN}%-20s${NC} %s\n" "$service:" "$url"
            fi
        done

        echo ""
        local frontend_url=$(gcloud run services describe "frontend" --region="$REGION" --format='value(status.url)' 2>/dev/null)
        if [ -n "$frontend_url" ]; then
            echo -e "${GREEN}Access your application at:${NC} ${BLUE}$frontend_url${NC}"
        fi
    elif [ "$DEPLOYMENT_TARGET" == "docker-compose" ]; then
        echo -e "${GREEN}Services running on localhost:${NC}\n"
        echo -e "  ${CYAN}Frontend:${NC}       http://localhost"
        echo -e "  ${CYAN}Gateway API:${NC}    http://localhost:8080"
        echo -e "  ${CYAN}Drive Intel:${NC}    http://localhost:8081"
        echo -e "  ${CYAN}Video Agent:${NC}    http://localhost:8082"
        echo -e "  ${CYAN}ML Service:${NC}     http://localhost:8003"
        echo -e "  ${CYAN}Meta Publisher:${NC} http://localhost:8083"
        echo -e "  ${CYAN}Titan Core:${NC}     http://localhost:8084"
    fi

    echo ""
}

display_logs() {
    log_step "Viewing Logs"

    if [ "$DEPLOYMENT_TARGET" == "cloud-run" ]; then
        log_info "To view logs, use:"
        log_info "  gcloud run services logs read SERVICE_NAME --region=$REGION"
    elif [ "$DEPLOYMENT_TARGET" == "docker-compose" ]; then
        log_info "To view logs, use:"
        log_info "  docker-compose -f docker-compose.production.yml logs -f [SERVICE_NAME]"
    fi
}

# =============================================================================
# Main Deployment Flow
# =============================================================================

main() {
    echo -e "${MAGENTA}"
    echo "============================================================================="
    echo "  Gemini Video - Production Deployment"
    echo "============================================================================="
    echo -e "${NC}"
    echo "  Project ID:        $PROJECT_ID"
    echo "  Region:            $REGION"
    echo "  Deployment Target: $DEPLOYMENT_TARGET"
    echo "  Image Tag:         $IMAGE_TAG"
    echo "  Registry:          $REGISTRY_URL"
    echo ""

    # Parse command line arguments
    local skip_build=false
    local skip_push=false
    local skip_deploy=false
    local do_rollback=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-build)
                skip_build=true
                shift
                ;;
            --skip-push)
                skip_push=true
                shift
                ;;
            --skip-deploy)
                skip_deploy=true
                shift
                ;;
            --rollback)
                do_rollback=true
                shift
                ;;
            --target)
                DEPLOYMENT_TARGET="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-build    Skip building Docker images"
                echo "  --skip-push     Skip pushing images to registry"
                echo "  --skip-deploy   Skip deployment step"
                echo "  --rollback      Rollback to previous deployment"
                echo "  --target        Deployment target: cloud-run or docker-compose"
                echo "  --help          Show this help message"
                echo ""
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Handle rollback
    if [ "$do_rollback" = true ]; then
        rollback_deployment
        exit 0
    fi

    # Validate prerequisites
    validate_prerequisites

    # Build images
    if [ "$skip_build" = false ]; then
        build_images
    else
        log_warning "Skipping build step"
    fi

    # Push images
    if [ "$skip_push" = false ] && [ "$DEPLOYMENT_TARGET" == "cloud-run" ]; then
        push_images
    elif [ "$skip_push" = true ]; then
        log_warning "Skipping push step"
    fi

    # Deploy
    if [ "$skip_deploy" = false ]; then
        if [ "$DEPLOYMENT_TARGET" == "cloud-run" ]; then
            deploy_to_cloud_run
            verify_health_cloud_run
        elif [ "$DEPLOYMENT_TARGET" == "docker-compose" ]; then
            deploy_to_docker_compose
        else
            log_error "Invalid deployment target: $DEPLOYMENT_TARGET"
            exit 1
        fi
    else
        log_warning "Skipping deploy step"
    fi

    # Display summary
    display_service_urls
    display_logs

    log_success "Deployment completed successfully!"
    echo ""
}

# Run main function
main "$@"
