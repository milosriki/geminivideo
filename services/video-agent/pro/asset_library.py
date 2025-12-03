"""
Professional Asset Library Manager for Pro-Grade Video Editing
Manages video, audio, image, font, LUT, and template assets with cloud storage integration.
"""

import os
import json
import hashlib
import subprocess
import tempfile
import requests
import shutil
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import mimetypes

# Google Cloud Storage imports
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False


class AssetType(Enum):
    """Asset type enumeration"""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    FONT = "font"
    LUT = "lut"
    TEMPLATE = "template"


class AssetCategory(Enum):
    """Asset category for organization"""
    # Video categories
    STOCK_FOOTAGE = "stock_footage"
    B_ROLL = "b_roll"
    PRODUCT_SHOT = "product_shot"

    # Audio categories
    MUSIC = "music"
    SOUND_EFFECT = "sound_effect"
    VOICEOVER = "voiceover"

    # Image categories
    PHOTO = "photo"
    GRAPHIC = "graphic"
    TEXTURE = "texture"
    BACKGROUND = "background"

    # Font categories
    SERIF = "serif"
    SANS_SERIF = "sans_serif"
    DISPLAY = "display"
    HANDWRITTEN = "handwritten"

    # LUT categories
    CINEMATIC = "cinematic"
    VINTAGE = "vintage"
    MODERN = "modern"
    CREATIVE = "creative"

    # Template categories
    LOWER_THIRD = "lower_third"
    TITLE = "title"
    CTA = "cta"
    TRANSITION = "transition"


class VideoCodec(Enum):
    """Common video codecs"""
    H264 = "h264"
    H265 = "h265"
    PRORES = "prores"
    VP9 = "vp9"
    AV1 = "av1"
    UNKNOWN = "unknown"


class AudioCodec(Enum):
    """Common audio codecs"""
    AAC = "aac"
    MP3 = "mp3"
    FLAC = "flac"
    WAV = "wav"
    OPUS = "opus"
    VORBIS = "vorbis"
    UNKNOWN = "unknown"


@dataclass
class VideoMetadata:
    """Video-specific metadata"""
    duration: float  # seconds
    width: int
    height: int
    fps: float
    codec: VideoCodec
    bitrate: int  # bits per second
    has_audio: bool
    aspect_ratio: str
    color_space: Optional[str] = None
    hdr: bool = False

    @property
    def resolution(self) -> str:
        """Get resolution string"""
        return f"{self.width}x{self.height}"

    @property
    def is_4k(self) -> bool:
        """Check if 4K resolution"""
        return self.width >= 3840 and self.height >= 2160

    @property
    def is_hd(self) -> bool:
        """Check if HD resolution"""
        return self.width >= 1280 and self.height >= 720


@dataclass
class AudioMetadata:
    """Audio-specific metadata"""
    duration: float  # seconds
    codec: AudioCodec
    sample_rate: int  # Hz
    channels: int
    bitrate: int  # bits per second
    bits_per_sample: Optional[int] = None

    @property
    def is_stereo(self) -> bool:
        """Check if stereo"""
        return self.channels == 2

    @property
    def is_surround(self) -> bool:
        """Check if surround sound"""
        return self.channels > 2


