# Quick Start Guide - Gemini Video AI Suite

Get up and running with the complete AI Ad Intelligence & Creation Suite in minutes.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose installed (usually comes with Docker Desktop)
- At least 8GB RAM available
- 10GB free disk space

## Step 1: Start All Services

The easiest way to get started is using our automated script:

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/milosriki/geminivideo.git
cd geminivideo

# Make scripts executable
chmod +x scripts/start-all.sh scripts/test-connections.sh

# Start everything
./scripts/start-all.sh
```

This script will:
1. ✅ Stop any existing services
2. ✅ Build all Docker images
3. ✅ Start all 5 services
4. ✅ Test connections between services
5. ✅ Display service URLs

**Alternative - Manual Start:**
```bash
docker-compose up -d --build
```

## Step 2: Verify Services Are Running

After starting, you should see:

```
✓ Drive Intel is healthy
✓ Video Agent is healthy
✓ Meta Publisher is healthy
✓ Gateway API is healthy
✓ Frontend is healthy
✓ Gateway can reach Drive Intel
✓ Gateway can reach Meta Publisher
```

**Service URLs:**
- 🎨 **Frontend Dashboard**: http://localhost:3000
- 🚪 **Gateway API**: http://localhost:8000
- 🎬 **Drive Intel**: http://localhost:8001
- 🎥 **Video Agent**: http://localhost:8002
- 📱 **Meta Publisher**: http://localhost:8003

## Step 3: Access the Dashboard

Open your browser and go to:
```
http://localhost:3000
```

You'll see 8 dashboard panels:
1. **Assets & Ingest** - Upload videos
2. **Ranked Clips** - View scored scenes
3. **Semantic Search** - Find clips by description
4. **Analysis** - Comprehensive scoring
5. **Compliance** - Platform checks
6. **Diversification** - Content variety metrics
7. **Reliability** - Prediction accuracy
8. **Render Job** - Create final videos

## Step 4: Ingest Your First Video

### Option A: Using the Web UI

1. Go to **Assets & Ingest** panel
2. Enter the path to your video folder: `/data/inputs`
3. Click **Ingest Folder**

### Option B: Using the API

```bash
# Copy a video to the input directory
docker cp /path/to/your/video.mp4 geminivideo-drive-intel-1:/app/data/inputs/

# Trigger ingestion via API
curl -X POST http://localhost:8000/api/ingest/local/folder \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "/app/data/inputs"}'
```

## Step 5: View Results

After ingestion completes:

1. **Go to Ranked Clips panel** - See automatically scored scenes
2. **Try Semantic Search** - Search "person exercising"
3. **View Analysis** - Check psychology and hook scores
4. **Create a Render** - Generate multi-format videos

## Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f gateway-api
docker-compose logs -f drive-intel
```

### Stop Services
```bash
docker-compose down
```

### Restart a Service
```bash
docker-compose restart gateway-api
```

### Check Service Health
```bash
curl http://localhost:8000/health    # Gateway
curl http://localhost:8001/health    # Drive Intel
curl http://localhost:8002/health    # Video Agent
curl http://localhost:8003/health    # Meta Publisher
```

## Test the System

### 1. List Assets
```bash
curl http://localhost:8000/api/assets
```

### 2. Score a Storyboard
```bash
curl -X POST http://localhost:8000/api/score/storyboard \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": [{
      "features": {
        "text_detected": ["Transform your body in 30 days"],
        "motion_score": 0.7
      }
    }],
    "metadata": {}
  }'
```

### 3. Check Diversification Metrics
```bash
curl http://localhost:8000/api/metrics/diversification
```

### 4. Check Reliability Metrics
```bash
curl http://localhost:8000/api/metrics/reliability
```

## Production Deployment

For production deployment to Google Cloud Platform:

```bash
# Configure GCP project
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"

# Deploy to Cloud Run
./scripts/deploy.sh
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete GCP setup instructions.

## Troubleshooting

### Services Won't Start

**Check Docker:**
```bash
docker --version
docker-compose --version
docker ps
```

**Check Logs:**
```bash
docker-compose logs drive-intel
docker-compose logs gateway-api
```

### Port Conflicts

If ports are already in use:

1. Edit `docker-compose.yml`
2. Change port mappings (e.g., "8000:8000" → "8080:8000")
3. Restart services

### Connection Refused

Wait 30-60 seconds for services to fully initialize, especially on first run when Docker images are being built.

### Out of Memory

Increase Docker Desktop memory allocation:
- Mac: Docker Desktop → Settings → Resources → Memory (recommend 8GB)
- Windows: Docker Desktop → Settings → Resources → Memory (recommend 8GB)

## Next Steps

1. **Add Sample Videos** - Ingest fitness/training videos
2. **Experiment with Scoring** - Try different content types
3. **Create Renders** - Generate multi-format ads
4. **Configure Meta** - Set META_ACCESS_TOKEN for live publishing
5. **Monitor Learning** - Track prediction accuracy

## Configuration

All settings are in `shared/config/`:
- `scene_ranking.yaml` - Ranking weights
- `weights.yaml` - Scoring weights (auto-updated)
- `triggers_config.json` - Psychology keywords
- `personas.json` - Target audiences
- `hook_templates.json` - Overlay templates

Edit these files and restart services to apply changes.

## Support

- **Documentation**: See README.md, DEPLOYMENT.md, SECURITY.md
- **Issues**: https://github.com/milosriki/geminivideo/issues
- **Epic #2**: All sub-issues (#12-#18)

## Architecture Overview

```
┌──────────────┐
│   Browser    │
│  Port 3000   │
└──────┬───────┘
       │
┌──────▼────────────┐
│   Gateway API     │
│   Port 8000       │
│  (Scoring Engine) │
└──┬────┬────┬──────┘
   │    │    │
   │    │    └────► Meta Publisher (8003)
   │    │           Marketing API
   │    │
   │    └─────────► Video Agent (8002)
   │               FFmpeg Rendering
   │
   └──────────────► Drive Intel (8001)
                    Scene Analysis
```

All services communicate via Docker network and are fully connected!
