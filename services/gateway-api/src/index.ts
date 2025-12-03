/**
 * Gateway API - Prediction & Scoring Engine
 * Unified proxy to internal services with scoring capabilities
 *
 * ============================================================================
 * 🔴 CRITICAL ANALYSIS FINDINGS (December 2024)
 * ============================================================================
 *
 * FAKE/MOCK ENDPOINTS:
 * - /api/analyze (line 353): Returns HARDCODED mock data immediately
 *   "hook_style: High Energy", "pacing: Fast" - NEVER does real analysis
 * - /api/metrics (line 518): Returns HARDCODED metrics
 *   impressions: 15000, clicks: 800 - FAKE numbers
 * - Scores in /api/generate (line 327-329): Falls back to hardcoded 85, 8, 8
 *
 * BROKEN DEPENDENCIES:
 * - DRIVE_INTEL_URL: defaults to localhost:8001 - may not be running
 * - VIDEO_AGENT_URL: defaults to localhost:8002 - may not be running
 * - ML_SERVICE_URL: defaults to localhost:8003 - may not be running
 * - META_PUBLISHER_URL: defaults to localhost:8083 - may not be running
 *
 * SYNC PROBLEMS:
 * - Redis queue (line 171): Pushes jobs but no worker consuming them
 * - PostgreSQL: Requires DATABASE_URL but schema may not match
 * - Learning service: updateWeights() exists but no feedback data
 *
 * WHAT'S ACTUALLY WORKING:
 * - Health check (/health)
 * - Database connection
 * - Proxy to other services (if they're running)
 * - Story arc rendering with clips
 *
 * FAST FIX: Remove mock data from /api/analyze and /api/metrics
 * ============================================================================
 */
import express, { Request, Response } from 'express';
import cors from 'cors';
import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';
import axios from 'axios';
import { createClient } from 'redis';
import { Pool } from 'pg';
import { v4 as uuidv4 } from 'uuid';

import { ScoringEngine } from './services/scoring-engine';
import { ReliabilityLogger } from './services/reliability-logger';
import { LearningService } from './services/learning-service';

const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(cors());
app.use(express.json());

// Redis client for async queues
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const redisClient = createClient({ url: REDIS_URL });
redisClient.on('error', (err) => console.warn('Redis Client Error (Queue disabled):', err.message));
redisClient.connect().then(() => {
  console.log('✅ Redis connected for async queues');
}).catch((err) => {
  console.warn('⚠️ Redis connection failed. Async queues will not work:', err.message);
});

// PostgreSQL client for database access
const DATABASE_URL = process.env.DATABASE_URL;
if (!DATABASE_URL) {
  console.error('❌ DATABASE_URL environment variable is required');
  console.error('Example: postgresql://user:password@host:5432/dbname');
  process.exit(1);
}

const pgPool = new Pool({
  connectionString: DATABASE_URL,
  ssl: DATABASE_URL.includes('localhost') || DATABASE_URL.includes('postgres')
    ? false
    : { rejectUnauthorized: false }
});
pgPool.on('error', (err: Error) => console.error('PostgreSQL Pool Error', err));

// Verify database connection
pgPool.query('SELECT NOW()')
  .then(() => console.log('✅ PostgreSQL connected'))
  .catch((err) => {
    console.error('❌ PostgreSQL connection failed:', err.message);
    process.exit(1);
  });

// Load configuration
const configPath = process.env.CONFIG_PATH || '../../shared/config';
const weightsConfig = yaml.load(
  fs.readFileSync(path.join(configPath, 'weights.yaml'), 'utf8')
) as any;
const triggersConfig = JSON.parse(
  fs.readFileSync(path.join(configPath, 'triggers_config.json'), 'utf8')
);
const personasConfig = JSON.parse(
  fs.readFileSync(path.join(configPath, 'personas.json'), 'utf8')
);

// Initialize services
const scoringEngine = new ScoringEngine(weightsConfig, triggersConfig, personasConfig);
const reliabilityLogger = new ReliabilityLogger();
const learningService = new LearningService(weightsConfig);

