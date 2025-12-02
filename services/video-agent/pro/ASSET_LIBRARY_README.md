# Professional Asset Library Manager

Complete asset management system for pro-grade video editing with cloud storage integration.

## Overview

The Asset Library Manager provides enterprise-grade asset management for video production workflows. It handles videos, audio, images, fonts, LUTs, and templates with automatic metadata extraction, cloud storage integration, and advanced search capabilities.

## Features

### 1. Multi-Type Asset Support
- **Video**: MP4, MOV, AVI, MKV with full metadata extraction
- **Audio**: MP3, WAV, FLAC, AAC with waveform generation
- **Images**: JPG, PNG, TIFF with thumbnail generation
- **Fonts**: TTF, OTF, WOFF with family/style detection
- **LUTs**: .CUBE, .3DL with preview generation
- **Templates**: Lower thirds, titles, CTAs, transitions

### 2. Metadata Extraction
- **Video**: Resolution, codec, bitrate, FPS, duration, aspect ratio, HDR detection
- **Audio**: Codec, sample rate, channels, duration, bitrate
- **Images**: Resolution, format, color mode, DPI, alpha channel
- **Fonts**: Family, style, weight, format, language support
- **LUTs**: Format, size, input/output ranges
- **Templates**: Type, duration, editable fields

### 3. Asset Organization
- **Categories**: Stock footage, B-roll, music, sound effects, backgrounds, etc.
- **Tags**: Flexible tagging system for custom categorization
- **Favorites**: Mark frequently used assets
- **Usage Tracking**: Track use count and last used timestamp
- **Versioning**: Create and track multiple versions of assets

### 4. Search & Filter
- **Text Search**: Search by name, description, tags
- **Type Filter**: Filter by asset type
- **Category Filter**: Filter by predefined categories
- **Tag Filter**: Multi-tag filtering
- **Duration Filter**: Min/max duration for video/audio
- **Resolution Filter**: Min resolution for video/image
- **Audio Filter**: Filter videos by audio presence
- **Sort Options**: By date, usage, name

### 5. Cloud Storage Integration
- **Google Cloud Storage**: Upload/download assets to GCS
- **Public URLs**: Generate public URLs for assets
- **Thumbnail Upload**: Automatically upload thumbnails
- **Batch Operations**: Bulk upload/download

### 6. Thumbnail Generation
- **Video Thumbnails**: Frame extraction at specific timestamp
- **Image Thumbnails**: Scaled previews
- **Audio Waveforms**: Visual waveform representation
- **LUT Previews**: Applied LUT visualization

### 7. Import Methods
- **Local Import**: Import from local file system
- **URL Import**: Download and import from URL
- **Bulk Import**: Import entire folders recursively
- **Copy/Reference**: Option to copy files or reference in place

### 8. Music Library Features
- **Mood Organization**: Categorize by mood (upbeat, calm, energetic, etc.)
- **Genre Organization**: Categorize by genre (rock, pop, electronic, etc.)
- **Duration Filtering**: Find tracks by length
- **License Tracking**: Track music licenses

### 9. Stock Footage Integration
- **Provider Hooks**: Base class for stock footage provider integration
- **Search**: Search stock libraries
- **Download**: Download stock assets directly

## Installation

### Requirements

```bash
# Core dependencies
pip install google-cloud-storage requests

# System requirements (must be installed)
# - FFmpeg (with FFprobe)
# - Python 3.8+
```

### Quick Start

```python
from services.video_agent.pro import AssetLibrary, AssetType, AssetCategory

# Initialize library
library = AssetLibrary(storage_dir="/path/to/assets")

# Import an asset
asset = library.import_asset(
    source_path="/path/to/video.mp4",
    asset_type=AssetType.VIDEO,
    name="Product Demo",
    category=AssetCategory.PRODUCT_SHOT,
    tags={"product", "demo", "4k"}
)

# Search assets
results = library.search_assets(
    query="product",
    asset_type=AssetType.VIDEO,
    min_resolution=(1920, 1080)
)

# Get library stats
stats = library.get_library_stats()
print(f"Total assets: {stats['total_assets']}")
```

## Usage Examples

