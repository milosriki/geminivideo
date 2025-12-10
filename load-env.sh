#!/bin/bash
# load-env.sh - Load environment variables from .env files
# Usage: source load-env.sh

set -e

# Load .env.local first (highest priority)
if [ -f .env.local ]; then
    echo "📋 Loading .env.local..."
    export $(grep -v '^#' .env.local | xargs)
fi

# Load .env (base config)
if [ -f .env ]; then
    echo "📋 Loading .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Load supabase/.env.prod if exists
if [ -f supabase/.env.prod ]; then
    echo "📋 Loading supabase/.env.prod..."
    export $(grep -v '^#' supabase/.env.prod | xargs)
fi

echo "✅ Environment variables loaded"

