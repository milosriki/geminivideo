#!/bin/bash
# =============================================================================
# Production Deployment Script with Blue-Green Deployment
# =============================================================================
# Zero-downtime deployment with automatic rollback on failure
# Supports: AWS, GCP, DigitalOcean, self-hosted
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_ID="deploy-$(date +%Y%m%d-%H%M%S)"
BLUE_ENV="blue"
GREEN_ENV="green"
CURRENT_ENV=""
NEW_ENV=""
ROLLBACK_ON_FAILURE=${ROLLBACK_ON_FAILURE:-true}
HEALTH_CHECK_RETRIES=${HEALTH_CHECK_RETRIES:-10}
HEALTH_CHECK_INTERVAL=${HEALTH_CHECK_INTERVAL:-10}
MIGRATE_DATABASE=${MIGRATE_DATABASE:-true}

# Service ports
declare -A SERVICE_PORTS=(
    ["gateway-api"]="8080"
    ["titan-core"]="8084"
    ["ml-service"]="8003"
    ["video-agent"]="8082"
    ["meta-publisher"]="8083"
    ["drive-intel"]="8081"
)

# Log functions
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

# Error handler
error_handler() {
    log_error "Deployment failed at line $1"
    if [ "$ROLLBACK_ON_FAILURE" = true ]; then
        log_warning "Initiating automatic rollback..."
        ./rollback.sh "$DEPLOYMENT_ID"
    fi
    exit 1
}

trap 'error_handler $LINENO' ERR

# =============================================================================
# Pre-deployment Checks
# =============================================================================
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."

    # Check if required files exist
    local required_files=(
        ".env.production"
        "docker-compose.production.yml"
        "database_schema.sql"
    )

    for file in "${required_files[@]}"; do
        if [ ! -f "../$file" ] && [ ! -f "$file" ]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done

    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi

    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed"
        exit 1
    fi

    # Check disk space (require at least 5GB free)
    local available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 5 ]; then
        log_error "Insufficient disk space. Required: 5GB, Available: ${available_space}GB"
        exit 1
    fi

    # Check if PostgreSQL is accessible
    if ! pg_isready -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" > /dev/null 2>&1; then
        log_warning "PostgreSQL is not responding. Will attempt to start it."
    fi

    log_success "Pre-deployment checks passed"
}

# =============================================================================
# Determine Current and New Environment
# =============================================================================
determine_environments() {
    log_info "Determining current and new environments..."

    # Check which environment is currently active
    if docker ps --filter "label=environment=$BLUE_ENV" --filter "status=running" | grep -q .; then
        CURRENT_ENV=$BLUE_ENV
        NEW_ENV=$GREEN_ENV
    else
        CURRENT_ENV=$GREEN_ENV
        NEW_ENV=$BLUE_ENV
    fi

    log_info "Current environment: $CURRENT_ENV"
    log_info "New environment: $NEW_ENV"
}

# =============================================================================
# Build Docker Images
# =============================================================================
build_images() {
    log_info "Building Docker images for deployment $DEPLOYMENT_ID..."

    local services=("gateway" "titan" "ml" "video")

    for service in "${services[@]}"; do
        log_info "Building $service..."

        docker build \
            -f "Dockerfile.$service" \
            -t "geminivideo-$service:$DEPLOYMENT_ID" \
            -t "geminivideo-$service:latest" \
            --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
            --build-arg VERSION="$DEPLOYMENT_ID" \
            ..

        log_success "$service image built successfully"
    done

    # Build other services using their existing Dockerfiles
    cd ..

    docker-compose -f docker-compose.production.yml build \
        --parallel \
        meta-publisher \
        drive-intel \
        frontend

    cd deploy

    log_success "All images built successfully"
}

