#!/bin/bash
# setup-supabase-sync.sh - Quick setup for Supabase sync workflow

set -e

echo "🔄 Setting up Supabase Sync Workflow"
echo "===================================="
echo ""

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "📦 Installing Supabase CLI..."
    npm install -g supabase@latest
else
    echo "✅ Supabase CLI already installed"
    supabase --version
fi

echo ""
echo "📋 Next steps:"
echo ""
echo "1. Link your Supabase project:"
echo "   supabase link --project-ref YOUR_PROJECT_REF"
echo ""
echo "2. Start local Supabase:"
echo "   supabase start"
echo ""
echo "3. Set up GitHub Secrets (go to):"
echo "   https://github.com/milosriki/geminivideo/settings/secrets/actions"
echo ""
echo "   Add these secrets:"
echo "   - SUPABASE_ACCESS_TOKEN (from Supabase Dashboard → Account → Access Tokens)"
echo "   - SUPABASE_PROJECT_REF (from Supabase Dashboard → Project Settings)"
echo "   - SUPABASE_DB_URL (from Supabase Dashboard → Settings → Database → Connection string)"
echo ""
echo "4. Test the workflow:"
echo "   # Make a change locally"
echo "   supabase db diff -f test_change"
echo "   git add supabase/migrations/"
echo "   git commit -m 'test: migration sync'"
echo "   git push"
echo ""
echo "✅ Setup complete! Read SUPABASE_SYNC_WORKFLOW.md for full details."
echo ""

