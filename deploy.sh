#!/bin/bash
# ============================================
# ONE-CLICK DEPLOYMENT SCRIPT
# Deploys the entire Winning Ads Generator stack
# ============================================

set -e

# ---------------------------------------------
# Color Codes for Beautiful Output
# ---------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# ---------------------------------------------
# Emoji & Symbols
# ---------------------------------------------
ROCKET="🚀"
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
CLOCK="⏰"
GEAR="⚙️"
PACKAGE="📦"
CLOUD="☁️"
FIRE="🔥"
SPARKLES="✨"

# ---------------------------------------------
# Global Variables
# ---------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
DEPLOYMENT_LOG="$PROJECT_ROOT/logs/deployment_$(date +%Y%m%d_%H%M%S).log"
REGION="us-central1"
REPO_NAME="geminivideo-repo"
DEPLOYMENT_TYPE=""
ROLLBACK_SNAPSHOTS=()

# Services to deploy
SERVICES=("titan-core" "ml-service" "drive-intel" "video-agent" "meta-publisher" "gateway-api")
DEPLOYED_SERVICES=()

# ---------------------------------------------
# Logging Functions
# ---------------------------------------------
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$DEPLOYMENT_LOG"
}

print_header() {
    echo -e "\n${CYAN}${BOLD}============================================${NC}"
    echo -e "${WHITE}${BOLD}$1${NC}"
    echo -e "${CYAN}${BOLD}============================================${NC}\n"
}

print_step() {
    echo -e "${BLUE}${BOLD}▶ $1${NC}"
    log "INFO" "$1"
}

print_success() {
    echo -e "${GREEN}${CHECK} $1${NC}"
    log "SUCCESS" "$1"
}

print_error() {
    echo -e "${RED}${CROSS} $1${NC}"
    log "ERROR" "$1"
}

print_warning() {
    echo -e "${YELLOW}${WARNING} $1${NC}"
    log "WARNING" "$1"
}

print_info() {
    echo -e "${CYAN}${INFO} $1${NC}"
    log "INFO" "$1"
}

progress_bar() {
    local duration=$1
    local steps=20
    local sleep_time=$(echo "scale=2; $duration / $steps" | bc)

    echo -n "Progress: ["
    for ((i=0; i<$steps; i++)); do
        sleep "$sleep_time"
        echo -n "="
    done
    echo "] Done"
}

spinner() {
    local pid=$1
    local message=$2
    local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0

    while kill -0 $pid 2>/dev/null; do
        i=$(((i + 1) % 10))
        printf "\r${CYAN}${spin:$i:1} ${message}...${NC}"
        sleep 0.1
    done
    printf "\r"
}

# ---------------------------------------------
# Prerequisites Checking
# ---------------------------------------------
check_prerequisites() {
    print_step "Checking prerequisites..."

    local missing_deps=()

    # Check for required commands
    command -v docker >/dev/null 2>&1 || missing_deps+=("docker")
    command -v docker-compose >/dev/null 2>&1 || missing_deps+=("docker-compose")
    command -v node >/dev/null 2>&1 || missing_deps+=("node")
    command -v npm >/dev/null 2>&1 || missing_deps+=("npm")

    if [ "$DEPLOYMENT_TYPE" = "cloud" ] || [ "$DEPLOYMENT_TYPE" = "full" ]; then
        command -v gcloud >/dev/null 2>&1 || missing_deps+=("gcloud")
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        echo -e "\n${YELLOW}Please install the missing dependencies:${NC}"
        for dep in "${missing_deps[@]}"; do
            echo -e "  - $dep"
        done
        exit 1
    fi

    print_success "All prerequisites met"

    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    print_success "Docker daemon is running"

    # Create logs directory
    mkdir -p "$PROJECT_ROOT/logs"
    print_success "Logs directory ready: $DEPLOYMENT_LOG"
}

# ---------------------------------------------
# Environment Loading and Validation
# ---------------------------------------------
load_environment() {
    print_step "Loading environment configuration..."

    local env_file=""

    if [ "$DEPLOYMENT_TYPE" = "local" ]; then
        env_file="$PROJECT_ROOT/.env"
        if [ ! -f "$env_file" ]; then
            print_warning ".env not found, using .env.example"
            if [ -f "$PROJECT_ROOT/.env.example" ]; then
                cp "$PROJECT_ROOT/.env.example" "$env_file"
                print_info "Created .env from .env.example"
            fi
        fi
    else
        env_file="$PROJECT_ROOT/.env.production"
        if [ ! -f "$env_file" ]; then
            print_error ".env.production not found"
            echo -e "\n${YELLOW}Please create .env.production:${NC}"
            echo -e "  cp .env.production.example .env.production"
            echo -e "  # Then edit and fill in your values"
            exit 1
        fi
    fi

    if [ -f "$env_file" ]; then
        set -a
        source "$env_file"
        set +a
        print_success "Environment loaded from $(basename $env_file)"
    fi
}

