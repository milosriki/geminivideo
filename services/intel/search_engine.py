"""
AdIntel OS - Typesense Search Engine
Fast faceted search for ad discovery (replaces Foreplay Discovery)

Features:
- Schema-based indexing for ads
- Faceted search (industry, platform, format, emotion)
- Vector search for semantic matching
- Auto-suggestions
- Winner filtering
"""

import typesense
from typesense.exceptions import ObjectNotFound, ObjectAlreadyExists
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import asyncio
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Search Configuration
# =============================================================================

@dataclass
class SearchConfig:
    """Typesense connection configuration"""
    host: str = "localhost"
    port: int = 8108
    protocol: str = "http"
    api_key: str = ""  # Set from environment
    connection_timeout_seconds: int = 10

    @classmethod
    def from_env(cls):
        import os
        return cls(
            host=os.getenv("TYPESENSE_HOST", "localhost"),
            port=int(os.getenv("TYPESENSE_PORT", "8108")),
            protocol=os.getenv("TYPESENSE_PROTOCOL", "http"),
            api_key=os.getenv("TYPESENSE_API_KEY", ""),
        )


# =============================================================================
# Ad Document Schema
# =============================================================================

AD_COLLECTION_SCHEMA = {
    "name": "ads",
    "fields": [
        # Core identifiers
        {"name": "id", "type": "string"},
        {"name": "ad_id", "type": "string", "facet": True},
        {"name": "brand_name", "type": "string", "facet": True},
        {"name": "brand_id", "type": "string", "optional": True},

        # Platform & Format
        {"name": "platform", "type": "string", "facet": True},  # meta, tiktok, google
        {"name": "format", "type": "string", "facet": True},    # video, image, carousel
        {"name": "placement", "type": "string", "facet": True, "optional": True},  # feed, story, reels

        # Content
        {"name": "headline", "type": "string", "optional": True},
        {"name": "body_text", "type": "string", "optional": True},
        {"name": "transcription", "type": "string", "optional": True},
        {"name": "cta", "type": "string", "facet": True, "optional": True},

        # Searchable combined text
        {"name": "search_text", "type": "string"},

        # Industry & Category
        {"name": "industry", "type": "string", "facet": True, "optional": True},
        {"name": "category", "type": "string", "facet": True, "optional": True},
        {"name": "subcategory", "type": "string", "facet": True, "optional": True},

        # Emotional Drivers (facets)
        {"name": "primary_emotion", "type": "string", "facet": True, "optional": True},
        {"name": "emotional_drivers", "type": "string[]", "facet": True, "optional": True},

        # Hook & Pattern Analysis
        {"name": "hook_type", "type": "string", "facet": True, "optional": True},
        {"name": "hook_text", "type": "string", "optional": True},
        {"name": "winning_patterns", "type": "string[]", "facet": True, "optional": True},

        # Performance Signals
        {"name": "running_duration_days", "type": "int32"},
        {"name": "is_winner", "type": "bool", "facet": True},
        {"name": "winner_score", "type": "int32", "optional": True},
        {"name": "estimated_spend", "type": "float", "optional": True},

        # Dates
        {"name": "first_seen", "type": "int64"},  # Unix timestamp
        {"name": "last_seen", "type": "int64"},
        {"name": "created_at", "type": "int64"},

        # Media
        {"name": "thumbnail_url", "type": "string", "optional": True},
        {"name": "video_url", "type": "string", "optional": True},
        {"name": "landing_page_url", "type": "string", "optional": True},

        # Tags & Custom
        {"name": "tags", "type": "string[]", "facet": True, "optional": True},
        {"name": "collections", "type": "string[]", "facet": True, "optional": True},

        # Vector embedding for semantic search
        {"name": "embedding", "type": "float[]", "num_dim": 768, "optional": True},
    ],
    "default_sorting_field": "running_duration_days",
    "token_separators": ["-", "_", "/"],
    "symbols_to_index": ["#", "@"],
}


