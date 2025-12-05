/**
 * Google Ads Publisher Service - Campaign Creation & Performance Tracking
 * Agent 13: Real Google Ads API Integration
 */
import express, { Request, Response } from 'express';
import cors from 'cors';
import { GoogleAdsManager } from './google/google-ads-manager';

const app = express();
const PORT = process.env.PORT || 8084;

// CORS configuration for production
const ALLOWED_ORIGINS = process.env.ALLOWED_ORIGINS
  ? process.env.ALLOWED_ORIGINS.split(',')
  : [
      'http://localhost:3000',
      'http://localhost:5173',
      'http://localhost:5174',
      'https://geminivideo.vercel.app',
      'https://geminivideo.netlify.app'
    ];

const corsOptions = {
  origin: (origin: string | undefined, callback: (err: Error | null, allow?: boolean) => void) => {
    // Allow requests with no origin (like mobile apps, curl, or server-to-server)
    if (!origin) {
      callback(null, true);
      return;
    }
    if (ALLOWED_ORIGINS.includes(origin)) {
      callback(null, true);
    } else {
      console.warn(`CORS blocked origin: ${origin}`);
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
};

// Middleware
app.use(cors(corsOptions));
app.options('*', cors(corsOptions)); // Handle preflight requests
app.use(express.json());

// Google Ads API configuration
const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID || '';
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET || '';
const GOOGLE_DEVELOPER_TOKEN = process.env.GOOGLE_DEVELOPER_TOKEN || '';
const GOOGLE_REFRESH_TOKEN = process.env.GOOGLE_REFRESH_TOKEN || '';
const GOOGLE_ADS_CUSTOMER_ID = process.env.GOOGLE_ADS_CUSTOMER_ID || '';

// Initialize Google Ads Manager if credentials are available
let googleAdsManager: GoogleAdsManager | null = null;
if (GOOGLE_CLIENT_ID && GOOGLE_CLIENT_SECRET && GOOGLE_DEVELOPER_TOKEN && GOOGLE_REFRESH_TOKEN && GOOGLE_ADS_CUSTOMER_ID) {
  googleAdsManager = new GoogleAdsManager({
    clientId: GOOGLE_CLIENT_ID,
    clientSecret: GOOGLE_CLIENT_SECRET,
    developerToken: GOOGLE_DEVELOPER_TOKEN,
    refreshToken: GOOGLE_REFRESH_TOKEN,
    customerId: GOOGLE_ADS_CUSTOMER_ID
  });
  console.log('Google Ads Manager initialized with real Google Ads API');
} else {
  console.log('Warning: Google Ads credentials not configured - running in dry-run mode');
  console.log('Required env vars: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_DEVELOPER_TOKEN, GOOGLE_REFRESH_TOKEN, GOOGLE_ADS_CUSTOMER_ID');
}

// Root endpoint
app.get('/', (req: Request, res: Response) => {
  res.json({
    service: 'google-ads',
    status: 'running',
    version: '1.0.0',
    real_sdk_enabled: !!googleAdsManager,
    dry_run_mode: !GOOGLE_CLIENT_ID,
    endpoints: {
      campaigns: '/api/campaigns',
      ad_groups: '/api/ad-groups',
      ads: '/api/ads',
      video_ads: '/api/video-ads',
      upload_creative: '/api/upload-creative',
      performance: '/api/performance',
      publish: '/api/publish'
    }
  });
});

// Agent 13: Create Campaign
app.post('/api/campaigns', async (req: Request, res: Response) => {
  try {
    if (!googleAdsManager) {
      return res.status(400).json({
        error: 'Google Ads SDK not configured',
        message: 'Set Google Ads credentials (GOOGLE_CLIENT_ID, etc.)'
      });
    }

    const { name, budget, biddingStrategy, startDate, endDate, status } = req.body;

    if (!name || !budget) {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'name and budget are required'
      });
    }

    const campaignId = await googleAdsManager.createCampaign({
      name,
      budget,
      biddingStrategy,
      startDate,
      endDate,
      status
    });

    res.json({
      status: 'success',
      campaign_id: campaignId,
      message: 'Campaign created successfully'
    });
  } catch (error: any) {
    console.error('Error creating campaign:', error);
    res.status(500).json({ error: error.message });
  }
});

