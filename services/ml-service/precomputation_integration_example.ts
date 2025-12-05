/**
 * Precomputation Integration Example
 *
 * Shows how to integrate predictive precomputation into your gateway API
 * for instant user experience.
 *
 * Agent 45: 10x Leverage - Predictive Precomputation
 */

import axios from 'axios';

// Configuration
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://ml-service:8003';

/**
 * Helper function to trigger precomputation (fire and forget)
 */
async function triggerPrecompute(endpoint: string, data: any) {
  try {
    await axios.post(`${ML_SERVICE_URL}${endpoint}`, data);
  } catch (err) {
    // Log but don't fail - precomputation is optional optimization
    console.error('Precompute error:', err);
  }
}

/**
 * Helper function to get cached result
 */
async function getCachedResult(cacheKey: string): Promise<any | null> {
  try {
    const response = await axios.get(
      `${ML_SERVICE_URL}/api/precompute/cache/${cacheKey}`
    );
    return response.data.result;
  } catch {
    // Cache miss
    return null;
  }
}

// ============================================================================
// VIDEO UPLOAD INTEGRATION
// ============================================================================

/**
 * Video upload endpoint with precomputation
 */
export async function handleVideoUpload(req: any, res: any) {
  try {
    // 1. Upload video (your existing logic)
    const video = await uploadVideo(req.body);

    // 2. Trigger precomputation (fire and forget)
    triggerPrecompute('/api/precompute/video', {
      video_id: video.id,
      user_id: req.user.id,
      video_data: {
        url: video.url,
        duration: video.duration,
        format: video.format
      }
    });

    // 3. Return immediately - precomputation happens in background
    res.json({
      success: true,
      video,
      message: 'Video uploaded, analysis in progress'
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

/**
 * Get video analysis endpoint with cache check
 */
export async function handleGetVideoAnalysis(req: any, res: any) {
  try {
    const videoId = req.params.id;
    const cacheKey = `ctr_prediction:video:${videoId}`;

    // 1. Check cache first
    const cachedResult = await getCachedResult(cacheKey);

    if (cachedResult) {
      // INSTANT response from cache (50ms)
      return res.json({
        ...cachedResult,
        cached: true,
        source: 'precomputed'
      });
    }

    // 2. Cache miss - compute now (slower, 2-5s)
    const result = await computeVideoAnalysis(videoId);

    res.json({
      ...result,
      cached: false,
      source: 'computed'
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

// ============================================================================
// CAMPAIGN CREATION INTEGRATION
// ============================================================================

/**
 * Campaign creation endpoint with precomputation
 */
export async function handleCampaignCreate(req: any, res: any) {
  try {
    // 1. Create campaign
    const campaign = await createCampaign(req.body);

    // 2. Trigger precomputation for variants
    triggerPrecompute('/api/precompute/campaign', {
      campaign_id: campaign.id,
      user_id: req.user.id,
      campaign_data: {
        budget: campaign.budget,
        target_audience: campaign.target_audience,
        objective: campaign.objective
      }
    });

    // 3. Return immediately
    res.json({
      success: true,
      campaign,
      message: 'Campaign created, variants generating'
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

/**
 * Get campaign variants endpoint with cache check
 */
export async function handleGetCampaignVariants(req: any, res: any) {
  try {
    const campaignId = req.params.id;
    const cacheKey = `variant_generation:campaign:${campaignId}`;

    // Check cache first
    const cachedVariants = await getCachedResult(cacheKey);

    if (cachedVariants) {
      // INSTANT response (50ms)
      return res.json({
        variants: cachedVariants,
        cached: true,
        source: 'precomputed'
      });
    }

    // Cache miss - generate now (slower, 10-15s)
    const variants = await generateVariants(campaignId);

    res.json({
      variants,
      cached: false,
      source: 'computed'
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

// ============================================================================
// USER LOGIN INTEGRATION
// ============================================================================

/**
 * User login endpoint with precomputation
 */
export async function handleUserLogin(req: any, res: any) {
  try {
    // 1. Authenticate user
    const user = await authenticateUser(req.body);
    const token = generateToken(user);

    // 2. Trigger precomputation for dashboard + predict actions
    triggerPrecompute('/api/precompute/login', {
      user_id: user.id,
      user_data: {
        last_login: new Date(),
        plan: user.plan
      }
    });

    // 3. Return immediately
    res.json({
      success: true,
      user,
      token,
      message: 'Dashboard loading optimized'
    });
  } catch (err) {
    res.status(401).json({ error: 'Authentication failed' });
  }
}

/**
 * Get dashboard data endpoint with cache check
 */
export async function handleGetDashboard(req: any, res: any) {
  try {
    const userId = req.user.id;
    const cacheKey = `dashboard_data:user:${userId}`;

    // Check cache first
    const cachedDashboard = await getCachedResult(cacheKey);

    if (cachedDashboard) {
      // INSTANT response (50ms)
      return res.json({
        ...cachedDashboard,
        cached: true,
        source: 'precomputed'
      });
    }

    // Cache miss - compute now (slower, 2-3s)
    const dashboard = await computeDashboard(userId);

    res.json({
      ...dashboard,
      cached: false,
      source: 'computed'
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

// ============================================================================
// ACTION PREDICTION INTEGRATION
// ============================================================================

/**
 * Get predicted next actions for user
 */
export async function handleGetPredictedActions(req: any, res: any) {
  try {
    const userId = req.user.id;

    // Get predictions from ML service
    const response = await axios.post(
      `${ML_SERVICE_URL}/api/precompute/predict-actions`,
      { user_id: userId }
    );

    const predictions = response.data.predictions;

    // Use predictions to show smart suggestions in UI
    res.json({
      success: true,
      predictions,
      suggestions: predictions.map((pred: any) => ({
        action: pred.action,
        text: getActionSuggestionText(pred.action),
        probability: pred.probability,
        icon: getActionIcon(pred.action)
      }))
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

/**
 * Helper to generate suggestion text
 */
function getActionSuggestionText(action: string): string {
  const suggestions: Record<string, string> = {
    video_upload: 'Upload a new video',
    campaign_create: 'Create a new campaign',
    variant_generate: 'Generate ad variants',
    dashboard_view: 'View your dashboard'
  };
  return suggestions[action] || 'Continue working';
}

/**
 * Helper to get action icon
 */
function getActionIcon(action: string): string {
  const icons: Record<string, string> = {
    video_upload: '📹',
    campaign_create: '🎯',
    variant_generate: '🎨',
    dashboard_view: '📊'
  };
  return icons[action] || '✨';
}

// ============================================================================
// CACHE MANAGEMENT INTEGRATION
// ============================================================================

/**
 * Invalidate cache when data changes
 */
export async function invalidateVideoCache(videoId: string) {
  try {
    await axios.delete(`${ML_SERVICE_URL}/api/precompute/cache`, {
      data: { pattern: `video:${videoId}:*` }
    });
  } catch (err) {
    console.error('Cache invalidation error:', err);
  }
}

/**
 * Invalidate campaign cache
 */
export async function invalidateCampaignCache(campaignId: string) {
  try {
    await axios.delete(`${ML_SERVICE_URL}/api/precompute/cache`, {
      data: { pattern: `campaign:${campaignId}:*` }
    });
  } catch (err) {
    console.error('Cache invalidation error:', err);
  }
}

/**
 * Proactively refresh cache
 */
export async function refreshCache(taskType: string) {
  try {
    await axios.post(
      `${ML_SERVICE_URL}/api/precompute/refresh/${taskType}`
    );
  } catch (err) {
    console.error('Cache refresh error:', err);
  }
}

// ============================================================================
// MONITORING INTEGRATION
// ============================================================================

/**
 * Get precomputation metrics for monitoring dashboard
 */
export async function handleGetPrecomputeMetrics(req: any, res: any) {
  try {
    const response = await axios.get(
      `${ML_SERVICE_URL}/api/precompute/metrics`
    );

    res.json(response.data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

/**
 * Get queue status
 */
export async function handleGetQueueStatus(req: any, res: any) {
  try {
    const response = await axios.get(
      `${ML_SERVICE_URL}/api/precompute/queue`
    );

    res.json(response.data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}

// ============================================================================
// EXPRESS ROUTER SETUP
// ============================================================================

/**
 * Example Express router setup
 */
export function setupPrecomputationRoutes(app: any) {
  // Video routes
  app.post('/api/videos', handleVideoUpload);
  app.get('/api/videos/:id/analysis', handleGetVideoAnalysis);

  // Campaign routes
  app.post('/api/campaigns', handleCampaignCreate);
  app.get('/api/campaigns/:id/variants', handleGetCampaignVariants);

  // Auth routes
  app.post('/api/auth/login', handleUserLogin);

  // Dashboard routes
  app.get('/api/dashboard', handleGetDashboard);

  // Prediction routes
  app.get('/api/predictions/actions', handleGetPredictedActions);

  // Monitoring routes (admin only)
  app.get('/api/admin/precompute/metrics', handleGetPrecomputeMetrics);
  app.get('/api/admin/precompute/queue', handleGetQueueStatus);

  console.log('✅ Precomputation routes configured');
}

// ============================================================================
// EXAMPLE USAGE
// ============================================================================

/**
 * Complete example showing before/after
 */
export class PrecomputationExample {
  /**
   * BEFORE: Slow, on-demand computation
   */
  async slowVideoAnalysisBefore(videoId: string) {
    console.time('Video Analysis (Before)');

    // Compute everything on-demand (2-5s)
    const sceneDetection = await computeSceneDetection(videoId);
    const faceDetection = await computeFaceDetection(videoId);
    const hookAnalysis = await computeHookAnalysis(videoId);
    const ctrPrediction = await computeCTRPrediction(videoId);

    console.timeEnd('Video Analysis (Before)');
    // Output: Video Analysis (Before): 3842ms

    return {
      sceneDetection,
      faceDetection,
      hookAnalysis,
      ctrPrediction
    };
  }

  /**
   * AFTER: Instant response from cache
   */
  async fastVideoAnalysisAfter(videoId: string) {
    console.time('Video Analysis (After)');

    // Check cache (50ms)
    const cacheKey = `hook_analysis:video:${videoId}`;
    const cached = await getCachedResult(cacheKey);

    console.timeEnd('Video Analysis (After)');
    // Output: Video Analysis (After): 52ms

    return cached || await this.slowVideoAnalysisBefore(videoId);
  }
}

// ============================================================================
// MOCK FUNCTIONS (replace with your actual implementations)
// ============================================================================

async function uploadVideo(data: any) {
  return { id: 'vid_' + Date.now(), ...data };
}

async function createCampaign(data: any) {
  return { id: 'camp_' + Date.now(), ...data };
}

async function authenticateUser(credentials: any) {
  return { id: 'user_' + Date.now(), email: credentials.email };
}

function generateToken(user: any) {
  return 'token_' + user.id;
}

async function computeVideoAnalysis(videoId: string) {
  return { videoId, analysis: 'computed' };
}

async function generateVariants(campaignId: string) {
  return Array.from({ length: 50 }, (_, i) => ({ id: i, variant: 'v' + i }));
}

async function computeDashboard(userId: string) {
  return { userId, campaigns: [], videos: [], stats: {} };
}

async function computeSceneDetection(videoId: string) {
  return { scenes: [] };
}

async function computeFaceDetection(videoId: string) {
  return { faces: [] };
}

async function computeHookAnalysis(videoId: string) {
  return { hooks: [] };
}

async function computeCTRPrediction(videoId: string) {
  return { ctr: 0.05 };
}

export default {
  handleVideoUpload,
  handleGetVideoAnalysis,
  handleCampaignCreate,
  handleGetCampaignVariants,
  handleUserLogin,
  handleGetDashboard,
  handleGetPredictedActions,
  setupPrecomputationRoutes
};
