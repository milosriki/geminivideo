#!/bin/bash

# Add secrets using GitHub CLI (if available)
# This is the most reliable method

set -e

REPO="milosriki/geminivideo"
GITHUB_TOKEN="${GITHUB_TOKEN:-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}"

echo "🔐 Adding Secrets via GitHub CLI"
echo "================================="
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed"
    echo ""
    echo "Installing GitHub CLI..."
    echo ""
    
    # Try to install via Homebrew (macOS)
    if command -v brew &> /dev/null; then
        brew install gh
    else
        echo "⚠️  Homebrew not found. Please install GitHub CLI manually:"
        echo "   https://cli.github.com/"
        echo ""
        echo "Or use the manual method in QUICK_START_ADD_SECRETS.md"
        exit 1
    fi
fi

# Authenticate with token
echo "🔑 Authenticating with GitHub..."
echo "$GITHUB_TOKEN" | gh auth login --with-token

# Verify authentication
if ! gh auth status &> /dev/null; then
    echo "❌ Authentication failed"
    exit 1
fi

echo "✅ Authenticated"
echo ""

# Add secrets
echo "📦 Adding secrets..."
echo ""

echo "sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3" | gh secret set SUPABASE_SECRET_KEY --repo "$REPO"
echo "✅ SUPABASE_SECRET_KEY: Added"

echo "sbp_125c933334f63cbb1dbbe0d77bb6c29afc4ee0a8" | gh secret set SUPABASE_ACCESS_TOKEN --repo "$REPO"
echo "✅ SUPABASE_ACCESS_TOKEN: Added"

echo ""
echo "⚠️  Still need: SUPABASE_DB_URL"
echo "Get from: https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj/settings/database"
echo ""

read -p "Do you have SUPABASE_DB_URL to add now? (paste it or press Enter to skip): " db_url
if [ -n "$db_url" ]; then
    echo "$db_url" | gh secret set SUPABASE_DB_URL --repo "$REPO"
    echo "✅ SUPABASE_DB_URL: Added"
fi

echo ""
echo "✅ Done!"
echo ""
echo "Verify at: https://github.com/$REPO/settings/secrets/actions"

