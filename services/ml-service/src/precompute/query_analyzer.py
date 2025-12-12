"""
Query Pattern Analyzer - Identify high-frequency prediction patterns

Agent 6: Precomputer Activator
Analyzes query logs to identify:
1. Top campaigns by query frequency
2. Most-predicted ad combinations
3. Scheduled campaigns requiring pre-warming
4. Time-based query patterns
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import redis

logger = logging.getLogger(__name__)


@dataclass
class QueryPattern:
    """Represents a query pattern for precomputation"""
    pattern_id: str
    query_type: str  # 'ctr_prediction', 'budget_allocation', 'creative_score'
    ad_id: Optional[str] = None
    campaign_id: Optional[str] = None
    tenant_id: Optional[str] = None
    frequency: int = 0
    last_seen: Optional[datetime] = None
    avg_compute_time_ms: float = 0.0
    priority_score: float = 0.0


@dataclass
class CampaignSchedule:
    """Campaign launch schedule for pre-warming"""
    campaign_id: str
    tenant_id: str
    launch_time: datetime
    ad_count: int
    estimated_queries: int


class QueryAnalyzer:
    """
    Analyzes query patterns to identify precomputation candidates.

    Uses Redis to track:
    - Query frequency per ad/campaign
    - Compute times per query type
    - Cache hit/miss rates
    - Scheduled campaign launches
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize query analyzer.

        Args:
            redis_url: Redis connection URL
        """
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis = redis.from_url(redis_url, decode_responses=True)

        # Tracking keys
        self.QUERY_LOG_KEY = "precompute:query_log"
        self.QUERY_FREQ_KEY = "precompute:query_freq"
        self.CAMPAIGN_SCHEDULE_KEY = "precompute:campaign_schedule"
        self.COMPUTE_TIME_KEY = "precompute:compute_time"

        logger.info("QueryAnalyzer initialized")

    # ========================================================================
    # QUERY TRACKING
    # ========================================================================

    def log_query(
        self,
        query_type: str,
        ad_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        compute_time_ms: Optional[float] = None,
        cache_hit: bool = False
    ):
        """
        Log a query for pattern analysis.

        Args:
            query_type: Type of query (ctr_prediction, budget_allocation, etc)
            ad_id: Optional ad ID
            campaign_id: Optional campaign ID
            tenant_id: Optional tenant ID
            compute_time_ms: Optional compute time in milliseconds
            cache_hit: Whether this was a cache hit
        """
        try:
            # Create pattern key
            pattern_key = self._create_pattern_key(query_type, ad_id, campaign_id, tenant_id)

            # Increment frequency counter
            freq_key = f"{self.QUERY_FREQ_KEY}:{pattern_key}"
            self.redis.incr(freq_key)
            self.redis.expire(freq_key, 7 * 24 * 3600)  # 7 days retention

            # Store query log entry
            log_entry = {
                "pattern_key": pattern_key,
                "query_type": query_type,
                "ad_id": ad_id,
                "campaign_id": campaign_id,
                "tenant_id": tenant_id,
                "compute_time_ms": compute_time_ms,
                "cache_hit": cache_hit,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Add to sorted set by timestamp
            score = datetime.utcnow().timestamp()
            self.redis.zadd(self.QUERY_LOG_KEY, {json.dumps(log_entry): score})

            # Trim to last 100k queries (keep storage manageable)
            self.redis.zremrangebyrank(self.QUERY_LOG_KEY, 0, -100001)

            # Track compute time if not cached
            if not cache_hit and compute_time_ms:
                time_key = f"{self.COMPUTE_TIME_KEY}:{query_type}"
                # Store as list with max 1000 entries
                self.redis.lpush(time_key, compute_time_ms)
                self.redis.ltrim(time_key, 0, 999)
                self.redis.expire(time_key, 7 * 24 * 3600)

        except Exception as e:
            logger.error(f"Failed to log query: {e}")

    def get_top_patterns(
        self,
        limit: int = 1000,
        query_type: Optional[str] = None,
        min_frequency: int = 2
    ) -> List[QueryPattern]:
        """
        Get top query patterns by frequency.

        Args:
            limit: Maximum number of patterns to return
            query_type: Optional filter by query type
            min_frequency: Minimum frequency threshold

        Returns:
            List of QueryPattern objects sorted by priority
        """
        try:
            patterns = []

            # Get all frequency keys
            pattern = f"{self.QUERY_FREQ_KEY}:*"
            if query_type:
                pattern = f"{self.QUERY_FREQ_KEY}:{query_type}:*"

            # Scan for keys
            cursor = 0
            while True:
                cursor, keys = self.redis.scan(cursor, match=pattern, count=1000)

                for key in keys:
                    frequency = int(self.redis.get(key) or 0)

                    if frequency >= min_frequency:
                        # Parse pattern key
                        pattern_key = key.replace(f"{self.QUERY_FREQ_KEY}:", "")
                        pattern_parts = self._parse_pattern_key(pattern_key)

                        if pattern_parts:
                            # Calculate avg compute time
                            avg_compute_time = self._get_avg_compute_time(pattern_parts["query_type"])

                            # Calculate priority score
                            priority = self._calculate_priority(frequency, avg_compute_time)

                            pattern = QueryPattern(
                                pattern_id=pattern_key,
                                query_type=pattern_parts["query_type"],
                                ad_id=pattern_parts.get("ad_id"),
                                campaign_id=pattern_parts.get("campaign_id"),
                                tenant_id=pattern_parts.get("tenant_id"),
                                frequency=frequency,
                                avg_compute_time_ms=avg_compute_time,
                                priority_score=priority
                            )
                            patterns.append(pattern)

                if cursor == 0:
                    break

            # Sort by priority score (high to low)
            patterns.sort(key=lambda p: p.priority_score, reverse=True)

            logger.info(f"Found {len(patterns)} query patterns (returning top {limit})")

            return patterns[:limit]

        except Exception as e:
            logger.error(f"Failed to get top patterns: {e}")
            return []

    def get_top_ads_for_precomputation(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get top ads that should be precomputed based on query frequency.

        Args:
            limit: Maximum number of ads to return

        Returns:
            List of ad dictionaries with metadata
        """
        patterns = self.get_top_patterns(limit=limit, query_type="ctr_prediction")

        ads = []
        for pattern in patterns:
            if pattern.ad_id:
                ads.append({
                    "ad_id": pattern.ad_id,
                    "campaign_id": pattern.campaign_id,
                    "tenant_id": pattern.tenant_id,
                    "frequency": pattern.frequency,
                    "priority": pattern.priority_score
                })

        return ads

    def get_top_campaigns_for_precomputation(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get top campaigns that should be precomputed based on query frequency.

        Args:
            limit: Maximum number of campaigns to return

        Returns:
            List of campaign dictionaries with metadata
        """
        patterns = self.get_top_patterns(limit=limit * 10, query_type="budget_allocation")

        # Group by campaign
        campaign_stats = defaultdict(lambda: {"frequency": 0, "priority": 0.0, "ad_count": 0})

        for pattern in patterns:
            if pattern.campaign_id:
                campaign_stats[pattern.campaign_id]["frequency"] += pattern.frequency
                campaign_stats[pattern.campaign_id]["priority"] = max(
                    campaign_stats[pattern.campaign_id]["priority"],
                    pattern.priority_score
                )
                campaign_stats[pattern.campaign_id]["ad_count"] += 1
                campaign_stats[pattern.campaign_id]["tenant_id"] = pattern.tenant_id

        # Convert to list and sort
        campaigns = [
            {
                "campaign_id": cid,
                "tenant_id": stats["tenant_id"],
                "frequency": stats["frequency"],
                "priority": stats["priority"],
                "ad_count": stats["ad_count"]
            }
            for cid, stats in campaign_stats.items()
        ]

        campaigns.sort(key=lambda c: c["priority"], reverse=True)

        return campaigns[:limit]

    # ========================================================================
    # SCHEDULED CAMPAIGNS
    # ========================================================================

    def register_campaign_launch(
        self,
        campaign_id: str,
        tenant_id: str,
        launch_time: datetime,
        ad_count: int,
        estimated_queries: int = 0
    ):
        """
        Register a scheduled campaign launch for pre-warming.

        Args:
            campaign_id: Campaign ID
            tenant_id: Tenant ID
            launch_time: Scheduled launch time
            ad_count: Number of ads in campaign
            estimated_queries: Estimated query volume
        """
        try:
            schedule = CampaignSchedule(
                campaign_id=campaign_id,
                tenant_id=tenant_id,
                launch_time=launch_time,
                ad_count=ad_count,
                estimated_queries=estimated_queries or ad_count * 10  # Default estimate
            )

            # Store in sorted set by launch time
            score = launch_time.timestamp()
            self.redis.zadd(
                self.CAMPAIGN_SCHEDULE_KEY,
                {json.dumps(asdict(schedule), default=str): score}
            )

            logger.info(f"Registered campaign launch: {campaign_id} at {launch_time}")

        except Exception as e:
            logger.error(f"Failed to register campaign launch: {e}")

    def get_upcoming_launches(
        self,
        hours_ahead: int = 24,
        hours_warmup: int = 2
    ) -> List[CampaignSchedule]:
        """
        Get campaigns launching soon that need pre-warming.

        Args:
            hours_ahead: Look ahead this many hours
            hours_warmup: Start warming this many hours before launch

        Returns:
            List of CampaignSchedule objects
        """
        try:
            # Calculate time window
            now = datetime.utcnow()
            warmup_start = now + timedelta(hours=hours_warmup)
            warmup_end = now + timedelta(hours=hours_ahead)

            # Query sorted set by time range
            launches_data = self.redis.zrangebyscore(
                self.CAMPAIGN_SCHEDULE_KEY,
                warmup_start.timestamp(),
                warmup_end.timestamp()
            )

            launches = []
            for data in launches_data:
                schedule_dict = json.loads(data)
                schedule_dict["launch_time"] = datetime.fromisoformat(schedule_dict["launch_time"])
                launches.append(CampaignSchedule(**schedule_dict))

            logger.info(f"Found {len(launches)} upcoming launches in next {hours_ahead}h")

            return launches

        except Exception as e:
            logger.error(f"Failed to get upcoming launches: {e}")
            return []

    # ========================================================================
    # TIME-BASED ANALYSIS
    # ========================================================================

    def analyze_query_patterns_by_hour(self) -> Dict[int, int]:
        """
        Analyze query distribution by hour of day.

        Returns:
            Dictionary mapping hour (0-23) to query count
        """
        try:
            # Get recent queries (last 7 days)
            cutoff = (datetime.utcnow() - timedelta(days=7)).timestamp()
            query_logs = self.redis.zrangebyscore(
                self.QUERY_LOG_KEY,
                cutoff,
                "+inf"
            )

            # Count by hour
            hour_counts = Counter()
            for log_data in query_logs:
                try:
                    log = json.loads(log_data)
                    timestamp = datetime.fromisoformat(log["timestamp"])
                    hour_counts[timestamp.hour] += 1
                except Exception:
                    continue

            return dict(hour_counts)

        except Exception as e:
            logger.error(f"Failed to analyze patterns by hour: {e}")
            return {}

    def identify_off_peak_hours(self) -> List[int]:
        """
        Identify off-peak hours (lowest query volume) for precomputation.

        Returns:
            List of hours (0-23) sorted by query volume (lowest first)
        """
        hour_counts = self.analyze_query_patterns_by_hour()

        if not hour_counts:
            # Default to 2am-6am if no data
            return [2, 3, 4, 5]

        # Sort hours by count (ascending)
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1])

        # Return top 4 off-peak hours
        off_peak = [hour for hour, _ in sorted_hours[:4]]

        logger.info(f"Identified off-peak hours: {off_peak}")

        return off_peak

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get query pattern statistics.

        Returns:
            Statistics dictionary
        """
        try:
            # Total patterns tracked
            pattern_count = len(list(self.redis.scan_iter(f"{self.QUERY_FREQ_KEY}:*")))

            # Total queries logged
            total_queries = self.redis.zcard(self.QUERY_LOG_KEY)

            # Scheduled campaigns
            scheduled_campaigns = self.redis.zcard(self.CAMPAIGN_SCHEDULE_KEY)

            # Cache hit rate (last 1000 queries)
            recent_queries = self.redis.zrange(self.QUERY_LOG_KEY, -1000, -1)
            cache_hits = 0
            cache_total = 0

            for log_data in recent_queries:
                try:
                    log = json.loads(log_data)
                    if log.get("cache_hit"):
                        cache_hits += 1
                    cache_total += 1
                except Exception:
                    continue

            cache_hit_rate = (cache_hits / cache_total * 100) if cache_total > 0 else 0

            # Avg compute time by type
            avg_compute_times = {}
            for query_type in ["ctr_prediction", "budget_allocation", "creative_score"]:
                avg_time = self._get_avg_compute_time(query_type)
                if avg_time > 0:
                    avg_compute_times[query_type] = avg_time

            return {
                "patterns_tracked": pattern_count,
                "total_queries_logged": total_queries,
                "scheduled_campaigns": scheduled_campaigns,
                "cache_hit_rate_percent": round(cache_hit_rate, 2),
                "avg_compute_time_ms": avg_compute_times,
                "off_peak_hours": self.identify_off_peak_hours()
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _create_pattern_key(
        self,
        query_type: str,
        ad_id: Optional[str],
        campaign_id: Optional[str],
        tenant_id: Optional[str]
    ) -> str:
        """Create unique pattern key from query parameters."""
        parts = [query_type]

        if tenant_id:
            parts.append(f"tenant:{tenant_id}")
        if campaign_id:
            parts.append(f"campaign:{campaign_id}")
        if ad_id:
            parts.append(f"ad:{ad_id}")

        return ":".join(parts)

    def _parse_pattern_key(self, pattern_key: str) -> Optional[Dict[str, str]]:
        """Parse pattern key back into components."""
        try:
            parts = pattern_key.split(":")

            result = {"query_type": parts[0]}

            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    key = parts[i]
                    value = parts[i + 1]
                    result[f"{key}_id"] = value

            return result

        except Exception:
            return None

    def _get_avg_compute_time(self, query_type: str) -> float:
        """Get average compute time for query type."""
        try:
            time_key = f"{self.COMPUTE_TIME_KEY}:{query_type}"
            times = self.redis.lrange(time_key, 0, -1)

            if not times:
                return 0.0

            times_float = [float(t) for t in times]
            return sum(times_float) / len(times_float)

        except Exception:
            return 0.0

    def _calculate_priority(self, frequency: int, avg_compute_time_ms: float) -> float:
        """
        Calculate priority score for precomputation.

        Higher priority = more benefit from precomputation.

        Priority formula:
        - High frequency queries get higher priority
        - Slow queries get higher priority (more time saved)
        - Score = frequency * log(compute_time_ms + 1)
        """
        import math

        # Normalize frequency (queries per day)
        freq_score = frequency

        # Compute time bonus (logarithmic - diminishing returns)
        time_score = math.log(avg_compute_time_ms + 1)

        # Combined priority
        priority = freq_score * time_score

        return priority


# Global instance
_query_analyzer = None


def get_query_analyzer() -> QueryAnalyzer:
    """
    Get global query analyzer instance.

    Returns:
        QueryAnalyzer instance
    """
    global _query_analyzer
    if _query_analyzer is None:
        _query_analyzer = QueryAnalyzer()
    return _query_analyzer
