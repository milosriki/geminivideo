# Video Storage Service - Quick Start

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export USE_GCS=false  # Use local storage for development
export LOCAL_STORAGE_PATH=/tmp/geminivideo
```

## Start the API

```bash
cd /home/user/geminivideo/services/titan-core
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

## Test the API

### 1. Health Check
```bash
curl http://localhost:8000/storage/health
```

### 2. Upload a Video
```bash
curl -X POST "http://localhost:8000/storage/upload?folder=uploads" \
  -F "file=@test-video.mp4"
```

Response:
```json
{
  "video_id": "abc-123",
  "filename": "test-video.mp4",
  "size": 1234567,
  "storage_path": "/tmp/geminivideo/uploads/abc-123.mp4",
  "storage_type": "local",
  "upload_time": "2025-12-02T10:30:00"
}
```

### 3. Get Download URL
```bash
curl "http://localhost:8000/storage/abc-123/url?folder=uploads"
```

### 4. List Videos
```bash
curl "http://localhost:8000/storage/list?limit=10"
```

### 5. Delete Video
```bash
curl -X DELETE "http://localhost:8000/storage/abc-123?folder=uploads"
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## File Structure

```
services/titan-core/api/
├── storage.py              # Main storage service (21KB)
├── storage_example.py      # Usage examples (5.3KB)
├── STORAGE_README.md       # Full documentation (7.9KB)
└── STORAGE_QUICKSTART.md   # This file
```

## Key Features

- Video file uploads (multipart/form-data)
- Google Cloud Storage integration
- Local storage fallback
- Signed URL generation
- File type validation (video files only)
- Size limits (500MB max)
- 5 REST endpoints
- Complete error handling

## Supported Formats

mp4, mov, avi, mkv, webm, flv, mpeg, 3gp

## Production Setup (GCS)

```bash
# 1. Set environment variables
export USE_GCS=true
export GCS_BUCKET=your-bucket-name
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# 2. Restart the API
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

## Need Help?

See STORAGE_README.md for complete documentation.
