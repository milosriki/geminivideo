"""
Pro Renderer - Advanced FFmpeg Rendering Pipeline with GPU Acceleration
Production-ready video rendering with hardware acceleration, multi-pass encoding,
chunked processing, and platform-specific optimizations.
"""

import subprocess
import json
import os
import re
import tempfile
import shutil
import logging
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QualityPreset(Enum):
    """Video quality presets"""
    DRAFT = "draft"
    STANDARD = "standard"
    HIGH = "high"
    MASTER = "master"


class Platform(Enum):
    """Target platforms with specific requirements"""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    GENERIC = "generic"


class OutputFormat(Enum):
    """Supported output formats"""
    MP4_H264 = "mp4_h264"
    MP4_H265 = "mp4_h265"
    WEBM_VP9 = "webm_vp9"
    PRORES = "prores"
    GIF = "gif"


class AspectRatio(Enum):
    """Common aspect ratios"""
    VERTICAL = "9:16"      # TikTok, Instagram Reels
    HORIZONTAL = "16:9"    # YouTube, landscape
    SQUARE = "1:1"         # Instagram feed
    PORTRAIT = "4:5"       # Instagram portrait


@dataclass
class GPUCapabilities:
    """GPU acceleration capabilities"""
    has_nvidia: bool = False
    has_nvenc: bool = False
    has_cuvid: bool = False
    has_vaapi: bool = False
    has_qsv: bool = False
    decoder: Optional[str] = None
    encoder: Optional[str] = None


@dataclass
class VideoMetadata:
    """Video file metadata"""
    duration: float
    width: int
    height: int
    fps: float
    bitrate: int
    codec: str
    has_audio: bool
    audio_codec: Optional[str] = None
    audio_channels: int = 0
    is_hdr: bool = False
    color_space: Optional[str] = None


@dataclass
class RenderSettings:
    """Rendering configuration"""
    width: int
    height: int
    fps: float
    video_bitrate: str
    audio_bitrate: str
    crf: int
    preset: str
    pix_fmt: str
    color_space: Optional[str] = None
    use_gpu: bool = True
    two_pass: bool = False


class ProgressTracker:
    """Track FFmpeg rendering progress"""

    def __init__(self, total_duration: float, callback: Optional[Callable[[float], None]] = None):
        self.total_duration = total_duration
        self.callback = callback
        self.current_time = 0.0

    def parse_progress(self, line: str) -> None:
        """Parse FFmpeg progress output"""
        # FFmpeg outputs progress like: time=00:01:23.45
        time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', line)
        if time_match:
            hours, minutes, seconds = time_match.groups()
            self.current_time = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            progress = min(100.0, (self.current_time / self.total_duration) * 100)

            if self.callback:
                self.callback(progress)


