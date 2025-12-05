/**
 * A/B Testing Routes
 * Agent 58 - A/B test experiment management
 *
 * Provides Thompson Sampling A/B test management:
 * - Create and manage experiments
 * - Track variant performance
 * - Determine statistical winners
 * - Promote winning variants
 */

import { Router, Request, Response } from 'express';
import { Pool } from 'pg';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import { apiRateLimiter, uploadRateLimiter, validateInput } from '../middleware/security';

const router = Router();

// Service URLs
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8003';

/**
 * Create A/B tests router with database connection
 */
export function createABTestsRouter(pgPool: Pool): Router {
  /**
   * POST /api/ab-tests
   * Create a new A/B test experiment
   */
  router.post(
    '/',
    uploadRateLimiter,
    validateInput({
      body: {
        name: { type: 'string', required: true, min: 1, max: 255, sanitize: true },
        campaign_id: { type: 'uuid', required: true },
        variants: { type: 'array', required: true, min: 2 },
        objective: { type: 'string', required: false, enum: ['ctr', 'conversions', 'roas', 'engagement'] },
        budget_split: { type: 'string', required: false, enum: ['even', 'thompson_sampling', 'weighted'] },
        total_budget: { type: 'number', required: true, min: 1 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const {
          name,
          campaign_id,
          variants,
          objective = 'conversions',
          budget_split = 'thompson_sampling',
          total_budget
        } = req.body;

        console.log(`Creating A/B test: ${name} with ${variants.length} variants`);

        // Validate campaign exists
        const campaignCheck = await pgPool.query(
          'SELECT id FROM campaigns WHERE id = $1',
          [campaign_id]
        );

        if (campaignCheck.rows.length === 0) {
          return res.status(404).json({
            error: 'Campaign not found',
            message: `Campaign with id ${campaign_id} does not exist`
          });
        }

        // Forward to ML service for Thompson Sampling experiment creation
        const mlResponse = await axios.post(
          `${ML_SERVICE_URL}/api/ml/ab/experiments`,
          {
            name,
            campaign_id,
            variants: variants.map((v: any, idx: number) => ({
              variant_id: v.variant_id || uuidv4(),
              name: v.name || `Variant ${idx + 1}`,
              ad_id: v.ad_id,
              video_id: v.video_id,
              creative_config: v.creative_config || {}
            })),
            objective,
            budget_split,
            total_budget
          },
          { timeout: 30000 }
        );

        const experiment = mlResponse.data;

        console.log(`A/B test created successfully: ${experiment.experiment_id}`);

        res.status(201).json({
          status: 'success',
          message: 'A/B test experiment created successfully',
          experiment: {
            experiment_id: experiment.experiment_id,
            name: experiment.name,
            campaign_id: experiment.campaign_id,
            variants: experiment.variants,
            objective: experiment.objective,
            budget_split: experiment.budget_split,
            total_budget: experiment.total_budget,
            status: experiment.status || 'active',
            created_at: experiment.created_at || new Date().toISOString()
          }
        });

      } catch (error: any) {
        console.error('Error creating A/B test:', error);
        res.status(error.response?.status || 500).json({
          error: 'Failed to create A/B test',
          message: error.message,
          details: error.response?.data
        });
      }
    }
  );

  /**
   * GET /api/ab-tests
   * List all A/B test experiments
   */
  router.get(
    '/',
    apiRateLimiter,
    validateInput({
      query: {
        campaign_id: { type: 'uuid', required: false },
        status: { type: 'string', required: false, enum: ['active', 'paused', 'completed'] },
        limit: { type: 'number', required: false, min: 1, max: 100 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { campaign_id, status, limit = 20 } = req.query;

        console.log(`Fetching A/B tests: campaign_id=${campaign_id || 'all'}, status=${status || 'all'}`);

        // Try ML service first
        try {
          const mlResponse = await axios.get(`${ML_SERVICE_URL}/api/ml/ab/experiments`, {
            params: { campaign_id, status, limit },
            timeout: 10000
          });

          return res.json(mlResponse.data);
        } catch (mlError: any) {
          console.warn('ML service unavailable, falling back to database:', mlError.message);
        }

        // Fallback to database query
        let query = `
          SELECT
            c.id as experiment_id,
            c.name,
            c.status,
            c.created_at,
            c.budget_daily as total_budget,
            COUNT(DISTINCT co.id) as variant_count,
            COALESCE(SUM(co.conversions), 0) as total_conversions,
            COALESCE(SUM(co.spend), 0) as total_spend
          FROM campaigns c
          LEFT JOIN campaign_outcomes co ON c.id = co.campaign_id
          WHERE c.status != 'deleted'
        `;

        const values: any[] = [];
        let paramIndex = 1;

        if (campaign_id) {
          query += ` AND c.id = $${paramIndex}`;
          values.push(campaign_id);
          paramIndex++;
        }

        if (status) {
          query += ` AND c.status = $${paramIndex}`;
          values.push(status);
          paramIndex++;
        }

        query += `
          GROUP BY c.id, c.name, c.status, c.created_at, c.budget_daily
          ORDER BY c.created_at DESC
          LIMIT $${paramIndex}
        `;

        values.push(parseInt(limit as string));

        const result = await pgPool.query(query, values);

        const experiments = result.rows.map(row => ({
          experiment_id: row.experiment_id,
          name: row.name,
          status: row.status,
          created_at: row.created_at,
          total_budget: parseFloat(row.total_budget),
          variant_count: parseInt(row.variant_count),
          total_conversions: parseInt(row.total_conversions),
          total_spend: parseFloat(row.total_spend)
        }));

        res.json({
          status: 'success',
          experiments,
          count: experiments.length
        });

      } catch (error: any) {
        console.error('Error fetching A/B tests:', error);
        res.status(500).json({
          error: 'Failed to fetch A/B tests',
          message: error.message,
          experiments: []
        });
      }
    }
  );

  /**
   * GET /api/ab-tests/:id
   * Get detailed A/B test experiment information
   */
  router.get(
    '/:id',
    apiRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;

        console.log(`Fetching A/B test details: ${id}`);

        // Try ML service first
        try {
          const mlResponse = await axios.get(`${ML_SERVICE_URL}/api/ml/ab/experiments/${id}`, {
            timeout: 10000
          });

          return res.json(mlResponse.data);
        } catch (mlError: any) {
          console.warn('ML service unavailable, falling back to database:', mlError.message);
        }

        // Fallback to database query
        const query = `
          SELECT
            c.id as experiment_id,
            c.name,
            c.status,
            c.budget_daily as total_budget,
            c.created_at,
            c.updated_at
          FROM campaigns c
          WHERE c.id = $1
        `;

        const result = await pgPool.query(query, [id]);

        if (result.rows.length === 0) {
          return res.status(404).json({
            error: 'A/B test not found',
            message: `A/B test with id ${id} does not exist`
          });
        }

        const experiment = result.rows[0];

        // Get variants (campaign outcomes)
        const variantsQuery = `
          SELECT
            co.id as variant_id,
            co.impressions,
            co.clicks,
            co.conversions,
            co.spend,
            co.roas,
            co.created_at
          FROM campaign_outcomes co
          WHERE co.campaign_id = $1
          ORDER BY co.conversions DESC
        `;

        const variantsResult = await pgPool.query(variantsQuery, [id]);

        res.json({
          status: 'success',
          experiment: {
            experiment_id: experiment.experiment_id,
            name: experiment.name,
            status: experiment.status,
            total_budget: parseFloat(experiment.total_budget),
            created_at: experiment.created_at,
            updated_at: experiment.updated_at,
            variants: variantsResult.rows.map((v, idx) => ({
              variant_id: v.variant_id,
              name: `Variant ${idx + 1}`,
              impressions: parseInt(v.impressions) || 0,
              clicks: parseInt(v.clicks) || 0,
              conversions: parseInt(v.conversions) || 0,
              spend: parseFloat(v.spend) || 0,
              roas: parseFloat(v.roas) || 0,
              ctr: parseInt(v.impressions) > 0
                ? (parseInt(v.clicks) / parseInt(v.impressions)) * 100
                : 0
            }))
          }
        });

      } catch (error: any) {
        console.error('Error fetching A/B test:', error);
        res.status(500).json({
          error: 'Failed to fetch A/B test',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/ab-tests/:id/winner
   * Determine the statistical winner of an A/B test
   */
  router.get(
    '/:id/winner',
    apiRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      },
      query: {
        confidence_level: { type: 'number', required: false, min: 0.8, max: 0.99 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;
        const { confidence_level = 0.95 } = req.query;

        console.log(`Determining A/B test winner: ${id}, confidence=${confidence_level}`);

        // Forward to ML service for Thompson Sampling winner calculation
        const mlResponse = await axios.get(
          `${ML_SERVICE_URL}/api/ml/ab/experiments/${id}/winner`,
          {
            params: { confidence_level },
            timeout: 30000
          }
        );

        res.json(mlResponse.data);

      } catch (error: any) {
        console.error('Error determining A/B test winner:', error);

        // If ML service is down, provide fallback based on simple metrics
        if (error.code === 'ECONNREFUSED' || error.response?.status === 503) {
          try {
            const { id } = req.params;

            // Get variants from database
            const variantsQuery = `
              SELECT
                co.id as variant_id,
                co.impressions,
                co.clicks,
                co.conversions,
                co.spend,
                co.roas
              FROM campaign_outcomes co
              WHERE co.campaign_id = $1
              ORDER BY co.conversions DESC
            `;

            const variantsResult = await pgPool.query(variantsQuery, [id]);

            if (variantsResult.rows.length === 0) {
              return res.status(404).json({
                error: 'No variants found',
                message: 'This experiment has no variants with data'
              });
            }

            // Simple winner determination by conversions
            const winner = variantsResult.rows[0];

            return res.json({
              status: 'success',
              method: 'fallback_simple_comparison',
              winner: {
                variant_id: winner.variant_id,
                conversions: parseInt(winner.conversions),
                spend: parseFloat(winner.spend),
                roas: parseFloat(winner.roas),
                confidence: 0 // Cannot calculate without ML service
              },
              note: 'Statistical analysis unavailable. Winner determined by highest conversions.',
              all_variants: variantsResult.rows.map(v => ({
                variant_id: v.variant_id,
                conversions: parseInt(v.conversions),
                spend: parseFloat(v.spend),
                roas: parseFloat(v.roas)
              }))
            });
          } catch (fallbackError: any) {
            return res.status(500).json({
              error: 'Failed to determine winner',
              message: fallbackError.message
            });
          }
        }

        res.status(error.response?.status || 500).json({
          error: 'Failed to determine winner',
          message: error.message,
          details: error.response?.data
        });
      }
    }
  );

  /**
   * POST /api/ab-tests/:id/promote
   * Promote winning variant to full production
   */
  router.post(
    '/:id/promote',
    uploadRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      },
      body: {
        variant_id: { type: 'uuid', required: true },
        new_budget: { type: 'number', required: true, min: 1 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;
        const { variant_id, new_budget } = req.body;

        console.log(`Promoting variant ${variant_id} from experiment ${id}`);

        // Forward to ML service
        const mlResponse = await axios.post(
          `${ML_SERVICE_URL}/api/ml/ab/experiments/${id}/promote`,
          { variant_id, new_budget },
          { timeout: 30000 }
        );

        // Update campaign status in database
        await pgPool.query(
          `UPDATE campaigns SET status = 'completed', updated_at = NOW() WHERE id = $1`,
          [id]
        );

        res.json({
          status: 'success',
          message: 'Variant promoted successfully',
          ...mlResponse.data
        });

      } catch (error: any) {
        console.error('Error promoting variant:', error);
        res.status(error.response?.status || 500).json({
          error: 'Failed to promote variant',
          message: error.message,
          details: error.response?.data
        });
      }
    }
  );

  /**
   * POST /api/ab-tests/:id/pause
   * Pause an A/B test experiment
   */
  router.post(
    '/:id/pause',
    apiRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;

        console.log(`Pausing A/B test: ${id}`);

        // Update campaign status
        const updateQuery = `
          UPDATE campaigns
          SET status = 'paused', updated_at = NOW()
          WHERE id = $1 AND status = 'active'
          RETURNING *
        `;

        const result = await pgPool.query(updateQuery, [id]);

        if (result.rows.length === 0) {
          return res.status(404).json({
            error: 'Experiment not found or not active',
            message: `Experiment with id ${id} does not exist or is not active`
          });
        }

        // Notify ML service
        try {
          await axios.post(
            `${ML_SERVICE_URL}/api/ml/ab/experiments/${id}/pause`,
            {},
            { timeout: 5000 }
          );
        } catch (mlError: any) {
          console.warn('ML service notification failed:', mlError.message);
        }

        res.json({
          status: 'success',
          message: 'A/B test paused successfully',
          experiment_id: id
        });

      } catch (error: any) {
        console.error('Error pausing A/B test:', error);
        res.status(500).json({
          error: 'Failed to pause A/B test',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/ab-tests/:id/results
   * Get detailed results for an A/B test
   */
  router.get(
    '/:id/results',
    apiRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;

        console.log(`Fetching A/B test results: ${id}`);

        // Forward to ML service for detailed statistical analysis
        const mlResponse = await axios.get(
          `${ML_SERVICE_URL}/api/ml/ab/experiments/${id}/results`,
          { timeout: 30000 }
        );

        res.json(mlResponse.data);

      } catch (error: any) {
        console.error('Error fetching A/B test results:', error);
        res.status(error.response?.status || 500).json({
          error: 'Failed to fetch A/B test results',
          message: error.message,
          details: error.response?.data
        });
      }
    }
  );

  /**
   * GET /api/ab-tests/:id/variants
   * Get variant performance data
   */
  router.get(
    '/:id/variants',
    apiRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;

        console.log(`Fetching variant performance: ${id}`);

        // Forward to ML service
        const mlResponse = await axios.get(
          `${ML_SERVICE_URL}/api/ml/ab/experiments/${id}/variants`,
          { timeout: 10000 }
        );

        res.json(mlResponse.data);

      } catch (error: any) {
        console.error('Error fetching variant data:', error);
        res.status(error.response?.status || 500).json({
          error: 'Failed to fetch variant data',
          message: error.message,
          details: error.response?.data
        });
      }
    }
  );

  return router;
}

export default createABTestsRouter;
