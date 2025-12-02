"""
Real Meta Ads Library API Scraper - Production Implementation
Agent 9/30 - ULTIMATE Production Plan
"""

from facebook_business.adobjects.adaccount import AdAccount
import requests
import logging
import json
import os
import time
from typing import Dict, List, Optional, Any, Iterator
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import urllib.parse

logger = logging.getLogger(__name__)


class AdPlatform(Enum):
    """Supported advertising platforms."""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    AUDIENCE_NETWORK = "audience_network"
    MESSENGER = "messenger"


class AdActiveStatus(Enum):
    """Ad active status filters."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ALL = "ALL"


@dataclass
class AdLibraryAd:
    """Meta Ads Library ad data structure."""
    id: str
    ad_archive_id: str
    page_id: str
    page_name: str
    ad_creative_bodies: List[str]
    ad_creative_link_captions: List[str]
    ad_creative_link_descriptions: List[str]
    ad_creative_link_titles: List[str]
    ad_delivery_start_time: str
    ad_delivery_stop_time: Optional[str]
    ad_snapshot_url: str
    currency: str
    funding_entity: str
    impressions: Optional[Dict[str, int]]
    spend: Optional[Dict[str, float]]
    bylines: Optional[str]
    languages: List[str]
    publisher_platforms: List[str]
    estimated_audience_size: Optional[Dict[str, int]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class RealAdsLibraryScraper:
    """Production Meta Ads Library API scraper with real API integration."""

    BASE_URL = "https://graph.facebook.com/v19.0/ads_archive"
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0

    def __init__(self, access_token: str):
        """
        Initialize scraper with Meta API access token.

        Args:
            access_token: Meta API access token with ads_read permission
        """
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MetaAdsLibraryScraper/1.0'
        })
        logger.info("Initialized RealAdsLibraryScraper")

    def search_ads(
        self,
        search_terms: str = None,
        ad_reached_countries: List[str] = ["US"],
        ad_active_status: AdActiveStatus = AdActiveStatus.ACTIVE,
        publisher_platforms: List[AdPlatform] = None,
        search_page_ids: List[str] = None,
        ad_type: str = "ALL",
        media_type: str = None,
        limit: int = 100
    ) -> List[AdLibraryAd]:
        """
        Search Meta Ads Library with filters.

        Args:
            search_terms: Keywords to search for
            ad_reached_countries: List of country codes (e.g., ["US", "GB"])
            ad_active_status: Filter by active status
            publisher_platforms: Platforms to search (Facebook, Instagram, etc.)
            search_page_ids: Filter by specific page IDs
            ad_type: "ALL" or "POLITICAL_AND_ISSUE_ADS"
            media_type: "IMAGE", "VIDEO", "MEME", or None for all
            limit: Maximum number of ads to return

        Returns:
            List of AdLibraryAd objects
        """
        logger.info(f"Searching ads with terms: {search_terms}, countries: {ad_reached_countries}")

        params = self._build_search_params(
            search_terms=search_terms,
            ad_reached_countries=ad_reached_countries,
            ad_active_status=ad_active_status,
            publisher_platforms=publisher_platforms,
            search_page_ids=search_page_ids,
            ad_type=ad_type,
            media_type=media_type,
            limit=min(limit, 1000)  # API max per request
        )

        all_ads = []
        total_fetched = 0

        for ads_batch in self._paginate_results(params, limit):
            all_ads.extend(ads_batch)
            total_fetched += len(ads_batch)

            if total_fetched >= limit:
                break

        logger.info(f"Retrieved {len(all_ads)} ads")
        return all_ads[:limit]

    def get_ad_details(self, ad_archive_id: str) -> AdLibraryAd:
        """
        Get detailed information for a specific ad.

        Args:
            ad_archive_id: The ad archive ID

        Returns:
            AdLibraryAd object with detailed information
        """
        logger.info(f"Fetching details for ad: {ad_archive_id}")

        params = {
            'access_token': self.access_token,
            'fields': self._get_fields_string(),
            'search_terms': ad_archive_id,
            'ad_reached_countries': 'US',
            'limit': 1
        }

        response = self._make_request(params)
        data = response.get('data', [])

        if not data:
            raise ValueError(f"Ad not found: {ad_archive_id}")

        return self._parse_ad(data[0])

    def get_page_ads(
        self,
        page_id: str,
        limit: int = 100,
        active_only: bool = True
    ) -> List[AdLibraryAd]:
        """
        Get all ads from a specific Facebook/Instagram page.

        Args:
            page_id: Facebook page ID
            limit: Maximum number of ads to return
            active_only: Only return currently active ads

        Returns:
            List of AdLibraryAd objects
        """
        logger.info(f"Fetching ads for page: {page_id}")

        status = AdActiveStatus.ACTIVE if active_only else AdActiveStatus.ALL

        return self.search_ads(
            search_page_ids=[page_id],
            ad_active_status=status,
            limit=limit
        )

    def download_ad_media(
        self,
        ad_archive_id: str,
        output_dir: str
    ) -> Dict[str, str]:
        """
        Download ad creative media (images/videos).

        Args:
            ad_archive_id: The ad archive ID
            output_dir: Directory to save media files

        Returns:
            Dictionary mapping media type to file path
        """
        logger.info(f"Downloading media for ad: {ad_archive_id}")

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Get ad snapshot URL
        ad = self.get_ad_details(ad_archive_id)

        downloaded_files = {}

        # Download snapshot HTML
        snapshot_path = os.path.join(output_dir, f"{ad_archive_id}_snapshot.html")
        try:
            response = self.session.get(ad.ad_snapshot_url, timeout=30)
            response.raise_for_status()

            with open(snapshot_path, 'w', encoding='utf-8') as f:
                f.write(response.text)

            downloaded_files['snapshot'] = snapshot_path
            logger.info(f"Downloaded snapshot to {snapshot_path}")
        except Exception as e:
            logger.error(f"Failed to download snapshot: {e}")

        return downloaded_files

    def extract_ad_copy(self, ad: AdLibraryAd) -> Dict[str, Any]:
        """
        Extract and structure ad copy elements.

        Args:
            ad: AdLibraryAd object

        Returns:
            Structured ad copy data
        """
        return {
            'headlines': ad.ad_creative_link_titles,
            'primary_text': ad.ad_creative_bodies,
            'descriptions': ad.ad_creative_link_descriptions,
            'captions': ad.ad_creative_link_captions,
            'page_name': ad.page_name,
            'languages': ad.languages,
            'platforms': ad.publisher_platforms,
            'call_to_actions': self._extract_ctas(ad),
            'hooks': self._extract_hooks(ad),
            'word_count': sum(len(text.split()) for text in ad.ad_creative_bodies),
        }

    def analyze_ad_patterns(
        self,
        ads: List[AdLibraryAd]
    ) -> Dict[str, Any]:
        """
        Analyze patterns across multiple ads.

        Args:
            ads: List of AdLibraryAd objects

        Returns:
            Pattern analysis results
        """
        logger.info(f"Analyzing patterns across {len(ads)} ads")

        if not ads:
            return {}

        # Hook patterns
        all_hooks = []
        for ad in ads:
            all_hooks.extend(self._extract_hooks(ad))

        # CTA patterns
        cta_counts = {}
        for ad in ads:
            for cta in self._extract_ctas(ad):
                cta_counts[cta] = cta_counts.get(cta, 0) + 1

        # Platform distribution
        platform_counts = {}
        for ad in ads:
            for platform in ad.publisher_platforms:
                platform_counts[platform] = platform_counts.get(platform, 0) + 1

        # Average copy length
        copy_lengths = []
        for ad in ads:
            for body in ad.ad_creative_bodies:
                copy_lengths.append(len(body.split()))

        avg_copy_length = sum(copy_lengths) / len(copy_lengths) if copy_lengths else 0

        # Active duration patterns
        durations = []
        for ad in ads:
            if ad.ad_delivery_stop_time:
                start = datetime.fromisoformat(ad.ad_delivery_start_time.replace('Z', '+00:00'))
                stop = datetime.fromisoformat(ad.ad_delivery_stop_time.replace('Z', '+00:00'))
                durations.append((stop - start).days)

        avg_duration = sum(durations) / len(durations) if durations else None

        return {
            'total_ads': len(ads),
            'common_hooks': self._get_top_items(all_hooks, 10),
            'cta_distribution': cta_counts,
            'platform_distribution': platform_counts,
            'avg_copy_length_words': round(avg_copy_length, 1),
            'avg_active_duration_days': round(avg_duration, 1) if avg_duration else None,
            'languages_used': list(set(lang for ad in ads for lang in ad.languages)),
        }

    def batch_scrape(
        self,
        queries: List[str],
        countries: List[str] = ["US"],
        limit_per_query: int = 50,
        delay_between_queries: float = 1.0
    ) -> Dict[str, List[AdLibraryAd]]:
        """
        Batch scrape multiple search terms with rate limiting.

        Args:
            queries: List of search terms
            countries: Countries to search in
            limit_per_query: Max ads per query
            delay_between_queries: Delay in seconds between requests

        Returns:
            Dictionary mapping query to list of ads
        """
        logger.info(f"Batch scraping {len(queries)} queries")

        results = {}

        for i, query in enumerate(queries):
            logger.info(f"Processing query {i+1}/{len(queries)}: {query}")

            try:
                ads = self.search_ads(
                    search_terms=query,
                    ad_reached_countries=countries,
                    limit=limit_per_query
                )
                results[query] = ads

                # Rate limiting
                if i < len(queries) - 1:
                    time.sleep(delay_between_queries)

            except Exception as e:
                logger.error(f"Failed to scrape query '{query}': {e}")
                results[query] = []

        return results

    def get_competitor_ads(
        self,
        competitor_page_ids: List[str],
        days_back: int = 30
    ) -> List[AdLibraryAd]:
        """
        Get competitor ads for analysis.

        Args:
            competitor_page_ids: List of competitor page IDs
            days_back: Number of days to look back

        Returns:
            List of all competitor ads
        """
        logger.info(f"Fetching competitor ads for {len(competitor_page_ids)} pages")

        all_ads = []

        for page_id in competitor_page_ids:
            try:
                ads = self.get_page_ads(
                    page_id=page_id,
                    limit=200,
                    active_only=False
                )

                # Filter by date
                cutoff_date = datetime.now() - timedelta(days=days_back)
                filtered_ads = [
                    ad for ad in ads
                    if datetime.fromisoformat(ad.ad_delivery_start_time.replace('Z', '+00:00')) >= cutoff_date
                ]

                all_ads.extend(filtered_ads)
                logger.info(f"Retrieved {len(filtered_ads)} ads from page {page_id}")

                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                logger.error(f"Failed to fetch ads for page {page_id}: {e}")

        return all_ads

    def export_to_json(
        self,
        ads: List[AdLibraryAd],
        output_path: str
    ) -> str:
        """
        Export ads to JSON file.

        Args:
            ads: List of AdLibraryAd objects
            output_path: Path to output JSON file

        Returns:
            Path to created file
        """
        logger.info(f"Exporting {len(ads)} ads to {output_path}")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        data = {
            'exported_at': datetime.now().isoformat(),
            'total_ads': len(ads),
            'ads': [ad.to_dict() for ad in ads]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully exported to {output_path}")
        return output_path

    # Private helper methods

    def _build_search_params(
        self,
        search_terms: Optional[str],
        ad_reached_countries: List[str],
        ad_active_status: AdActiveStatus,
        publisher_platforms: Optional[List[AdPlatform]],
        search_page_ids: Optional[List[str]],
        ad_type: str,
        media_type: Optional[str],
        limit: int
    ) -> Dict[str, Any]:
        """Build API request parameters."""
        params = {
            'access_token': self.access_token,
            'fields': self._get_fields_string(),
            'ad_reached_countries': json.dumps(ad_reached_countries),
            'ad_active_status': ad_active_status.value,
            'ad_type': ad_type,
            'limit': limit
        }

        if search_terms:
            params['search_terms'] = search_terms

        if publisher_platforms:
            params['publisher_platforms'] = json.dumps([p.value for p in publisher_platforms])

        if search_page_ids:
            params['search_page_ids'] = json.dumps(search_page_ids)

        if media_type:
            params['media_type'] = media_type

        return params

    def _get_fields_string(self) -> str:
        """Get API fields string."""
        return ','.join([
            'id',
            'ad_archive_id',
            'page_id',
            'page_name',
            'ad_creative_bodies',
            'ad_creative_link_captions',
            'ad_creative_link_descriptions',
            'ad_creative_link_titles',
            'ad_delivery_start_time',
            'ad_delivery_stop_time',
            'ad_snapshot_url',
            'currency',
            'funding_entity',
            'impressions',
            'spend',
            'bylines',
            'languages',
            'publisher_platforms',
            'estimated_audience_size'
        ])

    def _paginate_results(
        self,
        params: Dict[str, Any],
        max_results: int
    ) -> Iterator[List[AdLibraryAd]]:
        """Paginate through API results."""
        total_fetched = 0
        next_url = None

        while total_fetched < max_results:
            if next_url:
                response = self._make_request_url(next_url)
            else:
                response = self._make_request(params)

            data = response.get('data', [])

            if not data:
                break

            ads = [self._parse_ad(ad_data) for ad_data in data]
            yield ads

            total_fetched += len(ads)

            # Check for next page
            paging = response.get('paging', {})
            next_url = paging.get('next')

            if not next_url:
                break

            time.sleep(0.2)  # Rate limiting between pages

    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request with retry logic."""
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.get(
                    self.BASE_URL,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")

                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    raise

    def _make_request_url(self, url: str) -> Dict[str, Any]:
        """Make request to a specific URL (for pagination)."""
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")

                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    raise

    def _parse_ad(self, data: Dict[str, Any]) -> AdLibraryAd:
        """Parse API response into AdLibraryAd object."""
        return AdLibraryAd(
            id=data.get('id', ''),
            ad_archive_id=data.get('ad_archive_id', ''),
            page_id=data.get('page_id', ''),
            page_name=data.get('page_name', ''),
            ad_creative_bodies=data.get('ad_creative_bodies', []),
            ad_creative_link_captions=data.get('ad_creative_link_captions', []),
            ad_creative_link_descriptions=data.get('ad_creative_link_descriptions', []),
            ad_creative_link_titles=data.get('ad_creative_link_titles', []),
            ad_delivery_start_time=data.get('ad_delivery_start_time', ''),
            ad_delivery_stop_time=data.get('ad_delivery_stop_time'),
            ad_snapshot_url=data.get('ad_snapshot_url', ''),
            currency=data.get('currency', 'USD'),
            funding_entity=data.get('funding_entity', ''),
            impressions=data.get('impressions'),
            spend=data.get('spend'),
            bylines=data.get('bylines'),
            languages=data.get('languages', []),
            publisher_platforms=data.get('publisher_platforms', []),
            estimated_audience_size=data.get('estimated_audience_size')
        )

    def _extract_hooks(self, ad: AdLibraryAd) -> List[str]:
        """Extract hook patterns from ad copy."""
        hooks = []

        for body in ad.ad_creative_bodies:
            # Extract first sentence as hook
            sentences = body.split('.')
            if sentences:
                hook = sentences[0].strip()
                if len(hook) > 10:  # Minimum hook length
                    hooks.append(hook)

        return hooks

    def _extract_ctas(self, ad: AdLibraryAd) -> List[str]:
        """Extract call-to-action patterns."""
        # Common CTA patterns - would be extracted from actual ad data in production
        cta_keywords = ['learn more', 'shop now', 'sign up', 'get started', 'download', 'buy now']

        ctas = []
        for body in ad.ad_creative_bodies:
            body_lower = body.lower()
            for cta in cta_keywords:
                if cta in body_lower:
                    ctas.append(cta.title())

        return list(set(ctas))

    def _get_top_items(self, items: List[str], limit: int = 10) -> List[tuple]:
        """Get top occurring items."""
        counts = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1

        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:limit]
