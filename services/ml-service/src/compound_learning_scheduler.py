"""
Compound Learning Scheduler - Agent 50
Daily Learning Cycle Automation

Runs the compound learning cycle every day at 3 AM to:
- Process all new performance data
- Extract patterns and insights
- Update knowledge base
- Retrain models if needed
- Track compound improvement

This is the engine of exponential growth - running silently every night
to make the system 10x better over 365 days.
"""

import logging
import schedule
import time
import threading
import asyncio
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CompoundLearningScheduler:
    """Automated compound learning cycle scheduler"""

    def __init__(self, run_time: str = "03:00"):
        """
        Initialize compound learning scheduler

        Args:
            run_time: Time to run daily (HH:MM format, 24h)
        """
        self.run_time = run_time
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.last_run: Optional[datetime] = None
        self.total_cycles = 0

    async def run_learning_cycle(self, account_id: Optional[str] = None):
        """
        Run the compound learning cycle

        Args:
            account_id: Optional account to focus on (None = all accounts)
        """
        logger.info("🌙 Starting nightly compound learning cycle...")
        logger.info(f"   Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

        try:
            # Import here to avoid circular dependencies
            from src.compound_learner import compound_learner

            # Run the learning cycle
            result = await compound_learner.learning_cycle(account_id=account_id)

            # Log results
            logger.info("✅ Compound learning cycle completed!")
            logger.info(f"   Cycle ID: {result.cycle_id}")
            logger.info(f"   Status: {result.status}")
            logger.info(f"   Duration: {result.duration_seconds:.2f}s")
            logger.info(f"   New data points: {result.new_data_points}")
            logger.info(f"   New patterns: {result.new_patterns}")
            logger.info(f"   New knowledge nodes: {result.new_knowledge_nodes}")
            logger.info(f"   Models retrained: {result.models_retrained}")
            logger.info(f"   Improvement rate: {result.improvement_rate:.2%}")
            logger.info(f"   Cumulative improvement: {result.cumulative_improvement:.2%}")

            # Update stats
            self.last_run = datetime.utcnow()
            self.total_cycles += 1

            # Also create daily snapshots for all accounts
            await self._create_daily_snapshots()

            logger.info("🎯 System is getting smarter every day!")
            logger.info(f"   Total learning cycles completed: {self.total_cycles}")

            return result

        except Exception as e:
            logger.error(f"❌ Error in compound learning cycle: {e}", exc_info=True)
            return None

    async def _create_daily_snapshots(self):
        """Create daily improvement snapshots for all accounts"""
        try:
            from src.compound_learner import compound_learner

            # Get all unique account IDs
            # In production, would query from database
            # For now, this is a placeholder
            logger.info("Creating daily improvement snapshots...")

        except Exception as e:
            logger.error(f"Error creating daily snapshots: {e}")

    def run_learning_cycle_sync(self):
        """Synchronous wrapper for async learning cycle"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Run the async function
            loop.run_until_complete(self.run_learning_cycle())

            # Close the loop
            loop.close()

        except Exception as e:
            logger.error(f"Error in sync learning cycle wrapper: {e}", exc_info=True)

    def start(self):
        """Start the scheduler in a background thread"""
        if self.is_running:
            logger.warning("Compound learning scheduler already running")
            return

        logger.info(f"🚀 Starting compound learning scheduler")
        logger.info(f"   Daily run time: {self.run_time} UTC")
        logger.info(f"   This will run every night to make the system 10x better!")

        # Schedule the daily job
        schedule.every().day.at(self.run_time).do(self.run_learning_cycle_sync)

        # Run in background thread
        self.is_running = True
        self.thread = threading.Thread(target=self._run_schedule, daemon=True)
        self.thread.start()

        logger.info("✅ Compound learning scheduler started")
        logger.info("   The system will now improve exponentially every day")

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
        logger.info("Compound learning scheduler stopped")

    def run_now(self):
        """Run the learning cycle immediately (for testing)"""
        logger.info("🔥 Running learning cycle immediately (manual trigger)...")
        self.run_learning_cycle_sync()

    def get_stats(self) -> dict:
        """Get scheduler statistics"""
        return {
            'is_running': self.is_running,
            'run_time': self.run_time,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'total_cycles': self.total_cycles,
            'next_run': self._get_next_run_time()
        }

    def _get_next_run_time(self) -> Optional[str]:
        """Get next scheduled run time"""
        try:
            jobs = schedule.get_jobs()
            if jobs:
                next_run = jobs[0].next_run
                if next_run:
                    return next_run.isoformat()
        except:
            pass
        return None


# Global instance
compound_learning_scheduler = CompoundLearningScheduler(run_time="03:00")
