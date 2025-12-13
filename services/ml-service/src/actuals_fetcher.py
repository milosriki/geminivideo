"""
Actuals Fetcher - Agent 8 for €5M Investment Validation
Production-grade system to fetch real performance data from Meta Ads API.

This module:
1. Fetches actual ad performance (CTR, ROAS, conversions, spend) from Meta
2. Syncs actuals with ML predictions for model validation
3. Provides scheduled batch processing for all pending predictions
4. Tracks prediction accuracy and model drift

NO MOCK DATA - Production-ready for investment validation.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import time
from enum import Enum

# Database
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# Meta API
import sys
sys.path.append('/home/user/geminivideo/services/titan-core')
from meta.marketing_api import RealMetaAdsManager, MetaAPIError, MetaRateLimitError

# Local imports
from shared.db.models import PerformanceMetric, Video, Base
from shared.db.connection import get_db_session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FetchStatus(Enum):
    """Status of actuals fetch operation"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    RATE_LIMITED = "rate_limited"
    NO_DATA = "no_data"


@dataclass
class AdActuals:
    """Actual performance data from Meta Ads API"""
    ad_id: str
    video_id: str
    date: datetime
    impressions: int
    clicks: int
    spend: float
    actual_ctr: float
    conversions: int
    actual_roas: float
    revenue: float
    reach: int
    frequency: float
    cpm: float
    cpc: float
    raw_data: Dict[str, Any]
    fetched_at: datetime

    def to_performance_metric(self) -> Dict[str, Any]:
        """Convert to PerformanceMetric database model"""
        return {
            'video_id': self.video_id,
            'platform': 'meta',
            'date': self.date.date(),
            'impressions': self.impressions,
            'clicks': self.clicks,
            'spend': self.spend,
            'ctr': self.actual_ctr,
            'conversions': self.conversions,
            'raw_data': {
                **self.raw_data,
                'roas': self.actual_roas,
                'revenue': self.revenue,
                'reach': self.reach,
                'frequency': self.frequency,
                'cpm': self.cpm,
                'cpc': self.cpc,
                'fetched_at': self.fetched_at.isoformat()
            }
        }


@dataclass
class PredictionActualsComparison:
    """Comparison between predicted and actual performance"""
    video_id: str
    ad_id: str
    predicted_ctr: Optional[float]
    actual_ctr: float
    predicted_roas: Optional[float]
    actual_roas: float
    ctr_error: Optional[float]
    roas_error: Optional[float]
    ctr_accuracy: Optional[float]  # 1 - abs(error)
    roas_accuracy: Optional[float]
    days_since_prediction: int
    comparison_date: datetime


@dataclass
class FetchSummary:
    """Summary of actuals fetch operation"""
    total_ads: int
    successful: int
    failed: int
    rate_limited: int
    no_data: int
    total_spend: float
    total_conversions: int
    total_revenue: float
    duration_seconds: float
    timestamp: datetime


