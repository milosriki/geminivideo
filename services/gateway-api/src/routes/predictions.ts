/**
 * Predictions Routes
 * Agent 58 - ML Predictions and CTR forecasting
 *
 * Provides ML-powered predictions:
 * - CTR predictions for creatives
 * - ROAS forecasting
 * - Campaign performance predictions
 * - Confidence intervals
 */

import { Router, Request, Response } from 'express';
import { Pool } from 'pg';
import axios from 'axios';
import { apiRateLimiter, validateInput } from '../middleware/security';

const router = Router();

// Service URLs
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8003';
const TITAN_CORE_URL = process.env.TITAN_CORE_URL || 'http://localhost:8004';

/**
 * Create predictions router with database connection
 */
export function createPredictionsRouter(pgPool: Pool): Router {
  /**
   * POST /api/predictions/ctr
   * Predict CTR for a creative or campaign
   */
  router.post(
    '/ctr',
    apiRateLimiter,
    validateInput({
      body: {
        clip_data: { type: 'object', required: false },
        video_id: { type: 'uuid', required: false },
        clip_ids: { type: 'array', required: false },
        arc_name: { type: 'string', required: false, max: 100 },
        include_confidence: { type: 'boolean', required: false }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { clip_data, video_id, clip_ids, arc_name, include_confidence = true } = req.body;

        console.log(`Predicting CTR: video_id=${video_id}, clip_ids=${clip_ids?.length || 0}`);

        // Forward to ML service
        const mlResponse = await axios.post(
          `${ML_SERVICE_URL}/api/ml/predict-ctr`,
          {
            clip_data: clip_data || {
              video_id,
              clip_ids: clip_ids || [],
              arc_name: arc_name || 'default'
            },
            include_confidence
          },
          { timeout: 30000 }
        );

        const prediction = mlResponse.data;

        // Store prediction in database for tracking
        try {
          const insertQuery = `
            INSERT INTO predictions (
              video_id, predicted_ctr, predicted_roas, confidence_score,
              model_version, created_at
            )
            VALUES ($1, $2, $3, $4, $5, NOW())
          `;

          await pgPool.query(insertQuery, [
            video_id || null,
            prediction.predicted_ctr || 0,
            prediction.predicted_roas || 0,
            prediction.confidence || 0.5,
            prediction.model_version || 'xgboost-v1'
          ]).catch(err => {
            console.warn('Failed to store prediction:', err.message);
          });
        } catch (dbError) {
          // Non-fatal, continue
        }

        res.json({
          status: 'success',
          prediction: {
            predicted_ctr: prediction.predicted_ctr || 0.02,
            predicted_roas: prediction.predicted_roas || 2.0,
            confidence: prediction.confidence || 0.5,
            confidence_interval: prediction.confidence_interval || {
              lower: (prediction.predicted_ctr || 0.02) * 0.8,
              upper: (prediction.predicted_ctr || 0.02) * 1.2
            },
            model_version: prediction.model_version || 'xgboost-v1',
            timestamp: new Date().toISOString()
          }
        });

      } catch (error: any) {
        console.error('Error predicting CTR:', error);

        // Fallback to default predictions if ML service is down
        if (error.code === 'ECONNREFUSED' || error.response?.status === 503) {
          return res.json({
            status: 'success',
            prediction: {
              predicted_ctr: 0.02, // 2% default CTR
              predicted_roas: 2.0,  // 2.0 default ROAS
              confidence: 0.3,
              confidence_interval: {
                lower: 0.015,
                upper: 0.025
              },
              model_version: 'fallback-default',
              timestamp: new Date().toISOString(),
              note: 'ML service unavailable. Using default predictions.'
            }
          });
        }

        res.status(error.response?.status || 500).json({
          error: 'Failed to predict CTR',
          message: error.message,
          details: error.response?.data
        });
      }
    }
  );

  /**
   * POST /api/predictions/roas
   * Predict ROAS for a campaign
   */
  router.post(
    '/roas',
    apiRateLimiter,
    validateInput({
      body: {
        campaign_id: { type: 'uuid', required: false },
        budget: { type: 'number', required: true, min: 1 },
        target_audience: { type: 'object', required: false },
        platform: { type: 'string', required: false, enum: ['meta', 'google', 'tiktok'] }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { campaign_id, budget, target_audience, platform = 'meta' } = req.body;

        console.log(`Predicting ROAS: campaign=${campaign_id}, budget=$${budget}, platform=${platform}`);

        // Forward to ML service
        const mlResponse = await axios.post(
          `${ML_SERVICE_URL}/api/ml/predict-roas`,
          {
            campaign_id,
            budget,
            target_audience,
            platform
          },
          { timeout: 30000 }
        );

        res.json(mlResponse.data);

      } catch (error: any) {
        console.error('Error predicting ROAS:', error);

        // Fallback
        if (error.code === 'ECONNREFUSED' || error.response?.status === 503) {
          const { budget } = req.body;
          return res.json({
            status: 'success',
            prediction: {
              predicted_roas: 2.0,
              predicted_revenue: budget * 2.0,
              predicted_conversions: Math.floor(budget / 50), // Assume $50 CPA
              confidence: 0.3,
              model_version: 'fallback-default',
              note: 'ML service unavailable. Using default predictions.'
            }
          });
        }

        res.status(error.response?.status || 500).json({
          error: 'Failed to predict ROAS',
          message: error.message,
          details: error.response?.data
        });
      }
    }
  );

  /**
   * POST /api/predictions/campaign
   * Comprehensive campaign performance prediction
   */
  router.post(
    '/campaign',
    apiRateLimiter,
    validateInput({
      body: {
        campaign_data: { type: 'object', required: true },
        prediction_days: { type: 'number', required: false, min: 1, max: 365 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { campaign_data, prediction_days = 30 } = req.body;

        console.log(`Predicting campaign performance: ${prediction_days} days`);

        // Forward to Titan Core Oracle for comprehensive predictions
        const oracleResponse = await axios.post(
          `${TITAN_CORE_URL}/oracle/predict`,
          {
            campaign_data,
            prediction_type: 'all',
            timeframe_days: prediction_days
          },
          { timeout: 45000 }
        );

        res.json({
          status: 'success',
          predictions: oracleResponse.data,
          prediction_days,
          timestamp: new Date().toISOString()
        });

      } catch (error: any) {
        console.error('Error predicting campaign performance:', error);
        res.status(error.response?.status || 500).json({
          error: 'Failed to predict campaign performance',
          message: error.message,
          details: error.response?.data
        });
      }
    }
  );

  /**
   * GET /api/predictions/accuracy
   * Get prediction accuracy metrics
   */
  router.get(
    '/accuracy',
    apiRateLimiter,
    validateInput({
      query: {
        start_date: { type: 'string', required: false },
        end_date: { type: 'string', required: false },
        metric: { type: 'string', required: false, enum: ['ctr', 'roas', 'conversions', 'all'] }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { start_date, end_date, metric = 'all' } = req.query;

        console.log(`Fetching prediction accuracy: metric=${metric}`);

        // Query predictions vs actuals
        const query = `
          SELECT
            p.video_id,
            p.predicted_ctr,
            p.predicted_roas,
            p.created_at as prediction_date,
            COALESCE(AVG(pm.ctr), 0) as actual_ctr,
            COALESCE(SUM(pm.conversions) * 50 / NULLIF(SUM(pm.spend), 0), 0) as actual_roas
          FROM predictions p
          LEFT JOIN performance_metrics pm ON p.video_id = pm.video_id
          WHERE 1=1
          ${start_date ? `AND p.created_at >= '${start_date}'` : ''}
          ${end_date ? `AND p.created_at <= '${end_date}'` : ''}
          GROUP BY p.video_id, p.predicted_ctr, p.predicted_roas, p.created_at
          HAVING SUM(pm.impressions) > 100
          ORDER BY p.created_at DESC
          LIMIT 100
        `;

        const result = await pgPool.query(query);

        // Calculate accuracy metrics
        let ctrMae = 0;
        let roasMae = 0;
        let validCtrCount = 0;
        let validRoasCount = 0;

        const comparisons = result.rows.map(row => {
          const predictedCtr = parseFloat(row.predicted_ctr);
          const actualCtr = parseFloat(row.actual_ctr);
          const predictedRoas = parseFloat(row.predicted_roas);
          const actualRoas = parseFloat(row.actual_roas);

          const ctrError = Math.abs(predictedCtr - actualCtr);
          const roasError = Math.abs(predictedRoas - actualRoas);

          if (actualCtr > 0) {
            ctrMae += ctrError;
            validCtrCount++;
          }

          if (actualRoas > 0) {
            roasMae += roasError;
            validRoasCount++;
          }

          return {
            video_id: row.video_id,
            prediction_date: row.prediction_date,
            predicted: {
              ctr: predictedCtr,
              roas: predictedRoas
            },
            actual: {
              ctr: actualCtr,
              roas: actualRoas
            },
            errors: {
              ctr: ctrError,
              roas: roasError,
              ctr_percentage: actualCtr > 0 ? (ctrError / actualCtr) * 100 : 0,
              roas_percentage: actualRoas > 0 ? (roasError / actualRoas) * 100 : 0
            }
          };
        });

        res.json({
          status: 'success',
          overall_accuracy: {
            ctr_mae: validCtrCount > 0 ? ctrMae / validCtrCount : 0,
            roas_mae: validRoasCount > 0 ? roasMae / validRoasCount : 0,
            total_predictions: comparisons.length,
            valid_ctr_predictions: validCtrCount,
            valid_roas_predictions: validRoasCount
          },
          comparisons: metric === 'all' ? comparisons.slice(0, 20) : comparisons.slice(0, 20)
        });

      } catch (error: any) {
        console.error('Error fetching prediction accuracy:', error);
        res.status(500).json({
          error: 'Failed to fetch prediction accuracy',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/predictions/batch
   * Batch predict CTR for multiple creatives
   */
  router.post(
    '/batch',
    apiRateLimiter,
    validateInput({
      body: {
        creatives: { type: 'array', required: true, min: 1, max: 50 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { creatives } = req.body;

        console.log(`Batch predicting CTR for ${creatives.length} creatives`);

        // Forward to ML service
        const mlResponse = await axios.post(
          `${ML_SERVICE_URL}/api/ml/predict-ctr-batch`,
          { creatives },
          { timeout: 60000 } // 60 second timeout for batch
        );

        res.json(mlResponse.data);

      } catch (error: any) {
        console.error('Error batch predicting:', error);

        // Fallback: return default predictions for each creative
        if (error.code === 'ECONNREFUSED' || error.response?.status === 503) {
          const { creatives } = req.body;
          return res.json({
            status: 'success',
            predictions: creatives.map((creative: any, idx: number) => ({
              creative_id: creative.id || idx,
              predicted_ctr: 0.02,
              predicted_roas: 2.0,
              confidence: 0.3,
              model_version: 'fallback-default'
            })),
            note: 'ML service unavailable. Using default predictions.'
          });
        }

        res.status(error.response?.status || 500).json({
          error: 'Failed to batch predict',
          message: error.message,
          details: error.response?.data
        });
      }
    }
  );

  /**
   * GET /api/predictions/:id
   * Get a single prediction by ID
   */
  router.get(
    '/:id',
    apiRateLimiter,
    validateInput({ params: { id: { type: 'uuid', required: true } } }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;
        const result = await pgPool.query(
          'SELECT * FROM predictions WHERE id = $1',
          [id]
        );
        if (result.rows.length === 0) {
          return res.status(404).json({ error: 'Prediction not found' });
        }
        res.json({ success: true, data: result.rows[0] });
      } catch (error: any) {
        console.error(`Error fetching prediction ${req.params.id}: ${error.message}`);
        res.status(500).json({ error: error.message });
      }
    }
  );

  /**
   * DELETE /api/predictions/:id
   * Delete a prediction by ID
   */
  router.delete(
    '/:id',
    apiRateLimiter,
    validateInput({ params: { id: { type: 'uuid', required: true } } }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;
        const result = await pgPool.query(
          'DELETE FROM predictions WHERE id = $1 RETURNING id',
          [id]
        );
        if (result.rows.length === 0) {
          return res.status(404).json({ error: 'Prediction not found' });
        }
        res.json({ success: true, message: 'Prediction deleted' });
      } catch (error: any) {
        console.error(`Error deleting prediction ${req.params.id}: ${error.message}`);
        res.status(500).json({ error: error.message });
      }
    }
  );

  /**
   * GET /api/predictions/history
   * Get prediction history with optional filters
   */
  router.get(
    '/history',
    apiRateLimiter,
    validateInput({
      query: {
        campaign_id: { type: 'uuid', required: false },
        days: { type: 'number', required: false, min: 1, max: 365 },
        limit: { type: 'number', required: false, min: 1, max: 100 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { campaign_id, days = 30, limit = 50 } = req.query;
        let query = `
        SELECT * FROM predictions
        WHERE created_at > NOW() - INTERVAL '${days} days'
      `;
        const params: any[] = [];

        if (campaign_id) {
          params.push(campaign_id);
          query += ` AND campaign_id = $${params.length}`;
        }

        query += ` ORDER BY created_at DESC LIMIT ${limit}`;

        const result = await pgPool.query(query, params);
        res.json({ success: true, data: result.rows });
      } catch (error: any) {
        console.error(`Error fetching prediction history: ${error.message}`);
        res.status(500).json({ error: error.message });
      }
    }
  );

  return router;
}

export default createPredictionsRouter;
