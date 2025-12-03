"""
Enhanced XGBoost CTR Prediction Model - Agent 5
Production-ready model with 75+ features targeting R² > 0.88 (94% accuracy)
"""
import xgboost as xgb
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import os
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class EnhancedCTRPredictor:
    """Enhanced XGBoost-based CTR prediction model with 75+ features"""

    def __init__(self, model_path: str = 'models/enhanced_ctr_model.pkl'):
        """
        Initialize Enhanced CTR Predictor

        Args:
            model_path: Path to save/load the trained model
        """
        self.model_path = model_path
        self.model: Optional[xgb.XGBRegressor] = None
        self.feature_names: List[str] = self._get_feature_names()
        self.training_metrics: Dict[str, float] = {}
        self.is_trained = False
        self.scaler_params: Optional[Dict[str, Any]] = None

        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        # Try to load existing model
        if os.path.exists(model_path):
            try:
                self.load(model_path)
            except Exception as e:
                logger.warning(f"Failed to load existing model: {e}")

    def _get_feature_names(self) -> List[str]:
        """
        Define all 75+ feature names across 8 categories

        Returns:
            List of feature names
        """
        features = []

        # 1. Psychology scores (5 features)
        features.extend([
            'psychology_score',
            'pain_point_score',
            'transformation_promise',
            'urgency_factor',
            'authority_credibility',
            'social_proof_strength'
        ])

        # 2. Hook analysis (10 features)
        features.extend([
            'hook_strength',
            'hook_first_3_seconds',
            'has_number_in_hook',
            'has_question_in_hook',
            'motion_spike_intensity',
            'pattern_interrupt_score',
            'curiosity_gap_score',
            'visual_hook_quality',
            'audio_hook_quality',
            'hook_text_clarity'
        ])

        # 3. Visual patterns (15 features)
        features.extend([
            'scene_transition_count',
            'avg_scene_duration',
            'scene_duration_variance',
            'color_vibrancy_score',
            'color_contrast_ratio',
            'brightness_level',
            'saturation_level',
            'visual_complexity',
            'face_screen_time_ratio',
            'product_screen_time_ratio',
            'text_overlay_duration',
            'motion_intensity_avg',
            'motion_intensity_peak',
            'visual_novelty_score',
            'composition_quality'
        ])

        # 4. Technical quality (12 features)
        features.extend([
            'technical_score',
            'resolution_quality',
            'frame_rate_consistency',
            'audio_clarity',
            'audio_volume_consistency',
            'audio_background_ratio',
            'lighting_quality',
            'lighting_consistency',
            'stabilization_score',
            'focus_sharpness',
            'compression_artifacts',
            'aspect_ratio_score'
        ])

        # 5. Emotion features (10 features)
        features.extend([
            'dominant_emotion_score',
            'emotion_happy_ratio',
            'emotion_surprise_ratio',
            'emotion_neutral_ratio',
            'emotion_intensity_avg',
            'emotion_intensity_peak',
            'emotion_variance',
            'emotion_transitions',
            'face_count_avg',
            'face_engagement_score'
        ])

        # 6. Object detection (10 features)
        features.extend([
            'product_presence_score',
            'brand_logo_visibility',
            'people_count_avg',
            'object_diversity',
            'key_object_focus_time',
            'background_complexity',
            'object_movement_score',
            'product_size_ratio',
            'text_readability_score',
            'cta_button_prominence'
        ])

        # 7. Novelty & historical (8 features)
        features.extend([
            'novelty_score',
            'concept_uniqueness',
            'visual_style_novelty',
            'format_novelty',
            'historical_performance_similar',
            'trend_alignment_score',
            'competitive_differentiation',
            'creative_freshness'
        ])

        # 8. Demographic match (5 features)
        features.extend([
            'demographic_match',
            'age_targeting_alignment',
            'gender_targeting_alignment',
            'interest_targeting_alignment',
            'platform_optimization_score'
        ])

        return features

    def extract_features(self, clip_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract 75+ features from clip data

        Args:
            clip_data: Dictionary with clip analysis results and metadata

        Returns:
            Feature vector as numpy array (75+ features)
        """
        features = []

        # Helper function to safely extract nested values
        def safe_get(data: Dict, *keys, default=0.0):
            for key in keys:
                if isinstance(data, dict):
                    data = data.get(key, default)
                else:
                    return default
            return data if data is not None else default

        # 1. Psychology scores (6 features)
        features.append(safe_get(clip_data, 'psychology_score', default=0.5))
        psych = safe_get(clip_data, 'psychology_details', default={})
        features.append(safe_get(psych, 'pain_point', default=0.5))
        features.append(safe_get(psych, 'transformation', default=0.5))
        features.append(safe_get(psych, 'urgency', default=0.5))
        features.append(safe_get(psych, 'authority', default=0.5))
        features.append(safe_get(psych, 'social_proof', default=0.5))

        # 2. Hook analysis (10 features)
        features.append(safe_get(clip_data, 'hook_strength', default=0.5))
        hook_details = safe_get(clip_data, 'hook_details', default={})
        features.append(safe_get(clip_data, 'hook_first_3_seconds', default=0.5))
        features.append(1.0 if safe_get(hook_details, 'has_number') else 0.0)
        features.append(1.0 if safe_get(hook_details, 'has_question') else 0.0)
        features.append(safe_get(hook_details, 'motion_spike', default=0.5))
        features.append(safe_get(hook_details, 'pattern_interrupt', default=0.5))
        features.append(safe_get(hook_details, 'curiosity_gap', default=0.5))
        features.append(safe_get(hook_details, 'visual_quality', default=0.7))
        features.append(safe_get(hook_details, 'audio_quality', default=0.7))
        features.append(safe_get(hook_details, 'text_clarity', default=0.7))

        # 3. Visual patterns (15 features)
        visual = safe_get(clip_data, 'visual_patterns', default={})
        features.append(safe_get(clip_data, 'scene_count', default=3))
        features.append(safe_get(clip_data, 'avg_scene_duration', default=5.0))
        features.append(safe_get(clip_data, 'scene_score_variance', default=0.1))
        features.append(safe_get(visual, 'color_vibrancy', default=0.6))
        features.append(safe_get(visual, 'color_contrast', default=0.5))
        features.append(safe_get(visual, 'brightness', default=0.6))
        features.append(safe_get(visual, 'saturation', default=0.6))
        features.append(safe_get(visual, 'complexity', default=0.5))
        features.append(safe_get(visual, 'face_screen_time', default=0.3))
        features.append(safe_get(visual, 'product_screen_time', default=0.4))
        features.append(safe_get(visual, 'text_duration', default=0.2))
        features.append(safe_get(visual, 'motion_avg', default=0.5))
        features.append(safe_get(visual, 'motion_peak', default=0.7))
        features.append(safe_get(visual, 'novelty', default=0.5))
        features.append(safe_get(visual, 'composition', default=0.7))

        # 4. Technical quality (12 features)
        tech = safe_get(clip_data, 'technical_details', default={})
        features.append(safe_get(clip_data, 'technical_score', default=0.7))
        features.append(safe_get(tech, 'resolution_score', default=0.8))
        features.append(safe_get(tech, 'frame_rate', default=0.9))
        features.append(safe_get(tech, 'audio_clarity', default=0.7))
        features.append(safe_get(tech, 'audio_volume', default=0.8))
        features.append(safe_get(tech, 'audio_background', default=0.6))
        features.append(safe_get(tech, 'lighting', default=0.7))
        features.append(safe_get(tech, 'lighting_consistency', default=0.7))
        features.append(safe_get(tech, 'stabilization', default=0.8))
        features.append(safe_get(tech, 'focus', default=0.8))
        features.append(safe_get(tech, 'compression', default=0.9))
        features.append(safe_get(tech, 'aspect_ratio', default=1.0))

        # 5. Emotion features (10 features)
        emotion = safe_get(clip_data, 'emotion_features', default={})
        features.append(safe_get(emotion, 'dominant_emotion_score', default=0.5))
        features.append(safe_get(emotion, 'happy_ratio', default=0.4))
        features.append(safe_get(emotion, 'surprise_ratio', default=0.2))
        features.append(safe_get(emotion, 'neutral_ratio', default=0.3))
        features.append(safe_get(emotion, 'intensity_avg', default=0.5))
        features.append(safe_get(emotion, 'intensity_peak', default=0.7))
        features.append(safe_get(emotion, 'variance', default=0.2))
        features.append(safe_get(emotion, 'transitions', default=3.0))
        features.append(safe_get(emotion, 'face_count_avg', default=1.5))
        features.append(safe_get(emotion, 'engagement', default=0.6))

        # 6. Object detection (10 features)
        objects = safe_get(clip_data, 'object_detection', default={})
        features.append(safe_get(objects, 'product_presence', default=0.7))
        features.append(safe_get(objects, 'brand_visibility', default=0.6))
        features.append(safe_get(objects, 'people_count', default=1.5))
        features.append(safe_get(objects, 'diversity', default=0.5))
        features.append(safe_get(objects, 'key_object_time', default=0.4))
        features.append(safe_get(objects, 'background_complexity', default=0.5))
        features.append(safe_get(objects, 'movement', default=0.5))
        features.append(safe_get(objects, 'product_size', default=0.3))
        features.append(safe_get(objects, 'text_readability', default=0.8))
        features.append(safe_get(objects, 'cta_prominence', default=0.6))

        # 7. Novelty & historical (8 features)
        features.append(safe_get(clip_data, 'novelty_score', default=0.5))
        novelty = safe_get(clip_data, 'novelty_details', default={})
        features.append(safe_get(novelty, 'concept_unique', default=0.5))
        features.append(safe_get(novelty, 'visual_style', default=0.5))
        features.append(safe_get(novelty, 'format_novel', default=0.5))
        features.append(safe_get(clip_data, 'historical_performance', default=0.5))
        features.append(safe_get(clip_data, 'trend_alignment', default=0.5))
        features.append(safe_get(clip_data, 'competitive_diff', default=0.5))
        features.append(safe_get(clip_data, 'creative_freshness', default=0.5))

        # 8. Demographic match (5 features)
        features.append(safe_get(clip_data, 'demographic_match', default=0.6))
        demo = safe_get(clip_data, 'demographic_details', default={})
        features.append(safe_get(demo, 'age_match', default=0.6))
        features.append(safe_get(demo, 'gender_match', default=0.6))
        features.append(safe_get(demo, 'interest_match', default=0.6))
        features.append(safe_get(demo, 'platform_optimization', default=0.7))

        return np.array(features, dtype=np.float32)

    def prepare_training_data(
        self,
        historical_ads: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data from historical ad performance

        Args:
            historical_ads: List of dicts with 'clip_data' and 'actual_ctr'

        Returns:
            Tuple of (X, y) - features and target CTR values
        """
        X_list = []
        y_list = []

        for ad in historical_ads:
            try:
                features = self.extract_features(ad['clip_data'])
                ctr = ad['actual_ctr']

                # Validate CTR is in reasonable range
                if 0.0 <= ctr <= 1.0:
                    X_list.append(features)
                    y_list.append(ctr)
                else:
                    logger.warning(f"Invalid CTR value: {ctr}, skipping sample")
            except Exception as e:
                logger.warning(f"Error processing ad data: {e}")
                continue

        if len(X_list) == 0:
            raise ValueError("No valid training samples prepared")

        X = np.vstack(X_list)
        y = np.array(y_list, dtype=np.float32)

        logger.info(f"Prepared {len(y)} training samples with {X.shape[1]} features")

        return X, y

    def train(
        self,
        historical_ads: List[Dict[str, Any]],
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, float]:
        """
        Train enhanced XGBoost model on historical ad data

        Args:
            historical_ads: List of historical ad performance data
            test_size: Fraction of data for testing (default: 0.2)
            random_state: Random seed for reproducibility

        Returns:
            Dictionary of training metrics
        """
        logger.info(f"Training Enhanced CTR model on {len(historical_ads)} historical ads")

        # Prepare training data
        X, y = self.prepare_training_data(historical_ads)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        # Initialize XGBoost with optimized hyperparameters for R² > 0.88
        self.model = xgb.XGBRegressor(
            objective='reg:squarederror',
            n_estimators=300,  # More trees for better accuracy
            max_depth=8,  # Deeper trees for complex patterns
            learning_rate=0.03,  # Lower learning rate for fine-tuning
            min_child_weight=2,
            subsample=0.85,
            colsample_bytree=0.85,
            colsample_bylevel=0.85,
            gamma=0.05,  # Min loss reduction
            reg_alpha=0.05,  # L1 regularization
            reg_lambda=2.0,  # L2 regularization
            max_delta_step=1,  # Conservative updates
            random_state=random_state,
            n_jobs=-1,
            tree_method='hist',  # Faster training
            early_stopping_rounds=30,
            eval_metric='rmse'
        )

        # Train with early stopping
        eval_set = [(X_train, y_train), (X_test, y_test)]
        self.model.fit(
            X_train,
            y_train,
            eval_set=eval_set,
            verbose=False
        )

        # Calculate comprehensive metrics
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)

        # Clip predictions to valid CTR range
        train_pred = np.clip(train_pred, 0.0, 1.0)
        test_pred = np.clip(test_pred, 0.0, 1.0)

        # Regression metrics
        train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
        test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))

        train_mae = mean_absolute_error(y_train, train_pred)
        test_mae = mean_absolute_error(y_test, test_pred)

        train_r2 = r2_score(y_train, train_pred)
        test_r2 = r2_score(y_test, test_pred)

        # Accuracy within tolerance (±0.02 CTR = 94% accuracy target)
        tolerance = 0.02
        train_accuracy = np.mean(np.abs(y_train - train_pred) <= tolerance)
        test_accuracy = np.mean(np.abs(y_test - test_pred) <= tolerance)

        self.training_metrics = {
            'train_rmse': float(train_rmse),
            'test_rmse': float(test_rmse),
            'train_mae': float(train_mae),
            'test_mae': float(test_mae),
            'train_r2': float(train_r2),
            'test_r2': float(test_r2),
            'train_accuracy': float(train_accuracy),
            'test_accuracy': float(test_accuracy),
            'n_samples': int(X.shape[0]),
            'n_features': int(X.shape[1]),
            'n_train': int(len(y_train)),
            'n_test': int(len(y_test)),
            'trained_at': datetime.utcnow().isoformat(),
            'target_achieved': bool(test_r2 >= 0.88)
        }

        self.is_trained = True

        logger.info(f"Model trained: Test R² = {test_r2:.4f}, Test Accuracy = {test_accuracy:.2%}")
        if test_r2 >= 0.88:
            logger.info("✓ Target R² > 0.88 ACHIEVED!")
        else:
            logger.warning(f"✗ Target R² > 0.88 NOT achieved (current: {test_r2:.4f})")

        return self.training_metrics

    def predict(self, clip_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict CTR for a single clip

        Args:
            clip_data: Clip analysis data

        Returns:
            Dictionary with prediction results
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        # Extract features
        features = self.extract_features(clip_data)
        features = features.reshape(1, -1)

        # Predict
        predicted_ctr = self.model.predict(features)[0]
        predicted_ctr = float(np.clip(predicted_ctr, 0.0, 1.0))

        # Determine CTR band
        if predicted_ctr < 0.02:
            band = 'low'
        elif predicted_ctr < 0.05:
            band = 'medium'
        elif predicted_ctr < 0.10:
            band = 'high'
        else:
            band = 'excellent'

        # Calculate confidence based on model performance
        test_rmse = self.training_metrics.get('test_rmse', 0.05)
        confidence = 1.0 - min(test_rmse * 10, 0.5)

        return {
            'predicted_ctr': predicted_ctr,
            'predicted_band': band,
            'confidence': float(confidence)
        }

    def predict_batch(self, clips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Predict CTR for multiple clips

        Args:
            clips: List of clip analysis data

        Returns:
            List of prediction results
        """
        results = []

        for clip_data in clips:
            try:
                prediction = self.predict(clip_data)
                results.append(prediction)
            except Exception as e:
                logger.error(f"Error predicting clip: {e}")
                results.append({
                    'predicted_ctr': 0.0,
                    'predicted_band': 'error',
                    'confidence': 0.0,
                    'error': str(e)
                })

        return results

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores

        Returns:
            Dictionary mapping feature names to importance scores
        """
        if self.model is None:
            raise ValueError("Model not trained")

        importance = self.model.feature_importances_

        # Create sorted dictionary
        importance_dict = {
            name: float(score)
            for name, score in zip(self.feature_names, importance)
        }

        # Sort by importance
        importance_dict = dict(
            sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
        )

        return importance_dict

    def save(self, path: Optional[str] = None):
        """
        Save trained model to disk

        Args:
            path: Optional path to save model (uses default if None)
        """
        if self.model is None:
            raise ValueError("No model to save. Train the model first.")

        save_path = path or self.model_path

        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'training_metrics': self.training_metrics,
            'is_trained': self.is_trained,
            'scaler_params': self.scaler_params,
            'version': '1.0.0',
            'saved_at': datetime.utcnow().isoformat()
        }

        joblib.dump(model_data, save_path)
        logger.info(f"Enhanced CTR model saved to {save_path}")

    def load(self, path: Optional[str] = None):
        """
        Load trained model from disk

        Args:
            path: Optional path to load model from (uses default if None)
        """
        load_path = path or self.model_path

        if not os.path.exists(load_path):
            raise FileNotFoundError(f"Model file not found: {load_path}")

        model_data = joblib.load(load_path)

        self.model = model_data['model']
        self.feature_names = model_data.get('feature_names', self._get_feature_names())
        self.training_metrics = model_data.get('training_metrics', {})
        self.is_trained = model_data.get('is_trained', True)
        self.scaler_params = model_data.get('scaler_params')

        logger.info(f"Enhanced CTR model loaded from {load_path}")
        logger.info(f"Model version: {model_data.get('version', 'unknown')}")
        logger.info(f"Test R²: {self.training_metrics.get('test_r2', 'N/A')}")


def generate_synthetic_training_data(n_samples: int = 1000) -> List[Dict[str, Any]]:
    """
    Generate synthetic training data for initial model training

    Args:
        n_samples: Number of samples to generate

    Returns:
        List of synthetic historical ads with clip_data and actual_ctr
    """
    np.random.seed(42)

    historical_ads = []

    for i in range(n_samples):
        # Generate realistic feature values
        psychology_score = np.random.beta(4, 2)  # Skewed toward higher values
        hook_strength = np.random.beta(3, 2)
        technical_score = np.random.beta(5, 2)
        novelty_score = np.random.beta(2, 2)
        demographic_match = np.random.beta(3, 2)

        # Visual patterns
        scene_count = int(np.random.uniform(2, 8))
        motion_intensity = np.random.beta(3, 2)
        color_vibrancy = np.random.beta(4, 3)

        # Emotion features
        emotion_happy = np.random.beta(4, 3)
        emotion_intensity = np.random.beta(3, 2)

        # Create clip data
        clip_data = {
            'psychology_score': psychology_score,
            'psychology_details': {
                'pain_point': np.random.beta(3, 2),
                'transformation': np.random.beta(3, 2),
                'urgency': np.random.beta(2, 3),
                'authority': np.random.beta(3, 3),
                'social_proof': np.random.beta(3, 3)
            },
            'hook_strength': hook_strength,
            'hook_first_3_seconds': hook_strength * np.random.uniform(0.9, 1.1),
            'hook_details': {
                'has_number': bool(np.random.rand() > 0.6),
                'has_question': bool(np.random.rand() > 0.5),
                'motion_spike': np.random.beta(3, 2),
                'pattern_interrupt': np.random.beta(2, 2),
                'curiosity_gap': np.random.beta(3, 2),
                'visual_quality': np.random.beta(5, 2),
                'audio_quality': np.random.beta(4, 2),
                'text_clarity': np.random.beta(4, 2)
            },
            'visual_patterns': {
                'color_vibrancy': color_vibrancy,
                'color_contrast': np.random.beta(3, 2),
                'brightness': np.random.beta(4, 3),
                'saturation': np.random.beta(3, 2),
                'complexity': np.random.beta(2, 2),
                'face_screen_time': np.random.beta(3, 4),
                'product_screen_time': np.random.beta(4, 3),
                'text_duration': np.random.beta(2, 3),
                'motion_avg': motion_intensity,
                'motion_peak': motion_intensity * np.random.uniform(1.2, 1.5),
                'novelty': novelty_score,
                'composition': np.random.beta(4, 2)
            },
            'scene_count': scene_count,
            'avg_scene_duration': 30.0 / scene_count,
            'scene_score_variance': np.random.uniform(0.05, 0.2),
            'technical_score': technical_score,
            'technical_details': {
                'resolution_score': np.random.beta(6, 2),
                'frame_rate': np.random.beta(7, 2),
                'audio_clarity': np.random.beta(4, 2),
                'audio_volume': np.random.beta(5, 2),
                'audio_background': np.random.beta(3, 2),
                'lighting': np.random.beta(4, 2),
                'lighting_consistency': np.random.beta(4, 3),
                'stabilization': np.random.beta(5, 2),
                'focus': np.random.beta(5, 2),
                'compression': np.random.beta(6, 2),
                'aspect_ratio': 1.0
            },
            'emotion_features': {
                'dominant_emotion_score': emotion_happy,
                'happy_ratio': emotion_happy,
                'surprise_ratio': np.random.beta(2, 4),
                'neutral_ratio': np.random.beta(3, 4),
                'intensity_avg': emotion_intensity,
                'intensity_peak': emotion_intensity * 1.3,
                'variance': np.random.uniform(0.1, 0.4),
                'transitions': int(np.random.uniform(2, 6)),
                'face_count_avg': np.random.uniform(1, 3),
                'engagement': emotion_intensity * np.random.uniform(0.8, 1.2)
            },
            'object_detection': {
                'product_presence': np.random.beta(5, 2),
                'brand_visibility': np.random.beta(4, 3),
                'people_count': np.random.uniform(1, 3),
                'diversity': np.random.beta(2, 2),
                'key_object_time': np.random.beta(3, 3),
                'background_complexity': np.random.beta(2, 2),
                'movement': motion_intensity,
                'product_size': np.random.beta(3, 4),
                'text_readability': np.random.beta(5, 2),
                'cta_prominence': np.random.beta(4, 3)
            },
            'novelty_score': novelty_score,
            'novelty_details': {
                'concept_unique': np.random.beta(2, 2),
                'visual_style': np.random.beta(2, 2),
                'format_novel': np.random.beta(2, 3)
            },
            'historical_performance': np.random.beta(3, 2),
            'trend_alignment': np.random.beta(3, 2),
            'competitive_diff': np.random.beta(2, 2),
            'creative_freshness': novelty_score * np.random.uniform(0.9, 1.1),
            'demographic_match': demographic_match,
            'demographic_details': {
                'age_match': demographic_match * np.random.uniform(0.9, 1.1),
                'gender_match': demographic_match * np.random.uniform(0.9, 1.1),
                'interest_match': demographic_match * np.random.uniform(0.9, 1.1),
                'platform_optimization': np.random.beta(4, 2)
            }
        }

        # Calculate realistic CTR based on feature importance
        # More complex formula for realistic CTR prediction
        ctr = (
            0.20 * psychology_score +
            0.15 * hook_strength +
            0.12 * technical_score +
            0.10 * demographic_match +
            0.08 * emotion_happy +
            0.08 * motion_intensity +
            0.07 * novelty_score +
            0.05 * color_vibrancy +
            0.05 * emotion_intensity +
            0.10 * np.random.rand()  # Noise
        )

        # Add non-linear interactions
        ctr += 0.03 * psychology_score * hook_strength
        ctr += 0.02 * emotion_happy * demographic_match
        ctr -= 0.01 * (scene_count - 4) ** 2 / 20  # Optimal scene count ~ 4

        # Clip to realistic CTR range (0.5% to 15%)
        actual_ctr = np.clip(ctr / 1.3, 0.005, 0.15)

        historical_ads.append({
            'clip_data': clip_data,
            'actual_ctr': float(actual_ctr)
        })

    return historical_ads


# Global model instance
enhanced_ctr_predictor = EnhancedCTRPredictor()
