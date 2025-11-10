#!/bin/bash
# Development startup script for AI Ad Intelligence Suite
# This script starts all backend services locally for development

set -e

echo "🚀 Starting AI Ad Intelligence Suite - Development Mode"
echo "========================================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"

# Build TypeScript services
echo -e "\n${BLUE}Building TypeScript services...${NC}"

cd services/gateway-api
if [ ! -d "node_modules" ]; then
    echo "Installing gateway-api dependencies..."
    npm install
fi
npm run build
cd ../..

cd services/meta-publisher
if [ ! -d "node_modules" ]; then
    echo "Installing meta-publisher dependencies..."
    npm install
fi
npm run build
cd ../..

echo -e "${GREEN}✓ TypeScript services built${NC}"

# Install Python dependencies
echo -e "\n${BLUE}Setting up Python services...${NC}"

cd services/video-agent
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
deactivate
cd ../..

cd services/drive-intel
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
deactivate
cd ../..

echo -e "${GREEN}✓ Python services ready${NC}"

# Create data directory if it doesn't exist
mkdir -p data/input

echo -e "\n${GREEN}✓ All services are ready!${NC}"
echo ""
echo "To start the services, run these commands in separate terminals:"
echo ""
echo "  Terminal 1 - Gateway API:"
echo "    cd services/gateway-api"
echo "    VIDEO_AGENT_URL=http://localhost:8001 DRIVE_INTEL_URL=http://localhost:8002 META_PUBLISHER_URL=http://localhost:8003 WEIGHTS_PATH=../../shared/config/weights.yaml PORT=8080 node dist/index.js"
echo ""
echo "  Terminal 2 - Video Agent:"
echo "    cd services/video-agent"
echo "    source venv/bin/activate"
echo "    uvicorn main:app --host 0.0.0.0 --port 8001"
echo ""
echo "  Terminal 3 - Drive Intel:"
echo "    cd services/drive-intel"
echo "    source venv/bin/activate"
echo "    uvicorn main:app --host 0.0.0.0 --port 8002"
echo ""
echo "  Terminal 4 - Meta Publisher:"
echo "    cd services/meta-publisher"
echo "    PORT=8003 node dist/index.js"
echo ""
echo "  Terminal 5 - Frontend (optional):"
echo "    cd frontend"
echo "    npm install"
echo "    npm run dev"
echo ""
echo "Then visit:"
echo "  - Gateway API: http://localhost:8080"
echo "  - Frontend: http://localhost:5173"
echo ""
