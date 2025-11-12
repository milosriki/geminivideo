# Agent 7: Meta Integration Engineer

## Your Mission
Implement real Facebook SDK integration with A/B testing and Thompson Sampling.

## Priority: HIGH

## Tasks

### 1. Install Dependencies
```bash
npm install facebook-business
```

### 2. Meta SDK Integration
Create `services/meta-publisher/src/facebook/client.ts`:
```typescript
import { FacebookAdsApi, AdAccount, Campaign, AdSet, Ad, AdCreative } from 'facebook-business-sdk';

export class MetaAdsClient {
  private api: FacebookAdsApi;
  private accountId: string;

  constructor(accessToken: string, accountId: string) {
    this.api = FacebookAdsApi.init(accessToken);
    this.accountId = accountId;
  }

  async createCampaign(name: string, objective: string = 'REACH') {
    const account = new AdAccount(this.accountId);

    const campaign = await account.createCampaign([], {
      name,
      objective,
      status: 'PAUSED',
      special_ad_categories: []
    });

    return campaign.id;
  }

  async createAdSet(campaignId: string, targeting: any, budget: number) {
    const account = new AdAccount(this.accountId);

    const adSet = await account.createAdSet([], {
      name: `AdSet_${Date.now()}`,
      campaign_id: campaignId,
      daily_budget: budget * 100,  // In cents
      billing_event: 'IMPRESSIONS',
      optimization_goal: 'REACH',
      bid_amount: 200,
      targeting,
      status: 'PAUSED'
    });

    return adSet.id;
  }

  async createVideoAd(adSetId: string, videoUrl: string, caption: string) {
    const account = new AdAccount(this.accountId);

    // Upload video
    const video = await account.createAdVideo([], {
      source: videoUrl
    });

    // Create creative
    const creative = await account.createAdCreative([], {
      name: `Creative_${Date.now()}`,
      object_story_spec: {
        page_id: 'YOUR_PAGE_ID',  // TODO: Configure
        video_data: {
          video_id: video.id,
          title: caption.substring(0, 100),
          message: caption
        }
      }
    });

    // Create ad
    const ad = await account.createAd([], {
      name: `Ad_${Date.now()}`,
      adset_id: adSetId,
      creative: { creative_id: creative.id },
      status: 'PAUSED'
    });

    return ad.id;
  }

  async getInsights(adId: string) {
    const ad = new Ad(adId);
    const insights = await ad.getInsights([
      'impressions',
      'clicks',
      'ctr',
      'spend',
      'reach',
      'actions'
    ]);

    return insights[0];
  }

  async createABTest(variants: any[], budget: number) {
    // Create campaign
    const campaignId = await this.createCampaign('AI_Video_Ad_Test', 'REACH');

    // Create ad sets for each variant
    const adSetIds = [];
    for (const variant of variants) {
      const adSetId = await this.createAdSet(
        campaignId,
        variant.targeting,
        budget / variants.length
      );
      adSetIds.push(adSetId);

      // Create ad in each ad set
      await this.createVideoAd(adSetId, variant.videoUrl, variant.caption);
    }

    return { campaignId, adSetIds };
  }
}
```

### 3. Thompson Sampling Integration
Update `services/meta-publisher/src/optimization.py` (from Agent 3):
```typescript
import { ThompsonSampling } from './optimization';

interface AdVariant {
  videoUrl: string;
  caption: string;
  targeting: any;
  emotion_score: number;
  predicted_ctr: number;
}

export class ABTestOptimizer {
  private sampler: ThompsonSampling;
  private metaClient: MetaAdsClient;

  constructor(metaClient: MetaAdsClient, numVariants: number = 3) {
    this.sampler = new ThompsonSampling(numVariants);
    this.metaClient = metaClient;
  }

  async runOptimizedTest(variants: AdVariant[], budget: number) {
    // Create campaign with all variants
    const { campaignId, adSetIds } = await this.metaClient.createABTest(variants, budget);

    // Set up optimization loop
    const checkInterval = 3600000;  // Check every hour

    const optimize = async () => {
      for (let i = 0; i < adSetIds.length; i++) {
        const insights = await this.metaClient.getInsights(adSetIds[i]);

        const ctr = insights.ctr || 0;
        const context = {
          emotion: variants[i].emotion_score,
          predicted_ctr: variants[i].predicted_ctr
        };

        // Update Thompson Sampling
        this.sampler.update(i, ctr, context);
      }

      // Get best variant
      const stats = this.sampler.get_stats();
      const bestVariant = stats.best_variant;

      // Reallocate budget to best performer
      // (In production, would adjust ad set budgets)
      console.log(`Best variant: ${bestVariant} with stats:`, stats.variants[bestVariant]);

      // Continue monitoring
      setTimeout(optimize, checkInterval);
    };

    // Start optimization after initial data collection
    setTimeout(optimize, checkInterval * 2);

    return {
      campaignId,
      message: 'A/B test started with Thompson Sampling optimization'
    };
  }
}
```

