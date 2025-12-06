"""
AdIntel Orchestrator - The Brain That Wires Everything

This is the SINGLE ENTRY POINT that orchestrates:
1. Scraping (ad_library_scraper.py)
2. Enrichment (ad_enrichment.py)
3. Search (search_engine.py)
4. API (adintel_api.py)

MINIMAL CODE - MAXIMUM LEVERAGE
Uses existing infrastructure:
- PostgreSQL (from docker-compose)
- Redis (from docker-compose)
- Gemini (from titan-core)
"""

import asyncio
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import json

# Redis for job queue
import redis.asyncio as aioredis

# PostgreSQL for persistence
import asyncpg

# Our components
from .ad_library_scraper import MetaAdLibraryScraper, BrandTracker, ScrapedAd
from .ad_enrichment import AdEnrichmentPipeline, EnrichedAd
from .search_engine import AdSearchEngine, AdDocument, SearchConfig, AdIndexingPipeline

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration - Uses existing env vars from docker-compose
# =============================================================================

@dataclass
class OrchestratorConfig:
    """Uses existing infrastructure config"""
    # From docker-compose.yml
    database_url: str = os.getenv("DATABASE_URL", "postgresql://geminivideo:geminivideo@localhost:5432/geminivideo")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Typesense (add to docker-compose)
    typesense_host: str = os.getenv("TYPESENSE_HOST", "typesense")
    typesense_port: int = int(os.getenv("TYPESENSE_PORT", "8108"))
    typesense_api_key: str = os.getenv("TYPESENSE_API_KEY", "adintel-key")

    # Gemini (already in titan-core)
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

    # Scraping config
    scrape_interval_hours: int = 6
    max_ads_per_brand: int = 50
    winner_threshold_days: int = 30


# =============================================================================
# Database Schema - Add to existing PostgreSQL
# =============================================================================

SCHEMA_SQL = """
-- AdIntel tables (add to existing geminivideo database)

CREATE TABLE IF NOT EXISTS adintel_ads (
    id SERIAL PRIMARY KEY,
    ad_id VARCHAR(255) UNIQUE NOT NULL,
    brand_name VARCHAR(255) NOT NULL,
    brand_id VARCHAR(255),
    platform VARCHAR(50) DEFAULT 'meta',
    format VARCHAR(50) DEFAULT 'video',

    -- Content
    headline TEXT,
    body_text TEXT,
    transcription TEXT,
    cta VARCHAR(100),

    -- AI Enrichment
    primary_emotion VARCHAR(100),
    emotional_drivers JSONB DEFAULT '[]',
    hook_type VARCHAR(100),
    hook_text TEXT,
    winning_patterns JSONB DEFAULT '[]',
    winner_score INTEGER DEFAULT 0,

    -- Performance
    running_duration_days INTEGER DEFAULT 0,
    is_winner BOOLEAN DEFAULT FALSE,
    estimated_spend DECIMAL(12,2),

    -- Media
    thumbnail_url TEXT,
    video_url TEXT,
    landing_page_url TEXT,

    -- Metadata
    industry VARCHAR(100),
    category VARCHAR(100),
    tags JSONB DEFAULT '[]',

    -- Timestamps
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    enriched_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS adintel_brands (
    id SERIAL PRIMARY KEY,
    brand_id VARCHAR(255) UNIQUE NOT NULL,
    brand_name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    industry VARCHAR(100),

    -- Tracking
    is_tracked BOOLEAN DEFAULT FALSE,
    check_interval_hours INTEGER DEFAULT 24,
    last_checked TIMESTAMP,
    next_check TIMESTAMP,

    -- Stats
    total_ads INTEGER DEFAULT 0,
    winner_count INTEGER DEFAULT 0,
    avg_running_days DECIMAL(6,1) DEFAULT 0,

    -- Metadata
    platforms JSONB DEFAULT '["meta"]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS adintel_collections (
    id SERIAL PRIMARY KEY,
    collection_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    ad_ids JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_ads_brand ON adintel_ads(brand_name);
CREATE INDEX IF NOT EXISTS idx_ads_winner ON adintel_ads(is_winner);
CREATE INDEX IF NOT EXISTS idx_ads_industry ON adintel_ads(industry);
CREATE INDEX IF NOT EXISTS idx_ads_emotion ON adintel_ads(primary_emotion);
CREATE INDEX IF NOT EXISTS idx_ads_running_days ON adintel_ads(running_duration_days DESC);
CREATE INDEX IF NOT EXISTS idx_brands_tracked ON adintel_brands(is_tracked);
"""


