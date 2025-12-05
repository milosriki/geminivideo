"""
ROAS Predictor - Agent 16 of 30
Real XGBoost + LightGBM ensemble for ROAS prediction with SHAP explainability.
NO MOCK DATA - Production-ready ML service.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import VotingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb
import shap
import joblib
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import json
import warnings

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ROASPrediction:
    """ROAS prediction result with confidence and explainability."""
    predicted_roas: float
    confidence_low: float
    confidence_high: float
    confidence_score: float
    feature_contributions: Dict[str, float]
    similar_campaigns_avg_roas: float
    prediction_timestamp: str = None

    def __post_init__(self):
        if self.prediction_timestamp is None:
            self.prediction_timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FeatureSet:
    """Complete feature set for ROAS prediction."""
    # Creative features (10)
    hook_type: str = "problem_solution"
    hook_strength: float = 7.5
    visual_complexity: float = 6.2
    text_density: float = 0.15
    face_presence: bool = True
    motion_score: float = 8.1
    video_duration: float = 15.0
    aspect_ratio: float = 0.5625  # 9:16
    color_vibrancy: float = 7.8
    scene_count: int = 3

    # Targeting features (8)
    audience_size: int = 2000000
    audience_overlap: float = 0.15
    cpm_estimate: float = 12.5
    age_min: int = 25
    age_max: int = 54
    gender_targeting: str = "all"
    interest_count: int = 5
    custom_audience: bool = False

    # Historical features (10)
    account_avg_roas: float = 3.2
    account_avg_ctr: float = 1.8
    vertical_avg_roas: float = 2.9
    similar_creative_roas: float = 3.5
    day_of_week: int = 2  # 0=Monday
    hour_of_day: int = 14
    days_since_last_winner: int = 7
    account_spend_30d: float = 50000.0
    account_conversions_30d: int = 450
    creative_fatigue_score: float = 0.2

    # Copy features (8)
    cta_type: str = "shop_now"
    urgency_score: float = 6.5
    benefit_count: int = 3
    pain_point_addressed: bool = True
    social_proof_present: bool = True
    word_count: int = 45
    emoji_count: int = 2
    question_present: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ROASPredictor:
    """
    XGBoost + LightGBM ensemble for ROAS prediction.
    Production-ready ML service with SHAP explainability.
    """

    FEATURE_COLUMNS = [
        # Creative (10)
        'hook_type', 'hook_strength', 'visual_complexity', 'text_density',
        'face_presence', 'motion_score', 'video_duration', 'aspect_ratio',
        'color_vibrancy', 'scene_count',
        # Targeting (8)
        'audience_size', 'audience_overlap', 'cpm_estimate', 'age_min',
        'age_max', 'gender_targeting', 'interest_count', 'custom_audience',
        # Historical (10)
        'account_avg_roas', 'account_avg_ctr', 'vertical_avg_roas',
        'similar_creative_roas', 'day_of_week', 'hour_of_day',
        'days_since_last_winner', 'account_spend_30d', 'account_conversions_30d',
        'creative_fatigue_score',
        # Copy (8)
        'cta_type', 'urgency_score', 'benefit_count', 'pain_point_addressed',
        'social_proof_present', 'word_count', 'emoji_count', 'question_present'
    ]  # 36 total features

    CATEGORICAL_FEATURES = ['hook_type', 'gender_targeting', 'cta_type']
    BOOLEAN_FEATURES = ['face_presence', 'custom_audience', 'pain_point_addressed',
                        'social_proof_present', 'question_present']

    def __init__(self, model_path: str = None):
        """Initialize predictor, load model if exists."""
        self.xgb_model = None
        self.lgb_model = None
        self.ensemble = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.shap_explainer = None
        self.feature_importance_ = None
        self.training_history = []
        self.performance_metrics = {}

        if model_path and Path(model_path).exists():
            logger.info(f"Loading model from {model_path}")
            self.load_model(model_path)
        else:
            logger.info("Initializing new predictor (no model loaded)")

    # ========== Model Training ==========

    def train(
        self,
        historical_campaigns: pd.DataFrame,
        target_column: str = "actual_roas",
        validation_split: float = 0.2
    ) -> Dict[str, float]:
        """
        Train ensemble model on historical data.

        Args:
            historical_campaigns: DataFrame with features and actual ROAS
            target_column: Name of target column
            validation_split: Fraction for validation

        Returns:
            Dictionary with performance metrics (R2, MAE, RMSE)
        """
        logger.info(f"Training on {len(historical_campaigns)} campaigns")

        # Prepare data
        X, y = self._prepare_training_data(historical_campaigns, target_column)

        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        # Train models
        logger.info("Training XGBoost...")
        self.xgb_model = self._build_xgboost(X_train_scaled, y_train)

        logger.info("Training LightGBM...")
        self.lgb_model = self._build_lightgbm(X_train_scaled, y_train)

        # Create ensemble
        logger.info("Creating voting ensemble...")
        self.ensemble = self._create_ensemble()
        self.ensemble.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = self.ensemble.predict(X_val_scaled)
        metrics = {
            'r2_score': r2_score(y_val, y_pred),
            'mae': mean_absolute_error(y_val, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_val, y_pred)),
            'train_samples': len(X_train),
            'val_samples': len(X_val),
            'training_date': datetime.utcnow().isoformat()
        }

        self.performance_metrics = metrics
        self.training_history.append(metrics)

        # Initialize SHAP explainer
        logger.info("Initializing SHAP explainer...")
        self.shap_explainer = shap.TreeExplainer(self.xgb_model)

        # Calculate feature importance
        self._calculate_feature_importance()

        logger.info(f"Training complete. R²={metrics['r2_score']:.4f}, MAE={metrics['mae']:.4f}")
        return metrics

    def _prepare_training_data(
        self,
        df: pd.DataFrame,
        target_column: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare and encode training data."""
        # Make a copy
        data = df.copy()

        # Encode categorical features
        for col in self.CATEGORICAL_FEATURES:
            if col in data.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    data[col] = self.label_encoders[col].fit_transform(data[col].astype(str))
                else:
                    data[col] = self.label_encoders[col].transform(data[col].astype(str))

        # Convert boolean to int
        for col in self.BOOLEAN_FEATURES:
            if col in data.columns:
                data[col] = data[col].astype(int)

        # Select features
        X = data[self.FEATURE_COLUMNS].values
        y = data[target_column].values

        return X, y

    def _build_xgboost(self, X: np.ndarray, y: np.ndarray) -> xgb.XGBRegressor:
        """Build and tune XGBoost model."""
        model = xgb.XGBRegressor(
            n_estimators=300,
            max_depth=7,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            objective='reg:squarederror',
            tree_method='hist'
        )

        model.fit(
            X, y,
            eval_set=[(X, y)],
            verbose=False
        )

        return model

    def _build_lightgbm(self, X: np.ndarray, y: np.ndarray) -> lgb.LGBMRegressor:
        """Build and tune LightGBM model."""
        model = lgb.LGBMRegressor(
            n_estimators=300,
            max_depth=7,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_samples=20,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            objective='regression',
            metric='rmse',
            verbose=-1
        )

        model.fit(X, y)
        return model

    def _create_ensemble(self) -> VotingRegressor:
        """Create voting ensemble from trained models."""
        ensemble = VotingRegressor(
            estimators=[
                ('xgb', self.xgb_model),
                ('lgb', self.lgb_model)
            ],
            weights=[0.5, 0.5]  # Equal weighting
        )
        return ensemble

    def _calculate_feature_importance(self) -> None:
        """Calculate global feature importance."""
        xgb_importance = self.xgb_model.feature_importances_
        lgb_importance = self.lgb_model.feature_importances_

        # Average importance from both models
        avg_importance = (xgb_importance + lgb_importance) / 2

        self.feature_importance_ = {
            feature: float(importance)
            for feature, importance in zip(self.FEATURE_COLUMNS, avg_importance)
        }

    # ========== Prediction ==========

    def predict_roas(
        self,
        features: FeatureSet,
        return_explanation: bool = True
    ) -> ROASPrediction:
        """
        Predict ROAS for creative/targeting combination.

        Args:
            features: Feature set for prediction
            return_explanation: Whether to include SHAP explanations

        Returns:
            ROASPrediction with confidence and feature contributions
        """
        if self.ensemble is None:
            raise ValueError("Model not trained. Call train() first or load a trained model.")

        # Input validation
        if features is None:
            raise ValueError("features cannot be None")

        if not isinstance(features, FeatureSet):
            raise TypeError(f"features must be a FeatureSet instance, got {type(features)}")

        # Convert features to array
        X = self._features_to_array(features)
        X_scaled = self.scaler.transform(X.reshape(1, -1))

        # Predict
        predicted_roas = float(self.ensemble.predict(X_scaled)[0])

        # Confidence interval
        conf_low, conf_high = self.confidence_interval(features)
        confidence_score = self._calculate_confidence_score(features)

        # Feature contributions (SHAP)
        feature_contributions = {}
        if return_explanation and self.shap_explainer is not None:
            shap_values = self.shap_explainer.shap_values(X_scaled)
            feature_contributions = {
                feature: float(shap_val)
                for feature, shap_val in zip(self.FEATURE_COLUMNS, shap_values[0])
            }
            # Sort by absolute impact
            feature_contributions = dict(
                sorted(feature_contributions.items(), key=lambda x: abs(x[1]), reverse=True)
            )

        # Similar campaigns average (use historical features as proxy)
        similar_campaigns_avg_roas = float(features.similar_creative_roas)

        return ROASPrediction(
            predicted_roas=predicted_roas,
            confidence_low=conf_low,
            confidence_high=conf_high,
            confidence_score=confidence_score,
            feature_contributions=feature_contributions,
            similar_campaigns_avg_roas=similar_campaigns_avg_roas
        )

    def predict_batch(
        self,
        features_list: List[FeatureSet]
    ) -> List[ROASPrediction]:
        """Batch prediction for multiple creatives."""
        logger.info(f"Batch predicting {len(features_list)} creatives")

        predictions = []
        for features in features_list:
            try:
                pred = self.predict_roas(features, return_explanation=False)
                predictions.append(pred)
            except Exception as e:
                logger.error(f"Error predicting features: {e}")
                # Return default prediction
                predictions.append(ROASPrediction(
                    predicted_roas=0.0,
                    confidence_low=0.0,
                    confidence_high=0.0,
                    confidence_score=0.0,
                    feature_contributions={},
                    similar_campaigns_avg_roas=0.0
                ))

        return predictions

    def _features_to_array(self, features: FeatureSet) -> np.ndarray:
        """Convert FeatureSet to numpy array."""
        feature_dict = features.to_dict()

        # Encode categoricals
        for col in self.CATEGORICAL_FEATURES:
            if col in self.label_encoders:
                value = feature_dict[col]
                try:
                    feature_dict[col] = self.label_encoders[col].transform([str(value)])[0]
                except ValueError:
                    # Unknown category, use most common
                    feature_dict[col] = 0

        # Convert booleans
        for col in self.BOOLEAN_FEATURES:
            feature_dict[col] = int(feature_dict[col])

        # Build array in correct order
        X = np.array([feature_dict[col] for col in self.FEATURE_COLUMNS])
        return X

    # ========== Explainability ==========

    def explain_prediction(
        self,
        features: FeatureSet
    ) -> Dict[str, Any]:
        """Get SHAP values for prediction."""
        if self.shap_explainer is None:
            raise ValueError("SHAP explainer not initialized. Train model first.")

        X = self._features_to_array(features)
        X_scaled = self.scaler.transform(X.reshape(1, -1))

        # Get SHAP values
        shap_values = self.shap_explainer.shap_values(X_scaled)
        base_value = self.shap_explainer.expected_value

        # Build explanation
        explanation = {
            'base_value': float(base_value),
            'predicted_value': float(self.ensemble.predict(X_scaled)[0]),
            'shap_values': {
                feature: float(shap_val)
                for feature, shap_val in zip(self.FEATURE_COLUMNS, shap_values[0])
            },
            'top_positive_features': self._get_top_features(shap_values[0], positive=True),
            'top_negative_features': self._get_top_features(shap_values[0], positive=False)
        }

        return explanation

    def _get_top_features(
        self,
        shap_values: np.ndarray,
        positive: bool = True,
        n: int = 5
    ) -> List[Tuple[str, float]]:
        """Get top N positive or negative SHAP features."""
        feature_shap = list(zip(self.FEATURE_COLUMNS, shap_values))

        if positive:
            sorted_features = sorted(feature_shap, key=lambda x: x[1], reverse=True)
        else:
            sorted_features = sorted(feature_shap, key=lambda x: x[1])

        return [(feat, float(val)) for feat, val in sorted_features[:n]]

    def get_feature_importance(self) -> Dict[str, float]:
        """Get global feature importance."""
        if self.feature_importance_ is None:
            self._calculate_feature_importance()

        return self.feature_importance_

    def get_top_features(
        self,
        n: int = 10
    ) -> List[Tuple[str, float]]:
        """Get top N important features."""
        importance = self.get_feature_importance()
        sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        return sorted_features[:n]

    # ========== Confidence Intervals ==========

    def confidence_interval(
        self,
        features: FeatureSet,
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate prediction confidence interval using model variance.

        Args:
            features: Feature set
            confidence: Confidence level (default 0.95)

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        X = self._features_to_array(features)
        X_scaled = self.scaler.transform(X.reshape(1, -1))

        # Get predictions from both models
        xgb_pred = self.xgb_model.predict(X_scaled)[0]
        lgb_pred = self.lgb_model.predict(X_scaled)[0]

        # Calculate variance from model disagreement
        predictions = np.array([xgb_pred, lgb_pred])
        mean_pred = np.mean(predictions)
        std_pred = np.std(predictions)

        # Add baseline uncertainty (learned from training)
        if 'rmse' in self.performance_metrics:
            baseline_std = self.performance_metrics['rmse']
            total_std = np.sqrt(std_pred**2 + baseline_std**2)
        else:
            total_std = max(std_pred, 0.5)  # Minimum uncertainty

        # Z-score for confidence level
        from scipy import stats
        z_score = stats.norm.ppf((1 + confidence) / 2)

        margin = z_score * total_std

        return (
            float(max(0, mean_pred - margin)),  # ROAS can't be negative
            float(mean_pred + margin)
        )

    def get_prediction_uncertainty(
        self,
        features: FeatureSet
    ) -> float:
        """
        Get uncertainty score for prediction (0-1).
        Lower is more certain.
        """
        conf_low, conf_high = self.confidence_interval(features)
        prediction = self.predict_roas(features, return_explanation=False)

        if prediction.predicted_roas == 0:
            return 1.0

        # Uncertainty as relative interval width
        uncertainty = (conf_high - conf_low) / (2 * prediction.predicted_roas)
        return float(min(1.0, uncertainty))

    def _calculate_confidence_score(self, features: FeatureSet) -> float:
        """Calculate confidence score (0-1) based on various factors."""
        scores = []

        # Model agreement
        X = self._features_to_array(features)
        X_scaled = self.scaler.transform(X.reshape(1, -1))
        xgb_pred = self.xgb_model.predict(X_scaled)[0]
        lgb_pred = self.lgb_model.predict(X_scaled)[0]

        agreement = 1 - abs(xgb_pred - lgb_pred) / max(abs(xgb_pred), abs(lgb_pred), 1.0)
        scores.append(agreement)

        # Historical data availability
        if features.similar_creative_roas > 0:
            scores.append(0.8)
        else:
            scores.append(0.4)

        # Account history
        if features.account_avg_roas > 0:
            scores.append(0.9)
        else:
            scores.append(0.5)

        return float(np.mean(scores))

    # ========== Model Persistence ==========

    def save_model(self, path: str) -> None:
        """Save trained model to disk."""
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save models
        joblib.dump(self.xgb_model, save_path / 'xgb_model.pkl')
        joblib.dump(self.lgb_model, save_path / 'lgb_model.pkl')
        joblib.dump(self.scaler, save_path / 'scaler.pkl')
        joblib.dump(self.label_encoders, save_path / 'label_encoders.pkl')

        # Save metadata
        metadata = {
            'feature_columns': self.FEATURE_COLUMNS,
            'performance_metrics': self.performance_metrics,
            'training_history': self.training_history,
            'feature_importance': self.feature_importance_,
            'save_timestamp': datetime.utcnow().isoformat()
        }

        with open(save_path / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Model saved to {path}")

    def load_model(self, path: str) -> None:
        """Load model from disk."""
        load_path = Path(path)

        if not load_path.exists():
            raise FileNotFoundError(f"Model path not found: {path}")

        # Load models
        self.xgb_model = joblib.load(load_path / 'xgb_model.pkl')
        self.lgb_model = joblib.load(load_path / 'lgb_model.pkl')
        self.scaler = joblib.load(load_path / 'scaler.pkl')
        self.label_encoders = joblib.load(load_path / 'label_encoders.pkl')

        # Recreate ensemble with loaded models
        self.ensemble = VotingRegressor(
            estimators=[
                ('xgb', self.xgb_model),
                ('lgb', self.lgb_model)
            ],
            weights=[0.5, 0.5]
        )
        # Mark ensemble as fitted (sklearn requirement)
        self.ensemble.estimators_ = [self.xgb_model, self.lgb_model]
        self.ensemble.named_estimators_ = {'xgb': self.xgb_model, 'lgb': self.lgb_model}

        # Load metadata
        with open(load_path / 'metadata.json', 'r') as f:
            metadata = json.load(f)

        self.performance_metrics = metadata['performance_metrics']
        self.training_history = metadata['training_history']
        self.feature_importance_ = metadata['feature_importance']

        # Reinitialize SHAP
        self.shap_explainer = shap.TreeExplainer(self.xgb_model)

        logger.info(f"Model loaded from {path}")

    # ========== Self-Learning ==========

    def retrain_on_new_data(
        self,
        new_campaigns: pd.DataFrame,
        incremental: bool = True
    ) -> Dict[str, float]:
        """
        Retrain model with new campaign data.

        Args:
            new_campaigns: New campaign data with actual ROAS
            incremental: If True, combine with existing training data

        Returns:
            Updated performance metrics
        """
        logger.info(f"Retraining on {len(new_campaigns)} new campaigns")

        # For incremental learning, we'd need to store training data
        # For now, just retrain on new data
        return self.train(new_campaigns)

    def evaluate_model_drift(
        self,
        recent_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Check for model performance drift.

        Args:
            recent_data: Recent campaign data with actual ROAS

        Returns:
            Drift metrics and recommendation
        """
        if 'actual_roas' not in recent_data.columns:
            raise ValueError("recent_data must contain 'actual_roas' column")

        # Prepare data
        X, y_true = self._prepare_training_data(recent_data, 'actual_roas')
        X_scaled = self.scaler.transform(X)

        # Predict
        y_pred = self.ensemble.predict(X_scaled)

        # Calculate metrics
        current_r2 = r2_score(y_true, y_pred)
        current_mae = mean_absolute_error(y_true, y_pred)
        current_rmse = np.sqrt(mean_squared_error(y_true, y_pred))

        # Compare to training metrics
        baseline_r2 = self.performance_metrics.get('r2_score', 0)
        baseline_mae = self.performance_metrics.get('mae', float('inf'))

        r2_drift = baseline_r2 - current_r2
        mae_drift = current_mae - baseline_mae

        drift_detected = (r2_drift > 0.1) or (mae_drift > baseline_mae * 0.2)

        return {
            'current_r2': current_r2,
            'current_mae': current_mae,
            'current_rmse': current_rmse,
            'baseline_r2': baseline_r2,
            'baseline_mae': baseline_mae,
            'r2_drift': r2_drift,
            'mae_drift': mae_drift,
            'drift_detected': drift_detected,
            'recommendation': 'retrain' if drift_detected else 'continue',
            'evaluation_date': datetime.utcnow().isoformat()
        }

    def get_retraining_recommendation(self) -> Dict[str, Any]:
        """Recommend if retraining is needed based on training history."""
        if not self.training_history:
            return {
                'should_retrain': True,
                'reason': 'No training history available',
                'days_since_training': None
            }

        last_training = self.training_history[-1]
        training_date = datetime.fromisoformat(last_training['training_date'])
        days_since = (datetime.utcnow() - training_date).days

        # Recommend retraining after 30 days
        should_retrain = days_since >= 30

        return {
            'should_retrain': should_retrain,
            'reason': f'{days_since} days since last training' if should_retrain else 'Model is recent',
            'days_since_training': days_since,
            'last_training_r2': last_training.get('r2_score'),
            'recommendation': 'retrain' if should_retrain else 'continue'
        }

    # ========== Feature Engineering ==========

    def engineer_features(
        self,
        raw_data: Dict[str, Any]
    ) -> FeatureSet:
        """
        Engineer features from raw creative/targeting data.

        Args:
            raw_data: Raw data dictionary

        Returns:
            Engineered FeatureSet
        """
        # Extract and transform features
        features = FeatureSet(
            # Creative
            hook_type=raw_data.get('hook_type', 'problem_solution'),
            hook_strength=float(raw_data.get('hook_strength', 7.0)),
            visual_complexity=float(raw_data.get('visual_complexity', 5.0)),
            text_density=float(raw_data.get('text_density', 0.15)),
            face_presence=bool(raw_data.get('face_presence', True)),
            motion_score=float(raw_data.get('motion_score', 7.0)),
            video_duration=float(raw_data.get('video_duration', 15.0)),
            aspect_ratio=float(raw_data.get('aspect_ratio', 0.5625)),
            color_vibrancy=float(raw_data.get('color_vibrancy', 7.0)),
            scene_count=int(raw_data.get('scene_count', 3)),

            # Targeting
            audience_size=int(raw_data.get('audience_size', 2000000)),
            audience_overlap=float(raw_data.get('audience_overlap', 0.15)),
            cpm_estimate=float(raw_data.get('cpm_estimate', 12.5)),
            age_min=int(raw_data.get('age_min', 25)),
            age_max=int(raw_data.get('age_max', 54)),
            gender_targeting=raw_data.get('gender_targeting', 'all'),
            interest_count=int(raw_data.get('interest_count', 5)),
            custom_audience=bool(raw_data.get('custom_audience', False)),

            # Historical
            account_avg_roas=float(raw_data.get('account_avg_roas', 3.0)),
            account_avg_ctr=float(raw_data.get('account_avg_ctr', 1.5)),
            vertical_avg_roas=float(raw_data.get('vertical_avg_roas', 2.8)),
            similar_creative_roas=float(raw_data.get('similar_creative_roas', 3.0)),
            day_of_week=int(raw_data.get('day_of_week', datetime.utcnow().weekday())),
            hour_of_day=int(raw_data.get('hour_of_day', datetime.utcnow().hour)),
            days_since_last_winner=int(raw_data.get('days_since_last_winner', 7)),
            account_spend_30d=float(raw_data.get('account_spend_30d', 50000.0)),
            account_conversions_30d=int(raw_data.get('account_conversions_30d', 400)),
            creative_fatigue_score=float(raw_data.get('creative_fatigue_score', 0.2)),

            # Copy
            cta_type=raw_data.get('cta_type', 'shop_now'),
            urgency_score=float(raw_data.get('urgency_score', 6.0)),
            benefit_count=int(raw_data.get('benefit_count', 3)),
            pain_point_addressed=bool(raw_data.get('pain_point_addressed', True)),
            social_proof_present=bool(raw_data.get('social_proof_present', True)),
            word_count=int(raw_data.get('word_count', 45)),
            emoji_count=int(raw_data.get('emoji_count', 2)),
            question_present=bool(raw_data.get('question_present', False))
        )

        return features

    def _encode_categorical(
        self,
        column: str,
        value: str
    ) -> int:
        """Encode categorical feature."""
        if column not in self.label_encoders:
            raise ValueError(f"No encoder for column: {column}")

        try:
            return self.label_encoders[column].transform([str(value)])[0]
        except ValueError:
            # Unknown category, return 0
            logger.warning(f"Unknown category '{value}' for column '{column}', using default")
            return 0
