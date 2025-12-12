/**
 * Analytics Routes
 * Agent 58 - Comprehensive analytics and reporting
 *
 * Provides detailed analytics across campaigns and ads:
 * - Dashboard overview stats
 * - Campaign performance trends
 * - Predictions vs actual performance
 * - Real-time metrics
 * - Custom date range queries
 */

import { Router, Request, Response } from 'express';
import { Pool } from 'pg';
import { httpClient } from '../index';
import { apiRateLimiter, validateInput } from '../middleware/security';

const router = Router();

// Service URLs
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8003';
const META_PUBLISHER_URL = process.env.META_PUBLISHER_URL || 'http://localhost:8083';

/**
 * Create analytics router with database connection
 */
export function createAnalyticsRouter(pgPool: Pool): Router {
  /**
   * GET /api/analytics/overview
   * Dashboard overview statistics
   */
  router.get(
    '/overview',
    apiRateLimiter,
    validateInput({
      query: {
        start_date: { type: 'string', required: false },
        end_date: { type: 'string', required: false },
        time_range: { type: 'string', required: false, enum: ['today', '7d', '30d', '90d', 'all'] }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { start_date, end_date, time_range = '30d' } = req.query;

        console.log(`Fetching analytics overview: time_range=${time_range}`);

        // Calculate date range
        let dateFilter = '';
        const dateParams: any[] = [];
        let paramIndex = 1;

        if (start_date && end_date) {
          dateFilter = 'AND pm.date >= $1 AND pm.date <= $2';
          dateParams.push(start_date, end_date);
        } else if (time_range !== 'all') {
          // SECURITY FIX: Use parameterized query instead of string interpolation
          const timeRangeStr = String(time_range);
          const days = timeRangeStr === 'today' ? 0 : parseInt(timeRangeStr.replace('d', ''));
          
          // Validate days is a number
          if (isNaN(days) || days < 0 || days > 365) {
            return res.status(400).json({ error: 'Invalid time_range' });
          }
          
          // Use parameterized query
          dateFilter = `AND pm.date >= CURRENT_DATE - INTERVAL $${paramIndex} days`;
          dateParams.push(days);
          paramIndex++;
        }

        // Query overall metrics
        const metricsQuery = `
          SELECT
            COUNT(DISTINCT c.id) as total_campaigns,
            COUNT(DISTINCT v.id) as total_videos,
            COUNT(DISTINCT CASE WHEN c.status = 'active' THEN c.id END) as active_campaigns,
            COALESCE(SUM(pm.spend), 0) as total_spend,
            COALESCE(SUM(pm.impressions), 0) as total_impressions,
            COALESCE(SUM(pm.clicks), 0) as total_clicks,
            COALESCE(SUM(pm.conversions), 0) as total_conversions,
            COALESCE(AVG(pm.ctr), 0) as avg_ctr
          FROM campaigns c
          LEFT JOIN videos v ON c.id = v.campaign_id
          LEFT JOIN performance_metrics pm ON v.id = pm.video_id
          WHERE c.status != 'deleted' ${dateFilter}
        `;

        const metricsResult = await pgPool.query(metricsQuery, dateParams);
        const metrics = metricsResult.rows[0];

        // Calculate derived metrics
        const totalSpend = parseFloat(metrics.total_spend) || 0;
        const totalClicks = parseInt(metrics.total_clicks) || 0;
        const totalImpressions = parseInt(metrics.total_impressions) || 0;
        const totalConversions = parseInt(metrics.total_conversions) || 0;

        const ctr = totalImpressions > 0 ? (totalClicks / totalImpressions) * 100 : 0;
        const cpc = totalClicks > 0 ? totalSpend / totalClicks : 0;
        const cpa = totalConversions > 0 ? totalSpend / totalConversions : 0;
        const conversionRate = totalClicks > 0 ? (totalConversions / totalClicks) * 100 : 0;

        // Get top performing campaigns
        const topCampaignsQuery = `
          SELECT
            c.id,
            c.name,
            c.status,
            COALESCE(SUM(pm.spend), 0) as spend,
            COALESCE(SUM(pm.impressions), 0) as impressions,
            COALESCE(SUM(pm.clicks), 0) as clicks,
            COALESCE(SUM(pm.conversions), 0) as conversions,
            COALESCE(AVG(pm.ctr), 0) as ctr
          FROM campaigns c
          LEFT JOIN videos v ON c.id = v.campaign_id
          LEFT JOIN performance_metrics pm ON v.id = pm.video_id
          WHERE c.status != 'deleted' ${dateFilter}
          GROUP BY c.id, c.name, c.status
          HAVING SUM(pm.impressions) > 0
          ORDER BY SUM(pm.conversions) DESC
          LIMIT 5
        `;

        const topCampaignsResult = await pgPool.query(topCampaignsQuery, dateParams);

        // Get daily trend data
        const trendQuery = `
          SELECT
            pm.date,
            COALESCE(SUM(pm.spend), 0) as spend,
            COALESCE(SUM(pm.impressions), 0) as impressions,
            COALESCE(SUM(pm.clicks), 0) as clicks,
            COALESCE(SUM(pm.conversions), 0) as conversions
          FROM performance_metrics pm
          WHERE 1=1 ${dateFilter}
          GROUP BY pm.date
          ORDER BY pm.date DESC
          LIMIT 30
        `;

        const trendResult = await pgPool.query(trendQuery, dateParams);

        console.log(`Analytics overview generated: ${metrics.total_campaigns} campaigns, $${totalSpend.toFixed(2)} spend`);

        res.json({
          status: 'success',
          time_range: time_range,
          start_date: start_date || null,
          end_date: end_date || null,
          overview: {
            campaigns: {
              total: parseInt(metrics.total_campaigns) || 0,
              active: parseInt(metrics.active_campaigns) || 0,
              paused: parseInt(metrics.total_campaigns) - parseInt(metrics.active_campaigns)
            },
            videos: {
              total: parseInt(metrics.total_videos) || 0
            },
            performance: {
              spend: totalSpend,
              impressions: totalImpressions,
              clicks: totalClicks,
              conversions: totalConversions,
              ctr: ctr,
              cpc: cpc,
              cpa: cpa,
              conversion_rate: conversionRate
            }
          },
          top_campaigns: topCampaignsResult.rows.map(row => ({
            id: row.id,
            name: row.name,
            status: row.status,
            spend: parseFloat(row.spend),
            impressions: parseInt(row.impressions),
            clicks: parseInt(row.clicks),
            conversions: parseInt(row.conversions),
            ctr: parseFloat(row.ctr)
          })),
          trends: trendResult.rows.map(row => ({
            date: row.date,
            spend: parseFloat(row.spend),
            impressions: parseInt(row.impressions),
            clicks: parseInt(row.clicks),
            conversions: parseInt(row.conversions)
          }))
        });

      } catch (error: any) {
        console.error('Error fetching analytics overview:', error);
        res.status(500).json({
          error: 'Failed to fetch analytics overview',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/analytics/campaigns/:id
   * Detailed analytics for a specific campaign
   */
  router.get(
    '/campaigns/:id',
    apiRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      },
      query: {
        start_date: { type: 'string', required: false },
        end_date: { type: 'string', required: false }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;
        const { start_date, end_date } = req.query;

        console.log(`Fetching campaign analytics: ${id}`);

        // Date filter
        let dateFilter = '';
        const params: any[] = [id];

        if (start_date && end_date) {
          dateFilter = 'AND pm.date >= $2 AND pm.date <= $3';
          params.push(start_date, end_date);
        }

        // Get campaign info
        const campaignQuery = `
          SELECT c.*, COUNT(DISTINCT v.id) as video_count
          FROM campaigns c
          LEFT JOIN videos v ON c.id = v.campaign_id
          WHERE c.id = $1
          GROUP BY c.id
        `;

        const campaignResult = await pgPool.query(campaignQuery, [id]);

        if (campaignResult.rows.length === 0) {
          return res.status(404).json({
            error: 'Campaign not found',
            message: `Campaign with id ${id} does not exist`
          });
        }

        const campaign = campaignResult.rows[0];

        // Get performance metrics
        const metricsQuery = `
          SELECT
            COALESCE(SUM(pm.spend), 0) as total_spend,
            COALESCE(SUM(pm.impressions), 0) as total_impressions,
            COALESCE(SUM(pm.clicks), 0) as total_clicks,
            COALESCE(SUM(pm.conversions), 0) as total_conversions,
            COALESCE(AVG(pm.ctr), 0) as avg_ctr
          FROM videos v
          LEFT JOIN performance_metrics pm ON v.id = pm.video_id
          WHERE v.campaign_id = $1 ${dateFilter}
        `;

        const metricsResult = await pgPool.query(metricsQuery, params);
        const metrics = metricsResult.rows[0];

        // Get daily performance trend
        const trendQuery = `
          SELECT
            pm.date,
            COALESCE(SUM(pm.spend), 0) as spend,
            COALESCE(SUM(pm.impressions), 0) as impressions,
            COALESCE(SUM(pm.clicks), 0) as clicks,
            COALESCE(SUM(pm.conversions), 0) as conversions,
            COALESCE(AVG(pm.ctr), 0) as ctr
          FROM videos v
          LEFT JOIN performance_metrics pm ON v.id = pm.video_id
          WHERE v.campaign_id = $1 ${dateFilter}
          GROUP BY pm.date
          ORDER BY pm.date ASC
        `;

        const trendResult = await pgPool.query(trendQuery, params);

        // Get video performance breakdown
        const videosQuery = `
          SELECT
            v.id,
            v.title,
            v.video_url,
            v.thumbnail_url,
            COALESCE(SUM(pm.spend), 0) as spend,
            COALESCE(SUM(pm.impressions), 0) as impressions,
            COALESCE(SUM(pm.clicks), 0) as clicks,
            COALESCE(SUM(pm.conversions), 0) as conversions,
            COALESCE(AVG(pm.ctr), 0) as ctr
          FROM videos v
          LEFT JOIN performance_metrics pm ON v.id = pm.video_id
          WHERE v.campaign_id = $1 ${dateFilter}
          GROUP BY v.id, v.title, v.video_url, v.thumbnail_url
          ORDER BY SUM(pm.conversions) DESC
        `;

        const videosResult = await pgPool.query(videosQuery, params);

        res.json({
          status: 'success',
          campaign: {
            id: campaign.id,
            name: campaign.name,
            status: campaign.status,
            budget_daily: parseFloat(campaign.budget_daily),
            video_count: parseInt(campaign.video_count)
          },
          performance: {
            total_spend: parseFloat(metrics.total_spend),
            total_impressions: parseInt(metrics.total_impressions),
            total_clicks: parseInt(metrics.total_clicks),
            total_conversions: parseInt(metrics.total_conversions),
            avg_ctr: parseFloat(metrics.avg_ctr),
            cpc: parseInt(metrics.total_clicks) > 0
              ? parseFloat(metrics.total_spend) / parseInt(metrics.total_clicks)
              : 0,
            cpa: parseInt(metrics.total_conversions) > 0
              ? parseFloat(metrics.total_spend) / parseInt(metrics.total_conversions)
              : 0
          },
          daily_trend: trendResult.rows.map(row => ({
            date: row.date,
            spend: parseFloat(row.spend),
            impressions: parseInt(row.impressions),
            clicks: parseInt(row.clicks),
            conversions: parseInt(row.conversions),
            ctr: parseFloat(row.ctr)
          })),
          videos: videosResult.rows.map(row => ({
            id: row.id,
            title: row.title,
            video_url: row.video_url,
            thumbnail_url: row.thumbnail_url,
            performance: {
              spend: parseFloat(row.spend),
              impressions: parseInt(row.impressions),
              clicks: parseInt(row.clicks),
              conversions: parseInt(row.conversions),
              ctr: parseFloat(row.ctr)
            }
          }))
        });

      } catch (error: any) {
        console.error('Error fetching campaign analytics:', error);
        res.status(500).json({
          error: 'Failed to fetch campaign analytics',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/analytics/trends
   * Performance trends and insights
   */
  router.get(
    '/trends',
    apiRateLimiter,
    validateInput({
      query: {
        metric: { type: 'string', required: false, enum: ['spend', 'impressions', 'clicks', 'conversions', 'ctr'] },
        days: { type: 'number', required: false, min: 1, max: 365 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { metric = 'conversions', days = 30 } = req.query;

        console.log(`Fetching performance trends: metric=${metric}, days=${days}`);

        // Query daily trends
        const trendQuery = `
          SELECT
            pm.date,
            COALESCE(SUM(pm.spend), 0) as spend,
            COALESCE(SUM(pm.impressions), 0) as impressions,
            COALESCE(SUM(pm.clicks), 0) as clicks,
            COALESCE(SUM(pm.conversions), 0) as conversions,
            COALESCE(AVG(pm.ctr), 0) as ctr
          FROM performance_metrics pm
          WHERE pm.date >= CURRENT_DATE - INTERVAL '${parseInt(days as string)} days'
          GROUP BY pm.date
          ORDER BY pm.date ASC
        `;

        const trendResult = await pgPool.query(trendQuery);

        // Calculate week-over-week growth
        const nowData = trendResult.rows.slice(-7);
        const prevData = trendResult.rows.slice(-14, -7);

        const calculateGrowth = (current: any[], previous: any[], field: string) => {
          const currentSum = current.reduce((sum, row) => sum + parseFloat(row[field] || 0), 0);
          const previousSum = previous.reduce((sum, row) => sum + parseFloat(row[field] || 0), 0);

          if (previousSum === 0) return 0;
          return ((currentSum - previousSum) / previousSum) * 100;
        };

        const trends = {
          spend_growth: calculateGrowth(nowData, prevData, 'spend'),
          impressions_growth: calculateGrowth(nowData, prevData, 'impressions'),
          clicks_growth: calculateGrowth(nowData, prevData, 'clicks'),
          conversions_growth: calculateGrowth(nowData, prevData, 'conversions')
        };

        // Try to get ML service predictions
        let predictions = null;
        try {
          const mlResponse = await httpClient.get(`${ML_SERVICE_URL}/api/ml/predictions/trends`, {
            params: { days },
            timeout: 10000
          });
          predictions = mlResponse.data;
        } catch (mlError: any) {
          console.warn('ML predictions unavailable:', mlError.message);
        }

        res.json({
          status: 'success',
          metric,
          days: parseInt(days as string),
          daily_data: trendResult.rows.map(row => ({
            date: row.date,
            spend: parseFloat(row.spend),
            impressions: parseInt(row.impressions),
            clicks: parseInt(row.clicks),
            conversions: parseInt(row.conversions),
            ctr: parseFloat(row.ctr)
          })),
          week_over_week: trends,
          predictions: predictions || {
            message: 'ML predictions temporarily unavailable',
            available: false
          }
        });

      } catch (error: any) {
        console.error('Error fetching trends:', error);
        res.status(500).json({
          error: 'Failed to fetch trends',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/analytics/predictions-vs-actual
   * Compare ML predictions with actual performance
   */
  router.get(
    '/predictions-vs-actual',
    apiRateLimiter,
    validateInput({
      query: {
        start_date: { type: 'string', required: false },
        end_date: { type: 'string', required: false },
        limit: { type: 'number', required: false, min: 1, max: 100 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { start_date, end_date, limit = 20 } = req.query;

        console.log(`Fetching predictions vs actual comparison`);

        // Query ads with predictions and actual performance
        const query = `
          SELECT
            a.ad_id,
            a.predicted_ctr,
            a.predicted_roas,
            a.created_at as prediction_date,
            COALESCE(SUM(pm.impressions), 0) as actual_impressions,
            COALESCE(SUM(pm.clicks), 0) as actual_clicks,
            COALESCE(SUM(pm.spend), 0) as actual_spend,
            COALESCE(SUM(pm.conversions), 0) as actual_conversions,
            COALESCE(AVG(pm.ctr), 0) as actual_ctr,
            c.name as campaign_name
          FROM ads a
          LEFT JOIN videos v ON a.asset_id::text = v.id::text
          LEFT JOIN performance_metrics pm ON v.id = pm.video_id
          LEFT JOIN campaigns c ON v.campaign_id = c.id
          WHERE a.predicted_ctr IS NOT NULL
          ${start_date ? `AND a.created_at >= '${start_date}'` : ''}
          ${end_date ? `AND a.created_at <= '${end_date}'` : ''}
          GROUP BY a.ad_id, a.predicted_ctr, a.predicted_roas, a.created_at, c.name
          HAVING SUM(pm.impressions) > 100
          ORDER BY a.created_at DESC
          LIMIT $1
        `;

        const result = await pgPool.query(query, [parseInt(limit as string)]);

        // Calculate accuracy metrics
        let totalCtrError = 0;
        let totalRoasError = 0;
        let validCtrComparisons = 0;
        let validRoasComparisons = 0;

        const comparisons = result.rows.map(row => {
          const actualCtr = parseFloat(row.actual_ctr) || 0;
          const predictedCtr = parseFloat(row.predicted_ctr) || 0;
          const actualRoas = parseInt(row.actual_conversions) > 0
            ? (parseInt(row.actual_conversions) * 50) / parseFloat(row.actual_spend) // Assume $50 AOV
            : 0;
          const predictedRoas = parseFloat(row.predicted_roas) || 0;

          const ctrError = predictedCtr > 0 ? Math.abs(actualCtr - predictedCtr) / predictedCtr : 0;
          const roasError = predictedRoas > 0 ? Math.abs(actualRoas - predictedRoas) / predictedRoas : 0;

          if (ctrError > 0) {
            totalCtrError += ctrError;
            validCtrComparisons++;
          }

          if (roasError > 0 && actualRoas > 0) {
            totalRoasError += roasError;
            validRoasComparisons++;
          }

          return {
            ad_id: row.ad_id,
            campaign_name: row.campaign_name,
            prediction_date: row.prediction_date,
            predictions: {
              ctr: predictedCtr,
              roas: predictedRoas
            },
            actual: {
              ctr: actualCtr,
              roas: actualRoas,
              impressions: parseInt(row.actual_impressions),
              clicks: parseInt(row.actual_clicks),
              spend: parseFloat(row.actual_spend),
              conversions: parseInt(row.actual_conversions)
            },
            accuracy: {
              ctr_error_pct: (ctrError * 100).toFixed(2),
              roas_error_pct: (roasError * 100).toFixed(2),
              ctr_accurate: ctrError < 0.2, // Within 20%
              roas_accurate: roasError < 0.3 // Within 30%
            }
          };
        });

        const overallAccuracy = {
          avg_ctr_error_pct: validCtrComparisons > 0
            ? ((totalCtrError / validCtrComparisons) * 100).toFixed(2)
            : 0,
          avg_roas_error_pct: validRoasComparisons > 0
            ? ((totalRoasError / validRoasComparisons) * 100).toFixed(2)
            : 0,
          total_comparisons: comparisons.length,
          valid_ctr_comparisons: validCtrComparisons,
          valid_roas_comparisons: validRoasComparisons
        };

        res.json({
          status: 'success',
          overall_accuracy: overallAccuracy,
          comparisons
        });

      } catch (error: any) {
        console.error('Error fetching predictions vs actual:', error);
        res.status(500).json({
          error: 'Failed to fetch predictions comparison',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/analytics/real-time
   * Real-time performance metrics (last 24 hours)
   */
  router.get(
    '/real-time',
    apiRateLimiter,
    async (req: Request, res: Response) => {
      try {
        console.log('Fetching real-time analytics');

        // Query last 24 hours of data
        const query = `
          SELECT
            pm.platform,
            COALESCE(SUM(pm.spend), 0) as spend_24h,
            COALESCE(SUM(pm.impressions), 0) as impressions_24h,
            COALESCE(SUM(pm.clicks), 0) as clicks_24h,
            COALESCE(SUM(pm.conversions), 0) as conversions_24h,
            COALESCE(AVG(pm.ctr), 0) as avg_ctr_24h,
            COUNT(DISTINCT pm.video_id) as active_ads
          FROM performance_metrics pm
          WHERE pm.date >= CURRENT_DATE - INTERVAL '1 day'
          GROUP BY pm.platform
        `;

        const result = await pgPool.query(query);

        // Get active campaigns count
        const activeCampaignsQuery = `
          SELECT COUNT(*) as count
          FROM campaigns
          WHERE status = 'active'
        `;

        const activeCampaignsResult = await pgPool.query(activeCampaignsQuery);

        // Calculate totals
        const totals = result.rows.reduce((acc, row) => ({
          spend: acc.spend + parseFloat(row.spend_24h),
          impressions: acc.impressions + parseInt(row.impressions_24h),
          clicks: acc.clicks + parseInt(row.clicks_24h),
          conversions: acc.conversions + parseInt(row.conversions_24h)
        }), { spend: 0, impressions: 0, clicks: 0, conversions: 0 });

        res.json({
          status: 'success',
          timestamp: new Date().toISOString(),
          time_range: 'last_24_hours',
          active_campaigns: parseInt(activeCampaignsResult.rows[0].count),
          totals: {
            spend: totals.spend,
            impressions: totals.impressions,
            clicks: totals.clicks,
            conversions: totals.conversions,
            ctr: totals.impressions > 0 ? (totals.clicks / totals.impressions) * 100 : 0,
            cpc: totals.clicks > 0 ? totals.spend / totals.clicks : 0,
            cpa: totals.conversions > 0 ? totals.spend / totals.conversions : 0
          },
          by_platform: result.rows.map(row => ({
            platform: row.platform,
            spend: parseFloat(row.spend_24h),
            impressions: parseInt(row.impressions_24h),
            clicks: parseInt(row.clicks_24h),
            conversions: parseInt(row.conversions_24h),
            avg_ctr: parseFloat(row.avg_ctr_24h),
            active_ads: parseInt(row.active_ads)
          }))
        });

      } catch (error: any) {
        console.error('Error fetching real-time analytics:', error);
        res.status(500).json({
          error: 'Failed to fetch real-time analytics',
          message: error.message
        });
      }
    }
  );

  return router;
}

export default createAnalyticsRouter;
