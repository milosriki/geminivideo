#!/bin/bash
# COMPLETE CODEBASE AUDIT SCRIPT
# Run this to get ground truth of what exists and what's wired

echo "==========================================================="
echo "=== COMPLETE GEMINIVIDEO AUDIT ==="
echo "==========================================================="

# Check all critical files exist
echo ""
echo "=== CRITICAL FILES EXISTENCE CHECK ==="
echo ""

# Database Migrations
echo "Database Migrations:"
find . -name "*pending_ad_changes.sql" -o -name "*model_registry.sql" -o -name "*synthetic_revenue*.sql" 2>/dev/null | sort

# Python ML Modules
echo ""
echo "Python ML Modules:"
find services/ml-service/src -name "battle_hardened_sampler.py" -o -name "winner_index.py" -o -name "synthetic_revenue.py" -o -name "fatigue_detector.py" 2>/dev/null | sort

# TypeScript Workers
echo ""
echo "TypeScript Workers:"
find services/gateway-api/src -name "safe-executor.ts" -o -name "hubspot.ts" 2>/dev/null | sort

# Check BattleHardenedSampler features
echo ""
echo "=== BATTLEHARDENED SAMPLER FEATURES ==="
if [ -f "services/ml-service/src/battle_hardened_sampler.py" ]; then
    echo "✅ File exists"
    echo ""
    echo "Mode parameter:"
    grep -n "mode: str" services/ml-service/src/battle_hardened_sampler.py || echo "❌ Missing"
    echo ""
    echo "Ignorance zone:"
    grep -n "ignorance_zone" services/ml-service/src/battle_hardened_sampler.py | head -3 || echo "❌ Missing"
    echo ""
    echo "Service kill logic:"
    grep -n "should_kill_service_ad" services/ml-service/src/battle_hardened_sampler.py || echo "❌ Missing"
else
    echo "❌ File not found"
fi

# Check API Endpoints
echo ""
echo "=== API ENDPOINTS CHECK ==="
if [ -f "services/ml-service/src/main.py" ]; then
    echo "Battle-Hardened endpoints:"
    grep -n "/api/ml/battle-hardened" services/ml-service/src/main.py | head -5
    echo ""
    echo "RAG endpoints:"
    grep -n "/api/ml/rag" services/ml-service/src/main.py | head -5
    echo ""
    echo "Synthetic revenue endpoints:"
    grep -n "/api/ml/synthetic-revenue" services/ml-service/src/main.py | head -5
fi

# Check SafeExecutor implementation
echo ""
echo "=== SAFE EXECUTOR CHECK ==="
if [ -f "services/gateway-api/src/jobs/safe-executor.ts" ]; then
    if grep -q "claim_pending_ad_change" services/gateway-api/src/jobs/safe-executor.ts; then
        echo "✅ Uses native PostgreSQL queue"
    else
        echo "⚠️ May use pg-boss or other pattern"
    fi
else
    echo "❌ safe-executor.ts not found"
fi

# Count total lines of code
echo ""
echo "=== CODEBASE STATISTICS ==="
echo "Total Python files:"
find services -name "*.py" 2>/dev/null | wc -l
echo "Total TypeScript files:"
find services -name "*.ts" 2>/dev/null | wc -l
echo "Total SQL migrations:"
find database/migrations -name "*.sql" 2>/dev/null | wc -l

echo ""
echo "=== AUDIT COMPLETE ==="

