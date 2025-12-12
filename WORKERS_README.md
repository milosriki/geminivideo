# AGENT 3: WORKER ACTIVATOR - Background Workers System

This document describes the background worker system for GeminiVideo, configured and activated by Agent 3.

## Overview

The GeminiVideo platform uses Celery distributed task queues for background processing. This enables:

- **Asynchronous Processing**: Long-running tasks don't block API requests
- **Scalability**: Workers can be scaled horizontally
- **Reliability**: Task retry, failure handling, and monitoring
- **Scheduling**: Periodic tasks run automatically via Celery Beat

## Architecture

### ML Service Workers

**Purpose**: Process machine learning tasks, HubSpot webhooks, and monitoring

**Tasks**:
- `process_hubspot_webhook`: Asynchronous HubSpot deal webhook processing
  - Calculates synthetic revenue
  - Attributes conversions to ads
  - Sends feedback to BattleHardenedSampler
  - Queue: `hubspot-webhook-events`

- `monitor_fatigue`: Periodic ad fatigue monitoring (every 6 hours)
  - Detects fatiguing ads before CTR crashes
  - Monitors frequency, CPM, and engagement trends
  - Queues critical ads for SafeExecutor approval
  - Queue: `fatigue-monitoring`

- `auto_index_winner`: Auto-index winning ads to RAG (every 12 hours)
  - Generates embeddings from creative DNA
  - Adds winners to FAISS index
  - Enables semantic search for similar winners
  - Queue: `budget-optimization`

**Celery App**: `/services/ml-service/src/celery_app.py`

**Beat Schedule**: `/services/ml-service/src/celery_beat_tasks.py`

### Video Agent Workers

**Purpose**: Video processing, rendering, transcoding, and captioning

**Queues**:
- `render_queue`: High-quality video rendering (priority 10)
- `preview_queue`: Fast preview frame generation (priority 5)
- `transcode_queue`: Video format conversion (priority 7)
- `caption_queue`: AI-powered caption generation (priority 6)

**Tasks**:
- `render_video_task`: Full video rendering with FFmpeg
  - GPU acceleration support (NVIDIA h264_nvenc)
  - Transitions, overlays, subtitles
  - Progress tracking via Redis pub/sub
  - Timeout: 1 hour

- `generate_preview_task`: Extract preview frames
  - Fast thumbnail generation
  - Multiple frames at intervals
  - Timeout: 5 minutes

- `transcode_task`: Convert video formats
  - Supports H.264, H.265, VP9, AV1
  - Multiple containers (MP4, WebM, MKV)
  - Bitrate and quality control
  - Timeout: 30 minutes

- `caption_task`: Generate SRT subtitles
  - OpenAI Whisper speech recognition
  - Multiple model sizes (tiny to large)
  - Automatic language detection
  - Timeout: 15 minutes

- `cleanup_task`: Periodic cleanup (daily at 2 AM)
  - Removes old temporary files
  - Manages disk space limits
  - Cleans empty directories

- `monitor_resources_task`: System monitoring (every minute)
  - CPU, memory, disk, GPU usage
  - Publishes to Redis for real-time monitoring
  - Logs warnings for high resource usage

**Celery App**: `/services/video-agent/pro/celery_app.py`

## Usage

### Option 1: Shell Script (Local Development)

#### Start All Workers

```bash
./scripts/start-workers.sh
```

This starts:
- ML Worker (4 concurrent tasks)
- ML Beat Scheduler
- Video Render Worker (2 concurrent tasks)
- Video Preview Worker (4 concurrent tasks)
- Video Transcode Worker (2 concurrent tasks)
- Video Caption Worker (1 concurrent task)
- Video Beat Scheduler

#### Start Specific Workers

```bash
# ML workers only
./scripts/start-workers.sh --ml-only

# Video workers only
./scripts/start-workers.sh --video-only

# With Flower monitoring UI
./scripts/start-workers.sh --with-flower
```

#### Stop All Workers

```bash
./scripts/stop-workers.sh
```

Or manually:

```bash
pkill -F logs/workers/ml-worker.pid
pkill -F logs/workers/ml-beat.pid
pkill -F logs/workers/video-render.pid
# ... etc
```

### Option 2: Docker Compose (Production)

#### Start All Services + Workers

```bash
# Start infrastructure and application services
docker-compose up -d

# Start workers
docker-compose -f docker-compose.workers.yml up -d
```

Or combined:

```bash
docker-compose -f docker-compose.yml -f docker-compose.workers.yml up -d
```

