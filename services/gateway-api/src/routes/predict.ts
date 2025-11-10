/**
 * Prediction routes - AI scoring and predictions
 */
import { Router, Request, Response } from 'express';
import { PredictionService } from '../services/prediction';
import { ReliabilityLogger } from '../services/reliability';
import { logger } from '../logger';

export const predictRouter = Router();
const predictionService = new PredictionService();
const reliabilityLogger = new ReliabilityLogger();

// Get prediction for storyboard
predictRouter.post('/score', async (req: Request, res: Response) => {
  try {
    const { clips, context } = req.body;
    
    if (!clips || !Array.isArray(clips)) {
      return res.status(400).json({ error: 'Clips array required' });
    }
    
    // Calculate prediction scores
    const prediction = await predictionService.predict(clips, context || {});
    
    // Log for reliability tracking
    await reliabilityLogger.log({
      creativeId: context?.creativeId || 'unknown',
      prediction,
      timestamp: new Date().toISOString(),
      features: { clips: clips.length, context }
    });
    
    res.json(prediction);
  } catch (error: any) {
    logger.error('Prediction failed', { error: error.message });
    res.status(500).json({ error: error.message });
  }
});

// Get reliability stats
predictRouter.get('/reliability', async (req: Request, res: Response) => {
  try {
    const stats = await reliabilityLogger.getStats();
    res.json(stats);
  } catch (error: any) {
    logger.error('Failed to get reliability stats', { error: error.message });
    res.status(500).json({ error: error.message });
  }
});
