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
import { GoogleGenerativeAI } from '@google/generative-ai';

import { ScoringEngine } from './services/scoring-engine';
import { ReliabilityLogger } from './services/reliability-logger';
import { LearningService } from './services/learning-service';
import { adIntelligence, AdIntelligenceService } from './services/ad-intelligence';

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

// Real AI analysis endpoint using Gemini Vision API
app.post('/api/analyze', async (req: Request, res: Response) => {
  try {
    const { video_uri } = req.body;

    // Validate required fields
    if (!video_uri) {
      return res.status(400).json({ error: 'Missing required field: video_uri' });
    }

    // Initialize Gemini API
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      return res.status(500).json({ error: 'GEMINI_API_KEY environment variable not set' });
    }

    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash-exp' });

    console.log(`Analyzing video with Gemini: ${video_uri}`);

    // Call Gemini Vision API for real analysis
    const result = await model.generateContent({
      contents: [{
        role: 'user',
        parts: [{
          text: `Analyze this video ad at ${video_uri}. Return JSON with the following fields:
- hook_style: string (e.g., "High Energy", "Calm", "Dramatic")
- pacing: string (e.g., "Fast", "Medium", "Slow")
- visual_elements: array of strings (key visual components)
- emotional_trigger: string (primary emotion evoked)
- reasoning: string (brief explanation of your analysis)`
        }]
      }],
      generationConfig: {
        responseMimeType: 'application/json'
      }
    });

    // Parse and return AI analysis
    const analysisText = result.response.text();
    const analysis = JSON.parse(analysisText);

    console.log(`Gemini analysis completed for ${video_uri}`);

    res.json(analysis);

  } catch (error: any) {
    console.error('Error in Gemini analysis:', error);
    res.status(500).json({
      error: 'Failed to analyze video',
      details: error.message
    });
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

// Real metrics endpoint - fetches from meta-publisher service
app.get('/api/metrics', async (req: Request, res: Response) => {
  try {
    // Try to fetch real metrics from meta-publisher service
    console.log(`Fetching metrics from meta-publisher: ${META_PUBLISHER_URL}`);

    const response = await axios.get(`${META_PUBLISHER_URL}/api/metrics`, {
      params: req.query,
      timeout: 5000 // 5 second timeout
    });

    console.log('Metrics fetched successfully from meta-publisher');
    res.json(response.data);

  } catch (error: any) {
    console.error('Failed to fetch metrics from meta-publisher:', error.message);

    // Return error instead of fake data
    res.status(503).json({
      error: 'No real metrics available',
      details: `Meta publisher service is not available: ${error.message}`,
      service_url: META_PUBLISHER_URL
    });
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

// ============================================================================
// AD INTELLIGENCE ENDPOINTS - Real data from multiple sources
// ZERO MOCK DATA - Fails loudly if not configured
// ============================================================================

// GET /api/intelligence/status - Check what data sources are configured
app.get('/api/intelligence/status', (req: Request, res: Response) => {
  try {
    const status = adIntelligence.getStatus();
    res.json({
      configured_sources: Object.entries(status).filter(([_, v]) => v.configured).length,
      total_sources: Object.keys(status).length,
      sources: status
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// POST /api/intelligence/search - Search across all configured sources
app.post('/api/intelligence/search', async (req: Request, res: Response) => {
  try {
    const { query, industry, limit } = req.body;

    if (!query) {
      return res.status(400).json({ error: 'MISSING_PARAM: query is required' });
    }

    const result = await adIntelligence.searchAll({ query, industry, limit });
    res.json(result);
  } catch (error: any) {
    // NEVER return mock data - fail loudly
    res.status(503).json({
      error: error.message,
      help: 'Configure at least one data source. Run GET /api/intelligence/status to see options.'
    });
  }
});

// POST /api/intelligence/inject - Inject patterns into knowledge base for immediate use
app.post('/api/intelligence/inject', async (req: Request, res: Response) => {
  try {
    const { query, industry, limit } = req.body;

    if (!query) {
      return res.status(400).json({ error: 'MISSING_PARAM: query is required' });
    }

    // Search for patterns
    const searchResult = await adIntelligence.searchAll({ query, industry, limit: limit || 100 });

    // Inject into knowledge base
    const injectResult = await adIntelligence.injectToKnowledgeBase(searchResult.patterns);

    res.json({
      message: 'Knowledge injected successfully',
      patterns_found: searchResult.patterns.length,
      patterns_injected: injectResult.injected,
      sources_used: searchResult.source_counts,
      file_path: injectResult.file_path,
      errors: searchResult.errors
    });
  } catch (error: any) {
    res.status(503).json({ error: error.message });
  }
});

// GET /api/intelligence/patterns - Extract winning patterns from knowledge base
app.get('/api/intelligence/patterns', async (req: Request, res: Response) => {
  try {
    const industry = req.query.industry as string | undefined;
    const patterns = await adIntelligence.extractWinningPatterns(industry);
    res.json(patterns);
  } catch (error: any) {
    res.status(404).json({
      error: error.message,
      help: 'Run POST /api/intelligence/inject first to build knowledge base'
    });
  }
});

// GET /api/ads/trending - Real trending ads (NO MOCK DATA)
app.get('/api/ads/trending', async (req: Request, res: Response) => {
  try {
    const industry = req.query.industry as string || 'fitness';
    const limit = parseInt(req.query.limit as string) || 20;

    // Try to get real data from intelligence service
    const result = await adIntelligence.searchAll({
      query: industry,
      industry,
      limit
    });

    // Transform to frontend format
    const ads = result.patterns.slice(0, limit).map((p, i) => ({
      id: `${p.source}-${i}`,
      brand: p.raw_data?.page_name || p.raw_data?.brand || `${p.source} ad`,
      title: p.transcript?.slice(0, 50) || p.hook_type,
      views: p.performance_tier === 'top_1_percent' ? '1M+' :
             p.performance_tier === 'top_10_percent' ? '100K+' : 'N/A',
      engagement: p.performance_tier === 'top_1_percent' ? 'Top 1%' :
                  p.performance_tier === 'top_10_percent' ? 'Top 10%' : 'Unknown',
      platform: p.source === 'tiktok' ? 'TikTok' :
                p.source === 'meta_library' ? 'Meta' : 'Foreplay'
    }));

    res.json({ ads, source_counts: result.source_counts });
  } catch (error: any) {
    // NO MOCK DATA - Return honest error
    res.status(503).json({
      error: 'NO_TRENDING_DATA',
      details: error.message,
      help: 'Configure data sources: Set FOREPLAY_API_KEY or META_ACCESS_TOKEN',
      ads: [] // Empty array, not fake data
    });
  }
});

// GET /api/insights/ai - Real AI-powered insights (NO MOCK DATA)
app.get('/api/insights/ai', async (req: Request, res: Response) => {
  try {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      throw new Error('GEMINI_NOT_CONFIGURED: Set GEMINI_API_KEY for AI insights');
    }

    // Get recent prediction data
    const recentPredictions = reliabilityLogger.getReliabilityMetrics();

    // Get winning patterns if available
    let winningPatterns = null;
    try {
      winningPatterns = await adIntelligence.extractWinningPatterns();
    } catch {
      // Knowledge base not populated yet - that's ok
    }

    // Generate real AI insights using Gemini
    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash-exp' });

    const prompt = `Based on this performance data, generate 3 actionable insights for improving video ad performance.

Performance Data:
${JSON.stringify(recentPredictions, null, 2)}

${winningPatterns ? `Winning Patterns from competitors:\n${JSON.stringify(winningPatterns, null, 2)}` : 'No competitor data available yet.'}

Return JSON array with objects containing: id (number), type (tip|warning|success|trend), title (string), description (string), action (string).
Focus on specific, actionable recommendations.`;

    const result = await model.generateContent({
      contents: [{ role: 'user', parts: [{ text: prompt }] }],
      generationConfig: { responseMimeType: 'application/json' }
    });

    const insights = JSON.parse(result.response.text());

    res.json({
      insights: Array.isArray(insights) ? insights : insights.insights || [],
      generated_at: new Date().toISOString(),
      data_sources: {
        predictions: !!recentPredictions,
        competitor_patterns: !!winningPatterns
      }
    });
  } catch (error: any) {
    // NO MOCK DATA - Return honest error
    res.status(503).json({
      error: 'AI_INSIGHTS_UNAVAILABLE',
      details: error.message,
      insights: [] // Empty, not fake
    });
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
