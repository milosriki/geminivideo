#!/bin/bash
#
# Auto-Scaler Cron Job
# Agent 47 - Intelligent Budget Auto-Scaling
#
# Schedule this to run hourly:
# 0 * * * * /path/to/cron_auto_scaler.sh
#

set -e

# Change to ml-service directory
cd "$(dirname "$0")"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables
export DATABASE_URL="${DATABASE_URL:-postgresql://geminivideo:geminivideo@localhost:5432/geminivideo}"
export META_ACCESS_TOKEN="${META_ACCESS_TOKEN:-}"
export META_AD_ACCOUNT_ID="${META_AD_ACCOUNT_ID:-}"

# Log file
LOG_DIR="/var/log/geminivideo"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/auto_scaler.log"

echo "========================================" >> "$LOG_FILE"
echo "Auto-Scaler Run: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Run optimizer
python3 src/auto_scaler_scheduler.py --mode optimize >> "$LOG_FILE" 2>&1

# Exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Auto-scaler completed successfully" >> "$LOG_FILE"
else
    echo "❌ Auto-scaler failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"

exit $EXIT_CODE
