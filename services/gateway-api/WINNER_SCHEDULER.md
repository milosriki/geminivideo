# Winner Detection Scheduler

**Agent 02: Scheduled Winner Check**

## Overview

The Winner Detection Scheduler automatically identifies winning ads every 6 hours based on performance thresholds and indexes them in the ML service's FAISS vector database for similarity search and pattern analysis.

## Features

- **Automated Detection**: Runs every 6 hours (configurable via cron schedule)
- **Performance-Based Criteria**: Detects winners based on ROAS, CTR, spend, and runtime
- **ML Integration**: Automatically indexes winners in FAISS for similarity search
- **Webhook Notifications**: Sends alerts when new winners are detected
- **Manual Triggers**: Can be triggered via API endpoint or programmatically
- **Graceful Shutdown**: Properly stops scheduler on SIGTERM/SIGINT

## Files Created

### 1. `/src/routes/winners.ts`
Winner detection and management routes:
- `POST /api/v1/winners/detect` - Manually trigger winner detection
- `GET /api/v1/winners/list` - List all detected winners
- `GET /api/v1/winners/:id` - Get detailed winner information
- `POST /api/v1/winners/:id/replicate` - Create copies of winning ads

### 2. `/src/jobs/winner-scheduler.ts`
Scheduled job implementation:
- Cron-based scheduler (default: every 6 hours)
- Winner detection logic
- ML service integration for FAISS indexing
- Webhook notifications
- Scheduler state management

### 3. `.env.winner-scheduler.example`
Environment variable configuration template

## Configuration

### Environment Variables

```bash
# Enable/disable scheduler
ENABLE_WINNER_SCHEDULER=true

# Cron schedule (default: every 6 hours)
WINNER_CHECK_SCHEDULE=0 */6 * * *

# Winner detection criteria
WINNER_MIN_ROAS=2.0          # Minimum 2x return on ad spend
WINNER_MIN_CTR=0.02          # Minimum 2% click-through rate
WINNER_MIN_SPEND=100         # Minimum $100 spend
WINNER_MIN_HOURS=24          # Must run for 24 hours

# Notifications
WINNER_WEBHOOK_URL=https://your-webhook.com/winners
WINNER_ALERT_EMAIL=alerts@yourcompany.com
```

### Cron Schedule Examples

```bash
# Every 6 hours (default)
WINNER_CHECK_SCHEDULE=0 */6 * * *

# Every 4 hours
WINNER_CHECK_SCHEDULE=0 */4 * * *

# Every day at 2am
WINNER_CHECK_SCHEDULE=0 2 * * *

# Every hour
WINNER_CHECK_SCHEDULE=0 * * * *
```

## API Endpoints

### Manual Winner Detection

```bash
POST /api/v1/winners/detect
Content-Type: application/json

{
  "minROAS": 2.0,
  "minCTR": 0.02,
  "minSpend": 100,
  "minHours": 24
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Detected 5 winning ads",
  "criteria": {
    "minROAS": 2.0,
    "minCTR": 0.02,
    "minSpend": 100,
    "minHours": 24
  },
  "winners": [
    {
      "ad_id": "uuid",
      "campaign_name": "Campaign Name",
      "video_title": "Video Title",
      "arc_name": "fitness_transformation",
      "performance": {
        "ctr": 0.025,
        "roas": 3.5,
        "spend": 250,
        "impressions": 10000,
        "clicks": 250,
        "conversions": 15
      },
      "created_at": "2025-12-13T00:00:00Z"
    }
  ],
  "indexed": [
    {
      "ad_id": "uuid",
      "indexed": true,
      "similarity_index_id": "faiss-index-123"
    }
  ],
  "summary": {
    "total_detected": 5,
    "total_indexed": 5,
    "total_failed": 0
  }
}
```

### List Winners

```bash
GET /api/v1/winners/list?limit=20&offset=0&minROAS=2.0&minCTR=0.02
```

### Get Winner Details