# =============================================================================
# Job Queue - Uses existing Redis
# =============================================================================

class JobQueue:
    """Simple Redis-based job queue for async processing"""

    QUEUES = {
        "scrape": "adintel:queue:scrape",
        "enrich": "adintel:queue:enrich",
        "index": "adintel:queue:index",
    }

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        self.redis = await aioredis.from_url(self.redis_url)

    async def close(self):
        if self.redis:
            await self.redis.close()

    async def enqueue(self, queue_name: str, job_data: Dict):
        """Add job to queue"""
        queue_key = self.QUEUES.get(queue_name, f"adintel:queue:{queue_name}")
        await self.redis.rpush(queue_key, json.dumps(job_data))

    async def dequeue(self, queue_name: str, timeout: int = 0) -> Optional[Dict]:
        """Get next job from queue"""
        queue_key = self.QUEUES.get(queue_name, f"adintel:queue:{queue_name}")
        result = await self.redis.blpop(queue_key, timeout=timeout)
        if result:
            return json.loads(result[1])
        return None

    async def queue_length(self, queue_name: str) -> int:
        queue_key = self.QUEUES.get(queue_name, f"adintel:queue:{queue_name}")
        return await self.redis.llen(queue_key)


# =============================================================================
# The Orchestrator - Wires Everything Together
# =============================================================================