validate_environment() {
    print_step "Validating environment variables..."

    local required_vars=()
    local missing_vars=()

    if [ "$DEPLOYMENT_TYPE" = "cloud" ] || [ "$DEPLOYMENT_TYPE" = "full" ]; then
        required_vars=("GCP_PROJECT_ID" "GEMINI_API_KEY" "META_ACCESS_TOKEN" "META_AD_ACCOUNT_ID")
    else
        required_vars=("GEMINI_API_KEY")
    fi

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo -e "  ${RED}- $var${NC}"
        done
        exit 1
    fi

    print_success "All required environment variables are set"
}

# ---------------------------------------------
# Local Docker Compose Deployment
# ---------------------------------------------
deploy_local() {
    print_header "LOCAL DEPLOYMENT WITH DOCKER COMPOSE"

    print_step "Stopping any existing containers..."
    docker-compose down 2>/dev/null || true
    print_success "Existing containers stopped"

    print_step "Building Docker images..."
    docker-compose build --parallel 2>&1 | tee -a "$DEPLOYMENT_LOG" &
    local build_pid=$!
    spinner $build_pid "Building images"
    wait $build_pid

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        print_success "Docker images built successfully"
    else
        print_error "Failed to build Docker images"
        exit 1
    fi

    print_step "Starting services..."
    docker-compose up -d 2>&1 | tee -a "$DEPLOYMENT_LOG"

    if [ $? -eq 0 ]; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        exit 1
    fi

    # Wait for services to be healthy
    print_step "Waiting for services to become healthy..."
    sleep 5

    local max_wait=60
    local waited=0
    while [ $waited -lt $max_wait ]; do
        local healthy=$(docker-compose ps | grep -c "healthy" || true)
        echo -ne "\r${CYAN}Healthy services: $healthy/${#SERVICES[@]}${NC}"

        if [ "$healthy" -ge 2 ]; then
            break
        fi

        sleep 2
        waited=$((waited + 2))
    done
    echo ""

    print_success "Local deployment complete!"

    echo -e "\n${GREEN}${BOLD}${SPARKLES} Services are running:${NC}"
    echo -e "  ${CYAN}Gateway API:${NC}      http://localhost:8080"
    echo -e "  ${CYAN}Drive Intel:${NC}      http://localhost:8081"
    echo -e "  ${CYAN}Video Agent:${NC}      http://localhost:8082"
    echo -e "  ${CYAN}ML Service:${NC}       http://localhost:8003"
    echo -e "  ${CYAN}Meta Publisher:${NC}   http://localhost:8083"
    echo -e "  ${CYAN}Titan Core:${NC}       http://localhost:8084"
    echo -e "  ${CYAN}Frontend:${NC}         http://localhost:80"

    echo -e "\n${YELLOW}To view logs:${NC} docker-compose logs -f [service-name]"
    echo -e "${YELLOW}To stop:${NC}      docker-compose down"
}

# ---------------------------------------------
# Cloud Run Deployment
# ---------------------------------------------
setup_gcp_project() {
    print_step "Setting up GCP project..."

    # Set project
    gcloud config set project "$GCP_PROJECT_ID" 2>&1 | tee -a "$DEPLOYMENT_LOG"
    print_success "Project set to $GCP_PROJECT_ID"

    # Enable required APIs
    print_step "Enabling required GCP APIs..."
    local apis=(
        "run.googleapis.com"
        "artifactregistry.googleapis.com"
        "cloudbuild.googleapis.com"
        "secretmanager.googleapis.com"
    )

    for api in "${apis[@]}"; do
        echo -n "  Enabling $api... "
        gcloud services enable "$api" --quiet 2>&1 | tee -a "$DEPLOYMENT_LOG"
        echo -e "${GREEN}✓${NC}"
    done

    print_success "GCP APIs enabled"

    # Create Artifact Registry
    print_step "Creating Artifact Registry..."
    if gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" >/dev/null 2>&1; then
        print_info "Artifact Registry already exists"
    else
        gcloud artifacts repositories create "$REPO_NAME" \
            --repository-format=docker \
            --location="$REGION" \
            --description="Winning Ads Generator Repository" \
            2>&1 | tee -a "$DEPLOYMENT_LOG"
        print_success "Artifact Registry created"
    fi
}

