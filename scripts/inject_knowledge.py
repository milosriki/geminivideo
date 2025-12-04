#!/usr/bin/env python3
"""
Knowledge Injection CLI - Bulk load winning patterns into the knowledge base

This tool fetches ad patterns from multiple sources and injects them into
the PostgreSQL knowledge base for RAG-based ad generation.

Data Sources:
  - PAID: Foreplay API (100M+ ads)
  - FREE: Meta Ads Library, TikTok Creative Center, YouTube Trending
  - FREE: Kaggle Datasets, Reddit r/advertising
  - Internal: CompetitorTracker, winning_patterns table

Usage:
  python scripts/inject_knowledge.py inject --query "fitness supplements" --industry health
  python scripts/inject_knowledge.py status
  python scripts/inject_knowledge.py export -o backup.jsonl
  python scripts/inject_knowledge.py import -i data.csv
  python scripts/inject_knowledge.py clear --namespace winners
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

import requests
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Database imports
try:
    import psycopg2
    from psycopg2.extras import execute_values, RealDictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    print("Warning: psycopg2 not installed. Install with: pip install psycopg2-binary")

# Optional dependencies
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class KnowledgePattern:
    """Data model for a knowledge pattern"""
    source: str
    hook_type: Optional[str] = None
    emotional_triggers: Optional[List[str]] = None
    visual_style: Optional[str] = None
    pacing: Optional[str] = None
    cta_style: Optional[str] = None
    transcript: Optional[str] = None
    performance_tier: Optional[str] = None
    industry: Optional[str] = None
    ctr: Optional[float] = None
    raw_data: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None

    def to_dict(self):
        """Convert to dictionary, handling list fields"""
        data = asdict(self)
        # Ensure emotional_triggers is a list
        if self.emotional_triggers is None:
            data['emotional_triggers'] = []
        return data


class Config:
    """Configuration from environment variables"""

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        self.foreplay_api_key = os.getenv("FOREPLAY_API_KEY")
        self.meta_access_token = os.getenv("META_ACCESS_TOKEN")
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.tiktok_api_key = os.getenv("TIKTOK_API_KEY")

        # GCS for backup/export
        self.gcs_bucket = os.getenv("GCS_BUCKET", "geminivideo-knowledge")

        # API endpoints
        self.foreplay_api_base = "https://api.foreplay.co/v1"
        self.meta_ads_library_url = "https://graph.facebook.com/v18.0/ads_archive"

    def validate(self) -> List[str]:
        """Validate configuration and return list of available sources"""
        sources = []

        if self.database_url:
            sources.append("database")

        if self.foreplay_api_key:
            sources.append("foreplay")

        if self.meta_access_token:
            sources.append("meta")

        if self.youtube_api_key:
            sources.append("youtube")

        if self.tiktok_api_key:
            sources.append("tiktok")

        # Always available free sources
        sources.extend(["internal", "kaggle"])

        return sources


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging(log_file: Optional[str] = None, verbose: bool = False) -> logging.Logger:
    """Setup logging to file and console"""
    log_level = logging.DEBUG if verbose else logging.INFO

    # Create logger
    logger = logging.getLogger("knowledge_injection")
    logger.setLevel(log_level)
    logger.handlers = []  # Clear existing handlers

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler
    if log_file is None:
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"knowledge_injection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    logger.info(f"Logging to: {log_file}")
    return logger


# ============================================================================
# DATABASE CONNECTION
# ============================================================================

class DatabaseManager:
    """Manage PostgreSQL database connections and operations"""

    def __init__(self, database_url: str, logger: logging.Logger):
        self.database_url = database_url
        self.logger = logger
        self.conn = None

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def connect(self):
        """Establish database connection"""
        if not HAS_PSYCOPG2:
            raise RuntimeError("psycopg2 not installed. Install with: pip install psycopg2-binary")

        try:
            self.conn = psycopg2.connect(self.database_url)
            self.logger.info("✓ Database connected")
        except Exception as e:
            self.logger.error(f"✗ Database connection failed: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.logger.info("Database connection closed")

    def insert_patterns(self, patterns: List[KnowledgePattern], dry_run: bool = False) -> int:
        """
        Insert patterns into winning_patterns table

        Returns:
            Number of patterns inserted
        """
        if dry_run:
            self.logger.info(f"[DRY RUN] Would insert {len(patterns)} patterns")
            return len(patterns)

        if not patterns:
            return 0

        insert_query = """
            INSERT INTO winning_patterns (
                source, hook_type, emotional_triggers, visual_style,
                pacing, cta_style, transcript, performance_tier,
                industry, ctr, raw_data, created_at
            ) VALUES %s
            ON CONFLICT DO NOTHING
        """

        # Prepare values
        values = []
        for pattern in patterns:
            data = pattern.to_dict()
            values.append((
                data['source'],
                data['hook_type'],
                data['emotional_triggers'] or [],
                data['visual_style'],
                data['pacing'],
                data['cta_style'],
                data['transcript'],
                data['performance_tier'],
                data['industry'],
                data['ctr'],
                json.dumps(data['raw_data']) if data['raw_data'] else '{}',
                datetime.utcnow()
            ))

        try:
            with self.conn.cursor() as cursor:
                execute_values(cursor, insert_query, values)
                self.conn.commit()
                inserted = cursor.rowcount
                self.logger.info(f"✓ Inserted {inserted} patterns into database")
                return inserted
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"✗ Failed to insert patterns: {e}")
            raise

    def log_injection(self, query: str, industry: str, source_counts: Dict[str, int],
                     total_patterns: int, errors: List[str]) -> int:
        """Log knowledge injection operation"""
        insert_query = """
            INSERT INTO knowledge_injections (
                query, industry, foreplay_count, meta_library_count,
                tiktok_count, youtube_count, kaggle_count, internal_count,
                total_patterns, errors, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """

        with self.conn.cursor() as cursor:
            cursor.execute(insert_query, (
                query,
                industry,
                source_counts.get('foreplay', 0),
                source_counts.get('meta', 0),
                source_counts.get('tiktok', 0),
                source_counts.get('youtube', 0),
                source_counts.get('kaggle', 0),
                source_counts.get('internal', 0),
                total_patterns,
                errors,
                datetime.utcnow()
            ))
            self.conn.commit()
            injection_id = cursor.fetchone()[0]
            return injection_id

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        queries = {
            'total_patterns': "SELECT COUNT(*) FROM winning_patterns",
            'by_source': """
                SELECT source, COUNT(*) as count
                FROM winning_patterns
                GROUP BY source
                ORDER BY count DESC
            """,
            'by_industry': """
                SELECT industry, COUNT(*) as count
                FROM winning_patterns
                WHERE industry IS NOT NULL
                GROUP BY industry
                ORDER BY count DESC
                LIMIT 10
            """,
            'avg_ctr': "SELECT AVG(ctr) FROM winning_patterns WHERE ctr IS NOT NULL",
            'recent_injections': """
                SELECT query, industry, total_patterns, created_at
                FROM knowledge_injections
                ORDER BY created_at DESC
                LIMIT 5
            """
        }

        stats = {}

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Total patterns
            cursor.execute(queries['total_patterns'])
            stats['total_patterns'] = cursor.fetchone()[0]

            # By source
            cursor.execute(queries['by_source'])
            stats['by_source'] = [dict(row) for row in cursor.fetchall()]

            # By industry
            cursor.execute(queries['by_industry'])
            stats['by_industry'] = [dict(row) for row in cursor.fetchall()]

            # Avg CTR
            cursor.execute(queries['avg_ctr'])
            stats['avg_ctr'] = cursor.fetchone()[0]

            # Recent injections
            cursor.execute(queries['recent_injections'])
            stats['recent_injections'] = [dict(row) for row in cursor.fetchall()]

        return stats

    def export_patterns(self, output_file: str, industry: Optional[str] = None,
                       source: Optional[str] = None, limit: Optional[int] = None):
        """Export patterns to JSONL file"""
        query = "SELECT * FROM winning_patterns WHERE 1=1"
        params = []

        if industry:
            query += " AND industry = %s"
            params.append(industry)

        if source:
            query += " AND source = %s"
            params.append(source)

        query += " ORDER BY created_at DESC"

        if limit:
            query += f" LIMIT {limit}"

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)

            count = 0
            with open(output_file, 'w') as f:
                for row in cursor:
                    # Convert to dict and handle datetime serialization
                    data = dict(row)
                    data['created_at'] = data['created_at'].isoformat() if data['created_at'] else None
                    f.write(json.dumps(data) + '\n')
                    count += 1

            self.logger.info(f"✓ Exported {count} patterns to {output_file}")
            return count

    def clear_namespace(self, namespace: str) -> int:
        """Clear patterns by source namespace"""
        delete_query = "DELETE FROM winning_patterns WHERE source = %s"

        with self.conn.cursor() as cursor:
            cursor.execute(delete_query, (namespace,))
            self.conn.commit()
            deleted = cursor.rowcount
            self.logger.info(f"✓ Deleted {deleted} patterns from namespace '{namespace}'")
            return deleted


# ============================================================================
# DATA SOURCE CONNECTORS
# ============================================================================

class RetryHelper:
    """Helper for retry logic with exponential backoff"""

    @staticmethod
    def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0,
                          max_delay: float = 60.0, logger: Optional[logging.Logger] = None):
        """
        Retry a function with exponential backoff

        Args:
            func: Function to retry (should raise exception on failure)
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            logger: Optional logger for retry messages
        """
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt failed
                    if logger:
                        logger.error(f"All {max_retries} attempts failed: {e}")
                    raise

                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** attempt), max_delay)

                if logger:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")

                time.sleep(delay)


class ForeplayConnector:
    """Connector for Foreplay API (PAID - 100M+ ads)"""

    def __init__(self, api_key: str, logger: logging.Logger):
        self.api_key = api_key
        self.logger = logger
        self.base_url = "https://api.foreplay.co/v1"

    def fetch_patterns(self, query: str, industry: str, limit: int = 100) -> List[KnowledgePattern]:
        """Fetch ad patterns from Foreplay"""
        self.logger.info(f"Fetching from Foreplay API (query: '{query}', limit: {limit})...")

        def make_request():
            response = requests.get(
                f"{self.base_url}/ads/search",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={
                    "query": query,
                    "industry": industry,
                    "limit": limit,
                    "sort": "engagement_desc"
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        try:
            data = RetryHelper.retry_with_backoff(make_request, logger=self.logger)

            patterns = []
            for ad in data.get('ads', []):
                pattern = KnowledgePattern(
                    source='foreplay',
                    hook_type=ad.get('hook_type'),
                    emotional_triggers=ad.get('triggers', []),
                    visual_style=ad.get('visual_style'),
                    pacing=ad.get('pacing'),
                    cta_style=ad.get('cta_type'),
                    transcript=ad.get('transcript'),
                    performance_tier=self._classify_performance(ad.get('engagement_rate')),
                    industry=industry,
                    ctr=ad.get('ctr'),
                    raw_data=ad
                )
                patterns.append(pattern)

            self.logger.info(f"✓ Foreplay: {len(patterns)} patterns")
            return patterns

        except Exception as e:
            self.logger.error(f"✗ Foreplay fetch failed: {e}")
            return []

    @staticmethod
    def _classify_performance(engagement_rate: Optional[float]) -> str:
        """Classify performance tier based on engagement"""
        if engagement_rate is None:
            return 'unknown'
        if engagement_rate >= 0.10:
            return 'top_1_percent'
        elif engagement_rate >= 0.05:
            return 'top_10_percent'
        else:
            return 'average'


class MetaAdsLibraryConnector:
    """Connector for Meta Ads Library (FREE)"""

    def __init__(self, access_token: str, logger: logging.Logger):
        self.access_token = access_token
        self.logger = logger
        self.base_url = "https://graph.facebook.com/v18.0/ads_archive"

    def fetch_patterns(self, query: str, industry: str, limit: int = 100) -> List[KnowledgePattern]:
        """Fetch ad patterns from Meta Ads Library"""
        self.logger.info(f"Fetching from Meta Ads Library (query: '{query}', limit: {limit})...")

        def make_request():
            response = requests.get(
                self.base_url,
                params={
                    "access_token": self.access_token,
                    "search_terms": query,
                    "ad_reached_countries": "US",
                    "ad_active_status": "ALL",
                    "limit": min(limit, 1000),  # Meta API limit
                    "fields": "id,ad_creative_bodies,ad_creative_link_captions,impressions"
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        try:
            data = RetryHelper.retry_with_backoff(make_request, logger=self.logger)

            patterns = []
            for ad in data.get('data', [])[:limit]:
                # Extract hook from creative body
                hook = ad.get('ad_creative_bodies', [''])[0] if ad.get('ad_creative_bodies') else ''

                pattern = KnowledgePattern(
                    source='meta_library',
                    hook_type=self._classify_hook(hook),
                    emotional_triggers=self._extract_triggers(hook),
                    transcript=hook,
                    performance_tier='unknown',  # Meta doesn't provide engagement
                    industry=industry,
                    raw_data=ad
                )
                patterns.append(pattern)

            self.logger.info(f"✓ Meta Ads Library: {len(patterns)} patterns")
            return patterns

        except Exception as e:
            self.logger.error(f"✗ Meta Ads Library fetch failed: {e}")
            return []

    @staticmethod
    def _classify_hook(text: str) -> str:
        """Classify hook type from text"""
        text_lower = text.lower()
        if '?' in text:
            return 'question_based'
        elif any(w in text_lower for w in ['secret', 'discover', 'revealed']):
            return 'curiosity_gap'
        elif any(w in text_lower for w in ['now', 'today', 'limited']):
            return 'urgency_scarcity'
        else:
            return 'statement'

    @staticmethod
    def _extract_triggers(text: str) -> List[str]:
        """Extract emotional triggers from text"""
        triggers = []
        text_lower = text.lower()

        trigger_keywords = {
            'urgency': ['now', 'today', 'limited', 'hurry', 'fast'],
            'curiosity': ['secret', 'discover', 'revealed', 'hidden', 'truth'],
            'social_proof': ['thousands', 'millions', 'proven', 'trusted'],
            'scarcity': ['limited', 'exclusive', 'only', 'rare'],
            'authority': ['expert', 'professional', 'certified', 'doctor']
        }

        for trigger_type, keywords in trigger_keywords.items():
            if any(kw in text_lower for kw in keywords):
                triggers.append(trigger_type)

        return triggers


class InternalConnector:
    """Connector for internal CompetitorTracker data"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def fetch_patterns(self, query: str, industry: str, limit: int = 100) -> List[KnowledgePattern]:
        """Fetch patterns from internal CompetitorTracker"""
        self.logger.info(f"Fetching from internal CompetitorTracker...")

        try:
            # Import CompetitorTracker
            sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "market-intel"))
            from competitor_tracker import CompetitorTracker

            tracker = CompetitorTracker()
            ads = tracker.get_competitor_ads(days=90, min_engagement=0.01)

            # Filter by query keywords
            query_keywords = query.lower().split()
            filtered_ads = []
            for ad in ads:
                hook = ad.get('hook_text', '').lower()
                if any(kw in hook for kw in query_keywords):
                    filtered_ads.append(ad)

            # Limit results
            filtered_ads = filtered_ads[:limit]

            patterns = []
            for ad in filtered_ads:
                pattern = KnowledgePattern(
                    source='internal',
                    hook_type=self._classify_hook(ad.get('hook_text', '')),
                    transcript=ad.get('hook_text'),
                    performance_tier=self._classify_performance(ad.get('engagement', 0)),
                    industry=industry,
                    ctr=ad.get('engagement'),
                    raw_data=ad
                )
                patterns.append(pattern)

            self.logger.info(f"✓ Internal: {len(patterns)} patterns")
            return patterns

        except Exception as e:
            self.logger.error(f"✗ Internal fetch failed: {e}")
            return []

    @staticmethod
    def _classify_hook(text: str) -> str:
        """Classify hook type"""
        text_lower = text.lower()
        if '?' in text:
            return 'question_based'
        elif any(w in text_lower for w in ['secret', 'discover']):
            return 'curiosity_gap'
        else:
            return 'statement'

    @staticmethod
    def _classify_performance(engagement: float) -> str:
        """Classify performance tier"""
        if engagement >= 0.10:
            return 'top_1_percent'
        elif engagement >= 0.05:
            return 'top_10_percent'
        else:
            return 'average'