class AdIntelOrchestrator:
    """
    THE BRAIN - Coordinates all AdIntel components

    Flow:
    1. Schedule brand scrapes → Redis queue
    2. Worker picks up → MetaAdLibraryScraper
    3. Raw ads → PostgreSQL
    4. Enqueue enrichment → Redis queue
    5. Worker picks up → AdEnrichmentPipeline (uses Gemini from titan-core)
    6. Enriched ads → PostgreSQL + Typesense
    7. API serves from Typesense (fast search)
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        self.db_pool: Optional[asyncpg.Pool] = None
        self.job_queue: Optional[JobQueue] = None
        self.search_engine: Optional[AdSearchEngine] = None
        self.scraper: Optional[MetaAdLibraryScraper] = None
        self.enrichment: Optional[AdEnrichmentPipeline] = None

    async def initialize(self):
        """Boot up all components"""
        logger.info("🚀 Initializing AdIntel Orchestrator...")

        # 1. Connect to PostgreSQL (existing)
        self.db_pool = await asyncpg.create_pool(self.config.database_url)
        await self._init_schema()
        logger.info("✅ PostgreSQL connected")

        # 2. Connect to Redis (existing)
        self.job_queue = JobQueue(self.config.redis_url)
        await self.job_queue.connect()
        logger.info("✅ Redis connected")

        # 3. Initialize Typesense search
        search_config = SearchConfig(
            host=self.config.typesense_host,
            port=self.config.typesense_port,
            api_key=self.config.typesense_api_key,
        )
        self.search_engine = AdSearchEngine(search_config)
        await self.search_engine.initialize()
        logger.info("✅ Typesense initialized")

        # 4. Initialize scraper
        self.scraper = MetaAdLibraryScraper()
        logger.info("✅ Scraper ready")

        # 5. Initialize enrichment pipeline (uses existing Gemini)
        self.enrichment = AdEnrichmentPipeline()
        logger.info("✅ Enrichment pipeline ready")

        logger.info("🎉 AdIntel Orchestrator fully initialized!")

    async def _init_schema(self):
        """Create tables if not exist"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(SCHEMA_SQL)

    async def shutdown(self):
        """Clean shutdown"""
        if self.job_queue:
            await self.job_queue.close()
        if self.db_pool:
            await self.db_pool.close()
        if self.scraper:
            await self.scraper.close()

    # =========================================================================
    # HIGH-LEVEL OPERATIONS
    # =========================================================================

    async def track_brand(self, brand_name: str, domain: Optional[str] = None) -> str:
        """Start tracking a brand (like Foreplay Spyder)"""
        import hashlib
        brand_id = hashlib.md5(brand_name.lower().encode()).hexdigest()[:12]

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO adintel_brands (brand_id, brand_name, domain, is_tracked, next_check)
                VALUES ($1, $2, $3, TRUE, NOW())
                ON CONFLICT (brand_id) DO UPDATE SET is_tracked = TRUE, updated_at = NOW()
            """, brand_id, brand_name, domain)

        # Queue immediate scrape
        await self.job_queue.enqueue("scrape", {
            "brand_id": brand_id,
            "brand_name": brand_name,
            "action": "full_scrape",
        })

        logger.info(f"📡 Now tracking brand: {brand_name} ({brand_id})")
        return brand_id

    async def scrape_brand(self, brand_name: str) -> List[ScrapedAd]:
        """Scrape all ads for a brand"""
        logger.info(f"🔍 Scraping ads for: {brand_name}")

        ads = await self.scraper.scrape_brand_page(
            brand_name,
            max_ads=self.config.max_ads_per_brand
        )

        # Save to PostgreSQL
        for ad in ads:
            await self._save_ad_to_db(ad)

            # Queue for enrichment
            await self.job_queue.enqueue("enrich", {
                "ad_id": ad.id,
                "video_url": ad.media_url,
            })

        # Update brand stats
        await self._update_brand_stats(brand_name, len(ads))

        logger.info(f"✅ Scraped {len(ads)} ads for {brand_name}")
        return ads

    async def enrich_ad(self, ad_id: str, video_url: Optional[str] = None) -> Optional[EnrichedAd]:
        """Run AI enrichment on an ad"""
        logger.info(f"🧠 Enriching ad: {ad_id}")

        try:
            enriched = await self.enrichment.enrich(ad_id, video_url)

            # Update PostgreSQL
            await self._update_enriched_ad(ad_id, enriched)

            # Index in Typesense
            ad_data = await self._get_ad_from_db(ad_id)
            if ad_data:
                doc = AdDocument.from_enriched_ad(ad_data)
                await self.search_engine.index_ad(doc)

            logger.info(f"✅ Enriched ad {ad_id}, winner_score: {enriched.winner_score}")
            return enriched

        except Exception as e:
            logger.error(f"❌ Enrichment failed for {ad_id}: {e}")
            return None

    async def sync_to_search(self, limit: int = 1000):
        """Sync PostgreSQL → Typesense (ETL)"""
        logger.info(f"🔄 Syncing {limit} ads to Typesense...")

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM adintel_ads
                WHERE enriched_at IS NOT NULL
                ORDER BY updated_at DESC
                LIMIT $1
            """, limit)

        documents = []
        for row in rows:
            doc = AdDocument.from_enriched_ad(dict(row))
            documents.append(doc)

        result = await self.search_engine.index_ads_batch(documents)
        logger.info(f"✅ Synced {result['success']} ads to Typesense")
        return result

    async def discover_ads(
        self,
        query: str = "*",
        industry: Optional[str] = None,
        emotion: Optional[str] = None,
        winners_only: bool = False,
        page: int = 1,
        per_page: int = 20,
    ):
        """Search ads (like Foreplay Discovery)"""
        filters = {}
        if industry:
            filters["industry"] = industry
        if emotion:
            filters["primary_emotion"] = emotion
        if winners_only:
            filters["is_winner"] = True

        return await self.search_engine.search(
            query=query,
            filters=filters,
            page=page,
            per_page=per_page,
        )

    # =========================================================================
    # DATABASE HELPERS
    # =========================================================================

    async def _save_ad_to_db(self, ad: ScrapedAd):
        """Save scraped ad to PostgreSQL"""
        # ScrapedAd uses: id, page_name, platform (enum), media_type (enum)
        platform_str = ad.platform.value if hasattr(ad.platform, 'value') else str(ad.platform)
        format_str = ad.media_type.value if hasattr(ad.media_type, 'value') else str(ad.media_type)

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO adintel_ads (
                    ad_id, brand_name, platform, format, headline, body_text,
                    thumbnail_url, video_url, landing_page_url,
                    running_duration_days, is_winner, first_seen, last_seen
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (ad_id) DO UPDATE SET
                    last_seen = EXCLUDED.last_seen,
                    running_duration_days = EXCLUDED.running_duration_days,
                    is_winner = EXCLUDED.is_winner,
                    updated_at = NOW()
            """,
                ad.id, ad.page_name, platform_str, format_str,
                ad.headline, ad.body_text, ad.thumbnail_url, ad.media_url,
                ad.landing_page_url, ad.running_duration_days,
                ad.running_duration_days >= self.config.winner_threshold_days,
                ad.first_seen, ad.last_seen
            )

    async def _update_enriched_ad(self, ad_id: str, enriched: EnrichedAd):
        """Update ad with enrichment data"""
        # EnrichedAd uses: nlp (not nlp_analysis), hook (not hook_analysis)
        # Extract primary emotion from emotional_drivers list
        primary_emotion = None
        emotional_drivers = []
        if enriched.nlp:
            emotional_drivers = enriched.nlp.emotional_drivers or []
            primary_emotion = emotional_drivers[0] if emotional_drivers else None

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE adintel_ads SET
                    transcription = $2,
                    primary_emotion = $3,
                    emotional_drivers = $4,
                    hook_type = $5,
                    hook_text = $6,
                    winning_patterns = $7,
                    winner_score = $8,
                    enriched_at = NOW(),
                    updated_at = NOW()
                WHERE ad_id = $1
            """,
                ad_id,
                enriched.transcription.full_text if enriched.transcription else None,
                primary_emotion,
                json.dumps(emotional_drivers),
                enriched.hook.hook_type if enriched.hook else None,
                enriched.hook.hook_text if enriched.hook else None,
                json.dumps(enriched.winning_patterns),
                int(enriched.winner_score),
            )

    async def _get_ad_from_db(self, ad_id: str) -> Optional[Dict]:
        """Get ad from PostgreSQL"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM adintel_ads WHERE ad_id = $1", ad_id
            )
            return dict(row) if row else None

    async def _update_brand_stats(self, brand_name: str, ad_count: int):
        """Update brand statistics"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE adintel_brands SET
                    total_ads = $2,
                    last_checked = NOW(),
                    next_check = NOW() + INTERVAL '1 hour' * check_interval_hours,
                    updated_at = NOW()
                WHERE brand_name = $1
            """, brand_name, ad_count)


# =============================================================================
# Workers - Run as separate processes
# =============================================================================

async def run_scrape_worker(orchestrator: AdIntelOrchestrator):
    """Worker that processes scrape jobs"""
    logger.info("🏃 Scrape worker started")

    while True:
        job = await orchestrator.job_queue.dequeue("scrape", timeout=30)
        if job:
            try:
                await orchestrator.scrape_brand(job["brand_name"])
            except Exception as e:
                logger.error(f"Scrape job failed: {e}")

        # Check for scheduled scrapes
        await check_scheduled_scrapes(orchestrator)


async def run_enrich_worker(orchestrator: AdIntelOrchestrator):
    """Worker that processes enrichment jobs"""
    logger.info("🏃 Enrich worker started")

    while True:
        job = await orchestrator.job_queue.dequeue("enrich", timeout=30)
        if job:
            try:
                await orchestrator.enrich_ad(job["ad_id"], job.get("video_url"))
            except Exception as e:
                logger.error(f"Enrich job failed: {e}")


async def check_scheduled_scrapes(orchestrator: AdIntelOrchestrator):
    """Check for brands that need re-scraping"""
    async with orchestrator.db_pool.acquire() as conn:
        brands = await conn.fetch("""
            SELECT brand_id, brand_name FROM adintel_brands
            WHERE is_tracked = TRUE AND next_check <= NOW()
            LIMIT 5
        """)

    for brand in brands:
        await orchestrator.job_queue.enqueue("scrape", {
            "brand_id": brand["brand_id"],
            "brand_name": brand["brand_name"],
            "action": "scheduled",
        })


# =============================================================================
# CLI / Entry Point
# =============================================================================

async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="AdIntel Orchestrator")
    parser.add_argument("command", choices=["init", "worker", "scrape", "sync", "api"])
    parser.add_argument("--brand", help="Brand name for scrape command")
    args = parser.parse_args()

    orchestrator = AdIntelOrchestrator()
    await orchestrator.initialize()

    try:
        if args.command == "init":
            logger.info("✅ Schema initialized")

        elif args.command == "worker":
            # Run both workers concurrently
            await asyncio.gather(
                run_scrape_worker(orchestrator),
                run_enrich_worker(orchestrator),
            )

        elif args.command == "scrape":
            if args.brand:
                await orchestrator.track_brand(args.brand)
                await orchestrator.scrape_brand(args.brand)
            else:
                logger.error("--brand required")

        elif args.command == "sync":
            await orchestrator.sync_to_search(limit=10000)

        elif args.command == "api":
            # Run the API server
            import uvicorn
            from .adintel_api import app
            uvicorn.run(app, host="0.0.0.0", port=8090)

    finally:
        await orchestrator.shutdown()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
