# Video Storage Service

Complete video upload and storage solution with Google Cloud Storage (GCS) integration and local fallback.

## Features

- **Video Upload**: Multipart/form-data uploads with validation
- **Cloud Storage**: Google Cloud Storage (GCS) integration
- **Local Fallback**: Automatic fallback when GCS not configured
- **Signed URLs**: Secure time-limited download URLs
- **File Management**: List, delete, and organize videos
- **Type Validation**: Only allows video file types
- **Size Limits**: Configurable maximum file size (default: 500MB)

## Configuration

Set these environment variables:

```bash
# GCS Configuration
USE_GCS=true                          # Enable GCS (false for local storage)
GCS_BUCKET=geminivideo-renders        # GCS bucket name
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Local Storage (fallback)
LOCAL_STORAGE_PATH=/tmp/geminivideo   # Local storage directory
```

## Supported Video Formats

**File Extensions:**
- `.mp4` - MPEG-4 (recommended)
- `.mov` - QuickTime
- `.avi` - Audio Video Interleave
- `.mkv` - Matroska
- `.webm` - WebM
- `.flv` - Flash Video
- `.mpeg`, `.mpg` - MPEG
- `.3gp` - 3GPP

**MIME Types:**
- `video/mp4`
- `video/quicktime`
- `video/x-msvideo`
- `video/x-matroska`
- `video/webm`
- `video/x-flv`
- `video/mpeg`
- `video/3gpp`

## API Endpoints

### 1. Upload Video

**POST** `/storage/upload`

Upload a video file to storage.

**Parameters:**
- `file` (form-data, required): Video file to upload
- `folder` (query, optional): Folder/prefix for organization (default: "uploads")

**Response:**
```json
{
  "video_id": "uuid-string",
  "filename": "my-video.mp4",
  "size": 1234567,
  "storage_path": "gs://bucket/uploads/uuid.mp4",
  "storage_type": "gcs",
  "upload_time": "2025-12-02T10:30:00"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/storage/upload?folder=uploads" \
  -F "file=@/path/to/video.mp4"
```

---

### 2. Get Signed URL

**GET** `/storage/{video_id}/url`

Generate a signed URL for secure video download.

**Parameters:**
- `video_id` (path, required): UUID of the video
- `folder` (query, optional): Folder where video is stored (default: "uploads")
- `expiration` (query, optional): URL validity in minutes (default: 60, max: 1440)

**Response:**
```json
{
  "video_id": "uuid-string",
  "url": "https://storage.googleapis.com/...",
  "expires_in": 60
}
```

**Example:**
```bash
curl "http://localhost:8000/storage/{video_id}/url?expiration=120"
```

---

### 3. Delete Video

**DELETE** `/storage/{video_id}`

Delete a video from storage.

**Parameters:**
- `video_id` (path, required): UUID of the video
- `folder` (query, optional): Folder where video is stored (default: "uploads")

**Response:**
```json
{
  "success": true,
  "message": "Video uuid-string deleted successfully",
  "video_id": "uuid-string"
}
```

**Example:**
```bash
curl -X DELETE "http://localhost:8000/storage/{video_id}?folder=uploads"
```

---

### 4. List Videos

**GET** `/storage/list`

List all videos in storage with metadata.

**Parameters:**
- `prefix` (query, optional): Filter by folder/prefix
- `limit` (query, optional): Max videos to return (default: 100, max: 1000)

**Response:**
```json
{
  "videos": [
    {
      "video_id": "uuid-1",
      "filename": "video1.mp4",
      "size": 1234567,
      "storage_path": "gs://bucket/uploads/uuid-1.mp4",
      "storage_type": "gcs",
      "upload_time": "2025-12-02T10:30:00"
    }
  ],
  "total": 1,
  "storage_type": "gcs"
}
```

**Example:**
```bash
curl "http://localhost:8000/storage/list?prefix=uploads&limit=50"
```

---

### 5. Health Check

**GET** `/storage/health`

Check storage service status.

**Response:**
```json
{
  "status": "healthy",
  "storage_type": "gcs",
  "bucket": "geminivideo-renders"
}
```