// Agent 13: Create Ad Group
app.post('/api/ad-groups', async (req: Request, res: Response) => {
  try {
    if (!googleAdsManager) {
      return res.status(400).json({
        error: 'Google Ads SDK not configured'
      });
    }

    const { name, campaignId, cpcBidMicros, status } = req.body;

    if (!name || !campaignId || !cpcBidMicros) {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'name, campaignId, and cpcBidMicros are required'
      });
    }

    const adGroupId = await googleAdsManager.createAdGroup({
      name,
      campaignId,
      cpcBidMicros,
      status
    });

    res.json({
      status: 'success',
      ad_group_id: adGroupId,
      message: 'Ad Group created successfully'
    });
  } catch (error: any) {
    console.error('Error creating ad group:', error);
    res.status(500).json({ error: error.message });
  }
});

// Agent 13: Upload Video Creative
app.post('/api/upload-creative', async (req: Request, res: Response) => {
  try {
    if (!googleAdsManager) {
      return res.status(400).json({
        error: 'Google Ads SDK not configured'
      });
    }

    const { videoPath, title, description } = req.body;

    if (!videoPath) {
      return res.status(400).json({
        error: 'Missing required field',
        message: 'videoPath is required'
      });
    }

    // Upload to YouTube (required for Google Ads video ads)
    const videoId = await googleAdsManager.uploadVideoToYouTube(
      videoPath,
      title || 'Ad Video',
      description || 'Advertisement'
    );

    res.json({
      status: 'success',
      video_id: videoId,
      youtube_url: `https://www.youtube.com/watch?v=${videoId}`,
      message: 'Video uploaded to YouTube successfully'
    });
  } catch (error: any) {
    console.error('Error uploading creative:', error);
    res.status(500).json({ error: error.message });
  }
});

// Agent 13: Upload Image/Video Asset
app.post('/api/assets/upload', async (req: Request, res: Response) => {
  try {
    if (!googleAdsManager) {
      return res.status(400).json({
        error: 'Google Ads SDK not configured'
      });
    }

    const { filePath, assetType } = req.body;

    if (!filePath || !assetType) {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'filePath and assetType (IMAGE or VIDEO) are required'
      });
    }

    if (!['IMAGE', 'VIDEO'].includes(assetType)) {
      return res.status(400).json({
        error: 'Invalid assetType',
        message: 'assetType must be either IMAGE or VIDEO'
      });
    }

    const assetId = await googleAdsManager.uploadAsset(filePath, assetType);

    res.json({
      status: 'success',
      asset_id: assetId,
      asset_type: assetType,
      message: 'Asset uploaded successfully'
    });
  } catch (error: any) {
    console.error('Error uploading asset:', error);
    res.status(500).json({ error: error.message });
  }
});

// Agent 13: Create Video Ad (Complete Workflow)
app.post('/api/video-ads', async (req: Request, res: Response) => {
  try {
    if (!googleAdsManager) {
      return res.status(400).json({
        error: 'Google Ads SDK not configured'
      });
    }

    const {
      videoPath,
      campaignId,
      adGroupId,
      headline,
      description,
      finalUrl
    } = req.body;

    if (!videoPath || !campaignId || !adGroupId || !headline || !finalUrl) {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'videoPath, campaignId, adGroupId, headline, and finalUrl are required'
      });
    }

    const result = await googleAdsManager.createVideoAdComplete(
      videoPath,
      campaignId,
      adGroupId,
      headline,
      description || '',
      finalUrl
    );

    res.json({
      status: 'success',
      ad_id: result.adId,
      video_id: result.videoId,
      youtube_url: `https://www.youtube.com/watch?v=${result.videoId}`,
      message: 'Video ad created successfully'
    });
  } catch (error: any) {
    console.error('Error creating video ad:', error);
    res.status(500).json({ error: error.message });
  }
});

