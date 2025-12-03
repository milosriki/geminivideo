"""
Real-Time Preview Generator - PRO-GRADE Video Editing
Fast preview generation with GPU acceleration, caching, and WebSocket streaming.
Supports frame extraction, thumbnails, proxy videos, effects, waveforms, and compositing.
"""

import subprocess
import json
import os
import hashlib
import tempfile
import shutil
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Generator, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import base64
from io import BytesIO
from collections import OrderedDict

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProxyQuality(Enum):
    """Proxy video quality presets"""
    ULTRA_LOW = "240p"   # 240p for very fast scrubbing
    LOW = "360p"         # 360p for mobile editing
    MEDIUM = "480p"      # 480p for standard editing
    HIGH = "720p"        # 720p for high-quality preview


class EffectType(Enum):
    """Supported preview effects"""
    BLUR = "blur"
    SHARPEN = "sharpen"
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    SATURATION = "saturation"
    GRAYSCALE = "grayscale"
    SEPIA = "sepia"
    INVERT = "invert"
    VIGNETTE = "vignette"
    EDGE_DETECT = "edge_detect"
    EMBOSS = "emboss"
    COLOR_TINT = "color_tint"
    TEMPERATURE = "temperature"
    FADE = "fade"


class CacheStrategy(Enum):
    """Cache management strategies"""
    LRU = "lru"          # Least Recently Used
    LFU = "lfu"          # Least Frequently Used
    SIZE_LIMIT = "size"  # Size-based eviction
    TIME_LIMIT = "time"  # Time-based expiration


@dataclass
class GPUCapabilities:
    """GPU acceleration capabilities"""
    has_nvidia: bool = False
    has_nvenc: bool = False
    has_cuvid: bool = False
    has_vaapi: bool = False
    has_qsv: bool = False
    decoder: Optional[str] = None


@dataclass
class PreviewFrame:
    """Single preview frame data"""
    timestamp: float
    width: int
    height: int
    format: str
    data: bytes
    cached: bool = False
    generation_time: float = 0.0


@dataclass
class ThumbnailStrip:
    """Timeline thumbnail strip"""
    video_path: str
    total_frames: int
    width: int
    height: int
    columns: int
    rows: int
    image_data: bytes
    timestamps: List[float]


@dataclass
class WaveformData:
    """Audio waveform data for visualization"""
    audio_path: str
    duration: float
    sample_rate: int
    channels: int
    peaks: np.ndarray
    rms: np.ndarray
    samples_per_pixel: int


@dataclass
class ProxyVideoInfo:
    """Proxy video information"""
    original_path: str
    proxy_path: str
    original_resolution: Tuple[int, int]
    proxy_resolution: Tuple[int, int]
    quality: ProxyQuality
    file_size: int
    generation_time: float


@dataclass
class CompositePreview:
    """Composite preview from multiple tracks"""
    tracks: List[str]
    timestamp: float
    width: int
    height: int
    image_data: bytes
    blend_modes: List[str]


@dataclass
class EffectPreview:
    """Before/after effect preview"""
    original: bytes
    processed: bytes
    effect_type: str
    parameters: Dict[str, Any]
    processing_time: float


class PreviewCache:
    """LRU cache for preview frames and thumbnails"""

    def __init__(self, max_size_mb: int = 500, max_items: int = 1000):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_items = max_items
        self.cache: OrderedDict = OrderedDict()
        self.current_size = 0
        self.hits = 0
        self.misses = 0

    def _make_key(self, video_path: str, timestamp: float, width: int = 0, height: int = 0) -> str:
        """Generate cache key"""
        key_str = f"{video_path}:{timestamp}:{width}:{height}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, video_path: str, timestamp: float, width: int = 0, height: int = 0) -> Optional[bytes]:
        """Get cached frame"""
        key = self._make_key(video_path, timestamp, width, height)
        if key in self.cache:
            self.hits += 1
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        self.misses += 1
        return None

    def put(self, video_path: str, timestamp: float, data: bytes, width: int = 0, height: int = 0):
        """Cache frame data"""
        key = self._make_key(video_path, timestamp, width, height)
        data_size = len(data)

        # Remove old entries if necessary
        while (self.current_size + data_size > self.max_size_bytes or
               len(self.cache) >= self.max_items) and self.cache:
            oldest_key, oldest_data = self.cache.popitem(last=False)
            self.current_size -= len(oldest_data)

        self.cache[key] = data
        self.current_size += data_size

    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.current_size = 0
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        return {
            "size_mb": self.current_size / (1024 * 1024),
            "items": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%"
        }


