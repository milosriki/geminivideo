/**
 * Winners API Routes
 * Agent 11 Task: Winner REST Endpoints
 * Created: 2025-12-13
 *
 * Provides REST API endpoints for winner ad management:
 * - GET /api/winners/recent - Get recent winners
 * - GET /api/winners/:winnerId - Get winner details
 * - POST /api/winners/clone-winner - Clone a winning ad
 * - GET /api/winners/similar - Find similar winners
 * - GET /api/winners/stats - Get winner statistics
 * - POST /api/winners/budget/reallocate - Reallocate budget to winners
 */

import { Router, Request, Response } from 'express';
import axios from 'axios';
import {
  recordWinnerDetected,
  recordWinnerReplicated,
  recordBudgetReallocated,
  updateWinnerMetrics
} from '../monitoring/metrics';
import { setCacheHeaders } from '../middleware/cache';

const router = Router();

// Cache configuration for winner endpoints
const CACHE_TTL_RECENT = 60;        // 1 minute for recent winners (frequently changes)
const CACHE_TTL_STATS = 300;        // 5 minutes for stats (aggregates are stable)
const CACHE_TTL_SIMILAR = 600;      // 10 minutes for similar winners (patterns change slowly)

// ML Service URL
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8081';

// Rate limiter reference (imported where router is used)
let rateLimiter: any = null;

export function setRateLimiter(limiter: any) {
  rateLimiter = limiter;
}

// ============================================================================
// GET /api/winners/recent - Get recent winners
// ============================================================================
router.get('/recent', setCacheHeaders(CACHE_TTL_RECENT), async (req: Request, res: Response) => {
  try {
    const {
      limit = '10',
      min_ctr = '0.03',
      min_roas = '2.0',
      days_back = '7'
    } = req.query;

    // Call ML service RAG endpoint
    const response = await axios.post(
      `${ML_SERVICE_URL}/api/ml/rag/search-winners`,
      {
        min_ctr: parseFloat(min_ctr as string),
        min_roas: parseFloat(min_roas as string),
        days_back: parseInt(days_back as string),
        limit: parseInt(limit as string)
      },
      { timeout: 30000 }
    );

    const winners = response.data.winners || response.data.results || [];

    // Update metrics
    if (winners.length > 0) {
      updateWinnerMetrics(
        '24h',
        winners.reduce((sum: number, w: any) => sum + (w.ctr || 0), 0) / winners.length,
        winners.reduce((sum: number, w: any) => sum + (w.roas || 0), 0) / winners.length
      );
    }

    res.json({
      success: true,
      winners,
      meta: {
        total: winners.length,
        min_ctr: parseFloat(min_ctr as string),
        min_roas: parseFloat(min_roas as string),
        days_back: parseInt(days_back as string),
        fetched_at: new Date().toISOString()
      }
    });

  } catch (error: any) {
    console.error('Get recent winners error:', error.message);
    res.status(error.response?.status || 500).json({
      success: false,
      error: {
        code: 'FETCH_WINNERS_FAILED',
        message: 'Failed to fetch recent winners',
        details: error.response?.data
      }
    });
  }
});

// ============================================================================
// GET /api/winners/:winnerId - Get winner details
// ============================================================================
router.get('/:winnerId', async (req: Request, res: Response) => {
  try {
    const { winnerId } = req.params;

    // Call ML service to get winner details
    const response = await axios.get(
      `${ML_SERVICE_URL}/api/ml/rag/winner/${winnerId}`,
      { timeout: 10000 }
    );

    if (!response.data || !response.data.winner) {
      return res.status(404).json({
        success: false,
        error: {
          code: 'WINNER_NOT_FOUND',
          message: `Winner ${winnerId} not found`
        }
      });
    }

    res.json({
      success: true,
      winner: response.data.winner
    });

  } catch (error: any) {
    if (error.response?.status === 404) {
      return res.status(404).json({
        success: false,
        error: {
          code: 'WINNER_NOT_FOUND',
          message: `Winner ${req.params.winnerId} not found`
        }
      });
    }

    console.error('Get winner details error:', error.message);
    res.status(error.response?.status || 500).json({
      success: false,
      error: {
        code: 'FETCH_WINNER_FAILED',
        message: 'Failed to fetch winner details',
        details: error.response?.data
      }
    });
  }
});

