# Titan-Core Master API

Production-ready FastAPI application integrating AI Council components and PRO video processing.

## Features

### AI Council Components
- **CouncilOfTitans**: 4-model script evaluation (Gemini, Claude, GPT-4o, DeepCTR)
- **OracleAgent**: 8-engine ROAS prediction system
- **DirectorAgentV2**: Blueprint generation with Reflexion Loop

### PRO Video Processing
- GPU-accelerated rendering
- Auto-captions (Hormozi style)
- Smart cropping for multiple aspect ratios
- Platform-specific optimization

## Quick Start

### 1. Set Environment Variables

```bash
export GEMINI_API_KEY="your_gemini_api_key"
export OPENAI_API_KEY="your_openai_api_key"
export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

### 2. Start the API

```bash
# Using the start script
./start_api.sh

# Or directly with Python
python main.py

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health & Status

#### `GET /health`
Basic health check
```bash
curl http://localhost:8000/health
```

#### `GET /status`
Detailed system status with all component health
```bash
curl http://localhost:8000/status
```

### AI Council Endpoints

#### `POST /council/evaluate`
Evaluate a script with Council of Titans
```bash
curl -X POST http://localhost:8000/council/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "script": "Stop scrolling if you want to lose 20lbs in 90 days. We help busy professionals transform their bodies without spending hours in the gym. Book your free call now.",
    "visual_features": {
      "has_human_face": true,
      "hook_type": "pattern_interrupt"
    }
  }'
```

#### `POST /oracle/predict`
Get ROAS prediction from Oracle Agent
```bash
curl -X POST http://localhost:8000/oracle/predict \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "test_001",
    "features": {
      "hook_effectiveness": 8.5,
      "has_transformation": true,
      "cta_strength": 7.0,
      "num_emotional_triggers": 3
    }
  }'
```

#### `POST /director/generate`
Generate ad blueprints with Director Agent
```bash
curl -X POST http://localhost:8000/director/generate \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Elite Fitness Coaching",
    "offer": "Book your free transformation call",
    "target_avatar": "Busy professionals 30-45",
    "pain_points": ["no time for gym", "low energy", "weight gain"],
    "desires": ["look great", "feel confident", "have energy"],
    "num_variations": 10
  }'
```

### Video Processing Endpoints

#### `POST /render/start`
Start a render job
```bash
curl -X POST http://localhost:8000/render/start \
  -H "Content-Type: application/json" \
  -d '{
    "blueprint": {
      "id": "bp_001",
      "hook_text": "Stop scrolling if you want to lose 20lbs",
      "cta_text": "Book your free call now"
    },
    "platform": "instagram",
    "quality": "high",
    "aspect_ratio": "9:16"
  }'
```

#### `GET /render/{job_id}/status`
Get render job status
```bash
curl http://localhost:8000/render/render_abc123/status
```

#### `GET /render/{job_id}/download`
Download completed video
```bash
curl http://localhost:8000/render/render_abc123/download -o video.mp4
```

### Pipeline Endpoints (THE MAIN ONES)

#### `POST /pipeline/generate-campaign` ⭐
**Full end-to-end campaign generation**

This is the complete AI-powered ad generation pipeline:
1. Director generates N blueprint variations
2. Council evaluates each (approve if score > threshold)
3. Oracle predicts ROAS for approved blueprints
4. Returns ranked blueprints ready for rendering

```bash
curl -X POST http://localhost:8000/pipeline/generate-campaign \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Elite Fitness Coaching",
    "offer": "Book your free transformation call",
    "target_avatar": "Busy professionals 30-45 who want to get back in shape",
    "pain_points": [
      "no time for gym",
      "low energy",
      "gaining weight",
      "feel out of shape"
    ],
    "desires": [
      "look great",
      "feel confident",
      "have more energy",
      "be proud of their body"
    ],
    "num_variations": 20,
    "approval_threshold": 85.0,
    "platforms": ["instagram", "tiktok"]
  }'
```

**Response:**
```json
{
  "campaign_id": "campaign_1234567890",
  "status": "completed",
  "blueprints_generated": 20,
  "blueprints_approved": 12,
  "blueprints_rejected": 8,
  "top_blueprints": [
    {
      "id": "var_001",
      "council_score": 92.5,
      "predicted_roas": 3.8,
      "confidence": "high",
      "rank": 1,
      "blueprint": { ... }
    },
    ...
  ],
  "avg_council_score": 87.3,
  "avg_predicted_roas": 2.9,
  "duration_seconds": 45.2
}
```

#### `POST /pipeline/render-winning` ⭐
**Render the top blueprints**

