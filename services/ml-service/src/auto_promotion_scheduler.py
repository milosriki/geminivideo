"""
Auto-Promotion Scheduler
Agent 44 - Periodic checks and automatic promotion triggers

Runs background tasks to check experiments and promote winners automatically.
"""

import os
import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from src.auto_promoter import AutoPromoter, PromotionStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutoPromotionScheduler:
    """
    Background scheduler for automatic A/B test promotion.

    Runs periodic checks (default: every 6 hours) to:
    1. Check all active experiments
    2. Promote winners when statistically significant
    3. Reallocate budgets
    4. Extract and store insights
    5. Send notifications
    """

    def __init__(
        self,
        auto_promoter: AutoPromoter,
        check_interval_hours: int = 6,
        notification_webhook: Optional[str] = None
    ):
        """
        Initialize scheduler.

        Args:
            auto_promoter: AutoPromoter instance
            check_interval_hours: Hours between checks (default 6)
            notification_webhook: Optional webhook URL for notifications
        """
        self.auto_promoter = auto_promoter
        self.check_interval_hours = check_interval_hours
        self.notification_webhook = notification_webhook

        self.scheduler = AsyncIOScheduler()
        self.is_running = False

        logger.info(f"AutoPromotionScheduler initialized: check_interval={check_interval_hours}h")

    def start(self) -> None:
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        # Add periodic check job
        self.scheduler.add_job(
            self._check_and_promote_all,
            trigger=IntervalTrigger(hours=self.check_interval_hours),
            id='auto_promotion_check',
            name='Check and promote A/B test winners',
            replace_existing=True
        )

        # Add daily summary job (runs at 9 AM)
        self.scheduler.add_job(
            self._send_daily_summary,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_promotion_summary',
            name='Send daily promotion summary',
            replace_existing=True
        )

        # Add weekly compound learning report (runs Monday 9 AM)
        self.scheduler.add_job(
            self._send_weekly_compound_report,
            trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
            id='weekly_compound_report',
            name='Send weekly compound learning report',
            replace_existing=True
        )

        self.scheduler.start()
        self.is_running = True

        logger.info(f"✓ AutoPromotionScheduler started - checking every {self.check_interval_hours}h")

    def stop(self) -> None:
        """Stop the scheduler."""
        if not self.is_running:
            logger.warning("Scheduler not running")
            return

        self.scheduler.shutdown()
        self.is_running = False
        logger.info("AutoPromotionScheduler stopped")

    async def _check_and_promote_all(self) -> None:
        """
        Check all active experiments and promote winners.

        This is the main periodic job that runs every N hours.
        """
        try:
            logger.info("="*60)
            logger.info(f"AUTO-PROMOTION CHECK STARTED: {datetime.now()}")
            logger.info("="*60)

            # Check all active experiments
            results = await self.auto_promoter.check_all_active_experiments()

            # Count results by status
            promoted_count = sum(1 for r in results if r.status == PromotionStatus.PROMOTED)
            continue_count = sum(1 for r in results if r.status == PromotionStatus.CONTINUE_TESTING)
            insufficient_count = sum(1 for r in results if r.status == PromotionStatus.INSUFFICIENT_DATA)
            error_count = sum(1 for r in results if r.status == PromotionStatus.ERROR)

            # Log summary
            logger.info(f"Check complete: {len(results)} experiments checked")
            logger.info(f"  ✓ Promoted: {promoted_count}")
            logger.info(f"  → Continue testing: {continue_count}")
            logger.info(f"  ! Insufficient data: {insufficient_count}")
            logger.info(f"  ✗ Errors: {error_count}")

            # Send notifications for promotions
            if promoted_count > 0:
                promoted_results = [r for r in results if r.status == PromotionStatus.PROMOTED]
                await self._send_promotion_notifications(promoted_results)

            logger.info("="*60)

        except Exception as e:
            logger.error(f"Error in auto-promotion check: {str(e)}")

    async def _send_promotion_notifications(self, promoted_results: list) -> None:
        """
        Send notifications for newly promoted winners.

        Args:
            promoted_results: List of PromotionResult objects that were promoted
        """
        try:
            for result in promoted_results:
                message = self._format_promotion_message(result)
                logger.info(f"PROMOTION NOTIFICATION:\n{message}")

                # Send to webhook if configured
                if self.notification_webhook:
                    await self._send_webhook_notification(message, result)

        except Exception as e:
            logger.error(f"Error sending promotion notifications: {str(e)}")

    def _format_promotion_message(self, result) -> str:
        """Format promotion result as notification message."""
        improvement_pct = 0.0
        if result.winner_metrics and result.loser_metrics:
            winner_ctr = result.winner_metrics.get('ctr', 0)
            loser_ctr = result.loser_metrics.get('ctr', 0)
            if loser_ctr > 0:
                improvement_pct = (winner_ctr - loser_ctr) / loser_ctr * 100

        message = f"""
🎉 A/B TEST WINNER AUTO-PROMOTED

Experiment: {result.experiment_id}
Winner Ad: {result.winner_ad_id}
Confidence: {result.confidence:.1%}

Performance:
- Winner CTR: {result.winner_metrics.get('ctr', 0):.2f}%
- Improvement: {improvement_pct:+.1f}%
- Budget Reallocation: 80% winner / 20% loser

Insights Extracted: {len(result.insights.winning_factors) if result.insights else 0} winning factors

Promoted at: {result.promoted_at}
"""
        return message

    async def _send_webhook_notification(self, message: str, result) -> None:
        """Send notification to webhook."""
        try:
            import aiohttp

            payload = {
                'text': message,
                'experiment_id': result.experiment_id,
                'winner_ad_id': result.winner_ad_id,
                'confidence': result.confidence,
                'promoted_at': result.promoted_at.isoformat() if result.promoted_at else None
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.notification_webhook, json=payload, timeout=10) as response:
                    if response.status == 200:
                        logger.info(f"Webhook notification sent for {result.experiment_id}")
                    else:
                        logger.warning(f"Webhook returned status {response.status}")

        except Exception as e:
            logger.error(f"Error sending webhook notification: {str(e)}")

    async def _send_daily_summary(self) -> None:
        """
        Send daily summary of promotion activity.

        Runs every day at 9 AM.
        """
        try:
            logger.info("Generating daily promotion summary...")

            # Get promotions from last 24 hours
            history = await self.auto_promoter.get_promotion_history(days_back=1)

            if not history:
                logger.info("No promotions in last 24 hours")
                return

            # Format summary
            total_promotions = len(history)
            avg_confidence = sum(h['confidence'] for h in history) / total_promotions if total_promotions > 0 else 0

            improvements = []
            for h in history:
                winner_ctr = h['winner_metrics'].get('ctr', 0)
                loser_ctr = h['loser_metrics'].get('ctr', 0)
                if loser_ctr > 0:
                    improvement = (winner_ctr - loser_ctr) / loser_ctr * 100
                    improvements.append(improvement)

            avg_improvement = sum(improvements) / len(improvements) if improvements else 0

            summary = f"""
📊 DAILY AUTO-PROMOTION SUMMARY

Date: {datetime.now().strftime('%Y-%m-%d')}

Promotions: {total_promotions}
Avg Confidence: {avg_confidence:.1%}
Avg Improvement: {avg_improvement:+.1f}%

Recent Winners:
"""
            for h in history[:5]:  # Top 5
                summary += f"\n  • {h['experiment_id']}: {h['confidence']:.1%} confidence"

            logger.info(summary)

            # Send to webhook if configured
            if self.notification_webhook:
                await self._send_webhook_notification(summary, None)

        except Exception as e:
            logger.error(f"Error generating daily summary: {str(e)}")

    async def _send_weekly_compound_report(self) -> None:
        """
        Send weekly compound learning report.

        Shows cumulative improvement from all A/B tests.
        Runs every Monday at 9 AM.
        """
        try:
            logger.info("Generating weekly compound learning report...")

            # Get cumulative improvement report
            report = await self.auto_promoter.get_cumulative_improvement_report()

            if 'error' in report:
                logger.error(f"Error generating report: {report['error']}")
                return

            # Format report
            summary = f"""
📈 WEEKLY COMPOUND LEARNING REPORT

Week ending: {datetime.now().strftime('%Y-%m-%d')}

CUMULATIVE PERFORMANCE:
- Total A/B Tests: {report.get('total_experiments', 0)}
- Successful Promotions: {report.get('successful_promotions', 0)}
- Compound Improvement: {report.get('compound_improvement_pct', 0):.1f}%
- Avg Improvement/Test: {report.get('avg_improvement_per_test', 0):.1f}%
- Avg Confidence: {report.get('avg_confidence', 0):.1%}

LEARNING VELOCITY:
Each test makes the next one better. Your campaigns are improving
by {report.get('compound_improvement_pct', 0):.1f}% through automated learning.

This is the power of compound gains! 🚀
"""
            logger.info(summary)

            # Send to webhook if configured
            if self.notification_webhook:
                await self._send_webhook_notification(summary, None)

        except Exception as e:
            logger.error(f"Error generating weekly compound report: {str(e)}")

    async def force_check_now(self) -> dict:
        """
        Force an immediate check (useful for testing or manual triggers).

        Returns:
            Dict with check results
        """
        logger.info("Manual auto-promotion check triggered")
        await self._check_and_promote_all()
        return {
            'status': 'completed',
            'triggered_at': datetime.now().isoformat()
        }

    def get_status(self) -> dict:
        """Get scheduler status."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            })

        return {
            'is_running': self.is_running,
            'check_interval_hours': self.check_interval_hours,
            'jobs': jobs,
            'scheduler_state': 'running' if self.is_running else 'stopped'
        }


# Global scheduler instance
auto_promotion_scheduler: Optional[AutoPromotionScheduler] = None


def initialize_scheduler(
    auto_promoter: AutoPromoter,
    check_interval_hours: int = 6,
    notification_webhook: Optional[str] = None
) -> AutoPromotionScheduler:
    """Initialize and start the global scheduler."""
    global auto_promotion_scheduler

    auto_promotion_scheduler = AutoPromotionScheduler(
        auto_promoter=auto_promoter,
        check_interval_hours=check_interval_hours,
        notification_webhook=notification_webhook
    )

    auto_promotion_scheduler.start()

    logger.info("Global AutoPromotionScheduler initialized and started")
    return auto_promotion_scheduler


def get_scheduler() -> Optional[AutoPromotionScheduler]:
    """Get the global scheduler instance."""
    return auto_promotion_scheduler
