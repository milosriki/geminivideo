# Celery Task Queue - Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Install Dependencies

```bash
cd /home/user/geminivideo

# Install Celery and dependencies
pip install -r services/video-agent/pro/requirements_celery.txt

# Optional: Install Whisper for caption generation
# pip install openai-whisper

# Optional: Install Flower for monitoring
# pip install flower
```

### Step 2: Start All Services (Automatic)

```bash
# Start everything (Redis, workers, beat, flower)
./services/video-agent/pro/start_celery.sh all

# Check status
./services/video-agent/pro/start_celery.sh status
```

**That's it!** Your distributed task queue is now running.

---

## 🧪 Test the System

```bash
# Run the test suite
python3 services/video-agent/pro/test_celery.py
```

This will:
- ✓ Test Redis connection
- ✓ Check worker status
- ✓ Display system resources (CPU, GPU, memory)
- ✓ Submit test tasks
- ✓ Verify task execution

---

## 📊 Access Monitoring Dashboard

Open in browser: **http://localhost:5555**

The Flower dashboard shows:
- Active workers
- Task queues and lengths
- Task success/failure rates
- Real-time task execution
- Worker resource usage

---

## 💻 Submit Your First Task

### Python Script

```python
from services.video_agent.pro.celery_app import render_video_task

# Define your render job
job_data = {
    'scenes': [
        {
            'video_path': '/path/to/video1.mp4',
            'start_time': 0,
            'end_time': 10
        },
        {
            'video_path': '/path/to/video2.mp4',
            'start_time': 5,
            'end_time': 15
        }
    ],
    'output_format': {
        'width': 1920,
        'height': 1080,
        'fps': 30
    },
    'transitions': True,
    'use_gpu': True  # Enable GPU if available
}

# Submit the task
result = render_video_task.apply_async(args=[job_data], priority=9)

# Get the task ID
task_id = result.id
print(f"Task submitted: {task_id}")

# Wait for result (blocking)
output = result.get(timeout=3600)
print(f"✓ Render complete!")
print(f"  Output: {output['output_path']}")
print(f"  Size: {output['file_size'] / (1024**2):.2f} MB")
print(f"  Duration: {output['duration']:.2f}s")
```

### Via REST API

```bash
# Start the FastAPI server
uvicorn services.video-agent.pro.api_example:app --host 0.0.0.0 --port 8000

# Submit a render job
curl -X POST http://localhost:8000/api/render \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": [
      {"video_path": "/path/to/video1.mp4", "start_time": 0, "end_time": 10},
      {"video_path": "/path/to/video2.mp4", "start_time": 5, "end_time": 15}
    ],
    "output_format": {"width": 1920, "height": 1080, "fps": 30},
    "transitions": true,
    "use_gpu": true,
    "priority": 9
  }'

# Check task status
curl http://localhost:8000/api/task/{task_id}

# View API docs
# Open: http://localhost:8000/docs
```

---

## 🎯 Available Tasks

### 1. Render Video
Concatenate scenes with transitions and effects
```python
from services.video_agent.pro.celery_app import render_video_task
result = render_video_task.apply_async(args=[job_data])
```

### 2. Generate Previews
Extract thumbnail frames
```python
from services.video_agent.pro.celery_app import generate_preview_task
result = generate_preview_task.apply_async(
    args=['/path/to/video.mp4'],
    kwargs={'num_frames': 10}
)
```

### 3. Transcode Video
Convert to different format
```python
from services.video_agent.pro.celery_app import transcode_task
result = transcode_task.apply_async(
    args=['/path/to/input.mp4', {
        'codec': 'h264',
        'container': 'mp4',
        'width': 1280,
        'height': 720
    }]
)
```

### 4. Generate Captions
Whisper speech-to-text
```python
from services.video_agent.pro.celery_app import caption_task
result = caption_task.apply_async(
    args=['/path/to/video.mp4'],
    kwargs={'model': 'base'}
)
```

### 5. Batch Render
Process multiple videos in parallel
```python
from services.video_agent.pro.celery_app import batch_render_task
result = batch_render_task.apply_async(args=[[job1, job2, job3]])
```

### 6. Cleanup
Remove old temporary files
```python
from services.video_agent.pro.celery_app import cleanup_task
result = cleanup_task.apply_async(
    kwargs={'max_age_days': 7, 'max_size_gb': 50}
)
```

---

## 📈 Real-Time Progress Tracking

### Python (Redis Pub/Sub)

```python
import redis
import json

redis_client = redis.from_url('redis://localhost:6379/0', decode_responses=True)

# Subscribe to progress updates
pubsub = redis_client.pubsub()
pubsub.subscribe(f'task_progress:{task_id}')

for message in pubsub.listen():
    if message['type'] == 'message':
        data = json.loads(message['data'])
        print(f"Progress: {data['progress']}% - {data['message']}")

        if data['status'] in ['completed', 'failed']:
            break
```

### JavaScript (WebSocket)

```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/progress/${taskId}`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`Progress: ${data.progress}% - ${data.message}`);

    if (data.status === 'completed') {
        console.log('Task completed!');
        ws.close();
    }
};
```

---

## 🔧 Manual Component Control

### Start Individual Components

```bash
# Start Redis only
./services/video-agent/pro/start_celery.sh redis

# Start general worker
./services/video-agent/pro/start_celery.sh worker

