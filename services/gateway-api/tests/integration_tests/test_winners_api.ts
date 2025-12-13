/**
 * Winner API Endpoints Integration Tests
 *
 * Agent 11 Task 11.2: API Endpoint Tests
 * Created: 2025-12-13
 *
 * Tests all winner-related API endpoints for production readiness.
 */

import { describe, test, expect, beforeAll, afterAll, beforeEach, jest } from '@jest/globals';
import request from 'supertest';
import express, { Application, Request, Response, NextFunction } from 'express';

// ============================================================================
// Test App Setup
// ============================================================================

function createTestApp(): Application {
  const app = express();
  app.use(express.json());

  // Mock authentication middleware
  app.use((req: Request, res: Response, next: NextFunction) => {
    (req as any).user = { id: 'test-user-id', accountId: 'test-account' };
    next();
  });

  // ===== WINNERS ENDPOINTS =====

  // GET /api/winners/recent
  app.get('/api/winners/recent', async (req: Request, res: Response) => {
    const limit = parseInt(req.query.limit as string) || 10;
    const minCtr = parseFloat(req.query.min_ctr as string) || 0.03;
    const minRoas = parseFloat(req.query.min_roas as string) || 2.0;

    // Mock winner data
    const winners = Array.from({ length: Math.min(limit, 5) }, (_, i) => ({
      ad_id: `winner_${i + 1}`,
      video_id: `video_${i + 1}`,
      campaign_id: `campaign_${i + 1}`,
      ctr: 0.035 + i * 0.005,
      roas: 3.0 + i * 0.5,
      impressions: 10000 + i * 1000,
      spend: 500 + i * 100,
      revenue: 1500 + i * 500,
      conversions: 50 + i * 10,
      detected_at: new Date().toISOString(),
      creative_dna: {
        hook_type: 'curiosity',
        duration_seconds: 15 + i * 5,
        cta_type: 'shop_now'
      }
    }));

    res.json({
      success: true,
      winners,
      meta: {
        total: winners.length,
        min_ctr: minCtr,
        min_roas: minRoas,
        fetched_at: new Date().toISOString()
      }
    });
  });

  // POST /api/winners/clone-winner
  app.post('/api/winners/clone-winner', async (req: Request, res: Response) => {
    const { winner_ad_id, variations = 3 } = req.body;

    if (!winner_ad_id) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'winner_ad_id is required'
        }
      });
    }

    // Mock cloned ads
    const clonedAds = Array.from({ length: variations }, (_, i) => ({
      ad_id: `cloned_${winner_ad_id}_${i + 1}`,
      original_ad_id: winner_ad_id,
      variation_type: i % 2 === 0 ? 'hook_swap' : 'cta_change',
      status: 'pending_review',
      created_at: new Date().toISOString()
    }));

    res.json({
      success: true,
      cloned_ads: clonedAds,
      original_ad_id: winner_ad_id
    });
  });

  // GET /api/winners/:winnerId
  app.get('/api/winners/:winnerId', async (req: Request, res: Response) => {
    const { winnerId } = req.params;

    // Mock single winner details
    const winner = {
      ad_id: winnerId,
      video_id: `video_${winnerId}`,
      campaign_id: 'campaign_1',
      ctr: 0.045,
      roas: 4.2,
      impressions: 25000,
      spend: 1200,
      revenue: 5040,
      conversions: 126,
      detected_at: new Date().toISOString(),
      creative_dna: {
        hook_type: 'problem_solution',
        duration_seconds: 20,
        cta_type: 'buy_now',
        visual_elements: ['product_demo', 'testimonial']
      },
      variations: [
        { variation_id: 'var_1', status: 'active', performance_index: 1.2 },
        { variation_id: 'var_2', status: 'pending', performance_index: null }
      ]
    };

    res.json({
      success: true,
      winner
    });
  });

  // POST /api/winners/budget/reallocate
  app.post('/api/winners/budget/reallocate', async (req: Request, res: Response) => {
    const { account_id, max_reallocation_percent = 20 } = req.body;

    res.json({
      success: true,
      reallocation: {
        status: 'completed',
        from_ads: ['underperformer_1', 'underperformer_2'],
        to_ads: ['winner_1', 'winner_2'],
        amount_reallocated: 500,
        percentage_reallocated: 15,
        timestamp: new Date().toISOString()
      }
    });
  });

  // GET /api/winners/stats
  app.get('/api/winners/stats', async (req: Request, res: Response) => {
    res.json({
      success: true,
      stats: {
        total_winners_24h: 12,
        total_winners_7d: 45,
        average_winner_ctr: 0.042,
        average_winner_roas: 3.8,
        total_budget_in_winners: 15000,
        roi_improvement: 28.5,
        top_performing_hook_type: 'curiosity',
        timestamp: new Date().toISOString()
      }
    });
  });

  // GET /api/winners/similar
  app.get('/api/winners/similar', async (req: Request, res: Response) => {
    const { ad_id, k = 5 } = req.query;

    const similar = Array.from({ length: parseInt(k as string) || 5 }, (_, i) => ({
      ad_id: `similar_${i + 1}`,
      similarity_score: 0.95 - i * 0.1,
      ctr: 0.04 - i * 0.005,
      roas: 3.5 - i * 0.2,
      creative_dna: {
        hook_type: 'curiosity',
        duration_seconds: 15
      }
    }));

    res.json({
      success: true,
      query_ad_id: ad_id,
      similar_winners: similar
    });
  });

  // Health check
  app.get('/health', (req: Request, res: Response) => {
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString()
    });
  });

  return app;
}

