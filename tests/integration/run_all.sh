#!/bin/bash

################################################################################
# Integration Test Runner
# Runs all integration tests with coverage reporting and JUnit XML output
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Integration Test Suite - Titan-Core            ║${NC}"
echo -e "${BLUE}║     €5M Investment-Grade Ad Platform                ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
COVERAGE_TARGET=60
OUTPUT_DIR="$SCRIPT_DIR/test-results"
JUNIT_XML="$OUTPUT_DIR/junit.xml"
COVERAGE_XML="$OUTPUT_DIR/coverage.xml"
COVERAGE_HTML="$OUTPUT_DIR/htmlcov"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}✗ pytest not found. Installing...${NC}"
    pip install pytest pytest-asyncio pytest-cov httpx
fi

# Check if API server is running
echo -e "${YELLOW}→ Checking API server status...${NC}"
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${YELLOW}⚠ API server not running at http://localhost:8000${NC}"
    echo -e "${YELLOW}  Some tests may be skipped.${NC}"
    echo ""
fi

# Display test configuration
echo -e "${BLUE}Test Configuration:${NC}"
echo "  Project Root:    $PROJECT_ROOT"
echo "  Test Directory:  $SCRIPT_DIR"
echo "  Output Directory: $OUTPUT_DIR"
echo "  Coverage Target: ${COVERAGE_TARGET}%"
echo ""

# Run tests with different verbosity based on environment
if [ "$CI" = "true" ]; then
    VERBOSITY="-v"
else
    VERBOSITY="-vv"
fi

# Test suites
declare -A TEST_SUITES=(
    ["API Endpoints"]="test_api_endpoints.py"
    ["AI Council"]="test_ai_council.py"
    ["Video Pipeline"]="test_video_pipeline.py"
    ["Publishing"]="test_publishing.py"
    ["Predictions"]="test_predictions.py"
    ["Full E2E Flow"]="test_full_flow.py"
)

# Run individual test suites
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Running Test Suites${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

FAILED_SUITES=()
PASSED_SUITES=()

for suite_name in "${!TEST_SUITES[@]}"; do
    test_file="${TEST_SUITES[$suite_name]}"
    echo -e "${YELLOW}→ Running: ${suite_name}${NC}"

    if pytest "$SCRIPT_DIR/$test_file" \
        $VERBOSITY \
        --tb=short \
        --disable-warnings \
        -m "not slow" \
        2>&1 | tee "$OUTPUT_DIR/${test_file%.py}.log"; then
        echo -e "${GREEN}✓ ${suite_name} - PASSED${NC}"
        PASSED_SUITES+=("$suite_name")
    else
        echo -e "${RED}✗ ${suite_name} - FAILED${NC}"
        FAILED_SUITES+=("$suite_name")
    fi
    echo ""
done

# Run all tests with coverage
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Running Full Suite with Coverage${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

cd "$PROJECT_ROOT"

pytest "$SCRIPT_DIR" \
    $VERBOSITY \
    --tb=short \
    --disable-warnings \
    --cov=services/titan-core \
    --cov=services/gateway-api \
    --cov-report=term-missing \
    --cov-report=html:"$COVERAGE_HTML" \
    --cov-report=xml:"$COVERAGE_XML" \
    --junitxml="$JUNIT_XML" \
    -m "not slow" \
    || true

# Parse coverage results
if [ -f "$COVERAGE_XML" ]; then
    # Extract coverage percentage
    COVERAGE=$(python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('$COVERAGE_XML')
root = tree.getroot()
line_rate = float(root.attrib.get('line-rate', 0))
print(f'{line_rate * 100:.1f}')
" 2>/dev/null || echo "0.0")
else
    COVERAGE="0.0"
fi

# Generate summary report
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Suite results
echo -e "${GREEN}Passed Suites (${#PASSED_SUITES[@]}):${NC}"
for suite in "${PASSED_SUITES[@]}"; do
    echo -e "  ${GREEN}✓${NC} $suite"
done
echo ""

if [ ${#FAILED_SUITES[@]} -gt 0 ]; then
    echo -e "${RED}Failed Suites (${#FAILED_SUITES[@]}):${NC}"
    for suite in "${FAILED_SUITES[@]}"; do
        echo -e "  ${RED}✗${NC} $suite"
    done
    echo ""
fi

# Coverage results
echo -e "${BLUE}Coverage:${NC}"
echo -e "  Current:  ${COVERAGE}%"
echo -e "  Target:   ${COVERAGE_TARGET}%"

if (( $(echo "$COVERAGE >= $COVERAGE_TARGET" | bc -l) )); then
    echo -e "  Status:   ${GREEN}✓ PASSED${NC}"
    COVERAGE_PASSED=true
else
    echo -e "  Status:   ${RED}✗ BELOW TARGET${NC}"
    COVERAGE_PASSED=false
fi
echo ""

# Output locations
echo -e "${BLUE}Reports Generated:${NC}"
echo "  JUnit XML:     $JUNIT_XML"
echo "  Coverage XML:  $COVERAGE_XML"
echo "  Coverage HTML: $COVERAGE_HTML/index.html"
echo ""

# Final status
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

if [ ${#FAILED_SUITES[@]} -eq 0 ] && [ "$COVERAGE_PASSED" = true ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED - Coverage: ${COVERAGE}%${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    exit 0
elif [ ${#FAILED_SUITES[@]} -eq 0 ]; then
    echo -e "${YELLOW}⚠ Tests passed but coverage below target${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    exit 1
else
    echo -e "${RED}✗ TESTS FAILED - ${#FAILED_SUITES[@]} suite(s) failed${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    exit 1
fi