# Start GPU worker (if you have NVIDIA GPU)
./services/video-agent/pro/start_celery.sh worker-gpu

# Start beat scheduler (for periodic tasks)
./services/video-agent/pro/start_celery.sh beat

# Start Flower monitoring
./services/video-agent/pro/start_celery.sh flower
```

### Stop Services

```bash
# Stop all components
./services/video-agent/pro/start_celery.sh stop
```

### View Logs

```bash
# View worker logs
./services/video-agent/pro/start_celery.sh logs worker

# View beat logs
./services/video-agent/pro/start_celery.sh logs beat

# View flower logs
./services/video-agent/pro/start_celery.sh logs flower
```

---

## 🎛️ Advanced Configuration

### Environment Variables

```bash
# Redis connection
export REDIS_URL="redis://localhost:6379/0"

# Directories
export TEMP_DIR="/tmp/video-processing"
export RENDER_DIR="/tmp/renders"
export PREVIEW_DIR="/tmp/previews"

# Task timeouts (seconds)
export RENDER_TIMEOUT=3600      # 1 hour
export PREVIEW_TIMEOUT=300      # 5 minutes
export TRANSCODE_TIMEOUT=1800   # 30 minutes
export CAPTION_TIMEOUT=900      # 15 minutes

# Cleanup settings
export CLEANUP_AGE_DAYS=7
export MAX_TEMP_SIZE_GB=50
```

### Worker Types

```bash
# High-performance render worker (uses all CPU cores)
celery -A services.video-agent.pro.celery_app worker \
    -Q render_queue \
    --concurrency=8 \
    --hostname=render-heavy@%h

# GPU-accelerated worker (one task at a time)
celery -A services.video-agent.pro.celery_app worker \
    -Q render_queue \
    --concurrency=1 \
    --hostname=gpu@%h

# Preview worker (I/O bound, higher concurrency)
celery -A services.video-agent.pro.celery_app worker \
    -Q preview_queue,caption_queue \
    --concurrency=16 \
    --hostname=preview@%h
```

---

## 🔍 Monitoring & Debugging

### Celery Commands

```bash
# View active tasks
celery -A services.video-agent.pro.celery_app inspect active

# View registered tasks
celery -A services.video-agent.pro.celery_app inspect registered

# View worker stats
celery -A services.video-agent.pro.celery_app inspect stats

# Purge all pending tasks
celery -A services.video-agent.pro.celery_app purge
```

### Redis Commands

```bash
# Connect to Redis
redis-cli

# View queue lengths
LLEN render_queue
LLEN preview_queue
LLEN transcode_queue
LLEN caption_queue

# View all task results
KEYS celery-task-meta-*

# Get specific task result
GET celery-task-meta-{task-id}

# Monitor live activity
MONITOR
```

---

## 🐳 Docker Deployment

```bash
# Using Docker Compose
cd /home/user/geminivideo/services/video-agent/pro

# Build and start
docker-compose up -d

# Scale workers
docker-compose up -d --scale celery-worker=5

# View logs
docker-compose logs -f celery-worker

# Stop
docker-compose down
```

See `README_CELERY.md` for complete `docker-compose.yml` configuration.

---

## 🚨 Troubleshooting

### Workers Not Starting

```bash
# Check Redis
redis-cli ping

# Check logs
tail -f /var/log/celery/worker.log

# Test Python imports
python3 -c "from services.video_agent.pro.celery_app import app; print(app)"
```

### Tasks Stuck in Pending

```bash
# Check worker status
celery -A services.video-agent.pro.celery_app inspect active

# Restart workers
./services/video-agent/pro/start_celery.sh stop
./services/video-agent/pro/start_celery.sh all
```

### GPU Not Detected

```bash
# Check NVIDIA driver
nvidia-smi

# Check CUDA
nvcc --version

# Install NVIDIA driver if missing
# Ubuntu: sudo apt-get install nvidia-driver-525
```

### Memory Issues

```bash
# Monitor memory
watch -n 1 free -h

# Reduce worker concurrency
celery -A services.video-agent.pro.celery_app worker --concurrency=2

# Enable worker memory limits
# In celery_app.py: worker_max_tasks_per_child=50
```

---

## 📚 Documentation

- **Full Documentation**: `README_CELERY.md`
- **API Examples**: `api_example.py`
- **Test Suite**: `test_celery.py`
- **Startup Script**: `start_celery.sh`

---

## ✅ Verification Checklist

- [ ] Redis is running (`redis-cli ping` returns PONG)
- [ ] At least one worker is active
- [ ] Beat scheduler is running (for periodic cleanup)
- [ ] Flower dashboard is accessible
- [ ] Test tasks execute successfully
- [ ] Progress tracking works via Redis pub/sub
- [ ] GPU is detected (if you have NVIDIA GPU)
- [ ] Logs are being written to `/var/log/celery/`

---

## 🎉 You're Ready!

Your production-ready Celery distributed task queue is now operational!

**Key Features:**
- ✅ Multiple priority queues
- ✅ GPU acceleration support
- ✅ Real-time progress tracking
- ✅ Automatic retry with exponential backoff
- ✅ Resource monitoring
- ✅ Periodic cleanup
- ✅ Rate limiting
- ✅ Web monitoring dashboard
- ✅ REST API integration
- ✅ WebSocket support

For questions or issues, check the logs:
```bash
tail -f /var/log/celery/worker.log
```

Happy video processing! 🎬