### Basic Import

```python
from services.video_agent.pro import AssetLibrary, AssetType, AssetCategory

library = AssetLibrary(storage_dir="/tmp/asset_library")

# Import video with metadata extraction
video = library.import_asset(
    source_path="footage.mp4",
    asset_type=AssetType.VIDEO,
    name="Ocean Waves B-Roll",
    category=AssetCategory.B_ROLL,
    tags={"ocean", "nature", "4k"},
    description="Beautiful ocean waves footage",
    generate_thumbnail=True
)

print(f"Video: {video.name}")
print(f"Resolution: {video.metadata.resolution}")
print(f"Duration: {video.metadata.duration}s")
print(f"Codec: {video.metadata.codec.value}")
```

### Bulk Import

```python
# Import all videos from a folder
videos = library.bulk_import(
    folder_path="/path/to/video/library",
    asset_type=AssetType.VIDEO,
    category=AssetCategory.STOCK_FOOTAGE,
    recursive=True,
    file_extensions=['.mp4', '.mov', '.avi']
)

print(f"Imported {len(videos)} videos")

# Import music library
music = library.bulk_import(
    folder_path="/path/to/music",
    asset_type=AssetType.AUDIO,
    category=AssetCategory.MUSIC,
    recursive=True,
    file_extensions=['.mp3', '.wav', '.flac']
)

print(f"Imported {len(music)} music tracks")
```

### Import from URL

```python
# Download and import stock footage
asset = library.import_from_url(
    url="https://example.com/stock/video.mp4",
    asset_type=AssetType.VIDEO,
    name="Stock City Timelapse",
    category=AssetCategory.STOCK_FOOTAGE,
    tags={"city", "timelapse", "urban"}
)

print(f"Downloaded: {asset.name}")
print(f"Source: {asset.source_url}")
```

### Advanced Search

```python
# Find 4K videos under 60 seconds
results = library.search_assets(
    asset_type=AssetType.VIDEO,
    min_resolution=(3840, 2160),
    max_duration=60.0,
    sort_by="created_at",
    reverse=True
)

# Find cinematic LUTs
luts = library.search_assets(
    asset_type=AssetType.LUT,
    category=AssetCategory.CINEMATIC
)

# Find upbeat music 2-4 minutes
music = library.search_assets(
    asset_type=AssetType.AUDIO,
    tags={"upbeat"},
    min_duration=120.0,
    max_duration=240.0
)

# Find HD B-roll without audio
broll = library.search_assets(
    asset_type=AssetType.VIDEO,
    category=AssetCategory.B_ROLL,
    min_resolution=(1920, 1080),
    has_audio=False
)
```

### Favorites & Usage Tracking

```python
# Mark as favorite
library.set_favorite(asset.id, True)

# Track usage
library.mark_used(asset.id)

# Get recently used assets
recent = library.get_recently_used(limit=10)

# Get all favorites
favorites = library.get_favorites()
```

### Tagging

```python
# Add tags
library.add_tag(asset.id, "premium")
library.add_tag(asset.id, "featured")
library.add_tag(asset.id, "trending")

# Remove tag
library.remove_tag(asset.id, "trending")

# Search by tags
premium = library.search_assets(tags={"premium", "featured"})
```

### Cloud Storage

```python
from services.video_agent.pro import CloudStorageManager

# Initialize cloud storage
cloud = CloudStorageManager(
    bucket_name="my-video-assets",
    credentials_path="/path/to/gcs-credentials.json"
)

# Create library with cloud storage
library = AssetLibrary(
    storage_dir="/tmp/assets",
    cloud_storage=cloud
)

# Upload asset to cloud
library.upload_to_cloud(asset.id, include_thumbnail=True)

# Get public URL
url = cloud.get_public_url(asset.cloud_path)
```

### Versioning

```python
# Create new version of asset
new_version = library.create_version(
    asset_id=original.id,
    new_file_path="/path/to/updated.mp4"
)

print(f"Created version {new_version.version}")

# Get all versions
versions = library.get_asset_versions(original.id)
for v in versions:
    print(f"v{v.version}: {v.name}")
```

### Music Organization

