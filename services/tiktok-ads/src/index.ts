/**
 * TikTok Ads Publisher Service - Placeholder for Future Implementation
 * Agent 19: Multi-Platform Publishing Infrastructure
 *
 * This is a placeholder service structure for TikTok Ads integration.
 * Currently returns mock success responses for development.
 * Production implementation would integrate with TikTok Business API.
 */

import express, { Request, Response } from 'express';
import cors from 'cors';
import { v4 as uuidv4 } from 'uuid';

const app = express();
const PORT = process.env.PORT || 8085;

// CORS configuration for production
const ALLOWED_ORIGINS = process.env.ALLOWED_ORIGINS
  ? process.env.ALLOWED_ORIGINS.split(',')
  : [
      'http://localhost:3000',
      'http://localhost:5173',
      'http://localhost:5174',
      'http://localhost:8000',
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
app.options('*', cors(corsOptions));
app.use(express.json());

// TikTok API configuration (placeholder)
const TIKTOK_ACCESS_TOKEN = process.env.TIKTOK_ACCESS_TOKEN || '';
const TIKTOK_ADVERTISER_ID = process.env.TIKTOK_ADVERTISER_ID || '';

// Root endpoint
app.get('/', (req: Request, res: Response) => {
  res.json({
    service: 'tiktok-ads',
    status: 'running',
    version: '1.0.0-placeholder',
    real_sdk_enabled: false,
    placeholder_mode: true,
    message: 'This is a placeholder service for TikTok Ads API integration',
    endpoints: {
      campaigns: '/api/campaigns',
      ad_groups: '/api/ad-groups',
      ads: '/api/ads',
      video_ads: '/api/video-ads',
      performance: '/api/performance',
      publish: '/api/publish'
    },
    documentation: {
      tiktok_business_api: 'https://business-api.tiktok.com/portal/docs',
      integration_guide: 'https://ads.tiktok.com/marketing_api/docs'
    }
  });
});

// Health check
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    tiktok_configured: !!TIKTOK_ACCESS_TOKEN,
    placeholder_mode: true
  });
});

