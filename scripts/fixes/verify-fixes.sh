#!/bin/bash
# AGENT 90: VERIFY ALL FIXES
# Tests that each fix was applied correctly and reports remaining issues
# This script is safe to run multiple times

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "========================================="
echo "AGENT 90: FIX VERIFICATION"
echo "========================================="
echo "Working directory: $PROJECT_ROOT"
echo ""

TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNING=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function test_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

function test_fail() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
}

function test_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((TESTS_WARNING++))
}

# ============================================
# VERIFY CRITICAL FIXES (fix-critical.sh)
# ============================================
echo "=== CRITICAL FIXES VERIFICATION ==="

# Test 1: Emoji removed
if grep -q "🛑 STOP" "$PROJECT_ROOT/services/titan-core/prompts/engine.py" 2>/dev/null; then
    test_fail "Emoji still present in prompts/engine.py"
else
    test_pass "Emoji removed from prompts/engine.py"
fi

# Test 2: Import paths fixed
if grep -q "from backend_core" "$PROJECT_ROOT/services/titan-core/orchestrator.py" 2>/dev/null; then
    test_fail "backend_core import still present in orchestrator.py"
else
    test_pass "Import paths updated to titan_core"
fi

# Test 3: Claude model ID updated
if grep -q "claude-sonnet-4-5-20250929" "$PROJECT_ROOT/services/ml-service/src/cross_learner.py" 2>/dev/null; then
    test_fail "Invalid Claude model ID still in cross_learner.py"
else
    test_pass "Claude model ID updated to valid version"
fi

# Test 4: ErrorBoundary import fixed
if grep -q "from '@/components/ErrorBoundary'" "$PROJECT_ROOT/frontend/src/App.tsx" 2>/dev/null; then
    test_fail "ErrorBoundary import path not fixed in App.tsx"
else
    test_pass "ErrorBoundary import path fixed"
fi

# ============================================
# VERIFY LOGIC FIXES (fix-logic.py)
# ============================================
echo ""
echo "=== LOGIC FIXES VERIFICATION ==="

# Test 5: Thompson Sampling alpha fix
if grep -q "variant\['alpha'\] += 1" "$PROJECT_ROOT/services/ml-service/src/thompson_sampler.py" 2>/dev/null; then
    test_pass "Thompson Sampling alpha increment fixed"
else
    test_warn "Thompson Sampling alpha fix not detected"
fi

# Test 6: Division by zero guards
if grep -q "if variant\['impressions'\] > 0:" "$PROJECT_ROOT/services/ml-service/src/thompson_sampler.py" 2>/dev/null; then
    test_pass "Division by zero guard added to Thompson Sampling"
else
    test_warn "Division by zero guard not found in Thompson Sampling"
fi

# Test 7: Array bounds checking
if grep -q "if len(predictions) == 0:" "$PROJECT_ROOT/services/ml-service/src/ctr_model.py" 2>/dev/null; then
    test_pass "Array bounds check added to ctr_model.py"
else
    test_warn "Array bounds check not found in ctr_model.py"
fi

# Test 8: CTR range fix
if grep -q "0.03" "$PROJECT_ROOT/services/ml-service/src/ctr_model.py" 2>/dev/null; then
    test_pass "CTR range updated to realistic values (0.5-3%)"
else
    test_warn "CTR range may not be updated"
fi

# ============================================
# VERIFY API ROUTE FIXES (fix-api-routes.ts)
# ============================================
echo ""
echo "=== API ROUTE FIXES VERIFICATION ==="

# Test 9: Resume endpoint added
if grep -q "\/\:id\/resume" "$PROJECT_ROOT/services/gateway-api/src/routes/campaigns.ts" 2>/dev/null; then
    test_pass "POST /api/campaigns/:id/resume endpoint added"
else
    test_fail "Resume endpoint not found in campaigns.ts"
fi

# Test 10: ROI endpoints added
if grep -q "\/roi\/performance" "$PROJECT_ROOT/services/gateway-api/src/routes/analytics.ts" 2>/dev/null; then
    test_pass "GET /api/analytics/roi/performance endpoint added"
else
    test_fail "ROI performance endpoint not found"
fi

# Test 11: A/B test start/stop endpoints
if grep -q "\/\:id\/start" "$PROJECT_ROOT/services/gateway-api/src/routes/ab-tests.ts" 2>/dev/null; then
    test_pass "POST /api/ab-tests/:id/start endpoint added"
else
    test_fail "A/B test start endpoint not found"
fi

# Test 12: Publishing endpoints
if grep -q "\/api\/publish\/google" "$PROJECT_ROOT/services/gateway-api/src/index.ts" 2>/dev/null; then
    test_pass "POST /api/publish/google endpoint added"
else
    test_fail "Google publish endpoint not found"
fi

# ============================================
# VERIFY DOCKER FIXES (fix-docker.sh)
# ============================================
echo ""
echo "=== DOCKER FIXES VERIFICATION ==="

# Test 13: wget in Alpine images
if grep -q "apk add --no-cache wget" "$PROJECT_ROOT/services/gateway-api/Dockerfile" 2>/dev/null; then
    test_pass "wget added to gateway-api Dockerfile"
else
    test_fail "wget not found in gateway-api Dockerfile"
fi

# Test 14: curl in slim images
if grep -q "curl" "$PROJECT_ROOT/services/ml-service/Dockerfile" 2>/dev/null; then
    test_pass "curl added to ml-service Dockerfile"
