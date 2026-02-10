"""
Dynamic Query Engine - NLP-to-SQL Query Parser

Converts natural language analytics questions into structured database queries.
Part of the GeminiVideo intelligence platform.

Examples:
    "Show me top performing ads this week"
    "Which hook types have best CTR?"
    "Compare video performance by industry"

Architecture:
    1. Intent extraction (Gemini Flash)
    2. Query plan generation
    3. Safe SQL construction (parameterized)
    4. Result aggregation
"""

import os
import re
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    """Recognized query intents"""
    TOP_PERFORMERS = "top_performers"
    COMPARISON = "comparison"
    TREND = "trend"
    DISTRIBUTION = "distribution"
    DETAIL = "detail"
    AGGREGATION = "aggregation"
    ANOMALY = "anomaly"


class TimeRange(str, Enum):
    """Supported time ranges"""
    TODAY = "today"
    YESTERDAY = "yesterday"
    THIS_WEEK = "this_week"
    LAST_WEEK = "last_week"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    ALL_TIME = "all_time"


@dataclass
class ParsedQuery:
    """Structured representation of a parsed natural language query"""
    intent: QueryIntent
    metrics: List[str] = field(default_factory=list)
    dimensions: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    time_range: TimeRange = TimeRange.LAST_30_DAYS
    sort_by: Optional[str] = None
    sort_order: str = "DESC"
    limit: int = 10
    raw_query: str = ""
    confidence: float = 0.0


# Allowed tables and columns (SQL injection prevention)
ALLOWED_TABLES = {
    "feedback_events": [
        "id", "video_id", "prediction_id", "predicted_ctr", "actual_ctr",
        "predicted_score", "actual_performance", "feedback_type", "metadata",
        "created_at"
    ],
    "model_performance": [
        "id", "model_name", "evaluation_type", "predicted_value", "actual_value",
        "error", "latency_ms", "cost_usd", "input_tokens", "output_tokens",
        "cache_hit", "early_exit", "created_at"
    ],
    "winning_patterns": [
        "id", "source", "hook_type", "emotional_triggers", "visual_style",
        "pacing", "cta_style", "transcript", "performance_tier", "industry",
        "ctr", "raw_data", "created_at"
    ],
    "api_costs": [
        "id", "model_name", "operation_type", "input_tokens", "output_tokens",
        "total_tokens", "cost_usd", "latency_ms", "cache_hit", "early_exit",
        "created_at"
    ],
    "ab_tests": [
        "id", "experiment_id", "name", "status", "metric_name",
        "control_value", "test_value", "lift_percent", "p_value",
        "is_significant", "started_at", "ended_at", "created_at"
    ],
    "clips": [
        "id", "assetId", "startTime", "endTime", "duration", "score",
        "features", "status"
    ],
    "videos": [
        "id", "title", "predicted_ctr", "prediction_confidence", "models_used"
    ]
}

# Metric aliases (natural language → column mapping)
METRIC_ALIASES = {
    "ctr": "actual_ctr",
    "click rate": "actual_ctr",
    "click-through rate": "actual_ctr",
    "predicted ctr": "predicted_ctr",
    "cost": "cost_usd",
    "spend": "cost_usd",
    "latency": "latency_ms",
    "speed": "latency_ms",
    "accuracy": "error",
    "error": "error",
    "score": "score",
    "performance": "actual_ctr",
    "lift": "lift_percent",
    "confidence": "prediction_confidence",
    "tokens": "total_tokens",
}


class QueryParser:
    """
    Natural Language to SQL Query Parser

    Converts questions like "top 5 ads by CTR last week" into safe,
    parameterized SQL queries against the feedback/analytics tables.
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self._genai = None

    def _get_genai(self):
        """Lazy-load genai to avoid import failures"""
        if self._genai is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._genai = genai
            except ImportError:
                logger.warning("google-generativeai not installed, using rule-based parsing")
        return self._genai

    async def parse(self, natural_query: str) -> ParsedQuery:
        """
        Parse a natural language analytics query into a structured ParsedQuery.

        Args:
            natural_query: Natural language question (e.g., "top ads by CTR this week")

        Returns:
            ParsedQuery with intent, metrics, dimensions, filters, time range
        """
        # Try AI-powered parsing first
        genai = self._get_genai()
        if genai and self.api_key:
            try:
                return await self._ai_parse(natural_query, genai)
            except Exception as e:
                logger.warning(f"AI parsing failed, using rules: {e}")

        # Fallback to rule-based parsing
        return self._rule_based_parse(natural_query)

    async def _ai_parse(self, query: str, genai) -> ParsedQuery:
        """Use Gemini to extract structured query intent"""
        model = genai.GenerativeModel("gemini-2.0-flash-exp")

        prompt = f"""Parse this analytics query into structured components.

