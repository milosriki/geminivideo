"""
Meta Ads Library Integration - Real API Implementation
Connects to Facebook Ads Library API to search, download, and analyze ads
"""
import os
import logging
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from collections import Counter
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class RealMetaAdsLibrary:
    """
    Real implementation of Meta Ads Library integration using Facebook Business SDK.
    Provides production-ready methods for searching, downloading, and analyzing ads.
    """

    def __init__(self):
        """Initialize Meta Ads Library with credentials from environment"""
        self.access_token = os.getenv("META_ACCESS_TOKEN")
        self.app_id = os.getenv("META_APP_ID")
        self.app_secret = os.getenv("META_APP_SECRET")

        self.enabled = False
        self.api = None
        self.ad_account = None

        # Initialize Facebook Business SDK
        if self.access_token and self.app_id and self.app_secret:
            try:
                from facebook_business.api import FacebookAdsApi
                from facebook_business.adobjects.adaccount import AdAccount

                # Initialize API
                FacebookAdsApi.init(
                    app_id=self.app_id,
                    app_secret=self.app_secret,
                    access_token=self.access_token
                )
                self.api = FacebookAdsApi.get_default_api()
                self.enabled = True
                logger.info("✅ Meta Ads Library API initialized successfully")

            except ImportError:
                logger.warning(
                    "Facebook Business SDK not installed. "
                    "Install with: pip install facebook-business"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Meta Ads Library API: {e}")
        else:
            logger.warning(
                "Meta Ads Library credentials not configured. "
                "Set META_ACCESS_TOKEN, META_APP_ID, and META_APP_SECRET environment variables."
            )

    def search_ads(
        self,
        search_terms: str,
        countries: List[str] = None,
        media_type: str = "VIDEO",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search Meta Ads Library for ads matching criteria.

        Args:
            search_terms: Keywords to search for
            countries: List of country codes (e.g., ['US', 'GB'])
            media_type: Type of media ('VIDEO', 'IMAGE', 'ALL')
            limit: Maximum number of ads to return

        Returns:
            List of ad dictionaries with metadata
        """
        if not self.enabled:
            logger.warning("Meta Ads Library not enabled, returning empty results")
            return []

        try:
            from facebook_business.adobjects.adarchive import AdArchive

            # Build search parameters
            params = {
                'search_terms': search_terms,
                'ad_reached_countries': countries or ['US'],
                'ad_active_status': 'ALL',
                'limit': limit,
            }

            # Filter by media type if specified
            if media_type != 'ALL':
                params['ad_type'] = media_type

            # Search Ad Library
            logger.info(f"Searching Meta Ads Library: '{search_terms}' in {countries}")
            ads = []

            # Use Graph API directly for Ad Library search
            url = "https://graph.facebook.com/v18.0/ads_archive"
            params['access_token'] = self.access_token

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if 'data' in data:
                for ad_data in data['data']:
                    ad = self._parse_ad_data(ad_data)
                    if ad:
                        ads.append(ad)

                logger.info(f"Found {len(ads)} ads matching criteria")
            else:
                logger.warning("No ads found in response")

            return ads

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to search ads: {e}")
            return []

    def download_video(self, video_url: str, output_path: str) -> str:
        """
        Download video from Meta ad.

        Args:
            video_url: URL of the video to download
            output_path: Local path to save the video

        Returns:
            Path to downloaded video file
        """
        try:
            logger.info(f"Downloading video from: {video_url}")

            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # Download video
            response = requests.get(video_url, stream=True)
            response.raise_for_status()

            # Save to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"✅ Video downloaded to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            return ""

    def analyze_top_performers(
        self,
        niche_keywords: str,
        min_impressions: int = 10000,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Analyze top-performing ads in a niche.

        Args:
            niche_keywords: Keywords defining the niche
            min_impressions: Minimum impression threshold
            limit: Number of ads to analyze

        Returns:
            Dictionary with analysis insights
        """
        try:
            logger.info(f"Analyzing top performers for: {niche_keywords}")

            # Search for ads
            ads = self.search_ads(
                search_terms=niche_keywords,
                countries=['US'],
                media_type='VIDEO',
                limit=limit
            )

            if not ads:
                logger.warning("No ads found for analysis")
                return self._empty_analysis()

            # Filter by impressions
            high_performers = [
                ad for ad in ads
                if self._get_min_impressions(ad) >= min_impressions
            ]

            logger.info(f"Found {len(high_performers)} high-performing ads")

            # Analyze patterns
            analysis = {
                'total_ads_analyzed': len(high_performers),
                'date_range': self._analyze_date_range(high_performers),
                'copy_patterns': self._analyze_copy_patterns(high_performers),
                'timing_patterns': self._analyze_timing_patterns(high_performers),
                'spend_analysis': self._analyze_spend(high_performers),
                'top_ads': high_performers[:10],  # Top 10 performers
                'analyzed_at': datetime.utcnow().isoformat()
            }

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze top performers: {e}")
            return self._empty_analysis()

    def _parse_ad_data(self, ad_data: Dict) -> Optional[Dict]:
        """
        Parse raw ad data from API into standardized format.

        Args:
            ad_data: Raw ad data from API

        Returns:
            Parsed ad dictionary
        """
        try:
            return {
                'id': ad_data.get('id'),
                'ad_creative_body': ad_data.get('ad_creative_body', ''),
                'ad_creative_link_title': ad_data.get('ad_creative_link_title', ''),
                'ad_creative_link_caption': ad_data.get('ad_creative_link_caption', ''),
                'ad_delivery_start_time': ad_data.get('ad_delivery_start_time'),
                'ad_delivery_stop_time': ad_data.get('ad_delivery_stop_time'),
                'page_name': ad_data.get('page_name', ''),
                'impressions': ad_data.get('impressions', {}),
                'spend': ad_data.get('spend', {}),
                'video_url': self._extract_video_url(ad_data),
                'thumbnail_url': ad_data.get('ad_snapshot_url'),
                'languages': ad_data.get('languages', []),
                'publisher_platforms': ad_data.get('publisher_platforms', []),
                'raw_data': ad_data
            }
        except Exception as e:
            logger.error(f"Failed to parse ad data: {e}")
            return None

    def _extract_video_url(self, ad: Dict) -> Optional[str]:
        """
        Extract video URL from ad data.

        Args:
            ad: Ad data dictionary

        Returns:
            Video URL if found
        """
        try:
            # Check for video in ad_snapshot_url
            if 'ad_snapshot_url' in ad:
                # This would need additional parsing of the snapshot page
                pass

            # Check in ad creative data
            if 'ad_creatives' in ad:
                for creative in ad['ad_creatives']:
                    if 'video_url' in creative:
                        return creative['video_url']

            # Check raw data
            raw = ad.get('raw_data', {})
            if 'video_url' in raw:
                return raw['video_url']

            return None

        except Exception as e:
            logger.debug(f"Could not extract video URL: {e}")
            return None

    def _parse_impressions(self, impressions: Any) -> Dict[str, int]:
        """
        Parse impressions data into standardized format.

        Args:
            impressions: Impressions data (string range or dict)

        Returns:
            Dictionary with min, max, avg impressions
        """
        try:
            if isinstance(impressions, str):
                # Parse ranges like "10000-50000"
                if '-' in impressions:
                    parts = impressions.split('-')
                    min_imp = int(parts[0].replace(',', ''))
                    max_imp = int(parts[1].replace(',', ''))
                    return {
                        'min': min_imp,
                        'max': max_imp,
                        'avg': (min_imp + max_imp) // 2
                    }
                else:
                    # Single number
                    num = int(impressions.replace(',', ''))
                    return {'min': num, 'max': num, 'avg': num}

            elif isinstance(impressions, dict):
                return {
                    'min': impressions.get('lower_bound', 0),
                    'max': impressions.get('upper_bound', 0),
                    'avg': (impressions.get('lower_bound', 0) + impressions.get('upper_bound', 0)) // 2
                }

            return {'min': 0, 'max': 0, 'avg': 0}

        except Exception as e:
            logger.debug(f"Failed to parse impressions: {e}")
            return {'min': 0, 'max': 0, 'avg': 0}

    def _parse_spend(self, spend: Any) -> Dict[str, float]:
        """
        Parse spend data into standardized format.

        Args:
            spend: Spend data (string range or dict)

        Returns:
            Dictionary with min, max, avg spend
        """
        try:
            if isinstance(spend, str):
                # Parse ranges like "$100-$500"
                spend = spend.replace('$', '').replace(',', '')
                if '-' in spend:
                    parts = spend.split('-')
                    min_spend = float(parts[0])
                    max_spend = float(parts[1])
                    return {
                        'min': min_spend,
                        'max': max_spend,
                        'avg': (min_spend + max_spend) / 2
                    }
                else:
                    num = float(spend)
                    return {'min': num, 'max': num, 'avg': num}

            elif isinstance(spend, dict):
                return {
                    'min': float(spend.get('lower_bound', 0)),
                    'max': float(spend.get('upper_bound', 0)),
                    'avg': (float(spend.get('lower_bound', 0)) + float(spend.get('upper_bound', 0))) / 2
                }

            return {'min': 0.0, 'max': 0.0, 'avg': 0.0}

        except Exception as e:
            logger.debug(f"Failed to parse spend: {e}")
            return {'min': 0.0, 'max': 0.0, 'avg': 0.0}

    def _analyze_copy_patterns(self, ads: List[Dict]) -> Dict[str, Any]:
        """
        Analyze copy patterns in ad text.

        Args:
            ads: List of ads to analyze

        Returns:
            Dictionary with pattern counts and percentages
        """
        try:
            total = len(ads)
            if total == 0:
                return {}

            patterns = {
                'question': 0,
                'number': 0,
                'transformation': 0,
                'urgency': 0,
                'social_proof': 0,
                'negative_hooks': 0
            }

            # Keywords for each pattern
            urgency_words = ['now', 'today', 'limited', 'hurry', 'fast', 'quick', 'instant', 'immediately']
            transformation_words = ['transform', 'change', 'improve', 'boost', 'increase', 'grow', 'become']
            social_proof_words = ['proven', 'trusted', 'verified', 'recommended', 'popular', 'best-selling']
            negative_words = ['stop', 'avoid', 'never', 'quit', 'prevent', 'eliminate', 'lose', 'without']

            for ad in ads:
                body = ad.get('ad_creative_body', '').lower()
                title = ad.get('ad_creative_link_title', '').lower()
                text = f"{body} {title}"

                # Question hooks
                if '?' in text:
                    patterns['question'] += 1

                # Number hooks (contains digits)
                if re.search(r'\d+', text):
                    patterns['number'] += 1

                # Transformation hooks
                if any(word in text for word in transformation_words):
                    patterns['transformation'] += 1

                # Urgency hooks
                if any(word in text for word in urgency_words):
                    patterns['urgency'] += 1

                # Social proof hooks
                if any(word in text for word in social_proof_words):
                    patterns['social_proof'] += 1

                # Negative hooks
                if any(word in text for word in negative_words):
                    patterns['negative_hooks'] += 1

            # Convert to percentages
            return {
                'question': {
                    'count': patterns['question'],
                    'percentage': round(patterns['question'] / total * 100, 1)
                },
                'number': {
                    'count': patterns['number'],
                    'percentage': round(patterns['number'] / total * 100, 1)
                },
                'transformation': {
                    'count': patterns['transformation'],
                    'percentage': round(patterns['transformation'] / total * 100, 1)
                },
                'urgency': {
                    'count': patterns['urgency'],
                    'percentage': round(patterns['urgency'] / total * 100, 1)
                },
                'social_proof': {
                    'count': patterns['social_proof'],
                    'percentage': round(patterns['social_proof'] / total * 100, 1)
                },
                'negative_hooks': {
                    'count': patterns['negative_hooks'],
                    'percentage': round(patterns['negative_hooks'] / total * 100, 1)
                }
            }

        except Exception as e:
            logger.error(f"Failed to analyze copy patterns: {e}")
            return {}

    def _analyze_timing_patterns(self, ads: List[Dict]) -> Dict[str, Any]:
        """
        Analyze timing patterns (best launch days/times).

        Args:
            ads: List of ads to analyze

        Returns:
            Dictionary with timing insights
        """
        try:
            day_counter = Counter()
            month_counter = Counter()

            for ad in ads:
                start_time = ad.get('ad_delivery_start_time')
                if start_time:
                    try:
                        # Parse ISO format: 2023-01-15T10:30:00+0000
                        dt = datetime.fromisoformat(start_time.replace('+0000', '+00:00'))
                        day_name = dt.strftime('%A')
                        month_name = dt.strftime('%B')

                        day_counter[day_name] += 1
                        month_counter[month_name] += 1

                    except Exception as e:
                        logger.debug(f"Failed to parse date: {start_time}, {e}")
                        continue

            total = sum(day_counter.values())

            return {
                'best_launch_days': [
                    {
                        'day': day,
                        'count': count,
                        'percentage': round(count / total * 100, 1) if total > 0 else 0
                    }
                    for day, count in day_counter.most_common(3)
                ],
                'best_launch_months': [
                    {
                        'month': month,
                        'count': count,
                        'percentage': round(count / total * 100, 1) if total > 0 else 0
                    }
                    for month, count in month_counter.most_common(3)
                ]
            }

        except Exception as e:
            logger.error(f"Failed to analyze timing patterns: {e}")
            return {}

    def _analyze_spend(self, ads: List[Dict]) -> Dict[str, float]:
        """
        Analyze spend patterns across ads.

        Args:
            ads: List of ads to analyze

        Returns:
            Dictionary with spend statistics
        """
        try:
            spend_values = []

            for ad in ads:
                spend = ad.get('spend', {})
                parsed = self._parse_spend(spend)
                if parsed['avg'] > 0:
                    spend_values.append(parsed['avg'])

            if not spend_values:
                return {'avg': 0.0, 'max': 0.0, 'min': 0.0, 'total': 0.0}

            return {
                'avg': round(sum(spend_values) / len(spend_values), 2),
                'max': round(max(spend_values), 2),
                'min': round(min(spend_values), 2),
                'total': round(sum(spend_values), 2)
            }

        except Exception as e:
            logger.error(f"Failed to analyze spend: {e}")
            return {'avg': 0.0, 'max': 0.0, 'min': 0.0, 'total': 0.0}

    def _get_min_impressions(self, ad: Dict) -> int:
        """Get minimum impressions from ad data."""
        impressions = ad.get('impressions', {})
        parsed = self._parse_impressions(impressions)
        return parsed.get('min', 0)

    def _analyze_date_range(self, ads: List[Dict]) -> Dict[str, str]:
        """Analyze date range of ads."""
        try:
            dates = []
            for ad in ads:
                start = ad.get('ad_delivery_start_time')
                if start:
                    try:
                        dt = datetime.fromisoformat(start.replace('+0000', '+00:00'))
                        dates.append(dt)
                    except:
                        continue

            if dates:
                return {
                    'earliest': min(dates).isoformat(),
                    'latest': max(dates).isoformat()
                }

            return {'earliest': 'N/A', 'latest': 'N/A'}

        except Exception as e:
            logger.error(f"Failed to analyze date range: {e}")
            return {'earliest': 'N/A', 'latest': 'N/A'}

    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure."""
        return {
            'total_ads_analyzed': 0,
            'date_range': {'earliest': 'N/A', 'latest': 'N/A'},
            'copy_patterns': {},
            'timing_patterns': {},
            'spend_analysis': {'avg': 0.0, 'max': 0.0, 'min': 0.0, 'total': 0.0},
            'top_ads': [],
            'analyzed_at': datetime.utcnow().isoformat()
        }


# Singleton instance
meta_ads_library = RealMetaAdsLibrary()
