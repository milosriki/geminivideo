# Gemini Video - AI Ad Intelligence & Creation Suite

Production-quality AI-powered video analysis and ad creation platform for fitness/personal training vertical.

## 🚀 Features

- **Scene Enrichment & Feature Extraction** - Automated shot detection, object recognition, OCR, motion analysis
- **Predictive Scoring Engine** - Psychology-based content analysis with CTR prediction
- **Multi-Format Rendering** - Automated video remix with overlays, subtitles, and compliance checks
- **Meta Integration** - Direct publishing to Instagram/Facebook with insights ingestion
- **Analytics Dashboards** - Comprehensive analysis, diversification tracking, and reliability monitoring
- **Self-Learning Loop** - Automated weight calibration based on actual performance data

## 📋 Quick Start - Connect All Services & Deploy

### Prerequisites

- Docker & Docker Compose (required)
- At least 8GB RAM and 10GB disk space
- (Optional) Meta API access token for live publishing

### 🚀 One-Command Start (Easiest)

Connect and start all 5 services with automatic health checks:

```bash
# Clone and start
git clone https://github.com/milosriki/geminivideo.git
cd geminivideo

# Start everything with connection verification
./scripts/start-all.sh
```

This will:
- ✅ Build all Docker images
- ✅ Start all 5 services connected via Docker network
- ✅ Verify service health and connections
- ✅ Display all service URLs

**Services connected and running at:**
- 🎨 **Frontend Dashboard**: http://localhost *(Start here!)*
- 🚪 **Gateway API**: http://localhost:8080
- 🎬 **Drive Intel**: http://localhost:8081
- 🎥 **Video Agent**: http://localhost:8082
- 📱 **Meta Publisher**: http://localhost:8083
- 🤖 **ML Service**: http://localhost:8003

### Manual Start (Alternative)

```bash
# Start all services (disable BuildKit due to npm compatibility issue)
DOCKER_BUILDKIT=0 docker compose up -d --build

# Test connections
./scripts/test-connections.sh
```

### 📘 Complete Guide

**New here?** See [WHERE_ARE_WE_NOW.md](WHERE_ARE_WE_NOW.md) for project status and next steps.

See [QUICKSTART.md](QUICKSTART.md) for:
- Step-by-step setup instructions
- Connection testing
- Troubleshooting
- API usage examples

### Basic Workflow

1. **Ingest Videos**
   - Go to "Assets & Ingest" tab
   - Enter path to video folder (must be accessible to container)
   - Click "Ingest Folder"

2. **View Ranked Clips**
   - Go to "Ranked Clips" tab
   - Select an asset
   - View clips ranked by composite score

3. **Semantic Search**
   - Go to "Semantic Search" tab
   - Enter natural language query
   - Get semantically similar clips

4. **Score Content**
   - Go to "Analysis" tab
   - View comprehensive scoring breakdown
   - See predicted CTR band and confidence

5. **Render Video**
   - Go to "Render Job" tab
   - Create render job (sample provided)
   - Monitor job progress and compliance

6. **Track Metrics**
   - "Diversification" tab - Content variety metrics
   - "Reliability" tab - Prediction accuracy tracking

## 🏗️ Architecture

### Services

- **drive-intel** (Python/FastAPI) - Scene detection, feature extraction, semantic search
- **video-agent** (Python/FastAPI) - Video rendering, overlays, compliance checks
- **gateway-api** (Node/Express) - Unified API, scoring engine, reliability logging
- **meta-publisher** (Node/Express) - Meta Marketing API integration
- **frontend** (React/Vite) - Analytics dashboards and controls

### Configuration

All services use shared configuration in `shared/config/`:
- `scene_ranking.yaml` - Scene ranking weights and thresholds
- `hook_templates.json` - Text overlay templates
- `weights.yaml` - Scoring weights (auto-updated by learning loop)
- `triggers_config.json` - Psychology driver keywords
- `personas.json` - Target audience definitions

See `shared/config/README.md` for details.

## 🧪 Testing

### Run Services Individually

```bash
# Drive Intel
cd services/drive-intel
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Gateway API
cd services/gateway-api
npm install
npm run dev

# Frontend
cd frontend
npm install
npm run dev
```

### API Examples

```bash
# Ingest local folder
curl -X POST http://localhost:8080/api/ingest/local/folder \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "/path/to/videos"}'

# Get ranked clips
curl http://localhost:8080/api/assets/{asset_id}/clips?ranked=true&top=10

# Search clips
curl -X POST http://localhost:8080/api/search/clips \
  -H "Content-Type: application/json" \
  -d '{"query": "person doing squats", "top_k": 5}'

# Score storyboard
curl -X POST http://localhost:8080/api/score/storyboard \
  -H "Content-Type: application/json" \
  -d '{"scenes": [...], "metadata": {}}'

# Create render job
curl -X POST http://localhost:8080/api/render/remix \
  -H "Content-Type: application/json" \
  -d '{"scenes": [...], "variant": "reels"}'
```

## 📊 Scoring System

### Psychology Score (30%)
- Pain point keywords
- Transformation language
- Urgency triggers
- Authority signals
- Social proof

### Hook Strength (25%)
- Numbers in first 3s
- Questions
- Motion spikes
- Text length compliance

### Technical Score (20%)
- Resolution quality
- Audio quality
- Lighting
- Stabilization

### Demographic Match (15%)
- Persona keyword alignment
- Age range fit
- Fitness level match

### Novelty Score (10%)
- Semantic uniqueness
- Visual diversity

## 🔄 Learning Loop

The system automatically improves over time:

1. **Prediction Logging** - All scores logged to `logs/predictions.jsonl`
2. **Insights Ingestion** - Meta performance data linked to predictions
3. **Calibration** - System tracks in-band vs out-of-band predictions
4. **Weight Updates** - Automated adjustment when sufficient data available

Trigger learning update:
```bash
curl -X POST http://localhost:8080/api/internal/learning/update
```

## 🚢 Cloud Deployment

### Deploy to Google Cloud Platform

Deploy all connected services to GCP Cloud Run with one command:

```bash
# Configure your GCP project
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"

# Deploy all services
./scripts/deploy.sh
```

This will:
- ✅ Deploy all 5 services to Cloud Run
- ✅ Configure service networking and URLs
- ✅ Set up environment variables
- ✅ Display production URLs

**Or use GitHub Actions:**
- Push to `main` branch triggers automatic deployment
- Images built and pushed to Artifact Registry
- Services deployed to Cloud Run

### Deployment Options

1. **Local (Development)**: `./scripts/start-all.sh` - Docker Compose
2. **GCP Cloud Run (Production)**: `./scripts/deploy.sh` - Managed services
3. **CI/CD (Automated)**: GitHub Actions on push to main

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete guide including:
- GCP project setup and API enablement
- Artifact Registry configuration
- Secret Manager for tokens
- Monitoring and logging setup
- Cost optimization tips

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

Issues and pull requests welcome! See the [GitHub Issues](https://github.com/milosriki/geminivideo/issues) for epic #2 and sub-issues #12-#18.

## 📧 Support

For questions or issues, please open a GitHub issue or contact the maintainers.