# Celery Distributed Task Queue - Production Setup

## Overview

This is a complete, production-ready Celery distributed task queue system for video processing with:

- **Multiple Priority Queues**: render, preview, transcode, caption
- **GPU Worker Support**: Automatic GPU detection and routing
- **Progress Tracking**: Real-time progress via Redis pub/sub
- **Resource Monitoring**: CPU, GPU, memory tracking
- **Auto-scaling**: Rate limiting and concurrency control
- **Fault Tolerance**: Exponential backoff retry with jitter
- **Periodic Cleanup**: Automated old file deletion

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Redis Broker                            │
│              (Message Queue + Result Backend)                │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
   │  Worker │          │  Worker │          │  Worker │
   │  CPU 1  │          │  CPU 2  │          │  GPU 1  │
   │         │          │         │          │         │
   │ render  │          │preview  │          │ render  │
   │transcode│          │caption  │          │transcode│
   └─────────┘          └─────────┘          └─────────┘
```

## Prerequisites

### System Requirements
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y ffmpeg redis-server python3-dev

# For GPU support (optional)
# Install NVIDIA drivers and CUDA toolkit
# nvidia-smi should be available
```

### Python Dependencies
```bash
pip install celery[redis]==5.3.4
pip install redis==5.0.1
pip install psutil==5.9.6
pip install kombu==5.3.4

# For caption generation (optional)
pip install openai-whisper==20231117
```

## Quick Start

### 1. Start Redis Server
```bash
# Start Redis on default port 6379
redis-server

# Or with custom config
redis-server /etc/redis/redis.conf
```

### 2. Set Environment Variables
```bash
export REDIS_URL="redis://localhost:6379/0"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"
export TEMP_DIR="/tmp/video-processing"
export RENDER_DIR="/tmp/renders"
export PREVIEW_DIR="/tmp/previews"
```

### 3. Start Workers

#### General Purpose Worker (All Queues)
```bash
cd /home/user/geminivideo
celery -A services.video-agent.pro.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --hostname=worker@%h
```

#### Specialized Render Worker (CPU)
```bash
celery -A services.video-agent.pro.celery_app worker \
    -Q render_queue,transcode_queue \
    --loglevel=info \
    --concurrency=2 \
    --hostname=render-cpu@%h
```

#### GPU Worker (Hardware Acceleration)
```bash
# Requires NVIDIA GPU with CUDA
celery -A services.video-agent.pro.celery_app worker \
    -Q render_queue,transcode_queue \
    --loglevel=info \
    --concurrency=1 \
    --hostname=render-gpu@%h
```

#### Preview & Caption Worker
```bash
celery -A services.video-agent.pro.celery_app worker \
    -Q preview_queue,caption_queue \
    --loglevel=info \
    --concurrency=4 \
    --hostname=preview@%h
```

### 4. Start Beat Scheduler (for periodic tasks)
```bash
celery -A services.video-agent.pro.celery_app beat \
    --loglevel=info
```

### 5. Start Flower (Web Monitoring Dashboard)
```bash
pip install flower
celery -A services.video-agent.pro.celery_app flower \
    --port=5555
```
Open http://localhost:5555 in browser

## Task Usage

### Python Client Example

```python
from services.video_agent.pro.celery_app import (
    render_video_task,
    generate_preview_task,
    transcode_task,
    caption_task,
    batch_render_task,
    cleanup_task
)

# 1. Render a video
job_data = {
    'scenes': [
        {'video_path': '/path/to/scene1.mp4', 'start_time': 0, 'end_time': 10},
        {'video_path': '/path/to/scene2.mp4', 'start_time': 5, 'end_time': 15},
    ],
    'output_format': {
        'width': 1920,
        'height': 1080,
        'fps': 30
    },
    'transitions': True,
    'use_gpu': True,  # Enable GPU acceleration
    'subtitles': '/path/to/subtitles.srt'  # Optional
}

# Submit task
result = render_video_task.apply_async(
    args=[job_data],
    priority=9  # High priority (0-10)
)

# Get task ID
task_id = result.id
print(f"Task submitted: {task_id}")

# Wait for result (blocking)
output = result.get(timeout=3600)
print(f"Render complete: {output['output_path']}")

# Or check status asynchronously
if result.ready():
    output = result.result
else:
    print(f"Task status: {result.state}")


# 2. Generate preview frames
result = generate_preview_task.apply_async(
    args=['/path/to/video.mp4'],
    kwargs={'num_frames': 10}
)
preview_data = result.get()
print(f"Preview frames: {preview_data['preview_paths']}")


# 3. Transcode video
output_format = {
    'codec': 'h264',      # h264, h265, vp9, av1
    'container': 'mp4',   # mp4, webm, mkv
    'width': 1280,
    'height': 720,
    'bitrate': '5M'
}

result = transcode_task.apply_async(
    args=['/path/to/input.mp4', output_format]
)
transcode_data = result.get()
print(f"Transcoded: {transcode_data['output_path']}")


# 4. Generate captions with Whisper
result = caption_task.apply_async(
    args=['/path/to/video.mp4'],
    kwargs={'model': 'base'}  # tiny, base, small, medium, large
)
caption_data = result.get()
print(f"Captions: {caption_data['srt_path']}")


# 5. Batch render multiple videos
job_list = [
    {'scenes': [...], 'output_format': {...}},
    {'scenes': [...], 'output_format': {...}},
    {'scenes': [...], 'output_format': {...}},
]

result = batch_render_task.apply_async(args=[job_list])
results = result.get()
print(f"Batch complete: {len(results)} videos rendered")


# 6. Manual cleanup
result = cleanup_task.apply_async(
    kwargs={'max_age_days': 7, 'max_size_gb': 50}
)
cleanup_data = result.get()
print(f"Cleaned up: {cleanup_data['deleted_files']} files")
```

