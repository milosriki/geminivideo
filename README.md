# 🎬 AI Ad Intelligence & Creation Suite

A comprehensive platform for intelligent video ad creation, analysis, and publishing, powered by AI and designed for the Dubai fitness market.

## 🌟 Overview

The AI Ad Intelligence & Creation Suite combines video intelligence, psychological analysis, compliance checking, and automated publishing to create high-performing video advertisements. The system consists of:

- **Frontend**: React + Vite application with analysis panels (Assets, Psychology, Compliance, Diversification, Editor, Player)
- **Backend Services**: 
  - Gateway API (Node/Express TypeScript) - Central orchestration
  - Video Agent (Python FastAPI) - Video rendering and processing
  - Drive Intel (Python FastAPI) - Video intelligence and asset management
  - Meta Publisher (Node/Express) - Publishing and performance metrics
- **Shared Configuration**: Hooks, triggers, personas, weights, and schemas
- **CI/CD**: GitHub Actions for automated deployment and nightly learning updates

## 🚀 Quickstart - Local Development

### Prerequisites

- Node.js 20+ (for frontend and backend services)
- Python 3.11+ (for Python services)
- Docker and Docker Compose v2 (optional, for containerized deployment)

### Option 1: Local Development (Recommended for Development)

1. Clone the repository:
```bash
git clone https://github.com/milosriki/geminivideo.git
cd geminivideo
```

2. Run the setup script:
```bash
./dev-start.sh
```

This will:
- Install dependencies for all services
- Build TypeScript code
- Set up Python virtual environments
- Display commands to start each service

3. Start services in separate terminals:

**Terminal 1 - Gateway API:**
```bash
cd services/gateway-api
VIDEO_AGENT_URL=http://localhost:8001 \
DRIVE_INTEL_URL=http://localhost:8002 \
META_PUBLISHER_URL=http://localhost:8003 \
WEIGHTS_PATH=../../shared/config/weights.yaml \
PORT=8080 node dist/index.js
```

**Terminal 2 - Video Agent:**
```bash
cd services/video-agent
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001
```

**Terminal 3 - Drive Intel:**
```bash
cd services/drive-intel
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8002
```

**Terminal 4 - Meta Publisher:**
```bash
cd services/meta-publisher
PORT=8003 node dist/index.js
```

**Terminal 5 - Frontend (optional):**
```bash
cd frontend
npm install
npm run dev
```

4. Test the APIs:
```bash
./test-api.sh
```

Services will be available at:
- Gateway API: `http://localhost:8080`
- Video Agent: `http://localhost:8001`
- Drive Intel: `http://localhost:8002`
- Meta Publisher: `http://localhost:8003`
- Frontend: `http://localhost:5173`

### Option 2: Docker Compose (For Containerized Testing)

Note: Docker builds may require adjustments for your environment.

```bash
docker compose up --build
```

This will start all services in containers with the same port mappings as above.

### Testing the System

1. **Add test videos**: Place video files in `data/input/` directory

2. **Ingest assets**:
```bash
curl -X POST http://localhost:8080/ingest/drive/sync \
  -H "Content-Type: application/json" \
  -d '{"source": "local"}'
```

3. **List assets**:
```bash
curl http://localhost:8080/assets
```

4. **Get clips for an asset**:
```bash
curl http://localhost:8080/assets/{asset-id}/clips
```

5. **Create a remix**:
```bash
curl -X POST http://localhost:8080/render/remix \
  -H "Content-Type: application/json" \
  -d '{
    "storyboard": [{"clipId": "clip-id", "duration": 5.0}],
    "assetMap": {"clip-id": "asset-id"},
    "overlays": {"cta": "Join Now!"}
  }'
```

6. **Check job status**:
```bash
curl http://localhost:8080/render/jobs/{job-id}
```

7. **Trigger learning update** (increments psychology weight):
```bash
curl -X POST http://localhost:8080/internal/learning/update
```

## ☁️ Cloud Run Deployment

### Prerequisites

