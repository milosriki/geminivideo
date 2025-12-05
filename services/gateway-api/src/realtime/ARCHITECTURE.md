# Real-time Streaming Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  React Hooks     │  │  Components      │  │  EventSource/    │  │
│  │  - useSSE        │  │  - Dashboard     │  │  WebSocket       │  │
│  │  - useWebSocket  │  │  - Alerts        │  │                  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                       │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                    HTTP/SSE & WebSocket
                                │
┌───────────────────────────────▼───────────────────────────────────────┐
│                       GATEWAY API LAYER                                │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                    Express App (index.ts)                     │    │
│  │  - Routes                                                     │    │
│  │  - Middleware                                                 │    │
│  │  - Server initialization                                      │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │  SSE Manager     │  │  WebSocket Mgr   │  │  Channel Manager │   │
│  │                  │  │                  │  │                  │   │
│  │  - Connections   │  │  - Connections   │  │  - Subscriptions │   │
│  │  - Keep-alive    │  │  - Heartbeat     │  │  - Redis Pub/Sub │   │
│  │  - Streaming     │  │  - Messages      │  │  - Event routing │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
│           │                     │                      │               │
└───────────┼─────────────────────┼──────────────────────┼───────────────┘
            │                     │                      │
            │                     │         ┌────────────▼────────────┐
            │                     │         │      Redis Pub/Sub       │
            │                     │         │                          │
            │                     │         │  - job_progress:*        │
            │                     │         │  - campaign_metrics:*    │
            │                     │         │  - alerts:*              │
            │                     │         └────────────┬─────────────┘
            │                     │                      │
            │                     │                      │ Subscribe
            ▼                     ▼                      ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          WORKER LAYER                                 │
│                                                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │ Titan Core  │  │ ML Service  │  │ Google Ads  │  │   Others    ││
│  │             │  │             │  │   Service   │  │             ││
│  │ - Video     │  │ - AI Models │  │ - Campaigns │  │ - Jobs      ││
│  │ - Render    │  │ - Scoring   │  │ - Metrics   │  │ - Tasks     ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│
│                                                                        │
│  All services publish events to Redis channels                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. SSE Manager

**Purpose**: Manage Server-Sent Events connections for streaming data to clients

**Key Features**:
- Connection initialization with headers
- Keep-alive mechanism (every 15s)
- Event routing to specific clients
- Automatic cleanup on disconnect

**Flow**:
```
Client → GET /api/stream/council-score
         ↓
    Initialize SSE connection
         ↓
    Set headers (Content-Type: text/event-stream)
         ↓
    Send initial connected event
         ↓
    Stream events as they occur
         ↓
    Send completion event
         ↓
    Close connection
```

**Methods**:
```typescript
class SSEManager {
  initializeConnection(res, userId)
  sendEvent(client, event)
  sendChunk(client, chunk)
  sendComplete(client, data)
  sendError(client, error)
  broadcast(event)
}
```

---

### 2. WebSocket Manager

**Purpose**: Manage WebSocket connections for bidirectional real-time communication

**Key Features**:
- Connection lifecycle management
- Channel subscriptions
- Heartbeat/ping mechanism (every 30s)
- Client timeout detection (60s)
- Automatic cleanup

**Flow**:
```
Client → ws://server/ws?userId=123
         ↓
    Accept WebSocket connection
         ↓
    Send connected event
         ↓
    Handle incoming messages:
      - subscribe
      - unsubscribe
      - ping
         ↓
    Route events from channels
         ↓
    Send heartbeat every 30s
         ↓
    Detect disconnect
         ↓
    Cleanup resources
```

**Methods**:
```typescript
class WebSocketManager {
  initialize()
  handleConnection(ws, req)
  handleMessage(client, data)
  handleSubscribe(client, channel)
  broadcast(channel, event)
  sendToUser(userId, event)
}
```

---

### 3. Channel Manager

**Purpose**: Manage pub/sub channels using Redis for distributed event routing

**Key Features**:
- Redis pub/sub integration
- Local event emission (EventEmitter)
- Channel subscriptions
- Distributed communication

**Flow**:
```
Service publishes event
         ↓
    publish(channel, event)
         ↓
    Emit locally (immediate)
         ↓
    Publish to Redis (distributed)
         ↓
    Redis broadcasts to subscribers
         ↓
    All instances receive event
         ↓
    Route to subscribed clients
```

**Methods**:
```typescript
class ChannelManager {
  initialize()
  subscribe(channel, callback)
  unsubscribe(subscription)
  publish(channel, event)
  getStats()
}
```

---

## Event Flow Examples

### Example 1: Video Render Progress

