# Async Queues, Emotion Detection, and Story Arcs

This document describes the new features implemented for asynchronous video processing, emotion detection, and automated story arc ad generation.

## Overview

Three major features have been added:

1. **Asynchronous Job Queues** - Non-blocking video analysis and rendering
2. **Cloud Emotion Detection** - Lightweight facial emotion analysis using Google Cloud Vision
3. **Story Arc Templates** - Automated ad generation based on emotional progression

## Architecture

### Async Queue System

```
User Request → Gateway API → Redis Queue → Background Worker → Database
     ↓
  202 Accepted (instant)
```

**Components:**
- **Redis**: Message queue for job distribution
- **drive-worker**: Processes video analysis jobs
- **video-worker**: Processes rendering jobs
- **Gateway API**: Queues jobs and returns immediately

### Services

#### drive-worker.py
Background worker that:
- Pulls jobs from `analysis_queue` Redis queue
- Detects scenes using PySceneDetect
- Extracts features with YOLO and other ML models
- Detects emotions using Google Cloud Vision API
- Updates database with results

#### video-worker.py
Background worker that:
- Pulls jobs from `render_queue` Redis queue
- Renders videos with FFmpeg
- Concatenates clips with transitions
- Stores output paths in Redis

## API Endpoints

### POST /api/analyze

Queue a video for analysis (non-blocking).

**Request:**
```json
{
  "path": "/path/to/video.mp4",
  "filename": "video.mp4",
  "size_bytes": 10485760,
  "duration_seconds": 30.0
}
```

**Response (202 Accepted):**
```json
{
  "asset_id": "uuid-here",
  "status": "QUEUED",
  "message": "Analysis job queued successfully"
}
```

### POST /api/render/story_arc

Create a transformation ad using emotion-based story arcs.

**Request:**
```json
{
  "asset_id": "uuid-of-analyzed-video",
  "arc_name": "fitness_transformation"
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "render-job-uuid",
  "status": "QUEUED",
  "arc_name": "fitness_transformation",
  "selected_clips": ["clip1", "clip2", "clip3"],
  "message": "Render job queued successfully"
}
```

## Story Arc Templates

Story arcs are defined in `shared/config/story_arcs.json`.

### Available Templates

#### 1. fitness_transformation (30s)
Classic transformation narrative:
- **Step 1** (5s): Sad/struggle clips (before state)
- **Step 2** (10s): Neutral training clips (journey)
- **Step 3** (10s): Happy success clips (after state)
- **Step 4** (5s): Happy CTA clips (call to action)

#### 2. motivation_arc (20s)
Build momentum and inspire:
- **Step 1** (5s): Neutral baseline clips
- **Step 2** (15s): Happy energy clips

#### 3. quick_win (15s)
Fast-paced high energy:
- **Step 1** (15s): All happy success clips

### Clip Selection Logic

For each step in the story arc:
1. Query database for clips matching the required emotion
2. Order by CTR score (highest predicted click-through rate first)
3. Order by scene_score (motion/action intensity)
4. Select top clip for that step

If no emotion match found, falls back to highest scoring clip.

## Emotion Detection

### Google Cloud Vision Integration

The system uses Google Cloud Vision Face Detection API to analyze facial emotions in video frames.

**Detected Emotions:**
- Joy → mapped to "happy"
- Sorrow → mapped to "sad"
- Anger, Surprise, Neutral → mapped to "neutral"

**Process:**
1. Extract middle frame from each clip
2. Encode frame as JPEG
3. Call Google Vision API
4. Store emotion with confidence score
5. Use for story arc clip selection

**Benefits over DeepFace:**
- ✅ No TensorFlow (500MB+ saved)
- ✅ Cloud-based (no model files)
- ✅ Fast and reliable
- ✅ Official Google library

### Setup

To enable emotion detection, set up Google Cloud credentials:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

## Database Schema

### New Fields

**clips table:**
- `ctr_score` (FLOAT): ML-predicted click-through rate (0.0-1.0)

**emotions table:**
- `clip_id`: Reference to clip
- `emotion`: Simplified emotion (happy/sad/neutral)
- `emotion_scores`: JSON with all detected emotions
- `confidence`: Confidence score (0.0-1.0)

## Frontend Usage

### Render Transformation Ad

1. Navigate to "Render Job" tab
2. Enter the Asset ID of an analyzed video
3. Select story arc template:
   - Fitness Transformation (30s)
   - Motivation Arc (20s)
   - Quick Win (15s)
4. Click "🎥 Render Transformation Ad"
5. Job is queued and processed in background
6. Check status using the job ID

## Running the System

### Start All Services

```bash
docker-compose up
```

This starts:
- PostgreSQL (database)
- Redis (message queue)
- gateway-api (API server)
- drive-intel (analysis API)
- video-agent (rendering API)
- drive-worker (background analysis)
- video-worker (background rendering)
- ml-service (ML predictions)
- meta-publisher (publishing)
- frontend (UI)

### Worker Logs

Monitor workers:
```bash
docker-compose logs -f drive-worker
docker-compose logs -f video-worker
```

### Redis Queue Status

Check queue lengths:
```bash
docker exec -it geminivideo-redis redis-cli
> LLEN analysis_queue
> LLEN render_queue
```

## Development

### Adding New Story Arcs

Edit `shared/config/story_arcs.json`:

```json
{
  "your_arc_name": {
    "name": "Your Arc Name",
    "description": "Description of the arc",
    "target_industry": "fitness",
    "duration_seconds": 30,
    "steps": [
      {
        "order": 1,
        "emotion": "happy",
        "duration": 30,
        "description": "All happy clips",
        "visual_tags": ["success", "energy"]
      }
    ]
  }
}
```

No code changes needed - templates are loaded dynamically.

### Customizing Emotion Mapping

Edit `services/drive-intel/worker.py` in the `detect_emotion_for_clip` method to customize how Google Vision emotions map to your simplified categories.

## Performance

### Benchmarks

**Without Async Queues:**
- Video upload → analysis: 30-60s blocking
- User waits for entire analysis
- UI frozen during processing

**With Async Queues:**
- Video upload → 202 response: <100ms
- Analysis happens in background
- UI remains responsive
- Multiple jobs processed concurrently

### Scaling

Workers can be scaled independently:

```bash
docker-compose up --scale drive-worker=3 --scale video-worker=2
```

This runs:
- 3 parallel analysis workers
- 2 parallel rendering workers

## Troubleshooting

### Worker Not Processing Jobs

Check worker logs:
```bash
docker-compose logs drive-worker
```

Common issues:
- Redis connection failed
- Database connection failed
- Missing video file at path
- Google Cloud credentials not set

### Emotion Detection Failing

If emotion detection fails:
- Check Google Cloud credentials are set
- Verify google-cloud-vision is installed
- Worker will continue without emotion data

### Story Arc Returns No Clips

Possible causes:
- Asset hasn't finished analysis yet (check status)
- No emotion data available (emotion detection failed)
- Asset has no clips (video too short or scene detection failed)

## Future Enhancements

Potential improvements:
- Rate limiting on API endpoints
- Job priorities in Redis queues
- Progress updates via WebSocket
- Retry logic for failed jobs
- Dead letter queue for persistent failures
- Admin UI for queue management

## References

- Google Cloud Vision: https://cloud.google.com/vision/docs/detecting-faces
- Redis Python Client: https://redis-py.readthedocs.io/
- PySceneDetect: https://scenedetect.com/
- Ultralytics YOLO: https://docs.ultralytics.com/