- Google Cloud Project with billing enabled
- Cloud Run API enabled
- Artifact Registry repository created
- Service account with appropriate permissions

### Required Secrets

Configure these secrets in your GitHub repository:

- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_REGION`: Deployment region (default: us-central1)
- `GAR_REPO`: Artifact Registry repository name
- `GCP_SA_KEY`: Service account JSON key
- `GATEWAY_URL`: Gateway API URL (for nightly learning)

### Deployment

Push to `main` branch to trigger automatic deployment:

```bash
git push origin main
```

The GitHub Actions workflow will:
1. Build Docker images for all services
2. Push images to Google Artifact Registry
3. Deploy to Cloud Run with appropriate configurations
4. Set up environment variables and service URLs

### Manual Deployment

```bash
# Build and deploy gateway-api
gcloud run deploy gateway-api \
  --source ./services/gateway-api \
  --region us-central1 \
  --allow-unauthenticated

# Similar for other services...
```

## 📁 Directory Structure

```
/
├── README.md                          # This file
├── LICENSE                            # MIT License
├── docker-compose.yml                 # Local orchestration
│
├── services/
│   ├── gateway-api/                   # Node/Express TypeScript
│   │   ├── src/
│   │   │   ├── index.ts               # Main server
│   │   │   └── types.ts               # TypeScript types
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── video-agent/                   # Python FastAPI
│   │   ├── main.py                    # FFmpeg pipeline
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── drive-intel/                   # Python FastAPI
│   │   ├── main.py                    # Video intelligence
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── meta-publisher/                # Node/Express
│       ├── src/
│       │   └── index.ts               # Meta API stub
│       ├── Dockerfile
│       ├── package.json
│       └── tsconfig.json
│
├── frontend/                          # React + Vite
│   ├── src/
│   │   ├── App.tsx                    # Main application
│   │   ├── App.css                    # Styles
│   │   └── services/
│   │       └── api.ts                 # Gateway API client
│   ├── package.json
│   └── vite.config.ts
│
├── shared/
│   ├── config/
│   │   ├── hooks_config.json          # Hook templates
│   │   ├── triggers_config.json       # Psychological triggers
│   │   ├── personas.json              # Dubai fitness personas
│   │   └── weights.yaml               # Scoring weights
│   └── schemas/
│       └── openapi.yaml               # API documentation
│
├── .github/workflows/
│   ├── build-and-deploy-cloudrun.yml  # CI/CD deployment
│   └── nightly-learning.yml           # Automated weight updates
│
└── data/
    └── input/                         # Local video files
        └── .gitkeep