class MockConnector:
    """Mock connector for sources without API keys (for testing)"""

    def __init__(self, source_name: str, logger: logging.Logger):
        self.source_name = source_name
        self.logger = logger

    def fetch_patterns(self, query: str, industry: str, limit: int = 100) -> List[KnowledgePattern]:
        """Return empty list with warning"""
        self.logger.warning(f"⚠ {self.source_name.upper()}: No API key configured, skipping...")
        return []


# ============================================================================
# MAIN CLI COMMANDS
# ============================================================================

class KnowledgeInjector:
    """Main knowledge injection orchestrator"""

    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def inject(self, query: str, industry: str, limit: int = 100,
              sources: Optional[List[str]] = None, dry_run: bool = False,
              parallel: bool = True) -> Dict[str, Any]:
        """
        Inject knowledge from multiple sources

        Args:
            query: Search query (e.g., "fitness supplements")
            industry: Industry category (e.g., "health", "ecommerce")
            limit: Max patterns per source
            sources: List of sources to use (None = all available)
            dry_run: If True, don't actually insert into database
            parallel: If True, fetch from sources in parallel

        Returns:
            Summary dict with counts and errors
        """
        self.logger.info("=" * 80)
        self.logger.info(f"KNOWLEDGE INJECTION STARTED")
        self.logger.info(f"  Query: {query}")
        self.logger.info(f"  Industry: {industry}")
        self.logger.info(f"  Limit per source: {limit}")
        self.logger.info(f"  Dry run: {dry_run}")
        self.logger.info("=" * 80)

        # Determine available sources
        available_sources = self.config.validate()
        if sources:
            sources = [s for s in sources if s in available_sources]
        else:
            sources = available_sources

        self.logger.info(f"Sources to query: {', '.join(sources)}")

        # Create connectors
        connectors = self._create_connectors(sources)

        # Fetch patterns from all sources
        all_patterns = []
        source_counts = {}
        errors = []

        if parallel:
            # Parallel fetching
            with ThreadPoolExecutor(max_workers=len(connectors)) as executor:
                future_to_source = {
                    executor.submit(conn.fetch_patterns, query, industry, limit): name
                    for name, conn in connectors.items()
                }

                with tqdm(total=len(connectors), desc="Fetching from sources") as pbar:
                    for future in as_completed(future_to_source):
                        source_name = future_to_source[future]
                        try:
                            patterns = future.result()
                            all_patterns.extend(patterns)
                            source_counts[source_name] = len(patterns)
                        except Exception as e:
                            error_msg = f"{source_name}: {str(e)}"
                            errors.append(error_msg)
                            source_counts[source_name] = 0
                        pbar.update(1)
        else:
            # Sequential fetching
            for source_name, connector in tqdm(connectors.items(), desc="Fetching from sources"):
                try:
                    patterns = connector.fetch_patterns(query, industry, limit)
                    all_patterns.extend(patterns)
                    source_counts[source_name] = len(patterns)
                except Exception as e:
                    error_msg = f"{source_name}: {str(e)}"
                    errors.append(error_msg)
                    source_counts[source_name] = 0

        total_patterns = len(all_patterns)

        self.logger.info("")
        self.logger.info("FETCH SUMMARY:")
        for source, count in source_counts.items():
            self.logger.info(f"  {source:15s}: {count:4d} patterns")
        self.logger.info(f"  {'TOTAL':15s}: {total_patterns:4d} patterns")

        # Insert into database
        if total_patterns > 0 and self.config.database_url:
            try:
                with DatabaseManager(self.config.database_url, self.logger) as db:
                    inserted = db.insert_patterns(all_patterns, dry_run=dry_run)

                    if not dry_run:
                        injection_id = db.log_injection(
                            query, industry, source_counts, total_patterns, errors
                        )
                        self.logger.info(f"✓ Logged injection operation (ID: {injection_id})")
            except Exception as e:
                error_msg = f"Database error: {str(e)}"
                errors.append(error_msg)
                self.logger.error(f"✗ {error_msg}")
        elif not self.config.database_url:
            self.logger.warning("⚠ No DATABASE_URL configured, patterns not stored")

        # Summary
        summary = {
            'query': query,
            'industry': industry,
            'total_patterns': total_patterns,
            'source_counts': source_counts,
            'errors': errors,
            'dry_run': dry_run,
            'timestamp': datetime.utcnow().isoformat()
        }

        self.logger.info("=" * 80)
        self.logger.info(f"INJECTION COMPLETE: {total_patterns} patterns")
        if errors:
            self.logger.warning(f"Errors: {len(errors)}")
        self.logger.info("=" * 80)

        return summary

    def _create_connectors(self, sources: List[str]) -> Dict[str, Any]:
        """Create connector instances for each source"""
        connectors = {}

        for source in sources:
            if source == 'foreplay' and self.config.foreplay_api_key:
                connectors['foreplay'] = ForeplayConnector(
                    self.config.foreplay_api_key, self.logger
                )
            elif source == 'meta' and self.config.meta_access_token:
                connectors['meta'] = MetaAdsLibraryConnector(
                    self.config.meta_access_token, self.logger
                )
            elif source == 'internal':
                connectors['internal'] = InternalConnector(self.logger)
            elif source == 'youtube':
                connectors['youtube'] = MockConnector('youtube', self.logger)
            elif source == 'tiktok':
                connectors['tiktok'] = MockConnector('tiktok', self.logger)
            elif source == 'kaggle':
                connectors['kaggle'] = MockConnector('kaggle', self.logger)

        return connectors


