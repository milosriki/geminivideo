#!/bin/bash
# Quick Start Script for Knowledge Base Hot-Reload System
# Agent 14: Knowledge Base Hot-Reload Engineer

set -e  # Exit on error

echo "=========================================="
echo "Knowledge Base Hot-Reload System"
echo "Quick Start Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}Step 1: Checking Python environment...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"
echo ""

echo -e "${BLUE}Step 2: Installing dependencies...${NC}"
pip3 install fastapi uvicorn pydantic httpx 2>&1 | grep -i "successfully installed" || echo "Dependencies already installed"
echo -e "${GREEN}✓ Dependencies ready${NC}"
echo ""

echo -e "${BLUE}Step 3: Loading sample data...${NC}"
python3 load_sample_data.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Sample data loaded${NC}"
else
    echo -e "${RED}✗ Failed to load sample data${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}Step 4: Running example usage...${NC}"
python3 example_usage.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Examples completed successfully${NC}"
else
    echo -e "${RED}✗ Examples failed${NC}"
    exit 1
fi
echo ""

echo "=========================================="
echo -e "${GREEN}✓ Quick start completed successfully!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start the API server:"
echo "   python3 api.py"
echo ""
echo "2. Access the API:"
echo "   http://localhost:8004"
echo ""
echo "3. View API docs:"
echo "   http://localhost:8004/docs"
echo ""
echo "4. Integrate with frontend:"
echo "   Set VITE_KNOWLEDGE_API_URL=http://localhost:8004"
echo ""
echo "For more information, see README.md"
echo ""
