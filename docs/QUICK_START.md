# GeminiVideo - 5-Minute Quick Start Guide

Get GeminiVideo running locally in 5 minutes with Docker Compose.

## Prerequisites

Before you begin, ensure you have:

- **Docker Desktop** (v20.10+) - [Download here](https://www.docker.com/products/docker-desktop/)
- **Docker Compose** (v2.0+) - Included with Docker Desktop
- **Git** - For cloning the repository
- **At least 8GB RAM** and **10GB disk space**
- **Python 3.11+** (optional - for running validation scripts)
- **Node.js 18+** (optional - for local development without Docker)

### Quick Prerequisites Check

```bash
# Verify installations
docker --version          # Should be 20.10+
docker compose version    # Should be v2.0+
git --version
```

## Step 1: Clone and Setup (1 minute)

```bash
# Clone the repository
git clone https://github.com/milosriki/geminivideo.git
cd geminivideo

# Copy environment template
cp .env.example .env
```

## Step 2: Configure Environment Variables (2 minutes)

Open `.env` in your text editor and configure the **minimum required** variables:

### Required API Keys

```bash
# AI Model API Keys (REQUIRED)
GEMINI_API_KEY=your_actual_gemini_api_key_here
OPENAI_API_KEY=your_actual_openai_api_key_here
ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here

# Database (uses Docker defaults - no change needed for local dev)
DATABASE_URL=postgresql://geminivideo:geminivideo@postgres:5432/geminivideo

# Redis (uses Docker defaults - no change needed for local dev)
REDIS_URL=redis://redis:6379
```

### Optional API Keys (for full functionality)

```bash
# Meta Ads Integration (Optional - for publishing to Facebook/Instagram)
META_ACCESS_TOKEN=your_meta_access_token
META_AD_ACCOUNT_ID=act_1234567890
META_PAGE_ID=1234567890
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_CLIENT_TOKEN=your_meta_client_token

# AI Video Generation (Optional - for next-gen video creation)
RUNWAY_API_KEY=your_runway_api_key        # Recommended for production
KLING_API_KEY=your_kling_api_key          # Good for realistic motion
PIKA_API_KEY=your_pika_api_key            # Fast generation

# Voice Generation (Optional - for AI voiceovers)
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Google Cloud (Optional - for Drive integration)
GCP_PROJECT_ID=your_gcp_project_id
GCS_BUCKET_NAME=your_gcs_bucket_name
```

### Where to Get API Keys

| Service | Where to Get | Required? | Purpose |
|---------|--------------|-----------|---------|
| **Gemini API** | [Google AI Studio](https://makersuite.google.com/app/apikey) | ✅ Yes | AI analysis and content scoring |
| **OpenAI API** | [OpenAI Platform](https://platform.openai.com/api-keys) | ✅ Yes | AI embeddings and TTS |
| **Anthropic API** | [Anthropic Console](https://console.anthropic.com/) | ✅ Yes | AI reasoning and analysis |
| **Meta Access Token** | [Meta for Developers](https://developers.facebook.com/) | ⚠️ For publishing | Publish to Facebook/Instagram |
| **Runway API** | [Runway ML](https://runwayml.com/) | Optional | AI video generation |
| **ElevenLabs API** | [ElevenLabs](https://elevenlabs.io/) | Optional | AI voiceovers |

## Step 3: Start All Services (1 minute)

```bash
# Start all services with Docker Compose
docker compose up -d --build

# This will start:
# - PostgreSQL database (port 5432)
# - Redis cache (port 6379)
# - ML Service (port 8003)
# - Titan Core (port 8084)
# - Video Agent (port 8082)
# - Drive Intel (port 8081)
# - Meta Publisher (port 8083)
# - TikTok Ads (port 8085)
# - Gateway API (port 8080)
# - Frontend Dashboard (port 3000)
# - Background Workers (drive-worker, video-worker)
```

### Monitor Startup Progress

```bash
# Watch logs from all services
docker compose logs -f

# Or watch specific services
docker compose logs -f gateway-api
docker compose logs -f ml-service
docker compose logs -f frontend

# Check service health
docker compose ps
```

**Expected output:**
```
NAME                           STATUS              PORTS
geminivideo-postgres          running (healthy)   0.0.0.0:5432->5432/tcp
geminivideo-redis             running (healthy)   0.0.0.0:6379->6379/tcp
geminivideo-ml-service        running (healthy)   0.0.0.0:8003->8003/tcp
geminivideo-titan-core        running (healthy)   0.0.0.0:8084->8084/tcp
geminivideo-video-agent       running (healthy)   0.0.0.0:8082->8082/tcp
geminivideo-drive-intel       running (healthy)   0.0.0.0:8081->8081/tcp
geminivideo-meta-publisher    running (healthy)   0.0.0.0:8083->8083/tcp
geminivideo-tiktok-ads        running (healthy)   0.0.0.0:8085->8085/tcp
geminivideo-gateway-api       running (healthy)   0.0.0.0:8080->8080/tcp
geminivideo-frontend          running (healthy)   0.0.0.0:3000->80/tcp
geminivideo-drive-worker      running
geminivideo-video-worker      running
```

## Step 4: Verify Installation (1 minute)

### Access the Applications

Open in your browser:

- **Frontend Dashboard**: http://localhost:3000
- **Gateway API**: http://localhost:8080/health
- **API Documentation**: http://localhost:8080/docs (if available)

### Health Check All Services

```bash
# Gateway API
curl http://localhost:8080/health

# ML Service
curl http://localhost:8003/health

# Titan Core
curl http://localhost:8084/health

# Video Agent
curl http://localhost:8082/health

# Drive Intel
curl http://localhost:8081/health

# Meta Publisher
curl http://localhost:8083/health

# TikTok Ads
curl http://localhost:8085/health
```

**Expected response from each:**
```json
{
  "status": "healthy",
  "service": "gateway-api",
  "timestamp": "2025-12-06T..."
}
```

### Run Validation Script

```bash
# Full system validation
python3 scripts/final_validation.py

# Expected output:
# ✅ VALIDATION PASSED - System is production-ready
```

## Step 5: First API Call - Score Content (30 seconds)

### Test the Scoring Engine

```bash
# Score a sample storyboard
curl -X POST http://localhost:8080/api/score/storyboard \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": [
      {
        "clip_id": "test_001",
        "start_time": 0,
        "end_time": 3,
        "text": "Lose 10 pounds in 30 days",
        "features": {
          "has_face": true,
          "motion_energy": 0.8,
          "text_length": 24
        }
      }
    ],
    "metadata": {
      "target_audience": "fitness_beginners",
      "format": "reels"
    }
  }'
```

**Expected response:**
```json
{
  "composite_score": 0.78,
  "predicted_ctr_band": "high",
  "confidence": 0.85,
  "breakdown": {
    "psychology_score": 0.82,
    "hook_strength": 0.75,
    "technical_score": 0.80,
    "demographic_match": 0.76,
    "novelty_score": 0.70
  },
  "recommendations": [
    "Strong hook with numbers in first 3 seconds",
    "Pain point language detected",
    "Good motion energy"
  ]
}
```

### Test Campaign Creation

```bash
# Create a test campaign
curl -X POST http://localhost:8080/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Fitness Campaign",
    "objective": "CONVERSIONS",
    "budget": 100,
    "target_audience": "fitness_beginners",
    "status": "DRAFT"
  }'
```

### Test Video Analysis

```bash
# Analyze video (requires video file)
curl -X POST http://localhost:8081/api/analyze \
  -F "video=@/path/to/your/video.mp4"
```

## Step 6: Explore the Dashboard

Navigate to **http://localhost:3000** and explore:

1. **Dashboard** - Overview of campaigns and performance
2. **Campaigns** - Create and manage ad campaigns
3. **Creatives** - Upload and score video content
4. **Analytics** - View performance metrics and insights
5. **A/B Tests** - Run experiments and optimize
6. **Settings** - Configure integrations and preferences

### Quick Workflow Example

1. **Upload a video** → Navigate to Creatives → Upload Video
2. **Get AI score** → System analyzes and scores automatically
3. **Create campaign** → Use scored creative in a campaign
4. **Publish to Meta** → One-click publish to Facebook/Instagram (requires Meta API keys)
5. **Track performance** → View real-time analytics

## Common Docker Commands

```bash
# View running services
docker compose ps

# View logs
docker compose logs -f [service-name]

# Restart a service
docker compose restart [service-name]

# Stop all services
docker compose down

# Stop and remove all data (CAUTION: deletes database)
docker compose down -v

# Rebuild specific service
docker compose up -d --build [service-name]

# Execute command in running container
docker compose exec [service-name] sh

# View resource usage
docker stats
```

## Troubleshooting

### Issue: Services won't start

**Solution 1: Check Docker resources**
```bash
# Ensure Docker has enough memory (8GB minimum)
docker system info | grep Memory
```

**Solution 2: Check port conflicts**
```bash
# Check if ports are already in use
netstat -an | grep -E '3000|5432|6379|8080|8081|8082|8083|8084|8085'
# or on macOS
lsof -i :3000
lsof -i :8080
```

**Solution 3: Clean Docker state**
```bash
# Remove old containers and rebuild
docker compose down -v
docker system prune -f
docker compose up -d --build
```

### Issue: Database connection errors

**Symptoms:**
```
Error: connect ECONNREFUSED 127.0.0.1:5432
```

**Solution:**
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Check PostgreSQL logs
docker compose logs postgres

# Wait for PostgreSQL to be healthy
docker compose up -d postgres
docker compose ps postgres  # Wait for (healthy) status

# Restart dependent services
docker compose restart gateway-api ml-service video-agent
```

### Issue: Redis connection errors

**Symptoms:**
```
Error: Redis connection failed
```

**Solution:**
```bash
# Verify Redis is running
docker compose ps redis

# Test Redis connection
docker compose exec redis redis-cli ping
# Should return: PONG

# Restart services that depend on Redis
docker compose restart gateway-api titan-core
```

### Issue: Frontend shows 404 or connection errors

**Symptoms:**
- Frontend loads but API calls fail
- CORS errors in browser console

**Solution:**
```bash
# Check if gateway-api is running
curl http://localhost:8080/health

# Check frontend environment variables
docker compose exec frontend env | grep VITE_API_BASE_URL
# Should be: http://localhost:8080

# Rebuild frontend with correct env vars
docker compose up -d --build frontend
```

### Issue: Health checks failing

**Symptoms:**
```
unhealthy status in docker compose ps
```

**Solution:**
```bash
# Check service logs for specific errors
docker compose logs [service-name]

# Common fixes:
# 1. Environment variable missing
docker compose exec [service-name] env

# 2. Service not listening on expected port
docker compose exec [service-name] netstat -tlnp

# 3. Dependencies not ready - restart in order
docker compose up -d postgres redis
# Wait 10 seconds
docker compose up -d ml-service titan-core video-agent drive-intel
# Wait 20 seconds
docker compose up -d meta-publisher tiktok-ads gateway-api frontend
```

### Issue: Out of disk space

**Symptoms:**
```
Error: no space left on device
```

**Solution:**
```bash
# Check Docker disk usage
docker system df

# Clean up unused images and containers
docker system prune -a
docker volume prune

# Remove old build cache
docker builder prune -a
```

### Issue: Slow build times

**Solution:**
```bash
# Use BuildKit for faster builds (already default in recent Docker versions)
DOCKER_BUILDKIT=1 docker compose build

# Build services in parallel (already default with compose)
docker compose build --parallel

# Pull pre-built images if available (future optimization)
# docker compose pull
```

### Issue: API returns authentication errors

**Symptoms:**
```json
{"error": "Invalid API key"}
```

**Solution:**
```bash
# 1. Verify .env file is in root directory
ls -la .env

# 2. Check if .env is loaded correctly
docker compose config | grep API_KEY

# 3. Restart services after updating .env
docker compose down
docker compose up -d

# 4. Verify API keys are valid (test Gemini)
curl "https://generativelanguage.googleapis.com/v1/models?key=YOUR_GEMINI_KEY"
```

### Issue: Video processing fails

**Symptoms:**
- Video upload succeeds but processing hangs
- Worker logs show errors

**Solution:**
```bash
# Check video-worker is running
docker compose ps video-worker

# Check worker logs
docker compose logs video-worker

# Ensure video file is accessible
# Videos must be in a path accessible to Docker containers

# Check disk space for temp storage
df -h /tmp

# Restart workers
docker compose restart video-worker drive-worker
```

### Issue: Cannot access Meta/TikTok APIs

**Symptoms:**
```
Error: Failed to publish to Meta
```

**Solution:**
```bash
# 1. Verify credentials in .env
grep META_ .env
grep TIKTOK_ .env

# 2. Test Meta API directly
curl -i -X GET "https://graph.facebook.com/v18.0/me?access_token=YOUR_TOKEN"

# 3. Check if services can reach external APIs
docker compose exec meta-publisher ping -c 3 graph.facebook.com

# 4. Ensure ad account IDs are correct (must start with 'act_')
# META_AD_ACCOUNT_ID=act_1234567890  ✅
# META_AD_ACCOUNT_ID=1234567890      ❌
```

## Validation Checklist

Before running in production, verify:

- [ ] All services show `(healthy)` status in `docker compose ps`
- [ ] Frontend accessible at http://localhost:3000
- [ ] Gateway API health check returns 200
- [ ] Database migrations completed successfully
- [ ] All required API keys configured in `.env`
- [ ] Test API calls return expected responses
- [ ] Logs show no critical errors
- [ ] Validation script passes: `python3 scripts/final_validation.py`

## Next Steps

### Learn the API

- **API Reference**: See `/home/user/geminivideo/docs/API_REFERENCE.md`
- **Interactive docs**: http://localhost:8080/docs (if Swagger/OpenAPI enabled)

### Explore Features

- **AI Video Generation**: `/home/user/geminivideo/AI_VIDEO_GENERATION_QUICKSTART.md`
- **DCO System**: `/home/user/geminivideo/DCO_QUICKSTART.md`
- **Demo Mode**: `/home/user/geminivideo/DEMO_MODE_QUICK_START.md`
- **Multi-Platform Publishing**: `/home/user/geminivideo/MULTI_PLATFORM_PUBLISHING.md`

### Deploy to Production

- **Cloud Deployment**: `/home/user/geminivideo/DEPLOYMENT_GUIDE.md`
- **Google Cloud Run**: `/home/user/geminivideo/AGENT_24_CLOUD_RUN_DEPLOYMENT.md`
- **Environment Setup**: `/home/user/geminivideo/ENV_SETUP_GUIDE.md`

### Development

```bash
# Run individual services locally (without Docker)

# Gateway API (Node.js)
cd services/gateway-api
npm install
npm run dev  # Runs on port 8080

# ML Service (Python)
cd services/ml-service
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8003

# Frontend (React)
cd frontend
npm install
npm run dev  # Runs on port 5173 (Vite default)
```

### Testing

```bash
# Run integration tests
./scripts/run_integration_tests.sh

# Run validation
python3 scripts/final_validation.py

# Health check
./scripts/health-check.sh

# Pre-flight checks
./scripts/pre-flight.sh
```

## Architecture Overview

```
┌─────────────┐
│   Frontend  │  React + Vite (port 3000)
│  Dashboard  │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│  Gateway    │  Node.js + Express (port 8080)
│     API     │  - Routing & orchestration
└──────┬──────┘  - Authentication
       │          - Rate limiting
       ├──────────────┬───────────────┬──────────────┐
       ▼              ▼               ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│   ML     │   │  Titan   │   │  Video   │   │  Drive   │
│ Service  │   │   Core   │   │  Agent   │   │  Intel   │
│ (8003)   │   │ (8084)   │   │ (8082)   │   │ (8081)   │
└────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │              │
     │              │              │              │
     └──────────────┴──────────────┴──────────────┘
                    │                     │
              ┌─────▼─────┐        ┌─────▼─────┐
              │ PostgreSQL│        │   Redis   │
              │  (5432)   │        │  (6379)   │
              └───────────┘        └───────────┘
```

### Service Responsibilities

| Service | Port | Purpose |
|---------|------|---------|
| **Frontend** | 3000 | User interface, dashboards, visualization |
| **Gateway API** | 8080 | API gateway, routing, auth, rate limiting |
| **ML Service** | 8003 | CTR prediction, A/B testing, ROAS optimization |
| **Titan Core** | 8084 | Meta Ads integration, campaign management |
| **Video Agent** | 8082 | Video processing, rendering, voice generation |
| **Drive Intel** | 8081 | Scene analysis, feature extraction, asset management |
| **Meta Publisher** | 8083 | Facebook/Instagram ad publishing |
| **TikTok Ads** | 8085 | TikTok ad publishing |
| **PostgreSQL** | 5432 | Primary database |
| **Redis** | 6379 | Caching, queuing, pub/sub |

## Support & Resources

- **Documentation**: `/home/user/geminivideo/docs/`
- **Architecture**: `/home/user/geminivideo/docs/ARCHITECTURE.md`
- **API Reference**: `/home/user/geminivideo/docs/API_REFERENCE.md`
- **Troubleshooting**: `/home/user/geminivideo/docs/troubleshooting.md`
- **GitHub Issues**: https://github.com/milosriki/geminivideo/issues

## License

MIT License - See LICENSE file for details.

---

**Congratulations!** You now have GeminiVideo running locally. Start by exploring the frontend dashboard at http://localhost:3000 or try the API examples above.
