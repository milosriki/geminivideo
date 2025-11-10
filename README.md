# 🎬 AI Ad Intelligence & Creation Suite

A comprehensive end-to-end system for ingesting videos, mining and ranking scenes, predicting winning variants with psychology/technical/persona scoring, rendering multi-format ads, and running nightly learning loops.

## 🌟 Features

### 1. **Drive Intel Service** (Python/FastAPI)
- Google Drive and local folder ingestion with caching
- Intelligent scene detection using PySceneDetect
- Multi-modal feature extraction:
  - Motion score calculation (frame differencing)
  - Object detection via YOLOv8n
  - OCR text extraction via PaddleOCR
  - Speech transcription support (Whisper)
  - Text embeddings with SentenceTransformers
- FAISS-powered semantic search
- Scene ranking with configurable weights
- De-duplication clustering

### 2. **Video Agent Service** (Python/FastAPI)
- Async video rendering with job management
- Multi-format support (9:16 Reels, 1:1 Feed, 4:5 Stories)
- Phase-aware overlay generation (Hook → Authority/Proof → CTA)
- Subtitle generation and burn-in (SRT/ASS)
- FFmpeg transitions (xfade)
- Loudness normalization (EBU R128)
- Comprehensive compliance checking

### 3. **Gateway API** (Node/TypeScript/Express)
- Unified API gateway for all services
- AI-powered scoring modules:
  - **Psychology Score**: Trigger detection from OCR/transcript
  - **Hook Strength**: Brevity, numbers, questions, motion spikes
  - **Technical Score**: Compliance + quality metrics
  - **Demographic Match**: Persona keyword overlap
- Win probability prediction (low/mid/high bands)
- Reliability logging (JSONL)
- Learning loop with conservative weight updates

### 4. **Meta Publisher Service** (Node/TypeScript/Express)
- Meta Marketing API integration
- Video upload and creative creation
- Ad campaign management
- Insights API proxy
- Dry-run mode for testing

### 5. **Frontend Dashboard** (React/Vite/TypeScript)
- Assets library with scan/import
- Ranked clips visualization
- Semantic search interface
- Analysis panel with prediction scores
- Compliance status display
- Diversification dashboard
- Reliability chart with accuracy tracking

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- (Optional) Google Cloud service account for Drive ingestion
- (Optional) Meta/Facebook access token for publishing

### Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/milosriki/geminivideo.git
cd geminivideo
```

2. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start all services**
```bash
docker-compose up --build
```

4. **Access the services**
- Frontend: http://localhost:3000
- Gateway API: http://localhost:8080
- Drive Intel: http://localhost:8001
- Video Agent: http://localhost:8002
- Meta Publisher: http://localhost:8003

### Local Folder Ingestion

Place your video files in `./data/cache` and scan from the UI, or via API:

```bash
curl -X POST http://localhost:8080/assets/ingest/local \
  -H "Content-Type: application/json" \
  -d '{"folderPath": "/app/data/cache"}'
```

### Google Drive Ingestion

1. Create a Google Cloud service account
2. Enable Google Drive API
3. Download credentials JSON
4. Update `.env`:
```
USE_GOOGLE_DRIVE=true
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
DRIVE_FOLDER_ID=your_folder_id
```

5. Restart services and use the UI or API:
```bash
curl -X POST http://localhost:8080/assets/ingest/drive \
  -H "Content-Type: application/json" \
  -d '{"folderId": "your_folder_id", "maxFiles": 100}'
```

## 📚 API Reference

### Assets & Clips

**Get all assets**
```bash
GET /assets
```

**Get ranked clips for an asset**
```bash
GET /assets/{id}/clips?ranked=true&top=10
```

**Search clips semantically**
```bash
POST /assets/search/clips
{
  "q": "person holding phone",
  "topK": 10
}
```

### Video Rendering

**Create a remix job**
```bash
POST /render/remix
{
  "clips": [
    {"videoPath": "/path/to/video.mp4", "start": 0, "duration": 5}
  ],
  "variant": "reels",
  "enableSubtitles": true,
  "enableOverlays": true
}
```

**Get job status**
```bash
GET /render/jobs/{jobId}
```

### Prediction & Scoring

**Score clips and predict CTR**
```bash
POST /predict/score
{
  "clips": [...],
  "context": {"creativeId": "abc123"}
}
```

**Get reliability stats**
```bash
GET /predict/reliability
```

### Learning

**Update weights (internal)**
```bash
POST /internal/learning/update
{
  "predictions": [...],
  "actuals": [...]
}
```

### Meta Publishing

**Publish to Meta**
```bash
POST /publish/meta
{
  "videoUrl": "https://...",
  "pageId": "123456",
  "placements": ["feed", "story"]
}
```

**Get insights**
```bash
GET /insights?adId=123&datePreset=last_7d
```

## 🔧 Configuration

### Scene Ranking Weights
Edit `shared/config/scene_ranking.yaml`:
```yaml
weights:
  motion_score: 0.25
  object_relevance: 0.20
  ocr_relevance: 0.15
  novelty: 0.20
  duration_optimal: 0.10
  audio_presence: 0.10