@dataclass
class ImageMetadata:
    """Image-specific metadata"""
    width: int
    height: int
    format: str  # png, jpg, etc.
    color_mode: str  # RGB, RGBA, etc.
    has_alpha: bool = False
    dpi: Optional[int] = None

    @property
    def resolution(self) -> str:
        """Get resolution string"""
        return f"{self.width}x{self.height}"

    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio"""
        return self.width / self.height if self.height > 0 else 0


@dataclass
class FontMetadata:
    """Font-specific metadata"""
    family: str
    style: str  # Regular, Bold, Italic, etc.
    format: str  # ttf, otf, woff, etc.
    weight: Optional[int] = None
    is_variable: bool = False
    supported_languages: List[str] = field(default_factory=list)


@dataclass
class LUTMetadata:
    """LUT-specific metadata"""
    format: str  # .cube, .3dl, etc.
    size: int  # LUT size (e.g., 33 for 33x33x33)
    input_range: Tuple[float, float] = (0.0, 1.0)
    output_range: Tuple[float, float] = (0.0, 1.0)
    description: Optional[str] = None


@dataclass
class TemplateMetadata:
    """Template-specific metadata"""
    template_type: AssetCategory
    duration: Optional[float] = None
    resolution: Optional[str] = None
    editable_fields: List[str] = field(default_factory=list)
    preview_url: Optional[str] = None


@dataclass
class Asset:
    """Main asset data structure"""
    id: str  # Unique identifier (hash-based)
    name: str
    asset_type: AssetType
    category: Optional[AssetCategory] = None

    # File information
    local_path: Optional[str] = None
    cloud_path: Optional[str] = None
    file_size: int = 0  # bytes

    # Metadata
    metadata: Optional[Union[VideoMetadata, AudioMetadata, ImageMetadata, FontMetadata, LUTMetadata, TemplateMetadata]] = None

    # Organization
    tags: Set[str] = field(default_factory=set)
    description: Optional[str] = None

    # Thumbnails
    thumbnail_path: Optional[str] = None
    thumbnail_cloud_path: Optional[str] = None

    # Usage tracking
    is_favorite: bool = False
    use_count: int = 0
    last_used: Optional[datetime] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Versioning
    version: int = 1
    parent_id: Optional[str] = None  # For versioned assets

    # Source tracking
    source_url: Optional[str] = None
    license: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert sets to lists
        data['tags'] = list(self.tags)
        # Convert enums to strings
        data['asset_type'] = self.asset_type.value
        if self.category:
            data['category'] = self.category.value
        # Convert datetimes to ISO format
        if self.last_used:
            data['last_used'] = self.last_used.isoformat()
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Asset':
        """Create Asset from dictionary"""
        # Convert strings back to enums
        data['asset_type'] = AssetType(data['asset_type'])
        if data.get('category'):
            data['category'] = AssetCategory(data['category'])
        # Convert lists back to sets
        if 'tags' in data:
            data['tags'] = set(data['tags'])
        # Convert ISO strings back to datetime
        if data.get('last_used'):
            data['last_used'] = datetime.fromisoformat(data['last_used'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class FFProbeExtractor:
    """Extract metadata from media files using FFprobe"""

    @staticmethod
    def extract_video_metadata(file_path: str) -> Optional[VideoMetadata]:
        """Extract video metadata using FFprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)

            # Find video stream
            video_stream = None
            audio_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video' and not video_stream:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and not audio_stream:
                    audio_stream = stream

            if not video_stream:
                return None

            # Parse codec
            codec_name = video_stream.get('codec_name', 'unknown').lower()
            codec = VideoCodec.UNKNOWN
            for vc in VideoCodec:
                if vc.value in codec_name:
                    codec = vc
                    break

            # Calculate duration
            duration = float(video_stream.get('duration', 0))
            if duration == 0 and 'format' in data:
                duration = float(data['format'].get('duration', 0))

            # Get FPS
            fps_str = video_stream.get('r_frame_rate', '0/1')
            if '/' in fps_str:
                num, den = map(int, fps_str.split('/'))
                fps = num / den if den != 0 else 0
            else:
                fps = float(fps_str)

            # Calculate aspect ratio
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            aspect_ratio = f"{width}:{height}"
            if width and height:
                from math import gcd
                divisor = gcd(width, height)
                aspect_ratio = f"{width//divisor}:{height//divisor}"

            return VideoMetadata(
                duration=duration,
                width=width,
                height=height,
                fps=fps,
                codec=codec,
                bitrate=int(video_stream.get('bit_rate', 0)),
                has_audio=audio_stream is not None,
                aspect_ratio=aspect_ratio,
                color_space=video_stream.get('color_space'),
                hdr='hdr' in video_stream.get('color_transfer', '').lower()
            )

        except Exception as e:
            print(f"Error extracting video metadata: {e}")
            return None

    @staticmethod
    def extract_audio_metadata(file_path: str) -> Optional[AudioMetadata]:
        """Extract audio metadata using FFprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)

            # Find audio stream
            audio_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break

            if not audio_stream:
                return None

            # Parse codec
            codec_name = audio_stream.get('codec_name', 'unknown').lower()
            codec = AudioCodec.UNKNOWN
            for ac in AudioCodec:
                if ac.value in codec_name:
                    codec = ac
                    break

            # Calculate duration
            duration = float(audio_stream.get('duration', 0))
            if duration == 0 and 'format' in data:
                duration = float(data['format'].get('duration', 0))

            return AudioMetadata(
                duration=duration,
                codec=codec,
                sample_rate=int(audio_stream.get('sample_rate', 0)),
                channels=int(audio_stream.get('channels', 0)),
                bitrate=int(audio_stream.get('bit_rate', 0)),
                bits_per_sample=audio_stream.get('bits_per_sample')
            )

        except Exception as e:
            print(f"Error extracting audio metadata: {e}")
            return None


class ThumbnailGenerator:
    """Generate thumbnails for various asset types"""

    @staticmethod
    def generate_video_thumbnail(video_path: str, output_path: str, timestamp: float = 1.0) -> bool:
        """Generate thumbnail from video at specific timestamp"""
        try:
            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', video_path,
                '-vframes', '1',
                '-vf', 'scale=320:-1',
                '-y',
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=30)
            return result.returncode == 0

        except Exception as e:
            print(f"Error generating video thumbnail: {e}")
            return False

    @staticmethod
    def generate_image_thumbnail(image_path: str, output_path: str, max_size: int = 320) -> bool:
        """Generate thumbnail from image"""
        try:
            cmd = [
                'ffmpeg',
                '-i', image_path,
                '-vf', f'scale={max_size}:-1',
                '-y',
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=30)
            return result.returncode == 0

        except Exception as e:
            print(f"Error generating image thumbnail: {e}")
            return False

    @staticmethod
    def generate_audio_waveform(audio_path: str, output_path: str, width: int = 320, height: int = 180) -> bool:
        """Generate waveform visualization for audio"""
        try:
            cmd = [
                'ffmpeg',
                '-i', audio_path,
                '-filter_complex',
                f'showwavespic=s={width}x{height}:colors=0x00ff00',
                '-frames:v', '1',
                '-y',
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=30)
            return result.returncode == 0

        except Exception as e:
            print(f"Error generating audio waveform: {e}")
            return False

    @staticmethod
    def generate_lut_preview(lut_path: str, output_path: str) -> bool:
        """Generate preview image for LUT"""
        try:
            # Create a color gradient test pattern
            temp_input = tempfile.mktemp(suffix='.png')

            # Generate gradient pattern
            cmd_pattern = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', 'testsrc=size=320x180:rate=1:duration=1',
                '-frames:v', '1',
                '-y',
                temp_input
            ]
            subprocess.run(cmd_pattern, capture_output=True, timeout=10)

            # Apply LUT to pattern
            cmd_lut = [
                'ffmpeg',
                '-i', temp_input,
                '-vf', f'lut3d={lut_path}',
                '-y',
                output_path
            ]

            result = subprocess.run(cmd_lut, capture_output=True, timeout=10)

            # Cleanup
            if os.path.exists(temp_input):
                os.remove(temp_input)

            return result.returncode == 0

        except Exception as e:
            print(f"Error generating LUT preview: {e}")
            return False


class CloudStorageManager:
    """Manage cloud storage operations with Google Cloud Storage"""

    def __init__(self, bucket_name: str, credentials_path: Optional[str] = None):
        """
        Initialize cloud storage manager

        Args:
            bucket_name: GCS bucket name
            credentials_path: Path to GCS credentials JSON file
        """
        if not GCS_AVAILABLE:
            raise ImportError("google-cloud-storage is not installed. Install with: pip install google-cloud-storage")

        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.bucket_name = bucket_name

    def upload_file(self, local_path: str, cloud_path: str, content_type: Optional[str] = None) -> str:
        """
        Upload file to cloud storage

        Args:
            local_path: Local file path
            cloud_path: Destination path in cloud
            content_type: MIME type of file

        Returns:
            Public URL of uploaded file
        """
        blob = self.bucket.blob(cloud_path)

        if content_type:
            blob.upload_from_filename(local_path, content_type=content_type)
        else:
            blob.upload_from_filename(local_path)

        return f"gs://{self.bucket_name}/{cloud_path}"

    def download_file(self, cloud_path: str, local_path: str) -> bool:
        """
        Download file from cloud storage

        Args:
            cloud_path: Source path in cloud
            local_path: Destination local path

        Returns:
            Success status
        """
        try:
            blob = self.bucket.blob(cloud_path)
            blob.download_to_filename(local_path)
            return True
        except Exception as e:
            print(f"Error downloading file: {e}")
            return False

    def delete_file(self, cloud_path: str) -> bool:
        """Delete file from cloud storage"""
        try:
            blob = self.bucket.blob(cloud_path)
            blob.delete()
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    def file_exists(self, cloud_path: str) -> bool:
        """Check if file exists in cloud storage"""
        blob = self.bucket.blob(cloud_path)
        return blob.exists()

    def get_public_url(self, cloud_path: str) -> str:
        """Get public URL for file"""
        return f"https://storage.googleapis.com/{self.bucket_name}/{cloud_path}"


class AssetSearch:
    """Search and filter assets"""

    @staticmethod
    def search(
        assets: List[Asset],
        query: Optional[str] = None,
        asset_type: Optional[AssetType] = None,
        category: Optional[AssetCategory] = None,
        tags: Optional[Set[str]] = None,
        favorites_only: bool = False,
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
        min_resolution: Optional[Tuple[int, int]] = None,
        has_audio: Optional[bool] = None,
        sort_by: str = "created_at",
        reverse: bool = True
    ) -> List[Asset]:
        """
        Search assets with filters

        Args:
            assets: List of assets to search
            query: Search query (matches name, description, tags)
            asset_type: Filter by asset type
            category: Filter by category
            tags: Filter by tags (asset must have all specified tags)
            favorites_only: Only return favorites
            min_duration: Minimum duration for video/audio
            max_duration: Maximum duration for video/audio
            min_resolution: Minimum resolution (width, height) for video/image
            has_audio: Filter videos by audio presence
            sort_by: Sort field (created_at, updated_at, last_used, use_count, name)
            reverse: Reverse sort order

        Returns:
            Filtered and sorted list of assets
        """
        results = assets.copy()

        # Apply filters
        if query:
            query_lower = query.lower()
            results = [
                a for a in results
                if (query_lower in a.name.lower() or
                    (a.description and query_lower in a.description.lower()) or
                    any(query_lower in tag.lower() for tag in a.tags))
            ]

        if asset_type:
            results = [a for a in results if a.asset_type == asset_type]

        if category:
            results = [a for a in results if a.category == category]

        if tags:
            results = [a for a in results if tags.issubset(a.tags)]

        if favorites_only:
            results = [a for a in results if a.is_favorite]

        # Duration filters (for video/audio)
        if min_duration is not None:
            results = [
                a for a in results
                if isinstance(a.metadata, (VideoMetadata, AudioMetadata)) and
                a.metadata.duration >= min_duration
            ]

        if max_duration is not None:
            results = [
                a for a in results
                if isinstance(a.metadata, (VideoMetadata, AudioMetadata)) and
                a.metadata.duration <= max_duration
            ]

        # Resolution filter (for video/image)
        if min_resolution:
            min_width, min_height = min_resolution
            results = [
                a for a in results
                if ((isinstance(a.metadata, VideoMetadata) and
                     a.metadata.width >= min_width and a.metadata.height >= min_height) or
                    (isinstance(a.metadata, ImageMetadata) and
                     a.metadata.width >= min_width and a.metadata.height >= min_height))
            ]

        # Audio presence filter (for video)
        if has_audio is not None:
            results = [
                a for a in results
                if isinstance(a.metadata, VideoMetadata) and
                a.metadata.has_audio == has_audio
            ]

        # Sort results
        sort_key_map = {
            'created_at': lambda a: a.created_at,
            'updated_at': lambda a: a.updated_at,
            'last_used': lambda a: a.last_used or datetime.min,
            'use_count': lambda a: a.use_count,
            'name': lambda a: a.name.lower()
        }

        if sort_by in sort_key_map:
            results.sort(key=sort_key_map[sort_by], reverse=reverse)

        return results

    @staticmethod
    def get_recently_used(assets: List[Asset], limit: int = 10) -> List[Asset]:
        """Get recently used assets"""
        used_assets = [a for a in assets if a.last_used is not None]
        used_assets.sort(key=lambda a: a.last_used, reverse=True)
        return used_assets[:limit]

    @staticmethod
    def get_favorites(assets: List[Asset]) -> List[Asset]:
        """Get favorite assets"""
        return [a for a in assets if a.is_favorite]

    @staticmethod
    def get_by_type(assets: List[Asset], asset_type: AssetType) -> List[Asset]:
        """Get assets by type"""
        return [a for a in assets if a.asset_type == asset_type]


class AssetLibrary:
    """Main asset library management class"""

    def __init__(
        self,
        storage_dir: str,
        database_path: Optional[str] = None,
        cloud_storage: Optional[CloudStorageManager] = None
    ):
        """
        Initialize asset library

        Args:
            storage_dir: Local directory for asset storage
            database_path: Path to JSON database file
            cloud_storage: Optional cloud storage manager
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for asset types
        self.video_dir = self.storage_dir / "videos"
        self.audio_dir = self.storage_dir / "audio"
        self.image_dir = self.storage_dir / "images"
        self.font_dir = self.storage_dir / "fonts"
        self.lut_dir = self.storage_dir / "luts"
        self.template_dir = self.storage_dir / "templates"
        self.thumbnail_dir = self.storage_dir / "thumbnails"

        for dir_path in [
            self.video_dir, self.audio_dir, self.image_dir,
            self.font_dir, self.lut_dir, self.template_dir, self.thumbnail_dir
        ]:
            dir_path.mkdir(exist_ok=True)

        # Database
        self.database_path = database_path or str(self.storage_dir / "library.json")
        self.assets: Dict[str, Asset] = {}
        self.load_database()

        # Cloud storage
        self.cloud_storage = cloud_storage

        # FFprobe extractor
        self.ffprobe = FFProbeExtractor()

        # Thumbnail generator
        self.thumbnail_gen = ThumbnailGenerator()

    def _generate_asset_id(self, file_path: str) -> str:
        """Generate unique asset ID based on file hash"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]

    def _get_asset_directory(self, asset_type: AssetType) -> Path:
        """Get directory for asset type"""
        dir_map = {
            AssetType.VIDEO: self.video_dir,
            AssetType.AUDIO: self.audio_dir,
            AssetType.IMAGE: self.image_dir,
            AssetType.FONT: self.font_dir,
            AssetType.LUT: self.lut_dir,
            AssetType.TEMPLATE: self.template_dir
        }
        return dir_map.get(asset_type, self.storage_dir)

    def import_asset(
        self,
        source_path: str,
        asset_type: AssetType,
        name: Optional[str] = None,
        category: Optional[AssetCategory] = None,
        tags: Optional[Set[str]] = None,
        description: Optional[str] = None,
        copy_file: bool = True,
        generate_thumbnail: bool = True
    ) -> Optional[Asset]:
        """
        Import asset from local file

        Args:
            source_path: Path to source file
            asset_type: Type of asset
            name: Asset name (defaults to filename)
            category: Asset category
            tags: Asset tags
            description: Asset description
            copy_file: Whether to copy file to library storage
            generate_thumbnail: Whether to generate thumbnail

        Returns:
            Created Asset object or None on failure
        """
        if not os.path.exists(source_path):
            print(f"Source file not found: {source_path}")
            return None

        # Generate asset ID
        asset_id = self._generate_asset_id(source_path)

        # Check if asset already exists
        if asset_id in self.assets:
            print(f"Asset already exists: {self.assets[asset_id].name}")
            return self.assets[asset_id]

        # Determine name
        if not name:
            name = os.path.basename(source_path)

        # Determine destination path
        dest_dir = self._get_asset_directory(asset_type)
        file_ext = os.path.splitext(source_path)[1]
        dest_path = dest_dir / f"{asset_id}{file_ext}"

        # Copy or reference file
        if copy_file:
            shutil.copy2(source_path, dest_path)
            local_path = str(dest_path)
        else:
            local_path = source_path

        # Extract metadata
        metadata = None
        if asset_type == AssetType.VIDEO:
            metadata = self.ffprobe.extract_video_metadata(local_path)
        elif asset_type == AssetType.AUDIO:
            metadata = self.ffprobe.extract_audio_metadata(local_path)

        # Create asset
        asset = Asset(
            id=asset_id,
            name=name,
            asset_type=asset_type,
            category=category,
            local_path=local_path,
            file_size=os.path.getsize(local_path),
            metadata=metadata,
            tags=tags or set(),
            description=description
        )

        # Generate thumbnail
        if generate_thumbnail:
            self.generate_asset_thumbnail(asset)

        # Add to library
        self.assets[asset_id] = asset
        self.save_database()

        return asset

    def import_from_url(
        self,
        url: str,
        asset_type: AssetType,
        name: Optional[str] = None,
        category: Optional[AssetCategory] = None,
        tags: Optional[Set[str]] = None,
        description: Optional[str] = None
    ) -> Optional[Asset]:
        """
        Import asset from URL

        Args:
            url: URL to download from
            asset_type: Type of asset
            name: Asset name
            category: Asset category
            tags: Asset tags
            description: Asset description

        Returns:
            Created Asset object or None on failure
        """
        try:
            # Download file
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()

            # Determine filename
            if not name:
                parsed_url = urlparse(url)
                name = os.path.basename(parsed_url.path) or "downloaded_asset"

            # Determine file extension from content-type or URL
            content_type = response.headers.get('content-type', '')
            ext = mimetypes.guess_extension(content_type) or os.path.splitext(name)[1] or '.bin'

            # Save to temporary file
            temp_file = tempfile.mktemp(suffix=ext)
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Import the downloaded file
            asset = self.import_asset(
                source_path=temp_file,
                asset_type=asset_type,
                name=name,
                category=category,
                tags=tags,
                description=description,
                copy_file=True
            )

            if asset:
                asset.source_url = url
                self.save_database()

            # Cleanup temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)

            return asset

        except Exception as e:
            print(f"Error importing from URL: {e}")
            return None

    def bulk_import(
        self,
        folder_path: str,
        asset_type: AssetType,
        category: Optional[AssetCategory] = None,
        recursive: bool = True,
        file_extensions: Optional[List[str]] = None
    ) -> List[Asset]:
        """
        Bulk import assets from folder

        Args:
            folder_path: Path to folder
            asset_type: Type of assets
            category: Asset category
            recursive: Search recursively
            file_extensions: List of file extensions to import (e.g., ['.mp4', '.mov'])

        Returns:
            List of imported assets
        """
        imported_assets = []

        folder = Path(folder_path)
        if not folder.exists():
            print(f"Folder not found: {folder_path}")
            return imported_assets

        # Get file list
        if recursive:
            files = list(folder.rglob('*'))
        else:
            files = list(folder.glob('*'))

        # Filter by extension if specified
        if file_extensions:
            files = [f for f in files if f.suffix.lower() in [ext.lower() for ext in file_extensions]]

        # Import each file
        for file_path in files:
            if file_path.is_file():
                asset = self.import_asset(
                    source_path=str(file_path),
                    asset_type=asset_type,
                    category=category
                )
                if asset:
                    imported_assets.append(asset)

        return imported_assets

    def generate_asset_thumbnail(self, asset: Asset) -> bool:
        """
        Generate thumbnail for asset

        Args:
            asset: Asset to generate thumbnail for

        Returns:
            Success status
        """
        if not asset.local_path or not os.path.exists(asset.local_path):
            return False

        thumbnail_path = self.thumbnail_dir / f"{asset.id}.jpg"
        success = False

        if asset.asset_type == AssetType.VIDEO:
            success = self.thumbnail_gen.generate_video_thumbnail(
                asset.local_path,
                str(thumbnail_path)
            )
        elif asset.asset_type == AssetType.IMAGE:
            success = self.thumbnail_gen.generate_image_thumbnail(
                asset.local_path,
                str(thumbnail_path)
            )
        elif asset.asset_type == AssetType.AUDIO:
            success = self.thumbnail_gen.generate_audio_waveform(
                asset.local_path,
                str(thumbnail_path)
            )
        elif asset.asset_type == AssetType.LUT:
            success = self.thumbnail_gen.generate_lut_preview(
                asset.local_path,
                str(thumbnail_path)
            )

        if success:
            asset.thumbnail_path = str(thumbnail_path)
            self.save_database()

        return success

    def upload_to_cloud(self, asset_id: str, include_thumbnail: bool = True) -> bool:
        """
        Upload asset to cloud storage

        Args:
            asset_id: Asset ID
            include_thumbnail: Also upload thumbnail

        Returns:
            Success status
        """
        if not self.cloud_storage:
            print("Cloud storage not configured")
            return False

        asset = self.assets.get(asset_id)
        if not asset or not asset.local_path:
            return False

        try:
            # Upload main file
            file_ext = os.path.splitext(asset.local_path)[1]
            cloud_path = f"assets/{asset.asset_type.value}/{asset.id}{file_ext}"

            content_type, _ = mimetypes.guess_type(asset.local_path)
            asset.cloud_path = self.cloud_storage.upload_file(
                asset.local_path,
                cloud_path,
                content_type
            )

            # Upload thumbnail
            if include_thumbnail and asset.thumbnail_path and os.path.exists(asset.thumbnail_path):
                thumbnail_cloud_path = f"assets/thumbnails/{asset.id}.jpg"
                asset.thumbnail_cloud_path = self.cloud_storage.upload_file(
                    asset.thumbnail_path,
                    thumbnail_cloud_path,
                    'image/jpeg'
                )

            asset.updated_at = datetime.now()
            self.save_database()
            return True

        except Exception as e:
            print(f"Error uploading to cloud: {e}")
            return False

    def get_asset_metadata(self, asset_id: str) -> Optional[Union[VideoMetadata, AudioMetadata, ImageMetadata, FontMetadata, LUTMetadata, TemplateMetadata]]:
        """Get asset metadata"""
        asset = self.assets.get(asset_id)
        return asset.metadata if asset else None

    def search_assets(
        self,
        query: Optional[str] = None,
        **filters
    ) -> List[Asset]:
        """
        Search assets

        Args:
            query: Search query
            **filters: Additional filters (see AssetSearch.search)

        Returns:
            List of matching assets
        """
        return AssetSearch.search(list(self.assets.values()), query=query, **filters)

    def organize_by_type(self) -> Dict[AssetType, List[Asset]]:
        """Organize assets by type"""
        organized = {}
        for asset_type in AssetType:
            organized[asset_type] = AssetSearch.get_by_type(
                list(self.assets.values()),
                asset_type
            )
        return organized

    def organize_by_category(self) -> Dict[Optional[AssetCategory], List[Asset]]:
        """Organize assets by category"""
        organized = {}
        for asset in self.assets.values():
            if asset.category not in organized:
                organized[asset.category] = []
            organized[asset.category].append(asset)
        return organized

    def add_tag(self, asset_id: str, tag: str) -> bool:
        """Add tag to asset"""
        asset = self.assets.get(asset_id)
        if asset:
            asset.tags.add(tag)
            asset.updated_at = datetime.now()
            self.save_database()
            return True
        return False

    def remove_tag(self, asset_id: str, tag: str) -> bool:
        """Remove tag from asset"""
        asset = self.assets.get(asset_id)
        if asset and tag in asset.tags:
            asset.tags.remove(tag)
            asset.updated_at = datetime.now()
            self.save_database()
            return True
        return False

    def set_favorite(self, asset_id: str, is_favorite: bool = True) -> bool:
        """Set asset favorite status"""
        asset = self.assets.get(asset_id)
        if asset:
            asset.is_favorite = is_favorite
            asset.updated_at = datetime.now()
            self.save_database()
            return True
        return False

    def mark_used(self, asset_id: str) -> bool:
        """Mark asset as used (updates use count and last used timestamp)"""
        asset = self.assets.get(asset_id)
        if asset:
            asset.use_count += 1
            asset.last_used = datetime.now()
            self.save_database()
            return True
        return False

    def create_version(self, asset_id: str, new_file_path: str) -> Optional[Asset]:
        """
        Create new version of asset

        Args:
            asset_id: Original asset ID
            new_file_path: Path to new version file

        Returns:
            New versioned asset
        """
        original = self.assets.get(asset_id)
        if not original:
            return None

        # Import new version
        new_asset = self.import_asset(
            source_path=new_file_path,
            asset_type=original.asset_type,
            name=f"{original.name} (v{original.version + 1})",
            category=original.category,
            tags=original.tags.copy(),
            description=original.description
        )

        if new_asset:
            new_asset.version = original.version + 1
            new_asset.parent_id = asset_id
            self.save_database()

        return new_asset

    def get_asset_versions(self, asset_id: str) -> List[Asset]:
        """Get all versions of an asset"""
        versions = []
        for asset in self.assets.values():
            if asset.parent_id == asset_id or asset.id == asset_id:
                versions.append(asset)
        versions.sort(key=lambda a: a.version)
        return versions

    def delete_asset(self, asset_id: str, delete_files: bool = False) -> bool:
        """
        Delete asset from library

        Args:
            asset_id: Asset ID
            delete_files: Whether to delete physical files

        Returns:
            Success status
        """
        asset = self.assets.get(asset_id)
        if not asset:
            return False

        # Delete files if requested
        if delete_files:
            if asset.local_path and os.path.exists(asset.local_path):
                os.remove(asset.local_path)
            if asset.thumbnail_path and os.path.exists(asset.thumbnail_path):
                os.remove(asset.thumbnail_path)
            if asset.cloud_path and self.cloud_storage:
                self.cloud_storage.delete_file(asset.cloud_path.replace(f"gs://{self.cloud_storage.bucket_name}/", ""))
            if asset.thumbnail_cloud_path and self.cloud_storage:
                self.cloud_storage.delete_file(asset.thumbnail_cloud_path.replace(f"gs://{self.cloud_storage.bucket_name}/", ""))

        # Remove from library
        del self.assets[asset_id]
        self.save_database()
        return True

    def get_recently_used(self, limit: int = 10) -> List[Asset]:
        """Get recently used assets"""
        return AssetSearch.get_recently_used(list(self.assets.values()), limit)

    def get_favorites(self) -> List[Asset]:
        """Get favorite assets"""
        return AssetSearch.get_favorites(list(self.assets.values()))

    def get_library_stats(self) -> Dict[str, Any]:
        """Get library statistics"""
        stats = {
            'total_assets': len(self.assets),
            'by_type': {},
            'by_category': {},
            'total_size_bytes': 0,
            'favorites_count': 0,
            'with_thumbnails': 0
        }

        for asset in self.assets.values():
            # Count by type
            type_key = asset.asset_type.value
            stats['by_type'][type_key] = stats['by_type'].get(type_key, 0) + 1

            # Count by category
            if asset.category:
                cat_key = asset.category.value
                stats['by_category'][cat_key] = stats['by_category'].get(cat_key, 0) + 1

            # Total size
            stats['total_size_bytes'] += asset.file_size

            # Favorites
            if asset.is_favorite:
                stats['favorites_count'] += 1

            # Thumbnails
            if asset.thumbnail_path:
                stats['with_thumbnails'] += 1

        return stats

    def save_database(self):
        """Save library database to JSON file"""
        data = {
            'version': '1.0',
            'updated_at': datetime.now().isoformat(),
            'assets': {
                asset_id: asset.to_dict()
                for asset_id, asset in self.assets.items()
            }
        }

        with open(self.database_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_database(self):
        """Load library database from JSON file"""
        if not os.path.exists(self.database_path):
            return

        try:
            with open(self.database_path, 'r') as f:
                data = json.load(f)

            # Load assets
            for asset_id, asset_data in data.get('assets', {}).items():
                try:
                    asset = Asset.from_dict(asset_data)
                    self.assets[asset_id] = asset
                except Exception as e:
                    print(f"Error loading asset {asset_id}: {e}")

        except Exception as e:
            print(f"Error loading database: {e}")


# Convenience functions for stock footage integration

class StockFootageProvider:
    """Base class for stock footage provider integration"""

    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search stock footage"""
        raise NotImplementedError

    def download(self, asset_info: Dict[str, Any], output_path: str) -> bool:
        """Download stock footage asset"""
        raise NotImplementedError