def cmd_inject(args, config: Config, logger: logging.Logger):
    """Execute inject command"""
    injector = KnowledgeInjector(config, logger)

    sources = args.sources.split(',') if args.sources else None

    summary = injector.inject(
        query=args.query,
        industry=args.industry,
        limit=args.limit,
        sources=sources,
        dry_run=args.dry_run,
        parallel=not args.sequential
    )

    # Print summary
    print("\n" + "=" * 80)
    print("INJECTION SUMMARY")
    print("=" * 80)
    print(f"Query:          {summary['query']}")
    print(f"Industry:       {summary['industry']}")
    print(f"Total patterns: {summary['total_patterns']}")
    print(f"Dry run:        {summary['dry_run']}")
    print("\nSource breakdown:")
    for source, count in summary['source_counts'].items():
        print(f"  {source:15s}: {count:4d}")

    if summary['errors']:
        print(f"\nErrors ({len(summary['errors'])}):")
        for error in summary['errors']:
            print(f"  - {error}")

    print("=" * 80)


def cmd_status(args, config: Config, logger: logging.Logger):
    """Execute status command"""
    print("\n" + "=" * 80)
    print("KNOWLEDGE BASE STATUS")
    print("=" * 80)

    # Check configuration
    print("\nConfigured sources:")
    available_sources = config.validate()

    all_sources = ['foreplay', 'meta', 'youtube', 'tiktok', 'kaggle', 'internal']
    for source in all_sources:
        status = "✓" if source in available_sources else "✗"
        print(f"  {status} {source}")

    # Check database
    if not config.database_url:
        print("\n⚠ DATABASE_URL not configured")
        return

    try:
        with DatabaseManager(config.database_url, logger) as db:
            stats = db.get_stats()

            print(f"\nDatabase statistics:")
            print(f"  Total patterns: {stats['total_patterns']:,}")
            print(f"  Average CTR:    {stats['avg_ctr']:.4f}" if stats['avg_ctr'] else "  Average CTR:    N/A")

            print("\nPatterns by source:")
            for row in stats['by_source']:
                print(f"  {row['source']:15s}: {row['count']:5,}")

            print("\nTop industries:")
            for row in stats['by_industry'][:5]:
                industry = row['industry'] or 'Unknown'
                print(f"  {industry:15s}: {row['count']:5,}")

            if stats['recent_injections']:
                print("\nRecent injections:")
                for inj in stats['recent_injections']:
                    timestamp = inj['created_at'].strftime('%Y-%m-%d %H:%M')
                    print(f"  {timestamp} | {inj['query']:20s} | {inj['industry']:10s} | {inj['total_patterns']:4d} patterns")

    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        print(f"\n✗ Database error: {e}")

    print("=" * 80)


