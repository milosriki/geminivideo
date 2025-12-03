# Titan-Core Master API - Quick Start Guide

## What You Got

A production-ready FastAPI application at `/home/user/geminivideo/services/titan-core/api/main.py` that integrates:

### AI Council Components
- **CouncilOfTitans**: 4-model ensemble (Gemini, Claude, GPT-4o, DeepCTR)
- **OracleAgent**: 8-engine ROAS prediction system
- **DirectorAgentV2**: AI-powered blueprint generation

### PRO Video Processing
- GPU-accelerated rendering from `services/video-agent/pro`
- Auto-captions (Hormozi style)
- Smart cropping for multiple platforms
- Motion graphics and transitions

## Files Created

```
/home/user/geminivideo/services/titan-core/api/
├── main.py                  # 🎯 Master API Router (944 lines)
├── example_client.py        # Python client examples
├── test_api.py             # Unit tests
├── start_api.sh            # Quick start script
├── Dockerfile              # Docker image
├── docker-compose.yml      # Docker Compose config
├── .env.example           # Environment template
└── README.md              # Full documentation
```

## 5-Minute Quick Start

### 1. Set Your API Keys

```bash
cd /home/user/geminivideo/services/titan-core/api

# Copy environment template
cp .env.example .env

# Edit .env and add your keys
nano .env
```

Required keys:
- `GEMINI_API_KEY` - For Gemini models
- `OPENAI_API_KEY` - For GPT-4o
- `ANTHROPIC_API_KEY` - For Claude

### 2. Start the API

```bash
# Method 1: Using the start script (easiest)
./start_api.sh

# Method 2: Direct Python
python main.py

# Method 3: With uvicorn (development)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Method 4: Docker (production)
docker-compose up -d
```

### 3. Test It Works

```bash
# Health check
curl http://localhost:8000/health

# System status
curl http://localhost:8000/status

# Open API docs in browser
open http://localhost:8000/docs
```

## The Main Workflow (60 seconds)

### Step 1: Generate Campaign
```bash
curl -X POST http://localhost:8000/pipeline/generate-campaign \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Elite Fitness Coaching",
    "offer": "Book your free transformation call",
    "target_avatar": "Busy professionals 30-45",
    "pain_points": ["no time", "low energy", "weight gain"],
    "desires": ["look great", "feel confident", "have energy"],
    "num_variations": 10
  }'
```

**What it does:**
1. Director generates 10 blueprint variations
2. Council evaluates each (4 AI models)
3. Oracle predicts ROAS (8 engines)
4. Returns top blueprints ranked by predicted performance

**Response:**
```json
{
  "campaign_id": "campaign_1234567890",
  "blueprints_approved": 7,
  "top_blueprints": [
    {
      "id": "var_001",
      "council_score": 92.5,
      "predicted_roas": 3.8,
      "rank": 1
    }
  ]
}
```

### Step 2: Render Winners
```bash
# Use the top blueprints from step 1
curl -X POST http://localhost:8000/pipeline/render-winning \
  -H "Content-Type: application/json" \
  -d '{
    "blueprints": [...],
    "platform": "instagram",
    "quality": "high",
    "aspect_ratio": "9:16"
  }'
```

**What it does:**
1. PRO renderer creates videos
2. Adds auto-captions (Hormozi style)
3. Smart crops for target platform
4. Returns job IDs for tracking

**Response:**
```json
{
  "job_ids": ["render_abc123", "render_def456"],
  "total_jobs": 2,
  "status": "started"
}
```

### Step 3: Check Progress & Download
```bash
# Check status
curl http://localhost:8000/render/render_abc123/status

# Download when complete
curl http://localhost:8000/render/render_abc123/download -o video.mp4
```

## Python Client Example

