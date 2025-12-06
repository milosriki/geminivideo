# INTEGRATIONS GUIDE

Complete integration documentation for all external services in the GeminiVideo platform.

---

## Table of Contents

1. [Meta Marketing API](#1-meta-marketing-api)
2. [Google Ads API](#2-google-ads-api)
3. [Runway Gen-3 Alpha](#3-runway-gen-3-alpha)
4. [ElevenLabs Voice API](#4-elevenlabs-voice-api)
5. [Database (PostgreSQL & Redis)](#5-database-postgresql--redis)
6. [Quick Reference](#6-quick-reference)

---

## 1. META MARKETING API

### Overview
The Meta Marketing API integration enables automated Facebook and Instagram ad campaign creation, management, and conversion tracking through the Facebook Business SDK.

### Authentication Setup

#### Step 1: Create a Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com)
2. Create a new app or select an existing one
3. Navigate to **Settings > Basic**
4. Note your `App ID` and `App Secret`

#### Step 2: Generate Access Token

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer)
2. Select your app
3. Request these permissions:
   - `ads_management`
   - `ads_read`
   - `business_management`
   - `pages_read_engagement`
   - `pages_manage_ads`
4. Generate a **User Access Token**
5. Exchange for a **Long-Lived Token** (60 days):

```bash
curl -i -X GET "https://graph.facebook.com/v18.0/oauth/access_token?\
grant_type=fb_exchange_token&\
client_id=YOUR_APP_ID&\
client_secret=YOUR_APP_SECRET&\
fb_exchange_token=SHORT_LIVED_TOKEN"
```

#### Step 3: Configure Environment Variables

```bash
# Meta App Credentials
META_APP_ID=1234567890123456
META_APP_SECRET=abcdef1234567890abcdef1234567890
META_CLIENT_TOKEN=abcdef1234567890abcdef1234567890

# Meta Access Token (Long-lived)
META_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
META_ACCESS_TOKEN_EXPIRY=2025-12-31

# Meta Business Account
META_BUSINESS_ACCOUNT_ID=1234567890123456
META_AD_ACCOUNT_ID=act_1234567890
META_PAGE_ID=1234567890123456

# Meta Pixel & CAPI
META_PIXEL_ID=1234567890123456
META_CONVERSION_API_TOKEN=your_capi_token_here

# Configuration
META_API_VERSION=v18.0
META_SANDBOX_MODE=false
```

### Campaign Creation

#### Complete Campaign Workflow

```typescript
import { MetaAdsManager } from './services/meta-publisher/src/facebook/meta-ads-manager';

const metaManager = new MetaAdsManager({
  accessToken: process.env.META_ACCESS_TOKEN,
  adAccountId: process.env.META_AD_ACCOUNT_ID,
  pageId: process.env.META_PAGE_ID
});

// Step 1: Create Campaign
const campaignId = await metaManager.createCampaign({
  name: 'Product Launch Q1 2025',
  objective: 'OUTCOME_ENGAGEMENT',
  status: 'PAUSED',
  specialAdCategories: []
});

// Step 2: Create Ad Set
const adSetId = await metaManager.createAdSet({
  name: 'Cold Audience - US',
  campaignId: campaignId,
  bidAmount: 500, // cents
  dailyBudget: 5000, // cents = $50/day
  targeting: {
    geo_locations: { countries: ['US'] },
    age_min: 25,
    age_max: 45,
    genders: [0], // All genders
  },
  optimizationGoal: 'REACH',
  billingEvent: 'IMPRESSIONS',
  status: 'PAUSED'
});

// Step 3: Upload Video
const videoId = await metaManager.uploadVideo('/path/to/video.mp4');

// Step 4: Create Ad Creative
const creativeId = await metaManager.createAdCreative({
  name: 'Product Demo Creative',
  videoId: videoId,
  title: 'Transform Your Business Today',
  message: 'See results in 30 days or your money back!',
  callToAction: {
    type: 'LEARN_MORE',
    value: { link: 'https://yoursite.com/offer' }
  }
});

// Step 5: Create Ad
const adId = await metaManager.createAd({
  name: 'Product Demo Ad',
  adSetId: adSetId,
  creativeId: creativeId,
  status: 'PAUSED'
});

// Step 6: Activate
await metaManager.updateAdStatus(adId, 'ACTIVE');
```

#### Simplified Video Ad Creation

```typescript
// All-in-one method
const result = await metaManager.createVideoAd(
  '/path/to/video.mp4',
  campaignId,
  adSetId,
  {
    name: 'Quick Ad Creative',
    videoId: '', // Will be set after upload
    title: 'Limited Time Offer',
    message: '50% off for new customers',
    callToAction: { type: 'SHOP_NOW' }
  },
  'My First Ad'
);

console.log(`Ad Created: ${result.adId}`);
console.log(`Video ID: ${result.videoId}`);
console.log(`Creative ID: ${result.creativeId}`);
```

### Conversion API (CAPI) Webhook Configuration

#### Why CAPI?
- **Browser-independent tracking**: Works even with ad blockers
- **Better attribution**: Server-side events are more reliable
- **iOS 14.5+ compliance**: Bypasses App Tracking Transparency limitations
- **Deduplication**: Combines with Pixel events for accuracy

#### Step 1: Configure Webhook Endpoint

```python
# services/ml-service/src/capi_webhook_handler.py
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import os

CAPI_APP_SECRET = os.getenv('META_APP_SECRET')
META_VERIFY_TOKEN = os.getenv('META_VERIFY_TOKEN', 'your_custom_verify_token')

# Verification endpoint (GET)
@router.get("/webhooks/capi")
async def verify_webhook(hub_mode: str, hub_verify_token: str, hub_challenge: str):
    if hub_mode == 'subscribe' and hub_verify_token == META_VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

# Event receiver (POST)
@router.post("/webhooks/capi")
async def receive_capi_events(request: Request, background_tasks: BackgroundTasks):
    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256', '')
    body = await request.body()

    if not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()

    # Process events asynchronously
    for entry in data.get('entry', []):
        for event in entry.get('changes', []):
            background_tasks.add_task(process_capi_event, event)

    return {"status": "received"}
```

#### Step 2: Register Webhook in Meta

1. Go to **App Dashboard > Webhooks**
2. Subscribe to `Conversion API`
3. Enter callback URL: `https://yourdomain.com/webhooks/capi`
4. Enter verify token (matches `META_VERIFY_TOKEN`)
5. Subscribe to events: `conversions`, `purchases`, `leads`

#### Step 3: Send Conversion Events

```typescript
// Send conversion to CAPI
await metaManager.sendConversionEvent({
  eventName: 'Purchase',
  eventTime: Math.floor(Date.now() / 1000),
  actionSource: 'website',
  eventSourceUrl: 'https://yoursite.com/checkout/success',
  userData: {
    email: 'customer@example.com',
    phone: '+12125551234',
    externalId: 'user_12345',
    clientIpAddress: request.ip,
    clientUserAgent: request.headers['user-agent'],
    fbc: request.cookies.fbc,
    fbp: request.cookies.fbp
  },
  customData: {
    value: 99.99,
    currency: 'USD',
    content_ids: ['product_123'],
    content_type: 'product',
    num_items: 1
  }
}, process.env.META_PIXEL_ID);
```

### Ad Insights & Performance Tracking

```typescript
// Get ad performance
const insights = await metaManager.getAdInsights(adId, 'last_7d');

console.log({
  impressions: insights.impressions,
  clicks: insights.clicks,
  spend: insights.spend,
  ctr: insights.ctr,
  cpm: insights.cpm,
  conversions: insights.conversions,
  costPerConversion: insights.cost_per_conversion
});

// Get campaign-level insights
const campaignInsights = await metaManager.getCampaignInsights(
  campaignId,
  'last_30d'
);

// Sync to database for ML training
await metaManager.syncInsightsToDatabase(adId, insights);
```

### Rate Limits & Best Practices

- **Standard Tier**: 200 calls per hour per user
- **Development Tier**: 50 calls per hour
- **Retry Logic**: Automatic exponential backoff (implemented)
- **Batch Operations**: Use batch API for bulk operations
- **Event Deduplication**: Automatic via `event_id` hash

### Error Handling

```typescript
try {
  await metaManager.createCampaign({...});
} catch (error: any) {
  console.error('Error code:', error.code);
  console.error('Error type:', error.type);
  console.error('Message:', error.message);
  console.error('Trace ID:', error.fbtrace_id);

  // Common errors:
  // Code 4: Rate limit exceeded
  // Code 17: User request limit reached
  // Code 80004: API throttling
  // Code 190: Access token expired
}
```

---

## 2. GOOGLE ADS API

### Overview
Google Ads API integration for campaign creation, conversion tracking, and performance analytics.

### Credentials Setup

#### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project: `geminivideo-ads`
3. Enable **Google Ads API**

#### Step 2: Create OAuth2 Credentials

1. Navigate to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth 2.0 Client ID**
3. Application type: **Web application**
4. Authorized redirect URIs: `https://yourdomain.com/oauth/google/callback`
5. Note your **Client ID** and **Client Secret**

#### Step 3: Get Developer Token

1. Go to [Google Ads](https://ads.google.com)
2. Navigate to **Tools > API Center**
3. Apply for **Developer Token**
4. Wait for approval (usually 24-48 hours)

#### Step 4: Generate Refresh Token

```bash
# Run OAuth flow to get authorization code
open "https://accounts.google.com/o/oauth2/v2/auth?\
client_id=YOUR_CLIENT_ID&\
redirect_uri=YOUR_REDIRECT_URI&\
response_type=code&\
scope=https://www.googleapis.com/auth/adwords&\
access_type=offline&\
prompt=consent"

# Exchange authorization code for refresh token
curl -X POST https://oauth2.googleapis.com/token \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "code=AUTHORIZATION_CODE" \
  -d "grant_type=authorization_code" \
  -d "redirect_uri=YOUR_REDIRECT_URI"
```

#### Step 5: Configure Environment Variables

```bash
# OAuth2 Client Credentials
GOOGLE_CLIENT_ID=123456789012-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Google Ads Developer Token
GOOGLE_DEVELOPER_TOKEN=your_developer_token_here

# OAuth2 Refresh Token
GOOGLE_REFRESH_TOKEN=1//0abcdefghijklmnop

# Google Ads Account
GOOGLE_ADS_CUSTOMER_ID=1234567890
GOOGLE_ADS_MANAGER_CUSTOMER_ID=1234567890

# API Configuration
GOOGLE_ADS_API_VERSION=v16
```

### Conversion Tracking

#### Create Conversion Action

```typescript
import { GoogleConversionTracker } from './services/google-ads/src/conversion_tracking';

const tracker = new GoogleConversionTracker(
  process.env.GOOGLE_ADS_CUSTOMER_ID
);

// Create conversion action
const conversionActionId = await tracker.createConversionAction(
  'Purchase',
  'PURCHASE',
  50.00 // default value
);

console.log(`Conversion Action ID: ${conversionActionId}`);
```

#### Upload Offline Conversion

```typescript
// Upload conversion for a click
const result = await tracker.uploadConversion({
  conversionId: conversionActionId,
  conversionName: 'Purchase',
  conversionTime: new Date(),
  conversionValue: 99.99,
  currencyCode: 'USD',
  gclid: 'Cj0KCQiA...', // Google Click ID from URL
  orderId: 'order_12345',
  customerId: process.env.GOOGLE_ADS_CUSTOMER_ID
});

if (result.success) {
  console.log('Conversion uploaded successfully');
} else {
  console.error('Error:', result.error);
}
```

#### Sync Conversions from Database

```typescript
// Bulk upload conversions
const conversions = [
  {
    gclid: 'Cj0KCQiA...',
    conversionTime: new Date('2025-01-15'),
    value: 149.99,
    orderId: 'order_001'
  },
  {
    gclid: 'Cj0KCQiB...',
    conversionTime: new Date('2025-01-16'),
    value: 79.99,
    orderId: 'order_002'
  }
];

const syncResult = await tracker.syncConversionsFromDatabase(
  conversions,
  conversionActionId
);

console.log(`Synced: ${syncResult.successful} successful, ${syncResult.failed} failed`);
```

### Campaign Performance Analytics

```typescript
// Get conversion stats for a campaign
const stats = await tracker.getCampaignConversionStats(
  'campaign_123',
  new Date('2025-01-01'),
  new Date('2025-01-31')
);

console.log({
  totalConversions: stats.totalConversions,
  totalValue: stats.totalValue,
  averageValue: stats.averageValue,
  conversionRate: stats.conversionRate,
  costPerConversion: stats.costPerConversion,
  roas: stats.roas
});
```

### Get All Conversions

```typescript
// Get conversions in date range
const conversions = await tracker.getConversions(
  new Date('2025-01-01'),
  new Date('2025-01-31')
);

conversions.forEach(conv => {
  console.log({
    date: conv.date,
    action: conv.conversionActionName,
    conversions: conv.conversions,
    value: conv.value,
    campaign: conv.campaignName
  });
});
```

### API Endpoints

```typescript
import { Router } from 'express';
import { createConversionRouter } from './services/google-ads/src/conversion_tracking';

const app = express();
app.use('/api/google-ads', createConversionRouter());

// Available endpoints:
// POST   /api/google-ads/conversions/upload
// GET    /api/google-ads/conversions/stats/:campaignId
// GET    /api/google-ads/conversions
// GET    /api/google-ads/conversion-actions
```

### Rate Limits

- **Operations Limit**: 15,000 operations per day (standard access)
- **Developer Tokens**: Different limits based on access level
- **Best Practice**: Use batch operations when possible

---

## 3. RUNWAY GEN-3 ALPHA

### Overview
Runway Gen-3 Alpha enables AI-powered video generation from text prompts and images for creating product shots, lifestyle scenes, and B-roll footage.

### API Key Setup

1. Sign up at [Runway](https://runwayml.com)
2. Navigate to **Settings > API Keys**
3. Generate new API key
4. Set environment variable:

```bash
RUNWAY_API_KEY=your_runway_api_key_here
```

### Video Generation

#### Text-to-Video

```python
from services.titan_core.integrations.runway_gen3 import (
    RunwayGen3Client,
    GenerationRequest,
    RunwayModel,
    VideoAspectRatio
)

client = RunwayGen3Client(api_key=os.getenv('RUNWAY_API_KEY'))

# Generate video from text
result = await client.generate_video(GenerationRequest(
    prompt="Product floating in space with dynamic lighting, cinematic quality",
    model=RunwayModel.GEN3_ALPHA_TURBO,
    duration=5,  # 5 or 10 seconds
    aspect_ratio=VideoAspectRatio.PORTRAIT,
    seed=42  # Optional: for reproducible results
))

if result.status == 'completed':
    print(f"Video URL: {result.video_url}")
    print(f"Generation time: {result.generation_time}s")
    print(f"Cost: {result.cost_credits} credits")
else:
    print(f"Error: {result.error}")
```

#### Image-to-Video

```python
# Transform static image into video
result = await client.generate_video(GenerationRequest(
    prompt="Smooth camera rotation around product, professional lighting",
    image_url="https://yourbucket.com/product-image.jpg",
    duration=5,
    aspect_ratio=VideoAspectRatio.PORTRAIT
))
```

#### Pre-built Methods

```python
# Generate product shot
result = await client.generate_product_shot(
    product_image="https://yourbucket.com/product.jpg",
    scene_description="Elegant studio setup with soft shadows"
)

# Generate lifestyle scene
result = await client.generate_lifestyle_scene(
    description="Person using product in modern apartment",
    mood="luxury"  # Options: energetic, calm, luxury, playful
)

# Generate multiple variations
variations = await client.generate_variations(
    base_prompt="Product showcase in urban setting",
    count=3
)

for i, variant in enumerate(variations):
    print(f"Variant {i+1}: {variant.video_url}")
```

### Available Models

```python
class RunwayModel(Enum):
    GEN3_ALPHA_TURBO = "gen3a_turbo"  # Fastest, best for iteration
    GEN3_ALPHA = "gen3a_turbo"        # High quality
    GEN2 = "gen2"                     # Fallback option
```

### Aspect Ratios

```python
class VideoAspectRatio(Enum):
    PORTRAIT = "9:16"      # TikTok, Reels, Stories
    LANDSCAPE = "16:9"     # YouTube, Facebook
    SQUARE = "1:1"         # Instagram feed
    WIDESCREEN = "21:9"    # Cinematic
```

### Rate Limits & Pricing

- **Generation Time**: ~30-60 seconds per video
- **Max Duration**: 10 seconds per generation
- **Cost**: ~$0.05 per second for Gen-3 Turbo
- **Concurrent Requests**: 5 concurrent generations (Pro plan)
- **Polling Interval**: 5 seconds (implemented automatically)
- **Timeout**: 5 minutes (300 seconds)

### Error Handling

```python
try:
    result = await client.generate_video(request)
    if result.status == 'failed':
        print(f"Generation failed: {result.error}")
except Exception as e:
    print(f"API error: {e}")
```

### Mock Client for Testing

```python
# Use mock client when API key not available
from services.titan_core.integrations.runway_gen3 import get_runway_client

client = get_runway_client()  # Returns MockRunwayClient if no API key

# Mock client returns fake data instantly (for development)
result = await client.generate_video(request)
# Returns mock result with video_url="https://example.com/mock_video.mp4"
```

---

## 4. ELEVENLABS VOICE API

### Overview
ElevenLabs provides AI voice generation and cloning for professional voiceovers in multiple languages.

### API Key Setup

1. Sign up at [ElevenLabs](https://elevenlabs.io)
2. Navigate to **Profile > API Keys**
3. Generate new API key
4. Set environment variable:

```bash
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### Voice Generation

#### Basic Text-to-Speech

```python
from services.titan_core.integrations.elevenlabs_voice import (
    ElevenLabsClient,
    VoiceOverRequest,
    VoiceModel,
    VoiceSettings,
    VOICE_PRESETS
)

client = ElevenLabsClient(api_key=os.getenv('ELEVENLABS_API_KEY'))

# Generate voiceover
result = await client.generate_voiceover(VoiceOverRequest(
    text="Discover the revolutionary new product that will change your life!",
    voice_id=VOICE_PRESETS["rachel"],  # Calm female voice
    model=VoiceModel.ELEVEN_TURBO_V2,
    settings=VoiceSettings(
        stability=0.5,
        similarity_boost=0.75,
        style=0.5,
        use_speaker_boost=True
    )
))

if result.error:
    print(f"Error: {result.error}")
else:
    # Save audio
    with open('voiceover.mp3', 'wb') as f:
        f.write(result.audio_data)

    print(f"Duration: {result.duration_seconds}s")
    print(f"Characters used: {result.characters_used}")
```

### Pre-built Voice Presets

```python
VOICE_PRESETS = {
    "adam": "pNInz6obpgDQGcFmaJgB",     # Deep male voice
    "rachel": "21m00Tcm4TlvDq8ikWAM",   # Calm female voice
    "domi": "AZnzlk1XvdvUeBnXmlld",     # Young female, energetic
    "bella": "EXAVITQu4vr4xnSDxMaL",    # Soft female voice
    "elli": "MF3mGyEYCl7XYWbV9V6O",     # Young female, American
    "josh": "TxGEqnHWrfWFTfGW9XjX",     # Deep male, American
    "arnold": "VR6AewLTigWG4xSOukaG",   # Strong male voice
    "sam": "yoZ06aMxZJJ28mfd3POQ",      # Young male, American
}
```

### Voice Cloning

```python
# Clone a voice from audio samples
audio_samples = [
    open('sample1.mp3', 'rb').read(),
    open('sample2.mp3', 'rb').read(),
    open('sample3.mp3', 'rb').read()
]

voice_id = await client.clone_voice(
    name="Brand Voice",
    audio_files=audio_samples,
    description="Professional brand spokesperson voice"
)

if voice_id:
    print(f"Voice cloned successfully: {voice_id}")

    # Use cloned voice
    result = await client.generate_voiceover(VoiceOverRequest(
        text="This is our brand message",
        voice_id=voice_id
    ))
```

### Ad-Optimized Voiceover

```python
# Pre-configured for advertising
result = await client.generate_ad_voiceover(
    script="Limited time offer! Get 50% off today only!",
    voice_type="energetic_female"  # Options: energetic_male, calm_male,
                                   # calm_female, young_female, young_male,
                                   # authoritative
)
```

### Multilingual Support

```python
# Generate voiceover in different languages
result = await client.generate_multilingual(
    text="Bonjour! Découvrez notre nouveau produit.",
    voice_id=VOICE_PRESETS["rachel"],
    language="fr"  # French
)

# Supported languages: en, es, fr, de, it, pt, pl, hi, ar, zh, ja, ko, and more
```

### Voice Settings Explained

```python
VoiceSettings(
    stability=0.5,          # 0-1: Higher = more consistent, lower = more expressive
    similarity_boost=0.75,  # 0-1: Higher = more similar to original voice
    style=0.5,              # 0-1: Exaggeration of speaking style
    use_speaker_boost=True  # Enhance clarity and quality
)

# Recommended presets:
# - Audiobook: stability=0.75, similarity=0.8, style=0.3
# - Advertisement: stability=0.6, similarity=0.8, style=0.7
# - Conversational: stability=0.5, similarity=0.75, style=0.5
```

### Cost Estimation

```python
estimate = client.estimate_cost(
    "Your script text here. Make it as long as your actual script will be."
)

print(f"Characters: {estimate['characters']}")
print(f"Estimated cost: ${estimate['estimated_cost_usd']:.4f}")
print(f"Estimated duration: {estimate['estimated_duration_seconds']:.1f}s")
```

### Available Models

```python
class VoiceModel(Enum):
    ELEVEN_TURBO_V2 = "eleven_turbo_v2"              # Fast, good quality
    ELEVEN_MULTILINGUAL_V2 = "eleven_multilingual_v2"  # Best for languages
    ELEVEN_MONOLINGUAL_V1 = "eleven_monolingual_v1"    # English optimized
```

### Get Available Voices

```python
# List all available voices in your account
voices = await client.get_available_voices()

for voice in voices:
    print(f"{voice['name']}: {voice['voice_id']}")
```

### Rate Limits & Pricing

- **Free Tier**: 10,000 characters/month
- **Starter**: 30,000 characters/month
- **Creator**: 100,000 characters/month
- **Pro**: 500,000 characters/month
- **Cost**: ~$0.00003 per character (approximate)
- **Rate Limit**: Varies by plan
- **Character Limit**: 5,000 characters per request

---

## 5. DATABASE (POSTGRESQL & REDIS)

### PostgreSQL Setup

#### Connection Configuration

```bash
# Self-hosted PostgreSQL
POSTGRES_USER=geminivideo
POSTGRES_PASSWORD=your_secure_password_min_32_chars
POSTGRES_DB=geminivideo
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Full connection string
DATABASE_URL=postgresql://geminivideo:password@postgres:5432/geminivideo

# Connection pooling
DATABASE_POOL_MIN=2
DATABASE_POOL_MAX=10
DATABASE_POOL_TIMEOUT=20000
DATABASE_POOL_IDLE_TIMEOUT=30000
```

#### Alternative: Supabase (Managed PostgreSQL)

```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
```

### Schema Overview

#### Core Tables

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    company_name TEXT,
    role TEXT DEFAULT 'user',
    meta_access_token TEXT,
    meta_ad_account_id TEXT,
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Campaigns
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    product_name TEXT,
    offer TEXT,
    target_avatar TEXT,
    status TEXT DEFAULT 'draft',
    budget_daily DECIMAL(12, 2) DEFAULT 0,
    spend DECIMAL(12, 2) DEFAULT 0,
    revenue DECIMAL(12, 2) DEFAULT 0,
    roas DECIMAL(8, 2) DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    meta_campaign_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK (status IN ('draft', 'generating', 'active', 'paused', 'completed', 'archived'))
);

-- Blueprints (Ad Scripts)
CREATE TABLE blueprints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    title TEXT,
    hook_text TEXT,
    script TEXT,
    scenes JSONB DEFAULT '[]'::jsonb,
    council_score DECIMAL(5,2),
    predicted_roas DECIMAL(10,2),
    predicted_ctr DECIMAL(8, 4),
    status TEXT DEFAULT 'pending',
    verdict TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK (status IN ('pending', 'approved', 'rejected', 'rendering', 'completed')),
    CHECK (verdict IN ('approved', 'rejected', 'pending') OR verdict IS NULL)
);

-- Videos
CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    blueprint_id UUID REFERENCES blueprints(id),
    user_id UUID REFERENCES users(id),
    title VARCHAR(255),
    video_url TEXT,
    thumbnail_url TEXT,
    duration_seconds FLOAT,
    status VARCHAR(50) DEFAULT 'processing',
    meta_platform_id VARCHAR(255),
    predicted_ctr FLOAT,
    actual_roas FLOAT,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK (status IN ('uploading', 'processing', 'ready', 'failed', 'published', 'archived'))
);

-- Predictions (ML Model)
CREATE TABLE predictions (
    id VARCHAR(255) PRIMARY KEY,
    video_id VARCHAR(255) NOT NULL,
    ad_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    predicted_ctr FLOAT NOT NULL,
    predicted_roas FLOAT NOT NULL,
    predicted_conversion FLOAT NOT NULL,
    actual_ctr FLOAT,
    actual_roas FLOAT,
    actual_conversion FLOAT,
    council_score FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- A/B Tests
CREATE TABLE ab_tests (
    id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'running',
    control_variant_id VARCHAR(255),
    test_variant_id VARCHAR(255),
    metric_name VARCHAR(100),
    control_value FLOAT,
    test_value FLOAT,
    lift_percent FLOAT,
    p_value FLOAT,
    is_significant BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Running Migrations

```bash
# Run migrations
psql $DATABASE_URL -f database/migrations/001_creative_assets.sql
psql $DATABASE_URL -f database/migrations/002_schema_consolidation.sql
psql $DATABASE_URL -f database/migrations/003_performance_indexes.sql
```

### Python Database Connection

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Use in FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### TypeScript Database Connection

```typescript
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Query helper
export async function query(text: string, params?: any[]) {
  const client = await pool.connect();
  try {
    const result = await client.query(text, params);
    return result;
  } finally {
    client.release();
  }
}
```

### Redis Setup

#### Connection Configuration

```bash
# Self-hosted Redis
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=
REDIS_DB=0

# OR: Redis Cloud / Upstash (Serverless)
REDIS_URL=redis://username:password@your-redis-cloud.com:12345
UPSTASH_REDIS_REST_URL=https://your-region.upstash.io
UPSTASH_REDIS_REST_TOKEN=your_upstash_token

# Configuration
REDIS_ENABLED=true
REDIS_TTL_DEFAULT=3600
REDIS_MAX_RETRIES=3
REDIS_RETRY_DELAY=1000
```

#### Python Redis Client

```python
import redis
import json
import os

redis_client = redis.from_url(
    os.getenv('REDIS_URL'),
    decode_responses=True,
    socket_connect_timeout=5,
    socket_keepalive=True,
    retry_on_timeout=True
)

# Set with TTL
redis_client.setex(
    'prediction:campaign_123',
    3600,  # 1 hour TTL
    json.dumps({'ctr': 0.045, 'roas': 3.2})
)

# Get
data = redis_client.get('prediction:campaign_123')
if data:
    prediction = json.loads(data)
```

#### TypeScript Redis Client

```typescript
import { createClient } from 'redis';

const redisClient = createClient({
  url: process.env.REDIS_URL,
  socket: {
    reconnectStrategy: (retries) => Math.min(retries * 50, 500)
  }
});

await redisClient.connect();

// Set with expiration
await redisClient.setEx(
  'session:user_123',
  3600,
  JSON.stringify({ userId: '123', role: 'admin' })
);

// Get
const session = await redisClient.get('session:user_123');
if (session) {
  const data = JSON.parse(session);
}
```

#### Common Use Cases

```python
# Cache ML predictions
await redis_client.setex(
    f'ml:prediction:{video_id}',
    86400,  # 24 hours
    json.dumps({
        'ctr': 0.045,
        'roas': 3.2,
        'confidence': 0.87
    })
)

# Rate limiting
key = f'rate_limit:{user_id}:{endpoint}'
requests = await redis_client.incr(key)
if requests == 1:
    await redis_client.expire(key, 60)  # 60 second window
if requests > 100:
    raise Exception('Rate limit exceeded')

# Job queue
await redis_client.lpush('render_queue', json.dumps({
    'job_id': 'render_123',
    'blueprint_id': 'bp_456',
    'priority': 'high'
}))

# Session storage
await redis_client.hset(
    f'session:{session_id}',
    mapping={
        'user_id': user_id,
        'created_at': datetime.now().isoformat(),
        'ip_address': request.ip
    }
)
```

---

## 6. QUICK REFERENCE

### Environment Variables Checklist

```bash
# Essential (Required)
✓ DATABASE_URL
✓ REDIS_URL
✓ GEMINI_API_KEY
✓ JWT_SECRET
✓ META_ACCESS_TOKEN
✓ META_AD_ACCOUNT_ID

# AI Services (Optional but recommended)
○ RUNWAY_API_KEY
○ ELEVENLABS_API_KEY
○ OPENAI_API_KEY
○ ANTHROPIC_API_KEY

# Ad Platforms (At least one required)
✓ META_APP_ID, META_APP_SECRET
○ GOOGLE_ADS_CUSTOMER_ID, GOOGLE_DEVELOPER_TOKEN
○ TIKTOK_ACCESS_TOKEN, TIKTOK_ADVERTISER_ID

# Storage (Choose one)
○ GCS_BUCKET_NAME, GCP_SERVICE_ACCOUNT_JSON
○ AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET
○ R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET
```

### API Endpoint Summary

```
Meta Marketing API
├── POST   /api/meta/campaigns          - Create campaign
├── POST   /api/meta/adsets             - Create ad set
├── POST   /api/meta/videos             - Upload video
├── POST   /api/meta/creatives          - Create creative
├── POST   /api/meta/ads                - Create ad
├── GET    /api/meta/insights/:adId     - Get ad insights
└── POST   /webhooks/capi               - CAPI webhook receiver

Google Ads API
├── POST   /api/google-ads/conversions/upload
├── GET    /api/google-ads/conversions/stats/:campaignId
├── GET    /api/google-ads/conversions
└── GET    /api/google-ads/conversion-actions

Internal Services
├── POST   /api/video/generate          - Generate video (Runway)
├── POST   /api/voice/generate          - Generate voiceover (ElevenLabs)
├── POST   /api/ml/predict              - Get predictions
└── GET    /api/analytics/dashboard     - Get analytics data
```

### Common Workflows

#### Complete Ad Creation Flow

```
1. Create Campaign (Meta/Google)
   ↓
2. Generate Video Script (Titan AI)
   ↓
3. Generate Voiceover (ElevenLabs)
   ↓
4. Generate Video (Runway Gen-3)
   ↓
5. Render Final Video (Video Agent)
   ↓
6. Upload to Platform (Meta/Google)
   ↓
7. Create Ad (Meta/Google)
   ↓
8. Track Conversions (CAPI/Google Conversions API)
   ↓
9. Feed Back to ML (CAPI Feedback Loop)
   ↓
10. Retrain Models (Daily Job)
```

### Testing Integrations

```bash
# Test Meta API
curl -X POST https://graph.facebook.com/v18.0/act_YOUR_ACCOUNT_ID/campaigns \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d "name=Test Campaign&objective=OUTCOME_ENGAGEMENT&status=PAUSED"

# Test Google Ads API
curl -X POST https://googleads.googleapis.com/v16/customers/YOUR_CUSTOMER_ID/googleAds:searchStream \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "developer-token: YOUR_DEVELOPER_TOKEN" \
  -d '{"query": "SELECT campaign.id, campaign.name FROM campaign"}'

# Test Runway API
curl -X POST https://api.runwayml.com/v1/generations \
  -H "Authorization: Bearer YOUR_RUNWAY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test video", "model": "gen3a_turbo", "duration": 5}'

# Test ElevenLabs API
curl -X GET https://api.elevenlabs.io/v1/voices \
  -H "xi-api-key: YOUR_ELEVENLABS_API_KEY"

# Test Database
psql $DATABASE_URL -c "SELECT version();"

# Test Redis
redis-cli -u $REDIS_URL ping
```

### Troubleshooting

#### Meta API Issues

```
Error 190: Access Token Expired
→ Regenerate long-lived token

Error 4: Rate Limit Exceeded
→ Implement exponential backoff (already done)
→ Consider upgrading API tier

Error 100: Invalid Parameter
→ Check campaign objective matches ad set optimization goal
→ Verify targeting parameters format
```

#### Google Ads Issues

```
Error: Invalid refresh token
→ Regenerate refresh token through OAuth flow

Error: Developer token not approved
→ Wait for Google approval (24-48 hours)
→ Check token status in Google Ads API Center

Error: Customer not found
→ Verify GOOGLE_ADS_CUSTOMER_ID format (no dashes)
→ Ensure you have access to the account
```

#### Runway Issues

```
Error: Insufficient credits
→ Add credits to Runway account

Error: Generation timeout
→ Normal for complex prompts, wait up to 5 minutes
→ Check status via task_id polling

Error: Invalid prompt
→ Avoid NSFW content
→ Keep prompts under 500 characters
```

#### Database Issues

```
Connection refused
→ Check DATABASE_URL format
→ Verify PostgreSQL is running: docker ps

Too many connections
→ Increase DATABASE_POOL_MAX
→ Check for connection leaks

Migration failed
→ Run migrations in order
→ Check for existing constraints
```

---

## Support & Resources

### Official Documentation

- **Meta Marketing API**: https://developers.facebook.com/docs/marketing-apis
- **Google Ads API**: https://developers.google.com/google-ads/api/docs
- **Runway API**: https://docs.runwayml.com
- **ElevenLabs API**: https://docs.elevenlabs.io
- **PostgreSQL**: https://www.postgresql.org/docs
- **Redis**: https://redis.io/docs

### Internal Documentation

- Architecture: `/home/user/geminivideo/docs/VERIFIED_ARCHITECTURE_2025.md`
- API Reference: `/home/user/geminivideo/docs/API_REFERENCE.md`
- Deployment: `/home/user/geminivideo/docs/deployment.md`
- Troubleshooting: `/home/user/geminivideo/docs/troubleshooting.md`

### Validation Scripts

```bash
# Validate all environment variables
bash scripts/validate-env.py .env.production

# Test all integrations
bash scripts/final-checklist.py

# Health check all services
bash scripts/health-check.sh
```

---

**Last Updated**: 2025-01-06
**Version**: 1.0
**Maintainer**: GeminiVideo Platform Team