def cmd_export(args, config: Config, logger: logging.Logger):
    """Execute export command"""
    if not config.database_url:
        print("✗ DATABASE_URL not configured")
        return

    output_file = args.output or f"knowledge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

    print(f"\nExporting knowledge base to: {output_file}")

    try:
        with DatabaseManager(config.database_url, logger) as db:
            count = db.export_patterns(
                output_file,
                industry=args.industry,
                source=args.source,
                limit=args.limit
            )

        print(f"✓ Exported {count} patterns")
        print(f"  File: {output_file}")

        # Show file size
        file_size = Path(output_file).stat().st_size
        print(f"  Size: {file_size / 1024 / 1024:.2f} MB")

    except Exception as e:
        logger.error(f"Export failed: {e}")
        print(f"✗ Export failed: {e}")


def cmd_import(args, config: Config, logger: logging.Logger):
    """Execute import command"""
    if not config.database_url:
        print("✗ DATABASE_URL not configured")
        return

    input_file = args.input
    if not Path(input_file).exists():
        print(f"✗ File not found: {input_file}")
        return

    print(f"\nImporting from: {input_file}")

    # Detect file format
    if input_file.endswith('.csv'):
        patterns = import_from_csv(input_file, args.industry, logger)
    elif input_file.endswith('.jsonl'):
        patterns = import_from_jsonl(input_file, logger)
    else:
        print("✗ Unsupported file format (use .csv or .jsonl)")
        return

    if not patterns:
        print("✗ No patterns loaded from file")
        return

    print(f"Loaded {len(patterns)} patterns from file")

    # Insert into database
    try:
        with DatabaseManager(config.database_url, logger) as db:
            inserted = db.insert_patterns(patterns, dry_run=args.dry_run)
            print(f"✓ Inserted {inserted} patterns")
    except Exception as e:
        logger.error(f"Import failed: {e}")
        print(f"✗ Import failed: {e}")


