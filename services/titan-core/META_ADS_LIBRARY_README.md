# Meta Ads Library Integration

Production-ready integration with Meta (Facebook) Ads Library API for discovering, analyzing, and learning from successful video ads.

## Overview

This integration provides three main components:

1. **RealMetaAdsLibrary** (`meta_ads_library.py`) - Core API integration
2. **AdPatternMiner** (`scripts/meta_ads_library_pattern_miner.py`) - Pattern analysis tool
3. **Usage Examples** (`meta_ads_library_example.py`) - Example implementations

## Setup

### 1. Install Dependencies

The Facebook Business SDK is already included in `requirements.txt`:

```bash
cd /home/user/geminivideo/services/titan-core
pip install -r requirements.txt
```

### 2. Get Meta API Credentials

To use the Meta Ads Library API, you need:

1. **Meta App ID** - Create at https://developers.facebook.com/apps/
2. **Meta App Secret** - Found in your app's basic settings
3. **Access Token** - Generate from the Graph API Explorer

#### Quick Setup Steps:

1. Go to https://developers.facebook.com/apps/
2. Click "Create App" → Choose "Business" type
3. Go to App Settings → Basic → Copy App ID and App Secret
4. Go to Tools → Graph API Explorer
5. Select your app from the dropdown
6. Add permissions: `ads_read`, `pages_read_engagement`
7. Click "Generate Access Token"
8. Copy the token (it starts with `EAA...`)

### 3. Configure Environment Variables

Add to your `.env` file:

```bash
# Meta Ads Library API
META_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxx
META_APP_ID=1234567890123456
META_APP_SECRET=abcdef1234567890abcdef1234567890
```

**Note:** These are already defined in `.env.example`. Copy and fill with your values:

```bash
cp .env.example .env
# Edit .env and add your Meta credentials
```

## Usage

### Basic Search

```python
from meta_ads_library import meta_ads_library

# Search for ads
ads = meta_ads_library.search_ads(
    search_terms="fitness workout",
    countries=['US', 'GB'],
    media_type='VIDEO',
    limit=50
)

print(f"Found {len(ads)} ads")
for ad in ads[:5]:
    print(f"- {ad['page_name']}: {ad['ad_creative_body'][:60]}...")
```

### Analyze Top Performers

```python
# Analyze patterns in high-performing ads
analysis = meta_ads_library.analyze_top_performers(
    niche_keywords="skincare beauty",
    min_impressions=10000,
    limit=100
)

# Access insights
print(f"Total ads analyzed: {analysis['total_ads_analyzed']}")
print(f"Copy patterns: {analysis['copy_patterns']}")
print(f"Best launch days: {analysis['timing_patterns']['best_launch_days']}")
print(f"Average spend: ${analysis['spend_analysis']['avg']}")
```

### Download Videos

```python
# Download video from ad
video_path = meta_ads_library.download_video(
    video_url="https://video.xx.fbcdn.net/...",
    output_path="/tmp/ad_video.mp4"
)
```

### Pattern Mining Script

Run the pattern miner to analyze ads and update config:

```bash
# Use real API (default)
python scripts/meta_ads_library_pattern_miner.py \
    --niche "e-commerce product" \
    --min-impressions 10000 \
    --limit 50

# Use mock data (for testing)
python scripts/meta_ads_library_pattern_miner.py --use-mock

# Custom search
python scripts/meta_ads_library_pattern_miner.py \
    --niche "fitness supplement" \
    --min-impressions 50000 \
    --limit 100
```

### Run Examples

```bash
python services/titan-core/meta_ads_library_example.py
```

## API Methods

### RealMetaAdsLibrary Class

#### `search_ads(search_terms, countries, media_type, limit)`

Search Meta Ads Library for ads matching criteria.

**Parameters:**
- `search_terms` (str): Keywords to search for
- `countries` (List[str]): Country codes (e.g., ['US', 'GB'])
- `media_type` (str): 'VIDEO', 'IMAGE', or 'ALL'
- `limit` (int): Maximum number of ads to return

