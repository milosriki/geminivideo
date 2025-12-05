#!/bin/bash
# =============================================================================
# Emergency Rollback Script
# =============================================================================
# Reverts to previous deployment with database restoration
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ROLLBACK_ID="rollback-$(date +%Y%m%d-%H%M%S)"
DEPLOYMENT_ID=${1:-""}

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

# =============================================================================
# Get Previous Deployment Info
# =============================================================================
get_previous_deployment() {
    log_info "Identifying previous deployment..."

    local deployments_dir="/var/log/geminivideo/deployments"

    if [ ! -d "$deployments_dir" ]; then
        log_error "Deployments directory not found: $deployments_dir"
        exit 1
    fi

    # Find the second most recent deployment (current is latest)
    PREVIOUS_DEPLOYMENT=$(ls -t "$deployments_dir"/*.json | grep -v latest | head -2 | tail -1)

    if [ -z "$PREVIOUS_DEPLOYMENT" ]; then
        log_error "No previous deployment found"
        exit 1
    fi

    PREVIOUS_DEPLOYMENT_ID=$(basename "$PREVIOUS_DEPLOYMENT" .json)
    log_info "Previous deployment identified: $PREVIOUS_DEPLOYMENT_ID"
}

# =============================================================================
# Backup Current State
# =============================================================================
backup_current_state() {
    log_info "Backing up current state before rollback..."

    # Backup database
    local backup_file="/tmp/db_backup_before_rollback_${ROLLBACK_ID}.sql"
    log_info "Creating database backup: $backup_file"

    pg_dump "${DATABASE_URL:-postgresql://geminivideo:geminivideo@localhost:5432/geminivideo}" > "$backup_file"

    # Save current container states
    docker ps -a --format "{{.ID}}\t{{.Names}}\t{{.Status}}" > "/tmp/container_state_${ROLLBACK_ID}.txt"

    log_success "Current state backed up"
}

# =============================================================================
# Stop Current Deployment
# =============================================================================
stop_current_deployment() {
    log_info "Stopping current deployment..."

    cd ..
    docker-compose -f docker-compose.production.yml down --remove-orphans
    cd deploy

    log_success "Current deployment stopped"
}

# =============================================================================
# Restore Database
# =============================================================================
restore_database() {
    local restore_db=${1:-true}

    if [ "$restore_db" != true ]; then
        log_info "Skipping database restoration"
        return 0
    fi

    log_warning "Restoring database to previous state..."

    # Find database backup for previous deployment
    local backup_file="/tmp/db_backup_${DEPLOYMENT_ID}.sql"

    if [ ! -f "$backup_file" ]; then
        log_warning "Database backup not found: $backup_file"
        log_warning "Skipping database restoration - manual intervention may be required"
        return 0
    fi

    # Confirm database restoration
    if [ -t 0 ]; then
        read -p "Are you sure you want to restore the database? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            log_warning "Database restoration skipped by user"
            return 0
        fi
    fi

    # Restore database
    log_info "Restoring database from: $backup_file"
    psql "${DATABASE_URL:-postgresql://geminivideo:geminivideo@localhost:5432/geminivideo}" < "$backup_file"

    log_success "Database restored"
}

# =============================================================================
# Start Previous Deployment
# =============================================================================
start_previous_deployment() {
    log_info "Starting previous deployment: $PREVIOUS_DEPLOYMENT_ID"

    # Tag previous images as latest
    local services=("gateway" "titan" "ml" "video")

    for service in "${services[@]}"; do
        if docker images "geminivideo-$service:$PREVIOUS_DEPLOYMENT_ID" --format "{{.Repository}}" | grep -q .; then
            log_info "Tagging $service:$PREVIOUS_DEPLOYMENT_ID as latest"
            docker tag "geminivideo-$service:$PREVIOUS_DEPLOYMENT_ID" "geminivideo-$service:latest"
        fi
    done

    # Start services
    cd ..
    docker-compose -f docker-compose.production.yml up -d
    cd deploy

    log_success "Previous deployment started"
}

# =============================================================================
# Verify Rollback
# =============================================================================
verify_rollback() {
    log_info "Verifying rollback..."

    # Service ports
    declare -A SERVICE_PORTS=(
        ["gateway-api"]="8080"
        ["titan-core"]="8084"
        ["ml-service"]="8003"
        ["video-agent"]="8082"
    )

    local all_healthy=true

    # Wait for services to start
    sleep 30

    for service in "${!SERVICE_PORTS[@]}"; do
        local port="${SERVICE_PORTS[$service]}"
        log_info "Checking $service on port $port..."

        for i in {1..10}; do
            if curl -f -s -o /dev/null "http://localhost:$port/health"; then
                log_success "$service is healthy"
                break
            fi

            if [ $i -eq 10 ]; then
                all_healthy=false
                log_error "$service failed health check"
            else
                log_warning "Health check attempt $i/10 failed, retrying..."
                sleep 10
            fi
        done
    done

    if [ "$all_healthy" = false ]; then
        log_error "Rollback verification failed"
        return 1
    fi

    log_success "Rollback verified successfully"
    return 0
}

# =============================================================================
# Save Rollback Info
# =============================================================================
save_rollback_info() {
    log_info "Saving rollback information..."

    local rollback_file="/var/log/geminivideo/rollbacks/${ROLLBACK_ID}.json"
    mkdir -p "$(dirname "$rollback_file")"

    cat > "$rollback_file" <<EOF
{
    "rollback_id": "$ROLLBACK_ID",
    "timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
    "failed_deployment": "$DEPLOYMENT_ID",
    "restored_deployment": "$PREVIOUS_DEPLOYMENT_ID",
    "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "rolled_back_by": "${USER:-unknown}",
    "reason": "${ROLLBACK_REASON:-Manual rollback initiated}",
    "status": "success"
}
EOF

    log_success "Rollback information saved"
}

# =============================================================================
# Send Notification
# =============================================================================
send_notification() {
    local status=$1
    local message=$2

    log_info "Sending rollback notification..."

    # Slack webhook (if configured)
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"⚠️ ROLLBACK $ROLLBACK_ID: $status - $message\"}" \
            "$SLACK_WEBHOOK_URL" || true
    fi

    # Email notification (if configured)
    if [ -n "${NOTIFICATION_EMAIL:-}" ] && command -v mail &> /dev/null; then
        echo "$message" | mail -s "ROLLBACK $ROLLBACK_ID: $status" "$NOTIFICATION_EMAIL" || true
    fi

    # PagerDuty alert (if configured)
    if [ -n "${PAGERDUTY_API_KEY:-}" ]; then
        curl -X POST https://api.pagerduty.com/incidents \
            -H "Authorization: Token token=$PAGERDUTY_API_KEY" \
            -H "Content-Type: application/json" \
            -d "{
                \"incident\": {
                    \"type\": \"incident\",
                    \"title\": \"Production Rollback: $ROLLBACK_ID\",
                    \"body\": {
                        \"type\": \"incident_body\",
                        \"details\": \"$message\"
                    },
                    \"urgency\": \"high\"
                }
            }" || true
    fi
}

# =============================================================================
# Main Rollback Flow
# =============================================================================
main() {
    log_warning "==================================================================="
    log_warning "INITIATING EMERGENCY ROLLBACK: $ROLLBACK_ID"
    log_warning "==================================================================="

    # Load environment variables
    if [ -f "../.env.production" ]; then
        source "../.env.production"
    fi

    # Confirm rollback if interactive
    if [ -t 0 ]; then
        echo ""
        log_warning "This will rollback the current deployment and may restore the database."
        read -p "Are you sure you want to proceed? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            log_info "Rollback cancelled by user"
            exit 0
        fi
        echo ""
    fi

    # Execute rollback steps
    get_previous_deployment
    backup_current_state
    stop_current_deployment

    # Ask about database restoration
    local restore_db=false
    if [ -t 0 ]; then
        read -p "Do you want to restore the database? (yes/no): " db_confirm
        if [ "$db_confirm" = "yes" ]; then
            restore_db=true
        fi
    fi

    restore_database $restore_db
    start_previous_deployment
    verify_rollback

    # Rollback successful
    save_rollback_info
    send_notification "SUCCESS" "Rollback completed successfully. Restored to deployment: $PREVIOUS_DEPLOYMENT_ID"

    log_success "==================================================================="
    log_success "Rollback $ROLLBACK_ID completed successfully!"
    log_success "Restored to deployment: $PREVIOUS_DEPLOYMENT_ID"
    log_success "==================================================================="

    # Post-rollback instructions
    echo ""
    log_info "Post-Rollback Instructions:"
    log_info "1. Investigate the failed deployment: $DEPLOYMENT_ID"
    log_info "2. Check logs: docker-compose logs"
    log_info "3. Review rollback info: /var/log/geminivideo/rollbacks/${ROLLBACK_ID}.json"
    log_info "4. Test the restored deployment thoroughly"
    echo ""
}

# Run main function
main "$@"
