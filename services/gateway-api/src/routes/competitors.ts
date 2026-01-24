import { Router, Request, Response } from 'express';
import { Pool } from 'pg';
import { CompetitorService } from '../services/competitor-service';
import { apiRateLimiter, validateInput } from '../middleware/security';

export function createCompetitorRouter(pgPool: Pool): Router {
  const router = Router();
  const competitorService = new CompetitorService(pgPool);

  // Get all competitors
  router.get('/', apiRateLimiter, async (req: Request, res: Response) => {
    try {
      const competitors = await competitorService.getCompetitors();
      res.json({ status: 'success', competitors });
    } catch (error: any) {
      res.status(500).json({ error: 'Failed to fetch competitors', message: error.message });
    }
  });

  // Add a competitor
  router.post('/', 
    apiRateLimiter,
    validateInput({
      body: {
        brandName: { type: 'string', required: true, min: 2 },
        websiteUrl: { type: 'string', required: true, min: 5 },
        industry: { type: 'string', required: false }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { brandName, websiteUrl, industry } = req.body;
        const competitor = await competitorService.addCompetitor(brandName, websiteUrl, industry);
        res.status(201).json({ status: 'success', competitor });
      } catch (error: any) {
        res.status(500).json({ error: 'Failed to add competitor', message: error.message });
      }
    }
  );

  // Get competitor ads
  router.get('/:id/ads', apiRateLimiter, async (req: Request, res: Response) => {
    try {
      const ads = await competitorService.getCompetitorAds(req.params.id);
      res.json({ status: 'success', ads });
    } catch (error: any) {
      res.status(500).json({ error: 'Failed to fetch ads', message: error.message });
    }
  });

  // Get trending ads (global)
  router.get('/trending', apiRateLimiter, async (req: Request, res: Response) => {
    try {
      const ads = await competitorService.getTrendingAds();
      res.json({ status: 'success', ads });
    } catch (error: any) {
      res.status(500).json({ error: 'Failed to fetch trending ads', message: error.message });
    }
  });

  return router;
}
