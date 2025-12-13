"""
Intelligent Auto-Scaling for Campaign Budgets
Agent 47 of 50 - 10X LEVERAGE

Automatically scales campaign budgets based on performance metrics:
- Performance-based scaling (ROAS, CTR)
- Time-based optimization (learn peak hours)
- Safety controls (limits, thresholds, approvals)
- Compound scaling effects
- Real-time opportunity capture

This is the ULTIMATE 10X leverage - automatically scale winners,
pause losers, and capture opportunities while they're hot.
"""

import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, JSON, Boolean, Numeric, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import sys
import json

# Import Meta API integration
sys.path.append(os.path.join(os.path.dirname(__file__), '../../titan-core'))
from meta.marketing_api import RealMetaAdsManager

logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://geminivideo:geminivideo@localhost:5432/geminivideo"
)

Base = declarative_base()


# ==================== ENUMS ====================

class ScalingAction(Enum):
    """Types of scaling actions"""
    SCALE_UP_AGGRESSIVE = "scale_up_aggressive"  # 50% increase
    SCALE_UP = "scale_up"  # 20% increase
    MAINTAIN = "maintain"  # No change
    SCALE_DOWN = "scale_down"  # 30% decrease
    PAUSE = "pause"  # Pause campaign
    REACTIVATE = "reactivate"  # Reactivate paused campaign


class ScalingStatus(Enum):
    """Status of scaling execution"""
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTED = "executed"
    FAILED = "failed"
    REJECTED = "rejected"


# ==================== DATABASE MODELS ====================

class ScalingRule(Base):
    """Auto-scaling rules configuration"""
    __tablename__ = "scaling_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, nullable=False, index=True)
    campaign_id = Column(String, nullable=True, index=True)  # Null = applies to all campaigns

    # Rule configuration
    rule_name = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)

    # Performance thresholds
    roas_scale_up_aggressive = Column(Float, default=4.0)
    roas_scale_up = Column(Float, default=3.0)
    roas_scale_down = Column(Float, default=1.5)
    roas_pause = Column(Float, default=1.0)

    ctr_threshold = Column(Float, default=0.03)  # 3% CTR requirement for aggressive scaling
    min_impressions = Column(Integer, default=1000)  # Minimum data before scaling

    # Scaling multipliers
    multiplier_aggressive_up = Column(Float, default=1.5)  # 50% increase
    multiplier_up = Column(Float, default=1.2)  # 20% increase
    multiplier_down = Column(Float, default=0.7)  # 30% decrease

    # Safety limits
    max_daily_budget = Column(Numeric(10, 2), nullable=True)
    min_daily_budget = Column(Numeric(10, 2), default=10.00)
    max_daily_spend_limit = Column(Numeric(10, 2), nullable=True)

    # Approval requirements
    require_approval_threshold = Column(Numeric(10, 2), default=500.00)  # Require approval for budgets > $500
    auto_approve_up_to = Column(Numeric(10, 2), default=100.00)  # Auto-approve increases up to $100

    # Time-based settings
    enable_time_optimization = Column(Boolean, default=True)
    peak_hours_multiplier = Column(Float, default=1.3)  # 30% increase during peaks

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    config = Column(JSON, default={})


class ScalingAction(Base):
    """Record of all scaling actions"""
    __tablename__ = "scaling_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, nullable=False, index=True)
    campaign_id = Column(String, nullable=False, index=True)

    # Action details
    action_type = Column(String, nullable=False, index=True)  # ScalingAction enum value
    status = Column(String, default=ScalingStatus.PENDING.value, index=True)

    # Budget changes
    budget_before = Column(Numeric(10, 2), nullable=False)
    budget_after = Column(Numeric(10, 2), nullable=False)
    budget_change_pct = Column(Float, nullable=False)
    multiplier = Column(Float, nullable=False)

    # Performance metrics that triggered action
    roas = Column(Float, nullable=False)
    ctr = Column(Float, nullable=False)
    spend_24h = Column(Numeric(10, 2), nullable=False)
    revenue_24h = Column(Numeric(10, 2), nullable=False)
    impressions_24h = Column(Integer, nullable=False)
    clicks_24h = Column(Integer, nullable=False)
    conversions_24h = Column(Integer, default=0)

    # Reasoning
    reasoning = Column(Text, nullable=False)
    rule_id = Column(Integer, nullable=True)  # Reference to ScalingRule

    # Approval workflow
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_reason = Column(Text, nullable=True)

    # Execution
    executed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(JSON, default={})