// Create Campaign (Placeholder)
app.post('/api/campaigns', async (req: Request, res: Response) => {
  try {
    const { name, objective, budget, status } = req.body;

    console.log('[TIKTOK PLACEHOLDER] Create campaign:', { name, objective, budget, status });

    // Return mock success response
    const campaignId = `tiktok_campaign_${uuidv4()}`;

    res.json({
      status: 'success',
      campaign_id: campaignId,
      message: 'Campaign created successfully (placeholder)',
      placeholder: true,
      note: 'This is a mock response. Real TikTok API integration pending.'
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Create Ad Group (Placeholder)
app.post('/api/ad-groups', async (req: Request, res: Response) => {
  try {
    const { name, campaignId, budget, targeting } = req.body;

    console.log('[TIKTOK PLACEHOLDER] Create ad group:', { name, campaignId, budget });

    const adGroupId = `tiktok_adgroup_${uuidv4()}`;

    res.json({
      status: 'success',
      ad_group_id: adGroupId,
      campaign_id: campaignId,
      message: 'Ad group created successfully (placeholder)',
      placeholder: true
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Upload Video (Placeholder)
app.post('/api/videos/upload', async (req: Request, res: Response) => {
  try {
    const { videoPath, title } = req.body;

    console.log('[TIKTOK PLACEHOLDER] Upload video:', { videoPath, title });

    const videoId = `tiktok_video_${uuidv4()}`;

    res.json({
      status: 'success',
      video_id: videoId,
      message: 'Video uploaded successfully (placeholder)',
      placeholder: true
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Create Ad (Placeholder)
app.post('/api/ads', async (req: Request, res: Response) => {
  try {
    const { name, adGroupId, videoId, text, callToAction } = req.body;

    console.log('[TIKTOK PLACEHOLDER] Create ad:', { name, adGroupId, videoId });

    const adId = `tiktok_ad_${uuidv4()}`;

    res.json({
      status: 'success',
      ad_id: adId,
      ad_group_id: adGroupId,
      message: 'Ad created successfully (placeholder)',
      placeholder: true
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Create Video Ad - Complete Workflow (Placeholder)
app.post('/api/video-ads', async (req: Request, res: Response) => {
  try {
    const {
      videoPath,
      campaignId,
      adGroupId,
      text,
      callToAction
    } = req.body;

    console.log('[TIKTOK PLACEHOLDER] Create video ad complete:', {
      videoPath,
      campaignId,
      adGroupId
    });

    const videoId = `tiktok_video_${uuidv4()}`;
    const adId = `tiktok_ad_${uuidv4()}`;

    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    res.json({
      status: 'success',
      ad_id: adId,
      video_id: videoId,
      message: 'Video ad created successfully (placeholder)',
      placeholder: true,
      note: 'Real TikTok API would upload video and create ad'
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Get Campaign Performance (Placeholder)
app.get('/api/performance/campaign/:campaignId', async (req: Request, res: Response) => {
  try {
    const { campaignId } = req.params;
    const { startDate, endDate } = req.query;

    console.log('[TIKTOK PLACEHOLDER] Get campaign performance:', {
      campaignId,
      startDate,
      endDate
    });

    // Return mock performance data
    res.json({
      status: 'success',
      campaign_id: campaignId,
      performance: {
        impressions: Math.floor(Math.random() * 100000) + 50000,
        clicks: Math.floor(Math.random() * 5000) + 1000,
        spend: parseFloat((Math.random() * 1000 + 500).toFixed(2)),
        conversions: Math.floor(Math.random() * 100) + 20,
        ctr: parseFloat((Math.random() * 0.05 + 0.02).toFixed(4)),
        cpc: parseFloat((Math.random() * 2 + 0.5).toFixed(2)),
        cpa: parseFloat((Math.random() * 30 + 10).toFixed(2)),
        roas: parseFloat((Math.random() * 3 + 1).toFixed(2))
      },
      date_range: { startDate, endDate },
      placeholder: true,
      note: 'This is mock data for development'
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Get Ad Performance (Placeholder)
app.get('/api/performance/ad/:adId', async (req: Request, res: Response) => {
  try {
    const { adId } = req.params;
    const { startDate, endDate } = req.query;

    console.log('[TIKTOK PLACEHOLDER] Get ad performance:', { adId, startDate, endDate });

    res.json({
      status: 'success',
      ad_id: adId,
      performance: {
        impressions: Math.floor(Math.random() * 50000) + 10000,
        clicks: Math.floor(Math.random() * 2000) + 500,
        spend: parseFloat((Math.random() * 500 + 100).toFixed(2)),
        conversions: Math.floor(Math.random() * 50) + 10,
        ctr: parseFloat((Math.random() * 0.05 + 0.02).toFixed(4)),
        video_views: Math.floor(Math.random() * 30000) + 5000,
        video_completion_rate: parseFloat((Math.random() * 0.4 + 0.3).toFixed(4))
      },
      date_range: { startDate, endDate },
      placeholder: true
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Update Ad Status (Placeholder)
app.patch('/api/ads/:adId/status', async (req: Request, res: Response) => {
  try {
    const { adId } = req.params;
    const { status } = req.body;

    console.log('[TIKTOK PLACEHOLDER] Update ad status:', { adId, status });

    res.json({
      status: 'success',
      ad_id: adId,
      new_status: status,
      message: `Ad ${adId} status updated to ${status} (placeholder)`,
      placeholder: true
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Update Campaign Budget (Placeholder)
app.patch('/api/campaigns/:campaignId/budget', async (req: Request, res: Response) => {
  try {
    const { campaignId } = req.params;
    const { budget } = req.body;

    console.log('[TIKTOK PLACEHOLDER] Update campaign budget:', { campaignId, budget });

    res.json({
      status: 'success',
      campaign_id: campaignId,
      new_budget: budget,
      message: `Campaign ${campaignId} budget updated to ${budget} (placeholder)`,
      placeholder: true
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Get Account Info (Placeholder)
app.get('/api/account/info', async (req: Request, res: Response) => {
  try {
    console.log('[TIKTOK PLACEHOLDER] Get account info');

    res.json({
      status: 'success',
      account: {
        advertiser_id: TIKTOK_ADVERTISER_ID || 'placeholder_advertiser_123',
        name: 'Placeholder TikTok Advertiser',
        currency: 'USD',
        timezone: 'America/New_York',
        status: 'ACTIVE',
        balance: 10000.00
      },
      placeholder: true
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Publish - Complete Workflow (Placeholder)
app.post('/api/publish', async (req: Request, res: Response) => {
  try {
    const {
      videoPath,
      campaignName,
      budget,
      objective,
      targeting,
      adGroupName,
      text,
      callToAction
    } = req.body;

    console.log('[TIKTOK PLACEHOLDER] Publish workflow:', {
      campaignName,
      budget,
      objective
    });

    // Simulate multi-step workflow
    const campaignId = `tiktok_campaign_${uuidv4()}`;
    const adGroupId = `tiktok_adgroup_${uuidv4()}`;
    const videoId = `tiktok_video_${uuidv4()}`;
    const adId = `tiktok_ad_${uuidv4()}`;

    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 2000));

    res.json({
      status: 'success',
      campaign_id: campaignId,
      ad_group_id: adGroupId,
      video_id: videoId,
      ad_id: adId,
      ad_status: 'PAUSED',
      message: 'Campaign published successfully (placeholder)',
      placeholder: true,
      note: 'Real TikTok API would create campaign, ad group, upload video, and create ad',
      workflow: {
        step1: 'Create campaign',
        step2: 'Create ad group',
        step3: 'Upload video',
        step4: 'Create ad'
      }
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`TikTok Ads Publisher (Placeholder) listening on port ${PORT}`);
  console.log('⚠️  Running in PLACEHOLDER mode - returns mock responses');
  console.log('📝 For production: Integrate with TikTok Business API');
  console.log('🔗 Docs: https://business-api.tiktok.com/portal/docs');

  if (!TIKTOK_ACCESS_TOKEN) {
    console.log('ℹ️  Set TIKTOK_ACCESS_TOKEN for real API integration');
  }
});

export default app;
