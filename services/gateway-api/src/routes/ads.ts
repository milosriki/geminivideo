/**
 * Ads Management Routes
 * Agent 58 - Full CRUD for ad management
 *
 * Provides complete ad lifecycle management:
 * - Create/Read/Update/Delete ads
 * - Approve/reject ads for publishing
 * - Track ad performance
 * - Link ads to campaigns and videos
 */

import { Router, Request, Response } from 'express';
import { Pool } from 'pg';
import { v4 as uuidv4 } from 'uuid';
import { httpClient } from "../index";
import { apiRateLimiter, uploadRateLimiter, validateInput } from '../middleware/security';

const router = Router();

// Service URLs
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8003';
const TITAN_CORE_URL = process.env.TITAN_CORE_URL || 'http://localhost:8004';

/**
 * Create ads router with database connection
 */
export function createAdsRouter(pgPool: Pool): Router {
  /**
   * POST /api/ads
   * Create a new ad
   */
  router.post(
    '/',
    uploadRateLimiter,
    validateInput({
      body: {
        campaign_id: { type: 'uuid', required: false },
        video_id: { type: 'uuid', required: false },
        asset_id: { type: 'uuid', required: false },
        arc_name: { type: 'string', required: false, max: 100, sanitize: true },
        clip_ids: { type: 'array', required: false },
        caption: { type: 'string', required: false, max: 2200, sanitize: true },
        predicted_ctr: { type: 'number', required: false, min: 0, max: 1 },
        predicted_roas: { type: 'number', required: false, min: 0 },
        status: { type: 'string', required: false, enum: ['pending_approval', 'approved', 'rejected', 'published'] }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const {
          campaign_id,
          video_id,
          asset_id,
          arc_name,
          clip_ids,
          caption,
          predicted_ctr,
          predicted_roas,
          status = 'pending_approval'
        } = req.body;

        console.log(`Creating ad: campaign=${campaign_id}, video=${video_id}`);

        // Generate ad ID
        const adId = uuidv4();

        // If predictions not provided, get them from ML service
        let finalPredictedCtr = predicted_ctr;
        let finalPredictedRoas = predicted_roas;

        if (!predicted_ctr || !predicted_roas) {
          try {
            const mlResponse = await axios.post(
              `${ML_SERVICE_URL}/api/ml/predict-ctr`,
              {
                clip_data: {
                  clip_ids: clip_ids || [],
                  arc_name: arc_name || 'default'
                },
                include_confidence: true
              },
              { timeout: 10000 }
            );

            finalPredictedCtr = mlResponse.data.predicted_ctr || 0.02;
            finalPredictedRoas = mlResponse.data.predicted_roas || 2.0;
          } catch (mlError: any) {
            console.warn('ML prediction failed, using defaults:', mlError.message);
            finalPredictedCtr = predicted_ctr || 0.02;
            finalPredictedRoas = predicted_roas || 2.0;
          }
        }

        // Insert ad into database
        const query = `
          INSERT INTO ads (
            ad_id, asset_id, clip_ids, arc_name, predicted_ctr, predicted_roas,
            status, approved, created_at, notes
          )
          VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), $9)
          RETURNING *
        `;

        const values = [
          adId,
          asset_id || video_id, // Use video_id if asset_id not provided
          JSON.stringify(clip_ids || []),
          arc_name || 'default',
          finalPredictedCtr,
          finalPredictedRoas,
          status,
          status === 'approved',
          caption || ''
        ];

        const result = await pgPool.query(query, values);
        const ad = result.rows[0];

        console.log(`Ad created successfully: ${adId}`);

        res.status(201).json({
          status: 'success',
          message: 'Ad created successfully',
          ad: {
            ad_id: ad.ad_id,
            asset_id: ad.asset_id,
            clip_ids: ad.clip_ids,
            arc_name: ad.arc_name,
            predicted_ctr: parseFloat(ad.predicted_ctr),
            predicted_roas: parseFloat(ad.predicted_roas),
            status: ad.status,
            approved: ad.approved,
            created_at: ad.created_at,
            caption: ad.notes
          }
        });

      } catch (error: any) {
        console.error('Error creating ad:', error);
        res.status(500).json({
          error: 'Failed to create ad',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/ads
   * List all ads with optional filters
   */
  router.get(
    '/',
    apiRateLimiter,
    validateInput({
      query: {
        campaign_id: { type: 'uuid', required: false },
        status: { type: 'string', required: false, enum: ['pending_approval', 'approved', 'rejected', 'published'] },
        approved: { type: 'boolean', required: false },
        limit: { type: 'number', required: false, min: 1, max: 100 },
        offset: { type: 'number', required: false, min: 0 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { campaign_id, status, approved, limit = 20, offset = 0 } = req.query;

        console.log(`Fetching ads: status=${status || 'all'}, approved=${approved}`);

        let query = `
          SELECT
            a.*,
            v.title as video_title,
            v.video_url,
            v.thumbnail_url,
            c.name as campaign_name,
            COALESCE(SUM(pm.impressions), 0) as total_impressions,
            COALESCE(SUM(pm.clicks), 0) as total_clicks,
            COALESCE(SUM(pm.conversions), 0) as total_conversions,
            COALESCE(SUM(pm.spend), 0) as total_spend
          FROM ads a
          LEFT JOIN videos v ON a.asset_id::text = v.id::text
          LEFT JOIN campaigns c ON v.campaign_id = c.id
          LEFT JOIN performance_metrics pm ON v.id = pm.video_id
          WHERE 1=1
        `;

        const values: any[] = [];
        let paramIndex = 1;

        if (campaign_id) {
          query += ` AND c.id = $${paramIndex}`;
          values.push(campaign_id);
          paramIndex++;
        }

        if (status) {
          query += ` AND a.status = $${paramIndex}`;
          values.push(status);
          paramIndex++;
        }

        if (approved !== undefined) {
          query += ` AND a.approved = $${paramIndex}`;
          values.push(approved === 'true');
          paramIndex++;
        }

        query += `
          GROUP BY a.ad_id, a.asset_id, a.clip_ids, a.arc_name, a.predicted_ctr,
                   a.predicted_roas, a.status, a.approved, a.created_at, a.approved_at,
                   a.approved_by, a.published_at, a.notes,
                   v.title, v.video_url, v.thumbnail_url, c.name
          ORDER BY a.created_at DESC
          LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
        `;

        values.push(parseInt(limit as string), parseInt(offset as string));

        const result = await pgPool.query(query, values);

        // Get total count
        let countQuery = 'SELECT COUNT(*) FROM ads a';
        const countConditions: string[] = [];
        const countValues: any[] = [];
        let countIndex = 1;

        if (campaign_id) {
          countQuery += ' LEFT JOIN videos v ON a.asset_id::text = v.id::text LEFT JOIN campaigns c ON v.campaign_id = c.id';
          countConditions.push(`c.id = $${countIndex}`);
          countValues.push(campaign_id);
          countIndex++;
        }

        if (status) {
          countConditions.push(`a.status = $${countIndex}`);
          countValues.push(status);
          countIndex++;
        }

        if (approved !== undefined) {
          countConditions.push(`a.approved = $${countIndex}`);
          countValues.push(approved === 'true');
        }

        if (countConditions.length > 0) {
          countQuery += ' WHERE ' + countConditions.join(' AND ');
        }

        const countResult = await pgPool.query(countQuery, countValues);
        const totalCount = parseInt(countResult.rows[0].count);

        const ads = result.rows.map(row => ({
          ad_id: row.ad_id,
          campaign_name: row.campaign_name,
          video_title: row.video_title,
          video_url: row.video_url,
          thumbnail_url: row.thumbnail_url,
          arc_name: row.arc_name,
          predicted_ctr: parseFloat(row.predicted_ctr),
          predicted_roas: parseFloat(row.predicted_roas),
          status: row.status,
          approved: row.approved,
          created_at: row.created_at,
          approved_at: row.approved_at,
          approved_by: row.approved_by,
          published_at: row.published_at,
          performance: {
            impressions: parseInt(row.total_impressions),
            clicks: parseInt(row.total_clicks),
            conversions: parseInt(row.total_conversions),
            spend: parseFloat(row.total_spend),
            actual_ctr: parseInt(row.total_impressions) > 0
              ? (parseInt(row.total_clicks) / parseInt(row.total_impressions)) * 100
              : 0
          }
        }));

        console.log(`Found ${ads.length} ads (total: ${totalCount})`);

        res.json({
          status: 'success',
          ads,
          pagination: {
            total: totalCount,
            limit: parseInt(limit as string),
            offset: parseInt(offset as string),
            has_more: parseInt(offset as string) + ads.length < totalCount
          }
        });

      } catch (error: any) {
        console.error('Error fetching ads:', error);
        res.status(500).json({
          error: 'Failed to fetch ads',
          message: error.message,
          ads: []
        });
      }
    }
  );

  /**
   * GET /api/ads/:id
   * Get detailed ad information
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

        console.log(`Fetching ad details: ${id}`);

        const query = `
          SELECT
            a.*,
            v.title as video_title,
            v.description as video_description,
            v.video_url,
            v.thumbnail_url,
            v.duration_seconds,
            c.id as campaign_id,
            c.name as campaign_name,
            c.status as campaign_status,
            COALESCE(SUM(pm.impressions), 0) as total_impressions,
            COALESCE(SUM(pm.clicks), 0) as total_clicks,
            COALESCE(SUM(pm.conversions), 0) as total_conversions,
            COALESCE(SUM(pm.spend), 0) as total_spend
          FROM ads a
          LEFT JOIN videos v ON a.asset_id::text = v.id::text
          LEFT JOIN campaigns c ON v.campaign_id = c.id
          LEFT JOIN performance_metrics pm ON v.id = pm.video_id
          WHERE a.ad_id = $1
          GROUP BY a.ad_id, v.id, c.id
        `;

        const result = await pgPool.query(query, [id]);

        if (result.rows.length === 0) {
          return res.status(404).json({
            error: 'Ad not found',
            message: `Ad with id ${id} does not exist`
          });
        }

        const ad = result.rows[0];

        res.json({
          status: 'success',
          ad: {
            ad_id: ad.ad_id,
            campaign: {
              id: ad.campaign_id,
              name: ad.campaign_name,
              status: ad.campaign_status
            },
            video: {
              title: ad.video_title,
              description: ad.video_description,
              url: ad.video_url,
              thumbnail: ad.thumbnail_url,
              duration_seconds: parseFloat(ad.duration_seconds)
            },
            clip_ids: ad.clip_ids,
            arc_name: ad.arc_name,
            predictions: {
              ctr: parseFloat(ad.predicted_ctr),
              roas: parseFloat(ad.predicted_roas)
            },
            status: ad.status,
            approved: ad.approved,
            approved_at: ad.approved_at,
            approved_by: ad.approved_by,
            published_at: ad.published_at,
            created_at: ad.created_at,
            caption: ad.notes,
            performance: {
              impressions: parseInt(ad.total_impressions),
              clicks: parseInt(ad.total_clicks),
              conversions: parseInt(ad.total_conversions),
              spend: parseFloat(ad.total_spend),
              actual_ctr: parseInt(ad.total_impressions) > 0
                ? (parseInt(ad.total_clicks) / parseInt(ad.total_impressions)) * 100
                : 0,
              actual_roas: parseFloat(ad.total_spend) > 0
                ? (parseInt(ad.total_conversions) * 50) / parseFloat(ad.total_spend) // Assume $50 AOV
                : 0
            }
          }
        });

      } catch (error: any) {
        console.error('Error fetching ad:', error);
        res.status(500).json({
          error: 'Failed to fetch ad',
          message: error.message
        });
      }
    }
  );

  /**
   * PUT /api/ads/:id
   * Update ad details
   */
  router.put(
    '/:id',
    apiRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      },
      body: {
        caption: { type: 'string', required: false, max: 2200, sanitize: true },
        status: { type: 'string', required: false, enum: ['pending_approval', 'approved', 'rejected', 'published'] },
        predicted_ctr: { type: 'number', required: false, min: 0, max: 1 },
        predicted_roas: { type: 'number', required: false, min: 0 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;
        const updates = req.body;

        console.log(`Updating ad: ${id}`);

        // Check if ad exists
        const checkQuery = 'SELECT * FROM ads WHERE ad_id = $1';
        const checkResult = await pgPool.query(checkQuery, [id]);

        if (checkResult.rows.length === 0) {
          return res.status(404).json({
            error: 'Ad not found',
            message: `Ad with id ${id} does not exist`
          });
        }

        // Build update query dynamically
        const updateFields: string[] = [];
        const values: any[] = [];
        let paramIndex = 1;

        if (updates.caption !== undefined) {
          updateFields.push(`notes = $${paramIndex}`);
          values.push(updates.caption);
          paramIndex++;
        }

        if (updates.status !== undefined) {
          updateFields.push(`status = $${paramIndex}`);
          values.push(updates.status);
          paramIndex++;

          // Update approved flag based on status
          if (updates.status === 'approved') {
            updateFields.push(`approved = true, approved_at = NOW()`);
          } else if (updates.status === 'rejected') {
            updateFields.push(`approved = false`);
          }
        }

        if (updates.predicted_ctr !== undefined) {
          updateFields.push(`predicted_ctr = $${paramIndex}`);
          values.push(updates.predicted_ctr);
          paramIndex++;
        }

        if (updates.predicted_roas !== undefined) {
          updateFields.push(`predicted_roas = $${paramIndex}`);
          values.push(updates.predicted_roas);
          paramIndex++;
        }

        if (updateFields.length === 0) {
          return res.status(400).json({
            error: 'No updates provided',
            message: 'At least one field must be provided for update'
          });
        }

        // Add ad ID as last parameter
        values.push(id);

        const updateQuery = `
          UPDATE ads
          SET ${updateFields.join(', ')}
          WHERE ad_id = $${paramIndex}
          RETURNING *
        `;

        const result = await pgPool.query(updateQuery, values);
        const ad = result.rows[0];

        console.log(`Ad updated successfully: ${id}`);

        res.json({
          status: 'success',
          message: 'Ad updated successfully',
          ad: {
            ad_id: ad.ad_id,
            status: ad.status,
            approved: ad.approved,
            predicted_ctr: parseFloat(ad.predicted_ctr),
            predicted_roas: parseFloat(ad.predicted_roas),
            caption: ad.notes
          }
        });

      } catch (error: any) {
        console.error('Error updating ad:', error);
        res.status(500).json({
          error: 'Failed to update ad',
          message: error.message
        });
      }
    }
  );

  /**
   * DELETE /api/ads/:id
   * Delete an ad
   */
  router.delete(
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

        console.log(`Deleting ad: ${id}`);

        // Check if ad exists and is not published
        const checkQuery = 'SELECT * FROM ads WHERE ad_id = $1';
        const checkResult = await pgPool.query(checkQuery, [id]);

        if (checkResult.rows.length === 0) {
          return res.status(404).json({
            error: 'Ad not found',
            message: `Ad with id ${id} does not exist`
          });
        }

        const ad = checkResult.rows[0];

        if (ad.status === 'published') {
          return res.status(400).json({
            error: 'Cannot delete published ad',
            message: 'Published ads cannot be deleted. Please unpublish first.'
          });
        }

        // Delete the ad
        const deleteQuery = 'DELETE FROM ads WHERE ad_id = $1 RETURNING *';
        await pgPool.query(deleteQuery, [id]);

        console.log(`Ad deleted successfully: ${id}`);

        res.json({
          status: 'success',
          message: 'Ad deleted successfully',
          ad_id: id
        });

      } catch (error: any) {
        console.error('Error deleting ad:', error);
        res.status(500).json({
          error: 'Failed to delete ad',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/ads/:id/approve
   * Approve an ad for publishing
   */
  router.post(
    '/:id/approve',
    apiRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      },
      body: {
        notes: { type: 'string', required: false, max: 1000, sanitize: true }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;
        const { notes } = req.body;

        console.log(`Approving ad: ${id}`);

        const userId = (req as any).user?.id || 'system';

        const updateQuery = `
          UPDATE ads
          SET
            approved = true,
            status = 'approved',
            approved_at = NOW(),
            approved_by = $1,
            notes = COALESCE($2, notes)
          WHERE ad_id = $3
          RETURNING *
        `;

        const result = await pgPool.query(updateQuery, [userId, notes, id]);

        if (result.rows.length === 0) {
          return res.status(404).json({
            error: 'Ad not found',
            message: `Ad with id ${id} does not exist`
          });
        }

        const ad = result.rows[0];

        // Log approval in audit trail
        const auditQuery = `
          INSERT INTO audit_log (event_type, ad_id, user_id, details, timestamp)
          VALUES ($1, $2, $3, $4, NOW())
        `;

        await pgPool.query(auditQuery, [
          'AD_APPROVED',
          id,
          userId,
          JSON.stringify({ notes })
        ]).catch(err => {
          console.warn('[AUDIT] Failed to log approval:', err.message);
        });

        console.log(`Ad approved successfully: ${id}`);

        res.json({
          status: 'success',
          message: 'Ad approved successfully',
          ad: {
            ad_id: ad.ad_id,
            status: ad.status,
            approved: ad.approved,
            approved_at: ad.approved_at,
            approved_by: ad.approved_by
          }
        });

      } catch (error: any) {
        console.error('Error approving ad:', error);
        res.status(500).json({
          error: 'Failed to approve ad',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/ads/:id/reject
   * Reject an ad
   */
  router.post(
    '/:id/reject',
    apiRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      },
      body: {
        reason: { type: 'string', required: true, min: 1, max: 1000, sanitize: true }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;
        const { reason } = req.body;

        console.log(`Rejecting ad: ${id}`);

        const updateQuery = `
          UPDATE ads
          SET
            approved = false,
            status = 'rejected',
            notes = $1
          WHERE ad_id = $2
          RETURNING *
        `;

        const result = await pgPool.query(updateQuery, [reason, id]);

        if (result.rows.length === 0) {
          return res.status(404).json({
            error: 'Ad not found',
            message: `Ad with id ${id} does not exist`
          });
        }

        console.log(`Ad rejected successfully: ${id}`);

        res.json({
          status: 'success',
          message: 'Ad rejected successfully',
          ad_id: id,
          reason
        });

      } catch (error: any) {
        console.error('Error rejecting ad:', error);
        res.status(500).json({
          error: 'Failed to reject ad',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/ads/trending
   * Get trending ads by category with real performance data
   */
  router.get(
    '/trending',
    apiRateLimiter,
    validateInput({
      query: {
        category: { type: 'string', required: false },
        limit: { type: 'number', required: false, min: 1, max: 50 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { category = 'fitness', limit = 8 } = req.query;

        console.log(`Fetching trending ads: category=${category}, limit=${limit}`);

        // Query for top performing ads ordered by engagement/CTR
        const query = `
          SELECT
            a.ad_id as id,
            COALESCE(c.name, 'Top Brand') as brand,
            COALESCE(v.title, a.arc_name, 'High Performance Ad') as title,
            CASE
              WHEN COALESCE(SUM(pm.impressions), 0) > 1000000 THEN ROUND(COALESCE(SUM(pm.impressions), 0)::numeric / 1000000, 1)::text || 'M'
              WHEN COALESCE(SUM(pm.impressions), 0) > 1000 THEN ROUND(COALESCE(SUM(pm.impressions), 0)::numeric / 1000, 1)::text || 'K'
              ELSE COALESCE(SUM(pm.impressions), 0)::text
            END as views,
            CASE
              WHEN COALESCE(SUM(pm.impressions), 0) > 0
              THEN ROUND((COALESCE(SUM(pm.clicks), 0)::numeric / SUM(pm.impressions) * 100), 1)::text || '%'
              ELSE '0%'
            END as engagement,
            COALESCE(
              CASE
                WHEN v.video_url LIKE '%tiktok%' THEN 'TikTok'
                WHEN v.video_url LIKE '%youtube%' THEN 'YouTube'
                WHEN v.video_url LIKE '%instagram%' THEN 'Instagram'
                WHEN v.video_url LIKE '%facebook%' THEN 'Facebook'
                ELSE 'Meta'
              END,
              'Meta'
            ) as platform,
            v.thumbnail_url as thumbnail,
            v.video_url as "videoUrl",
            a.created_at as "datePublished",
            $1 as category
          FROM ads a
          LEFT JOIN videos v ON a.asset_id::text = v.id::text
          LEFT JOIN campaigns c ON v.campaign_id = c.id
          LEFT JOIN performance_metrics pm ON v.id = pm.video_id
          WHERE a.status IN ('approved', 'published')
            AND a.approved = true
          GROUP BY a.ad_id, c.name, v.title, a.arc_name, v.thumbnail_url, v.video_url, a.created_at
          HAVING COALESCE(SUM(pm.impressions), 0) > 0
          ORDER BY
            CASE
              WHEN COALESCE(SUM(pm.impressions), 0) > 0
              THEN COALESCE(SUM(pm.clicks), 0)::float / SUM(pm.impressions)
              ELSE a.predicted_ctr
            END DESC,
            a.predicted_ctr DESC
          LIMIT $2
        `;

        const result = await pgPool.query(query, [category, parseInt(limit as string)]);

        console.log(`Found ${result.rows.length} trending ads`);

        res.json({
          status: 'success',
          ads: result.rows,
          count: result.rows.length,
          category
        });

      } catch (error: any) {
        console.error('Error fetching trending ads:', error);
        // Return empty array on error rather than failing
        res.json({
          status: 'success',
          ads: [],
          count: 0,
          message: 'No trending ads available'
        });
      }
    }
  );

  /**
   * GET /api/ads/search
   * Search ads with filters - pro implementation
   */
  router.get(
    '/search',
    apiRateLimiter,
    validateInput({
      query: {
        q: { type: 'string', required: false, max: 200, sanitize: true },
        platform: { type: 'string', required: false, enum: ['all', 'meta', 'tiktok', 'youtube', 'google'] },
        category: { type: 'string', required: false },
        minEngagement: { type: 'string', required: false },
        dateRange: { type: 'string', required: false },
        sortBy: { type: 'string', required: false, enum: ['engagement', 'views', 'recent', 'relevance'] },
        limit: { type: 'number', required: false, min: 1, max: 100 },
        offset: { type: 'number', required: false, min: 0 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const {
          q: searchQuery = '',
          platform = 'all',
          category = 'all',
          minEngagement = '0',
          dateRange = '30',
          sortBy = 'engagement',
          limit = 20,
          offset = 0
        } = req.query;

        console.log(`Searching ads: q="${searchQuery}", platform=${platform}, category=${category}`);

        // Build dynamic query with filters
        const conditions: string[] = ['a.status IN (\'approved\', \'published\')'];
        const values: any[] = [];
        let paramIndex = 1;

        // Text search on brand name, ad title, arc name
        if (searchQuery && (searchQuery as string).trim()) {
          conditions.push(`(
            LOWER(c.name) LIKE LOWER($${paramIndex}) OR
            LOWER(v.title) LIKE LOWER($${paramIndex}) OR
            LOWER(a.arc_name) LIKE LOWER($${paramIndex}) OR
            LOWER(v.description) LIKE LOWER($${paramIndex})
          )`);
          values.push(`%${searchQuery}%`);
          paramIndex++;
        }

        // Platform filter
        if (platform && platform !== 'all') {
          const platformPatterns: Record<string, string> = {
            meta: '%facebook%|%instagram%',
            tiktok: '%tiktok%',
            youtube: '%youtube%',
            google: '%google%'
          };
          if (platformPatterns[platform as string]) {
            conditions.push(`(v.video_url ~* $${paramIndex})`);
            values.push(platformPatterns[platform as string]);
            paramIndex++;
          }
        }

        // Date range filter
        if (dateRange && dateRange !== 'all') {
          const days = parseInt(dateRange as string);
          if (!isNaN(days) && days > 0) {
            conditions.push(`a.created_at >= NOW() - INTERVAL '${days} days'`);
          }
        }

        // Build ORDER BY clause
        let orderBy = '';
        switch (sortBy) {
          case 'views':
            orderBy = 'COALESCE(SUM(pm.impressions), 0) DESC';
            break;
          case 'recent':
            orderBy = 'a.created_at DESC';
            break;
          case 'relevance':
            orderBy = searchQuery ? `
              CASE
                WHEN LOWER(c.name) LIKE LOWER('%${searchQuery}%') THEN 1
                WHEN LOWER(v.title) LIKE LOWER('%${searchQuery}%') THEN 2
                ELSE 3
              END, a.predicted_ctr DESC` : 'a.predicted_ctr DESC';
            break;
          case 'engagement':
          default:
            orderBy = `
              CASE
                WHEN COALESCE(SUM(pm.impressions), 0) > 0
                THEN COALESCE(SUM(pm.clicks), 0)::float / SUM(pm.impressions)
                ELSE a.predicted_ctr
              END DESC`;
        }

        const query = `
          SELECT
            a.ad_id as id,
            COALESCE(c.name, 'Brand') as brand,
            COALESCE(v.title, a.arc_name, 'Ad Creative') as title,
            CASE
              WHEN COALESCE(SUM(pm.impressions), 0) > 1000000 THEN ROUND(COALESCE(SUM(pm.impressions), 0)::numeric / 1000000, 1)::text || 'M'
              WHEN COALESCE(SUM(pm.impressions), 0) > 1000 THEN ROUND(COALESCE(SUM(pm.impressions), 0)::numeric / 1000, 1)::text || 'K'
              ELSE COALESCE(SUM(pm.impressions), 0)::text
            END as views,
            CASE
              WHEN COALESCE(SUM(pm.impressions), 0) > 0
              THEN ROUND((COALESCE(SUM(pm.clicks), 0)::numeric / SUM(pm.impressions) * 100), 1)::text || '%'
              ELSE ROUND(a.predicted_ctr * 100, 1)::text || '%'
            END as engagement,
            COALESCE(
              CASE
                WHEN v.video_url LIKE '%tiktok%' THEN 'TikTok'
                WHEN v.video_url LIKE '%youtube%' THEN 'YouTube'
                WHEN v.video_url LIKE '%instagram%' THEN 'Instagram'
                WHEN v.video_url LIKE '%facebook%' THEN 'Facebook'
                ELSE 'Meta'
              END,
              'Meta'
            ) as platform,
            v.thumbnail_url as thumbnail,
            v.video_url as "videoUrl",
            a.created_at as "datePublished",
            $${paramIndex} as category
          FROM ads a
          LEFT JOIN videos v ON a.asset_id::text = v.id::text
          LEFT JOIN campaigns c ON v.campaign_id = c.id
          LEFT JOIN performance_metrics pm ON v.id = pm.video_id
          WHERE ${conditions.join(' AND ')}
          GROUP BY a.ad_id, c.name, v.title, a.arc_name, v.thumbnail_url, v.video_url, a.created_at, a.predicted_ctr
          ${minEngagement && parseFloat(minEngagement as string) > 0 ? `
            HAVING (
              CASE
                WHEN COALESCE(SUM(pm.impressions), 0) > 0
                THEN COALESCE(SUM(pm.clicks), 0)::float / SUM(pm.impressions) * 100
                ELSE a.predicted_ctr * 100
              END
            ) >= ${parseFloat(minEngagement as string)}
          ` : ''}
          ORDER BY ${orderBy}
          LIMIT $${paramIndex + 1} OFFSET $${paramIndex + 2}
        `;

        values.push(category, parseInt(limit as string), parseInt(offset as string));

        const result = await pgPool.query(query, values);

        // Get total count for pagination
        const countQuery = `
          SELECT COUNT(DISTINCT a.ad_id) as total
          FROM ads a
          LEFT JOIN videos v ON a.asset_id::text = v.id::text
          LEFT JOIN campaigns c ON v.campaign_id = c.id
          WHERE ${conditions.join(' AND ')}
        `;

        const countResult = await pgPool.query(countQuery, values.slice(0, -3));
        const totalCount = parseInt(countResult.rows[0]?.total || '0');

        console.log(`Search found ${result.rows.length} ads (total: ${totalCount})`);

        res.json({
          status: 'success',
          ads: result.rows,
          count: result.rows.length,
          pagination: {
            total: totalCount,
            limit: parseInt(limit as string),
            offset: parseInt(offset as string),
            hasMore: parseInt(offset as string) + result.rows.length < totalCount
          },
          filters: {
            query: searchQuery,
            platform,
            category,
            minEngagement,
            dateRange,
            sortBy
          }
        });

      } catch (error: any) {
        console.error('Error searching ads:', error);
        res.status(500).json({
          error: 'Search failed',
          message: error.message,
          ads: []
        });
      }
    }
  );

  return router;
}

export default createAdsRouter;
