#!/bin/bash

# Simple script to add GitHub Secrets using GitHub CLI (gh)
# If GitHub CLI is not installed, this will provide manual instructions

set -e

REPO="milosriki/geminivideo"

echo "🔐 GitHub Secrets Setup"
echo "======================="
echo ""

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    echo ""
    echo "📦 Install GitHub CLI:"
    echo "  macOS: brew install gh"
    echo "  Linux: See https://cli.github.com/"
    echo ""
    echo "🔐 Then authenticate:"
    echo "  gh auth login"
    echo ""
    echo "📝 Or add secrets manually:"
    echo "  1. Go to: https://github.com/$REPO/settings/secrets/actions"
    echo "  2. Click 'New repository secret'"
    echo "  3. Add the following secrets:"
    echo ""
    echo "     Name: SUPABASE_DB_URL"
    echo "     Value: (from Supabase Dashboard → Settings → Database → Connection string)"
    echo ""
    echo "     Name: SUPABASE_ACCESS_TOKEN"
    echo "     Value: (from Supabase Dashboard → Account → Access Tokens → Generate new token)"
    echo ""
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI"
    echo ""
    echo "Run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI is installed and authenticated"
echo ""

# Get values from user
echo "Enter the missing Supabase values:"
echo ""

# Get SUPABASE_DB_URL
read -p "📦 SUPABASE_DB_URL: " DB_URL
if [ -n "$DB_URL" ]; then
    echo "Adding SUPABASE_DB_URL..."
    echo "$DB_URL" | gh secret set SUPABASE_DB_URL --repo "$REPO"
    echo "✅ Added SUPABASE_DB_URL"
else
    echo "⚠️  Skipping SUPABASE_DB_URL"
fi

echo ""

# Get SUPABASE_ACCESS_TOKEN
read -p "🔑 SUPABASE_ACCESS_TOKEN: " ACCESS_TOKEN
if [ -n "$ACCESS_TOKEN" ]; then
    echo "Adding SUPABASE_ACCESS_TOKEN..."
    echo "$ACCESS_TOKEN" | gh secret set SUPABASE_ACCESS_TOKEN --repo "$REPO"
    echo "✅ Added SUPABASE_ACCESS_TOKEN"
else
    echo "⚠️  Skipping SUPABASE_ACCESS_TOKEN"
fi

echo ""
echo "✅ Done!"
echo ""
echo "Verify at: https://github.com/$REPO/settings/secrets/actions"

