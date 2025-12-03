/**
 * Meta Publisher Service - Creative Publishing & Insights Ingestion
 * Agents 11-15: Real Facebook SDK Integration
 */
import express, { Request, Response } from 'express';
import cors from 'cors';
import axios from 'axios';
import { MetaAdsManager } from './facebook/meta-ads-manager';
import { InsightsIngestionService } from './services/insights-ingestion';

const app = express();
const PORT = process.env.PORT || 8083;

// CORS configuration - use environment variable for allowed origins
// CORS_ORIGINS should be comma-separated list of allowed origins
// e.g., "https://frontend.run.app,http://localhost:3000"
const CORS_ORIGINS = (process.env.CORS_ORIGINS || 'http://localhost:3000,http://localhost:8080').split(',');
const corsOptions = {
  origin: CORS_ORIGINS,
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
};

// Middleware
app.use(cors(corsOptions));
app.use(express.json());

// Meta API configuration
const META_ACCESS_TOKEN = process.env.META_ACCESS_TOKEN || '';
const META_AD_ACCOUNT_ID = process.env.META_AD_ACCOUNT_ID || '';
const META_PAGE_ID = process.env.META_PAGE_ID || '';
const META_API_VERSION = process.env.META_API_VERSION || 'v18.0';
const META_API_BASE = `https://graph.facebook.com/${META_API_VERSION}`;

// Initialize Meta Ads Manager if credentials are available
let metaAdsManager: MetaAdsManager | null = null;
if (META_ACCESS_TOKEN && META_AD_ACCOUNT_ID && META_PAGE_ID) {
  metaAdsManager = new MetaAdsManager({
    accessToken: META_ACCESS_TOKEN,
    adAccountId: META_AD_ACCOUNT_ID,
    pageId: META_PAGE_ID
  });
  console.log('Meta Ads Manager initialized with real Facebook SDK');

  // Initialize Insights Ingestion Service
  const DATABASE_URL = process.env.DATABASE_URL;
  console.log('Checking DATABASE_URL for Insights Ingestion:', DATABASE_URL ? 'Set' : 'Not Set');

  if (DATABASE_URL) {
    const ingestionService = new InsightsIngestionService(metaAdsManager, DATABASE_URL);
    ingestionService.startCronJob();
  } else {
    console.warn('DATABASE_URL not set - Insights Ingestion disabled');
  }

} else {
  console.log('Warning: Meta credentials not configured - running in dry-run mode');
}

// Helper function to validate Meta API URLs
function validateMetaApiUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    // Only allow official Facebook Graph API domains
    return parsed.hostname === 'graph.facebook.com' &&
      parsed.protocol === 'https:';
  } catch {
    return false;
  }
}

// Root endpoint
app.get('/', (req: Request, res: Response) => {
  res.json({
    service: 'meta-publisher',
    status: 'running',
    version: '2.0.0',
    real_sdk_enabled: !!metaAdsManager,
    dry_run_mode: !META_ACCESS_TOKEN,
    endpoints: {
      campaigns: '/api/campaigns',
      adsets: '/api/adsets',
      ads: '/api/ads',
      video_ads: '/api/video-ads',
      insights: '/api/insights',
      legacy_publish: '/publish/meta (deprecated)',
      legacy_insights: '/insights (deprecated)'
    }
  });
});

