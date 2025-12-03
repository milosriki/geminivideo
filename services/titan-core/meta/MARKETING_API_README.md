# Meta Marketing API v19.0 Integration

**Agent 7/30 - ULTIMATE Production Plan**

Production-grade Meta Ads Manager client with full error handling, retry logic, and rate limiting.

## Features

✅ **Real Meta Marketing API v19.0** - No mock data, production-ready
✅ **Full Campaign Management** - Create, update, pause, activate, delete
✅ **Ad Set Management** - Advanced targeting and optimization
✅ **Creative Management** - Video & image uploads
✅ **Insights & Reporting** - Comprehensive performance metrics
✅ **Budget Management** - Dynamic budget updates
✅ **Error Handling** - Exponential backoff retry logic
✅ **Rate Limiting** - Automatic rate limit detection and retry
✅ **Type Safety** - Full type hints and validation
✅ **Logging** - Detailed logging for all operations

## Installation

```bash
# Install Meta Business SDK
pip install facebook-business

# Already included in requirements.txt
```

## Quick Start

### 1. Get Meta Credentials

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a new app or use existing one
3. Add "Marketing API" product
4. Generate access token with `ads_management` permission
5. Get your Ad Account ID from [Meta Ads Manager](https://business.facebook.com/adsmanager)

### 2. Initialize Client

```python
from meta import RealMetaAdsManager, CampaignObjective

# Initialize with credentials
manager = RealMetaAdsManager(
    access_token='YOUR_ACCESS_TOKEN',
    ad_account_id='123456789',  # With or without 'act_' prefix
    app_secret='YOUR_APP_SECRET',  # Optional but recommended
    app_id='YOUR_APP_ID'  # Optional
)

# Health check
health = manager.health_check()
print(health)
```

### 3. Create Campaign

```python
campaign_id = manager.create_campaign(
    name="Summer Campaign 2024",
    objective=CampaignObjective.OUTCOME_TRAFFIC,
    daily_budget_cents=5000,  # $50/day
    status="PAUSED"
)
```

### 4. Create Ad Set with Targeting

```python
# Build targeting
targeting = manager.build_targeting(
    countries=['US', 'CA'],
    age_min=25,
    age_max=45,
    interests=[
        {'id': '6003139266461', 'name': 'Video games'}
    ]
)

# Create ad set
ad_set_id = manager.create_ad_set(
    campaign_id=campaign_id,
    name="US/CA Gamers 25-45",
    daily_budget_cents=2000,
    targeting=targeting,
    optimization_goal='LINK_CLICKS'
)
```

### 5. Upload Video & Create Ad

```python
# Upload video
video_id = manager.upload_video(
    video_path='/path/to/video.mp4',
    title='Product Demo'
)

# Create creative
creative_id = manager.create_ad_creative(
    name='Demo Creative',
    video_id=video_id,
    message='Check out our product!',
    link='https://example.com',
    call_to_action_type='SHOP_NOW'
)

# Create ad
ad_id = manager.create_ad(
    ad_set_id=ad_set_id,
    creative_id=creative_id,
    name='Product Ad'
)
```

### 6. Get Performance Insights

```python
# Campaign insights
insights = manager.get_campaign_insights(
    campaign_id=campaign_id,
    fields=['impressions', 'clicks', 'spend', 'ctr'],
    date_preset='last_7d'
)

for insight in insights:
    print(f"Impressions: {insight['impressions']}")
    print(f"Clicks: {insight['clicks']}")
    print(f"Spend: ${insight['spend']}")
```

## API Reference

### Campaign Management

#### `create_campaign()`
```python
campaign_id = manager.create_campaign(
    name: str,
    objective: CampaignObjective,
    daily_budget_cents: int = None,
    lifetime_budget_cents: int = None,
    status: str = "PAUSED",
    special_ad_categories: List[str] = None
) -> str
```

**Campaign Objectives:**
- `OUTCOME_TRAFFIC` - Drive traffic to website/app
- `OUTCOME_ENGAGEMENT` - Increase engagement
- `OUTCOME_LEADS` - Generate leads
- `OUTCOME_SALES` - Drive sales
- `OUTCOME_APP_PROMOTION` - Promote app installs
- `OUTCOME_AWARENESS` - Build brand awareness

#### `get_campaign(campaign_id: str)`
Get campaign details including status, budget, dates.

#### `update_campaign(campaign_id: str, **updates)`
Update any campaign field (name, budget, status, etc.)

#### `pause_campaign(campaign_id: str)`
Pause active campaign.

#### `activate_campaign(campaign_id: str)`
Activate paused campaign.

#### `delete_campaign(campaign_id: str)`
Permanently delete campaign.

### Ad Set Management

#### `create_ad_set()`
```python
ad_set_id = manager.create_ad_set(
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
) -> str
```

**Optimization Goals:**
- `IMPRESSIONS` - Maximize impressions
- `LINK_CLICKS` - Maximize link clicks
- `LANDING_PAGE_VIEWS` - Maximize landing page views
- `REACH` - Maximize reach
- `VIDEO_VIEWS` - Maximize video views
- `THRUPLAY` - Maximize video ThruPlays

**Billing Events:**
- `IMPRESSIONS` - Billed per impression
- `LINK_CLICKS` - Billed per link click
- `THRUPLAY` - Billed per ThruPlay

#### `update_ad_set(ad_set_id: str, **updates)`
Update ad set fields.

#### `get_ad_set(ad_set_id: str)`
Get ad set details.

### Creative & Ad Management

#### `upload_video(video_path: str, title: str = None)`
Upload video file, returns video_id.

#### `upload_image(image_path: str)`
Upload image file, returns image_hash.

#### `create_ad_creative()`
```python
creative_id = manager.create_ad_creative(
    name: str,
    video_id: str = None,
    image_hash: str = None,
    message: str = "",
    link: str = "",
    call_to_action_type: str = "LEARN_MORE",
    page_id: str = None
) -> str
```

**Call-to-Action Types:**
- `LEARN_MORE` - Learn More button
- `SHOP_NOW` - Shop Now button
- `SIGN_UP` - Sign Up button
- `DOWNLOAD` - Download button
- `WATCH_MORE` - Watch More button
- `APPLY_NOW` - Apply Now button

#### `create_ad()`
```python
ad_id = manager.create_ad(
    ad_set_id: str,
    creative_id: str,
    name: str,
    status: str = "PAUSED"
) -> str
```

### Insights & Reporting

#### `get_campaign_insights()`
```python
insights = manager.get_campaign_insights(
    campaign_id: str,
    fields: List[str] = None,
    date_preset: str = "last_7d",
    breakdowns: List[str] = None,
    time_range: Dict[str, str] = None
) -> List[Dict[str, Any]]
```

**Available Fields:**
- `impressions` - Total impressions
- `clicks` - Total clicks
- `spend` - Total spend
- `reach` - Unique reach
- `frequency` - Average frequency
- `cpm` - Cost per 1000 impressions
- `cpc` - Cost per click
- `ctr` - Click-through rate
- `video_views` - Video views
- `video_view_time` - Total video watch time
- `actions` - All actions (likes, comments, shares)
- `conversions` - Conversion events

**Date Presets:**
- `today` - Today
- `yesterday` - Yesterday
- `last_7d` - Last 7 days
- `last_14d` - Last 14 days
- `last_30d` - Last 30 days
- `last_90d` - Last 90 days
- `lifetime` - All time

**Breakdowns:**
- `age` - By age group
- `gender` - By gender
- `country` - By country
- `region` - By region
- `placement` - By placement
- `device_platform` - By device

#### `get_ad_insights(ad_id: str, fields: List[str] = None)`
Get individual ad performance.

#### `get_account_insights(date_preset: str = "last_30d")`
Get account-level overview.

### Budget Management

#### `update_budget(campaign_id: str, daily_budget_cents: int)`
Update campaign daily budget.

#### `get_spend(campaign_id: str, date_range: tuple = None)`
Get total spend for campaign.

### Targeting Helpers

#### `build_targeting()`
```python
targeting = manager.build_targeting(
    countries: List[str] = None,
    age_min: int = 18,
    age_max: int = 65,
    genders: List[int] = None,  # 1=male, 2=female
    interests: List[Dict] = None,
    custom_audiences: List[str] = None,
    excluded_audiences: List[str] = None,
    lookalike_audiences: List[str] = None,
    geo_locations: Dict[str, Any] = None,
    locales: List[int] = None,
    device_platforms: List[str] = None,
    publisher_platforms: List[str] = None,
    facebook_positions: List[str] = None
) -> Dict[str, Any]
```

**Examples:**

Basic country targeting:
```python
targeting = manager.build_targeting(
    countries=['US', 'CA', 'GB'],
    age_min=25,
    age_max=45
)
```

Interest-based targeting:
```python
targeting = manager.build_targeting(
    countries=['US'],
    interests=[
        {'id': '6003139266461', 'name': 'Video games'},
        {'id': '6003107902433', 'name': 'Technology'}
    ]
)
```

Custom audience targeting:
```python
targeting = manager.build_targeting(
    countries=['US'],
    lookalike_audiences=['123456789'],
    excluded_audiences=['987654321']
)
```

## Error Handling

The client includes comprehensive error handling:

### Retry Logic
- Automatic retry with exponential backoff
- Configurable max retries and delays
- Handles transient errors automatically

```python
from meta import RetryConfig

custom_retry = RetryConfig(
    max_retries=5,
    base_delay=2.0,
    max_delay=120.0,
    exponential_base=2.5
)

manager = RealMetaAdsManager(
    access_token=token,
    ad_account_id=account_id,
    retry_config=custom_retry
)
```

### Rate Limiting
- Automatic detection of rate limit errors (codes 17, 613, 80004)
- Exponential backoff before retry
- Raises `MetaRateLimitError` after max retries

### Exception Types

```python
from meta import MetaAPIError, MetaRateLimitError

try:
    campaign_id = manager.create_campaign(...)
except MetaRateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Wait before retry
except MetaAPIError as e:
    print(f"API error: {e}")
    # Handle other API errors
```

## Logging

All operations are logged with Python's logging module:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or configure specific logger
logger = logging.getLogger('meta.marketing_api')
logger.setLevel(logging.INFO)
```

**Log Examples:**
```
INFO:meta.marketing_api:Meta Ads API initialized for account act_123456789
INFO:meta.marketing_api:Creating campaign: Summer Campaign with objective OUTCOME_TRAFFIC
INFO:meta.marketing_api:Campaign created: 120210000000001
WARNING:meta.marketing_api:Rate limit hit (code 17), attempt 1/3
INFO:meta.marketing_api:Waiting 2.0s before retry...
```

## Best Practices

### 1. Always Start with Paused Status
```python
# Create everything paused for review
campaign_id = manager.create_campaign(..., status='PAUSED')
ad_set_id = manager.create_ad_set(..., status='PAUSED')
ad_id = manager.create_ad(..., status='PAUSED')

# Review everything, then activate
manager.activate_campaign(campaign_id)
```

### 2. Use Health Checks
```python
health = manager.health_check()
if health['status'] != 'healthy':
    raise Exception(f"API unhealthy: {health['error']}")
```

### 3. Monitor Spend Regularly
```python
spend = manager.get_spend(campaign_id)
if spend > MAX_BUDGET:
    manager.pause_campaign(campaign_id)
```

### 4. Handle Rate Limits
```python
try:
    insights = manager.get_campaign_insights(campaign_id)
except MetaRateLimitError:
    # Wait and retry later
    time.sleep(60)
```

### 5. Use Breakdowns for Deep Insights
```python
insights = manager.get_campaign_insights(
    campaign_id,
    breakdowns=['age', 'gender', 'placement']
)
```

## Environment Variables

Set these in `.env` file:

```bash
META_ACCESS_TOKEN=your_access_token_here
META_AD_ACCOUNT_ID=123456789
META_APP_SECRET=your_app_secret
META_APP_ID=your_app_id
```

## Complete Example

See `marketing_api_example.py` for comprehensive usage examples including:

- Complete campaign workflow
- Video and image ad creation
- Advanced targeting strategies
- Performance monitoring
- Budget management
- Error handling patterns

## API Version

Current implementation uses **Meta Marketing API v19.0** (latest as of 2024).

## Resources

- [Meta Marketing API Documentation](https://developers.facebook.com/docs/marketing-apis)
- [Facebook Business SDK Python](https://github.com/facebook/facebook-python-business-sdk)
- [Ad Account Structure](https://developers.facebook.com/docs/marketing-api/reference/ad-account)
- [Campaign Objectives](https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group#objectives)

## Support

For issues or questions:
1. Check Meta API documentation
2. Review example file: `marketing_api_example.py`
3. Enable debug logging for detailed error info
4. Check Meta Developer Console for API status

## License

Production code for Titan Core - ULTIMATE 30-Agent Plan
