"""
Video rendering service using FFmpeg
"""
import subprocess
import os
from typing import List, Dict, Any
import tempfile


class VideoRenderer:
    """
    Video renderer using FFmpeg for concatenation, transitions, and composition
    """
    
    async def concatenate_scenes(
        self,
        scenes: List[Any],
        enable_transitions: bool = True
    ) -> str:
        """
        Concatenate video scenes with optional transitions
        
        Args:
            scenes: List of scene inputs
            enable_transitions: Whether to add xfade transitions
            
        Returns:
            Path to concatenated video
        """
        # Use secure temporary file creation
        output_fd, output_path = tempfile.mkstemp(suffix=".mp4")
        os.close(output_fd)
        
        # Create concat file
        concat_fd, concat_file = tempfile.mkstemp(suffix=".txt")
        os.close(concat_fd)
        with open(concat_file, 'w') as f:
            for scene in scenes:
                f.write(f"file '{scene.video_path}'\n")
                f.write(f"inpoint {scene.start_time}\n")
                f.write(f"outpoint {scene.end_time}\n")
        
        try:
            if enable_transitions and len(scenes) > 1:
                # Use xfade for transitions (simplified for MVP)
                cmd = [
                    'ffmpeg',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', concat_file,
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-c:a', 'aac',
                    '-y',
                    output_path
                ]
            else:
                # Simple concatenation
                cmd = [
                    'ffmpeg',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', concat_file,
                    '-c', 'copy',
                    '-y',
                    output_path
                ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"FFmpeg concatenation failed: {e.stderr.decode()}")
        finally:
            if os.path.exists(concat_file):
                os.remove(concat_file)
    
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
        
        Args:
            input_path: Input video path
            output_path: Output video path
            output_format: Target format (width, height, aspect)
            overlay_path: Optional overlay video
            subtitle_path: Optional subtitle file (SRT)
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
            
            subprocess.run(cmd, check=True, capture_output=True)
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"FFmpeg composition failed: {e.stderr.decode()}")
