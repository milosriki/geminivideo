#!/bin/bash
# =============================================================================
# Gemini Video - Interactive Environment Setup Script
# =============================================================================
# This script helps you set up environment variables for all services
# - Prompts for required values with validation
# - Creates .env files for each service
# - Validates API keys and connections
# - Outputs a comprehensive summary
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMPLATE_FILE="$PROJECT_ROOT/.env.deployment"
OUTPUT_FILE="$PROJECT_ROOT/.env.production"

# Associative arrays to store configurations
declare -A CONFIG
declare -A VALIDATIONS

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo -e "\n${MAGENTA}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║${NC}  ${BOLD}Gemini Video - Interactive Environment Setup${NC}                  ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_section() {
    echo -e "\n${CYAN}┌─────────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC} ${BOLD}$1${NC}"
    echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────┘${NC}\n"
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

prompt_input() {
    local prompt="$1"
    local var_name="$2"
    local default="$3"
    local secret="${4:-false}"
    local value=""

    if [ -n "$default" ]; then
        echo -e "${CYAN}?${NC} $prompt"
        echo -e "  ${YELLOW}(default: $default)${NC}"
    else
        echo -e "${CYAN}?${NC} $prompt"
    fi

    if [ "$secret" = "true" ]; then
        read -s -p "  > " value
        echo ""
    else
        read -p "  > " value
    fi

    if [ -z "$value" ] && [ -n "$default" ]; then
        value="$default"
    fi

    CONFIG[$var_name]="$value"
}

