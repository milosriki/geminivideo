"""
PRODUCTION-READY Celery Distributed Task Queue for Video Processing

This module provides a complete Celery application with:
- Redis broker and result backend
- Multiple priority queues (render, preview, transcode, caption)
- GPU worker detection and routing
- Progress reporting via Redis pub/sub
- Resource monitoring (CPU, GPU, memory)
- Task retry with exponential backoff
- Beat scheduler for periodic cleanup
- Rate limiting and concurrency control
- Production-grade error handling and logging

Usage:
    # Start worker with all queues
    celery -A services.video-agent.pro.celery_app worker --loglevel=info

    # Start worker for specific queue with concurrency
    celery -A services.video-agent.pro.celery_app worker -Q render_queue --concurrency=4

    # Start GPU worker
    celery -A services.video-agent.pro.celery_app worker -Q render_queue --hostname=gpu@%h

    # Start beat scheduler
    celery -A services.video-agent.pro.celery_app beat --loglevel=info

    # Monitor with flower
    celery -A services.video-agent.pro.celery_app flower
"""

import os
import sys
import time
import json
import logging
import subprocess
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from functools import wraps

import redis
import psutil
from celery import Celery, Task, group, chain, chord
from celery.schedules import crontab
from celery.signals import task_prerun, task_postrun, task_failure, worker_ready
from kombu import Queue, Exchange

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

# Temporary directories
TEMP_DIR = os.getenv('TEMP_DIR', '/tmp/video-processing')
RENDER_DIR = os.getenv('RENDER_DIR', '/tmp/renders')
PREVIEW_DIR = os.getenv('PREVIEW_DIR', '/tmp/previews')

# Create directories
for directory in [TEMP_DIR, RENDER_DIR, PREVIEW_DIR]:
    Path(directory).mkdir(parents=True, exist_ok=True)

# Task timeouts (seconds)
RENDER_TIMEOUT = int(os.getenv('RENDER_TIMEOUT', 3600))  # 1 hour
PREVIEW_TIMEOUT = int(os.getenv('PREVIEW_TIMEOUT', 300))  # 5 minutes
TRANSCODE_TIMEOUT = int(os.getenv('TRANSCODE_TIMEOUT', 1800))  # 30 minutes
CAPTION_TIMEOUT = int(os.getenv('CAPTION_TIMEOUT', 900))  # 15 minutes

# Cleanup settings
CLEANUP_AGE_DAYS = int(os.getenv('CLEANUP_AGE_DAYS', 7))
MAX_TEMP_SIZE_GB = int(os.getenv('MAX_TEMP_SIZE_GB', 50))

# ============================================================================
# CELERY APP CONFIGURATION
# ============================================================================

app = Celery('video_processing')

# Define exchanges
default_exchange = Exchange('default', type='direct')
priority_exchange = Exchange('priority', type='topic')

