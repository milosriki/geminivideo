# Real-time Streaming Quick Reference

## 🚀 Start Server

```bash
cd /home/user/geminivideo/services/gateway-api
npm start
```

Expected output:
```
Gateway API listening on port 8000
✅ Channel manager initialized
✅ WebSocket server initialized on /ws
✅ SSE manager initialized
🎉 Real-time infrastructure ready!
```

---

## 📡 SSE Endpoints (Server-Sent Events)

### 1. Stream AI Council Score
```bash
curl -N "http://localhost:8000/api/stream/council-score?videoUrl=VIDEO_URL&transcript=TRANSCRIPT"
```

### 2. Stream Video Render Progress
```bash
curl -N "http://localhost:8000/api/stream/render-progress/JOB_ID"
```

### 3. Stream Campaign Metrics
```bash
curl -N "http://localhost:8000/api/stream/campaign-metrics/CAMPAIGN_ID"
```

### 4. Stream A/B Test Results
```bash
curl -N "http://localhost:8000/api/stream/ab-test-results/TEST_ID"
```

---

## 🔌 WebSocket Connection

### Connect
```bash
wscat -c "ws://localhost:8000/ws?userId=USER_ID"
```

### Subscribe to Channel
```json
{"type":"subscribe","channel":{"type":"job_progress","id":"job_123"}}
```

### Ping
```json
{"type":"ping"}
```

---

## ⚛️ React Frontend Hooks

### SSE Hooks

```typescript
import {
  useSSE,
  useCouncilScoreStream,
  useRenderProgressStream,
  useCampaignMetricsStream
} from '@/hooks/useSSE';

// Council Score
const { stages, finalScore, startStreaming } =
  useCouncilScoreStream(videoUrl, transcript);

// Render Progress
const { progress, currentFrame, stage } =
  useRenderProgressStream(jobId);

// Campaign Metrics
const { metrics, startStreaming, stopStreaming } =
  useCampaignMetricsStream(campaignId);
```

### WebSocket Hooks

```typescript
import {
  useWebSocket,
  useJobProgress,
  useRealtimeAlerts,
  useLiveMetrics
} from '@/hooks/useWebSocket';

// Job Progress
const { progress, status } = useJobProgress(jobId);

// Real-time Alerts
const { alerts, dismissAlert } = useRealtimeAlerts(userId);

// Live Metrics
const { metrics } = useLiveMetrics(entityId, entityType);
```

---

## 🛠️ Backend Integration

### Publish Events

```typescript
import { getChannelManager } from './realtime';

const channelManager = getChannelManager();

// Publish progress update
await channelManager.publish(
  { type: 'job_progress', id: jobId },
  {
    type: 'job_progress',
    jobId,
    status: 'processing',
    progress: 0.5,
    message: 'Halfway done!',
    timestamp: new Date().toISOString()
  }
);
```

### Using SSE Manager

```typescript
import { getSSEManager } from './realtime';

const sseManager = getSSEManager();
const client = sseManager.initializeConnection(res, userId);

// Send event
sseManager.sendEvent(client, {
  type: 'custom_event',
  data: { /* ... */ },
  timestamp: new Date().toISOString()
});

// Complete stream
sseManager.sendComplete(client, { result: 'success' });
```

---

## 🧪 Testing

### Run Test Suite
```bash
cd /home/user/geminivideo/services/gateway-api
./test-realtime.sh
```

### Manual Tests

```bash
# Health check
curl http://localhost:8000/health

# Real-time stats
curl http://localhost:8000/api/realtime/stats

# Test SSE
curl -N http://localhost:8000/api/stream/council-score?videoUrl=test&transcript=hello

# Test WebSocket
wscat -c "ws://localhost:8000/ws?userId=test"
```

---

## 📊 Monitoring

### Check Stats
```bash
curl http://localhost:8000/api/realtime/stats | jq
```

### Response
```json
{
  "status": "healthy",
  "sse": {
    "totalConnections": 5,
    "totalEvents": 234
  },
  "channels": {
    "isConnected": true,
    "activeChannels": 3,
    "totalSubscriptions": 8
  }
}
```

---

## 🔧 Troubleshooting

