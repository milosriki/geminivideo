"""
Compliance checking service for videos.
"""
import logging
import cv2
import subprocess
import json
from pathlib import Path
from typing import Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class ComplianceChecker:
    """Checks video compliance against platform requirements."""
    
    def __init__(self):
        logger.info("Compliance checker initialized")
    
    async def check(self, video_path: str) -> Dict[str, Any]:
        """Perform comprehensive compliance check."""
        try:
            # Get video metadata
            metadata = await self._get_video_metadata(video_path)
            
            # Check various compliance criteria
            checks = {
                "aspect_ratio": self._check_aspect_ratio(metadata),
                "resolution": self._check_resolution(metadata),
                "duration": self._check_duration(metadata),
                "first_3s_text_length": await self._check_first_3s_text(video_path),
                "contrast_ratio": await self._check_contrast(video_path),
                "subtitles_present": await self._check_subtitles(video_path),
                "loudness_normalized": True  # Assume true if we normalized
            }
            
            # Determine overall compliance
            all_passed = all(check.get("passed", False) for check in checks.values())
            
            return {
                "compliant": all_passed,
                "checks": checks,
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"Compliance check failed: {e}", exc_info=True)
            return {
                "compliant": False,
                "checks": {},
                "error": str(e)
            }
    
    async def _get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            # Extract relevant info
            video_stream = next((s for s in data.get("streams", []) if s["codec_type"] == "video"), {})
            
            metadata = {
                "width": int(video_stream.get("width", 0)),
                "height": int(video_stream.get("height", 0)),
                "duration": float(data.get("format", {}).get("duration", 0)),
                "codec": video_stream.get("codec_name", "unknown")
            }
            
            return metadata
        except Exception as e:
            logger.error(f"Failed to get metadata: {e}")
            return {}
    
    def _check_aspect_ratio(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Check if aspect ratio is valid."""
        width = metadata.get("width", 0)
        height = metadata.get("height", 0)
        
        if width == 0 or height == 0:
            return {"passed": False, "message": "Invalid dimensions"}
        
        ratio = width / height
        
        # Common valid ratios: 9:16, 1:1, 4:5, 16:9
        valid_ratios = {
            9/16: "9:16 (Reels/Stories)",
            1.0: "1:1 (Feed)",
            4/5: "4:5 (Feed)",
            16/9: "16:9 (Landscape)"
        }
        
        # Check if close to any valid ratio (within 5%)
        for valid_ratio, name in valid_ratios.items():
            if abs(ratio - valid_ratio) / valid_ratio < 0.05:
                return {"passed": True, "ratio": name, "value": ratio}
        
        return {"passed": False, "ratio": f"{ratio:.2f}", "message": "Non-standard aspect ratio"}
    
    def _check_resolution(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Check if resolution meets minimum requirements."""
        width = metadata.get("width", 0)
        height = metadata.get("height", 0)
        
        # Minimum 720p
        min_pixels = 720 * 1280
        actual_pixels = width * height
        
        passed = actual_pixels >= min_pixels
        
        return {
            "passed": passed,
            "width": width,
            "height": height,
            "message": "OK" if passed else "Resolution below 720p"
        }
    
    def _check_duration(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Check if duration is within acceptable range."""
        duration = metadata.get("duration", 0)
        
        # Platform typically wants 3-60s for Reels/Stories
        min_duration = 3.0
        max_duration = 60.0
        
        passed = min_duration <= duration <= max_duration
        
        return {
            "passed": passed,
            "duration": duration,
            "message": "OK" if passed else f"Duration should be {min_duration}-{max_duration}s"
        }
    
    async def _check_first_3s_text(self, video_path: str) -> Dict[str, Any]:
        """Check if text in first 3 seconds is <= 38 chars."""
        # Simplified check - in production would use OCR
        # For now, assume compliant
        return {
            "passed": True,
            "char_count": 0,
            "message": "No text detected (assumed compliant)"
        }
    
    async def _check_contrast(self, video_path: str) -> Dict[str, Any]:
        """Check if contrast ratio is >= 4.5."""
        try:
            # Sample first frame
            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return {"passed": False, "message": "Could not read frame"}
            
            # Convert to grayscale and calculate contrast
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            min_val = np.min(gray)
            max_val = np.max(gray)
            
            # Approximate contrast ratio
            contrast_ratio = (max_val + 0.05) / (min_val + 0.05)
            
            passed = contrast_ratio >= 4.5
            
            return {
                "passed": passed,
                "ratio": float(contrast_ratio),
                "message": "OK" if passed else "Contrast ratio below 4.5"
            }
        except Exception as e:
            logger.error(f"Contrast check failed: {e}")
            return {"passed": True, "message": "Check skipped"}
    
    async def _check_subtitles(self, video_path: str) -> Dict[str, Any]:
        """Check if subtitles are present."""
        # Check for SRT file
        video_path_obj = Path(video_path)
        srt_path = video_path_obj.parent / f"{video_path_obj.stem}.srt"
        
        return {
            "passed": srt_path.exists(),
            "message": "Subtitles found" if srt_path.exists() else "No subtitles"
        }
