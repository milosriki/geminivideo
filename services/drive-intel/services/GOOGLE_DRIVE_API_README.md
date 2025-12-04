# Google Drive API Integration - Agent 22

**Production-Grade Real API Integration | NO MOCK DATA**

## Overview

Complete Google Drive API integration with service account authentication, OAuth 2.0, webhooks, batch operations, and comprehensive file management. Built for the ULTIMATE 30-agent production plan.

## Features

### ✅ Authentication Methods
- **Service Account**: For server-to-server applications
- **OAuth 2.0**: For user-authorized access
- Automatic token refresh
- Secure credential management

### ✅ File Operations
- List folder contents with pagination
- Filter and list video files
- Get detailed file metadata
- Download files to disk
- Download files to memory (bytes)
- Batch download multiple files
- Search files by name/metadata

### ✅ Folder Management
- Create new folders
- Move files between folders
- Watch folders for changes (webhooks)
- Stop folder watches

### ✅ Storage Management
- Get storage quota information
- Track usage statistics
- Monitor storage limits

## Installation

```bash
# Install Google API dependencies
pip install google-auth google-auth-oauthlib google-api-python-client

# Or install all project dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Service Account Authentication

```python
from services.drive_intel.services.google_drive import GoogleDriveService

# Initialize with service account
service = GoogleDriveService(
    credentials_path='path/to/service-account.json'
)

# List videos in a folder
videos = service.list_videos(folder_id='your-folder-id')

for video in videos:
    print(f"{video.name} - {video.size_mb():.2f} MB")
```

### 2. OAuth 2.0 Authentication

```python
# Initialize and authenticate with OAuth
service = GoogleDriveService()
service.authenticate_oauth(
    token_path='~/.geminivideo/token.json',
    credentials_path='path/to/oauth_credentials.json'
)

# Get storage quota
quota = service.get_storage_quota()
print(f"Using {quota['usage_percent']:.1f}% of storage")
```

## API Reference

### DriveFile Dataclass

```python
@dataclass
class DriveFile:
    id: str                          # Google Drive file ID
    name: str                        # File name
    mime_type: str                   # MIME type
    size: int                        # Size in bytes
    created_time: str                # Creation timestamp
    modified_time: str               # Modification timestamp
    parents: List[str]               # Parent folder IDs
    web_view_link: str               # Web view URL

    # Video-specific (optional)
    duration_ms: Optional[int]       # Video duration in milliseconds
    width: Optional[int]             # Video width
    height: Optional[int]            # Video height

    # Additional metadata
    version: Optional[int]           # File version
    md5_checksum: Optional[str]      # MD5 hash
    trashed: bool                    # Trash status
```

**Methods:**
- `is_video() -> bool`: Check if file is a video
- `size_mb() -> float`: Get size in megabytes

### GoogleDriveService Class

#### Authentication

```python
def __init__(self, credentials_path: str = None, credentials: Credentials = None)
```
Initialize with service account or OAuth credentials.

```python
def authenticate(self, credentials_path: str) -> None
```
Authenticate with service account JSON file.

```python
def authenticate_oauth(self, token_path: str, credentials_path: str) -> None
```
Authenticate with OAuth 2.0 flow.

#### File Listing

```python
def list_folder(self, folder_id: str, page_size: int = 100) -> List[DriveFile]
```
List all files in a folder.

**Parameters:**
- `folder_id`: Google Drive folder ID
- `page_size`: Files per page (max 1000)

**Returns:** List of `DriveFile` objects

```python
def list_videos(self, folder_id: str, page_size: int = 100) -> List[DriveFile]
```
List only video files in a folder.

#### File Download

```python
def download_file(self, file_id: str, destination: str) -> str
```
Download file to disk with progress tracking.

**Parameters:**
- `file_id`: Google Drive file ID
- `destination`: Local file path

**Returns:** Path to downloaded file

```python
def download_to_memory(self, file_id: str) -> bytes
```
Download file to memory (returns bytes).

**Use case:** Small files, in-memory processing

```python
def batch_download(self, file_ids: List[str], destination_dir: str) -> Dict[str, str]
```
Download multiple files in batch.

**Returns:** Dictionary mapping file_id to local path

#### File Metadata

```python
def get_file_metadata(self, file_id: str) -> DriveFile
```
Get detailed file metadata including video properties.

#### Search

```python
def search_files(
    self,
    query: str,
    folder_id: str = None,
    mime_type: str = None,
    max_results: int = 50
) -> List[DriveFile]
```
Search for files by name or metadata.

**Parameters:**
- `query`: Search query (file name)
- `folder_id`: Limit to folder (optional)
- `mime_type`: Filter by MIME type (optional)
- `max_results`: Max results to return

#### Folder Operations

```python
def create_folder(self, name: str, parent_id: str = None) -> str
```
Create a new folder.

**Returns:** New folder ID

```python
def move_file(self, file_id: str, new_parent_id: str) -> bool
```
Move file to a different folder.

#### Webhooks

```python
def watch_folder(
    self,
    folder_id: str,
    webhook_url: str,
    expiration_hours: int = 24
) -> Dict[str, Any]
```
Set up webhook notification for folder changes.

**Parameters:**
- `folder_id`: Folder to watch
- `webhook_url`: HTTPS endpoint for notifications
- `expiration_hours`: Watch duration (max 24)

**Returns:** Channel info (id, resource_id, expiration)

**Requirements:**
- Webhook URL must be HTTPS
- Endpoint must be publicly accessible
- Must handle Google Drive notification format

```python
def stop_watch(self, channel_id: str, resource_id: str) -> bool
```
Stop watching a folder.

#### Storage Management

```python
def get_storage_quota() -> Dict[str, int]
```
Get storage quota information.

**Returns:**
```python
{
    'limit': int,              # Total storage in bytes
    'usage': int,              # Used storage in bytes
    'usage_in_drive': int,     # Drive usage in bytes
    'usage_in_drive_trash': int,  # Trash usage in bytes
    'usage_percent': float     # Percentage used
}
```

## Usage Examples

### Example 1: Video Ingestion Pipeline

```python
from google_drive import GoogleDriveService
from pathlib import Path