class MusicLibrary:
    """Music library organization helpers"""

    @staticmethod
    def categorize_by_mood(assets: List[Asset]) -> Dict[str, List[Asset]]:
        """Categorize music by mood (based on tags)"""
        moods = ['upbeat', 'calm', 'energetic', 'dramatic', 'inspiring', 'happy', 'sad', 'intense']
        categorized = {mood: [] for mood in moods}
        categorized['other'] = []

        for asset in assets:
            if asset.asset_type != AssetType.AUDIO:
                continue

            found_mood = False
            for mood in moods:
                if mood in asset.tags:
                    categorized[mood].append(asset)
                    found_mood = True
                    break

            if not found_mood:
                categorized['other'].append(asset)

        return categorized

    @staticmethod
    def categorize_by_genre(assets: List[Asset]) -> Dict[str, List[Asset]]:
        """Categorize music by genre (based on tags)"""
        genres = ['rock', 'pop', 'electronic', 'classical', 'jazz', 'hip-hop', 'ambient', 'cinematic']
        categorized = {genre: [] for genre in genres}
        categorized['other'] = []

        for asset in assets:
            if asset.asset_type != AssetType.AUDIO:
                continue

            found_genre = False
            for genre in genres:
                if genre in asset.tags:
                    categorized[genre].append(asset)
                    found_genre = True
                    break

            if not found_genre:
                categorized['other'].append(asset)

        return categorized


# Example usage and testing
if __name__ == "__main__":
    # Initialize library
    library = AssetLibrary(storage_dir="/tmp/asset_library")

    print("Asset Library Manager initialized")
    print(f"Storage directory: {library.storage_dir}")

    # Get library stats
    stats = library.get_library_stats()
    print(f"\nLibrary Statistics:")
    print(f"  Total assets: {stats['total_assets']}")
    print(f"  By type: {stats['by_type']}")
    print(f"  Favorites: {stats['favorites_count']}")