class CampaignPerformanceSnapshot(Base):
    """Hourly performance snapshots for learning patterns"""
    __tablename__ = "campaign_performance_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(String, nullable=False, index=True)

    # Timestamp
    snapshot_time = Column(DateTime, nullable=False, index=True)
    hour_of_day = Column(Integer, nullable=False)  # 0-23
    day_of_week = Column(Integer, nullable=False)  # 0-6 (Monday = 0)

    # Performance metrics
    roas = Column(Float, nullable=False)
    ctr = Column(Float, nullable=False)
    conversion_rate = Column(Float, default=0.0)
    spend_hourly = Column(Numeric(10, 2), nullable=False)
    revenue_hourly = Column(Numeric(10, 2), nullable=False)

    # Volume metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)

    # Budget at time of snapshot
    daily_budget = Column(Numeric(10, 2), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)


class OptimalHourProfile(Base):
    """Learned optimal hours for each campaign"""
    __tablename__ = "optimal_hour_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(String, nullable=False, unique=True, index=True)

    # Hour profiles (0-23)
    hour_performance = Column(JSON, nullable=False)  # {hour: avg_roas, ctr, etc.}
    peak_hours = Column(JSON, nullable=False)  # List of high-performing hours
    valley_hours = Column(JSON, nullable=False)  # List of low-performing hours

    # Learning metadata
    samples_count = Column(Integer, default=0)
    last_learned = Column(DateTime, default=datetime.utcnow)
    confidence_score = Column(Float, default=0.0)  # 0-1

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================== CORE AUTO-SCALER ====================

@dataclass
class CampaignMetrics:
    """24-hour campaign performance metrics"""
    campaign_id: str
    impressions: int
    clicks: int
    spend: float
    revenue: float
    conversions: int
    daily_budget: float
    ctr: float
    roas: float
    conversion_rate: float
    current_hour: int