# Initialize
service = GoogleDriveService(credentials_path='service-account.json')

# List all videos
folder_id = 'your-folder-id'
videos = service.list_videos(folder_id)

print(f"Found {len(videos)} videos")

# Download videos
download_dir = Path('/tmp/videos')
download_dir.mkdir(exist_ok=True)

for video in videos[:5]:  # First 5 videos
    if video.size_mb() < 100:  # Skip large files
        local_path = service.download_file(
            video.id,
            str(download_dir / video.name)
        )
        print(f"Downloaded: {local_path}")
```

### Example 2: Batch Processing

```python
# Get all video IDs
videos = service.list_videos(folder_id)
video_ids = [v.id for v in videos[:10]]

# Batch download
results = service.batch_download(
    file_ids=video_ids,
    destination_dir='/tmp/batch_videos'
)

# Check results
successful = [fid for fid, path in results.items() if path]
print(f"Downloaded {len(successful)}/{len(video_ids)} videos")
```

### Example 3: Search and Filter

```python
# Search for specific videos
results = service.search_files(
    query='interview',
    folder_id=folder_id,
    max_results=20
)

# Filter by size
small_videos = [v for v in results if v.is_video() and v.size_mb() < 50]

print(f"Found {len(small_videos)} small interview videos")
```

### Example 4: Folder Organization

```python
# Create processing folders
processed_folder = service.create_folder('Processed Videos', parent_id=folder_id)
pending_folder = service.create_folder('Pending Videos', parent_id=folder_id)

# Move files
for video in videos:
    if video.duration_ms and video.duration_ms < 60000:  # < 1 minute
        service.move_file(video.id, processed_folder)
    else:
        service.move_file(video.id, pending_folder)
```

### Example 5: Webhook Monitoring

```python
# Set up folder watch
channel_info = service.watch_folder(
    folder_id='your-folder-id',
    webhook_url='https://yourapp.com/webhook/drive',
    expiration_hours=24
)

print(f"Channel ID: {channel_info['channel_id']}")

# Your webhook endpoint should handle POST requests:
# {
#   "kind": "api#channel",
#   "id": "channel-id",
#   "resourceId": "resource-id",
#   "resourceUri": "...",
#   "changed": true
# }

# Stop watching when done
service.stop_watch(
    channel_id=channel_info['channel_id'],
    resource_id=channel_info['resource_id']
)
```

### Example 6: Storage Monitoring

```python
# Check storage quota
quota = service.get_storage_quota()

if quota['usage_percent'] > 80:
    print("⚠️  Warning: Storage usage above 80%")
    print(f"Used: {quota['usage'] / 1024**3:.2f} GB")
    print(f"Limit: {quota['limit'] / 1024**3:.2f} GB")

    # List large files
    all_files = service.list_folder(folder_id, page_size=1000)
    large_files = sorted(
        [f for f in all_files if f.size_mb() > 100],
        key=lambda x: x.size,
        reverse=True
    )

    print(f"\nLargest files:")
    for f in large_files[:10]:
        print(f"  {f.name}: {f.size_mb():.2f} MB")
