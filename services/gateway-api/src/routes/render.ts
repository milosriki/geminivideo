/**
 * Render routes - Proxy to video-agent service
 */
import { Router, Request, Response } from 'express';
import axios from 'axios';
import { config } from '../config';
import { logger } from '../logger';

export const renderRouter = Router();

// Create remix job
renderRouter.post('/remix', async (req: Request, res: Response) => {
  try {
    const response = await axios.post(
      `${config.videoAgentUrl}/render/remix`,
      req.body
    );
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to create remix job', { error: error.message });
    res.status(500).json({ error: error.message });
  }
});

// Get job status
renderRouter.get('/jobs/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    
    // Validate ID to prevent URL injection
    if (!/^[a-zA-Z0-9_-]+$/.test(id)) {
      return res.status(400).json({ error: 'Invalid job ID format' });
    }
    
    const response = await axios.get(
      `${config.videoAgentUrl}/render/jobs/${id}`
    );
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to get job status', { error: error.message });
    res.status(500).json({ error: error.message });
  }
});

// List jobs
renderRouter.get('/jobs', async (req: Request, res: Response) => {
  try {
    const response = await axios.get(
      `${config.videoAgentUrl}/render/jobs`,
      { params: req.query }
    );
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to list jobs', { error: error.message });
    res.status(500).json({ error: error.message });
  }
});
