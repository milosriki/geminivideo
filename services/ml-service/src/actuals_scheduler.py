"""
Actuals Scheduler - Automated hourly fetching of Meta Ad performance
Continuously syncs real performance data with ML predictions for validation

This scheduler runs every hour to:
1. Fetch actual performance from Meta Ads API
2. Update database with real CTR, ROAS, conversions
3. Compare with ML predictions for model accuracy tracking
4. Support investment validation with real data
"""

import logging
import schedule
import time
import threading
import asyncio
from typing import Optional
from datetime import datetime

from src.actuals_fetcher import actuals_fetcher

logger = logging.getLogger(__name__)


class ActualsScheduler:
    """Automated actuals fetching scheduler"""

    def __init__(self, interval_hours: int = 1, min_age_hours: int = 24, max_age_days: int = 30):
        """
        Initialize actuals scheduler

        Args:
            interval_hours: Hours between fetch runs (default: 1 = hourly)
            min_age_hours: Only fetch for ads older than this (allow ad to run)
            max_age_days: Don't fetch for ads older than this (stale data)
        """
        self.interval_hours = interval_hours
        self.min_age_hours = min_age_hours
        self.max_age_days = max_age_days
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.last_run: Optional[datetime] = None
        self.last_summary = None

    def fetch_actuals(self):
        """Fetch actuals from Meta API and sync to database"""
        logger.info("🔄 Starting scheduled actuals fetch...")
        self.last_run = datetime.utcnow()

        try:
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            summary = loop.run_until_complete(
                actuals_fetcher.sync_actuals_for_pending_predictions(
                    min_age_hours=self.min_age_hours,
                    max_age_days=self.max_age_days
                )
            )

            loop.close()

            self.last_summary = summary

            logger.info(
                f"✅ Scheduled actuals fetch complete:\n"
                f"   - Ads processed: {summary.total_ads}\n"
                f"   - Successful: {summary.successful}\n"
                f"   - Failed: {summary.failed}\n"
                f"   - Rate limited: {summary.rate_limited}\n"
                f"   - No data: {summary.no_data}\n"
                f"   - Total spend: ${summary.total_spend:.2f}\n"
                f"   - Conversions: {summary.total_conversions}\n"
                f"   - Revenue: ${summary.total_revenue:.2f}\n"
                f"   - Duration: {summary.duration_seconds:.1f}s"
            )

            # Log stats
            stats = actuals_fetcher.get_stats()
            logger.info(
                f"📊 Cumulative stats:\n"
                f"   - Total fetches: {stats['total_fetches']}\n"
                f"   - Success rate: {stats['success_rate']:.1f}%\n"
                f"   - Rate limits: {stats['rate_limits_hit']}\n"
                f"   - Total spend tracked: ${stats['total_spend_tracked']:.2f}\n"
                f"   - Total conversions: {stats['total_conversions_tracked']}"
            )

        except Exception as e:
            logger.error(f"❌ Error during scheduled actuals fetch: {e}", exc_info=True)

    def start(self):
        """Start the scheduler in a background thread"""
        if self.is_running:
            logger.warning("Actuals scheduler already running")
            return

        logger.info(
            f"Starting actuals scheduler:\n"
            f"   - Interval: every {self.interval_hours} hour(s)\n"
            f"   - Min ad age: {self.min_age_hours} hours\n"
            f"   - Max ad age: {self.max_age_days} days"
        )

        # Run immediately on start
        logger.info("Running initial actuals fetch...")
        try:
            self.fetch_actuals()
        except Exception as e:
            logger.error(f"Initial fetch failed: {e}")

        # Schedule recurring job
        schedule.every(self.interval_hours).hours.do(self.fetch_actuals)

        # Run in background thread
        self.is_running = True
        self.thread = threading.Thread(target=self._run_schedule, daemon=True)
        self.thread.start()

        logger.info("✅ Actuals scheduler started")

    def _run_schedule(self):
        """Background thread that runs the scheduler"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Actuals scheduler stopped")

    def get_status(self) -> dict:
        """Get scheduler status"""
        return {
            'is_running': self.is_running,
            'interval_hours': self.interval_hours,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'last_summary': {
                'total_ads': self.last_summary.total_ads,
                'successful': self.last_summary.successful,
                'failed': self.last_summary.failed,
                'total_spend': self.last_summary.total_spend,
                'total_conversions': self.last_summary.total_conversions,
                'total_revenue': self.last_summary.total_revenue,
                'duration_seconds': self.last_summary.duration_seconds
            } if self.last_summary else None,
            'fetcher_stats': actuals_fetcher.get_stats()
        }


# Global instance - runs every hour
actuals_scheduler = ActualsScheduler(
    interval_hours=1,  # Hourly
    min_age_hours=24,  # Only fetch ads that ran for at least 24h
    max_age_days=30    # Don't fetch ads older than 30 days
)