Query: "{query}"

Available intents: top_performers, comparison, trend, distribution, detail, aggregation, anomaly
Available metrics: ctr, cost, latency, accuracy, score, lift, tokens
Available dimensions: hook_type, model_name, industry, source, platform, visual_style, status
Available time ranges: today, yesterday, this_week, last_week, this_month, last_month, last_7_days, last_30_days, last_90_days, all_time

Return JSON:
{{
    "intent": "string",
    "metrics": ["string"],
    "dimensions": ["string"],
    "filters": {{}},
    "time_range": "string",
    "sort_by": "string or null",
    "sort_order": "ASC or DESC",
    "limit": number,
    "confidence": 0.0-1.0
}}"""

        result = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json", "temperature": 0.1}
        )

        parsed = json.loads(result.text)

        return ParsedQuery(
            intent=QueryIntent(parsed.get("intent", "aggregation")),
            metrics=parsed.get("metrics", ["ctr"]),
            dimensions=parsed.get("dimensions", []),
            filters=parsed.get("filters", {}),
            time_range=TimeRange(parsed.get("time_range", "last_30_days")),
            sort_by=parsed.get("sort_by"),
            sort_order=parsed.get("sort_order", "DESC"),
            limit=min(parsed.get("limit", 10), 100),
            raw_query=query,
            confidence=parsed.get("confidence", 0.8)
        )

    def _rule_based_parse(self, query: str) -> ParsedQuery:
        """Fallback rule-based query parsing"""
        q = query.lower().strip()

        # Detect intent
        intent = QueryIntent.AGGREGATION
        if any(w in q for w in ["top", "best", "highest", "winning"]):
            intent = QueryIntent.TOP_PERFORMERS
        elif any(w in q for w in ["compare", "versus", "vs", "between"]):
            intent = QueryIntent.COMPARISON
        elif any(w in q for w in ["trend", "over time", "daily", "weekly", "growth"]):
            intent = QueryIntent.TREND
        elif any(w in q for w in ["distribution", "breakdown", "spread", "by"]):
            intent = QueryIntent.DISTRIBUTION
        elif any(w in q for w in ["detail", "specific", "show me", "what is"]):
            intent = QueryIntent.DETAIL
        elif any(w in q for w in ["unusual", "anomal", "spike", "drop", "outlier"]):
            intent = QueryIntent.ANOMALY

        # Detect metrics
        metrics = []
        for alias, column in METRIC_ALIASES.items():
            if alias in q:
                metrics.append(column)
        if not metrics:
            metrics = ["actual_ctr"]

        # Detect time range
        time_range = TimeRange.LAST_30_DAYS
        time_map = {
            "today": TimeRange.TODAY,
            "yesterday": TimeRange.YESTERDAY,
            "this week": TimeRange.THIS_WEEK,
            "last week": TimeRange.LAST_WEEK,
            "this month": TimeRange.THIS_MONTH,
            "last month": TimeRange.LAST_MONTH,
            "7 days": TimeRange.LAST_7_DAYS,
            "30 days": TimeRange.LAST_30_DAYS,
            "90 days": TimeRange.LAST_90_DAYS,
            "all time": TimeRange.ALL_TIME,
        }
        for phrase, tr in time_map.items():
            if phrase in q:
                time_range = tr
                break

        # Detect limit
        limit = 10
        limit_match = re.search(r'top\s+(\d+)', q)
        if limit_match:
            limit = min(int(limit_match.group(1)), 100)

        # Detect dimensions
        dimensions = []
        dim_map = {
            "hook": "hook_type",
            "model": "model_name",
            "industry": "industry",
            "source": "source",
            "platform": "platform",
            "visual": "visual_style",
        }
        for keyword, dim in dim_map.items():
            if keyword in q:
                dimensions.append(dim)

        return ParsedQuery(
            intent=intent,
            metrics=list(set(metrics)),
            dimensions=dimensions,
            time_range=time_range,
            sort_by=metrics[0] if metrics else None,
            sort_order="DESC" if intent == QueryIntent.TOP_PERFORMERS else "DESC",
            limit=limit,
            raw_query=query,
            confidence=0.6
        )

    def build_safe_sql(self, parsed: ParsedQuery) -> Tuple[str, List[Any]]:
        """
        Build a parameterized SQL query from a ParsedQuery.

        Returns:
            Tuple of (sql_template, parameters) — ALWAYS parameterized, never interpolated.
        """
        # Determine target table
        table = self._select_table(parsed)
        params: List[Any] = []

        # Validate columns
        allowed = ALLOWED_TABLES.get(table, [])
        safe_metrics = [m for m in parsed.metrics if m in allowed or m in METRIC_ALIASES.values()]
        safe_dims = [d for d in parsed.dimensions if d in allowed]

        if not safe_metrics:
            safe_metrics = ["id"]

        # Build SELECT
        select_parts = []
        if safe_dims:
            select_parts.extend(safe_dims)
        if parsed.intent in (QueryIntent.AGGREGATION, QueryIntent.DISTRIBUTION, QueryIntent.TREND):
            for m in safe_metrics:
                select_parts.append(f"AVG({m}) as avg_{m}")
                select_parts.append(f"COUNT(*) as count")
        else:
            select_parts.extend(safe_metrics)

        # Remove duplicates while preserving order
        seen = set()
        unique_parts = []
        for p in select_parts:
            if p not in seen:
                seen.add(p)
                unique_parts.append(p)
        select_parts = unique_parts

        sql = f"SELECT {', '.join(select_parts)} FROM {table}"

        # Build WHERE
        where_clauses = []

        # Time filter
        time_col = "created_at"
        start_date = self._resolve_time_range(parsed.time_range)
        if start_date and parsed.time_range != TimeRange.ALL_TIME:
            where_clauses.append(f"{time_col} >= %s")
            params.append(start_date)

        # Additional filters
        for col, val in parsed.filters.items():
            if col in allowed:
                where_clauses.append(f"{col} = %s")
                params.append(val)

        if where_clauses:
            sql += f" WHERE {' AND '.join(where_clauses)}"

        # GROUP BY
        if safe_dims and parsed.intent in (
            QueryIntent.AGGREGATION, QueryIntent.DISTRIBUTION, QueryIntent.TREND
        ):
            sql += f" GROUP BY {', '.join(safe_dims)}"

        # ORDER BY
        if parsed.sort_by and (parsed.sort_by in allowed or f"avg_{parsed.sort_by}" in sql):
            order_col = f"avg_{parsed.sort_by}" if f"avg_{parsed.sort_by}" in sql else parsed.sort_by
            order_dir = "ASC" if parsed.sort_order.upper() == "ASC" else "DESC"
            sql += f" ORDER BY {order_col} {order_dir}"

        # LIMIT
        sql += f" LIMIT %s"
        params.append(parsed.limit)

        return sql, params

    def _select_table(self, parsed: ParsedQuery) -> str:
        """Select the most appropriate table based on query context"""
        metrics_str = " ".join(parsed.metrics)
        dims_str = " ".join(parsed.dimensions)
        combined = f"{metrics_str} {dims_str} {parsed.raw_query}".lower()

        if any(w in combined for w in ["cost", "token", "api", "latency"]):
            return "api_costs"
        elif any(w in combined for w in ["model", "accuracy", "error", "predict"]):
            return "model_performance"
        elif any(w in combined for w in ["pattern", "hook", "industry", "visual", "winning"]):
            return "winning_patterns"
        elif any(w in combined for w in ["experiment", "ab", "test", "lift"]):
            return "ab_tests"
        elif any(w in combined for w in ["clip", "scene", "video"]):
            return "clips"
        else:
            return "feedback_events"

    def _resolve_time_range(self, tr: TimeRange) -> Optional[datetime]:
        """Convert time range enum to a start datetime"""
        now = datetime.utcnow()
        mapping = {
            TimeRange.TODAY: now.replace(hour=0, minute=0, second=0),
            TimeRange.YESTERDAY: (now - timedelta(days=1)).replace(hour=0, minute=0, second=0),
            TimeRange.THIS_WEEK: now - timedelta(days=now.weekday()),
            TimeRange.LAST_WEEK: now - timedelta(days=now.weekday() + 7),
            TimeRange.THIS_MONTH: now.replace(day=1),
            TimeRange.LAST_MONTH: (now.replace(day=1) - timedelta(days=1)).replace(day=1),
            TimeRange.LAST_7_DAYS: now - timedelta(days=7),
            TimeRange.LAST_30_DAYS: now - timedelta(days=30),
            TimeRange.LAST_90_DAYS: now - timedelta(days=90),
            TimeRange.ALL_TIME: None,
        }
        return mapping.get(tr)
