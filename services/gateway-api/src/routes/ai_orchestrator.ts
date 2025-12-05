import express, { Request, Response } from 'express';
import { AIOrchestrator } from '../services/ai/AIOrchestrator';

const router = express.Router();
const orchestrator = new AIOrchestrator();

// POST /api/ai/generate-creatives
router.post('/generate-creatives', async (req: Request, res: Response) => {
    try {
        const { clientId, objective, budget, targetAudience, historicalData } = req.body;

        if (!clientId || !objective || !budget || !targetAudience) {
            return res.status(400).json({ error: 'Missing required fields' });
        }

        const creatives = await orchestrator.generateOptimizedCreatives({
            clientId,
            objective,
            budget,
            targetAudience,
            historicalData
        });

        res.json({
            status: 'success',
            count: creatives.length,
            creatives
        });
    } catch (error: any) {
        console.error('Error generating creatives:', error);
        res.status(500).json({ error: error.message });
    }
});

// POST /api/ai/ingest-performance
router.post('/ingest-performance', async (req: Request, res: Response) => {
    try {
        const signal = req.body;

        if (!signal.creativeId || !signal.actualROAS) {
            return res.status(400).json({ error: 'Missing required fields' });
        }

        await orchestrator.ingestPerformanceData(signal);

        res.json({ status: 'success', message: 'Performance data ingested' });
    } catch (error: any) {
        console.error('Error ingesting performance data:', error);
        res.status(500).json({ error: error.message });
    }
});

export default router;
