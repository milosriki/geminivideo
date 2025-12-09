import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class HookClassifier:
    """
    Classifies video hooks based on heuristic rules and metadata.
    Future versions will use deep learning models.
    """
    
    def __init__(self):
        self.rules = [
            self._rule_fast_paced,
            self._rule_audio_spike,
            self._rule_text_overlay
        ]

    def classify(self, video_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze video metadata to determine hook quality.
        """
        score = 0.0
        signals = []
        
        # Apply heuristic rules
        for rule in self.rules:
            rule_score, signal = rule(video_metadata)
            if rule_score > 0:
                score += rule_score
                signals.append(signal)
        
        # Normalize score
        final_score = min(score, 1.0)
        
        classification = "WEAK"
        if final_score > 0.7:
            classification = "VIRAL"
        elif final_score > 0.4:
            classification = "STRONG"
            
        return {
            "classification": classification,
            "score": final_score,
            "signals": signals,
            "model_version": "heuristic_v1"
        }

    def _rule_fast_paced(self, meta: Dict[str, Any]) -> tuple[float, str]:
        """Check for fast cuts in the first 3 seconds."""
        cuts = meta.get("scene_cuts", [])
        early_cuts = [c for c in cuts if c < 3.0]
        
        if len(early_cuts) >= 2:
            return 0.4, "Fast pacing (2+ cuts in 3s)"
        return 0.0, ""

    def _rule_audio_spike(self, meta: Dict[str, Any]) -> tuple[float, str]:
        """Check for immediate audio engagement."""
        audio_levels = meta.get("audio_levels", []) # List of db levels per second
        if audio_levels and audio_levels[0] > -10: # Loud start
            return 0.3, "Strong audio start"
        return 0.0, ""

    def _rule_text_overlay(self, meta: Dict[str, Any]) -> tuple[float, str]:
        """Check if text appears immediately."""
        text_events = meta.get("text_events", [])
        if any(t.get("start_time", 99) < 1.0 for t in text_events):
            return 0.3, "Immediate text overlay"
        return 0.0, ""

# Singleton instance
hook_classifier = HookClassifier()
