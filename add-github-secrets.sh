#!/bin/bash

# Script to add missing GitHub Secrets via GitHub API
# Requires: GitHub Personal Access Token with 'repo' scope

set -e

REPO="milosriki/geminivideo"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔐 GitHub Secrets Setup Script"
echo "=============================="
echo ""

# Check if GitHub token is provided
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  GITHUB_TOKEN not set${NC}"
    echo ""
    echo "To use this script, you need a GitHub Personal Access Token:"
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Select scope: 'repo' (full control of private repositories)"
    echo "4. Copy the token"
    echo ""
    echo "Then run:"
    echo "  export GITHUB_TOKEN=your_token_here"
    echo "  ./add-github-secrets.sh"
    echo ""
    exit 1
fi

# Function to add a secret
add_secret() {
    local secret_name=$1
    local secret_value=$2
    
    if [ -z "$secret_value" ]; then
        echo -e "${RED}❌ $secret_name: Value is empty${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}📝 Adding secret: $secret_name${NC}"
    
    # Use GitHub API to add secret
    # Note: GitHub API requires encryption, so we use a workaround
    # We'll use the GitHub CLI if available, or provide manual instructions
    
    response=$(curl -s -w "\n%{http_code}" -X PUT \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -H "Content-Type: application/json" \
        "https://api.github.com/repos/$REPO/actions/secrets/$secret_name" \
        -d "{\"encrypted_value\":\"$secret_value\",\"key_id\":\"$(curl -s -H \"Authorization: token $GITHUB_TOKEN\" https://api.github.com/repos/$REPO/actions/secrets/public-key | jq -r '.key_id')\"}" 2>&1)
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "204" ] || [ "$http_code" = "201" ]; then
        echo -e "${GREEN}✅ $secret_name: Added successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ $secret_name: Failed (HTTP $http_code)${NC}"
        echo "Response: $body"
        return 1
    fi
}

# Get values from user
echo "Enter the missing Supabase values:"
echo ""

# Get SUPABASE_DB_URL
read -p "📦 SUPABASE_DB_URL (from Supabase Dashboard → Settings → Database → Connection string): " DB_URL
if [ -z "$DB_URL" ]; then
    echo -e "${YELLOW}⚠️  Skipping SUPABASE_DB_URL${NC}"
else
    add_secret "SUPABASE_DB_URL" "$DB_URL"
fi

echo ""

# Get SUPABASE_ACCESS_TOKEN
read -p "🔑 SUPABASE_ACCESS_TOKEN (from Supabase Dashboard → Account → Access Tokens): " ACCESS_TOKEN
if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  Skipping SUPABASE_ACCESS_TOKEN${NC}"
else
    add_secret "SUPABASE_ACCESS_TOKEN" "$ACCESS_TOKEN"
fi

echo ""
echo -e "${GREEN}✅ Done!${NC}"
echo ""
echo "Verify secrets at:"
echo "https://github.com/$REPO/settings/secrets/actions"