build_and_push_images() {
    print_step "Building and pushing Docker images to GCP..."

    local project_id=$(gcloud config get-value project)

    for service in "${SERVICES[@]}"; do
        local service_dir="$PROJECT_ROOT/services/$service"
        local image_name="$REGION-docker.pkg.dev/$project_id/$REPO_NAME/$service"

        if [ ! -d "$service_dir" ]; then
            print_warning "Service directory not found: $service_dir, skipping..."
            continue
        fi

        print_info "Building $service..."
        echo -e "${CYAN}  Image: $image_name${NC}"

        gcloud builds submit \
            --tag "$image_name" \
            "$service_dir" \
            --timeout=20m \
            2>&1 | tee -a "$DEPLOYMENT_LOG" &

        local build_pid=$!
        spinner $build_pid "Building $service"
        wait $build_pid

        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "$service built and pushed"
            DEPLOYED_SERVICES+=("$service")
        else
            print_error "Failed to build $service"
            return 1
        fi
    done

    print_success "All images built and pushed"
}

deploy_cloud_run_services() {
    print_step "Deploying services to Cloud Run..."

    local project_id=$(gcloud config get-value project)

    # Deploy independent services first
    local independent_services=("titan-core" "ml-service" "drive-intel" "video-agent")

    for service in "${independent_services[@]}"; do
        if [[ ! " ${DEPLOYED_SERVICES[@]} " =~ " ${service} " ]]; then
            continue
        fi

        local image_name="$REGION-docker.pkg.dev/$project_id/$REPO_NAME/$service"

        print_info "Deploying $service to Cloud Run..."

        local env_vars=""
        case $service in
            "titan-core")
                env_vars="GEMINI_API_KEY=$GEMINI_API_KEY,META_APP_ID=$META_APP_ID,META_ACCESS_TOKEN=$META_ACCESS_TOKEN"
                ;;
            *)
                env_vars="PORT=8080"
                ;;
        esac

        gcloud run deploy "$service" \
            --image "$image_name" \
            --region "$REGION" \
            --platform managed \
            --allow-unauthenticated \
            --set-env-vars "$env_vars" \
            --memory 1Gi \
            --cpu 1 \
            --timeout 600 \
            --max-instances 10 \
            --min-instances 0 \
            2>&1 | tee -a "$DEPLOYMENT_LOG"

        if [ $? -eq 0 ]; then
            print_success "$service deployed"
        else
            print_error "Failed to deploy $service"
            return 1
        fi
    done

    # Get service URLs
    print_step "Retrieving service URLs..."
    local titan_url=$(gcloud run services describe titan-core --region "$REGION" --format 'value(status.url)' 2>/dev/null || echo "")
    local ml_url=$(gcloud run services describe ml-service --region "$REGION" --format 'value(status.url)' 2>/dev/null || echo "")
    local drive_url=$(gcloud run services describe drive-intel --region "$REGION" --format 'value(status.url)' 2>/dev/null || echo "")
    local video_url=$(gcloud run services describe video-agent --region "$REGION" --format 'value(status.url)' 2>/dev/null || echo "")

    # Deploy meta-publisher with placeholder
    if [[ " ${DEPLOYED_SERVICES[@]} " =~ " meta-publisher " ]]; then
        print_info "Deploying meta-publisher..."
        local meta_image="$REGION-docker.pkg.dev/$project_id/$REPO_NAME/meta-publisher"

        gcloud run deploy meta-publisher \
            --image "$meta_image" \
            --region "$REGION" \
            --platform managed \
            --allow-unauthenticated \
            --set-env-vars "META_ACCESS_TOKEN=$META_ACCESS_TOKEN,META_AD_ACCOUNT_ID=$META_AD_ACCOUNT_ID,GATEWAY_URL=placeholder" \
            --memory 1Gi \
            --timeout 600 \
            2>&1 | tee -a "$DEPLOYMENT_LOG"

        print_success "meta-publisher deployed"
    fi

    local meta_url=$(gcloud run services describe meta-publisher --region "$REGION" --format 'value(status.url)' 2>/dev/null || echo "")

    # Deploy gateway-api with all service URLs
    if [[ " ${DEPLOYED_SERVICES[@]} " =~ " gateway-api " ]]; then
        print_info "Deploying gateway-api with service URLs..."
        local gateway_image="$REGION-docker.pkg.dev/$project_id/$REPO_NAME/gateway-api"

        gcloud run deploy gateway-api \
            --image "$gateway_image" \
            --region "$REGION" \
            --platform managed \
            --allow-unauthenticated \
            --set-env-vars "DRIVE_INTEL_URL=$drive_url,VIDEO_AGENT_URL=$video_url,ML_SERVICE_URL=$ml_url,META_PUBLISHER_URL=$meta_url,TITAN_CORE_URL=$titan_url" \
            --memory 2Gi \
            --cpu 2 \
            --timeout 600 \
            --max-instances 20 \
            2>&1 | tee -a "$DEPLOYMENT_LOG"

        print_success "gateway-api deployed"
    fi

    # Update meta-publisher with gateway URL
    local gateway_url=$(gcloud run services describe gateway-api --region "$REGION" --format 'value(status.url)' 2>/dev/null || echo "")

    if [ -n "$gateway_url" ] && [[ " ${DEPLOYED_SERVICES[@]} " =~ " meta-publisher " ]]; then
        print_info "Updating meta-publisher with gateway URL..."
        gcloud run services update meta-publisher \
            --region "$REGION" \
            --update-env-vars "GATEWAY_URL=$gateway_url" \
            2>&1 | tee -a "$DEPLOYMENT_LOG"
        print_success "meta-publisher updated"
    fi

    print_success "All Cloud Run services deployed"

    # Display URLs
    echo -e "\n${GREEN}${BOLD}${CLOUD} Cloud Run Service URLs:${NC}"
    [ -n "$gateway_url" ] && echo -e "  ${CYAN}Gateway API:${NC}      $gateway_url"
    [ -n "$drive_url" ] && echo -e "  ${CYAN}Drive Intel:${NC}      $drive_url"
    [ -n "$video_url" ] && echo -e "  ${CYAN}Video Agent:${NC}      $video_url"
    [ -n "$ml_url" ] && echo -e "  ${CYAN}ML Service:${NC}       $ml_url"
    [ -n "$meta_url" ] && echo -e "  ${CYAN}Meta Publisher:${NC}   $meta_url"
    [ -n "$titan_url" ] && echo -e "  ${CYAN}Titan Core:${NC}       $titan_url"

    # Save URLs to file
    cat > "$PROJECT_ROOT/.env.deployed" <<EOF
