/**
 * Alert System Routes with WebSocket Support
 * Agent 16 - Real-Time Performance Alerts
 *
 * Provides API routes for alert management and real-time WebSocket notifications
 */

import { Router, Request, Response } from 'express';
import { Pool } from 'pg';
import axios from 'axios';
import WebSocket from 'ws';
import { logger } from '../logger';
import { apiRateLimiter, validateInput } from '../middleware/security';

const router = Router();

// ML Service URL (from environment)
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8003';

// WebSocket server for real-time alerts
let wss: WebSocket.Server | null = null;

/**
 * Initialize WebSocket server for real-time alert notifications
 */
export function initializeAlertWebSocket(server: any) {
  wss = new WebSocket.Server({
    server,
    path: '/ws/alerts'
  });

  wss.on('connection', (ws: WebSocket, req: any) => {
    const clientIp = req.socket.remoteAddress;
    logger.info(`Alert WebSocket client connected: ${clientIp}`);

    // Send initial connection confirmation
    ws.send(JSON.stringify({
      type: 'connected',
      message: 'Alert notification channel connected',
      timestamp: new Date().toISOString()
    }));

    // Handle client messages (e.g., subscribe to specific campaigns)
    ws.on('message', (message: string) => {
      try {
        const data = JSON.parse(message.toString());
        logger.info(`WebSocket message from client: ${JSON.stringify(data)}`);

        // Handle subscription requests
        if (data.type === 'subscribe') {
          ws.send(JSON.stringify({
            type: 'subscribed',
            campaign_id: data.campaign_id,
            message: 'Subscribed to campaign alerts'
          }));
        }
      } catch (error) {
        logger.error(`Error parsing WebSocket message: ${error}`);
      }
    });

    ws.on('close', () => {
      logger.info(`Alert WebSocket client disconnected: ${clientIp}`);
    });

    ws.on('error', (error) => {
      logger.error(`Alert WebSocket error: ${error}`);
    });
  });

  logger.info('Alert WebSocket server initialized on /ws/alerts');
}

/**
 * Broadcast alert to all connected WebSocket clients
 */
export function broadcastAlert(alert: any) {
  if (!wss) {
    logger.warn('WebSocket server not initialized');
    return;
  }

  const message = JSON.stringify({
    type: 'alert',
    data: alert,
    timestamp: new Date().toISOString()
  });

  let sentCount = 0;
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(message);
      sentCount++;
    }
  });

  logger.info(`Alert broadcast to ${sentCount} WebSocket clients`);
}

/**
 * Create alerts router with database pool
 */
export function createAlertsRouter(pgPool: Pool): Router {

// ============================================================
// ALERT RULE MANAGEMENT
// ============================================================

/**
 * Create or update an alert rule
 * POST /api/alerts/rules
 */
router.post(
  '/rules',
  apiRateLimiter,
  validateInput({
    body: {
      rule_name: { type: 'string', required: true, max: 100 },
      campaign_id: { type: 'uuid', required: true },
      metric_name: { type: 'string', required: true },
      threshold: { type: 'number', required: true }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    logger.info(`Creating alert rule: ${req.body.rule_id}`);

    const response = await axios.post(`${ML_SERVICE_URL}/api/alerts/rules`, req.body);

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error creating alert rule: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to create alert rule',
      details: error.message
    });
  }
  }
);

/**
 * Get all alert rules
 * GET /api/alerts/rules
 */
router.get('/rules', apiRateLimiter, async (req: Request, res: Response) => {
  try {
    const enabledOnly = req.query.enabled_only === 'true';

    const response = await axios.get(`${ML_SERVICE_URL}/api/alerts/rules`, {
      params: { enabled_only: enabledOnly }
    });

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error getting alert rules: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to get alert rules',
      details: error.message
    });
  }
});

/**
 * Get a specific alert rule
 * GET /api/alerts/rules/:ruleId
 */
router.get(
  '/rules/:ruleId',
  apiRateLimiter,
  validateInput({
    params: {
      ruleId: { type: 'uuid', required: true }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    const { ruleId } = req.params;

    const response = await axios.get(`${ML_SERVICE_URL}/api/alerts/rules/${ruleId}`);

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error getting alert rule: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to get alert rule',
      details: error.message
    });
  }
  }
);

/**
 * Delete an alert rule
 * DELETE /api/alerts/rules/:ruleId
 */
router.delete(
  '/rules/:ruleId',
  apiRateLimiter,
  validateInput({
    params: {
      ruleId: { type: 'uuid', required: true }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    const { ruleId } = req.params;

    const response = await axios.delete(`${ML_SERVICE_URL}/api/alerts/rules/${ruleId}`);

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error deleting alert rule: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to delete alert rule',
      details: error.message
    });
  }
  }
);

/**
 * Enable an alert rule
 * PUT /api/alerts/rules/:ruleId/enable
 */
router.put(
  '/rules/:ruleId/enable',
  apiRateLimiter,
  validateInput({
    params: {
      ruleId: { type: 'uuid', required: true }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    const { ruleId } = req.params;

    const response = await axios.put(`${ML_SERVICE_URL}/api/alerts/rules/${ruleId}/enable`);

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error enabling alert rule: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to enable alert rule',
      details: error.message
    });
  }
  }
);

