"""
Mock Data for ML Model Tests
Agent 29 of 30
"""

import numpy as np
import pandas as pd
from typing import Dict, List


def generate_mock_training_data(n_samples: int = 100) -> pd.DataFrame:
    """Generate mock training data for ML models."""
    np.random.seed(42)

    return pd.DataFrame({
        # Creative features
        'hook_type': np.random.choice(['problem_solution', 'curiosity', 'testimonial', 'demonstration'], n_samples),
        'hook_strength': np.random.uniform(5.0, 10.0, n_samples),
        'visual_complexity': np.random.uniform(4.0, 9.0, n_samples),
        'text_density': np.random.uniform(0.05, 0.25, n_samples),
        'face_presence': np.random.choice([True, False], n_samples),
        'motion_score': np.random.uniform(5.0, 10.0, n_samples),
        'video_duration': np.random.uniform(10.0, 30.0, n_samples),
        'aspect_ratio': np.random.choice([0.5625, 1.0, 1.91], n_samples),
        'color_vibrancy': np.random.uniform(5.0, 10.0, n_samples),
        'scene_count': np.random.randint(2, 8, n_samples),

        # Targeting features
        'audience_size': np.random.randint(1000000, 5000000, n_samples),
        'audience_overlap': np.random.uniform(0.1, 0.3, n_samples),
        'cpm_estimate': np.random.uniform(8.0, 20.0, n_samples),
        'age_min': np.random.choice([18, 25, 35], n_samples),
        'age_max': np.random.choice([44, 54, 65], n_samples),
        'gender_targeting': np.random.choice(['all', 'male', 'female'], n_samples),
        'interest_count': np.random.randint(3, 10, n_samples),
        'custom_audience': np.random.choice([True, False], n_samples),

        # Historical features
        'account_avg_roas': np.random.uniform(2.0, 4.5, n_samples),
        'account_avg_ctr': np.random.uniform(1.0, 3.0, n_samples),
        'vertical_avg_roas': np.random.uniform(2.0, 4.0, n_samples),
        'similar_creative_roas': np.random.uniform(2.5, 4.5, n_samples),
        'day_of_week': np.random.randint(0, 7, n_samples),
        'hour_of_day': np.random.randint(0, 24, n_samples),
        'days_since_last_winner': np.random.randint(1, 30, n_samples),
        'account_spend_30d': np.random.uniform(30000, 100000, n_samples),
        'account_conversions_30d': np.random.randint(200, 800, n_samples),
        'creative_fatigue_score': np.random.uniform(0.0, 0.5, n_samples),

        # Copy features
        'cta_type': np.random.choice(['shop_now', 'learn_more', 'sign_up', 'download'], n_samples),
        'urgency_score': np.random.uniform(4.0, 9.0, n_samples),
        'benefit_count': np.random.randint(2, 6, n_samples),
        'pain_point_addressed': np.random.choice([True, False], n_samples),
        'social_proof_present': np.random.choice([True, False], n_samples),
        'word_count': np.random.randint(30, 80, n_samples),
        'emoji_count': np.random.randint(0, 5, n_samples),
        'question_present': np.random.choice([True, False], n_samples),

        # Target
        'actual_roas': np.random.uniform(1.5, 5.0, n_samples)
    })


def mock_feature_set() -> Dict:
    """Generate a single mock feature set."""
    return {
        'hook_type': 'problem_solution',
        'hook_strength': 8.0,
        'visual_complexity': 7.5,
        'text_density': 0.12,
        'face_presence': True,
        'motion_score': 8.5,
        'video_duration': 15.0,
        'aspect_ratio': 0.5625,
        'color_vibrancy': 8.0,
        'scene_count': 4,
        'audience_size': 2500000,
        'audience_overlap': 0.18,
        'cpm_estimate': 13.5,
        'age_min': 25,
        'age_max': 54,
        'gender_targeting': 'all',
        'interest_count': 6,
        'custom_audience': False,
        'account_avg_roas': 3.5,
        'account_avg_ctr': 2.1,
        'vertical_avg_roas': 3.2,
        'similar_creative_roas': 3.8,
        'day_of_week': 3,
        'hour_of_day': 14,
        'days_since_last_winner': 5,
        'account_spend_30d': 75000.0,
        'account_conversions_30d': 600,
        'creative_fatigue_score': 0.15,
        'cta_type': 'shop_now',
        'urgency_score': 7.0,
        'benefit_count': 4,
        'pain_point_addressed': True,
        'social_proof_present': True,
        'word_count': 48,
        'emoji_count': 3,
        'question_present': False
    }


def mock_prediction_response() -> Dict:
    """Generate mock prediction response."""
    return {
        'predicted_roas': 3.45,
        'confidence_low': 3.10,
        'confidence_high': 3.80,
        'confidence_score': 0.85,
        'feature_contributions': {
            'hook_strength': 0.45,
            'account_avg_roas': 0.32,
            'similar_creative_roas': 0.28,
            'visual_complexity': 0.15
        },
        'similar_campaigns_avg_roas': 3.40,
        'prediction_timestamp': '2024-01-01T00:00:00Z'
    }
