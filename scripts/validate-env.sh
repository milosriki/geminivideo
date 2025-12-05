#!/bin/bash
# =============================================================================
# Environment Variables Validation Script - Enhanced Version
# =============================================================================
# This script validates that all required environment variables are set
# and have valid values. It uses the comprehensive Python validator.
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
SKIP_CONNECTIVITY="${SKIP_CONNECTIVITY:-false}"

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  ${BOLD}Environment Variables Validation${NC}                                ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════╝${NC}\n"
}

check_python() {
    if command -v python3 &> /dev/null; then
        echo "python3"
        return 0
    elif command -v python &> /dev/null; then
        echo "python"
        return 0
    else
        return 1
    fi
}

install_dependencies() {
    local python_cmd="$1"

    echo -e "${YELLOW}Installing required Python packages...${NC}"

    # Try to install required packages
    $python_cmd -m pip install --quiet psycopg2-binary redis boto3 google-generativeai openai anthropic 2>/dev/null || {
        echo -e "${YELLOW}⚠ Warning: Could not install some packages. Connectivity tests may be skipped.${NC}"
    }
}

# =============================================================================
# Main Execution
# =============================================================================

print_header

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/$ENV_FILE" ]; then
    echo -e "${RED}✗ Environment file not found: $ENV_FILE${NC}"
    echo -e "${YELLOW}Available .env files:${NC}"
    find "$PROJECT_ROOT" -maxdepth 1 -name ".env*" -type f | sed 's/^/  - /'
    echo ""
    echo -e "${CYAN}Run 'bash scripts/setup-env.sh' to create environment configuration${NC}"
    exit 1
fi

echo -e "${BLUE}Loading: $ENV_FILE${NC}\n"

# Check if Python is available
PYTHON_CMD=$(check_python) || {
    echo -e "${RED}✗ Python not found${NC}"
    echo -e "${YELLOW}Please install Python 3.7+ to use the comprehensive validator${NC}"
    echo -e "${CYAN}Falling back to basic validation...${NC}\n"

    # Basic validation fallback
    source "$PROJECT_ROOT/$ENV_FILE"

    FAILED=0

    # Check critical variables
    [ -z "$DATABASE_URL" ] && { echo -e "${RED}✗ DATABASE_URL not set${NC}"; FAILED=1; } || echo -e "${GREEN}✓ DATABASE_URL set${NC}"
    [ -z "$GEMINI_API_KEY" ] && { echo -e "${RED}✗ GEMINI_API_KEY not set${NC}"; FAILED=1; } || echo -e "${GREEN}✓ GEMINI_API_KEY set${NC}"
    [ -z "$JWT_SECRET" ] && { echo -e "${RED}✗ JWT_SECRET not set${NC}"; FAILED=1; } || echo -e "${GREEN}✓ JWT_SECRET set${NC}"

    echo ""
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ Basic validation passed${NC}"
        echo -e "${YELLOW}⚠ Install Python for comprehensive validation${NC}"
        exit 0
    else
        echo -e "${RED}✗ Validation failed${NC}"
        exit 1
    fi
}

# Check if validate-env.py exists
VALIDATOR_SCRIPT="$SCRIPT_DIR/validate-env.py"
if [ ! -f "$VALIDATOR_SCRIPT" ]; then
    echo -e "${RED}✗ Validator script not found: $VALIDATOR_SCRIPT${NC}"
    echo -e "${YELLOW}Expected location: $VALIDATOR_SCRIPT${NC}"
    exit 1
fi

# Make it executable
chmod +x "$VALIDATOR_SCRIPT"

# Check for required packages (optional, for connectivity tests)
echo -e "${CYAN}Checking Python environment...${NC}"

# Check if we should skip connectivity tests
SKIP_FLAG=""
if [ "$SKIP_CONNECTIVITY" = "true" ]; then
    SKIP_FLAG="--skip-connectivity"
    echo -e "${YELLOW}⚠ Skipping connectivity tests (SKIP_CONNECTIVITY=true)${NC}\n"
else
    # Try to import required packages
    $PYTHON_CMD -c "import psycopg2" 2>/dev/null || {
        echo -e "${YELLOW}⚠ psycopg2 not installed - database connectivity tests will be skipped${NC}"
        echo -e "${CYAN}Install with: pip install psycopg2-binary${NC}"
    }

    $PYTHON_CMD -c "import redis" 2>/dev/null || {
        echo -e "${YELLOW}⚠ redis-py not installed - Redis connectivity tests will be skipped${NC}"
        echo -e "${CYAN}Install with: pip install redis${NC}"
    }

    echo ""
fi

# Run Python validator
echo -e "${BOLD}Running comprehensive validation...${NC}\n"

if [ -n "$CI" ] || [ "$OUTPUT_JSON" = "true" ]; then
    # CI/CD mode - output JSON
    $PYTHON_CMD "$VALIDATOR_SCRIPT" --env-file "$PROJECT_ROOT/$ENV_FILE" $SKIP_FLAG --json
else
    # Interactive mode - human-readable output
    $PYTHON_CMD "$VALIDATOR_SCRIPT" --env-file "$PROJECT_ROOT/$ENV_FILE" $SKIP_FLAG
fi

EXIT_CODE=$?

# Additional post-validation checks
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Environment validation successful!${NC}"
    echo -e "${CYAN}Ready for deployment${NC}\n"

    # Show next steps
    echo -e "${BOLD}Next steps:${NC}"
    echo -e "  1. Review configuration: ${BLUE}$ENV_FILE${NC}"
    echo -e "  2. Test locally: ${BLUE}docker-compose up${NC}"
    echo -e "  3. Deploy: ${BLUE}bash scripts/deploy-production.sh${NC}"
    echo ""
else
    echo -e "${RED}✗ Environment validation failed${NC}"
    echo -e "${YELLOW}Please fix the issues above before deploying${NC}\n"

    # Show helpful commands
    echo -e "${BOLD}Helpful commands:${NC}"
    echo -e "  • Edit config: ${BLUE}nano $ENV_FILE${NC}"
    echo -e "  • Run setup: ${BLUE}bash scripts/setup-env.sh${NC}"
    echo -e "  • Check again: ${BLUE}bash scripts/validate-env.sh $ENV_FILE${NC}"
    echo ""
fi

exit $EXIT_CODE