```python
from services.video_agent.pro import MusicLibrary

# Get all audio assets
audio = library.search_assets(asset_type=AssetType.AUDIO)

# Organize by mood
by_mood = MusicLibrary.categorize_by_mood(audio)
print(f"Upbeat tracks: {len(by_mood['upbeat'])}")
print(f"Calm tracks: {len(by_mood['calm'])}")
print(f"Energetic tracks: {len(by_mood['energetic'])}")

# Organize by genre
by_genre = MusicLibrary.categorize_by_genre(audio)
print(f"Electronic: {len(by_genre['electronic'])}")
print(f"Cinematic: {len(by_genre['cinematic'])}")
```

### Library Statistics

```python
stats = library.get_library_stats()

print(f"Total assets: {stats['total_assets']}")
print(f"Total size: {stats['total_size_bytes'] / (1024**3):.2f} GB")
print(f"Favorites: {stats['favorites_count']}")
print(f"With thumbnails: {stats['with_thumbnails']}")

print("\nBy type:")
for asset_type, count in stats['by_type'].items():
    print(f"  {asset_type}: {count}")

print("\nBy category:")
for category, count in stats['by_category'].items():
    print(f"  {category}: {count}")
```

### Asset Organization

```python
# Organize by type
by_type = library.organize_by_type()
print(f"Videos: {len(by_type[AssetType.VIDEO])}")
print(f"Audio: {len(by_type[AssetType.AUDIO])}")
print(f"Images: {len(by_type[AssetType.IMAGE])}")

# Organize by category
by_category = library.organize_by_category()
for category, assets in by_category.items():
    if category:
        print(f"{category.value}: {len(assets)} assets")
```

## Data Structures

### Asset

Main asset data structure containing:
- **id**: Unique identifier (hash-based)
- **name**: Asset name
- **asset_type**: Type enum (VIDEO, AUDIO, IMAGE, FONT, LUT, TEMPLATE)
- **category**: Category enum
- **local_path**: Local file path
- **cloud_path**: Cloud storage path
- **file_size**: File size in bytes
- **metadata**: Type-specific metadata object
- **tags**: Set of tags
- **description**: Text description
- **thumbnail_path**: Local thumbnail path
- **thumbnail_cloud_path**: Cloud thumbnail path
- **is_favorite**: Favorite flag
- **use_count**: Usage counter
- **last_used**: Last used timestamp
- **created_at**: Creation timestamp
- **updated_at**: Update timestamp
- **version**: Version number
- **parent_id**: Parent asset ID for versions
- **source_url**: Source URL if imported from web
- **license**: License information

### VideoMetadata

- **duration**: Duration in seconds
- **width**: Video width
- **height**: Video height
- **fps**: Frames per second
- **codec**: Video codec enum
- **bitrate**: Bitrate in bits/second
- **has_audio**: Audio track presence
- **aspect_ratio**: Aspect ratio string
- **color_space**: Color space
- **hdr**: HDR flag

### AudioMetadata

- **duration**: Duration in seconds
- **codec**: Audio codec enum
- **sample_rate**: Sample rate in Hz
- **channels**: Number of channels
- **bitrate**: Bitrate in bits/second
- **bits_per_sample**: Bit depth

### ImageMetadata

- **width**: Image width
- **height**: Image height
- **format**: Image format (png, jpg, etc.)
- **color_mode**: Color mode (RGB, RGBA, etc.)
- **has_alpha**: Alpha channel presence
- **dpi**: DPI resolution

## API Reference

### AssetLibrary

Main library management class.

#### `__init__(storage_dir, database_path=None, cloud_storage=None)`

Initialize asset library.

**Parameters:**
- `storage_dir`: Local storage directory path
- `database_path`: Optional JSON database file path
- `cloud_storage`: Optional CloudStorageManager instance

#### `import_asset(source_path, asset_type, name=None, category=None, tags=None, description=None, copy_file=True, generate_thumbnail=True)`

Import asset from local file.

**Returns:** Asset object or None on failure

#### `import_from_url(url, asset_type, name=None, category=None, tags=None, description=None)`

Import asset from URL.

**Returns:** Asset object or None on failure

