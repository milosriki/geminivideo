#!/bin/bash

# Ensure we are in the correct directory
cd "$(dirname "$0")"

# Set PYTHONPATH to include the current directory so imports work
export PYTHONPATH=$PYTHONPATH:.

# Check for python3.13 availability (more stable than 3.14 for some libs)
if command -v python3.13 &> /dev/null; then
    PYTHON_CMD="python3.13"
else
    PYTHON_CMD="python3"
fi

echo "🚀 Running Titan Orchestrator with $PYTHON_CMD..."
$PYTHON_CMD orchestrator.py