```bash
GET /api/v1/winners/:id
```

### Replicate Winner

```bash
POST /api/v1/winners/:id/replicate
Content-Type: application/json

{
  "variations": 3,
  "campaign_id": "optional-campaign-uuid",
  "modify_arc": false,
  "modify_clips": false
}
```

## How It Works

### 1. Scheduled Detection

Every 6 hours (configurable), the scheduler:

1. Queries the database for ads meeting winner criteria:
   - ROAS ≥ 2.0
   - CTR ≥ 2%
   - Spend ≥ $100
   - Running for ≥ 24 hours

2. For each winner detected:
   - Extracts performance metrics
   - Indexes in ML service's FAISS database
   - Logs the detection

3. Sends webhook notifications if configured

### 2. Winner Detection Query

```sql
SELECT
  a.ad_id,
  a.campaign_id,
  a.arc_name,
  c.name as campaign_name,
  v.title as video_title,
  SUM(pm.impressions) as total_impressions,
  SUM(pm.clicks) as total_clicks,
  SUM(pm.conversions) as total_conversions,
  SUM(pm.spend) as total_spend,
  (SUM(pm.clicks)::FLOAT / SUM(pm.impressions)) as actual_ctr,
  ((SUM(pm.conversions) * 50.0) / SUM(pm.spend)) as actual_roas
FROM ads a
LEFT JOIN campaigns c ON a.campaign_id = c.id
LEFT JOIN videos v ON a.video_id::text = v.id::text
LEFT JOIN performance_metrics pm ON v.id = pm.video_id
WHERE a.created_at <= NOW() - INTERVAL '24 hours'
  AND a.approved = true
  AND a.status IN ('approved', 'published')
GROUP BY a.ad_id, c.id, v.id
HAVING
  SUM(pm.spend) >= 100
  AND (SUM(pm.clicks)::FLOAT / NULLIF(SUM(pm.impressions), 0)) >= 0.02
  AND ((SUM(pm.conversions) * 50.0) / NULLIF(SUM(pm.spend), 0)) >= 2.0
ORDER BY actual_roas DESC, actual_ctr DESC
```

### 3. FAISS Indexing

Winners are indexed in the ML service's FAISS vector database:

```bash
POST http://ml-service:8003/api/ml/winners/index
{
  "ad_id": "uuid",
  "metadata": {
    "campaign_name": "Campaign",
    "video_title": "Video Title",
    "arc_name": "fitness_transformation",
    "actual_ctr": 0.025,
    "actual_roas": 3.5,
    "total_spend": 250,
    "detected_at": "2025-12-13T00:00:00Z"
  }
}
```

## Integration

### Server Startup

The scheduler automatically starts when the gateway-api boots:

```typescript
// In src/index.ts
const server = app.listen(PORT, async () => {
  // ... other initialization ...

  // Initialize Winner Detection Scheduler (Agent 02)
  try {
    console.log('🚀 Starting winner detection scheduler...');
    const { startWinnerScheduler } = require('./jobs/winner-scheduler');
    startWinnerScheduler(pgPool);
    console.log('✅ Winner detection scheduler started (runs every 6 hours)');
  } catch (error) {
    console.error('❌ Failed to start winner detection scheduler:', error);
  }
});
```

### Graceful Shutdown

The scheduler stops gracefully on shutdown:

```typescript
process.on('SIGTERM', async () => {
  const { stopWinnerScheduler } = require('./jobs/winner-scheduler');
  stopWinnerScheduler();
  // ... other shutdown logic ...
});
```

## Monitoring

### Check Scheduler Status

Programmatically check the scheduler status:

```typescript
import { getWinnerSchedulerStatus } from './jobs/winner-scheduler';

const status = getWinnerSchedulerStatus();
console.log(status);
// {
//   enabled: true,
//   schedule: '0 */6 * * *',
//   running: true,
//   lastRun: '2025-12-13T06:00:00Z',
//   lastRunStatus: 'success',
//   winnersDetected: 5,
//   config: { ... }
// }
```