class ActualsFetcher:
    """
    Production-grade actuals fetcher from Meta Ads API.

    Responsibilities:
    1. Fetch real ad performance data from Meta
    2. Sync actuals with predictions in database
    3. Calculate prediction accuracy metrics
    4. Handle rate limiting and errors gracefully
    5. Support batch processing with progress tracking
    """

    def __init__(
        self,
        access_token: Optional[str] = None,
        ad_account_id: Optional[str] = None,
        db_session: Optional[Session] = None,
        max_retries: int = 3,
        rate_limit_delay: float = 60.0
    ):
        """
        Initialize actuals fetcher.

        Args:
            access_token: Meta access token (defaults to env var)
            ad_account_id: Meta ad account ID (defaults to env var)
            db_session: Database session (creates new if None)
            max_retries: Maximum retry attempts for failed requests
            rate_limit_delay: Delay in seconds when rate limited
        """
        # Meta API credentials
        self.access_token = access_token or os.getenv('META_ACCESS_TOKEN')
        self.ad_account_id = ad_account_id or os.getenv('META_AD_ACCOUNT_ID')
        self.app_secret = os.getenv('META_APP_SECRET')
        self.app_id = os.getenv('META_APP_ID')

        if not self.access_token or not self.ad_account_id:
            logger.warning(
                "Meta credentials not configured. Set META_ACCESS_TOKEN and META_AD_ACCOUNT_ID. "
                "Actuals fetcher will be in simulation mode."
            )
            self.meta_api = None
        else:
            # Initialize Meta API client
            try:
                self.meta_api = RealMetaAdsManager(
                    access_token=self.access_token,
                    ad_account_id=self.ad_account_id,
                    app_secret=self.app_secret,
                    app_id=self.app_id
                )
                logger.info(f"✅ Meta API client initialized for account {self.ad_account_id}")
            except Exception as e:
                logger.error(f"Failed to initialize Meta API: {e}")
                self.meta_api = None

        # Database session
        self.db_session = db_session
        self.owns_session = db_session is None

        # Configuration
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay

        # Performance tracking
        self.stats = {
            'total_fetches': 0,
            'successful_fetches': 0,
            'failed_fetches': 0,
            'rate_limits_hit': 0,
            'total_spend_tracked': 0.0,
            'total_conversions_tracked': 0
        }

    def _get_session(self) -> Session:
        """Get database session (create if needed)"""
        if self.db_session:
            return self.db_session
        return get_db_session()

    def _close_session_if_owned(self, session: Session) -> None:
        """Close session only if we created it"""
        if self.owns_session and session:
            session.close()

    # ==================== Core Fetching Methods ====================

    async def fetch_ad_actuals(
        self,
        ad_id: str,
        video_id: str,
        days_back: int = 7,
        retry_count: int = 0
    ) -> Optional[AdActuals]:
        """
        Fetch actual performance data for a specific ad.

        Args:
            ad_id: Meta Ad ID
            video_id: Internal video/creative ID
            days_back: Number of days to look back (default: 7)
            retry_count: Current retry attempt

        Returns:
            AdActuals object or None if failed
        """
        if not self.meta_api:
            logger.warning(f"Meta API not configured, cannot fetch actuals for ad {ad_id}")
            return None

        try:
            logger.info(f"Fetching actuals for ad {ad_id} (last {days_back} days)")

            # Fetch insights from Meta API
            insights = self.meta_api.get_ad_insights(
                ad_id=ad_id,
                fields=[
                    'impressions', 'clicks', 'spend', 'reach', 'frequency',
                    'cpm', 'cpc', 'ctr', 'actions', 'action_values',
                    'conversions', 'conversion_values', 'purchase_roas'
                ],
                date_preset=f'last_{days_back}d'
            )

            if not insights:
                logger.warning(f"No insights returned for ad {ad_id}")
                self.stats['failed_fetches'] += 1
                return None

            # Extract metrics
            impressions = int(insights.get('impressions', 0))
            clicks = int(insights.get('clicks', 0))
            spend = float(insights.get('spend', 0))
            reach = int(insights.get('reach', 0))
            frequency = float(insights.get('frequency', 0))
            cpm = float(insights.get('cpm', 0))
            cpc = float(insights.get('cpc', 0))

            # Calculate CTR
            actual_ctr = float(insights.get('ctr', 0))
            if actual_ctr == 0 and impressions > 0:
                actual_ctr = (clicks / impressions) * 100

            # Extract conversions
            conversions = 0
            actions = insights.get('actions', [])
            for action in actions:
                if action.get('action_type') in ['purchase', 'offsite_conversion.fb_pixel_purchase']:
                    conversions = int(action.get('value', 0))
                    break

            # Extract revenue
            revenue = 0.0
            action_values = insights.get('action_values', [])
            for value in action_values:
                if value.get('action_type') in ['purchase', 'offsite_conversion.fb_pixel_purchase']:
                    revenue = float(value.get('value', 0))
                    break

            # If no revenue in action_values, try conversion_values
            if revenue == 0.0:
                conversion_values = insights.get('conversion_values', [])
                if conversion_values:
                    revenue = sum(float(cv.get('value', 0)) for cv in conversion_values)

            # Calculate ROAS
            actual_roas = revenue / spend if spend > 0 else 0.0

            # Alternative: Use Meta's purchase_roas if available
            if 'purchase_roas' in insights and insights['purchase_roas']:
                roas_data = insights['purchase_roas']
                if isinstance(roas_data, list) and len(roas_data) > 0:
                    actual_roas = float(roas_data[0].get('value', actual_roas))

            actuals = AdActuals(
                ad_id=ad_id,
                video_id=video_id,
                date=datetime.utcnow(),
                impressions=impressions,
                clicks=clicks,
                spend=spend,
                actual_ctr=actual_ctr,
                conversions=conversions,
                actual_roas=actual_roas,
                revenue=revenue,
                reach=reach,
                frequency=frequency,
                cpm=cpm,
                cpc=cpc,
                raw_data=insights,
                fetched_at=datetime.utcnow()
            )

            self.stats['total_fetches'] += 1
            self.stats['successful_fetches'] += 1
            self.stats['total_spend_tracked'] += spend
            self.stats['total_conversions_tracked'] += conversions

            logger.info(
                f"✅ Fetched actuals for ad {ad_id}: "
                f"CTR={actual_ctr:.2f}%, ROAS={actual_roas:.2f}, "
                f"Conversions={conversions}, Spend=${spend:.2f}"
            )

            return actuals

        except MetaRateLimitError as e:
            logger.warning(f"Rate limit hit for ad {ad_id}: {e}")
            self.stats['rate_limits_hit'] += 1

            if retry_count < self.max_retries:
                logger.info(f"Waiting {self.rate_limit_delay}s before retry...")
                await asyncio.sleep(self.rate_limit_delay)
                return await self.fetch_ad_actuals(ad_id, video_id, days_back, retry_count + 1)
            else:
                logger.error(f"Max retries exceeded for ad {ad_id} due to rate limiting")
                self.stats['failed_fetches'] += 1
                return None

        except MetaAPIError as e:
            logger.error(f"Meta API error fetching ad {ad_id}: {e}")
            self.stats['failed_fetches'] += 1

            if retry_count < self.max_retries:
                logger.info(f"Retrying in {2 ** retry_count}s...")
                await asyncio.sleep(2 ** retry_count)
                return await self.fetch_ad_actuals(ad_id, video_id, days_back, retry_count + 1)
            else:
                return None

        except Exception as e:
            logger.error(f"Unexpected error fetching ad {ad_id}: {e}", exc_info=True)
            self.stats['failed_fetches'] += 1
            return None

    async def fetch_batch_actuals(
        self,
        ad_video_pairs: List[Tuple[str, str]],
        days_back: int = 7,
        batch_delay: float = 1.0
    ) -> List[AdActuals]:
        """
        Fetch actuals for multiple ads in batch.

        Args:
            ad_video_pairs: List of (ad_id, video_id) tuples
            days_back: Number of days to look back
            batch_delay: Delay between requests to avoid rate limiting

        Returns:
            List of AdActuals objects (only successful fetches)
        """
        logger.info(f"Batch fetching actuals for {len(ad_video_pairs)} ads")
        start_time = time.time()

        results = []
        for i, (ad_id, video_id) in enumerate(ad_video_pairs, 1):
            logger.info(f"Processing {i}/{len(ad_video_pairs)}: ad {ad_id}")

            actuals = await self.fetch_ad_actuals(ad_id, video_id, days_back)
            if actuals:
                results.append(actuals)

            # Rate limiting delay (except for last item)
            if i < len(ad_video_pairs):
                await asyncio.sleep(batch_delay)

        duration = time.time() - start_time
        logger.info(
            f"✅ Batch fetch complete: {len(results)}/{len(ad_video_pairs)} successful "
            f"in {duration:.1f}s"
        )

        return results

    # ==================== Database Sync Methods ====================

    def save_actuals_to_db(self, actuals: AdActuals) -> bool:
        """
        Save actuals to database (PerformanceMetric table).

        Args:
            actuals: AdActuals object

        Returns:
            True if successful, False otherwise
        """
        session = self._get_session()

        try:
            # Check if metric already exists for this video/date
            existing = session.query(PerformanceMetric).filter(
                and_(
                    PerformanceMetric.video_id == actuals.video_id,
                    PerformanceMetric.date == actuals.date.date(),
                    PerformanceMetric.platform == 'meta'
                )
            ).first()

            if existing:
                # Update existing record
                existing.impressions = actuals.impressions
                existing.clicks = actuals.clicks
                existing.spend = actuals.spend
                existing.ctr = actuals.actual_ctr
                existing.conversions = actuals.conversions
                existing.raw_data = actuals.to_performance_metric()['raw_data']
                logger.info(f"Updated existing metric for video {actuals.video_id}")
            else:
                # Create new record
                metric = PerformanceMetric(**actuals.to_performance_metric())
                session.add(metric)
                logger.info(f"Created new metric for video {actuals.video_id}")

            session.commit()
            return True

        except SQLAlchemyError as e:
            logger.error(f"Database error saving actuals: {e}")
            session.rollback()
            return False
        finally:
            self._close_session_if_owned(session)

    async def sync_actuals_batch(self, actuals_list: List[AdActuals]) -> Dict[str, int]:
        """
        Save batch of actuals to database.

        Args:
            actuals_list: List of AdActuals objects

        Returns:
            Dictionary with success/failure counts
        """
        logger.info(f"Syncing {len(actuals_list)} actuals to database")

        success_count = 0
        failure_count = 0

        for actuals in actuals_list:
            if self.save_actuals_to_db(actuals):
                success_count += 1
            else:
                failure_count += 1

        logger.info(f"✅ Database sync complete: {success_count} saved, {failure_count} failed")

        return {
            'success': success_count,
            'failed': failure_count,
            'total': len(actuals_list)
        }

    # ==================== Prediction Comparison Methods ====================

    def compare_with_predictions(
        self,
        actuals: AdActuals,
        predicted_ctr: Optional[float] = None,
        predicted_roas: Optional[float] = None
    ) -> PredictionActualsComparison:
        """
        Compare actuals with ML predictions.

        Args:
            actuals: AdActuals object
            predicted_ctr: Predicted CTR (fetch from DB if None)
            predicted_roas: Predicted ROAS (fetch from DB if None)

        Returns:
            PredictionActualsComparison object
        """
        # Fetch predictions from database if not provided
        session = self._get_session()
        days_since_prediction = 0

        try:
            if predicted_ctr is None or predicted_roas is None:
                # Import Prediction model
                from shared.db.models import Prediction

                # Query for the most recent prediction for this video/ad
                prediction = session.query(Prediction).filter(
                    and_(
                        Prediction.video_id == actuals.video_id,
                        Prediction.ad_id == actuals.ad_id
                    )
                ).order_by(Prediction.created_at.desc()).first()

                if prediction:
                    if predicted_ctr is None:
                        predicted_ctr = prediction.predicted_ctr
                    if predicted_roas is None:
                        predicted_roas = prediction.predicted_roas

                    # Calculate days since prediction
                    if prediction.created_at:
                        days_since_prediction = (datetime.utcnow() - prediction.created_at).days

                    logger.info(
                        f"Fetched prediction for video {actuals.video_id}: "
                        f"CTR={predicted_ctr:.2f}, ROAS={predicted_roas:.2f}, "
                        f"Age={days_since_prediction} days"
                    )
                else:
                    logger.warning(f"No prediction found for video {actuals.video_id}")
        except Exception as e:
            logger.error(f"Error fetching prediction: {e}")
        finally:
            self._close_session_if_owned(session)

        # Calculate errors
        ctr_error = None
        ctr_accuracy = None
        if predicted_ctr is not None and actuals.actual_ctr > 0:
            ctr_error = ((actuals.actual_ctr - predicted_ctr) / actuals.actual_ctr) * 100
            ctr_accuracy = max(0, 1 - abs(ctr_error) / 100)

        roas_error = None
        roas_accuracy = None
        if predicted_roas is not None and actuals.actual_roas > 0:
            roas_error = ((actuals.actual_roas - predicted_roas) / actuals.actual_roas) * 100
            roas_accuracy = max(0, 1 - abs(roas_error) / 100)

        return PredictionActualsComparison(
            video_id=actuals.video_id,
            ad_id=actuals.ad_id,
            predicted_ctr=predicted_ctr,
            actual_ctr=actuals.actual_ctr,
            predicted_roas=predicted_roas,
            actual_roas=actuals.actual_roas,
            ctr_error=ctr_error,
            roas_error=roas_error,
            ctr_accuracy=ctr_accuracy,
            roas_accuracy=roas_accuracy,
            days_since_prediction=days_since_prediction,
            comparison_date=datetime.utcnow()
        )

    # ==================== Scheduled Sync Methods ====================

    async def sync_actuals_for_pending_predictions(
        self,
        min_age_hours: int = 24,
        max_age_days: int = 30
    ) -> FetchSummary:
        """
        Cron job: Fetch actuals for all videos with predictions older than min_age_hours.

        This is the main scheduled task that runs hourly to:
        1. Find videos with Meta platform IDs
        2. Fetch their actual performance
        3. Update database
        4. Calculate prediction accuracy

        Args:
            min_age_hours: Only fetch for videos older than this (allows ad to run)
            max_age_days: Don't fetch for videos older than this (stale data)

        Returns:
            FetchSummary with operation statistics
        """
        logger.info("🔄 Starting scheduled actuals sync...")
        start_time = time.time()

        session = self._get_session()

        try:
            # Query videos with Meta platform IDs created within time window
            cutoff_date = datetime.utcnow() - timedelta(hours=min_age_hours)
            max_age_date = datetime.utcnow() - timedelta(days=max_age_days)

            videos = session.query(Video).filter(
                and_(
                    Video.meta_platform_id.isnot(None),
                    Video.meta_platform_id != '',
                    Video.created_at <= cutoff_date,
                    Video.created_at >= max_age_date
                )
            ).all()

            logger.info(f"Found {len(videos)} videos eligible for actuals sync")

            if not videos:
                duration = time.time() - start_time
                return FetchSummary(
                    total_ads=0,
                    successful=0,
                    failed=0,
                    rate_limited=0,
                    no_data=0,
                    total_spend=0.0,
                    total_conversions=0,
                    total_revenue=0.0,
                    duration_seconds=duration,
                    timestamp=datetime.utcnow()
                )

            # Prepare batch
            ad_video_pairs = [
                (video.meta_platform_id, str(video.id))
                for video in videos
            ]

            # Fetch actuals
            actuals_list = await self.fetch_batch_actuals(ad_video_pairs, days_back=7)

            # Sync to database
            sync_result = await self.sync_actuals_batch(actuals_list)

            # Calculate summary
            duration = time.time() - start_time
            total_spend = sum(a.spend for a in actuals_list)
            total_conversions = sum(a.conversions for a in actuals_list)
            total_revenue = sum(a.revenue for a in actuals_list)

            summary = FetchSummary(
                total_ads=len(videos),
                successful=sync_result['success'],
                failed=sync_result['failed'],
                rate_limited=self.stats['rate_limits_hit'],
                no_data=len(videos) - len(actuals_list),
                total_spend=total_spend,
                total_conversions=total_conversions,
                total_revenue=total_revenue,
                duration_seconds=duration,
                timestamp=datetime.utcnow()
            )

            logger.info(
                f"✅ Scheduled sync complete: "
                f"{summary.successful}/{summary.total_ads} successful, "
                f"${summary.total_spend:.2f} spend tracked, "
                f"{summary.total_conversions} conversions, "
                f"${summary.total_revenue:.2f} revenue "
                f"in {summary.duration_seconds:.1f}s"
            )

            return summary

        except Exception as e:
            logger.error(f"Error in scheduled sync: {e}", exc_info=True)
            duration = time.time() - start_time
            return FetchSummary(
                total_ads=0,
                successful=0,
                failed=0,
                rate_limited=0,
                no_data=0,
                total_spend=0.0,
                total_conversions=0,
                total_revenue=0.0,
                duration_seconds=duration,
                timestamp=datetime.utcnow()
            )
        finally:
            self._close_session_if_owned(session)

    # ==================== Utility Methods ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get fetcher statistics"""
        success_rate = 0.0
        if self.stats['total_fetches'] > 0:
            success_rate = (self.stats['successful_fetches'] / self.stats['total_fetches']) * 100

        return {
            **self.stats,
            'success_rate': success_rate,
            'meta_api_configured': self.meta_api is not None
        }

    def reset_stats(self) -> None:
        """Reset statistics counters"""
        self.stats = {
            'total_fetches': 0,
            'successful_fetches': 0,
            'failed_fetches': 0,
            'rate_limits_hit': 0,
            'total_spend_tracked': 0.0,
            'total_conversions_tracked': 0
        }
        logger.info("Statistics reset")


# ==================== Singleton Instance ====================

# Global instance for easy import
actuals_fetcher = ActualsFetcher()


# ==================== Async Helper ====================

def run_async(coro):
    """Helper to run async function in sync context"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
