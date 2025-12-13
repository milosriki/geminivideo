/**
 * TikTok Ads Publisher Service - Production Implementation
 * =========================================================
 *
 * Real TikTok Business API integration.
 * Returns clear errors when not configured - NO MOCK DATA.
 *
 * Configuration Required:
 * - TIKTOK_ACCESS_TOKEN: OAuth access token from TikTok Business Center
 * - TIKTOK_ADVERTISER_ID: Your advertiser account ID
 *
 * API Documentation: https://business-api.tiktok.com/portal/docs
 *
 * Agent 19: Multi-Platform Publishing Infrastructure
 */

import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import axios, { AxiosInstance, AxiosError } from 'axios';
import FormData from 'form-data';
import * as fs from 'fs';
import * as path from 'path';

const app = express();
const PORT = process.env.PORT || 8085;

// TikTok API Configuration
const TIKTOK_API_BASE = 'https://business-api.tiktok.com/open_api/v1.3';
const TIKTOK_ACCESS_TOKEN = process.env.TIKTOK_ACCESS_TOKEN || '';
const TIKTOK_ADVERTISER_ID = process.env.TIKTOK_ADVERTISER_ID || '';

// Validate configuration on startup
const IS_CONFIGURED = Boolean(TIKTOK_ACCESS_TOKEN && TIKTOK_ADVERTISER_ID);

// CORS configuration
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

// Create axios instance for TikTok API
const tiktokClient: AxiosInstance = axios.create({
  baseURL: TIKTOK_API_BASE,
  headers: {
    'Access-Token': TIKTOK_ACCESS_TOKEN,
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Error response interface
interface TikTokError {
  code: number;
  message: string;
  request_id?: string;
}

// Configuration check middleware - returns clear error if not configured
function requireConfiguration(req: Request, res: Response, next: NextFunction): void {
  if (!IS_CONFIGURED) {
    res.status(503).json({
      error: 'TikTok API not configured',
      code: 'TIKTOK_NOT_CONFIGURED',
      message: 'TikTok Business API credentials are not set. Please configure TIKTOK_ACCESS_TOKEN and TIKTOK_ADVERTISER_ID environment variables.',
      documentation: 'https://business-api.tiktok.com/portal/docs',
      setup_steps: [
        '1. Create a TikTok Business Center account',
        '2. Register your app in the Developer Portal',
        '3. Generate an access token',
        '4. Set TIKTOK_ACCESS_TOKEN and TIKTOK_ADVERTISER_ID environment variables',
        '5. Restart this service'
      ]
    });
    return;
  }
  next();
}

// Handle TikTok API errors
function handleTikTokError(error: AxiosError, res: Response): void {
  const status = error.response?.status || 500;
  const data = error.response?.data as any;

  console.error('[TikTok API Error]', {
    status,
    code: data?.code,
    message: data?.message,
    request_id: data?.request_id,
  });

  res.status(status).json({
    error: 'TikTok API error',
    code: data?.code || 'UNKNOWN_ERROR',
    message: data?.message || error.message,
    request_id: data?.request_id,
    details: data?.data || null
  });
}

// Root endpoint
app.get('/', (req: Request, res: Response) => {
  res.json({
    service: 'tiktok-ads',
    status: IS_CONFIGURED ? 'ready' : 'not_configured',
    version: '2.0.0',
    configured: IS_CONFIGURED,
    advertiser_id: TIKTOK_ADVERTISER_ID ? `${TIKTOK_ADVERTISER_ID.slice(0, 4)}****` : null,
    endpoints: IS_CONFIGURED ? {
      campaigns: '/api/campaigns',
      ad_groups: '/api/ad-groups',
      ads: '/api/ads',
      video_upload: '/api/videos/upload',
      publish: '/api/publish',
      performance: '/api/performance/:campaignId'
    } : null,
    message: IS_CONFIGURED
      ? 'TikTok Ads API ready for production use'
      : 'TikTok API not configured. Set TIKTOK_ACCESS_TOKEN and TIKTOK_ADVERTISER_ID.',
    documentation: 'https://business-api.tiktok.com/portal/docs'
  });
});

// Health check
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: IS_CONFIGURED ? 'healthy' : 'degraded',
    timestamp: new Date().toISOString(),
    configured: IS_CONFIGURED,
    reason: IS_CONFIGURED ? null : 'TikTok API credentials not configured'
  });
});

