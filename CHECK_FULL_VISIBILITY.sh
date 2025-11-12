#!/bin/bash
# FULL VISIBILITY CHECK SCRIPT
# Run this to see EVERYTHING about the geminivideo project

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                    GEMINIVIDEO FULL VISIBILITY CHECK                     ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Repository Info
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 REPOSITORY INFO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git remote -v | head -2
echo ""
echo "🌐 GitHub URLs:"
echo "   Repository:     https://github.com/milosriki/geminivideo"
echo "   Branches:       https://github.com/milosriki/geminivideo/branches"
echo "   Pull Requests:  https://github.com/milosriki/geminivideo/pulls"
echo "   Issues:         https://github.com/milosriki/geminivideo/issues"
echo "   Actions:        https://github.com/milosriki/geminivideo/actions"
echo "   Commits:        https://github.com/milosriki/geminivideo/commits"
echo ""

# Current Branch
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌿 CURRENT BRANCH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git branch --show-current
echo ""

# All Branches
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌳 ALL REMOTE BRANCHES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git fetch origin --prune 2>&1 | grep -v "From https"
echo ""
git branch -r | while read branch; do
    clean_branch=$(echo "$branch" | sed 's/origin\///' | xargs)
    if [ ! -z "$clean_branch" ] && [ "$clean_branch" != "HEAD" ]; then
        echo "  ✓ $clean_branch"
        echo "    https://github.com/milosriki/geminivideo/tree/$clean_branch"
    fi
done
echo ""

# Recent Commits
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 RECENT COMMITS (Last 15)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git log --oneline --all --decorate -15 | while read line; do
    commit_hash=$(echo "$line" | awk '{print $1}')
    echo "$line"
    echo "  🔗 https://github.com/milosriki/geminivideo/commit/$commit_hash"
done
echo ""

# Service Files
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏗️  SERVICES STRUCTURE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ls -d services/*/ 2>/dev/null | while read svc; do
    echo "📁 $svc"
    find "$svc" -name "*.py" -o -name "*.ts" -o -name "*.tsx" 2>/dev/null | head -10 | sed 's/^/  /'
done
echo ""

# Critical Missing Files Check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 CRITICAL FILES CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Database
if [ -d "shared/db" ]; then
    echo "✅ shared/db/ exists"
    ls -la shared/db/ | tail -n +4
else
    echo "❌ shared/db/ MISSING - Need Agent 1 (Database)"
fi
echo ""

# Docker Compose
if [ -f "docker-compose.yml" ]; then
    echo "✅ docker-compose.yml exists"
else
    echo "❌ docker-compose.yml MISSING - Need Agent 1 (Database) + Agent 5 (DevOps)"
fi
echo ""

# ML Dependencies Check
echo "🤖 ML Dependencies Check:"
echo ""
echo "drive-intel requirements.txt:"
if grep -q "deepface" services/drive-intel/requirements.txt 2>/dev/null; then
    echo "  ✅ deepface found"
else
    echo "  ❌ deepface MISSING - Need Agent 2 (Emotion)"
fi

if grep -q "xgboost" services/*/requirements.txt services/*/package.json 2>/dev/null; then
    echo "  ✅ xgboost found"
else
    echo "  ❌ xgboost MISSING - Need Agent 2 (ML Models)"
fi

if grep -q "vowpal" services/*/requirements.txt services/*/package.json 2>/dev/null; then
    echo "  ✅ vowpal-wabbit found"
else
    echo "  ❌ vowpal-wabbit MISSING - Need Agent 2 (ML Models)"
fi

echo ""
echo "meta-publisher package.json:"
if grep -q "facebook-business-sdk" services/meta-publisher/package.json 2>/dev/null; then
    echo "  ✅ facebook-business-sdk found"
else
    echo "  ❌ facebook-business-sdk MISSING - Need Agent 3 (Meta SDK)"
fi
echo ""

# Configuration Files
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚙️  CONFIGURATION FILES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -d "shared/config" ]; then
    echo "✅ shared/config/ exists:"
    ls shared/config/ | sed 's/^/  /'
else
    echo "❌ shared/config/ missing"
fi
echo ""

# GitHub Workflows
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚙️  GITHUB ACTIONS WORKFLOWS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -d ".github/workflows" ]; then
    ls .github/workflows/*.yml 2>/dev/null | while read workflow; do
        echo "✅ $(basename $workflow)"
        echo "   https://github.com/milosriki/geminivideo/blob/main/.github/workflows/$(basename $workflow)"
    done
else
    echo "❌ No workflows found"
fi
echo ""

# Agent Instructions
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 AGENT INSTRUCTIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -d ".github/agents" ]; then
    ls .github/agents/*.md 2>/dev/null | while read agent; do
        echo "✅ $(basename $agent)"
    done
else
    echo "❌ No agent instructions found"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 COMPLETION SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ BUILT (40%):"
echo "  • 5 microservices (gateway, drive-intel, video-agent, meta-publisher, frontend)"
echo "  • CI/CD workflows (deploy-cloud-run.yml, codeql.yml)"
echo "  • Configuration files (weights.yaml, scene_ranking.yaml)"
echo "  • Agent instructions (12 agent files)"
echo "  • Basic tests"
echo ""
echo "❌ MISSING (60% - CRITICAL):"
echo "  🔴 Database Layer (0%) - Agent 1 needed"
echo "     • No PostgreSQL setup"
echo "     • No shared/db/schema.sql"
echo "     • No SQLAlchemy models"
echo "     • No docker-compose.yml"
echo ""
echo "  🔴 Emotion Recognition (0%) - Agent 2 needed"
echo "     • No DeepFace integration"
echo "     • Target: 85% accuracy"
echo ""
echo "  🔴 ML Models (0%) - Agent 2 needed"
echo "     • No XGBoost (CTR prediction - 94% target)"
echo "     • No Vowpal Wabbit (A/B testing)"
echo "     • Only heuristic scoring"
echo ""
echo "  🔴 Meta SDK (0%) - Agent 3 needed"
echo "     • No facebook-business-sdk"
echo "     • Mock/stub code only"
echo "     • Can't publish real ads"
echo ""
echo "  🟡 Frontend Wiring (30%) - Agent 4 needed"
echo "     • UI exists but not connected to backend"
echo "     • No API client"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 NEXT STEPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Read: COMPLETE_VISIBILITY_REPORT.md (full details)"
echo "2. Start Agent 1 (Database) + Agent 2 (ML/Emotion) in parallel"
echo "3. Then Agent 3 (Meta) + Agent 4 (Frontend) in parallel"
echo "4. Finally Agent 5 (DevOps/Testing)"
echo ""
echo "Estimated: 2-3 days with parallel execution"
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                           END OF VISIBILITY CHECK                        ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
