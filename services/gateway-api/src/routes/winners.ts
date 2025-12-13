/**
 * Winner Detection Routes
 * Agent 01 - Automatic winner detection and replication
 *
 * Provides automatic detection of winning ads based on performance thresholds:
 * - Detect winners when ROAS > 2x, CTR > 2%, spend > $100
 * - Index winners in FAISS for similarity search
 * - Replicate winning patterns with variations
 */

import { Router, Request, Response } from 'express';
import { Pool } from 'pg';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';
import { apiRateLimiter, uploadRateLimiter, validateInput } from '../middleware/security';

const router = Router();

// Service URLs
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8003';

interface WinnerCriteria {
  minROAS: number;    // Default: 2.0
  minCTR: number;     // Default: 0.02 (2%)
  minSpend: number;   // Default: 100
  minHours: number;   // Default: 24
}

const DEFAULT_CRITERIA: WinnerCriteria = {
  minROAS: 2.0,
  minCTR: 0.02,
  minSpend: 100,
  minHours: 24
};

/**
 * Create winners router with database connection
 */
export function createWinnersRouter(pgPool: Pool): Router {
  /**
   * POST /api/v1/winners/detect
   * Manually trigger winner detection
   */
  router.post(
    '/detect',
    uploadRateLimiter,
    validateInput({
      body: {
        minROAS: { type: 'number', required: false, min: 0 },
        minCTR: { type: 'number', required: false, min: 0, max: 1 },
        minSpend: { type: 'number', required: false, min: 0 },
        minHours: { type: 'number', required: false, min: 0 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const criteria: WinnerCriteria = { ...DEFAULT_CRITERIA, ...req.body };

        console.log('[Winner Detection] Running with criteria:', criteria);

        // Calculate the time threshold (default 24 hours ago)
        const hoursAgo = new Date();
        hoursAgo.setHours(hoursAgo.getHours() - criteria.minHours);

        // Query ads with performance metrics that meet winner criteria
        const query = `
          SELECT
            a.ad_id,
            a.campaign_id,
            a.video_id,
            a.asset_id,
            a.arc_name,
            a.clip_ids,
            a.title,
            a.description,
            a.predicted_ctr,
            a.predicted_roas,
            a.thumbnail_url,
            a.video_url,
            a.created_at,
            c.name as campaign_name,
            v.title as video_title,
            COALESCE(SUM(pm.impressions), 0) as total_impressions,
            COALESCE(SUM(pm.clicks), 0) as total_clicks,
            COALESCE(SUM(pm.conversions), 0) as total_conversions,
            COALESCE(SUM(pm.spend), 0) as total_spend,
            CASE
              WHEN SUM(pm.impressions) > 0
              THEN (SUM(pm.clicks)::FLOAT / SUM(pm.impressions))
              ELSE 0
            END as actual_ctr,
            CASE
              WHEN SUM(pm.spend) > 0
              THEN ((SUM(pm.conversions) * 50.0) / SUM(pm.spend))
              ELSE 0
            END as actual_roas
          FROM ads a
          LEFT JOIN campaigns c ON a.campaign_id = c.id
          LEFT JOIN videos v ON a.video_id::text = v.id::text OR a.asset_id::text = v.id::text
          LEFT JOIN performance_metrics pm ON v.id = pm.video_id
          WHERE a.created_at <= $1
            AND a.approved = true
            AND a.status IN ('approved', 'published')
          GROUP BY a.ad_id, c.id, v.id
          HAVING
            SUM(pm.spend) >= $2
            AND (SUM(pm.clicks)::FLOAT / NULLIF(SUM(pm.impressions), 0)) >= $3
            AND ((SUM(pm.conversions) * 50.0) / NULLIF(SUM(pm.spend), 0)) >= $4
          ORDER BY actual_roas DESC, actual_ctr DESC
        `;

        const values = [
          hoursAgo,
          criteria.minSpend,
          criteria.minCTR,
          criteria.minROAS
        ];

        const result = await pgPool.query(query, values);
        const winners = result.rows;

        console.log(`[Winner Detection] Found ${winners.length} winners`);

        // Index winners in ML service FAISS index
        const indexedWinners = [];
        for (const winner of winners) {
          try {
            // Call ML service to add winner to FAISS index
            const mlResponse = await axios.post(
              `${ML_SERVICE_URL}/api/ml/winners/index`,
              {
                ad_id: winner.ad_id,
                metadata: {
                  campaign_id: winner.campaign_id,
                  campaign_name: winner.campaign_name,
                  video_title: winner.video_title,
                  arc_name: winner.arc_name,
                  clip_ids: winner.clip_ids,
                  actual_ctr: parseFloat(winner.actual_ctr),
                  actual_roas: parseFloat(winner.actual_roas),
                  total_spend: parseFloat(winner.total_spend),
                  total_impressions: parseInt(winner.total_impressions),
                  total_clicks: parseInt(winner.total_clicks),
                  total_conversions: parseInt(winner.total_conversions),
                  thumbnail_url: winner.thumbnail_url,
                  video_url: winner.video_url,
                  detected_at: new Date().toISOString()
                }
              },
              { timeout: 10000 }
            );

            indexedWinners.push({
              ad_id: winner.ad_id,
              indexed: mlResponse.data.success || true,
              similarity_index_id: mlResponse.data.index_id
            });

            console.log(`[Winner Detection] Indexed winner ${winner.ad_id} in FAISS`);
          } catch (mlError: any) {
            console.error(`[Winner Detection] Failed to index winner ${winner.ad_id}:`, mlError.message);
            indexedWinners.push({
              ad_id: winner.ad_id,
              indexed: false,
              error: mlError.message
            });
          }
        }

        res.json({
          status: 'success',
          message: `Detected ${winners.length} winning ads`,
          criteria,
          winners: winners.map(w => ({
            ad_id: w.ad_id,
            campaign_name: w.campaign_name,
            video_title: w.video_title,
            arc_name: w.arc_name,
            performance: {
              ctr: parseFloat(w.actual_ctr),
              roas: parseFloat(w.actual_roas),
              spend: parseFloat(w.total_spend),
              impressions: parseInt(w.total_impressions),
              clicks: parseInt(w.total_clicks),
              conversions: parseInt(w.total_conversions)
            },
            created_at: w.created_at
          })),
          indexed: indexedWinners,
          summary: {
            total_detected: winners.length,
            total_indexed: indexedWinners.filter(w => w.indexed).length,
            total_failed: indexedWinners.filter(w => !w.indexed).length
          }
        });

      } catch (error: any) {
        console.error('[Winner Detection] Error:', error);
        res.status(500).json({
          error: 'Failed to detect winners',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/v1/winners/list
   * List all detected winners
   */
  router.get(
    '/list',
    apiRateLimiter,
    validateInput({
      query: {
        limit: { type: 'number', required: false, min: 1, max: 100 },
        offset: { type: 'number', required: false, min: 0 },
        minROAS: { type: 'number', required: false, min: 0 },
        minCTR: { type: 'number', required: false, min: 0 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { limit = 20, offset = 0, minROAS, minCTR } = req.query;

        console.log('[Winner List] Fetching winners');

        // Query all ads that meet winner criteria
        let query = `
          SELECT
            a.ad_id,
            a.campaign_id,
            a.video_id,
            a.arc_name,
            a.title,
            a.description,
            a.thumbnail_url,
            a.video_url,
            a.created_at,
            c.name as campaign_name,
            v.title as video_title,
            COALESCE(SUM(pm.impressions), 0) as total_impressions,
            COALESCE(SUM(pm.clicks), 0) as total_clicks,
            COALESCE(SUM(pm.conversions), 0) as total_conversions,
            COALESCE(SUM(pm.spend), 0) as total_spend,
            CASE
              WHEN SUM(pm.impressions) > 0
              THEN (SUM(pm.clicks)::FLOAT / SUM(pm.impressions))
              ELSE 0
            END as actual_ctr,
            CASE
              WHEN SUM(pm.spend) > 0
              THEN ((SUM(pm.conversions) * 50.0) / SUM(pm.spend))
              ELSE 0
            END as actual_roas
          FROM ads a
          LEFT JOIN campaigns c ON a.campaign_id = c.id
          LEFT JOIN videos v ON a.video_id::text = v.id::text OR a.asset_id::text = v.id::text
          LEFT JOIN performance_metrics pm ON v.id = pm.video_id
          WHERE a.approved = true
            AND a.status IN ('approved', 'published')
          GROUP BY a.ad_id, c.id, v.id
          HAVING
            SUM(pm.spend) >= $1
        `;

        const values: any[] = [DEFAULT_CRITERIA.minSpend];
        let paramIndex = 2;

        if (minROAS) {
          query += ` AND ((SUM(pm.conversions) * 50.0) / NULLIF(SUM(pm.spend), 0)) >= $${paramIndex}`;
          values.push(parseFloat(minROAS as string));
          paramIndex++;
        } else {
          query += ` AND ((SUM(pm.conversions) * 50.0) / NULLIF(SUM(pm.spend), 0)) >= $${paramIndex}`;
          values.push(DEFAULT_CRITERIA.minROAS);
          paramIndex++;
        }

        if (minCTR) {
          query += ` AND (SUM(pm.clicks)::FLOAT / NULLIF(SUM(pm.impressions), 0)) >= $${paramIndex}`;
          values.push(parseFloat(minCTR as string));
          paramIndex++;
        } else {
          query += ` AND (SUM(pm.clicks)::FLOAT / NULLIF(SUM(pm.impressions), 0)) >= $${paramIndex}`;
          values.push(DEFAULT_CRITERIA.minCTR);
          paramIndex++;
        }

        query += `
          ORDER BY actual_roas DESC, actual_ctr DESC
          LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
        `;

        values.push(parseInt(limit as string), parseInt(offset as string));

        const result = await pgPool.query(query, values);
        const winners = result.rows;

        console.log(`[Winner List] Found ${winners.length} winners`);

        res.json({
          status: 'success',
          winners: winners.map(w => ({
            ad_id: w.ad_id,
            campaign_name: w.campaign_name,
            video_title: w.video_title,
            arc_name: w.arc_name,
            title: w.title,
            description: w.description,
            thumbnail_url: w.thumbnail_url,
            video_url: w.video_url,
            performance: {
              ctr: parseFloat(w.actual_ctr),
              roas: parseFloat(w.actual_roas),
              spend: parseFloat(w.total_spend),
              impressions: parseInt(w.total_impressions),
              clicks: parseInt(w.total_clicks),
              conversions: parseInt(w.total_conversions)
            },
            created_at: w.created_at
          })),
          pagination: {
            total: winners.length,
            limit: parseInt(limit as string),
            offset: parseInt(offset as string),
            has_more: winners.length === parseInt(limit as string)
          }
        });

      } catch (error: any) {
        console.error('[Winner List] Error:', error);
        res.status(500).json({
          error: 'Failed to fetch winners',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/v1/winners/:id
   * Get detailed information about a specific winner
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

        console.log(`[Winner Details] Fetching winner: ${id}`);

        const query = `
          SELECT
            a.*,
            c.name as campaign_name,
            c.budget_daily as campaign_budget,
            c.target_audience as campaign_audience,
            v.title as video_title,
            v.description as video_description,
            v.video_url,
            v.thumbnail_url,
            v.duration_seconds,
            COALESCE(SUM(pm.impressions), 0) as total_impressions,
            COALESCE(SUM(pm.clicks), 0) as total_clicks,
            COALESCE(SUM(pm.conversions), 0) as total_conversions,
            COALESCE(SUM(pm.spend), 0) as total_spend,
            CASE
              WHEN SUM(pm.impressions) > 0
              THEN (SUM(pm.clicks)::FLOAT / SUM(pm.impressions))
              ELSE 0
            END as actual_ctr,
            CASE
              WHEN SUM(pm.spend) > 0
              THEN ((SUM(pm.conversions) * 50.0) / SUM(pm.spend))
              ELSE 0
            END as actual_roas
          FROM ads a
          LEFT JOIN campaigns c ON a.campaign_id = c.id
          LEFT JOIN videos v ON a.video_id::text = v.id::text OR a.asset_id::text = v.id::text
          LEFT JOIN performance_metrics pm ON v.id = pm.video_id
          WHERE a.ad_id = $1
          GROUP BY a.ad_id, c.id, v.id
        `;

        const result = await pgPool.query(query, [id]);

        if (result.rows.length === 0) {
          return res.status(404).json({
            error: 'Winner not found',
            message: `Ad with id ${id} does not exist`
          });
        }

        const winner = result.rows[0];

        // Get similar winners from ML service
        let similarWinners = [];
        try {
          const mlResponse = await axios.post(
            `${ML_SERVICE_URL}/api/ml/winners/similar`,
            {
              ad_id: id,
              k: 5
            },
            { timeout: 10000 }
          );

          similarWinners = mlResponse.data.similar_winners || [];
          console.log(`[Winner Details] Found ${similarWinners.length} similar winners`);
        } catch (mlError: any) {
          console.warn('[Winner Details] Failed to fetch similar winners:', mlError.message);
        }

        res.json({
          status: 'success',
          winner: {
            ad_id: winner.ad_id,
            campaign: {
              id: winner.campaign_id,
              name: winner.campaign_name,
              budget_daily: parseFloat(winner.campaign_budget) || 0,
              target_audience: winner.campaign_audience
            },
            video: {
              id: winner.video_id,
              title: winner.video_title,
              description: winner.video_description,
              url: winner.video_url,
              thumbnail: winner.thumbnail_url,
              duration_seconds: parseFloat(winner.duration_seconds) || 0
            },
            arc_name: winner.arc_name,
            clip_ids: winner.clip_ids,
            title: winner.title,
            description: winner.description,
            predictions: {
              ctr: parseFloat(winner.predicted_ctr) || 0,
              roas: parseFloat(winner.predicted_roas) || 0
            },
            performance: {
              ctr: parseFloat(winner.actual_ctr),
              roas: parseFloat(winner.actual_roas),
              spend: parseFloat(winner.total_spend),
              impressions: parseInt(winner.total_impressions),
              clicks: parseInt(winner.total_clicks),
              conversions: parseInt(winner.total_conversions),
              prediction_accuracy: {
                ctr_delta: parseFloat(winner.actual_ctr) - (parseFloat(winner.predicted_ctr) || 0),
                roas_delta: parseFloat(winner.actual_roas) - (parseFloat(winner.predicted_roas) || 0)
              }
            },
            status: winner.status,
            approved: winner.approved,
            created_at: winner.created_at,
            similar_winners: similarWinners
          }
        });

      } catch (error: any) {
        console.error('[Winner Details] Error:', error);
        res.status(500).json({
          error: 'Failed to fetch winner details',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/v1/winners/:id/replicate
   * Create a copy of a winning ad with variations
   */
  router.post(
    '/:id/replicate',
    uploadRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      },
      body: {
        variations: { type: 'number', required: false, min: 1, max: 10 },
        campaign_id: { type: 'uuid', required: false },
        modify_arc: { type: 'boolean', required: false },
        modify_clips: { type: 'boolean', required: false }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;
        const { variations = 3, campaign_id, modify_arc = false, modify_clips = false } = req.body;

        console.log(`[Winner Replication] Replicating winner ${id} with ${variations} variations`);

        // Get the original winner
        const query = `
          SELECT * FROM ads WHERE ad_id = $1
        `;

        const result = await pgPool.query(query, [id]);

        if (result.rows.length === 0) {
          return res.status(404).json({
            error: 'Winner not found',
            message: `Ad with id ${id} does not exist`
          });
        }

        const originalAd = result.rows[0];

        // Create variations
        const replicatedAds = [];
        for (let i = 0; i < variations; i++) {
          const newAdId = uuidv4();

          // Build variation title
          let variantTitle = originalAd.title || 'Winner Variant';
          if (originalAd.title) {
            variantTitle = `${originalAd.title} - Variant ${i + 1}`;
          }

          // Insert replicated ad
          const insertQuery = `
            INSERT INTO ads (
              ad_id, campaign_id, video_id, asset_id, clip_ids, arc_name,
              title, description, status, approved, platform, format,
              thumbnail_url, video_url, cta_text, cta_url, targeting,
              budget, predicted_ctr, predicted_roas, notes, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, NOW())
            RETURNING *
          `;

          const insertValues = [
            newAdId,
            campaign_id || originalAd.campaign_id,
            originalAd.video_id,
            originalAd.asset_id,
            originalAd.clip_ids,
            modify_arc ? `${originalAd.arc_name}-variant-${i + 1}` : originalAd.arc_name,
            variantTitle,
            originalAd.description,
            'pending_approval', // Start as pending for review
            false, // Not approved by default
            originalAd.platform,
            originalAd.format,
            originalAd.thumbnail_url,
            originalAd.video_url,
            originalAd.cta_text,
            originalAd.cta_url,
            originalAd.targeting,
            originalAd.budget,
            originalAd.predicted_ctr,
            originalAd.predicted_roas,
            `Replicated from winner ${id} - Variation ${i + 1}`
          ];

          const insertResult = await pgPool.query(insertQuery, insertValues);
          const newAd = insertResult.rows[0];

          replicatedAds.push({
            ad_id: newAd.ad_id,
            title: newAd.title,
            arc_name: newAd.arc_name,
            status: newAd.status,
            created_at: newAd.created_at
          });

          console.log(`[Winner Replication] Created variant ${i + 1}: ${newAdId}`);
        }

        res.json({
          status: 'success',
          message: `Successfully replicated winner with ${variations} variations`,
          original_ad_id: id,
          replicated_ads: replicatedAds,
          summary: {
            total_created: replicatedAds.length,
            campaign_id: campaign_id || originalAd.campaign_id,
            variations_config: {
              modify_arc,
              modify_clips
            }
          }
        });

      } catch (error: any) {
        console.error('[Winner Replication] Error:', error);
        res.status(500).json({
          error: 'Failed to replicate winner',
          message: error.message
        });
      }
    }
  );

  return router;
}

export default createWinnersRouter;
