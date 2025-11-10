/**
 * Assets routes - Proxy to drive-intel service
 */
import { Router, Request, Response } from 'express';
import axios from 'axios';
import { config } from '../config';
import { logger } from '../logger';

export const assetsRouter = Router();

// Get all assets
assetsRouter.get('/', async (req: Request, res: Response) => {
  try {
    const response = await axios.get(`${config.driveIntelUrl}/assets`);
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to get assets', { error: error.message });
    res.status(500).json({ error: error.message });
  }
});

// Get asset clips
assetsRouter.get('/:id/clips', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const { ranked, top } = req.query;
    
    const response = await axios.get(
      `${config.driveIntelUrl}/assets/${id}/clips`,
      { params: { ranked, top } }
    );
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to get clips', { error: error.message });
    res.status(500).json({ error: error.message });
  }
});

// Search clips
assetsRouter.post('/search/clips', async (req: Request, res: Response) => {
  try {
    const response = await axios.post(
      `${config.driveIntelUrl}/search/clips`,
      req.body
    );
    res.json(response.data);
  } catch (error: any) {
    logger.error('Search failed', { error: error.message });
    res.status(500).json({ error: error.message });
  }
});

// Ingest from Drive
assetsRouter.post('/ingest/drive', async (req: Request, res: Response) => {
  try {
    const response = await axios.post(
      `${config.driveIntelUrl}/ingest/drive/folder`,
      req.body
    );
    res.json(response.data);
  } catch (error: any) {
    logger.error('Drive ingestion failed', { error: error.message });
    res.status(500).json({ error: error.message });
  }
});

// Ingest from local
assetsRouter.post('/ingest/local', async (req: Request, res: Response) => {
  try {
    const response = await axios.post(
      `${config.driveIntelUrl}/ingest/local/folder`,
      req.body
    );
    res.json(response.data);
  } catch (error: any) {
    logger.error('Local ingestion failed', { error: error.message });
    res.status(500).json({ error: error.message });
  }
});
