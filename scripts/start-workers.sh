#!/bin/bash
# ============================================================================
# AGENT 3: WORKER ACTIVATOR - Background Workers Startup Script
# ============================================================================
# This script starts all Celery workers for background task processing
#
# Workers configured:
# 1. ML Service Workers (HubSpot webhooks, fatigue monitoring, auto-indexing)
# 2. ML Service Beat Scheduler (periodic tasks)
# 3. Video Agent Workers (video rendering, transcoding, captioning)
# 4. Video Agent Beat Scheduler (cleanup, resource monitoring)
# 5. Flower Web UI (optional, for monitoring)
#
# Usage:
#   ./scripts/start-workers.sh           # Start all workers
#   ./scripts/start-workers.sh --ml-only  # Start only ML workers
#   ./scripts/start-workers.sh --video-only  # Start only video workers
#   ./scripts/start-workers.sh --with-flower  # Start with Flower monitoring UI
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ML_SERVICE_DIR="${PROJECT_ROOT}/services/ml-service"
VIDEO_AGENT_DIR="${PROJECT_ROOT}/services/video-agent"
REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
LOG_DIR="${PROJECT_ROOT}/logs/workers"

# Parse arguments
START_ML=true
START_VIDEO=true
START_FLOWER=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --ml-only)
            START_VIDEO=false
            shift
            ;;
        --video-only)
            START_ML=false
            shift
            ;;
        --with-flower)
            START_FLOWER=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--ml-only] [--video-only] [--with-flower]"
            exit 1
            ;;
    esac
done

# Create log directory
mkdir -p "$LOG_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        AGENT 3: WORKER ACTIVATOR - Starting Workers           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Redis connection
echo -e "${YELLOW}Checking Redis connection...${NC}"
if redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${RED}✗ Redis is not accessible at $REDIS_URL${NC}"
    echo -e "${YELLOW}Please start Redis first: docker-compose up -d redis${NC}"
    exit 1
fi
echo ""

# ============================================================================
# ML SERVICE WORKERS
# ============================================================================

if [ "$START_ML" = true ]; then
    echo -e "${BLUE}Starting ML Service Workers...${NC}"

    cd "$ML_SERVICE_DIR"

    # Start ML Celery Worker
    echo -e "${YELLOW}Starting ML Celery Worker (hubspot-webhook-events, fatigue-monitoring, budget-optimization)...${NC}"
    celery -A src.celery_app worker \
        --loglevel=info \
        --concurrency=4 \
        --queues=hubspot-webhook-events,fatigue-monitoring,budget-optimization \
        --logfile="${LOG_DIR}/ml-worker.log" \
        --pidfile="${LOG_DIR}/ml-worker.pid" \
        --detach

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ML Worker started (PID: $(cat ${LOG_DIR}/ml-worker.pid))${NC}"
    else
        echo -e "${RED}✗ Failed to start ML Worker${NC}"
    fi

    # Start ML Celery Beat Scheduler
    echo -e "${YELLOW}Starting ML Celery Beat Scheduler (periodic tasks)...${NC}"
    celery -A src.celery_app beat \
        --loglevel=info \
        --logfile="${LOG_DIR}/ml-beat.log" \
        --pidfile="${LOG_DIR}/ml-beat.pid" \
        --detach

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ML Beat Scheduler started (PID: $(cat ${LOG_DIR}/ml-beat.pid))${NC}"
    else
        echo -e "${RED}✗ Failed to start ML Beat Scheduler${NC}"
    fi

    echo ""
fi

# ============================================================================
# VIDEO AGENT WORKERS
# ============================================================================

