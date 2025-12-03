#!/bin/bash
# =============================================================================
# Environment Variables Validation Script
# =============================================================================
# This script validates that all required environment variables are set
# and have valid values (not placeholders)
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${1:-.env.production}"

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# =============================================================================
# Helper Functions
# =============================================================================

log_check() {
    local name="$1"
    local value="$2"
    local required="${3:-true}"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    # Check if empty
    if [ -z "$value" ]; then
        if [ "$required" = "true" ]; then
            echo -e "${RED}✗${NC} $name: ${RED}MISSING (Required)${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            return 1
        else
            echo -e "${YELLOW}⚠${NC} $name: ${YELLOW}Not set (Optional)${NC}"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
            return 0
        fi
    fi

    # Check if placeholder
    if [[ "$value" =~ ^(your-|YOUR_|your_|xxxx|XXXX|placeholder) ]]; then
        if [ "$required" = "true" ]; then
            echo -e "${RED}✗${NC} $name: ${RED}Placeholder value detected${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            return 1
        else
            echo -e "${YELLOW}⚠${NC} $name: ${YELLOW}Placeholder value (Optional)${NC}"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
            return 0
        fi
    fi

    # Looks good
    echo -e "${GREEN}✓${NC} $name: Set"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    return 0
}

log_url_check() {
    local name="$1"
    local value="$2"
    local required="${3:-true}"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [ -z "$value" ]; then
        if [ "$required" = "true" ]; then
            echo -e "${RED}✗${NC} $name: ${RED}MISSING${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            return 1
        else
            echo -e "${YELLOW}⚠${NC} $name: ${YELLOW}Not set (Optional)${NC}"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
            return 0
        fi
    fi

    if [[ ! "$value" =~ ^(https?|postgresql|redis)://  ]]; then
        echo -e "${RED}✗${NC} $name: ${RED}Invalid URL format${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi

    echo -e "${GREEN}✓${NC} $name: Valid URL"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    return 0
}

# =============================================================================
# Load Environment Variables
# =============================================================================

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}  ${BOLD}Environment Variables Validation${NC}                                ${CYAN}║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"

if [ ! -f "$PROJECT_ROOT/$ENV_FILE" ]; then
    echo -e "${RED}✗ Environment file not found: $ENV_FILE${NC}"
    echo -e "${YELLOW}Run 'bash scripts/setup-env.sh' to create it${NC}"
    exit 1
fi

echo -e "${BLUE}Loading: $ENV_FILE${NC}\n"

# Load environment variables
set -a
source "$PROJECT_ROOT/$ENV_FILE"
set +a

# =============================================================================
# Validation Checks
# =============================================================================

echo -e "\n${BOLD}━━━ Database Configuration ━━━${NC}\n"
log_url_check "DATABASE_URL" "$DATABASE_URL" true
log_check "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD" true

if [ -n "$SUPABASE_URL" ]; then
    echo -e "\n${CYAN}Using Supabase:${NC}"
    log_url_check "SUPABASE_URL" "$SUPABASE_URL" false
    log_check "SUPABASE_ANON_KEY" "$SUPABASE_ANON_KEY" false
    log_check "SUPABASE_SERVICE_ROLE_KEY" "$SUPABASE_SERVICE_ROLE_KEY" false
fi

echo -e "\n${BOLD}━━━ Cache Configuration ━━━${NC}\n"
if [ -n "$UPSTASH_REDIS_REST_URL" ]; then
    echo -e "${CYAN}Using Upstash Redis:${NC}"
    log_url_check "UPSTASH_REDIS_REST_URL" "$UPSTASH_REDIS_REST_URL" false
    log_check "UPSTASH_REDIS_REST_TOKEN" "$UPSTASH_REDIS_REST_TOKEN" false
else
    log_url_check "REDIS_URL" "$REDIS_URL" true
fi

echo -e "\n${BOLD}━━━ AI API Keys ━━━${NC}\n"
log_check "GEMINI_API_KEY" "$GEMINI_API_KEY" true
log_check "OPENAI_API_KEY" "$OPENAI_API_KEY" false
log_check "ANTHROPIC_API_KEY" "$ANTHROPIC_API_KEY" false

echo -e "\n${BOLD}━━━ Google Cloud Platform ━━━${NC}\n"
if [ "$DEPLOYMENT_TARGET" = "cloud-run" ]; then
    log_check "GCP_PROJECT_ID" "$GCP_PROJECT_ID" true
    log_check "GCP_REGION" "$GCP_REGION" true
    log_check "GCS_BUCKET_NAME" "$GCS_BUCKET_NAME" true
    log_check "CLOUD_RUN_SERVICE_ACCOUNT" "$CLOUD_RUN_SERVICE_ACCOUNT" true
else
    log_check "GCP_PROJECT_ID" "$GCP_PROJECT_ID" false
    log_check "GCS_BUCKET_NAME" "$GCS_BUCKET_NAME" false
fi

echo -e "\n${BOLD}━━━ Security Configuration ━━━${NC}\n"
log_check "JWT_SECRET" "$JWT_SECRET" true
log_check "CORS_ORIGINS" "$CORS_ORIGINS" true

# Check JWT secret strength
if [ -n "$JWT_SECRET" ] && [ ${#JWT_SECRET} -lt 32 ]; then
    echo -e "${YELLOW}⚠${NC} JWT_SECRET is shorter than recommended (32+ characters)"
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
fi

echo -e "\n${BOLD}━━━ Meta/Facebook Ads (Optional) ━━━${NC}\n"
log_check "META_APP_ID" "$META_APP_ID" false
log_check "META_APP_SECRET" "$META_APP_SECRET" false
log_check "META_ACCESS_TOKEN" "$META_ACCESS_TOKEN" false
log_check "META_AD_ACCOUNT_ID" "$META_AD_ACCOUNT_ID" false

echo -e "\n${BOLD}━━━ Firebase Authentication (Optional) ━━━${NC}\n"
log_check "VITE_FIREBASE_PROJECT_ID" "$VITE_FIREBASE_PROJECT_ID" false
log_check "VITE_FIREBASE_API_KEY" "$VITE_FIREBASE_API_KEY" false
log_check "VITE_FIREBASE_AUTH_DOMAIN" "$VITE_FIREBASE_AUTH_DOMAIN" false

# =============================================================================
# Summary
# =============================================================================

echo -e "\n${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
echo -e "${BOLD}Validation Summary:${NC}"
echo -e "  Total checks: $TOTAL_CHECKS"
echo -e "  ${GREEN}✓ Passed: $PASSED_CHECKS${NC}"
echo -e "  ${YELLOW}⚠ Warnings: $WARNING_CHECKS${NC}"
echo -e "  ${RED}✗ Failed: $FAILED_CHECKS${NC}"
echo ""

if [ $FAILED_CHECKS -gt 0 ]; then
    echo -e "${RED}✗ Validation FAILED${NC}"
    echo -e "${YELLOW}Please fix the errors above before deploying${NC}"
    echo -e "${CYAN}Run 'bash scripts/setup-env.sh' to reconfigure${NC}"
    exit 1
elif [ $WARNING_CHECKS -gt 0 ]; then
    echo -e "${YELLOW}⚠ Validation passed with warnings${NC}"
    echo -e "${CYAN}Optional services may not be available${NC}"
    exit 0
else
    echo -e "${GREEN}✓ All validations passed!${NC}"
    echo -e "${CYAN}Ready to deploy${NC}"
    exit 0
fi