GATEWAY_URL=$gateway_url
DRIVE_INTEL_URL=$drive_url
VIDEO_AGENT_URL=$video_url
ML_SERVICE_URL=$ml_url
META_PUBLISHER_URL=$meta_url
TITAN_CORE_URL=$titan_url
EOF

    print_success "Service URLs saved to .env.deployed"
}

validate_deployment() {
    print_step "Validating deployed services..."

    if [ "$DEPLOYMENT_TYPE" = "local" ]; then
        local urls=(
            "http://localhost:8080/health"
            "http://localhost:8081/health"
        )
    else
        source "$PROJECT_ROOT/.env.deployed"
        local urls=(
            "$GATEWAY_URL/health"
            "$DRIVE_INTEL_URL/health"
        )
    fi

    local failed=0
    for url in "${urls[@]}"; do
        echo -n "  Testing $url... "
        if curl -sf "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
            failed=$((failed + 1))
        fi
    done

    if [ $failed -eq 0 ]; then
        print_success "All health checks passed"
        return 0
    else
        print_warning "$failed health check(s) failed"
        return 1
    fi
}

# ---------------------------------------------
# Vercel Frontend Deployment
# ---------------------------------------------
show_vercel_instructions() {
    print_header "FRONTEND DEPLOYMENT TO VERCEL"

    echo -e "${YELLOW}${BOLD}To deploy the frontend to Vercel:${NC}\n"

    echo -e "${WHITE}1. Install Vercel CLI:${NC}"
    echo -e "   ${CYAN}npm install -g vercel${NC}\n"

    echo -e "${WHITE}2. Navigate to frontend directory:${NC}"
    echo -e "   ${CYAN}cd $PROJECT_ROOT/frontend${NC}\n"

    echo -e "${WHITE}3. Deploy to Vercel:${NC}"
    echo -e "   ${CYAN}vercel --prod${NC}\n"

    echo -e "${WHITE}4. Set environment variables in Vercel dashboard:${NC}"
    if [ -f "$PROJECT_ROOT/.env.deployed" ]; then
        source "$PROJECT_ROOT/.env.deployed"
        echo -e "   ${CYAN}VITE_GATEWAY_URL${NC}=${GREEN}$GATEWAY_URL${NC}"
        echo -e "   ${CYAN}VITE_DRIVE_INTEL_URL${NC}=${GREEN}$DRIVE_INTEL_URL${NC}"
    else
        echo -e "   ${CYAN}VITE_GATEWAY_URL${NC}=<your-gateway-url>"
        echo -e "   ${CYAN}VITE_DRIVE_INTEL_URL${NC}=<your-drive-intel-url>"
    fi

    echo -e "\n${INFO} Visit: ${CYAN}https://vercel.com/dashboard${NC}"
}

