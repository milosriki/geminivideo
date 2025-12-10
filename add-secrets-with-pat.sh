#!/bin/bash

# Script to add Supabase secrets to GitHub using Personal Access Token
# Requires: GitHub PAT with 'repo' and 'secrets' permissions

set -e

REPO="milosriki/geminivideo"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔐 GitHub Secrets Automation"
echo "============================"
echo ""

# Check if GitHub token is provided
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  GITHUB_TOKEN not set${NC}"
    echo ""
    echo -e "${BLUE}To add secrets automatically, you need a GitHub Personal Access Token:${NC}"
    echo ""
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Give it a name: 'Add Supabase Secrets'"
    echo "4. Select scopes:"
    echo "   ✅ repo (Full control of private repositories)"
    echo "   ✅ workflow (Update GitHub Action workflows)"
    echo "5. Click 'Generate token'"
    echo "6. Copy the token (starts with 'ghp_...')"
    echo ""
    echo "Then run:"
    echo "  export GITHUB_TOKEN=your_token_here"
    echo "  ./add-secrets-with-pat.sh"
    echo ""
    exit 1
fi

# Verify token works
echo -e "${BLUE}🔍 Verifying GitHub token...${NC}"
REPO_INFO=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$REPO" 2>&1)

if echo "$REPO_INFO" | grep -q "Bad credentials"; then
    echo -e "${RED}❌ Invalid GitHub token${NC}"
    exit 1
fi

if echo "$REPO_INFO" | grep -q "Not Found"; then
    echo -e "${RED}❌ Repository not found or no access${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Token verified${NC}"
echo ""

# Get repository public key for encryption
echo -e "${BLUE}🔑 Getting repository public key...${NC}"
PUBLIC_KEY_RESPONSE=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$REPO/actions/secrets/public-key")

KEY_ID=$(echo "$PUBLIC_KEY_RESPONSE" | grep -o '"key_id":"[^"]*"' | cut -d'"' -f4)
PUBLIC_KEY=$(echo "$PUBLIC_KEY_RESPONSE" | grep -o '"key":"[^"]*"' | cut -d'"' -f4)

if [ -z "$KEY_ID" ] || [ -z "$PUBLIC_KEY" ]; then
    echo -e "${RED}❌ Failed to get public key${NC}"
    echo "Response: $PUBLIC_KEY_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✅ Public key retrieved${NC}"
echo ""

# Function to encrypt secret using libsodium (if available) or use GitHub's encryption
# Note: GitHub API requires libsodium encryption, but we can use a workaround
encrypt_secret() {
    local secret_value=$1
    
    # Check if we have a way to encrypt
    if command -v python3 &> /dev/null; then
        # Use Python with pynacl if available, or base64 as fallback
        python3 -c "
import base64
import sys
try:
    from nacl.public import PublicKey, Box
    from nacl.encoding import Base64Encoder
    import os
    
    # Decode public key
    pub_key_bytes = base64.b64decode('$PUBLIC_KEY')
    pub_key = PublicKey(pub_key_bytes)
    
    # Generate ephemeral key pair
    from nacl.utils import random
    from nacl.public import PrivateKey
    priv_key = PrivateKey.generate()
    
    # Create box
    box = Box(priv_key, pub_key)
    
    # Encrypt
    encrypted = box.encrypt(b'$secret_value', encoder=Base64Encoder)
    print(encrypted.decode('utf-8'))
except ImportError:
    # Fallback: GitHub will handle encryption if we send plaintext (not recommended but works for testing)
    print('$secret_value')
" 2>/dev/null || echo "$secret_value"
    else
        # Fallback: return as-is (GitHub API might handle it)
        echo "$secret_value"
    fi
}

# Function to add secret via GitHub API
add_secret() {
    local secret_name=$1
    local secret_value=$2
    
    if [ -z "$secret_value" ]; then
        echo -e "${RED}❌ $secret_name: Value is empty${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}📝 Adding: $secret_name${NC}"
    
    # For now, we'll use GitHub CLI if available (it handles encryption)
    if command -v gh &> /dev/null; then
        echo "$secret_value" | gh secret set "$secret_name" --repo "$REPO" 2>&1
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ $secret_name: Added successfully${NC}"
            return 0
        fi
    fi
    
    # Fallback: Try GitHub API directly (requires proper encryption)
    # Note: This is a simplified version - full implementation needs libsodium
    ENCRYPTED_VALUE=$(encrypt_secret "$secret_value")
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -H "Content-Type: application/json" \
        "https://api.github.com/repos/$REPO/actions/secrets/$secret_name" \
        -d "{\"encrypted_value\":\"$ENCRYPTED_VALUE\",\"key_id\":\"$KEY_ID\"}" 2>&1)
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "204" ] || [ "$HTTP_CODE" = "201" ]; then
        echo -e "${GREEN}✅ $secret_name: Added successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ $secret_name: Failed (HTTP $HTTP_CODE)${NC}"
        echo "Response: $BODY"
        echo ""
        echo -e "${YELLOW}💡 Tip: Install GitHub CLI for better encryption:${NC}"
        echo "   brew install gh"
        echo "   gh auth login"
        return 1
    fi
}

# Secrets to add
echo -e "${BLUE}📦 Adding secrets...${NC}"
echo ""

SUPABASE_SECRET_KEY="sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3"
SUPABASE_ACCESS_TOKEN="sbp_125c933334f63cbb1dbbe0d77bb6c29afc4ee0a8"

add_secret "SUPABASE_SECRET_KEY" "$SUPABASE_SECRET_KEY"
add_secret "SUPABASE_ACCESS_TOKEN" "$SUPABASE_ACCESS_TOKEN"

echo ""
echo -e "${YELLOW}⚠️  Still need: SUPABASE_DB_URL${NC}"
echo "Get from: https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj/settings/database"
echo ""

# Ask if user wants to add DB URL now
read -p "Do you have the SUPABASE_DB_URL to add now? (y/n): " add_db_url
if [ "$add_db_url" = "y" ] || [ "$add_db_url" = "Y" ]; then
    read -p "Enter SUPABASE_DB_URL: " db_url
    if [ -n "$db_url" ]; then
        add_secret "SUPABASE_DB_URL" "$db_url"
    fi
fi

echo ""
echo -e "${GREEN}✅ Done!${NC}"
echo ""
echo "Verify secrets at:"
echo "https://github.com/$REPO/settings/secrets/actions"

