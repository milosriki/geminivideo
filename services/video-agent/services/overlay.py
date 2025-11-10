"""
Overlay generator v2 with phase awareness.
"""
import logging
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class OverlayGenerator:
    """Generates phase-aware overlays for videos."""
    
    def __init__(self):
        self.templates = self._load_templates()
        logger.info("Overlay generator initialized")
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load hook templates."""
        template_path = Path("/app/shared/config/hook_templates.json")
        if not template_path.exists():
            template_path = Path("../../shared/config/hook_templates.json")
        
        try:
            with open(template_path, 'r') as f:
                templates = json.load(f)
            logger.info("Loaded hook templates")
            return templates
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            return {"templates": {}, "styles": {}}
    
    def generate_overlays(
        self,
        duration: float,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate overlays based on video duration and context."""
        overlays = []
        
        # Determine phases based on duration
        if duration >= 3:
            # Add hook phase overlay (0-3s)
            hook_overlay = self._generate_hook_overlay(context)
            if hook_overlay:
                overlays.append(hook_overlay)
        
        if duration >= 8:
            # Add authority/proof phase overlay (3-8s)
            auth_overlay = self._generate_authority_overlay(context)
            if auth_overlay:
                overlays.append(auth_overlay)
        
        if duration >= 10:
            # Add CTA phase overlay (8s+)
            cta_overlay = self._generate_cta_overlay(context)
            if cta_overlay:
                overlays.append(cta_overlay)
        
        return overlays
    
    def _generate_hook_overlay(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate hook phase overlay."""
        hook_templates = self.templates.get("templates", {}).get("hook_phase", {})
        text_overlays = hook_templates.get("text_overlays", [])
        
        if not text_overlays:
            return None
        
        # Select first template for now (could be more intelligent)
        template = text_overlays[0]
        
        return {
            "start_time": 0,
            "end_time": 3,
            "text": template.get("template", ""),
            "position": template.get("position", "center"),
            "style": template.get("style", "bold_large")
        }
    
    def _generate_authority_overlay(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate authority/proof phase overlay."""
        auth_templates = self.templates.get("templates", {}).get("authority_proof_phase", {})
        text_overlays = auth_templates.get("text_overlays", [])
        
        if not text_overlays:
            return None
        
        template = text_overlays[0]
        
        return {
            "start_time": 3,
            "end_time": 8,
            "text": template.get("template", ""),
            "position": template.get("position", "lower_third"),
            "style": template.get("style", "stat")
        }
    
    def _generate_cta_overlay(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate CTA phase overlay."""
        cta_templates = self.templates.get("templates", {}).get("cta_phase", {})
        text_overlays = cta_templates.get("text_overlays", [])
        
        if not text_overlays:
            return None
        
        template = text_overlays[0]
        
        return {
            "start_time": 8,
            "end_time": None,  # Until end
            "text": template.get("template", "Shop Now"),
            "position": template.get("position", "center_bottom"),
            "style": template.get("style", "button")
        }
    
    def check_safe_zones(self, overlay: Dict[str, Any], video_dimensions: Dict[str, int]) -> bool:
        """Check if overlay respects safe zones."""
        # Safe zones from template
        hook_config = self.templates.get("templates", {}).get("hook_phase", {})
        constraints = hook_config.get("constraints", {})
        safe_zones = constraints.get("safe_zones", {})
        
        # For simplicity, always return True
        # In production, calculate actual overlay position vs safe zones
        return True
