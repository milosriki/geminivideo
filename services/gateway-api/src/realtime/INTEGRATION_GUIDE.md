# Real-time Streaming Integration Guide

## Quick Integration Steps

### 1. Backend Integration

The real-time infrastructure is already integrated into the main Express app (`src/index.ts`). It automatically initializes on startup.

**No additional setup needed!**

### 2. Publish Events from Your Services

Use the channel manager to publish events to subscribed clients:

```typescript
import { getChannelManager } from './realtime';

// Example: Publishing job progress
const channelManager = getChannelManager();

await channelManager.publish(
  { type: 'job_progress', id: jobId },
  {
    type: 'job_progress',
    jobId,
    status: 'processing',
    stage: 'rendering',
    progress: 0.5,
    message: 'Rendering frame 500/1000',
    timestamp: new Date().toISOString()
  }
);
```

### 3. Use in Existing Routes

**Example: Add streaming to video generation**

```typescript
// In your existing video generation endpoint
import { getChannelManager } from '../realtime';

app.post('/api/generate-video', async (req, res) => {
  const jobId = uuid();
  const channelManager = getChannelManager();

  // Start async job
  processVideoJob(jobId, async (progress) => {
    // Publish progress updates
    await channelManager.publish(
      { type: 'video_render', id: jobId },
      {
        type: 'video_render_progress',
        jobId,
        currentFrame: progress.frame,
        totalFrames: progress.total,
        progress: progress.percent,
        fps: 30,
        stage: progress.stage,
        timestamp: new Date().toISOString()
      }
    );
  });

  res.json({ jobId, websocketUrl: `/ws?jobId=${jobId}` });
});
```

### 4. Frontend Integration

**Step 1: Add the hooks to your component**

```typescript
import { useRenderProgressStream } from '@/hooks/useSSE';

function VideoGenerationPage() {
  const [jobId, setJobId] = useState<string | null>(null);

  const {
    progress,
    stage,
    currentFrame,
    totalFrames,
    estimatedTime
  } = useRenderProgressStream(jobId);

  const handleStartGeneration = async () => {
    const response = await fetch('/api/generate-video', {
      method: 'POST',
      body: JSON.stringify({ /* params */ })
    });
    const data = await response.json();
    setJobId(data.jobId); // Automatically starts streaming!
  };

  return (
    <div>
      <button onClick={handleStartGeneration}>Generate Video</button>

      {jobId && (
        <div>
          <h3>Generating Video...</h3>
          <div>Stage: {stage}</div>
          <div>Frame: {currentFrame} / {totalFrames}</div>
          <div>Progress: {(progress * 100).toFixed(1)}%</div>
          <div>ETA: {Math.round(estimatedTime)}s</div>

          <div className="progress-bar">
            <div style={{ width: `${progress * 100}%` }} />
          </div>
        </div>
      )}
    </div>
  );
}
```

**Step 2: That's it! No complex setup needed.**

## Integration Examples

### Example 1: AI Council Streaming

**Backend (already implemented in `/routes/streaming.ts`)**
```
GET /api/stream/council-score?videoUrl=X&transcript=Y
```

**Frontend**
```typescript
import { useCouncilScoreStream } from '@/hooks/useSSE';

function EvaluationPage() {
  const {
    stages,
    currentStage,
    finalScore,
    startStreaming
  } = useCouncilScoreStream(videoUrl, transcript);

  return (
    <div>
      <button onClick={startStreaming}>Evaluate</button>

      {Object.entries(stages).map(([model, data]) => (
        <div key={model}>
          <h4>{model}</h4>
          <p>{data.thinking}</p>
          {data.score && <p>Score: {data.score}</p>}
        </div>
      ))}

      {finalScore && (
        <div>Final Score: {finalScore.composite}</div>
      )}
    </div>
  );
}
```

### Example 2: Real-time Campaign Metrics

**Backend (already implemented in `/routes/streaming.ts`)**
```
GET /api/stream/campaign-metrics/:campaignId
```

**Frontend**
```typescript
import { useCampaignMetricsStream } from '@/hooks/useSSE';

function CampaignDashboard({ campaignId }) {
  const {
    metrics,
    change,
    startStreaming,
    stopStreaming
  } = useCampaignMetricsStream(campaignId);

  return (
    <div>
      <button onClick={startStreaming}>Start Live Updates</button>
      <button onClick={stopStreaming}>Stop</button>

      {metrics && (
        <div>
          <div>Impressions: {metrics.impressions} (+{change.impressions})</div>
          <div>Clicks: {metrics.clicks} (+{change.clicks})</div>
          <div>CTR: {(metrics.ctr * 100).toFixed(2)}%</div>
          <div>ROAS: {metrics.roas.toFixed(2)}x</div>
        </div>
      )}
    </div>
  );
}
```

### Example 3: Real-time Alerts

**Backend - Publish alerts**
```typescript
import { getChannelManager } from './realtime';
import { createAlertEvent } from './realtime/events';

// When alert condition detected
const alert = createAlertEvent(
  'warning',
  'performance',
  'High CPC Detected',
  'Campaign CPC exceeded $5.00 threshold',
  {
    actionRequired: true,
    entityId: campaignId,
    entityType: 'campaign'
  }
);

await channelManager.publish(
  { type: 'alerts', userId: userId },
  alert
);
```

