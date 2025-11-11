import express, { Express, Request, Response } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';

dotenv.config();

const app: Express = express();
const PORT = process.env.PORT || 8083;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

interface PublishRequest {
  video_url: string;
  caption: string;
  targeting: {
    age_range?: [number, number];
    interests?: string[];
    locations?: string[];
  };
  budget: {
    daily_budget: number;
    currency: string;
  };
  prediction_id?: string;
}

interface InsightData {
  ad_id: string;
  impressions: number;
  clicks: number;
  ctr: number;
  spend: number;
  reach: number;
  engagement: number;
}

// Health check endpoint
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    service: 'meta-publisher',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

/**
 * POST /publish/meta
 * Publish video ad to Meta (Facebook/Instagram)
 */
app.post('/publish/meta', async (req: Request, res: Response) => {
  try {
    const publishReq: PublishRequest = req.body;

    if (!publishReq.video_url || !publishReq.caption) {
      return res.status(400).json({ error: 'Missing required fields: video_url, caption' });
    }

    // In production, would use Meta Marketing API:
    // const response = await axios.post(
    //   `https://graph.facebook.com/v18.0/${adAccountId}/adcreatives`,
    //   {
    //     access_token: process.env.META_ACCESS_TOKEN,
    //     object_story_spec: {
    //       video_data: {
    //         video_id: uploadedVideoId,
    //         message: publishReq.caption
    //       }
    //     },
    //     ...targeting and budget config
    //   }
    // );

    // Mock response
    const adId = `ad_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const response = {
      ad_id: adId,
      status: 'active',
      platform: 'meta',
      created_at: new Date().toISOString(),
      prediction_id: publishReq.prediction_id,
      video_url: publishReq.video_url,
      targeting: publishReq.targeting,
      budget: publishReq.budget
    };

    res.json(response);
  } catch (error) {
    console.error('Publish error:', error);
    res.status(500).json({ 
      error: 'Publish failed', 
      details: (error as Error).message 
    });
  }
});

/**
 * GET /insights
 * Fetch ad performance insights from Meta
 * Updates prediction logs with actual CTR
 */
app.get('/insights', async (req: Request, res: Response) => {
  try {
    const adId = req.query.ad_id as string;
    const predictionId = req.query.prediction_id as string;

    if (!adId) {
      return res.status(400).json({ error: 'Missing ad_id parameter' });
    }

    // In production, would fetch from Meta Insights API:
    // const response = await axios.get(
    //   `https://graph.facebook.com/v18.0/${adId}/insights`,
    //   {
    //     params: {
    //       access_token: process.env.META_ACCESS_TOKEN,
    //       fields: 'impressions,clicks,ctr,spend,reach,engagement'
    //     }
    //   }
    // );

    // Mock insights data
    const insights: InsightData = {
      ad_id: adId,
      impressions: Math.floor(Math.random() * 100000) + 10000,
      clicks: Math.floor(Math.random() * 5000) + 500,
      ctr: 0.03 + Math.random() * 0.05, // 3-8% CTR
      spend: Math.floor(Math.random() * 500) + 100,
      reach: Math.floor(Math.random() * 50000) + 5000,
      engagement: Math.floor(Math.random() * 3000) + 300
    };

    // Update prediction log if prediction_id provided
    if (predictionId) {
      await updatePredictionLog(predictionId, insights.ctr);
    }

    res.json({
      ad_id: adId,
      insights,
      updated_at: new Date().toISOString()
    });
  } catch (error) {
    console.error('Insights error:', error);
    res.status(500).json({ 
      error: 'Failed to fetch insights', 
      details: (error as Error).message 
    });
  }
});

/**
 * Helper function to update prediction log with actual CTR
 * Links back to gateway's prediction logging system
 */
async function updatePredictionLog(predictionId: string, actualCTR: number): Promise<void> {
  try {
    const logsPath = path.join(__dirname, '../../../logs/predictions.jsonl');
    
    if (!fs.existsSync(logsPath)) {
      console.warn('Prediction log file not found');
      return;
    }

    // Read all logs
    const content = fs.readFileSync(logsPath, 'utf8');
    const lines = content.split('\n').filter(line => line.trim());
    
    // Update matching entry
    const updatedLines = lines.map(line => {
      try {
        const entry = JSON.parse(line);
        if (entry.prediction_id === predictionId) {
          entry.actual_ctr = actualCTR;
          entry.updated_at = new Date().toISOString();
        }
        return JSON.stringify(entry);
      } catch {
        return line;
      }
    });

    // Write back
    fs.writeFileSync(logsPath, updatedLines.join('\n') + '\n', 'utf8');
    console.log(`Updated prediction ${predictionId} with actual CTR: ${actualCTR}`);
  } catch (error) {
    console.error('Failed to update prediction log:', error);
  }
}

// Start server
app.listen(PORT, () => {
  console.log(`Meta Publisher service listening on port ${PORT}`);
});

export default app;