**Example:**
```bash
curl "http://localhost:8000/storage/health"
```

## Usage Examples

### Python (requests)

```python
import requests

# Upload video
with open("video.mp4", "rb") as f:
    files = {"file": ("video.mp4", f, "video/mp4")}
    response = requests.post(
        "http://localhost:8000/storage/upload",
        files=files,
        params={"folder": "uploads"}
    )
    video_id = response.json()["video_id"]

# Get signed URL
response = requests.get(
    f"http://localhost:8000/storage/{video_id}/url",
    params={"expiration": 120}
)
url = response.json()["url"]

# Download video
video_response = requests.get(url)
with open("downloaded.mp4", "wb") as f:
    f.write(video_response.content)
```

### JavaScript (fetch)

```javascript
// Upload video
const formData = new FormData();
formData.append('file', videoFile);

const uploadResponse = await fetch(
  'http://localhost:8000/storage/upload?folder=uploads',
  {
    method: 'POST',
    body: formData
  }
);
const { video_id } = await uploadResponse.json();

// Get signed URL
const urlResponse = await fetch(
  `http://localhost:8000/storage/${video_id}/url?expiration=60`
);
const { url } = await urlResponse.json();

// Download video
window.open(url, '_blank');
```

## Error Handling

### Common Error Codes

- **400 Bad Request**: Invalid file type or empty file
- **404 Not Found**: Video not found
- **413 Payload Too Large**: File exceeds size limit
- **500 Internal Server Error**: Storage operation failed

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Storage Strategies

### Google Cloud Storage (Production)

**Advantages:**
- Scalable and reliable
- Global CDN distribution
- Signed URLs for security
- No local disk usage

**Setup:**
1. Create GCS bucket
2. Set up service account with Storage Admin role
3. Download service account key JSON
4. Set environment variables:
   ```bash
   export USE_GCS=true
   export GCS_BUCKET=your-bucket-name
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
   ```

### Local Storage (Development/Testing)

**Advantages:**
- No cloud setup required
- Faster for local development
- No egress costs

**Setup:**
1. Set environment variable:
   ```bash
   export USE_GCS=false
   export LOCAL_STORAGE_PATH=/tmp/geminivideo
   ```
2. Service automatically creates directory

## Integration with Video Pipeline

The storage service integrates with the video rendering pipeline:

```python
from api.storage import storage_service

# After rendering video
video_info = await storage_service.upload_rendered(
    local_path="/tmp/render/output.mp4",
    job_id="job-123"
)

# Generate download URL
url = storage_service.get_signed_url(
    blob_name=f"renders/job-123.mp4",
    expiration_minutes=120
)

# Return to client
return {
    "job_id": "job-123",
    "download_url": url,
    "expires_in": 120
}
```

## Security Considerations

1. **File Type Validation**: Only video files accepted
2. **Size Limits**: Prevents abuse (500MB default)
3. **Signed URLs**: Time-limited access (max 24 hours)
4. **UUID Filenames**: Prevents path traversal attacks
5. **CORS Configuration**: Configure for production domains

## Performance Tips

1. **Upload Large Files**: Use streaming uploads for files > 100MB
2. **Parallel Operations**: Upload/delete multiple files concurrently
3. **CDN Integration**: Use GCS CDN for faster global delivery
4. **Compression**: Compress videos before upload when possible
5. **Cleanup**: Regularly delete old videos to save storage costs

## Monitoring

Track these metrics in production:

- Upload success/failure rate
- Average upload time
- Storage usage (GB)
- Signed URL generation rate
- Download bandwidth

## Troubleshooting

### Issue: "GCS initialization failed"

**Solution:** Check:
- `GOOGLE_APPLICATION_CREDENTIALS` path is correct
- Service account has Storage Admin role
- Bucket exists and is accessible

### Issue: "File too large"

**Solution:** Increase `MAX_FILE_SIZE` constant or compress video

### Issue: "Invalid file type"

**Solution:** Ensure file has correct extension and MIME type

### Issue: "Video not found"

**Solution:** Verify video_id and folder parameters match upload location

## License

Part of the GeminiVideo project.