### SSE Not Working
```bash
# Check server
curl http://localhost:8000/health

# Test endpoint
curl -N http://localhost:8000/api/stream/council-score?videoUrl=test&transcript=test

# Check CORS (should see Access-Control headers)
curl -v http://localhost:8000/api/stream/council-score?videoUrl=test&transcript=test
```

### WebSocket Not Working
```bash
# Test connection
wscat -c "ws://localhost:8000/ws"

# Check if server is listening
netstat -an | grep 8000
```

### Redis Issues
```bash
# Check Redis
redis-cli ping

# Monitor channels
redis-cli
> SUBSCRIBE job_progress:*
```

---

## 📁 Key Files

### Backend
```
/services/gateway-api/src/
├── realtime/
│   ├── events.ts              # Event types
│   ├── channels.ts            # Channel manager
│   ├── websocket-manager.ts   # WebSocket manager
│   └── sse-manager.ts         # SSE manager
├── routes/
│   └── streaming.ts           # SSE endpoints
└── index.ts                   # Main app
```

### Frontend
```
/frontend/src/
├── hooks/
│   ├── useSSE.ts              # SSE hooks
│   └── useWebSocket.ts        # WebSocket hooks
└── components/
    └── RealtimeExample.tsx    # Examples
```

---

## 📚 Documentation

| File | Description |
|------|-------------|
| `AGENT_38_REALTIME_STREAMING.md` | Complete documentation |
| `INTEGRATION_GUIDE.md` | Integration guide |
| `AGENT_38_SUMMARY.md` | Implementation summary |
| `REALTIME_QUICK_REFERENCE.md` | This file |

---

## 🎯 Common Use Cases

### 1. Show AI Thinking Process
```typescript
const { stages, finalScore, startStreaming } =
  useCouncilScoreStream(videoUrl, transcript);

<button onClick={startStreaming}>Evaluate</button>

{stages.gemini?.thinking && <p>{stages.gemini.thinking}</p>}
{finalScore && <p>Score: {finalScore.composite}</p>}
```

### 2. Live Render Progress
```typescript
const { progress, stage, currentFrame, totalFrames } =
  useRenderProgressStream(jobId);

<div>
  <p>Stage: {stage}</p>
  <p>Frame: {currentFrame} / {totalFrames}</p>
  <progress value={progress} max={1} />
</div>
```

### 3. Real-time Metrics
```typescript
const { metrics, startStreaming } =
  useCampaignMetricsStream(campaignId);

<button onClick={startStreaming}>Start Live Updates</button>

{metrics && (
  <div>
    <p>Impressions: {metrics.impressions}</p>
    <p>CTR: {(metrics.ctr * 100).toFixed(2)}%</p>
    <p>ROAS: {metrics.roas.toFixed(2)}x</p>
  </div>
)}
```

### 4. Alert Notifications
```typescript
const { alerts, dismissAlert } = useRealtimeAlerts(userId);

{alerts.map(alert => (
  <div key={alert.alertId}>
    <h4>{alert.title}</h4>
    <p>{alert.message}</p>
    <button onClick={() => dismissAlert(alert.alertId)}>
      Dismiss
    </button>
  </div>
))}
```

---

## 💡 Tips

1. **SSE vs WebSocket**
   - Use SSE for one-way streaming (AI responses, progress)
   - Use WebSocket for two-way communication (chat, collaboration)

2. **Always Cleanup**
   ```typescript
   useEffect(() => {
     return () => disconnect(); // Important!
   }, []);
   ```

3. **Error Handling**
   ```typescript
   const { error } = useSSE(url, {
     onError: (err) => console.error('Error:', err)
   });
   ```

4. **Reconnection**
   ```typescript
   useSSE(url, {
     reconnect: true,
     maxReconnectAttempts: 5
   });
   ```

---

## ⚡ Quick Commands

```bash
# Start server
npm start

# Test everything
./test-realtime.sh

# Test SSE
curl -N http://localhost:8000/api/stream/council-score?videoUrl=test&transcript=hello

# Test WebSocket
wscat -c ws://localhost:8000/ws

# Check stats
curl http://localhost:8000/api/realtime/stats

# Monitor Redis
redis-cli MONITOR
```

---

**Status**: ✅ Production Ready
**Documentation**: Complete
**Examples**: Included
**Testing**: Automated script available

🎉 **Real-time streaming is ready to use!**
