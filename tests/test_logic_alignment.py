"""
Logic Alignment Tests
Validates that scoring and ranking logic is consistent across all services
"""

import pytest
import yaml
import json
from pathlib import Path


class TestWeightConfiguration:
    """Test weight configurations across all config files"""
    
    @pytest.fixture
    def config_path(self):
        return Path(__file__).parent.parent / "shared" / "config"
    
    @pytest.fixture
    def weights_config(self, config_path):
        with open(config_path / "weights.yaml") as f:
            return yaml.safe_load(f)
    
    @pytest.fixture
    def scene_ranking_config(self, config_path):
        with open(config_path / "scene_ranking.yaml") as f:
            return yaml.safe_load(f)
    
    def test_psychology_weights_sum_to_one(self, weights_config):
        """Psychology weights should sum to 1.0"""
        psych_weights = weights_config['psychology_weights']
        total = sum(psych_weights.values())
        assert abs(total - 1.0) < 0.01, f"Psychology weights sum to {total}, expected 1.0"
    
    def test_hook_weights_sum_to_one(self, weights_config):
        """Hook weights should sum to 1.0"""
        hook_weights = weights_config['hook_weights']
        total = sum(hook_weights.values())
        assert abs(total - 1.0) < 0.01, f"Hook weights sum to {total}, expected 1.0"
    
    def test_technical_weights_sum_to_one(self, weights_config):
        """Technical weights should sum to 1.0"""
        tech_weights = weights_config['technical_weights']
        total = sum(tech_weights.values())
        assert abs(total - 1.0) < 0.01, f"Technical weights sum to {total}, expected 1.0"
    
    def test_demographic_weights_sum_to_one(self, weights_config):
        """Demographic weights should sum to 1.0"""
        demo_weights = weights_config['demographic_weights']
        total = sum(demo_weights.values())
        assert abs(total - 1.0) < 0.01, f"Demographic weights sum to {total}, expected 1.0"
    
    def test_novelty_weights_sum_to_one(self, weights_config):
        """Novelty weights should sum to 1.0"""
        novelty_weights = weights_config['novelty_weights']
        total = sum(novelty_weights.values())
        assert abs(total - 1.0) < 0.01, f"Novelty weights sum to {total}, expected 1.0"
    
    def test_scene_ranking_weights_sum_to_one(self, scene_ranking_config):
        """Scene ranking weights should sum to 1.0"""
        ranking_weights = scene_ranking_config['weights']
        total = sum(ranking_weights.values())
        assert abs(total - 1.0) < 0.01, f"Scene ranking weights sum to {total}, expected 1.0"
    
    def test_probability_bands_coverage(self, weights_config):
        """Probability bands should cover full 0-1 range"""
        bands = weights_config['probability_bands']
        
        assert 'low' in bands
        assert 'mid' in bands
        assert 'high' in bands
        
        # Check coverage
        assert bands['low']['min'] == 0.0
        assert bands['high']['max'] == 1.0
        
        # Check no gaps
        assert bands['low']['max'] == bands['mid']['min']
        assert bands['mid']['max'] == bands['high']['min']


class TestCompositeScoreAlignment:
    """Test that composite score calculations are aligned"""
    
    def test_gateway_composite_weights_sum_to_one(self):
        """Gateway composite weights (psychology, hook, technical, demographic, novelty) should sum to 1.0"""
        # As defined in scoring-engine.ts
        weights = {
            'psychology': 0.3,
            'hook': 0.25,
            'technical': 0.2,
            'demographic': 0.15,
            'novelty': 0.1
        }
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.01, f"Gateway composite weights sum to {total}, expected 1.0"
    
    def test_composite_score_range(self):
        """Composite scores should always be in range [0, 1]"""
        # Test with extreme values
        test_cases = [
            (0.0, 0.0, 0.0, 0.0, 0.0),
            (1.0, 1.0, 1.0, 1.0, 1.0),
            (0.5, 0.5, 0.5, 0.5, 0.5),
            (0.2, 0.8, 0.3, 0.9, 0.1),
        ]
        
        weights = [0.3, 0.25, 0.2, 0.15, 0.1]
        
        for scores in test_cases:
            composite = sum(s * w for s, w in zip(scores, weights))
            assert 0.0 <= composite <= 1.0, f"Composite score {composite} out of range for inputs {scores}"


