#!/bin/bash
# ML Model Retraining Cron Job
# Agent 10 - Investment-grade model retraining automation
#
# This script should be run daily to check model accuracy and retrain if needed
#
# To schedule this cron job:
# 1. Make this script executable: chmod +x /path/to/cron_retrain.sh
# 2. Add to crontab: crontab -e
# 3. Add this line to run daily at 2 AM:
#    0 2 * * * /path/to/cron_retrain.sh >> /var/log/ml-retrain.log 2>&1
#
# Or use Cloud Scheduler / Kubernetes CronJob for production

# Configuration
ML_SERVICE_URL="${ML_SERVICE_URL:-http://localhost:8003}"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
LOG_FILE="${LOG_FILE:-/var/log/ml-retrain.log}"

echo "========================================="
echo "ML Model Retraining Check - $(date)"
echo "========================================="

# Call the check-retrain endpoint
response=$(curl -s -w "\n%{http_code}" -X POST "${ML_SERVICE_URL}/api/ml/check-retrain")
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

echo "HTTP Status: $http_code"
echo "Response: $body"

# Parse the response
status=$(echo "$body" | jq -r '.status' 2>/dev/null || echo "unknown")

if [ "$http_code" -eq 200 ]; then
    echo "✅ Check completed successfully"

    case "$status" in
        "retrained")
            samples=$(echo "$body" | jq -r '.samples' 2>/dev/null || echo "unknown")
            test_r2=$(echo "$body" | jq -r '.metrics.test_r2' 2>/dev/null || echo "unknown")
            echo "✅ Model retrained with $samples samples (R²: $test_r2)"

            # Send success notification to Slack if configured
            if [ -n "$SLACK_WEBHOOK_URL" ]; then
                curl -X POST "$SLACK_WEBHOOK_URL" \
                    -H 'Content-Type: application/json' \
                    -d "{\"text\":\"✅ ML Model Retrained: $samples samples, R²: $test_r2\"}"
            fi
            ;;
        "no_retrain_needed")
            mae=$(echo "$body" | jq -r '.current_accuracy.ctr_mae' 2>/dev/null || echo "unknown")
            echo "✅ Model accuracy acceptable (MAE: $mae)"
            ;;
        "insufficient_data")
            count=$(echo "$body" | jq -r '.count' 2>/dev/null || echo "unknown")
            echo "⚠️  Insufficient training data: $count samples"
            ;;
        *)
            echo "⚠️  Unknown status: $status"
            ;;
    esac
else
    echo "❌ Error: HTTP $http_code"

    # Send error notification to Slack if configured
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"❌ ML Retraining Check Failed: HTTP $http_code\"}"
    fi

    exit 1
fi

echo "========================================="
echo ""