```python
from example_client import TitanCoreClient

client = TitanCoreClient()

# Generate campaign
campaign = client.generate_campaign(
    product_name="Elite Fitness Coaching",
    offer="Book your free call",
    target_avatar="Busy professionals 30-45",
    pain_points=["no time", "low energy"],
    desires=["look great", "feel confident"],
    num_variations=10
)

print(f"Generated {campaign['blueprints_approved']} winning blueprints")
print(f"Avg ROAS: {campaign['avg_predicted_roas']:.2f}x")

# Render top 3
top_blueprints = [bp['blueprint'] for bp in campaign['top_blueprints'][:3]]
result = client.render_winning(blueprints=top_blueprints)

print(f"Started {result['total_jobs']} render jobs")
```

## All Available Endpoints

### Health & Status
- `GET /health` - Basic health check
- `GET /status` - Detailed system status

### AI Council
- `POST /council/evaluate` - Evaluate script (4 AI models)
- `POST /oracle/predict` - Predict ROAS (8 engines)
- `POST /director/generate` - Generate blueprints

### Video Processing
- `POST /render/start` - Start single render
- `GET /render/{job_id}/status` - Get render status
- `GET /render/{job_id}/download` - Download video

### Pipeline (THE MAIN ONES) ⭐
- `POST /pipeline/generate-campaign` - Full end-to-end generation
- `POST /pipeline/render-winning` - Render top blueprints

## Architecture Overview

```
┌─────────────────────────────────────┐
│     Master API Router (main.py)     │
│         FastAPI + Uvicorn           │
└─────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Council │ │ Oracle  │ │Director │
│ 4 Models│ │8 Engines│ │Reflexion│
└─────────┘ └─────────┘ └─────────┘
                 │
                 ▼
        ┌────────────────┐
        │Ultimate Pipeline│
        └────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │  PRO Renderer  │
        │  • Captions    │
        │  • Smart Crop  │
        │  • GPU Accel   │
        └────────────────┘
```

## Production Deployment

### Docker (Recommended)
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Systemd Service
```bash
# Create service file
sudo cp titan-core-api.service /etc/systemd/system/

# Start service
sudo systemctl start titan-core-api
sudo systemctl enable titan-core-api

# Check status
sudo systemctl status titan-core-api
```

### Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring

### Health Checks
```bash
# Basic health
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/status | jq
```

### Logs
```bash
# Docker logs
docker-compose logs -f titan-core-api

# Direct logs (check working directory)
tail -f /var/log/titan-core-api.log
```

## Performance Tips

1. **Use the pipeline endpoints** (`/pipeline/*`) - they're optimized for the full workflow
2. **Enable GPU** - Set appropriate environment variables for video processing
3. **Adjust concurrent renders** - Set `MAX_CONCURRENT_RENDERS` based on your hardware
4. **Cache responses** - Consider adding Redis for caching predictions
5. **Batch operations** - Use `/pipeline/render-winning` for multiple videos

## Troubleshooting

### API Won't Start
```bash
# Check Python version (need 3.11+)
python --version

# Install dependencies
pip install -r ../requirements.txt

# Check port availability
lsof -i :8000
```

### AI Council Not Available
```bash
# Check API keys are set
echo $GEMINI_API_KEY
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Check imports
python -c "from ai_council import CouncilOfTitans"
```

### Video Rendering Fails
```bash
# Check FFmpeg is installed
ffmpeg -version

# Check GPU availability (optional but recommended)
nvidia-smi

# Check output directory exists and is writable
ls -la /tmp/titan-core/outputs
```

### 503 Service Unavailable
- Component not initialized
- Check `/status` endpoint to see which component is down
- Verify API keys are correct
- Check logs for detailed error messages

## Next Steps

1. **Try the examples**: Run `python example_client.py`
2. **Read full docs**: Check `README.md` for complete API documentation
3. **Run tests**: Execute `pytest test_api.py -v`
4. **Customize config**: Edit `.env` for your production settings
5. **Add monitoring**: Integrate with Prometheus/Grafana

## Support Resources

- **API Documentation**: http://localhost:8000/docs
- **Full README**: `README.md`
- **Example Client**: `example_client.py`
- **Unit Tests**: `test_api.py`

---

**You're ready to generate winning ads with AI! 🚀**

Run: `./start_api.sh` and visit http://localhost:8000/docs