#### `bulk_import(folder_path, asset_type, category=None, recursive=True, file_extensions=None)`

Bulk import assets from folder.

**Returns:** List of imported Asset objects

#### `search_assets(query=None, **filters)`

Search assets with filters.

**Filters:**
- `asset_type`: AssetType enum
- `category`: AssetCategory enum
- `tags`: Set of tags
- `favorites_only`: Boolean
- `min_duration`: Float (seconds)
- `max_duration`: Float (seconds)
- `min_resolution`: Tuple (width, height)
- `has_audio`: Boolean
- `sort_by`: String (created_at, updated_at, last_used, use_count, name)
- `reverse`: Boolean

**Returns:** List of matching Asset objects

#### `generate_asset_thumbnail(asset)`

Generate thumbnail for asset.

**Returns:** Boolean success status

#### `upload_to_cloud(asset_id, include_thumbnail=True)`

Upload asset to cloud storage.

**Returns:** Boolean success status

#### `get_asset_metadata(asset_id)`

Get asset metadata.

**Returns:** Metadata object or None

#### `organize_by_type()`

Organize assets by type.

**Returns:** Dict mapping AssetType to List[Asset]

#### `organize_by_category()`

Organize assets by category.

**Returns:** Dict mapping AssetCategory to List[Asset]

#### `add_tag(asset_id, tag)`

Add tag to asset.

**Returns:** Boolean success status

#### `remove_tag(asset_id, tag)`

Remove tag from asset.

**Returns:** Boolean success status

#### `set_favorite(asset_id, is_favorite=True)`

Set favorite status.

**Returns:** Boolean success status

#### `mark_used(asset_id)`

Mark asset as used.

**Returns:** Boolean success status

#### `create_version(asset_id, new_file_path)`

Create new version of asset.

**Returns:** New Asset object or None

#### `get_asset_versions(asset_id)`

Get all versions of asset.

**Returns:** List of Asset objects

#### `delete_asset(asset_id, delete_files=False)`

Delete asset from library.

**Returns:** Boolean success status

#### `get_recently_used(limit=10)`

Get recently used assets.

**Returns:** List of Asset objects

#### `get_favorites()`

Get favorite assets.

**Returns:** List of Asset objects

#### `get_library_stats()`

Get library statistics.

**Returns:** Dict with statistics

### AssetSearch

Static methods for searching and filtering assets.

#### `search(assets, query=None, **filters)`

Search assets with filters.

#### `get_recently_used(assets, limit=10)`

Get recently used assets.

#### `get_favorites(assets)`

Get favorite assets.

#### `get_by_type(assets, asset_type)`

Get assets by type.

### CloudStorageManager

Manage Google Cloud Storage operations.

#### `__init__(bucket_name, credentials_path=None)`

Initialize cloud storage manager.

#### `upload_file(local_path, cloud_path, content_type=None)`

Upload file to cloud.

**Returns:** Cloud URL string

#### `download_file(cloud_path, local_path)`

Download file from cloud.

**Returns:** Boolean success status

#### `delete_file(cloud_path)`

Delete file from cloud.

**Returns:** Boolean success status

#### `file_exists(cloud_path)`

Check if file exists in cloud.

**Returns:** Boolean

#### `get_public_url(cloud_path)`

Get public URL for file.

**Returns:** URL string

### FFProbeExtractor

Extract metadata using FFprobe.

#### `extract_video_metadata(file_path)`

Extract video metadata.

**Returns:** VideoMetadata object or None

#### `extract_audio_metadata(file_path)`

Extract audio metadata.

**Returns:** AudioMetadata object or None

### ThumbnailGenerator

Generate thumbnails for various asset types.

#### `generate_video_thumbnail(video_path, output_path, timestamp=1.0)`

Generate video thumbnail.

**Returns:** Boolean success status

#### `generate_image_thumbnail(image_path, output_path, max_size=320)`

Generate image thumbnail.

**Returns:** Boolean success status

#### `generate_audio_waveform(audio_path, output_path, width=320, height=180)`

Generate audio waveform.

**Returns:** Boolean success status

#### `generate_lut_preview(lut_path, output_path)`