// Agent 13: Create Video Ad from existing YouTube video
app.post('/api/ads', async (req: Request, res: Response) => {
  try {
    if (!googleAdsManager) {
      return res.status(400).json({
        error: 'Google Ads SDK not configured'
      });
    }

    const { name, adGroupId, videoId, headline, description, callToAction, finalUrl } = req.body;

    if (!name || !adGroupId || !videoId || !headline || !finalUrl) {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'name, adGroupId, videoId, headline, and finalUrl are required'
      });
    }

    const adId = await googleAdsManager.createVideoAd({
      name,
      adGroupId,
      videoId,
      headline,
      description: description || '',
      callToAction,
      finalUrl
    });

    res.json({
      status: 'success',
      ad_id: adId,
      message: 'Ad created successfully'
    });
  } catch (error: any) {
    console.error('Error creating ad:', error);
    res.status(500).json({ error: error.message });
  }
});

// Agent 13: Get Campaign Performance
app.get('/api/performance/campaign/:campaignId', async (req: Request, res: Response) => {
  try {
    if (!googleAdsManager) {
      return res.status(400).json({
        error: 'Google Ads SDK not configured'
      });
    }

    const { campaignId } = req.params;
    const { startDate, endDate } = req.query;

    const dateRange = startDate && endDate ? {
      startDate: startDate as string,
      endDate: endDate as string
    } : undefined;

    const performance = await googleAdsManager.getCampaignPerformance(
      campaignId,
      dateRange
    );

    res.json({
      status: 'success',
      campaign_id: campaignId,
      performance,
      date_range: dateRange || 'last_7_days'
    });
  } catch (error: any) {
    console.error('Error getting campaign performance:', error);
    res.status(500).json({ error: error.message });
  }
});

// Agent 13: Get Ad Performance
app.get('/api/performance/ad/:adId', async (req: Request, res: Response) => {
  try {
    if (!googleAdsManager) {
      return res.status(400).json({
        error: 'Google Ads SDK not configured'
      });
    }

    const { adId } = req.params;
    const { startDate, endDate } = req.query;

    const dateRange = startDate && endDate ? {
      startDate: startDate as string,
      endDate: endDate as string
    } : undefined;

    const performance = await googleAdsManager.getAdPerformance(
      adId,
      dateRange
    );

    res.json({
      status: 'success',
      ad_id: adId,
      performance,
      date_range: dateRange || 'last_7_days'
    });
  } catch (error: any) {
    console.error('Error getting ad performance:', error);
    res.status(500).json({ error: error.message });
  }
});

// Agent 13: Get Ad Group Performance
app.get('/api/performance/ad-group/:adGroupId', async (req: Request, res: Response) => {
  try {
    if (!googleAdsManager) {
      return res.status(400).json({
        error: 'Google Ads SDK not configured'
      });
    }

    const { adGroupId } = req.params;
    const { startDate, endDate } = req.query;

    const dateRange = startDate && endDate ? {
      startDate: startDate as string,
      endDate: endDate as string
    } : undefined;

    const performance = await googleAdsManager.getAdGroupPerformance(
      adGroupId,
      dateRange
    );

    res.json({
      status: 'success',
      ad_group_id: adGroupId,
      performance,
      date_range: dateRange || 'last_7_days'
    });
  } catch (error: any) {
    console.error('Error getting ad group performance:', error);
    res.status(500).json({ error: error.message });
  }
});

// Update Ad Status
app.patch('/api/ads/:adId/status', async (req: Request, res: Response) => {
  try {
    if (!googleAdsManager) {
      return res.status(400).json({
        error: 'Google Ads SDK not configured'
      });
    }

    const { adId } = req.params;
    const { status } = req.body;

    if (!['ENABLED', 'PAUSED'].includes(status)) {
      return res.status(400).json({
        error: 'Invalid status',
        message: 'status must be either ENABLED or PAUSED'
      });
    }

    await googleAdsManager.updateAdStatus(adId, status);

    res.json({
      status: 'success',
      message: `Ad ${adId} status updated to ${status}`
    });
  } catch (error: any) {
    console.error('Error updating ad status:', error);
    res.status(500).json({ error: error.message });
  }
});

