/**
 * Campaign Management Routes
 * Agent 58 - Full CRUD for campaign management
 *
 * Provides complete campaign lifecycle management:
 * - Create/Read/Update/Delete campaigns
 * - Launch and pause campaigns
 * - Query campaign performance
 * - Budget management
 */

import { Router, Request, Response } from 'express';
import { Pool } from 'pg';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';
import { apiRateLimiter, uploadRateLimiter, validateInput } from '../middleware/security';

const router = Router();

// Service URLs
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8003';
const TITAN_CORE_URL = process.env.TITAN_CORE_URL || 'http://localhost:8004';
const META_PUBLISHER_URL = process.env.META_PUBLISHER_URL || 'http://localhost:8083';

/**
 * POST /api/campaigns
 * Create a new campaign
 */
export function createCampaignsRouter(pgPool: Pool): Router {
  router.post(
    '/',
    uploadRateLimiter,
    validateInput({
      body: {
        name: { type: 'string', required: true, min: 1, max: 255, sanitize: true },
        budget_daily: { type: 'number', required: true, min: 1 },
        target_audience: { type: 'object', required: false },
        objective: { type: 'string', required: false, enum: ['conversions', 'traffic', 'awareness', 'engagement'] },
        status: { type: 'string', required: false, enum: ['draft', 'active', 'paused'] }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { name, budget_daily, target_audience, objective = 'conversions', status = 'draft' } = req.body;

        console.log(`Creating campaign: ${name}, budget: $${budget_daily}`);

        // Generate campaign ID
        const campaignId = uuidv4();

        // Insert campaign into database
        const query = `
          INSERT INTO campaigns (id, name, status, budget_daily, target_audience, created_at, updated_at)
          VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
          RETURNING *
        `;

        const values = [
          campaignId,
          name,
          status,
          budget_daily,
          JSON.stringify(target_audience || {})
        ];

        const result = await pgPool.query(query, values);
        const campaign = result.rows[0];

        // If campaign is active, notify ML service for tracking
        if (status === 'active') {
          try {
            await axios.post(`${ML_SERVICE_URL}/api/ml/campaigns/track`, {
              campaign_id: campaignId,
              name,
              budget: budget_daily,
              objective
            }, { timeout: 5000 });
          } catch (mlError: any) {
            console.warn('ML service notification failed:', mlError.message);
            // Non-fatal, continue
          }
        }

        console.log(`Campaign created successfully: ${campaignId}`);

        res.status(201).json({
          status: 'success',
          message: 'Campaign created successfully',
          campaign: {
            id: campaign.id,
            name: campaign.name,
            status: campaign.status,
            budget_daily: parseFloat(campaign.budget_daily),
            target_audience: campaign.target_audience,
            created_at: campaign.created_at,
            updated_at: campaign.updated_at
          }
        });

      } catch (error: any) {
        console.error('Error creating campaign:', error);
        res.status(500).json({
          error: 'Failed to create campaign',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/campaigns
   * List all campaigns with optional filters
   */
  router.get(
    '/',
    apiRateLimiter,
    validateInput({
      query: {
        status: { type: 'string', required: false, enum: ['draft', 'active', 'paused', 'completed'] },
        limit: { type: 'number', required: false, min: 1, max: 100 },
        offset: { type: 'number', required: false, min: 0 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { status, limit = 20, offset = 0 } = req.query;

        console.log(`Fetching campaigns: status=${status || 'all'}, limit=${limit}`);

        let query = `
          SELECT
            c.id,
            c.name,
            c.status,
            c.budget_daily,
            c.target_audience,
            c.created_at,
            c.updated_at,
            COUNT(DISTINCT v.id) as video_count,
            COALESCE(SUM(pm.spend), 0) as total_spend,
            COALESCE(SUM(pm.impressions), 0) as total_impressions,
            COALESCE(SUM(pm.clicks), 0) as total_clicks,
            COALESCE(SUM(pm.conversions), 0) as total_conversions
          FROM campaigns c
          LEFT JOIN videos v ON c.id = v.campaign_id
          LEFT JOIN performance_metrics pm ON v.id = pm.video_id
        `;

        const values: any[] = [];
        let paramIndex = 1;

        if (status) {
          query += ` WHERE c.status = $${paramIndex}`;
          values.push(status);
          paramIndex++;
        }

        query += `
          GROUP BY c.id, c.name, c.status, c.budget_daily, c.target_audience, c.created_at, c.updated_at
          ORDER BY c.created_at DESC
          LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
        `;

        values.push(parseInt(limit as string), parseInt(offset as string));

        const result = await pgPool.query(query, values);

        // Get total count
        let countQuery = 'SELECT COUNT(*) FROM campaigns';
        if (status) {
          countQuery += ' WHERE status = $1';
        }
        const countResult = await pgPool.query(countQuery, status ? [status] : []);
        const totalCount = parseInt(countResult.rows[0].count);

        const campaigns = result.rows.map(row => ({
          id: row.id,
          name: row.name,
          status: row.status,
          budget_daily: parseFloat(row.budget_daily),
          target_audience: row.target_audience,
          created_at: row.created_at,
          updated_at: row.updated_at,
          stats: {
            video_count: parseInt(row.video_count),
            total_spend: parseFloat(row.total_spend),
            total_impressions: parseInt(row.total_impressions),
            total_clicks: parseInt(row.total_clicks),
            total_conversions: parseInt(row.total_conversions),
            ctr: parseInt(row.total_impressions) > 0
              ? (parseInt(row.total_clicks) / parseInt(row.total_impressions)) * 100
              : 0
          }
        }));

        console.log(`Found ${campaigns.length} campaigns (total: ${totalCount})`);

        res.json({
          status: 'success',
          campaigns,
          pagination: {
            total: totalCount,
            limit: parseInt(limit as string),
            offset: parseInt(offset as string),
            has_more: parseInt(offset as string) + campaigns.length < totalCount
          }
        });

      } catch (error: any) {
        console.error('Error fetching campaigns:', error);
        res.status(500).json({
          error: 'Failed to fetch campaigns',
          message: error.message,
          campaigns: []
        });
      }
    }
  );

  /**
   * GET /api/campaigns/:id
   * Get detailed campaign information
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

        console.log(`Fetching campaign details: ${id}`);

        const query = `
          SELECT
            c.*,
            COUNT(DISTINCT v.id) as video_count,
            COALESCE(SUM(pm.spend), 0) as total_spend,
            COALESCE(SUM(pm.impressions), 0) as total_impressions,
            COALESCE(SUM(pm.clicks), 0) as total_clicks,
            COALESCE(SUM(pm.conversions), 0) as total_conversions,
            COALESCE(AVG(pm.ctr), 0) as avg_ctr
          FROM campaigns c
          LEFT JOIN videos v ON c.id = v.campaign_id
          LEFT JOIN performance_metrics pm ON v.id = pm.video_id
          WHERE c.id = $1
          GROUP BY c.id
        `;

        const result = await pgPool.query(query, [id]);

        if (result.rows.length === 0) {
          return res.status(404).json({
            error: 'Campaign not found',
            message: `Campaign with id ${id} does not exist`
          });
        }

        const campaign = result.rows[0];

        // Get videos for this campaign
        const videosQuery = `
          SELECT
            v.*,
            COALESCE(SUM(pm.impressions), 0) as impressions,
            COALESCE(SUM(pm.clicks), 0) as clicks,
            COALESCE(SUM(pm.spend), 0) as spend,
            COALESCE(SUM(pm.conversions), 0) as conversions
          FROM videos v
          LEFT JOIN performance_metrics pm ON v.id = pm.video_id
          WHERE v.campaign_id = $1
          GROUP BY v.id
          ORDER BY v.created_at DESC
        `;

        const videosResult = await pgPool.query(videosQuery, [id]);

        res.json({
          status: 'success',
          campaign: {
            id: campaign.id,
            name: campaign.name,
            status: campaign.status,
            budget_daily: parseFloat(campaign.budget_daily),
            target_audience: campaign.target_audience,
            created_at: campaign.created_at,
            updated_at: campaign.updated_at,
            stats: {
              video_count: parseInt(campaign.video_count),
              total_spend: parseFloat(campaign.total_spend),
              total_impressions: parseInt(campaign.total_impressions),
              total_clicks: parseInt(campaign.total_clicks),
              total_conversions: parseInt(campaign.total_conversions),
              avg_ctr: parseFloat(campaign.avg_ctr) || 0
            },
            videos: videosResult.rows.map(v => ({
              id: v.id,
              title: v.title,
              status: v.status,
              video_url: v.video_url,
              thumbnail_url: v.thumbnail_url,
              duration_seconds: parseFloat(v.duration_seconds) || 0,
              created_at: v.created_at,
              performance: {
                impressions: parseInt(v.impressions),
                clicks: parseInt(v.clicks),
                spend: parseFloat(v.spend),
                conversions: parseInt(v.conversions)
              }
            }))
          }
        });

      } catch (error: any) {
        console.error('Error fetching campaign:', error);
        res.status(500).json({
          error: 'Failed to fetch campaign',
          message: error.message
        });
      }
    }
  );

  /**
   * PUT /api/campaigns/:id
   * Update campaign details
   */
  router.put(
    '/:id',
    apiRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      },
      body: {
        name: { type: 'string', required: false, min: 1, max: 255, sanitize: true },
        budget_daily: { type: 'number', required: false, min: 0 },
        target_audience: { type: 'object', required: false },
        status: { type: 'string', required: false, enum: ['draft', 'active', 'paused', 'completed'] }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;
        const updates = req.body;

        console.log(`Updating campaign: ${id}`);

        // Check if campaign exists
        const checkQuery = 'SELECT * FROM campaigns WHERE id = $1';
        const checkResult = await pgPool.query(checkQuery, [id]);

        if (checkResult.rows.length === 0) {
          return res.status(404).json({
            error: 'Campaign not found',
            message: `Campaign with id ${id} does not exist`
          });
        }

        // Build update query dynamically
        const updateFields: string[] = [];
        const values: any[] = [];
        let paramIndex = 1;

        if (updates.name !== undefined) {
          updateFields.push(`name = $${paramIndex}`);
          values.push(updates.name);
          paramIndex++;
        }

        if (updates.budget_daily !== undefined) {
          updateFields.push(`budget_daily = $${paramIndex}`);
          values.push(updates.budget_daily);
          paramIndex++;
        }

        if (updates.target_audience !== undefined) {
          updateFields.push(`target_audience = $${paramIndex}`);
          values.push(JSON.stringify(updates.target_audience));
          paramIndex++;
        }

        if (updates.status !== undefined) {
          updateFields.push(`status = $${paramIndex}`);
          values.push(updates.status);
          paramIndex++;
        }

        if (updateFields.length === 0) {
          return res.status(400).json({
            error: 'No updates provided',
            message: 'At least one field must be provided for update'
          });
        }

        // Add updated_at timestamp
        updateFields.push(`updated_at = NOW()`);

        // Add campaign ID as last parameter
        values.push(id);

        const updateQuery = `
          UPDATE campaigns
          SET ${updateFields.join(', ')}
          WHERE id = $${paramIndex}
          RETURNING *
        `;

        const result = await pgPool.query(updateQuery, values);
        const campaign = result.rows[0];

        console.log(`Campaign updated successfully: ${id}`);

        res.json({
          status: 'success',
          message: 'Campaign updated successfully',
          campaign: {
            id: campaign.id,
            name: campaign.name,
            status: campaign.status,
            budget_daily: parseFloat(campaign.budget_daily),
            target_audience: campaign.target_audience,
            created_at: campaign.created_at,
            updated_at: campaign.updated_at
          }
        });

      } catch (error: any) {
        console.error('Error updating campaign:', error);
        res.status(500).json({
          error: 'Failed to update campaign',
          message: error.message
        });
      }
    }
  );

  /**
   * DELETE /api/campaigns/:id
   * Delete a campaign (soft delete by setting status to 'deleted')
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

        console.log(`Deleting campaign: ${id}`);

        // Check if campaign exists
        const checkQuery = 'SELECT * FROM campaigns WHERE id = $1';
        const checkResult = await pgPool.query(checkQuery, [id]);

        if (checkResult.rows.length === 0) {
          return res.status(404).json({
            error: 'Campaign not found',
            message: `Campaign with id ${id} does not exist`
          });
        }

        // Soft delete by setting status to 'deleted'
        const deleteQuery = `
          UPDATE campaigns
          SET status = 'deleted', updated_at = NOW()
          WHERE id = $1
          RETURNING *
        `;

        await pgPool.query(deleteQuery, [id]);

        console.log(`Campaign deleted successfully: ${id}`);

        res.json({
          status: 'success',
          message: 'Campaign deleted successfully',
          campaign_id: id
        });

      } catch (error: any) {
        console.error('Error deleting campaign:', error);
        res.status(500).json({
          error: 'Failed to delete campaign',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/campaigns/:id/launch
   * Launch a campaign (set status to active and publish to platforms)
   */
  router.post(
    '/:id/launch',
    uploadRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      },
      body: {
        platforms: { type: 'array', required: false },
        budget_allocation: { type: 'object', required: false }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;
        const { platforms = ['meta'], budget_allocation } = req.body;

        console.log(`Launching campaign: ${id} on platforms: ${platforms.join(', ')}`);

        // Check if campaign exists
        const checkQuery = 'SELECT * FROM campaigns WHERE id = $1';
        const checkResult = await pgPool.query(checkQuery, [id]);

        if (checkResult.rows.length === 0) {
          return res.status(404).json({
            error: 'Campaign not found',
            message: `Campaign with id ${id} does not exist`
          });
        }

        const campaign = checkResult.rows[0];

        // Update campaign status to active
        const updateQuery = `
          UPDATE campaigns
          SET status = 'active', updated_at = NOW()
          WHERE id = $1
          RETURNING *
        `;

        const updateResult = await pgPool.query(updateQuery, [id]);
        const updatedCampaign = updateResult.rows[0];

        // Notify platforms
        const platformResults: any[] = [];

        for (const platform of platforms) {
          try {
            if (platform === 'meta') {
              const response = await axios.post(`${META_PUBLISHER_URL}/campaigns/activate`, {
                campaign_id: id,
                name: campaign.name,
                budget: budget_allocation?.meta || campaign.budget_daily
              }, { timeout: 10000 });

              platformResults.push({
                platform: 'meta',
                status: 'success',
                data: response.data
              });
            }
            // Add other platforms (Google, TikTok) here
          } catch (platformError: any) {
            console.error(`Platform ${platform} activation failed:`, platformError.message);
            platformResults.push({
              platform,
              status: 'failed',
              error: platformError.message
            });
          }
        }

        console.log(`Campaign launched successfully: ${id}`);

        res.json({
          status: 'success',
          message: 'Campaign launched successfully',
          campaign: {
            id: updatedCampaign.id,
            name: updatedCampaign.name,
            status: updatedCampaign.status,
            budget_daily: parseFloat(updatedCampaign.budget_daily)
          },
          platforms: platformResults
        });

      } catch (error: any) {
        console.error('Error launching campaign:', error);
        res.status(500).json({
          error: 'Failed to launch campaign',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/campaigns/:id/pause
   * Pause a running campaign
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

        console.log(`Pausing campaign: ${id}`);

        // Update campaign status to paused
        const updateQuery = `
          UPDATE campaigns
          SET status = 'paused', updated_at = NOW()
          WHERE id = $1 AND status = 'active'
          RETURNING *
        `;

        const result = await pgPool.query(updateQuery, [id]);

        if (result.rows.length === 0) {
          return res.status(404).json({
            error: 'Campaign not found or not active',
            message: `Campaign with id ${id} does not exist or is not active`
          });
        }

        const campaign = result.rows[0];

        console.log(`Campaign paused successfully: ${id}`);

        res.json({
          status: 'success',
          message: 'Campaign paused successfully',
          campaign: {
            id: campaign.id,
            name: campaign.name,
            status: campaign.status
          }
        });

      } catch (error: any) {
        console.error('Error pausing campaign:', error);
        res.status(500).json({
          error: 'Failed to pause campaign',
          message: error.message
        });
      }
    }
  );

  return router;
}

export default createCampaignsRouter;