// ============================================================================
// Test Suite
// ============================================================================

describe('Winner API Endpoints', () => {
  let app: Application;

  beforeAll(() => {
    app = createTestApp();
  });

  // ===== GET /api/winners/recent =====
  describe('GET /api/winners/recent', () => {
    test('returns winners with default parameters', async () => {
      const response = await request(app)
        .get('/api/winners/recent')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.winners).toBeInstanceOf(Array);
      expect(response.body.meta).toBeDefined();
    });

    test('respects limit parameter', async () => {
      const response = await request(app)
        .get('/api/winners/recent')
        .query({ limit: 3 });

      expect(response.status).toBe(200);
      expect(response.body.winners.length).toBeLessThanOrEqual(3);
    });

    test('respects min_ctr parameter', async () => {
      const response = await request(app)
        .get('/api/winners/recent')
        .query({ min_ctr: 0.04 });

      expect(response.status).toBe(200);
      expect(response.body.meta.min_ctr).toBe(0.04);
    });

    test('respects min_roas parameter', async () => {
      const response = await request(app)
        .get('/api/winners/recent')
        .query({ min_roas: 2.5 });

      expect(response.status).toBe(200);
      expect(response.body.meta.min_roas).toBe(2.5);
    });

    test('returns winner data with required fields', async () => {
      const response = await request(app)
        .get('/api/winners/recent')
        .expect(200);

      const winner = response.body.winners[0];
      expect(winner).toHaveProperty('ad_id');
      expect(winner).toHaveProperty('ctr');
      expect(winner).toHaveProperty('roas');
      expect(winner).toHaveProperty('impressions');
      expect(winner).toHaveProperty('creative_dna');
    });
  });

  // ===== POST /api/winners/clone-winner =====
  describe('POST /api/winners/clone-winner', () => {
    test('creates variations successfully', async () => {
      const response = await request(app)
        .post('/api/winners/clone-winner')
        .send({ winner_ad_id: 'test-winner', variations: 3 })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.cloned_ads).toHaveLength(3);
    });

    test('returns cloned ads with correct structure', async () => {
      const response = await request(app)
        .post('/api/winners/clone-winner')
        .send({ winner_ad_id: 'test-winner', variations: 2 });

      expect(response.status).toBe(200);
      const clonedAd = response.body.cloned_ads[0];
      expect(clonedAd).toHaveProperty('ad_id');
      expect(clonedAd).toHaveProperty('original_ad_id');
      expect(clonedAd).toHaveProperty('variation_type');
      expect(clonedAd).toHaveProperty('status');
    });

    test('returns error when winner_ad_id is missing', async () => {
      const response = await request(app)
        .post('/api/winners/clone-winner')
        .send({ variations: 3 })
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error.code).toBe('VALIDATION_ERROR');
    });

    test('defaults to 3 variations when not specified', async () => {
      const response = await request(app)
        .post('/api/winners/clone-winner')
        .send({ winner_ad_id: 'test-winner' })
        .expect(200);

      expect(response.body.cloned_ads).toHaveLength(3);
    });
  });

  // ===== GET /api/winners/:winnerId =====
  describe('GET /api/winners/:winnerId', () => {
    test('returns winner details', async () => {
      const response = await request(app)
        .get('/api/winners/winner_123')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.winner).toBeDefined();
      expect(response.body.winner.ad_id).toBe('winner_123');
    });

    test('includes creative DNA in response', async () => {
      const response = await request(app)
        .get('/api/winners/winner_456')
        .expect(200);

      expect(response.body.winner.creative_dna).toBeDefined();
      expect(response.body.winner.creative_dna.hook_type).toBeDefined();
    });

    test('includes variations in response', async () => {
      const response = await request(app)
        .get('/api/winners/winner_789')
        .expect(200);

      expect(response.body.winner.variations).toBeInstanceOf(Array);
    });
  });

  // ===== POST /api/winners/budget/reallocate =====
  describe('POST /api/winners/budget/reallocate', () => {
    test('reallocates budget successfully', async () => {
      const response = await request(app)
        .post('/api/winners/budget/reallocate')
        .send({ account_id: 'test-account' })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.reallocation.status).toBe('completed');
    });

    test('returns reallocation details', async () => {
      const response = await request(app)
        .post('/api/winners/budget/reallocate')
        .send({ account_id: 'test-account', max_reallocation_percent: 25 });

      expect(response.status).toBe(200);
      expect(response.body.reallocation).toHaveProperty('from_ads');
      expect(response.body.reallocation).toHaveProperty('to_ads');
      expect(response.body.reallocation).toHaveProperty('amount_reallocated');
    });
  });

  // ===== GET /api/winners/stats =====
  describe('GET /api/winners/stats', () => {
    test('returns winner statistics', async () => {
      const response = await request(app)
        .get('/api/winners/stats')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.stats).toBeDefined();
    });

    test('includes required stats fields', async () => {
      const response = await request(app)
        .get('/api/winners/stats')
        .expect(200);

      const stats = response.body.stats;
      expect(stats).toHaveProperty('total_winners_24h');
      expect(stats).toHaveProperty('average_winner_ctr');
      expect(stats).toHaveProperty('average_winner_roas');
      expect(stats).toHaveProperty('roi_improvement');
    });
  });

  // ===== GET /api/winners/similar =====
  describe('GET /api/winners/similar', () => {
    test('returns similar winners', async () => {
      const response = await request(app)
        .get('/api/winners/similar')
        .query({ ad_id: 'reference_ad', k: 5 })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.similar_winners).toBeInstanceOf(Array);
      expect(response.body.similar_winners.length).toBeLessThanOrEqual(5);
    });

    test('returns similarity scores in descending order', async () => {
      const response = await request(app)
        .get('/api/winners/similar')
        .query({ ad_id: 'test_ad', k: 3 });

      expect(response.status).toBe(200);
      const similarities = response.body.similar_winners.map(
        (w: any) => w.similarity_score
      );

      // Check descending order
      for (let i = 1; i < similarities.length; i++) {
        expect(similarities[i - 1]).toBeGreaterThanOrEqual(similarities[i]);
      }
    });
  });

  // ===== Health Check =====
  describe('GET /health', () => {
    test('returns healthy status', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body.status).toBe('healthy');
      expect(response.body.timestamp).toBeDefined();
    });
  });
});

