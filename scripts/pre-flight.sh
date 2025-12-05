#!/bin/bash
# =============================================================================
# AGENT 60: PRE-FLIGHT CHECK
# Final validation before €5M investor demo
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CHECKLIST_SCRIPT="$SCRIPT_DIR/final-checklist.py"
REPORT_DIR="$PROJECT_ROOT/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JSON_REPORT="$REPORT_DIR/pre-flight-$TIMESTAMP.json"
TEXT_REPORT="$REPORT_DIR/pre-flight-$TIMESTAMP.txt"

# =============================================================================
# Functions
# =============================================================================

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    GEMINI VIDEO PRE-FLIGHT CHECK                           ║"
    echo "║                 Final Validation for €5M Investor Demo                     ║"
    echo "╚════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    local title=$1
    echo -e "\n${BLUE}${BOLD}▶ $title${NC}"
    echo -e "${DIM}$(printf '─%.0s' {1..80})${NC}"
}

check_dependencies() {
    print_section "Checking Dependencies"

    local missing_deps=()

    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ Python 3 not found${NC}"
        missing_deps+=("python3")
    else
        local python_version=$(python3 --version 2>&1 | awk '{print $2}')
        echo -e "${GREEN}✓ Python 3 installed${NC} (v$python_version)"
    fi

    # Check required Python packages
    if ! python3 -c "import httpx" 2>/dev/null; then
        echo -e "${YELLOW}⚠ httpx not installed${NC}"
        missing_deps+=("python3-httpx")
    fi

    if ! python3 -c "import psycopg2" 2>/dev/null; then
        echo -e "${YELLOW}⚠ psycopg2 not installed${NC}"
        missing_deps+=("python3-psycopg2")
    fi

    if ! python3 -c "import redis" 2>/dev/null; then
        echo -e "${YELLOW}⚠ redis not installed${NC}"
        missing_deps+=("python3-redis")
    fi

    # Check Docker (optional)
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}✓ Docker installed${NC}"
    else
        echo -e "${DIM}  Docker not found (optional)${NC}"
    fi

    # Check docker-compose (optional)
    if command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}✓ docker-compose installed${NC}"
    else
        echo -e "${DIM}  docker-compose not found (optional)${NC}"
    fi

    # If missing deps, offer to install
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo -e "\n${YELLOW}Missing dependencies: ${missing_deps[*]}${NC}"
        echo -e "${YELLOW}Installing...${NC}\n"
        pip3 install httpx psycopg2-binary redis --quiet
    fi
}

check_services_running() {
    print_section "Checking Services Status"

    local services=(
        "postgres:5432"
        "redis:6379"
        "gateway-api:8080"
        "frontend:3000"
    )

    local all_running=true

    for service in "${services[@]}"; do
        local name=${service%:*}
        local port=${service#*:}

        if nc -z localhost $port 2>/dev/null || curl -s http://localhost:$port/health &>/dev/null; then
            echo -e "${GREEN}✓ $name running on port $port${NC}"
        else
            echo -e "${RED}✗ $name not responding on port $port${NC}"
            all_running=false
        fi
    done

    if [ "$all_running" = false ]; then
        echo -e "\n${YELLOW}Some services are not running.${NC}"
        echo -e "${YELLOW}Start services with: docker-compose up -d${NC}\n"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}Pre-flight check aborted.${NC}"
            exit 1
        fi
    fi
}

run_checklist() {
    print_section "Running Comprehensive Validation"

    # Create reports directory
    mkdir -p "$REPORT_DIR"

    echo -e "${CYAN}Executing: $CHECKLIST_SCRIPT${NC}\n"

    # Run the Python checklist script
    if python3 "$CHECKLIST_SCRIPT" --json 2>&1 | tee "$TEXT_REPORT"; then
        local exit_code=${PIPESTATUS[0]}

        # Move JSON report if it exists
        if [ -f "checklist-report.json" ]; then
            mv checklist-report.json "$JSON_REPORT"
        fi

        return $exit_code
    else
        local exit_code=${PIPESTATUS[0]}
        return $exit_code
    fi
}

generate_pdf_report() {
    print_section "Generating PDF Report"

    # Check if we can generate PDF
    if command -v pandoc &> /dev/null && command -v wkhtmltopdf &> /dev/null; then
        local pdf_report="$REPORT_DIR/pre-flight-$TIMESTAMP.pdf"

        echo -e "${CYAN}Converting to PDF...${NC}"

        # Create markdown report
        local md_report="$REPORT_DIR/pre-flight-$TIMESTAMP.md"
        cat > "$md_report" <<EOF
# Gemini Video - Pre-Flight Check Report

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Project:** Gemini Video - AI Video Marketing Platform
**Purpose:** Final validation for €5M investor demo

---

$(cat "$TEXT_REPORT")

---

## Next Steps

### If GO:
1. ✓ Proceed with investor demo
2. ✓ All systems operational
3. ✓ Backup plan not needed

### If NO-GO:
1. ✗ Fix critical issues listed above
2. ✗ Re-run pre-flight check
3. ✗ Do not proceed with demo

---

*Report generated by Agent 60: Final Deployment Checklist*
EOF

        # Convert to PDF
        if pandoc "$md_report" -o "$pdf_report" --pdf-engine=wkhtmltopdf 2>/dev/null; then
            echo -e "${GREEN}✓ PDF report saved to: $pdf_report${NC}"
        else
            echo -e "${YELLOW}⚠ Could not generate PDF (pandoc/wkhtmltopdf required)${NC}"
        fi
    else
        echo -e "${DIM}PDF generation skipped (pandoc/wkhtmltopdf not installed)${NC}"
    fi
}