// ============================================================================
// CAMPAIGN MANAGEMENT
// ============================================================================

// Create Campaign
app.post('/api/campaigns', requireConfiguration, async (req: Request, res: Response) => {
  try {
    const { name, objective, budget, budget_mode = 'BUDGET_MODE_DAY' } = req.body;

    if (!name || !objective || !budget) {
      return res.status(400).json({
        error: 'Missing required fields',
        required: ['name', 'objective', 'budget'],
        received: req.body
      });
    }

    console.log('[TikTok] Creating campaign:', { name, objective, budget });

    const response = await tiktokClient.post('/campaign/create/', {
      advertiser_id: TIKTOK_ADVERTISER_ID,
      campaign_name: name,
      objective_type: objective, // TRAFFIC, CONVERSIONS, APP_INSTALLS, REACH, VIDEO_VIEWS
      budget_mode,
      budget: budget * 100, // TikTok uses cents
    });

    if (response.data.code !== 0) {
      return res.status(400).json({
        error: 'TikTok API error',
        code: response.data.code,
        message: response.data.message,
        request_id: response.data.request_id
      });
    }

    const campaignId = response.data.data.campaign_id;
    console.log('[TikTok] Campaign created:', campaignId);

    res.json({
      status: 'success',
      campaign_id: campaignId,
      message: 'Campaign created successfully',
      data: response.data.data
    });

  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      handleTikTokError(error, res);
    } else {
      console.error('[TikTok] Error creating campaign:', error);
      res.status(500).json({ error: error.message });
    }
  }
});