## Progress Tracking

### Subscribe to Progress Updates (Redis Pub/Sub)

```python
import redis
import json

# Connect to Redis
redis_client = redis.from_url('redis://localhost:6379/0', decode_responses=True)

# Subscribe to task progress
pubsub = redis_client.pubsub()
task_id = "your-task-id"
pubsub.subscribe(f'task_progress:{task_id}')

# Listen for updates
for message in pubsub.listen():
    if message['type'] == 'message':
        data = json.loads(message['data'])
        print(f"Progress: {data['progress']}% - {data['message']}")

        if data['status'] in ['completed', 'failed']:
            break

pubsub.unsubscribe()
```

### Get Current Task Status (Redis Get)

```python
import redis
import json

redis_client = redis.from_url('redis://localhost:6379/0', decode_responses=True)

task_id = "your-task-id"
status_data = redis_client.get(f'task_status:{task_id}')

if status_data:
    status = json.loads(status_data)
    print(f"Task {task_id}:")
    print(f"  Status: {status['status']}")
    print(f"  Progress: {status['progress']}%")
    print(f"  Message: {status['message']}")
else:
    print(f"No status data for task {task_id}")
```

## Resource Monitoring

### Get System Resources

```python
import redis
import json

redis_client = redis.from_url('redis://localhost:6379/0', decode_responses=True)

# Get latest resource stats
resources_data = redis_client.get('system_resources')

if resources_data:
    resources = json.loads(resources_data)
    print(f"CPU: {resources['cpu']['percent']}%")
    print(f"Memory: {resources['memory']['percent']}%")
    print(f"Disk: {resources['disk']['percent']}%")
    print(f"GPU Available: {resources['gpu']['available']}")

    if resources['gpu']['available']:
        for gpu in resources['gpu']['gpus']:
            print(f"  GPU {gpu['index']}: {gpu['name']} - {gpu['utilization']}% utilized")
```

### Subscribe to Resource Updates

```python
pubsub = redis_client.pubsub()
pubsub.subscribe('resource_monitor')

for message in pubsub.listen():
    if message['type'] == 'message':
        resources = json.loads(message['data'])
        print(f"System Update - CPU: {resources['cpu']['percent']}%, "
              f"Memory: {resources['memory']['percent']}%")
```

## Production Deployment

### Systemd Service Files

#### `/etc/systemd/system/celery-worker.service`
```ini
[Unit]
Description=Celery Worker Service
After=network.target redis.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/home/user/geminivideo
Environment="REDIS_URL=redis://localhost:6379/0"
Environment="TEMP_DIR=/var/tmp/video-processing"
Environment="RENDER_DIR=/var/renders"
ExecStart=/usr/local/bin/celery -A services.video-agent.pro.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --pidfile=/var/run/celery/worker.pid \
    --logfile=/var/log/celery/worker.log \
    --detach
ExecStop=/usr/local/bin/celery -A services.video-agent.pro.celery_app control shutdown
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### `/etc/systemd/system/celery-beat.service`
```ini
[Unit]
Description=Celery Beat Scheduler
After=network.target redis.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/home/user/geminivideo
Environment="REDIS_URL=redis://localhost:6379/0"
ExecStart=/usr/local/bin/celery -A services.video-agent.pro.celery_app beat \
    --loglevel=info \
    --pidfile=/var/run/celery/beat.pid \
    --logfile=/var/log/celery/beat.log \
    --detach
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat
sudo systemctl status celery-worker celery-beat
```

### Docker Deployment

#### `docker-compose.yml`
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

  celery-worker:
    build: .
    command: celery -A services.video-agent.pro.celery_app worker --loglevel=info --concurrency=4
    volumes:
      - ./:/app
      - /tmp/video-processing:/tmp/video-processing
      - /tmp/renders:/tmp/renders
    environment:
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
    deploy:
      replicas: 3

  celery-beat:
    build: .
    command: celery -A services.video-agent.pro.celery_app beat --loglevel=info
    volumes:
      - ./:/app
    environment:
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis

  flower:
    build: .
    command: celery -A services.video-agent.pro.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis

volumes:
  redis-data:
```

