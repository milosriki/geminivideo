"""
Scene ranking and clustering service
"""
from typing import List, Dict
import numpy as np
from models.asset import Clip


class RankingService:
    """
    Rank and cluster video clips based on extracted features
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.weights = config.get('weights', {})
        self.thresholds = config.get('thresholds', {})
    
    def rank_clips(self, clips: List[Clip]) -> List[Clip]:
        """
        Rank clips based on feature scores
        
        Args:
            clips: List of clips to rank
            
        Returns:
            Sorted list of clips with scores and ranks assigned
        """
        # Calculate score for each clip
        for clip in clips:
            clip.score = self._calculate_score(clip)
        
        # Sort by score descending
        ranked_clips = sorted(clips, key=lambda c: c.score, reverse=True)
        
        # Assign ranks
        for idx, clip in enumerate(ranked_clips):
            clip.rank = idx + 1
        
        return ranked_clips
    
    def _calculate_score(self, clip: Clip) -> float:
        """
        Calculate weighted score for a clip
        """
        features = clip.features
        
        # Motion score
        motion_score = features.motion_score * self.weights.get('motion_score', 0.25)
        
        # Object diversity (number of unique objects)
        object_diversity = (
            min(len(features.objects) / 5.0, 1.0) * 
            self.weights.get('object_diversity', 0.20)
        )
        
        # Text presence (has text detected)
        text_presence = (
            (1.0 if features.text_detected else 0.0) * 
            self.weights.get('text_presence', 0.15)
        )
        
        # Transcript quality (has transcript)
        transcript_quality = (
            (1.0 if features.transcript else 0.0) * 
            self.weights.get('transcript_quality', 0.15)
        )
        
        # Technical quality
        technical_quality = (
            features.technical_quality * 
            self.weights.get('technical_quality', 0.10)
        )
        
        # Novelty score (will be set by search service if embedding available)
        novelty_score = 0.0
        if hasattr(clip, 'novelty_score'):
            novelty_score = clip.novelty_score * self.weights.get('novelty_score', 0.15)
        
        total_score = (
            motion_score + 
            object_diversity + 
            text_presence + 
            transcript_quality + 
            technical_quality + 
            novelty_score
        )
        
        return total_score
    
    def cluster_and_deduplicate(
        self, 
        clips: List[Clip], 
        similarity_threshold: float = None
    ) -> List[Clip]:
        """
        Cluster similar clips and keep only the top representative from each cluster
        
        Args:
            clips: Ranked list of clips
            similarity_threshold: Cosine similarity threshold (default from config)
            
        Returns:
            Deduplicated list of clips
        """
        if not clips:
            return []
        
        if similarity_threshold is None:
            similarity_threshold = self.thresholds.get('clustering_similarity', 0.85)
        
        # Only cluster clips with embeddings
        clips_with_embeddings = [c for c in clips if c.features.embedding is not None]
        clips_without_embeddings = [c for c in clips if c.features.embedding is None]
        
        if not clips_with_embeddings:
            return clips
        
        # Track which clips have been clustered
        clustered = set()
        result_clips = []
        
        for i, clip in enumerate(clips_with_embeddings):
            if i in clustered:
                continue
            
            # Add this clip as a representative
            result_clips.append(clip)
            clustered.add(i)
            
            # Find similar clips
            for j in range(i + 1, len(clips_with_embeddings)):
                if j in clustered:
                    continue
                
                similarity = self._cosine_similarity(
                    clip.features.embedding,
                    clips_with_embeddings[j].features.embedding
                )
                
                if similarity > similarity_threshold:
                    clustered.add(j)
        
        # Add clips without embeddings at the end
        result_clips.extend(clips_without_embeddings)
        
        return result_clips
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2:
            return 0.0
        
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
