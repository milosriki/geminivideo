"""
AdIntel OS - AI-Powered Ad Intelligence Platform
Your own Foreplay alternative, fully owned

Components:
- ad_library_scraper: Direct Meta Ad Library scraping
- ad_enrichment: AI pipeline (Whisper + Gemini + Llama)
- search_engine: Typesense-powered discovery
- adintel_api: REST API with credits

External Integrations (for bootstrapping/learning):
- foreplay_scraper: Official Foreplay API integration
- creatorify_client: Creatify AI URL-to-Video

Data Management:
- fb_historical_import: Facebook historical data injector
- metrics_comparator: Performance comparison engine
"""

# Core AdIntel components
from .ad_library_scraper import (
    MetaAdLibraryScraper,
    BrandTracker,
    WinnerDetector,
    ScrapedAd,
    BrandProfile,
)

from .ad_enrichment import (
    AdEnrichmentPipeline,
    WhisperClient,
    GeminiAnalyzer,
    LlamaAnalyzer,
    EnrichedAd,
    TranscriptionResult,
    HookAnalysis,
)

from .search_engine import (
    AdSearchEngine,
    AdDocument,
    SearchConfig,
    SearchResponse,
    AdIndexingPipeline,
)

from .adintel_api import app as adintel_app

# External integrations (for learning phase)
from .foreplay_scraper import ForeplayIntegration
from .creatorify_client import CreatifyIntegration

# Data management
from .fb_historical_import import FacebookHistoricalImporter
from .metrics_comparator import MetricsComparator

__all__ = [
    # Core
    "MetaAdLibraryScraper",
    "BrandTracker",
    "WinnerDetector",
    "ScrapedAd",
    "BrandProfile",
    "AdEnrichmentPipeline",
    "WhisperClient",
    "GeminiAnalyzer",
    "LlamaAnalyzer",
    "EnrichedAd",
    "TranscriptionResult",
    "HookAnalysis",
    "AdSearchEngine",
    "AdDocument",
    "SearchConfig",
    "SearchResponse",
    "AdIndexingPipeline",
    "adintel_app",
    # External
    "ForeplayIntegration",
    "CreatifyIntegration",
    # Data
    "FacebookHistoricalImporter",
    "MetricsComparator",
]

__version__ = "1.0.0"
