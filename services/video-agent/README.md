# Video Agent Service

Video rendering and remixing service for creating ad content from storyboards.

## Features

- **Video Remixing**: Combine clips into new videos based on storyboard
- **Background Job Queue**: Async rendering with job status tracking
- **Compliance Checking**: Content policy validation before rendering
- **FFmpeg Integration**: Professional video encoding and effects
- **Transition Effects**: Fade, crossfade, and other transitions

## Endpoints

### Health Check
```
GET /health
```

### Rendering
```
POST /render/remix           - Queue a render job from storyboard
GET  /render/status/{job_id} - Check render job status
GET  /render/jobs            - List all render jobs
```

## Configuration

Environment variables:
- `PORT` - Server port (default: 8082)
- `OUTPUT_DIR` - Directory for rendered videos (default: /outputs)
- `MAX_RENDER_DURATION` - Maximum video duration in seconds (default: 60)

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python -m uvicorn src.index:app --reload --port 8082
```

## Docker

```bash
# Build image
docker build -t video-agent .

# Run container
docker run -p 8082:8082 -v $(pwd)/outputs:/outputs video-agent
```

## Storyboard Format

```json
{
  "storyboard": [
    {
      "clip_id": "uuid",
      "asset_id": "uuid",
      "start_time": 0.0,
      "end_time": 5.0,
      "transition": "fade",
      "effects": ["stabilize", "color_grade"]
    }
  ],
  "output_format": "mp4",
  "resolution": "1920x1080",
  "fps": 30,
  "audio_track": "path/to/audio.mp3",
  "compliance_check": true
}
```

## FFmpeg Command Template

The service uses ffmpeg for video composition:

```bash
ffmpeg -i clip1.mp4 -i clip2.mp4 -i clip3.mp4 \
  -filter_complex \
  "[0:v]fade=t=out:st=5:d=1[v0]; \
   [1:v]fade=t=in:st=0:d=1,fade=t=out:st=5:d=1[v1]; \
   [2:v]fade=t=in:st=0:d=1[v2]; \
   [v0][v1][v2]concat=n=3:v=1:a=0[outv]" \
  -map "[outv]" \
  -c:v libx264 -preset fast -crf 22 \
  -r 30 -s 1920x1080 \
  output.mp4
```

## Compliance Checks

The service validates:
- Video duration limits
- Number of clips
- Content policy compliance
- Licensing requirements
- Brand safety guidelines