print_go_nogo_decision() {
    local exit_code=$1

    echo -e "\n${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════════════════════════════════════════╗"
    echo "║                         FINAL GO / NO-GO DECISION                          ║"
    echo "╚════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}${BOLD}"
        cat <<EOF
    ██████╗  ██████╗     ███████╗ ██████╗ ██████╗     ██╗      █████╗ ██╗   ██╗███╗   ██╗ ██████╗██╗  ██╗
   ██╔════╝ ██╔═══██╗    ██╔════╝██╔═══██╗██╔══██╗    ██║     ██╔══██╗██║   ██║████╗  ██║██╔════╝██║  ██║
   ██║  ███╗██║   ██║    █████╗  ██║   ██║██████╔╝    ██║     ███████║██║   ██║██╔██╗ ██║██║     ███████║
   ██║   ██║██║   ██║    ██╔══╝  ██║   ██║██╔══██╗    ██║     ██╔══██║██║   ██║██║╚██╗██║██║     ██╔══██║
   ╚██████╔╝╚██████╔╝    ██║     ╚██████╔╝██║  ██║    ███████╗██║  ██║╚██████╔╝██║ ╚████║╚██████╗██║  ██║
    ╚═════╝  ╚═════╝     ╚═╝      ╚═════╝ ╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝

EOF
        echo -e "${NC}"
        echo -e "${GREEN}✓✓✓ ALL SYSTEMS GO ✓✓✓${NC}"
        echo -e "${GREEN}Platform is ready for €5M investor demo.${NC}"
        echo -e "${GREEN}All critical systems operational.${NC}\n"

        echo -e "${BOLD}Next Steps:${NC}"
        echo -e "  1. Review demo script: ${CYAN}cat INVESTOR_DEMO.md${NC}"
        echo -e "  2. Open frontend: ${CYAN}http://localhost:3000${NC}"
        echo -e "  3. Test key flows manually"
        echo -e "  4. ${GREEN}Proceed with confidence!${NC}\n"

    else
        echo -e "${RED}${BOLD}"
        cat <<EOF
   ███╗   ██╗ ██████╗       ██████╗  ██████╗     ███████╗████████╗ ██████╗ ██████╗
   ████╗  ██║██╔═══██╗     ██╔════╝ ██╔═══██╗    ██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗
   ██╔██╗ ██║██║   ██║     ██║  ███╗██║   ██║    ███████╗   ██║   ██║   ██║██████╔╝
   ██║╚██╗██║██║   ██║     ██║   ██║██║   ██║    ╚════██║   ██║   ██║   ██║██╔═══╝
   ██║ ╚████║╚██████╔╝     ╚██████╔╝╚██████╔╝    ███████║   ██║   ╚██████╔╝██║
   ╚═╝  ╚═══╝ ╚═════╝       ╚═════╝  ╚═════╝     ╚══════╝   ╚═╝    ╚═════╝ ╚═╝

EOF
        echo -e "${NC}"
        echo -e "${RED}✗✗✗ CRITICAL ISSUES DETECTED ✗✗✗${NC}"
        echo -e "${RED}Platform is NOT ready for investor demo.${NC}"
        echo -e "${RED}Fix critical issues before proceeding.${NC}\n"

        echo -e "${BOLD}Next Steps:${NC}"
        echo -e "  1. Review failures in report above"
        echo -e "  2. Fix critical infrastructure/service issues"
        echo -e "  3. Check logs: ${CYAN}docker-compose logs${NC}"
        echo -e "  4. Re-run: ${CYAN}./scripts/pre-flight.sh${NC}\n"
    fi

    echo -e "${BOLD}Reports saved to:${NC}"
    echo -e "  • Text:  ${CYAN}$TEXT_REPORT${NC}"
    if [ -f "$JSON_REPORT" ]; then
        echo -e "  • JSON:  ${CYAN}$JSON_REPORT${NC}"
    fi
    echo -e ""
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    print_header

    # Step 1: Check dependencies
    check_dependencies

    # Step 2: Check services
    check_services_running

    # Step 3: Run comprehensive checklist
    if run_checklist; then
        exit_code=0
    else
        exit_code=$?
    fi

    # Step 4: Generate PDF report (optional)
    generate_pdf_report

    # Step 5: Print GO/NO-GO decision
    print_go_nogo_decision $exit_code

    # Exit with checklist exit code
    exit $exit_code
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${YELLOW}Pre-flight check interrupted.${NC}"; exit 130' INT

# Run main
main "$@"
