"""
Synthetic Revenue Calculator
============================

Purpose:
    Converts CRM pipeline stages to synthetic revenue values for immediate optimization.
    Enables ML models to optimize BEFORE deals close (critical for 5-7 day sales cycles).

Problem Solved:
    Standard ROAS optimization waits for closed deals, but service businesses need to
    optimize based on pipeline movement (appointments scheduled, demos booked, etc).

    Example (PTD Fitness):
        - Appointment scheduled = $2,250 synthetic value
          (15% show rate * 60% close rate * $15k avg deal)
        - Show up to appointment = $9,000 synthetic value
          (60% close rate * $15k avg deal)
        - Closed won = $15,000 actual value

Created: 2025-12-07
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class StageValue:
    """Pipeline stage value configuration"""
    stage_name: str
    value: float
    confidence: float
    description: Optional[str] = None


@dataclass
class SyntheticRevenueResult:
    """Synthetic revenue calculation result"""
    stage_from: Optional[str]
    stage_to: str
    synthetic_value: float
    calculated_value: float  # Incremental value (stage_to - stage_from)
    confidence: float
    reason: str
    timestamp: datetime


class SyntheticRevenueCalculator:
    """
    Calculates synthetic revenue from CRM pipeline stage changes.

    Loads configuration from database (synthetic_revenue_config table).
    Supports multiple tenants with different stage value mappings.
    """

    def __init__(self, db_connection_string: Optional[str] = None):
        """
        Initialize Synthetic Revenue Calculator.

        Args:
            db_connection_string: PostgreSQL connection string
                                 (defaults to DATABASE_URL env var)
        """
        self.db_connection_string = db_connection_string or os.getenv("DATABASE_URL")
        self.config_cache: Dict[str, Dict[str, StageValue]] = {}
        self.cache_timestamp: Dict[str, datetime] = {}
        self.cache_ttl_seconds = 300  # 5 minutes

        logger.info("SyntheticRevenueCalculator initialized")

    def _get_db_connection(self):
        """Get database connection."""
        if not self.db_connection_string:
            raise ValueError("DATABASE_URL not configured")

        return psycopg2.connect(self.db_connection_string)

    def _load_tenant_config(self, tenant_id: str) -> Dict[str, StageValue]:
        """
        Load tenant configuration from database.

        Returns:
            Dict mapping stage_name -> StageValue
        """
        # Check cache
        now = datetime.now(timezone.utc)
        if tenant_id in self.config_cache:
            cache_age = (now - self.cache_timestamp[tenant_id]).total_seconds()
            if cache_age < self.cache_ttl_seconds:
                logger.debug(f"Using cached config for {tenant_id}")
                return self.config_cache[tenant_id]

        # Load from database
        logger.info(f"Loading synthetic revenue config for {tenant_id}")

        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT stage_values, avg_deal_value, sales_cycle_days, win_rate
                FROM synthetic_revenue_config
                WHERE tenant_id = %s AND is_active = true
            """, (tenant_id,))

            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if not row:
                logger.warning(f"No config found for {tenant_id}, using default")
                return self._get_default_config()

            # Parse stage_values JSONB
            stage_values_json = row["stage_values"]
            stage_config = {}

            for stage_name, stage_data in stage_values_json.items():
                stage_config[stage_name] = StageValue(
                    stage_name=stage_name,
                    value=float(stage_data["value"]),
                    confidence=float(stage_data["confidence"]),
                    description=stage_data.get("description"),
                )

            # Cache it
            self.config_cache[tenant_id] = stage_config
            self.cache_timestamp[tenant_id] = now

            logger.info(f"Loaded {len(stage_config)} stages for {tenant_id}")
            return stage_config

        except Exception as e:
            logger.error(f"Error loading config for {tenant_id}: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, StageValue]:
        """Get default configuration (fallback)."""
        return {
            "lead": StageValue("lead", 0, 0.10),
            "appointment_scheduled": StageValue("appointment_scheduled", 2250, 0.60),
            "show_up": StageValue("show_up", 9000, 0.85),
            "closed_won": StageValue("closed_won", 15000, 1.00),
            "closed_lost": StageValue("closed_lost", 0, 1.00),
        }

    def get_stage_value(
        self,
        tenant_id: str,
        stage_name: str,
    ) -> Tuple[float, float]:
        """
        Get synthetic value for a stage.

        Args:
            tenant_id: Tenant identifier
            stage_name: Pipeline stage name

        Returns:
            Tuple of (value, confidence)
        """
        config = self._load_tenant_config(tenant_id)

        if stage_name not in config:
            logger.warning(f"Unknown stage '{stage_name}' for {tenant_id}")
            return (0.0, 0.0)

        stage = config[stage_name]
        return (stage.value, stage.confidence)

    def calculate_stage_change(
        self,
        tenant_id: str,
        stage_from: Optional[str],
        stage_to: str,
        deal_value: Optional[float] = None,
    ) -> SyntheticRevenueResult:
        """
        Calculate synthetic revenue for a stage change.

        Args:
            tenant_id: Tenant identifier
            stage_from: Previous stage (None if new lead)
            stage_to: New stage
            deal_value: Actual deal value (if known, overrides config)

        Returns:
            SyntheticRevenueResult with incremental value
        """
        config = self._load_tenant_config(tenant_id)

        # Get stage values
        if stage_from:
            from_value, from_confidence = (
                config[stage_from].value,
                config[stage_from].confidence,
            ) if stage_from in config else (0, 0)
        else:
            from_value, from_confidence = 0, 0

        if stage_to in config:
            to_stage = config[stage_to]
            to_value = to_stage.value
            to_confidence = to_stage.confidence

            # Override with actual deal value if closed_won
            if stage_to == "closed_won" and deal_value is not None:
                to_value = deal_value
                to_confidence = 1.0

        else:
            logger.warning(f"Unknown stage '{stage_to}' for {tenant_id}")
            to_value, to_confidence = 0, 0

        # Calculate incremental value
        incremental_value = to_value - from_value

        # Generate reason
        reason = self._generate_reason(
            stage_from=stage_from,
            stage_to=stage_to,
            incremental_value=incremental_value,
            confidence=to_confidence,
        )

        return SyntheticRevenueResult(
            stage_from=stage_from,
            stage_to=stage_to,
            synthetic_value=to_value,
            calculated_value=incremental_value,
            confidence=to_confidence,
            reason=reason,
            timestamp=datetime.now(timezone.utc),
        )

    def calculate_ad_pipeline_roas(
        self,
        tenant_id: str,
        ad_spend: float,
        stage_changes: List[Dict],
    ) -> Dict:
        """
        Calculate Pipeline ROAS for an ad based on stage changes.

        Args:
            tenant_id: Tenant identifier
            ad_spend: Total ad spend
            stage_changes: List of stage changes, each with:
                          {"stage_from": str, "stage_to": str, "deal_value": float}

        Returns:
            Dict with pipeline_value, pipeline_roas, confidence
        """
        total_pipeline_value = 0
        total_confidence_weighted_value = 0
        total_confidence = 0

        for change in stage_changes:
            result = self.calculate_stage_change(
                tenant_id=tenant_id,
                stage_from=change.get("stage_from"),
                stage_to=change["stage_to"],
                deal_value=change.get("deal_value"),
            )

            # Accumulate pipeline value
            total_pipeline_value += result.calculated_value

            # Weight by confidence for avg confidence calculation
            total_confidence_weighted_value += result.calculated_value * result.confidence
            total_confidence += result.confidence

        # Calculate ROAS
        pipeline_roas = total_pipeline_value / max(ad_spend, 0.01)

        # Calculate average confidence
        avg_confidence = (
            total_confidence_weighted_value / max(total_pipeline_value, 0.01)
            if total_pipeline_value > 0
            else 0
        )

        return {
            "pipeline_value": round(total_pipeline_value, 2),
            "pipeline_roas": round(pipeline_roas, 2),
            "avg_confidence": round(avg_confidence, 4),
            "num_stage_changes": len(stage_changes),
            "ad_spend": ad_spend,
        }

    def get_all_stages(self, tenant_id: str) -> List[StageValue]:
        """
        Get all configured stages for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of StageValue objects sorted by value
        """
        config = self._load_tenant_config(tenant_id)
        stages = list(config.values())
        stages.sort(key=lambda s: s.value)
        return stages

    def _generate_reason(
        self,
        stage_from: Optional[str],
        stage_to: str,
        incremental_value: float,
        confidence: float,
    ) -> str:
        """Generate human-readable reason for synthetic revenue."""

        if stage_from is None:
            return f"New lead entered '{stage_to}' stage (+${incremental_value:.0f}, {confidence*100:.0f}% confidence)"

        if incremental_value > 0:
            return (
                f"Advanced from '{stage_from}' to '{stage_to}' "
                f"(+${incremental_value:.0f} synthetic value, {confidence*100:.0f}% confidence)"
            )
        elif incremental_value < 0:
            return (
                f"Moved backward from '{stage_from}' to '{stage_to}' "
                f"(-${abs(incremental_value):.0f} synthetic value)"
            )
        else:
            return f"No value change ('{stage_from}' → '{stage_to}')"

    def invalidate_cache(self, tenant_id: Optional[str] = None):
        """
        Invalidate configuration cache.

        Args:
            tenant_id: Specific tenant to invalidate (None = all)
        """
        if tenant_id:
            if tenant_id in self.config_cache:
                del self.config_cache[tenant_id]
                del self.cache_timestamp[tenant_id]
                logger.info(f"Cache invalidated for {tenant_id}")
        else:
            self.config_cache.clear()
            self.cache_timestamp.clear()
            logger.info("All cache invalidated")


# Singleton instance
_synthetic_revenue_calculator = None


def get_synthetic_revenue_calculator() -> SyntheticRevenueCalculator:
    """Get singleton Synthetic Revenue Calculator instance."""
    global _synthetic_revenue_calculator
    if _synthetic_revenue_calculator is None:
        _synthetic_revenue_calculator = SyntheticRevenueCalculator()
    return _synthetic_revenue_calculator