```
┌──────────────┐
│ Titan Core   │ Video rendering service
└──────┬───────┘
       │
       │ 1. Publish progress
       │    channelManager.publish({ type: 'video_render', id: 'job_123' }, event)
       │
       ▼
┌──────────────┐
│   Redis      │ Pub/Sub channel: video_render:job_123
└──────┬───────┘
       │
       │ 2. Broadcast to all instances
       │
       ▼
┌──────────────────┐
│ Gateway API      │ Channel Manager receives event
│ Channel Manager  │
└──────┬───────────┘
       │
       │ 3. Route to subscribed clients
       │
       ▼
┌──────────────────┐
│ SSE Manager      │ Send to SSE clients
│                  │
│ Client 1 ────────┼─────► data: {...progress...}
│ Client 2 ────────┼─────► data: {...progress...}
└──────────────────┘
```

### Example 2: Real-time Alerts

```
┌──────────────┐
│ ML Service   │ Detects performance issue
└──────┬───────┘
       │
       │ 1. Publish alert
       │    channelManager.publish({ type: 'alerts', userId: '456' }, alertEvent)
       │
       ▼
┌──────────────┐
│   Redis      │ Pub/Sub channel: alerts:456
└──────┬───────┘
       │
       │ 2. Broadcast
       │
       ▼
┌──────────────────┐
│ Gateway API      │ Channel Manager receives
│ Channel Manager  │
└──────┬───────────┘
       │
       │ 3. Route to user's WebSocket
       │
       ▼
┌──────────────────┐
│ WebSocket Mgr    │ Send to specific user
│                  │
│ User 456 ────────┼─────► {"type":"alert", "severity":"warning",...}
└──────────────────┘
```

### Example 3: AI Council Streaming

```
┌──────────────┐
│ Frontend     │ User clicks "Evaluate"
└──────┬───────┘
       │
       │ GET /api/stream/council-score
       │
       ▼
┌──────────────────┐
│ Gateway API      │ SSE endpoint
│ /routes/         │
│ streaming.ts     │
└──────┬───────────┘
       │
       │ For each AI model:
       │
       ▼
┌──────────────────┐
│ AI APIs          │ Gemini, Claude, GPT-4, Perplexity
│ (External)       │
└──────┬───────────┘
       │
       │ Stream response chunks
       │
       ▼
┌──────────────────┐
│ SSE Manager      │ Forward chunks to client
└──────┬───────────┘
       │
       │ data: {"model":"gemini","chunk":"Analyzing..."}
       │ data: {"model":"gemini","chunk":"Strong..."}
       │ data: {"model":"gemini","score":0.78}
       │ ...
       │
       ▼
┌──────────────────┐
│ Frontend         │ Display streaming text
│ useSSE hook      │ Show each model's thinking
└──────────────────┘
```

---

## Message Format Standards

### SSE Message Format

```
id: event_123
event: custom_event_type
data: {"type":"job_progress","jobId":"123",...}

```

### WebSocket Message Format

**Client → Server**:
```json
{
  "type": "subscribe",
  "channel": {
    "type": "job_progress",
    "id": "job_123"
  }
}
```

**Server → Client**:
```json
{
  "type": "job_progress",
  "jobId": "job_123",
  "status": "processing",
  "progress": 0.75,
  "message": "Rendering frame 750/1000",
  "timestamp": "2025-12-05T10:00:00Z"
}
```

### Redis Pub/Sub

**Channel naming**: `{type}:{id}` or `{type}:{id}:{userId}`

Examples:
- `job_progress:job_123`
- `campaign_metrics:camp_456`
- `alerts:user_789`

**Message payload**: JSON string
```json
{
  "type": "job_progress",
  "jobId": "job_123",
  "status": "processing",
  "progress": 0.75,
  "timestamp": "2025-12-05T10:00:00Z"
}
```

---

## Connection Lifecycle

### SSE Connection Lifecycle

```
1. Client opens connection
   └─► EventSource(url)

2. Server initializes
   └─► Set headers
   └─► Send connected event
   └─► Start keep-alive (15s)

3. Event streaming
   └─► Send events as they occur
   └─► data: {...}\n\n

4. Completion
   └─► Send complete event
   └─► Close connection

5. Error/Disconnect
   └─► Client auto-reconnects
   └─► Max 5 attempts, 3s interval
```

### WebSocket Connection Lifecycle

```
1. Client connects
   └─► new WebSocket(url)

2. Server accepts
   └─► Send connected event
   └─► Start heartbeat (30s)

3. Subscription phase
   └─► Client sends subscribe
   └─► Server confirms subscription

4. Message exchange
   └─► Bidirectional messages
   └─► Event routing

5. Heartbeat
   └─► Server sends ping (30s)
   └─► Client responds pong
   └─► Detect timeout (60s)

6. Disconnect
   └─► Clean up subscriptions
   └─► Remove from clients map
   └─► Client auto-reconnects
```

---

## Scaling Considerations

### Horizontal Scaling

**Problem**: Multiple gateway instances need to share events