# Configure Celery
app.conf.update(
    # Broker settings
    broker_url=BROKER_URL,
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,

    # Result backend
    result_backend=RESULT_BACKEND,
    result_extended=True,
    result_expires=86400,  # 24 hours

    # Task serialization
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,

    # Task execution
    task_track_started=True,
    task_time_limit=RENDER_TIMEOUT,
    task_soft_time_limit=RENDER_TIMEOUT - 60,
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    worker_disable_rate_limits=False,

    # Queue definitions with priorities
    task_queues=(
        Queue('render_queue', exchange=priority_exchange, routing_key='render.#',
              priority=10, queue_arguments={'x-max-priority': 10}),
        Queue('preview_queue', exchange=default_exchange, routing_key='preview',
              priority=5, queue_arguments={'x-max-priority': 10}),
        Queue('transcode_queue', exchange=default_exchange, routing_key='transcode',
              priority=7, queue_arguments={'x-max-priority': 10}),
        Queue('caption_queue', exchange=default_exchange, routing_key='caption',
              priority=6, queue_arguments={'x-max-priority': 10}),
    ),

    # Default queue
    task_default_queue='render_queue',
    task_default_exchange='priority',
    task_default_routing_key='render.normal',

    # Task routing
    task_routes={
        'services.video-agent.pro.celery_app.render_video_task': {
            'queue': 'render_queue',
            'routing_key': 'render.high',
            'priority': 9
        },
        'services.video-agent.pro.celery_app.generate_preview_task': {
            'queue': 'preview_queue',
            'routing_key': 'preview'
        },
        'services.video-agent.pro.celery_app.transcode_task': {
            'queue': 'transcode_queue',
            'routing_key': 'transcode'
        },
        'services.video-agent.pro.celery_app.caption_task': {
            'queue': 'caption_queue',
            'routing_key': 'caption'
        },
        'services.video-agent.pro.celery_app.batch_render_task': {
            'queue': 'render_queue',
            'routing_key': 'render.batch'
        },
        'services.video-agent.pro.celery_app.cleanup_task': {
            'queue': 'render_queue',
            'routing_key': 'render.low',
            'priority': 1
        },
    },

    # Beat schedule
    beat_schedule={
        'cleanup-old-renders': {
            'task': 'services.video-agent.pro.celery_app.cleanup_task',
            'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
        },
        'monitor-resources': {
            'task': 'services.video-agent.pro.celery_app.monitor_resources_task',
            'schedule': 60.0,  # Every minute
        },
    },

    # Rate limiting (tasks per second per worker)
    task_annotations={
        'services.video-agent.pro.celery_app.render_video_task': {
            'rate_limit': '10/m'  # 10 renders per minute
        },
        'services.video-agent.pro.celery_app.transcode_task': {
            'rate_limit': '20/m'
        },
        'services.video-agent.pro.celery_app.caption_task': {
            'rate_limit': '5/m'  # Whisper is resource-intensive
        },
    },
)

# ============================================================================
# REDIS CLIENT FOR PROGRESS REPORTING
# ============================================================================

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def publish_progress(task_id: str, progress: float, status: str, message: str = ""):
    """Publish task progress to Redis pub/sub channel"""
    try:
        data = {
            'task_id': task_id,
            'progress': progress,
            'status': status,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        redis_client.publish(f'task_progress:{task_id}', json.dumps(data))
        redis_client.setex(f'task_status:{task_id}', 86400, json.dumps(data))
    except Exception as e:
        logger.error(f"Failed to publish progress: {e}")

# ============================================================================
# GPU DETECTION AND RESOURCE MONITORING
# ============================================================================

def detect_gpu() -> Dict[str, Any]:
    """Detect available GPUs using nvidia-smi"""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,name,memory.total,memory.free,utilization.gpu',
             '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            gpus = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 5:
                        gpus.append({
                            'index': int(parts[0]),
                            'name': parts[1],
                            'memory_total': int(parts[2]),
                            'memory_free': int(parts[3]),
                            'utilization': int(parts[4])
                        })
            return {'available': True, 'gpus': gpus, 'count': len(gpus)}
        else:
            return {'available': False, 'gpus': [], 'count': 0}
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"GPU detection failed: {e}")
        return {'available': False, 'gpus': [], 'count': 0}