```

## Setup Instructions

### 1. Get Google Cloud Credentials

#### For Service Account:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Drive API:
   - APIs & Services → Library → Google Drive API → Enable
4. Create service account:
   - APIs & Services → Credentials → Create Credentials → Service Account
   - Download JSON key file
5. Share your Drive folder with the service account email

#### For OAuth 2.0:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID
3. Application type: Desktop app
4. Download JSON file

### 2. Environment Setup

```bash
# Set environment variables
export GOOGLE_SERVICE_ACCOUNT_KEY=/path/to/service-account.json
export GOOGLE_OAUTH_CREDENTIALS=/path/to/oauth_credentials.json
export GOOGLE_DRIVE_FOLDER_ID=your-folder-id

# Or use .env file
cat > .env << EOF
GOOGLE_SERVICE_ACCOUNT_KEY=/path/to/service-account.json
GOOGLE_DRIVE_FOLDER_ID=your-folder-id
EOF
```

### 3. Find Folder/File IDs

**From URL:**
```
https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j
                                        ^^^^^^^^^^^^^^^^^^^^
                                        This is the folder ID
```

**Using API:**
```python
service = GoogleDriveService(credentials_path='service-account.json')

# Search for folder by name
results = service.search_files('My Videos', mime_type='application/vnd.google-apps.folder')
for folder in results:
    print(f"{folder.name}: {folder.id}")
```

## Error Handling

```python
from googleapiclient.errors import HttpError

try:
    videos = service.list_videos(folder_id)
except HttpError as e:
    if e.resp.status == 404:
        print("Folder not found")
    elif e.resp.status == 403:
        print("Permission denied - check sharing settings")
    else:
        print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Considerations

### Pagination
```python
# For large folders, use pagination
page_token = None
all_files = []

while True:
    results = service.service.files().list(
        q=f"'{folder_id}' in parents",
        pageSize=100,
        pageToken=page_token,
        fields="nextPageToken, files(id, name)"
    ).execute()

    all_files.extend(results.get('files', []))
    page_token = results.get('nextPageToken')

    if not page_token:
        break
```

### Rate Limits
- Google Drive API: 1,000 requests/100 seconds/user
- Implement exponential backoff for rate limit errors

### Best Practices
- Use batch operations for multiple files
- Cache metadata when possible
- Download to disk for large files (>100 MB)
- Use streaming downloads for very large files
- Implement retry logic with exponential backoff

## Testing

```bash
# Run comprehensive test suite
python test_google_drive.py

# Test specific functionality
python -c "
from google_drive import GoogleDriveService
service = GoogleDriveService(credentials_path='service-account.json')
quota = service.get_storage_quota()
print(f'Storage: {quota[\"usage_percent\"]:.1f}%')
"
```

## Integration with Geminivideo Pipeline

```python
# services/drive-intel/ingestion_pipeline.py
from services.google_drive import GoogleDriveService
from services.scene_detector import SceneDetector
from services.transcription import TranscriptionService

def ingest_drive_videos(folder_id: str):
    """Complete ingestion pipeline from Google Drive."""

    # 1. Get videos from Drive
    drive = GoogleDriveService(credentials_path='service-account.json')
    videos = drive.list_videos(folder_id)

    # 2. Download and process
    for video in videos:
        local_path = drive.download_file(video.id, f'/tmp/{video.name}')

        # 3. Extract scenes
        detector = SceneDetector()
        scenes = detector.detect_scenes(local_path)

        # 4. Transcribe audio
        transcription = TranscriptionService()
        text = transcription.transcribe(local_path)

        # 5. Store metadata
        metadata = {
            'drive_id': video.id,
            'name': video.name,
            'scenes': scenes,
            'transcript': text,
            'duration_ms': video.duration_ms,
            'resolution': f'{video.width}x{video.height}'
        }

        yield metadata
```

## Troubleshooting

### Authentication Issues
```
Error: Credentials file not found
→ Check file path is correct
→ Ensure file has .json extension
→ Verify file contains valid JSON
```

### Permission Errors
```
Error: 403 Permission Denied
→ Share folder with service account email
→ Grant "Viewer" or "Editor" access
→ Wait a few minutes for permissions to propagate
```

### Rate Limiting
```
Error: 429 Too Many Requests
→ Implement exponential backoff
→ Reduce request frequency
→ Use batch operations
```

## Security Best Practices

1. **Never commit credentials to version control**
   ```bash
   echo "*.json" >> .gitignore
   echo ".env" >> .gitignore
   ```

2. **Use environment variables**
   ```python
   import os
   creds_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
   ```

3. **Limit API scopes** to minimum required
   ```python
   SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
   ```

4. **Rotate service account keys** regularly

5. **Monitor API usage** in Google Cloud Console

## License

Part of the Geminivideo ULTIMATE 30-Agent Production Plan.

## Support

For issues or questions:
1. Check Google Drive API documentation
2. Review error logs
3. Verify credentials and permissions
4. Test with minimal example

---

**Agent 22 of 30** | Real Google Drive API Integration | Production-Ready | NO MOCK DATA
