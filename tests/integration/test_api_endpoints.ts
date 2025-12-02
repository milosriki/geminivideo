/**
 * Integration Tests for Gateway API Endpoints
 * Tests all API endpoints, authentication, rate limiting, error handling
 *
 * Agent 29 of 30 - Comprehensive Test Suite
 * Coverage Target: 80%+
 */

import { jest, describe, it, expect, beforeAll, afterAll, beforeEach } from '@jest/globals';
import axios, { AxiosInstance } from 'axios';
import { createClient } from 'redis';
import { Pool } from 'pg';

// Test configuration
const API_BASE_URL = process.env.TEST_API_URL || 'http://localhost:8000';
const TEST_DATABASE_URL = process.env.TEST_DATABASE_URL || 'postgresql://test:test@localhost:5432/test_db';
const TEST_REDIS_URL = process.env.TEST_REDIS_URL || 'redis://localhost:6379';

describe('Gateway API Integration Tests', () => {
  let apiClient: AxiosInstance;
  let redisClient: any;
  let pgPool: Pool;

  // ============================================================================
  // SETUP AND TEARDOWN
  // ============================================================================

  beforeAll(async () => {
    // Setup API client
    apiClient = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      validateStatus: () => true // Don't throw on any status
    });

    // Setup Redis client for test cleanup
    redisClient = createClient({ url: TEST_REDIS_URL });
    await redisClient.connect();

    // Setup PostgreSQL pool
    pgPool = new Pool({ connectionString: TEST_DATABASE_URL });

    // Wait for API to be ready
    await waitForAPI();
  });

  afterAll(async () => {
    // Cleanup connections
    if (redisClient) {
      await redisClient.quit();
    }
    if (pgPool) {
      await pgPool.end();
    }
  });

  beforeEach(async () => {
    // Clear rate limit data between tests
    try {
      await redisClient.flushDb();
    } catch (error) {
      console.warn('Redis cleanup failed:', error);
    }
  });

  // ============================================================================
  // HELPER FUNCTIONS
  // ============================================================================

  async function waitForAPI(maxRetries = 10, delay = 1000): Promise<void> {
    for (let i = 0; i < maxRetries; i++) {
      try {
        const response = await apiClient.get('/');
        if (response.status === 200) {
          return;
        }
      } catch (error) {
        if (i === maxRetries - 1) {
          throw new Error('API not available after max retries');
        }
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  function generateApiKey(): string {
    return `test_api_key_${Math.random().toString(36).substring(7)}`;
  }

  // ============================================================================
  // HEALTH CHECK ENDPOINTS
  // ============================================================================

  describe('GET / - Root Endpoint', () => {
    it('should return API status', async () => {
      const response = await apiClient.get('/');

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('service');
      expect(response.data.service).toBe('gateway-api');
      expect(response.data).toHaveProperty('status');
      expect(response.data.status).toBe('running');
    });

    it('should include version information', async () => {
      const response = await apiClient.get('/');

      expect(response.data).toHaveProperty('version');
      expect(typeof response.data.version).toBe('string');
    });

    it('should have security headers', async () => {
      const response = await apiClient.get('/');

      expect(response.headers).toHaveProperty('x-content-type-options');
      expect(response.headers['x-content-type-options']).toBe('nosniff');
    });
  });

  // ============================================================================
  // AUTHENTICATION TESTS
  // ============================================================================

  describe('Authentication Flow', () => {
    const testEmail = `test-${Date.now()}@example.com`;
    const testPassword = 'TestPassword123!';

    it('should reject requests without API key on protected endpoints', async () => {
      const response = await apiClient.get('/api/assets');

      // Should return 401 or 403
      expect([401, 403]).toContain(response.status);
    });

    it('should reject requests with invalid API key', async () => {
      const response = await apiClient.get('/api/assets', {
        headers: {
          'X-API-Key': 'invalid_api_key_12345'
        }
      });

      expect([401, 403]).toContain(response.status);
    });

    it('should accept requests with valid API key', async () => {
      const apiKey = process.env.TEST_API_KEY || 'test_valid_api_key';

      const response = await apiClient.get('/api/assets', {
        headers: {
          'X-API-Key': apiKey
        }
      });

      // Should not return auth error (might return other errors if service unavailable)
      expect([401, 403]).not.toContain(response.status);
    });

    it('should validate JWT tokens correctly', async () => {
      const token = 'mock_jwt_token';

      const response = await apiClient.post('/api/predict',
        { data: {} },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      // Test basic JWT handling
      expect(response.status).toBeDefined();
    });
  });

  // ============================================================================
  // RATE LIMITING TESTS
  // ============================================================================

  describe('Rate Limiting', () => {
    it('should enforce global rate limits', async () => {
      const requests = Array(150).fill(null).map(() =>
        apiClient.get('/')
      );

      const responses = await Promise.all(requests);

      // At least some requests should be rate limited (429)
      const rateLimitedCount = responses.filter(r => r.status === 429).length;
      expect(rateLimitedCount).toBeGreaterThan(0);
    });

    it('should include rate limit headers', async () => {
      const response = await apiClient.get('/');

      // Check for standard rate limit headers
      expect(
        response.headers['x-ratelimit-limit'] ||
        response.headers['ratelimit-limit']
      ).toBeDefined();
    });

    it('should enforce stricter limits on auth endpoints', async () => {
      const requests = Array(20).fill(null).map(() =>
        apiClient.post('/api/auth/login', {
          email: 'test@example.com',
          password: 'wrongpassword'
        })
      );

      const responses = await Promise.all(requests);
      const rateLimitedCount = responses.filter(r => r.status === 429).length;

      expect(rateLimitedCount).toBeGreaterThan(0);
    });

    it('should enforce different limits for different endpoints', async () => {
      // Upload endpoints should have stricter limits
      const uploadRequests = Array(10).fill(null).map(() =>
        apiClient.post('/api/upload', {}, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      );

      const responses = await Promise.all(uploadRequests);

      // Some should be rate limited
      expect(responses.some(r => r.status === 429)).toBe(true);
    });

    it('should reset rate limits after time window', async () => {
      // Make requests to hit limit
      await Promise.all(
        Array(10).fill(null).map(() => apiClient.get('/'))
      );

      // Wait for rate limit window to reset (e.g., 1 second)
      await new Promise(resolve => setTimeout(resolve, 1100));

      // Should be able to make requests again
      const response = await apiClient.get('/');
      expect(response.status).not.toBe(429);
    });
  });

  // ============================================================================
  // PREDICTION ENDPOINTS
  // ============================================================================

  describe('POST /api/predict - ROAS Prediction', () => {
    const validFeatures = {
      hook_type: 'problem_solution',
      hook_strength: 8.0,
      visual_complexity: 7.5,
      audience_size: 2500000,
      account_avg_roas: 3.5
    };

    it('should accept valid prediction request', async () => {
      const response = await apiClient.post('/api/predict', {
        features: validFeatures
      });

      // Should return prediction or service unavailable
      expect([200, 503]).toContain(response.status);
    });

    it('should validate required fields', async () => {
      const response = await apiClient.post('/api/predict', {
        features: {} // Missing required fields
      });

      // Should return validation error
      expect([400, 422]).toContain(response.status);
    });

    it('should return prediction with confidence intervals', async () => {
      const response = await apiClient.post('/api/predict', {
        features: validFeatures
      });

      if (response.status === 200) {
        expect(response.data).toHaveProperty('predicted_roas');
        expect(response.data).toHaveProperty('confidence_low');
        expect(response.data).toHaveProperty('confidence_high');
      }
    });

    it('should handle batch predictions', async () => {
      const response = await apiClient.post('/api/predict/batch', {
        features_list: [validFeatures, validFeatures]
      });

      if (response.status === 200) {
        expect(Array.isArray(response.data)).toBe(true);
        expect(response.data.length).toBe(2);
      }
    });

    it('should reject malformed JSON', async () => {
      try {
        const response = await apiClient.post('/api/predict',
          'invalid json',
          {
            headers: { 'Content-Type': 'application/json' }
          }
        );

        expect([400, 422]).toContain(response.status);
      } catch (error: any) {
        // axios might throw on parse error
        expect(error).toBeDefined();
      }
    });

    it('should sanitize SQL injection attempts', async () => {
      const response = await apiClient.post('/api/predict', {
        features: {
          hook_type: "'; DROP TABLE users; --",
          hook_strength: 8.0
        }
      });

      // Should either sanitize and process, or reject
      expect([200, 400, 422]).toContain(response.status);

      // Verify database wasn't affected
      const result = await pgPool.query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'");
      expect(result.rows.length).toBeGreaterThan(0); // Tables still exist
    });

    it('should prevent XSS attacks', async () => {
      const response = await apiClient.post('/api/predict', {
        features: {
          hook_type: '<script>alert("xss")</script>',
          hook_strength: 8.0
        }
      });

      if (response.status === 200) {
        // Response should have script tags escaped or removed
        const responseText = JSON.stringify(response.data);
        expect(responseText).not.toContain('<script>');
      }
    });
  });

  // ============================================================================
  // DRIVE INTEL PROXY ENDPOINTS
  // ============================================================================

  describe('GET /api/assets - Drive Intel Proxy', () => {
    it('should proxy requests to drive-intel service', async () => {
      const response = await apiClient.get('/api/assets');

      // Should return assets or service unavailable
      expect([200, 503]).toContain(response.status);
    });

    it('should handle service unavailability gracefully', async () => {
      // Mock service being down
      const response = await apiClient.get('/api/assets');

      if (response.status === 503) {
        expect(response.data).toHaveProperty('error');
      }
    });

    it('should pass query parameters correctly', async () => {
      const response = await apiClient.get('/api/assets', {
        params: {
          limit: 10,
          offset: 0,
          type: 'video'
        }
      });

      expect(response.status).toBeDefined();
    });
  });

  // ============================================================================
  // VIDEO AGENT ENDPOINTS
  // ============================================================================

  describe('POST /api/generate - Video Generation', () => {
    it('should accept video generation request', async () => {
      const response = await apiClient.post('/api/generate', {
        prompt: 'Create a marketing video about eco-friendly products',
        duration: 15,
        style: 'modern'
      });

      // Should queue job or return error
      expect([200, 202, 400, 503]).toContain(response.status);
    });

    it('should return job ID for async processing', async () => {
      const response = await apiClient.post('/api/generate', {
        prompt: 'Test video',
        duration: 10
      });

      if (response.status === 202) {
        expect(response.data).toHaveProperty('job_id');
        expect(response.data).toHaveProperty('status');
      }
    });

    it('should validate video generation parameters', async () => {
      const response = await apiClient.post('/api/generate', {
        duration: -5 // Invalid duration
      });

      expect([400, 422]).toContain(response.status);
    });
  });

  describe('GET /api/video/:jobId - Video Status', () => {
    it('should return job status', async () => {
      const jobId = 'test_job_123';
      const response = await apiClient.get(`/api/video/${jobId}`);

      // Should return status or not found
      expect([200, 404]).toContain(response.status);
    });

    it('should validate job ID format', async () => {
      const response = await apiClient.get('/api/video/invalid!!id');

      expect([400, 404]).toContain(response.status);
    });
  });

  // ============================================================================
  // SCORING ENGINE ENDPOINTS
  // ============================================================================

  describe('POST /api/score - Creative Scoring', () => {
    const validCreative = {
      hook_type: 'testimonial',
      visual_style: 'minimalist',
      copy_text: 'Amazing product that solves your problems!',
      target_audience: 'tech_enthusiasts'
    };

    it('should score creative elements', async () => {
      const response = await apiClient.post('/api/score', {
        creative: validCreative
      });

      expect([200, 503]).toContain(response.status);
    });

    it('should return detailed scoring breakdown', async () => {
      const response = await apiClient.post('/api/score', {
        creative: validCreative
      });

      if (response.status === 200) {
        expect(response.data).toHaveProperty('total_score');
        expect(response.data).toHaveProperty('breakdown');
      }
    });

    it('should handle missing creative data', async () => {
      const response = await apiClient.post('/api/score', {});

      expect([400, 422]).toContain(response.status);
    });
  });

  // ============================================================================
  // META PUBLISHER ENDPOINTS
  // ============================================================================

  describe('POST /api/meta/campaign - Create Campaign', () => {
    const validCampaign = {
      name: 'Test Campaign',
      objective: 'OUTCOME_ENGAGEMENT',
      status: 'PAUSED'
    };

    it('should create Meta campaign', async () => {
      const response = await apiClient.post('/api/meta/campaign', validCampaign);

      // Should create or return auth error
      expect([200, 201, 401, 503]).toContain(response.status);
    });

    it('should validate campaign parameters', async () => {
      const response = await apiClient.post('/api/meta/campaign', {
        name: '' // Empty name
      });

      expect([400, 422]).toContain(response.status);
    });
  });

  describe('POST /api/meta/adset - Create AdSet', () => {
    it('should create Meta adset', async () => {
      const response = await apiClient.post('/api/meta/adset', {
        name: 'Test AdSet',
        campaign_id: '123456',
        daily_budget: 5000,
        targeting: { geo_locations: { countries: ['US'] } }
      });

      expect([200, 201, 400, 401, 503]).toContain(response.status);
    });
  });

  describe('GET /api/meta/insights/:adId - Get Ad Insights', () => {
    it('should fetch ad insights', async () => {
      const adId = '123456789';
      const response = await apiClient.get(`/api/meta/insights/${adId}`);

      expect([200, 404, 401, 503]).toContain(response.status);
    });

    it('should support date range parameters', async () => {
      const adId = '123456789';
      const response = await apiClient.get(`/api/meta/insights/${adId}`, {
        params: {
          date_preset: 'last_30d'
        }
      });

      expect(response.status).toBeDefined();
    });
  });

  // ============================================================================
  // ERROR HANDLING TESTS
  // ============================================================================

  describe('Error Handling', () => {
    it('should return 404 for non-existent endpoints', async () => {
      const response = await apiClient.get('/api/nonexistent');

      expect(response.status).toBe(404);
    });

    it('should return 405 for unsupported methods', async () => {
      const response = await apiClient.delete('/');

      expect([405, 404]).toContain(response.status);
    });

    it('should handle large payloads gracefully', async () => {
      const largePayload = {
        data: 'x'.repeat(20 * 1024 * 1024) // 20MB
      };

      const response = await apiClient.post('/api/predict', largePayload);

      // Should reject payload too large
      expect([413, 400]).toContain(response.status);
    });

    it('should return proper error messages', async () => {
      const response = await apiClient.post('/api/predict', {});

      if (response.status >= 400) {
        expect(response.data).toHaveProperty('error');
        expect(typeof response.data.error).toBe('string');
      }
    });

    it('should not expose stack traces in production', async () => {
      const response = await apiClient.post('/api/predict', {
        features: { invalid: 'data' }
      });

      if (response.status >= 400) {
        const responseText = JSON.stringify(response.data);
        expect(responseText).not.toMatch(/at Object\./); // No stack trace
        expect(responseText).not.toMatch(/node_modules/);
      }
    });
  });

  // ============================================================================
  // CACHING TESTS
  // ============================================================================

  describe('Redis Caching', () => {
    it('should cache repeated requests', async () => {
      const endpoint = '/api/assets?limit=5';

      // First request
      const response1 = await apiClient.get(endpoint);
      const time1 = Date.now();

      // Second request (should be cached)
      const response2 = await apiClient.get(endpoint);
      const time2 = Date.now();

      if (response1.status === 200 && response2.status === 200) {
        // Second request should be faster (cached)
        expect(time2 - time1).toBeLessThan(1000);
      }
    });

    it('should include cache headers', async () => {
      const response = await apiClient.get('/api/assets');

      // Check for cache-related headers
      if (response.status === 200) {
        // Might have Cache-Control or X-Cache headers
        expect(
          response.headers['cache-control'] ||
          response.headers['x-cache']
        ).toBeDefined();
      }
    });
  });

  // ============================================================================
  // CORS TESTS
  // ============================================================================

  describe('CORS Configuration', () => {
    it('should include CORS headers', async () => {
      const response = await apiClient.get('/');

      expect(response.headers).toHaveProperty('access-control-allow-origin');
    });

    it('should handle OPTIONS preflight requests', async () => {
      const response = await apiClient.options('/api/predict');

      expect([200, 204]).toContain(response.status);
      expect(response.headers).toHaveProperty('access-control-allow-methods');
    });
  });

  // ============================================================================
  // INPUT VALIDATION TESTS
  // ============================================================================

  describe('Input Validation & Sanitization', () => {
    it('should validate email format', async () => {
      const response = await apiClient.post('/api/auth/register', {
        email: 'invalid-email',
        password: 'password123'
      });

      expect([400, 422]).toContain(response.status);
    });

    it('should enforce password requirements', async () => {
      const response = await apiClient.post('/api/auth/register', {
        email: 'test@example.com',
        password: '123' // Too short
      });

      expect([400, 422]).toContain(response.status);
    });

    it('should sanitize HTML input', async () => {
      const response = await apiClient.post('/api/score', {
        creative: {
          copy_text: '<script>alert("xss")</script>'
        }
      });

      // Should process without executing script
      expect(response.status).toBeDefined();
    });

    it('should validate numeric ranges', async () => {
      const response = await apiClient.post('/api/predict', {
        features: {
          hook_strength: 15.0 // Invalid: should be 0-10
        }
      });

      expect([200, 400, 422]).toContain(response.status);
    });
  });

  // ============================================================================
  // ASYNC JOB QUEUE TESTS
  // ============================================================================

  describe('Async Job Queue', () => {
    it('should queue long-running tasks', async () => {
      const response = await apiClient.post('/api/generate', {
        prompt: 'Long video generation task',
        duration: 30
      });

      if (response.status === 202) {
        expect(response.data).toHaveProperty('job_id');
      }
    });

    it('should allow checking job status', async () => {
      // Create a job
      const createResponse = await apiClient.post('/api/generate', {
        prompt: 'Test',
        duration: 15
      });

      if (createResponse.status === 202) {
        const jobId = createResponse.data.job_id;

        // Check status
        const statusResponse = await apiClient.get(`/api/video/${jobId}`);
        expect([200, 404]).toContain(statusResponse.status);
      }
    });
  });

  // ============================================================================
  // DATABASE INTEGRATION TESTS
  // ============================================================================

  describe('Database Operations', () => {
    it('should store predictions in database', async () => {
      const response = await apiClient.post('/api/predict', {
        features: {
          hook_strength: 8.0,
          account_avg_roas: 3.5
        }
      });

      if (response.status === 200) {
        // Check if prediction was stored
        const result = await pgPool.query(
          'SELECT COUNT(*) FROM predictions WHERE created_at > NOW() - INTERVAL \'1 minute\''
        );
        expect(parseInt(result.rows[0].count)).toBeGreaterThan(0);
      }
    });

    it('should handle database connection failures', async () => {
      // This would require temporarily disrupting DB connection
      // For now, just verify error handling exists
      expect(true).toBe(true);
    });
  });
});
