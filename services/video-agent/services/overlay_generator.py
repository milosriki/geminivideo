"""
Overlay generation for Hook -> Proof -> CTA phases
"""
import json
import tempfile
from typing import Dict, Any, List, Optional


class OverlayGenerator:
    """
    Generate text overlays based on driver signals and hook templates
    """
    
    def __init__(self, templates: Dict[str, Any]):
        self.templates = templates.get('templates', [])
        self.styles = templates.get('overlay_styles', {})
    
    def generate_overlays(
        self,
        scenes: List[Any],
        driver_signals: Dict[str, Any],
        template_id: Optional[str] = None,
        duration: float = 0
    ) -> str:
        """
        Generate overlay instructions for video
        
        Args:
            scenes: List of scenes
            driver_signals: Driver signals from analysis
            template_id: Optional specific template ID
            duration: Total video duration
            
        Returns:
            Path to overlay file (simplified for MVP - returns None, overlays applied via drawtext)
        """
        # For MVP, we'll return None and handle overlays in subtitle generation
        # A full implementation would create an overlay video or complex filter
        
        # Extract key overlay text from driver signals
        overlays = []
        
        # Hook phase (first 3 seconds)
        if 'hook_text' in driver_signals:
            overlays.append({
                'text': driver_signals['hook_text'],
                'start': 0,
                'duration': 3,
                'phase': 'hook'
            })
        
        # Proof phase (middle section)
        if 'proof_text' in driver_signals:
            mid_point = duration / 2
            overlays.append({
                'text': driver_signals['proof_text'],
                'start': mid_point,
                'duration': 4,
                'phase': 'proof'
            })
        
        # CTA phase (last 3 seconds)
        if 'cta_text' in driver_signals:
            overlays.append({
                'text': driver_signals['cta_text'],
                'start': max(0, duration - 3),
                'duration': 3,
                'phase': 'cta'
            })
        
        # Store overlay data (in real implementation, would render to video)
        overlay_fd, overlay_file = tempfile.mkstemp(suffix=".json")
        os.close(overlay_fd)
        with open(overlay_file, 'w') as f:
            json.dump(overlays, f)
        
        return overlay_file