class ProRenderer:
    """
    Production-ready advanced FFmpeg rendering pipeline with GPU acceleration,
    multi-pass encoding, chunked processing, and platform optimizations.
    """

    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the Pro Renderer

        Args:
            temp_dir: Custom temporary directory for intermediate files
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.gpu_capabilities = self.detect_gpu_acceleration()
        logger.info(f"GPU Capabilities: {self.gpu_capabilities}")

    def detect_gpu_acceleration(self) -> GPUCapabilities:
        """
        Detect available GPU acceleration capabilities

        Returns:
            GPUCapabilities object with detected hardware
        """
        caps = GPUCapabilities()

        try:
            # Query FFmpeg for available encoders and decoders
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                timeout=5
            )
            encoders = result.stdout

            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-decoders'],
                capture_output=True,
                text=True,
                timeout=5
            )
            decoders = result.stdout

            # Check for NVIDIA NVENC
            if 'h264_nvenc' in encoders:
                caps.has_nvidia = True
                caps.has_nvenc = True
                caps.encoder = 'h264_nvenc'
                logger.info("✓ NVIDIA NVENC encoder detected")

            # Check for NVIDIA CUVID
            if 'h264_cuvid' in decoders:
                caps.has_cuvid = True
                caps.decoder = 'h264_cuvid'
                logger.info("✓ NVIDIA CUVID decoder detected")

            # Check for VAAPI (Intel/AMD)
            if 'h264_vaapi' in encoders:
                caps.has_vaapi = True
                if not caps.encoder:
                    caps.encoder = 'h264_vaapi'
                logger.info("✓ VAAPI encoder detected")

            # Check for Intel Quick Sync
            if 'h264_qsv' in encoders:
                caps.has_qsv = True
                if not caps.encoder:
                    caps.encoder = 'h264_qsv'
                logger.info("✓ Intel Quick Sync detected")

            # Verify GPU is actually available by testing
            if caps.encoder:
                test_result = self._test_gpu_encoder(caps.encoder)
                if not test_result:
                    logger.warning(f"GPU encoder {caps.encoder} exists but test failed, falling back to CPU")
                    caps.encoder = None
                    caps.has_nvenc = False
                    caps.has_vaapi = False
                    caps.has_qsv = False

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg query timed out")
        except FileNotFoundError:
            logger.error("FFmpeg not found in PATH")
        except Exception as e:
            logger.error(f"Error detecting GPU: {e}")

        return caps

    def _test_gpu_encoder(self, encoder: str) -> bool:
        """
        Test if GPU encoder actually works

        Args:
            encoder: Encoder name to test

        Returns:
            True if encoder works, False otherwise
        """
        try:
            test_file = os.path.join(self.temp_dir, 'gpu_test.mp4')

            # Create a simple test video
            cmd = [
                'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=640x480:rate=30',
                '-t', '1', '-c:v', encoder, '-y', test_file
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10
            )

            if os.path.exists(test_file):
                os.remove(test_file)

            return result.returncode == 0

        except Exception as e:
            logger.debug(f"GPU test failed: {e}")
            return False

    def get_video_metadata(self, video_path: str) -> VideoMetadata:
        """
        Extract video metadata using ffprobe

        Args:
            video_path: Path to video file

        Returns:
            VideoMetadata object
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise RuntimeError(f"ffprobe failed: {result.stderr}")

            data = json.loads(result.stdout)

            # Find video stream
            video_stream = next(
                (s for s in data['streams'] if s['codec_type'] == 'video'),
                None
            )

            if not video_stream:
                raise ValueError("No video stream found")

            # Find audio stream
            audio_stream = next(
                (s for s in data['streams'] if s['codec_type'] == 'audio'),
                None
            )

            # Extract metadata
            duration = float(data['format'].get('duration', 0))
            width = int(video_stream['width'])
            height = int(video_stream['height'])

            # Calculate FPS
            fps_str = video_stream.get('r_frame_rate', '30/1')
            num, denom = map(int, fps_str.split('/'))
            fps = num / denom if denom != 0 else 30.0

            bitrate = int(data['format'].get('bit_rate', 0))
            codec = video_stream['codec_name']

            # HDR detection
            color_space = video_stream.get('color_space')
            color_transfer = video_stream.get('color_transfer')
            is_hdr = color_transfer in ['smpte2084', 'arib-std-b67'] if color_transfer else False

            # Audio info
            has_audio = audio_stream is not None
            audio_codec = audio_stream['codec_name'] if audio_stream else None
            audio_channels = int(audio_stream.get('channels', 0)) if audio_stream else 0

            return VideoMetadata(
                duration=duration,
                width=width,
                height=height,
                fps=fps,
                bitrate=bitrate,
                codec=codec,
                has_audio=has_audio,
                audio_codec=audio_codec,
                audio_channels=audio_channels,
                is_hdr=is_hdr,
                color_space=color_space
            )

        except subprocess.TimeoutExpired:
            raise RuntimeError("ffprobe timed out")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse ffprobe output: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to get video metadata: {e}")

    def get_optimal_settings(
        self,
        platform: Platform,
        quality: QualityPreset,
        aspect_ratio: Optional[AspectRatio] = None,
        target_width: Optional[int] = None
    ) -> RenderSettings:
        """
        Get optimal render settings for target platform

        Args:
            platform: Target platform
            quality: Quality preset
            aspect_ratio: Target aspect ratio
            target_width: Target width (height calculated from aspect ratio)

        Returns:
            RenderSettings object
        """
        # Platform-specific settings
        platform_settings = {
            Platform.INSTAGRAM: {
                'max_width': 1080,
                'max_bitrate': '5M',
                'audio_bitrate': '128k',
                'fps': 30,
            },
            Platform.TIKTOK: {
                'max_width': 1080,
                'max_bitrate': '6M',
                'audio_bitrate': '128k',
                'fps': 30,
            },
            Platform.YOUTUBE: {
                'max_width': 1920,
                'max_bitrate': '16M',
                'audio_bitrate': '192k',
                'fps': 60,
            },
            Platform.TWITTER: {
                'max_width': 1280,
                'max_bitrate': '5M',
                'audio_bitrate': '128k',
                'fps': 30,
            },
            Platform.FACEBOOK: {
                'max_width': 1280,
                'max_bitrate': '8M',
                'audio_bitrate': '128k',
                'fps': 30,
            },
            Platform.GENERIC: {
                'max_width': 1920,
                'max_bitrate': '10M',
                'audio_bitrate': '192k',
                'fps': 30,
            }
        }

        # Quality preset settings
        quality_settings = {
            QualityPreset.DRAFT: {
                'crf': 28,
                'preset': 'veryfast',
                'two_pass': False,
            },
            QualityPreset.STANDARD: {
                'crf': 23,
                'preset': 'medium',
                'two_pass': False,
            },
            QualityPreset.HIGH: {
                'crf': 20,
                'preset': 'slow',
                'two_pass': True,
            },
            QualityPreset.MASTER: {
                'crf': 18,
                'preset': 'slower',
                'two_pass': True,
            }
        }

        platform_cfg = platform_settings[platform]
        quality_cfg = quality_settings[quality]

        # Calculate dimensions based on aspect ratio
        if aspect_ratio:
            width = target_width or platform_cfg['max_width']

            if aspect_ratio == AspectRatio.VERTICAL:  # 9:16
                width = min(width, 1080)
                height = int(width * 16 / 9)
            elif aspect_ratio == AspectRatio.HORIZONTAL:  # 16:9
                width = min(width, platform_cfg['max_width'])
                height = int(width * 9 / 16)
            elif aspect_ratio == AspectRatio.SQUARE:  # 1:1
                width = min(width, 1080)
                height = width
            elif aspect_ratio == AspectRatio.PORTRAIT:  # 4:5
                width = min(width, 1080)
                height = int(width * 5 / 4)
            else:
                width = platform_cfg['max_width']
                height = int(width * 9 / 16)
        else:
            width = target_width or platform_cfg['max_width']
            height = int(width * 9 / 16)

        # Ensure even dimensions (required by many codecs)
        width = width if width % 2 == 0 else width - 1
        height = height if height % 2 == 0 else height - 1

        return RenderSettings(
            width=width,
            height=height,
            fps=platform_cfg['fps'],
            video_bitrate=platform_cfg['max_bitrate'],
            audio_bitrate=platform_cfg['audio_bitrate'],
            crf=quality_cfg['crf'],
            preset=quality_cfg['preset'],
            pix_fmt='yuv420p',
            two_pass=quality_cfg['two_pass'],
            use_gpu=self.gpu_capabilities.encoder is not None
        )

    def build_filtergraph(
        self,
        operations: List[Dict[str, Any]],
        settings: RenderSettings,
        metadata: VideoMetadata
    ) -> str:
        """
        Build complex FFmpeg filtergraph from operations

        Args:
            operations: List of filter operations
            settings: Render settings
            metadata: Input video metadata

        Returns:
            FFmpeg filtergraph string
        """
        filters = []

        # Scale to target resolution
        if metadata.width != settings.width or metadata.height != settings.height:
            filters.append(f"scale={settings.width}:{settings.height}:flags=lanczos")

        # FPS conversion
        if abs(metadata.fps - settings.fps) > 0.01:
            filters.append(f"fps={settings.fps}")

        # Process each operation
        for op in operations:
            op_type = op.get('type')

            if op_type == 'trim':
                start = op.get('start', 0)
                end = op.get('end')
                if end:
                    filters.append(f"trim=start={start}:end={end},setpts=PTS-STARTPTS")
                else:
                    filters.append(f"trim=start={start},setpts=PTS-STARTPTS")

            elif op_type == 'crop':
                x = op.get('x', 0)
                y = op.get('y', 0)
                w = op.get('width', settings.width)
                h = op.get('height', settings.height)
                filters.append(f"crop={w}:{h}:{x}:{y}")

            elif op_type == 'rotate':
                angle = op.get('angle', 0)
                if angle == 90:
                    filters.append("transpose=1")
                elif angle == 180:
                    filters.append("transpose=1,transpose=1")
                elif angle == 270:
                    filters.append("transpose=2")
                else:
                    filters.append(f"rotate={angle}*PI/180")

            elif op_type == 'blur':
                strength = op.get('strength', 5)
                filters.append(f"gblur=sigma={strength}")

            elif op_type == 'brightness':
                value = op.get('value', 0)
                filters.append(f"eq=brightness={value}")

            elif op_type == 'contrast':
                value = op.get('value', 1.0)
                filters.append(f"eq=contrast={value}")

            elif op_type == 'saturation':
                value = op.get('value', 1.0)
                filters.append(f"eq=saturation={value}")

            elif op_type == 'fade_in':
                duration = op.get('duration', 1.0)
                filters.append(f"fade=t=in:st=0:d={duration}")

            elif op_type == 'fade_out':
                duration = op.get('duration', 1.0)
                start = metadata.duration - duration
                filters.append(f"fade=t=out:st={start}:d={duration}")

            elif op_type == 'speed':
                factor = op.get('factor', 1.0)
                if factor != 1.0:
                    filters.append(f"setpts={1.0/factor}*PTS")

            elif op_type == 'reverse':
                filters.append("reverse")

            elif op_type == 'hflip':
                filters.append("hflip")

            elif op_type == 'vflip':
                filters.append("vflip")

            elif op_type == 'sharpen':
                strength = op.get('strength', 1.0)
                filters.append(f"unsharp=5:5:{strength}:5:5:{strength}")

            elif op_type == 'denoise':
                strength = op.get('strength', 1.0)
                filters.append(f"hqdn3d={strength}")

            elif op_type == 'overlay':
                # Handled separately with complex filters
                pass

            elif op_type == 'text':
                text = op.get('text', '')
                x = op.get('x', 'center')
                y = op.get('y', 'center')
                fontsize = op.get('fontsize', 24)
                fontcolor = op.get('fontcolor', 'white')
                # Escape special characters
                text = text.replace(':', r'\:').replace("'", r"\'")
                filters.append(
                    f"drawtext=text='{text}':fontsize={fontsize}:"
                    f"fontcolor={fontcolor}:x={x}:y={y}"
                )

        # HDR to SDR conversion if needed
        if metadata.is_hdr:
            filters.append("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")

        # Ensure pixel format
        if settings.pix_fmt:
            filters.append(f"format={settings.pix_fmt}")

        return ','.join(filters) if filters else None

    def encode_video(
        self,
        input_path: str,
        output_path: str,
        settings: RenderSettings,
        output_format: OutputFormat = OutputFormat.MP4_H264,
        filtergraph: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
        metadata: Optional[VideoMetadata] = None
    ) -> bool:
        """
        Encode video with specified settings

        Args:
            input_path: Input video path
            output_path: Output video path
            settings: Render settings
            output_format: Output format
            filtergraph: FFmpeg filtergraph
            progress_callback: Progress callback function
            metadata: Input video metadata

        Returns:
            True if successful
        """
        try:
            if not metadata:
                metadata = self.get_video_metadata(input_path)

            # Build FFmpeg command
            cmd = ['ffmpeg', '-y']

            # Hardware decoding
            if settings.use_gpu and self.gpu_capabilities.decoder:
                if self.gpu_capabilities.has_cuvid:
                    cmd.extend(['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda'])
                elif self.gpu_capabilities.has_vaapi:
                    cmd.extend(['-hwaccel', 'vaapi', '-hwaccel_device', '/dev/dri/renderD128'])

            # Input file
            cmd.extend(['-i', input_path])

            # Apply filtergraph
            if filtergraph:
                cmd.extend(['-vf', filtergraph])

            # Output format settings
            if output_format == OutputFormat.MP4_H264:
                self._add_h264_settings(cmd, settings)
            elif output_format == OutputFormat.MP4_H265:
                self._add_h265_settings(cmd, settings)
            elif output_format == OutputFormat.WEBM_VP9:
                self._add_vp9_settings(cmd, settings)
            elif output_format == OutputFormat.PRORES:
                self._add_prores_settings(cmd, settings)
            elif output_format == OutputFormat.GIF:
                self._add_gif_settings(cmd, settings)

            # Audio settings
            if metadata.has_audio and output_format != OutputFormat.GIF:
                cmd.extend([
                    '-c:a', 'aac',
                    '-b:a', settings.audio_bitrate,
                    '-ar', '48000'
                ])
            else:
                cmd.extend(['-an'])

            # Progress reporting
            cmd.extend(['-progress', 'pipe:1', '-stats_period', '0.5'])

            # Output file
            cmd.append(output_path)

            logger.info(f"Encoding command: {' '.join(cmd)}")

            # Execute encoding
            if settings.two_pass and output_format in [OutputFormat.MP4_H264, OutputFormat.MP4_H265]:
                return self._encode_two_pass(cmd, metadata, progress_callback)
            else:
                return self._encode_single_pass(cmd, metadata, progress_callback)

        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            return False

    def _add_h264_settings(self, cmd: List[str], settings: RenderSettings) -> None:
        """Add H.264 encoding settings"""
        if settings.use_gpu and self.gpu_capabilities.has_nvenc:
            cmd.extend([
                '-c:v', 'h264_nvenc',
                '-preset', 'p7',  # NVENC preset
                '-rc', 'vbr',
                '-cq', str(settings.crf),
                '-b:v', settings.video_bitrate,
                '-maxrate', settings.video_bitrate,
                '-bufsize', str(int(settings.video_bitrate.rstrip('Mk')) * 2) + settings.video_bitrate[-1],
            ])
        elif settings.use_gpu and self.gpu_capabilities.has_vaapi:
            cmd.extend([
                '-c:v', 'h264_vaapi',
                '-qp', str(settings.crf),
                '-b:v', settings.video_bitrate,
            ])
        elif settings.use_gpu and self.gpu_capabilities.has_qsv:
            cmd.extend([
                '-c:v', 'h264_qsv',
                '-preset', settings.preset,
                '-global_quality', str(settings.crf),
                '-b:v', settings.video_bitrate,
            ])
        else:
            # CPU encoding
            cmd.extend([
                '-c:v', 'libx264',
                '-preset', settings.preset,
                '-crf', str(settings.crf),
                '-b:v', settings.video_bitrate,
                '-maxrate', settings.video_bitrate,
                '-bufsize', str(int(settings.video_bitrate.rstrip('Mk')) * 2) + settings.video_bitrate[-1],
            ])

        cmd.extend(['-pix_fmt', settings.pix_fmt, '-movflags', '+faststart'])

    def _add_h265_settings(self, cmd: List[str], settings: RenderSettings) -> None:
        """Add H.265 encoding settings"""
        if settings.use_gpu and self.gpu_capabilities.has_nvenc:
            cmd.extend([
                '-c:v', 'hevc_nvenc',
                '-preset', 'p7',
                '-rc', 'vbr',
                '-cq', str(settings.crf),
                '-b:v', settings.video_bitrate,
            ])
        elif settings.use_gpu and self.gpu_capabilities.has_vaapi:
            cmd.extend([
                '-c:v', 'hevc_vaapi',
                '-qp', str(settings.crf),
                '-b:v', settings.video_bitrate,
            ])
        else:
            cmd.extend([
                '-c:v', 'libx265',
                '-preset', settings.preset,
                '-crf', str(settings.crf),
                '-b:v', settings.video_bitrate,
            ])

        cmd.extend(['-pix_fmt', settings.pix_fmt, '-movflags', '+faststart'])

    def _add_vp9_settings(self, cmd: List[str], settings: RenderSettings) -> None:
        """Add VP9 encoding settings"""
        cmd.extend([
            '-c:v', 'libvpx-vp9',
            '-b:v', settings.video_bitrate,
            '-crf', str(settings.crf),
            '-quality', 'good',
            '-speed', '2' if settings.preset == 'fast' else '1',
            '-tile-columns', '2',
            '-tile-rows', '1',
            '-row-mt', '1',
        ])

    def _add_prores_settings(self, cmd: List[str], settings: RenderSettings) -> None:
        """Add ProRes encoding settings"""
        # ProRes profile: 0=Proxy, 1=LT, 2=Standard, 3=HQ
        profile = {
            QualityPreset.DRAFT: '0',
            QualityPreset.STANDARD: '2',
            QualityPreset.HIGH: '3',
            QualityPreset.MASTER: '3',
        }

        cmd.extend([
            '-c:v', 'prores_ks',
            '-profile:v', profile.get(QualityPreset.STANDARD, '2'),
            '-pix_fmt', 'yuv422p10le',
        ])

    def _add_gif_settings(self, cmd: List[str], settings: RenderSettings) -> None:
        """Add GIF encoding settings"""
        # GIF requires palette generation for best quality
        palette_filters = "fps={},scale={}:{}:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse".format(
            min(settings.fps, 15),  # GIFs typically use lower FPS
            settings.width,
            settings.height
        )

        # Replace existing filter
        for i, arg in enumerate(cmd):
            if arg == '-vf':
                cmd[i + 1] = palette_filters
                break
        else:
            cmd.extend(['-vf', palette_filters])

    def _encode_single_pass(
        self,
        cmd: List[str],
        metadata: VideoMetadata,
        progress_callback: Optional[Callable[[float], None]]
    ) -> bool:
        """Execute single-pass encoding"""
        try:
            tracker = ProgressTracker(metadata.duration, progress_callback)

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in process.stdout:
                tracker.parse_progress(line)
                if 'error' in line.lower():
                    logger.error(f"FFmpeg error: {line}")

            process.wait()

            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg failed with code {process.returncode}")

            logger.info("Encoding completed successfully")
            return True

        except Exception as e:
            logger.error(f"Single-pass encoding failed: {e}")
            return False

    def _encode_two_pass(
        self,
        cmd: List[str],
        metadata: VideoMetadata,
        progress_callback: Optional[Callable[[float], None]]
    ) -> bool:
        """Execute two-pass encoding"""
        try:
            # Pass 1
            logger.info("Starting pass 1/2")
            pass1_cmd = cmd.copy()

            # Find output file
            output_file = pass1_cmd[-1]
            pass1_cmd[-1] = os.devnull

            # Add pass 1 settings
            for i, arg in enumerate(pass1_cmd):
                if arg in ['-c:v', '-vcodec']:
                    codec_idx = i
                    break

            pass1_cmd.insert(codec_idx + 2, '-pass')
            pass1_cmd.insert(codec_idx + 3, '1')
            pass1_cmd.insert(codec_idx + 4, '-passlogfile')
            pass1_cmd.insert(codec_idx + 5, os.path.join(self.temp_dir, 'ffmpeg2pass'))

            # Execute pass 1
            tracker = ProgressTracker(metadata.duration,
                                     lambda p: progress_callback(p * 0.5) if progress_callback else None)

            process = subprocess.Popen(
                pass1_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in process.stdout:
                tracker.parse_progress(line)

            process.wait()

            if process.returncode != 0:
                raise RuntimeError(f"Pass 1 failed with code {process.returncode}")

            # Pass 2
            logger.info("Starting pass 2/2")
            pass2_cmd = cmd.copy()

            # Add pass 2 settings
            for i, arg in enumerate(pass2_cmd):
                if arg in ['-c:v', '-vcodec']:
                    codec_idx = i
                    break

            pass2_cmd.insert(codec_idx + 2, '-pass')
            pass2_cmd.insert(codec_idx + 3, '2')
            pass2_cmd.insert(codec_idx + 4, '-passlogfile')
            pass2_cmd.insert(codec_idx + 5, os.path.join(self.temp_dir, 'ffmpeg2pass'))

            # Execute pass 2
            tracker = ProgressTracker(metadata.duration,
                                     lambda p: progress_callback(50 + p * 0.5) if progress_callback else None)

            process = subprocess.Popen(
                pass2_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in process.stdout:
                tracker.parse_progress(line)

            process.wait()

            if process.returncode != 0:
                raise RuntimeError(f"Pass 2 failed with code {process.returncode}")

            # Clean up pass log files
            for ext in ['log', 'log.mbtree']:
                log_file = os.path.join(self.temp_dir, f'ffmpeg2pass-0.{ext}')
                if os.path.exists(log_file):
                    os.remove(log_file)

            logger.info("Two-pass encoding completed successfully")
            return True

        except Exception as e:
            logger.error(f"Two-pass encoding failed: {e}")
            return False

    def chunk_and_render(
        self,
        input_path: str,
        output_path: str,
        settings: RenderSettings,
        output_format: OutputFormat = OutputFormat.MP4_H264,
        chunk_duration: int = 60,
        max_workers: int = 4,
        filtergraph: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> bool:
        """
        Split video into chunks, process in parallel, and concatenate

        Args:
            input_path: Input video path
            output_path: Output video path
            settings: Render settings
            output_format: Output format
            chunk_duration: Duration of each chunk in seconds
            max_workers: Maximum parallel workers
            filtergraph: FFmpeg filtergraph
            progress_callback: Progress callback

        Returns:
            True if successful
        """
        try:
            metadata = self.get_video_metadata(input_path)

            # Calculate number of chunks
            num_chunks = int(metadata.duration / chunk_duration) + 1

            if num_chunks <= 1:
                # Video is short, process directly
                return self.encode_video(
                    input_path, output_path, settings,
                    output_format, filtergraph, progress_callback, metadata
                )

            logger.info(f"Splitting video into {num_chunks} chunks for parallel processing")

            # Create temp directory for chunks
            chunk_dir = os.path.join(self.temp_dir, f'chunks_{int(time.time())}')
            os.makedirs(chunk_dir, exist_ok=True)

            try:
                # Split video into chunks
                chunk_files = self._split_video_chunks(
                    input_path, chunk_dir, chunk_duration, metadata
                )

                # Process chunks in parallel
                processed_chunks = self._process_chunks_parallel(
                    chunk_files, chunk_dir, settings, output_format,
                    filtergraph, max_workers, progress_callback
                )

                if not processed_chunks:
                    raise RuntimeError("No chunks were processed successfully")

                # Concatenate chunks
                success = self.concatenate_chunks(processed_chunks, output_path)

                return success

            finally:
                # Clean up temp directory
                if os.path.exists(chunk_dir):
                    shutil.rmtree(chunk_dir)

        except Exception as e:
            logger.error(f"Chunked rendering failed: {e}")
            return False

    def _split_video_chunks(
        self,
        input_path: str,
        chunk_dir: str,
        chunk_duration: int,
        metadata: VideoMetadata
    ) -> List[str]:
        """Split video into chunks"""
        chunk_files = []

        for i, start_time in enumerate(range(0, int(metadata.duration), chunk_duration)):
            chunk_file = os.path.join(chunk_dir, f'chunk_{i:04d}.mp4')

            cmd = [
                'ffmpeg', '-y',
                '-ss', str(start_time),
                '-i', input_path,
                '-t', str(chunk_duration),
                '-c', 'copy',
                '-avoid_negative_ts', 'make_zero',
                chunk_file
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=300)

            if result.returncode == 0 and os.path.exists(chunk_file):
                chunk_files.append(chunk_file)
                logger.info(f"Created chunk {i + 1}: {chunk_file}")
            else:
                logger.warning(f"Failed to create chunk {i}")

        return chunk_files

    def _process_chunks_parallel(
        self,
        chunk_files: List[str],
        chunk_dir: str,
        settings: RenderSettings,
        output_format: OutputFormat,
        filtergraph: Optional[str],
        max_workers: int,
        progress_callback: Optional[Callable[[float], None]]
    ) -> List[str]:
        """Process chunks in parallel"""
        processed_chunks = []
        total_chunks = len(chunk_files)
        completed = 0

        def process_chunk(chunk_file: str, index: int) -> Optional[str]:
            try:
                output_file = os.path.join(
                    chunk_dir,
                    f'processed_{index:04d}.{self._get_extension(output_format)}'
                )

                success = self.encode_video(
                    chunk_file, output_file, settings,
                    output_format, filtergraph, None, None
                )

                return output_file if success else None

            except Exception as e:
                logger.error(f"Failed to process chunk {index}: {e}")
                return None

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_chunk, chunk_file, i): i
                for i, chunk_file in enumerate(chunk_files)
            }

            for future in as_completed(futures):
                result = future.result()
                if result:
                    processed_chunks.append(result)

                completed += 1
                if progress_callback:
                    progress_callback((completed / total_chunks) * 100)

                logger.info(f"Processed chunk {completed}/{total_chunks}")

        # Sort chunks by filename to maintain order
        processed_chunks.sort()
        return processed_chunks

    def concatenate_chunks(self, chunk_files: List[str], output_path: str) -> bool:
        """
        Concatenate video chunks

        Args:
            chunk_files: List of chunk file paths
            output_path: Output file path

        Returns:
            True if successful
        """
        try:
            if not chunk_files:
                raise ValueError("No chunks to concatenate")

            # Create concat list file
            concat_file = os.path.join(
                os.path.dirname(chunk_files[0]),
                'concat_list.txt'
            )

            with open(concat_file, 'w') as f:
                for chunk_file in chunk_files:
                    # Use relative path or escape spaces
                    f.write(f"file '{os.path.basename(chunk_file)}'\n")

            # Concatenate using FFmpeg concat demuxer
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',
                output_path
            ]

            logger.info("Concatenating chunks...")
            result = subprocess.run(cmd, capture_output=True, timeout=300)

            if result.returncode != 0:
                raise RuntimeError(f"Concatenation failed: {result.stderr.decode()}")

            logger.info(f"Successfully concatenated {len(chunk_files)} chunks")
            return True

        except Exception as e:
            logger.error(f"Concatenation failed: {e}")
            return False

    def _get_extension(self, output_format: OutputFormat) -> str:
        """Get file extension for output format"""
        extensions = {
            OutputFormat.MP4_H264: 'mp4',
            OutputFormat.MP4_H265: 'mp4',
            OutputFormat.WEBM_VP9: 'webm',
            OutputFormat.PRORES: 'mov',
            OutputFormat.GIF: 'gif',
        }
        return extensions.get(output_format, 'mp4')

    def render_video(
        self,
        input_path: str,
        output_path: str,
        platform: Platform = Platform.GENERIC,
        quality: QualityPreset = QualityPreset.STANDARD,
        output_format: OutputFormat = OutputFormat.MP4_H264,
        aspect_ratio: Optional[AspectRatio] = None,
        operations: Optional[List[Dict[str, Any]]] = None,
        use_chunking: bool = False,
        chunk_duration: int = 60,
        max_workers: int = 4,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> bool:
        """
        Main rendering method - high-level API

        Args:
            input_path: Input video path
            output_path: Output video path
            platform: Target platform
            quality: Quality preset
            output_format: Output format
            aspect_ratio: Target aspect ratio
            operations: List of filter operations
            use_chunking: Use chunked rendering for long videos
            chunk_duration: Chunk duration in seconds
            max_workers: Max parallel workers
            progress_callback: Progress callback

        Returns:
            True if successful
        """
        try:
            logger.info(f"Starting render: {input_path} -> {output_path}")
            logger.info(f"Platform: {platform.value}, Quality: {quality.value}, Format: {output_format.value}")

            # Get video metadata
            metadata = self.get_video_metadata(input_path)
            logger.info(f"Input: {metadata.width}x{metadata.height} @ {metadata.fps}fps, {metadata.duration:.2f}s")

            # Get optimal settings
            settings = self.get_optimal_settings(platform, quality, aspect_ratio)
            logger.info(f"Output settings: {settings.width}x{settings.height} @ {settings.fps}fps")

            # Build filtergraph
            filtergraph = None
            if operations:
                filtergraph = self.build_filtergraph(operations, settings, metadata)
                logger.info(f"Filtergraph: {filtergraph}")

            # Choose rendering method
            if use_chunking and metadata.duration > chunk_duration:
                return self.chunk_and_render(
                    input_path, output_path, settings, output_format,
                    chunk_duration, max_workers, filtergraph, progress_callback
                )
            else:
                return self.encode_video(
                    input_path, output_path, settings, output_format,
                    filtergraph, progress_callback, metadata
                )

        except Exception as e:
            logger.error(f"Render failed: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    # Initialize renderer
    renderer = ProRenderer()

    # Example: Simple render
    def progress_handler(progress: float):
        print(f"Progress: {progress:.1f}%")

    # Example operations
    operations = [
        {'type': 'trim', 'start': 0, 'end': 30},
        {'type': 'brightness', 'value': 0.1},
        {'type': 'fade_in', 'duration': 1.0},
        {'type': 'fade_out', 'duration': 1.0},
    ]

    # Render for Instagram
    success = renderer.render_video(
        input_path='/path/to/input.mp4',
        output_path='/path/to/output.mp4',
        platform=Platform.INSTAGRAM,
        quality=QualityPreset.HIGH,
        output_format=OutputFormat.MP4_H264,
        aspect_ratio=AspectRatio.VERTICAL,
        operations=operations,
        progress_callback=progress_handler
    )

    print(f"Render {'succeeded' if success else 'failed'}")