### 4. Update Meta Publisher Service
Update `services/meta-publisher/src/index.ts`:
```typescript
import { MetaAdsClient } from './facebook/client';
import { ABTestOptimizer } from './optimization';

const META_TOKEN = process.env.META_ACCESS_TOKEN;
const ACCOUNT_ID = process.env.META_AD_ACCOUNT_ID;

const metaClient = new MetaAdsClient(META_TOKEN, ACCOUNT_ID);
const optimizer = new ABTestOptimizer(metaClient);

app.post('/publish/meta', async (req, res) => {
  const {
    video_url,
    caption,
    targeting,
    budget,
    prediction_id,
    enable_ab_test = false,
    variants = []
  } = req.body;

  try {
    if (enable_ab_test && variants.length > 1) {
      // Run A/B test with optimization
      const result = await optimizer.runOptimizedTest(variants, budget.daily_budget);
      return res.json(result);
    }

    // Single ad publish
    const campaignId = await metaClient.createCampaign('AI_Video_Ad');
    const adSetId = await metaClient.createAdSet(campaignId, targeting, budget.daily_budget);
    const adId = await metaClient.createVideoAd(adSetId, video_url, caption);

    // Link to prediction
    if (prediction_id) {
      // Store ad_id with prediction in DB
      const db = SessionLocal();
      const pred = db.query(Prediction).filter(Prediction.prediction_id == prediction_id).first();
      if (pred) {
        pred.ad_id = adId;
        db.commit();
      }
      db.close();
    }

    res.json({
      ad_id: adId,
      campaign_id: campaignId,
      status: 'published',
      message: 'Ad published successfully to Meta'
    });
  } catch (error) {
    res.status(500).json({
      error: error.message,
      message: 'Failed to publish ad'
    });
  }
});

app.get('/insights', async (req, res) => {
  const { ad_id, prediction_id } = req.query;

  try {
    const insights = await metaClient.getInsights(ad_id);

    // Update prediction with actual CTR
    if (prediction_id) {
      const db = SessionLocal();
      const pred = db.query(Prediction).filter(Prediction.prediction_id == prediction_id).first();
      if (pred) {
        pred.actual_ctr = insights.ctr;
        pred.updated_at = new Date();
        db.commit();
      }
      db.close();
    }

    res.json({
      ad_id,
      insights: {
        impressions: insights.impressions,
        clicks: insights.clicks,
        ctr: insights.ctr,
        spend: insights.spend,
        reach: insights.reach
      },
      updated_at: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

### 5. Configuration
Update `shared/config/fb_integration.json`:
```json
{
  "token": "${META_ACCESS_TOKEN}",
  "account_id": "${META_AD_ACCOUNT_ID}",
  "page_id": "${META_PAGE_ID}",
  "a_b_testing": {
    "enabled": true,
    "variants": 3,
    "optimization_metric": "ctr",
    "min_budget_per_variant": 50,
    "check_interval_hours": 1
  },
  "default_targeting": {
    "age_min": 25,
    "age_max": 45,
    "genders": [1, 2],
    "geo_locations": {
      "countries": ["US", "CA", "GB"]
    }
  }
}
```

### 6. Testing
Create `tests/test_meta_integration.py`:
```python
import pytest
from unittest.mock import Mock, patch

def test_meta_client_initialization():
    client = MetaAdsClient('test_token', 'act_123')
    assert client.accountId == 'act_123'

@patch('facebook_business_sdk.AdAccount.createCampaign')
def test_create_campaign(mock_create):
    mock_create.return_value = Mock(id='campaign_123')
    client = MetaAdsClient('test_token', 'act_123')
    campaign_id = await client.createCampaign('Test Campaign')
    assert campaign_id == 'campaign_123'
```

## Deliverables
- [ ] Facebook SDK integration
- [ ] Campaign/AdSet/Ad creation
- [ ] Video upload and creative creation
- [ ] A/B testing with Thompson Sampling
- [ ] Insights fetching
- [ ] Prediction update on actual CTR
- [ ] Configuration management
- [ ] Tests for Meta integration

## Branch
`agent-7-meta-integration`

## Blockers
- **Agent 3** (needs optimization models)
- Meta access token and account setup (manual)

## Who Depends On You
- Agent 5 (frontend needs publish endpoint)
- Nightly learning (needs actual CTR data)