// Service URLs
const DRIVE_INTEL_URL = process.env.DRIVE_INTEL_URL || 'http://localhost:8001';
const VIDEO_AGENT_URL = process.env.VIDEO_AGENT_URL || 'http://localhost:8002';
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8003';
const META_PUBLISHER_URL = process.env.META_PUBLISHER_URL || 'http://localhost:8083';

// Root endpoint
app.get('/', (req: Request, res: Response) => {
  res.json({
    service: 'gateway-api',
    status: 'running',
    version: '1.0.0'
  });
});

// Helper function to validate service URLs
function validateServiceUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    // Only allow HTTP/HTTPS and specific internal service patterns
    return (parsed.protocol === 'http:' || parsed.protocol === 'https:') &&
      (parsed.hostname === 'localhost' ||
        parsed.hostname.includes('drive-intel') ||
        parsed.hostname.includes('video-agent') ||
        parsed.hostname.includes('ml-service') ||
        parsed.hostname.includes('meta-publisher') ||
        parsed.hostname.includes('.run.app')); // Cloud Run domains
  } catch {
    return false;
  }
}

// Proxy to drive-intel service
app.get('/api/assets', async (req: Request, res: Response) => {
  try {
    if (!validateServiceUrl(DRIVE_INTEL_URL)) {
      throw new Error('Invalid service URL');
    }
    const response = await axios.get(`${DRIVE_INTEL_URL}/assets`, {
      params: req.query
    });
    res.json(response.data);
  } catch (error: any) {
    res.status(error.response?.status || 500).json({
      error: error.message
    });
  }
});

app.get('/api/assets/:assetId/clips', async (req: Request, res: Response) => {
  try {
    const response = await axios.get(
      `${DRIVE_INTEL_URL}/assets/${req.params.assetId}/clips`,
      { params: req.query }
    );
    res.json(response.data);
  } catch (error: any) {
    res.status(error.response?.status || 500).json({
      error: error.message
    });
  }
});