### Logs

The scheduler logs all activities:

```
[2025-12-13T06:00:00Z] INFO: 🔍 Starting scheduled winner detection...
[2025-12-13T06:00:01Z] INFO: ✅ Scheduled winner detection complete (winnersFound: 5, duration: 1234ms)
[2025-12-13T06:00:01Z] INFO: Indexed 5/5 winners in ML service
[2025-12-13T06:00:01Z] INFO: Notifying about 5 new winners
[2025-12-13T06:00:02Z] INFO: Winner webhook notification sent successfully
```

## Manual Trigger

Trigger winner detection outside of the schedule:

```typescript
import { triggerWinnerDetection } from './jobs/winner-scheduler';

// Manually trigger detection
await triggerWinnerDetection(pgPool);
```

## Webhook Payload

When winners are detected, the scheduler sends this webhook:

```json
{
  "event": "winners_detected",
  "count": 5,
  "winners": [
    {
      "ad_id": "uuid",
      "campaign_name": "Campaign Name",
      "video_title": "Video Title",
      "arc_name": "fitness_transformation",
      "ctr": 0.025,
      "roas": 3.5,
      "spend": 250,
      "detected_at": "2025-12-13T06:00:00Z"
    }
  ],
  "timestamp": "2025-12-13T06:00:00Z"
}
```

## Success Criteria

✅ **All criteria met:**

1. ✅ Scheduler starts when server boots
2. ✅ Runs detection every 6 hours (configurable via env var)
3. ✅ Detects winners based on performance thresholds
4. ✅ Indexes winners in ML service FAISS database
5. ✅ Logs all detection results
6. ✅ Sends webhook notifications for new winners
7. ✅ Can be triggered manually via API
8. ✅ Gracefully shuts down on SIGTERM/SIGINT

## Testing

### Manual Test

1. Set environment variables:
```bash
export ENABLE_WINNER_SCHEDULER=true
export WINNER_CHECK_SCHEDULE="*/5 * * * *"  # Every 5 minutes for testing
export WINNER_MIN_ROAS=1.5
export WINNER_MIN_CTR=0.01
export WINNER_MIN_SPEND=50
```

2. Start the server:
```bash
npm run dev
```

3. Watch the logs for scheduled runs every 5 minutes

### API Test

```bash
# Trigger manual detection
curl -X POST http://localhost:8000/api/v1/winners/detect \
  -H "Content-Type: application/json" \
  -d '{
    "minROAS": 2.0,
    "minCTR": 0.02,
    "minSpend": 100,
    "minHours": 24
  }'

# List winners
curl http://localhost:8000/api/v1/winners/list?limit=10

# Get winner details
curl http://localhost:8000/api/v1/winners/{ad_id}

# Replicate winner
curl -X POST http://localhost:8000/api/v1/winners/{ad_id}/replicate \
  -H "Content-Type: application/json" \
  -d '{
    "variations": 3,
    "modify_arc": false
  }'
```

## Troubleshooting

### Scheduler Not Starting

Check logs for errors:
```bash
grep "winner.*scheduler" logs/combined.log
```

Verify environment variable:
```bash
echo $ENABLE_WINNER_SCHEDULER
```

### No Winners Detected

Lower the thresholds for testing:
```bash
export WINNER_MIN_ROAS=1.0
export WINNER_MIN_CTR=0.001
export WINNER_MIN_SPEND=1
export WINNER_MIN_HOURS=1
```

### FAISS Indexing Fails

Check ML service connectivity:
```bash
curl http://localhost:8003/health
```

Verify ML service URL:
```bash
echo $ML_SERVICE_URL
```

## Future Enhancements

- Email notification support
- Slack/Discord integration
- Winner performance trending
- Automatic budget reallocation to winners
- A/B test winner promotion
- Winner similarity search API
- Dashboard widget for winner stats
