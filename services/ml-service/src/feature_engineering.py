"""
Feature Engineering Pipeline for XGBoost CTR Prediction
Agent 2 - Extract and transform clip features for ML model
"""
from typing import Dict, List, Any
import numpy as np
import pandas as pd
from datetime import datetime


class FeatureExtractor:
    """Extract features from clip data for XGBoost model"""

    def __init__(self):
        self.feature_names = self._get_feature_names()

    def extract_features(self, clip_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract feature vector from clip/storyboard data

        Args:
            clip_data: Dictionary with scoring results and clip metadata

        Returns:
            Feature vector as numpy array
        """
        features = []

        # Psychology scores (5 features)
        psychology = clip_data.get('psychology_score', 0)
        features.append(psychology)

        # Psychology sub-scores (if available)
        psych_details = clip_data.get('psychology_details', {})
        features.append(psych_details.get('pain_point', 0))
        features.append(psych_details.get('transformation', 0))
        features.append(psych_details.get('urgency', 0))
        features.append(psych_details.get('authority', 0))
        features.append(psych_details.get('social_proof', 0))

        # Hook strength (4 features)
        hook_score = clip_data.get('hook_strength', 0)
        features.append(hook_score)

        hook_details = clip_data.get('hook_details', {})
        features.append(1 if hook_details.get('has_number') else 0)
        features.append(1 if hook_details.get('has_question') else 0)
        features.append(hook_details.get('motion_spike', 0))

        # Technical scores (5 features)
        technical = clip_data.get('technical_score', 0)
        features.append(technical)

        tech_details = clip_data.get('technical_details', {})
        features.append(tech_details.get('resolution_score', 0.7))
        features.append(tech_details.get('audio_quality', 0.7))
        features.append(tech_details.get('lighting', 0.7))
        features.append(tech_details.get('stabilization', 0.7))

        # Demographic & Novelty (2 features)
        features.append(clip_data.get('demographic_match', 0))
        features.append(clip_data.get('novelty_score', 0.5))

        # Composite scores (2 features)
        features.append(clip_data.get('composite_score', 0))
        features.append(clip_data.get('win_probability', {}).get('value', 0))

        # Clip metadata (7 features)
        features.append(clip_data.get('duration_seconds', 30))  # Ad duration
        features.append(clip_data.get('scene_count', 1))  # Number of scenes
        features.append(clip_data.get('clip_count', 1))  # Number of clips

        # First scene duration (important for hook)
        first_scene_duration = clip_data.get('first_scene_duration', 3)
        features.append(first_scene_duration)

        # Average scene duration
        avg_scene_duration = clip_data.get('avg_scene_duration', 5)
        features.append(avg_scene_duration)

        # Emotion features (if available from DeepFace)
        emotion_data = clip_data.get('emotion_features', {})
        features.append(emotion_data.get('dominant_emotion_score', 0))
        features.append(emotion_data.get('emotion_variance', 0))

        # Scene quality metrics (4 features)
        features.append(clip_data.get('avg_scene_score', 0))
        features.append(clip_data.get('max_scene_score', 0))
        features.append(clip_data.get('min_scene_score', 0))
        features.append(clip_data.get('scene_score_variance', 0))

        # Time-based features (3 features)
        # Hour of day (if scheduling matters)
        hour = datetime.now().hour
        features.append(hour / 24.0)  # Normalize to [0,1]

        # Day of week
        day_of_week = datetime.now().weekday()
        features.append(day_of_week / 7.0)  # Normalize to [0,1]

        # Is weekend
        features.append(1 if day_of_week >= 5 else 0)

        # Text features (3 features)
        features.append(clip_data.get('text_length', 0) / 100.0)  # Normalized
        features.append(clip_data.get('keyword_density', 0))
        features.append(clip_data.get('call_to_action_present', 0))

        # Advanced features (Agent 2 - Visual Density)
        duration = max(clip_data.get('duration_seconds', 30), 1)
        scene_count = clip_data.get('scene_count', 1)
        features.append(scene_count / duration)  # scene_change_rate

        total_objects = clip_data.get('total_objects', 0)
        frame_count = clip_data.get('frame_count', duration * 30) # Assume 30fps if missing
        features.append(total_objects / max(frame_count, 1)) # object_density

        return np.array(features, dtype=np.float32)

    def extract_batch_features(self, clip_data_list: List[Dict[str, Any]]) -> np.ndarray:
        """
        Extract features for multiple clips at once

        Args:
            clip_data_list: List of clip data dictionaries

        Returns:
            Feature matrix (n_samples, n_features)
        """
        feature_vectors = [self.extract_features(clip) for clip in clip_data_list]
        return np.vstack(feature_vectors)

    def extract_features_as_dataframe(self, clip_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Extract features and return as pandas DataFrame with column names

        Args:
            clip_data: Dictionary with scoring results and clip metadata

        Returns:
            DataFrame with one row of features
        """
        features = self.extract_features(clip_data)
        return pd.DataFrame([features], columns=self.feature_names)

    def extract_batch_features_as_dataframe(
        self,
        clip_data_list: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Extract features for multiple clips and return as DataFrame

        Args:
            clip_data_list: List of clip data dictionaries

        Returns:
            DataFrame with features for all clips
        """
        feature_matrix = self.extract_batch_features(clip_data_list)
        return pd.DataFrame(feature_matrix, columns=self.feature_names)

    def _get_feature_names(self) -> List[str]:
        """Return list of feature names in order"""
        return [
            # Psychology (6 features)
            'psychology_score',
            'pain_point',
            'transformation',
            'urgency',
            'authority',
            'social_proof',

            # Hook strength (4 features)
            'hook_strength',
            'has_number',
            'has_question',
            'motion_spike',

            # Technical (5 features)
            'technical_score',
            'resolution_score',
            'audio_quality',
            'lighting',
            'stabilization',

            # Demographic & Novelty (2 features)
            'demographic_match',
            'novelty_score',

            # Composite (2 features)
            'composite_score',
            'win_probability',

            # Clip metadata (7 features)
            'duration_seconds',
            'scene_count',
            'clip_count',
            'first_scene_duration',
            'avg_scene_duration',
            'dominant_emotion_score',
            'emotion_variance',

            # Scene quality (4 features)
            'avg_scene_score',
            'max_scene_score',
            'min_scene_score',
            'scene_score_variance',

            # Time features (3 features)
            'hour_of_day',
            'day_of_week',
            'is_weekend',

            # Text features (3 features)
            'text_length_normalized',
            'keyword_density',
            'keyword_density',
            'call_to_action_present',

            # Advanced features
            'scene_change_rate',
            'object_density'
        ]

    def get_feature_count(self) -> int:
        """Return number of features"""
        return len(self.feature_names)

    def get_feature_importance_names(self, importance_scores: np.ndarray) -> pd.DataFrame:
        """
        Create a DataFrame of feature importances

        Args:
            importance_scores: Feature importance values from XGBoost

        Returns:
            DataFrame with feature names and importance scores
        """
        df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance_scores
        })
        return df.sort_values('importance', ascending=False)


# Singleton instance
feature_extractor = FeatureExtractor()
