#!/bin/bash
# Quick verification script for worker setup

echo "=== AGENT 3: WORKER SYSTEM VERIFICATION ==="
echo ""

# Check if required files exist
echo "Checking files..."
files=(
    "services/ml-service/src/celery_app.py"
    "services/ml-service/src/celery_tasks.py"
    "services/ml-service/src/celery_beat_tasks.py"
    "services/video-agent/pro/celery_app.py"
    "scripts/start-workers.sh"
    "docker-compose.workers.yml"
    "WORKERS_README.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file MISSING"
    fi
done

echo ""
echo "Checking requirements..."
if grep -q "celery" services/ml-service/requirements.txt; then
    echo "✓ Celery in ml-service requirements"
else
    echo "✗ Celery NOT in ml-service requirements"
fi

if grep -q "celery" services/video-agent/requirements.txt; then
    echo "✓ Celery in video-agent requirements"
else
    echo "✗ Celery NOT in video-agent requirements"
fi

echo ""
echo "=== SETUP COMPLETE ==="
echo ""
echo "To start workers:"
echo "  Local: ./scripts/start-workers.sh"
echo "  Docker: docker-compose -f docker-compose.workers.yml up -d"
echo ""
echo "Documentation: ./WORKERS_README.md"
