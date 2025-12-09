/**
 * Report Generation Routes
 * Agent 18 - Professional PDF & Excel Campaign Reports
 *
 * Provides elite marketers with investment-grade reports for:
 * - Client presentations
 * - Stakeholder updates
 * - Board meetings
 * - Investor relations
 */

import { Router, Request, Response } from 'express';
import { httpClient } from "../index";
import { apiRateLimiter, validateInput } from '../middleware/security';

const router = Router();

// ML Service URL
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8003';

/**
 * POST /api/reports/generate
 * Generate a new campaign performance report
 */
router.post(
  '/generate',
  apiRateLimiter,
  validateInput({
    body: {
      report_type: {
        type: 'string',
        required: true,
        enum: [
          'campaign_performance',
          'ad_creative_analysis',
          'audience_insights',
          'roas_breakdown',
          'weekly_summary',
          'monthly_executive'
        ]
      },
      format: { type: 'string', required: true, enum: ['pdf', 'excel'] },
      start_date: { type: 'string', required: true },
      end_date: { type: 'string', required: true },
      campaign_ids: { type: 'array', required: false },
      ad_ids: { type: 'array', required: false },
      company_name: { type: 'string', required: false, max: 200 },
      company_logo: { type: 'string', required: false, max: 500 },
      filters: { type: 'object', required: false }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      console.log(`Generating report: ${req.body.report_type} (${req.body.format})`);

      // Forward to ML service
      const response = await httpClient.post(
        `${ML_SERVICE_URL}/api/reports/generate`,
        req.body,
        { timeout: 120000 } // 2 minute timeout for report generation
      );

      res.json(response.data);
    } catch (error: any) {
      console.error('Report generation error:', error.message);
      res.status(error.response?.status || 500).json({
        error: 'Report generation failed',
        message: error.message,
        details: error.response?.data
      });
    }
  }
);

/**
 * GET /api/reports
 * List all generated reports
 */
router.get(
  '/',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const { limit = 20 } = req.query;

      console.log(`Fetching report list (limit: ${limit})`);

      const response = await httpClient.get(
        `${ML_SERVICE_URL}/api/reports`,
        {
          params: { limit },
          timeout: 30000
        }
      );

      res.json(response.data);
    } catch (error: any) {
      console.error('Error fetching reports:', error.message);
      res.status(error.response?.status || 500).json({
        error: 'Failed to fetch reports',
        message: error.message,
        reports: [],
        count: 0
      });
    }
  }
);

/**
 * GET /api/reports/:id/download
 * Download a report file
 */
router.get(
  '/:id/download',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const { id } = req.params;

      console.log(`Downloading report: ${id}`);

      // Stream file from ML service
      const response = await httpClient.get(
        `${ML_SERVICE_URL}/api/reports/${id}/download`,
        {
          responseType: 'stream',
          timeout: 60000
        }
      );

      // Forward headers
      res.setHeader('Content-Type', response.headers['content-type']);
      res.setHeader('Content-Disposition', response.headers['content-disposition']);

      // Pipe the stream
      response.data.pipe(res);
    } catch (error: any) {
      console.error('Report download error:', error.message);
      res.status(error.response?.status || 500).json({
        error: 'Failed to download report',
        message: error.message
      });
    }
  }
);

/**
 * DELETE /api/reports/:id
 * Delete a report
 */
router.delete(
  '/:id',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      const { id } = req.params;

      console.log(`Deleting report: ${id}`);

      const response = await httpClient.delete(
        `${ML_SERVICE_URL}/api/reports/${id}`,
        { timeout: 30000 }
      );

      res.json(response.data);
    } catch (error: any) {
      console.error('Report deletion error:', error.message);
      res.status(error.response?.status || 500).json({
        error: 'Failed to delete report',
        message: error.message
      });
    }
  }
);

/**
 * GET /api/reports/templates
 * Get available report templates and their descriptions
 */
router.get(
  '/templates',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    try {
      // Return template information
      const templates = [
        {
          id: 'campaign_performance',
          name: 'Campaign Performance',
          description: 'Overall campaign metrics with spend, ROAS, conversions, and CTR breakdown',
          icon: 'chart-bar',
          suitable_for: ['CMO', 'Marketing Manager', 'Client Reports']
        },
        {
          id: 'ad_creative_analysis',
          name: 'Ad Creative Analysis',
          description: 'Which creatives performed best - analyze hook types, video length, and engagement',
          icon: 'film',
          suitable_for: ['Creative Director', 'Content Team', 'A/B Testing']
        },
        {
          id: 'audience_insights',
          name: 'Audience Insights',
          description: 'Demographics, placements, devices, and behavioral patterns',
          icon: 'users',
          suitable_for: ['Media Buyer', 'Targeting Specialist', 'Strategy']
        },
        {
          id: 'roas_breakdown',
          name: 'ROAS Breakdown',
          description: 'Revenue attribution by channel, campaign, and attribution window',
          icon: 'dollar-sign',
          suitable_for: ['CFO', 'Finance Team', 'ROI Analysis']
        },
        {
          id: 'weekly_summary',
          name: 'Weekly Summary',
          description: 'Week-over-week comparison with trend analysis',
          icon: 'calendar',
          suitable_for: ['Weekly Reviews', 'Team Sync', 'Quick Updates']
        },
        {
          id: 'monthly_executive',
          name: 'Monthly Executive',
          description: 'Executive summary for stakeholders with growth trends and recommendations',
          icon: 'briefcase',
          suitable_for: ['C-Suite', 'Board of Directors', 'Investors']
        }
      ];

      res.json({
        templates,
        count: templates.length
      });
    } catch (error: any) {
      console.error('Error fetching templates:', error.message);
      res.status(500).json({
        error: 'Failed to fetch templates',
        message: error.message
      });
    }
  }
);

export default router;