#### Start Specific Workers

```bash
# ML workers only
docker-compose -f docker-compose.workers.yml up -d celery-ml-worker celery-ml-beat

# Video workers only
docker-compose -f docker-compose.workers.yml up -d \
    celery-video-render \
    celery-video-preview \
    celery-video-transcode \
    celery-video-caption \
    celery-video-beat

# With monitoring
docker-compose -f docker-compose.workers.yml up -d flower
```

#### Stop Workers

```bash
docker-compose -f docker-compose.workers.yml down
```

#### View Logs

```bash
# All workers
docker-compose -f docker-compose.workers.yml logs -f

# Specific worker
docker-compose -f docker-compose.workers.yml logs -f celery-ml-worker

# Last 100 lines
docker-compose -f docker-compose.workers.yml logs --tail=100 celery-video-render
```

## Monitoring

### Flower Web UI

Flower provides a web-based monitoring interface for Celery.

**Access**: http://localhost:5555

**Default Credentials**:
- Username: `admin`
- Password: `changeme` (set via `FLOWER_USER` and `FLOWER_PASSWORD` env vars)

**Features**:
- Real-time task monitoring
- Worker status and statistics
- Task history and details
- Broker (Redis) monitoring
- Rate limit configuration

### Redis CLI

Monitor queues directly:

```bash
# Connect to Redis
redis-cli -u redis://localhost:6379

# Check queue lengths
LLEN hubspot-webhook-events
LLEN fatigue-monitoring
LLEN render_queue

# View task progress
GET task_status:TASK_ID_HERE

# Subscribe to progress updates
SUBSCRIBE task_progress:TASK_ID_HERE
```

### Celery CLI

```bash
# Inspect active tasks
celery -A src.celery_app inspect active

# Inspect registered tasks
celery -A src.celery_app inspect registered

# Check worker stats
celery -A src.celery_app inspect stats

# Ping workers
celery -A src.celery_app inspect ping
```

## Configuration

### Environment Variables

**Redis**:
- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379/0`)

**Database**:
- `DATABASE_URL`: PostgreSQL connection URL

**ML Service**:
- `ML_SERVICE_URL`: ML service endpoint for internal communication

**Video Processing**:
- `TEMP_DIR`: Temporary file directory (default: `/tmp/video-processing`)
- `RENDER_DIR`: Rendered video output directory (default: `/tmp/renders`)
- `PREVIEW_DIR`: Preview frame directory (default: `/tmp/previews`)
- `RENDER_TIMEOUT`: Render task timeout in seconds (default: 3600)
- `CLEANUP_AGE_DAYS`: Delete files older than N days (default: 7)
- `MAX_TEMP_SIZE_GB`: Max temporary storage size (default: 50 GB)

**Flower**:
- `FLOWER_USER`: Flower UI username (default: `admin`)
- `FLOWER_PASSWORD`: Flower UI password (default: `changeme`)

### Concurrency Settings

Workers are configured with different concurrency levels based on task complexity:

| Worker | Concurrency | Reason |
|--------|-------------|--------|
| ML Worker | 4 | I/O-bound tasks (HTTP, DB) |
| Video Render | 2 | CPU/GPU-intensive |
| Video Preview | 4 | Fast, parallelizable |
| Video Transcode | 2 | CPU-intensive |
| Video Caption | 1 | GPU-intensive (Whisper) |

Adjust concurrency in:
- Shell script: `--concurrency=N` flag
- Docker Compose: `command` section

### Queue Priorities

Tasks are routed to queues with different priorities:

| Queue | Priority | Purpose |
|-------|----------|---------|
| `render_queue` | 10 | High-quality renders |
| `transcode_queue` | 7 | Format conversion |
| `caption_queue` | 6 | Caption generation |
| `preview_queue` | 5 | Fast previews |
| `budget-optimization` | Default | Budget tasks |
| `hubspot-webhook-events` | Default | Webhooks |
| `fatigue-monitoring` | Default | Monitoring |

## Scaling

### Horizontal Scaling

Add more workers:

```bash
# Additional render worker
celery -A pro.celery_app worker \
    --queues=render_queue \
    --concurrency=2 \
    --hostname=render2@%h

# GPU-specific worker
celery -A pro.celery_app worker \
    --queues=render_queue \
    --concurrency=1 \
    --hostname=gpu@%h