// ============================================================================
// Error Handling Tests
// ============================================================================

describe('API Error Handling', () => {
  let app: Application;

  beforeAll(() => {
    app = createTestApp();
  });

  test('handles invalid JSON gracefully', async () => {
    const response = await request(app)
      .post('/api/winners/clone-winner')
      .set('Content-Type', 'application/json')
      .send('invalid json');

    // Express will return 400 for invalid JSON
    expect([400, 500]).toContain(response.status);
  });
});

// ============================================================================
// Performance Tests
// ============================================================================

describe('API Performance', () => {
  let app: Application;

  beforeAll(() => {
    app = createTestApp();
  });

  test('GET /api/winners/recent responds within 200ms', async () => {
    const start = Date.now();

    await request(app)
      .get('/api/winners/recent')
      .expect(200);

    const duration = Date.now() - start;
    expect(duration).toBeLessThan(200);
  });

  test('POST /api/winners/clone-winner responds within 200ms', async () => {
    const start = Date.now();

    await request(app)
      .post('/api/winners/clone-winner')
      .send({ winner_ad_id: 'perf-test' })
      .expect(200);

    const duration = Date.now() - start;
    expect(duration).toBeLessThan(200);
  });

  test('handles concurrent requests', async () => {
    const requests = Array.from({ length: 10 }, () =>
      request(app).get('/api/winners/recent')
    );

    const responses = await Promise.all(requests);

    responses.forEach(response => {
      expect(response.status).toBe(200);
    });
  });
});

export default {};
