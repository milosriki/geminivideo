# Asset Library Manager - Quick Start Guide

## Installation

```bash
# Install dependencies
pip install google-cloud-storage requests

# Ensure FFmpeg is installed
ffmpeg -version
ffprobe -version
```

## 5-Minute Quick Start

### 1. Initialize Library

```python
from services.video_agent.pro import AssetLibrary, AssetType, AssetCategory

# Create library
library = AssetLibrary(storage_dir="/path/to/your/assets")
```

### 2. Import Your First Asset

```python
# Import a video
video = library.import_asset(
    source_path="my_video.mp4",
    asset_type=AssetType.VIDEO,
    name="My First Video",
    tags={"demo", "test"}
)

print(f"Imported: {video.name}")
print(f"Duration: {video.metadata.duration}s")
print(f"Resolution: {video.metadata.resolution}")
```

### 3. Bulk Import

```python
# Import all videos from a folder
videos = library.bulk_import(
    folder_path="/path/to/videos",
    asset_type=AssetType.VIDEO,
    recursive=True,
    file_extensions=['.mp4', '.mov']
)

print(f"Imported {len(videos)} videos")
```

### 4. Search Assets

```python
# Search by text
results = library.search_assets(query="product")

# Search by filters
hd_videos = library.search_assets(
    asset_type=AssetType.VIDEO,
    min_resolution=(1920, 1080)
)

# Complex search
short_4k = library.search_assets(
    asset_type=AssetType.VIDEO,
    min_resolution=(3840, 2160),
    max_duration=60.0,
    tags={"product"}
)
```

### 5. Organize & Manage

```python
# Add to favorites
library.set_favorite(video.id, True)

# Add tags
library.add_tag(video.id, "premium")
library.add_tag(video.id, "featured")

# Track usage
library.mark_used(video.id)

# Get recently used
recent = library.get_recently_used(limit=10)
```

## Common Use Cases

### Music Library Organization

```python
from services.video_agent.pro import MusicLibrary

# Import music
music_tracks = library.bulk_import(
    folder_path="/path/to/music",
    asset_type=AssetType.AUDIO,
    category=AssetCategory.MUSIC
)

# Organize by mood
by_mood = MusicLibrary.categorize_by_mood(music_tracks)
upbeat = by_mood['upbeat']
calm = by_mood['calm']

# Search for specific music
background_music = library.search_assets(
    asset_type=AssetType.AUDIO,
    tags={"upbeat"},
    min_duration=120.0,  # At least 2 minutes
    max_duration=240.0   # Max 4 minutes
)
```

### Stock Footage Management

```python
# Import from URL
stock = library.import_from_url(
    url="https://example.com/footage.mp4",
    asset_type=AssetType.VIDEO,
    name="Ocean Waves",
    category=AssetCategory.STOCK_FOOTAGE,
    tags={"ocean", "nature", "b-roll"}
)

# Find B-roll
broll = library.search_assets(
    category=AssetCategory.B_ROLL,
    has_audio=False  # Silent clips for background
)
```

### LUT Library

```python
# Import LUTs
luts = library.bulk_import(
    folder_path="/path/to/luts",
    asset_type=AssetType.LUT,
    category=AssetCategory.CINEMATIC,
    file_extensions=['.cube', '.3dl']
)

# Generate previews
for lut in luts:
    library.generate_asset_thumbnail(lut)

# Find specific looks
cinematic_luts = library.search_assets(
    asset_type=AssetType.LUT,
    category=AssetCategory.CINEMATIC
)
```

### Cloud Storage

```python
from services.video_agent.pro import CloudStorageManager

# Setup cloud storage
cloud = CloudStorageManager(
    bucket_name="my-assets",
    credentials_path="/path/to/gcs-credentials.json"
)

library = AssetLibrary(
    storage_dir="/local/assets",
    cloud_storage=cloud
)

# Upload to cloud
library.upload_to_cloud(video.id, include_thumbnail=True)

# Get public URL
url = cloud.get_public_url(video.cloud_path)
```

## Asset Types

### Supported Types

- **VIDEO**: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`
- **AUDIO**: `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`
- **IMAGE**: `.jpg`, `.png`, `.tiff`, `.bmp`, `.webp`
- **FONT**: `.ttf`, `.otf`, `.woff`, `.woff2`
- **LUT**: `.cube`, `.3dl`
- **TEMPLATE**: Custom format for motion graphics templates

## Search Filters Reference

```python
library.search_assets(
    # Text search
    query="keyword",

    # Type & category
    asset_type=AssetType.VIDEO,
    category=AssetCategory.PRODUCT_SHOT,

    # Tags
    tags={"tag1", "tag2"},  # Must have ALL tags

    # Favorites
    favorites_only=True,

    # Duration (seconds)
    min_duration=10.0,
    max_duration=60.0,

    # Resolution (width, height)
    min_resolution=(1920, 1080),

    # Audio presence (video only)
    has_audio=True,

    # Sorting
    sort_by="created_at",  # or "updated_at", "last_used", "use_count", "name"
    reverse=True  # Descending order
)
```

## Statistics & Organization

```python
# Get library stats
stats = library.get_library_stats()
print(f"Total: {stats['total_assets']} assets")
print(f"Size: {stats['total_size_bytes'] / (1024**3):.2f} GB")

# Organize by type
by_type = library.organize_by_type()
print(f"Videos: {len(by_type[AssetType.VIDEO])}")
print(f"Audio: {len(by_type[AssetType.AUDIO])}")

# Organize by category
by_category = library.organize_by_category()
```

## Pro Tips

1. **Always generate thumbnails** for quick visual preview
2. **Use consistent tagging** for better organization
3. **Mark favorites** for frequently used assets
4. **Track usage** to identify popular assets
5. **Use bulk import** for initial setup
6. **Upload to cloud** for backup and sharing
7. **Use specific categories** rather than generic tags
8. **Version important assets** rather than overwriting

## Common Patterns

### Find Perfect B-Roll

```python
broll = library.search_assets(
    asset_type=AssetType.VIDEO,
    category=AssetCategory.B_ROLL,
    min_resolution=(1920, 1080),
    max_duration=30.0,
    has_audio=False,
    sort_by="created_at",
    reverse=True
)
```

### Find Background Music

```python
music = library.search_assets(
    asset_type=AssetType.AUDIO,
    category=AssetCategory.MUSIC,
    tags={"upbeat"},
    min_duration=120.0
)
```

### Find 4K Product Shots

```python
products = library.search_assets(
    asset_type=AssetType.VIDEO,
    category=AssetCategory.PRODUCT_SHOT,
    min_resolution=(3840, 2160),
    tags={"product"}
)
```

### Find Recently Used Assets

```python
recent = library.get_recently_used(limit=20)
```

### Find All Favorites

```python
favorites = library.get_favorites()
```

## Demo Script

See `/home/user/geminivideo/services/video-agent/pro/asset_library_demo.py` for comprehensive demos of all features.

## Full Documentation

See `/home/user/geminivideo/services/video-agent/pro/ASSET_LIBRARY_README.md` for complete API reference and advanced features.