def cmd_clear(args, config: Config, logger: logging.Logger):
    """Execute clear command"""
    if not config.database_url:
        print("✗ DATABASE_URL not configured")
        return

    namespace = args.namespace

    # Confirm deletion
    if not args.force:
        response = input(f"⚠ Delete all patterns from namespace '{namespace}'? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled")
            return

    try:
        with DatabaseManager(config.database_url, logger) as db:
            deleted = db.clear_namespace(namespace)
            print(f"✓ Deleted {deleted} patterns from namespace '{namespace}'")
    except Exception as e:
        logger.error(f"Clear failed: {e}")
        print(f"✗ Clear failed: {e}")


# ============================================================================
# IMPORT HELPERS
# ============================================================================

def import_from_csv(csv_path: str, industry: str, logger: logging.Logger) -> List[KnowledgePattern]:
    """Import patterns from CSV file"""
    if not HAS_PANDAS:
        logger.error("pandas not installed. Install with: pip install pandas")
        return []

    patterns = []

    try:
        df = pd.read_csv(csv_path)

        for _, row in df.iterrows():
            pattern = KnowledgePattern(
                source=row.get('source', 'csv_import'),
                hook_type=row.get('hook_type'),
                emotional_triggers=row.get('emotional_triggers', '').split(',') if row.get('emotional_triggers') else [],
                visual_style=row.get('visual_style'),
                pacing=row.get('pacing'),
                cta_style=row.get('cta_style'),
                transcript=row.get('transcript') or row.get('hook_text'),
                performance_tier=row.get('performance_tier'),
                industry=industry,
                ctr=float(row['ctr']) if 'ctr' in row and pd.notna(row['ctr']) else None,
                raw_data={'imported_from': csv_path}
            )
            patterns.append(pattern)

        logger.info(f"Loaded {len(patterns)} patterns from CSV")

    except Exception as e:
        logger.error(f"Failed to import CSV: {e}")

    return patterns


