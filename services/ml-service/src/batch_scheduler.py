"""
Batch Scheduler - Automatic batch processing at optimal times

AGENT 42: 10x LEVERAGE - Batch Scheduling

Automatically processes batches at off-peak times (2 AM) for:
- Maximum cost savings
- Optimal resource utilization
- Minimal user impact

Features:
- Scheduled batch processing (cron-like)
- Smart batch size optimization
- Auto-retry on failure
- Notification on completion
"""

import asyncio
import logging
from datetime import datetime, time as dt_time
from typing import Optional
import signal
import sys
import os

from batch_processor import (
    BatchProcessor,
    BatchJobType,
    BatchProvider,
    BatchStatus
)
from alerts.alert_notifier import AlertNotifier, NotificationConfig, NotificationChannel

logger = logging.getLogger(__name__)


class BatchScheduler:
    """
    Automated batch processing scheduler.

    Runs batch jobs at scheduled times (default: 2 AM) for optimal cost savings.
    """

    def __init__(
        self,
        batch_processor: Optional[BatchProcessor] = None,
        schedule_time: dt_time = dt_time(2, 0),  # 2 AM
        check_interval_seconds: int = 60,  # Check every minute
        notifier: Optional[AlertNotifier] = None
    ):
        """
        Initialize batch scheduler.

        Args:
            batch_processor: BatchProcessor instance
            schedule_time: Time to run batches (default 2 AM)
            check_interval_seconds: How often to check schedule
            notifier: AlertNotifier instance for notifications
        """
        self.batch_processor = batch_processor or BatchProcessor()
        self.schedule_time = schedule_time
        self.check_interval_seconds = check_interval_seconds
        self.running = False
        self.last_run_date = None
        self.notifier = notifier or AlertNotifier()

        logger.info(f"BatchScheduler initialized (schedule: {schedule_time})")

    async def start(self):
        """Start the scheduler."""
        self.running = True
        logger.info("Batch scheduler started")

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            while self.running:
                await self._check_and_run()
                await asyncio.sleep(self.check_interval_seconds)
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
        finally:
            logger.info("Batch scheduler stopped")

    def stop(self):
        """Stop the scheduler."""
        logger.info("Stopping batch scheduler...")
        self.running = False

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    async def _check_and_run(self):
        """Check if it's time to run batches."""
        now = datetime.now()
        current_time = now.time()
        current_date = now.date()

        # Check if we're within the schedule window (±30 minutes)
        schedule_datetime = datetime.combine(current_date, self.schedule_time)
        time_diff = abs((now - schedule_datetime).total_seconds())

        # Run if within 30-minute window and haven't run today
        if time_diff <= 1800 and current_date != self.last_run_date:
            logger.info(f"Schedule triggered at {now}")
            await self._run_all_batches()
            self.last_run_date = current_date

    async def _run_all_batches(self):
        """
        Process all queued batches.

        This runs all pending jobs across all job types and providers.
        """
        logger.info("=" * 80)
        logger.info("BATCH PROCESSING STARTED")
        logger.info("=" * 80)

        start_time = datetime.now()
        total_jobs = 0
        total_batches = 0
        total_savings = 0.0

        # Get queue statistics
        queue_stats = self._get_queue_stats()
        logger.info(f"Queue statistics: {queue_stats}")

        # Process each job type and provider combination
        for job_type in BatchJobType:
            for provider in BatchProvider:
                try:
                    # Check if there are jobs to process
                    job_count = self.batch_processor.get_queued_job_count(job_type, provider)

                    if job_count > 0:
                        logger.info(f"Processing {job_count} jobs for {job_type.value}/{provider.value}")

                        # Process batch
                        batch_id = await self.batch_processor.process_batch(
                            job_type=job_type,
                            provider=provider,
                            max_jobs=1000  # Process up to 1000 jobs per batch
                        )

                        if batch_id:
                            total_jobs += job_count
                            total_batches += 1

                            # Get batch metadata to track savings
                            batch_info = await self.batch_processor.check_batch_status(batch_id)
                            savings = batch_info.get("cost_savings", 0.0)
                            total_savings += savings

                            logger.info(f"✅ Batch submitted: {batch_id} (${savings:.2f} savings)")
                        else:
                            logger.warning(f"Failed to submit batch for {job_type.value}/{provider.value}")

                except Exception as e:
                    logger.error(f"Error processing {job_type.value}/{provider.value}: {e}", exc_info=True)

        # Log summary
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 80)
        logger.info("BATCH PROCESSING COMPLETED")
        logger.info(f"Total batches: {total_batches}")
        logger.info(f"Total jobs: {total_jobs}")
        logger.info(f"Total savings: ${total_savings:.2f}")
        logger.info(f"Duration: {duration:.1f}s")
        logger.info("=" * 80)

        # Send notification (if configured)
        await self._send_notification(
            total_batches=total_batches,
            total_jobs=total_jobs,
            total_savings=total_savings,
            duration=duration
        )

    def _get_queue_stats(self) -> dict:
        """Get queue statistics."""
        stats = {}
        total = 0

        for job_type in BatchJobType:
            for provider in BatchProvider:
                count = self.batch_processor.get_queued_job_count(job_type, provider)
                if count > 0:
                    key = f"{job_type.value}/{provider.value}"
                    stats[key] = count
                    total += count

        stats["total"] = total
        return stats

    async def _send_notification(
        self,
        total_batches: int,
        total_jobs: int,
        total_savings: float,
        duration: float
    ):
        """
        Send notification about batch completion.

        Args:
            total_batches: Number of batches processed
            total_jobs: Number of jobs processed
            total_savings: Total cost savings
            duration: Processing duration
        """
        try:
            message = f"""🎯 Batch Processing Complete

📊 Summary:
- Batches: {total_batches}
- Jobs: {total_jobs}
- Cost Savings: ${total_savings:.2f}
- Duration: {duration:.1f}s

⏰ Next run: Tomorrow at {self.schedule_time}
"""
            logger.info(f"Notification: {message}")

            # Send notifications via configured channels
            alert_data = {
                "title": "Batch Processing Complete",
                "message": message,
                "severity": "info",
                "category": "batch_processing",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "total_batches": total_batches,
                    "total_jobs": total_jobs,
                    "cost_savings": total_savings,
                    "duration_seconds": duration
                }
            }

            # Send to Slack and Email if configured
            channels = [NotificationChannel.SLACK, NotificationChannel.EMAIL]
            await self.notifier.notify(alert_data, channels=channels)

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    # ========================================================================
    # MANUAL TRIGGER
    # ========================================================================

    async def run_now(self):
        """
        Manually trigger batch processing (outside schedule).

        Useful for:
        - Testing
        - Emergency processing
        - On-demand batch runs
        """
        logger.info("Manual batch processing triggered")
        await self._run_all_batches()

    async def run_specific_batch(
        self,
        job_type: BatchJobType,
        provider: BatchProvider
    ) -> Optional[str]:
        """
        Manually process a specific batch type.

        Args:
            job_type: Type of jobs to process
            provider: API provider

        Returns:
            Batch ID
        """
        logger.info(f"Manual batch processing: {job_type.value}/{provider.value}")

        batch_id = await self.batch_processor.process_batch(
            job_type=job_type,
            provider=provider
        )

        if batch_id:
            logger.info(f"Batch submitted: {batch_id}")
        else:
            logger.warning("No jobs to process or batch submission failed")

        return batch_id

    # ========================================================================
    # BATCH MONITORING
    # ========================================================================

    async def monitor_active_batches(self):
        """
        Monitor active batches and update their status.

        This should run periodically to check batch completion.
        """
        active_batches = self.batch_processor.get_active_batches()

        if not active_batches:
            logger.debug("No active batches to monitor")
            return

        logger.info(f"Monitoring {len(active_batches)} active batches")

        for batch in active_batches:
            batch_id = batch["batch_id"]

            try:
                # Check status
                status = await self.batch_processor.check_batch_status(batch_id)

                if status.get("status") == "completed":
                    logger.info(f"✅ Batch completed: {batch_id}")

                    # Retrieve and process results
                    results = await self.batch_processor.retrieve_batch_results(batch_id)
                    logger.info(f"Retrieved {len(results)} results from {batch_id}")

                    # Process results: store in database and trigger callbacks
                    try:
                        await self._process_batch_results(batch_id, batch, results)
                        logger.info(f"Successfully processed results for batch {batch_id}")
                    except Exception as e:
                        logger.error(f"Error processing results for batch {batch_id}: {e}", exc_info=True)

                elif status.get("status") == "failed":
                    logger.error(f"❌ Batch failed: {batch_id}")

                    # Handle failure: retry or notify
                    try:
                        await self._handle_batch_failure(batch_id, batch, status)
                    except Exception as e:
                        logger.error(f"Error handling failure for batch {batch_id}: {e}", exc_info=True)

                else:
                    logger.debug(f"⏳ Batch in progress: {batch_id} ({status.get('status')})")

            except Exception as e:
                logger.error(f"Error monitoring batch {batch_id}: {e}", exc_info=True)

    async def start_monitoring_loop(self):
        """
        Start continuous monitoring of active batches.

        This runs in parallel with the scheduler to check batch completion.
        """
        logger.info("Starting batch monitoring loop")

        try:
            while self.running:
                await self.monitor_active_batches()
                await asyncio.sleep(300)  # Check every 5 minutes
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}", exc_info=True)

    async def _process_batch_results(self, batch_id: str, batch: dict, results: list):
        """
        Process completed batch results.

        Args:
            batch_id: Batch ID
            batch: Batch metadata
            results: List of batch results
        """
        from shared.db.connection import get_db_context
        from sqlalchemy import text

        job_type = batch.get("job_type")
        logger.info(f"Processing {len(results)} results for batch {batch_id} (type: {job_type})")

        # Store results in database
        async with get_db_context() as db:
            for result in results:
                try:
                    # Store based on job type
                    if job_type == "ctr_prediction":
                        # Update predictions table
                        await db.execute(
                            text("""
                                INSERT INTO batch_results (batch_id, job_type, result_data, created_at)
                                VALUES (:batch_id, :job_type, :result_data, NOW())
                            """),
                            {
                                "batch_id": batch_id,
                                "job_type": job_type,
                                "result_data": str(result)
                            }
                        )
                    # Add more job types as needed
                except Exception as e:
                    logger.error(f"Error storing result: {e}")

            await db.commit()

        # Send success notification
        alert_data = {
            "title": f"Batch {batch_id} Completed",
            "message": f"Successfully processed {len(results)} results from batch {batch_id}",
            "severity": "info",
            "category": "batch_completion",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "batch_id": batch_id,
                "job_type": job_type,
                "result_count": len(results)
            }
        }
        await self.notifier.notify(alert_data, channels=[NotificationChannel.DATABASE])

    async def _handle_batch_failure(self, batch_id: str, batch: dict, status: dict):
        """
        Handle failed batch processing.

        Args:
            batch_id: Batch ID
            batch: Batch metadata
            status: Batch status information
        """
        job_type = batch.get("job_type")
        retry_count = batch.get("retry_count", 0)
        max_retries = int(os.getenv("BATCH_MAX_RETRIES", "3"))

        logger.error(f"Batch {batch_id} failed (retry {retry_count}/{max_retries})")

        # Retry logic
        if retry_count < max_retries:
            logger.info(f"Scheduling retry for batch {batch_id}")
            # Update batch metadata with retry count
            batch["retry_count"] = retry_count + 1

            # Resubmit batch after delay
            await asyncio.sleep(60 * (retry_count + 1))  # Exponential backoff

            # Resubmit using batch processor
            try:
                provider = BatchProvider(batch.get("provider", "openai"))
                job_type_enum = BatchJobType(job_type)
                new_batch_id = await self.batch_processor.process_batch(
                    job_type=job_type_enum,
                    provider=provider
                )
                logger.info(f"Resubmitted as batch {new_batch_id}")
            except Exception as e:
                logger.error(f"Failed to resubmit batch: {e}")
        else:
            # Max retries exceeded - send alert
            logger.error(f"Batch {batch_id} exceeded max retries ({max_retries})")

        # Send failure notification
        alert_data = {
            "title": f"Batch {batch_id} Failed",
            "message": f"Batch {batch_id} failed after {retry_count} retries. Error: {status.get('error', 'Unknown error')}",
            "severity": "high",
            "category": "batch_failure",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "batch_id": batch_id,
                "job_type": job_type,
                "retry_count": retry_count,
                "error": status.get("error", "Unknown error")
            }
        }
        await self.notifier.notify(
            alert_data,
            channels=[NotificationChannel.SLACK, NotificationChannel.EMAIL, NotificationChannel.DATABASE]
        )


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """Main entry point for batch scheduler."""
    import argparse

    parser = argparse.ArgumentParser(description="Batch API Scheduler")
    parser.add_argument(
        "--schedule-time",
        type=str,
        default="02:00",
        help="Schedule time in HH:MM format (default: 02:00)"
    )
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run batch processing immediately and exit"
    )
    parser.add_argument(
        "--job-type",
        type=str,
        choices=[jt.value for jt in BatchJobType],
        help="Process specific job type only (use with --run-now)"
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=[p.value for p in BatchProvider],
        help="Process specific provider only (use with --run-now)"
    )
    parser.add_argument(
        "--monitor-only",
        action="store_true",
        help="Only monitor active batches (no scheduling)"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Parse schedule time
    hour, minute = map(int, args.schedule_time.split(':'))
    schedule_time = dt_time(hour, minute)

    # Initialize scheduler
    scheduler = BatchScheduler(schedule_time=schedule_time)

    if args.run_now:
        # Run immediately and exit
        if args.job_type and args.provider:
            job_type = BatchJobType(args.job_type)
            provider = BatchProvider(args.provider)
            await scheduler.run_specific_batch(job_type, provider)
        else:
            await scheduler.run_now()
        return

    if args.monitor_only:
        # Only monitor active batches
        scheduler.running = True
        await scheduler.start_monitoring_loop()
        return

    # Start scheduler with monitoring
    tasks = [
        scheduler.start(),
        scheduler.start_monitoring_loop()
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