Generate LUT preview.

**Returns:** Boolean success status

### MusicLibrary

Music library organization helpers.

#### `categorize_by_mood(assets)`

Categorize music by mood.

**Returns:** Dict mapping mood string to List[Asset]

#### `categorize_by_genre(assets)`

Categorize music by genre.

**Returns:** Dict mapping genre string to List[Asset]

## Enums

### AssetType
- VIDEO
- AUDIO
- IMAGE
- FONT
- LUT
- TEMPLATE

### AssetCategory
- STOCK_FOOTAGE
- B_ROLL
- PRODUCT_SHOT
- MUSIC
- SOUND_EFFECT
- VOICEOVER
- PHOTO
- GRAPHIC
- TEXTURE
- BACKGROUND
- SERIF
- SANS_SERIF
- DISPLAY
- HANDWRITTEN
- CINEMATIC
- VINTAGE
- MODERN
- CREATIVE
- LOWER_THIRD
- TITLE
- CTA
- TRANSITION

### VideoCodec
- H264
- H265
- PRORES
- VP9
- AV1
- UNKNOWN

### AudioCodec
- AAC
- MP3
- FLAC
- WAV
- OPUS
- VORBIS
- UNKNOWN

## Database Format

Assets are stored in JSON format:

```json
{
  "version": "1.0",
  "updated_at": "2025-12-02T10:00:00",
  "assets": {
    "abc123def456": {
      "id": "abc123def456",
      "name": "Product Demo Video",
      "asset_type": "video",
      "category": "product_shot",
      "local_path": "/path/to/video.mp4",
      "cloud_path": "gs://bucket/assets/video/abc123def456.mp4",
      "file_size": 157286400,
      "metadata": {
        "duration": 30.5,
        "width": 3840,
        "height": 2160,
        "fps": 30.0,
        "codec": "h264",
        "bitrate": 40000000,
        "has_audio": true,
        "aspect_ratio": "16:9"
      },
      "tags": ["product", "demo", "4k"],
      "description": "High-quality product demo",
      "is_favorite": true,
      "use_count": 5,
      "created_at": "2025-12-02T09:00:00",
      "updated_at": "2025-12-02T10:00:00"
    }
  }
}
```

## Performance Considerations

- **Metadata Extraction**: FFprobe operations can be slow for large files
- **Thumbnail Generation**: Video thumbnails require FFmpeg processing
- **Cloud Upload**: Large files may take significant time to upload
- **Database**: JSON database loads entirely into memory
- **Search**: Linear search through all assets (consider indexing for large libraries)

## Best Practices

1. **Organization**: Use consistent tagging and categorization
2. **Thumbnails**: Generate thumbnails for quick preview
3. **Cloud Storage**: Upload important assets for backup and sharing
4. **Favorites**: Mark frequently used assets for quick access
5. **Versioning**: Use versioning for iterative asset development
6. **Bulk Import**: Use bulk import for initial library setup
7. **Metadata**: Let system extract metadata automatically
8. **Search**: Use specific filters to narrow results quickly

## Troubleshooting

### FFprobe not found
Ensure FFmpeg is installed and in system PATH:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Verify installation
ffprobe -version
```

### Cloud storage errors
Check GCS credentials and permissions:
```bash
# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Verify bucket access
gsutil ls gs://your-bucket-name
```

### Import failures
Check file permissions and format support:
```bash
# Check file permissions
ls -la /path/to/file

# Verify format with FFprobe
ffprobe /path/to/file
```

## Future Enhancements

- [ ] PostgreSQL/MySQL database backend option
- [ ] Elasticsearch integration for full-text search
- [ ] AI-powered auto-tagging
- [ ] Face detection and recognition
- [ ] Audio transcription and indexing
- [ ] Duplicate detection
- [ ] Asset compression and optimization
- [ ] CDN integration
- [ ] Collaborative features (sharing, comments)
- [ ] Asset collections and playlists
- [ ] Smart recommendations
- [ ] Usage analytics and reporting

## License

Part of the GeminiVideo Pro-Grade Video Editing System.

## Support

For issues and feature requests, please refer to the main project documentation.
