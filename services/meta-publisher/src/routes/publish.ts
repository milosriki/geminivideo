/**
 * Publishing routes - Upload and create ads on Meta
 */
import { Router, Request, Response } from 'express';
import { MetaService } from '../services/meta';
import { logger } from '../logger';

export const publishRouter = Router();
const metaService = new MetaService();

// Publish to Meta
publishRouter.post('/meta', async (req: Request, res: Response) => {
  try {
    const {
      videoUrl,
      fileHash,
      placements,
      campaign,
      adSetId,
      pageId
    } = req.body;

    if (!videoUrl && !fileHash) {
      return res.status(400).json({ error: 'videoUrl or fileHash required' });
    }

    if (!pageId) {
      return res.status(400).json({ error: 'pageId required' });
    }

    // Create ad
    const result = await metaService.publishAd({
      videoUrl,
      fileHash,
      placements: placements || ['feed', 'story'],
      campaign,
      adSetId,
      pageId
    });

    res.json(result);
  } catch (error: any) {
    logger.error('Publishing failed', { error: error.message });
    res.status(500).json({ error: error.message });
  }
});

// Upload video
publishRouter.post('/upload', async (req: Request, res: Response) => {
  try {
    const { videoPath } = req.body;

    if (!videoPath) {
      return res.status(400).json({ error: 'videoPath required' });
    }

    const result = await metaService.uploadVideo(videoPath);
    res.json(result);
  } catch (error: any) {
    logger.error('Upload failed', { error: error.message });
    res.status(500).json({ error: error.message });
  }
});
