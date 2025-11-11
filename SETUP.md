# Setup Guide - Phase 1: Core Foundation

This guide covers setting up the Phase 1 implementation with PostgreSQL, scene detection, emotion recognition, and FFmpeg rendering.

## Prerequisites

### System Requirements
- Python 3.10+
- Node.js 16+
- PostgreSQL 15+
- FFmpeg 4.4+
- Docker & Docker Compose (optional, recommended)

### Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip nodejs npm postgresql ffmpeg
```

**macOS:**
```bash
brew install python nodejs postgresql ffmpeg
brew services start postgresql
```

## Quick Start with Docker Compose (Recommended)

1. **Start all services:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   - Frontend: http://localhost:80
   - Gateway API: http://localhost:8080
   - Drive Intel: http://localhost:8081
   - Video Agent: http://localhost:8082
   - Meta Publisher: http://localhost:8083
   - PostgreSQL: localhost:5432

3. **Initialize the database:**
   The database tables are automatically created on first run.

## Manual Setup (Development)

### 1. Setup PostgreSQL

```bash
# Create database and user
sudo -u postgres psql

postgres=# CREATE DATABASE geminivideo;
postgres=# CREATE USER geminivideo WITH PASSWORD 'geminivideo';
postgres=# GRANT ALL PRIVILEGES ON DATABASE geminivideo TO geminivideo;
postgres=# \q
```

### 2. Setup Drive Intel Service

```bash
cd services/drive-intel

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://geminivideo:geminivideo@localhost:5432/geminivideo"

# Initialize database
cd ../../
python shared/db.py

# Start service
cd services/drive-intel
python -m uvicorn src.main:app --reload --port 8081
```

**First Run Notes:**
- DeepFace will download models (~100MB) on first emotion detection
- This is normal and happens once
- Models are cached in `~/.deepface/`

### 3. Setup Video Agent Service

```bash
cd services/video-agent

# Install dependencies
pip install -r requirements.txt

# Verify FFmpeg is installed
ffmpeg -version

# Start service
python -m uvicorn src.index:app --reload --port 8082
```

### 4. Setup Gateway API

```bash
cd services/gateway-api

# Install dependencies
npm install

# Start service
npm run dev
# Runs on http://localhost:8080
```

### 5. Setup Meta Publisher

```bash
cd services/meta-publisher

# Install dependencies
npm install

# Start service
npm run dev
# Runs on http://localhost:8083
```

### 6. Setup Frontend

```bash
cd services/frontend

# Install dependencies
npm install

# Set environment variables
export VITE_GATEWAY_URL=http://localhost:8080
export VITE_DRIVE_INTEL_URL=http://localhost:8081

# Start service
npm run dev
# Runs on http://localhost:5173
```

## Testing the Implementation

### 1. Health Checks

Check all services are running:

```bash
# Drive Intel
curl http://localhost:8081/health

# Video Agent
curl http://localhost:8082/health

# Gateway API
curl http://localhost:8080/health
```

Expected response includes feature availability:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "features": {
    "database": true,
    "scene_detection": true,
    "emotion_recognition": true
  }
}
```

### 2. Ingest a Video

```bash
# Prepare a test video
mkdir -p /tmp/test_videos
# Place a video file at /tmp/test_videos/test.mp4

# Ingest the video
curl -X POST http://localhost:8081/ingest/local/folder \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/tmp/test_videos/test.mp4",
    "recursive": false
  }'
```

Response:
```json
{
  "asset_id": "uuid-here",
  "status": "processing",
  "message": "Ingestion started for /tmp/test_videos/test.mp4"
}
```

### 3. Check Processing Status

```bash
# List assets
curl http://localhost:8081/assets

# Get clips for an asset (replace ASSET_ID)
curl http://localhost:8081/assets/ASSET_ID/clips?ranked=true&top=10
```

### 4. View in Frontend

1. Open http://localhost:5173 (or http://localhost:80 with docker-compose)
2. You should see your ingested videos
3. Click "View Clips" to see detected scenes with emotion data
4. Clips are ranked by score with emotion indicators

### 5. Run Tests

```bash
cd tests
pip install -r requirements.txt
python -m pytest test_ranking.py -v
```

Expected: All 23 tests passing

## Environment Variables

### Drive Intel Service
- `DATABASE_URL` - PostgreSQL connection string
  - Default: `postgresql://geminivideo:geminivideo@localhost:5432/geminivideo`
- `PORT` - Service port (default: 8081)

### Video Agent Service
- `OUTPUT_DIR` - Directory for rendered videos
  - Default: `/tmp/geminivideo/outputs`
- `PORT` - Service port (default: 8082)

### Frontend
- `VITE_GATEWAY_URL` - Gateway API URL (default: http://localhost:8080)
- `VITE_DRIVE_INTEL_URL` - Drive Intel URL (default: http://localhost:8081)

## Features Implemented

### ✅ PostgreSQL Persistence
- SQLAlchemy models for Assets, Clips, Emotions
- Automatic table creation
- Graceful fallback to in-memory storage

### ✅ Real Scene Detection
- PySceneDetect ContentDetector
- Automatic scene boundary detection
- Configurable threshold (default: 27.0)
- Real video metadata extraction

### ✅ Emotion Recognition
- DeepFace with pre-trained models
- Multi-frame sampling (3 frames per clip)
- 7 emotions: happy, sad, angry, fear, surprise, neutral, disgust
- Confidence scores
- Emotion-based scene scoring

### ✅ FFmpeg Rendering
- Clip extraction with timecodes
- Clip concatenation
- Configurable resolution and FPS
- Transition support (fade)

### ✅ Frontend Integration
- Real-time asset and clip display
- Emotion visualization with color coding
- Confidence indicators
- Scene score display

## Troubleshooting

### PostgreSQL Connection Failed
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify credentials in DATABASE_URL
- Check database exists: `psql -U geminivideo -d geminivideo`

### DeepFace Model Download Issues
- Ensure internet connectivity
- Models download to `~/.deepface/`
- Can take 2-5 minutes on first run
- Retry if download fails

### FFmpeg Not Found
- Install: `sudo apt-get install ffmpeg` or `brew install ffmpeg`
- Verify: `ffmpeg -version`
- Service falls back to mock rendering if unavailable

### Scene Detection Not Working
- Ensure video file exists at specified path
- Check file permissions
- Supported formats: mp4, avi, mov, mkv
- Service falls back to mock scenes if file not found

### Frontend Not Connecting
- Check VITE_GATEWAY_URL and VITE_DRIVE_INTEL_URL
- Verify services are running (health checks)
- Check browser console for CORS errors
- Ensure ports are not blocked by firewall

## Performance Notes

### Scene Detection
- Processing time: ~5-10 seconds per minute of video
- Memory usage: ~500MB per video
- CPU intensive

### Emotion Recognition
- Processing time: ~2-3 seconds per clip
- First run: +2-5 minutes for model download
- GPU acceleration not yet implemented (CPU only)

### Database
- PostgreSQL recommended for production
- In-memory mode suitable for development only
- No data persistence without PostgreSQL

## Next Steps

Phase 2 will add:
- XGBoost CTR prediction
- Vowpal Wabbit A/B optimization
- Meta Ads integration
- Nightly learning scripts
- Advanced video generation

## Support

For issues:
1. Check logs in service output
2. Verify all dependencies installed
3. Check GitHub Issues
4. Review error messages carefully

## License

MIT