def get_system_resources() -> Dict[str, Any]:
    """Get current system resource usage"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    gpu_info = detect_gpu()

    return {
        'cpu': {
            'percent': cpu_percent,
            'count': psutil.cpu_count(),
            'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        },
        'memory': {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent,
            'used': memory.used
        },
        'disk': {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        },
        'gpu': gpu_info,
        'timestamp': datetime.utcnow().isoformat()
    }

def select_gpu() -> Optional[int]:
    """Select the GPU with most free memory"""
    gpu_info = detect_gpu()
    if not gpu_info['available'] or not gpu_info['gpus']:
        return None

    # Select GPU with most free memory
    best_gpu = max(gpu_info['gpus'], key=lambda g: g['memory_free'])
    return best_gpu['index']

# ============================================================================
# CUSTOM TASK CLASS
# ============================================================================

class VideoProcessingTask(Task):
    """Base task class with progress reporting and error handling"""

    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(f"Task {task_id} failed: {exc}")
        publish_progress(task_id, 0, 'failed', str(exc))
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry"""
        logger.warning(f"Task {task_id} retrying: {exc}")
        publish_progress(task_id, 0, 'retrying', str(exc))
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        logger.info(f"Task {task_id} completed successfully")
        publish_progress(task_id, 100, 'completed', 'Task completed successfully')
        super().on_success(retval, task_id, args, kwargs)

# ============================================================================
# VIDEO PROCESSING TASKS
# ============================================================================

@app.task(base=VideoProcessingTask, bind=True, name='services.video-agent.pro.celery_app.render_video_task',
          time_limit=RENDER_TIMEOUT, soft_time_limit=RENDER_TIMEOUT - 60)
