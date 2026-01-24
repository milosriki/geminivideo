#!/bin/bash

# setup-vercel-env.sh
# Script to set up Vercel Environment Variables
# Usage: ./scripts/setup-vercel-env.sh

echo "🚀 Setting up Vercel Environment Variables..."

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Please install it with 'npm i -g vercel'."
    exit 1
fi

# Function to set env var
set_env() {
    local key=$1
    local value=$2
    local envs=${3:-"production development preview"}
    
    if [ -z "$value" ]; then
        echo "⚠️  Skipping $key (empty value)"
        return
    fi

    echo "Setting $key..."
    for env in $envs; do
        echo "$value" | vercel env add "$key" "$env" --force
    done
}

echo "--- Supabase Configuration ---"
read -p "Enter Supabase URL: " supabase_url
read -p "Enter Supabase Anon Key: " supabase_anon_key

set_env "VITE_SUPABASE_URL" "$supabase_url"
set_env "VITE_SUPABASE_ANON_KEY" "$supabase_anon_key"

echo "--- Gateway Configuration ---"
read -p "Enter Gateway URL (e.g., https://gateway-api-...): " gateway_url
set_env "VITE_GATEWAY_URL" "$gateway_url"

echo "🎉 Vercel environment variables setup complete!"
echo "💡 You may need to redeploy your project for changes to take effect."