/**
 * Disable an alert rule
 * PUT /api/alerts/rules/:ruleId/disable
 */
router.put(
  '/rules/:ruleId/disable',
  apiRateLimiter,
  validateInput({
    params: {
      ruleId: { type: 'uuid', required: true }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    const { ruleId } = req.params;

    const response = await axios.put(`${ML_SERVICE_URL}/api/alerts/rules/${ruleId}/disable`);

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error disabling alert rule: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to disable alert rule',
      details: error.message
    });
  }
  }
);

// ============================================================
// ALERT MONITORING & TRIGGERING
// ============================================================

/**
 * Check a metric against alert rules
 * POST /api/alerts/check
 *
 * This is the core endpoint for real-time alert monitoring
 */
router.post(
  '/check',
  apiRateLimiter,
  validateInput({
    body: {
      campaign_id: { type: 'uuid', required: true },
      metric_name: { type: 'string', required: true },
      metric_value: { type: 'number', required: true }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    logger.info(`Checking metric: ${req.body.metric_name} for campaign ${req.body.campaign_id}`);

    const response = await axios.post(`${ML_SERVICE_URL}/api/alerts/check`, req.body);

    // If alerts were triggered, broadcast to WebSocket clients
    if (response.data.alerts_triggered > 0) {
      response.data.alerts.forEach((alert: any) => {
        broadcastAlert(alert);
      });
    }

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error checking metric: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to check metric',
      details: error.message
    });
  }
  }
);

/**
 * Get active alerts
 * GET /api/alerts
 */
router.get('/', apiRateLimiter, async (req: Request, res: Response) => {
  try {
    const { campaign_id, alert_type, severity, limit } = req.query;

    const response = await axios.get(`${ML_SERVICE_URL}/api/alerts`, {
      params: {
        campaign_id,
        alert_type,
        severity,
        limit: limit || 100
      }
    });

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error getting active alerts: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to get active alerts',
      details: error.message
    });
  }
});

/**
 * Get alert history
 * GET /api/alerts/history
 */
router.get('/history', apiRateLimiter, async (req: Request, res: Response) => {
  try {
    const { campaign_id, days_back, limit } = req.query;

    const response = await axios.get(`${ML_SERVICE_URL}/api/alerts/history`, {
      params: {
        campaign_id,
        days_back: days_back || 7,
        limit: limit || 100
      }
    });

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error getting alert history: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to get alert history',
      details: error.message
    });
  }
});

/**
 * Get alert statistics
 * GET /api/alerts/stats
 */
router.get('/stats', apiRateLimiter, async (req: Request, res: Response) => {
  try {
    const { campaign_id } = req.query;

    const response = await axios.get(`${ML_SERVICE_URL}/api/alerts/stats`, {
      params: { campaign_id }
    });

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error getting alert stats: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to get alert stats',
      details: error.message
    });
  }
});

/**
 * Get a specific alert
 * GET /api/alerts/:alertId
 */
router.get(
  '/:alertId',
  apiRateLimiter,
  validateInput({
    params: {
      alertId: { type: 'uuid', required: true }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    const { alertId } = req.params;

    const response = await axios.get(`${ML_SERVICE_URL}/api/alerts/${alertId}`);

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error getting alert: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to get alert',
      details: error.message
    });
  }
  }
);

/**
 * Acknowledge an alert
 * PUT /api/alerts/:alertId/acknowledge
 */
router.put(
  '/:alertId/acknowledge',
  apiRateLimiter,
  validateInput({
    params: {
      alertId: { type: 'uuid', required: true }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    const { alertId } = req.params;
    const { user_id } = req.body;

    const response = await axios.put(
      `${ML_SERVICE_URL}/api/alerts/${alertId}/acknowledge`,
      { user_id }
    );

    // Broadcast acknowledgment to WebSocket clients
    broadcastAlert({
      type: 'alert_acknowledged',
      alert_id: alertId,
      user_id,
      timestamp: new Date().toISOString()
    });

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error acknowledging alert: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to acknowledge alert',
      details: error.message
    });
  }
  }
);

/**
 * Resolve an alert
 * PUT /api/alerts/:alertId/resolve
 */
router.put(
  '/:alertId/resolve',
  apiRateLimiter,
  validateInput({
    params: {
      alertId: { type: 'uuid', required: true }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    const { alertId } = req.params;

    const response = await axios.put(`${ML_SERVICE_URL}/api/alerts/${alertId}/resolve`);

    // Broadcast resolution to WebSocket clients
    broadcastAlert({
      type: 'alert_resolved',
      alert_id: alertId,
      timestamp: new Date().toISOString()
    });

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error resolving alert: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to resolve alert',
      details: error.message
    });
  }
  }
);

/**
 * Send a test alert notification
 * POST /api/alerts/test
 */
router.post(
  '/test',
  apiRateLimiter,
  validateInput({
    body: {
      channel: { type: 'string', required: false, enum: ['slack', 'email', 'webhook'] }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    const { channel } = req.body;

    const response = await axios.post(`${ML_SERVICE_URL}/api/alerts/test`, null, {
      params: { channel: channel || 'slack' }
    });

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error sending test notification: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to send test notification',
      details: error.message
    });
  }
  }
);