// Get Campaign
app.get('/api/campaigns/:campaignId', requireConfiguration, async (req: Request, res: Response) => {
  try {
    const { campaignId } = req.params;

    const response = await tiktokClient.get('/campaign/get/', {
      params: {
        advertiser_id: TIKTOK_ADVERTISER_ID,
        filtering: JSON.stringify({ campaign_ids: [campaignId] })
      }
    });

    if (response.data.code !== 0) {
      return res.status(400).json({
        error: 'TikTok API error',
        code: response.data.code,
        message: response.data.message
      });
    }

    const campaign = response.data.data.list?.[0];
    if (!campaign) {
      return res.status(404).json({
        error: 'Campaign not found',
        campaign_id: campaignId
      });
    }

    res.json({
      status: 'success',
      campaign
    });

  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      handleTikTokError(error, res);
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// ============================================================================
// AD GROUP MANAGEMENT
// ============================================================================

// Create Ad Group
app.post('/api/ad-groups', requireConfiguration, async (req: Request, res: Response) => {
  try {
    const {
      name,
      campaignId,
      budget,
      schedule_type = 'SCHEDULE_FROM_NOW',
      optimization_goal = 'CLICK',
      bid_type = 'BID_TYPE_NO_BID',
      placement_type = 'PLACEMENT_TYPE_AUTOMATIC',
      location_ids = ['6252001'], // US by default
      gender = 'GENDER_UNLIMITED',
      age_groups = ['AGE_18_24', 'AGE_25_34', 'AGE_35_44', 'AGE_45_54']
    } = req.body;

    if (!name || !campaignId || !budget) {
      return res.status(400).json({
        error: 'Missing required fields',
        required: ['name', 'campaignId', 'budget']
      });
    }

    console.log('[TikTok] Creating ad group:', { name, campaignId, budget });

    const response = await tiktokClient.post('/adgroup/create/', {
      advertiser_id: TIKTOK_ADVERTISER_ID,
      campaign_id: campaignId,
      adgroup_name: name,
      budget: budget * 100, // cents
      schedule_type,
      optimization_goal,
      bid_type,
      placement_type,
      location_ids,
      gender,
      age_groups,
      operating_system: ['ANDROID', 'IOS'],
    });

    if (response.data.code !== 0) {
      return res.status(400).json({
        error: 'TikTok API error',
        code: response.data.code,
        message: response.data.message
      });
    }

    const adGroupId = response.data.data.adgroup_id;
    console.log('[TikTok] Ad group created:', adGroupId);

    res.json({
      status: 'success',
      ad_group_id: adGroupId,
      campaign_id: campaignId,
      message: 'Ad group created successfully'
    });

  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      handleTikTokError(error, res);
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// ============================================================================
// VIDEO UPLOAD
// ============================================================================

// Upload Video
app.post('/api/videos/upload', requireConfiguration, async (req: Request, res: Response) => {
  try {
    const { videoPath, videoUrl } = req.body;

    if (!videoPath && !videoUrl) {
      return res.status(400).json({
        error: 'Missing video source',
        message: 'Provide either videoPath (local file) or videoUrl (remote URL)'
      });
    }

    console.log('[TikTok] Uploading video:', { videoPath, videoUrl });

    let response;

    if (videoUrl) {
      // Upload from URL
      response = await tiktokClient.post('/file/video/ad/upload/', {
        advertiser_id: TIKTOK_ADVERTISER_ID,
        upload_type: 'UPLOAD_BY_URL',
        video_url: videoUrl,
      });
    } else {
      // Upload from file
      if (!fs.existsSync(videoPath)) {
        return res.status(400).json({
          error: 'Video file not found',
          path: videoPath
        });
      }

      const form = new FormData();
      form.append('advertiser_id', TIKTOK_ADVERTISER_ID);
      form.append('upload_type', 'UPLOAD_BY_FILE');
      form.append('video_file', fs.createReadStream(videoPath));

      response = await tiktokClient.post('/file/video/ad/upload/', form, {
        headers: {
          ...form.getHeaders(),
          'Access-Token': TIKTOK_ACCESS_TOKEN,
        },
        maxContentLength: Infinity,
        maxBodyLength: Infinity,
      });
    }

    if (response.data.code !== 0) {
      return res.status(400).json({
        error: 'TikTok API error',
        code: response.data.code,
        message: response.data.message
      });
    }

    const videoId = response.data.data.video_id;
    console.log('[TikTok] Video uploaded:', videoId);

    res.json({
      status: 'success',
      video_id: videoId,
      message: 'Video uploaded successfully'
    });

  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      handleTikTokError(error, res);
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// ============================================================================
// AD CREATION
// ============================================================================

// Create Ad
app.post('/api/ads', requireConfiguration, async (req: Request, res: Response) => {
  try {
    const {
      name,
      adGroupId,
      videoId,
      displayName,
      text,
      callToAction = 'LEARN_MORE',
      landingPageUrl
    } = req.body;

    if (!name || !adGroupId || !videoId || !landingPageUrl) {
      return res.status(400).json({
        error: 'Missing required fields',
        required: ['name', 'adGroupId', 'videoId', 'landingPageUrl']
      });
    }

    console.log('[TikTok] Creating ad:', { name, adGroupId, videoId });

    const response = await tiktokClient.post('/ad/create/', {
      advertiser_id: TIKTOK_ADVERTISER_ID,
      adgroup_id: adGroupId,
      creatives: [{
        ad_name: name,
        ad_format: 'SINGLE_VIDEO',
        video_id: videoId,
        display_name: displayName || name,
        ad_text: text || '',
        call_to_action: callToAction,
        landing_page_url: landingPageUrl,
      }]
    });

    if (response.data.code !== 0) {
      return res.status(400).json({
        error: 'TikTok API error',
        code: response.data.code,
        message: response.data.message
      });
    }

    const adId = response.data.data.ad_ids?.[0];
    console.log('[TikTok] Ad created:', adId);

    res.json({
      status: 'success',
      ad_id: adId,
      ad_group_id: adGroupId,
      message: 'Ad created successfully'
    });

  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      handleTikTokError(error, res);
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// ============================================================================
// COMPLETE PUBLISH WORKFLOW
// ============================================================================

// Publish - Complete Workflow (Campaign -> Ad Group -> Video Upload -> Ad)
app.post('/api/publish', requireConfiguration, async (req: Request, res: Response) => {
  try {
    const {
      campaignName,
      videoPath,
      videoUrl,
      budget,
      objective = 'TRAFFIC',
      targeting = {},
      adGroupName,
      text,
      callToAction = 'LEARN_MORE',
      landingPageUrl
    } = req.body;

    if (!campaignName || (!videoPath && !videoUrl) || !budget || !landingPageUrl) {
      return res.status(400).json({
        error: 'Missing required fields',
        required: ['campaignName', 'videoPath OR videoUrl', 'budget', 'landingPageUrl']
      });
    }

    console.log('[TikTok] Starting publish workflow:', { campaignName, budget, objective });

    const results: any = {
      steps: [],
      success: false
    };

    try {
      // Step 1: Create Campaign
      console.log('[TikTok] Step 1: Creating campaign...');
      const campaignResponse = await tiktokClient.post('/campaign/create/', {
        advertiser_id: TIKTOK_ADVERTISER_ID,
        campaign_name: campaignName,
        objective_type: objective,
        budget_mode: 'BUDGET_MODE_DAY',
        budget: budget * 100,
      });

      if (campaignResponse.data.code !== 0) {
        throw new Error(`Campaign creation failed: ${campaignResponse.data.message}`);
      }

      const campaignId = campaignResponse.data.data.campaign_id;
      results.campaign_id = campaignId;
      results.steps.push({ step: 'campaign', status: 'success', id: campaignId });
      console.log('[TikTok] Campaign created:', campaignId);

      // Step 2: Create Ad Group
      console.log('[TikTok] Step 2: Creating ad group...');
      const adGroupResponse = await tiktokClient.post('/adgroup/create/', {
        advertiser_id: TIKTOK_ADVERTISER_ID,
        campaign_id: campaignId,
        adgroup_name: adGroupName || `${campaignName} - AdGroup`,
        budget: budget * 100,
        schedule_type: 'SCHEDULE_FROM_NOW',
        optimization_goal: objective === 'CONVERSIONS' ? 'CONVERT' : 'CLICK',
        bid_type: 'BID_TYPE_NO_BID',
        placement_type: 'PLACEMENT_TYPE_AUTOMATIC',
        location_ids: targeting.location_ids || ['6252001'],
        gender: targeting.gender || 'GENDER_UNLIMITED',
        age_groups: targeting.age_groups || ['AGE_18_24', 'AGE_25_34', 'AGE_35_44'],
        operating_system: ['ANDROID', 'IOS'],
      });

      if (adGroupResponse.data.code !== 0) {
        throw new Error(`Ad group creation failed: ${adGroupResponse.data.message}`);
      }

      const adGroupId = adGroupResponse.data.data.adgroup_id;
      results.ad_group_id = adGroupId;
      results.steps.push({ step: 'adgroup', status: 'success', id: adGroupId });
      console.log('[TikTok] Ad group created:', adGroupId);

      // Step 3: Upload Video
      console.log('[TikTok] Step 3: Uploading video...');
      let videoResponse;
      if (videoUrl) {
        videoResponse = await tiktokClient.post('/file/video/ad/upload/', {
          advertiser_id: TIKTOK_ADVERTISER_ID,
          upload_type: 'UPLOAD_BY_URL',
          video_url: videoUrl,
        });
      } else {
        const form = new FormData();
        form.append('advertiser_id', TIKTOK_ADVERTISER_ID);
        form.append('upload_type', 'UPLOAD_BY_FILE');
        form.append('video_file', fs.createReadStream(videoPath));

        videoResponse = await tiktokClient.post('/file/video/ad/upload/', form, {
          headers: { ...form.getHeaders(), 'Access-Token': TIKTOK_ACCESS_TOKEN },
          maxContentLength: Infinity,
          maxBodyLength: Infinity,
        });
      }

      if (videoResponse.data.code !== 0) {
        throw new Error(`Video upload failed: ${videoResponse.data.message}`);
      }

      const videoId = videoResponse.data.data.video_id;
      results.video_id = videoId;
      results.steps.push({ step: 'video', status: 'success', id: videoId });
      console.log('[TikTok] Video uploaded:', videoId);

      // Step 4: Create Ad
      console.log('[TikTok] Step 4: Creating ad...');
      const adResponse = await tiktokClient.post('/ad/create/', {
        advertiser_id: TIKTOK_ADVERTISER_ID,
        adgroup_id: adGroupId,
        creatives: [{
          ad_name: `${campaignName} - Video Ad`,
          ad_format: 'SINGLE_VIDEO',
          video_id: videoId,
          display_name: campaignName,
          ad_text: text || '',
          call_to_action: callToAction,
          landing_page_url: landingPageUrl,
        }]
      });

      if (adResponse.data.code !== 0) {
        throw new Error(`Ad creation failed: ${adResponse.data.message}`);
      }

      const adId = adResponse.data.data.ad_ids?.[0];
      results.ad_id = adId;
      results.steps.push({ step: 'ad', status: 'success', id: adId });
      console.log('[TikTok] Ad created:', adId);

      results.success = true;
      results.ad_status = 'PAUSED'; // Ads start paused
      results.message = 'Campaign published successfully';

      console.log('[TikTok] Publish workflow completed successfully');

      res.json({
        status: 'success',
        ...results
      });

    } catch (stepError: any) {
      console.error('[TikTok] Publish workflow failed:', stepError.message);
      results.error = stepError.message;
      results.message = 'Publish workflow failed - see steps for details';

      res.status(500).json({
        status: 'error',
        ...results
      });
    }

  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      handleTikTokError(error, res);
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// ============================================================================
// PERFORMANCE METRICS
// ============================================================================

// Get Campaign Performance
app.get('/api/performance/campaign/:campaignId', requireConfiguration, async (req: Request, res: Response) => {
  try {
    const { campaignId } = req.params;
    const { startDate, endDate } = req.query;

    // Default to last 7 days
    const end = endDate ? new Date(endDate as string) : new Date();
    const start = startDate ? new Date(startDate as string) : new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);

    const response = await tiktokClient.get('/report/integrated/get/', {
      params: {
        advertiser_id: TIKTOK_ADVERTISER_ID,
        service_type: 'AUCTION',
        report_type: 'BASIC',
        data_level: 'AUCTION_CAMPAIGN',
        dimensions: JSON.stringify(['campaign_id', 'stat_time_day']),
        metrics: JSON.stringify([
          'spend', 'impressions', 'clicks', 'ctr', 'cpc',
          'conversions', 'conversion_rate', 'cpa', 'reach'
        ]),
        start_date: start.toISOString().split('T')[0],
        end_date: end.toISOString().split('T')[0],
        filtering: JSON.stringify({ campaign_ids: [campaignId] }),
        page_size: 100
      }
    });

    if (response.data.code !== 0) {
      return res.status(400).json({
        error: 'TikTok API error',
        code: response.data.code,
        message: response.data.message
      });
    }

    res.json({
      status: 'success',
      campaign_id: campaignId,
      date_range: {
        start: start.toISOString().split('T')[0],
        end: end.toISOString().split('T')[0]
      },
      data: response.data.data.list || [],
      page_info: response.data.data.page_info
    });

  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      handleTikTokError(error, res);
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// Get Ad Performance
app.get('/api/performance/ad/:adId', requireConfiguration, async (req: Request, res: Response) => {
  try {
    const { adId } = req.params;
    const { startDate, endDate } = req.query;

    const end = endDate ? new Date(endDate as string) : new Date();
    const start = startDate ? new Date(startDate as string) : new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);

    const response = await tiktokClient.get('/report/integrated/get/', {
      params: {
        advertiser_id: TIKTOK_ADVERTISER_ID,
        service_type: 'AUCTION',
        report_type: 'BASIC',
        data_level: 'AUCTION_AD',
        dimensions: JSON.stringify(['ad_id', 'stat_time_day']),
        metrics: JSON.stringify([
          'spend', 'impressions', 'clicks', 'ctr', 'cpc',
          'video_play_actions', 'video_watched_2s', 'video_watched_6s',
          'average_video_play', 'average_video_play_per_user'
        ]),
        start_date: start.toISOString().split('T')[0],
        end_date: end.toISOString().split('T')[0],
        filtering: JSON.stringify({ ad_ids: [adId] }),
        page_size: 100
      }
    });

    if (response.data.code !== 0) {
      return res.status(400).json({
        error: 'TikTok API error',
        code: response.data.code,
        message: response.data.message
      });
    }

    res.json({
      status: 'success',
      ad_id: adId,
      date_range: {
        start: start.toISOString().split('T')[0],
        end: end.toISOString().split('T')[0]
      },
      data: response.data.data.list || [],
      page_info: response.data.data.page_info
    });

  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      handleTikTokError(error, res);
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// ============================================================================
// STATUS UPDATES
// ============================================================================

// Update Ad Status
app.patch('/api/ads/:adId/status', requireConfiguration, async (req: Request, res: Response) => {
  try {
    const { adId } = req.params;
    const { status } = req.body; // ENABLE, DISABLE, DELETE

    if (!status || !['ENABLE', 'DISABLE', 'DELETE'].includes(status)) {
      return res.status(400).json({
        error: 'Invalid status',
        allowed: ['ENABLE', 'DISABLE', 'DELETE']
      });
    }

    const response = await tiktokClient.post('/ad/status/update/', {
      advertiser_id: TIKTOK_ADVERTISER_ID,
      ad_ids: [adId],
      operation_status: status
    });

    if (response.data.code !== 0) {
      return res.status(400).json({
        error: 'TikTok API error',
        code: response.data.code,
        message: response.data.message
      });
    }

    res.json({
      status: 'success',
      ad_id: adId,
      new_status: status,
      message: `Ad ${status.toLowerCase()}d successfully`
    });

  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      handleTikTokError(error, res);
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// Update Campaign Budget
app.patch('/api/campaigns/:campaignId/budget', requireConfiguration, async (req: Request, res: Response) => {
  try {
    const { campaignId } = req.params;
    const { budget } = req.body;

    if (!budget || budget <= 0) {
      return res.status(400).json({
        error: 'Invalid budget',
        message: 'Budget must be a positive number'
      });
    }

    const response = await tiktokClient.post('/campaign/update/', {
      advertiser_id: TIKTOK_ADVERTISER_ID,
      campaign_id: campaignId,
      budget: budget * 100 // cents
    });

    if (response.data.code !== 0) {
      return res.status(400).json({
        error: 'TikTok API error',
        code: response.data.code,
        message: response.data.message
      });
    }

    res.json({
      status: 'success',
      campaign_id: campaignId,
      new_budget: budget,
      message: 'Campaign budget updated successfully'
    });

  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      handleTikTokError(error, res);
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// ============================================================================
// ACCOUNT INFO
// ============================================================================

// Get Account Info
app.get('/api/account/info', requireConfiguration, async (req: Request, res: Response) => {
  try {
    const response = await tiktokClient.get('/advertiser/info/', {
      params: {
        advertiser_ids: JSON.stringify([TIKTOK_ADVERTISER_ID])
      }
    });

    if (response.data.code !== 0) {
      return res.status(400).json({
        error: 'TikTok API error',
        code: response.data.code,
        message: response.data.message
      });
    }

    const account = response.data.data.list?.[0];

    res.json({
      status: 'success',
      account: account || { advertiser_id: TIKTOK_ADVERTISER_ID }
    });

  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      handleTikTokError(error, res);
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`TikTok Ads Service listening on port ${PORT}`);

  if (IS_CONFIGURED) {
    console.log('✅ TikTok API configured and ready');
    console.log(`   Advertiser ID: ${TIKTOK_ADVERTISER_ID.slice(0, 4)}****`);
  } else {
    console.log('⚠️  TikTok API NOT CONFIGURED');
    console.log('   Set TIKTOK_ACCESS_TOKEN and TIKTOK_ADVERTISER_ID to enable');
    console.log('   All endpoints will return 503 until configured');
    console.log('📝 Documentation: https://business-api.tiktok.com/portal/docs');
  }
});

export default app;