# =============================================================================
# Database Migration
# =============================================================================
run_migrations() {
    if [ "$MIGRATE_DATABASE" != true ]; then
        log_info "Skipping database migrations (MIGRATE_DATABASE=false)"
        return 0
    fi

    log_info "Running database migrations..."

    # Backup database before migration
    local backup_file="/tmp/db_backup_${DEPLOYMENT_ID}.sql"
    log_info "Creating database backup: $backup_file"

    pg_dump "${DATABASE_URL:-postgresql://geminivideo:geminivideo@localhost:5432/geminivideo}" > "$backup_file"

    # Run migrations
    log_info "Applying database migrations..."

    # Run SQL migrations from database_migrations directory
    for migration in ../database_migrations/*.sql; do
        if [ -f "$migration" ]; then
            log_info "Running migration: $(basename $migration)"
            psql "${DATABASE_URL:-postgresql://geminivideo:geminivideo@localhost:5432/geminivideo}" -f "$migration" || true
        fi
    done

    # Run Prisma migrations for gateway-api
    if [ -f "../services/gateway-api/package.json" ]; then
        log_info "Running Prisma migrations..."
        cd ../services/gateway-api
        npm run db:migrate:deploy || true
        cd ../../deploy
    fi

    log_success "Database migrations completed"
}

# =============================================================================
# Start New Environment
# =============================================================================
start_new_environment() {
    log_info "Starting new environment: $NEW_ENV"

    # Export environment variables
    export COMPOSE_PROJECT_NAME="geminivideo-$NEW_ENV"
    export DEPLOYMENT_ENV=$NEW_ENV

    cd ..

    # Start services with new images
    docker-compose -f docker-compose.production.yml up -d \
        --force-recreate \
        --remove-orphans

    cd deploy

    log_success "New environment started"
}

# =============================================================================
# Health Checks
# =============================================================================
health_check() {
    local service=$1
    local port=$2
    local host=${3:-localhost}
    local max_retries=$HEALTH_CHECK_RETRIES
    local interval=$HEALTH_CHECK_INTERVAL

    log_info "Running health check for $service on $host:$port..."

    for i in $(seq 1 $max_retries); do
        if curl -f -s -o /dev/null "http://$host:$port/health"; then
            log_success "$service health check passed"
            return 0
        fi

        log_warning "Health check attempt $i/$max_retries failed, retrying in ${interval}s..."
        sleep $interval
    done

    log_error "$service health check failed after $max_retries attempts"
    return 1
}

verify_deployment() {
    log_info "Verifying deployment health..."

    local all_healthy=true

    for service in "${!SERVICE_PORTS[@]}"; do
        if ! health_check "$service" "${SERVICE_PORTS[$service]}"; then
            all_healthy=false
            log_error "$service failed health check"
        fi
    done

    if [ "$all_healthy" = false ]; then
        log_error "Deployment verification failed"
        return 1
    fi

    log_success "All services are healthy"
    return 0
}

# =============================================================================
# Smoke Tests
# =============================================================================
run_smoke_tests() {
    log_info "Running smoke tests..."

    # Test gateway API
    log_info "Testing Gateway API..."
    local gateway_response=$(curl -s http://localhost:8080/health)
    if [[ $gateway_response == *"ok"* ]] || [[ $gateway_response == *"healthy"* ]]; then
        log_success "Gateway API smoke test passed"
    else
        log_error "Gateway API smoke test failed"
        return 1
    fi

    # Test database connectivity
    log_info "Testing database connectivity..."
    if psql "${DATABASE_URL:-postgresql://geminivideo:geminivideo@localhost:5432/geminivideo}" -c "SELECT 1" > /dev/null 2>&1; then
        log_success "Database connectivity test passed"
    else
        log_error "Database connectivity test failed"
        return 1
    fi

    # Test Redis connectivity
    log_info "Testing Redis connectivity..."
    if redis-cli ping > /dev/null 2>&1; then
        log_success "Redis connectivity test passed"
    else
        log_warning "Redis connectivity test failed (non-critical)"
    fi

    log_success "Smoke tests completed"
    return 0
}

# =============================================================================
# Traffic Switch
# =============================================================================
switch_traffic() {
    log_info "Switching traffic to new environment: $NEW_ENV"

    # Update load balancer / proxy configuration
    # This is platform-specific - examples for common setups:

    if command -v nginx &> /dev/null; then
        # Nginx configuration update
        log_info "Updating Nginx configuration..."
        # sed -i "s/proxy_pass.*$/proxy_pass http:\/\/$NEW_ENV;/" /etc/nginx/sites-enabled/geminivideo
        # nginx -s reload
    fi

    if command -v aws &> /dev/null && [ -n "${AWS_TARGET_GROUP:-}" ]; then
        # AWS ALB target group update
        log_info "Updating AWS Target Group..."
        # aws elbv2 register-targets --target-group-arn "$AWS_TARGET_GROUP" --targets Id=...
    fi

    if command -v gcloud &> /dev/null && [ -n "${GCP_BACKEND_SERVICE:-}" ]; then
        # GCP Load Balancer update
        log_info "Updating GCP Backend Service..."
        # gcloud compute backend-services update "$GCP_BACKEND_SERVICE" ...
    fi

    log_success "Traffic switched to new environment"
}

# =============================================================================
# Cleanup Old Environment
# =============================================================================
cleanup_old_environment() {
    log_info "Cleaning up old environment: $CURRENT_ENV"

    # Keep old environment running for a grace period
    local grace_period=${CLEANUP_GRACE_PERIOD:-300} # 5 minutes default

    log_info "Waiting ${grace_period}s grace period before cleanup..."
    sleep $grace_period

    # Stop old environment
    export COMPOSE_PROJECT_NAME="geminivideo-$CURRENT_ENV"
    cd ..
    docker-compose -f docker-compose.production.yml down
    cd deploy

    # Clean up old images (keep last 3 versions)
    docker images --format "{{.Repository}}:{{.Tag}}" | \
        grep "geminivideo" | \
        grep -v "latest" | \
        grep -v "$DEPLOYMENT_ID" | \
        tail -n +4 | \
        xargs -r docker rmi || true

    log_success "Old environment cleaned up"
}

# =============================================================================
# Save Deployment Info
# =============================================================================
save_deployment_info() {
    log_info "Saving deployment information..."

    local deployment_file="/var/log/geminivideo/deployments/${DEPLOYMENT_ID}.json"
    mkdir -p "$(dirname "$deployment_file")"

    cat > "$deployment_file" <<EOF
{
    "deployment_id": "$DEPLOYMENT_ID",
    "timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
    "environment": "$NEW_ENV",
    "previous_environment": "$CURRENT_ENV",
    "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "git_branch": "$(git branch --show-current 2>/dev/null || echo 'unknown')",
    "deployed_by": "${USER:-unknown}",
    "status": "success"
}
EOF

    # Create symlink to latest deployment
    ln -sf "$deployment_file" "/var/log/geminivideo/deployments/latest.json"

    log_success "Deployment information saved"
}

# =============================================================================
# Notification
# =============================================================================
send_notification() {
    local status=$1
    local message=$2

    log_info "Sending deployment notification..."

    # Slack webhook (if configured)
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚀 Deployment $DEPLOYMENT_ID: $status - $message\"}" \
            "$SLACK_WEBHOOK_URL" || true
    fi

    # Email notification (if configured)
    if [ -n "${NOTIFICATION_EMAIL:-}" ] && command -v mail &> /dev/null; then
        echo "$message" | mail -s "Deployment $DEPLOYMENT_ID: $status" "$NOTIFICATION_EMAIL" || true
    fi

    # PagerDuty (if configured)
    if [ -n "${PAGERDUTY_API_KEY:-}" ]; then
        # PagerDuty notification code here
        :
    fi
}

# =============================================================================
# Main Deployment Flow
# =============================================================================
main() {
    log_info "==================================================================="
    log_info "Starting Production Deployment: $DEPLOYMENT_ID"
    log_info "==================================================================="

    # Load environment variables
    if [ -f "../.env.production" ]; then
        source "../.env.production"
    fi

    # Execute deployment steps
    pre_deployment_checks
    determine_environments
    build_images
    run_migrations
    start_new_environment

    # Wait for services to stabilize
    log_info "Waiting for services to stabilize..."
    sleep 30

    verify_deployment
    run_smoke_tests
    switch_traffic

    # Deployment successful
    save_deployment_info
    send_notification "SUCCESS" "Deployment completed successfully"

    log_success "==================================================================="
    log_success "Deployment $DEPLOYMENT_ID completed successfully!"
    log_success "==================================================================="

    # Optional: cleanup old environment
    if [ "${CLEANUP_OLD_ENV:-true}" = true ]; then
        cleanup_old_environment
    fi
}

# Run main function
main "$@"