// ============================================================
// CONVENIENCE ENDPOINTS FOR SPECIFIC METRICS
// ============================================================

/**
 * Check ROAS metric
 * POST /api/alerts/check/roas
 */
router.post(
  '/check/roas',
  apiRateLimiter,
  validateInput({
    body: {
      campaign_id: { type: 'uuid', required: true },
      campaign_name: { type: 'string', required: false },
      roas: { type: 'number', required: true },
      context: { type: 'object', required: false }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    const { campaign_id, campaign_name, roas, context } = req.body;

    const response = await axios.post(`${ML_SERVICE_URL}/api/alerts/check`, {
      metric_name: 'roas',
      metric_value: roas,
      campaign_id,
      campaign_name,
      context,
      alert_types: ['roas_drop']
    });

    // Broadcast alerts if triggered
    if (response.data.alerts_triggered > 0) {
      response.data.alerts.forEach((alert: any) => {
        broadcastAlert(alert);
      });
    }

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error checking ROAS: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to check ROAS',
      details: error.message
    });
  }
  }
);

/**
 * Check budget metric
 * POST /api/alerts/check/budget
 */
router.post(
  '/check/budget',
  apiRateLimiter,
  validateInput({
    body: {
      campaign_id: { type: 'uuid', required: true },
      campaign_name: { type: 'string', required: false },
      budget_spent_pct: { type: 'number', required: true },
      context: { type: 'object', required: false }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    const { campaign_id, campaign_name, budget_spent_pct, context } = req.body;

    const response = await axios.post(`${ML_SERVICE_URL}/api/alerts/check`, {
      metric_name: 'budget_spent_pct',
      metric_value: budget_spent_pct,
      campaign_id,
      campaign_name,
      context,
      alert_types: ['budget_warning', 'budget_depleted']
    });

    // Broadcast alerts if triggered
    if (response.data.alerts_triggered > 0) {
      response.data.alerts.forEach((alert: any) => {
        broadcastAlert(alert);
      });
    }

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error checking budget: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to check budget',
      details: error.message
    });
  }
  }
);

/**
 * Check CTR metric
 * POST /api/alerts/check/ctr
 */
router.post(
  '/check/ctr',
  apiRateLimiter,
  validateInput({
    body: {
      campaign_id: { type: 'uuid', required: true },
      campaign_name: { type: 'string', required: false },
      ctr_drop_pct: { type: 'number', required: true },
      context: { type: 'object', required: false }
    }
  }),
  async (req: Request, res: Response) => {
  try {
    const { campaign_id, campaign_name, ctr_drop_pct, context } = req.body;

    const response = await axios.post(`${ML_SERVICE_URL}/api/alerts/check`, {
      metric_name: 'ctr_drop_pct',
      metric_value: ctr_drop_pct,
      campaign_id,
      campaign_name,
      context,
      alert_types: ['ctr_anomaly']
    });

    // Broadcast alerts if triggered
    if (response.data.alerts_triggered > 0) {
      response.data.alerts.forEach((alert: any) => {
        broadcastAlert(alert);
      });
    }

    res.json(response.data);
  } catch (error: any) {
    logger.error(`Error checking CTR: ${error.message}`);
    res.status(error.response?.status || 500).json({
      error: 'Failed to check CTR',
      details: error.message
    });
  }
  }
);

/**
 * Update an alert
 * PUT /api/alerts/:alertId
 */
router.put(
  '/:alertId',
  apiRateLimiter,
  validateInput({
    params: { alertId: { type: 'uuid', required: true } },
    body: {
      severity: { type: 'string', required: false },
      message: { type: 'string', required: false, max: 500 }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const { alertId } = req.params;
      const { severity, message } = req.body;

      const result = await pgPool.query(
        `UPDATE alerts
         SET severity = COALESCE($1, severity),
             message = COALESCE($2, message),
             updated_at = NOW()
         WHERE id = $3
         RETURNING *`,
        [severity, message, alertId]
      );

      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Alert not found' });
      }
      res.json({ success: true, data: result.rows[0] });
    } catch (error: any) {
      console.error(`Error updating alert ${req.params.alertId}: ${error.message}`);
      res.status(500).json({ error: error.message });
    }
  }
);

/**
 * Delete an alert
 * DELETE /api/alerts/:alertId
 */
router.delete(
  '/:alertId',
  apiRateLimiter,
  validateInput({ params: { alertId: { type: 'uuid', required: true } } }),
  async (req: Request, res: Response) => {
    try {
      const { alertId } = req.params;
      const result = await pgPool.query(
        'DELETE FROM alerts WHERE id = $1 RETURNING id',
        [alertId]
      );
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Alert not found' });
      }
      res.json({ success: true, message: 'Alert deleted' });
    } catch (error: any) {
      console.error(`Error deleting alert ${req.params.alertId}: ${error.message}`);
      res.status(500).json({ error: error.message });
    }
  }
);

  return router;
}

export default createAlertsRouter;