**Returns:** List[Dict] - List of ad dictionaries

**Example:**
```python
ads = meta_ads_library.search_ads(
    search_terms="online course",
    countries=['US'],
    media_type='VIDEO',
    limit=20
)
```

#### `download_video(video_url, output_path)`

Download video from Meta ad.

**Parameters:**
- `video_url` (str): URL of the video
- `output_path` (str): Local path to save video

**Returns:** str - Path to downloaded file

**Example:**
```python
path = meta_ads_library.download_video(
    video_url="https://video.xx.fbcdn.net/...",
    output_path="/tmp/ad.mp4"
)
```

#### `analyze_top_performers(niche_keywords, min_impressions, limit)`

Analyze top-performing ads in a niche.

**Parameters:**
- `niche_keywords` (str): Keywords defining the niche
- `min_impressions` (int): Minimum impression threshold
- `limit` (int): Number of ads to analyze

**Returns:** Dict - Analysis results with patterns

**Example:**
```python
analysis = meta_ads_library.analyze_top_performers(
    niche_keywords="beauty skincare",
    min_impressions=25000,
    limit=50
)
```

## Analysis Output Structure

### analyze_top_performers() Returns:

```python
{
    'total_ads_analyzed': 42,
    'date_range': {
        'earliest': '2024-01-15T10:00:00+00:00',
        'latest': '2024-11-30T18:30:00+00:00'
    },
    'copy_patterns': {
        'question': {'count': 28, 'percentage': 66.7},
        'number': {'count': 35, 'percentage': 83.3},
        'transformation': {'count': 18, 'percentage': 42.9},
        'urgency': {'count': 22, 'percentage': 52.4},
        'social_proof': {'count': 15, 'percentage': 35.7},
        'negative_hooks': {'count': 12, 'percentage': 28.6}
    },
    'timing_patterns': {
        'best_launch_days': [
            {'day': 'Monday', 'count': 12, 'percentage': 28.6},
            {'day': 'Tuesday', 'count': 10, 'percentage': 23.8},
            {'day': 'Wednesday', 'count': 8, 'percentage': 19.0}
        ],
        'best_launch_months': [...]
    },
    'spend_analysis': {
        'avg': 1250.50,
        'max': 5000.00,
        'min': 100.00,
        'total': 52521.00
    },
    'top_ads': [...]  # Top 10 performing ads
}
```

## Pattern Analysis Features

The integration analyzes multiple ad patterns:

### 1. Copy Patterns
- **Question hooks**: Ads with questions (?)
- **Number hooks**: Ads with statistics/numbers
- **Transformation**: Before/after, improvement language
- **Urgency**: Limited time, act now language
- **Social proof**: Testimonials, popularity indicators
- **Negative hooks**: Problem/solution framing

### 2. Timing Patterns
- Best days to launch ads
- Best months for campaigns
- Seasonal trends

### 3. Spend Analysis
- Average ad spend
- Spend ranges (min/max)
- Total spend across analyzed ads

### 4. Visual Patterns (planned)
- Face detection in thumbnails
- Color analysis
- Text overlay detection

## Error Handling

The implementation gracefully handles errors:

```python
if not meta_ads_library.enabled:
    print("API not configured, using fallback")
    # Falls back to mock data
```

All methods include try/except blocks and return sensible defaults on failure.

## Rate Limits

Meta Ads Library API has rate limits:

- **Rate limit**: 200 calls per hour per app
- **Search limit**: 5000 ads per search (use pagination for more)

The implementation respects these limits. If you hit rate limits:

1. Wait 1 hour for the limit to reset
2. Reduce `limit` parameter in searches
3. Use more specific `search_terms` to reduce results

## Troubleshooting

### "Meta Ads Library not enabled"

**Problem:** API credentials not configured

**Solution:**
```bash
# Check environment variables
echo $META_ACCESS_TOKEN
echo $META_APP_ID
echo $META_APP_SECRET

# Reload .env file
source .env
```

### "Invalid access token"

**Problem:** Access token expired or invalid

