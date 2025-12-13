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

// Initialize GCS client with production safety checks
// GCS_MOCK_MODE should ONLY be 'true' in local development
// In production, this MUST be 'false' or undefined
const GCS_MOCK_MODE = process.env.GCS_MOCK_MODE === 'true';
const NODE_ENV = process.env.NODE_ENV || 'development';
const IS_PRODUCTION = NODE_ENV === 'production';

// CRITICAL: Validate GCS configuration in production
if (IS_PRODUCTION && GCS_MOCK_MODE) {
  const errorMsg = '[CRITICAL] GCS_MOCK_MODE is enabled in production environment. This is not allowed. Set GCS_MOCK_MODE=false or remove it from environment variables.';
  console.error(errorMsg);
  throw new Error(errorMsg);
}

// Warn if mock mode is enabled in non-production
if (GCS_MOCK_MODE && !IS_PRODUCTION) {
  console.warn('[WARNING] GCS_MOCK_MODE is enabled. Using mock storage for local development. This should NEVER happen in production.');
}

// Initialize Google Cloud Storage client
// In production: GCS_MOCK_MODE must be false, and real credentials must be configured
// In development: GCS_MOCK_MODE can be true for testing without GCS access
const storage = GCS_MOCK_MODE
  ? null
  : new Storage({
    projectId: process.env.PROJECT_ID || 'gen-lang-client-0427673522'
  });

const BUCKET_NAME = process.env.GCS_BUCKET || 'ai-studio-bucket-208288753973-us-west1';

// Validate GCS configuration in production
if (IS_PRODUCTION) {
  if (!storage) {
    throw new Error('[CRITICAL] Google Cloud Storage is not initialized in production. Check GCS_MOCK_MODE and credentials.');
  }
  if (!process.env.PROJECT_ID) {
    console.warn('[WARNING] PROJECT_ID environment variable is not set. Using default project ID.');
  }
  if (!process.env.GCS_BUCKET) {
    console.warn('[WARNING] GCS_BUCKET environment variable is not set. Using default bucket name.');
  }
  console.log('[INFO] Google Cloud Storage initialized successfully for production', {
    projectId: process.env.PROJECT_ID || 'default',
    bucket: BUCKET_NAME
  });
}

// In-memory store for development/testing (replace with database in production)
const knowledgeRegistry: Map<string, any> = new Map();

/**
 * Sanitize GCS path to prevent path traversal attacks
 * @param filename - The filename to sanitize
 * @returns Sanitized filename safe for GCS storage
 */
function sanitizeGcsPath(filename: string): string {
  if (!filename || typeof filename !== 'string') {
    return 'sanitized-file';
  }
  
  // Split by path separators and filter out dangerous parts
  const parts = filename
    .split(/[\/\\]/)
    .filter(part => part !== '..' && part !== '.' && part.length > 0);
  
  // If all parts were filtered out, return a safe default
  if (parts.length === 0) {
    return 'sanitized-file';
  }
  
  // Take only the last part (filename) and sanitize it
  const safeName = parts[parts.length - 1]
    .replace(/[^a-zA-Z0-9._-]/g, '_') // Replace unsafe characters
    .substring(0, 255); // Limit length
  
  return safeName || 'sanitized-file';
}

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
    const rawFileName = file?.originalname || 'mock-file.json';
    const fileName = sanitizeGcsPath(rawFileName);
    
    // Also sanitize category and subcategory to prevent path traversal
    const sanitizedCategory = sanitizeGcsPath(body.category);
    const sanitizedSubcategory = sanitizeGcsPath(body.subcategory);
    
    const gcsPath = `gs://${BUCKET_NAME}/knowledge/${sanitizedCategory}/${sanitizedSubcategory}/${fileName}`;

    // Upload to GCS if not in mock mode
    if (storage && file) {
      const bucket = storage.bucket(BUCKET_NAME);
      const blob = bucket.file(`knowledge/${sanitizedCategory}/${sanitizedSubcategory}/${fileName}`);

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
      category: sanitizedCategory,
      subcategory: sanitizedSubcategory,
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