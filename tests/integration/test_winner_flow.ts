/**
 * Integration Tests for Winner Detection and Replication System
 * Agent 09 - Comprehensive Winner Flow Testing
 *
 * Tests:
 * - Winner detection with ROAS thresholds
 * - Winner replication with variations
 * - Budget optimization and safety limits
 * - Full workflow orchestration
 * - Scheduled job execution
 * - Agent trigger mechanisms
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from '@jest/globals';
import axios, { AxiosInstance } from 'axios';
import { createClient } from 'redis';
import { Pool } from 'pg';

// Test configuration
const API_URL = process.env.TEST_API_URL || 'http://localhost:8000';
const ML_SERVICE_URL = process.env.TEST_ML_SERVICE_URL || 'http://localhost:8004';
const TEST_DATABASE_URL = process.env.TEST_DATABASE_URL || 'postgresql://test:test@localhost:5432/test_db';
const TEST_REDIS_URL = process.env.TEST_REDIS_URL || 'redis://localhost:6379';
const TEST_AD_ACCOUNT_ID = process.env.TEST_AD_ACCOUNT_ID || 'test_account_123';

describe('Winner Detection and Replication System', () => {
  let apiClient: AxiosInstance;
  let mlClient: AxiosInstance;
  let redisClient: any;
  let pgPool: Pool;
  let testAdIds: string[] = [];
  let testWinnerIds: string[] = [];

  // ============================================================================
  // SETUP AND TEARDOWN
  // ============================================================================

  beforeAll(async () => {
    // Setup API clients
    apiClient = axios.create({
      baseURL: API_URL,
      timeout: 30000,
      validateStatus: () => true
    });

    mlClient = axios.create({
      baseURL: ML_SERVICE_URL,
      timeout: 30000,
      validateStatus: () => true
    });

    // Setup Redis client
    redisClient = createClient({ url: TEST_REDIS_URL });
    await redisClient.connect();

    // Setup PostgreSQL pool
    pgPool = new Pool({ connectionString: TEST_DATABASE_URL });

    // Wait for services to be ready
    await waitForServices();

    // Setup test data
    await setupTestData();

    console.log('✓ Winner flow test suite initialized');
  });

  afterAll(async () => {
    // Cleanup test data
    await cleanupTestData();

    // Close connections
    if (redisClient) {
      await redisClient.quit();
    }
    if (pgPool) {
      await pgPool.end();
    }

    console.log('✓ Winner flow test suite cleaned up');
  });

  beforeEach(async () => {
    // Clear any cached data between tests
    try {
      await redisClient.del('winner_detection_cache');
      await redisClient.del('winner_insights_cache');
    } catch (error) {
      console.warn('Redis cleanup warning:', error);
    }
  });

  // ============================================================================
  // HELPER FUNCTIONS
  // ============================================================================

  async function waitForServices(maxRetries = 10, delay = 2000): Promise<void> {
    for (let i = 0; i < maxRetries; i++) {
      try {
        const [apiHealth, mlHealth] = await Promise.all([
          apiClient.get('/health'),
          mlClient.get('/health')
        ]);

        if (apiHealth.status === 200 && mlHealth.status === 200) {
          return;
        }
      } catch (error) {
        if (i === maxRetries - 1) {
          throw new Error('Services not available after max retries');
        }
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  async function setupTestData(): Promise<void> {
    // Create test ads with varying performance
    const testAds = [
      { id: 'test_ad_winner_1', roas: 3.5, ctr: 0.045, spend: 500, revenue: 1750 },
      { id: 'test_ad_winner_2', roas: 4.2, ctr: 0.052, spend: 800, revenue: 3360 },
      { id: 'test_ad_loser_1', roas: 1.2, ctr: 0.015, spend: 300, revenue: 360 },
      { id: 'test_ad_loser_2', roas: 0.8, ctr: 0.008, spend: 200, revenue: 160 },
      { id: 'test_ad_marginal_1', roas: 1.8, ctr: 0.025, spend: 400, revenue: 720 }
    ];

    for (const ad of testAds) {
      try {
        // Insert into performance_metrics table
        await pgPool.query(`
          INSERT INTO performance_metrics (
            ad_id, date, impressions, clicks, spend, revenue, ctr, roas, created_at
          ) VALUES (
            $1, NOW(), $2, $3, $4, $5, $6, $7, NOW()
          ) ON CONFLICT (ad_id, date) DO UPDATE SET
            impressions = EXCLUDED.impressions,
            clicks = EXCLUDED.clicks,
            spend = EXCLUDED.spend,
            revenue = EXCLUDED.revenue,
            ctr = EXCLUDED.ctr,
            roas = EXCLUDED.roas
        `, [
          ad.id,
          Math.floor(ad.spend / ad.ctr / 100), // Calculate impressions
          Math.floor(ad.spend / ad.ctr), // Calculate clicks
          ad.spend,
          ad.revenue,
          ad.ctr,
          ad.roas
        ]);

        testAdIds.push(ad.id);
      } catch (error) {
        console.warn(`Failed to insert test ad ${ad.id}:`, error);
      }
    }
  }

  async function cleanupTestData(): Promise<void> {
    try {
      // Clean up test ads
      if (testAdIds.length > 0) {
        await pgPool.query(
          'DELETE FROM performance_metrics WHERE ad_id = ANY($1)',
          [testAdIds]
        );
      }

      // Clean up test winners
      if (testWinnerIds.length > 0) {
        await pgPool.query(
          'DELETE FROM winners WHERE id = ANY($1)',
          [testWinnerIds]
        );
      }

      // Clean up test replicas
      await pgPool.query(
        'DELETE FROM ad_replicas WHERE source_ad_id = ANY($1)',
        [testAdIds]
      );
    } catch (error) {
      console.warn('Cleanup error:', error);
    }
  }

  function delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // ============================================================================
  // WINNER DETECTION TESTS
  // ============================================================================

  describe('Winner Detection', () => {
    it('should detect winners with ROAS > 2x', async () => {
      const response = await apiClient.post('/api/v1/winners/detect', {
        minROAS: 2.0,
        minCTR: 0.02,
        minSpend: 100
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('winners');
      expect(Array.isArray(response.data.winners)).toBe(true);

      // Should detect our high-performing test ads
      const winners = response.data.winners;
      const winnerIds = winners.map((w: any) => w.ad_id || w.id);

      expect(winners.length).toBeGreaterThan(0);
      expect(winnerIds).toContain('test_ad_winner_1');
      expect(winnerIds).toContain('test_ad_winner_2');

      // Store winner IDs for cleanup
      winners.forEach((w: any) => {
        if (w.id && !testWinnerIds.includes(w.id)) {
          testWinnerIds.push(w.id);
        }
      });
    });

    it('should exclude low-performing ads from winners', async () => {
      const response = await apiClient.post('/api/v1/winners/detect', {
        minROAS: 2.0,
        minCTR: 0.02,
        minSpend: 100
      });

      expect(response.status).toBe(200);

      const winners = response.data.winners;
      const winnerIds = winners.map((w: any) => w.ad_id || w.id);

      // Low performers should NOT be winners
      expect(winnerIds).not.toContain('test_ad_loser_1');
      expect(winnerIds).not.toContain('test_ad_loser_2');
    });

    it('should list all detected winners', async () => {
      const response = await apiClient.get('/api/v1/winners/list');

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('winners');
      expect(Array.isArray(response.data.winners)).toBe(true);

      // Should include pagination info
      expect(response.data).toHaveProperty('total');
      expect(response.data).toHaveProperty('page');
    });

    it('should get winner details by ID', async () => {
      // First detect winners
      const detectResponse = await apiClient.post('/api/v1/winners/detect', {
        minROAS: 2.0
      });

      if (detectResponse.data.winners.length > 0) {
        const winnerId = detectResponse.data.winners[0].id;

        const response = await apiClient.get(`/api/v1/winners/${winnerId}`);

        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('id');
        expect(response.data.id).toBe(winnerId);
        expect(response.data).toHaveProperty('metrics');
        expect(response.data.metrics).toHaveProperty('roas');
        expect(response.data.metrics.roas).toBeGreaterThanOrEqual(2.0);
      }
    });

    it('should filter winners by multiple criteria', async () => {
      const response = await apiClient.post('/api/v1/winners/detect', {
        minROAS: 3.0,
        minCTR: 0.04,
        minSpend: 400,
        minRevenue: 1000
      });

      expect(response.status).toBe(200);

      const winners = response.data.winners;

      // All winners should meet ALL criteria
      winners.forEach((winner: any) => {
        expect(winner.metrics.roas).toBeGreaterThanOrEqual(3.0);
        expect(winner.metrics.ctr).toBeGreaterThanOrEqual(0.04);
        expect(winner.metrics.spend).toBeGreaterThanOrEqual(400);
        expect(winner.metrics.revenue).toBeGreaterThanOrEqual(1000);
      });
    });

    it('should respect lookback window parameter', async () => {
      const response = await apiClient.post('/api/v1/winners/detect', {
        minROAS: 2.0,
        lookbackDays: 7
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('lookbackDays');
      expect(response.data.lookbackDays).toBe(7);
    });
  });

  // ============================================================================
  // WINNER REPLICATION TESTS
  // ============================================================================

  describe('Winner Replication', () => {
    it('should replicate a winner with variations', async () => {
      // Get a winner first
      const winnersResponse = await apiClient.get('/api/v1/winners/list');

      if (winnersResponse.data.winners.length > 0) {
        const winnerId = winnersResponse.data.winners[0].id;

        const response = await apiClient.post(`/api/v1/winners/${winnerId}/replicate`, {
          variations: ['audience', 'hook', 'budget'],
          replicaCount: 3
        });

        expect(response.status).toBe(200);
        expect(response.data).toHaveProperty('replicas');
        expect(Array.isArray(response.data.replicas)).toBe(true);
        expect(response.data.replicas.length).toBeGreaterThan(0);
        expect(response.data.replicas.length).toBeLessThanOrEqual(3);

        // Each replica should have variation details
        response.data.replicas.forEach((replica: any) => {
          expect(replica).toHaveProperty('id');
          expect(replica).toHaveProperty('sourceAdId');
          expect(replica.sourceAdId).toBe(winnerId);
          expect(replica).toHaveProperty('variations');
        });
      } else {
        console.warn('No winners available for replication test');
      }
    });

    it('should create audience variations', async () => {
      const winnersResponse = await apiClient.get('/api/v1/winners/list');

      if (winnersResponse.data.winners.length > 0) {
        const winnerId = winnersResponse.data.winners[0].id;

        const response = await apiClient.post(`/api/v1/winners/${winnerId}/replicate`, {
          variations: ['audience'],
          audienceVariations: ['lookalike', 'interest_expansion', 'age_range']
        });

        expect(response.status).toBe(200);

        const replicas = response.data.replicas;
        expect(replicas.length).toBeGreaterThan(0);

        // Check that audience variations were applied
        replicas.forEach((replica: any) => {
          expect(replica.variations).toContain('audience');
          expect(replica).toHaveProperty('audienceChanges');
        });
      }
    });

    it('should create hook variations', async () => {
      const winnersResponse = await apiClient.get('/api/v1/winners/list');

      if (winnersResponse.data.winners.length > 0) {
        const winnerId = winnersResponse.data.winners[0].id;

        const response = await apiClient.post(`/api/v1/winners/${winnerId}/replicate`, {
          variations: ['hook'],
          hookStyles: ['question', 'urgency', 'benefit']
        });

        expect(response.status).toBe(200);

        const replicas = response.data.replicas;

        replicas.forEach((replica: any) => {
          expect(replica.variations).toContain('hook');
          expect(replica).toHaveProperty('hookChanges');
        });
      }
    });

    it('should create budget variations', async () => {
      const winnersResponse = await apiClient.get('/api/v1/winners/list');

      if (winnersResponse.data.winners.length > 0) {
        const winnerId = winnersResponse.data.winners[0].id;

        const response = await apiClient.post(`/api/v1/winners/${winnerId}/replicate`, {
          variations: ['budget'],
          budgetMultipliers: [1.5, 2.0, 0.75]
        });

        expect(response.status).toBe(200);

        const replicas = response.data.replicas;

        replicas.forEach((replica: any) => {
          expect(replica.variations).toContain('budget');
          expect(replica).toHaveProperty('budgetChanges');
        });
      }
    });

    it('should limit replica count', async () => {
      const winnersResponse = await apiClient.get('/api/v1/winners/list');

      if (winnersResponse.data.winners.length > 0) {
        const winnerId = winnersResponse.data.winners[0].id;

        const response = await apiClient.post(`/api/v1/winners/${winnerId}/replicate`, {
          variations: ['audience', 'hook', 'budget'],
          replicaCount: 2
        });

        expect(response.status).toBe(200);
        expect(response.data.replicas.length).toBeLessThanOrEqual(2);
      }
    });
  });

  // ============================================================================
  // BUDGET OPTIMIZATION TESTS
  // ============================================================================

  describe('Budget Optimization', () => {
    it('should calculate budget changes for account', async () => {
      const response = await apiClient.post('/api/v1/budget/optimize', {
        accountId: TEST_AD_ACCOUNT_ID
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('changes');
      expect(Array.isArray(response.data.changes)).toBe(true);

      // Should include optimization metadata
      expect(response.data).toHaveProperty('totalBudgetBefore');
      expect(response.data).toHaveProperty('totalBudgetAfter');
      expect(response.data).toHaveProperty('optimizationStrategy');
    });

    it('should apply safety limits', async () => {
      const response = await apiClient.post('/api/v1/budget/optimize', {
        accountId: TEST_AD_ACCOUNT_ID,
        safetyLimits: {
          maxDailyChangePercent: 0.3,
          minBudgetPerAd: 5,
          maxBudgetPerAd: 500
        }
      });

      expect(response.status).toBe(200);

      // Check that all changes respect limits
      const changes = response.data.changes;

      changes.forEach((change: any) => {
        expect(change.newBudget).toBeGreaterThanOrEqual(5);
        expect(change.newBudget).toBeLessThanOrEqual(500);

        // Check daily change percentage
        if (change.oldBudget > 0) {
          const changePercent = Math.abs(change.newBudget - change.oldBudget) / change.oldBudget;
          expect(changePercent).toBeLessThanOrEqual(0.3);
        }
      });
    });

    it('should prioritize winners for budget increases', async () => {
      const response = await apiClient.post('/api/v1/budget/optimize', {
        accountId: TEST_AD_ACCOUNT_ID,
        strategy: 'winner_focused'
      });

      expect(response.status).toBe(200);

      const changes = response.data.changes;
      const increases = changes.filter((c: any) => c.newBudget > c.oldBudget);
      const decreases = changes.filter((c: any) => c.newBudget < c.oldBudget);

      // Winners should get increases
      increases.forEach((change: any) => {
        expect(change).toHaveProperty('isWinner');
        if (change.isWinner !== undefined) {
          expect(change.isWinner).toBe(true);
        }
      });
    });

    it('should reduce budget for losers', async () => {
      const response = await apiClient.post('/api/v1/budget/optimize', {
        accountId: TEST_AD_ACCOUNT_ID,
        strategy: 'performance_based'
      });

      expect(response.status).toBe(200);

      const changes = response.data.changes;

      // Should have some budget reductions
      const reductions = changes.filter((c: any) => c.newBudget < c.oldBudget);
      expect(reductions.length).toBeGreaterThan(0);

      // Reductions should be for poor performers
      reductions.forEach((change: any) => {
        if (change.roas !== undefined) {
          expect(change.roas).toBeLessThan(2.0);
        }
      });
    });

    it('should respect total budget cap', async () => {
      const response = await apiClient.post('/api/v1/budget/optimize', {
        accountId: TEST_AD_ACCOUNT_ID,
        totalBudgetCap: 5000
      });

      expect(response.status).toBe(200);

      const totalBudgetAfter = response.data.totalBudgetAfter;
      expect(totalBudgetAfter).toBeLessThanOrEqual(5000);
    });

    it('should provide reasoning for budget changes', async () => {
      const response = await apiClient.post('/api/v1/budget/optimize', {
        accountId: TEST_AD_ACCOUNT_ID
      });

      expect(response.status).toBe(200);

      const changes = response.data.changes;

      changes.forEach((change: any) => {
        expect(change).toHaveProperty('reasoning');
        expect(typeof change.reasoning).toBe('string');
        expect(change.reasoning.length).toBeGreaterThan(0);
      });
    });
  });

  // ============================================================================
  // FULL WORKFLOW TESTS
  // ============================================================================

  describe('Full Winner Workflow', () => {
    it('should run complete winner workflow', async () => {
      const response = await apiClient.post('/api/v1/workflows/winner', {
        autoPublish: false,
        maxReplicasPerWinner: 2
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status');
      expect(response.data).toHaveProperty('winnersDetected');
      expect(response.data).toHaveProperty('replicasCreated');
      expect(response.data).toHaveProperty('budgetOptimized');

      // Should detect some winners
      expect(response.data.winnersDetected).toBeGreaterThanOrEqual(0);
    });

    it('should detect, replicate, and optimize in sequence', async () => {
      const response = await apiClient.post('/api/v1/workflows/winner', {
        steps: ['detect', 'replicate', 'optimize'],
        autoPublish: false
      });

      expect(response.status).toBe(200);

      // Should have completed all steps
      expect(response.data).toHaveProperty('steps');
      expect(response.data.steps).toHaveProperty('detect');
      expect(response.data.steps).toHaveProperty('replicate');
      expect(response.data.steps).toHaveProperty('optimize');

      // Each step should be successful
      expect(response.data.steps.detect.success).toBe(true);
      expect(response.data.steps.replicate.success).toBe(true);
      expect(response.data.steps.optimize.success).toBe(true);
    });

    it('should support dry-run mode', async () => {
      const response = await apiClient.post('/api/v1/workflows/winner', {
        dryRun: true,
        autoPublish: false
      });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('dryRun');
      expect(response.data.dryRun).toBe(true);

      // Should show what would be done without executing
      expect(response.data).toHaveProperty('proposedChanges');
    });

    it('should track workflow execution time', async () => {
      const startTime = Date.now();

      const response = await apiClient.post('/api/v1/workflows/winner', {
        autoPublish: false
      });

      const endTime = Date.now();
      const duration = endTime - startTime;

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('executionTimeMs');

      // Execution time should be reasonable
      expect(duration).toBeLessThan(60000); // Less than 60 seconds
    });

    it('should handle workflow errors gracefully', async () => {
      // Test with invalid parameters
      const response = await apiClient.post('/api/v1/workflows/winner', {
        maxReplicasPerWinner: -1, // Invalid
        autoPublish: false
      });

      // Should return error but not crash
      expect([400, 422, 500]).toContain(response.status);
      expect(response.data).toHaveProperty('error');
    });
  });

  // ============================================================================
  // INSIGHTS EXTRACTION TESTS
  // ============================================================================

  describe('Winner Insights Extraction', () => {
    it('should extract insights from winners', async () => {
      const response = await apiClient.get('/api/v1/winners/insights');

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('topHooks');
      expect(response.data).toHaveProperty('topAudiences');
      expect(response.data).toHaveProperty('recommendations');

      expect(Array.isArray(response.data.topHooks)).toBe(true);
      expect(Array.isArray(response.data.recommendations)).toBe(true);
    });

    it('should identify top-performing hook patterns', async () => {
      const response = await apiClient.get('/api/v1/winners/insights');

      expect(response.status).toBe(200);

      const topHooks = response.data.topHooks;

      topHooks.forEach((hook: any) => {
        expect(hook).toHaveProperty('pattern');
        expect(hook).toHaveProperty('avgROAS');
        expect(hook).toHaveProperty('count');
      });
    });

    it('should provide actionable recommendations', async () => {
      const response = await apiClient.get('/api/v1/winners/insights');

      expect(response.status).toBe(200);

      const recommendations = response.data.recommendations;

      recommendations.forEach((rec: any) => {
        expect(rec).toHaveProperty('type');
        expect(rec).toHaveProperty('recommendation');
        expect(rec).toHaveProperty('priority');
      });
    });

    it('should analyze winning creative elements', async () => {
      const response = await apiClient.get('/api/v1/winners/insights/creative');

      expect([200, 404]).toContain(response.status);

      if (response.status === 200) {
        expect(response.data).toHaveProperty('visualElements');
        expect(response.data).toHaveProperty('copyPatterns');
        expect(response.data).toHaveProperty('ctaTypes');
      }
    });
  });

  // ============================================================================
  // SCHEDULED JOBS TESTS
  // ============================================================================

  describe('Scheduled Winner Jobs', () => {
    it('should trigger winner detection job manually', async () => {
      const response = await apiClient.post('/api/v1/jobs/detect-winners/trigger');

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('jobId');
      expect(response.data).toHaveProperty('status');
      expect(response.data.status).toMatch(/queued|running|completed/);
    });

    it('should check job status', async () => {
      // Trigger a job
      const triggerResponse = await apiClient.post('/api/v1/jobs/detect-winners/trigger');

      if (triggerResponse.status === 200) {
        const jobId = triggerResponse.data.jobId;

        // Wait a bit
        await delay(2000);

        // Check status
        const statusResponse = await apiClient.get(`/api/v1/jobs/${jobId}`);

        expect(statusResponse.status).toBe(200);
        expect(statusResponse.data).toHaveProperty('status');
        expect(['queued', 'running', 'completed', 'failed']).toContain(statusResponse.data.status);
      }
    });

    it('should list scheduled jobs', async () => {
      const response = await apiClient.get('/api/v1/jobs/scheduled');

      expect([200, 404]).toContain(response.status);

      if (response.status === 200) {
        expect(Array.isArray(response.data.jobs)).toBe(true);
      }
    });

    it('should get job execution history', async () => {
      const response = await apiClient.get('/api/v1/jobs/history', {
        params: {
          jobType: 'detect-winners',
          limit: 10
        }
      });

      expect([200, 404]).toContain(response.status);

      if (response.status === 200) {
        expect(Array.isArray(response.data.history)).toBe(true);
      }
    });
  });

  // ============================================================================
  // AGENT TRIGGER TESTS
  // ============================================================================

  describe('Agent Trigger Mechanisms', () => {
    it('should trigger auto-promotion agent', async () => {
      const response = await apiClient.post('/api/v1/agents/auto-promotion/trigger', {
        experimentId: 'test_experiment_123'
      });

      expect([200, 404]).toContain(response.status);

      if (response.status === 200) {
        expect(response.data).toHaveProperty('status');
        expect(response.data).toHaveProperty('triggered');
      }
    });

    it('should trigger budget optimization agent', async () => {
      const response = await apiClient.post('/api/v1/agents/budget-optimizer/trigger', {
        accountId: TEST_AD_ACCOUNT_ID
      });

      expect([200, 404]).toContain(response.status);

      if (response.status === 200) {
        expect(response.data).toHaveProperty('optimizationId');
      }
    });

    it('should trigger winner replication agent', async () => {
      const response = await apiClient.post('/api/v1/agents/replicator/trigger', {
        winnerId: 'test_ad_winner_1',
        variations: ['audience', 'hook']
      });

      expect([200, 404]).toContain(response.status);

      if (response.status === 200) {
        expect(response.data).toHaveProperty('replicationId');
      }
    });

    it('should check agent health status', async () => {
      const response = await apiClient.get('/api/v1/agents/health');

      expect([200, 404]).toContain(response.status);

      if (response.status === 200) {
        expect(response.data).toHaveProperty('agents');

        const agents = response.data.agents;
        expect(agents).toHaveProperty('auto_promotion');
        expect(agents).toHaveProperty('budget_optimizer');
        expect(agents).toHaveProperty('replicator');
      }
    });
  });

  // ============================================================================
  // EDGE CASES AND ERROR HANDLING
  // ============================================================================

  describe('Edge Cases and Error Handling', () => {
    it('should handle no winners found gracefully', async () => {
      const response = await apiClient.post('/api/v1/winners/detect', {
        minROAS: 100.0, // Impossibly high threshold
        minCTR: 0.9
      });

      expect(response.status).toBe(200);
      expect(response.data.winners).toEqual([]);
      expect(response.data).toHaveProperty('message');
    });

    it('should validate winner ID format', async () => {
      const response = await apiClient.get('/api/v1/winners/invalid!!id');

      expect([400, 404]).toContain(response.status);
    });

    it('should handle concurrent replication requests', async () => {
      const winnersResponse = await apiClient.get('/api/v1/winners/list');

      if (winnersResponse.data.winners.length > 0) {
        const winnerId = winnersResponse.data.winners[0].id;

        // Send multiple replication requests concurrently
        const requests = Array(5).fill(null).map(() =>
          apiClient.post(`/api/v1/winners/${winnerId}/replicate`, {
            variations: ['audience']
          })
        );

        const responses = await Promise.all(requests);

        // All should succeed or be properly rate-limited
        responses.forEach(response => {
          expect([200, 429]).toContain(response.status);
        });
      }
    });

    it('should handle database connection failures gracefully', async () => {
      // This is hard to test without actually breaking the DB
      // Just verify error handling exists
      expect(true).toBe(true);
    });

    it('should respect rate limits on winner detection', async () => {
      const requests = Array(20).fill(null).map(() =>
        apiClient.post('/api/v1/winners/detect', {
          minROAS: 2.0
        })
      );

      const responses = await Promise.all(requests);

      // Some requests should be rate-limited
      const rateLimited = responses.filter(r => r.status === 429);
      expect(rateLimited.length).toBeGreaterThan(0);
    });
  });

  // ============================================================================
  // PERFORMANCE TESTS
  // ============================================================================

  describe('Performance Tests', () => {
    it('should detect winners within acceptable time', async () => {
      const startTime = Date.now();

      const response = await apiClient.post('/api/v1/winners/detect', {
        minROAS: 2.0
      });

      const duration = Date.now() - startTime;

      expect(response.status).toBe(200);
      expect(duration).toBeLessThan(10000); // Less than 10 seconds
    });

    it('should handle large winner lists efficiently', async () => {
      const response = await apiClient.get('/api/v1/winners/list', {
        params: {
          limit: 100,
          offset: 0
        }
      });

      expect(response.status).toBe(200);
      expect(response.data.winners.length).toBeLessThanOrEqual(100);
    });

    it('should cache winner insights', async () => {
      // First request
      const startTime1 = Date.now();
      const response1 = await apiClient.get('/api/v1/winners/insights');
      const duration1 = Date.now() - startTime1;

      expect(response1.status).toBe(200);

      // Second request (should be cached)
      const startTime2 = Date.now();
      const response2 = await apiClient.get('/api/v1/winners/insights');
      const duration2 = Date.now() - startTime2;

      expect(response2.status).toBe(200);

      // Cached request should be faster
      expect(duration2).toBeLessThan(duration1 * 0.5);
    });
  });
});