```

### Prediction Weights
Edit `shared/config/weights.yaml`:
```yaml
prediction_weights:
  psychology_score: 0.30
  technical_score: 0.25
  hook_strength: 0.25
  demographic_match: 0.20
```

### Hook Templates
Edit `shared/config/hook_templates.json` for overlay customization.

### Personas
Edit `shared/config/personas.json` to add/modify target personas.

### Triggers
Edit `shared/config/triggers_config.json` for psychological trigger patterns.

## 🧪 Testing

### Smoke Tests
```bash
./scripts/smoke_test.sh
```

### Load Tests
```bash
./scripts/load_test.sh
```

### Manual Testing
See `scripts/test_examples.sh` for curl examples.

## 🏗️ Architecture

```
┌─────────────────┐
│    Frontend     │  React/Vite Dashboard
│   (Port 3000)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Gateway API   │  Unified API + Scoring
│   (Port 8080)   │
└────┬────┬───┬───┘
     │    │   │
     ▼    ▼   ▼
┌────────┐┌────────┐┌─────────┐
│ Drive  ││ Video  ││  Meta   │
│ Intel  ││ Agent  ││Publisher│
│  8001  ││  8002  ││  8003   │
└────────┘└────────┘└─────────┘
```

## 📊 Data Models

### Clip (Enriched)
```typescript
{
  id: string
  videoId: string
  start: number
  end: number
  duration: number
  objects: string[]
  ocr_tokens: string[]
  motion_score: number
  transcript_excerpt?: string
  embeddingVectorId?: string
  rankScore: number
  clusterId?: string
}
```

### Prediction Output
```typescript
{
  scores: {
    psychology: number
    technical: number
    hookStrength: number
    demographicMatch: number
  }
  predictedCTR: {
    band: 'low' | 'mid' | 'high'
    confidence: number
    probability: number
  }
  triggerStack: string[]
  personaCandidates: string[]
}
```

## 🔄 Nightly Learning Workflow

The system includes a learning loop that updates prediction weights based on actual performance:

1. Predictions are logged to `logs/predictions.jsonl`
2. Metrics are ingested from Meta Insights API
3. `POST /internal/learning/update` adjusts weights conservatively
4. New weights are applied to future predictions

Schedule with cron:
```bash
0 2 * * * /path/to/scripts/nightly_learning.sh
```

## 🐛 Troubleshooting

### Services won't start
- Check Docker logs: `docker-compose logs -f`
- Verify port availability: `lsof -i :8080`
- Ensure sufficient disk space for cache/outputs

### Drive ingestion fails
- Verify service account has access to folder
- Check credentials file path in `.env`
- Confirm DRIVE_FOLDER_ID is correct

### Video rendering fails
- Check FFmpeg installation in container
- Verify input video format compatibility
- Review video-agent logs for errors

### Model downloads fail
- YOLOv8n, PaddleOCR, and SentenceTransformers download on first use
- Ensure container has internet access
- May require several GB of disk space

## 📝 Environment Variables

| Variable | Service | Description | Default |
|----------|---------|-------------|---------|
| `USE_GOOGLE_DRIVE` | drive-intel | Enable Google Drive ingestion | `false` |
| `GOOGLE_APPLICATION_CREDENTIALS` | drive-intel | Path to service account JSON | - |
| `DRIVE_FOLDER_ID` | drive-intel | Google Drive folder ID | - |
| `MAX_DRIVE_VIDEOS` | drive-intel | Max videos to ingest | `500` |
| `ENABLE_GPU` | video-agent | Enable GPU acceleration | `false` |
| `FFMPEG_THREADS` | video-agent | FFmpeg thread count | `4` |
| `META_ACCESS_TOKEN` | meta-publisher | Meta/Facebook access token | - |
| `META_AD_ACCOUNT_ID` | meta-publisher | Meta ad account ID | - |
| `META_DRY_RUN` | meta-publisher | Dry-run mode (no actual API calls) | `true` |
| `ENABLE_LLM_FALLBACK` | gateway-api | Enable LLM for psychology scoring | `false` |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- PySceneDetect for scene detection
- Ultralytics YOLOv8 for object detection
- PaddleOCR for text recognition
- SentenceTransformers for embeddings
- FFmpeg for video processing
- Meta Marketing API for ad publishing

## 📞 Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

Built with ❤️ for creators and marketers