## Monitoring and Debugging

### View Worker Status
```bash
celery -A services.video-agent.pro.celery_app inspect active
celery -A services.video-agent.pro.celery_app inspect registered
celery -A services.video-agent.pro.celery_app inspect stats
```

### View Queue Lengths
```bash
celery -A services.video-agent.pro.celery_app inspect active_queues
```

### Purge All Tasks
```bash
celery -A services.video-agent.pro.celery_app purge
```

### View Scheduled Tasks
```bash
celery -A services.video-agent.pro.celery_app inspect scheduled
```

### Redis CLI Commands
```bash
# Connect to Redis
redis-cli

# View all task keys
KEYS celery-task-meta-*

# Get task result
GET celery-task-meta-<task-id>

# View queue lengths
LLEN celery  # Default queue
LLEN render_queue
LLEN preview_queue

# Monitor pub/sub
SUBSCRIBE task_progress:*
```

## Performance Tuning

### Worker Concurrency
- **CPU-bound tasks** (rendering, transcoding): Set concurrency = CPU cores
- **I/O-bound tasks** (previews, captions): Set concurrency = 2-4x CPU cores
- **GPU tasks**: Set concurrency = 1 per GPU

### Rate Limiting
Adjust in `celery_app.py`:
```python
task_annotations={
    'render_video_task': {'rate_limit': '10/m'},  # 10 per minute
    'transcode_task': {'rate_limit': '20/m'},
    'caption_task': {'rate_limit': '5/m'},
}
```

### Memory Management
```python
# Restart workers after N tasks to prevent memory leaks
worker_max_tasks_per_child=50
```

### Task Timeouts
```python
# Adjust timeouts in environment variables
export RENDER_TIMEOUT=3600      # 1 hour
export PREVIEW_TIMEOUT=300      # 5 minutes
export TRANSCODE_TIMEOUT=1800   # 30 minutes
export CAPTION_TIMEOUT=900      # 15 minutes
```

## Troubleshooting

### Workers Not Starting
```bash
# Check Redis connection
redis-cli ping

# Check Python imports
python3 -c "from services.video_agent.pro.celery_app import app; print(app)"

# Check logs
tail -f /var/log/celery/worker.log
```

### Tasks Stuck in Pending
```bash
# Check active workers
celery -A services.video-agent.pro.celery_app inspect active

# Check worker registration
celery -A services.video-agent.pro.celery_app inspect registered

# Restart workers
sudo systemctl restart celery-worker
```

### Out of Memory
```bash
# Monitor memory usage
watch -n 1 free -h

# Reduce worker concurrency
celery -A services.video-agent.pro.celery_app worker --concurrency=2

# Enable memory limits
ulimit -m 4000000  # 4GB
```

### Slow Performance
```bash
# Check system resources
celery -A services.video-agent.pro.celery_app call monitor_resources_task

# Check queue backlog
celery -A services.video-agent.pro.celery_app inspect active_queues

# Add more workers
# Start additional worker instances on different machines
```

## Security Considerations

1. **Redis Authentication**: Use password protection
   ```bash
   redis-cli CONFIG SET requirepass "your-strong-password"
   export REDIS_URL="redis://:your-strong-password@localhost:6379/0"
   ```

2. **Network Isolation**: Run Redis on private network
   ```bash
   # In redis.conf
   bind 127.0.0.1
   ```

3. **File Permissions**: Restrict temp directory access
   ```bash
   chmod 700 /tmp/video-processing
   chown www-data:www-data /tmp/video-processing
   ```

4. **Task Validation**: Validate all input paths
   ```python
   # Already implemented in tasks
   if not os.path.exists(video_path):
       raise FileNotFoundError(f"Video file not found: {video_path}")
   ```

## Maintenance

### Daily
- Monitor queue lengths via Flower dashboard
- Check disk space in temp directories
- Review error logs

### Weekly
- Verify beat scheduler is running cleanup tasks
- Check resource utilization trends
- Review failed task logs

### Monthly
- Update Celery and dependencies
- Review and optimize task routing
- Audit system resource allocation

## Support

For issues or questions:
1. Check logs: `/var/log/celery/worker.log`
2. Review Celery documentation: https://docs.celeryq.dev/
3. Monitor with Flower: http://localhost:5555

## License

Production-ready code for geminivideo project.
