# AI Ad Intelligence & Creation Suite

Complete end-to-end platform for AI-powered video ad creation, optimization, and publishing.

## 🚀 Quickstart

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/milosriki/geminivideo.git
   cd geminivideo
   ```

2. **Start Gateway API**
   ```bash
   cd services/gateway-api
   npm install
   npm run dev
   # Runs on http://localhost:8080
   ```

3. **Start Drive Intel Service**
   ```bash
   cd services/drive-intel
   pip install -r requirements.txt
   python -m uvicorn src.main:app --reload --port 8081
   # Runs on http://localhost:8081
   ```

4. **Start Video Agent Service**
   ```bash
   cd services/video-agent
   pip install -r requirements.txt
   python -m uvicorn src.index:app --reload --port 8082
   # Runs on http://localhost:8082
   ```

5. **Start Meta Publisher Service**
   ```bash
   cd services/meta-publisher
   npm install
   npm run dev
   # Runs on http://localhost:8083
   ```

6. **Start Frontend**
   ```bash
   cd services/frontend
   npm install
   npm run dev
   # Runs on http://localhost:5173
   ```

### Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Access services
# Frontend: http://localhost:80
# Gateway API: http://localhost:8080
# Drive Intel: http://localhost:8081
# Video Agent: http://localhost:8082
# Meta Publisher: http://localhost:8083
```

## 📋 Features

### 🎬 Video Intelligence
- **Asset Ingestion**: Ingest from local folders or Google Drive
- **Scene Detection**: Automatic scene boundary detection
- **Feature Extraction**: Motion, faces, objects, text, embeddings
- **FAISS Indexing**: Fast similarity search

### 🎯 AI Scoring & Ranking
- **Psychology Scoring**: Curiosity, urgency, social proof, surprise, empathy
- **Hook Strength Analysis**: Detect and score engagement hooks
- **Novelty Detection**: Embedding-based uniqueness scoring
- **Composite Ranking**: Multi-factor clip ranking

### 🎨 Video Creation
- **Storyboard Builder**: Visual clip sequencing
- **Automated Rendering**: Background job queue with ffmpeg
- **Transition Effects**: Fade, crossfade, and more
- **Compliance Checking**: Content policy validation

### 📊 Publishing & Analytics
- **Meta Publishing**: Automated ad publishing to Facebook/Instagram
- **Performance Tracking**: Real-time CTR and engagement metrics
- **Prediction Logging**: Track predicted vs actual performance

### 🤖 Continuous Learning
- **Nightly Calibration**: Auto-adjust scoring weights based on actual performance
- **Pattern Mining**: Extract patterns from successful ads
- **Model Improvement**: Iterative learning from published ad data

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │ (React/Vite)
└──────┬──────┘
       │
┌──────▼──────────┐
│   Gateway API   │ (Node/Express + TypeScript)
│   - Knowledge   │
│   - Scoring     │
│   - Routing     │
└─────┬─┬─┬───────┘
      │ │ │
  ┌───┘ │ └────┐
  │     │      │
┌─▼─────▼──┐ ┌─▼──────────┐ ┌──────────────┐
│Drive Intel│ │Video Agent │ │Meta Publisher│
│(FastAPI)  │ │(FastAPI)   │ │(Express)     │
│- Ingest   │ │- Render    │ │- Publish     │
│- Detect   │ │- Jobs      │ │- Insights    │
│- Extract  │ │- Compliance│ │- Tracking    │
└───────────┘ └────────────┘ └──────────────┘
```

## 📁 Project Structure

```
geminivideo/
├── .github/workflows/       # CI/CD workflows
│   └── deploy-cloud-run.yml
├── services/
│   ├── gateway-api/         # Gateway & Knowledge Router
│   ├── drive-intel/         # Video Intelligence Service
│   ├── video-agent/         # Rendering Service
│   ├── meta-publisher/      # Publishing & Analytics
│   └── frontend/            # React UI
├── shared/config/           # Shared configuration
│   ├── hooks/
│   ├── drivers/
│   ├── personas/
│   ├── weights.yaml
│   └── scene_ranking.yaml
├── knowledge/               # Knowledge base
│   └── README.md
├── scripts/                 # Automation scripts
│   ├── nightly_learning.py
│   └── meta_ads_library_pattern_miner.py
├── tests/                   # Test suites
├── logs/                    # Prediction logs
└── DEPLOYMENT.md            # Deployment guide
```

## 🔧 Configuration

### Environment Variables

**Gateway API:**
- `PROJECT_ID` - GCP project ID
- `GCS_BUCKET` - GCS bucket for knowledge storage
- `GCS_MOCK_MODE` - Enable mock mode for local dev

**Services:**
- `PORT` - Service port
- `GATEWAY_URL` - Gateway API URL
- `META_ACCESS_TOKEN` - Meta Marketing API token

See each service's README for detailed configuration.

## 📖 Documentation

- [Deployment Guide](DEPLOYMENT.md) - Complete GCP deployment instructions
- [Knowledge Base](knowledge/README.md) - Knowledge management system
- [Gateway API](services/gateway-api/README.md) - API documentation
- [Drive Intel](services/drive-intel/README.md) - Video intelligence
- [Video Agent](services/video-agent/README.md) - Rendering service
- [Meta Publisher](services/meta-publisher/README.md) - Publishing service
- [Frontend](services/frontend/README.md) - UI documentation

## 🧪 Testing

```bash
# Run unit tests
cd tests
python -m pytest test_ranking.py

# Run integration tests
python -m pytest test_integration.py

# Smoke test
./scripts/smoke_test.sh
```

## 🚀 Deployment

### Google Cloud Platform

Automated deployment via GitHub Actions on push to `main`:

```bash
# Manual deployment
gcloud run deploy gateway-api \
  --image=us-west1-docker.pkg.dev/PROJECT_ID/cloud-run-repo/gateway-api:latest \
  --region=us-west1 \
  --platform=managed
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete instructions.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🔗 Related Issues

- Epic #2: AI Ad Intelligence & Creation Suite
- Issues: #12 #13 #14 #15 #16 #17 #18

## 📧 Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/milosriki/geminivideo/issues)
- Documentation: See individual service READMEs