"""
Subtitle generation and burn-in pipeline.
"""
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import pysubs2

logger = logging.getLogger(__name__)

class SubtitlePipeline:
    """Handles subtitle generation and burn-in."""
    
    def __init__(self):
        logger.info("Subtitle pipeline initialized")
    
    async def generate_subtitles(
        self,
        video_path: str,
        transcript: Optional[str] = None
    ) -> Optional[str]:
        """Generate SRT file from transcript."""
        if not transcript:
            logger.warning("No transcript provided, skipping subtitles")
            return None
        
        try:
            # Create subtitle file
            subs = pysubs2.SSAFile()
            
            # Parse transcript into subtitle events
            # For simplicity, create one subtitle per sentence
            sentences = transcript.split('. ')
            duration_per_sentence = 3000  # 3 seconds per sentence
            
            for i, sentence in enumerate(sentences):
                if sentence.strip():
                    event = pysubs2.SSAEvent(
                        start=i * duration_per_sentence,
                        end=(i + 1) * duration_per_sentence,
                        text=sentence.strip()
                    )
                    subs.append(event)
            
            # Save SRT file
            video_path_obj = Path(video_path)
            srt_path = video_path_obj.parent / f"{video_path_obj.stem}.srt"
            subs.save(str(srt_path))
            
            logger.info(f"Generated subtitles: {srt_path}")
            return str(srt_path)
        except Exception as e:
            logger.error(f"Subtitle generation failed: {e}")
            return None
    
    async def burn_in_subtitles(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str
    ) -> str:
        """Burn subtitles into video using FFmpeg."""
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vf", f"subtitles={subtitle_path}",
                "-c:a", "copy",
                output_path
            ]
            
            logger.debug(f"Burning subtitles: {' '.join(cmd)}")
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Burned subtitles into: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Subtitle burn-in failed: {e.stderr}")
            raise
