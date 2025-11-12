"""
Compliance checking for rendered videos
"""
import cv2
import os
from typing import Dict, Any, Optional
import numpy as np


class ComplianceChecker:
    """
    Check video compliance against platform requirements
    """
    
    def check_compliance(
        self,
        video_path: str,
        variant: str,
        subtitle_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run compliance checks on rendered video
        
        Args:
            video_path: Path to video file
            variant: Video variant (reels, feed, stories)
            subtitle_path: Path to subtitle file
            
        Returns:
            Compliance report with passes/warnings/failures
        """
        checks = {
            'resolution': self._check_resolution(video_path, variant),
            'duration': self._check_duration(video_path),
            'hook_text_length': self._check_hook_text(subtitle_path),
            'contrast_ratio': self._check_contrast(video_path),
            'subtitles_present': subtitle_path is not None and os.path.exists(subtitle_path)
        }
        
        # Determine overall status
        failed = [k for k, v in checks.items() if isinstance(v, dict) and not v.get('passed', True)]
        warnings = [k for k, v in checks.items() if isinstance(v, dict) and v.get('warning', False)]
        
        return {
            'passed': len(failed) == 0,
            'checks': checks,
            'failed': failed,
            'warnings': warnings,
            'timestamp': None
        }
    
    def _check_resolution(self, video_path: str, variant: str) -> Dict[str, Any]:
        """Check video resolution matches variant requirements"""
        expected_resolutions = {
            'reels': (1080, 1920),
            'feed': (1080, 1080),
            'stories': (1080, 1920)
        }
        
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        expected = expected_resolutions.get(variant, (1080, 1920))
        
        return {
            'passed': (width, height) == expected,
            'actual': (width, height),
            'expected': expected
        }
    
    def _check_duration(self, video_path: str) -> Dict[str, Any]:
        """Check video duration is reasonable"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        
        # Instagram Reels: 3-90 seconds
        min_duration = 3
        max_duration = 90
        
        passed = min_duration <= duration <= max_duration
        warning = duration > 60  # Warn if longer than 60s
        
        return {
            'passed': passed,
            'warning': warning,
            'duration': duration,
            'min': min_duration,
            'max': max_duration
        }
    
    def _check_hook_text(self, subtitle_path: Optional[str]) -> Dict[str, Any]:
        """Check first 3s hook text is <=38 characters"""
        if not subtitle_path or not os.path.exists(subtitle_path):
            return {'passed': True, 'length': 0}
        
        try:
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract first subtitle entry
            lines = content.strip().split('\n')
            if len(lines) >= 3:
                # Third line should be the text
                first_text = lines[2]
                length = len(first_text)
                
                return {
                    'passed': length <= 38,
                    'length': length,
                    'max': 38,
                    'text': first_text[:50]
                }
        except Exception:
            # Exception handled - return default values if SRT parsing fails
            pass
        
        return {'passed': True, 'length': 0}
    
    def _check_contrast(self, video_path: str) -> Dict[str, Any]:
        """Check contrast ratio of sample frame"""
        cap = cv2.VideoCapture(video_path)
        
        # Get middle frame
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 2)
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return {'passed': True, 'ratio': 0}
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate contrast (simple std deviation method)
        std_dev = np.std(gray)
        
        # Normalize to approximate contrast ratio
        # Higher std dev = higher contrast
        # Rough approximation: std_dev > 40 suggests good contrast
        contrast_ratio = std_dev / 10  # Simplified
        
        return {
            'passed': contrast_ratio >= 4.5,
            'ratio': float(contrast_ratio),
            'min': 4.5
        }