```

## 🔧 Configuration

### Scoring Weights (shared/config/weights.yaml)

The system uses configurable weights for scoring ad concepts:

- `psychology_weight`: 0.35 - Hook and trigger effectiveness
- `compliance_weight`: 0.25 - Platform requirement adherence
- `diversification_weight`: 0.20 - Variety and coverage
- `novelty_weight`: 0.20 - Uniqueness and freshness

These weights are automatically adjusted by the nightly learning workflow based on performance metrics.

### Personas (shared/config/personas.json)

Four Dubai fitness personas:
- Busy Professional (28-45, corporate executive)
- Fitness Enthusiast (22-35, varied occupation)
- Wellness Seeker (30-50, entrepreneur/executive)
- Fitness Beginner (25-40, varied occupation)

### Hooks & Triggers (shared/config/)

- Hook templates: Urgency, Curiosity, Social Proof, Transformation
- Primary drivers: Aspirational Identity, Social Belonging, FOMO, Pain Avoidance, Curiosity
- Secondary drivers: Time Efficiency, Status Elevation, Validation

## 🎯 Features

### Current Implementation

✅ Asset ingestion from local folder  
✅ Basic video metadata extraction (duration, resolution, aspect ratio)  
✅ Single clip per asset generation  
✅ Video remix job creation with FFmpeg  
✅ Compliance checking (aspect ratio, resolution, duration)  
✅ Meta publishing stub with placeholder creative IDs  
✅ Performance metrics generation (demo data)  
✅ Learning weight adjustment (demo increment)  
✅ Frontend with 6 analysis panels  
✅ Docker Compose orchestration  
✅ GitHub Actions CI/CD  

### Placeholder Logic (TODO Comments in Code)

The following features have placeholders for future implementation:

🔜 **Video Intelligence** (drive-intel service):
- Scene detection and segmentation
- OCR text extraction
- Object detection (YOLO)
- Speech-to-text transcription
- Google Drive integration

🔜 **Hook & Novelty Engine** (gateway-api service):
- Hook template generation
- Embedding-based novelty scoring
- FAISS similarity search
- Hook-persona matching

🔜 **Real Meta Integration** (meta-publisher service):
- Meta Marketing API authentication
- Real creative upload
- Live metrics ingestion
- Campaign management

🔜 **Advanced Video Processing** (video-agent service):
- Scene transitions
- Text overlay rendering
- CTA positioning and styling
- Multi-clip concatenation
- Audio mixing

🔜 **Psychology Analysis** (frontend):
- Hook relevance visualization
- Trigger alignment scores
- Persona match breakdown
- Emotional appeal metrics

🔜 **Diversification Dashboard** (frontend):
- Entropy calculations
- Portfolio variety analysis
- Coverage heatmaps

## 📚 API Documentation

See `shared/schemas/openapi.yaml` for complete API documentation.

### Key Endpoints

**Gateway API (port 8080)**:
- `POST /ingest/drive/sync` - Sync videos from local/drive
- `GET /assets` - List all assets
- `GET /assets/:id/clips` - Get clips for asset
- `POST /render/remix` - Create video remix
- `GET /render/jobs/:id` - Get render job status
- `POST /publish/meta` - Publish to Meta
- `GET /performance/metrics` - Get performance data
- `POST /internal/learning/update` - Update weights

## 🧪 Testing

### Service Health Checks

```bash
# Check all services
curl http://localhost:8080/health  # gateway-api
curl http://localhost:8001/health  # video-agent
curl http://localhost:8002/health  # drive-intel
curl http://localhost:8003/health  # meta-publisher
```

### End-to-End Workflow

1. Place a video in `data/input/sample.mp4`
2. Sync: `POST /ingest/drive/sync`
3. List: `GET /assets`
4. Get clips: `GET /assets/{id}/clips`
5. Create remix: `POST /render/remix`
6. Poll status: `GET /render/jobs/{id}`
7. Publish: `POST /publish/meta`
8. Check metrics: `GET /performance/metrics`

## 🔒 Security

- Service-to-service communication within Docker network
- Environment variables for configuration
- Secrets management via GitHub Secrets
- Service account authentication for Cloud Run

## 📈 Monitoring & Observability

Cloud Run provides built-in:
- Request logging
- Performance metrics
- Error tracking
- Resource utilization

Future enhancements:
- Structured logging
- Distributed tracing
- Custom metrics dashboards
- Alert configurations

## 🚧 Future Roadmap

### Phase 1: Intelligence (Next PR)
- Implement scene detection
- Add OCR text extraction
- Integrate object detection
- Add speech-to-text

### Phase 2: Hook Engine (Future PR)
- Build embedding model integration
- Implement FAISS novelty detection
- Create hook generation pipeline
- Add hook-persona matching

### Phase 3: Real Publishing (Future PR)
- Integrate Meta Marketing API
- Implement real creative upload
- Add live metrics ingestion
- Build campaign management

### Phase 4: Diversification (Future PR)
- Implement entropy calculations
- Build portfolio analysis
- Create coverage dashboards
- Add variety recommendations

### Phase 5: Self-Learning (Future PR)
- Real performance-based weight adjustments
- A/B test automation
- Multi-armed bandit optimization
- Continuous improvement loops

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙋 Support

For issues and questions:
- GitHub Issues: https://github.com/milosriki/geminivideo/issues
- Documentation: See `shared/schemas/openapi.yaml`

---

**Built with ❤️ for the Dubai fitness community**