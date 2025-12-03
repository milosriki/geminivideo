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
import rateLimit from 'express-rate-limit';
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
import { kaggleLoader, huggingfaceLoader } from './services/dataset-loaders';
import { youtubeClient } from './services/youtube-client';
import { createCacheService, SemanticCache } from './services/cache-service';
import { CostTracker } from './services/cost-tracker';
import { SmartModelRouter } from './services/smart-router';

const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(cors());
app.use(express.json());

// Rate limiting
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: { error: 'Too many requests, please try again later.' },
  standardHeaders: true,
  legacyHeaders: false,
});

// Apply to all API routes
app.use('/api/', apiLimiter);

// Stricter limit for expensive operations
const heavyLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 10, // 10 requests per minute
  message: { error: 'Rate limit exceeded for this operation.' },
  standardHeaders: true,
  legacyHeaders: false,
});

// Redis client for async queues and caching
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const redisClient = createClient({ url: REDIS_URL });
redisClient.on('error', (err) => console.warn('Redis Client Error (Queue disabled):', err.message));

// Initialize cache service
let cacheService: SemanticCache;

redisClient.connect().then(() => {
  console.log('✅ Redis connected for async queues and caching');
  // Initialize cache service after Redis is connected
  cacheService = createCacheService(redisClient, { prefix: 'geminivideo' });
  console.log('✅ Cache service initialized');
  // Initialize Smart Model Router
  smartRouter = new SmartModelRouter(redisClient);
  console.log('✅ Smart Model Router initialized');
}).catch((err) => {
  console.warn('⚠️ Redis connection failed. Async queues and caching will not work:', err.message);
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

// Verify database connection and initialize jobs table
pgPool.query('SELECT NOW()')
  .then(async () => {
    console.log('✅ PostgreSQL connected');

    // Create jobs table if it doesn't exist
    const createJobsTableQuery = `
      CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL CHECK (type IN ('video', 'image', 'script', 'analysis')),
        name TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
        progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
        created_at TIMESTAMP DEFAULT NOW()
      )
    `;

    await pgPool.query(createJobsTableQuery);
    console.log('✅ Jobs table initialized');

    // Create AI credits tables if they don't exist
    const createCreditsTablesQuery = `
      CREATE TABLE IF NOT EXISTS ai_credits (
        user_id VARCHAR(255) PRIMARY KEY,
        total_credits INTEGER NOT NULL DEFAULT 10000,
        used_credits INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS ai_credit_usage (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(255) NOT NULL,
        credits_used INTEGER NOT NULL,
        operation VARCHAR(100) NOT NULL,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP DEFAULT NOW()
      );

      CREATE INDEX IF NOT EXISTS idx_credit_usage_user ON ai_credit_usage(user_id);
      CREATE INDEX IF NOT EXISTS idx_credit_usage_created ON ai_credit_usage(created_at DESC);
    `;

    await pgPool.query(createCreditsTablesQuery);
    console.log('✅ AI credits tables initialized');

    // Initialize default user with credits if not exists
    const initDefaultUserQuery = `
      INSERT INTO ai_credits (user_id, total_credits, used_credits)
      VALUES ('default_user', 10000, 1500)
      ON CONFLICT (user_id) DO NOTHING;
    `;

    await pgPool.query(initDefaultUserQuery);

    // Seed some sample usage history for the default user (only if no records exist)
    const checkUsageQuery = 'SELECT COUNT(*) as count FROM ai_credit_usage WHERE user_id = $1';
    const usageCount = await pgPool.query(checkUsageQuery, ['default_user']);

    if (parseInt(usageCount.rows[0].count) === 0) {
      const seedUsageQuery = `
        INSERT INTO ai_credit_usage (user_id, credits_used, operation, metadata, created_at)
        VALUES
          ('default_user', 500, 'video_generation', '{"duration": 30, "quality": "hd"}', NOW() - INTERVAL '2 days'),
          ('default_user', 300, 'video_analysis', '{"clips_analyzed": 5}', NOW() - INTERVAL '1 day'),
          ('default_user', 200, 'script_generation', '{"variants": 3}', NOW() - INTERVAL '1 day'),
          ('default_user', 400, 'video_generation', '{"duration": 60, "quality": "4k"}', NOW() - INTERVAL '12 hours'),
          ('default_user', 100, 'text_analysis', '{"words": 500}', NOW() - INTERVAL '6 hours');
      `;

      await pgPool.query(seedUsageQuery);
      console.log('✅ AI credits initialized with sample usage history');
    } else {
      console.log('✅ AI credits tables ready (existing data found)');
    }
  })
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
const costTracker = new CostTracker(pgPool);

// Smart Model Router (initialized after Redis connects)
let smartRouter: SmartModelRouter;

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
app.post('/api/analyze', heavyLimiter, async (req: Request, res: Response) => {
  const startTime = Date.now();
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

    // Record cost (estimate tokens: ~4 chars per token)
    const latency = Date.now() - startTime;
    const estimatedInputTokens = Math.ceil(300 / 4); // Estimated prompt length
    const estimatedOutputTokens = Math.ceil(analysisText.length / 4);
    const totalTokens = estimatedInputTokens + estimatedOutputTokens;

    await costTracker.recordCost(
      'gemini-2.0-flash-exp',
      totalTokens,
      latency,
      'analysis',
      {
        inputTokens: estimatedInputTokens,
        outputTokens: estimatedOutputTokens
      }
    );

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
app.post('/api/render/remix', heavyLimiter, async (req: Request, res: Response) => {
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
app.post('/api/generate', heavyLimiter, async (req: Request, res: Response) => {
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

app.post('/api/render/story_arc', heavyLimiter, async (req: Request, res: Response) => {
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
        SELECT c.clip_id, c.ctr_score, e.emotion_type as emotion
        FROM clips c
        LEFT JOIN emotions e ON c.clip_id = e.clip_id
        WHERE c.asset_id = $1 AND e.emotion_type = $2
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
// GET /api/kpis - KPI summary with period-over-period comparison
app.get('/api/kpis', async (req: Request, res: Response) => {
  try {
    const range = req.query.range as string || '7d';

    // Parse range (e.g., '7d', '30d', '90d')
    const rangeMatch = range.match(/^(\d+)d$/);
    if (!rangeMatch) {
      return res.status(400).json({
        error: 'Invalid range format. Use format like "7d", "30d", "90d"'
      });
    }

    const days = parseInt(rangeMatch[1]);

    console.log(`Fetching KPIs for range: ${days} days`);

    // Query current period
    const currentPeriodQuery = `
      SELECT
        COALESCE(SUM(revenue), 0) as total_revenue,
        COALESCE(SUM(spend), 0) as total_spend,
        COALESCE(SUM(conversions), 0) as total_conversions,
        COALESCE(AVG(ctr), 0) as avg_ctr,
        COALESCE(AVG(cpa), 0) as avg_cpa
      FROM daily_analytics
      WHERE date >= CURRENT_DATE - INTERVAL '1 day' * $1
        AND date < CURRENT_DATE
    `;

    // Query previous period (same length, before current period)
    const previousPeriodQuery = `
      SELECT
        COALESCE(SUM(revenue), 0) as total_revenue,
        COALESCE(SUM(spend), 0) as total_spend,
        COALESCE(SUM(conversions), 0) as total_conversions,
        COALESCE(AVG(ctr), 0) as avg_ctr,
        COALESCE(AVG(cpa), 0) as avg_cpa
      FROM daily_analytics
      WHERE date >= CURRENT_DATE - INTERVAL '1 day' * $1 * 2
        AND date < CURRENT_DATE - INTERVAL '1 day' * $1
    `;

    const [currentResult, previousResult] = await Promise.all([
      pgPool.query(currentPeriodQuery, [days]),
      pgPool.query(previousPeriodQuery, [days])
    ]);

    const current = currentResult.rows[0];
    const previous = previousResult.rows[0];

    // Calculate metrics
    const totalRevenue = parseFloat(current.total_revenue);
    const totalSpend = parseFloat(current.total_spend);
    const totalConversions = parseFloat(current.total_conversions);
    const avgCtr = parseFloat(current.avg_ctr);
    const avgCpa = parseFloat(current.avg_cpa);

    const prevRevenue = parseFloat(previous.total_revenue);
    const prevSpend = parseFloat(previous.total_spend);
    const prevConversions = parseFloat(previous.total_conversions);
    const prevRoas = prevSpend > 0 ? prevRevenue / prevSpend : 0;

    // Calculate ROAS
    const roas = totalSpend > 0 ? totalRevenue / totalSpend : 0;

    // Calculate CPA (if we have conversions)
    const cpa = totalConversions > 0 ? totalSpend / totalConversions : avgCpa;

    // Calculate percent changes
    const revenueChange = prevRevenue > 0
      ? Math.round(((totalRevenue - prevRevenue) / prevRevenue) * 100)
      : 0;

    const spendChange = prevSpend > 0
      ? Math.round(((totalSpend - prevSpend) / prevSpend) * 100)
      : 0;

    const roasChange = prevRoas > 0
      ? Math.round(((roas - prevRoas) / prevRoas) * 100)
      : 0;

    const conversionsChange = prevConversions > 0
      ? Math.round(((totalConversions - prevConversions) / prevConversions) * 100)
      : 0;

    // Return KPIs
    res.json({
      kpis: {
        total_revenue: Math.round(totalRevenue),
        total_spend: Math.round(totalSpend),
        roas: parseFloat(roas.toFixed(2)),
        conversions: Math.round(totalConversions),
        ctr: parseFloat(avgCtr.toFixed(2)),
        cpa: Math.round(cpa),
        revenue_change: revenueChange,
        spend_change: spendChange,
        roas_change: roasChange,
        conversions_change: conversionsChange
      }
    });

  } catch (error: any) {
    console.error('Error fetching KPIs:', error.message);

    // If table doesn't exist or query fails, return zeros
    if (error.message.includes('does not exist') || error.code === '42P01') {
      console.warn('daily_analytics table does not exist, returning zeros');
      res.json({
        kpis: {
          total_revenue: 0,
          total_spend: 0,
          roas: 0,
          conversions: 0,
          ctr: 0,
          cpa: 0,
          revenue_change: 0,
          spend_change: 0,
          roas_change: 0,
          conversions_change: 0
        }
      });
    } else {
      res.status(500).json({ error: error.message });
    }
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
// JOB QUEUE ENDPOINTS - Manage background jobs
// ============================================================================

// GET /api/jobs/pending - Return list of pending/processing jobs
app.get('/api/jobs/pending', async (req: Request, res: Response) => {
  try {
    console.log('Fetching pending/processing jobs');

    // Query database for jobs with pending or processing status
    const query = `
      SELECT
        id,
        type,
        name,
        status,
        progress,
        created_at
      FROM jobs
      WHERE status IN ('pending', 'processing')
      ORDER BY created_at DESC
    `;

    const result = await pgPool.query(query);

    console.log(`Found ${result.rows.length} pending/processing jobs`);

    res.json({
      count: result.rows.length,
      jobs: result.rows.map(row => ({
        id: row.id,
        type: row.type,
        name: row.name,
        status: row.status,
        progress: row.progress || 0,
        createdAt: row.created_at ? new Date(row.created_at).toLocaleString() : 'Just now'
      }))
    });

  } catch (error: any) {
    console.error('Error fetching pending jobs:', error.message);
    res.status(500).json({
      error: 'Failed to fetch pending jobs',
      details: error.message
    });
  }
});

// POST /api/jobs/:id/cancel - Cancel a specific job
app.post('/api/jobs/:id/cancel', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;

    console.log(`Attempting to cancel job: ${id}`);

    // Check if job exists and is cancellable
    const checkQuery = `
      SELECT id, type, name, status
      FROM jobs
      WHERE id = $1
    `;

    const checkResult = await pgPool.query(checkQuery, [id]);

    if (checkResult.rows.length === 0) {
      return res.status(404).json({
        error: 'Job not found',
        job_id: id
      });
    }

    const job = checkResult.rows[0];

    // Check if job is already completed or failed
    if (job.status === 'completed') {
      return res.status(400).json({
        error: 'Cannot cancel completed job',
        job_id: id,
        current_status: job.status
      });
    }

    if (job.status === 'failed') {
      return res.status(400).json({
        error: 'Cannot cancel failed job',
        job_id: id,
        current_status: job.status
      });
    }

    // Update job status to failed (cancelled)
    const updateQuery = `
      UPDATE jobs
      SET status = 'failed',
          progress = 0
      WHERE id = $1
      RETURNING *
    `;

    const updateResult = await pgPool.query(updateQuery, [id]);

    console.log(`Job ${id} cancelled successfully`);

    res.json({
      message: 'Job cancelled successfully',
      job: {
        id: updateResult.rows[0].id,
        type: updateResult.rows[0].type,
        name: updateResult.rows[0].name,
        status: updateResult.rows[0].status,
        progress: updateResult.rows[0].progress,
        created_at: updateResult.rows[0].created_at
      }
    });

  } catch (error: any) {
    console.error('Error cancelling job:', error.message);
    res.status(500).json({
      error: 'Failed to cancel job',
      details: error.message
    });
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
app.post('/api/intelligence/search', heavyLimiter, async (req: Request, res: Response) => {
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
app.post('/api/intelligence/inject', heavyLimiter, async (req: Request, res: Response) => {
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

// ============================================================================
// YOUTUBE API ENDPOINTS - Trending video analysis
// ============================================================================

// GET /api/youtube/trending - Get trending YouTube videos by category/region
app.get('/api/youtube/trending', async (req: Request, res: Response) => {
  try {
    const category = req.query.category as string | undefined;
    const region = req.query.region as string || 'US';
    const limit = parseInt(req.query.limit as string) || 20;

    if (!youtubeClient.isConfigured()) {
      return res.status(503).json({
        error: 'YOUTUBE_NOT_CONFIGURED',
        message: 'Set YOUTUBE_API_KEY environment variable (free from console.cloud.google.com)',
        help: 'Get API key at: https://console.cloud.google.com/apis/credentials'
      });
    }

    const videos = await youtubeClient.getTrendingVideos({
      category,
      region,
      limit
    });

    res.json({
      videos: videos.map(v => ({
        video_id: v.raw_data.video_id,
        title: v.raw_data.title,
        channel: v.raw_data.channel,
        view_count: v.raw_data.view_count,
        like_count: v.raw_data.like_count,
        url: v.raw_data.url,
        hook_type: v.hook_type,
        emotional_triggers: v.emotional_triggers,
        performance_tier: v.performance_tier,
        industry: v.industry
      })),
      metadata: {
        count: videos.length,
        category: category || 'all',
        region,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error: any) {
    res.status(500).json({
      error: 'YOUTUBE_ERROR',
      details: error.message
    });
  }
});

// GET /api/youtube/search - Search YouTube videos by keyword
app.get('/api/youtube/search', async (req: Request, res: Response) => {
  try {
    const query = req.query.q as string;
    const limit = parseInt(req.query.limit as string) || 20;
    const order = req.query.order as 'date' | 'rating' | 'relevance' | 'viewCount' || 'viewCount';

    if (!query) {
      return res.status(400).json({
        error: 'MISSING_PARAM',
        message: 'Query parameter "q" is required'
      });
    }

    if (!youtubeClient.isConfigured()) {
      return res.status(503).json({
        error: 'YOUTUBE_NOT_CONFIGURED',
        message: 'Set YOUTUBE_API_KEY environment variable'
      });
    }

    const videos = await youtubeClient.searchVideos({
      query,
      limit,
      order
    });

    res.json({
      videos: videos.map(v => ({
        video_id: v.raw_data.video_id,
        title: v.raw_data.title,
        channel: v.raw_data.channel,
        view_count: v.raw_data.view_count,
        like_count: v.raw_data.like_count,
        url: v.raw_data.url,
        hook_type: v.hook_type,
        emotional_triggers: v.emotional_triggers,
        performance_tier: v.performance_tier,
        industry: v.industry
      })),
      metadata: {
        count: videos.length,
        query,
        order,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error: any) {
    res.status(500).json({
      error: 'YOUTUBE_SEARCH_ERROR',
      details: error.message
    });
  }
});

// GET /api/youtube/video/:videoId - Get detailed video information
app.get('/api/youtube/video/:videoId', async (req: Request, res: Response) => {
  try {
    const { videoId } = req.params;

    if (!youtubeClient.isConfigured()) {
      return res.status(503).json({
        error: 'YOUTUBE_NOT_CONFIGURED',
        message: 'Set YOUTUBE_API_KEY environment variable'
      });
    }

    const videos = await youtubeClient.getVideoDetails(videoId);

    if (videos.length === 0) {
      return res.status(404).json({
        error: 'VIDEO_NOT_FOUND',
        message: `No video found with ID: ${videoId}`
      });
    }

    const video = videos[0];

    res.json({
      video_id: video.raw_data.video_id,
      title: video.raw_data.title,
      description: video.raw_data.description,
      channel: video.raw_data.channel,
      published_at: video.raw_data.published_at,
      view_count: video.raw_data.view_count,
      like_count: video.raw_data.like_count,
      comment_count: video.raw_data.comment_count,
      duration: video.raw_data.duration,
      tags: video.raw_data.tags,
      url: video.raw_data.url,
      thumbnails: video.raw_data.thumbnails,
      analysis: {
        hook_type: video.hook_type,
        emotional_triggers: video.emotional_triggers,
        visual_style: video.visual_style,
        pacing: video.pacing,
        cta_style: video.cta_style,
        performance_tier: video.performance_tier,
        industry: video.industry
      }
    });
  } catch (error: any) {
    res.status(500).json({
      error: 'YOUTUBE_VIDEO_ERROR',
      details: error.message
    });
  }
});

// GET /api/campaigns - List all campaigns with performance data
app.get('/api/campaigns', async (req: Request, res: Response) => {
  try {
    console.log('Fetching campaigns with performance data');

    // Query campaigns and aggregate performance metrics
    const query = `
      SELECT
        c.id,
        c.name,
        c.status,
        c.budget_daily,
        COALESCE(SUM(pm.spend), 0) as spend,
        COALESCE(SUM(pm.conversions), 0) as conversions,
        COALESCE(SUM(pm.conversions * 300), 0) as revenue,
        CASE
          WHEN COALESCE(SUM(pm.spend), 0) > 0
          THEN ROUND((COALESCE(SUM(pm.conversions * 300), 0) / COALESCE(SUM(pm.spend), 0))::numeric, 2)
          ELSE 0
        END as roas
      FROM campaigns c
      LEFT JOIN videos v ON v.campaign_id = c.id
      LEFT JOIN performance_metrics pm ON pm.video_id = v.id
      GROUP BY c.id, c.name, c.status, c.budget_daily
      ORDER BY c.created_at DESC
    `;

    const result = await pgPool.query(query);

    console.log(`Campaigns fetched: ${result.rows.length} campaigns found`);

    // Transform to expected format
    const campaigns = result.rows.map(row => ({
      id: row.id,
      name: row.name,
      status: row.status,
      spend: parseFloat(row.spend) || 0,
      revenue: parseFloat(row.revenue) || 0,
      roas: parseFloat(row.roas) || 0,
      conversions: parseInt(row.conversions) || 0
    }));

    res.json({ campaigns });

  } catch (error: any) {
    console.error('Error fetching campaigns:', error.message);
    res.status(500).json({
      error: error.message,
      campaigns: [] // Return empty array on error, not mock data
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

// ============================================================================
// DATASET LOADERS - Offline data sources (Kaggle + HuggingFace)
// ============================================================================

// GET /api/datasets/status - Check what datasets are available
app.get('/api/datasets/status', async (req: Request, res: Response) => {
  try {
    const kaggleDatasets = kaggleLoader.getAvailableDatasets();
    const datasetStats = [];

    // Get stats for each dataset
    for (const datasetPath of kaggleDatasets) {
      try {
        const filename = path.basename(datasetPath);
        const stats = await kaggleLoader.getDatasetStats(filename);
        datasetStats.push({
          filename,
          path: datasetPath,
          ...stats
        });
      } catch (error: any) {
        console.warn(`Failed to get stats for ${datasetPath}:`, error.message);
      }
    }

    res.json({
      kaggle: {
        configured: kaggleDatasets.length > 0,
        datasets_count: kaggleDatasets.length,
        datasets: datasetStats,
        data_path: process.env.KAGGLE_DATA_PATH || '/data/kaggle'
      },
      huggingface: {
        configured: huggingfaceLoader.isConfigured(),
        note: huggingfaceLoader.isConfigured()
          ? 'Ready for AI ad generation'
          : 'Set HUGGINGFACE_API_TOKEN (free from huggingface.co)'
      },
      help: kaggleDatasets.length === 0
        ? 'Run scripts/download_datasets.sh to download free datasets'
        : 'All datasets ready for use'
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// POST /api/datasets/import - Import patterns from local datasets
app.post('/api/datasets/import', async (req: Request, res: Response) => {
  try {
    const { source, dataset, industry, limit } = req.body;

    if (!source) {
      return res.status(400).json({ error: 'MISSING_PARAM: source is required (kaggle or huggingface)' });
    }

    let patterns = [];

    if (source === 'kaggle') {
      if (!dataset) {
        return res.status(400).json({ error: 'MISSING_PARAM: dataset filename is required for Kaggle' });
      }

      // Load patterns from specific dataset
      patterns = await kaggleLoader.loadAdDataset(dataset);

      // Filter by industry if specified
      if (industry) {
        patterns = patterns.filter((p: any) =>
          p.industry.toLowerCase().includes(industry.toLowerCase())
        );
      }

      // Apply limit
      if (limit) {
        patterns = patterns.slice(0, parseInt(limit));
      }

    } else if (source === 'huggingface') {
      const { prompt, variant_count } = req.body;

      if (!prompt) {
        return res.status(400).json({ error: 'MISSING_PARAM: prompt is required for HuggingFace' });
      }

      // Generate ad variants
      const variants = await huggingfaceLoader.generateAdVariants(
        prompt,
        variant_count || 3
      );

      // Transform to patterns
      patterns = variants.map((v: string) =>
        huggingfaceLoader.transformToPattern(v, prompt)
      );

      // Set industry if specified
      if (industry) {
        patterns.forEach((p: any) => {
          p.industry = industry;
        });
      }

    } else {
      return res.status(400).json({ error: 'INVALID_SOURCE: source must be kaggle or huggingface' });
    }

    // Inject patterns into knowledge base
    const injectResult = await adIntelligence.injectToKnowledgeBase(patterns);

    res.json({
      message: 'Patterns imported successfully',
      source,
      patterns_loaded: patterns.length,
      patterns_injected: injectResult.injected,
      file_path: injectResult.file_path,
      timestamp: new Date().toISOString()
    });

  } catch (error: any) {
    res.status(500).json({
      error: error.message,
      help: error.message.includes('KAGGLE_FILE_NOT_FOUND')
        ? 'Run scripts/download_datasets.sh to download datasets'
        : error.message.includes('HUGGINGFACE_NOT_CONFIGURED')
        ? 'Set HUGGINGFACE_API_TOKEN environment variable'
        : undefined
    });
  }
});

// POST /api/datasets/generate-variants - Generate ad variants using HuggingFace
app.post('/api/datasets/generate-variants', heavyLimiter, async (req: Request, res: Response) => {
  try {
    const { prompt, count, analyze } = req.body;

    if (!prompt) {
      return res.status(400).json({ error: 'MISSING_PARAM: prompt is required' });
    }

    if (!huggingfaceLoader.isConfigured()) {
      return res.status(503).json({
        error: 'HUGGINGFACE_NOT_CONFIGURED',
        help: 'Set HUGGINGFACE_API_TOKEN (free from huggingface.co)'
      });
    }

    // Generate variants
    const variants = await huggingfaceLoader.generateAdVariants(prompt, count || 3);

    // Optionally analyze each variant
    let analyzed = [];
    if (analyze) {
      for (const variant of variants) {
        try {
          const analysis = await huggingfaceLoader.analyzeAdText(variant);
          analyzed.push({
            text: variant,
            ...analysis
          });
        } catch (error) {
          analyzed.push({
            text: variant,
            error: 'Analysis failed'
          });
        }
      }
    }

    res.json({
      prompt,
      variants: analyze ? analyzed : variants,
      count: variants.length,
      generated_at: new Date().toISOString()
    });

  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// GET /api/insights/ai - Real AI-powered insights (NO MOCK DATA)
app.get('/api/insights/ai', heavyLimiter, async (req: Request, res: Response) => {
  const startTime = Date.now();
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

    const responseText = result.response.text();
    const insights = JSON.parse(responseText);

    // Record cost
    const latency = Date.now() - startTime;
    const estimatedTokens = Math.ceil((prompt.length + responseText.length) / 4);
    await costTracker.recordCost(
      'gemini-2.0-flash-exp',
      estimatedTokens,
      latency,
      'insights'
    );

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

// ============================================================================
// FEEDBACK LOOP ENDPOINTS - Learning from actual performance
// ============================================================================

// POST /api/feedback - Record prediction vs actual performance
app.post('/api/feedback', async (req: Request, res: Response) => {
  try {
    const { video_id, prediction_id, predicted_ctr, actual_ctr } = req.body;

    // Validate required fields
    if (!video_id || !prediction_id || predicted_ctr === undefined || actual_ctr === undefined) {
      return res.status(400).json({
        error: 'Missing required fields',
        required: ['video_id', 'prediction_id', 'predicted_ctr', 'actual_ctr']
      });
    }

    console.log(`Recording feedback: video_id=${video_id}, predicted=${predicted_ctr}, actual=${actual_ctr}`);

    // Insert into feedback_events table
    const feedbackQuery = `
      INSERT INTO feedback_events (video_id, prediction_id, predicted_ctr, actual_ctr, created_at)
      VALUES ($1, $2, $3, $4, NOW())
      RETURNING id, created_at
    `;

    const feedbackResult = await pgPool.query(feedbackQuery, [
      video_id,
      prediction_id,
      predicted_ctr,
      actual_ctr
    ]);

    // If actual_ctr > 0.03 (3%), add to winning_patterns
    if (actual_ctr > 0.03) {
      console.log(`High-performing ad detected (CTR=${actual_ctr}), adding to winning_patterns`);

      const patternQuery = `
        INSERT INTO winning_patterns (
          source,
          performance_tier,
          ctr,
          raw_data,
          created_at
        )
        VALUES ($1, $2, $3, $4, NOW())
        RETURNING id
      `;

      const performanceTier = actual_ctr > 0.10 ? 'top_1_percent' :
                               actual_ctr > 0.05 ? 'top_10_percent' : 'average';

      await pgPool.query(patternQuery, [
        'internal',
        performanceTier,
        actual_ctr,
        JSON.stringify({
          video_id,
          prediction_id,
          predicted_ctr,
          actual_ctr,
          captured_at: new Date().toISOString()
        })
      ]);

      console.log(`Added to winning_patterns as ${performanceTier}`);
    }

    res.status(201).json({
      message: 'Feedback recorded successfully',
      feedback_id: feedbackResult.rows[0].id,
      recorded_at: feedbackResult.rows[0].created_at,
      added_to_patterns: actual_ctr > 0.03
    });

  } catch (error: any) {
    console.error('Error recording feedback:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// POST /api/model-performance - Record model accuracy
app.post('/api/model-performance', async (req: Request, res: Response) => {
  try {
    const { model_name, predicted_value, actual_value, latency_ms, cost_usd } = req.body;

    // Validate required fields
    if (!model_name || predicted_value === undefined || actual_value === undefined) {
      return res.status(400).json({
        error: 'Missing required fields',
        required: ['model_name', 'predicted_value', 'actual_value']
      });
    }

    // Calculate error
    const error = Math.abs(predicted_value - actual_value);

    console.log(`Recording model performance: model=${model_name}, error=${error.toFixed(4)}`);

    // Insert into model_performance table
    const query = `
      INSERT INTO model_performance (
        model_name,
        predicted_value,
        actual_value,
        error,
        latency_ms,
        cost_usd,
        created_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, NOW())
      RETURNING id, created_at
    `;

    const result = await pgPool.query(query, [
      model_name,
      predicted_value,
      actual_value,
      error,
      latency_ms || null,
      cost_usd || null
    ]);

    res.status(201).json({
      message: 'Model performance recorded successfully',
      performance_id: result.rows[0].id,
      recorded_at: result.rows[0].created_at,
      error
    });

  } catch (error: any) {
    console.error('Error recording model performance:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// GET /api/feedback/summary - Get feedback summary
app.get('/api/feedback/summary', async (req: Request, res: Response) => {
  try {
    const days = parseInt(req.query.days as string) || 30;

    console.log(`Fetching feedback summary for last ${days} days`);

    // Query feedback_summary view
    const query = `
      SELECT
        date,
        feedback_count,
        avg_predicted,
        avg_actual,
        avg_error,
        correlation
      FROM feedback_summary
      WHERE date >= NOW() - INTERVAL '1 day' * $1
      ORDER BY date DESC
    `;

    const result = await pgPool.query(query, [days]);

    // Calculate overall statistics
    const overall = {
      total_feedback: result.rows.reduce((sum, row) => sum + parseInt(row.feedback_count), 0),
      avg_correlation: result.rows.length > 0
        ? result.rows.reduce((sum, row) => sum + (parseFloat(row.correlation) || 0), 0) / result.rows.length
        : null,
      avg_error: result.rows.length > 0
        ? result.rows.reduce((sum, row) => sum + parseFloat(row.avg_error), 0) / result.rows.length
        : null
    };

    res.json({
      days,
      overall,
      daily_summary: result.rows.map(row => ({
        date: row.date,
        count: parseInt(row.feedback_count),
        avg_predicted: parseFloat(row.avg_predicted),
        avg_actual: parseFloat(row.avg_actual),
        avg_error: parseFloat(row.avg_error),
        correlation: row.correlation ? parseFloat(row.correlation) : null
      }))
    });

  } catch (error: any) {
    console.error('Error fetching feedback summary:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// GET /api/model-performance/:model - Get model calibration
app.get('/api/model-performance/:model', async (req: Request, res: Response) => {
  try {
    const { model } = req.params;
    const days = parseInt(req.query.days as string) || 30;

    console.log(`Fetching performance metrics for model: ${model} (last ${days} days)`);

    // Query model_performance for last N days
    const query = `
      SELECT
        COUNT(*) as prediction_count,
        AVG(ABS(predicted_value - actual_value)) as mae,
        STDDEV(predicted_value - actual_value) as std_error,
        AVG(CASE WHEN ABS(predicted_value - actual_value) < 0.02 THEN 1.0 ELSE 0.0 END) as accuracy_2pct,
        AVG(latency_ms) as avg_latency,
        SUM(cost_usd) as total_cost,
        MIN(created_at) as first_prediction,
        MAX(created_at) as last_prediction
      FROM model_performance
      WHERE model_name = $1
        AND created_at >= NOW() - INTERVAL '1 day' * $2
        AND actual_value IS NOT NULL
    `;

    const result = await pgPool.query(query, [model, days]);

    if (result.rows.length === 0 || parseInt(result.rows[0].prediction_count) === 0) {
      return res.status(404).json({
        error: 'No performance data found',
        model,
        days
      });
    }

    const metrics = result.rows[0];

    // Get recent predictions for trend analysis
    const recentQuery = `
      SELECT
        DATE(created_at) as date,
        AVG(ABS(predicted_value - actual_value)) as daily_mae,
        COUNT(*) as daily_count
      FROM model_performance
      WHERE model_name = $1
        AND created_at >= NOW() - INTERVAL '1 day' * $2
        AND actual_value IS NOT NULL
      GROUP BY DATE(created_at)
      ORDER BY date DESC
      LIMIT 7
    `;

    const recentResult = await pgPool.query(recentQuery, [model, days]);

    res.json({
      model,
      period_days: days,
      summary: {
        prediction_count: parseInt(metrics.prediction_count),
        mae: parseFloat(metrics.mae),
        std_error: metrics.std_error ? parseFloat(metrics.std_error) : null,
        accuracy_within_2pct: parseFloat(metrics.accuracy_2pct),
        avg_latency_ms: metrics.avg_latency ? parseFloat(metrics.avg_latency) : null,
        total_cost_usd: metrics.total_cost ? parseFloat(metrics.total_cost) : null,
        first_prediction: metrics.first_prediction,
        last_prediction: metrics.last_prediction
      },
      recent_trend: recentResult.rows.map(row => ({
        date: row.date,
        mae: parseFloat(row.daily_mae),
        count: parseInt(row.daily_count)
      }))
    });

  } catch (error: any) {
    console.error('Error fetching model performance:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// COST TRACKING ENDPOINTS - Monitor and project AI API costs
// ============================================================================

// GET /api/costs/daily - Get daily cost breakdown
app.get('/api/costs/daily', async (req: Request, res: Response) => {
  try {
    const days = parseInt(req.query.days as string) || 30;

    console.log(`Fetching daily costs for last ${days} days`);

    const dailyCosts = await costTracker.getDailyCosts(days);

    res.json({
      days,
      total_entries: dailyCosts.length,
      daily_costs: dailyCosts
    });

  } catch (error: any) {
    console.error('Error fetching daily costs:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// GET /api/costs/by-model - Get costs by model
app.get('/api/costs/by-model', async (req: Request, res: Response) => {
  try {
    const days = parseInt(req.query.days as string) || 30;
    const model = req.query.model as string | undefined;

    console.log(`Fetching model costs for last ${days} days${model ? ` (model: ${model})` : ''}`);

    const modelCosts = await costTracker.getModelCosts(model, days);

    res.json({
      days,
      model: model || 'all',
      total_models: modelCosts.length,
      model_costs: modelCosts
    });

  } catch (error: any) {
    console.error('Error fetching model costs:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// GET /api/costs/total - Get total spend summary
app.get('/api/costs/total', async (req: Request, res: Response) => {
  try {
    const days = parseInt(req.query.days as string) || 30;

    console.log(`Fetching total spend for last ${days} days`);

    const totalSpend = await costTracker.getTotalSpend(days);

    res.json({
      days,
      ...totalSpend
    });

  } catch (error: any) {
    console.error('Error fetching total spend:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// GET /api/costs/projection - Get cost projections
app.get('/api/costs/projection', async (req: Request, res: Response) => {
  try {
    const days = parseInt(req.query.days as string) || 30;

    console.log(`Calculating cost projection based on last ${days} days`);

    const projection = await costTracker.getCostProjection(days);

    res.json({
      based_on_days: days,
      ...projection,
      generated_at: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('Error calculating cost projection:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// GET /api/costs/pricing - Get model pricing information
app.get('/api/costs/pricing', (req: Request, res: Response) => {
  try {
    const pricing = costTracker.getModelPricing();

    res.json({
      pricing_per_1k_tokens: pricing,
      note: 'Prices shown are approximate blended rates for input/output tokens'
    });

  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// ANALYTICS CHART ENDPOINT - Real performance data visualization
// ============================================================================

// GET /api/analytics/chart - Get chart data for date range
app.get('/api/analytics/chart', async (req: Request, res: Response) => {
  try {
    const range = (req.query.range as string) || '7d';

    console.log(`Fetching analytics chart data for range: ${range}`);

    // Parse range parameter to days
    let days: number;
    if (range === '24h') {
      days = 1;
    } else if (range === '7d') {
      days = 7;
    } else if (range === '30d') {
      days = 30;
    } else if (range === '90d') {
      days = 90;
    } else {
      return res.status(400).json({
        error: 'Invalid range parameter',
        valid_ranges: ['24h', '7d', '30d', '90d']
      });
    }

    // Create daily_analytics table if it doesn't exist
    const createTableQuery = `
      CREATE TABLE IF NOT EXISTS daily_analytics (
        id SERIAL PRIMARY KEY,
        date DATE NOT NULL UNIQUE,
        spend DECIMAL(10, 2) NOT NULL DEFAULT 0,
        revenue DECIMAL(10, 2) NOT NULL DEFAULT 0,
        impressions INTEGER NOT NULL DEFAULT 0,
        clicks INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      );

      CREATE INDEX IF NOT EXISTS idx_daily_analytics_date ON daily_analytics(date);
    `;

    await pgPool.query(createTableQuery);

    // Query analytics data for the specified range
    const query = `
      SELECT
        date,
        spend,
        revenue,
        impressions,
        clicks
      FROM daily_analytics
      WHERE date >= CURRENT_DATE - INTERVAL '1 day' * $1
      ORDER BY date ASC
    `;

    const result = await pgPool.query(query, [days]);

    // Format data for chart
    const chart = result.rows.map(row => {
      const spend = parseFloat(row.spend);
      const revenue = parseFloat(row.revenue);
      const roas = spend > 0 ? revenue / spend : 0;

      // Format date as "Nov 27"
      const dateObj = new Date(row.date);
      const formattedDate = dateObj.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      });

      return {
        date: formattedDate,
        spend: spend,
        revenue: revenue,
        roas: parseFloat(roas.toFixed(2)),
        impressions: parseInt(row.impressions),
        clicks: parseInt(row.clicks)
      };
    });

    console.log(`Analytics chart fetched: ${chart.length} data points`);

    res.json({
      chart: chart,
      metadata: {
        range: range,
        days: days,
        data_points: chart.length,
        fetched_at: new Date().toISOString()
      }
    });

  } catch (error: any) {
    console.error('Error fetching analytics chart:', error.message);
    res.status(500).json({
      error: 'Failed to fetch analytics chart',
      details: error.message,
      chart: [] // Return empty array on error, not mock data
    });
  }
});

// ============================================================================
// SMART MODEL ROUTER ENDPOINT - Cost-aware multi-model evaluation
// ============================================================================

// POST /api/evaluate - Smart evaluation with cost-aware routing
app.post('/api/evaluate', heavyLimiter, async (req: Request, res: Response) => {
  try {
    const { content, evaluation_type, min_confidence } = req.body;

    // Validate required fields
    if (!content) {
      return res.status(400).json({
        error: 'Missing required field: content',
        required: ['content'],
        optional: ['evaluation_type', 'min_confidence']
      });
    }

    // Check if smartRouter is initialized
    if (!smartRouter) {
      return res.status(503).json({
        error: 'Smart Model Router not initialized',
        details: 'Redis connection required. Check Redis status.'
      });
    }

    console.log('Smart evaluation request: type=' + (evaluation_type || 'ad_score') + ', min_confidence=' + (min_confidence || 0.85));

    // Call Smart Model Router
    const result = await smartRouter.evaluateWithSmartRouting(
      content,
      evaluation_type || 'ad_score',
      min_confidence || 0.85
    );

    // Record cost tracking
    if (result.total_cost > 0) {
      try {
        await costTracker.recordModelCost({
          model: result.models_used.join(','),
          operation: evaluation_type || 'ad_score',
          tokens_in: 0, // Estimated internally
          tokens_out: 0,
          cost_usd: result.total_cost,
          latency_ms: result.total_latency_ms,
          metadata: {
            models_used: result.models_used,
            cache_hit: result.cache_hit,
            early_exit: result.early_exit
          }
        });
      } catch (trackError: any) {
        console.warn('Failed to record cost tracking:', trackError.message);
      }
    }

    res.json({
      score: result.score,
      confidence: result.confidence,
      reasoning: result.reasoning,
      models_used: result.models_used,
      cost_usd: result.total_cost,
      latency_ms: result.total_latency_ms,
      cache_hit: result.cache_hit,
      early_exit: result.early_exit,
      timestamp: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('Error in smart evaluation:', error.message);
    res.status(500).json({
      error: 'Evaluation failed',
      details: error.message
    });
  }
});

// GET /api/evaluate/cost-report - Get cost and performance report
app.get('/api/evaluate/cost-report', (req: Request, res: Response) => {
  try {
    if (!smartRouter) {
      return res.status(503).json({
        error: 'Smart Model Router not initialized'
      });
    }

    const report = smartRouter.getCostReport();
    res.json({
      ...report,
      timestamp: new Date().toISOString()
    });
  } catch (error: any) {
    console.error('Error getting cost report:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// ANALYTICS PERFORMANCE ENDPOINT - Performance metrics by day
// ============================================================================

// GET /api/analytics/performance - Get performance metrics by day
app.get('/api/analytics/performance', async (req: Request, res: Response) => {
  try {
    const days = parseInt(req.query.days as string) || 7;

    console.log(`Fetching performance metrics for last ${days} days`);

    // Ensure performance_metrics table exists
    const createTableQuery = `
      CREATE TABLE IF NOT EXISTS performance_metrics (
        id SERIAL PRIMARY KEY,
        date DATE NOT NULL,
        spend NUMERIC(10, 2) NOT NULL DEFAULT 0,
        revenue NUMERIC(10, 2) NOT NULL DEFAULT 0,
        clicks INTEGER NOT NULL DEFAULT 0,
        impressions INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(date)
      )
    `;

    await pgPool.query(createTableQuery);
    console.log('performance_metrics table ready');

    // Query performance data for last N days
    const query = `
      SELECT
        date,
        spend,
        revenue,
        clicks,
        impressions
      FROM performance_metrics
      WHERE date >= CURRENT_DATE - INTERVAL '1 day' * $1
      ORDER BY date ASC
    `;

    const result = await pgPool.query(query, [days]);

    // Transform data: calculate ROAS and format by day name
    const data = result.rows.map(row => {
      const date = new Date(row.date);
      const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const dayName = dayNames[date.getDay()];

      const spend = parseFloat(row.spend);
      const revenue = parseFloat(row.revenue);
      const roas = spend > 0 ? revenue / spend : 0;

      return {
        day: dayName,
        roas: parseFloat(roas.toFixed(2)),
        spend: spend,
        revenue: revenue,
        clicks: parseInt(row.clicks)
      };
    });

    console.log(`Performance data fetched: ${data.length} days`);

    res.json({ data });

  } catch (error: any) {
    console.error('Error fetching performance metrics:', error.message);
    res.status(500).json({
      error: 'Failed to fetch performance metrics',
      details: error.message
    });
  }
});

// ============================================================================
// AI CREDITS ENDPOINTS - Track and manage AI credit usage
// ============================================================================

// GET /api/credits - Get user's AI credit balance and usage history
app.get('/api/credits', async (req: Request, res: Response) => {
  try {
    // Use default user since auth isn't implemented
    const userId = req.query.user_id as string || 'default_user';

    console.log(`Fetching AI credits for user: ${userId}`);

    // Get user's credit balance
    const creditsQuery = `
      SELECT
        user_id,
        total_credits,
        used_credits,
        (total_credits - used_credits) as available_credits,
        created_at,
        updated_at
      FROM ai_credits
      WHERE user_id = $1
    `;

    const creditsResult = await pgPool.query(creditsQuery, [userId]);

    if (creditsResult.rows.length === 0) {
      // Initialize new user with default credits
      const initQuery = `
        INSERT INTO ai_credits (user_id, total_credits, used_credits)
        VALUES ($1, 10000, 0)
        RETURNING user_id, total_credits, used_credits, (total_credits - used_credits) as available_credits, created_at, updated_at
      `;

      const initResult = await pgPool.query(initQuery, [userId]);
      const newUser = initResult.rows[0];

      return res.json({
        credits: {
          available: newUser.available_credits,
          total: newUser.total_credits,
          used: newUser.used_credits,
          usage_history: []
        }
      });
    }

    const credits = creditsResult.rows[0];

    // Get usage history (last 30 days)
    const usageQuery = `
      SELECT
        DATE(created_at) as date,
        SUM(credits_used) as used,
        operation,
        metadata
      FROM ai_credit_usage
      WHERE user_id = $1
        AND created_at >= NOW() - INTERVAL '30 days'
      GROUP BY DATE(created_at), operation, metadata, created_at
      ORDER BY created_at DESC
      LIMIT 50
    `;

    const usageResult = await pgPool.query(usageQuery, [userId]);

    // Format usage history
    const usageHistory = usageResult.rows.map(row => ({
      date: row.date.toISOString().split('T')[0],
      used: parseInt(row.used),
      operation: row.operation,
      ...(row.metadata && Object.keys(row.metadata).length > 0 ? row.metadata : {})
    }));

    res.json({
      credits: {
        available: parseInt(credits.available_credits),
        total: parseInt(credits.total_credits),
        used: parseInt(credits.used_credits),
        usage_history: usageHistory
      }
    });

    console.log(`Credits fetched successfully for user: ${userId}`);

  } catch (error: any) {
    console.error('Error fetching AI credits:', error.message);
    res.status(500).json({
      error: 'Failed to fetch AI credits',
      details: error.message
    });
  }
});

// POST /api/credits/deduct - Deduct credits for an operation (internal use)
app.post('/api/credits/deduct', async (req: Request, res: Response) => {
  try {
    const { user_id, credits, operation, metadata } = req.body;

    // Validate required fields
    if (!user_id || !credits || !operation) {
      return res.status(400).json({
        error: 'Missing required fields',
        required: ['user_id', 'credits', 'operation']
      });
    }

    console.log(`Deducting ${credits} credits for user ${user_id} (${operation})`);

    // Check if user has enough credits
    const checkQuery = `
      SELECT total_credits, used_credits
      FROM ai_credits
      WHERE user_id = $1
    `;

    const checkResult = await pgPool.query(checkQuery, [user_id]);

    if (checkResult.rows.length === 0) {
      return res.status(404).json({
        error: 'User not found',
        user_id
      });
    }

    const currentCredits = checkResult.rows[0];
    const available = currentCredits.total_credits - currentCredits.used_credits;

    if (available < credits) {
      return res.status(402).json({
        error: 'Insufficient credits',
        available,
        requested: credits
      });
    }

    // Deduct credits
    const deductQuery = `
      UPDATE ai_credits
      SET used_credits = used_credits + $1,
          updated_at = NOW()
      WHERE user_id = $2
      RETURNING total_credits, used_credits, (total_credits - used_credits) as available_credits
    `;

    const deductResult = await pgPool.query(deductQuery, [credits, user_id]);

    // Log usage
    const logQuery = `
      INSERT INTO ai_credit_usage (user_id, credits_used, operation, metadata, created_at)
      VALUES ($1, $2, $3, $4, NOW())
      RETURNING id, created_at
    `;

    await pgPool.query(logQuery, [
      user_id,
      credits,
      operation,
      metadata ? JSON.stringify(metadata) : '{}'
    ]);

    const updatedCredits = deductResult.rows[0];

    res.json({
      message: 'Credits deducted successfully',
      credits: {
        available: parseInt(updatedCredits.available_credits),
        total: parseInt(updatedCredits.total_credits),
        used: parseInt(updatedCredits.used_credits)
      }
    });

    console.log(`Credits deducted: ${credits} from user ${user_id}. New balance: ${updatedCredits.available_credits}`);

  } catch (error: any) {
    console.error('Error deducting credits:', error.message);
    res.status(500).json({
      error: 'Failed to deduct credits',
      details: error.message
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

// Cache statistics endpoint
app.get('/api/cache/stats', async (req: Request, res: Response) => {
  try {
    if (!cacheService) {
      return res.status(503).json({
        error: 'Cache service not available',
        details: 'Redis connection may have failed'
      });
    }

    const stats = await cacheService.getCacheStats();
    res.json(stats);
  } catch (error: any) {
    console.error('Error fetching cache stats:', error);
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Gateway API listening on port ${PORT}`);
});

export default app;
