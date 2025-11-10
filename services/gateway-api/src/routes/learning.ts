/**
 * Learning routes - Internal weight updates
 */
import { Router, Request, Response } from 'express';
import { LearningService } from '../services/learning';
import { logger } from '../logger';

export const learningRouter = Router();
const learningService = new LearningService();

// Update weights based on actuals
learningRouter.post('/update', async (req: Request, res: Response) => {
  try {
    const { predictions, actuals } = req.body;
    
    if (!predictions || !actuals) {
      return res.status(400).json({ error: 'predictions and actuals required' });
    }
    
    const result = await learningService.updateWeights(predictions, actuals);
    
    res.json({
      status: 'success',
      result
    });
  } catch (error: any) {
    logger.error('Learning update failed', { error: error.message });
    res.status(500).json({ error: error.message });
  }
});

// Get current weights
learningRouter.get('/weights', async (req: Request, res: Response) => {
  try {
    const weights = await learningService.getCurrentWeights();
    res.json(weights);
  } catch (error: any) {
    logger.error('Failed to get weights', { error: error.message });
    res.status(500).json({ error: error.message });
  }
});
