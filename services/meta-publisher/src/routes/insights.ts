/**
 * Insights routes - Fetch ad metrics from Meta
 */
import { Router, Request, Response } from 'express';
import { MetaService } from '../services/meta';
import { logger } from '../logger';

export const insightsRouter = Router();
const metaService = new MetaService();

// Get insights for an ad
insightsRouter.get('/', async (req: Request, res: Response) => {
  try {
    const { adId, datePreset } = req.query;

    if (!adId) {
      return res.status(400).json({ error: 'adId required' });
    }

    const result = await metaService.getInsights(
      adId as string,
      (datePreset as string) || 'last_7d'
    );

    res.json(result);
  } catch (error: any) {
    logger.error('Insights fetch failed', { error: error.message });
    res.status(500).json({ error: error.message });
  }
});