Use this after `/pipeline/generate-campaign` to render the winning blueprints:
1. PRO Renderer produces videos
2. Auto-captions with Hormozi style
3. Smart crop to target aspect ratio
4. Returns job IDs for tracking

```bash
curl -X POST http://localhost:8000/pipeline/render-winning \
  -H "Content-Type: application/json" \
  -d '{
    "blueprints": [ ... top blueprints from generate-campaign ... ],
    "platform": "instagram",
    "quality": "high",
    "aspect_ratio": "9:16",
    "max_concurrent": 5
  }'
```

**Response:**
```json
{
  "job_ids": [
    "render_abc123",
    "render_def456",
    "render_ghi789"
  ],
  "total_jobs": 3,
  "status": "started",
  "message": "Started 3 render jobs"
}
```

## Complete Workflow Example

### 1. Generate Campaign
```bash
CAMPAIGN=$(curl -X POST http://localhost:8000/pipeline/generate-campaign \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Elite Fitness Coaching",
    "offer": "Book your free call",
    "target_avatar": "Busy professionals 30-45",
    "pain_points": ["no time", "low energy", "weight gain"],
    "desires": ["look great", "feel confident", "have energy"],
    "num_variations": 10
  }')

echo $CAMPAIGN
```

### 2. Extract Top Blueprints
```bash
# Extract top 3 blueprints from the response
TOP_BLUEPRINTS=$(echo $CAMPAIGN | jq '.top_blueprints[:3]')
```

### 3. Render Winners
```bash
RENDER_JOBS=$(curl -X POST http://localhost:8000/pipeline/render-winning \
  -H "Content-Type: application/json" \
  -d "{
    \"blueprints\": $TOP_BLUEPRINTS,
    \"platform\": \"instagram\",
    \"quality\": \"high\",
    \"aspect_ratio\": \"9:16\"
  }")

echo $RENDER_JOBS
```

### 4. Check Render Status
```bash
# Extract first job ID
JOB_ID=$(echo $RENDER_JOBS | jq -r '.job_ids[0]')

# Check status
curl http://localhost:8000/render/$JOB_ID/status

# Download when complete
curl http://localhost:8000/render/$JOB_ID/download -o winner_1.mp4
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `API_HOST` | API host | `0.0.0.0` |
| `API_PORT` | API port | `8000` |
| `DEBUG` | Debug mode | `false` |
| `OUTPUT_DIR` | Output directory | `/tmp/titan-core/outputs` |
| `CACHE_DIR` | Cache directory | `/tmp/titan-core/cache` |
| `MAX_CONCURRENT_RENDERS` | Max concurrent renders | `5` |
| `DEFAULT_NUM_VARIATIONS` | Default variations | `10` |
| `APPROVAL_THRESHOLD` | Council approval threshold | `85.0` |
| `CORS_ORIGINS` | CORS origins (comma-separated) | `*` |

## Error Handling

The API uses standard HTTP status codes:
- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error
- `503` - Service Unavailable

All errors return JSON with `detail` and `message` fields:
```json
{
  "detail": "Detailed error information",
  "message": "Human-readable error message"
}
```

## Request Logging

All requests are logged with unique request IDs:
```
2024-01-15 10:30:45 - main - INFO - [abc-123] POST /pipeline/generate-campaign
2024-01-15 10:31:02 - main - INFO - [abc-123] Status: 200
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Master API Router                     │
│                     (FastAPI)                            │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ AI Council   │  │   Oracle     │  │   Director   │
│              │  │   Agent      │  │   Agent      │
│ • Gemini     │  │              │  │              │
│ • GPT-4o     │  │ 8 Engines    │  │ Reflexion    │
│ • Claude     │  │              │  │ Loop         │
│ • DeepCTR    │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                  ┌──────────────────┐
                  │  Ultimate        │
                  │  Pipeline        │
                  └──────────────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │  PRO Video       │
                  │  Processing      │
                  │                  │
                  │ • Rendering      │
                  │ • Captions       │
                  │ • Smart Crop     │
                  └──────────────────┘
```

## Production Deployment

### Using Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Using Gunicorn
```bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### Using systemd
```ini
[Unit]
Description=Titan-Core Master API
After=network.target

[Service]
Type=simple
User=titan-core
WorkingDirectory=/opt/titan-core/api
Environment="PATH=/opt/titan-core/venv/bin"
ExecStart=/opt/titan-core/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## Monitoring

### Health Check Endpoint
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/status
```

### Prometheus Metrics
Add `prometheus-fastapi-instrumentator` for metrics:
```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

## Support

For issues or questions:
- Check the API docs: http://localhost:8000/docs
- Review the logs for detailed error messages
- Ensure all API keys are set correctly

## License

Proprietary - Titan-Core Team