**Solution**: Redis pub/sub

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Gateway 1    │     │ Gateway 2    │     │ Gateway 3    │
│ Client A ────┤     │ Client B ────┤     │ Client C ────┤
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Redis      │
                     │   Pub/Sub    │
                     └──────────────┘
                            ▲
                            │
                     ┌──────┴───────┐
                     │   Workers    │
                     └──────────────┘
```

Event published by worker reaches all gateway instances, which forward to their connected clients.

### Load Balancing

**Sticky Sessions**: Required for WebSocket (use userId/clientId)
**SSE**: Can work without sticky sessions (short-lived)

---

## Performance Optimization

### 1. Batching Events

Instead of sending every tiny update:

```typescript
// Buffer events
let buffer: Event[] = [];

// Flush every 100ms
setInterval(() => {
  if (buffer.length > 0) {
    sseManager.sendEvent(client, {
      type: 'batch',
      events: buffer
    });
    buffer = [];
  }
}, 100);
```

### 2. Connection Pooling

Reuse Redis connections:

```typescript
// Single Redis client for all channels
const redis = createClient(redisUrl);

// Multiple subscriptions on same connection
await redis.subscribe('channel1');
await redis.subscribe('channel2');
```

### 3. Compression

For large payloads:

```typescript
// Compress data before sending
const compressed = gzip(JSON.stringify(largeData));
sseManager.sendEvent(client, {
  type: 'compressed',
  data: compressed.toString('base64'),
  encoding: 'gzip'
});
```

---

## Security Considerations

### 1. Authentication

**SSE**:
```typescript
// Add token to URL
const url = `/api/stream/council-score?token=${authToken}`;

// Verify on server
if (!verifyToken(req.query.token)) {
  res.status(401).end();
  return;
}
```

**WebSocket**:
```typescript
// Add token to URL
const ws = new WebSocket(`ws://server/ws?token=${authToken}`);

// Verify on connection
if (!verifyToken(query.token)) {
  ws.close(1008, 'Unauthorized');
  return;
}
```

### 2. Rate Limiting

```typescript
// Limit connections per user
const connectionsPerUser = new Map<string, number>();

if (connectionsPerUser.get(userId) >= MAX_CONNECTIONS) {
  res.status(429).end();
  return;
}
```

### 3. Channel Authorization

```typescript
// Verify user can access channel
if (!canAccessChannel(userId, channelId)) {
  ws.close(1008, 'Access denied');
  return;
}
```

---

## Monitoring & Debugging

### Stats Endpoint

```
GET /api/realtime/stats
```

Returns:
```json
{
  "status": "healthy",
  "sse": {
    "totalConnections": 15,
    "totalEvents": 1250
  },
  "channels": {
    "isConnected": true,
    "activeChannels": 8,
    "totalSubscriptions": 23
  }
}
```

### Logging

```typescript
// Connection logs
console.log(`📱 Client connected: ${clientId}`);
console.log(`👋 Client disconnected: ${clientId}`);

// Event logs
console.log(`📡 Subscribed to channel: ${channelName}`);
console.log(`📊 Progress update for ${jobId}: ${progress}`);

// Error logs
console.error(`❌ Failed to send event: ${error}`);
```

### Redis Monitoring

```bash
# Monitor all Redis activity
redis-cli MONITOR

# Subscribe to channels
redis-cli SUBSCRIBE 'job_progress:*'

# Check channel subscribers
redis-cli PUBSUB NUMSUB job_progress:job_123
```

---

## Error Handling

### SSE Errors

```typescript
try {
  sseManager.sendEvent(client, event);
} catch (error) {
  console.error('SSE error:', error);
  sseManager.sendError(client, error.message);
}
```

### WebSocket Errors

```typescript
ws.on('error', (error) => {
  console.error('WebSocket error:', error);
  // Cleanup connection
  handleDisconnect(client);
});
```

### Channel Errors

```typescript
try {
  await channelManager.publish(channel, event);
} catch (error) {
  console.error('Channel publish error:', error);
  // Emit locally as fallback
  this.emit(`channel:${channelName}`, event);
}
```

---

## Best Practices

1. **Always cleanup connections**
   ```typescript
   useEffect(() => {
     return () => disconnect();
   }, []);
   ```

2. **Handle errors gracefully**
   ```typescript
   const { error } = useSSE(url, {
     onError: (err) => showErrorToast(err.message)
   });
   ```

3. **Implement reconnection**
   ```typescript
   useSSE(url, {
     reconnect: true,
     maxReconnectAttempts: 5
   });
   ```

4. **Rate limit events**
   ```typescript
   // Send max 10/second
   throttle(sendEvent, 100);
   ```

5. **Monitor performance**
   ```typescript
   // Log event delivery time
   const start = Date.now();
   await sendEvent(event);
   console.log(`Sent in ${Date.now() - start}ms`);
   ```

---

**Architecture Status**: ✅ Production Ready
**Documentation**: Complete
**Scalability**: Horizontal scaling via Redis
**Security**: Authentication ready
**Monitoring**: Stats endpoint + logging
