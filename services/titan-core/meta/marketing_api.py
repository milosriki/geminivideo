"""
Real Meta Marketing API v19.0 Integration
Production-grade client for Meta Ads Manager with full error handling and retry logic.
"""

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.advideo import AdVideo
from facebook_business.adobjects.adimage import AdImage
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.exceptions import FacebookRequestError
import os
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CampaignObjective(Enum):
    """Campaign objectives for Meta Ads API v19.0"""
    OUTCOME_TRAFFIC = "OUTCOME_TRAFFIC"
    OUTCOME_ENGAGEMENT = "OUTCOME_ENGAGEMENT"
    OUTCOME_LEADS = "OUTCOME_LEADS"
    OUTCOME_SALES = "OUTCOME_SALES"
    OUTCOME_APP_PROMOTION = "OUTCOME_APP_PROMOTION"
    OUTCOME_AWARENESS = "OUTCOME_AWARENESS"


class OptimizationGoal(Enum):
    """Ad Set optimization goals"""
    IMPRESSIONS = "IMPRESSIONS"
    LINK_CLICKS = "LINK_CLICKS"
    LANDING_PAGE_VIEWS = "LANDING_PAGE_VIEWS"
    OFFSITE_CONVERSIONS = "OFFSITE_CONVERSIONS"
    REACH = "REACH"
    THRUPLAY = "THRUPLAY"
    VIDEO_VIEWS = "VIDEO_VIEWS"
    ENGAGEMENT = "ENGAGEMENT"


class BillingEvent(Enum):
    """Billing event types"""
    IMPRESSIONS = "IMPRESSIONS"
    LINK_CLICKS = "LINK_CLICKS"
    THRUPLAY = "THRUPLAY"


class MetaAPIError(Exception):
    """Custom exception for Meta API errors"""
    pass


class MetaRateLimitError(MetaAPIError):
    """Rate limit exceeded exception"""
    pass


