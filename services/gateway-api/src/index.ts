/**
 * Gateway API - Prediction & Scoring Engine
 * Unified proxy to internal services with scoring capabilities
 * Enhanced with comprehensive security middleware (Agent 5)
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

// Security middleware imports (Agent 5)
import {
  initializeSecurityRedis,
  securityHeaders,
  corsConfig,
  globalRateLimiter,
  authRateLimiter,
  apiRateLimiter,
  uploadRateLimiter,
  validateInput,
  sqlInjectionProtection,
  xssProtection,
  auditLog,
  bruteForceProtection,
  validateApiKey
} from './middleware/security';

const app = express();
const PORT = process.env.PORT || 8000;

// ============================================================================
// SECURITY MIDDLEWARE LAYER (Agent 5 - OWASP Best Practices)
// ============================================================================

// 1. Security Headers - Must be first
app.use(securityHeaders);

// 2. CORS Configuration - Secure cross-origin requests
app.use(cors(corsConfig));

// 3. Body Parser - Parse JSON with size limits
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 4. Audit Logging - Log all requests
app.use(auditLog);

// 5. Global Rate Limiting - Prevent abuse
app.use(globalRateLimiter);

// 6. SQL Injection Protection - Sanitize inputs
app.use(sqlInjectionProtection);

// 7. XSS Protection - Sanitize HTML
app.use(xssProtection);

// Initialize security Redis for distributed rate limiting
initializeSecurityRedis().catch(err => {
  console.warn('Security Redis initialization failed:', err.message);
});

// Redis client for async queues
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const redisClient = createClient({ url: REDIS_URL });
redisClient.on('error', (err) => console.error('Redis Client Error', err));
redisClient.connect().then(() => {
  console.log('✅ Redis connected for async queues');
});

// PostgreSQL client for database access
const DATABASE_URL = process.env.DATABASE_URL;
if (!DATABASE_URL) {
  console.error('❌ DATABASE_URL environment variable is required');
  console.error('Example: postgresql://user:password@host:5432/dbname');
  process.exit(1);
}

const pgPool = new Pool({ connectionString: DATABASE_URL });
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
app.post('/api/analyze',
  apiRateLimiter,
  validateInput({
    body: {
      path: { type: 'string', required: true, min: 1, max: 1000 },
      filename: { type: 'string', required: true, min: 1, max: 255 },
      size_bytes: { type: 'number', required: false, min: 0 },
      duration_seconds: { type: 'number', required: false, min: 0 }
    }
  }),
  async (req: Request, res: Response) => {
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

app.post('/api/ingest/local/folder',
  uploadRateLimiter,
  validateInput({
    body: {
      folder_path: { type: 'string', required: true, min: 1, max: 1000 },
      max_files: { type: 'number', required: false, min: 1, max: 1000 }
    }
  }),
  async (req: Request, res: Response) => {
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

app.post('/api/search/clips',
  apiRateLimiter,
  validateInput({
    body: {
      query: { type: 'string', required: true, min: 1, max: 500, sanitize: true },
      filters: { type: 'object', required: false },
      limit: { type: 'number', required: false, min: 1, max: 100 }
    }
  }),
  async (req: Request, res: Response) => {
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
app.post('/api/score/storyboard',
  apiRateLimiter,
  validateInput({
    body: {
      scenes: { type: 'array', required: true },
      metadata: { type: 'object', required: false }
    }
  }),
  async (req: Request, res: Response) => {
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
app.post('/api/render/remix',
  uploadRateLimiter,
  validateInput({
    body: {
      clip_ids: { type: 'array', required: true },
      transitions: { type: 'boolean', required: false },
      output_format: { type: 'string', required: false, enum: ['mp4', 'webm', 'mov'] }
    }
  }),
  async (req: Request, res: Response) => {
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

// Story Arc rendering endpoint - creates ads from templates
app.post('/api/render/story_arc',
  uploadRateLimiter,
  validateInput({
    body: {
      arc_name: { type: 'string', required: false, min: 1, max: 100 },
      asset_id: { type: 'uuid', required: true }
    }
  }),
  async (req: Request, res: Response) => {
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
app.post('/api/publish/meta',
  uploadRateLimiter,
  validateInput({
    body: {
      video_path: { type: 'string', required: true, min: 1, max: 1000 },
      caption: { type: 'string', required: false, max: 2200, sanitize: true },
      scheduled_time: { type: 'string', required: false }
    }
  }),
  async (req: Request, res: Response) => {
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
app.post('/api/trigger/analyze-drive-folder',
  authRateLimiter,
  bruteForceProtection({ freeRetries: 3 }),
  validateInput({
    body: {
      folder_id: { type: 'string', required: true, min: 1, max: 200 },
      max_videos: { type: 'number', required: false, min: 1, max: 1000 }
    }
  }),
  async (req: Request, res: Response) => {
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
app.post('/api/trigger/refresh-meta-metrics',
  authRateLimiter,
  bruteForceProtection({ freeRetries: 3 }),
  validateInput({
    body: {
      days_back: { type: 'number', required: false, min: 1, max: 365 }
    }
  }),
  async (req: Request, res: Response) => {
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
app.post('/api/approval/approve/:ad_id',
  authRateLimiter,
  validateInput({
    params: {
      ad_id: { type: 'uuid', required: true }
    },
    body: {
      approved: { type: 'boolean', required: true },
      notes: { type: 'string', required: false, max: 1000, sanitize: true }
    }
  }),
  async (req: Request, res: Response) => {
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
// META ADS LIBRARY ENDPOINTS (Agent 26 - Ad Spy Dashboard)
// ============================================================================

const TITAN_CORE_URL = process.env.TITAN_CORE_URL || 'http://localhost:8004';

// POST /api/meta/ads-library/search
// Search Meta Ads Library with filters
app.post('/api/meta/ads-library/search',
  apiRateLimiter,
  validateInput({
    body: {
      search_terms: { type: 'string', required: false, min: 1, max: 500, sanitize: true },
      countries: { type: 'array', required: false },
      platforms: { type: 'array', required: false },
      media_type: { type: 'string', required: false, enum: ['ALL', 'VIDEO', 'IMAGE'] },
      active_status: { type: 'string', required: false, enum: ['ALL', 'ACTIVE', 'INACTIVE'] },
      limit: { type: 'number', required: false, min: 1, max: 200 }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    const {
      search_terms,
      countries = ['US'],
      platforms = ['facebook', 'instagram'],
      media_type = 'ALL',
      active_status = 'ACTIVE',
      limit = 100
    } = req.body;

    console.log(`Searching Meta Ads Library: "${search_terms}", countries: ${countries}, limit: ${limit}`);

    // Forward to Titan Core Meta Ads Library scraper
    const response = await axios.post(`${TITAN_CORE_URL}/meta/ads-library/search`, {
      search_terms,
      countries,
      platforms,
      media_type,
      active_status,
      limit
    }, {
      timeout: 60000 // 60 second timeout for API calls
    });

    res.json(response.data);

  } catch (error: any) {
    console.error('Meta Ads Library search error:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.message,
      details: error.response?.data || 'Search failed'
    });
  }
});

// GET /api/meta/ads-library/page/:page_id
// Get all ads from a specific Facebook/Instagram page
app.get('/api/meta/ads-library/page/:page_id',
  apiRateLimiter,
  validateInput({
    params: {
      page_id: { type: 'string', required: true, min: 1, max: 100 }
    },
    query: {
      limit: { type: 'number', required: false, min: 1, max: 200 },
      active_only: { type: 'boolean', required: false }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    const { page_id } = req.params;
    const { limit = 100, active_only = true } = req.query;

    console.log(`Fetching ads for page: ${page_id}`);

    const response = await axios.get(`${TITAN_CORE_URL}/meta/ads-library/page/${page_id}`, {
      params: { limit, active_only },
      timeout: 60000
    });

    res.json(response.data);

  } catch (error: any) {
    console.error('Page ads fetch error:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.message,
      details: error.response?.data || 'Failed to fetch page ads'
    });
  }
});

// POST /api/meta/ads-library/analyze
// Analyze patterns across multiple ads
app.post('/api/meta/ads-library/analyze',
  apiRateLimiter,
  validateInput({
    body: {
      ads: { type: 'array', required: true, min: 1, max: 500 }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    const { ads } = req.body;

    console.log(`Analyzing patterns for ${ads.length} ads`);

    const response = await axios.post(`${TITAN_CORE_URL}/meta/ads-library/analyze`, {
      ads
    }, {
      timeout: 30000
    });

    res.json(response.data);

  } catch (error: any) {
    console.error('Pattern analysis error:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.message,
      details: error.response?.data || 'Analysis failed'
    });
  }
});

// GET /api/meta/ads-library/ad/:ad_archive_id
// Get detailed information for a specific ad
app.get('/api/meta/ads-library/ad/:ad_archive_id',
  apiRateLimiter,
  validateInput({
    params: {
      ad_archive_id: { type: 'string', required: true, min: 1, max: 100 }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    const { ad_archive_id } = req.params;

    console.log(`Fetching details for ad: ${ad_archive_id}`);

    const response = await axios.get(`${TITAN_CORE_URL}/meta/ads-library/ad/${ad_archive_id}`, {
      timeout: 30000
    });

    res.json(response.data);

  } catch (error: any) {
    console.error('Ad details fetch error:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.message,
      details: error.response?.data || 'Failed to fetch ad details'
    });
  }
});

// POST /api/meta/ads-library/batch
// Batch scrape multiple search terms
app.post('/api/meta/ads-library/batch',
  apiRateLimiter,
  validateInput({
    body: {
      queries: { type: 'array', required: true, min: 1, max: 50 },
      countries: { type: 'array', required: false },
      limit_per_query: { type: 'number', required: false, min: 1, max: 100 }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    const { queries, countries = ['US'], limit_per_query = 50 } = req.body;

    console.log(`Batch scraping ${queries.length} queries`);

    const response = await axios.post(`${TITAN_CORE_URL}/meta/ads-library/batch`, {
      queries,
      countries,
      limit_per_query
    }, {
      timeout: 120000 // 2 minute timeout for batch operations
    });

    res.json(response.data);

  } catch (error: any) {
    console.error('Batch scrape error:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.message,
      details: error.response?.data || 'Batch scrape failed'
    });
  }
});

// Health check
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, () => {
  console.log(`Gateway API listening on port ${PORT}`);
});

export default app;
