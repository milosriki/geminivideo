#!/bin/bash
# AGENT 90: RUN ALL FIXES
# Master script to execute all fix scripts in the correct order
# This script is IDEMPOTENT - safe to run multiple times

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "AGENT 90: MASTER FIX EXECUTION"
echo "========================================="
echo "This will run all fix scripts in sequence"
echo ""
echo "Scripts to execute:"
echo "  1. fix-critical.sh    - Syntax & import errors"
echo "  2. fix-logic.py       - Algorithm & math errors"
echo "  3. fix-docker.sh      - Docker configuration"
echo "  4. fix-api-routes.ts  - Missing API endpoints"
echo "  5. fix-security.sh    - Security vulnerabilities"
echo "  6. verify-fixes.sh    - Verify all fixes"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted by user"
    exit 1
fi

echo ""
echo "========================================="
echo "STEP 1/6: CRITICAL FIXES"
echo "========================================="
"$SCRIPT_DIR/fix-critical.sh"

echo ""
echo "========================================="
echo "STEP 2/6: LOGIC FIXES"
echo "========================================="
"$SCRIPT_DIR/fix-logic.py"

echo ""
echo "========================================="
echo "STEP 3/6: DOCKER FIXES"
echo "========================================="
"$SCRIPT_DIR/fix-docker.sh"

echo ""
echo "========================================="
echo "STEP 4/6: API ROUTE FIXES"
echo "========================================="
# Check if ts-node is available
if command -v ts-node &> /dev/null; then
    "$SCRIPT_DIR/fix-api-routes.ts"
elif command -v npx &> /dev/null; then
    npx ts-node "$SCRIPT_DIR/fix-api-routes.ts"
else
    echo "⚠ WARNING: ts-node not found. Skipping API route fixes."
    echo "To fix: npm install -g ts-node"
    echo "Then run: $SCRIPT_DIR/fix-api-routes.ts"
fi

echo ""
echo "========================================="
echo "STEP 5/6: SECURITY FIXES"
echo "========================================="
"$SCRIPT_DIR/fix-security.sh"

echo ""
echo "========================================="
echo "STEP 6/6: VERIFICATION"
echo "========================================="
"$SCRIPT_DIR/verify-fixes.sh"

echo ""
echo "========================================="
echo "ALL FIXES COMPLETE!"
echo "========================================="
echo ""
echo "Review the verification results above."
echo "If success rate > 95%, you're ready for:"
echo "  1. Full test suite: npm test && pytest"
echo "  2. Docker deployment: docker-compose up -d"
echo "  3. Integration testing"
echo "  4. Investor demonstration"
echo ""
echo "For manual fixes needed, see:"
echo "  $SCRIPT_DIR/README.md"
echo ""