// Update Campaign Budget
app.patch('/api/campaigns/:campaignId/budget', async (req: Request, res: Response) => {
  try {
    if (!googleAdsManager) {
      return res.status(400).json({
        error: 'Google Ads SDK not configured'
      });
    }

    const { campaignId } = req.params;
    const { budget } = req.body;

    if (!budget || budget <= 0) {
      return res.status(400).json({
        error: 'Invalid budget',
        message: 'budget must be a positive number'
      });
    }

    await googleAdsManager.updateCampaignBudget(campaignId, budget);

    res.json({
      status: 'success',
      message: `Campaign ${campaignId} budget updated to ${budget}`
    });
  } catch (error: any) {
    console.error('Error updating campaign budget:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get Account Info
app.get('/api/account/info', async (req: Request, res: Response) => {
  try {
    if (!googleAdsManager) {
      return res.status(400).json({
        error: 'Google Ads SDK not configured'
      });
    }

    const info = await googleAdsManager.getAccountInfo();

    res.json({
      status: 'success',
      account: info
    });
  } catch (error: any) {
    console.error('Error getting account info:', error);
    res.status(500).json({ error: error.message });
  }
});

// Publish to Google Ads (Complete workflow endpoint)
app.post('/api/publish', async (req: Request, res: Response) => {
  try {
    const {
      videoPath,
      campaignName,
      budget,
      adGroupName,
      cpcBidMicros,
      headline,
      description,
      finalUrl
    } = req.body;

    // Dry-run mode if no credentials
    if (!googleAdsManager) {
      return res.json({
        status: 'dry_run',
        message: 'No Google Ads credentials provided - dry run mode',
        would_create: {
          campaign_id: 'dry_run_campaign_123',
          ad_group_id: 'dry_run_ad_group_456',
          ad_id: 'dry_run_ad_789',
          status: 'PAUSED'
        },
        input: req.body
      });
    }

    // Validate required fields
    if (!videoPath || !campaignName || !budget || !adGroupName || !cpcBidMicros || !headline || !finalUrl) {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'videoPath, campaignName, budget, adGroupName, cpcBidMicros, headline, and finalUrl are required'
      });
    }

    // Step 1: Create Campaign
    const campaignId = await googleAdsManager.createCampaign({
      name: campaignName,
      budget,
      status: 'PAUSED'
    });

    // Step 2: Create Ad Group
    const adGroupId = await googleAdsManager.createAdGroup({
      name: adGroupName,
      campaignId,
      cpcBidMicros,
      status: 'PAUSED'
    });

    // Step 3: Upload video and create ad
    const result = await googleAdsManager.createVideoAdComplete(
      videoPath,
      campaignId,
      adGroupId,
      headline,
      description || '',
      finalUrl
    );

    res.json({
      status: 'success',
      campaign_id: campaignId,
      ad_group_id: adGroupId,
      ad_id: result.adId,
      video_id: result.videoId,
      youtube_url: `https://www.youtube.com/watch?v=${result.videoId}`,
      ad_status: 'PAUSED',
      message: 'Ad created successfully (PAUSED)'
    });

  } catch (error: any) {
    console.error('Error publishing to Google Ads:', error);
    res.status(500).json({
      error: error.message,
      details: error.response?.data
    });
  }
});

// Health check
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    google_ads_configured: !!googleAdsManager
  });
});

app.listen(PORT, () => {
  console.log(`Google Ads Publisher listening on port ${PORT}`);
  if (!googleAdsManager) {
    console.log('Warning: Running in dry-run mode (no Google Ads credentials)');
  }
});

export default app;