def render_video_task(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main video rendering task with GPU support

    Args:
        job_data: Dictionary containing:
            - scenes: List of scene data
            - output_format: Target format specifications
            - transitions: Whether to enable transitions
            - overlays: Optional overlay paths
            - subtitles: Optional subtitle paths
            - use_gpu: Whether to use GPU acceleration

    Returns:
        Dictionary with render results including output_path
    """
    task_id = self.request.id
    logger.info(f"Starting render task {task_id}")
    publish_progress(task_id, 0, 'started', 'Initializing render')

    try:
        scenes = job_data.get('scenes', [])
        output_format = job_data.get('output_format', {'width': 1920, 'height': 1080, 'fps': 30})
        enable_transitions = job_data.get('transitions', True)
        use_gpu = job_data.get('use_gpu', False)

        if not scenes:
            raise ValueError("No scenes provided for rendering")

        # Select GPU if requested and available
        gpu_id = None
        if use_gpu:
            gpu_id = select_gpu()
            if gpu_id is not None:
                logger.info(f"Using GPU {gpu_id} for rendering")
                os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_id)

        # Create temporary concat file
        concat_file = os.path.join(TEMP_DIR, f'concat_{task_id}.txt')
        output_path = os.path.join(RENDER_DIR, f'render_{task_id}.mp4')

        publish_progress(task_id, 10, 'processing', 'Preparing scene list')

        # Write concat file
        with open(concat_file, 'w') as f:
            for scene in scenes:
                video_path = scene.get('video_path') or scene.get('path')
                if video_path and os.path.exists(video_path):
                    f.write(f"file '{video_path}'\n")
                    if 'start_time' in scene:
                        f.write(f"inpoint {scene['start_time']}\n")
                    if 'end_time' in scene:
                        f.write(f"outpoint {scene['end_time']}\n")

        publish_progress(task_id, 20, 'processing', 'Building FFmpeg command')

        # Build FFmpeg command
        width = output_format.get('width', 1920)
        height = output_format.get('height', 1080)
        fps = output_format.get('fps', 30)

        # Base command
        cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file]

        # Video filters
        vf_filters = [
            f"scale={width}:{height}:force_original_aspect_ratio=decrease",
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            f"fps={fps}"
        ]

        # Add subtitles if provided
        subtitle_path = job_data.get('subtitles')
        if subtitle_path and os.path.exists(subtitle_path):
            escaped_path = subtitle_path.replace('\\', '\\\\').replace(':', '\\:')
            vf_filters.append(f"subtitles='{escaped_path}'")

        cmd.extend(['-vf', ','.join(vf_filters)])

        # Audio filter - loudness normalization
        cmd.extend(['-af', 'loudnorm=I=-16:LRA=11:TP=-1.5'])

        # Video codec
        if gpu_id is not None:
            # Use NVIDIA hardware encoding
            cmd.extend(['-c:v', 'h264_nvenc', '-preset', 'p4', '-rc', 'vbr', '-cq', '23'])
        else:
            # Use software encoding
            cmd.extend(['-c:v', 'libx264', '-preset', 'medium', '-crf', '23'])

        # Audio codec
        cmd.extend(['-c:a', 'aac', '-b:a', '128k'])

        # Output options
        cmd.extend(['-movflags', '+faststart', '-y', output_path])

        publish_progress(task_id, 30, 'processing', 'Starting FFmpeg render')

        # Execute FFmpeg with progress tracking
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Monitor progress
        duration_total = 0
        for line in process.stderr:
            # Parse FFmpeg progress
            if 'Duration:' in line and duration_total == 0:
                try:
                    time_str = line.split('Duration:')[1].split(',')[0].strip()
                    h, m, s = time_str.split(':')
                    duration_total = float(h) * 3600 + float(m) * 60 + float(s)
                except:
                    pass

            if 'time=' in line and duration_total > 0:
                try:
                    time_str = line.split('time=')[1].split()[0]
                    h, m, s = time_str.split(':')
                    time_current = float(h) * 3600 + float(m) * 60 + float(s)
                    progress = min(30 + (time_current / duration_total * 60), 90)
                    publish_progress(task_id, progress, 'processing', f'Rendering: {int(progress)}%')
                except:
                    pass

        process.wait()

        if process.returncode != 0:
            error_output = process.stderr.read() if hasattr(process.stderr, 'read') else ''
            raise RuntimeError(f"FFmpeg render failed: {error_output}")

        # Cleanup
        if os.path.exists(concat_file):
            os.remove(concat_file)

        publish_progress(task_id, 95, 'processing', 'Finalizing render')

        # Get output file info
        file_size = os.path.getsize(output_path)

        # Get video duration
        probe_cmd = [
            'ffprobe', '-v', 'error', '-show_entries',
            'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
            output_path
        ]
        duration_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        duration = float(duration_result.stdout.strip()) if duration_result.returncode == 0 else 0

        result = {
            'output_path': output_path,
            'file_size': file_size,
            'duration': duration,
            'format': output_format,
            'used_gpu': gpu_id is not None,
            'gpu_id': gpu_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        publish_progress(task_id, 100, 'completed', 'Render completed successfully')
        logger.info(f"Render task {task_id} completed: {output_path}")

        return result

    except Exception as e:
        logger.error(f"Render task {task_id} failed: {e}", exc_info=True)
        publish_progress(task_id, 0, 'failed', str(e))
        raise


@app.task(base=VideoProcessingTask, bind=True, name='services.video-agent.pro.celery_app.generate_preview_task',
          time_limit=PREVIEW_TIMEOUT, soft_time_limit=PREVIEW_TIMEOUT - 30)
def generate_preview_task(self, video_path: str, num_frames: int = 10) -> Dict[str, Any]:
    """
    Generate preview thumbnail frames from video

    Args:
        video_path: Path to source video
        num_frames: Number of preview frames to extract

    Returns:
        Dictionary with preview frame paths
    """
    task_id = self.request.id
    logger.info(f"Starting preview generation task {task_id}")
    publish_progress(task_id, 0, 'started', 'Initializing preview generation')

    try:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Get video duration
        probe_cmd = [
            'ffprobe', '-v', 'error', '-show_entries',
            'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        duration_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
        duration = float(duration_result.stdout.strip()) if duration_result.returncode == 0 else 0

        if duration <= 0:
            raise ValueError("Could not determine video duration")

        publish_progress(task_id, 20, 'processing', f'Extracting {num_frames} preview frames')

        # Create preview directory for this task
        preview_dir = os.path.join(PREVIEW_DIR, task_id)
        os.makedirs(preview_dir, exist_ok=True)

        # Calculate frame timestamps
        interval = duration / (num_frames + 1)
        preview_paths = []

        for i in range(num_frames):
            timestamp = interval * (i + 1)
            output_path = os.path.join(preview_dir, f'frame_{i:03d}.jpg')

            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', video_path,
                '-vframes', '1',
                '-vf', 'scale=320:180',
                '-y',
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=30)

            if result.returncode == 0 and os.path.exists(output_path):
                preview_paths.append(output_path)
                progress = 20 + ((i + 1) / num_frames * 70)
                publish_progress(task_id, progress, 'processing',
                               f'Generated frame {i + 1}/{num_frames}')
            else:
                logger.warning(f"Failed to generate frame at {timestamp}s")

        result = {
            'preview_dir': preview_dir,
            'preview_paths': preview_paths,
            'num_frames': len(preview_paths),
            'video_duration': duration,
            'timestamp': datetime.utcnow().isoformat()
        }

        publish_progress(task_id, 100, 'completed', f'Generated {len(preview_paths)} preview frames')
        logger.info(f"Preview task {task_id} completed: {len(preview_paths)} frames")

        return result

    except Exception as e:
        logger.error(f"Preview task {task_id} failed: {e}", exc_info=True)
        publish_progress(task_id, 0, 'failed', str(e))
        raise


@app.task(base=VideoProcessingTask, bind=True, name='services.video-agent.pro.celery_app.transcode_task',
          time_limit=TRANSCODE_TIMEOUT, soft_time_limit=TRANSCODE_TIMEOUT - 60)
def transcode_task(self, input_path: str, output_format: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transcode video to different format

    Args:
        input_path: Source video path
        output_format: Target format specification:
            - codec: Video codec (h264, h265, vp9, av1)
            - container: Container format (mp4, webm, mkv)
            - width: Target width
            - height: Target height
            - bitrate: Target bitrate (e.g., "5M")

    Returns:
        Dictionary with transcoded video path
    """
    task_id = self.request.id
    logger.info(f"Starting transcode task {task_id}")
    publish_progress(task_id, 0, 'started', 'Initializing transcode')

    try:
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        codec = output_format.get('codec', 'h264')
        container = output_format.get('container', 'mp4')
        width = output_format.get('width')
        height = output_format.get('height')
        bitrate = output_format.get('bitrate')

        output_path = os.path.join(RENDER_DIR, f'transcode_{task_id}.{container}')

        publish_progress(task_id, 10, 'processing', 'Building transcode command')

        # Build FFmpeg command
        cmd = ['ffmpeg', '-i', input_path]

        # Video codec mapping
        codec_map = {
            'h264': 'libx264',
            'h265': 'libx265',
            'vp9': 'libvpx-vp9',
            'av1': 'libaom-av1'
        }

        video_codec = codec_map.get(codec, 'libx264')
        cmd.extend(['-c:v', video_codec])

        # Scaling
        if width and height:
            cmd.extend(['-vf', f'scale={width}:{height}'])

        # Bitrate
        if bitrate:
            cmd.extend(['-b:v', bitrate])
        else:
            cmd.extend(['-crf', '23'])

        # Audio
        cmd.extend(['-c:a', 'aac', '-b:a', '128k'])

        # Container-specific options
        if container == 'mp4':
            cmd.extend(['-movflags', '+faststart'])

        cmd.extend(['-y', output_path])

        publish_progress(task_id, 20, 'processing', 'Starting transcode')

        # Execute with progress monitoring
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        duration_total = 0
        for line in process.stderr:
            if 'Duration:' in line and duration_total == 0:
                try:
                    time_str = line.split('Duration:')[1].split(',')[0].strip()
                    h, m, s = time_str.split(':')
                    duration_total = float(h) * 3600 + float(m) * 60 + float(s)
                except:
                    pass

            if 'time=' in line and duration_total > 0:
                try:
                    time_str = line.split('time=')[1].split()[0]
                    h, m, s = time_str.split(':')
                    time_current = float(h) * 3600 + float(m) * 60 + float(s)
                    progress = min(20 + (time_current / duration_total * 70), 90)
                    publish_progress(task_id, progress, 'processing', f'Transcoding: {int(progress)}%')
                except:
                    pass

        process.wait()

        if process.returncode != 0:
            raise RuntimeError("FFmpeg transcode failed")

        file_size = os.path.getsize(output_path)

        result = {
            'output_path': output_path,
            'input_path': input_path,
            'file_size': file_size,
            'format': output_format,
            'timestamp': datetime.utcnow().isoformat()
        }

        publish_progress(task_id, 100, 'completed', 'Transcode completed successfully')
        logger.info(f"Transcode task {task_id} completed: {output_path}")

        return result

    except Exception as e:
        logger.error(f"Transcode task {task_id} failed: {e}", exc_info=True)
        publish_progress(task_id, 0, 'failed', str(e))
        raise


@app.task(base=VideoProcessingTask, bind=True, name='services.video-agent.pro.celery_app.caption_task',
          time_limit=CAPTION_TIMEOUT, soft_time_limit=CAPTION_TIMEOUT - 30)
def caption_task(self, video_path: str, model: str = 'base') -> Dict[str, Any]:
    """
    Generate captions using Whisper speech recognition

    Args:
        video_path: Path to video file
        model: Whisper model size (tiny, base, small, medium, large)

    Returns:
        Dictionary with SRT subtitle path
    """
    task_id = self.request.id
    logger.info(f"Starting caption task {task_id}")
    publish_progress(task_id, 0, 'started', 'Initializing caption generation')

    try:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Extract audio
        audio_path = os.path.join(TEMP_DIR, f'audio_{task_id}.wav')

        publish_progress(task_id, 10, 'processing', 'Extracting audio')

        extract_cmd = [
            'ffmpeg', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', '16000', '-ac', '1',
            '-y', audio_path
        ]

        result = subprocess.run(extract_cmd, capture_output=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError("Audio extraction failed")

        publish_progress(task_id, 30, 'processing', f'Running Whisper {model} model')

        # Run Whisper transcription
        # Note: This assumes whisper is installed (pip install openai-whisper)
        try:
            import whisper

            whisper_model = whisper.load_model(model)
            transcription_result = whisper_model.transcribe(
                audio_path,
                task='transcribe',
                verbose=False
            )

            publish_progress(task_id, 80, 'processing', 'Generating SRT file')

            # Generate SRT file
            srt_path = os.path.join(RENDER_DIR, f'captions_{task_id}.srt')

            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(transcription_result['segments'], start=1):
                    start = segment['start']
                    end = segment['end']
                    text = segment['text'].strip()

                    # Format timestamps
                    start_time = format_timestamp(start)
                    end_time = format_timestamp(end)

                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{text}\n\n")

            # Cleanup audio
            if os.path.exists(audio_path):
                os.remove(audio_path)

            result = {
                'srt_path': srt_path,
                'video_path': video_path,
                'language': transcription_result.get('language', 'unknown'),
                'num_segments': len(transcription_result['segments']),
                'model': model,
                'timestamp': datetime.utcnow().isoformat()
            }

            publish_progress(task_id, 100, 'completed', 'Caption generation completed')
            logger.info(f"Caption task {task_id} completed: {srt_path}")

            return result

        except ImportError:
            # Fallback: Use whisper CLI if available
            logger.warning("Whisper Python module not available, trying CLI")

            srt_path = os.path.join(RENDER_DIR, f'captions_{task_id}.srt')

            whisper_cmd = [
                'whisper', audio_path,
                '--model', model,
                '--output_format', 'srt',
                '--output_dir', RENDER_DIR,
                '--task', 'transcribe'
            ]

            result = subprocess.run(whisper_cmd, capture_output=True, timeout=600)

            if result.returncode != 0:
                raise RuntimeError("Whisper transcription failed")

            # Move to expected location
            generated_srt = audio_path.replace('.wav', '.srt')
            if os.path.exists(generated_srt):
                shutil.move(generated_srt, srt_path)

            # Cleanup
            if os.path.exists(audio_path):
                os.remove(audio_path)

            result = {
                'srt_path': srt_path,
                'video_path': video_path,
                'model': model,
                'timestamp': datetime.utcnow().isoformat()
            }

            publish_progress(task_id, 100, 'completed', 'Caption generation completed')
            return result

    except Exception as e:
        logger.error(f"Caption task {task_id} failed: {e}", exc_info=True)
        publish_progress(task_id, 0, 'failed', str(e))

        # Cleanup on error
        audio_path = os.path.join(TEMP_DIR, f'audio_{task_id}.wav')
        if os.path.exists(audio_path):
            os.remove(audio_path)

        raise


@app.task(base=VideoProcessingTask, bind=True, name='services.video-agent.pro.celery_app.batch_render_task')
def batch_render_task(self, job_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process multiple render jobs in parallel using Celery groups

    Args:
        job_list: List of job data dictionaries

    Returns:
        List of render results
    """
    task_id = self.request.id
    logger.info(f"Starting batch render task {task_id} with {len(job_list)} jobs")
    publish_progress(task_id, 0, 'started', f'Starting batch of {len(job_list)} renders')

    try:
        # Create a group of render tasks
        job = group(
            render_video_task.s(job_data) for job_data in job_list
        )

        publish_progress(task_id, 10, 'processing', 'Dispatching render jobs')

        # Execute group
        result = job.apply_async()

        # Wait for all tasks to complete
        results = result.get(timeout=RENDER_TIMEOUT * len(job_list))

        publish_progress(task_id, 100, 'completed', f'Batch render completed: {len(results)} videos')
        logger.info(f"Batch render task {task_id} completed: {len(results)} renders")

        return results

    except Exception as e:
        logger.error(f"Batch render task {task_id} failed: {e}", exc_info=True)
        publish_progress(task_id, 0, 'failed', str(e))
        raise


@app.task(base=VideoProcessingTask, bind=True, name='services.video-agent.pro.celery_app.cleanup_task')
def cleanup_task(self, max_age_days: int = None, max_size_gb: int = None) -> Dict[str, Any]:
    """
    Clean up old temporary files and renders

    Args:
        max_age_days: Delete files older than this many days
        max_size_gb: Delete oldest files if total size exceeds this

    Returns:
        Dictionary with cleanup statistics
    """
    task_id = self.request.id
    logger.info(f"Starting cleanup task {task_id}")
    publish_progress(task_id, 0, 'started', 'Starting cleanup')

    max_age = max_age_days or CLEANUP_AGE_DAYS
    max_size = max_size_gb or MAX_TEMP_SIZE_GB

    try:
        deleted_files = 0
        freed_space = 0
        cutoff_time = time.time() - (max_age * 86400)

        # Directories to clean
        cleanup_dirs = [TEMP_DIR, RENDER_DIR, PREVIEW_DIR]

        for directory in cleanup_dirs:
            if not os.path.exists(directory):
                continue

            publish_progress(task_id, 30, 'processing', f'Scanning {directory}')

            # Get all files with their stats
            files = []
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    try:
                        stat = os.stat(filepath)
                        files.append({
                            'path': filepath,
                            'mtime': stat.st_mtime,
                            'size': stat.st_size
                        })
                    except (OSError, FileNotFoundError):
                        pass

            # Delete old files
            for file_info in files:
                if file_info['mtime'] < cutoff_time:
                    try:
                        os.remove(file_info['path'])
                        deleted_files += 1
                        freed_space += file_info['size']
                        logger.debug(f"Deleted old file: {file_info['path']}")
                    except (OSError, FileNotFoundError):
                        pass

            publish_progress(task_id, 60, 'processing', f'Checking size limits for {directory}')

            # Check total size and delete oldest if needed
            remaining_files = [f for f in files if os.path.exists(f['path'])]
            total_size = sum(f['size'] for f in remaining_files)
            total_size_gb = total_size / (1024 ** 3)

            if total_size_gb > max_size:
                # Sort by modification time (oldest first)
                remaining_files.sort(key=lambda f: f['mtime'])

                target_size = max_size * 0.8 * (1024 ** 3)  # Target 80% of max

                for file_info in remaining_files:
                    if total_size <= target_size:
                        break

                    try:
                        os.remove(file_info['path'])
                        deleted_files += 1
                        freed_space += file_info['size']
                        total_size -= file_info['size']
                        logger.debug(f"Deleted for size limit: {file_info['path']}")
                    except (OSError, FileNotFoundError):
                        pass

        # Clean empty directories
        publish_progress(task_id, 90, 'processing', 'Removing empty directories')

        for directory in cleanup_dirs:
            for root, dirs, files in os.walk(directory, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                    except (OSError, FileNotFoundError):
                        pass

        result = {
            'deleted_files': deleted_files,
            'freed_space_bytes': freed_space,
            'freed_space_gb': freed_space / (1024 ** 3),
            'max_age_days': max_age,
            'max_size_gb': max_size,
            'timestamp': datetime.utcnow().isoformat()
        }

        publish_progress(task_id, 100, 'completed',
                        f'Cleanup completed: {deleted_files} files, {result["freed_space_gb"]:.2f} GB freed')
        logger.info(f"Cleanup task {task_id} completed: {deleted_files} files deleted")

        return result

    except Exception as e:
        logger.error(f"Cleanup task {task_id} failed: {e}", exc_info=True)
        publish_progress(task_id, 0, 'failed', str(e))
        raise


@app.task(name='services.video-agent.pro.celery_app.monitor_resources_task')
def monitor_resources_task() -> Dict[str, Any]:
    """
    Monitor system resources and publish to Redis
    Runs periodically via Celery Beat

    Returns:
        Current resource usage statistics
    """
    try:
        resources = get_system_resources()

        # Store in Redis with 5-minute expiry
        redis_client.setex(
            'system_resources',
            300,
            json.dumps(resources)
        )

        # Publish to pub/sub
        redis_client.publish('resource_monitor', json.dumps(resources))

        # Log warnings for high resource usage
        if resources['cpu']['percent'] > 90:
            logger.warning(f"High CPU usage: {resources['cpu']['percent']}%")

        if resources['memory']['percent'] > 90:
            logger.warning(f"High memory usage: {resources['memory']['percent']}%")

        if resources['disk']['percent'] > 90:
            logger.warning(f"High disk usage: {resources['disk']['percent']}%")

        return resources

    except Exception as e:
        logger.error(f"Resource monitoring failed: {e}", exc_info=True)
        return {}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

# ============================================================================
# CELERY SIGNALS
# ============================================================================

@worker_ready.connect
def on_worker_ready(sender=None, **kwargs):
    """Log when worker is ready"""
    logger.info(f"Worker {sender} is ready")
    resources = get_system_resources()
    logger.info(f"System resources: CPU {resources['cpu']['percent']}%, "
                f"Memory {resources['memory']['percent']}%, "
                f"GPU available: {resources['gpu']['available']}")

@task_prerun.connect
def on_task_prerun(task_id=None, task=None, **kwargs):
    """Log task start"""
    logger.info(f"Task {task.name} [{task_id}] starting")

@task_postrun.connect
def on_task_postrun(task_id=None, task=None, **kwargs):
    """Log task completion"""
    logger.info(f"Task {task.name} [{task_id}] completed")

@task_failure.connect
def on_task_failure(task_id=None, exception=None, **kwargs):
    """Log task failure"""
    logger.error(f"Task [{task_id}] failed: {exception}")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    app.start()