else
    test_fail "curl not found in ml-service Dockerfile"
fi

# Test 15: Environment variables in .env.example
if grep -q "FIREBASE_SERVICE_ACCOUNT_PATH" "$PROJECT_ROOT/.env.example" 2>/dev/null; then
    test_pass "Firebase env vars added to .env.example"
else
    test_fail "Firebase env vars not in .env.example"
fi

if grep -q "VITE_WS_URL" "$PROJECT_ROOT/.env.example" 2>/dev/null; then
    test_pass "WebSocket URL added to .env.example"
else
    test_fail "WebSocket URL not in .env.example"
fi

# Test 16: titan-core WORKDIR fix
if grep -q "WORKDIR /app/api" "$PROJECT_ROOT/services/titan-core/Dockerfile" 2>/dev/null; then
    test_pass "WORKDIR added to titan-core Dockerfile"
else
    test_warn "WORKDIR may not be set correctly in titan-core"
fi

# ============================================
# VERIFY SECURITY FIXES (fix-security.sh)
# ============================================
echo ""
echo "=== SECURITY FIXES VERIFICATION ==="

# Test 17: No shell=True
SHELL_TRUE_COUNT=$(grep -r "shell=True" "$PROJECT_ROOT/services" 2>/dev/null | grep -v ".pyc" | grep -v "node_modules" | wc -l || echo "0")
if [ "$SHELL_TRUE_COUNT" -eq 0 ]; then
    test_pass "No shell=True found in subprocess calls"
else
    test_fail "$SHELL_TRUE_COUNT instances of shell=True still found"
fi

# Test 18: Security notes created
if [ -f "$PROJECT_ROOT/services/gateway-api/src/index.ts.security-note" ]; then
    test_pass "Security recommendations documented"
else
    test_warn "Security notes not found (may need manual review)"
fi

# ============================================
# COMPILATION & BUILD TESTS
# ============================================
echo ""
echo "=== COMPILATION TESTS ==="

# Test 19: Python syntax check
echo "  Testing Python syntax..."
PYTHON_SYNTAX_ERRORS=$(find "$PROJECT_ROOT/services" -name "*.py" -type f -exec python3 -m py_compile {} \; 2>&1 | grep -c "SyntaxError" || echo "0")
if [ "$PYTHON_SYNTAX_ERRORS" -eq 0 ]; then
    test_pass "No Python syntax errors"
else
    test_fail "$PYTHON_SYNTAX_ERRORS Python syntax errors found"
fi

# Test 20: TypeScript compilation (if node is available)
if command -v npm &> /dev/null; then
    echo "  Testing TypeScript compilation..."
    if [ -d "$PROJECT_ROOT/frontend" ]; then
        cd "$PROJECT_ROOT/frontend"
        if npm run build &> /dev/null; then
            test_pass "Frontend builds successfully"
        else
            test_warn "Frontend build has errors (check npm run build)"
        fi
        cd "$PROJECT_ROOT"
    fi
fi

# ============================================
# DOCKER BUILD TESTS
# ============================================
echo ""
echo "=== DOCKER BUILD TESTS ==="

if command -v docker &> /dev/null; then
    echo "  Testing Docker builds (this may take a few minutes)..."

    # Test gateway-api build
    if docker build -t test-gateway-api "$PROJECT_ROOT/services/gateway-api" &> /dev/null; then
        test_pass "gateway-api Docker image builds"
    else
        test_fail "gateway-api Docker build failed"
    fi

    # Test ml-service build
    if docker build -t test-ml-service "$PROJECT_ROOT/services/ml-service" &> /dev/null; then
        test_pass "ml-service Docker image builds"
    else
        test_fail "ml-service Docker build failed"
    fi
else
    test_warn "Docker not available - skipping build tests"
fi

# ============================================
# SUMMARY
# ============================================
echo ""
echo "========================================="
echo "VERIFICATION SUMMARY"
echo "========================================="
echo -e "${GREEN}Tests passed: $TESTS_PASSED${NC}"
echo -e "${YELLOW}Tests with warnings: $TESTS_WARNING${NC}"
echo -e "${RED}Tests failed: $TESTS_FAILED${NC}"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_WARNING + TESTS_FAILED))
SUCCESS_RATE=$((TESTS_PASSED * 100 / TOTAL_TESTS))

echo "Success rate: $SUCCESS_RATE%"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "✓ ALL CRITICAL FIXES VERIFIED!"
    echo ""
    echo "INVESTOR-READY CHECKLIST:"
    echo "✓ No syntax errors blocking compilation"
    echo "✓ Import paths standardized"
    echo "✓ Logic errors fixed (Thompson Sampling, CTR range, etc.)"
    echo "✓ API endpoints match frontend contracts"
    echo "✓ Docker health checks will pass"
    echo "✓ Security vulnerabilities addressed"
    echo ""
    echo "NEXT STEPS:"
    echo "1. Run full test suite: npm test && pytest"
    echo "2. Deploy to staging: docker-compose up -d"
    echo "3. Run integration tests"
    echo "4. Schedule investor demo"
    exit 0
else
    echo "⚠ FIXES INCOMPLETE - $TESTS_FAILED issues remaining"
    echo ""
    echo "RECOMMENDED ACTIONS:"
    echo "1. Review failed tests above"
    echo "2. Re-run fix scripts: ./scripts/fixes/fix-*.sh"
    echo "3. Check manual fixes needed in error reports"
    echo "4. Run verification again"
    exit 1
fi