@dataclass
class RetryConfig:
    """Retry configuration for API calls"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0


class RealMetaAdsManager:
    """Production Meta Marketing API v19.0 client with full error handling and retry logic."""

    def __init__(
        self,
        access_token: str,
        ad_account_id: str,
        app_secret: str = None,
        app_id: str = None,
        retry_config: RetryConfig = None
    ):
        """
        Initialize with real Meta credentials.

        Args:
            access_token: Meta access token with ads_management permission
            ad_account_id: Ad account ID (with or without 'act_' prefix)
            app_secret: Optional app secret for enhanced security
            app_id: Optional app ID
            retry_config: Optional retry configuration
        """
        self.access_token = access_token
        self.ad_account_id = ad_account_id if ad_account_id.startswith('act_') else f'act_{ad_account_id}'
        self.app_secret = app_secret
        self.app_id = app_id
        self.retry_config = retry_config or RetryConfig()

        # Initialize Facebook Ads API
        try:
            FacebookAdsApi.init(
                access_token=access_token,
                app_secret=app_secret,
                app_id=app_id
            )
            self.api = FacebookAdsApi.get_default_api()
            logger.info(f"Meta Ads API initialized for account {self.ad_account_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Meta Ads API: {e}")
            raise MetaAPIError(f"API initialization failed: {e}")

        # Get ad account object
        self.ad_account = AdAccount(self.ad_account_id)
        self._verify_account_access()

    def _verify_account_access(self) -> None:
        """Verify account access and permissions."""
        try:
            account_info = self.ad_account.api_get(fields=['id', 'name', 'account_status'])
            logger.info(f"Connected to account: {account_info.get('name')} (Status: {account_info.get('account_status')})")
        except FacebookRequestError as e:
            logger.error(f"Account access verification failed: {e}")
            raise MetaAPIError(f"Cannot access account {self.ad_account_id}: {e}")

    def _retry_on_error(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry logic.

        Args:
            func: Function to execute
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            MetaAPIError: If all retries exhausted
        """
        last_exception = None

        for attempt in range(self.retry_config.max_retries):
            try:
                return func(*args, **kwargs)
            except FacebookRequestError as e:
                last_exception = e
                error_code = e.api_error_code()
                error_message = e.api_error_message()

                # Check for rate limiting (error code 17 or 613)
                if error_code in [17, 613, 80004]:
                    logger.warning(f"Rate limit hit (code {error_code}), attempt {attempt + 1}/{self.retry_config.max_retries}")
                    if attempt < self.retry_config.max_retries - 1:
                        delay = min(
                            self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt),
                            self.retry_config.max_delay
                        )
                        logger.info(f"Waiting {delay}s before retry...")
                        time.sleep(delay)
                        continue
                    raise MetaRateLimitError(f"Rate limit exceeded: {error_message}")

                # Check for transient errors
                if error_code in [1, 2, 190, 200]:
                    logger.warning(f"Transient error (code {error_code}): {error_message}, attempt {attempt + 1}/{self.retry_config.max_retries}")
                    if attempt < self.retry_config.max_retries - 1:
                        delay = min(
                            self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt),
                            self.retry_config.max_delay
                        )
                        time.sleep(delay)
                        continue

                # Non-retryable error
                logger.error(f"API error (code {error_code}): {error_message}")
                raise MetaAPIError(f"API error {error_code}: {error_message}")
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error in API call: {e}")
                if attempt < self.retry_config.max_retries - 1:
                    delay = self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt)
                    time.sleep(delay)
                    continue
                raise MetaAPIError(f"Unexpected error: {e}")

        raise MetaAPIError(f"Max retries ({self.retry_config.max_retries}) exceeded: {last_exception}")

    # ==================== Campaign Management ====================

    def create_campaign(
        self,
        name: str,
        objective: CampaignObjective,
        daily_budget_cents: int = None,
        lifetime_budget_cents: int = None,
        status: str = "PAUSED",
        special_ad_categories: List[str] = None
    ) -> str:
        """
        Create a new campaign.

        Args:
            name: Campaign name
            objective: Campaign objective from CampaignObjective enum
            daily_budget_cents: Daily budget in cents (mutually exclusive with lifetime_budget)
            lifetime_budget_cents: Lifetime budget in cents
            status: Campaign status (PAUSED, ACTIVE)
            special_ad_categories: List of special ad categories (e.g., ['CREDIT', 'EMPLOYMENT'])

        Returns:
            Campaign ID
        """
        logger.info(f"Creating campaign: {name} with objective {objective.value}")

        params = {
            'name': name,
            'objective': objective.value,
            'status': status,
        }

        if daily_budget_cents:
            params['daily_budget'] = daily_budget_cents
        elif lifetime_budget_cents:
            params['lifetime_budget'] = lifetime_budget_cents
        else:
            raise ValueError("Either daily_budget_cents or lifetime_budget_cents must be provided")

        if special_ad_categories:
            params['special_ad_categories'] = special_ad_categories

        def _create():
            campaign = self.ad_account.create_campaign(params=params)
            return campaign['id']

        campaign_id = self._retry_on_error(_create)
        logger.info(f"Campaign created: {campaign_id}")
        return campaign_id

    def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get campaign details.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign data dictionary
        """
        logger.info(f"Fetching campaign: {campaign_id}")

        fields = [
            'id', 'name', 'objective', 'status', 'daily_budget', 'lifetime_budget',
            'created_time', 'updated_time', 'special_ad_categories', 'start_time',
            'stop_time', 'effective_status'
        ]

        def _get():
            campaign = Campaign(campaign_id)
            return campaign.api_get(fields=fields)

        data = self._retry_on_error(_get)
        logger.info(f"Campaign fetched: {data.get('name')}")
        return dict(data)

    def update_campaign(self, campaign_id: str, **updates) -> bool:
        """
        Update campaign fields.

        Args:
            campaign_id: Campaign ID
            **updates: Fields to update (e.g., name="New Name", daily_budget=10000)

        Returns:
            True if successful
        """
        logger.info(f"Updating campaign {campaign_id}: {updates}")

        def _update():
            campaign = Campaign(campaign_id)
            campaign.api_update(params=updates)
            return True

        result = self._retry_on_error(_update)
        logger.info(f"Campaign {campaign_id} updated successfully")
        return result

    def pause_campaign(self, campaign_id: str) -> bool:
        """Pause a campaign."""
        return self.update_campaign(campaign_id, status='PAUSED')

    def activate_campaign(self, campaign_id: str) -> bool:
        """Activate a campaign."""
        return self.update_campaign(campaign_id, status='ACTIVE')

    def delete_campaign(self, campaign_id: str) -> bool:
        """
        Delete a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            True if successful
        """
        logger.info(f"Deleting campaign: {campaign_id}")

        def _delete():
            campaign = Campaign(campaign_id)
            campaign.api_delete()
            return True

        result = self._retry_on_error(_delete)
        logger.info(f"Campaign {campaign_id} deleted")
        return result

    # ==================== Ad Set Management ====================

    def create_ad_set(
        self,
        campaign_id: str,
        name: str,
        daily_budget_cents: int,
        targeting: Dict[str, Any],
        optimization_goal: str,
        billing_event: str = "IMPRESSIONS",
        bid_strategy: str = "LOWEST_COST_WITHOUT_CAP",
        start_time: str = None,
        end_time: str = None,
        status: str = "PAUSED"
    ) -> str:
        """
        Create an ad set with targeting.

        Args:
            campaign_id: Parent campaign ID
            name: Ad set name
            daily_budget_cents: Daily budget in cents
            targeting: Targeting specification dictionary
            optimization_goal: Optimization goal (e.g., 'LINK_CLICKS', 'IMPRESSIONS')
            billing_event: Billing event type
            bid_strategy: Bid strategy
            start_time: Start time (ISO 8601 format or Unix timestamp)
            end_time: End time (ISO 8601 format or Unix timestamp)
            status: Ad set status

        Returns:
            Ad set ID
        """
        logger.info(f"Creating ad set: {name} in campaign {campaign_id}")

        params = {
            'name': name,
            'campaign_id': campaign_id,
            'daily_budget': daily_budget_cents,
            'targeting': targeting,
            'optimization_goal': optimization_goal,
            'billing_event': billing_event,
            'bid_strategy': bid_strategy,
            'status': status,
        }

        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time

        def _create():
            ad_set = self.ad_account.create_ad_set(params=params)
            return ad_set['id']

        ad_set_id = self._retry_on_error(_create)
        logger.info(f"Ad set created: {ad_set_id}")
        return ad_set_id

    def update_ad_set(self, ad_set_id: str, **updates) -> bool:
        """
        Update ad set fields.

        Args:
            ad_set_id: Ad set ID
            **updates: Fields to update

        Returns:
            True if successful
        """
        logger.info(f"Updating ad set {ad_set_id}: {updates}")

        def _update():
            ad_set = AdSet(ad_set_id)
            ad_set.api_update(params=updates)
            return True

        result = self._retry_on_error(_update)
        logger.info(f"Ad set {ad_set_id} updated successfully")
        return result

    def get_ad_set(self, ad_set_id: str) -> Dict[str, Any]:
        """
        Get ad set details.

        Args:
            ad_set_id: Ad set ID

        Returns:
            Ad set data dictionary
        """
        logger.info(f"Fetching ad set: {ad_set_id}")

        fields = [
            'id', 'name', 'campaign_id', 'status', 'daily_budget', 'lifetime_budget',
            'targeting', 'optimization_goal', 'billing_event', 'bid_strategy',
            'start_time', 'end_time', 'created_time', 'updated_time', 'effective_status'
        ]

        def _get():
            ad_set = AdSet(ad_set_id)
            return ad_set.api_get(fields=fields)

        data = self._retry_on_error(_get)
        logger.info(f"Ad set fetched: {data.get('name')}")
        return dict(data)

    # ==================== Creative & Ad Management ====================

    def upload_video(self, video_path: str, title: str = None) -> str:
        """
        Upload video file to Meta.

        Args:
            video_path: Path to video file
            title: Video title (defaults to filename)

        Returns:
            Video ID
        """
        logger.info(f"Uploading video: {video_path}")

        if not os.path.exists(video_path):
            raise ValueError(f"Video file not found: {video_path}")

        if title is None:
            title = os.path.basename(video_path)

        def _upload():
            video = AdVideo(parent_id=self.ad_account_id)
            video[AdVideo.Field.filepath] = video_path
            video[AdVideo.Field.name] = title
            video.remote_create()
            return video['id']

        video_id = self._retry_on_error(_upload)
        logger.info(f"Video uploaded: {video_id}")
        return video_id

    def upload_image(self, image_path: str) -> str:
        """
        Upload image to Meta.

        Args:
            image_path: Path to image file

        Returns:
            Image hash
        """
        logger.info(f"Uploading image: {image_path}")

        if not os.path.exists(image_path):
            raise ValueError(f"Image file not found: {image_path}")

        def _upload():
            image = AdImage(parent_id=self.ad_account_id)
            image[AdImage.Field.filename] = image_path
            image.remote_create()
            return image['hash']

        image_hash = self._retry_on_error(_upload)
        logger.info(f"Image uploaded: {image_hash}")
        return image_hash

    def create_ad_creative(
        self,
        name: str,
        video_id: str = None,
        image_hash: str = None,
        message: str = "",
        link: str = "",
        call_to_action_type: str = "LEARN_MORE",
        page_id: str = None
    ) -> str:
        """
        Create ad creative.

        Args:
            name: Creative name
            video_id: Video ID (mutually exclusive with image_hash)
            image_hash: Image hash
            message: Ad text/message
            link: Destination URL
            call_to_action_type: CTA button type
            page_id: Facebook page ID (required for some placements)

        Returns:
            Creative ID
        """
        logger.info(f"Creating ad creative: {name}")

        object_story_spec = {}

        if page_id:
            object_story_spec['page_id'] = page_id

        if video_id:
            object_story_spec['video_data'] = {
                'video_id': video_id,
                'message': message,
            }
            if link:
                object_story_spec['video_data']['call_to_action'] = {
                    'type': call_to_action_type,
                    'value': {'link': link}
                }
        elif image_hash:
            object_story_spec['link_data'] = {
                'image_hash': image_hash,
                'message': message,
                'link': link,
                'call_to_action': {
                    'type': call_to_action_type,
                    'value': {'link': link}
                }
            }
        else:
            raise ValueError("Either video_id or image_hash must be provided")

        params = {
            'name': name,
            'object_story_spec': object_story_spec,
        }

        def _create():
            creative = self.ad_account.create_ad_creative(params=params)
            return creative['id']

        creative_id = self._retry_on_error(_create)
        logger.info(f"Ad creative created: {creative_id}")
        return creative_id

    def create_ad(
        self,
        ad_set_id: str,
        creative_id: str,
        name: str,
        status: str = "PAUSED"
    ) -> str:
        """
        Create ad in ad set.

        Args:
            ad_set_id: Parent ad set ID
            creative_id: Ad creative ID
            name: Ad name
            status: Ad status

        Returns:
            Ad ID
        """
        logger.info(f"Creating ad: {name} in ad set {ad_set_id}")

        params = {
            'name': name,
            'adset_id': ad_set_id,
            'creative': {'creative_id': creative_id},
            'status': status,
        }

        def _create():
            ad = self.ad_account.create_ad(params=params)
            return ad['id']

        ad_id = self._retry_on_error(_create)
        logger.info(f"Ad created: {ad_id}")
        return ad_id

    # ==================== Insights & Reporting ====================

    def get_campaign_insights(
        self,
        campaign_id: str,
        fields: List[str] = None,
        date_preset: str = "last_7d",
        breakdowns: List[str] = None,
        time_range: Dict[str, str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get campaign performance metrics.

        Args:
            campaign_id: Campaign ID
            fields: Metrics to retrieve (defaults to common metrics)
            date_preset: Date preset ('today', 'yesterday', 'last_7d', 'last_30d', etc.)
            breakdowns: Breakdowns list (e.g., ['age', 'gender'])
            time_range: Custom time range {'since': 'YYYY-MM-DD', 'until': 'YYYY-MM-DD'}

        Returns:
            List of insight dictionaries
        """
        logger.info(f"Fetching insights for campaign: {campaign_id}")

        if fields is None:
            fields = [
                'impressions', 'clicks', 'spend', 'reach', 'frequency',
                'cpm', 'cpc', 'ctr', 'video_views', 'video_view_time'
            ]

        params = {'fields': fields}

        if time_range:
            params['time_range'] = time_range
        else:
            params['date_preset'] = date_preset

        if breakdowns:
            params['breakdowns'] = breakdowns

        def _get():
            campaign = Campaign(campaign_id)
            insights = campaign.get_insights(params=params)
            return [dict(insight) for insight in insights]

        data = self._retry_on_error(_get)
        logger.info(f"Campaign insights fetched: {len(data)} records")
        return data

    def get_ad_insights(
        self,
        ad_id: str,
        fields: List[str] = None,
        date_preset: str = "last_7d"
    ) -> Dict[str, Any]:
        """
        Get ad performance metrics.

        Args:
            ad_id: Ad ID
            fields: Metrics to retrieve
            date_preset: Date preset

        Returns:
            Insights dictionary
        """
        logger.info(f"Fetching insights for ad: {ad_id}")

        if fields is None:
            fields = [
                'impressions', 'clicks', 'spend', 'reach',
                'cpm', 'cpc', 'ctr', 'actions', 'conversions'
            ]

        params = {
            'fields': fields,
            'date_preset': date_preset,
        }

        def _get():
            ad = Ad(ad_id)
            insights = ad.get_insights(params=params)
            return dict(insights[0]) if insights else {}

        data = self._retry_on_error(_get)
        logger.info(f"Ad insights fetched")
        return data

    def get_account_insights(
        self,
        date_preset: str = "last_30d",
        fields: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get account-level insights.

        Args:
            date_preset: Date preset
            fields: Metrics to retrieve

        Returns:
            Account insights dictionary
        """
        logger.info(f"Fetching account insights")

        if fields is None:
            fields = [
                'impressions', 'clicks', 'spend', 'reach', 'frequency',
                'cpm', 'cpc', 'ctr', 'account_name'
            ]

        params = {
            'fields': fields,
            'date_preset': date_preset,
        }

        def _get():
            insights = self.ad_account.get_insights(params=params)
            return dict(insights[0]) if insights else {}

        data = self._retry_on_error(_get)
        logger.info(f"Account insights fetched")
        return data

    # ==================== Budget Management ====================

    def update_budget(self, campaign_id: str, daily_budget_cents: int) -> bool:
        """
        Update campaign daily budget.

        Args:
            campaign_id: Campaign ID
            daily_budget_cents: New daily budget in cents

        Returns:
            True if successful
        """
        return self.update_campaign(campaign_id, daily_budget=daily_budget_cents)

    def get_spend(
        self,
        campaign_id: str,
        date_range: Tuple[str, str] = None
    ) -> float:
        """
        Get campaign spend.

        Args:
            campaign_id: Campaign ID
            date_range: Optional tuple of (start_date, end_date) in 'YYYY-MM-DD' format

        Returns:
            Total spend amount
        """
        logger.info(f"Fetching spend for campaign: {campaign_id}")

        if date_range:
            time_range = {'since': date_range[0], 'until': date_range[1]}
            insights = self.get_campaign_insights(
                campaign_id,
                fields=['spend'],
                time_range=time_range
            )
        else:
            insights = self.get_campaign_insights(
                campaign_id,
                fields=['spend'],
                date_preset='lifetime'
            )

        total_spend = sum(float(insight.get('spend', 0)) for insight in insights)
        logger.info(f"Total spend: ${total_spend}")
        return total_spend

    # ==================== Targeting Helpers ====================

    def build_targeting(
        self,
        countries: List[str] = None,
        age_min: int = 18,
        age_max: int = 65,
        genders: List[int] = None,
        interests: List[Dict] = None,
        custom_audiences: List[str] = None,
        excluded_audiences: List[str] = None,
        lookalike_audiences: List[str] = None,
        geo_locations: Dict[str, Any] = None,
        locales: List[int] = None,
        device_platforms: List[str] = None,
        publisher_platforms: List[str] = None,
        facebook_positions: List[str] = None
    ) -> Dict[str, Any]:
        """
        Build targeting specification dictionary.

        Args:
            countries: List of country codes (e.g., ['US', 'CA'])
            age_min: Minimum age (18-65)
            age_max: Maximum age (18-65)
            genders: Gender list (1=male, 2=female)
            interests: List of interest dicts [{'id': '...', 'name': '...'}]
            custom_audiences: List of custom audience IDs
            excluded_audiences: List of audience IDs to exclude
            lookalike_audiences: List of lookalike audience IDs
            geo_locations: Custom geo locations dict
            locales: List of locale IDs
            device_platforms: Device platforms (e.g., ['mobile', 'desktop'])
            publisher_platforms: Publisher platforms (e.g., ['facebook', 'instagram'])
            facebook_positions: Facebook positions (e.g., ['feed', 'story'])

        Returns:
            Targeting specification dictionary
        """
        targeting = {
            'age_min': age_min,
            'age_max': age_max,
        }

        # Geo targeting
        if geo_locations:
            targeting['geo_locations'] = geo_locations
        elif countries:
            targeting['geo_locations'] = {'countries': countries}
        else:
            targeting['geo_locations'] = {'countries': ['US']}

        # Demographics
        if genders:
            targeting['genders'] = genders

        if locales:
            targeting['locales'] = locales

        # Interests
        if interests:
            targeting['flexible_spec'] = [{'interests': interests}]

        # Audiences
        if custom_audiences:
            targeting['custom_audiences'] = [{'id': aud_id} for aud_id in custom_audiences]

        if lookalike_audiences:
            if 'custom_audiences' not in targeting:
                targeting['custom_audiences'] = []
            targeting['custom_audiences'].extend([{'id': aud_id} for aud_id in lookalike_audiences])

        if excluded_audiences:
            targeting['excluded_custom_audiences'] = [{'id': aud_id} for aud_id in excluded_audiences]

        # Placements
        if device_platforms or publisher_platforms or facebook_positions:
            targeting['device_platforms'] = device_platforms or ['mobile', 'desktop']
            targeting['publisher_platforms'] = publisher_platforms or ['facebook', 'instagram']

            if facebook_positions:
                targeting['facebook_positions'] = facebook_positions

        logger.info(f"Built targeting spec: {json.dumps(targeting, indent=2)}")
        return targeting

    # ==================== Utility Methods ====================

    def get_api_version(self) -> str:
        """Get current API version."""
        return self.api.api_version

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on API connection.

        Returns:
            Health status dictionary
        """
        try:
            account_info = self.ad_account.api_get(fields=['id', 'name', 'account_status'])
            return {
                'status': 'healthy',
                'account_id': account_info.get('id'),
                'account_name': account_info.get('name'),
                'account_status': account_info.get('account_status'),
                'api_version': self.get_api_version()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