// Agent 12: Create Campaign
app.post('/api/campaigns', async (req: Request, res: Response) => {
  try {
    if (!metaAdsManager) {
      return res.status(400).json({
        error: 'Meta SDK not configured',
        message: 'Set META_ACCESS_TOKEN, META_AD_ACCOUNT_ID, and META_PAGE_ID'
      });
    }

    const { name, objective, status, specialAdCategories } = req.body;

    const campaignId = await metaAdsManager.createCampaign({
      name,
      objective,
      status,
      specialAdCategories
    });

    res.json({
      status: 'success',
      campaign_id: campaignId,
      message: 'Campaign created successfully'
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Agent 12: Create AdSet
app.post('/api/adsets', async (req: Request, res: Response) => {
  try {
    if (!metaAdsManager) {
      return res.status(400).json({
        error: 'Meta SDK not configured'
      });
    }

    const {
      name,
      campaignId,
      bidAmount,
      dailyBudget,
      targeting,
      optimizationGoal,
      billingEvent,
      status
    } = req.body;

    const adSetId = await metaAdsManager.createAdSet({
      name,
      campaignId,
      bidAmount,
      dailyBudget,
      targeting,
      optimizationGoal,
      billingEvent,
      status
    });

    res.json({
      status: 'success',
      adset_id: adSetId,
      message: 'AdSet created successfully'
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Agent 13: Create Video Ad (Complete Workflow)
app.post('/api/video-ads', async (req: Request, res: Response) => {
  try {
    if (!metaAdsManager) {
      return res.status(400).json({
        error: 'Meta SDK not configured'
      });
    }

    const {
      videoPath,
      campaignId,
      adSetId,
      creative,
      adName
    } = req.body;

    const result = await metaAdsManager.createVideoAd(
      videoPath,
      campaignId,
      adSetId,
      creative,
      adName
    );

    res.json({
      status: 'success',
      ...result,
      message: 'Video ad created successfully'
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Agent 13: Upload Video Only
app.post('/api/videos/upload', async (req: Request, res: Response) => {
  try {
    if (!metaAdsManager) {
      return res.status(400).json({
        error: 'Meta SDK not configured'
      });
    }

    const { videoPath } = req.body;

    const videoId = await metaAdsManager.uploadVideo(videoPath);

    res.json({
      status: 'success',
      video_id: videoId,
      message: 'Video uploaded successfully'
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Agent 13: Create Ad from existing creative
app.post('/api/ads', async (req: Request, res: Response) => {
  try {
    if (!metaAdsManager) {
      return res.status(400).json({
        error: 'Meta SDK not configured'
      });
    }

    const { name, adSetId, creativeId, status } = req.body;

    const adId = await metaAdsManager.createAd({
      name,
      adSetId,
      creativeId,
      status
    });

    res.json({
      status: 'success',
      ad_id: adId,
      message: 'Ad created successfully'
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Agent 14: Get Ad Insights
app.get('/api/insights/ad/:adId', async (req: Request, res: Response) => {
  try {
    if (!metaAdsManager) {
      return res.status(400).json({
        error: 'Meta SDK not configured'
      });
    }

    const { adId } = req.params;
    const { datePreset = 'last_7d' } = req.query;

    const insights = await metaAdsManager.getAdInsights(
      adId,
      datePreset as string
    );

    res.json({
      status: 'success',
      insights
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Agent 14: Get Campaign Insights
app.get('/api/insights/campaign/:campaignId', async (req: Request, res: Response) => {
  try {
    if (!metaAdsManager) {
      return res.status(400).json({
        error: 'Meta SDK not configured'
      });
    }

    const { campaignId } = req.params;
    const { datePreset = 'last_7d' } = req.query;

    const insights = await metaAdsManager.getCampaignInsights(
      campaignId,
      datePreset as string
    );

    res.json({
      status: 'success',
      insights
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Agent 14: Get AdSet Insights
app.get('/api/insights/adset/:adSetId', async (req: Request, res: Response) => {
  try {
    if (!metaAdsManager) {
      return res.status(400).json({
        error: 'Meta SDK not configured'
      });
    }

    const { adSetId } = req.params;
    const { datePreset = 'last_7d' } = req.query;

    const insights = await metaAdsManager.getAdSetInsights(
      adSetId,
      datePreset as string
    );

    res.json({
      status: 'success',
      insights
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Update Ad Status
app.patch('/api/ads/:adId/status', async (req: Request, res: Response) => {
  try {
    if (!metaAdsManager) {
      return res.status(400).json({
        error: 'Meta SDK not configured'
      });
    }

    const { adId } = req.params;
    const { status } = req.body;

    await metaAdsManager.updateAdStatus(adId, status);

    res.json({
      status: 'success',
      message: `Ad ${adId} status updated to ${status}`
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Update AdSet Budget
app.patch('/api/adsets/:adSetId/budget', async (req: Request, res: Response) => {
  try {
    if (!metaAdsManager) {
      return res.status(400).json({
        error: 'Meta SDK not configured'
      });
    }

    const { adSetId } = req.params;
    const { dailyBudget } = req.body;

    await metaAdsManager.updateAdSetBudget(adSetId, dailyBudget);

    res.json({
      status: 'success',
      message: `AdSet ${adSetId} budget updated`
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Get Account Info
app.get('/api/account/info', async (req: Request, res: Response) => {
  try {
    if (!metaAdsManager) {
      return res.status(400).json({
        error: 'Meta SDK not configured'
      });
    }

    const info = await metaAdsManager.getAccountInfo();

    res.json({
      status: 'success',
      account: info
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Publish to Meta
app.post('/publish/meta', async (req: Request, res: Response) => {
  try {
    const {
      videoUrl,
      fileHash,
      adSetId,
      pageId
    } = req.body;

    const placements = req.body.placements || ['instagram_reels', 'facebook_reels'];

    // Dry-run mode if no access token
    if (!META_ACCESS_TOKEN) {
      return res.json({
        status: 'dry_run',
        message: 'No META_ACCESS_TOKEN provided - dry run mode',
        would_create: {
          creative_id: 'dry_run_creative_123',
          ad_id: 'dry_run_ad_456',
          status: 'PAUSED'
        },
        input: req.body
      });
    }

    // Validate API base URL
    if (!validateMetaApiUrl(META_API_BASE)) {
      throw new Error('Invalid Meta API base URL');
    }

    // Step 1: Create Ad Creative
    const creativeResponse = await axios.post(
      `${META_API_BASE}/${pageId}/adcreatives`,
      {
        name: `Remix Creative ${new Date().toISOString()}`,
        object_story_spec: {
          page_id: pageId,
          video_data: {
            video_id: fileHash || videoUrl,
            call_to_action: {
              type: 'LEARN_MORE',
              value: {
                link: 'https://example.com'
              }
            }
          }
        }
      },
      {
        params: { access_token: META_ACCESS_TOKEN }
      }
    );

    const creativeId = creativeResponse.data.id;

    // Step 2: Create Ad (PAUSED)
    const adResponse = await axios.post(
      `${META_API_BASE}/${adSetId}/ads`,
      {
        name: `Remix Ad ${new Date().toISOString()}`,
        adset_id: adSetId,
        creative: { creative_id: creativeId },
        status: 'PAUSED'
      },
      {
        params: { access_token: META_ACCESS_TOKEN }
      }
    );

    const adId = adResponse.data.id;

    res.json({
      status: 'success',
      creative_id: creativeId,
      ad_id: adId,
      ad_status: 'PAUSED',
      message: 'Ad created successfully (PAUSED)'
    });

  } catch (error: any) {
    console.error('Error publishing to Meta:', error.response?.data || error.message);
    res.status(500).json({
      error: error.response?.data?.error?.message || error.message,
      details: error.response?.data
    });
  }
});

// Get Insights
app.get('/insights', async (req: Request, res: Response) => {
  try {
    const { adId, datePreset = 'last_7d' } = req.query;

    if (!adId) {
      return res.status(400).json({ error: 'adId is required' });
    }

    // Dry-run mode
    if (!META_ACCESS_TOKEN) {
      return res.json({
        status: 'dry_run',
        message: 'No META_ACCESS_TOKEN provided - dry run mode',
        mock_data: {
          ad_id: adId,
          impressions: 1000,
          clicks: 50,
          ctr: 0.05,
          spend: 25.50,
          actions: [
            { action_type: 'link_click', value: 45 },
            { action_type: 'video_view', value: 800 }
          ],
          video_metrics: {
            video_30_sec_watched_actions: 600,
            video_avg_time_watched_actions: 8.5
          }
        }
      });
    }

    // Validate API base URL
    if (!validateMetaApiUrl(META_API_BASE)) {
      throw new Error('Invalid Meta API base URL');
    }

    const response = await axios.get(
      `${META_API_BASE}/${adId}/insights`,
      {
        params: {
          access_token: META_ACCESS_TOKEN,
          date_preset: datePreset,
          fields: 'impressions,clicks,ctr,spend,actions,video_30_sec_watched_actions,video_avg_time_watched_actions'
        }
      }
    );

    const insights = response.data.data[0] || {};

    // Normalize metrics
    const normalizedInsights = {
      ad_id: adId,
      impressions: parseInt(insights.impressions || '0'),
      clicks: parseInt(insights.clicks || '0'),
      ctr: parseFloat(insights.ctr || '0'),
      spend: parseFloat(insights.spend || '0'),
      actions: insights.actions || [],
      video_metrics: {
        video_30_sec_watched: insights.video_30_sec_watched_actions?.[0]?.value || 0,
        video_avg_time_watched: insights.video_avg_time_watched_actions?.[0]?.value || 0
      }
    };

    res.json(normalizedInsights);

  } catch (error: any) {
    console.error('Error fetching insights:', error.response?.data || error.message);
    res.status(500).json({
      error: error.response?.data?.error?.message || error.message
    });
  }
});

// Dashboard: Get Creatives Performance
app.get('/api/creatives', async (req: Request, res: Response) => {
  try {
    // Mock data for dashboard visualization
    const mockCreatives = Array.from({ length: 10 }).map((_, i) => ({
      creativeId: `c_${i}`,
      name: `Creative ${i + 1}`,
      platform: 'Meta',
      campaign: `Campaign ${String.fromCharCode(65 + i)}`,
      impressions: 1000 + i * 100,
      clicks: 50 + i * 5,
      conversions: 5 + i,
      spend: 100 + i * 10,
      revenue: 200 + i * 20,
      ctr: 0.05,
      cvr: 0.1,
      cpa: 20,
      roas: 2.0
    }));
    res.json(mockCreatives);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Dashboard: Get Timeseries Data
app.get('/api/timeseries', async (req: Request, res: Response) => {
  try {
    // Mock timeseries data
    const now = Date.now();
    const day = 24 * 60 * 60 * 1000;
    const mockSeries = Array.from({ length: 30 }).map((_, i) => ({
      ts: now - (29 - i) * day,
      value: 100 + Math.random() * 50
    }));
    res.json(mockSeries);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Link insights to predictions
app.post('/insights/link-prediction', async (req: Request, res: Response) => {
  try {
    const { predictionId, adId, insights } = req.body;

    // Calculate actual CTR
    const actualCTR = insights.clicks / insights.impressions;

    // In a full implementation, would update the prediction log
    // For now, return the linkage info
    res.json({
      status: 'linked',
      prediction_id: predictionId,
      ad_id: adId,
      actual_ctr: actualCTR,
      message: 'Insights linked to prediction (stub implementation)'
    });

  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Health check
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    meta_configured: !!META_ACCESS_TOKEN
  });
});

app.listen(PORT, () => {
  console.log(`Meta Publisher listening on port ${PORT}`);
  if (!META_ACCESS_TOKEN) {
    console.log('Warning: Running in dry-run mode (no META_ACCESS_TOKEN)');
  }
});

export default app;