class BudgetAutoScaler:
    """
    Intelligent auto-scaling engine for campaign budgets.

    Automatically adjusts budgets based on:
    - Real-time ROAS performance
    - CTR and engagement metrics
    - Time-of-day patterns
    - Historical performance
    - Safety limits and rules
    """

    def __init__(
        self,
        meta_access_token: str = None,
        ad_account_id: str = None,
        db_session: Session = None
    ):
        """
        Initialize auto-scaler.

        Args:
            meta_access_token: Meta API access token
            ad_account_id: Meta ad account ID
            db_session: Database session (optional, will create if not provided)
        """
        # Meta API client
        self.meta_access_token = meta_access_token or os.getenv("META_ACCESS_TOKEN")
        self.ad_account_id = ad_account_id or os.getenv("META_AD_ACCOUNT_ID")

        if self.meta_access_token and self.ad_account_id:
            self.meta_api = RealMetaAdsManager(
                access_token=self.meta_access_token,
                ad_account_id=self.ad_account_id
            )
            logger.info(f"Meta API initialized for account {self.ad_account_id}")
        else:
            self.meta_api = None
            logger.warning("Meta API not initialized - set META_ACCESS_TOKEN and META_AD_ACCOUNT_ID")

        # Database
        if db_session:
            self.db = db_session
        else:
            engine = create_engine(DATABASE_URL)
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            self.db = Session()

        logger.info("BudgetAutoScaler initialized")

    async def get_24h_metrics(self, campaign_id: str) -> Optional[CampaignMetrics]:
        """
        Fetch 24-hour performance metrics from Meta API.

        Args:
            campaign_id: Meta campaign ID

        Returns:
            CampaignMetrics object or None if error
        """
        if not self.meta_api:
            logger.error("Meta API not initialized")
            return None

        try:
            # Get campaign insights for last 24 hours
            insights = self.meta_api.get_campaign_insights(
                campaign_id=campaign_id,
                fields=[
                    'impressions', 'clicks', 'spend', 'reach', 'frequency',
                    'ctr', 'actions', 'action_values', 'conversions'
                ],
                date_preset='last_24_hours'
            )

            if not insights or len(insights) == 0:
                logger.warning(f"No insights data for campaign {campaign_id}")
                return None

            # Aggregate insights (should be single record for 24h)
            data = insights[0]

            # Get current campaign details
            campaign_info = self.meta_api.get_campaign(campaign_id)
            daily_budget = float(campaign_info.get('daily_budget', 0)) / 100  # Convert cents to dollars

            # Extract metrics
            impressions = int(data.get('impressions', 0))
            clicks = int(data.get('clicks', 0))
            spend = float(data.get('spend', 0))

            # Calculate CTR
            ctr = clicks / impressions if impressions > 0 else 0.0

            # Get conversions and revenue from actions
            actions = data.get('actions', [])
            action_values = data.get('action_values', [])

            conversions = 0
            revenue = 0.0

            for action in actions:
                if action.get('action_type') in ['purchase', 'offsite_conversion.fb_pixel_purchase']:
                    conversions += int(action.get('value', 0))

            for action_value in action_values:
                if action_value.get('action_type') in ['purchase', 'offsite_conversion.fb_pixel_purchase']:
                    revenue += float(action_value.get('value', 0))

            # Calculate ROAS
            roas = revenue / spend if spend > 0 else 0.0

            # Calculate conversion rate
            conversion_rate = conversions / clicks if clicks > 0 else 0.0

            # Get current hour
            current_hour = datetime.utcnow().hour

            return CampaignMetrics(
                campaign_id=campaign_id,
                impressions=impressions,
                clicks=clicks,
                spend=spend,
                revenue=revenue,
                conversions=conversions,
                daily_budget=daily_budget,
                ctr=ctr,
                roas=roas,
                conversion_rate=conversion_rate,
                current_hour=current_hour
            )

        except Exception as e:
            logger.error(f"Error fetching metrics for campaign {campaign_id}: {e}")
            return None

    def get_scaling_rule(self, account_id: str, campaign_id: str = None) -> ScalingRule:
        """
        Get applicable scaling rule for campaign.

        Args:
            account_id: Ad account ID
            campaign_id: Campaign ID (optional)

        Returns:
            ScalingRule object (campaign-specific or account default)
        """
        # Try campaign-specific rule first
        if campaign_id:
            rule = self.db.query(ScalingRule).filter_by(
                account_id=account_id,
                campaign_id=campaign_id,
                enabled=True
            ).first()

            if rule:
                return rule

        # Fall back to account-level default rule
        rule = self.db.query(ScalingRule).filter_by(
            account_id=account_id,
            campaign_id=None,
            enabled=True
        ).first()

        if rule:
            return rule

        # Create default rule if none exists
        logger.info(f"Creating default scaling rule for account {account_id}")
        default_rule = ScalingRule(
            account_id=account_id,
            campaign_id=None,
            rule_name="Default Auto-Scaling Rule",
            enabled=True
        )
        self.db.add(default_rule)
        self.db.commit()

        return default_rule

    def determine_scaling_action(
        self,
        metrics: CampaignMetrics,
        rule: ScalingRule
    ) -> Tuple[str, float, str]:
        """
        Determine what scaling action to take based on metrics and rules.

        Args:
            metrics: Campaign performance metrics
            rule: Scaling rule configuration

        Returns:
            Tuple of (action_type, multiplier, reasoning)
        """
        # Check minimum data threshold
        if metrics.impressions < rule.min_impressions:
            return (
                ScalingAction.MAINTAIN.value,
                1.0,
                f"Insufficient data: {metrics.impressions} impressions < {rule.min_impressions} threshold"
            )

        # AGGRESSIVE SCALE UP: ROAS > 4x AND CTR > 3%
        if metrics.roas >= rule.roas_scale_up_aggressive and metrics.ctr >= rule.ctr_threshold:
            return (
                ScalingAction.SCALE_UP_AGGRESSIVE.value,
                rule.multiplier_aggressive_up,
                f"Exceptional performance: ROAS {metrics.roas:.2f}x (>{rule.roas_scale_up_aggressive}x) and CTR {metrics.ctr*100:.2f}% (>{rule.ctr_threshold*100}%)"
            )

        # SCALE UP: ROAS > 3x
        if metrics.roas >= rule.roas_scale_up:
            return (
                ScalingAction.SCALE_UP.value,
                rule.multiplier_up,
                f"Strong performance: ROAS {metrics.roas:.2f}x (>{rule.roas_scale_up}x)"
            )

        # SCALE DOWN: ROAS < 1.5x
        if metrics.roas < rule.roas_scale_down and metrics.roas >= rule.roas_pause:
            return (
                ScalingAction.SCALE_DOWN.value,
                rule.multiplier_down,
                f"Underperforming: ROAS {metrics.roas:.2f}x (<{rule.roas_scale_down}x)"
            )

        # PAUSE: ROAS < 1x
        if metrics.roas < rule.roas_pause:
            return (
                ScalingAction.PAUSE.value,
                0.0,
                f"Critical underperformance: ROAS {metrics.roas:.2f}x (<{rule.roas_pause}x) - pausing to stop losses"
            )

        # MAINTAIN: Everything else
        return (
            ScalingAction.MAINTAIN.value,
            1.0,
            f"Performance within normal range: ROAS {metrics.roas:.2f}x"
        )

    def calculate_new_budget(
        self,
        current_budget: float,
        multiplier: float,
        rule: ScalingRule
    ) -> float:
        """
        Calculate new budget with safety limits applied.

        Args:
            current_budget: Current daily budget
            multiplier: Scaling multiplier
            rule: Scaling rule with limits

        Returns:
            New budget amount (respecting min/max limits)
        """
        new_budget = current_budget * multiplier

        # Apply minimum budget
        if new_budget < float(rule.min_daily_budget):
            new_budget = float(rule.min_daily_budget)

        # Apply maximum budget if set
        if rule.max_daily_budget and new_budget > float(rule.max_daily_budget):
            new_budget = float(rule.max_daily_budget)

        return round(new_budget, 2)

    def requires_approval(
        self,
        new_budget: float,
        current_budget: float,
        rule: ScalingRule
    ) -> bool:
        """
        Check if budget change requires manual approval.

        Args:
            new_budget: Proposed new budget
            current_budget: Current budget
            rule: Scaling rule with approval thresholds

        Returns:
            True if approval required
        """
        # Check absolute budget threshold
        if new_budget > float(rule.require_approval_threshold):
            return True

        # Check increase amount threshold
        increase = new_budget - current_budget
        if increase > float(rule.auto_approve_up_to):
            return True

        return False

    async def evaluate_and_scale(self, campaign_id: str, account_id: str = None) -> Dict[str, Any]:
        """
        Evaluate campaign performance and execute scaling action.

        Args:
            campaign_id: Meta campaign ID
            account_id: Ad account ID (defaults to instance account)

        Returns:
            Dictionary with action details and results
        """
        logger.info(f"Evaluating campaign {campaign_id} for auto-scaling")

        account_id = account_id or self.ad_account_id

        # Get performance metrics
        metrics = await self.get_24h_metrics(campaign_id)

        if not metrics:
            logger.error(f"Failed to fetch metrics for campaign {campaign_id}")
            return {
                "success": False,
                "error": "Failed to fetch campaign metrics"
            }

        # Get scaling rule
        rule = self.get_scaling_rule(account_id, campaign_id)

        # Determine action
        action_type, multiplier, reasoning = self.determine_scaling_action(metrics, rule)

        # Calculate new budget
        new_budget = self.calculate_new_budget(
            metrics.daily_budget,
            multiplier,
            rule
        )

        budget_change_pct = ((new_budget - metrics.daily_budget) / metrics.daily_budget * 100) if metrics.daily_budget > 0 else 0

        # Check if approval required
        needs_approval = self.requires_approval(new_budget, metrics.daily_budget, rule)

        # Create scaling action record
        scaling_action = ScalingAction(
            account_id=account_id,
            campaign_id=campaign_id,
            action_type=action_type,
            status=ScalingStatus.PENDING.value if needs_approval else ScalingStatus.APPROVED.value,
            budget_before=metrics.daily_budget,
            budget_after=new_budget,
            budget_change_pct=budget_change_pct,
            multiplier=multiplier,
            roas=metrics.roas,
            ctr=metrics.ctr,
            spend_24h=metrics.spend,
            revenue_24h=metrics.revenue,
            impressions_24h=metrics.impressions,
            clicks_24h=metrics.clicks,
            conversions_24h=metrics.conversions,
            reasoning=reasoning,
            rule_id=rule.id,
            requires_approval=needs_approval
        )

        self.db.add(scaling_action)
        self.db.commit()

        result = {
            "success": True,
            "action_id": scaling_action.id,
            "campaign_id": campaign_id,
            "action_type": action_type,
            "budget_before": float(metrics.daily_budget),
            "budget_after": float(new_budget),
            "budget_change_pct": budget_change_pct,
            "multiplier": multiplier,
            "reasoning": reasoning,
            "requires_approval": needs_approval,
            "metrics": {
                "roas": metrics.roas,
                "ctr": metrics.ctr,
                "spend": metrics.spend,
                "revenue": metrics.revenue,
                "impressions": metrics.impressions,
                "clicks": metrics.clicks,
                "conversions": metrics.conversions
            }
        }

        # Execute immediately if no approval needed
        if not needs_approval and multiplier != 1.0:
            execution_result = await self.execute_scaling_action(scaling_action.id)
            result["executed"] = execution_result.get("success", False)
            result["execution_details"] = execution_result
        else:
            result["executed"] = False
            if needs_approval:
                result["message"] = "Action pending approval"
            else:
                result["message"] = "No budget change needed"

        return result

    async def execute_scaling_action(self, action_id: int) -> Dict[str, Any]:
        """
        Execute a scaling action (update budget in Meta).

        Args:
            action_id: Scaling action ID

        Returns:
            Execution result dictionary
        """
        action = self.db.query(ScalingAction).filter_by(id=action_id).first()

        if not action:
            return {"success": False, "error": "Action not found"}

        if action.status == ScalingStatus.EXECUTED.value:
            return {"success": False, "error": "Action already executed"}

        if action.requires_approval and action.status != ScalingStatus.APPROVED.value:
            return {"success": False, "error": "Action requires approval"}

        try:
            # Execute based on action type
            if action.action_type == ScalingAction.PAUSE.value:
                # Pause campaign
                self.meta_api.pause_campaign(action.campaign_id)
                logger.info(f"Paused campaign {action.campaign_id}")

            elif action.action_type == ScalingAction.REACTIVATE.value:
                # Reactivate campaign
                self.meta_api.activate_campaign(action.campaign_id)
                logger.info(f"Reactivated campaign {action.campaign_id}")

            elif action.multiplier != 1.0:
                # Update budget
                new_budget_cents = int(float(action.budget_after) * 100)
                self.meta_api.update_budget(action.campaign_id, new_budget_cents)
                logger.info(f"Updated budget for campaign {action.campaign_id}: ${action.budget_before} -> ${action.budget_after}")

            # Mark as executed
            action.status = ScalingStatus.EXECUTED.value
            action.executed_at = datetime.utcnow()
            self.db.commit()

            return {
                "success": True,
                "action_id": action_id,
                "campaign_id": action.campaign_id,
                "budget_before": float(action.budget_before),
                "budget_after": float(action.budget_after),
                "executed_at": action.executed_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to execute scaling action {action_id}: {e}")
            action.status = ScalingStatus.FAILED.value
            action.error_message = str(e)
            self.db.commit()

            return {
                "success": False,
                "error": str(e)
            }

    async def run_hourly_optimization(self, account_id: str = None) -> Dict[str, Any]:
        """
        Run auto-scaling for all active campaigns.

        Args:
            account_id: Ad account ID (defaults to instance account)

        Returns:
            Summary of actions taken
        """
        logger.info("Starting hourly optimization run")

        account_id = account_id or self.ad_account_id

        if not self.meta_api:
            return {"success": False, "error": "Meta API not initialized"}

        try:
            # Get all active campaigns from database
            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "account_id": account_id,
                "campaigns_evaluated": 0,
                "actions_taken": 0,
                "actions_pending_approval": 0,
                "errors": 0,
                "details": []
            }

            # Get active campaigns from scaling rules or performance snapshots
            # Query recent campaigns that have been actively tracked
            try:
                # Import Campaign model if available
                sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'shared'))
                from db.models import Campaign, PerformanceMetric
                
                # Get campaigns with recent activity (last 7 days)
                recent_date = datetime.utcnow() - timedelta(days=7)
                
                # Query campaigns from performance_metrics table
                campaign_ids = self.db.query(PerformanceMetric.campaign_id).distinct()\
                    .filter(PerformanceMetric.created_at >= recent_date)\
                    .filter(PerformanceMetric.campaign_id.isnot(None))\
                    .all()
                
                campaign_ids = [cid[0] for cid in campaign_ids if cid[0]]
                
                logger.info(f"Found {len(campaign_ids)} campaigns with recent activity")
                
            except Exception as e:
                logger.warning(f"Could not query campaigns from database: {e}")
                # Fallback: Get campaigns from scaling_rules
                try:
                    rule_campaigns = self.db.query(ScalingRule.campaign_id).distinct()\
                        .filter(ScalingRule.account_id == account_id)\
                        .filter(ScalingRule.enabled == True)\
                        .filter(ScalingRule.campaign_id.isnot(None))\
                        .all()
                    campaign_ids = [cid[0] for cid in rule_campaigns if cid[0]]
                    logger.info(f"Using {len(campaign_ids)} campaigns from scaling rules")
                except Exception as e2:
                    logger.error(f"Could not get campaigns from scaling rules: {e2}")
                    campaign_ids = []

            # Evaluate each campaign for scaling opportunities
            for campaign_id in campaign_ids:
                try:
                    recommendation = await self.recommend_scaling_action(account_id, campaign_id)
                    
                    results["campaigns_evaluated"] += 1
                    
                    if recommendation["action"] != ScalingAction.MAINTAIN.value:
                        # Create scaling action
                        action_result = await self.execute_scaling_action(
                            account_id=account_id,
                            campaign_id=campaign_id,
                            action_type=ScalingAction[recommendation["action"].upper()],
                            reason=recommendation.get("reason", "Auto-scaler recommendation"),
                            current_budget=recommendation.get("current_budget", 0),
                            new_budget=recommendation.get("new_budget", 0),
                            auto_approve=False  # Require manual approval for safety
                        )
                        
                        if action_result.get("status") == "pending_approval":
                            results["actions_pending_approval"] += 1
                        elif action_result.get("status") == "executed":
                            results["actions_taken"] += 1
                        
                        results["details"].append({
                            "campaign_id": campaign_id,
                            "action": recommendation["action"],
                            "reason": recommendation.get("reason"),
                            "status": action_result.get("status"),
                            "metrics": recommendation.get("metrics", {})
                        })
                        
                    logger.debug(f"Evaluated campaign {campaign_id}: {recommendation['action']}")
                    
                except Exception as e:
                    logger.error(f"Error evaluating campaign {campaign_id}: {e}")
                    results["errors"] += 1
                    results["details"].append({
                        "campaign_id": campaign_id,
                        "error": str(e)
                    })

            logger.info(f"Hourly optimization complete: {results['campaigns_evaluated']} campaigns evaluated, "
                       f"{results['actions_pending_approval']} actions pending approval, "
                       f"{results['actions_taken']} actions executed")

            return results

        except Exception as e:
            logger.error(f"Error in hourly optimization: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def log_performance_snapshot(self, campaign_id: str):
        """
        Log hourly performance snapshot for time-based learning.

        Args:
            campaign_id: Campaign ID
        """
        metrics = await self.get_24h_metrics(campaign_id)

        if not metrics:
            return

        now = datetime.utcnow()

        snapshot = CampaignPerformanceSnapshot(
            campaign_id=campaign_id,
            snapshot_time=now,
            hour_of_day=now.hour,
            day_of_week=now.weekday(),
            roas=metrics.roas,
            ctr=metrics.ctr,
            conversion_rate=metrics.conversion_rate,
            spend_hourly=metrics.spend / 24,  # Approximate hourly spend
            revenue_hourly=metrics.revenue / 24,
            impressions=metrics.impressions,
            clicks=metrics.clicks,
            conversions=metrics.conversions,
            daily_budget=metrics.daily_budget
        )

        self.db.add(snapshot)
        self.db.commit()

        logger.info(f"Logged performance snapshot for campaign {campaign_id}")

    def approve_scaling_action(self, action_id: int, approved_by: str) -> bool:
        """
        Approve a pending scaling action.

        Args:
            action_id: Scaling action ID
            approved_by: User who approved

        Returns:
            True if successful
        """
        action = self.db.query(ScalingAction).filter_by(id=action_id).first()

        if not action:
            logger.error(f"Action {action_id} not found")
            return False

        action.status = ScalingStatus.APPROVED.value
        action.approved_by = approved_by
        action.approved_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Action {action_id} approved by {approved_by}")
        return True

    def reject_scaling_action(self, action_id: int, reason: str) -> bool:
        """
        Reject a pending scaling action.

        Args:
            action_id: Scaling action ID
            reason: Rejection reason

        Returns:
            True if successful
        """
        action = self.db.query(ScalingAction).filter_by(id=action_id).first()

        if not action:
            logger.error(f"Action {action_id} not found")
            return False

        action.status = ScalingStatus.REJECTED.value
        action.rejected_reason = reason
        self.db.commit()

        logger.info(f"Action {action_id} rejected: {reason}")
        return True


# ==================== INITIALIZATION ====================

def create_tables():
    """Create all database tables"""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    logger.info("Auto-scaler database tables created")


if __name__ == "__main__":
    # Initialize database tables
    create_tables()
    print("Auto-scaler database tables created successfully")
