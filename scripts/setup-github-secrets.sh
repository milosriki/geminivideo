#!/bin/bash

# setup-github-secrets.sh
# Script to set up GitHub Secrets for Gemini Video project
# Usage: ./scripts/setup-github-secrets.sh

echo "🚀 Setting up GitHub Secrets..."

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) could not be found. Please install it first."
    exit 1
fi

# Check if user is logged in
if ! gh auth status &> /dev/null; then
    echo "⚠️  You are not logged in to GitHub CLI. Please run 'gh auth login' first."
    exit 1
fi

# Function to set a secret
set_secret() {
    local name=$1
    local prompt=$2
    
    echo ""
    echo "🔑 Setting $name..."
    if [ -z "$3" ]; then
        read -s -p "$prompt: " value
        echo ""
    else
        value=$3
    fi
    
    if [ -n "$value" ]; then
        gh secret set "$name" --body "$value"
        echo "✅ $name set."
    else
        echo "⚠️  Skipping $name (empty value)."
    fi
}

# 1. GCP Secrets
echo ""
echo "--- GCP Configuration ---"
read -p "Enter GCP Project ID: " gcp_project_id
if [ -n "$gcp_project_id" ]; then
    gh secret set "GCP_PROJECT_ID" --body "$gcp_project_id"
    echo "✅ GCP_PROJECT_ID set."
fi

echo "For GCP_SA_KEY, please provide the path to your service-account.json file."
read -p "Path to service-account.json: " key_path
if [ -f "$key_path" ]; then
    # Base64 encode the key file
    base64_key=$(base64 < "$key_path")
    gh secret set "GCP_SA_KEY" --body "$base64_key"
    echo "✅ GCP_SA_KEY set."
else
    echo "⚠️  File not found: $key_path. Skipping GCP_SA_KEY."
fi

# 2. Supabase Secrets
echo ""
echo "--- Supabase Configuration ---"
set_secret "SUPABASE_ACCESS_TOKEN" "Enter Supabase Access Token"
set_secret "SUPABASE_PROJECT_REF" "Enter Supabase Project Ref (e.g., akhirugwpozlxfvtqmvj)"
set_secret "SUPABASE_DB_URL" "Enter Supabase DB URL (postgresql://postgres:...)"
set_secret "SUPABASE_URL" "Enter Supabase URL (https://...supabase.co)"
set_secret "SUPABASE_ANON_KEY" "Enter Supabase Anon Key"
set_secret "SUPABASE_SERVICE_ROLE_KEY" "Enter Supabase Service Role Key"

# 3. Service Secrets
echo ""
echo "--- Service Secrets ---"
set_secret "GEMINI_API_KEY" "Enter Gemini API Key"
set_secret "REDIS_URL" "Enter Redis URL"
set_secret "DATABASE_URL" "Enter Database URL (same as SUPABASE_DB_URL usually)"
set_secret "JWT_SECRET" "Enter JWT Secret"
set_secret "CORS_ORIGINS" "Enter CORS Origins (comma separated)"
set_secret "SLACK_WEBHOOK_URL" "Enter Slack Webhook URL (optional)"

# 4. Meta Secrets
echo ""
echo "--- Meta/Facebook Secrets ---"
set_secret "META_ACCESS_TOKEN" "Enter Meta Access Token"
set_secret "META_AD_ACCOUNT_ID" "Enter Meta Ad Account ID"
set_secret "META_APP_ID" "Enter Meta App ID"
set_secret "META_APP_SECRET" "Enter Meta App Secret"

echo ""
echo "🎉 All secrets processed!"