# Brand collection for tracking
BRAND_COLLECTION_SCHEMA = {
    "name": "brands",
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "name", "type": "string"},
        {"name": "domain", "type": "string", "optional": True},
        {"name": "industry", "type": "string", "facet": True, "optional": True},
        {"name": "ad_count", "type": "int32"},
        {"name": "avg_running_days", "type": "float"},
        {"name": "winner_count", "type": "int32"},
        {"name": "platforms", "type": "string[]", "facet": True},
        {"name": "last_updated", "type": "int64"},
    ],
    "default_sorting_field": "ad_count",
}


# =============================================================================
# Search Documents
# =============================================================================

@dataclass
class AdDocument:
    """Document for indexing in Typesense"""
    id: str
    ad_id: str
    brand_name: str
    platform: str
    format: str
    running_duration_days: int
    is_winner: bool
    first_seen: int
    last_seen: int
    created_at: int
    search_text: str

    # Optional fields
    brand_id: Optional[str] = None
    placement: Optional[str] = None
    headline: Optional[str] = None
    body_text: Optional[str] = None
    transcription: Optional[str] = None
    cta: Optional[str] = None
    industry: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    primary_emotion: Optional[str] = None
    emotional_drivers: List[str] = field(default_factory=list)
    hook_type: Optional[str] = None
    hook_text: Optional[str] = None
    winning_patterns: List[str] = field(default_factory=list)
    winner_score: Optional[int] = None
    estimated_spend: Optional[float] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    landing_page_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    collections: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None

    @classmethod
    def from_enriched_ad(cls, enriched_ad: Dict[str, Any]) -> "AdDocument":
        """Create document from enriched ad data"""
        ad_id = enriched_ad.get("ad_id", "")

        # Build search text from all text content
        search_parts = [
            enriched_ad.get("brand_name", ""),
            enriched_ad.get("headline", ""),
            enriched_ad.get("body_text", ""),
            enriched_ad.get("transcription", ""),
            enriched_ad.get("hook_text", ""),
        ]
        search_text = " ".join(filter(None, search_parts))

        # Parse dates to timestamps
        first_seen = enriched_ad.get("first_seen")
        last_seen = enriched_ad.get("last_seen")

        if isinstance(first_seen, datetime):
            first_seen = int(first_seen.timestamp())
        elif isinstance(first_seen, str):
            first_seen = int(datetime.fromisoformat(first_seen).timestamp())
        else:
            first_seen = first_seen or int(datetime.now().timestamp())

        if isinstance(last_seen, datetime):
            last_seen = int(last_seen.timestamp())
        elif isinstance(last_seen, str):
            last_seen = int(datetime.fromisoformat(last_seen).timestamp())
        else:
            last_seen = last_seen or int(datetime.now().timestamp())

        running_days = enriched_ad.get("running_duration_days", 0)

        return cls(
            id=hashlib.md5(ad_id.encode()).hexdigest(),
            ad_id=ad_id,
            brand_name=enriched_ad.get("brand_name", "Unknown"),
            brand_id=enriched_ad.get("brand_id"),
            platform=enriched_ad.get("platform", "meta"),
            format=enriched_ad.get("format", "video"),
            placement=enriched_ad.get("placement"),
            headline=enriched_ad.get("headline"),
            body_text=enriched_ad.get("body_text"),
            transcription=enriched_ad.get("transcription"),
            cta=enriched_ad.get("cta"),
            industry=enriched_ad.get("industry"),
            category=enriched_ad.get("category"),
            subcategory=enriched_ad.get("subcategory"),
            primary_emotion=enriched_ad.get("primary_emotion"),
            emotional_drivers=enriched_ad.get("emotional_drivers", []),
            hook_type=enriched_ad.get("hook_type"),
            hook_text=enriched_ad.get("hook_text"),
            winning_patterns=enriched_ad.get("winning_patterns", []),
            running_duration_days=running_days,
            is_winner=running_days >= 30,
            winner_score=enriched_ad.get("winner_score"),
            estimated_spend=enriched_ad.get("estimated_spend"),
            first_seen=first_seen,
            last_seen=last_seen,
            created_at=int(datetime.now().timestamp()),
            search_text=search_text,
            thumbnail_url=enriched_ad.get("thumbnail_url"),
            video_url=enriched_ad.get("video_url"),
            landing_page_url=enriched_ad.get("landing_page_url"),
            tags=enriched_ad.get("tags", []),
            collections=enriched_ad.get("collections", []),
            embedding=enriched_ad.get("embedding"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for indexing"""
        d = asdict(self)
        # Remove None values and empty lists for optional fields
        return {k: v for k, v in d.items() if v is not None and v != []}


@dataclass
class SearchResult:
    """Search result with highlights"""
    document: AdDocument
    score: float
    highlights: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_hit(cls, hit: Dict[str, Any]) -> "SearchResult":
        doc_dict = hit["document"]
        # Reconstruct AdDocument
        doc = AdDocument(
            id=doc_dict["id"],
            ad_id=doc_dict["ad_id"],
            brand_name=doc_dict["brand_name"],
            platform=doc_dict["platform"],
            format=doc_dict["format"],
            running_duration_days=doc_dict["running_duration_days"],
            is_winner=doc_dict["is_winner"],
            first_seen=doc_dict["first_seen"],
            last_seen=doc_dict["last_seen"],
            created_at=doc_dict["created_at"],
            search_text=doc_dict.get("search_text", ""),
        )
        # Add optional fields
        for field_name in ["headline", "body_text", "transcription", "industry",
                          "primary_emotion", "hook_type", "winner_score", "thumbnail_url"]:
            if field_name in doc_dict:
                setattr(doc, field_name, doc_dict[field_name])

        return cls(
            document=doc,
            score=hit.get("text_match", 0),
            highlights=hit.get("highlights", {}),
        )


@dataclass
class FacetCount:
    """Facet value with count"""
    value: str
    count: int


@dataclass
class SearchResponse:
    """Complete search response"""
    hits: List[SearchResult]
    found: int
    page: int
    per_page: int
    facets: Dict[str, List[FacetCount]] = field(default_factory=dict)
    search_time_ms: int = 0


# =============================================================================
# Search Engine Client
# =============================================================================

class AdSearchEngine:
    """
    Typesense-powered search engine for ad discovery

    Similar to Foreplay's Discovery feature but fully owned
    """

    def __init__(self, config: Optional[SearchConfig] = None):
        self.config = config or SearchConfig.from_env()
        self.client = typesense.Client({
            "nodes": [{
                "host": self.config.host,
                "port": str(self.config.port),
                "protocol": self.config.protocol,
            }],
            "api_key": self.config.api_key,
            "connection_timeout_seconds": self.config.connection_timeout_seconds,
        })

    async def initialize(self):
        """Create collections if they don't exist"""
        try:
            await asyncio.to_thread(
                self.client.collections.create, AD_COLLECTION_SCHEMA
            )
            logger.info("Created 'ads' collection")
        except ObjectAlreadyExists:
            logger.info("'ads' collection already exists")

        try:
            await asyncio.to_thread(
                self.client.collections.create, BRAND_COLLECTION_SCHEMA
            )
            logger.info("Created 'brands' collection")
        except ObjectAlreadyExists:
            logger.info("'brands' collection already exists")

    async def index_ad(self, ad_doc: AdDocument) -> bool:
        """Index a single ad document"""
        try:
            await asyncio.to_thread(
                self.client.collections["ads"].documents.upsert,
                ad_doc.to_dict()
            )
            return True
        except Exception as e:
            logger.error(f"Failed to index ad {ad_doc.ad_id}: {e}")
            return False

    async def index_ads_batch(self, ads: List[AdDocument], batch_size: int = 100) -> Dict[str, int]:
        """Batch index ads for efficiency"""
        results = {"success": 0, "failed": 0}

        for i in range(0, len(ads), batch_size):
            batch = ads[i:i + batch_size]
            docs = [ad.to_dict() for ad in batch]

            try:
                response = await asyncio.to_thread(
                    self.client.collections["ads"].documents.import_,
                    docs,
                    {"action": "upsert"}
                )

                for item in response:
                    if item.get("success"):
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                        logger.warning(f"Failed: {item.get('error')}")

            except Exception as e:
                logger.error(f"Batch import failed: {e}")
                results["failed"] += len(batch)

        logger.info(f"Indexed {results['success']} ads, {results['failed']} failed")
        return results

    async def search(
        self,
        query: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        facet_by: Optional[List[str]] = None,
        sort_by: str = "running_duration_days:desc",
        page: int = 1,
        per_page: int = 20,
        include_fields: Optional[List[str]] = None,
    ) -> SearchResponse:
        """
        Search ads with filters and facets

        Args:
            query: Search query (use * for all)
            filters: Filter conditions e.g. {"platform": "meta", "is_winner": True}
            facet_by: Fields to get facet counts for
            sort_by: Sort field and direction
            page: Page number (1-indexed)
            per_page: Results per page
            include_fields: Fields to return (None = all)
        """
        # Build filter string
        filter_by = self._build_filter_string(filters) if filters else ""

        # Default facets
        if facet_by is None:
            facet_by = ["platform", "industry", "primary_emotion", "is_winner", "hook_type"]

        search_params = {
            "q": query,
            "query_by": "search_text,brand_name,headline,transcription",
            "filter_by": filter_by,
            "facet_by": ",".join(facet_by),
            "sort_by": sort_by,
            "page": page,
            "per_page": per_page,
            "highlight_full_fields": "headline,transcription",
        }

        if include_fields:
            search_params["include_fields"] = ",".join(include_fields)

        try:
            result = await asyncio.to_thread(
                self.client.collections["ads"].documents.search,
                search_params
            )

            # Parse results
            hits = [SearchResult.from_hit(hit) for hit in result.get("hits", [])]

            # Parse facets
            facets = {}
            for facet in result.get("facet_counts", []):
                field_name = facet["field_name"]
                facets[field_name] = [
                    FacetCount(value=c["value"], count=c["count"])
                    for c in facet.get("counts", [])
                ]

            return SearchResponse(
                hits=hits,
                found=result.get("found", 0),
                page=page,
                per_page=per_page,
                facets=facets,
                search_time_ms=result.get("search_time_ms", 0),
            )

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return SearchResponse(hits=[], found=0, page=page, per_page=per_page)

    async def search_winners(
        self,
        industry: Optional[str] = None,
        platform: Optional[str] = None,
        emotion: Optional[str] = None,
        min_days: int = 30,
        page: int = 1,
        per_page: int = 20,
    ) -> SearchResponse:
        """Search for winning ads only"""
        filters = {"is_winner": True, "running_duration_days": f">={min_days}"}

        if industry:
            filters["industry"] = industry
        if platform:
            filters["platform"] = platform
        if emotion:
            filters["primary_emotion"] = emotion

        return await self.search(
            query="*",
            filters=filters,
            sort_by="winner_score:desc,running_duration_days:desc",
            page=page,
            per_page=per_page,
        )

    async def search_by_emotion(
        self,
        emotion: str,
        include_related: bool = True,
        page: int = 1,
        per_page: int = 20,
    ) -> SearchResponse:
        """Search ads by emotional driver"""
        if include_related:
            # Search primary + emotional_drivers array
            filters = {"primary_emotion": emotion}
        else:
            filters = {"primary_emotion": emotion}

        return await self.search(
            query="*",
            filters=filters,
            facet_by=["hook_type", "winning_patterns", "industry"],
            page=page,
            per_page=per_page,
        )

    async def search_by_hook_type(
        self,
        hook_type: str,
        page: int = 1,
        per_page: int = 20,
    ) -> SearchResponse:
        """Search ads by hook type (question, statement, shocking, etc.)"""
        return await self.search(
            query="*",
            filters={"hook_type": hook_type},
            facet_by=["primary_emotion", "industry", "platform"],
            page=page,
            per_page=per_page,
        )

    async def search_similar(
        self,
        ad_id: str,
        limit: int = 10,
    ) -> SearchResponse:
        """Find similar ads using vector search (requires embeddings)"""
        # First get the ad's embedding
        try:
            doc = await asyncio.to_thread(
                self.client.collections["ads"].documents[ad_id].retrieve
            )
        except ObjectNotFound:
            return SearchResponse(hits=[], found=0, page=1, per_page=limit)

        embedding = doc.get("embedding")
        if not embedding:
            # Fall back to text search on same brand/industry
            return await self.search(
                query="*",
                filters={
                    "industry": doc.get("industry"),
                    "id": f"!={ad_id}",  # Exclude original
                },
                per_page=limit,
            )

        # Vector search
        search_params = {
            "q": "*",
            "vector_query": f"embedding:([{','.join(map(str, embedding))}], k:{limit})",
            "filter_by": f"id:!={ad_id}",
            "per_page": limit,
        }

        try:
            result = await asyncio.to_thread(
                self.client.collections["ads"].documents.search,
                search_params
            )
            hits = [SearchResult.from_hit(hit) for hit in result.get("hits", [])]
            return SearchResponse(hits=hits, found=len(hits), page=1, per_page=limit)
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return SearchResponse(hits=[], found=0, page=1, per_page=limit)

    async def get_suggestions(
        self,
        query: str,
        limit: int = 10,
    ) -> List[str]:
        """Get autocomplete suggestions"""
        try:
            result = await asyncio.to_thread(
                self.client.collections["ads"].documents.search,
                {
                    "q": query,
                    "query_by": "brand_name,headline",
                    "prefix": True,
                    "per_page": limit,
                    "include_fields": "brand_name,headline",
                }
            )

            suggestions = set()
            for hit in result.get("hits", []):
                doc = hit["document"]
                if doc.get("brand_name"):
                    suggestions.add(doc["brand_name"])
                if doc.get("headline"):
                    # Extract matching portion
                    suggestions.add(doc["headline"][:50])

            return list(suggestions)[:limit]

        except Exception as e:
            logger.error(f"Suggestions failed: {e}")
            return []

    async def get_brand_analytics(self, brand_name: str) -> Dict[str, Any]:
        """Get analytics for a specific brand"""
        result = await self.search(
            query="*",
            filters={"brand_name": brand_name},
            facet_by=["platform", "format", "primary_emotion", "hook_type", "is_winner"],
            per_page=100,
        )

        if result.found == 0:
            return {}

        # Calculate analytics
        winner_count = sum(1 for h in result.hits if h.document.is_winner)
        avg_duration = sum(h.document.running_duration_days for h in result.hits) / len(result.hits)

        return {
            "brand_name": brand_name,
            "total_ads": result.found,
            "winner_count": winner_count,
            "winner_rate": winner_count / result.found if result.found > 0 else 0,
            "avg_running_days": round(avg_duration, 1),
            "facets": {k: [{"value": f.value, "count": f.count} for f in v] for k, v in result.facets.items()},
        }

    async def get_industry_trends(self) -> Dict[str, Any]:
        """Get trending patterns across industries"""
        result = await self.search(
            query="*",
            filters={"is_winner": True},
            facet_by=["industry", "primary_emotion", "hook_type", "winning_patterns"],
            per_page=0,  # Only need facets
        )

        return {
            "total_winners": result.found,
            "by_industry": result.facets.get("industry", []),
            "by_emotion": result.facets.get("primary_emotion", []),
            "by_hook_type": result.facets.get("hook_type", []),
            "top_patterns": result.facets.get("winning_patterns", [])[:10],
        }

    async def delete_ad(self, ad_id: str) -> bool:
        """Delete an ad from the index"""
        try:
            doc_id = hashlib.md5(ad_id.encode()).hexdigest()
            await asyncio.to_thread(
                self.client.collections["ads"].documents[doc_id].delete
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete ad {ad_id}: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            ads_info = await asyncio.to_thread(
                self.client.collections["ads"].retrieve
            )
            return {
                "total_ads": ads_info.get("num_documents", 0),
                "fields": len(ads_info.get("fields", [])),
                "created_at": ads_info.get("created_at"),
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"total_ads": 0, "error": str(e)}

    def _build_filter_string(self, filters: Dict[str, Any]) -> str:
        """Build Typesense filter string from dict"""
        parts = []
        for key, value in filters.items():
            if value is None:
                continue
            if isinstance(value, bool):
                parts.append(f"{key}:={str(value).lower()}")
            elif isinstance(value, str):
                if value.startswith(">=") or value.startswith("<=") or value.startswith("!="):
                    parts.append(f"{key}:{value}")
                else:
                    parts.append(f"{key}:={value}")
            elif isinstance(value, (int, float)):
                parts.append(f"{key}:={value}")
            elif isinstance(value, list):
                parts.append(f"{key}:[{','.join(value)}]")

        return " && ".join(parts)


# =============================================================================
# Indexing Pipeline
# =============================================================================

class AdIndexingPipeline:
    """
    Pipeline to index ads from scrapers and enrichment

    Connects:
    - MetaAdLibraryScraper -> AdEnrichmentPipeline -> AdSearchEngine
    """

    def __init__(
        self,
        search_engine: AdSearchEngine,
        embedding_model: Optional[Any] = None,  # For vector search
    ):
        self.search = search_engine
        self.embedding_model = embedding_model

    async def index_from_scraper(
        self,
        scraped_ads: List[Dict[str, Any]],
        enriched: bool = True,
    ) -> Dict[str, int]:
        """Index ads from scraper output"""
        documents = []

        for ad in scraped_ads:
            # Convert to document format
            doc = AdDocument.from_enriched_ad(ad)

            # Generate embedding if model available
            if self.embedding_model and enriched:
                doc.embedding = await self._generate_embedding(doc)

            documents.append(doc)

        return await self.search.index_ads_batch(documents)

    async def _generate_embedding(self, doc: AdDocument) -> Optional[List[float]]:
        """Generate embedding for semantic search"""
        if not self.embedding_model:
            return None

        # Combine text for embedding
        text = f"{doc.brand_name} {doc.headline or ''} {doc.transcription or ''}"

        try:
            # Assuming embedding model has encode method
            embedding = await asyncio.to_thread(
                self.embedding_model.encode, text
            )
            return embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

    async def reindex_all(self, ads_source) -> Dict[str, int]:
        """Full reindex from data source"""
        # Delete existing and recreate
        try:
            await asyncio.to_thread(
                self.search.client.collections["ads"].delete
            )
        except ObjectNotFound:
            pass

        await self.search.initialize()

        # Get all ads and index
        all_ads = await ads_source.get_all_ads()
        return await self.index_from_scraper(all_ads)


# =============================================================================
# Usage Example
# =============================================================================

async def main():
    """Example usage of search engine"""
    # Initialize
    config = SearchConfig(
        host="localhost",
        port=8108,
        protocol="http",
        api_key="your-api-key",
    )

    engine = AdSearchEngine(config)
    await engine.initialize()

    # Example: Index some ads
    sample_ad = AdDocument.from_enriched_ad({
        "ad_id": "123456789",
        "brand_name": "Acme Corp",
        "platform": "meta",
        "format": "video",
        "headline": "Transform Your Morning Routine",
        "transcription": "Are you tired of feeling tired? Our product will change everything...",
        "industry": "health",
        "primary_emotion": "aspiration",
        "hook_type": "question",
        "running_duration_days": 45,
        "winner_score": 85,
        "first_seen": datetime.now(),
        "last_seen": datetime.now(),
    })

    await engine.index_ad(sample_ad)

    # Search for winners
    results = await engine.search_winners(
        industry="health",
        min_days=30,
        per_page=20,
    )

    print(f"Found {results.found} winning ads")
    for hit in results.hits:
        print(f"  - {hit.document.brand_name}: {hit.document.headline}")

    # Get industry trends
    trends = await engine.get_industry_trends()
    print(f"\nTop emotions: {trends['by_emotion'][:5]}")
    print(f"Top hook types: {trends['by_hook_type'][:5]}")


if __name__ == "__main__":
    asyncio.run(main())
