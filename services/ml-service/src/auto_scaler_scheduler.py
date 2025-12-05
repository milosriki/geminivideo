"""
Auto-Scaler Scheduler
Part of Agent 47 - Auto-Scaling System

Runs hourly optimization for all active campaigns.
Can be triggered by:
- Cron job
- Celery beat
- Manual execution
"""

import logging
import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auto_scaler import BudgetAutoScaler, create_tables, ScalingRule
from time_optimizer import TimeBasedOptimizer

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://geminivideo:geminivideo@localhost:5432/geminivideo"
)


class AutoScalerScheduler:
    """
    Scheduler for running auto-scaling operations.
    """

    def __init__(self):
        """Initialize scheduler"""
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        self.db = Session()

        self.scaler = BudgetAutoScaler(db_session=self.db)
        self.time_optimizer = TimeBasedOptimizer(db_session=self.db)

        logger.info("AutoScalerScheduler initialized")

    async def run_hourly_optimization(self):
        """
        Run hourly optimization for all campaigns.
        """
        logger.info("=" * 80)
        logger.info("STARTING HOURLY AUTO-SCALING RUN")
        logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
        logger.info("=" * 80)

        try:
            # Get all enabled scaling rules
            rules = self.db.query(ScalingRule).filter_by(enabled=True).all()

            if not rules:
                logger.warning("No enabled scaling rules found")
                return {
                    "success": False,
                    "message": "No enabled scaling rules"
                }

            # Group by account
            accounts = {}
            for rule in rules:
                if rule.account_id not in accounts:
                    accounts[rule.account_id] = []
                accounts[rule.account_id].append(rule)

            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "accounts_processed": 0,
                "campaigns_evaluated": 0,
                "actions_executed": 0,
                "actions_pending_approval": 0,
                "errors": 0,
                "details": []
            }

            # Process each account
            for account_id, account_rules in accounts.items():
                logger.info(f"\n>>> Processing account: {account_id}")
                logger.info(f"    Rules: {len(account_rules)}")

                try:
                    # Get campaigns for this account
                    # In production, you'd query your campaign database or Meta API
                    # For now, we'll get campaigns from rules
                    campaign_ids = [r.campaign_id for r in account_rules if r.campaign_id]

                    if not campaign_ids:
                        logger.info(f"    No specific campaigns - would process all for account")
                        continue

                    summary["accounts_processed"] += 1

                    # Evaluate each campaign
                    for campaign_id in campaign_ids:
                        try:
                            logger.info(f"\n    >>> Evaluating campaign: {campaign_id}")

                            # Log performance snapshot for time-based learning
                            await self.scaler.log_performance_snapshot(campaign_id)

                            # Evaluate and potentially scale
                            result = await self.scaler.evaluate_and_scale(
                                campaign_id=campaign_id,
                                account_id=account_id
                            )

                            summary["campaigns_evaluated"] += 1

                            if result.get("success"):
                                if result.get("executed"):
                                    summary["actions_executed"] += 1
                                    logger.info(f"        ✅ Action executed: {result['action_type']}")
                                    logger.info(f"        Budget: ${result['budget_before']} -> ${result['budget_after']}")
                                elif result.get("requires_approval"):
                                    summary["actions_pending_approval"] += 1
                                    logger.info(f"        ⏳ Action pending approval: {result['action_type']}")
                                else:
                                    logger.info(f"        ℹ️  No action needed: {result['action_type']}")

                                summary["details"].append({
                                    "campaign_id": campaign_id,
                                    "status": "success",
                                    "action": result.get("action_type"),
                                    "executed": result.get("executed", False)
                                })
                            else:
                                logger.error(f"        ❌ Evaluation failed: {result.get('error')}")
                                summary["errors"] += 1
                                summary["details"].append({
                                    "campaign_id": campaign_id,
                                    "status": "error",
                                    "error": result.get("error")
                                })

                        except Exception as e:
                            logger.error(f"        ❌ Error evaluating campaign {campaign_id}: {e}")
                            summary["errors"] += 1
                            summary["details"].append({
                                "campaign_id": campaign_id,
                                "status": "error",
                                "error": str(e)
                            })

                except Exception as e:
                    logger.error(f"    ❌ Error processing account {account_id}: {e}")
                    summary["errors"] += 1

            logger.info("\n" + "=" * 80)
            logger.info("HOURLY AUTO-SCALING COMPLETE")
            logger.info(f"Accounts Processed: {summary['accounts_processed']}")
            logger.info(f"Campaigns Evaluated: {summary['campaigns_evaluated']}")
            logger.info(f"Actions Executed: {summary['actions_executed']}")
            logger.info(f"Actions Pending Approval: {summary['actions_pending_approval']}")
            logger.info(f"Errors: {summary['errors']}")
            logger.info("=" * 80)

            return summary

        except Exception as e:
            logger.error(f"Fatal error in hourly optimization: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def run_time_learning(self):
        """
        Run time-based learning for all campaigns.
        This should run daily to update optimal hour profiles.
        """
        logger.info("=" * 80)
        logger.info("STARTING TIME-BASED LEARNING")
        logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
        logger.info("=" * 80)

        try:
            # Learn optimal hours for all campaigns
            result = self.time_optimizer.bulk_learn_campaigns(min_samples=24)

            logger.info("\n" + "=" * 80)
            logger.info("TIME-BASED LEARNING COMPLETE")
            logger.info(f"Total Campaigns: {result['total_campaigns']}")
            logger.info(f"Learned: {result['learned']}")
            logger.info(f"Insufficient Data: {result['insufficient_data']}")
            logger.info(f"Errors: {result['errors']}")
            logger.info("=" * 80)

            return result

        except Exception as e:
            logger.error(f"Fatal error in time learning: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


async def main():
    """
    Main entry point for scheduler.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Auto-Scaler Scheduler")
    parser.add_argument(
        "--mode",
        choices=["optimize", "learn", "both"],
        default="optimize",
        help="Mode to run: optimize (hourly), learn (time-based), or both"
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database tables"
    )

    args = parser.parse_args()

    # Initialize database if requested
    if args.init_db:
        logger.info("Initializing database tables...")
        create_tables()
        logger.info("Database tables created")

    # Create scheduler
    scheduler = AutoScalerScheduler()

    # Run based on mode
    if args.mode == "optimize" or args.mode == "both":
        result = await scheduler.run_hourly_optimization()
        print("\n📊 OPTIMIZATION SUMMARY:")
        print(f"Campaigns Evaluated: {result.get('campaigns_evaluated', 0)}")
        print(f"Actions Executed: {result.get('actions_executed', 0)}")
        print(f"Pending Approval: {result.get('actions_pending_approval', 0)}")

    if args.mode == "learn" or args.mode == "both":
        result = await scheduler.run_time_learning()
        print("\n📈 LEARNING SUMMARY:")
        print(f"Campaigns Learned: {result.get('learned', 0)}")
        print(f"Insufficient Data: {result.get('insufficient_data', 0)}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(main())
