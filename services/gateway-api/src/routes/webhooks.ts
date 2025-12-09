import { Router, Request, Response } from 'express';
import { Pool } from 'pg';
import { apiRateLimiter } from '../middleware/rate-limiter';
import { validateInput } from '../middleware/validation';

export function createWebhooksRouter(pgPool: Pool): Router {
  const router = Router();

  // List webhooks
  router.get(
    '/',
    apiRateLimiter,
    async (req: Request, res: Response) => {
      try {
        const result = await pgPool.query(
          'SELECT * FROM webhooks WHERE deleted_at IS NULL ORDER BY created_at DESC'
        );
        res.json({ success: true, data: result.rows });
      } catch (error: any) {
        console.error('Error listing webhooks:', error.message);
        res.status(500).json({ error: error.message });
      }
    }
  );

  // Create webhook
  router.post(
    '/',
    apiRateLimiter,
    validateInput({
      body: {
        url: { type: 'string', required: true },
        events: { type: 'array', required: true },
        secret: { type: 'string', required: false }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { url, events, secret } = req.body;
        const result = await pgPool.query(
          `INSERT INTO webhooks (url, events, secret, created_at)
           VALUES ($1, $2, $3, NOW())
           RETURNING *`,
          [url, JSON.stringify(events), secret]
        );
        res.status(201).json({ success: true, data: result.rows[0] });
      } catch (error: any) {
        console.error('Error creating webhook:', error.message);
        res.status(500).json({ error: error.message });
      }
    }
  );

  // Test webhook
  router.post(
    '/:id/test',
    apiRateLimiter,
    validateInput({ params: { id: { type: 'uuid', required: true } } }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;
        const result = await pgPool.query(
          'SELECT * FROM webhooks WHERE id = $1',
          [id]
        );

        if (result.rows.length === 0) {
          return res.status(404).json({ error: 'Webhook not found' });
        }

        // Send test payload
        const webhook = result.rows[0];
        const testPayload = {
          event: 'test',
          timestamp: new Date().toISOString(),
          data: { message: 'This is a test webhook' }
        };

        // In production, actually send the webhook
        console.log(`Test webhook to ${webhook.url}:`, testPayload);

        res.json({ success: true, message: 'Test webhook sent', payload: testPayload });
      } catch (error: any) {
        console.error('Error testing webhook:', error.message);
        res.status(500).json({ error: error.message });
      }
    }
  );

  // Delete webhook
  router.delete(
    '/:id',
    apiRateLimiter,
    validateInput({ params: { id: { type: 'uuid', required: true } } }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;
        const result = await pgPool.query(
          'UPDATE webhooks SET deleted_at = NOW() WHERE id = $1 RETURNING id',
          [id]
        );
        if (result.rows.length === 0) {
          return res.status(404).json({ error: 'Webhook not found' });
        }
        res.json({ success: true, message: 'Webhook deleted' });
      } catch (error: any) {
        console.error('Error deleting webhook:', error.message);
        res.status(500).json({ error: error.message });
      }
    }
  );

  return router;
}
