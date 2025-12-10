#!/bin/bash

# Script to add all Supabase secrets to GitHub
# Requires: GitHub Personal Access Token with 'repo' scope

set -e

REPO="milosriki/geminivideo"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔐 Adding Supabase Secrets to GitHub"
echo "===================================="
echo ""

# Check if GitHub token is provided
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  GITHUB_TOKEN not set${NC}"
    echo ""
    echo "To add secrets automatically, you need a GitHub Personal Access Token:"
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Select scope: 'repo' (full control)"
    echo "4. Copy the token"
    echo ""
    echo "Then run:"
    echo "  export GITHUB_TOKEN=your_github_token"
    echo "  ./add-all-secrets.sh"
    echo ""
    echo "Or add secrets manually at:"
    echo "  https://github.com/$REPO/settings/secrets/actions"
    exit 1
fi

# Function to get GitHub public key for encryption
get_public_key() {
    local response=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$REPO/actions/secrets/public-key")
    
    echo "$response" | grep -o '"key_id":"[^"]*"' | cut -d'"' -f4
}

# Function to encrypt secret value (simplified - GitHub API handles this)
add_secret() {
    local secret_name=$1
    local secret_value=$2
    
    if [ -z "$secret_value" ]; then
        echo -e "${RED}❌ $secret_name: Value is empty${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}📝 Adding: $secret_name${NC}"
    
    # Get public key
    local key_id=$(get_public_key)
    if [ -z "$key_id" ]; then
        echo -e "${RED}❌ Failed to get GitHub public key${NC}"
        return 1
    fi
    
    # Note: In production, you'd encrypt the value with the public key
    # For now, we'll use GitHub CLI if available, or provide manual instructions
    if command -v gh &> /dev/null; then
        echo "$secret_value" | gh secret set "$secret_name" --repo "$REPO"
        echo -e "${GREEN}✅ $secret_name: Added${NC}"
    else
        echo -e "${YELLOW}⚠️  GitHub CLI not found. Please add manually:${NC}"
        echo "   Name: $secret_name"
        echo "   Value: [hidden]"
        echo "   Go to: https://github.com/$REPO/settings/secrets/actions"
    fi
}

# Secrets from user
SUPABASE_SECRET_KEY="sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3"
SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFraGlydWd3cG96bHhmdnRxbXZqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjM1OTYyOSwiZXhwIjoyMDc3OTM1NjI5fQ.owJC_fsEfG3BVHGWQ1MiAY9HMlOtOvUp1yN3IxqizhI"
SUPABASE_ACCESS_TOKEN="sbp_125c933334f63cbb1dbbe0d77bb6c29afc4ee0a8"

echo "Adding secrets..."
echo ""

# Add new format keys
add_secret "SUPABASE_SECRET_KEY" "$SUPABASE_SECRET_KEY"
add_secret "SUPABASE_ACCESS_TOKEN" "$SUPABASE_ACCESS_TOKEN"

# Keep service role key (legacy format)
add_secret "SUPABASE_SERVICE_ROLE_KEY" "$SUPABASE_SERVICE_ROLE_KEY"

echo ""
echo -e "${YELLOW}⚠️  Still need: SUPABASE_DB_URL${NC}"
echo "Get from: Supabase Dashboard → Settings → Database → Connection string"
echo ""

echo -e "${GREEN}✅ Done!${NC}"
echo ""
echo "Verify at: https://github.com/$REPO/settings/secrets/actions"

