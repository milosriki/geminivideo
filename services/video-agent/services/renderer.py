"""
Video rendering service with FFmpeg.
"""
import logging
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class RendererService:
    """Service for rendering videos."""
    
    def __init__(self):
        self.output_dir = Path("/app/data/outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_threads = int(os.getenv("FFMPEG_THREADS", "4"))
        logger.info(f"Renderer initialized (threads: {self.ffmpeg_threads})")
    
    async def render(self, request: Dict[str, Any], job_id: str) -> str:
        """Render a video from clips."""
        try:
            clips = request.get("clips", [])
            variant = request.get("variant", "reels")
            use_transitions = request.get("useTransitions", False)
            normalize_audio = request.get("normalizeAudio", True)
            
            # Determine output dimensions
            dimensions = self._get_variant_dimensions(variant)
            
            # Build FFmpeg command
            output_path = self.output_dir / f"{job_id}.mp4"
            
            # For simplicity, we'll concat clips
            # In production, this would be more sophisticated
            if len(clips) == 1:
                # Single clip
                clip = clips[0]
                await self._render_single_clip(clip, output_path, dimensions, normalize_audio)
            else:
                # Multiple clips
                await self._render_multiple_clips(clips, output_path, dimensions, use_transitions, normalize_audio)
            
            logger.info(f"Rendered video: {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"Rendering failed: {e}", exc_info=True)
            raise
    
    def _get_variant_dimensions(self, variant: str) -> Dict[str, int]:
        """Get dimensions for variant."""
        dimensions = {
            "reels": {"width": 1080, "height": 1920},  # 9:16
            "feed": {"width": 1080, "height": 1080},   # 1:1
            "stories": {"width": 1080, "height": 1350} # 4:5
        }
        return dimensions.get(variant, dimensions["reels"])
    
    async def _render_single_clip(
        self,
        clip: Dict[str, Any],
        output_path: Path,
        dimensions: Dict[str, int],
        normalize_audio: bool
    ):
        """Render a single clip."""
        video_path = clip.get("videoPath")
        start = clip.get("start", 0)
        duration = clip.get("duration", 10)
        
        if not video_path:
            raise ValueError("Clip missing videoPath")
        
        # Build FFmpeg command
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", video_path,
            "-t", str(duration),
            "-vf", f"scale={dimensions['width']}:{dimensions['height']}:force_original_aspect_ratio=increase,crop={dimensions['width']}:{dimensions['height']}",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-threads", str(self.ffmpeg_threads)
        ]
        
        # Add audio filters
        if normalize_audio:
            cmd.extend(["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"])
        
        cmd.append(str(output_path))
        
        # Execute
        await self._run_ffmpeg(cmd)
    
    async def _render_multiple_clips(
        self,
        clips: List[Dict[str, Any]],
        output_path: Path,
        dimensions: Dict[str, int],
        use_transitions: bool,
        normalize_audio: bool
    ):
        """Render multiple clips with concat."""
        # Create a concat file
        concat_file = output_path.parent / f"{output_path.stem}_concat.txt"
        
        with open(concat_file, 'w') as f:
            for clip in clips:
                video_path = clip.get("videoPath")
                if video_path:
                    f.write(f"file '{video_path}'\n")
        
        # Build FFmpeg command
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-vf", f"scale={dimensions['width']}:{dimensions['height']}:force_original_aspect_ratio=increase,crop={dimensions['width']}:{dimensions['height']}",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-threads", str(self.ffmpeg_threads)
        ]
        
        # Add audio filters
        if normalize_audio:
            cmd.extend(["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"])
        
        cmd.append(str(output_path))
        
        # Execute
        await self._run_ffmpeg(cmd)
        
        # Clean up concat file
        concat_file.unlink()
    
    async def _run_ffmpeg(self, cmd: List[str]):
        """Run FFmpeg command."""
        try:
            logger.debug(f"Running FFmpeg: {' '.join(cmd)}")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"FFmpeg error: {stderr.decode()}")
                raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")
        except Exception as e:
            logger.error(f"FFmpeg execution failed: {e}")
            raise

import asyncio
