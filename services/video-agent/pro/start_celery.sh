#!/bin/bash
#
# Celery Service Startup Script
#
# This script starts all Celery components for the video processing queue:
# - Redis server (if not running)
# - Celery workers (multiple types)
# - Celery beat scheduler
# - Flower monitoring dashboard
#
# Usage:
#   ./start_celery.sh [component]
#
# Components:
#   all         - Start all components (default)
#   redis       - Start Redis server only
#   worker      - Start general worker
#   worker-gpu  - Start GPU worker
#   beat        - Start beat scheduler
#   flower      - Start Flower dashboard
#   stop        - Stop all components
#   status      - Check status of all components
#

set -e

# Configuration
REDIS_PORT=6379
REDIS_URL="redis://localhost:${REDIS_PORT}/0"
CELERY_APP="services.video-agent.pro.celery_app"
PROJECT_ROOT="/home/user/geminivideo"
LOG_DIR="/var/log/celery"
PID_DIR="/var/run/celery"

# Create directories
mkdir -p "$LOG_DIR" 2>/dev/null || true
mkdir -p "$PID_DIR" 2>/dev/null || true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_redis() {
    if redis-cli -p "$REDIS_PORT" ping > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

start_redis() {
    log_info "Starting Redis server..."

    if check_redis; then
        log_warning "Redis is already running on port $REDIS_PORT"
        return 0
    fi

    if command -v redis-server > /dev/null; then
        redis-server --daemonize yes --port "$REDIS_PORT" --dir /tmp
        sleep 2

        if check_redis; then
            log_success "Redis started successfully on port $REDIS_PORT"
        else
            log_error "Failed to start Redis"
            return 1
        fi
    else
        log_error "redis-server not found. Please install Redis:"
        echo "  Ubuntu/Debian: sudo apt-get install redis-server"
        echo "  macOS: brew install redis"
        return 1
    fi
}

start_worker() {
    local worker_type="$1"
    local queue="${2:-render_queue,preview_queue,transcode_queue,caption_queue}"
    local concurrency="${3:-4}"
    local hostname="${4:-worker}"

    log_info "Starting Celery $worker_type worker..."

    cd "$PROJECT_ROOT" || exit 1

    export REDIS_URL="$REDIS_URL"
    export CELERY_BROKER_URL="$REDIS_URL"
    export CELERY_RESULT_BACKEND="$REDIS_URL"

    celery -A "$CELERY_APP" worker \
        -Q "$queue" \
        --loglevel=info \
        --concurrency="$concurrency" \
        --hostname="${hostname}@%h" \
        --pidfile="$PID_DIR/${hostname}.pid" \
        --logfile="$LOG_DIR/${hostname}.log" \
        --detach

    sleep 2

    if [ -f "$PID_DIR/${hostname}.pid" ]; then
        log_success "$worker_type worker started (PID: $(cat $PID_DIR/${hostname}.pid))"
    else
        log_error "Failed to start $worker_type worker"
        return 1
    fi
}

start_beat() {
    log_info "Starting Celery Beat scheduler..."

    cd "$PROJECT_ROOT" || exit 1

    export REDIS_URL="$REDIS_URL"
    export CELERY_BROKER_URL="$REDIS_URL"
    export CELERY_RESULT_BACKEND="$REDIS_URL"

    celery -A "$CELERY_APP" beat \
        --loglevel=info \
        --pidfile="$PID_DIR/beat.pid" \
        --logfile="$LOG_DIR/beat.log" \
        --detach

    sleep 2

    if [ -f "$PID_DIR/beat.pid" ]; then
        log_success "Beat scheduler started (PID: $(cat $PID_DIR/beat.pid))"
    else
        log_error "Failed to start Beat scheduler"
        return 1
    fi
}

start_flower() {
    local port="${1:-5555}"

    log_info "Starting Flower monitoring dashboard..."

    if ! command -v celery > /dev/null; then
        log_error "Celery not found. Please install: pip install celery[redis]"
        return 1
    fi

    cd "$PROJECT_ROOT" || exit 1

    export CELERY_BROKER_URL="$REDIS_URL"
    export CELERY_RESULT_BACKEND="$REDIS_URL"

    nohup celery -A "$CELERY_APP" flower \
        --port="$port" \
        --url_prefix=flower \
        > "$LOG_DIR/flower.log" 2>&1 &

    local flower_pid=$!
    echo "$flower_pid" > "$PID_DIR/flower.pid"

    sleep 3

    if ps -p "$flower_pid" > /dev/null; then
        log_success "Flower started on http://localhost:$port (PID: $flower_pid)"
    else
        log_error "Failed to start Flower"
        return 1
    fi
}

stop_component() {
    local component="$1"
    local pid_file="$PID_DIR/${component}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        log_info "Stopping $component (PID: $pid)..."

        if kill "$pid" 2>/dev/null; then
            sleep 2
            rm -f "$pid_file"
            log_success "$component stopped"
        else
            log_warning "$component process not found (stale PID file)"
            rm -f "$pid_file"
        fi
    else
        log_warning "$component is not running (no PID file)"
    fi
}

stop_all() {
    log_info "Stopping all Celery components..."

    # Stop workers
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            component=$(basename "$pid_file" .pid)
            stop_component "$component"
        fi
    done

    # Kill any remaining celery processes
    pkill -f "celery.*$CELERY_APP" 2>/dev/null || true

    log_success "All Celery components stopped"
}

show_status() {
    log_info "Checking component status..."
    echo ""

    # Redis status
    if check_redis; then
        log_success "Redis: Running on port $REDIS_PORT"
    else
        log_error "Redis: Not running"
    fi

    # Check each component
    for component in worker worker-gpu worker-preview beat flower; do
        pid_file="$PID_DIR/${component}.pid"
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            if ps -p "$pid" > /dev/null 2>&1; then
                log_success "$component: Running (PID: $pid)"
            else
                log_warning "$component: Not running (stale PID)"
            fi
        else
            log_warning "$component: Not running"
        fi
    done

    # Celery status
    echo ""
    log_info "Celery worker status:"
    cd "$PROJECT_ROOT" || exit 1
    export REDIS_URL="$REDIS_URL"
    celery -A "$CELERY_APP" inspect active 2>/dev/null || log_warning "No active workers found"
}

show_logs() {
    local component="${1:-worker}"
    local log_file="$LOG_DIR/${component}.log"

    if [ -f "$log_file" ]; then
        log_info "Showing logs for $component (last 50 lines):"
        tail -n 50 "$log_file"
    else
        log_error "Log file not found: $log_file"
    fi
}

start_all() {
    log_info "Starting all Celery components..."
    echo ""

    # Start Redis
    start_redis || exit 1
    echo ""

    # Start general worker
    start_worker "general" "render_queue,preview_queue,transcode_queue,caption_queue" 4 "worker" || exit 1
    echo ""

    # Start GPU worker (if GPU available)
    if command -v nvidia-smi > /dev/null 2>&1; then
        log_info "GPU detected, starting GPU worker..."
        start_worker "GPU" "render_queue,transcode_queue" 1 "worker-gpu" || true
        echo ""
    else
        log_warning "No GPU detected, skipping GPU worker"
        echo ""
    fi

    # Start preview worker
    start_worker "preview" "preview_queue,caption_queue" 4 "worker-preview" || exit 1
    echo ""

    # Start beat
    start_beat || exit 1
    echo ""

    # Start flower
    if command -v celery > /dev/null && celery --help | grep -q flower; then
        start_flower 5555 || log_warning "Failed to start Flower (optional)"
    else
        log_warning "Flower not installed. Install with: pip install flower"
    fi

    echo ""
    log_success "All components started successfully!"
    echo ""
    echo "Access points:"
    echo "  - Flower Dashboard: http://localhost:5555"
    echo "  - Redis: localhost:$REDIS_PORT"
    echo ""
    echo "Logs location: $LOG_DIR"
    echo "PID files: $PID_DIR"
    echo ""
    echo "Useful commands:"
    echo "  ./start_celery.sh status    - Check component status"
    echo "  ./start_celery.sh stop      - Stop all components"
    echo "  ./start_celery.sh logs      - View worker logs"
}

# Main script
case "${1:-all}" in
    redis)
        start_redis
        ;;
    worker)
        start_redis
        start_worker "general" "render_queue,preview_queue,transcode_queue,caption_queue" 4 "worker"
        ;;
    worker-gpu)
        start_redis
        start_worker "GPU" "render_queue,transcode_queue" 1 "worker-gpu"
        ;;
    worker-preview)
        start_redis
        start_worker "preview" "preview_queue,caption_queue" 4 "worker-preview"
        ;;
    beat)
        start_redis
        start_beat
        ;;
    flower)
        start_redis
        start_flower 5555
        ;;
    stop)
        stop_all
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "${2:-worker}"
        ;;
    all)
        start_all
        ;;
    *)
        echo "Usage: $0 [component]"
        echo ""
        echo "Components:"
        echo "  all            - Start all components (default)"
        echo "  redis          - Start Redis server only"
        echo "  worker         - Start general worker"
        echo "  worker-gpu     - Start GPU worker"
        echo "  worker-preview - Start preview worker"
        echo "  beat           - Start beat scheduler"
        echo "  flower         - Start Flower dashboard"
        echo "  stop           - Stop all components"
        echo "  status         - Check status of all components"
        echo "  logs [name]    - Show logs for component"
        exit 1
        ;;
esac
