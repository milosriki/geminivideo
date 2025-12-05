"""
Prediction Logger for €5M Investment Validation

This system tracks all ML predictions and compares them with actual performance
to validate model accuracy and ROI predictions.

Usage:
    logger = PredictionLogger()
    prediction_id = await logger.log_prediction(
        video_id="abc123",
        ad_id="fb_123456",
        predicted_ctr=0.045,
        predicted_roas=3.2,
        predicted_conversion=0.012,
        council_score=0.87,
        hook_type="problem_solution",
        template_type="ugc_style",
        platform="meta"
    )

    # Later, after campaign runs:
    result = await logger.update_with_actuals(
        prediction_id=prediction_id,
        actual_ctr=0.048,
        actual_roas=3.5,
        actual_conversion=0.013,
        impressions=10000,
        clicks=480,
        spend=150.00
    )
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
import logging

from shared.db.connection import get_db_context
from shared.db.models import Prediction

logger = logging.getLogger(__name__)


class PredictionLogger:
    """
    Production-grade prediction logging system for model validation.

    This class provides comprehensive tracking of ML predictions and their
    actual outcomes, enabling continuous model improvement and ROI validation.
    """

    def __init__(self):
        """Initialize the prediction logger."""
        self.logger = logging.getLogger(f"{__name__}.PredictionLogger")

    async def log_prediction(
        self,
        video_id: str,
        ad_id: str,
        predicted_ctr: float,
        predicted_roas: float,
        predicted_conversion: float,
        council_score: float,
        hook_type: str,
        template_type: str,
        platform: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save prediction to database for later validation.

        Args:
            video_id: Unique identifier for the video
            ad_id: Platform-specific ad identifier
            predicted_ctr: Predicted click-through rate (0-1)
            predicted_roas: Predicted return on ad spend
            predicted_conversion: Predicted conversion rate (0-1)
            council_score: AI council confidence score (0-1)
            hook_type: Type of hook used (e.g., "problem_solution", "testimonial")
            template_type: Template type (e.g., "ugc_style", "branded")
            platform: Platform name (e.g., "meta", "tiktok", "google")
            metadata: Additional metadata to store with prediction

        Returns:
            str: Unique prediction ID for later reference

        Raises:
            ValueError: If any required parameters are invalid
            Exception: If database operation fails
        """
        # Validate inputs
        self._validate_prediction_inputs(
            predicted_ctr, predicted_roas, predicted_conversion,
            council_score, platform
        )

        try:
            async with get_db_context() as session:
                prediction_id = str(uuid.uuid4())

                prediction = Prediction(
                    id=prediction_id,
                    video_id=video_id,
                    ad_id=ad_id,
                    platform=platform,
                    predicted_ctr=predicted_ctr,
                    predicted_roas=predicted_roas,
                    predicted_conversion=predicted_conversion,
                    council_score=council_score,
                    hook_type=hook_type,
                    template_type=template_type,
                    metadata=metadata or {},
                    created_at=datetime.utcnow()
                )

                session.add(prediction)
                await session.commit()

                self.logger.info(
                    f"Logged prediction {prediction_id} for video {video_id}: "
                    f"CTR={predicted_ctr:.4f}, ROAS={predicted_roas:.2f}, "
                    f"Conv={predicted_conversion:.4f}"
                )

                return prediction_id

        except Exception as e:
            self.logger.error(f"Failed to log prediction: {str(e)}")
            raise

    async def get_pending_predictions(
        self,
        days_old: int = 7,
        platform: Optional[str] = None,
        min_council_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Get predictions that need actual data fetched.

        Args:
            days_old: Only return predictions older than this many days
            platform: Filter by platform (optional)
            min_council_score: Minimum council score filter (optional)

        Returns:
            List of prediction dictionaries with pending actuals
        """
        try:
            async with get_db_context() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days_old)

                # Build query
                query = select(Prediction).where(
                    and_(
                        Prediction.actual_ctr.is_(None),
                        Prediction.created_at <= cutoff_date
                    )
                )

                # Add optional filters
                if platform:
                    query = query.where(Prediction.platform == platform)

                if min_council_score is not None:
                    query = query.where(Prediction.council_score >= min_council_score)

                query = query.order_by(Prediction.created_at.asc())

                result = await session.execute(query)
                predictions = result.scalars().all()

                # Convert to dictionaries
                pending = [self._prediction_to_dict(pred) for pred in predictions]

                self.logger.info(
                    f"Found {len(pending)} pending predictions "
                    f"(days_old>={days_old}, platform={platform})"
                )

                return pending

        except Exception as e:
            self.logger.error(f"Failed to fetch pending predictions: {str(e)}")
            raise

    async def update_with_actuals(
        self,
        prediction_id: str,
        actual_ctr: float,
        actual_roas: float,
        actual_conversion: float,
        impressions: int,
        clicks: int,
        spend: float
    ) -> Dict[str, Any]:
        """
        Update prediction record with actual performance data.

        Args:
            prediction_id: ID of the prediction to update
            actual_ctr: Actual click-through rate achieved
            actual_roas: Actual return on ad spend achieved
            actual_conversion: Actual conversion rate achieved
            impressions: Number of impressions delivered
            clicks: Number of clicks received
            spend: Total ad spend in USD

        Returns:
            Dictionary with comparison metrics including:
            - ctr_error: Absolute error in CTR prediction
            - roas_error: Absolute error in ROAS prediction
            - conversion_error: Absolute error in conversion prediction
            - ctr_accuracy_pct: CTR prediction accuracy percentage
            - roas_accuracy_pct: ROAS prediction accuracy percentage
            - overall_accuracy: Weighted average accuracy

        Raises:
            ValueError: If prediction_id not found or inputs invalid
            Exception: If database operation fails
        """
        try:
            async with get_db_context() as session:
                # Fetch existing prediction
                result = await session.execute(
                    select(Prediction).where(Prediction.id == prediction_id)
                )
                prediction = result.scalar_one_or_none()

                if not prediction:
                    raise ValueError(f"Prediction {prediction_id} not found")

                if prediction.actual_ctr is not None:
                    self.logger.warning(
                        f"Prediction {prediction_id} already has actuals, overwriting"
                    )

                # Update with actuals
                prediction.actual_ctr = actual_ctr
                prediction.actual_roas = actual_roas
                prediction.actual_conversion = actual_conversion
                prediction.impressions = impressions
                prediction.clicks = clicks
                prediction.spend = spend
                prediction.actuals_fetched_at = datetime.utcnow()

                # Calculate accuracy metrics
                ctr_error = abs(prediction.predicted_ctr - actual_ctr)
                roas_error = abs(prediction.predicted_roas - actual_roas)
                conversion_error = abs(prediction.predicted_conversion - actual_conversion)

                # Calculate percentage accuracy (avoid division by zero)
                ctr_accuracy = self._calculate_accuracy(
                    prediction.predicted_ctr, actual_ctr
                )
                roas_accuracy = self._calculate_accuracy(
                    prediction.predicted_roas, actual_roas
                )
                conversion_accuracy = self._calculate_accuracy(
                    prediction.predicted_conversion, actual_conversion
                )

                # Weighted average accuracy (CTR and ROAS weighted higher)
                overall_accuracy = (
                    0.4 * ctr_accuracy +
                    0.4 * roas_accuracy +
                    0.2 * conversion_accuracy
                )

                # Store accuracy metrics in metadata
                if prediction.metadata is None:
                    prediction.metadata = {}

                prediction.metadata.update({
                    'ctr_error': ctr_error,
                    'roas_error': roas_error,
                    'conversion_error': conversion_error,
                    'ctr_accuracy_pct': ctr_accuracy,
                    'roas_accuracy_pct': roas_accuracy,
                    'conversion_accuracy_pct': conversion_accuracy,
                    'overall_accuracy': overall_accuracy
                })

                await session.commit()

                comparison = {
                    'prediction_id': prediction_id,
                    'video_id': prediction.video_id,
                    'ad_id': prediction.ad_id,
                    'platform': prediction.platform,
                    'predicted': {
                        'ctr': prediction.predicted_ctr,
                        'roas': prediction.predicted_roas,
                        'conversion': prediction.predicted_conversion
                    },
                    'actual': {
                        'ctr': actual_ctr,
                        'roas': actual_roas,
                        'conversion': actual_conversion,
                        'impressions': impressions,
                        'clicks': clicks,
                        'spend': spend
                    },
                    'errors': {
                        'ctr_error': ctr_error,
                        'roas_error': roas_error,
                        'conversion_error': conversion_error
                    },
                    'accuracy': {
                        'ctr_accuracy_pct': ctr_accuracy,
                        'roas_accuracy_pct': roas_accuracy,
                        'conversion_accuracy_pct': conversion_accuracy,
                        'overall_accuracy': overall_accuracy
                    },
                    'council_score': prediction.council_score,
                    'hook_type': prediction.hook_type,
                    'template_type': prediction.template_type
                }

                self.logger.info(
                    f"Updated prediction {prediction_id} with actuals: "
                    f"Overall accuracy={overall_accuracy:.1f}%"
                )

                return comparison

        except Exception as e:
            self.logger.error(
                f"Failed to update prediction {prediction_id} with actuals: {str(e)}"
            )
            raise

    async def get_model_performance_stats(
        self,
        days: int = 30,
        platform: Optional[str] = None,
        hook_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get aggregate model performance statistics.

        Args:
            days: Number of days to look back
            platform: Filter by platform (optional)
            hook_type: Filter by hook type (optional)

        Returns:
            Dictionary with aggregate statistics:
            - total_predictions: Total number of predictions
            - predictions_with_actuals: Number with actual data
            - avg_ctr_error: Average CTR prediction error
            - avg_roas_error: Average ROAS prediction error
            - avg_overall_accuracy: Average overall accuracy
            - median_council_score: Median council confidence score
        """
        try:
            async with get_db_context() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days)

                # Build query
                query = select(Prediction).where(
                    Prediction.created_at >= cutoff_date
                )

                if platform:
                    query = query.where(Prediction.platform == platform)

                if hook_type:
                    query = query.where(Prediction.hook_type == hook_type)

                result = await session.execute(query)
                predictions = result.scalars().all()

                # Filter predictions with actuals
                with_actuals = [p for p in predictions if p.actual_ctr is not None]

                if not with_actuals:
                    return {
                        'total_predictions': len(predictions),
                        'predictions_with_actuals': 0,
                        'avg_ctr_error': None,
                        'avg_roas_error': None,
                        'avg_overall_accuracy': None,
                        'median_council_score': None
                    }

                # Calculate statistics
                ctr_errors = [
                    abs(p.predicted_ctr - p.actual_ctr)
                    for p in with_actuals
                ]
                roas_errors = [
                    abs(p.predicted_roas - p.actual_roas)
                    for p in with_actuals
                ]

                accuracies = [
                    p.metadata.get('overall_accuracy', 0)
                    for p in with_actuals
                    if p.metadata
                ]

                council_scores = sorted([p.council_score for p in predictions])
                median_idx = len(council_scores) // 2

                stats = {
                    'total_predictions': len(predictions),
                    'predictions_with_actuals': len(with_actuals),
                    'avg_ctr_error': sum(ctr_errors) / len(ctr_errors),
                    'avg_roas_error': sum(roas_errors) / len(roas_errors),
                    'avg_overall_accuracy': sum(accuracies) / len(accuracies) if accuracies else None,
                    'median_council_score': council_scores[median_idx] if council_scores else None,
                    'days_analyzed': days,
                    'platform_filter': platform,
                    'hook_type_filter': hook_type
                }

                self.logger.info(
                    f"Performance stats: {len(with_actuals)}/{len(predictions)} "
                    f"predictions with actuals, avg accuracy="
                    f"{stats['avg_overall_accuracy']:.1f}%" if stats['avg_overall_accuracy'] else "N/A"
                )

                return stats

        except Exception as e:
            self.logger.error(f"Failed to calculate performance stats: {str(e)}")
            raise

    async def get_prediction_by_id(self, prediction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single prediction by ID.

        Args:
            prediction_id: The prediction ID to fetch

        Returns:
            Prediction dictionary or None if not found
        """
        try:
            async with get_db_context() as session:
                result = await session.execute(
                    select(Prediction).where(Prediction.id == prediction_id)
                )
                prediction = result.scalar_one_or_none()

                if prediction:
                    return self._prediction_to_dict(prediction)
                return None

        except Exception as e:
            self.logger.error(f"Failed to fetch prediction {prediction_id}: {str(e)}")
            raise

    async def get_predictions_by_video(
        self,
        video_id: str,
        include_actuals_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all predictions for a specific video.

        Args:
            video_id: The video ID to fetch predictions for
            include_actuals_only: Only return predictions with actual data

        Returns:
            List of prediction dictionaries
        """
        try:
            async with get_db_context() as session:
                query = select(Prediction).where(Prediction.video_id == video_id)

                if include_actuals_only:
                    query = query.where(Prediction.actual_ctr.is_not(None))

                query = query.order_by(Prediction.created_at.desc())

                result = await session.execute(query)
                predictions = result.scalars().all()

                return [self._prediction_to_dict(pred) for pred in predictions]

        except Exception as e:
            self.logger.error(
                f"Failed to fetch predictions for video {video_id}: {str(e)}"
            )
            raise

    # Private helper methods

    def _validate_prediction_inputs(
        self,
        predicted_ctr: float,
        predicted_roas: float,
        predicted_conversion: float,
        council_score: float,
        platform: str
    ):
        """Validate prediction input parameters."""
        if not (0 <= predicted_ctr <= 1):
            raise ValueError(f"predicted_ctr must be between 0 and 1, got {predicted_ctr}")

        if predicted_roas < 0:
            raise ValueError(f"predicted_roas must be non-negative, got {predicted_roas}")

        if not (0 <= predicted_conversion <= 1):
            raise ValueError(
                f"predicted_conversion must be between 0 and 1, got {predicted_conversion}"
            )

        if not (0 <= council_score <= 1):
            raise ValueError(
                f"council_score must be between 0 and 1, got {council_score}"
            )

        valid_platforms = ['meta', 'tiktok', 'google', 'youtube', 'snapchat']
        if platform not in valid_platforms:
            raise ValueError(
                f"platform must be one of {valid_platforms}, got {platform}"
            )

    def _calculate_accuracy(self, predicted: float, actual: float) -> float:
        """
        Calculate prediction accuracy as a percentage.

        Returns 100 - (abs_error / actual * 100), capped at 0-100.
        """
        if actual == 0:
            return 100.0 if predicted == 0 else 0.0

        error_pct = abs(predicted - actual) / actual * 100
        accuracy = max(0.0, min(100.0, 100.0 - error_pct))
        return round(accuracy, 2)

    def _prediction_to_dict(self, prediction: Prediction) -> Dict[str, Any]:
        """Convert Prediction model to dictionary."""
        return {
            'id': prediction.id,
            'video_id': prediction.video_id,
            'ad_id': prediction.ad_id,
            'platform': prediction.platform,
            'predicted': {
                'ctr': prediction.predicted_ctr,
                'roas': prediction.predicted_roas,
                'conversion': prediction.predicted_conversion
            },
            'actual': {
                'ctr': prediction.actual_ctr,
                'roas': prediction.actual_roas,
                'conversion': prediction.actual_conversion,
                'impressions': prediction.impressions,
                'clicks': prediction.clicks,
                'spend': prediction.spend
            } if prediction.actual_ctr is not None else None,
            'council_score': prediction.council_score,
            'hook_type': prediction.hook_type,
            'template_type': prediction.template_type,
            'metadata': prediction.metadata,
            'created_at': prediction.created_at.isoformat() if prediction.created_at else None,
            'actuals_fetched_at': (
                prediction.actuals_fetched_at.isoformat()
                if prediction.actuals_fetched_at else None
            )
        }


# Convenience functions for common operations

async def log_prediction(**kwargs) -> str:
    """
    Convenience function to log a prediction.

    Usage:
        prediction_id = await log_prediction(
            video_id="abc123",
            ad_id="fb_123456",
            predicted_ctr=0.045,
            ...
        )
    """
    logger = PredictionLogger()
    return await logger.log_prediction(**kwargs)


async def update_prediction_with_actuals(prediction_id: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to update a prediction with actuals.

    Usage:
        result = await update_prediction_with_actuals(
            prediction_id="pred123",
            actual_ctr=0.048,
            actual_roas=3.5,
            ...
        )
    """
    logger = PredictionLogger()
    return await logger.update_with_actuals(prediction_id, **kwargs)


async def get_model_accuracy(days: int = 30) -> Dict[str, Any]:
    """
    Convenience function to get model accuracy stats.

    Usage:
        stats = await get_model_accuracy(days=30)
        print(f"Average accuracy: {stats['avg_overall_accuracy']:.1f}%")
    """
    logger = PredictionLogger()
    return await logger.get_model_performance_stats(days=days)