// ============================================================================
// POST /api/winners/clone-winner - Clone a winning ad
// ============================================================================
router.post('/clone-winner', async (req: Request, res: Response) => {
  try {
    const { winner_ad_id, variations = 3, variation_types } = req.body;

    if (!winner_ad_id) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'winner_ad_id is required'
        }
      });
    }

    if (variations < 1 || variations > 10) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'variations must be between 1 and 10'
        }
      });
    }

    // Call ML service to create variations
    const response = await axios.post(
      `${ML_SERVICE_URL}/api/ml/replicate/create-variations`,
      {
        winner_ad_id,
        count: variations,
        variation_types: variation_types || ['hook_swap', 'cta_change']
      },
      { timeout: 60000 }
    );

    const clonedAds = response.data.variations || [];

    // Record metrics
    clonedAds.forEach((ad: any) => {
      recordWinnerReplicated('success', ad.variation_type || 'unknown');
    });

    res.json({
      success: true,
      cloned_ads: clonedAds,
      original_ad_id: winner_ad_id,
      meta: {
        requested_variations: variations,
        created_variations: clonedAds.length,
        timestamp: new Date().toISOString()
      }
    });

  } catch (error: any) {
    console.error('Clone winner error:', error.message);
    res.status(error.response?.status || 500).json({
      success: false,
      error: {
        code: 'CLONE_WINNER_FAILED',
        message: 'Failed to clone winner',
        details: error.response?.data
      }
    });
  }
});

// ============================================================================
// GET /api/winners/similar - Find similar winners
// ============================================================================
router.get('/similar', setCacheHeaders(CACHE_TTL_SIMILAR), async (req: Request, res: Response) => {
  try {
    const { ad_id, k = '5' } = req.query;

    if (!ad_id) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'ad_id query parameter is required'
        }
      });
    }

    // Call ML service RAG search
    const response = await axios.post(
      `${ML_SERVICE_URL}/api/ml/rag/search-winners`,
      {
        reference_ad_id: ad_id,
        k: parseInt(k as string),
        find_similar: true
      },
      { timeout: 30000 }
    );

    const similarWinners = response.data.similar || response.data.results || [];

    res.json({
      success: true,
      query_ad_id: ad_id,
      similar_winners: similarWinners.map((w: any, i: number) => ({
        ad_id: w.ad_id,
        similarity_score: w.similarity || (1 - i * 0.1),
        ctr: w.ctr,
        roas: w.roas,
        creative_dna: w.creative_dna
      }))
    });

  } catch (error: any) {
    console.error('Find similar winners error:', error.message);
    res.status(error.response?.status || 500).json({
      success: false,
      error: {
        code: 'SIMILAR_SEARCH_FAILED',
        message: 'Failed to find similar winners',
        details: error.response?.data
      }
    });
  }
});

// ============================================================================
// GET /api/winners/stats - Get winner statistics
// ============================================================================
router.get('/stats', setCacheHeaders(CACHE_TTL_STATS), async (req: Request, res: Response) => {
  try {
    // Call ML service for stats
    const response = await axios.get(
      `${ML_SERVICE_URL}/api/ml/rag/memory-stats`,
      { timeout: 10000 }
    );

    const stats = response.data;

    res.json({
      success: true,
      stats: {
        total_winners_24h: stats.winners_24h || 0,
        total_winners_7d: stats.winners_7d || stats.total_winners || 0,
        average_winner_ctr: stats.avg_ctr || 0,
        average_winner_roas: stats.avg_roas || 0,
        total_budget_in_winners: stats.total_budget || 0,
        roi_improvement: stats.roi_improvement || 0,
        top_performing_hook_type: stats.top_hook_type || 'unknown',
        timestamp: new Date().toISOString()
      }
    });

  } catch (error: any) {
    console.error('Get winner stats error:', error.message);
    res.status(error.response?.status || 500).json({
      success: false,
      error: {
        code: 'STATS_FETCH_FAILED',
        message: 'Failed to fetch winner statistics',
        details: error.response?.data
      }
    });
  }
});

// ============================================================================
// POST /api/winners/budget/reallocate - Reallocate budget to winners
// ============================================================================
router.post('/budget/reallocate', async (req: Request, res: Response) => {
  try {
    const {
      account_id,
      max_reallocation_percent = 20,
      dry_run = false
    } = req.body;

    // Call ML service budget allocation endpoint
    const response = await axios.post(
      `${ML_SERVICE_URL}/api/ml/budget/reallocate-to-winners`,
      {
        account_id: account_id || 'default',
        max_reallocation_percent,
        dry_run
      },
      { timeout: 60000 }
    );

    const result = response.data;

    // Record metrics (only if not dry run)
    if (!dry_run && result.amount_reallocated > 0) {
      recordBudgetReallocated(account_id || 'default', result.amount_reallocated);
    }

    res.json({
      success: true,
      reallocation: {
        status: dry_run ? 'dry_run' : (result.status || 'completed'),
        from_ads: result.from_ads || [],
        to_ads: result.to_ads || [],
        amount_reallocated: result.amount_reallocated || 0,
        percentage_reallocated: result.percentage_reallocated || 0,
        timestamp: new Date().toISOString()
      }
    });

  } catch (error: any) {
    console.error('Budget reallocation error:', error.message);
    res.status(error.response?.status || 500).json({
      success: false,
      error: {
        code: 'BUDGET_REALLOCATION_FAILED',
        message: 'Failed to reallocate budget',
        details: error.response?.data
      }
    });
  }
});

export default router;
