#!/bin/bash

# Script to add Supabase environment variables to Vercel
# Requires: Vercel CLI installed and authenticated

set -e

PROJECT_NAME="geminivideo"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔗 Adding Supabase Environment Variables to Vercel"
echo "=================================================="
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}⚠️  Vercel CLI not installed${NC}"
    echo ""
    echo "Install it:"
    echo "  npm i -g vercel"
    echo ""
    echo "Or add variables manually in Vercel Dashboard:"
    echo "  https://vercel.com/dashboard"
    exit 1
fi

# Check if authenticated
if ! vercel whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not authenticated with Vercel${NC}"
    echo ""
    echo "Run: vercel login"
    exit 1
fi

echo -e "${GREEN}✅ Vercel CLI ready${NC}"
echo ""

# Environment variables
SUPABASE_URL="https://akhirugwpozlxfvtqmvj.supabase.co"
SUPABASE_ANON_KEY="sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG"

# Environments to add to
ENVIRONMENTS=("production" "preview" "development")

echo -e "${BLUE}📦 Adding environment variables...${NC}"
echo ""

for env in "${ENVIRONMENTS[@]}"; do
    echo -e "${YELLOW}Adding to ${env}...${NC}"
    
    # Add VITE_SUPABASE_URL
    echo "$SUPABASE_URL" | vercel env add VITE_SUPABASE_URL "$env" --yes 2>&1 | grep -v "Adding" || true
    
    # Add VITE_SUPABASE_ANON_KEY
    echo "$SUPABASE_ANON_KEY" | vercel env add VITE_SUPABASE_ANON_KEY "$env" --yes 2>&1 | grep -v "Adding" || true
    
    echo -e "${GREEN}✅ ${env}: Variables added${NC}"
    echo ""
done

echo -e "${GREEN}✅ Done!${NC}"
echo ""
echo "📋 Summary:"
echo "  - VITE_SUPABASE_URL: Added to all environments"
echo "  - VITE_SUPABASE_ANON_KEY: Added to all environments"
echo ""
echo "🔄 Next steps:"
echo "  1. Redeploy your project in Vercel"
echo "  2. Verify variables at: https://vercel.com/dashboard"
echo ""
echo "🔗 Verify at:"
echo "  https://vercel.com/dashboard → Your Project → Settings → Environment Variables"

