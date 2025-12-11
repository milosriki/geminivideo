#!/bin/bash
set -e

echo "🚀 Setting up LangGraph Agent Server..."

# 1. Install uv if missing (Fast Python package manager)
if ! command -v uv &> /dev/null; then
    if [ -f "$HOME/.cargo/bin/uv" ]; then
        export PATH="$HOME/.cargo/bin:$PATH"
    else
        echo "📦 Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    fi
fi

# 2. Navigate to the correct directory
cd "$(dirname "$0")"

# 3. Force Python 3.12 (Bypasses the Python 3.14 incompatibility)
echo "🐍 Installing Python 3.12 (to fix compatibility issues)..."
uv python install 3.12

# 4. Create virtual environment with Python 3.12
if [ ! -d ".venv" ]; then
    echo "🛠️ Creating virtual environment..."
    uv venv --python 3.12
fi

# 5. Install dependencies
echo "📥 Installing dependencies..."
uv pip install -U "langgraph-cli[inmem]"

# 6. Start the server
echo "✅ Starting LangGraph Server..."
echo "👉 Open LangSmith Studio and connect to: http://localhost:2024"
export PYTHONPATH=$PYTHONPATH:$(pwd)/../..
uv run langgraph dev