if [ "$START_VIDEO" = true ]; then
    echo -e "${BLUE}Starting Video Agent Workers...${NC}"

    cd "$VIDEO_AGENT_DIR"

    # Start Video Render Worker (high priority)
    echo -e "${YELLOW}Starting Video Render Worker (render_queue)...${NC}"
    celery -A pro.celery_app worker \
        --loglevel=info \
        --concurrency=2 \
        --queues=render_queue \
        --hostname=render@%h \
        --logfile="${LOG_DIR}/video-render.log" \
        --pidfile="${LOG_DIR}/video-render.pid" \
        --detach

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Video Render Worker started (PID: $(cat ${LOG_DIR}/video-render.pid))${NC}"
    else
        echo -e "${RED}✗ Failed to start Video Render Worker${NC}"
    fi

    # Start Video Preview Worker
    echo -e "${YELLOW}Starting Video Preview Worker (preview_queue)...${NC}"
    celery -A pro.celery_app worker \
        --loglevel=info \
        --concurrency=4 \
        --queues=preview_queue \
        --hostname=preview@%h \
        --logfile="${LOG_DIR}/video-preview.log" \
        --pidfile="${LOG_DIR}/video-preview.pid" \
        --detach

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Video Preview Worker started (PID: $(cat ${LOG_DIR}/video-preview.pid))${NC}"
    else
        echo -e "${RED}✗ Failed to start Video Preview Worker${NC}"
    fi

    # Start Video Transcode Worker
    echo -e "${YELLOW}Starting Video Transcode Worker (transcode_queue)...${NC}"
    celery -A pro.celery_app worker \
        --loglevel=info \
        --concurrency=2 \
        --queues=transcode_queue \
        --hostname=transcode@%h \
        --logfile="${LOG_DIR}/video-transcode.log" \
        --pidfile="${LOG_DIR}/video-transcode.pid" \
        --detach

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Video Transcode Worker started (PID: $(cat ${LOG_DIR}/video-transcode.pid))${NC}"
    else
        echo -e "${RED}✗ Failed to start Video Transcode Worker${NC}"
    fi

    # Start Video Caption Worker
    echo -e "${YELLOW}Starting Video Caption Worker (caption_queue)...${NC}"
    celery -A pro.celery_app worker \
        --loglevel=info \
        --concurrency=1 \
        --queues=caption_queue \
        --hostname=caption@%h \
        --logfile="${LOG_DIR}/video-caption.log" \
        --pidfile="${LOG_DIR}/video-caption.pid" \
        --detach

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Video Caption Worker started (PID: $(cat ${LOG_DIR}/video-caption.pid))${NC}"
    else
        echo -e "${RED}✗ Failed to start Video Caption Worker${NC}"
    fi

    # Start Video Beat Scheduler
    echo -e "${YELLOW}Starting Video Beat Scheduler (cleanup, resource monitoring)...${NC}"
    celery -A pro.celery_app beat \
        --loglevel=info \
        --logfile="${LOG_DIR}/video-beat.log" \
        --pidfile="${LOG_DIR}/video-beat.pid" \
        --detach

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Video Beat Scheduler started (PID: $(cat ${LOG_DIR}/video-beat.pid))${NC}"
    else
        echo -e "${RED}✗ Failed to start Video Beat Scheduler${NC}"
    fi

    echo ""
fi

# ============================================================================
# FLOWER MONITORING UI (OPTIONAL)
# ============================================================================

if [ "$START_FLOWER" = true ]; then
    echo -e "${BLUE}Starting Flower Monitoring UI...${NC}"

    # Flower can monitor multiple Celery apps
    cd "$PROJECT_ROOT"

    celery -A services.ml-service.src.celery_app flower \
        --port=5555 \
        --broker="$REDIS_URL" \
        --logfile="${LOG_DIR}/flower.log" \
        --pidfile="${LOG_DIR}/flower.pid" \
        --detach

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Flower UI started at http://localhost:5555 (PID: $(cat ${LOG_DIR}/flower.pid))${NC}"
    else
        echo -e "${RED}✗ Failed to start Flower UI${NC}"
    fi

    echo ""
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Workers Started Successfully                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Worker Status:${NC}"

if [ "$START_ML" = true ]; then
    echo -e "  ${GREEN}✓${NC} ML Service Worker (HubSpot webhooks, fatigue monitoring, budget optimization)"
    echo -e "  ${GREEN}✓${NC} ML Beat Scheduler (runs every 6-12 hours)"
fi

if [ "$START_VIDEO" = true ]; then
    echo -e "  ${GREEN}✓${NC} Video Render Worker (high-quality video rendering)"
    echo -e "  ${GREEN}✓${NC} Video Preview Worker (fast preview generation)"
    echo -e "  ${GREEN}✓${NC} Video Transcode Worker (format conversion)"
    echo -e "  ${GREEN}✓${NC} Video Caption Worker (AI-powered captions)"
    echo -e "  ${GREEN}✓${NC} Video Beat Scheduler (cleanup & resource monitoring)"
fi

if [ "$START_FLOWER" = true ]; then
    echo -e "  ${GREEN}✓${NC} Flower Monitoring UI: http://localhost:5555"
fi

echo ""
echo -e "${BLUE}Logs:${NC} $LOG_DIR"
echo ""
echo -e "${YELLOW}To stop all workers:${NC}"
echo -e "  pkill -F ${LOG_DIR}/ml-worker.pid"
echo -e "  pkill -F ${LOG_DIR}/ml-beat.pid"
echo -e "  pkill -F ${LOG_DIR}/video-render.pid"
echo -e "  pkill -F ${LOG_DIR}/video-preview.pid"
echo -e "  pkill -F ${LOG_DIR}/video-transcode.pid"
echo -e "  pkill -F ${LOG_DIR}/video-caption.pid"
echo -e "  pkill -F ${LOG_DIR}/video-beat.pid"
echo ""
echo -e "${YELLOW}Or use the stop script:${NC}"
echo -e "  ./scripts/stop-workers.sh"
echo ""

# Create stop script
cat > "${PROJECT_ROOT}/scripts/stop-workers.sh" << 'STOP_SCRIPT'
#!/bin/bash
# Stop all Celery workers

LOG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/logs/workers"

echo "Stopping all workers..."

for pidfile in "$LOG_DIR"/*.pid; do
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        worker_name=$(basename "$pidfile" .pid)

        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping $worker_name (PID: $pid)..."
            kill "$pid"
            rm -f "$pidfile"
        else
            echo "$worker_name is not running, removing stale PID file"
            rm -f "$pidfile"
        fi
    fi
done

echo "All workers stopped."
STOP_SCRIPT

chmod +x "${PROJECT_ROOT}/scripts/stop-workers.sh"

echo -e "${GREEN}✓ Stop script created: ./scripts/stop-workers.sh${NC}"
echo ""