**Frontend**
```typescript
import { useRealtimeAlerts } from '@/hooks/useWebSocket';

function AlertsWidget({ userId }) {
  const { alerts, dismissAlert } = useRealtimeAlerts(userId);

  return (
    <div>
      {alerts.map(alert => (
        <div key={alert.alertId} className={`alert-${alert.severity}`}>
          <h4>{alert.title}</h4>
          <p>{alert.message}</p>
          <button onClick={() => dismissAlert(alert.alertId)}>
            Dismiss
          </button>
        </div>
      ))}
    </div>
  );
}
```

## Testing Your Integration

### 1. Start the Backend
```bash
cd /home/user/geminivideo/services/gateway-api
npm start
```

Should see:
```
Gateway API listening on port 8000
🚀 Initializing real-time infrastructure...
✅ Channel manager initialized
✅ WebSocket server initialized on /ws
✅ SSE manager initialized
🎉 Real-time infrastructure ready!
```

### 2. Test SSE Endpoint
```bash
# Test council score streaming
curl -N "http://localhost:8000/api/stream/council-score?videoUrl=test&transcript=hello"

# Test render progress
curl -N "http://localhost:8000/api/stream/render-progress/test_job_123"
```

### 3. Test WebSocket
```bash
# Install wscat
npm install -g wscat

# Connect
wscat -c "ws://localhost:8000/ws?userId=test"

# Should receive:
# {"type":"connected","message":"Connected to real-time service",...}
```

### 4. Check Stats
```bash
curl http://localhost:8000/api/realtime/stats
```

## Common Integration Patterns

### Pattern 1: Job-Based Streaming

Use for: Video generation, rendering, processing

```typescript
// 1. Create job
const { jobId } = await createJob(params);

// 2. Subscribe to progress
const { progress, status } = useJobProgress(jobId);

// 3. Backend publishes updates
channelManager.publish(
  { type: 'job_progress', id: jobId },
  progressEvent
);
```

### Pattern 2: Entity-Based Streaming

Use for: Campaign metrics, A/B tests, live stats

```typescript
// 1. Subscribe to entity
const { metrics } = useLiveMetrics(campaignId, 'campaign');

// 2. Backend publishes changes
channelManager.publish(
  { type: 'live_metrics', id: campaignId },
  metricEvent
);
```

### Pattern 3: User-Based Streaming

Use for: Alerts, notifications, personal updates

```typescript
// 1. Subscribe to user channel
const { alerts } = useRealtimeAlerts(userId);

// 2. Backend sends to specific user
channelManager.publish(
  { type: 'alerts', userId: userId },
  alertEvent
);
```

## Troubleshooting

### "SSE connection closes immediately"

**Check:**
- Server is running: `curl http://localhost:8000/health`
- SSE endpoint exists: `curl -N http://localhost:8000/api/stream/...`
- CORS headers are set (already configured)
- Proxy buffering disabled (add to nginx if needed)

**Solution:**
```nginx
# In nginx.conf (if using nginx)
location /api/stream {
    proxy_pass http://localhost:8000;
    proxy_buffering off;
    proxy_set_header X-Accel-Buffering no;
}
```

### "WebSocket connection refused"

**Check:**
- Server listening on correct port
- WebSocket path is `/ws`
- No firewall blocking

**Solution:**
```bash
# Test locally
wscat -c "ws://localhost:8000/ws"

# If remote
wscat -c "wss://your-domain.com/ws"
```

### "No events received"

**Check:**
- Channel name matches subscription
- Events are being published (check logs)
- Redis is connected (check `/api/realtime/stats`)

**Debug:**
```bash
# Watch Redis channels
redis-cli
> SUBSCRIBE job_progress:*
```

## Performance Tips

### 1. Batch Updates

Instead of sending every tiny update:

```typescript
// Bad: Send 1000 updates/second
for (let i = 0; i < 1000; i++) {
  await publish(event);
}

// Good: Batch and send 10/second
let buffer = [];
setInterval(() => {
  if (buffer.length > 0) {
    await publish(aggregateEvents(buffer));
    buffer = [];
  }
}, 100);
```

### 2. Use Appropriate Transport

- **SSE**: One-way streaming (AI responses, progress)
- **WebSocket**: Two-way communication (chat, collaboration)

### 3. Cleanup Connections

Always disconnect when done:

```typescript
useEffect(() => {
  return () => {
    disconnect(); // Cleanup
  };
}, []);
```

## Migration from Polling

### Before (Polling)

```typescript
// Old way: Poll every 2 seconds
useEffect(() => {
  const interval = setInterval(async () => {
    const status = await fetch(`/api/jobs/${jobId}/status`);
    setProgress(status.progress);
  }, 2000);

  return () => clearInterval(interval);
}, [jobId]);
```

### After (SSE Streaming)

```typescript
// New way: Real-time updates
const { progress } = useRenderProgressStream(jobId);
// That's it! Automatic updates, no polling!
```

**Benefits:**
- Lower server load (no polling requests)
- Instant updates (no 2-second delay)
- Better UX (smoother progress)
- Premium feel

## Need Help?

1. Check logs: Look for "real-time" or "SSE" or "WebSocket" in server logs
2. Test endpoints: Use curl/wscat to verify backend works
3. Check stats: `/api/realtime/stats` shows active connections
4. Review docs: See `AGENT_38_REALTIME_STREAMING.md`

---

## Summary

✅ Backend already integrated - no setup needed
✅ Import hooks - add to your components
✅ Call hooks with IDs - automatic streaming
✅ Display data - instant updates

**Real-time streaming is ready to use throughout your app!**
