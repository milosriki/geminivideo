#!/bin/bash

# Vercel Account Diagnostic Script
# This script helps diagnose Vercel account connection issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║   Vercel Account Connection Diagnostic Tool          ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}⚠️  Vercel CLI not found${NC}"
    echo ""
    echo "Install it with:"
    echo "  npm i -g vercel"
    echo ""
    echo "For now, we'll run checks that don't require the CLI."
    VERCEL_CLI_AVAILABLE=false
else
    VERCEL_CLI_AVAILABLE=true
    echo -e "${GREEN}✅ Vercel CLI is installed${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  STEP 1: Checking Local Project Configuration"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check if .vercel directory exists
if [ -d ".vercel" ]; then
    echo -e "${GREEN}✅ Found .vercel directory${NC}"
    
    # Check project.json
    if [ -f ".vercel/project.json" ]; then
        echo -e "${GREEN}✅ Found .vercel/project.json${NC}"
        echo ""
        echo "Project Configuration:"
        echo "─────────────────────────────────────────────"
        cat .vercel/project.json | grep -E '"projectId"|"orgId"' || echo "Unable to parse project.json"
        echo "─────────────────────────────────────────────"
        
        PROJECT_ID=$(cat .vercel/project.json | grep -o '"projectId":"[^"]*"' | cut -d'"' -f4)
        ORG_ID=$(cat .vercel/project.json | grep -o '"orgId":"[^"]*"' | cut -d'"' -f4)
        
        if [ ! -z "$PROJECT_ID" ]; then
            echo -e "${BLUE}📝 Project ID: ${PROJECT_ID}${NC}"
        fi
        if [ ! -z "$ORG_ID" ]; then
            echo -e "${BLUE}📝 Organization ID: ${ORG_ID}${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  .vercel/project.json not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No .vercel directory found${NC}"
    echo "   This means the project hasn't been linked via Vercel CLI"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  STEP 2: Checking Vercel CLI Authentication"
echo "═══════════════════════════════════════════════════════"
echo ""

if [ "$VERCEL_CLI_AVAILABLE" = true ]; then
    # Check who is logged in
    VERCEL_USER=$(vercel whoami 2>/dev/null || echo "")
    
    if [ ! -z "$VERCEL_USER" ]; then
        echo -e "${GREEN}✅ Logged into Vercel CLI as:${NC}"
        echo -e "${BLUE}   👤 ${VERCEL_USER}${NC}"
        echo ""
        echo "Is this the correct Vercel account?"
        echo -e "${YELLOW}   If NO, run: vercel logout && vercel login${NC}"
    else
        echo -e "${RED}❌ Not logged into Vercel CLI${NC}"
        echo ""
        echo "To log in, run:"
        echo "  vercel login"
    fi
else
    echo -e "${YELLOW}⚠️  Vercel CLI not available - skipping this check${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  STEP 3: Checking Git Remote"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check git remote
if command -v git &> /dev/null && [ -d ".git" ]; then
    GIT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
    
    if [ ! -z "$GIT_REMOTE" ]; then
        echo -e "${GREEN}✅ Found Git remote:${NC}"
        echo -e "${BLUE}   🔗 ${GIT_REMOTE}${NC}"
        
        # Extract GitHub info
        if [[ "$GIT_REMOTE" =~ github\.com[:/]([^/]+)/([^/\.]+) ]]; then
            GITHUB_OWNER="${BASH_REMATCH[1]}"
            GITHUB_REPO="${BASH_REMATCH[2]}"
            echo ""
            echo -e "${BLUE}   📁 Owner: ${GITHUB_OWNER}${NC}"
            echo -e "${BLUE}   📦 Repository: ${GITHUB_REPO}${NC}"
            echo ""
            echo "You can check GitHub webhooks at:"
            echo -e "${BLUE}   https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/settings/hooks${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  No Git remote found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Not a Git repository or Git not installed${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  STEP 4: Checking Environment Files"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check for environment files
ENV_FILES=(".env" ".env.local" ".env.production" ".env.example")
FOUND_ENV_FILES=()

for file in "${ENV_FILES[@]}"; do
    if [ -f "$file" ]; then
        FOUND_ENV_FILES+=("$file")
        echo -e "${GREEN}✅ Found: ${file}${NC}"
        
        # Check for Vercel-related variables
        if grep -q "VERCEL" "$file" 2>/dev/null; then
            echo -e "${BLUE}   Contains VERCEL variables${NC}"
        fi
        
        # Check for Supabase variables (common in this project)
        if grep -q "SUPABASE" "$file" 2>/dev/null; then
            echo -e "${BLUE}   Contains SUPABASE variables${NC}"
        fi
    fi
done

if [ ${#FOUND_ENV_FILES[@]} -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No environment files found${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  STEP 5: Checking vercel.json Configuration"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check for vercel.json
VERCEL_JSON_FILES=("vercel.json" "frontend/vercel.json")

FOUND_VERCEL_JSON=false
for file in "${VERCEL_JSON_FILES[@]}"; do
    if [ -f "$file" ]; then
        FOUND_VERCEL_JSON=true
        echo -e "${GREEN}✅ Found: ${file}${NC}"
        echo ""
        echo "Configuration preview:"
        echo "─────────────────────────────────────────────"
        head -n 20 "$file" 2>/dev/null || cat "$file"
        echo "─────────────────────────────────────────────"
    fi
done

if [ "$FOUND_VERCEL_JSON" = false ]; then
    echo -e "${YELLOW}⚠️  No vercel.json found${NC}"
    echo "   This is optional - Vercel can auto-detect most projects"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  SUMMARY & NEXT STEPS"
echo "═══════════════════════════════════════════════════════"
echo ""

echo "To verify your Vercel account connection:"
echo ""
echo "1. ${BLUE}Check Vercel Dashboard:${NC}"
echo "   → https://vercel.com/dashboard"
echo "   → Verify the email in top-right corner is YOUR account"
echo "   → Look for your project in the projects list"
echo ""

echo "2. ${BLUE}Check GitHub Integration:${NC}"
echo "   → https://github.com/settings/installations"
echo "   → Find 'Vercel' and click 'Configure'"
echo "   → Verify it has access to your repository"
echo ""

if [ ! -z "$GITHUB_OWNER" ] && [ ! -z "$GITHUB_REPO" ]; then
    echo "3. ${BLUE}Check Repository Webhooks:${NC}"
    echo "   → https://github.com/${GITHUB_OWNER}/${GITHUB_REPO}/settings/hooks"
    echo "   → Look for webhook pointing to Vercel"
    echo "   → Check recent delivery status"
    echo ""
fi

echo "4. ${BLUE}Verify Project Settings in Vercel:${NC}"
echo "   → Project → Settings → Git"
echo "   → Confirm the connected repository is correct"
echo ""

if [ "$VERCEL_CLI_AVAILABLE" = true ] && [ ! -z "$VERCEL_USER" ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Current Vercel CLI user: ${VERCEL_USER}${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
fi

echo ""
echo "📚 For detailed troubleshooting, see:"
echo "   • VERCEL_ACCOUNT_DIAGNOSTIC_GUIDE.md (comprehensive guide)"
echo "   • VERCEL_ACCOUNT_QUICK_CHECK.md (quick reference)"
echo ""
echo "✅ Diagnostic check complete!"
echo ""