```

Docker Compose scaling:

```bash
docker-compose -f docker-compose.workers.yml up -d --scale celery-video-render=3
```

### Vertical Scaling

Increase concurrency:

```bash
# Higher concurrency for preview worker
celery -A pro.celery_app worker \
    --queues=preview_queue \
    --concurrency=8
```

## Troubleshooting

### Workers Not Starting

**Check Redis**:
```bash
redis-cli -u $REDIS_URL ping
```

**Check Logs**:
```bash
tail -f logs/workers/ml-worker.log
```

**Check Process**:
```bash
ps aux | grep celery
```

### Tasks Not Processing

**Check Queue Length**:
```bash
redis-cli LLEN render_queue
```

**Inspect Active Workers**:
```bash
celery -A src.celery_app inspect active
```

**Purge Queue** (careful!):
```bash
celery -A src.celery_app purge
```

### High Memory Usage

**Set Max Tasks Per Child**:
```bash
celery -A pro.celery_app worker --max-tasks-per-child=10
```

**Monitor Resources**:
```bash
celery -A pro.celery_app inspect stats
```

### GPU Not Detected

**Check NVIDIA Drivers**:
```bash
nvidia-smi
```

**Set CUDA Device**:
```bash
export CUDA_VISIBLE_DEVICES=0
```

## Task Execution Examples

### Python API

```python
from src.celery_tasks import process_hubspot_webhook, monitor_all_ads_fatigue

# Async execution
result = process_hubspot_webhook.delay({
    'dealId': 'deal_123',
    'stageTo': 'closedwon',
    'dealValue': 10000,
    'tenantId': 'tenant_1'
})

# Get result
output = result.get(timeout=30)
print(output)

# Periodic monitoring (called by Beat)
result = monitor_all_ads_fatigue.delay()
```

### HTTP API (via ML Service)

```bash
# Trigger webhook processing
curl -X POST http://localhost:8003/api/webhooks/hubspot \
  -H "Content-Type: application/json" \
  -d '{
    "dealId": "deal_123",
    "stageTo": "closedwon",
    "dealValue": 10000
  }'
```

### Video Processing API

```python
from pro.celery_app import render_video_task, generate_preview_task

# Render video
result = render_video_task.delay({
    'scenes': [
        {'video_path': '/path/to/scene1.mp4'},
        {'video_path': '/path/to/scene2.mp4'}
    ],
    'output_format': {
        'width': 1920,
        'height': 1080,
        'fps': 30
    },
    'use_gpu': True
})

# Check progress
from pro.celery_app import redis_client
import json

progress_data = redis_client.get(f'task_status:{result.id}')
if progress_data:
    progress = json.loads(progress_data)
    print(f"Progress: {progress['progress']}%")
    print(f"Status: {progress['status']}")
```

## Files Created by Agent 3

1. **Startup Script**: `/home/user/geminivideo/scripts/start-workers.sh`
   - Starts all workers locally
   - Creates stop script automatically
   - Checks Redis connectivity
   - Colored output and logging

2. **Stop Script**: `/home/user/geminivideo/scripts/stop-workers.sh`
   - Auto-generated by start script
   - Stops all workers gracefully
   - Cleans up PID files

3. **Docker Compose**: `/home/user/geminivideo/docker-compose.workers.yml`
   - Production worker configuration
   - All services with healthchecks
   - Volume management
   - Restart policies

4. **Updated Requirements**:
   - `/services/ml-service/requirements.txt`: Added Celery, Kombu, Flower
   - `/services/video-agent/requirements.txt`: Added Celery, Kombu, Flower, psutil

5. **This Documentation**: `/home/user/geminivideo/WORKERS_README.md`

## Next Steps

1. **Install Dependencies**:
   ```bash
   cd services/ml-service && pip install -r requirements.txt
   cd ../video-agent && pip install -r requirements.txt
   ```

2. **Start Redis**:
   ```bash
   docker-compose up -d redis
   ```

3. **Start Workers**:
   ```bash
   ./scripts/start-workers.sh
   ```

4. **Monitor**:
   - Logs: `tail -f logs/workers/*.log`
   - Flower: http://localhost:5555

5. **Test Tasks**:
   - Send a test HubSpot webhook
   - Trigger a video render
   - Check Flower for task status

## Support

For issues or questions about the worker system:
1. Check logs in `logs/workers/`
2. Monitor Flower UI at http://localhost:5555
3. Inspect Redis queues with `redis-cli`
4. Review Celery docs: https://docs.celeryq.dev/

---

**Agent 3: THE WORKER ACTIVATOR** ✅ Complete
