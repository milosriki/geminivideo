import { Router, Request, Response } from 'express';
import { Storage } from '@google-cloud/storage';
import { v4 as uuidv4 } from 'uuid';
import {
  KnowledgeUploadRequest,
  KnowledgeUploadResponse,
  KnowledgeActivateRequest,
  KnowledgeActivateResponse,
  KnowledgeStatusResponse,
  KnowledgeFile
} from './types';

const router = Router();

// Initialize GCS client - can be mocked for local development
// TODO: [CRITICAL] Ensure GCS_MOCK_MODE is false in production
// Real GCS bucket credentials must be configured in .env
const storage = process.env.GCS_MOCK_MODE === 'true'
  ? null
  : new Storage({
    projectId: process.env.PROJECT_ID || 'gen-lang-client-0427673522'
  });

const BUCKET_NAME = process.env.GCS_BUCKET || 'ai-studio-bucket-208288753973-us-west1';

// In-memory store for development/testing (replace with database in production)
const knowledgeRegistry: Map<string, any> = new Map();

/**
 * POST /knowledge/upload
 * Upload knowledge content to GCS bucket
 */
router.post('/upload', async (req: Request, res: Response) => {
  try {
    const file = (req as any).file; // multer middleware would populate this
    const body: KnowledgeUploadRequest = req.body;

    if (!file && !req.body.mock) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const uploadId = uuidv4();
    const timestamp = new Date().toISOString();
    
    // SECURITY FIX: Sanitize filename to prevent path traversal
    function sanitizeGcsPath(userPath: string): string {
        // Remove any path traversal attempts
        const normalized = path.normalize(userPath);
        
        // Remove any .. or . components
        const parts = normalized.split(path.sep).filter(part => 
            part !== '..' && part !== '.' && part !== ''
        );
        
        // Generate safe filename
        const safeFilename = parts[parts.length - 1];
        const sanitized = safeFilename.replace(/[^a-zA-Z0-9._-]/g, '_');
        
        // Add hash to prevent collisions
        const hash = crypto.createHash('sha256')
            .update(userPath + Date.now().toString())
            .digest('hex')
            .substring(0, 8);
        
        return `${sanitized}_${hash}`;
    }
    
    const rawFileName = file?.originalname || 'mock-file.json';
    const safeFileName = sanitizeGcsPath(rawFileName);
    const gcsPath = `gs://${BUCKET_NAME}/knowledge/${body.category}/${body.subcategory}/${safeFileName}`;

    // Upload to GCS if not in mock mode
    if (storage && file) {
      const bucket = storage.bucket(BUCKET_NAME);
      const blob = bucket.file(`knowledge/${body.category}/${body.subcategory}/${safeFileName}`);

      await blob.save(file.buffer, {
        metadata: {
          contentType: file.mimetype,
          metadata: {
            uploadId,
            ...body.metadata
          }
        }
      });
    }

    // Store in registry
    knowledgeRegistry.set(uploadId, {
      uploadId,
      category: body.category,
      subcategory: body.subcategory,
      gcsPath,
      metadata: body.metadata,
      timestamp,
      status: 'uploaded'
    });

    const response: KnowledgeUploadResponse = {
      upload_id: uploadId,
      gcs_path: gcsPath,
      status: 'uploaded',
      timestamp
    };

    res.json(response);
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ error: 'Upload failed', details: (error as Error).message });
  }
});

/**
 * POST /knowledge/activate
 * Activate a knowledge version for hot-reload
 */
router.post('/activate', async (req: Request, res: Response) => {
  try {
    const body: KnowledgeActivateRequest = req.body;

    if (!body.upload_id || !body.category) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const uploadRecord = knowledgeRegistry.get(body.upload_id);
    if (!uploadRecord) {
      return res.status(404).json({ error: 'Upload not found' });
    }

    const activatedAt = new Date().toISOString();
    const version = uploadRecord.metadata.version || '1.0.0';

    // Update registry
    uploadRecord.status = 'active';
    uploadRecord.activatedAt = activatedAt;
    knowledgeRegistry.set(body.upload_id, uploadRecord);

    // In production, publish to Pub/Sub for hot-reload notification
    const affectedServices = ['drive-intel', 'video-agent', 'meta-publisher'];

    const response: KnowledgeActivateResponse = {
      status: 'active',
      version,
      activated_at: activatedAt,
      affected_services: affectedServices
    };

    res.json(response);
  } catch (error) {
    console.error('Activation error:', error);
    res.status(500).json({ error: 'Activation failed', details: (error as Error).message });
  }
});

/**
 * GET /knowledge/status
 * Get current knowledge status for a category
 */
router.get('/status', async (req: Request, res: Response) => {
  try {
    const category = req.query.category as string;

    if (!category) {
      return res.status(400).json({ error: 'Category parameter required' });
    }

    // Find active versions for this category
    const activeFiles: KnowledgeFile[] = [];
    let lastUpdated = '';
    let activeVersion = '0.0.0';

    for (const [_, record] of knowledgeRegistry) {
      if (record.category === category && record.status === 'active') {
        activeFiles.push({
          name: record.gcsPath.split('/').pop(),
          gcs_path: record.gcsPath,
          size_bytes: record.size || 0,
          checksum: record.checksum || 'sha256:mock'
        });

        if (record.activatedAt > lastUpdated) {
          lastUpdated = record.activatedAt;
          activeVersion = record.metadata.version;
        }
      }
    }

    const response: KnowledgeStatusResponse = {
      category,
      active_version: activeVersion || '0.0.0',
      last_updated: lastUpdated || new Date().toISOString(),
      files: activeFiles
    };

    res.json(response);
  } catch (error) {
    console.error('Status check error:', error);
    res.status(500).json({ error: 'Status check failed', details: (error as Error).message });
  }
});

export default router;
