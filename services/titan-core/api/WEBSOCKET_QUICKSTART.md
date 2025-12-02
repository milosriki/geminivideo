# WebSocket Progress Service - Quick Start

## 1-Minute Setup

```bash
# Install dependencies
pip install redis[hiredis] websockets

# Start Redis
docker-compose up redis

# Test it works
python api/test_websocket.py
```

## Basic Usage

### Report Progress (Server-Side)

```python
from api.websocket import ProgressReporter

async def my_job(job_id: str):
    reporter = ProgressReporter()
    await reporter.initialize()

    try:
        # Start
        await reporter.report(job_id, "processing", 0.0, "Starting...")

        # Update
        await reporter.report(job_id, "processing", 0.5, "Halfway...")

        # Complete
        await reporter.report_complete(job_id, {"url": "https://..."})

    except Exception as e:
        await reporter.report_error(job_id, str(e))
    finally:
        await reporter.close()
```

### Subscribe to Progress (Client-Side)

```javascript
const ws = new WebSocket(`ws://localhost:8084/ws/jobs/${jobId}`);

ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    console.log(`${data.progress * 100}%: ${data.message}`);

    if (data.status === 'completed') {
        console.log('Done!', data.result);
    }
};
```

## WebSocket Endpoint

```
ws://server:8084/ws/jobs/{job_id}
```

## Message Types

```javascript
// Progress
{ status: "processing", stage: "rendering", progress: 0.5, message: "..." }

// Complete
{ status: "completed", progress: 1.0, result: {...} }

// Error
{ status: "failed", error: "...", message: "..." }

// Ping
{ type: "ping", message: "keepalive" }
```

## Common Stages

- `rendering` - Video rendering
- `captioning` - Caption generation
- `cropping` - Video cropping
- `uploading` - File upload
- `processing` - General work
- `analyzing` - AI analysis

## FastAPI Integration

```python
from fastapi import BackgroundTasks
from api.websocket import ProgressReporter
import uuid

@app.post("/jobs")
async def create_job(bg: BackgroundTasks):
    job_id = str(uuid.uuid4())
    bg.add_task(my_job, job_id)
    return {"job_id": job_id, "ws": f"/ws/jobs/{job_id}"}
```

## Test It

```bash
# Terminal 1: Start API
python run_api.py

# Terminal 2: Run example
python -m api.websocket_example

# Browser: Open websocket_client.html
```

## Cheat Sheet

```python
# Initialize
reporter = ProgressReporter()
await reporter.initialize()

# Report progress (0.0 to 1.0)
await reporter.report(job_id, stage, progress, message)

# Add metadata
await reporter.report(
    job_id, "rendering", 0.5, "Working...",
    metadata={"frame": 100, "fps": 30}
)

# Error
await reporter.report_error(job_id, "Something broke")

# Complete
await reporter.report_complete(job_id, {"result": "data"})

# Check status
status = await reporter.get_status(job_id)

# Cleanup
await reporter.close()
```

## Full Docs

See `WEBSOCKET_README.md` for complete documentation.