// Async analysis endpoint - queues job instead of blocking
app.post('/api/analyze', async (req: Request, res: Response) => {
  try {
    const { path: videoPath, filename, size_bytes, duration_seconds } = req.body;

    // Validate required fields
    if (!videoPath || !filename) {
      return res.status(400).json({ error: 'Missing required fields: path, filename' });
    }

    // Create asset in database with QUEUED status
    const assetId = uuidv4();
    const query = `
      INSERT INTO assets (asset_id, path, filename, size_bytes, duration_seconds, 
                         resolution, format, status, ingested_at)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
      RETURNING asset_id
    `;

    await pgPool.query(query, [
      assetId,
      videoPath,
      filename,
      size_bytes || 0,
      duration_seconds || 0,
      '1920x1080',  // Default
      'mp4',        // Default
      'QUEUED'
    ]);

    // Push job to Redis queue
    await redisClient.rPush('analysis_queue', assetId);

    // Return immediately with 202 Accepted
    res.status(202).json({
      asset_id: assetId,
      status: 'QUEUED',
      message: 'Analysis job queued successfully'
    });

  } catch (error: any) {
    console.error('Error queuing analysis:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/ingest/local/folder', async (req: Request, res: Response) => {
  try {
    const response = await axios.post(
      `${DRIVE_INTEL_URL}/ingest/local/folder`,
      req.body
    );
    res.json(response.data);
  } catch (error: any) {
    res.status(error.response?.status || 500).json({
      error: error.message
    });
  }
});

app.post('/api/search/clips', async (req: Request, res: Response) => {
  try {
    const response = await axios.post(
      `${DRIVE_INTEL_URL}/search/clips`,
      req.body
    );
    res.json(response.data);
  } catch (error: any) {
    res.status(error.response?.status || 500).json({
      error: error.message
    });
  }
});

// Scoring endpoint with XGBoost integration (Agent 4)
app.post('/api/score/storyboard', async (req: Request, res: Response) => {
  try {
    const { scenes, metadata } = req.body;

    // Calculate rule-based scores
    const scores = scoringEngine.scoreStoryboard(scenes, metadata);

    // Get XGBoost CTR prediction
    let xgboostPrediction = null;
    try {
      const mlResponse = await axios.post(`${ML_SERVICE_URL}/api/ml/predict-ctr`, {
        clip_data: {
          ...scores,
          ...metadata,
          scene_count: scenes.length
        },
        include_confidence: true
      });
      xgboostPrediction = mlResponse.data;
    } catch (mlError: any) {
      console.warn('XGBoost prediction failed, using rule-based scores only:', mlError.message);
    }

    // Combine scores
    const finalScores = {
      ...scores,
      xgboost_ctr: xgboostPrediction?.predicted_ctr || null,
      xgboost_confidence: xgboostPrediction?.confidence || null,
      // Use XGBoost prediction if available, otherwise use rule-based
      final_ctr_prediction: xgboostPrediction?.predicted_ctr || scores.win_probability?.value || 0.02
    };

    // Log prediction
    const predictionId = reliabilityLogger.logPrediction({
      scenes,
      scores: finalScores,
      metadata,
      timestamp: new Date().toISOString()
    });

    res.json({
      prediction_id: predictionId,
      scores: finalScores,
      timestamp: new Date().toISOString()
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Proxy to video-agent service
app.post('/api/render/remix', async (req: Request, res: Response) => {
  try {
    if (!validateServiceUrl(VIDEO_AGENT_URL)) {
      throw new Error('Invalid service URL');
    }
    const response = await axios.post(
      `${VIDEO_AGENT_URL}/render/remix`,
      req.body
    );
    res.json(response.data);
  } catch (error: any) {
    res.status(error.response?.status || 500).json({
      error: error.message
    });
  }
});

// Generation endpoint - Proxies to Titan Core
app.post('/api/generate', async (req: Request, res: Response) => {
  try {
    const { assets, target_audience } = req.body;
    const TITAN_CORE_URL = process.env.TITAN_CORE_URL || 'http://localhost:8088'; // Default to 8088 based on docker-compose usually

    console.log(`Generating creative via Titan Core: ${TITAN_CORE_URL}`);

    // Transform payload for Titan Core
    const titanPayload = {
      video_context: assets && assets.length > 0 ? assets[0] : "Generic Video",
      niche: target_audience || "General"
    };

    // Call Titan Core
    const response = await axios.post(`${TITAN_CORE_URL}/generate`, titanPayload);
    const titanResult = response.data;

    // Parse blueprint if it's a string
    let blueprint: any = {};
    try {
      if (typeof titanResult.blueprint === 'string') {
        // Try to find JSON in the string if it's wrapped in markdown code blocks
        const jsonMatch = titanResult.blueprint.match(/```json\n([\s\S]*?)\n```/) ||
          titanResult.blueprint.match(/```\n([\s\S]*?)\n```/) ||
          [null, titanResult.blueprint];
        const jsonStr = jsonMatch[1] || titanResult.blueprint;
        blueprint = JSON.parse(jsonStr);
      } else {
        blueprint = titanResult.blueprint;
      }
    } catch (e) {
      console.warn("Failed to parse blueprint JSON", e);
      blueprint = { hook: "Generated Hook", body: titanResult.blueprint, cta: "Sign Up" };
    }

    // Transform response for Frontend (AdCreative[])
    const adCreative = {
      primarySourceFileName: assets && assets.length > 0 ? assets[0] : "generated.mp4",
      variationTitle: "Titan Generated Ad",
      headline: blueprint.hook || "Viral Hook",
      body: blueprint.body || "Compelling Ad Body",
      cta: blueprint.cta || "Learn More",
      editPlan: [],
      __roiScore: titanResult.council_review?.final_score || 85,
      __hookScore: titanResult.council_review?.breakdown?.gemini_3_pro || 8,
      __ctaScore: titanResult.council_review?.breakdown?.gpt_4o || 8
    };

    res.json(adCreative);

  } catch (error: any) {
    console.error("Generation Error:", error.message);
    // Fallback for demo if Titan is down
    res.json({
      primarySourceFileName: req.body.assets?.[0] || "fallback.mp4",
      variationTitle: "Fallback Generated Ad",
      headline: "Error connecting to Titan",
      body: "Please check backend logs. " + error.message,
      cta: "Retry",
      editPlan: [],
      __roiScore: 0,
      __hookScore: 0,
      __ctaScore: 0
    });
  }
});

// ============================================================================
// 🔴 FAKE ENDPOINT - Returns hardcoded mock data, NO real analysis!
// ============================================================================
// Async analysis endpoint - queues job instead of blocking
// MODIFIED: Returns synchronous mock for UI demo purposes while queuing
app.post('/api/analyze', async (req: Request, res: Response) => {
  try {
    const { video_uri } = req.body; // Frontend sends video_uri

    // ⚠️ THIS IS 100% FAKE - No AI analysis happens!
    // TODO: Replace with actual Gemini vision analysis:
    // const analysis = await gemini.analyzeVideo(video_uri);
    // return res.json(analysis);

    // Return immediate analysis for UI
    res.json({
      reasoning: "AI Analysis of " + (video_uri || "video"),  // FAKE
      hook_style: "High Energy",      // HARDCODED - always returns this
      pacing: "Fast",                 // HARDCODED - always returns this
      visual_elements: ["Person", "Text Overlay", "Product"],  // HARDCODED
      emotional_trigger: "Excitement" // HARDCODED - always returns this
    });

    // In a real scenario, we would still queue the deep analysis here
    // ... existing queue logic ...

  } catch (error: any) {
    console.error('Error in analysis:', error);
    res.status(500).json({ error: error.message });
  }
});
app.post('/api/render/story_arc', async (req: Request, res: Response) => {
  try {
    const { arc_name, asset_id } = req.body;

    // Load story arcs configuration
    const storyArcsPath = path.join(configPath, 'story_arcs.json');
    const storyArcs = JSON.parse(fs.readFileSync(storyArcsPath, 'utf8'));

    // Get the requested arc
    const arc = storyArcs[arc_name || 'fitness_transformation'];
    if (!arc) {
      return res.status(404).json({
        error: 'Story arc not found',
        available_arcs: Object.keys(storyArcs)
      });
    }

    // Query database for clips matching each step
    const selectedClips: string[] = [];

    for (const step of arc.steps) {
      const query = `
        SELECT c.clip_id, c.ctr_score, e.emotion
        FROM clips c
        LEFT JOIN emotions e ON c.clip_id = e.clip_id
        WHERE c.asset_id = $1 AND e.emotion = $2
        ORDER BY c.ctr_score DESC, c.scene_score DESC
        LIMIT 1
      `;

      const result = await pgPool.query(query, [asset_id, step.emotion]);

      if (result.rows.length > 0) {
        selectedClips.push(result.rows[0].clip_id);
      } else {
        // Fallback: get any clip if no emotion match
        const fallbackQuery = `
          SELECT clip_id FROM clips
          WHERE asset_id = $1
          ORDER BY ctr_score DESC, scene_score DESC
          LIMIT 1
        `;
        const fallbackResult = await pgPool.query(fallbackQuery, [asset_id]);
        if (fallbackResult.rows.length > 0) {
          selectedClips.push(fallbackResult.rows[0].clip_id);
        }
      }
    }

    if (selectedClips.length === 0) {
      return res.status(404).json({
        error: 'No clips found for story arc',
        asset_id
      });
    }

    // Create render job
    const jobId = uuidv4();
    const renderJob = {
      job_id: jobId,
      clip_ids: selectedClips,
      arc_name,
      enable_transitions: true,
      output_path: `/tmp/output_${jobId}.mp4`
    };

    // Push to render queue
    await redisClient.rPush('render_queue', JSON.stringify(renderJob));

    // Return job info
    res.status(202).json({
      job_id: jobId,
      status: 'QUEUED',
      arc_name,
      selected_clips: selectedClips,
      message: 'Render job queued successfully'
    });

  } catch (error: any) {
    console.error('Error creating story arc render:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/render/status/:jobId', async (req: Request, res: Response) => {
  try {
    const response = await axios.get(
      `${VIDEO_AGENT_URL}/render/status/${req.params.jobId}`
    );
    res.json(response.data);
  } catch (error: any) {
    res.status(error.response?.status || 500).json({
      error: error.message
    });
  }
});

// Proxy to meta-publisher service
app.post('/api/publish/meta', async (req: Request, res: Response) => {
  try {
    const response = await axios.post(
      `${META_PUBLISHER_URL}/publish/meta`,
      req.body
    );
    res.json(response.data);
  } catch (error: any) {
    res.status(error.response?.status || 500).json({
      error: error.message
    });
  }
});

app.get('/api/insights', async (req: Request, res: Response) => {
  try {
    const response = await axios.get(
      `${META_PUBLISHER_URL}/insights`,
      { params: req.query }
    );
    res.json(response.data);
  } catch (error: any) {
    res.status(error.response?.status || 500).json({
      error: error.message
    });
  }
});

app.get('/api/creatives', async (req: Request, res: Response) => {
  try {
    const response = await axios.get(`${META_PUBLISHER_URL}/api/creatives`, { params: req.query });
    res.json(response.data);
  } catch (error: any) {
    res.status(error.response?.status || 500).json({ error: error.message });
  }
});

app.get('/api/timeseries', async (req: Request, res: Response) => {
  try {
    const response = await axios.get(`${META_PUBLISHER_URL}/api/timeseries`, { params: req.query });
    res.json(response.data);
  } catch (error: any) {
    res.status(error.response?.status || 500).json({ error: error.message });
  }
});

// ============================================================================
// 🔴 FAKE ENDPOINT - Returns hardcoded metrics, NOT from real campaigns!
// ============================================================================
app.get('/api/metrics', async (req: Request, res: Response) => {
  try {
    // ⚠️ ALL FAKE DATA BELOW - No real Meta integration
    // TODO: Replace with actual Meta Ads API insights:
    // const insights = await metaAdsManager.getAccountInsights();
    // return res.json(insights);

    // Aggregate metrics from meta-publisher or return mock
    res.json({
      totals: {
        impressions: 15000,   // FAKE: No real data source
        clicks: 800,          // FAKE: No real data source
        conversions: 120,     // FAKE: No real data source
        spend: 2500,          // FAKE: No real data source
        revenue: 7500,        // FAKE: No real data source
        ctr: 0.053,           // FAKE: Calculated from fake numbers
        cvr: 0.15,            // FAKE: Calculated from fake numbers
        cpa: 20.83,           // FAKE: Calculated from fake numbers
        roas: 3.0             // FAKE: Calculated from fake numbers
      }
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/stream', (req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  const interval = setInterval(() => {
    res.write(`data: ${JSON.stringify({ timestamp: Date.now() })}\n\n`);
  }, 5000);

  req.on('close', () => {
    clearInterval(interval);
  });
});

// Learning loop endpoint
app.post('/api/internal/learning/update', async (req: Request, res: Response) => {
  try {
    const result = await learningService.updateWeights();
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Diversification metrics
app.get('/api/metrics/diversification', (req: Request, res: Response) => {
  try {
    const metrics = reliabilityLogger.getDiversificationMetrics();
    res.json(metrics);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Reliability metrics
app.get('/api/metrics/reliability', (req: Request, res: Response) => {
  try {
    const metrics = reliabilityLogger.getReliabilityMetrics();
    res.json(metrics);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Human Workflow API - Manual Trigger Endpoints

// POST /api/trigger/analyze-drive-folder
// Manual trigger button: "Analyze My Google Drive Ads"
app.post('/api/trigger/analyze-drive-folder', async (req: Request, res: Response) => {
  try {
    const { folder_id, max_videos } = req.body;

    // Validate required fields
    if (!folder_id) {
      return res.status(400).json({ error: 'Missing required field: folder_id' });
    }

    console.log(`Triggering Drive folder analysis: folder_id=${folder_id}, max_videos=${max_videos || 'all'}`);

    // Call drive-intel service bulk_analyzer
    const response = await axios.post(`${DRIVE_INTEL_URL}/bulk_analyzer`, {
      folder_id,
      max_videos: max_videos || 10
    });

    console.log(`Drive folder analysis completed: ${response.data.videos_analyzed || 0} videos analyzed`);

    // Return 202 Accepted for async operation
    res.status(202).json({
      status: 'accepted',
      message: 'Drive folder analysis initiated',
      results: response.data
    });

  } catch (error: any) {
    console.error('Error triggering Drive folder analysis:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.message
    });
  }
});

// POST /api/trigger/refresh-meta-metrics
// Manual trigger button: "Refresh Meta Learning Data"
app.post('/api/trigger/refresh-meta-metrics', async (req: Request, res: Response) => {
  try {
    const { days_back } = req.body;

    console.log(`Triggering Meta learning cycle: days_back=${days_back || 7}`);

    // Call ML service meta learning agent
    const response = await axios.post(`${ML_SERVICE_URL}/api/ml/learning-cycle`, {
      days_back: days_back || 7
    });

    console.log(`Meta learning cycle completed: ${response.data.campaigns_analyzed || 0} campaigns analyzed`);

    // Return 202 Accepted for async operation
    res.status(202).json({
      status: 'accepted',
      message: 'Meta learning cycle initiated',
      results: {
        campaigns_analyzed: response.data.campaigns_analyzed || 0,
        avg_ctr: response.data.avg_ctr || 0,
        avg_roas: response.data.avg_roas || 0
      }
    });

  } catch (error: any) {
    console.error('Error triggering Meta learning cycle:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.message
    });
  }
});

// GET /api/approval/queue
// Shows pending ads awaiting human approval
app.get('/api/approval/queue', async (req: Request, res: Response) => {
  try {
    console.log('Fetching approval queue');

    // Query database for ads where approved=false
    const query = `
      SELECT
        ad_id,
        asset_id,
        clip_ids,
        arc_name,
        predicted_ctr,
        predicted_roas,
        status,
        created_at,
        notes
      FROM ads
      WHERE approved = false AND status = 'pending_approval'
      ORDER BY created_at DESC
    `;

    const result = await pgPool.query(query);

    console.log(`Approval queue fetched: ${result.rows.length} ads pending`);

    res.json({
      count: result.rows.length,
      ads: result.rows
    });

  } catch (error: any) {
    console.error('Error fetching approval queue:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// POST /api/approval/approve/:ad_id
// Human clicks "Approve" button
app.post('/api/approval/approve/:ad_id', async (req: Request, res: Response) => {
  try {
    const { ad_id } = req.params;
    const { approved, notes } = req.body;

    // Validate required fields
    if (typeof approved !== 'boolean') {
      return res.status(400).json({ error: 'Missing required field: approved (boolean)' });
    }

    console.log(`Processing approval for ad_id=${ad_id}, approved=${approved}`);

    // Update database: approved=true, approved_at=NOW()
    const query = `
      UPDATE ads
      SET
        approved = $1,
        notes = $2,
        approved_at = NOW(),
        status = CASE WHEN $1 = true THEN 'approved' ELSE 'rejected' END
      WHERE ad_id = $3
      RETURNING *
    `;

    const result = await pgPool.query(query, [approved, notes || '', ad_id]);

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Ad not found' });
    }

    console.log(`Ad ${ad_id} ${approved ? 'approved' : 'rejected'} successfully`);

    res.json({
      message: `Ad ${approved ? 'approved' : 'rejected'} successfully`,
      ad: result.rows[0]
    });

  } catch (error: any) {
    console.error('Error processing approval:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// Health check
app.get('/health', async (req: Request, res: Response) => {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    services: {
      redis: false,
      postgres: false
    }
  };

  try {
    // Check Redis
    if (redisClient.isOpen) {
      await redisClient.ping();
      health.services.redis = true;
    }
  } catch (e) {
    console.warn('Health check: Redis failed', e);
  }

  try {
    // Check Postgres
    const pgRes = await pgPool.query('SELECT 1');
    if (pgRes.rowCount === 1) {
      health.services.postgres = true;
    }
  } catch (e) {
    console.warn('Health check: Postgres failed', e);
  }

  // If critical services fail, status could be 'degraded'
  if (!health.services.redis || !health.services.postgres) {
    // For now, we keep it 'healthy' but log the failure to avoid crashing load balancers
    // In strict mode, we might set status to 'degraded'
    console.warn('Service degraded:', health.services);
  }

  res.json(health);
});

app.listen(PORT, () => {
  console.log(`Gateway API listening on port ${PORT}`);
});

export default app;
