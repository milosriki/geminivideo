"""
Unit tests for ranking service
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ranking import RankingService
from models.asset import Clip, ClipFeatures


def test_ranking_score_calculation():
    """Test that ranking scores are calculated correctly"""
    config = {
        'weights': {
            'motion_score': 0.25,
            'object_diversity': 0.20,
            'text_presence': 0.15,
            'transcript_quality': 0.15,
            'technical_quality': 0.10,
            'novelty_score': 0.15
        },
        'thresholds': {
            'clustering_similarity': 0.85
        }
    }
    
    ranking_service = RankingService(config)
    
    # Create test clip
    clip = Clip(
        id="test_clip_1",
        asset_id="test_asset",
        start_time=0,
        end_time=5,
        duration=5,
        features=ClipFeatures(
            motion_score=0.8,
            objects=["person", "dumbbell", "mat"],
            text_detected=["Get Fit"],
            transcript="Transform your body",
            technical_quality=0.9
        )
    )
    
    clips = [clip]
    ranked = ranking_service.rank_clips(clips)
    
    assert len(ranked) == 1
    assert ranked[0].score > 0
    assert ranked[0].rank == 1


def test_ranking_order():
    """Test that clips are ranked in correct order"""
    config = {
        'weights': {
            'motion_score': 1.0,
            'object_diversity': 0.0,
            'text_presence': 0.0,
            'transcript_quality': 0.0,
            'technical_quality': 0.0,
            'novelty_score': 0.0
        },
        'thresholds': {}
    }
    
    ranking_service = RankingService(config)
    
    # Create clips with different motion scores
    clip1 = Clip(
        id="clip1",
        asset_id="test",
        start_time=0,
        end_time=5,
        duration=5,
        features=ClipFeatures(motion_score=0.3)
    )
    
    clip2 = Clip(
        id="clip2",
        asset_id="test",
        start_time=5,
        end_time=10,
        duration=5,
        features=ClipFeatures(motion_score=0.8)
    )
    
    clip3 = Clip(
        id="clip3",
        asset_id="test",
        start_time=10,
        end_time=15,
        duration=5,
        features=ClipFeatures(motion_score=0.5)
    )
    
    clips = [clip1, clip2, clip3]
    ranked = ranking_service.rank_clips(clips)
    
    # Should be ordered by motion score: clip2, clip3, clip1
    assert ranked[0].id == "clip2"
    assert ranked[1].id == "clip3"
    assert ranked[2].id == "clip1"


if __name__ == "__main__":
    test_ranking_score_calculation()
    test_ranking_order()
    print("All tests passed!")