prompt_confirm() {
    local prompt="$1"
    local default="${2:-n}"
    local response

    if [ "$default" = "y" ]; then
        echo -e "${CYAN}?${NC} $prompt ${YELLOW}[Y/n]${NC}"
    else
        echo -e "${CYAN}?${NC} $prompt ${YELLOW}[y/N]${NC}"
    fi

    read -p "  > " response
    response=${response:-$default}

    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

validate_not_empty() {
    local value="$1"
    local name="$2"

    if [ -z "$value" ] || [[ "$value" =~ ^(your-|YOUR_) ]]; then
        log_error "$name cannot be empty or use placeholder value"
        return 1
    fi
    return 0
}

validate_url() {
    local url="$1"
    local name="$2"

    if [[ ! "$url" =~ ^https?:// ]]; then
        log_error "$name must be a valid URL starting with http:// or https://"
        return 1
    fi
    return 0
}

validate_email() {
    local email="$1"
    local name="$2"

    if [[ ! "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        log_error "$name must be a valid email address"
        return 1
    fi
    return 0
}

validate_postgres_url() {
    local url="$1"

    if [[ ! "$url" =~ ^postgresql:// ]]; then
        log_error "Database URL must start with postgresql://"
        return 1
    fi
    return 0
}

validate_redis_url() {
    local url="$1"

    if [[ ! "$url" =~ ^redis(s)?:// ]]; then
        log_error "Redis URL must start with redis:// or rediss://"
        return 1
    fi
    return 0
}

test_gemini_key() {
    local key="$1"
    log_info "Testing Gemini API key..."

    local response=$(curl -s -o /dev/null -w "%{http_code}" \
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro?key=$key")

    if [ "$response" = "200" ]; then
        log_success "Gemini API key is valid"
        return 0
    else
        log_error "Gemini API key validation failed (HTTP $response)"
        return 1
    fi
}

test_openai_key() {
    local key="$1"
    log_info "Testing OpenAI API key..."

    local response=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $key" \
        "https://api.openai.com/v1/models")

    if [ "$response" = "200" ]; then
        log_success "OpenAI API key is valid"
        return 0
    else
        log_error "OpenAI API key validation failed (HTTP $response)"
        return 1
    fi
}

test_anthropic_key() {
    local key="$1"
    log_info "Testing Anthropic API key..."

    local response=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "x-api-key: $key" \
        -H "anthropic-version: 2023-06-01" \
        "https://api.anthropic.com/v1/messages" \
        -d '{"model":"claude-3-haiku-20240307","max_tokens":1,"messages":[{"role":"user","content":"test"}]}')

    if [ "$response" = "200" ]; then
        log_success "Anthropic API key is valid"
        return 0
    else
        log_warning "Anthropic API key validation inconclusive (HTTP $response)"
        return 0  # Don't fail on this
    fi
}

test_database_connection() {
    local db_url="$1"
    log_info "Testing database connection..."

    if command -v psql >/dev/null 2>&1; then
        if psql "$db_url" -c "SELECT 1;" >/dev/null 2>&1; then
            log_success "Database connection successful"
            return 0
        else
            log_warning "Could not connect to database (may not be running yet)"
            return 0  # Don't fail setup
        fi
    else
        log_info "psql not found, skipping database connection test"
        return 0
    fi
}

test_redis_connection() {
    local redis_url="$1"
    log_info "Testing Redis connection..."

    if command -v redis-cli >/dev/null 2>&1; then
        # Extract host and port from URL
        local host=$(echo "$redis_url" | sed -n 's|redis://\([^:]*\):.*|\1|p')
        local port=$(echo "$redis_url" | sed -n 's|redis://[^:]*:\([0-9]*\).*|\1|p')

        if [ -n "$host" ] && [ -n "$port" ]; then
            if redis-cli -h "$host" -p "$port" ping >/dev/null 2>&1; then
                log_success "Redis connection successful"
                return 0
            else
                log_warning "Could not connect to Redis (may not be running yet)"
                return 0  # Don't fail setup
            fi
        fi
    else
        log_info "redis-cli not found, skipping Redis connection test"
        return 0
    fi
}

# =============================================================================
# Configuration Collection Functions
# =============================================================================

collect_deployment_config() {
    print_section "Deployment Configuration"

    log_info "Choose your deployment target:"
    echo "  1) Docker Compose (local/self-hosted)"
    echo "  2) Google Cloud Run (serverless)"
    read -p "  > " deploy_choice

    case $deploy_choice in
        1)
            CONFIG[DEPLOYMENT_TARGET]="docker-compose"
            CONFIG[NODE_ENV]="production"
            ;;
        2)
            CONFIG[DEPLOYMENT_TARGET]="cloud-run"
            CONFIG[NODE_ENV]="production"
            ;;
        *)
            log_error "Invalid choice"
            exit 1
            ;;
    esac

    log_success "Deployment target: ${CONFIG[DEPLOYMENT_TARGET]}"
}

collect_database_config() {
    print_section "Database Configuration"

    if prompt_confirm "Do you want to use Supabase? (Recommended for easy setup)" "n"; then
        prompt_input "Supabase URL (from https://app.supabase.com/project/_/settings/api):" \
            "SUPABASE_URL" ""
        prompt_input "Supabase Anon Key:" "SUPABASE_ANON_KEY" "" "true"
        prompt_input "Supabase Service Role Key:" "SUPABASE_SERVICE_ROLE_KEY" "" "true"

        # Extract database URL from Supabase
        local project_ref=$(echo "${CONFIG[SUPABASE_URL]}" | sed -n 's|https://\([^.]*\)\.supabase\.co|\1|p')
        prompt_input "Supabase Database Password:" "POSTGRES_PASSWORD" "" "true"
        CONFIG[DATABASE_URL]="postgresql://postgres:${CONFIG[POSTGRES_PASSWORD]}@db.${project_ref}.supabase.co:5432/postgres"

        log_success "Supabase configuration collected"
    else
        prompt_input "PostgreSQL Host:" "POSTGRES_HOST" "localhost"
        prompt_input "PostgreSQL Port:" "POSTGRES_PORT" "5432"
        prompt_input "PostgreSQL Database Name:" "POSTGRES_DB" "geminivideo"
        prompt_input "PostgreSQL Username:" "POSTGRES_USER" "geminivideo"
        prompt_input "PostgreSQL Password:" "POSTGRES_PASSWORD" "" "true"

        CONFIG[DATABASE_URL]="postgresql://${CONFIG[POSTGRES_USER]}:${CONFIG[POSTGRES_PASSWORD]}@${CONFIG[POSTGRES_HOST]}:${CONFIG[POSTGRES_PORT]}/${CONFIG[POSTGRES_DB]}"

        log_success "PostgreSQL configuration collected"
    fi

    validate_postgres_url "${CONFIG[DATABASE_URL]}" || exit 1
    test_database_connection "${CONFIG[DATABASE_URL]}"
}

collect_redis_config() {
    print_section "Redis Configuration"

    if prompt_confirm "Do you want to use Upstash Redis? (Recommended for serverless)" "y"; then
        prompt_input "Upstash Redis REST URL (from https://console.upstash.com/):" \
            "UPSTASH_REDIS_REST_URL" ""
        prompt_input "Upstash Redis REST Token:" "UPSTASH_REDIS_REST_TOKEN" "" "true"

        validate_url "${CONFIG[UPSTASH_REDIS_REST_URL]}" "Upstash Redis URL" || exit 1
        log_success "Upstash Redis configuration collected"
    else
        prompt_input "Redis URL:" "REDIS_URL" "redis://localhost:6379"
        validate_redis_url "${CONFIG[REDIS_URL]}" || exit 1
        test_redis_connection "${CONFIG[REDIS_URL]}"
    fi
}

collect_ai_keys() {
    print_section "AI API Keys"

    log_info "Google Gemini API Key is REQUIRED"
    prompt_input "Gemini API Key (from https://aistudio.google.com/app/apikey):" \
        "GEMINI_API_KEY" "" "true"
    validate_not_empty "${CONFIG[GEMINI_API_KEY]}" "Gemini API Key" || exit 1
    test_gemini_key "${CONFIG[GEMINI_API_KEY]}"

    if prompt_confirm "Do you want to add OpenAI API key? (Recommended)" "y"; then
        prompt_input "OpenAI API Key (from https://platform.openai.com/api-keys):" \
            "OPENAI_API_KEY" "" "true"
        if [ -n "${CONFIG[OPENAI_API_KEY]}" ]; then
            test_openai_key "${CONFIG[OPENAI_API_KEY]}"
        fi
    fi

    if prompt_confirm "Do you want to add Anthropic API key? (Recommended)" "y"; then
        prompt_input "Anthropic API Key (from https://console.anthropic.com/):" \
            "ANTHROPIC_API_KEY" "" "true"
        if [ -n "${CONFIG[ANTHROPIC_API_KEY]}" ]; then
            test_anthropic_key "${CONFIG[ANTHROPIC_API_KEY]}"
        fi
    fi
}

collect_gcp_config() {
    print_section "Google Cloud Platform"

    if [ "${CONFIG[DEPLOYMENT_TARGET]}" = "cloud-run" ]; then
        log_info "GCP configuration is REQUIRED for Cloud Run deployment"
        prompt_input "GCP Project ID:" "GCP_PROJECT_ID" ""
        validate_not_empty "${CONFIG[GCP_PROJECT_ID]}" "GCP Project ID" || exit 1

        prompt_input "GCP Region:" "GCP_REGION" "us-central1"
        prompt_input "GCS Bucket Name (will be created if doesn't exist):" "GCS_BUCKET_NAME" ""
        validate_not_empty "${CONFIG[GCS_BUCKET_NAME]}" "GCS Bucket Name" || exit 1

        prompt_input "Service Account Email:" "CLOUD_RUN_SERVICE_ACCOUNT" \
            "geminivideo-sa@${CONFIG[GCP_PROJECT_ID]}.iam.gserviceaccount.com"

        CONFIG[CLOUD_RUN_REGION]="${CONFIG[GCP_REGION]}"
        CONFIG[GCS_PROJECT_ID]="${CONFIG[GCP_PROJECT_ID]}"
        CONFIG[REGISTRY_URL]="${CONFIG[GCP_REGION]}-docker.pkg.dev/${CONFIG[GCP_PROJECT_ID]}/geminivideo"

        log_success "GCP configuration collected"
    else
        if prompt_confirm "Do you want to configure GCP for Google Cloud Storage?" "n"; then
            prompt_input "GCP Project ID:" "GCP_PROJECT_ID" ""
            prompt_input "GCS Bucket Name:" "GCS_BUCKET_NAME" ""
            prompt_input "Path to service account JSON:" "GOOGLE_APPLICATION_CREDENTIALS" ""
        fi
    fi
}

collect_meta_config() {
    print_section "Meta/Facebook Ads (Optional)"

    if prompt_confirm "Do you want to configure Meta Ads publishing?" "y"; then
        log_info "You'll need a Meta App from https://developers.facebook.com/apps/"

        prompt_input "Meta App ID:" "META_APP_ID" ""
        prompt_input "Meta App Secret:" "META_APP_SECRET" "" "true"
        prompt_input "Meta Access Token (long-lived):" "META_ACCESS_TOKEN" "" "true"
        prompt_input "Meta Ad Account ID (format: act_1234567890):" "META_AD_ACCOUNT_ID" ""
        prompt_input "Meta Page ID:" "META_PAGE_ID" ""

        log_success "Meta configuration collected"
    else
        log_info "Skipping Meta configuration"
    fi
}

collect_firebase_config() {
    print_section "Firebase (Frontend Authentication)"

    if prompt_confirm "Do you want to configure Firebase authentication?" "y"; then
        log_info "Get these from https://console.firebase.google.com/project/_/settings/general"

        prompt_input "Firebase API Key:" "VITE_FIREBASE_API_KEY" ""
        prompt_input "Firebase Auth Domain:" "VITE_FIREBASE_AUTH_DOMAIN" ""
        prompt_input "Firebase Project ID:" "VITE_FIREBASE_PROJECT_ID" ""
        prompt_input "Firebase Storage Bucket:" "VITE_FIREBASE_STORAGE_BUCKET" ""
        prompt_input "Firebase Messaging Sender ID:" "VITE_FIREBASE_MESSAGING_SENDER_ID" ""
        prompt_input "Firebase App ID:" "VITE_FIREBASE_APP_ID" ""
        prompt_input "Firebase Measurement ID (optional):" "VITE_FIREBASE_MEASUREMENT_ID" ""

        log_success "Firebase configuration collected"
    else
        log_info "Skipping Firebase configuration"
    fi
}

collect_security_config() {
    print_section "Security Configuration"

    log_info "Generating secure JWT secret..."
    CONFIG[JWT_SECRET]=$(openssl rand -base64 64 | tr -d '\n')
    log_success "JWT secret generated"

    prompt_input "CORS Allowed Origins (comma-separated):" \
        "CORS_ORIGINS" "http://localhost:3000,http://localhost:5173"

    if [ "${CONFIG[DEPLOYMENT_TARGET]}" = "cloud-run" ]; then
        prompt_input "Your production frontend domain:" "FRONTEND_DOMAIN" ""
        if [ -n "${CONFIG[FRONTEND_DOMAIN]}" ]; then
            CONFIG[CORS_ORIGINS]="https://${CONFIG[FRONTEND_DOMAIN]},https://www.${CONFIG[FRONTEND_DOMAIN]}"
        fi
    fi
}

# =============================================================================
# File Generation Functions
# =============================================================================

generate_master_env() {
    local output_file="$1"

    log_info "Generating master .env.production file..."

    # Start with the template
    cp "$TEMPLATE_FILE" "$output_file"

    # Replace values
    for key in "${!CONFIG[@]}"; do
        local value="${CONFIG[$key]}"
        # Escape special characters for sed
        value=$(echo "$value" | sed 's/[\/&]/\\&/g')

        # Replace in file (handle both formats: KEY=value and KEY=placeholder)
        sed -i "s|^${key}=.*|${key}=${value}|g" "$output_file"
    done

    log_success "Master .env.production created"
}

generate_service_envs() {
    print_section "Generating Service-Specific .env Files"

    # Gateway API
    if [ -d "$PROJECT_ROOT/services/gateway-api" ]; then
        cat > "$PROJECT_ROOT/services/gateway-api/.env" <<EOF
DATABASE_URL=${CONFIG[DATABASE_URL]}
REDIS_URL=${CONFIG[REDIS_URL]:-redis://localhost:6379}
NODE_ENV=${CONFIG[NODE_ENV]}
PORT=${CONFIG[GATEWAY_PORT]:-8080}
JWT_SECRET=${CONFIG[JWT_SECRET]}
GCS_BUCKET=${CONFIG[GCS_BUCKET_NAME]:-}
GCS_PROJECT_ID=${CONFIG[GCP_PROJECT_ID]:-}
META_APP_ID=${CONFIG[META_APP_ID]:-}
META_APP_SECRET=${CONFIG[META_APP_SECRET]:-}
META_ACCESS_TOKEN=${CONFIG[META_ACCESS_TOKEN]:-}
ML_SERVICE_URL=${CONFIG[ML_SERVICE_URL]:-http://ml-service:8003}
LOG_LEVEL=info
EOF
        log_success "Gateway API .env created"
    fi

    # Titan-Core API
    if [ -d "$PROJECT_ROOT/services/titan-core/api" ]; then
        cat > "$PROJECT_ROOT/services/titan-core/api/.env" <<EOF
GEMINI_API_KEY=${CONFIG[GEMINI_API_KEY]}
OPENAI_API_KEY=${CONFIG[OPENAI_API_KEY]:-}
ANTHROPIC_API_KEY=${CONFIG[ANTHROPIC_API_KEY]:-}
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
OUTPUT_DIR=/tmp/titan-core/outputs
CACHE_DIR=/tmp/titan-core/cache
MAX_CONCURRENT_RENDERS=5
DEFAULT_NUM_VARIATIONS=10
APPROVAL_THRESHOLD=85.0
CORS_ORIGINS=${CONFIG[CORS_ORIGINS]}
EOF
        log_success "Titan-Core API .env created"
    fi

    # Frontend
    if [ -d "$PROJECT_ROOT/frontend" ]; then
        cat > "$PROJECT_ROOT/frontend/.env" <<EOF
VITE_FIREBASE_API_KEY=${CONFIG[VITE_FIREBASE_API_KEY]:-}
VITE_FIREBASE_AUTH_DOMAIN=${CONFIG[VITE_FIREBASE_AUTH_DOMAIN]:-}
VITE_FIREBASE_PROJECT_ID=${CONFIG[VITE_FIREBASE_PROJECT_ID]:-}
VITE_FIREBASE_STORAGE_BUCKET=${CONFIG[VITE_FIREBASE_STORAGE_BUCKET]:-}
VITE_FIREBASE_MESSAGING_SENDER_ID=${CONFIG[VITE_FIREBASE_MESSAGING_SENDER_ID]:-}
VITE_FIREBASE_APP_ID=${CONFIG[VITE_FIREBASE_APP_ID]:-}
VITE_FIREBASE_MEASUREMENT_ID=${CONFIG[VITE_FIREBASE_MEASUREMENT_ID]:-}
VITE_API_URL=${CONFIG[GATEWAY_URL]:-http://localhost:8080}
VITE_ENV=${CONFIG[NODE_ENV]}
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_PERFORMANCE=true
VITE_META_PIXEL_ID=${CONFIG[VITE_META_PIXEL_ID]:-}
EOF
        log_success "Frontend .env created"
    fi

    # Copy to other service directories as needed
    for service in drive-intel video-agent ml-service meta-publisher; do
        if [ -d "$PROJECT_ROOT/services/$service" ]; then
            cp "$OUTPUT_FILE" "$PROJECT_ROOT/services/$service/.env"
            log_success "$service .env created"
        fi
    done
}

# =============================================================================
# Summary and Validation
# =============================================================================

print_summary() {
    print_section "Configuration Summary"

    echo -e "${BOLD}Deployment Configuration:${NC}"
    echo "  Target: ${CONFIG[DEPLOYMENT_TARGET]}"
    echo "  Environment: ${CONFIG[NODE_ENV]}"
    echo ""

    echo -e "${BOLD}Database:${NC}"
    if [ -n "${CONFIG[SUPABASE_URL]}" ]; then
        echo "  Type: Supabase"
        echo "  URL: ${CONFIG[SUPABASE_URL]}"
    else
        echo "  Type: PostgreSQL"
        echo "  Host: ${CONFIG[POSTGRES_HOST]}"
        echo "  Database: ${CONFIG[POSTGRES_DB]}"
    fi
    echo ""

    echo -e "${BOLD}Cache:${NC}"
    if [ -n "${CONFIG[UPSTASH_REDIS_REST_URL]}" ]; then
        echo "  Type: Upstash Redis"
        echo "  URL: ${CONFIG[UPSTASH_REDIS_REST_URL]}"
    else
        echo "  Type: Redis"
        echo "  URL: ${CONFIG[REDIS_URL]}"
    fi
    echo ""

    echo -e "${BOLD}AI APIs:${NC}"
    echo "  Gemini: $([ -n "${CONFIG[GEMINI_API_KEY]}" ] && echo "✓ Configured" || echo "✗ Not configured")"
    echo "  OpenAI: $([ -n "${CONFIG[OPENAI_API_KEY]}" ] && echo "✓ Configured" || echo "✗ Not configured")"
    echo "  Anthropic: $([ -n "${CONFIG[ANTHROPIC_API_KEY]}" ] && echo "✓ Configured" || echo "✗ Not configured")"
    echo ""

    if [ "${CONFIG[DEPLOYMENT_TARGET]}" = "cloud-run" ]; then
        echo -e "${BOLD}Google Cloud Platform:${NC}"
        echo "  Project: ${CONFIG[GCP_PROJECT_ID]}"
        echo "  Region: ${CONFIG[GCP_REGION]}"
        echo "  Bucket: ${CONFIG[GCS_BUCKET_NAME]}"
        echo ""
    fi

    echo -e "${BOLD}Meta Ads:${NC}"
    echo "  Configured: $([ -n "${CONFIG[META_APP_ID]}" ] && echo "Yes" || echo "No")"
    echo ""

    echo -e "${BOLD}Firebase:${NC}"
    echo "  Configured: $([ -n "${CONFIG[VITE_FIREBASE_PROJECT_ID]}" ] && echo "Yes" || echo "No")"
    echo ""

    echo -e "${BOLD}Generated Files:${NC}"
    echo "  Master: .env.production"
    echo "  Services: gateway-api, titan-core, frontend, and more"
    echo ""
}

print_next_steps() {
    print_section "Next Steps"

    echo -e "${BOLD}1. Review Configuration${NC}"
    echo "   cat $OUTPUT_FILE"
    echo ""

    echo -e "${BOLD}2. Test Connections${NC}"
    echo "   bash scripts/test-connections.sh"
    echo ""

    if [ "${CONFIG[DEPLOYMENT_TARGET]}" = "cloud-run" ]; then
        echo -e "${BOLD}3. Set Up GCP (if not done)${NC}"
        echo "   gcloud auth login"
        echo "   gcloud config set project ${CONFIG[GCP_PROJECT_ID]}"
        echo "   gcloud services enable run.googleapis.com"
        echo "   gcloud services enable artifactregistry.googleapis.com"
        echo "   gsutil mb gs://${CONFIG[GCS_BUCKET_NAME]}"
        echo ""

        echo -e "${BOLD}4. Deploy to Cloud Run${NC}"
        echo "   bash scripts/deploy-production.sh"
        echo ""
    else
        echo -e "${BOLD}3. Start Services${NC}"
        echo "   docker-compose -f docker-compose.production.yml up -d"
        echo ""

        echo -e "${BOLD}4. Initialize Database${NC}"
        echo "   python scripts/init_db.py"
        echo ""
    fi

    echo -e "${BOLD}5. Access Services${NC}"
    if [ "${CONFIG[DEPLOYMENT_TARGET]}" = "docker-compose" ]; then
        echo "   Frontend: http://localhost:3000"
        echo "   Gateway API: http://localhost:8080"
        echo "   Titan-Core: http://localhost:8084"
    else
        echo "   URLs will be displayed after deployment"
    fi
    echo ""

    echo -e "${YELLOW}For detailed documentation, see:${NC}"
    echo "  docs/DEPLOYMENT.md"
    echo "  docs/CONFIGURATION.md"
    echo ""
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    print_header

    # Check if template exists
    if [ ! -f "$TEMPLATE_FILE" ]; then
        log_error "Template file not found: $TEMPLATE_FILE"
        log_info "Please ensure .env.deployment exists in project root"
        exit 1
    fi

    # Check for required tools
    if ! command -v openssl >/dev/null 2>&1; then
        log_error "openssl is required but not installed"
        exit 1
    fi

    # Warning if output file exists
    if [ -f "$OUTPUT_FILE" ]; then
        log_warning "Output file already exists: $OUTPUT_FILE"
        if ! prompt_confirm "Do you want to overwrite it?" "n"; then
            log_info "Exiting without changes"
            exit 0
        fi
        # Backup existing file
        cp "$OUTPUT_FILE" "${OUTPUT_FILE}.backup.$(date +%Y%m%d-%H%M%S)"
        log_success "Existing file backed up"
    fi

    # Collect all configurations
    collect_deployment_config
    collect_database_config
    collect_redis_config
    collect_ai_keys
    collect_gcp_config
    collect_meta_config
    collect_firebase_config
    collect_security_config

    # Generate files
    print_section "Generating Configuration Files"
    generate_master_env "$OUTPUT_FILE"
    generate_service_envs

    # Show summary
    print_summary

    # Validate critical configurations
    print_section "Validation"
    local validation_passed=true

    if ! validate_not_empty "${CONFIG[GEMINI_API_KEY]}" "Gemini API Key"; then
        validation_passed=false
    fi

    if ! validate_postgres_url "${CONFIG[DATABASE_URL]}"; then
        validation_passed=false
    fi

    if [ "$validation_passed" = true ]; then
        log_success "All critical validations passed"
    else
        log_error "Some validations failed. Please review the configuration."
        exit 1
    fi

    # Final confirmation
    echo ""
    if prompt_confirm "Configuration complete. Deploy now?" "n"; then
        log_info "Starting deployment..."
        bash "$SCRIPT_DIR/deploy-production.sh"
    else
        print_next_steps
    fi

    log_success "Setup complete!"
}

# Run main function
main "$@"