class TestScoringLogicConsistency:
    """Test that scoring logic is consistent across services"""
    
    def test_psychology_score_factors(self):
        """Psychology score should consider all required factors"""
        required_factors = [
            'pain_point',
            'transformation',
            'urgency',
            'authority',
            'social_proof'
        ]
        
        config_path = Path(__file__).parent.parent / "shared" / "config" / "weights.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        psych_weights = config['psychology_weights']
        for factor in required_factors:
            assert factor in psych_weights, f"Missing psychology factor: {factor}"
    
    def test_hook_strength_factors(self):
        """Hook strength should consider all required factors"""
        required_factors = [
            'has_number',
            'has_question',
            'motion_spike',
            'first_3s_text'
        ]
        
        config_path = Path(__file__).parent.parent / "shared" / "config" / "weights.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        hook_weights = config['hook_weights']
        for factor in required_factors:
            assert factor in hook_weights, f"Missing hook factor: {factor}"
    
    def test_scene_ranking_factors(self):
        """Scene ranking should consider all required factors"""
        required_factors = [
            'motion_score',
            'object_diversity',
            'text_presence',
            'transcript_quality',
            'novelty_score',
            'technical_quality'
        ]
        
        config_path = Path(__file__).parent.parent / "shared" / "config" / "scene_ranking.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        ranking_weights = config['weights']
        for factor in required_factors:
            assert factor in ranking_weights, f"Missing ranking factor: {factor}"


class TestPerformanceBandLogic:
    """Test performance band prediction logic"""
    
    @pytest.fixture
    def bands_config(self):
        config_path = Path(__file__).parent.parent / "shared" / "config" / "weights.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        return config['probability_bands']
    
    def test_band_classification_low(self, bands_config):
        """Low scores should be classified as low band"""
        low_score = 0.2
        band = self._classify_band(low_score, bands_config)
        assert band == 'low'
    
    def test_band_classification_mid(self, bands_config):
        """Mid scores should be classified as mid band"""
        mid_score = 0.5
        band = self._classify_band(mid_score, bands_config)
        assert band == 'mid'
    
    def test_band_classification_high(self, bands_config):
        """High scores should be classified as high band"""
        high_score = 0.85
        band = self._classify_band(high_score, bands_config)
        assert band == 'high'
    
    def test_band_boundaries(self, bands_config):
        """Boundary scores should be classified correctly"""
        # Test exact boundaries
        assert self._classify_band(0.0, bands_config) == 'low'
        assert self._classify_band(0.3, bands_config) in ['low', 'mid']  # Boundary
        assert self._classify_band(0.7, bands_config) in ['mid', 'high']  # Boundary
        assert self._classify_band(1.0, bands_config) == 'high'
    
    def _classify_band(self, score, bands_config):
        """Helper to classify score into band"""
        if score < bands_config['low']['max']:
            return 'low'
        elif score >= bands_config['high']['min']:
            return 'high'
        else:
            return 'mid'


class TestConfigFileIntegrity:
    """Test that all config files are valid and complete"""
    
    @pytest.fixture
    def config_path(self):
        return Path(__file__).parent.parent / "shared" / "config"
    
    def test_all_required_configs_exist(self, config_path):
        """All required config files should exist"""
        required_files = [
            "weights.yaml",
            "scene_ranking.yaml",
            "triggers_config.json",
            "personas.json",
            "hook_templates.json"
        ]
        
        for filename in required_files:
            filepath = config_path / filename
            assert filepath.exists(), f"Missing required config file: {filename}"
    
    def test_yaml_files_valid(self, config_path):
        """All YAML config files should be valid"""
        yaml_files = ["weights.yaml", "scene_ranking.yaml"]
        
        for filename in yaml_files:
            filepath = config_path / filename
            with open(filepath) as f:
                try:
                    config = yaml.safe_load(f)
                    assert config is not None, f"{filename} is empty"
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {filename}: {e}")
    
    def test_json_files_valid(self, config_path):
        """All JSON config files should be valid"""
        json_files = ["triggers_config.json", "personas.json", "hook_templates.json"]
        
        for filename in json_files:
            filepath = config_path / filename
            with open(filepath) as f:
                try:
                    config = json.load(f)
                    assert config is not None, f"{filename} is empty"
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {filename}: {e}")


class TestLearningParametersAlignment:
    """Test that learning parameters are properly configured"""
    
    @pytest.fixture
    def learning_config(self):
        config_path = Path(__file__).parent.parent / "shared" / "config" / "weights.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        return config['learning']
    
    def test_learning_parameters_exist(self, learning_config):
        """Learning parameters should be defined"""
        required_params = [
            'min_samples_for_update',
            'max_weight_delta',
            'learning_rate'
        ]
        
        for param in required_params:
            assert param in learning_config, f"Missing learning parameter: {param}"
    
    def test_learning_rate_in_valid_range(self, learning_config):
        """Learning rate should be in valid range (0, 1)"""
        lr = learning_config['learning_rate']
        assert 0 < lr < 1, f"Learning rate {lr} should be in range (0, 1)"
    
    def test_max_weight_delta_reasonable(self, learning_config):
        """Max weight delta should be reasonable (0, 0.5)"""
        delta = learning_config['max_weight_delta']
        assert 0 < delta < 0.5, f"Max weight delta {delta} should be in range (0, 0.5)"
    
    def test_min_samples_positive(self, learning_config):
        """Min samples should be positive"""
        min_samples = learning_config['min_samples_for_update']
        assert min_samples > 0, f"Min samples {min_samples} should be positive"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
