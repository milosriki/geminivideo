/**
 * Winner Replication Routes
 * Winner detection, analysis, and replication endpoints
 *
 * Provides winner management:
 * - List winning ads based on performance criteria
 * - Get winner insights and creative DNA
 * - Replicate winning elements to new campaigns
 * - Track winner performance over time
 * - Manage RAG indexing queue for winners
 */

import { Router, Request, Response } from 'express';
import { Pool } from 'pg';
import axios from 'axios';
import { apiRateLimiter, validateInput } from '../middleware/security';

const router = Router();

// Service URLs
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8003';
const RAG_SERVICE_URL = process.env.RAG_SERVICE_URL || 'http://localhost:8005';

/**
 * Create winners router with database connection
 */
export function createWinnersRouter(pgPool: Pool): Router {
  /**
   * GET /api/winners
   * List winning ads based on performance criteria
   */
  router.get(
    '/',
    apiRateLimiter,
    validateInput({
      query: {
        days_back: { type: 'number', required: false, min: 1, max: 365 },
        min_ctr: { type: 'number', required: false, min: 0, max: 1 },
        min_roas: { type: 'number', required: false, min: 0 },
        min_impressions: { type: 'number', required: false, min: 0 },
        platform: { type: 'string', required: false, max: 50 },
        limit: { type: 'number', required: false, min: 1, max: 100 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const {
          days_back = 30,
          min_ctr = 0.03,
          min_roas = 3.0,
          min_impressions = 1000,
          platform,
          limit = 50
        } = req.query;

        console.log(`Fetching winners: days_back=${days_back}, min_ctr=${min_ctr}, min_roas=${min_roas}`);

        // Query winning ads from performance_metrics
        let query = `
          SELECT 
            pm.id,
            pm.video_id,
            v.video_url,
            v.thumbnail_url,
            a.ad_id,
            a.campaign_id,
            a.arc_name,
            a.title,
            pm.platform,
            pm.ctr,
            (pm.raw_data->>'roas')::FLOAT as roas,
            pm.impressions,
            pm.clicks,
            pm.conversions,
            pm.spend,
            pm.date,
            pm.created_at,
            CASE
              WHEN pm.ctr > $1 AND (pm.raw_data->>'roas')::FLOAT > $2 THEN 'both'
              WHEN pm.ctr > $1 THEN 'ctr'
              ELSE 'roas'
            END as winner_type
          FROM performance_metrics pm
          LEFT JOIN videos v ON v.id = pm.video_id
          LEFT JOIN ads a ON a.video_id = pm.video_id
          WHERE pm.impressions >= $3
          AND pm.created_at >= NOW() - ($4 || ' days')::INTERVAL
          AND (pm.ctr > $1 OR (pm.raw_data->>'roas')::FLOAT > $2)
        `;

        const params: any[] = [min_ctr, min_roas, min_impressions, days_back];
        let paramIndex = params.length + 1;

        if (platform) {
          query += ` AND pm.platform = $${paramIndex}`;
          params.push(platform);
          paramIndex++;
        }

        query += ` ORDER BY 
          CASE
            WHEN pm.ctr > $1 AND (pm.raw_data->>'roas')::FLOAT > $2 THEN 1
            WHEN (pm.raw_data->>'roas')::FLOAT > $2 THEN 2
            ELSE 3
          END,
          pm.ctr DESC,
          (pm.raw_data->>'roas')::FLOAT DESC
          LIMIT $${paramIndex}
        `;
        params.push(limit);

        const result = await pgPool.query(query, params);

        res.json({
          status: 'success',
          winners: result.rows,
          count: result.rows.length,
          criteria: {
            min_ctr,
            min_roas,
            min_impressions,
            days_back,
            platform: platform || 'all'
          }
        });
      } catch (error: any) {
        console.error('Error fetching winners:', error);
        res.status(500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/winners/stats
   * Get winner statistics
   */
  router.get(
    '/stats',
    apiRateLimiter,
    validateInput({
      query: {
        days_back: { type: 'number', required: false, min: 1, max: 365 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { days_back = 30 } = req.query;

        console.log(`Fetching winner stats for ${days_back} days`);

        // Call database function for stats
        const result = await pgPool.query(
          'SELECT * FROM get_winner_stats($1)',
          [days_back]
        );

        const stats = result.rows[0] || {
          total_winners: 0,
          ctr_winners: 0,
          roas_winners: 0,
          both_winners: 0,
          avg_winner_ctr: 0,
          avg_winner_roas: 0,
          pending_index_jobs: 0,
          indexed_winners: 0
        };

        res.json({
          status: 'success',
          stats: {
            total_winners: parseInt(stats.total_winners) || 0,
            ctr_winners: parseInt(stats.ctr_winners) || 0,
            roas_winners: parseInt(stats.roas_winners) || 0,
            both_winners: parseInt(stats.both_winners) || 0,
            avg_winner_ctr: parseFloat(stats.avg_winner_ctr) || 0,
            avg_winner_roas: parseFloat(stats.avg_winner_roas) || 0,
            pending_index_jobs: parseInt(stats.pending_index_jobs) || 0,
            indexed_winners: parseInt(stats.indexed_winners) || 0
          },
          period_days: days_back
        });
      } catch (error: any) {
        console.error('Error fetching winner stats:', error);
        res.status(500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/winners/:video_id/insights
   * Get detailed insights for a winning ad
   */
  router.get(
    '/:video_id/insights',
    apiRateLimiter,
    validateInput({
      params: {
        video_id: { type: 'uuid', required: true }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { video_id } = req.params;

        console.log(`Fetching insights for winner: ${video_id}`);

        // Get winner insights from database
        const insightQuery = `
          SELECT *
          FROM winner_insights
          WHERE video_id = $1
          ORDER BY created_at DESC
          LIMIT 1
        `;

        const insightResult = await pgPool.query(insightQuery, [video_id]);

        if (insightResult.rows.length === 0) {
          // No insights yet, fetch from ML service to generate
          try {
            const mlResponse = await axios.get(
              `${ML_SERVICE_URL}/api/ml/creative-dna/analyze/${video_id}`,
              { timeout: 15000 }
            );

            res.json({
              status: 'success',
              insights: mlResponse.data,
              source: 'ml_service',
              cached: false
            });
            return;
          } catch (mlError: any) {
            console.warn('ML service unavailable, returning empty insights:', mlError.message);
            res.json({
              status: 'success',
              insights: {
                video_id,
                message: 'Insights generation in progress'
              },
              source: 'pending',
              cached: false
            });
            return;
          }
        }

        const insight = insightResult.rows[0];

        res.json({
          status: 'success',
          insights: {
            video_id: insight.video_id,
            ad_id: insight.ad_id,
            winner_type: insight.winner_type,
            metrics: insight.metrics,
            creative_elements: insight.creative_elements,
            hook_analysis: insight.hook_analysis,
            script_patterns: insight.script_patterns,
            audience_insights: insight.audience_insights,
            indexed_at: insight.indexed_at,
            rag_indexed: insight.rag_indexed
          },
          source: 'database',
          cached: true
        });
      } catch (error: any) {
        console.error('Error fetching winner insights:', error);
        res.status(500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/winners/:video_id/replicate
   * Replicate a winning ad's elements to a new campaign
   */
  router.post(
    '/:video_id/replicate',
    apiRateLimiter,
    validateInput({
      params: {
        video_id: { type: 'uuid', required: true }
      },
      body: {
        campaign_id: { type: 'uuid', required: true },
        elements: { type: 'array', required: false }, // ['hook', 'script', 'arc', 'targeting']
        variations: { type: 'number', required: false, min: 1, max: 10 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { video_id } = req.params;
        const { campaign_id, elements = ['hook', 'script', 'arc'], variations = 3 } = req.body;

        console.log(`Replicating winner ${video_id} to campaign ${campaign_id}`);

        // Get winner insights
        const insightQuery = `
          SELECT *
          FROM winner_insights
          WHERE video_id = $1
          ORDER BY created_at DESC
          LIMIT 1
        `;

        const insightResult = await pgPool.query(insightQuery, [video_id]);

        if (insightResult.rows.length === 0) {
          res.status(404).json({
            status: 'error',
            message: 'Winner insights not found. Ensure the video has been analyzed.'
          });
          return;
        }

        const insight = insightResult.rows[0];

        // Call ML service to generate variations based on winner elements
        try {
          const replicationResponse = await axios.post(
            `${ML_SERVICE_URL}/api/ml/winner/replicate`,
            {
              video_id,
              campaign_id,
              winner_insights: {
                creative_elements: insight.creative_elements,
                hook_analysis: insight.hook_analysis,
                script_patterns: insight.script_patterns,
                metrics: insight.metrics
              },
              elements_to_replicate: elements,
              num_variations: variations
            },
            { timeout: 30000 }
          );

          res.json({
            status: 'success',
            replication: replicationResponse.data,
            message: `Generated ${variations} variations based on winner elements`
          });
        } catch (mlError: any) {
          console.error('ML service replication failed:', mlError.message);
          res.status(503).json({
            status: 'error',
            message: 'Replication service temporarily unavailable',
            details: mlError.message
          });
        }
      } catch (error: any) {
        console.error('Error replicating winner:', error);
        res.status(500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/winners/queue
   * Get RAG indexing queue status
   */
  router.get(
    '/queue',
    apiRateLimiter,
    async (req: Request, res: Response) => {
      try {
        console.log('Fetching winner indexing queue status');

        const queueQuery = `
          SELECT 
            job_id,
            job_type,
            payload,
            status,
            created_at,
            started_at,
            completed_at,
            error_message,
            retry_count
          FROM pending_jobs
          WHERE job_type = 'rag_index_winner'
          ORDER BY created_at DESC
          LIMIT 100
        `;

        const result = await pgPool.query(queueQuery);

        const summary = {
          pending: 0,
          processing: 0,
          completed: 0,
          failed: 0
        };

        result.rows.forEach(job => {
          summary[job.status as keyof typeof summary]++;
        });

        res.json({
          status: 'success',
          queue: result.rows,
          summary,
          total: result.rows.length
        });
      } catch (error: any) {
        console.error('Error fetching queue:', error);
        res.status(500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/winners/queue/:job_id/retry
   * Retry a failed indexing job
   */
  router.post(
    '/queue/:job_id/retry',
    apiRateLimiter,
    validateInput({
      params: {
        job_id: { type: 'uuid', required: true }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { job_id } = req.params;

        console.log(`Retrying job: ${job_id}`);

        const updateQuery = `
          UPDATE pending_jobs
          SET status = 'pending',
              retry_count = retry_count + 1,
              error_message = NULL
          WHERE job_id = $1
          AND status = 'failed'
          AND retry_count < max_retries
          RETURNING *
        `;

        const result = await pgPool.query(updateQuery, [job_id]);

        if (result.rows.length === 0) {
          res.status(404).json({
            status: 'error',
            message: 'Job not found, not failed, or max retries exceeded'
          });
          return;
        }

        res.json({
          status: 'success',
          job: result.rows[0],
          message: 'Job queued for retry'
        });
      } catch (error: any) {
        console.error('Error retrying job:', error);
        res.status(500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/winners/cleanup
   * Clean up old completed/failed jobs
   */
  router.post(
    '/cleanup',
    apiRateLimiter,
    validateInput({
      body: {
        days_old: { type: 'number', required: false, min: 1, max: 365 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { days_old = 7 } = req.body;

        console.log(`Cleaning up jobs older than ${days_old} days`);

        const result = await pgPool.query(
          'SELECT cleanup_old_jobs($1) as deleted_count',
          [days_old]
        );

        const deletedCount = result.rows[0]?.deleted_count || 0;

        res.json({
          status: 'success',
          deleted_count: deletedCount,
          message: `Removed ${deletedCount} old jobs`
        });
      } catch (error: any) {
        console.error('Error cleaning up jobs:', error);
        res.status(500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  return router;
}

export default createWinnersRouter;
