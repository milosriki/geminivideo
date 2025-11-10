"""
Ranking and clustering service for clips.
"""
import logging
from typing import List, Dict, Any
import yaml
import os
from pathlib import Path
import re
import numpy as np

logger = logging.getLogger(__name__)

class RankingService:
    """Service for ranking and clustering video clips."""
    
    def __init__(self):
        self.config = self._load_config()
        logger.info("Ranking service initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load ranking configuration."""
        config_path = Path("/app/shared/config/scene_ranking.yaml")
        if not config_path.exists():
            # Fallback to default location
            config_path = Path("../../shared/config/scene_ranking.yaml")
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info("Loaded ranking config")
            return config
        except Exception as e:
            logger.error(f"Failed to load ranking config: {e}")
            # Return default config
            return {
                "weights": {
                    "motion_score": 0.25,
                    "object_relevance": 0.20,
                    "ocr_relevance": 0.15,
                    "novelty": 0.20,
                    "duration_optimal": 0.10,
                    "audio_presence": 0.10
                },
                "optimal_duration": {"min": 3.0, "max": 15.0, "target": 8.0}
            }
    
    def rank_clips(self, clips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank clips based on features and configuration."""
        try:
            weights = self.config.get("weights", {})
            
            for clip in clips:
                # Calculate component scores
                motion_score = clip.get("motion_score", 0.0)
                object_score = self._calculate_object_relevance(clip.get("objects", []))
                ocr_score = self._calculate_ocr_relevance(clip.get("ocr_tokens", []))
                duration_score = self._calculate_duration_score(clip.get("duration", 0.0))
                audio_score = 1.0 if clip.get("transcript_excerpt") else 0.0
                novelty_score = 0.5  # Placeholder, will be calculated with FAISS later
                
                # Calculate weighted rank score
                rank_score = (
                    motion_score * weights.get("motion_score", 0.25) +
                    object_score * weights.get("object_relevance", 0.20) +
                    ocr_score * weights.get("ocr_relevance", 0.15) +
                    novelty_score * weights.get("novelty", 0.20) +
                    duration_score * weights.get("duration_optimal", 0.10) +
                    audio_score * weights.get("audio_presence", 0.10)
                )
                
                clip["rankScore"] = float(rank_score)
            
            # Sort by rank score
            clips.sort(key=lambda c: c["rankScore"], reverse=True)
            
            logger.info(f"Ranked {len(clips)} clips")
            return clips
        except Exception as e:
            logger.error(f"Ranking failed: {e}", exc_info=True)
            return clips
    
    def _calculate_object_relevance(self, objects: List[str]) -> float:
        """Calculate object relevance score."""
        if not objects:
            return 0.0
        
        relevant_objects = self.config.get("relevant_objects", {})
        high_priority = set(relevant_objects.get("high_priority", []))
        medium_priority = set(relevant_objects.get("medium_priority", []))
        
        score = 0.0
        for obj in objects:
            if obj.lower() in high_priority:
                score += 1.0
            elif obj.lower() in medium_priority:
                score += 0.5
            else:
                score += 0.2
        
        # Normalize by number of objects (capped at 10)
        return min(1.0, score / 10.0)
    
    def _calculate_ocr_relevance(self, ocr_tokens: List[str]) -> float:
        """Calculate OCR relevance score."""
        if not ocr_tokens:
            return 0.0
        
        ocr_patterns = self.config.get("ocr_patterns", {})
        high_value = ocr_patterns.get("high_value", [])
        medium_value = ocr_patterns.get("medium_value", [])
        
        score = 0.0
        text = " ".join(ocr_tokens).lower()
        
        # Check high value patterns
        for pattern in high_value:
            if re.search(pattern, text, re.IGNORECASE):
                score += 1.0
        
        # Check medium value patterns
        for pattern in medium_value:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.5
        
        # Normalize (cap at 3 matches)
        return min(1.0, score / 3.0)
    
    def _calculate_duration_score(self, duration: float) -> float:
        """Calculate duration optimality score."""
        optimal = self.config.get("optimal_duration", {})
        min_dur = optimal.get("min", 3.0)
        max_dur = optimal.get("max", 15.0)
        target_dur = optimal.get("target", 8.0)
        
        if duration < min_dur or duration > max_dur:
            # Outside optimal range
            return 0.3
        
        # Calculate distance from target
        distance = abs(duration - target_dur)
        max_distance = max(target_dur - min_dur, max_dur - target_dur)
        
        if max_distance == 0:
            return 1.0
        
        score = 1.0 - (distance / max_distance)
        return max(0.0, score)
    
    def get_config(self) -> Dict[str, Any]:
        """Get the ranking configuration."""
        return self.config
