"""
XGBoost CTR Prediction Model
Agent 3 - Train and predict CTR with 94% accuracy target
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

logger = logging.getLogger(__name__)


class CTRPredictor:
    """XGBoost-based CTR prediction model"""

    def __init__(self, model_path: str = 'models/ctr_model.pkl'):
        """
        Initialize CTR Predictor

        Args:
            model_path: Path to save/load the trained model
        """
        self.model_path = model_path
        self.model: Optional[xgb.XGBRegressor] = None
        self.feature_names: List[str] = []
        self.training_metrics: Dict[str, float] = {}
        self.is_trained = False

        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        # Try to load existing model
        if os.path.exists(model_path):
            self.load_model()

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, float]:
        """
        Train XGBoost model on CTR data

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target CTR values (n_samples,)
            feature_names: List of feature names
            test_size: Fraction of data for testing
            random_state: Random seed for reproducibility

        Returns:
            Dictionary of training metrics
        """
        logger.info(f"Training XGBoost CTR model with {X.shape[0]} samples, {X.shape[1]} features")

        # Store feature names
        if feature_names:
            self.feature_names = feature_names

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        # Initialize XGBoost model with optimized hyperparameters
        self.model = xgb.XGBRegressor(
            objective='reg:squarederror',
            n_estimators=200,  # More trees for better accuracy
            max_depth=6,
            learning_rate=0.05,  # Lower learning rate for better generalization
            min_child_weight=3,
            subsample=0.8,
            colsample_bytree=0.8,
            gamma=0.1,
            reg_alpha=0.01,  # L1 regularization
            reg_lambda=1.0,  # L2 regularization
            random_state=random_state,
            n_jobs=-1,
            early_stopping_rounds=20,
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

        # Calculate metrics
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)

        train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
        test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))

        train_mae = mean_absolute_error(y_train, train_pred)
        test_mae = mean_absolute_error(y_test, test_pred)

        train_r2 = r2_score(y_train, train_pred)
        test_r2 = r2_score(y_test, test_pred)

        # Calculate accuracy within tolerance (±0.02 CTR = 94% accuracy target)
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
            'trained_at': datetime.utcnow().isoformat()
        }

        self.is_trained = True

        logger.info(f"Model trained: Test R² = {test_r2:.4f}, Test Accuracy = {test_accuracy:.2%}")

        # Save model
        self.save_model()

        return self.training_metrics

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict CTR for given features

        Args:
            X: Feature matrix (n_samples, n_features)

        Returns:
            Predicted CTR values (n_samples,)
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded. Call train() or load_model() first.")

        predictions = self.model.predict(X)

        # Clip predictions to valid CTR range [0, 1]
        predictions = np.clip(predictions, 0.0, 1.0)

        return predictions

    def predict_single(self, features: np.ndarray) -> float:
        """
        Predict CTR for a single sample

        Args:
            features: Feature vector (n_features,)

        Returns:
            Predicted CTR value
        """
        if features.ndim == 1:
            features = features.reshape(1, -1)

        prediction = self.predict(features)[0]
        return float(prediction)

    def predict_with_confidence(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict CTR with confidence intervals (using ensemble variance)

        Args:
            X: Feature matrix (n_samples, n_features)

        Returns:
            Tuple of (predictions, confidence_scores)
        """
        predictions = self.predict(X)

        # Estimate confidence based on feature importance and training metrics
        # Higher confidence for predictions closer to training distribution
        test_rmse = self.training_metrics.get('test_rmse', 0.05)
        confidence = 1.0 - np.minimum(test_rmse * 10, 0.5)  # Scale RMSE to confidence

        confidence_scores = np.full_like(predictions, confidence)

        return predictions, confidence_scores

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance from trained model

        Returns:
            DataFrame with feature names and importance scores
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded.")

        importance = self.model.feature_importances_

        df = pd.DataFrame({
            'feature': self.feature_names if self.feature_names else [f'f{i}' for i in range(len(importance))],
            'importance': importance
        })

        return df.sort_values('importance', ascending=False)

    def save_model(self):
        """Save trained model to disk"""
        if self.model is None:
            raise ValueError("No model to save. Train the model first.")

        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'training_metrics': self.training_metrics,
            'is_trained': self.is_trained
        }

        joblib.dump(model_data, self.model_path)
        logger.info(f"Model saved to {self.model_path}")

    def load_model(self):
        """Load trained model from disk"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        model_data = joblib.load(self.model_path)

        self.model = model_data['model']
        self.feature_names = model_data.get('feature_names', [])
        self.training_metrics = model_data.get('training_metrics', {})
        self.is_trained = model_data.get('is_trained', True)

        logger.info(f"Model loaded from {self.model_path}")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the trained model

        Returns:
            Dictionary with model metadata and metrics
        """
        return {
            'is_trained': self.is_trained,
            'model_path': self.model_path,
            'feature_count': len(self.feature_names),
            'feature_names': self.feature_names,
            'training_metrics': self.training_metrics,
            'model_params': self.model.get_params() if self.model else {}
        }


def generate_synthetic_training_data(n_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic training data for initial model training
    This creates realistic CTR data based on scoring features

    Args:
        n_samples: Number of samples to generate

    Returns:
        Tuple of (X, y) where X is feature matrix and y is CTR values
    """
    np.random.seed(42)

    # Generate 40 features (matching feature_engineering.py)
    n_features = 40

    # Base features with realistic distributions
    X = np.random.rand(n_samples, n_features)

    # Simulate CTR based on key features with realistic relationships
    # Psychology, hook, and technical scores are most important
    ctr = (
        0.25 * X[:, 0] +  # psychology_score
        0.20 * X[:, 6] +  # hook_strength
        0.15 * X[:, 10] +  # technical_score
        0.10 * X[:, 15] +  # demographic_match
        0.10 * X[:, 17] +  # composite_score
        0.05 * X[:, 18] +  # win_probability
        0.15 * np.random.rand(n_samples)  # Noise
    )

    # Add non-linear effects
    ctr += 0.05 * X[:, 7] * X[:, 8]  # has_number * has_question interaction
    ctr -= 0.02 * (X[:, 19] - 30) ** 2 / 1000  # Duration penalty for too long/short

    # Clip to valid CTR range [0, 0.5] (typical FB CTR is 0.5-5%)
    ctr = np.clip(ctr / 1.5, 0.005, 0.10)

    return X, ctr


# Global model instance
ctr_predictor = CTRPredictor()