def import_from_jsonl(jsonl_path: str, logger: logging.Logger) -> List[KnowledgePattern]:
    """Import patterns from JSONL file"""
    patterns = []

    try:
        with open(jsonl_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                pattern = KnowledgePattern(
                    source=data.get('source', 'jsonl_import'),
                    hook_type=data.get('hook_type'),
                    emotional_triggers=data.get('emotional_triggers', []),
                    visual_style=data.get('visual_style'),
                    pacing=data.get('pacing'),
                    cta_style=data.get('cta_style'),
                    transcript=data.get('transcript'),
                    performance_tier=data.get('performance_tier'),
                    industry=data.get('industry'),
                    ctr=data.get('ctr'),
                    raw_data=data.get('raw_data', {})
                )
                patterns.append(pattern)

        logger.info(f"Loaded {len(patterns)} patterns from JSONL")

    except Exception as e:
        logger.error(f"Failed to import JSONL: {e}")

    return patterns


# ============================================================================
# CLI SETUP
# ============================================================================

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Knowledge Injection CLI - Bulk load winning ad patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Inject fitness patterns from all sources
  python scripts/inject_knowledge.py inject \\
    --query "fitness supplements" \\
    --industry health \\
    --limit 500

  # Inject from specific sources only
  python scripts/inject_knowledge.py inject \\
    --query "skincare routine" \\
    --industry beauty \\
    --sources foreplay,meta \\
    --limit 200

  # Dry run (don't insert into database)
  python scripts/inject_knowledge.py inject \\
    --query "meal prep" \\
    --industry food \\
    --dry-run

  # Check knowledge base status
  python scripts/inject_knowledge.py status

  # Export all patterns
  python scripts/inject_knowledge.py export -o backup.jsonl

  # Export specific industry
  python scripts/inject_knowledge.py export \\
    --industry health \\
    --limit 1000 \\
    -o health_patterns.jsonl

  # Import from CSV
  python scripts/inject_knowledge.py import \\
    -i data/competitor_ads.csv \\
    --industry health

  # Clear a namespace
  python scripts/inject_knowledge.py clear --namespace test_data --force
        """
    )

    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--log-file', help='Path to log file (default: auto-generated)')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # INJECT command
    inject_parser = subparsers.add_parser('inject', help='Inject knowledge from sources')
    inject_parser.add_argument('--query', required=True, help='Search query (e.g., "fitness supplements")')
    inject_parser.add_argument('--industry', required=True, help='Industry category (e.g., "health", "ecommerce")')
    inject_parser.add_argument('--limit', type=int, default=100, help='Max patterns per source (default: 100)')
    inject_parser.add_argument('--sources', help='Comma-separated list of sources (default: all available)')
    inject_parser.add_argument('--dry-run', action='store_true', help='Fetch but don\'t insert into database')
    inject_parser.add_argument('--sequential', action='store_true', help='Fetch sources sequentially (default: parallel)')

    # STATUS command
    status_parser = subparsers.add_parser('status', help='Show knowledge base status')

    # EXPORT command
    export_parser = subparsers.add_parser('export', help='Export knowledge base')
    export_parser.add_argument('-o', '--output', help='Output file path (default: auto-generated)')
    export_parser.add_argument('--industry', help='Filter by industry')
    export_parser.add_argument('--source', help='Filter by source')
    export_parser.add_argument('--limit', type=int, help='Limit number of patterns')

    # IMPORT command
    import_parser = subparsers.add_parser('import', help='Import patterns from file')
    import_parser.add_argument('-i', '--input', required=True, help='Input file path (.csv or .jsonl)')
    import_parser.add_argument('--industry', default='general', help='Industry category')
    import_parser.add_argument('--dry-run', action='store_true', help='Load but don\'t insert into database')

    # CLEAR command
    clear_parser = subparsers.add_parser('clear', help='Clear patterns by namespace')
    clear_parser.add_argument('--namespace', required=True, help='Namespace to clear (source name)')
    clear_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Setup logging
    logger = setup_logging(log_file=args.log_file, verbose=args.verbose)

    # Load configuration
    config = Config()

    # Execute command
    try:
        if args.command == 'inject':
            cmd_inject(args, config, logger)
        elif args.command == 'status':
            cmd_status(args, config, logger)
        elif args.command == 'export':
            cmd_export(args, config, logger)
        elif args.command == 'import':
            cmd_import(args, config, logger)
        elif args.command == 'clear':
            cmd_clear(args, config, logger)
    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