**Solution:**
1. Go to Graph API Explorer: https://developers.facebook.com/tools/explorer/
2. Generate new access token
3. Update `META_ACCESS_TOKEN` in `.env`

### "Insufficient permissions"

**Problem:** Access token doesn't have required permissions

**Solution:**
1. In Graph API Explorer, click "Get Token" → "Get User Access Token"
2. Select permissions: `ads_read`, `pages_read_engagement`
3. Generate new token
4. Update `.env`

### No ads found

**Problem:** Search terms too specific or no matching ads

**Solution:**
- Use broader search terms
- Try different country codes
- Check if ads exist for your query on https://www.facebook.com/ads/library/

## Production Considerations

### 1. Token Management

Access tokens expire. For production:

- Use long-lived tokens (60 days)
- Implement token refresh logic
- Monitor token expiration

### 2. Caching

Implement caching to reduce API calls:

```python
import json
from pathlib import Path

# Cache search results
cache_file = Path('/tmp/meta_ads_cache.json')
if cache_file.exists():
    with open(cache_file, 'r') as f:
        ads = json.load(f)
else:
    ads = meta_ads_library.search_ads(...)
    with open(cache_file, 'w') as f:
        json.dump(ads, f)
```

### 3. Monitoring

Log API usage:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API calls are automatically logged
```

### 4. Database Integration

Store results in Supabase:

```python
from services.supabase_connector import supabase_connector

# Save analysis results
supabase_connector.save_campaign_insights(
    campaign_id='analysis_001',
    insights=analysis
)
```

## Integration with Existing System

### Update Hook Templates

The pattern miner automatically updates hook templates:

```bash
python scripts/meta_ads_library_pattern_miner.py
# Updates: shared/config/hooks/hook_templates.json
# Generates: logs/pattern_mining_report.json
```

### Use in Video Generation

```python
# In video generation pipeline
from meta_ads_library import meta_ads_library

# Get top performers for reference
analysis = meta_ads_library.analyze_top_performers(
    niche_keywords=user_niche,
    min_impressions=10000,
    limit=20
)

# Use patterns to inform video creation
copy_patterns = analysis['copy_patterns']
if copy_patterns['question']['percentage'] > 60:
    # Use question hooks
    hook_type = 'curiosity_gap'
```

## Advanced Usage

### Custom Pattern Analysis

```python
def analyze_emoji_usage(ads):
    """Custom analysis: emoji usage in ad copy"""
    import re
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        "]+", flags=re.UNICODE)

    emoji_count = 0
    for ad in ads:
        text = ad.get('ad_creative_body', '')
        if emoji_pattern.search(text):
            emoji_count += 1

    return {
        'ads_with_emojis': emoji_count,
        'percentage': emoji_count / len(ads) * 100 if ads else 0
    }

# Use with search results
ads = meta_ads_library.search_ads(...)
emoji_analysis = analyze_emoji_usage(ads)
```

### Competitor Analysis

```python
# Search for competitor ads
competitor_ads = meta_ads_library.search_ads(
    search_terms="competitor_brand_name",
    countries=['US'],
    media_type='VIDEO',
    limit=100
)

# Analyze their patterns
analysis = meta_ads_library.analyze_top_performers(
    niche_keywords="competitor_brand_name",
    min_impressions=5000,
    limit=100
)
```

## API Endpoints Used

This implementation uses the Meta Graph API v18.0:

- **Ad Archive Search**: `GET /ads_archive`
- **Ad Details**: `GET /{ad-id}`

Documentation: https://developers.facebook.com/docs/marketing-api/reference/ads-archive/

## Contributing

To extend the integration:

1. Add new analysis methods to `RealMetaAdsLibrary` class
2. Update pattern miner to use new data
3. Add examples to `meta_ads_library_example.py`
4. Update this README

## License

Part of the GeminiVideo project.

## Support

For issues or questions:
- Check Meta API documentation: https://developers.facebook.com/docs/
- Review error logs in the console output
- Ensure credentials are correctly configured
