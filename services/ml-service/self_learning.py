"""
Self-Learning Feedback Loop for ML Models

This module implements automated learning from prediction outcomes, drift detection,
A/B testing, and automated retraining triggers for ML models.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from scipy import stats
from scipy.stats import ks_2samp, ttest_ind
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
from collections import defaultdict
import sys
import os

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'shared'))

from sqlalchemy import select, and_, update, delete
from db.models import (
    PredictionRecord, ModelPerformanceHistory as ModelPerformanceHistoryModel,
    DriftReport as DriftReportModel, ABTest as ABTestModel,
    FeatureImportanceHistory as FeatureImportanceHistoryModel,
    LearningAlert as LearningAlertModel
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelType(Enum):
    ROAS_PREDICTOR = "roas_predictor"
    HOOK_CLASSIFIER = "hook_classifier"
    VISUAL_PATTERN = "visual_pattern"
    CTR_PREDICTOR = "ctr_predictor"


class DriftType(Enum):
    DATA_DRIFT = "data_drift"
    CONCEPT_DRIFT = "concept_drift"
    PREDICTION_DRIFT = "prediction_drift"


@dataclass
class PredictionOutcome:
    prediction_id: str
    model_type: ModelType
    predicted_value: float
    actual_value: float
    features: Dict[str, Any]
    timestamp: datetime
    error: float
    error_percentage: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'prediction_id': self.prediction_id,
            'model_type': self.model_type.value,
            'predicted_value': self.predicted_value,
            'actual_value': self.actual_value,
            'features': self.features,
            'timestamp': self.timestamp.isoformat(),
            'error': self.error,
            'error_percentage': self.error_percentage
        }


@dataclass
class DriftReport:
    drift_type: DriftType
    severity: str  # low, medium, high, critical
    affected_features: List[str]
    statistical_tests: Dict[str, Any]
    recommendation: str
    detected_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'drift_type': self.drift_type.value,
            'severity': self.severity,
            'affected_features': self.affected_features,
            'statistical_tests': self.statistical_tests,
            'recommendation': self.recommendation,
            'detected_at': self.detected_at.isoformat()
        }


@dataclass
class ModelPerformance:
    model_type: ModelType
    mae: float
    rmse: float
    r2: float
    mape: float
    sample_count: int
    last_updated: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'model_type': self.model_type.value,
            'mae': self.mae,
            'rmse': self.rmse,
            'r2': self.r2,
            'mape': self.mape,
            'sample_count': self.sample_count,
            'last_updated': self.last_updated.isoformat()
        }


class SelfLearningEngine:
    """Automated learning from prediction outcomes."""

    def __init__(
        self,
        database_session,
        model_registry: Dict[str, Any]
    ):
        """Initialize with database session and models."""
        self.db_session = database_session
        self.model_registry = model_registry

        logger.info("SelfLearningEngine initialized with PostgreSQL persistence")

    # Outcome Collection
    async def collect_prediction_outcomes(
        self,
        model_type: ModelType = None,
        days_back: int = 7
    ) -> List[PredictionOutcome]:
        """Collect prediction outcomes for analysis."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)

            # Query database for outcomes
            query = select(PredictionRecord).where(
                and_(
                    PredictionRecord.outcome_recorded_at >= cutoff_date,
                    PredictionRecord.actual_value.isnot(None)
                )
            )

            if model_type:
                query = query.where(PredictionRecord.model_type == model_type.value)

            result = await self.db_session.execute(query)
            db_outcomes = result.scalars().all()

            # Convert to PredictionOutcome objects
            filtered_outcomes = []
            for db_outcome in db_outcomes:
                outcome = PredictionOutcome(
                    prediction_id=db_outcome.prediction_id,
                    model_type=ModelType(db_outcome.model_type),
                    predicted_value=db_outcome.predicted_value,
                    actual_value=db_outcome.actual_value,
                    features=db_outcome.features,
                    timestamp=db_outcome.outcome_recorded_at,
                    error=db_outcome.error,
                    error_percentage=db_outcome.error_percentage
                )
                filtered_outcomes.append(outcome)

            logger.info(f"Collected {len(filtered_outcomes)} outcomes for {model_type or 'all models'} from last {days_back} days")
            return filtered_outcomes

        except Exception as e:
            logger.error(f"Error collecting prediction outcomes: {str(e)}")
            raise

    async def record_outcome(
        self,
        prediction_id: str,
        actual_value: float
    ) -> PredictionOutcome:
        """Record actual outcome for prediction."""
        try:
            # Find prediction in database
            result = await self.db_session.execute(
                select(PredictionRecord).where(PredictionRecord.prediction_id == prediction_id)
            )
            db_prediction = result.scalar_one_or_none()

            if not db_prediction:
                raise ValueError(f"Prediction {prediction_id} not found")

            predicted_value = db_prediction.predicted_value

            # Calculate error metrics
            error = actual_value - predicted_value
            error_percentage = (error / actual_value * 100) if actual_value != 0 else 0

            # Update prediction record with outcome
            db_prediction.actual_value = actual_value
            db_prediction.error = error
            db_prediction.error_percentage = error_percentage
            db_prediction.outcome_recorded_at = datetime.now()

            await self.db_session.commit()

            outcome = PredictionOutcome(
                prediction_id=prediction_id,
                model_type=ModelType(db_prediction.model_type),
                predicted_value=predicted_value,
                actual_value=actual_value,
                features=db_prediction.features,
                timestamp=db_prediction.outcome_recorded_at,
                error=error,
                error_percentage=error_percentage
            )

            logger.info(f"Recorded outcome for prediction {prediction_id}: error={error:.2f}")

            return outcome

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error recording outcome: {str(e)}")
            raise

    # Error Analysis
    def calculate_prediction_error(
        self,
        prediction_id: str
    ) -> Dict[str, float]:
        """Calculate error metrics for prediction."""
        try:
            outcome = next((o for o in self.outcomes if o.prediction_id == prediction_id), None)

            if not outcome:
                raise ValueError(f"No outcome found for prediction {prediction_id}")

            absolute_error = abs(outcome.error)
            squared_error = outcome.error ** 2

            return {
                'error': outcome.error,
                'absolute_error': absolute_error,
                'squared_error': squared_error,
                'percentage_error': outcome.error_percentage,
                'absolute_percentage_error': abs(outcome.error_percentage)
            }

        except Exception as e:
            logger.error(f"Error calculating prediction error: {str(e)}")
            raise

    def analyze_error_distribution(
        self,
        model_type: ModelType,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Analyze error distribution over time."""
        try:
            outcomes = self.collect_prediction_outcomes(model_type, days_back)

            if not outcomes:
                return {
                    'sample_count': 0,
                    'error': 'No outcomes available'
                }

            errors = np.array([o.error for o in outcomes])
            abs_errors = np.abs(errors)

            # Calculate distribution statistics
            distribution = {
                'sample_count': len(outcomes),
                'mean_error': float(np.mean(errors)),
                'median_error': float(np.median(errors)),
                'std_error': float(np.std(errors)),
                'mean_absolute_error': float(np.mean(abs_errors)),
                'percentiles': {
                    '25th': float(np.percentile(errors, 25)),
                    '50th': float(np.percentile(errors, 50)),
                    '75th': float(np.percentile(errors, 75)),
                    '90th': float(np.percentile(errors, 90)),
                    '95th': float(np.percentile(errors, 95))
                },
                'skewness': float(stats.skew(errors)),
                'kurtosis': float(stats.kurtosis(errors))
            }

            # Test for normality
            if len(errors) >= 8:
                _, p_value = stats.shapiro(errors)
                distribution['normality_test'] = {
                    'test': 'Shapiro-Wilk',
                    'p_value': float(p_value),
                    'is_normal': p_value > 0.05
                }

            logger.info(f"Analyzed error distribution for {model_type.value}: MAE={distribution['mean_absolute_error']:.4f}")
            return distribution

        except Exception as e:
            logger.error(f"Error analyzing error distribution: {str(e)}")
            raise

    def identify_systematic_errors(
        self,
        model_type: ModelType
    ) -> List[Dict[str, Any]]:
        """Identify systematic prediction errors."""
        try:
            outcomes = self.collect_prediction_outcomes(model_type, days_back=30)

            if len(outcomes) < 10:
                return []

            systematic_errors = []

            # Group by feature values to find patterns
            feature_groups = defaultdict(list)
            for outcome in outcomes:
                for feature_name, feature_value in outcome.features.items():
                    if isinstance(feature_value, (int, float, bool, str)):
                        feature_groups[feature_name].append({
                            'value': feature_value,
                            'error': outcome.error,
                            'error_pct': outcome.error_percentage
                        })

            # Analyze each feature for systematic bias
            for feature_name, values in feature_groups.items():
                if len(values) < 5:
                    continue

                errors = [v['error'] for v in values]
                mean_error = np.mean(errors)
                std_error = np.std(errors)

                # Check if mean error is significantly different from zero
                if len(errors) >= 3:
                    t_stat, p_value = stats.ttest_1samp(errors, 0)

                    if p_value < 0.05 and abs(mean_error) > std_error * 0.5:
                        systematic_errors.append({
                            'feature': feature_name,
                            'mean_error': float(mean_error),
                            'std_error': float(std_error),
                            'sample_count': len(errors),
                            't_statistic': float(t_stat),
                            'p_value': float(p_value),
                            'bias_direction': 'overestimation' if mean_error > 0 else 'underestimation',
                            'severity': 'high' if abs(mean_error) > std_error else 'medium'
                        })

            logger.info(f"Identified {len(systematic_errors)} systematic errors for {model_type.value}")
            return systematic_errors

        except Exception as e:
            logger.error(f"Error identifying systematic errors: {str(e)}")
            raise

    # Drift Detection
    def identify_feature_drift(
        self,
        model_type: ModelType,
        reference_period_days: int = 30,
        current_period_days: int = 7
    ) -> DriftReport:
        """Detect feature distribution drift."""
        try:
            # Get reference and current data
            reference_cutoff = datetime.now() - timedelta(days=reference_period_days)
            current_cutoff = datetime.now() - timedelta(days=current_period_days)

            reference_outcomes = [
                o for o in self.outcomes
                if o.model_type == model_type and o.timestamp < current_cutoff
            ]
            current_outcomes = [
                o for o in self.outcomes
                if o.model_type == model_type and o.timestamp >= current_cutoff
            ]

            if len(reference_outcomes) < 10 or len(current_outcomes) < 10:
                return DriftReport(
                    drift_type=DriftType.DATA_DRIFT,
                    severity='low',
                    affected_features=[],
                    statistical_tests={'error': 'Insufficient data'},
                    recommendation='Collect more data for drift detection',
                    detected_at=datetime.now()
                )

            # Extract features
            reference_features = defaultdict(list)
            current_features = defaultdict(list)

            for outcome in reference_outcomes:
                for fname, fvalue in outcome.features.items():
                    if isinstance(fvalue, (int, float)):
                        reference_features[fname].append(fvalue)

            for outcome in current_outcomes:
                for fname, fvalue in outcome.features.items():
                    if isinstance(fvalue, (int, float)):
                        current_features[fname].append(fvalue)

            # Run KS test for each feature
            affected_features = []
            statistical_tests = {}

            for fname in reference_features.keys():
                if fname in current_features:
                    ref_data = np.array(reference_features[fname])
                    cur_data = np.array(current_features[fname])

                    ks_stat, p_value = self.run_ks_test(ref_data, cur_data)

                    statistical_tests[fname] = {
                        'ks_statistic': ks_stat,
                        'p_value': p_value,
                        'drifted': p_value < 0.05
                    }

                    if p_value < 0.05:
                        affected_features.append(fname)

            # Determine severity
            drift_ratio = len(affected_features) / max(len(reference_features), 1)
            if drift_ratio > 0.5:
                severity = 'critical'
                recommendation = 'Immediate model retraining required'
            elif drift_ratio > 0.3:
                severity = 'high'
                recommendation = 'Schedule model retraining soon'
            elif drift_ratio > 0.1:
                severity = 'medium'
                recommendation = 'Monitor closely and consider retraining'
            else:
                severity = 'low'
                recommendation = 'Continue monitoring'

            report = DriftReport(
                drift_type=DriftType.DATA_DRIFT,
                severity=severity,
                affected_features=affected_features,
                statistical_tests=statistical_tests,
                recommendation=recommendation,
                detected_at=datetime.now()
            )

            self.drift_reports.append(report)
            logger.info(f"Feature drift detected: {len(affected_features)} features affected, severity={severity}")

            return report

        except Exception as e:
            logger.error(f"Error identifying feature drift: {str(e)}")
            raise

    def detect_concept_drift(
        self,
        model_type: ModelType
    ) -> DriftReport:
        """Detect concept drift (relationship changes)."""
        try:
            # Compare model performance over time windows
            recent_outcomes = self.collect_prediction_outcomes(model_type, days_back=7)
            older_outcomes = [
                o for o in self.outcomes
                if o.model_type == model_type and
                o.timestamp < (datetime.now() - timedelta(days=7)) and
                o.timestamp >= (datetime.now() - timedelta(days=30))
            ]

            if len(recent_outcomes) < 10 or len(older_outcomes) < 10:
                return DriftReport(
                    drift_type=DriftType.CONCEPT_DRIFT,
                    severity='low',
                    affected_features=[],
                    statistical_tests={'error': 'Insufficient data'},
                    recommendation='Collect more data for concept drift detection',
                    detected_at=datetime.now()
                )

            # Calculate error metrics for both periods
            recent_errors = np.array([abs(o.error) for o in recent_outcomes])
            older_errors = np.array([abs(o.error) for o in older_outcomes])

            # Statistical tests
            t_stat, p_value = ttest_ind(recent_errors, older_errors)
            ks_stat, ks_p_value = ks_2samp(recent_errors, older_errors)

            # Compare means
            recent_mae = np.mean(recent_errors)
            older_mae = np.mean(older_errors)
            performance_change = (recent_mae - older_mae) / older_mae * 100

            statistical_tests = {
                't_test': {
                    'statistic': float(t_stat),
                    'p_value': float(p_value)
                },
                'ks_test': {
                    'statistic': float(ks_stat),
                    'p_value': float(ks_p_value)
                },
                'recent_mae': float(recent_mae),
                'older_mae': float(older_mae),
                'performance_change_pct': float(performance_change)
            }

            # Determine severity based on performance degradation
            drifted = p_value < 0.05 and performance_change > 0

            if drifted:
                if performance_change > 50:
                    severity = 'critical'
                    recommendation = 'Immediate model retraining required - severe performance degradation'
                elif performance_change > 25:
                    severity = 'high'
                    recommendation = 'Model retraining recommended - significant performance drop'
                elif performance_change > 10:
                    severity = 'medium'
                    recommendation = 'Monitor and consider retraining'
                else:
                    severity = 'low'
                    recommendation = 'Continue monitoring'
            else:
                severity = 'low'
                recommendation = 'No significant concept drift detected'

            report = DriftReport(
                drift_type=DriftType.CONCEPT_DRIFT,
                severity=severity,
                affected_features=['model_performance'],
                statistical_tests=statistical_tests,
                recommendation=recommendation,
                detected_at=datetime.now()
            )

            self.drift_reports.append(report)
            logger.info(f"Concept drift check: performance change={performance_change:.2f}%, severity={severity}")

            return report

        except Exception as e:
            logger.error(f"Error detecting concept drift: {str(e)}")
            raise

    def detect_prediction_drift(
        self,
        model_type: ModelType
    ) -> DriftReport:
        """Detect prediction distribution drift."""
        try:
            recent_outcomes = self.collect_prediction_outcomes(model_type, days_back=7)
            older_outcomes = [
                o for o in self.outcomes
                if o.model_type == model_type and
                o.timestamp < (datetime.now() - timedelta(days=7)) and
                o.timestamp >= (datetime.now() - timedelta(days=30))
            ]

            if len(recent_outcomes) < 10 or len(older_outcomes) < 10:
                return DriftReport(
                    drift_type=DriftType.PREDICTION_DRIFT,
                    severity='low',
                    affected_features=[],
                    statistical_tests={'error': 'Insufficient data'},
                    recommendation='Collect more data for prediction drift detection',
                    detected_at=datetime.now()
                )

            recent_predictions = np.array([o.predicted_value for o in recent_outcomes])
            older_predictions = np.array([o.predicted_value for o in older_outcomes])

            # Run KS test
            ks_stat, p_value = self.run_ks_test(older_predictions, recent_predictions)

            # Calculate distribution statistics
            recent_mean = np.mean(recent_predictions)
            older_mean = np.mean(older_predictions)
            mean_shift = (recent_mean - older_mean) / older_mean * 100

            statistical_tests = {
                'ks_statistic': float(ks_stat),
                'p_value': float(p_value),
                'recent_mean': float(recent_mean),
                'older_mean': float(older_mean),
                'mean_shift_pct': float(mean_shift),
                'recent_std': float(np.std(recent_predictions)),
                'older_std': float(np.std(older_predictions))
            }

            # Determine severity
            if p_value < 0.01:
                severity = 'high'
                recommendation = 'Significant prediction drift detected - investigate model behavior'
            elif p_value < 0.05:
                severity = 'medium'
                recommendation = 'Moderate prediction drift - monitor closely'
            else:
                severity = 'low'
                recommendation = 'No significant prediction drift'

            report = DriftReport(
                drift_type=DriftType.PREDICTION_DRIFT,
                severity=severity,
                affected_features=['predictions'],
                statistical_tests=statistical_tests,
                recommendation=recommendation,
                detected_at=datetime.now()
            )

            self.drift_reports.append(report)
            logger.info(f"Prediction drift: KS p-value={p_value:.4f}, mean shift={mean_shift:.2f}%")

            return report

        except Exception as e:
            logger.error(f"Error detecting prediction drift: {str(e)}")
            raise

    def run_ks_test(
        self,
        reference: np.ndarray,
        current: np.ndarray
    ) -> Tuple[float, float]:
        """Run Kolmogorov-Smirnov test for drift."""
        try:
            statistic, p_value = ks_2samp(reference, current)
            return float(statistic), float(p_value)
        except Exception as e:
            logger.error(f"Error running KS test: {str(e)}")
            raise

    # Model Retraining
    def trigger_model_retrain(
        self,
        model_type: ModelType,
        reason: str = "scheduled"
    ) -> Dict[str, Any]:
        """Trigger model retraining."""
        try:
            retrain_id = str(uuid.uuid4())

            # Collect training data
            outcomes = self.collect_prediction_outcomes(model_type, days_back=90)

            if len(outcomes) < 50:
                return {
                    'retrain_id': retrain_id,
                    'status': 'failed',
                    'reason': 'Insufficient training data',
                    'sample_count': len(outcomes)
                }

            # Get current performance baseline
            current_performance = self.get_model_performance(model_type, days_back=30)

            result = {
                'retrain_id': retrain_id,
                'model_type': model_type.value,
                'status': 'triggered',
                'reason': reason,
                'sample_count': len(outcomes),
                'current_performance': current_performance.to_dict() if current_performance else None,
                'triggered_at': datetime.now().isoformat()
            }

            logger.info(f"Triggered retraining for {model_type.value}: {reason}")
            return result

        except Exception as e:
            logger.error(f"Error triggering model retrain: {str(e)}")
            raise

    def should_retrain(
        self,
        model_type: ModelType
    ) -> Tuple[bool, str]:
        """Determine if model should be retrained."""
        try:
            reasons = []

            # Check for drift
            feature_drift = self.identify_feature_drift(model_type)
            if feature_drift.severity in ['high', 'critical']:
                reasons.append(f"Feature drift detected: {feature_drift.severity}")

            concept_drift = self.detect_concept_drift(model_type)
            if concept_drift.severity in ['high', 'critical']:
                reasons.append(f"Concept drift detected: {concept_drift.severity}")

            # Check performance degradation
            performance = self.get_model_performance(model_type, days_back=7)
            if performance and performance.mape > 30:  # More than 30% error
                reasons.append(f"High error rate: MAPE={performance.mape:.2f}%")

            # Check data availability
            outcomes = self.collect_prediction_outcomes(model_type, days_back=30)
            if len(outcomes) > 100:  # Enough new data for retraining
                reasons.append(f"Sufficient new data available: {len(outcomes)} samples")

            should_retrain = len(reasons) > 0
            reason = '; '.join(reasons) if reasons else 'No retraining needed'

            logger.info(f"Retrain check for {model_type.value}: {should_retrain} - {reason}")
            return should_retrain, reason

        except Exception as e:
            logger.error(f"Error checking if should retrain: {str(e)}")
            raise

    def get_retraining_recommendation(
        self,
        model_type: ModelType = None
    ) -> Dict[str, Any]:
        """Get retraining recommendations."""
        try:
            recommendations = {}

            model_types = [model_type] if model_type else list(ModelType)

            for mt in model_types:
                should_retrain, reason = self.should_retrain(mt)

                recommendations[mt.value] = {
                    'should_retrain': should_retrain,
                    'reason': reason,
                    'priority': 'high' if 'critical' in reason.lower() else 'medium' if should_retrain else 'low',
                    'checked_at': datetime.now().isoformat()
                }

            return recommendations

        except Exception as e:
            logger.error(f"Error getting retraining recommendation: {str(e)}")
            raise

    # A/B Testing Models
    async def ab_test_model_versions(
        self,
        model_type: ModelType,
        model_a_id: str,
        model_b_id: str,
        traffic_split: float = 0.5,
        duration_days: int = 7
    ) -> Dict[str, Any]:
        """A/B test two model versions."""
        try:
            test_id = str(uuid.uuid4())
            start_date = datetime.now()
            end_date = start_date + timedelta(days=duration_days)

            # Create A/B test in database
            db_test = ABTestModel(
                test_id=test_id,
                model_type=model_type.value,
                model_a_id=model_a_id,
                model_b_id=model_b_id,
                traffic_split=traffic_split,
                duration_days=duration_days,
                start_date=start_date,
                end_date=end_date,
                status='active',
                results={
                    'model_a': {'predictions': [], 'outcomes': []},
                    'model_b': {'predictions': [], 'outcomes': []}
                }
            )

            self.db_session.add(db_test)
            await self.db_session.commit()

            logger.info(f"Started A/B test {test_id} for {model_type.value}: {model_a_id} vs {model_b_id}")
            return {
                'test_id': test_id,
                'status': 'active',
                'config': {
                    'model_a_id': model_a_id,
                    'model_b_id': model_b_id,
                    'traffic_split': traffic_split,
                    'duration_days': duration_days,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            }

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error creating A/B test: {str(e)}")
            raise

    def get_ab_test_results(
        self,
        test_id: str
    ) -> Dict[str, Any]:
        """Get A/B test results."""
        try:
            if test_id not in self.ab_tests:
                raise ValueError(f"A/B test {test_id} not found")

            test = self.ab_tests[test_id]

            # Calculate metrics for both models
            results = {}
            for model_key in ['model_a', 'model_b']:
                outcomes = test['results'][model_key]['outcomes']

                if not outcomes:
                    results[model_key] = {
                        'sample_count': 0,
                        'status': 'insufficient_data'
                    }
                    continue

                predictions = [o['predicted'] for o in outcomes]
                actuals = [o['actual'] for o in outcomes]

                mae = mean_absolute_error(actuals, predictions)
                rmse = np.sqrt(mean_squared_error(actuals, predictions))

                # Calculate MAPE (avoiding division by zero)
                mape = np.mean([
                    abs((a - p) / a * 100) for a, p in zip(actuals, predictions) if a != 0
                ]) if actuals else 0

                results[model_key] = {
                    'sample_count': len(outcomes),
                    'mae': float(mae),
                    'rmse': float(rmse),
                    'mape': float(mape),
                    'mean_prediction': float(np.mean(predictions)),
                    'mean_actual': float(np.mean(actuals))
                }

            # Compare models
            if results.get('model_a', {}).get('sample_count', 0) > 0 and results.get('model_b', {}).get('sample_count', 0) > 0:
                model_a_errors = [o['actual'] - o['predicted'] for o in test['results']['model_a']['outcomes']]
                model_b_errors = [o['actual'] - o['predicted'] for o in test['results']['model_b']['outcomes']]

                # T-test for statistical significance
                t_stat, p_value = ttest_ind(model_a_errors, model_b_errors)

                results['comparison'] = {
                    't_statistic': float(t_stat),
                    'p_value': float(p_value),
                    'statistically_significant': p_value < 0.05,
                    'mae_difference': results['model_a']['mae'] - results['model_b']['mae'],
                    'winner': 'model_a' if results['model_a']['mae'] < results['model_b']['mae'] else 'model_b'
                }

            return {
                'test_id': test_id,
                'status': test['status'],
                'model_type': test['model_type'],
                'results': results,
                'start_date': test['start_date'].isoformat(),
                'end_date': test['end_date'].isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting A/B test results: {str(e)}")
            raise

    def select_winning_model(
        self,
        test_id: str,
        min_confidence: float = 0.95
    ) -> str:
        """Select statistically significant winner."""
        try:
            results = self.get_ab_test_results(test_id)

            if 'comparison' not in results['results']:
                raise ValueError("Insufficient data to determine winner")

            comparison = results['results']['comparison']

            # Check statistical significance
            if not comparison['statistically_significant']:
                logger.warning(f"No statistically significant winner for test {test_id}")
                return None

            # Check confidence level
            confidence = 1 - comparison['p_value']
            if confidence < min_confidence:
                logger.warning(f"Confidence {confidence:.3f} below minimum {min_confidence}")
                return None

            winner = comparison['winner']
            test = self.ab_tests[test_id]

            winner_id = test['model_a_id'] if winner == 'model_a' else test['model_b_id']

            # Update test status
            test['status'] = 'completed'
            test['winner'] = winner_id

            logger.info(f"Selected winner for test {test_id}: {winner_id} (confidence={confidence:.3f})")
            return winner_id

        except Exception as e:
            logger.error(f"Error selecting winning model: {str(e)}")
            raise

    # Feature Weights
    def update_feature_weights(
        self,
        model_type: ModelType,
        performance_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Update feature weights based on performance."""
        try:
            if performance_data.empty:
                return {}

            # Calculate correlation with outcomes
            feature_weights = {}

            if 'actual_value' in performance_data.columns:
                target = performance_data['actual_value']

                for col in performance_data.columns:
                    if col != 'actual_value' and pd.api.types.is_numeric_dtype(performance_data[col]):
                        correlation = performance_data[col].corr(target)

                        if not np.isnan(correlation):
                            # Weight is absolute correlation
                            feature_weights[col] = abs(float(correlation))

            # Normalize weights
            if feature_weights:
                total_weight = sum(feature_weights.values())
                if total_weight > 0:
                    feature_weights = {
                        k: v / total_weight for k, v in feature_weights.items()
                    }

            # Store in history
            timestamp = datetime.now()
            for feature, weight in feature_weights.items():
                self.feature_importance_history[model_type][feature].append((timestamp, weight))

            logger.info(f"Updated feature weights for {model_type.value}: {len(feature_weights)} features")
            return feature_weights

        except Exception as e:
            logger.error(f"Error updating feature weights: {str(e)}")
            raise

    def get_feature_importance_trends(
        self,
        model_type: ModelType,
        days_back: int = 90
    ) -> Dict[str, List[float]]:
        """Get feature importance over time."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)

            trends = {}

            for feature, history in self.feature_importance_history[model_type].items():
                # Filter by date
                filtered_history = [
                    (timestamp, importance)
                    for timestamp, importance in history
                    if timestamp >= cutoff_date
                ]

                if filtered_history:
                    trends[feature] = [importance for _, importance in filtered_history]

            return trends

        except Exception as e:
            logger.error(f"Error getting feature importance trends: {str(e)}")
            raise

    # Learning Reports
    def generate_learning_report(
        self,
        period_days: int = 7
    ) -> Dict[str, Any]:
        """Generate weekly learning report."""
        try:
            report = {
                'period_days': period_days,
                'generated_at': datetime.now().isoformat(),
                'models': {}
            }

            for model_type in ModelType:
                outcomes = self.collect_prediction_outcomes(model_type, period_days)

                if not outcomes:
                    continue

                # Performance metrics
                performance = self.get_model_performance(model_type, period_days)

                # Error analysis
                error_dist = self.analyze_error_distribution(model_type, period_days)

                # Drift detection
                feature_drift = self.identify_feature_drift(model_type)
                concept_drift = self.detect_concept_drift(model_type)

                # Systematic errors
                systematic_errors = self.identify_systematic_errors(model_type)

                # Retraining recommendation
                should_retrain, retrain_reason = self.should_retrain(model_type)

                report['models'][model_type.value] = {
                    'performance': performance.to_dict() if performance else None,
                    'error_distribution': error_dist,
                    'drift_detection': {
                        'feature_drift': feature_drift.to_dict(),
                        'concept_drift': concept_drift.to_dict()
                    },
                    'systematic_errors': systematic_errors,
                    'retraining': {
                        'recommended': should_retrain,
                        'reason': retrain_reason
                    }
                }

            logger.info(f"Generated learning report for {period_days} days")
            return report

        except Exception as e:
            logger.error(f"Error generating learning report: {str(e)}")
            raise

    def get_model_performance(
        self,
        model_type: ModelType,
        days_back: int = 30
    ) -> ModelPerformance:
        """Get model performance metrics."""
        try:
            outcomes = self.collect_prediction_outcomes(model_type, days_back)

            if not outcomes:
                return None

            predictions = np.array([o.predicted_value for o in outcomes])
            actuals = np.array([o.actual_value for o in outcomes])

            # Calculate metrics
            mae = mean_absolute_error(actuals, predictions)
            rmse = np.sqrt(mean_squared_error(actuals, predictions))

            # R-squared (handle edge cases)
            try:
                r2 = r2_score(actuals, predictions)
            except:
                r2 = 0.0

            # MAPE (avoiding division by zero)
            mape = np.mean([
                abs((a - p) / a * 100) for a, p in zip(actuals, predictions) if a != 0
            ]) if len(actuals) > 0 else 0

            performance = ModelPerformance(
                model_type=model_type,
                mae=float(mae),
                rmse=float(rmse),
                r2=float(r2),
                mape=float(mape),
                sample_count=len(outcomes),
                last_updated=datetime.now()
            )

            # Store in history
            self.performance_history[model_type].append(performance)

            logger.info(f"Calculated performance for {model_type.value}: MAE={mae:.4f}, MAPE={mape:.2f}%")
            return performance

        except Exception as e:
            logger.error(f"Error getting model performance: {str(e)}")
            raise

    def compare_model_versions(
        self,
        model_type: ModelType,
        version_ids: List[str]
    ) -> Dict[str, ModelPerformance]:
        """Compare performance across versions."""
        try:
            # This would typically query different model versions from the registry
            # For now, return the current model's performance
            comparison = {}

            for version_id in version_ids:
                # In a real implementation, this would filter outcomes by version
                performance = self.get_model_performance(model_type, days_back=30)
                if performance:
                    comparison[version_id] = performance

            logger.info(f"Compared {len(comparison)} versions for {model_type.value}")
            return comparison

        except Exception as e:
            logger.error(f"Error comparing model versions: {str(e)}")
            raise

    # Scheduled Jobs
    def run_daily_learning_job(self) -> Dict[str, Any]:
        """Run daily learning analysis."""
        try:
            results = {
                'job': 'daily_learning',
                'executed_at': datetime.now().isoformat(),
                'tasks': []
            }

            for model_type in ModelType:
                # Check for drift
                feature_drift = self.identify_feature_drift(model_type, current_period_days=1)
                concept_drift = self.detect_concept_drift(model_type)

                # Update performance metrics
                performance = self.get_model_performance(model_type, days_back=7)

                # Check for alerts
                if feature_drift.severity in ['high', 'critical']:
                    self.create_alert('feature_drift', model_type, feature_drift.to_dict())

                if concept_drift.severity in ['high', 'critical']:
                    self.create_alert('concept_drift', model_type, concept_drift.to_dict())

                results['tasks'].append({
                    'model_type': model_type.value,
                    'feature_drift_severity': feature_drift.severity,
                    'concept_drift_severity': concept_drift.severity,
                    'performance': performance.to_dict() if performance else None
                })

            logger.info("Completed daily learning job")
            return results

        except Exception as e:
            logger.error(f"Error running daily learning job: {str(e)}")
            raise

    def run_weekly_learning_job(self) -> Dict[str, Any]:
        """Run weekly comprehensive analysis."""
        try:
            results = {
                'job': 'weekly_learning',
                'executed_at': datetime.now().isoformat(),
                'report': None,
                'retraining_recommendations': None,
                'active_ab_tests': []
            }

            # Generate comprehensive report
            results['report'] = self.generate_learning_report(period_days=7)

            # Get retraining recommendations
            results['retraining_recommendations'] = self.get_retraining_recommendation()

            # Check active A/B tests
            for test_id, test in self.ab_tests.items():
                if test['status'] == 'active':
                    # Check if test should be concluded
                    if datetime.now() >= test['end_date']:
                        try:
                            winner = self.select_winning_model(test_id)
                            results['active_ab_tests'].append({
                                'test_id': test_id,
                                'status': 'completed',
                                'winner': winner
                            })
                        except Exception as e:
                            logger.warning(f"Could not determine winner for test {test_id}: {str(e)}")
                    else:
                        test_results = self.get_ab_test_results(test_id)
                        results['active_ab_tests'].append({
                            'test_id': test_id,
                            'status': 'active',
                            'results': test_results
                        })

            logger.info("Completed weekly learning job")
            return results

        except Exception as e:
            logger.error(f"Error running weekly learning job: {str(e)}")
            raise

    # Alerts
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for learning-related alerts."""
        try:
            # Return recent alerts (last 24 hours)
            cutoff = datetime.now() - timedelta(days=1)
            recent_alerts = [
                alert for alert in self.alerts
                if datetime.fromisoformat(alert['created_at']) >= cutoff
            ]

            logger.info(f"Found {len(recent_alerts)} recent alerts")
            return recent_alerts

        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
            raise

    async def create_alert(
        self,
        alert_type: str,
        model_type: ModelType,
        details: Dict[str, Any]
    ) -> str:
        """Create learning alert."""
        try:
            alert_id = str(uuid.uuid4())

            # Create alert in database
            db_alert = LearningAlertModel(
                alert_id=alert_id,
                alert_type=alert_type,
                model_type=model_type.value,
                severity=details.get('severity', 'medium'),
                details=details,
                status='active'
            )

            self.db_session.add(db_alert)
            await self.db_session.commit()

            logger.warning(f"Created alert {alert_id}: {alert_type} for {model_type.value}")
            return alert_id

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error creating alert: {str(e)}")
            raise

    # Helper method to register a prediction
    async def register_prediction(
        self,
        model_type: ModelType,
        predicted_value: float,
        features: Dict[str, Any]
    ) -> str:
        """Register a prediction for tracking."""
        try:
            prediction_id = str(uuid.uuid4())

            # Store prediction in database
            db_prediction = PredictionRecord(
                prediction_id=prediction_id,
                model_type=model_type.value,
                predicted_value=predicted_value,
                features=features
            )

            self.db_session.add(db_prediction)
            await self.db_session.commit()

            return prediction_id

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error registering prediction: {str(e)}")
            raise
