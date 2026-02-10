"""
Dynamic Aggregator - Execute and format analytics queries

Works with QueryParser to run queries and present results in
human-readable formats with charts, tables, and summaries.

Usage:
    from engines.query_parser import QueryParser
    from engines.dynamic_aggregator import DynamicAggregator

    parser = QueryParser()
    aggregator = DynamicAggregator(db_url)

    result = await aggregator.query("top 5 ads by CTR this week")
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Structured query result with metadata"""
    data: List[Dict[str, Any]] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    row_count: int = 0
    query_time_ms: float = 0
    sql_used: str = ""
    natural_query: str = ""
    summary: str = ""
    chart_type: Optional[str] = None  # "bar", "line", "pie", "table"
    confidence: float = 0.0


class DynamicAggregator:
    """
    Query execution engine that runs parsed queries and formats results.

    Handles:
    - Database connection management
    - Query execution with timeout
    - Result formatting and summarization
    - Chart type recommendation
    """

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL", "")
        self._parser = None

    def _get_parser(self):
        """Lazy-load parser"""
        if self._parser is None:
            from engines.query_parser import QueryParser
            self._parser = QueryParser()
        return self._parser

    async def query(self, natural_query: str) -> QueryResult:
        """
        Full pipeline: parse → build SQL → execute → format.

        Args:
            natural_query: Natural language question

        Returns:
            QueryResult with data, summary, and chart recommendation
        """
        import time
        start = time.time()

        parser = self._get_parser()

        # 1. Parse natural language to structured query
        parsed = await parser.parse(natural_query)

        # 2. Build parameterized SQL
        sql, params = parser.build_safe_sql(parsed)

        # 3. Execute query
        rows, columns = await self._execute(sql, params)

        elapsed_ms = (time.time() - start) * 1000

        # 4. Format results
        result = QueryResult(
            data=rows,
            columns=columns,
            row_count=len(rows),
            query_time_ms=round(elapsed_ms, 2),
            sql_used=sql,
            natural_query=natural_query,
            confidence=parsed.confidence,
            chart_type=self._recommend_chart(parsed, rows)
        )

        # 5. Generate summary
        result.summary = self._generate_summary(parsed, result)

        return result

    async def _execute(self, sql: str, params: List[Any]) -> Tuple[List[Dict], List[str]]:
        """
        Execute parameterized SQL against the database.

        Returns:
            Tuple of (rows as list of dicts, column names)
        """
        if not self.database_url:
            logger.warning("No DATABASE_URL configured, returning empty results")
            return [], []

        try:
            from sqlalchemy import text
            from sqlalchemy.ext.asyncio import create_async_engine

            # Convert postgres:// to postgresql+asyncpg://
            db_url = self.database_url
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

            engine = create_async_engine(db_url)

            async with engine.begin() as conn:
                # Execute with parameters (safe from injection)
                result = await conn.execute(
                    text(sql.replace("%s", ":p")),
                    {f"p{i}": v for i, v in enumerate(params)}
                )
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchall()]

            await engine.dispose()
            return rows, columns

        except ImportError:
            logger.error("sqlalchemy or asyncpg not installed")
            return [], []
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return [], []

    def _recommend_chart(self, parsed, rows: List[Dict]) -> str:
        """Recommend visualization type based on query intent and data shape"""
        from engines.query_parser import QueryIntent

        if not rows:
            return "table"

        if parsed.intent == QueryIntent.TREND:
            return "line"
        elif parsed.intent == QueryIntent.DISTRIBUTION:
            return "pie" if len(rows) <= 8 else "bar"
        elif parsed.intent == QueryIntent.COMPARISON:
            return "bar"
        elif parsed.intent == QueryIntent.TOP_PERFORMERS:
            return "bar"
        elif parsed.intent == QueryIntent.ANOMALY:
            return "scatter"
        else:
            return "table"

    def _generate_summary(self, parsed, result: QueryResult) -> str:
        """Generate a human-readable summary of query results"""
        from engines.query_parser import QueryIntent

        if not result.data:
            return f"No data found for: {result.natural_query}"

        count = result.row_count

        if parsed.intent == QueryIntent.TOP_PERFORMERS:
            top_row = result.data[0]
            metric_key = parsed.metrics[0] if parsed.metrics else list(top_row.keys())[0]
            metric_val = top_row.get(metric_key, top_row.get(f"avg_{metric_key}", "N/A"))
            return (
                f"Found {count} results. "
                f"Top performer: {metric_val} ({metric_key}). "
                f"Query took {result.query_time_ms:.0f}ms."
            )
        elif parsed.intent == QueryIntent.TREND:
            return (
                f"Trend data: {count} time periods analyzed. "
                f"Query took {result.query_time_ms:.0f}ms."
            )
        elif parsed.intent == QueryIntent.COMPARISON:
            dims = parsed.dimensions
            dim_label = dims[0] if dims else "category"
            return (
                f"Comparing {count} {dim_label} groups. "
                f"Query took {result.query_time_ms:.0f}ms."
            )
        elif parsed.intent == QueryIntent.DISTRIBUTION:
            return (
                f"Distribution across {count} categories. "
                f"Query took {result.query_time_ms:.0f}ms."
            )
        else:
            return (
                f"Returned {count} rows in {result.query_time_ms:.0f}ms. "
                f"Confidence: {result.confidence:.0%}."
            )

    async def explain(self, natural_query: str) -> Dict[str, Any]:
        """
        Explain what a query would do without executing it.

        Args:
            natural_query: Natural language question

        Returns:
            Dict with parsed intent, SQL preview, and explanation
        """
        parser = self._get_parser()
        parsed = await parser.parse(natural_query)
        sql, params = parser.build_safe_sql(parsed)

        return {
            "natural_query": natural_query,
            "parsed_intent": parsed.intent.value,
            "metrics": parsed.metrics,
            "dimensions": parsed.dimensions,
            "time_range": parsed.time_range.value,
            "filters": parsed.filters,
            "sql_preview": sql,
            "param_count": len(params),
            "target_table": parser._select_table(parsed),
            "confidence": parsed.confidence,
            "chart_recommendation": self._recommend_chart(parsed, [])
        }
