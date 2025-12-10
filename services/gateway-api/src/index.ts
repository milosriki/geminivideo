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
  console.warn('Security Redis initialization failed (non-fatal):', err.message);
});

// Redis client for async queues (optional - graceful degradation)
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const REDIS_ENABLED = process.env.REDIS_ENABLED !== 'false';
let redisClient: ReturnType<typeof createClient> | null = null;
let redisConnected = false;

if (REDIS_ENABLED) {
  redisClient = createClient({ url: REDIS_URL });
  redisClient.on('error', (err) => {
    if (redisConnected) {
      console.error('Redis Client Error:', err.message);
    }
    // Don't spam logs if Redis is unavailable
  });
  redisClient.connect()
    .then(() => {
      redisConnected = true;
      console.log('✅ Redis connected for async queues');
    })
    .catch((err) => {
      console.warn('⚠️ Redis connection failed (Queue disabled):', err.message);
      redisClient = null;
    });
} else {
  console.log('ℹ️ Redis disabled via REDIS_ENABLED=false');
}

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
const TITAN_CORE_URL = process.env.TITAN_CORE_URL || 'http://titan-core:8000';
const META_PUBLISHER_URL = process.env.META_PUBLISHER_URL || 'http://localhost:8083';
const GOOGLE_ADS_URL = process.env.GOOGLE_ADS_URL || 'http://localhost:8084';

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
        parsed.hostname.includes('google-ads') ||
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

      // Push job to Redis queue (if available)
      if (redisClient && redisConnected) {
        await redisClient.rPush('analysis_queue', assetId);
      } else {
        console.warn('⚠️ Redis unavailable - job queued in DB only');
      }

      // Return immediately with 202 Accepted
      res.status(202).json({
        asset_id: assetId,
        status: 'QUEUED',
        message: redisClient ? 'Analysis job queued successfully' : 'Analysis job queued (sync mode - no Redis)'
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
      const scores = await scoringEngine.scoreStoryboard(scenes, metadata);

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

      // Push to render queue (if available)
      if (redisClient && redisConnected) {
        await redisClient.rPush('render_queue', JSON.stringify(renderJob));
      } else {
        console.warn('⚠️ Redis unavailable - render job not queued');
      }

      // Return job info
      res.status(202).json({
        job_id: jobId,
        status: redisClient ? 'QUEUED' : 'PENDING',
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
// CRITICAL SECURITY: Approval gate for €5M investment protection
app.post('/api/publish/meta',
  uploadRateLimiter,
  validateInput({
    body: {
      ad_id: { type: 'uuid', required: true },
      video_path: { type: 'string', required: true, min: 1, max: 1000 },
      caption: { type: 'string', required: false, max: 2200, sanitize: true },
      scheduled_time: { type: 'string', required: false }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const { ad_id, video_path, caption, scheduled_time } = req.body;

      // ====================================================================
      // SECURITY GATE: Check if ad is approved before publishing to Meta
      // ====================================================================
      console.log(`[SECURITY] Checking approval status for ad_id=${ad_id}`);

      const approvalQuery = `
        SELECT ad_id, approved, status, asset_id, arc_name, predicted_ctr, predicted_roas
        FROM ads
        WHERE ad_id = $1
      `;

      const approvalResult = await pgPool.query(approvalQuery, [ad_id]);

      if (approvalResult.rows.length === 0) {
        console.error(`[SECURITY] Ad not found: ad_id=${ad_id}`);
        return res.status(404).json({
          error: 'Ad not found',
          message: 'The specified ad does not exist in the system'
        });
      }

      const ad = approvalResult.rows[0];

      // CRITICAL CHECK: Must be approved AND status must be 'approved'
      if (!ad.approved || ad.status !== 'approved') {
        console.error(`[SECURITY] UNAUTHORIZED PUBLISH ATTEMPT BLOCKED: ad_id=${ad_id}, approved=${ad.approved}, status=${ad.status}`);

        // Log the unauthorized attempt
        const auditQuery = `
          INSERT INTO audit_log (event_type, ad_id, details, timestamp)
          VALUES ($1, $2, $3, NOW())
        `;

        await pgPool.query(auditQuery, [
          'UNAUTHORIZED_PUBLISH_ATTEMPT',
          ad_id,
          JSON.stringify({
            approved: ad.approved,
            status: ad.status,
            video_path,
            ip_address: req.ip,
            user_agent: req.get('user-agent')
          })
        ]).catch(err => {
          console.warn('[AUDIT] Failed to log unauthorized attempt:', err.message);
        });

        return res.status(403).json({
          error: 'Forbidden',
          message: 'This ad has not been approved for publishing',
          details: {
            ad_id,
            approved: ad.approved,
            status: ad.status,
            required_status: 'approved'
          }
        });
      }

      console.log(`[SECURITY] Ad approved for publishing: ad_id=${ad_id}, predicted_ctr=${ad.predicted_ctr}, predicted_roas=${ad.predicted_roas}`);

      // ====================================================================
      // AUDIT TRAIL: Log successful publish attempt
      // ====================================================================

      // Extract user ID from request context (if available from auth middleware)
      const userId = (req as any).user?.id || 'system';

      // Update approved_by field
      const updateQuery = `
        UPDATE ads
        SET
          approved_by = $1,
          published_at = NOW(),
          status = 'published'
        WHERE ad_id = $2
      `;

      await pgPool.query(updateQuery, [userId, ad_id]);

      // Log the publish event
      const publishAuditQuery = `
        INSERT INTO audit_log (event_type, ad_id, user_id, details, timestamp)
        VALUES ($1, $2, $3, $4, NOW())
      `;

      await pgPool.query(publishAuditQuery, [
        'PUBLISH_INITIATED',
        ad_id,
        userId,
        JSON.stringify({
          // ====================================================================

          const response = await axios.post(
            `${META_PUBLISHER_URL}/publish/meta`,
            {
              ad_id,
              video_path,
              caption,
              scheduled_time
            }
          );

          console.log(`[SUCCESS] Ad published to Meta: ad_id=${ad_id}, meta_response=${response.status}`);

          res.json({
            ...response.data,
            security_check: {
              approved: true,
              approved_by: userId,
              published_at: new Date().toISOString()
            }
          });

        } catch (error: any) {
          console.error('[ERROR] Publish failed:', error.message);
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

// ============================================================================
// GOOGLE ADS INTEGRATION ENDPOINTS (Agent 13)
// ============================================================================

// Create Google Ads Campaign
app.post('/api/google-ads/campaigns',
  uploadRateLimiter,
  validateInput({
    body: {
      name: { type: 'string', required: true, min: 1, max: 255 },
      budget: { type: 'number', required: true, min: 1 },
      biddingStrategy: { type: 'string', required: false },
      startDate: { type: 'string', required: false },
      endDate: { type: 'string', required: false },
      status: { type: 'string', required: false, enum: ['ACTIVE', 'PAUSED'] }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      if (!validateServiceUrl(GOOGLE_ADS_URL)) {
        throw new Error('Invalid service URL');
      }
      const response = await axios.post(
        `${GOOGLE_ADS_URL}/api/campaigns`,
        req.body
      );
      res.json(response.data);
    } catch (error: any) {
      res.status(error.response?.status || 500).json({
        error: error.message,
        details: error.response?.data
      });
    }
  });

// Create Google Ads Ad Group
app.post('/api/google-ads/ad-groups',
  uploadRateLimiter,
  validateInput({
    body: {
      name: { type: 'string', required: true, min: 1, max: 255 },
      campaignId: { type: 'string', required: true },
      cpcBidMicros: { type: 'number', required: true, min: 1 },
      status: { type: 'string', required: false, enum: ['ACTIVE', 'PAUSED'] }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      if (!validateServiceUrl(GOOGLE_ADS_URL)) {
        throw new Error('Invalid service URL');
      }
      const response = await axios.post(
        `${GOOGLE_ADS_URL}/api/ad-groups`,
        req.body
      );
      res.json(response.data);
    } catch (error: any) {
      res.status(error.response?.status || 500).json({
        error: error.message,
        details: error.response?.data
      });
    }
  });

// Upload Creative to Google Ads (YouTube)
app.post('/api/google-ads/upload-creative',
  uploadRateLimiter,
  validateInput({
    body: {
      videoPath: { type: 'string', required: true, min: 1, max: 1000 },
      title: { type: 'string', required: false, max: 100, sanitize: true },
      description: { type: 'string', required: false, max: 5000, sanitize: true }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      if (!validateServiceUrl(GOOGLE_ADS_URL)) {
        throw new Error('Invalid service URL');
      }
      const response = await axios.post(
        `${GOOGLE_ADS_URL}/api/upload-creative`,
        req.body
      );
      res.json(response.data);
    } catch (error: any) {
      res.status(error.response?.status || 500).json({
        error: error.message,
        details: error.response?.data
      });
    }
  });

// Create Google Ads Video Ad
app.post('/api/google-ads/video-ads',
  uploadRateLimiter,
  validateInput({
    body: {
      videoPath: { type: 'string', required: true, min: 1, max: 1000 },
      campaignId: { type: 'string', required: true },
      adGroupId: { type: 'string', required: true },
      headline: { type: 'string', required: true, min: 1, max: 100, sanitize: true },
      description: { type: 'string', required: false, max: 1000, sanitize: true },
      finalUrl: { type: 'string', required: true, min: 1, max: 1000 }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      if (!validateServiceUrl(GOOGLE_ADS_URL)) {
        throw new Error('Invalid service URL');
      }
      const response = await axios.post(
        `${GOOGLE_ADS_URL}/api/video-ads`,
        req.body
      );
      res.json(response.data);
    } catch (error: any) {
      res.status(error.response?.status || 500).json({
        error: error.message,
        details: error.response?.data
      });
    }
  });

// Get Google Ads Campaign Performance
app.get('/api/google-ads/performance/campaign/:campaignId',
  apiRateLimiter,
  validateInput({
    params: {
      campaignId: { type: 'string', required: true }
    },
    query: {
      startDate: { type: 'string', required: false },
      endDate: { type: 'string', required: false }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      if (!validateServiceUrl(GOOGLE_ADS_URL)) {
        throw new Error('Invalid service URL');
      }
      const { campaignId } = req.params;
      const response = await axios.get(
        `${GOOGLE_ADS_URL}/api/performance/campaign/${campaignId}`,
        { params: req.query }
      );
      res.json(response.data);
    } catch (error: any) {
      res.status(error.response?.status || 500).json({
        error: error.message,
        details: error.response?.data
      });
    }
  });

// Get Google Ads Ad Performance
app.get('/api/google-ads/performance/ad/:adId',
  apiRateLimiter,
  validateInput({
    params: {
      adId: { type: 'string', required: true }
    },
    query: {
      startDate: { type: 'string', required: false },
      endDate: { type: 'string', required: false }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      if (!validateServiceUrl(GOOGLE_ADS_URL)) {
        throw new Error('Invalid service URL');
      }
      const { adId } = req.params;
      const response = await axios.get(
        `${GOOGLE_ADS_URL}/api/performance/ad/${adId}`,
        { params: req.query }
      );
      res.json(response.data);
    } catch (error: any) {
      res.status(error.response?.status || 500).json({
        error: error.message,
        details: error.response?.data
      });
    }
  });

// Publish to Google Ads (Complete Workflow)
app.post('/api/google-ads/publish',
  uploadRateLimiter,
  validateInput({
    body: {
      videoPath: { type: 'string', required: true, min: 1, max: 1000 },
      campaignName: { type: 'string', required: true, min: 1, max: 255 },
      budget: { type: 'number', required: true, min: 1 },
      adGroupName: { type: 'string', required: true, min: 1, max: 255 },
      cpcBidMicros: { type: 'number', required: true, min: 1 },
      headline: { type: 'string', required: true, min: 1, max: 100, sanitize: true },
      description: { type: 'string', required: false, max: 1000, sanitize: true },
      finalUrl: { type: 'string', required: true, min: 1, max: 1000 }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      if (!validateServiceUrl(GOOGLE_ADS_URL)) {
        throw new Error('Invalid service URL');
      }
      const response = await axios.post(
        `${GOOGLE_ADS_URL}/api/publish`,
        req.body
      );
      res.json(response.data);
    } catch (error: any) {
      res.status(error.response?.status || 500).json({
        error: error.message,
        details: error.response?.data
      });
    }
  });

// Update Google Ads Ad Status
app.patch('/api/google-ads/ads/:adId/status',
  apiRateLimiter,
  validateInput({
    params: {
      adId: { type: 'string', required: true }
    },
    body: {
      status: { type: 'string', required: true, enum: ['ENABLED', 'PAUSED'] }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      if (!validateServiceUrl(GOOGLE_ADS_URL)) {
        throw new Error('Invalid service URL');
      }
      const { adId } = req.params;
      const response = await axios.patch(
        `${GOOGLE_ADS_URL}/api/ads/${adId}/status`,
        req.body
      );
      res.json(response.data);
    } catch (error: any) {
      res.status(error.response?.status || 500).json({
        error: error.message,
        details: error.response?.data
      });
    }
  });

// Update Google Ads Campaign Budget
app.patch('/api/google-ads/campaigns/:campaignId/budget',
  apiRateLimiter,
  validateInput({
    params: {
      campaignId: { type: 'string', required: true }
    },
    body: {
      budget: { type: 'number', required: true, min: 1 }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      if (!validateServiceUrl(GOOGLE_ADS_URL)) {
        throw new Error('Invalid service URL');
      }
      const { campaignId } = req.params;
      const response = await axios.patch(
        `${GOOGLE_ADS_URL}/api/campaigns/${campaignId}/budget`,
        req.body
      );
      res.json(response.data);
    } catch (error: any) {
      res.status(error.response?.status || 500).json({
        error: error.message,
        details: error.response?.data
      });
    }
  });

// Get Google Ads Account Info
app.get('/api/google-ads/account/info',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      if (!validateServiceUrl(GOOGLE_ADS_URL)) {
        throw new Error('Invalid service URL');
      }
      const response = await axios.get(
        `${GOOGLE_ADS_URL}/api/account/info`
      );
      res.json(response.data);
    } catch (error: any) {
      res.status(error.response?.status || 500).json({
        error: error.message,
        details: error.response?.data
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

      // Call drive-intel service bulk-analyze endpoint
      const response = await axios.post(`${DRIVE_INTEL_URL}/api/bulk-analyze`, {
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

// ============================================================================
// FRONTEND INTEGRATION ENDPOINTS
// ============================================================================

// POST /api/generate - Generate video creatives (Studio Page)
app.post('/api/generate',
  uploadRateLimiter,
  validateInput({
    body: {
      assets: { type: 'array', required: true },
      target_audience: { type: 'string', required: false, max: 500 }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const { assets, target_audience } = req.body;

      // Validate assets exist
      if (!assets || assets.length === 0) {
        return res.status(400).json({
          error: 'No assets provided',
          message: 'Please upload or select videos first'
        });
      }

      console.log(`Generating creatives for ${assets.length} asset(s), audience: ${target_audience || 'general'}`);

      // Forward to titan-core for Gemini generation
      const response = await axios.post(`${TITAN_CORE_URL}/pipeline/generate-campaign`, {
        video_files: assets,
        audience: target_audience || 'general',
        platform: 'reels'
      }, {
        timeout: 120000 // 2 min timeout for video generation
      });

      res.json({
        status: 'success',
        video_uri: response.data.video_uri || assets[0],
        job_id: response.data.job_id,
        message: 'Creative generation started'
      });

    } catch (error: any) {
      console.error('Generation error:', error.message);
      res.status(500).json({
        error: 'Generation failed',
        message: error.message,
        details: error.response?.data
      });
    }
  });

// GET /api/experiments - Fetch A/B test experiments (AB Testing Dashboard)
app.get('/api/experiments', async (req: Request, res: Response) => {
  try {
    console.log('Fetching A/B test experiments from campaigns');

    // Query campaign_outcomes table for real experiment data
    const query = `
      WITH numbered_variants AS (
        SELECT
          co.id,
          co.campaign_id,
          co.impressions,
          co.clicks,
          co.conversions,
          co.spend,
          co.roas,
          co.created_at,
          ROW_NUMBER() OVER (PARTITION BY co.campaign_id ORDER BY co.created_at) as variant_num
        FROM campaign_outcomes co
      )
      SELECT
        c.id as id,
        c.name,
        c.status,
        c.created_at as "startDate",
        'conversions' as objective,
        c.budget_daily as "totalBudget",
        json_agg(json_build_object(
          'id', nv.id,
          'name', c.name || ' - Variant ' || nv.variant_num,
          'impressions', COALESCE(nv.impressions, 0),
          'clicks', COALESCE(nv.clicks, 0),
          'conversions', COALESCE(nv.conversions, 0),
          'spend', COALESCE(nv.spend, 0),
          'revenue', COALESCE(nv.roas * nv.spend, 0),
          'alpha', COALESCE(nv.clicks, 0) + 1,
          'beta', (COALESCE(nv.impressions, 0) - COALESCE(nv.clicks, 0)) + 1
        )) FILTER (WHERE nv.id IS NOT NULL) as variants
      FROM campaigns c
      LEFT JOIN numbered_variants nv ON c.id = nv.campaign_id
      WHERE c.status IN ('active', 'running', 'paused')
      GROUP BY c.id, c.name, c.status, c.created_at, c.budget_daily
      ORDER BY c.created_at DESC
      LIMIT 10
    `;

    const result = await pgPool.query(query);

    const experiments = result.rows.map(row => ({
      id: row.id,
      name: row.name,
      status: row.status === 'active' ? 'running' : row.status,
      variants: row.variants || [],
      startDate: row.startDate,
      totalBudget: parseFloat(row.totalBudget) || 5000,
      explorationRate: 20 // Default Thompson Sampling exploration rate
    }));

    console.log(`Found ${experiments.length} experiments with ${experiments.reduce((sum, exp) => sum + (exp.variants?.length || 0), 0)} total variants`);

    res.json(experiments);

  } catch (error: any) {
    console.error('Error fetching experiments:', error);
    res.status(500).json({
      error: error.message,
      experiments: [] // Return empty array on error
    });
  }
});

// GET /api/ab-tests - Alternative endpoint for AB tests (proxies to ML service)
app.get('/api/ab-tests', async (req: Request, res: Response) => {
  try {
    console.log('Fetching AB tests from ML service');

    const response = await axios.get(`${ML_SERVICE_URL}/api/ml/ab/experiments`, {
      timeout: 30000
    });

    res.json(response.data);

  } catch (error: any) {
    console.warn('ML service unavailable, falling back to database:', error.message);

    // Fallback to database query
    try {
      const dbQuery = `
        SELECT
          c.id,
          c.name,
          c.status,
          c.created_at,
          c.budget_daily as total_budget,
          COUNT(DISTINCT co.id) as variant_count
        FROM campaigns c
        LEFT JOIN campaign_outcomes co ON c.id = co.campaign_id
        WHERE c.status IN ('active', 'running', 'paused')
        GROUP BY c.id, c.name, c.status, c.created_at, c.budget_daily
        ORDER BY c.created_at DESC
        LIMIT 20
      `;

      const result = await pgPool.query(dbQuery);

      res.json({
        experiments: result.rows.map(row => ({
          experiment_id: row.id,
          experiment_name: row.name,
          status: row.status,
          created_at: row.created_at,
          total_budget: parseFloat(row.total_budget) || 5000,
          variant_count: parseInt(row.variant_count) || 0
        })),
        count: result.rows.length
      });

    } catch (dbError: any) {
      console.error('Database fallback failed:', dbError);
      res.status(500).json({
        error: 'Failed to fetch AB tests',
        experiments: [],
        count: 0
      });
    }
  }
});

// GET /api/ab-tests/:id/results - Get detailed AB test results
app.get('/api/ab-tests/:id/results', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    console.log(`Fetching AB test results for experiment: ${id}`);

    const response = await axios.get(`${ML_SERVICE_URL}/api/ml/ab/experiments/${id}/results`, {
      timeout: 30000
    });

    res.json(response.data);

  } catch (error: any) {
    console.error('Error fetching AB test results:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.message,
      details: error.response?.data || 'Failed to fetch AB test results'
    });
  }
});

// GET /api/ab-tests/:id/variants - Get variant performance data
app.get('/api/ab-tests/:id/variants', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    console.log(`Fetching variant performance for experiment: ${id}`);

    const response = await axios.get(`${ML_SERVICE_URL}/api/ml/ab/experiments/${id}/variants`, {
      timeout: 30000
    });

    res.json(response.data);

  } catch (error: any) {
    console.error('Error fetching variant data:', error.message);
    res.status(error.response?.status || 500).json({
      error: error.message,
      details: error.response?.data || 'Failed to fetch variant data'
    });
  }
});

// GET /api/insights/ai - Real-time AI insights (Dashboard)
app.get('/api/insights/ai', async (req: Request, res: Response) => {
  try {
    console.log('Fetching AI insights from Titan Core');

    // Forward to titan-core for Gemini analysis
    const response = await axios.get(`${TITAN_CORE_URL}/insights/generate`, {
      params: { context: 'dashboard' },
      timeout: 30000
    });

    res.json(response.data);

  } catch (error: any) {
    console.warn('Titan Core insights unavailable, returning fallback:', error.message);

    // Fallback to basic insights if Titan is down
    res.json({
      insights: [
        {
          type: 'info',
          title: 'System Status',
          description: 'All services operational. Advanced AI insights temporarily unavailable.',
          priority: 'low',
          timestamp: new Date().toISOString()
        },
        {
          type: 'success',
          title: 'Backend Services',
          description: '6/7 services running on Cloud Run with real integrations.',
          priority: 'medium',
          timestamp: new Date().toISOString()
        }
      ]
    });
  }
});

// GET /api/ads/trending - Meta Ads Library trending ads (Ad Spy Page)
app.get('/api/ads/trending', async (req: Request, res: Response) => {
  try {
    const { category = 'fitness', limit = 10 } = req.query;

    console.log(`Fetching trending ads: category=${category}, limit=${limit}`);

    // Use existing Meta Ads Library endpoint
    const response = await axios.post(`${TITAN_CORE_URL}/meta/ads-library/search`, {
      search_terms: category,
      countries: ['US'],
      platforms: ['facebook', 'instagram'],
      media_type: 'VIDEO',
      active_status: 'ACTIVE',
      limit: parseInt(limit as string) || 10
    }, {
      timeout: 60000
    });

    res.json(response.data.ads || []);

  } catch (error: any) {
    console.error('Error fetching trending ads:', error.message);
    res.status(500).json({
      error: error.message,
      ads: [] // Return empty array on error
    });
  }
});

// GET /avatars - List available avatars (Studio Page)
app.get('/avatars', async (req: Request, res: Response) => {
  try {
    console.log('Fetching avatars list');

    // Forward to titan-core which has avatar config
    const response = await axios.get(`${TITAN_CORE_URL}/avatars/list`, {
      timeout: 10000
    });

    res.json(response.data);

  } catch (error: any) {
    console.warn('Titan Core avatars unavailable, returning fallback:', error.message);

    // Fallback to basic avatar list
    res.json([
      { key: 'avatar-1', name: 'Sarah', voice: 'natural-female', style: 'professional' },
      { key: 'avatar-2', name: 'James', voice: 'natural-male', style: 'authoritative' },
      { key: 'avatar-3', name: 'Emily', voice: 'professional', style: 'friendly' },
      { key: 'avatar-4', name: 'Marcus', voice: 'energetic', style: 'dynamic' }
    ]);
  }
});

// ============================================================================
// AI COUNCIL ENDPOINTS (Titan Core Integration)
// ============================================================================

// POST /api/council/evaluate - AI Council creative evaluation
app.post('/api/council/evaluate',
  apiRateLimiter,
  validateInput({
    body: {
      creative_id: { type: 'string', required: false, min: 1, max: 100 },
      video_uri: { type: 'string', required: false, min: 1, max: 1000 },
      metadata: { type: 'object', required: false }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const { creative_id, video_uri, metadata } = req.body;

      if (!creative_id && !video_uri) {
        return res.status(400).json({
          error: 'Either creative_id or video_uri is required'
        });
      }

      console.log(`AI Council evaluation: creative_id=${creative_id || 'N/A'}, video_uri=${video_uri || 'N/A'}`);

      // Forward to Titan Core AI Council
      const response = await axios.post(`${TITAN_CORE_URL}/council/evaluate`, {
        creative_id,
        video_uri,
        metadata
      }, {
        timeout: 60000 // 60 second timeout for AI evaluation
      });

      res.json(response.data);

    } catch (error: any) {
      console.error('AI Council evaluation error:', error.message);
      res.status(error.response?.status || 500).json({
        error: 'Evaluation failed',
        message: error.message,
        details: error.response?.data
      });
    }
  });

// POST /api/oracle/predict - Oracle predictive analytics
app.post('/api/oracle/predict',
  apiRateLimiter,
  validateInput({
    body: {
      campaign_data: { type: 'object', required: true },
      prediction_type: { type: 'string', required: false, enum: ['ctr', 'roas', 'conversions', 'all'] }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const { campaign_data, prediction_type = 'all' } = req.body;

      if (!campaign_data || Object.keys(campaign_data).length === 0) {
        return res.status(400).json({
          error: 'campaign_data is required and cannot be empty'
        });
      }

      console.log(`Oracle prediction: type=${prediction_type}, data_keys=${Object.keys(campaign_data).length}`);

      // Forward to Titan Core Oracle
      const response = await axios.post(`${TITAN_CORE_URL}/oracle/predict`, {
        campaign_data,
        prediction_type
      }, {
        timeout: 45000 // 45 second timeout for predictions
      });

      res.json(response.data);

    } catch (error: any) {
      console.error('Oracle prediction error:', error.message);
      res.status(error.response?.status || 500).json({
        error: 'Prediction failed',
        message: error.message,
        details: error.response?.data
      });
    }
  });

// POST /api/director/generate - Director creative generation
app.post('/api/director/generate',
  uploadRateLimiter,
  validateInput({
    body: {
      brief: { type: 'string', required: true, min: 10, max: 5000, sanitize: true },
      assets: { type: 'array', required: false },
      style: { type: 'string', required: false, max: 100 },
      duration: { type: 'number', required: false, min: 5, max: 300 }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const { brief, assets, style, duration } = req.body;

      if (!brief || brief.trim().length < 10) {
        return res.status(400).json({
          error: 'Brief is required and must be at least 10 characters'
        });
      }

      console.log(`Director generation: brief_length=${brief.length}, assets=${assets?.length || 0}, style=${style || 'auto'}`);

      // Forward to Titan Core Director
      const response = await axios.post(`${TITAN_CORE_URL}/director/generate`, {
        brief,
        assets: assets || [],
        style: style || 'auto',
        duration: duration || 30
      }, {
        timeout: 180000 // 3 minute timeout for creative generation
      });

      res.status(202).json({
        status: 'accepted',
        message: 'Creative generation started',
        job_id: response.data.job_id,
        estimated_time: response.data.estimated_time || '2-5 minutes',
        data: response.data
      });

    } catch (error: any) {
      console.error('Director generation error:', error.message);
      res.status(error.response?.status || 500).json({
        error: 'Generation failed',
        message: error.message,
        details: error.response?.data
      });
    }
  });

// Titan-Core Proxy Routes
app.post('/api/titan/council/evaluate', async (req, res) => {
  try {
    const response = await fetch(`${TITAN_CORE_URL}/api/titan/council/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });
    const data = await response.json();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/titan/director/generate', async (req, res) => {
  try {
    const response = await fetch(`${TITAN_CORE_URL}/api/titan/director/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });
    const data = await response.json();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/titan/oracle/predict', async (req, res) => {
  try {
    const response = await fetch(`${TITAN_CORE_URL}/api/titan/oracle/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });
    const data = await response.json();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// POST /api/pipeline/generate-campaign - Full campaign generation pipeline
app.post('/api/pipeline/generate-campaign',
  uploadRateLimiter,
  validateInput({
    body: {
      video_files: { type: 'array', required: true, min: 1 },
      audience: { type: 'string', required: false, max: 500 },
      platform: { type: 'string', required: false, enum: ['reels', 'stories', 'feed', 'tiktok', 'youtube'] },
      campaign_objective: { type: 'string', required: false, enum: ['conversions', 'traffic', 'awareness', 'engagement'] }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const { video_files, audience, platform = 'reels', campaign_objective = 'conversions' } = req.body;

      if (!video_files || video_files.length === 0) {
        return res.status(400).json({
          error: 'At least one video file is required'
        });
      }

      console.log(`Pipeline campaign generation: videos=${video_files.length}, audience=${audience || 'general'}, platform=${platform}`);

      // Forward to Titan Core Pipeline
      const response = await axios.post(`${TITAN_CORE_URL}/pipeline/generate-campaign`, {
        video_files,
        audience: audience || 'general',
        platform,
        campaign_objective
      }, {
        timeout: 180000 // 3 minute timeout for full pipeline
      });

      res.status(202).json({
        status: 'accepted',
        message: 'Campaign generation pipeline started',
        job_id: response.data.job_id,
        campaign_id: response.data.campaign_id,
        estimated_time: response.data.estimated_time || '3-7 minutes',
        data: response.data
      });

    } catch (error: any) {
      console.error('Pipeline generation error:', error.message);
      res.status(error.response?.status || 500).json({
        error: 'Pipeline failed',
        message: error.message,
        details: error.response?.data
      });
    }
  });

// ============================================================================
// ML SERVICE PROXIES (Agent 16 - Critical ML Intelligence Endpoints)
// ============================================================================

// POST /api/ml/predict-ctr - CTR prediction
app.post('/api/ml/predict-ctr',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/predict-ctr`, req.body, { timeout: 30000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('ML CTR prediction error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'CTR prediction failed', details: error.response?.data });
    }
  });

// POST /api/ml/feedback - Learning loop feedback
app.post('/api/ml/feedback',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/feedback`, req.body, { timeout: 30000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('ML feedback error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Feedback submission failed', details: error.response?.data });
    }
  });

// POST /api/ml/ab/select-variant - Thompson Sampling variant selection
app.post('/api/ml/ab/select-variant',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/ab/select-variant`, req.body, { timeout: 10000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('ML variant selection error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Variant selection failed', details: error.response?.data });
    }
  });

// POST /api/ml/ab/register-variant - Register A/B test variant
app.post('/api/ml/ab/register-variant',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/ab/register-variant`, req.body, { timeout: 10000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('ML register variant error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Variant registration failed', details: error.response?.data });
    }
  });

// POST /api/ml/ab/update-variant - Update variant performance
app.post('/api/ml/ab/update-variant',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/ab/update-variant`, req.body, { timeout: 10000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('ML update variant error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Variant update failed', details: error.response?.data });
    }
  });

// GET /api/ml/ab/variant-stats/:variant_id - Get variant statistics
app.get('/api/ml/ab/variant-stats/:variant_id',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.get(`${ML_SERVICE_URL}/api/ml/ab/variant-stats/${req.params.variant_id}`, { timeout: 10000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('ML variant stats error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Failed to get variant stats', details: error.response?.data });
    }
  });

// GET /api/ml/ab/all-variants - Get all variants
app.get('/api/ml/ab/all-variants',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.get(`${ML_SERVICE_URL}/api/ml/ab/all-variants`, { timeout: 10000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('ML all variants error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Failed to get variants', details: error.response?.data });
    }
  });

// POST /api/ml/ab/apply-decay - Apply time decay for ad fatigue
app.post('/api/ml/ab/apply-decay',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/ab/apply-decay`, null, {
        params: req.query,
        timeout: 30000
      });
      res.json(response.data);
    } catch (error: any) {
      console.error('ML time decay error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Time decay failed', details: error.response?.data });
    }
  });

// ============================================================================
// RAG WINNER MEMORY ENDPOINTS (Agent 50)
// Persistent memory for winning ads with GCS + Redis
// ============================================================================

// POST /api/ml/rag/search-winners - Search similar winning ads
app.post('/api/ml/rag/search-winners',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/rag/search-winners`, req.body, { timeout: 30000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('RAG search error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'RAG search failed', details: error.response?.data });
    }
  });

// POST /api/ml/rag/index-winner - Add winning ad to memory
app.post('/api/ml/rag/index-winner',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/rag/index-winner`, req.body, { timeout: 30000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('RAG indexing error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'RAG indexing failed', details: error.response?.data });
    }
  });

// GET /api/ml/rag/memory-stats - Get RAG memory statistics
app.get('/api/ml/rag/memory-stats',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.get(`${ML_SERVICE_URL}/api/ml/rag/memory-stats`, { timeout: 10000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('RAG stats error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'RAG stats failed', details: error.response?.data });
    }
  });

// GET /api/ml/rag/winner/:ad_id - Get specific winner from memory
app.get('/api/ml/rag/winner/:ad_id',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.get(`${ML_SERVICE_URL}/api/ml/rag/winner/${req.params.ad_id}`, { timeout: 10000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('RAG retrieval error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'RAG retrieval failed', details: error.response?.data });
    }
  });

// DELETE /api/ml/rag/clear-cache - Clear Redis cache
app.delete('/api/ml/rag/clear-cache',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.delete(`${ML_SERVICE_URL}/api/ml/rag/clear-cache`, { timeout: 10000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('RAG cache clear error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Cache clear failed', details: error.response?.data });
    }
  });

// ============================================================================
// SELF-LEARNING LOOPS 4-7: CREATIVE DNA, COMPOUND LEARNER, ACTUALS, AUTO-PROMOTER
// All 7 loops for maximum self-upgrading intelligence
// ============================================================================

// Creative DNA (Loop 4) - Extract WHY ads win
app.post('/api/ml/dna/extract',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/dna/extract`, req.body, { timeout: 30000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('Creative DNA extraction error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'DNA extraction failed', details: error.response?.data });
    }
  });

app.post('/api/ml/dna/build-formula',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/dna/build-formula`, req.body, { timeout: 60000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('DNA formula build error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Formula build failed', details: error.response?.data });
    }
  });

app.post('/api/ml/dna/apply',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/dna/apply`, req.body, { timeout: 30000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('DNA application error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'DNA application failed', details: error.response?.data });
    }
  });

app.post('/api/ml/dna/score',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/dna/score`, req.body, { timeout: 30000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('Creative scoring error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Creative scoring failed', details: error.response?.data });
    }
  });

// Compound Learner (Loop 5) - Ensemble learning
app.post('/api/ml/compound/learning-cycle',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/compound/learning-cycle`, req.body, { timeout: 120000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('Learning cycle error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Learning cycle failed', details: error.response?.data });
    }
  });

app.post('/api/ml/compound/trajectory',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/compound/trajectory`, req.body, { timeout: 30000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('Trajectory calculation error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Trajectory calculation failed', details: error.response?.data });
    }
  });

app.post('/api/ml/compound/snapshot',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/compound/snapshot`, req.body, { timeout: 30000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('Snapshot creation error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Snapshot creation failed', details: error.response?.data });
    }
  });

app.get('/api/ml/compound/history/:account_id',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.get(`${ML_SERVICE_URL}/api/ml/compound/history/${req.params.account_id}`, { timeout: 30000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('History retrieval error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'History retrieval failed', details: error.response?.data });
    }
  });

// Actuals Fetcher (Loop 6) - Auto-validation
app.post('/api/ml/actuals/fetch',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/actuals/fetch`, req.body, { timeout: 60000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('Actuals fetch error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Actuals fetch failed', details: error.response?.data });
    }
  });

app.post('/api/ml/actuals/batch',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/actuals/batch`, req.body, { timeout: 180000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('Batch actuals fetch error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Batch fetch failed', details: error.response?.data });
    }
  });

app.post('/api/ml/actuals/sync-scheduled',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/actuals/sync-scheduled`, req.body, { timeout: 300000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('Scheduled sync error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Scheduled sync failed', details: error.response?.data });
    }
  });

app.get('/api/ml/actuals/stats',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.get(`${ML_SERVICE_URL}/api/ml/actuals/stats`, { timeout: 10000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('Actuals stats error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Stats retrieval failed', details: error.response?.data });
    }
  });

// Auto-Promoter (Loop 7) - Scale winners
app.post('/api/ml/auto-promote/check',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/auto-promote/check`, req.body, { timeout: 60000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('Auto-promotion check error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Promotion check failed', details: error.response?.data });
    }
  });

app.post('/api/ml/auto-promote/check-all',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/auto-promote/check-all`, req.body, { timeout: 180000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('Bulk promotion check error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Bulk check failed', details: error.response?.data });
    }
  });

app.post('/api/ml/auto-promote/history',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/auto-promote/history`, req.body, { timeout: 30000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('Promotion history error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'History retrieval failed', details: error.response?.data });
    }
  });

app.get('/api/ml/auto-promote/cumulative-improvement',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.get(`${ML_SERVICE_URL}/api/ml/auto-promote/cumulative-improvement`, { timeout: 30000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('Cumulative improvement error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Improvement report failed', details: error.response?.data });
    }
  });

// Self-Learning Cycle (All 7 loops together)
app.post('/api/ml/self-learning-cycle',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/self-learning-cycle`, req.body, { timeout: 300000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('Self-learning cycle error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Self-learning cycle failed', details: error.response?.data });
    }
  });

// ============================================================================
// MULTI-PLATFORM PUBLISHING ENDPOINTS (Agent 19)
// ============================================================================

import { MultiPlatformPublisher } from './multi-platform/multi_publisher';
import { statusAggregator } from './multi-platform/status_aggregator';

const TIKTOK_ADS_URL = process.env.TIKTOK_ADS_URL || 'http://localhost:8085';

// Initialize multi-platform publisher
const multiPlatformPublisher = new MultiPlatformPublisher({
  videoAgentUrl: VIDEO_AGENT_URL,
  metaPublisherUrl: META_PUBLISHER_URL,
  googleAdsUrl: GOOGLE_ADS_URL,
  tiktokAdsUrl: TIKTOK_ADS_URL
});

// POST /api/publish/multi - Unified multi-platform publishing
app.post('/api/publish/multi',
  uploadRateLimiter,
  validateInput({
    body: {
      creative_id: { type: 'string', required: true, min: 1, max: 100 },
      video_path: { type: 'string', required: true, min: 1, max: 1000 },
      platforms: { type: 'array', required: true, min: 1, max: 3 },
      budget_allocation: { type: 'object', required: true },
      campaign_name: { type: 'string', required: true, min: 1, max: 255, sanitize: true },
      campaign_config: { type: 'object', required: false }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const {
        creative_id,
        video_path,
        platforms,
        budget_allocation,
        campaign_name,
        campaign_config,
        creative_config
      } = req.body;

      console.log(`[Multi-Platform] Publishing to: ${platforms.join(', ')}`);

      // Validate platforms
      const validPlatforms = ['meta', 'google', 'tiktok'];
      const invalidPlatforms = platforms.filter((p: string) => !validPlatforms.includes(p));

      if (invalidPlatforms.length > 0) {
        return res.status(400).json({
          error: 'Invalid platforms',
          message: `Invalid platforms: ${invalidPlatforms.join(', ')}. Valid: ${validPlatforms.join(', ')}`
        });
      }

      // Validate budget allocation
      for (const platform of platforms) {
        if (!budget_allocation[platform] || budget_allocation[platform] <= 0) {
          return res.status(400).json({
            error: 'Invalid budget allocation',
            message: `Budget allocation for ${platform} must be > 0`
          });
        }
      }

      // Publish to all platforms
      const result = await multiPlatformPublisher.publishMultiPlatform({
        creative_id,
        video_path,
        platforms,
        budget_allocation,
        campaign_name,
        campaign_config: campaign_config || {},
        creative_config
      });

      res.status(202).json({
        status: 'accepted',
        ...result,
        message: result.message,
        next_steps: {
          check_status: `/api/publish/status/${result.job_id}`,
          monitor_progress: `/api/publish/status/${result.job_id}`
        }
      });

    } catch (error: any) {
      console.error('[Multi-Platform] Publishing error:', error.message);
      res.status(500).json({
        error: 'Multi-platform publishing failed',
        message: error.message,
        details: error.response?.data
      });
    }
  });

// GET /api/publish/status/:job_id - Check multi-platform publishing status
app.get('/api/publish/status/:job_id',
  apiRateLimiter,
  validateInput({
    params: {
      job_id: { type: 'string', required: true }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const { job_id } = req.params;

      const job = statusAggregator.getJobStatus(job_id);

      if (!job) {
        return res.status(404).json({
          error: 'Job not found',
          message: `Publishing job ${job_id} not found`
        });
      }

      // Get aggregated metrics if available
      const metrics = statusAggregator.aggregateMetrics(job_id);
      const comparison = statusAggregator.getPlatformComparison(job_id);

      res.json({
        status: 'success',
        job: {
          jobId: job.jobId,
          creativeId: job.creativeId,
          campaignName: job.campaignName,
          platforms: job.platforms,
          overallStatus: job.overallStatus,
          successCount: job.successCount,
          failureCount: job.failureCount,
          totalPlatforms: job.totalPlatforms,
          createdAt: job.createdAt,
          completedAt: job.completedAt
        },
        platformStatuses: job.platformStatuses,
        metrics,
        platformComparison: comparison,
        budgetAllocation: job.budgetAllocation
      });

    } catch (error: any) {
      console.error('[Multi-Platform] Status check error:', error.message);
      res.status(500).json({
        error: 'Failed to get job status',
        message: error.message
      });
    }
  });

// GET /api/platforms/specs - Get platform creative specifications
app.get('/api/platforms/specs',
  apiRateLimiter,
  validateInput({
    query: {
      platforms: { type: 'string', required: false }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const platformsQuery = req.query.platforms as string;
      const validPlatforms = ['meta', 'google', 'tiktok'] as const;
      const platforms: ('meta' | 'google' | 'tiktok')[] = platformsQuery
        ? (platformsQuery.split(',').map(p => p.trim()).filter(p => {
            return p.length > 0 && validPlatforms.includes(p as typeof validPlatforms[number]);
          }) as ('meta' | 'google' | 'tiktok')[])
        : ['meta', 'google', 'tiktok'];

      const specs = multiPlatformPublisher.getPlatformSpecs(platforms);

      res.json({
        status: 'success',
        platforms,
        specs,
        total_specs: specs.length,
        usage: {
          meta: 'Facebook/Instagram Ads - Various placements (Feed, Reels, Stories)',
          google: 'Google Ads - YouTube and Display Network',
          tiktok: 'TikTok Ads - Vertical video only (9:16)'
        }
      });

    } catch (error: any) {
      console.error('[Multi-Platform] Specs error:', error.message);
      res.status(500).json({
        error: 'Failed to get platform specs',
        message: error.message
      });
    }
  });

// POST /api/platforms/budget-allocation - Calculate recommended budget allocation
app.post('/api/platforms/budget-allocation',
  apiRateLimiter,
  validateInput({
    body: {
      platforms: { type: 'array', required: true, min: 1, max: 3 },
      total_budget: { type: 'number', required: true, min: 1 },
      custom_weights: { type: 'object', required: false }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const { platforms, total_budget, custom_weights } = req.body;

      const allocation = multiPlatformPublisher.calculateBudgetAllocation(
        platforms,
        total_budget,
        custom_weights
      );

      res.json({
        status: 'success',
        total_budget,
        platforms,
        allocation,
        percentages: Object.keys(allocation).reduce((acc, platform) => {
          acc[platform] = ((allocation[platform] / total_budget) * 100).toFixed(1) + '%';
          return acc;
        }, {} as Record<string, string>),
        note: custom_weights
          ? 'Budget allocated using custom weights'
          : 'Budget allocated using default platform weights (Meta: 50%, Google: 30%, TikTok: 20%)'
      });

    } catch (error: any) {
      console.error('[Multi-Platform] Budget allocation error:', error.message);
      res.status(500).json({
        error: 'Failed to calculate budget allocation',
        message: error.message
      });
    }
  });

// GET /api/publish/jobs - Get all publishing jobs
app.get('/api/publish/jobs',
  apiRateLimiter,
  validateInput({
    query: {
      limit: { type: 'number', required: false, min: 1, max: 100 }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const limit = req.query.limit ? parseInt(req.query.limit as string) : 10;

      const jobs = statusAggregator.getRecentJobs(limit);
      const summary = statusAggregator.getSummary();

      res.json({
        status: 'success',
        jobs,
        summary,
        count: jobs.length
      });

    } catch (error: any) {
      console.error('[Multi-Platform] Jobs list error:', error.message);
      res.status(500).json({
        error: 'Failed to get publishing jobs',
        message: error.message
      });
    }
  });

// GET /api/publish/summary - Get publishing summary statistics
app.get('/api/publish/summary',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const summary = statusAggregator.getSummary();

      res.json({
        status: 'success',
        summary,
        timestamp: new Date().toISOString()
      });

    } catch (error: any) {
      console.error('[Multi-Platform] Summary error:', error.message);
      res.status(500).json({
        error: 'Failed to get publishing summary',
        message: error.message
      });
    }
  });

// ============================================================================
// API ROUTE MODULES (Agent 58 - Full API Wiring)
// ============================================================================

// Campaign Management Routes
import { createCampaignsRouter } from './routes/campaigns';
const campaignsRouter = createCampaignsRouter(pgPool);
app.use('/api/campaigns', campaignsRouter);

// Analytics Routes
import { createAnalyticsRouter } from './routes/analytics';
const analyticsRouter = createAnalyticsRouter(pgPool);
app.use('/api/analytics', analyticsRouter);

// A/B Testing Routes
import { createABTestsRouter } from './routes/ab-tests';
const abTestsRouter = createABTestsRouter(pgPool);
app.use('/api/ab-tests', abTestsRouter);

// Ads Management Routes
import { createAdsRouter } from './routes/ads';
const adsRouter = createAdsRouter(pgPool);
app.use('/api/ads', adsRouter);

// Predictions Routes
import { createPredictionsRouter } from './routes/predictions';
const predictionsRouter = createPredictionsRouter(pgPool);
app.use('/api/predictions', predictionsRouter);

// ============================================================================
// ONBOARDING ENDPOINTS
// ============================================================================

import { createOnboardingRouter } from './routes/onboarding';
const onboardingRouter = createOnboardingRouter(pgPool);
app.use('/api/onboarding', onboardingRouter);

// ============================================================================
// DEMO MODE ENDPOINTS (Agent 20 - Investor Demo Mode)
// ============================================================================

import demoRouter from './routes/demo';
app.use('/api/demo', demoRouter);

// ============================================================================
// ALERT SYSTEM ENDPOINTS (Agent 16 - Real-Time Performance Alerts)
// ============================================================================

import alertsRouter, { initializeAlertWebSocket } from './routes/alerts';
app.use('/api/alerts', alertsRouter);

// ============================================================================
// REPORT GENERATION ENDPOINTS (Agent 18 - Campaign Performance Reports)
// ============================================================================

import reportRoutes from './routes/reports';
app.use('/api/reports', reportRoutes);

// ============================================================================
// REAL-TIME STREAMING ENDPOINTS (Agent 38 - SSE/WebSocket)
// ============================================================================

import streamingRoutes from './routes/streaming';
app.use('/api', streamingRoutes);

// Import real-time infrastructure
import {
  initializeChannelManager,
  initializeWebSocketManager,
  getSSEManager,
  shutdownChannelManager,
  shutdownWebSocketManager,
  shutdownSSEManager
} from './realtime';

// ============================================================================
// IMAGE GENERATION ENDPOINTS (Agent 37 - AI Image Generation)
// ============================================================================

import { createImageGenerationRouter } from './routes/image-generation';
const imageGenerationRouter = createImageGenerationRouter(pgPool);
app.use('/api/image', imageGenerationRouter);

// ============================================================================
// ARTERY MODULES - Service Business Intelligence
// ============================================================================

// HubSpot Webhook (Artery #1: HubSpot → ML-Service)
import hubspotWebhookRouter from './webhooks/hubspot';
app.use('/api', hubspotWebhookRouter);
console.log('✅ HubSpot webhook handler mounted at /api/webhook/hubspot');

// ML Proxy Routes (Artery Module Endpoints)
import mlProxyRouter from './routes/ml-proxy';
app.use('/api/ml', mlProxyRouter);
console.log('✅ Artery module endpoints mounted at /api/ml/*');

// ============================================================================
// HEALTH CHECK
// ============================================================================

app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString()
  });
});

// Real-time stats endpoint
app.get('/api/realtime/stats', (req: Request, res: Response) => {
  const sseManager = getSSEManager();
  const channelManager = require('./realtime').getChannelManager();

  res.json({
    status: 'healthy',
    sse: sseManager.getStats(),
    channels: channelManager.getStats(),
    timestamp: new Date().toISOString()
  });
});

const server = app.listen(PORT, async () => {
  console.log(`Gateway API listening on port ${PORT}`);

  // Initialize real-time infrastructure
  try {
    console.log('🚀 Initializing real-time infrastructure...');

    // Initialize channel manager (Redis pub/sub)
    await initializeChannelManager();
    console.log('✅ Channel manager initialized');

    // Initialize WebSocket manager
    initializeWebSocketManager(server);
    console.log('✅ WebSocket server initialized on /ws');

    // Initialize SSE manager (singleton, auto-initializes)
    getSSEManager();
    console.log('✅ SSE manager initialized');

    // Initialize alert WebSocket (existing)
    initializeAlertWebSocket(server);
    console.log('✅ Alert WebSocket server initialized on /ws/alerts');

    console.log('🎉 Real-time infrastructure ready!');
  } catch (error) {
    console.error('❌ Failed to initialize real-time infrastructure:', error);
  }
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('🛑 SIGTERM received, shutting down gracefully...');

  try {
    await shutdownWebSocketManager();
    await shutdownChannelManager();
    shutdownSSEManager();

    server.close(() => {
      console.log('✅ Server closed');
      process.exit(0);
    });
  } catch (error) {
    console.error('❌ Error during shutdown:', error);
    process.exit(1);
  }
});

process.on('SIGINT', async () => {
  console.log('🛑 SIGINT received, shutting down gracefully...');

  try {
    await shutdownWebSocketManager();
    await shutdownChannelManager();
    shutdownSSEManager();

    server.close(() => {
      console.log('✅ Server closed');
      process.exit(0);
    });
  } catch (error) {
    console.error('❌ Error during shutdown:', error);
    process.exit(1);
  }
});

export default app;