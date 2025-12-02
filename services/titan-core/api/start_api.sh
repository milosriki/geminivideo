#!/bin/bash
# Start Titan-Core Master API

# Set environment variables
export GEMINI_API_KEY="${GEMINI_API_KEY:-your_gemini_key_here}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-your_openai_key_here}"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-your_anthropic_key_here}"

export API_HOST="${API_HOST:-0.0.0.0}"
export API_PORT="${API_PORT:-8000}"
export DEBUG="${DEBUG:-true}"

export OUTPUT_DIR="/tmp/titan-core/outputs"
export CACHE_DIR="/tmp/titan-core/cache"

# Create directories
mkdir -p "$OUTPUT_DIR"
mkdir -p "$CACHE_DIR"

echo "🚀 Starting Titan-Core Master API..."
echo "📍 Host: $API_HOST:$API_PORT"
echo "🔧 Debug mode: $DEBUG"
echo ""
echo "📖 Docs available at: http://localhost:$API_PORT/docs"
echo ""

# Run the API
cd "$(dirname "$0")"
python main.py
