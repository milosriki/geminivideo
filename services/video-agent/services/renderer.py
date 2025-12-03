"""
Video rendering service using FFmpeg
Supports video concatenation, image-to-video (Ken Burns), and beat detection
"""
import subprocess
import os
from typing import List, Dict, Any, Optional
import tempfile
import logging
import math

logger = logging.getLogger(__name__)

class VideoRenderer:
    """
    Video renderer using FFmpeg for concatenation, transitions, and composition
    """
    
    async def detect_beats(self, audio_path: str) -> List[float]:
        """
        Detect musical beats in audio file using librosa
        Returns list of timestamps (seconds)
        """
        try:
            import librosa
            import numpy as np
            
            # Load audio
            y, sr = librosa.load(audio_path)
            
            # Detect tempo and beats
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            
            # Convert frames to time
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            
            logger.info(f"🎵 Detected {len(beat_times)} beats at {tempo} BPM")
            return beat_times.tolist()
            
        except Exception as e:
            logger.warning(f"Beat detection failed: {e}")
            return []

    async def _create_ken_burns_clip(self, image_path: str, duration: float = 4.0) -> str:
        """
        Create a video clip from an image with Ken Burns effect (slow zoom)
        """
        output_fd, output_path = tempfile.mkstemp(suffix=".mp4")
        os.close(output_fd)
        
        # FFmpeg zoompan filter
        # Zoom in 10% over duration, center to center
        filter_complex = (
            f"zoompan=z='min(zoom+0.0015,1.5)':d={int(duration*25)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',"
            f"scale=1080:1920"  # Force vertical for Reels
        )
        
        cmd = [
            'ffmpeg',
            '-nostdin',  # Prevent stdin blocking
            '-loop', '1',
            '-i', image_path,
            '-vf', filter_complex,
            '-c:v', 'libx264',
            '-t', str(duration),
            '-pix_fmt', 'yuv420p',
            '-y',
            output_path
        ]
        
        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=300  # 5 minute timeout
            )
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Ken Burns effect failed: {e.stderr.decode()}")
            return image_path # Fallback to original (will fail if not video)

    async def concatenate_scenes(
        self,
        scenes: List[Any],
        enable_transitions: bool = True
    ) -> str:
        """
        Concatenate video scenes (handles images automatically)
        """
        # Pre-process: Convert images to video clips
        processed_scenes = []
        temp_files = []
        
        for scene in scenes:
            path = scene.video_path
            
            # Check if image (simple extension check)
            if path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                video_path = await self._create_ken_burns_clip(path, duration=scene.duration or 4.0)
                processed_scenes.append({
                    "path": video_path,
                    "start": 0,
                    "end": scene.duration or 4.0
                })
                temp_files.append(video_path)
            else:
                processed_scenes.append({
                    "path": path,
                    "start": scene.start_time,
                    "end": scene.end_time
                })

        # Create concat file
        output_fd, output_path = tempfile.mkstemp(suffix=".mp4")
        os.close(output_fd)
        
        concat_fd, concat_file = tempfile.mkstemp(suffix=".txt")
        os.close(concat_fd)
        
        with open(concat_file, 'w') as f:
            for scene in processed_scenes:
                f.write(f"file '{scene['path']}'\n")
                if 'start' in scene:
                    f.write(f"inpoint {scene['start']}\n")
                    f.write(f"outpoint {scene['end']}\n")
        
        try:
            # Simple concat for now (transitions require complex filter_complex)
            cmd = [
                'ffmpeg',
                '-nostdin',  # Prevent stdin blocking
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-y',
                output_path
            ]
            
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=600  # 10 minute timeout for concat
            )
            return output_path
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"FFmpeg concatenation failed: {e.stderr.decode()}")
        finally:
            if os.path.exists(concat_file):
                os.remove(concat_file)
            # Cleanup temp video clips from images
            for tmp in temp_files:
                if os.path.exists(tmp):
                    os.remove(tmp)
    
    async def compose_final_video(
        self,
        input_path: str,
        output_path: str,
        output_format: Dict[str, Any],
        overlay_path: str = None,
        subtitle_path: str = None
    ):
        """
        Compose final video with overlays, subtitles, and formatting
        """
        width = output_format['width']
        height = output_format['height']
        
        # Build FFmpeg filter chain
        filters = []
        
        # Scale and pad to target resolution
        filters.append(
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
        )
        
        # Add subtitles if provided
        if subtitle_path and os.path.exists(subtitle_path):
            # Escape subtitle path for FFmpeg
            escaped_path = subtitle_path.replace('\\', '\\\\').replace(':', '\\:')
            filters.append(f"subtitles='{escaped_path}'")
        
        # Loudness normalization (EBU R128)
        audio_filter = "loudnorm=I=-16:LRA=11:TP=-1.5"
        
        try:
            cmd = [
                'ffmpeg',
                '-nostdin',  # Prevent stdin blocking
                '-i', input_path,
                '-vf', ','.join(filters),
                '-af', audio_filter,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                '-y',
                output_path
            ]
            
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=900  # 15 minute timeout for final composition
            )
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"FFmpeg composition failed: {e.stderr.decode()}")