class PreviewGenerator:
    """
    Real-time preview generator for PRO-GRADE video editing.

    Features:
    - Fast frame extraction with GPU acceleration
    - Thumbnail generation at intervals
    - Proxy video creation for smooth editing
    - Real-time effect preview
    - Audio waveform extraction
    - Timeline thumbnail strips
    - WebSocket streaming
    - Intelligent caching
    - Multi-track compositing
    """

    def __init__(self,
                 cache_size_mb: int = 500,
                 cache_max_items: int = 1000,
                 temp_dir: Optional[str] = None,
                 enable_gpu: bool = True):
        """
        Initialize preview generator

        Args:
            cache_size_mb: Maximum cache size in MB
            cache_max_items: Maximum number of cached items
            temp_dir: Temporary directory for proxy videos
            enable_gpu: Enable GPU acceleration
        """
        self.cache = PreviewCache(cache_size_mb, cache_max_items)
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.enable_gpu = enable_gpu
        self.gpu_caps = self._detect_gpu_capabilities()
        self.proxy_cache: Dict[str, ProxyVideoInfo] = {}

        logger.info(f"PreviewGenerator initialized with GPU support: {self.gpu_caps.has_nvidia or self.gpu_caps.has_vaapi}")

    def _detect_gpu_capabilities(self) -> GPUCapabilities:
        """Detect available GPU acceleration"""
        caps = GPUCapabilities()

        if not self.enable_gpu:
            return caps

        try:
            # Check for NVIDIA GPU
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-hwaccels'],
                capture_output=True,
                text=True,
                timeout=5
            )

            hwaccels = result.stdout.lower()

            if 'cuda' in hwaccels or 'nvdec' in hwaccels:
                caps.has_nvidia = True
                caps.has_cuvid = True
                caps.decoder = 'h264_cuvid'
                logger.info("NVIDIA GPU detected")

            if 'vaapi' in hwaccels:
                caps.has_vaapi = True
                logger.info("VAAPI acceleration detected")

            if 'qsv' in hwaccels:
                caps.has_qsv = True
                logger.info("Intel QSV detected")

        except Exception as e:
            logger.warning(f"GPU detection failed: {e}")

        return caps

    def _get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata using ffprobe"""
        try:
            result = subprocess.run([
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ], capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                raise RuntimeError(f"ffprobe failed: {result.stderr}")

            data = json.loads(result.stdout)

            # Find video stream
            video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
            audio_stream = next((s for s in data['streams'] if s['codec_type'] == 'audio'), None)

            if not video_stream:
                raise ValueError("No video stream found")

            # Parse FPS
            fps_parts = video_stream.get('r_frame_rate', '30/1').split('/')
            fps = int(fps_parts[0]) / int(fps_parts[1])

            return {
                'duration': float(data['format'].get('duration', 0)),
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'fps': fps,
                'codec': video_stream.get('codec_name', 'unknown'),
                'bitrate': int(data['format'].get('bit_rate', 0)),
                'has_audio': audio_stream is not None,
                'audio_codec': audio_stream.get('codec_name') if audio_stream else None,
                'audio_channels': int(audio_stream.get('channels', 0)) if audio_stream else 0,
            }
        except Exception as e:
            logger.error(f"Failed to get video metadata: {e}")
            raise

    def extract_frame(self,
                     video_path: str,
                     timestamp: float,
                     width: Optional[int] = None,
                     height: Optional[int] = None,
                     use_cache: bool = True) -> Image.Image:
        """
        Extract single frame at timestamp

        Args:
            video_path: Path to video file
            timestamp: Timestamp in seconds
            width: Output width (None = original)
            height: Output height (None = original)
            use_cache: Use cached frame if available

        Returns:
            PIL Image object
        """
        start_time = time.time()

        # Check cache
        if use_cache:
            cached_data = self.cache.get(video_path, timestamp, width or 0, height or 0)
            if cached_data:
                logger.debug(f"Frame cache hit for {video_path} @ {timestamp}s")
                return Image.open(BytesIO(cached_data))

        # Build FFmpeg command
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error']

        # GPU acceleration
        if self.gpu_caps.has_nvidia and self.gpu_caps.decoder:
            cmd.extend(['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda'])
        elif self.gpu_caps.has_vaapi:
            cmd.extend(['-hwaccel', 'vaapi', '-hwaccel_device', '/dev/dri/renderD128'])

        # Seek to timestamp
        cmd.extend(['-ss', str(timestamp)])

        # Input file
        cmd.extend(['-i', video_path])

        # Extract single frame
        cmd.extend(['-frames:v', '1'])

        # Scale if needed
        if width or height:
            scale_w = width if width else -1
            scale_h = height if height else -1
            cmd.extend(['-vf', f'scale={scale_w}:{scale_h}'])

        # Output to pipe
        cmd.extend(['-f', 'image2pipe', '-vcodec', 'png', 'pipe:1'])

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=30)

            if result.returncode != 0:
                raise RuntimeError(f"Frame extraction failed: {result.stderr.decode()}")

            # Load image
            image = Image.open(BytesIO(result.stdout))

            # Cache the frame
            if use_cache:
                self.cache.put(video_path, timestamp, result.stdout, width or 0, height or 0)

            elapsed = time.time() - start_time
            logger.debug(f"Extracted frame at {timestamp}s in {elapsed:.3f}s")

            return image

        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Frame extraction timed out for {video_path} @ {timestamp}s")
        except Exception as e:
            logger.error(f"Failed to extract frame: {e}")
            raise

    def generate_thumbnails(self,
                           video_path: str,
                           interval: float = 1.0,
                           width: int = 160,
                           height: int = 90,
                           max_thumbnails: Optional[int] = None) -> List[PreviewFrame]:
        """
        Generate thumbnails at regular intervals

        Args:
            video_path: Path to video file
            interval: Interval between thumbnails in seconds
            width: Thumbnail width
            height: Thumbnail height
            max_thumbnails: Maximum number of thumbnails

        Returns:
            List of PreviewFrame objects
        """
        logger.info(f"Generating thumbnails for {video_path} at {interval}s intervals")

        # Get video metadata
        metadata = self._get_video_metadata(video_path)
        duration = metadata['duration']

        # Calculate timestamps
        timestamps = []
        t = 0
        while t < duration:
            timestamps.append(t)
            t += interval
            if max_thumbnails and len(timestamps) >= max_thumbnails:
                break

        # Extract frames in parallel
        thumbnails = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self.extract_frame, video_path, ts, width, height): ts
                for ts in timestamps
            }

            for future in as_completed(futures):
                ts = futures[future]
                try:
                    img = future.result()

                    # Convert to bytes
                    buffer = BytesIO()
                    img.save(buffer, format='JPEG', quality=85)
                    img_bytes = buffer.getvalue()

                    thumbnails.append(PreviewFrame(
                        timestamp=ts,
                        width=width,
                        height=height,
                        format='jpeg',
                        data=img_bytes,
                        cached=True
                    ))
                except Exception as e:
                    logger.error(f"Failed to generate thumbnail at {ts}s: {e}")

        # Sort by timestamp
        thumbnails.sort(key=lambda x: x.timestamp)

        logger.info(f"Generated {len(thumbnails)} thumbnails")
        return thumbnails

    def generate_proxy(self,
                      video_path: str,
                      quality: ProxyQuality = ProxyQuality.MEDIUM,
                      output_dir: Optional[str] = None) -> str:
        """
        Generate proxy video for smooth editing

        Args:
            video_path: Path to original video
            quality: Proxy quality preset
            output_dir: Output directory (None = temp dir)

        Returns:
            Path to proxy video
        """
        start_time = time.time()

        # Check if proxy already exists
        cache_key = f"{video_path}:{quality.value}"
        if cache_key in self.proxy_cache:
            proxy_info = self.proxy_cache[cache_key]
            if os.path.exists(proxy_info.proxy_path):
                logger.info(f"Using cached proxy: {proxy_info.proxy_path}")
                return proxy_info.proxy_path

        logger.info(f"Generating {quality.value} proxy for {video_path}")

        # Get original metadata
        metadata = self._get_video_metadata(video_path)
        orig_width = metadata['width']
        orig_height = metadata['height']

        # Calculate proxy resolution
        resolution_map = {
            ProxyQuality.ULTRA_LOW: 240,
            ProxyQuality.LOW: 360,
            ProxyQuality.MEDIUM: 480,
            ProxyQuality.HIGH: 720,
        }

        target_height = resolution_map[quality]
        target_width = int(orig_width * target_height / orig_height)
        # Make divisible by 2
        target_width = target_width - (target_width % 2)
        target_height = target_height - (target_height % 2)

        # Output path
        output_dir = output_dir or self.temp_dir
        os.makedirs(output_dir, exist_ok=True)

        video_name = Path(video_path).stem
        proxy_filename = f"{video_name}_proxy_{quality.value}.mp4"
        proxy_path = os.path.join(output_dir, proxy_filename)

        # Build FFmpeg command
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-y']

        # GPU acceleration for decoding
        if self.gpu_caps.has_nvidia:
            cmd.extend(['-hwaccel', 'cuda'])
        elif self.gpu_caps.has_vaapi:
            cmd.extend(['-hwaccel', 'vaapi'])

        # Input
        cmd.extend(['-i', video_path])

        # Video encoding
        cmd.extend([
            '-vf', f'scale={target_width}:{target_height}',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '28',  # Lower quality for proxies
            '-profile:v', 'baseline',
            '-level', '3.0',
        ])

        # Audio encoding (lower quality)
        if metadata['has_audio']:
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', '64k',
                '-ac', '2'  # Stereo
            ])
        else:
            cmd.extend(['-an'])

        # Output
        cmd.append(proxy_path)

        try:
            # Run with progress monitoring
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode != 0:
                raise RuntimeError(f"Proxy generation failed: {result.stderr}")

            # Get file size
            file_size = os.path.getsize(proxy_path)
            elapsed = time.time() - start_time

            # Cache proxy info
            proxy_info = ProxyVideoInfo(
                original_path=video_path,
                proxy_path=proxy_path,
                original_resolution=(orig_width, orig_height),
                proxy_resolution=(target_width, target_height),
                quality=quality,
                file_size=file_size,
                generation_time=elapsed
            )
            self.proxy_cache[cache_key] = proxy_info

            logger.info(f"Generated proxy in {elapsed:.2f}s: {proxy_path} ({file_size / 1024 / 1024:.2f} MB)")
            return proxy_path

        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Proxy generation timed out")
        except Exception as e:
            logger.error(f"Failed to generate proxy: {e}")
            if os.path.exists(proxy_path):
                os.remove(proxy_path)
            raise

    def preview_effect(self,
                      frame: Union[Image.Image, str],
                      effect_type: Union[EffectType, str],
                      parameters: Optional[Dict[str, Any]] = None) -> Image.Image:
        """
        Apply effect to single frame for preview

        Args:
            frame: PIL Image or path to image file
            effect_type: Effect type to apply
            parameters: Effect parameters

        Returns:
            Processed PIL Image
        """
        # Load frame if path provided
        if isinstance(frame, str):
            frame = Image.open(frame)

        # Copy frame
        processed = frame.copy()

        # Parse effect type
        if isinstance(effect_type, str):
            effect_type = EffectType(effect_type.lower())

        params = parameters or {}

        # Apply effect
        if effect_type == EffectType.BLUR:
            radius = params.get('radius', 5)
            processed = processed.filter(ImageFilter.GaussianBlur(radius))

        elif effect_type == EffectType.SHARPEN:
            amount = params.get('amount', 1.0)
            processed = processed.filter(ImageFilter.SHARPEN)
            if amount > 1:
                for _ in range(int(amount) - 1):
                    processed = processed.filter(ImageFilter.SHARPEN)

        elif effect_type == EffectType.BRIGHTNESS:
            factor = params.get('factor', 1.5)
            enhancer = ImageEnhance.Brightness(processed)
            processed = enhancer.enhance(factor)

        elif effect_type == EffectType.CONTRAST:
            factor = params.get('factor', 1.5)
            enhancer = ImageEnhance.Contrast(processed)
            processed = enhancer.enhance(factor)

        elif effect_type == EffectType.SATURATION:
            factor = params.get('factor', 1.5)
            enhancer = ImageEnhance.Color(processed)
            processed = enhancer.enhance(factor)

        elif effect_type == EffectType.GRAYSCALE:
            processed = processed.convert('L').convert('RGB')

        elif effect_type == EffectType.SEPIA:
            # Convert to grayscale first
            gray = processed.convert('L')
            # Create sepia tone
            sepia = Image.new('RGB', processed.size)
            sepia_pixels = []
            for pixel in gray.getdata():
                # Sepia tone formula
                r = min(255, int(pixel * 1.0))
                g = min(255, int(pixel * 0.95))
                b = min(255, int(pixel * 0.82))
                sepia_pixels.append((r, g, b))
            sepia.putdata(sepia_pixels)
            processed = sepia

        elif effect_type == EffectType.INVERT:
            if processed.mode == 'RGBA':
                r, g, b, a = processed.split()
                rgb = Image.merge('RGB', (r, g, b))
                inverted = Image.eval(rgb, lambda x: 255 - x)
                processed = Image.merge('RGBA', (*inverted.split(), a))
            else:
                processed = Image.eval(processed, lambda x: 255 - x)

        elif effect_type == EffectType.VIGNETTE:
            strength = params.get('strength', 0.5)
            # Create radial gradient mask
            width, height = processed.size
            mask = Image.new('L', (width, height), 0)
            draw = ImageDraw.Draw(mask)

            # Draw ellipse
            for i in range(int(min(width, height) / 2)):
                alpha = int(255 * (1 - i / (min(width, height) / 2) * strength))
                draw.ellipse([i, i, width-i, height-i], fill=alpha)

            # Apply mask
            darkened = Image.new('RGB', processed.size, (0, 0, 0))
            processed = Image.composite(processed, darkened, mask)

        elif effect_type == EffectType.EDGE_DETECT:
            processed = processed.filter(ImageFilter.FIND_EDGES)

        elif effect_type == EffectType.EMBOSS:
            processed = processed.filter(ImageFilter.EMBOSS)

        elif effect_type == EffectType.COLOR_TINT:
            color = params.get('color', (255, 200, 150))
            strength = params.get('strength', 0.3)

            # Create color overlay
            overlay = Image.new('RGB', processed.size, color)
            processed = Image.blend(processed.convert('RGB'), overlay, strength)

        elif effect_type == EffectType.TEMPERATURE:
            temp = params.get('temperature', 0)  # -100 to 100

            if temp > 0:  # Warm
                r, g, b = processed.split()
                r = r.point(lambda x: min(255, x + temp))
                g = g.point(lambda x: min(255, x + temp // 2))
                processed = Image.merge('RGB', (r, g, b))
            elif temp < 0:  # Cool
                r, g, b = processed.split()
                b = b.point(lambda x: min(255, x - temp))
                g = g.point(lambda x: min(255, x - temp // 2))
                processed = Image.merge('RGB', (r, g, b))

        elif effect_type == EffectType.FADE:
            opacity = params.get('opacity', 0.5)
            white = Image.new('RGB', processed.size, (255, 255, 255))
            processed = Image.blend(processed.convert('RGB'), white, 1 - opacity)

        return processed

    def extract_waveform(self,
                        audio_path: str,
                        width: int = 1920,
                        height: int = 200,
                        samples_per_pixel: int = 100) -> WaveformData:
        """
        Extract audio waveform data for visualization

        Args:
            audio_path: Path to audio/video file
            width: Waveform width in pixels
            height: Waveform height in pixels
            samples_per_pixel: Audio samples per pixel

        Returns:
            WaveformData object
        """
        logger.info(f"Extracting waveform from {audio_path}")

        try:
            # Get audio metadata
            result = subprocess.run([
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 'a:0',
                audio_path
            ], capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                raise RuntimeError("No audio stream found")

            data = json.loads(result.stdout)
            audio_stream = data['streams'][0]

            sample_rate = int(audio_stream.get('sample_rate', 44100))
            channels = int(audio_stream.get('channels', 2))
            duration = float(audio_stream.get('duration', 0))

            # Extract raw audio data
            cmd = [
                'ffmpeg',
                '-hide_banner',
                '-loglevel', 'error',
                '-i', audio_path,
                '-f', 's16le',
                '-acodec', 'pcm_s16le',
                '-ar', str(sample_rate),
                '-ac', '1',  # Mono
                'pipe:1'
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=60)

            if result.returncode != 0:
                raise RuntimeError(f"Failed to extract audio: {result.stderr.decode()}")

            # Convert to numpy array
            audio_data = np.frombuffer(result.stdout, dtype=np.int16)

            # Calculate peaks and RMS for visualization
            total_samples = len(audio_data)
            pixels = min(width, total_samples // samples_per_pixel)

            peaks = np.zeros(pixels, dtype=np.float32)
            rms = np.zeros(pixels, dtype=np.float32)

            for i in range(pixels):
                start = i * samples_per_pixel
                end = min(start + samples_per_pixel, total_samples)
                chunk = audio_data[start:end]

                if len(chunk) > 0:
                    # Normalize to -1.0 to 1.0
                    normalized = chunk.astype(np.float32) / 32768.0
                    peaks[i] = np.max(np.abs(normalized))
                    rms[i] = np.sqrt(np.mean(normalized ** 2))

            logger.info(f"Extracted waveform: {pixels} pixels, {duration:.2f}s")

            return WaveformData(
                audio_path=audio_path,
                duration=duration,
                sample_rate=sample_rate,
                channels=channels,
                peaks=peaks,
                rms=rms,
                samples_per_pixel=samples_per_pixel
            )

        except subprocess.TimeoutExpired:
            raise TimeoutError("Waveform extraction timed out")
        except Exception as e:
            logger.error(f"Failed to extract waveform: {e}")
            raise

    def generate_thumbnail_strip(self,
                                video_path: str,
                                columns: int = 10,
                                rows: int = 10,
                                thumb_width: int = 160,
                                thumb_height: int = 90) -> ThumbnailStrip:
        """
        Generate timeline thumbnail strip (sprite sheet)

        Args:
            video_path: Path to video file
            columns: Number of columns
            rows: Number of rows
            thumb_width: Thumbnail width
            thumb_height: Thumbnail height

        Returns:
            ThumbnailStrip object
        """
        logger.info(f"Generating thumbnail strip: {columns}x{rows}")

        # Get video metadata
        metadata = self._get_video_metadata(video_path)
        duration = metadata['duration']

        # Calculate timestamps
        total_thumbs = columns * rows
        interval = duration / total_thumbs
        timestamps = [i * interval for i in range(total_thumbs)]

        # Create output image
        strip_width = columns * thumb_width
        strip_height = rows * thumb_height
        strip_image = Image.new('RGB', (strip_width, strip_height), (0, 0, 0))

        # Extract and place thumbnails
        for idx, ts in enumerate(timestamps):
            try:
                # Extract frame
                frame = self.extract_frame(video_path, ts, thumb_width, thumb_height)

                # Calculate position
                col = idx % columns
                row = idx // columns
                x = col * thumb_width
                y = row * thumb_height

                # Paste into strip
                strip_image.paste(frame, (x, y))

            except Exception as e:
                logger.warning(f"Failed to extract thumbnail {idx} at {ts}s: {e}")

        # Convert to bytes
        buffer = BytesIO()
        strip_image.save(buffer, format='JPEG', quality=90)
        strip_bytes = buffer.getvalue()

        logger.info(f"Generated thumbnail strip: {strip_width}x{strip_height}")

        return ThumbnailStrip(
            video_path=video_path,
            total_frames=total_thumbs,
            width=strip_width,
            height=strip_height,
            columns=columns,
            rows=rows,
            image_data=strip_bytes,
            timestamps=timestamps
        )

    def stream_preview(self,
                      video_path: str,
                      start: float,
                      end: float,
                      fps: int = 10,
                      width: int = 640,
                      height: int = 360) -> Generator[bytes, None, None]:
        """
        Stream preview frames for WebSocket transmission

        Args:
            video_path: Path to video file
            start: Start timestamp
            end: End timestamp
            fps: Preview frame rate
            width: Frame width
            height: Frame height

        Yields:
            JPEG frame data as bytes
        """
        logger.info(f"Streaming preview from {start}s to {end}s at {fps} fps")

        duration = end - start
        interval = 1.0 / fps
        num_frames = int(duration * fps)

        # Build FFmpeg command for streaming
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error']

        # GPU acceleration
        if self.gpu_caps.has_nvidia:
            cmd.extend(['-hwaccel', 'cuda'])
        elif self.gpu_caps.has_vaapi:
            cmd.extend(['-hwaccel', 'vaapi'])

        # Input with seek
        cmd.extend([
            '-ss', str(start),
            '-t', str(duration),
            '-i', video_path
        ])

        # Output settings
        cmd.extend([
            '-vf', f'fps={fps},scale={width}:{height}',
            '-f', 'image2pipe',
            '-vcodec', 'mjpeg',
            '-q:v', '5',
            'pipe:1'
        ])

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10**8
            )

            frame_count = 0
            buffer = b''

            # JPEG markers
            SOI = b'\xff\xd8'  # Start of Image
            EOI = b'\xff\xd9'  # End of Image

            while frame_count < num_frames:
                chunk = process.stdout.read(4096)
                if not chunk:
                    break

                buffer += chunk

                # Look for complete JPEG frames
                while SOI in buffer:
                    start_idx = buffer.index(SOI)
                    buffer = buffer[start_idx:]

                    if EOI in buffer:
                        end_idx = buffer.index(EOI) + 2
                        frame_data = buffer[:end_idx]
                        buffer = buffer[end_idx:]

                        frame_count += 1
                        yield frame_data
                    else:
                        break

            process.wait(timeout=5)

            logger.info(f"Streamed {frame_count} frames")

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            if process:
                process.kill()
            raise

    def composite_preview(self,
                         tracks: List[Dict[str, Any]],
                         timestamp: float,
                         width: int = 1920,
                         height: int = 1080,
                         blend_mode: str = 'normal') -> CompositePreview:
        """
        Generate composite preview from multiple tracks

        Args:
            tracks: List of track dictionaries with 'path', 'opacity', 'blend_mode'
            timestamp: Timestamp to preview
            width: Output width
            height: Output height
            blend_mode: Default blend mode

        Returns:
            CompositePreview object
        """
        logger.info(f"Generating composite preview with {len(tracks)} tracks at {timestamp}s")

        if not tracks:
            raise ValueError("No tracks provided")

        # Create base canvas
        composite = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        track_paths = []
        blend_modes = []

        for track_info in tracks:
            try:
                video_path = track_info['path']
                opacity = track_info.get('opacity', 1.0)
                track_blend = track_info.get('blend_mode', blend_mode)

                track_paths.append(video_path)
                blend_modes.append(track_blend)

                # Extract frame
                frame = self.extract_frame(video_path, timestamp, width, height)

                # Convert to RGBA
                if frame.mode != 'RGBA':
                    frame = frame.convert('RGBA')

                # Apply opacity
                if opacity < 1.0:
                    alpha = frame.split()[3]
                    alpha = alpha.point(lambda x: int(x * opacity))
                    frame.putalpha(alpha)

                # Composite based on blend mode
                if track_blend == 'normal':
                    composite = Image.alpha_composite(composite, frame)
                elif track_blend == 'multiply':
                    # Simplified multiply blend
                    composite = Image.blend(composite, frame, 0.5)
                elif track_blend == 'screen':
                    # Simplified screen blend
                    composite = Image.blend(composite, frame, 0.7)
                else:
                    # Default to normal
                    composite = Image.alpha_composite(composite, frame)

            except Exception as e:
                logger.warning(f"Failed to composite track {track_info.get('path')}: {e}")

        # Convert to RGB and bytes
        composite_rgb = composite.convert('RGB')
        buffer = BytesIO()
        composite_rgb.save(buffer, format='JPEG', quality=95)
        composite_bytes = buffer.getvalue()

        return CompositePreview(
            tracks=track_paths,
            timestamp=timestamp,
            width=width,
            height=height,
            image_data=composite_bytes,
            blend_modes=blend_modes
        )

    def effect_preview_comparison(self,
                                  video_path: str,
                                  timestamp: float,
                                  effect_type: EffectType,
                                  parameters: Dict[str, Any],
                                  width: int = 1920,
                                  height: int = 1080) -> EffectPreview:
        """
        Generate before/after effect preview comparison

        Args:
            video_path: Path to video file
            timestamp: Timestamp to preview
            effect_type: Effect to apply
            parameters: Effect parameters
            width: Output width
            height: Output height

        Returns:
            EffectPreview object with before/after
        """
        start_time = time.time()

        logger.info(f"Generating effect preview: {effect_type.value}")

        # Extract original frame
        original = self.extract_frame(video_path, timestamp, width, height)

        # Apply effect
        processed = self.preview_effect(original, effect_type, parameters)

        # Convert to bytes
        original_buffer = BytesIO()
        original.save(original_buffer, format='JPEG', quality=95)
        original_bytes = original_buffer.getvalue()

        processed_buffer = BytesIO()
        processed.save(processed_buffer, format='JPEG', quality=95)
        processed_bytes = processed_buffer.getvalue()

        elapsed = time.time() - start_time

        return EffectPreview(
            original=original_bytes,
            processed=processed_bytes,
            effect_type=effect_type.value,
            parameters=parameters,
            processing_time=elapsed
        )

    def export_preview_frame(self,
                            video_path: str,
                            timestamp: float,
                            effects: List[Dict[str, Any]],
                            width: int = 1920,
                            height: int = 1080) -> bytes:
        """
        Generate final export preview with all effects applied

        Args:
            video_path: Path to video file
            timestamp: Timestamp to preview
            effects: List of effects to apply in order
            width: Output width
            height: Output height

        Returns:
            JPEG frame data as bytes
        """
        logger.info(f"Generating export preview with {len(effects)} effects")

        # Extract base frame
        frame = self.extract_frame(video_path, timestamp, width, height)

        # Apply effects in sequence
        for effect_info in effects:
            effect_type = EffectType(effect_info['type'])
            parameters = effect_info.get('parameters', {})
            frame = self.preview_effect(frame, effect_type, parameters)

        # Convert to bytes
        buffer = BytesIO()
        frame.save(buffer, format='JPEG', quality=95)

        return buffer.getvalue()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache.get_stats()

    def clear_cache(self):
        """Clear all caches"""
        self.cache.clear()
        logger.info("Cache cleared")

    def cleanup_proxies(self):
        """Remove all generated proxy videos"""
        count = 0
        for proxy_info in self.proxy_cache.values():
            if os.path.exists(proxy_info.proxy_path):
                try:
                    os.remove(proxy_info.proxy_path)
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove proxy {proxy_info.proxy_path}: {e}")

        self.proxy_cache.clear()
        logger.info(f"Cleaned up {count} proxy videos")


# Example usage and testing
if __name__ == "__main__":
    import sys

    # Initialize generator
    generator = PreviewGenerator(cache_size_mb=500, enable_gpu=True)

    print("=== Preview Generator Test ===\n")

    if len(sys.argv) < 2:
        print("Usage: python preview_generator.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]

    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    try:
        # 1. Extract single frame
        print("1. Extracting frame at 5.0s...")
        frame = generator.extract_frame(video_path, 5.0, width=640, height=360)
        print(f"   Frame size: {frame.size}")

        # 2. Generate thumbnails
        print("\n2. Generating thumbnails...")
        thumbnails = generator.generate_thumbnails(video_path, interval=2.0, max_thumbnails=10)
        print(f"   Generated {len(thumbnails)} thumbnails")

        # 3. Generate proxy
        print("\n3. Generating proxy video...")
        proxy_path = generator.generate_proxy(video_path, ProxyQuality.MEDIUM)
        print(f"   Proxy: {proxy_path}")

        # 4. Preview effect
        print("\n4. Applying blur effect...")
        blurred = generator.preview_effect(frame, EffectType.BLUR, {'radius': 10})
        print(f"   Blurred frame size: {blurred.size}")

        # 5. Extract waveform
        print("\n5. Extracting waveform...")
        waveform = generator.extract_waveform(video_path, width=800, height=100)
        print(f"   Waveform: {len(waveform.peaks)} pixels, {waveform.duration:.2f}s")

        # 6. Generate thumbnail strip
        print("\n6. Generating thumbnail strip...")
        strip = generator.generate_thumbnail_strip(video_path, columns=5, rows=5)
        print(f"   Strip: {strip.width}x{strip.height}, {strip.total_frames} frames")

        # 7. Cache stats
        print("\n7. Cache statistics:")
        stats = generator.get_cache_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")

        print("\n=== All tests completed successfully ===")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
