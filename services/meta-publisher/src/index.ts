/**
 * Meta Publisher Service - Creative Publishing & Insights Ingestion
 */
import express, { Request, Response } from 'express';
import cors from 'cors';
import axios from 'axios';

const app = express();
const PORT = process.env.PORT || 8003;

// Middleware
app.use(cors());
app.use(express.json());

// Meta API configuration
const META_ACCESS_TOKEN = process.env.META_ACCESS_TOKEN || '';
const META_API_VERSION = process.env.META_API_VERSION || 'v18.0';
const META_API_BASE = `https://graph.facebook.com/${META_API_VERSION}`;

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
    version: '1.0.0',
    dry_run_mode: !META_ACCESS_TOKEN
  });
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
