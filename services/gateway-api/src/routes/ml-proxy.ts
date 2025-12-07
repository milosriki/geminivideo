/**
 * ML Proxy Routes - Artery Module Endpoints
 *
 * Purpose:
 *   Proxies Battle-Hardened Sampler, Synthetic Revenue, and Attribution
 *   endpoints from ML-Service to Gateway API with rate limiting.
 *
 * Endpoints:
 *   Battle-Hardened Sampler:
 *     - POST /api/ml/battle-hardened/select
 *     - POST /api/ml/battle-hardened/feedback
 *
 *   Synthetic Revenue:
 *     - POST /api/ml/synthetic-revenue/calculate
 *     - POST /api/ml/synthetic-revenue/ad-roas
 *     - POST /api/ml/synthetic-revenue/get-stages
 *
 *   Attribution:
 *     - POST /api/ml/attribution/track-click
 *     - POST /api/ml/attribution/attribute-conversion
 *
 * Created: 2025-12-07
 */

import { Router, Request, Response } from 'express';
import axios from 'axios';
import rateLimit from 'express-rate-limit';

const router = Router();

// Environment variables
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8003';

// Rate limiters
const standardRateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Max 100 requests per window
  standardHeaders: true,
  legacyHeaders: false,
});

const heavyRateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 30, // Max 30 requests for heavy operations
  standardHeaders: true,
  legacyHeaders: false,
});

/**
 * Proxy request to ML-Service
 */
async function proxyToMl(
  req: Request,
  res: Response,
  endpoint: string,
  timeout: number = 30000
): Promise<void> {
  try {
    const response = await axios.post(
      `${ML_SERVICE_URL}${endpoint}`,
      req.body,
      {
        timeout,
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    res.json(response.data);

  } catch (error: any) {
    console.error(`[ML Proxy] Error calling ${endpoint}:`, error.message);

    const status = error.response?.status || 500;
    const errorData = error.response?.data || { error: error.message };

    res.status(status).json(errorData);
  }
}

// ============================================================
// BATTLE-HARDENED SAMPLER ENDPOINTS
// ============================================================

/**
 * POST /api/ml/battle-hardened/select
 * Allocate budget across ads using blended scoring
 */
router.post(
  '/battle-hardened/select',
  standardRateLimiter,
  async (req: Request, res: Response) => {
    await proxyToMl(req, res, '/api/ml/battle-hardened/select', 30000);
  }
);

/**
 * POST /api/ml/battle-hardened/feedback
 * Register actual performance feedback
 */
router.post(
  '/battle-hardened/feedback',
  standardRateLimiter,
  async (req: Request, res: Response) => {
    await proxyToMl(req, res, '/api/ml/battle-hardened/feedback', 10000);
  }
);

// ============================================================
// SYNTHETIC REVENUE ENDPOINTS
// ============================================================

/**
 * POST /api/ml/synthetic-revenue/calculate
 * Calculate synthetic revenue for stage change
 */
router.post(
  '/synthetic-revenue/calculate',
  standardRateLimiter,
  async (req: Request, res: Response) => {
    await proxyToMl(req, res, '/api/ml/synthetic-revenue/calculate', 10000);
  }
);

/**
 * POST /api/ml/synthetic-revenue/ad-roas
 * Calculate Pipeline ROAS for an ad
 */
router.post(
  '/synthetic-revenue/ad-roas',
  standardRateLimiter,
  async (req: Request, res: Response) => {
    await proxyToMl(req, res, '/api/ml/synthetic-revenue/ad-roas', 10000);
  }
);

/**
 * POST /api/ml/synthetic-revenue/get-stages
 * Get all configured pipeline stages
 */
router.post(
  '/synthetic-revenue/get-stages',
  standardRateLimiter,
  async (req: Request, res: Response) => {
    await proxyToMl(req, res, '/api/ml/synthetic-revenue/get-stages', 10000);
  }
);

// ============================================================
// ATTRIBUTION ENDPOINTS
// ============================================================

/**
 * POST /api/ml/attribution/track-click
 * Track ad click with device fingerprint
 */
router.post(
  '/attribution/track-click',
  heavyRateLimiter, // Heavy operation (writes to DB)
  async (req: Request, res: Response) => {
    await proxyToMl(req, res, '/api/ml/attribution/track-click', 10000);
  }
);

/**
 * POST /api/ml/attribution/attribute-conversion
 * Attribute conversion using 3-layer matching
 */
router.post(
  '/attribution/attribute-conversion',
  heavyRateLimiter, // Heavy operation (3-layer matching)
  async (req: Request, res: Response) => {
    await proxyToMl(req, res, '/api/ml/attribution/attribute-conversion', 30000);
  }
);

// ============================================================
// HEALTH CHECK
// ============================================================

/**
 * GET /api/ml/artery/health
 * Health check for artery modules
 */
router.get('/artery/health', async (req: Request, res: Response) => {
  try {
    const mlHealth = await axios.get(`${ML_SERVICE_URL}/health`, { timeout: 5000 });

    res.json({
      status: 'healthy',
      ml_service: {
        status: mlHealth.data.status,
        url: ML_SERVICE_URL,
      },
      endpoints: {
        battle_hardened: 2,
        synthetic_revenue: 3,
        attribution: 2,
      },
    });

  } catch (error: any) {
    res.status(503).json({
      status: 'degraded',
      error: 'ML Service unreachable',
      ml_service_url: ML_SERVICE_URL,
    });
  }
});

export default router;
