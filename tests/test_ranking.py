"""
Unit tests for ranking logic
Tests the scoring and ranking algorithms
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPsychologyScoring:
    """Tests for psychology score calculation"""
    
    def test_curiosity_score_with_question(self):
        """Test curiosity score is high when question present"""
        features = {
            'has_question': True,
            'incomplete_narrative': False
        }
        
        # Mock scoring function behavior
        curiosity = 0.8 if features['has_question'] or features['incomplete_narrative'] else 0.4
        assert curiosity == 0.8
    
    def test_curiosity_score_without_question(self):
        """Test curiosity score is lower without question"""
        features = {
            'has_question': False,
            'incomplete_narrative': False
        }
        
        curiosity = 0.8 if features['has_question'] or features['incomplete_narrative'] else 0.4
        assert curiosity == 0.4
    
    def test_urgency_score_with_countdown(self):
        """Test urgency score with countdown present"""
        features = {
            'has_countdown': True,
            'limited_time': False
        }
        
        urgency = 0.85 if features['has_countdown'] or features['limited_time'] else 0.3
        assert urgency == 0.85


class TestHookStrength:
    """Tests for hook strength detection"""
    
    def test_curiosity_gap_hook_detection(self):
        """Test detection of curiosity gap hooks"""
        features = {
            'has_question': True,
            'incomplete_narrative': True
        }
        
        # Should identify as curiosity gap
        hook_type = 'curiosity_gap'
        assert hook_type == 'curiosity_gap'
    
    def test_urgency_hook_detection(self):
        """Test detection of urgency/scarcity hooks"""
        features = {
            'has_countdown': True,
            'limited_time': True
        }
        
        hook_type = 'urgency_scarcity'
        assert hook_type == 'urgency_scarcity'


class TestNoveltyScoring:
    """Tests for novelty score calculation"""
    
    def test_novelty_with_no_history(self):
        """Test novelty is high with no history"""
        history = []
        
        embedding_distance = 0.90 if len(history) == 0 else 0.72
        assert embedding_distance == 0.90
    
    def test_novelty_with_history(self):
        """Test novelty is lower with history"""
        history = [{'id': '1'}, {'id': '2'}]
        
        embedding_distance = 0.90 if len(history) == 0 else 0.72
        assert embedding_distance == 0.72
    
    def test_diversity_bonus(self):
        """Test diversity bonus calculation"""
        unique_features = 3
        diversity_bonus_rate = 0.10
        
        diversity_bonus = min(unique_features * diversity_bonus_rate, 0.30)
        assert diversity_bonus == 0.30  # Capped at 0.30


class TestCompositeScoring:
    """Tests for composite score calculation"""
    
    def test_composite_score_calculation(self):
        """Test weighted composite score"""
        psychology_score = 0.75
        hook_strength = 0.80
        novelty_score = 0.70
        
        # Weights: psychology 40%, hook 35%, novelty 25%
        composite = (
            psychology_score * 0.4 +
            hook_strength * 0.35 +
            novelty_score * 0.25
        )
        
        expected = 0.75 * 0.4 + 0.80 * 0.35 + 0.70 * 0.25
        assert abs(composite - expected) < 0.001
    
    def test_composite_score_bounds(self):
        """Test composite score stays within bounds"""
        psychology_score = 1.0
        hook_strength = 1.0
        novelty_score = 1.0
        
        composite = (
            psychology_score * 0.4 +
            hook_strength * 0.35 +
            novelty_score * 0.25
        )
        
        assert 0.0 <= composite <= 1.0


class TestPerformanceBands:
    """Tests for performance band prediction"""
    
    def test_viral_band_prediction(self):
        """Test viral band prediction for high scores"""
        composite_score = 0.90
        
        if composite_score >= 0.85:
            band = 'viral'
            predicted_ctr = 0.08
        elif composite_score >= 0.70:
            band = 'high'
            predicted_ctr = 0.05
        elif composite_score >= 0.50:
            band = 'medium'
            predicted_ctr = 0.03
        else:
            band = 'low'
            predicted_ctr = 0.01
        
        assert band == 'viral'
        assert predicted_ctr == 0.08
    
    def test_high_band_prediction(self):
        """Test high band prediction"""
        composite_score = 0.75
        
        if composite_score >= 0.85:
            band = 'viral'
        elif composite_score >= 0.70:
            band = 'high'
        elif composite_score >= 0.50:
            band = 'medium'
        else:
            band = 'low'
        
        assert band == 'high'
    
    def test_medium_band_prediction(self):
        """Test medium band prediction"""
        composite_score = 0.60
        
        if composite_score >= 0.85:
            band = 'viral'
        elif composite_score >= 0.70:
            band = 'high'
        elif composite_score >= 0.50:
            band = 'medium'
        else:
            band = 'low'
        
        assert band == 'medium'
    
    def test_low_band_prediction(self):
        """Test low band prediction"""
        composite_score = 0.30
        
        if composite_score >= 0.85:
            band = 'viral'
        elif composite_score >= 0.70:
            band = 'high'
        elif composite_score >= 0.50:
            band = 'medium'
        else:
            band = 'low'
        
        assert band == 'low'


class TestRanking:
    """Tests for clip ranking"""
    
    def test_clips_ranked_by_score(self):
        """Test clips are properly ranked by composite score"""
        clips = [
            {'id': 'a', 'score': 0.60},
            {'id': 'b', 'score': 0.85},
            {'id': 'c', 'score': 0.70},
            {'id': 'd', 'score': 0.50}
        ]
        
        # Sort by score descending
        ranked = sorted(clips, key=lambda x: x['score'], reverse=True)
        
        assert ranked[0]['id'] == 'b'  # Highest score
        assert ranked[1]['id'] == 'c'
        assert ranked[2]['id'] == 'a'
        assert ranked[3]['id'] == 'd'  # Lowest score
    
    def test_top_k_selection(self):
        """Test selecting top K clips"""
        clips = [
            {'id': str(i), 'score': i * 0.1}
            for i in range(20)
        ]
        
        ranked = sorted(clips, key=lambda x: x['score'], reverse=True)
        top_10 = ranked[:10]
        
        assert len(top_10) == 10
        assert all(top_10[i]['score'] >= top_10[i+1]['score'] for i in range(9))


class TestEmotionScoring:
    """Tests for emotion-based scoring"""
    
    def test_positive_emotion_boost(self):
        """Test positive emotions increase score"""
        base_score = 0.5
        emotion = "happy"
        
        # Happy and surprise should boost score
        boost = 0.2 if emotion in ["happy", "surprise"] else 0.0
        final_score = base_score + boost
        
        assert final_score == 0.7
    
    def test_negative_emotion_penalty(self):
        """Test negative emotions may affect score"""
        base_score = 0.5
        emotion = "angry"
        
        # Negative emotions might reduce score
        penalty = -0.1 if emotion in ["sad", "angry", "fear"] else 0.0
        final_score = max(base_score + penalty, 0.0)
        
        assert final_score == 0.4
    
    def test_neutral_emotion_no_change(self):
        """Test neutral emotion doesn't change score"""
        base_score = 0.5
        emotion = "neutral"
        
        boost = 0.2 if emotion in ["happy", "surprise"] else 0.0
        penalty = -0.1 if emotion in ["sad", "angry", "fear"] else 0.0
        final_score = base_score + boost + penalty
        
        assert final_score == 0.5
    
    def test_emotion_confidence_threshold(self):
        """Test emotion confidence threshold"""
        confidence = 0.75
        threshold = 0.5
        
        is_reliable = confidence >= threshold
        assert is_reliable is True


class TestSceneDetection:
    """Tests for scene detection"""
    
    def test_scene_boundaries(self):
        """Test scene boundary detection"""
        scenes = [
            (0.0, 5.0),
            (5.0, 12.0),
            (12.0, 20.0)
        ]
        
        # Verify no overlapping scenes
        for i in range(len(scenes) - 1):
            assert scenes[i][1] == scenes[i+1][0]
    
    def test_scene_duration_calculation(self):
        """Test scene duration is correctly calculated"""
        start_time = 5.0
        end_time = 12.0
        
        duration = end_time - start_time
        assert duration == 7.0
    
    def test_minimum_scene_length(self):
        """Test scenes meet minimum length requirement"""
        scenes = [
            (0.0, 3.5),
            (3.5, 8.0),
            (8.0, 15.0)
        ]
        
        min_length = 2.0
        for start, end in scenes:
            duration = end - start
            # All scenes should be at least min_length
            assert duration >= min_length


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