# ---------------------------------------------
# Rollback Functionality
# ---------------------------------------------
rollback_deployment() {
    print_header "ROLLING BACK DEPLOYMENT"
    print_warning "Rolling back to previous version..."

    if [ "$DEPLOYMENT_TYPE" = "local" ]; then
        docker-compose down
        print_success "Local deployment stopped"
    else
        for service in "${DEPLOYED_SERVICES[@]}"; do
            print_info "Rolling back $service..."
            gcloud run services update-traffic "$service" \
                --to-revisions=LATEST=0 \
                --region "$REGION" \
                2>&1 | tee -a "$DEPLOYMENT_LOG"
        done
        print_success "Rollback complete"
    fi
}

# ---------------------------------------------
# Main Deployment Flow
# ---------------------------------------------
deploy_backend() {
    print_header "BACKEND DEPLOYMENT TO CLOUD RUN"

    setup_gcp_project
    build_and_push_images || { print_error "Build failed"; return 1; }
    deploy_cloud_run_services || { print_error "Deployment failed"; return 1; }

    sleep 5
    validate_deployment || print_warning "Some services may not be ready yet"

    print_success "Backend deployment complete!"
}

show_menu() {
    print_header "${ROCKET} WINNING ADS GENERATOR - ONE-CLICK DEPLOYMENT"

    echo -e "${WHITE}What would you like to deploy?${NC}\n"
    echo -e "  ${GREEN}1)${NC} Local Development (Docker Compose)"
    echo -e "  ${GREEN}2)${NC} Backend to Cloud Run (GCP)"
    echo -e "  ${GREEN}3)${NC} Full Stack (Backend + Vercel Instructions)"
    echo -e "  ${GREEN}4)${NC} Show Vercel Instructions Only"
    echo -e "  ${GREEN}5)${NC} Validate Current Deployment"
    echo -e "  ${GREEN}6)${NC} View Deployment Logs"
    echo -e "  ${GREEN}7)${NC} Rollback Deployment"
    echo -e "  ${GREEN}0)${NC} Exit"
    echo ""
    read -p "$(echo -e ${CYAN}Enter choice [0-7]: ${NC})" choice
}

main() {
    # Ensure logs directory exists
    mkdir -p "$PROJECT_ROOT/logs"

    show_menu

    case $choice in
        1)
            DEPLOYMENT_TYPE="local"
            check_prerequisites
            load_environment
            deploy_local
            ;;
        2)
            DEPLOYMENT_TYPE="cloud"
            check_prerequisites
            load_environment
            validate_environment
            deploy_backend
            ;;
        3)
            DEPLOYMENT_TYPE="full"
            check_prerequisites
            load_environment
            validate_environment
            deploy_backend
            show_vercel_instructions
            ;;
        4)
            show_vercel_instructions
            ;;
        5)
            echo -e "\n${BLUE}Select deployment to validate:${NC}"
            echo -e "  1) Local"
            echo -e "  2) Cloud"
            read -p "Choice: " val_choice
            DEPLOYMENT_TYPE=$( [ "$val_choice" = "1" ] && echo "local" || echo "cloud" )
            validate_deployment
            ;;
        6)
            if [ -f "$DEPLOYMENT_LOG" ]; then
                tail -f "$DEPLOYMENT_LOG"
            else
                print_error "No deployment logs found"
            fi
            ;;
        7)
            echo -e "\n${RED}${BOLD}⚠️  WARNING: This will rollback your deployment!${NC}"
            read -p "Are you sure? (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                DEPLOYMENT_TYPE="cloud"
                rollback_deployment
            fi
            ;;
        0)
            echo -e "${CYAN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    echo -e "\n${GREEN}${BOLD}${FIRE} DEPLOYMENT SCRIPT COMPLETE! ${FIRE}${NC}"
    echo -e "${CYAN}Logs saved to: $DEPLOYMENT_LOG${NC}\n"
}

# Handle Ctrl+C
trap 'echo -e "\n${RED}Deployment interrupted${NC}"; exit 130' INT

# Run main
main "$@"
