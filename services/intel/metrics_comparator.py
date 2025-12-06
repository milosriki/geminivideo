"""
Smart Metrics Comparator Agent

Compares metrics across different data sources to:
1. Detect discrepancies (FB reports vs HubSpot vs AnyTrack)
2. Identify attribution issues
3. Find true ROAS (not just platform-reported)
4. Alert on suspicious data

Sources compared:
- Meta Ads (reported conversions)
- HubSpot (actual deals closed)
- AnyTrack (affiliate/tracking data)
- Google Ads (if used)
- Internal CAPI data
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class DataSource(Enum):
    META_ADS = "meta_ads"
    HUBSPOT = "hubspot"
    ANYTRACK = "anytrack"
    GOOGLE_ADS = "google_ads"
    INTERNAL_CAPI = "internal_capi"


class DiscrepancyLevel(Enum):
    NONE = "none"           # < 5% difference
    MINOR = "minor"         # 5-15% difference
    MODERATE = "moderate"   # 15-30% difference
    MAJOR = "major"         # 30-50% difference
    CRITICAL = "critical"   # > 50% difference


class AlertType(Enum):
    CONVERSION_MISMATCH = "conversion_mismatch"
    REVENUE_MISMATCH = "revenue_mismatch"
    SPEND_MISMATCH = "spend_mismatch"
    ROAS_MISMATCH = "roas_mismatch"
    ATTRIBUTION_ISSUE = "attribution_issue"
    DATA_DELAY = "data_delay"
    MISSING_DATA = "missing_data"


@dataclass
class MetricsSnapshot:
    """Metrics from a single source"""
    source: DataSource
    timestamp: datetime
    period_start: datetime
    period_end: datetime

    # Core metrics
    spend: float
    revenue: float
    conversions: int
    clicks: int
    impressions: int

    # Calculated
    roas: float
    ctr: float
    cpc: float
    cpa: float

    # Optional
    leads: int = 0
    deals_closed: int = 0
    pipeline_value: float = 0


@dataclass
class Discrepancy:
    """A detected discrepancy between sources"""
    id: str
    alert_type: AlertType
    level: DiscrepancyLevel

    source_a: DataSource
    source_b: DataSource

    metric_name: str
    value_a: float
    value_b: float
    difference_pct: float

    campaign_id: Optional[str]
    period: Tuple[datetime, datetime]

    recommendation: str
    detected_at: datetime


@dataclass
class ComparisonResult:
    """Result of comparing metrics across sources"""
    sources_compared: List[DataSource]
    period: Tuple[datetime, datetime]

    # Aggregated metrics
    true_spend: float
    true_revenue: float
    true_roas: float
    true_conversions: int

    # Discrepancies
    discrepancies: List[Discrepancy]
    overall_health: str  # good, warning, critical

    # Recommendations
    recommendations: List[str]


class MetricsComparator:
    """
    Smart Metrics Comparator Agent

    Compares data from multiple sources to find:
    1. Conversion discrepancies (FB says 100, HubSpot says 80)
    2. Revenue mismatches (platform vs actual)
    3. Attribution gaps
    4. Data quality issues
    """

    # Thresholds for discrepancy levels
    MINOR_THRESHOLD = 0.05      # 5%
    MODERATE_THRESHOLD = 0.15   # 15%
    MAJOR_THRESHOLD = 0.30      # 30%
    CRITICAL_THRESHOLD = 0.50   # 50%

    def __init__(self):
        self.sources: Dict[DataSource, Any] = {}
        self.last_comparison: Optional[ComparisonResult] = None

    def register_source(self, source: DataSource, client: Any):
        """
        Register a data source for comparison.

        Args:
            source: Source type
            client: Client instance for that source
        """
        self.sources[source] = client
        logger.info(f"Registered source: {source.value}")

    # =========================================================================
    # Data Collection
    # =========================================================================

    async def collect_metrics(
        self,
        source: DataSource,
        period_start: datetime,
        period_end: datetime,
        campaign_id: Optional[str] = None
    ) -> Optional[MetricsSnapshot]:
        """
        Collect metrics from a specific source.

        Args:
            source: Which source to query
            period_start: Start of period
            period_end: End of period
            campaign_id: Optional campaign filter

        Returns:
            MetricsSnapshot or None if source unavailable
        """
        if source not in self.sources:
            logger.warning(f"Source {source.value} not registered")
            return None

        client = self.sources[source]

        try:
            if source == DataSource.META_ADS:
                return await self._collect_meta_metrics(client, period_start, period_end, campaign_id)
            elif source == DataSource.HUBSPOT:
                return await self._collect_hubspot_metrics(client, period_start, period_end, campaign_id)
            elif source == DataSource.ANYTRACK:
                return await self._collect_anytrack_metrics(client, period_start, period_end, campaign_id)
            elif source == DataSource.GOOGLE_ADS:
                return await self._collect_google_metrics(client, period_start, period_end, campaign_id)
            elif source == DataSource.INTERNAL_CAPI:
                return await self._collect_capi_metrics(client, period_start, period_end, campaign_id)
            else:
                logger.warning(f"Unknown source: {source}")
                return None

        except Exception as e:
            logger.error(f"Error collecting metrics from {source.value}: {e}")
            return None

    async def _collect_meta_metrics(
        self,
        client,
        start: datetime,
        end: datetime,
        campaign_id: Optional[str]
    ) -> MetricsSnapshot:
        """Collect metrics from Meta Ads"""
        # Use Meta Insights API
        data = await client.get_insights(
            date_start=start,
            date_end=end,
            campaign_id=campaign_id
        )

        return MetricsSnapshot(
            source=DataSource.META_ADS,
            timestamp=datetime.now(),
            period_start=start,
            period_end=end,
            spend=data.get("spend", 0),
            revenue=data.get("revenue", 0),
            conversions=data.get("conversions", 0),
            clicks=data.get("clicks", 0),
            impressions=data.get("impressions", 0),
            roas=data.get("roas", 0),
            ctr=data.get("ctr", 0),
            cpc=data.get("cpc", 0),
            cpa=data.get("cpa", 0)
        )

    async def _collect_hubspot_metrics(
        self,
        client,
        start: datetime,
        end: datetime,
        campaign_id: Optional[str]
    ) -> MetricsSnapshot:
        """Collect metrics from HubSpot"""
        # Get closed deals in period
        deals = client.get_closed_deals_by_campaign(
            campaign_id=campaign_id,
            date_range=(start, end)
        ) if campaign_id else []

        total_revenue = sum(d.amount for d in deals)
        total_deals = len(deals)

        # Get pipeline value
        pipeline = client.get_pipeline_value(by_stage=False)

        return MetricsSnapshot(
            source=DataSource.HUBSPOT,
            timestamp=datetime.now(),
            period_start=start,
            period_end=end,
            spend=0,  # HubSpot doesn't track ad spend
            revenue=total_revenue,
            conversions=total_deals,
            clicks=0,
            impressions=0,
            roas=0,
            ctr=0,
            cpc=0,
            cpa=0,
            deals_closed=total_deals,
            pipeline_value=pipeline.get("total", 0)
        )

    async def _collect_anytrack_metrics(
        self,
        client,
        start: datetime,
        end: datetime,
        campaign_id: Optional[str]
    ) -> MetricsSnapshot:
        """Collect metrics from AnyTrack"""
        conversions = client.get_conversions(
            date_from=start,
            date_to=end,
            campaign_id=campaign_id
        )

        total_revenue = sum(c.revenue for c in conversions)
        total_conversions = len(conversions)

        return MetricsSnapshot(
            source=DataSource.ANYTRACK,
            timestamp=datetime.now(),
            period_start=start,
            period_end=end,
            spend=0,
            revenue=total_revenue,
            conversions=total_conversions,
            clicks=0,
            impressions=0,
            roas=0,
            ctr=0,
            cpc=0,
            cpa=0
        )

    async def _collect_google_metrics(
        self,
        client,
        start: datetime,
        end: datetime,
        campaign_id: Optional[str]
    ) -> MetricsSnapshot:
        """Collect metrics from Google Ads"""
        data = await client.get_campaign_performance(
            start_date=start,
            end_date=end,
            campaign_id=campaign_id
        )

        return MetricsSnapshot(
            source=DataSource.GOOGLE_ADS,
            timestamp=datetime.now(),
            period_start=start,
            period_end=end,
            spend=data.get("cost", 0),
            revenue=data.get("conversion_value", 0),
            conversions=data.get("conversions", 0),
            clicks=data.get("clicks", 0),
            impressions=data.get("impressions", 0),
            roas=data.get("roas", 0),
            ctr=data.get("ctr", 0),
            cpc=data.get("avg_cpc", 0),
            cpa=data.get("cost_per_conversion", 0)
        )

    async def _collect_capi_metrics(
        self,
        client,
        start: datetime,
        end: datetime,
        campaign_id: Optional[str]
    ) -> MetricsSnapshot:
        """Collect metrics from internal CAPI data"""
        data = await client.get_conversion_summary(
            start_date=start,
            end_date=end,
            campaign_id=campaign_id
        )

        return MetricsSnapshot(
            source=DataSource.INTERNAL_CAPI,
            timestamp=datetime.now(),
            period_start=start,
            period_end=end,
            spend=0,
            revenue=data.get("total_value", 0),
            conversions=data.get("total_conversions", 0),
            clicks=0,
            impressions=0,
            roas=0,
            ctr=0,
            cpc=0,
            cpa=0
        )

    # =========================================================================
    # Comparison Logic
    # =========================================================================

    async def compare_all_sources(
        self,
        period_start: datetime,
        period_end: datetime,
        campaign_id: Optional[str] = None
    ) -> ComparisonResult:
        """
        Compare metrics across all registered sources.

        Args:
            period_start: Start of comparison period
            period_end: End of comparison period
            campaign_id: Optional campaign filter

        Returns:
            ComparisonResult with discrepancies and recommendations
        """
        # Collect from all sources
        snapshots: Dict[DataSource, MetricsSnapshot] = {}

        for source in self.sources.keys():
            snapshot = await self.collect_metrics(
                source=source,
                period_start=period_start,
                period_end=period_end,
                campaign_id=campaign_id
            )
            if snapshot:
                snapshots[source] = snapshot

        if len(snapshots) < 2:
            logger.warning("Need at least 2 sources to compare")
            return ComparisonResult(
                sources_compared=list(snapshots.keys()),
                period=(period_start, period_end),
                true_spend=0,
                true_revenue=0,
                true_roas=0,
                true_conversions=0,
                discrepancies=[],
                overall_health="unknown",
                recommendations=["Need more data sources for comparison"]
            )

        # Find discrepancies
        discrepancies = []

        # Compare pairwise
        sources_list = list(snapshots.keys())
        for i, source_a in enumerate(sources_list):
            for source_b in sources_list[i+1:]:
                pairwise_discrepancies = self._compare_pair(
                    snapshots[source_a],
                    snapshots[source_b],
                    campaign_id
                )
                discrepancies.extend(pairwise_discrepancies)

        # Calculate true metrics (use most trustworthy source)
        true_metrics = self._calculate_true_metrics(snapshots)

        # Determine overall health
        health = self._determine_health(discrepancies)

        # Generate recommendations
        recommendations = self._generate_recommendations(discrepancies, snapshots)

        result = ComparisonResult(
            sources_compared=list(snapshots.keys()),
            period=(period_start, period_end),
            true_spend=true_metrics["spend"],
            true_revenue=true_metrics["revenue"],
            true_roas=true_metrics["roas"],
            true_conversions=true_metrics["conversions"],
            discrepancies=discrepancies,
            overall_health=health,
            recommendations=recommendations
        )

        self.last_comparison = result
        return result

    def _compare_pair(
        self,
        snapshot_a: MetricsSnapshot,
        snapshot_b: MetricsSnapshot,
        campaign_id: Optional[str]
    ) -> List[Discrepancy]:
        """Compare two snapshots and find discrepancies"""
        discrepancies = []
        timestamp = datetime.now()

        # Compare key metrics
        metrics_to_compare = [
            ("conversions", AlertType.CONVERSION_MISMATCH),
            ("revenue", AlertType.REVENUE_MISMATCH),
            ("spend", AlertType.SPEND_MISMATCH)
        ]

        for metric_name, alert_type in metrics_to_compare:
            value_a = getattr(snapshot_a, metric_name, 0)
            value_b = getattr(snapshot_b, metric_name, 0)

            # Skip if both are 0 or one source doesn't track this
            if value_a == 0 and value_b == 0:
                continue
            if value_a == 0 or value_b == 0:
                # One source has data, other doesn't
                if max(value_a, value_b) > 100:  # Only alert if significant
                    discrepancies.append(Discrepancy(
                        id=f"disc_{timestamp.timestamp()}_{metric_name}",
                        alert_type=AlertType.MISSING_DATA,
                        level=DiscrepancyLevel.MODERATE,
                        source_a=snapshot_a.source,
                        source_b=snapshot_b.source,
                        metric_name=metric_name,
                        value_a=value_a,
                        value_b=value_b,
                        difference_pct=100.0,
                        campaign_id=campaign_id,
                        period=(snapshot_a.period_start, snapshot_a.period_end),
                        recommendation=f"Check why {snapshot_b.source.value if value_b == 0 else snapshot_a.source.value} has no {metric_name} data",
                        detected_at=timestamp
                    ))
                continue

            # Calculate difference
            diff_pct = abs(value_a - value_b) / max(value_a, value_b)
            level = self._get_discrepancy_level(diff_pct)

            if level != DiscrepancyLevel.NONE:
                discrepancies.append(Discrepancy(
                    id=f"disc_{timestamp.timestamp()}_{metric_name}",
                    alert_type=alert_type,
                    level=level,
                    source_a=snapshot_a.source,
                    source_b=snapshot_b.source,
                    metric_name=metric_name,
                    value_a=value_a,
                    value_b=value_b,
                    difference_pct=diff_pct * 100,
                    campaign_id=campaign_id,
                    period=(snapshot_a.period_start, snapshot_a.period_end),
                    recommendation=self._get_recommendation(alert_type, level, snapshot_a.source, snapshot_b.source),
                    detected_at=timestamp
                ))

        return discrepancies

    def _get_discrepancy_level(self, diff_pct: float) -> DiscrepancyLevel:
        """Determine discrepancy level from percentage difference"""
        if diff_pct >= self.CRITICAL_THRESHOLD:
            return DiscrepancyLevel.CRITICAL
        elif diff_pct >= self.MAJOR_THRESHOLD:
            return DiscrepancyLevel.MAJOR
        elif diff_pct >= self.MODERATE_THRESHOLD:
            return DiscrepancyLevel.MODERATE
        elif diff_pct >= self.MINOR_THRESHOLD:
            return DiscrepancyLevel.MINOR
        else:
            return DiscrepancyLevel.NONE

    def _get_recommendation(
        self,
        alert_type: AlertType,
        level: DiscrepancyLevel,
        source_a: DataSource,
        source_b: DataSource
    ) -> str:
        """Generate recommendation based on discrepancy"""
        if alert_type == AlertType.CONVERSION_MISMATCH:
            if source_a == DataSource.META_ADS and source_b == DataSource.HUBSPOT:
                return "Meta may be over-reporting. Trust HubSpot for actual deals. Check attribution window settings."
            elif source_a == DataSource.META_ADS and source_b == DataSource.ANYTRACK:
                return "Check if AnyTrack pixel is firing correctly. Verify click ID passing."
            else:
                return "Investigate conversion tracking setup on both platforms."

        elif alert_type == AlertType.REVENUE_MISMATCH:
            if source_b == DataSource.HUBSPOT:
                return "HubSpot shows actual closed deal values. Use this for true ROAS calculation."
            else:
                return "Verify revenue values are being passed correctly to all platforms."

        elif alert_type == AlertType.SPEND_MISMATCH:
            return "Spend mismatch detected. Check for billing discrepancies or timezone issues."

        else:
            return "Investigate data sources for consistency."

    def _calculate_true_metrics(
        self,
        snapshots: Dict[DataSource, MetricsSnapshot]
    ) -> Dict[str, float]:
        """
        Calculate true metrics using source hierarchy.

        Priority:
        1. Spend: Meta/Google (they charge you)
        2. Revenue: HubSpot (actual deals)
        3. Conversions: Average of sources
        """
        true_metrics = {
            "spend": 0,
            "revenue": 0,
            "conversions": 0,
            "roas": 0
        }

        # Spend: Trust ad platforms
        if DataSource.META_ADS in snapshots:
            true_metrics["spend"] += snapshots[DataSource.META_ADS].spend
        if DataSource.GOOGLE_ADS in snapshots:
            true_metrics["spend"] += snapshots[DataSource.GOOGLE_ADS].spend

        # Revenue: Trust CRM (HubSpot)
        if DataSource.HUBSPOT in snapshots:
            true_metrics["revenue"] = snapshots[DataSource.HUBSPOT].revenue
        elif DataSource.ANYTRACK in snapshots:
            true_metrics["revenue"] = snapshots[DataSource.ANYTRACK].revenue
        elif DataSource.META_ADS in snapshots:
            true_metrics["revenue"] = snapshots[DataSource.META_ADS].revenue

        # Conversions: Average across sources
        conversion_values = [s.conversions for s in snapshots.values() if s.conversions > 0]
        if conversion_values:
            true_metrics["conversions"] = int(sum(conversion_values) / len(conversion_values))

        # Calculate true ROAS
        if true_metrics["spend"] > 0:
            true_metrics["roas"] = true_metrics["revenue"] / true_metrics["spend"]

        return true_metrics

    def _determine_health(self, discrepancies: List[Discrepancy]) -> str:
        """Determine overall data health"""
        if not discrepancies:
            return "good"

        critical_count = sum(1 for d in discrepancies if d.level == DiscrepancyLevel.CRITICAL)
        major_count = sum(1 for d in discrepancies if d.level == DiscrepancyLevel.MAJOR)

        if critical_count > 0:
            return "critical"
        elif major_count > 2:
            return "critical"
        elif major_count > 0:
            return "warning"
        else:
            return "good"

    def _generate_recommendations(
        self,
        discrepancies: List[Discrepancy],
        snapshots: Dict[DataSource, MetricsSnapshot]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # General recommendations based on discrepancies
        for d in discrepancies:
            if d.level in [DiscrepancyLevel.CRITICAL, DiscrepancyLevel.MAJOR]:
                recommendations.append(d.recommendation)

        # Add general advice
        if DataSource.HUBSPOT in snapshots and DataSource.META_ADS in snapshots:
            meta_conv = snapshots[DataSource.META_ADS].conversions
            hubspot_conv = snapshots[DataSource.HUBSPOT].deals_closed

            if meta_conv > 0 and hubspot_conv > 0:
                ratio = hubspot_conv / meta_conv
                if ratio < 0.5:
                    recommendations.append(
                        f"Only {ratio*100:.0f}% of Meta-reported conversions become HubSpot deals. "
                        "Consider adjusting attribution or improving lead quality."
                    )

        # Dedupe
        return list(set(recommendations))[:5]

    # =========================================================================
    # Alerts & Monitoring
    # =========================================================================

    async def check_for_alerts(
        self,
        threshold: DiscrepancyLevel = DiscrepancyLevel.MAJOR
    ) -> List[Discrepancy]:
        """
        Check for alerts above threshold.

        Args:
            threshold: Minimum level to alert on

        Returns:
            List of discrepancies at or above threshold
        """
        if not self.last_comparison:
            return []

        threshold_order = [
            DiscrepancyLevel.MINOR,
            DiscrepancyLevel.MODERATE,
            DiscrepancyLevel.MAJOR,
            DiscrepancyLevel.CRITICAL
        ]

        threshold_idx = threshold_order.index(threshold)

        return [
            d for d in self.last_comparison.discrepancies
            if threshold_order.index(d.level) >= threshold_idx
        ]

    def get_health_summary(self) -> Dict[str, Any]:
        """Get current health summary"""
        if not self.last_comparison:
            return {
                "status": "unknown",
                "message": "No comparison run yet"
            }

        return {
            "status": self.last_comparison.overall_health,
            "sources": [s.value for s in self.last_comparison.sources_compared],
            "discrepancy_count": len(self.last_comparison.discrepancies),
            "critical_count": sum(1 for d in self.last_comparison.discrepancies if d.level == DiscrepancyLevel.CRITICAL),
            "true_roas": self.last_comparison.true_roas,
            "recommendations": self.last_comparison.recommendations[:3]
        }
