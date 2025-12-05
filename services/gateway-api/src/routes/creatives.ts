/**
 * Creatives Management Routes
 * Agent 92 - Creative upload and asset management
 *
 * Provides creative file upload and management:
 * - Upload creative assets (images, videos)
 * - Track asset metadata
 * - Generate thumbnails
 * - Associate with campaigns
 */

import { Router, Request, Response } from 'express';
import { Pool } from 'pg';
import { v4 as uuidv4 } from 'uuid';
import multer from 'multer';
import * as path from 'path';
import * as fs from 'fs';
import axios from 'axios';
import { apiRateLimiter, uploadRateLimiter, validateInput } from '../middleware/security';

const router = Router();

// Service URLs
const TITAN_CORE_URL = process.env.TITAN_CORE_URL || 'http://localhost:8004';
const VIDEO_AGENT_URL = process.env.VIDEO_AGENT_URL || 'http://localhost:8002';

// Configure multer for file uploads
const uploadDir = process.env.UPLOAD_DIR || '/tmp/uploads';

// Ensure upload directory exists
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

// Configure storage
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    // Generate unique filename: timestamp-uuid-originalname
    const uniqueId = uuidv4();
    const timestamp = Date.now();
    const ext = path.extname(file.originalname);
    const basename = path.basename(file.originalname, ext);
    const sanitizedBasename = basename.replace(/[^a-zA-Z0-9_-]/g, '_');

    cb(null, `${timestamp}-${uniqueId}-${sanitizedBasename}${ext}`);
  }
});

// File filter - only allow specific file types
const fileFilter = (req: any, file: Express.Multer.File, cb: multer.FileFilterCallback) => {
  const allowedMimes = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'video/mp4',
    'video/quicktime',
    'video/x-msvideo',
    'video/webm',
    'video/mpeg'
  ];

  if (allowedMimes.includes(file.mimetype)) {
    cb(null, true);
  } else {
    cb(new Error(`Invalid file type: ${file.mimetype}. Allowed: images (JPEG, PNG, GIF, WebP) and videos (MP4, MOV, AVI, WebM, MPEG)`));
  }
};

// Configure multer
const upload = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: 500 * 1024 * 1024, // 500MB max file size
    files: 10 // Max 10 files per upload
  }
});

/**
 * Create creatives router with database connection
 */
export function createCreativesRouter(pgPool: Pool): Router {
  /**
   * POST /api/creatives/upload
   * Handle multipart file upload for creative assets
   */
  router.post(
    '/upload',
    uploadRateLimiter,
    upload.array('files', 10), // Accept up to 10 files
    async (req: Request, res: Response) => {
      try {
        const files = req.files as Express.Multer.File[];

        if (!files || files.length === 0) {
          return res.status(400).json({
            error: 'No files uploaded',
            message: 'Please select at least one file to upload'
          });
        }

        console.log(`Uploading ${files.length} creative file(s)`);

        // Extract metadata from request body
        const {
          campaign_id,
          creative_type = 'video',
          title,
          description,
          tags
        } = req.body;

        const uploadedAssets: any[] = [];

        // Process each uploaded file
        for (const file of files) {
          const assetId = uuidv4();
          const filePath = file.path;
          const fileUrl = `/uploads/${file.filename}`;

          // Determine asset type
          const isVideo = file.mimetype.startsWith('video/');
          const isImage = file.mimetype.startsWith('image/');

          // Extract metadata
          const metadata = {
            originalname: file.originalname,
            mimetype: file.mimetype,
            size: file.size,
            filename: file.filename,
            path: filePath,
            url: fileUrl
          };

          // Insert into database
          const query = `
            INSERT INTO creative_assets (
              id,
              campaign_id,
              type,
              title,
              description,
              file_path,
              file_url,
              file_size,
              mime_type,
              metadata,
              status,
              created_at,
              updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
            RETURNING *
          `;

          const values = [
            assetId,
            campaign_id || null,
            isVideo ? 'video' : isImage ? 'image' : 'other',
            title || file.originalname,
            description || '',
            filePath,
            fileUrl,
            file.size,
            file.mimetype,
            JSON.stringify(metadata),
            'uploaded'
          ];

          try {
            const result = await pgPool.query(query, values);
            const asset = result.rows[0];

            // For videos, trigger thumbnail generation
            if (isVideo) {
              try {
                await axios.post(`${VIDEO_AGENT_URL}/generate-thumbnail`, {
                  asset_id: assetId,
                  video_path: filePath
                }, { timeout: 30000 });
              } catch (thumbError: any) {
                console.warn('Thumbnail generation failed:', thumbError.message);
                // Non-fatal, continue
              }
            }

            uploadedAssets.push({
              id: asset.id,
              campaign_id: asset.campaign_id,
              type: asset.type,
              title: asset.title,
              file_url: asset.file_url,
              file_size: parseInt(asset.file_size),
              mime_type: asset.mime_type,
              status: asset.status,
              created_at: asset.created_at
            });

            console.log(`Asset uploaded successfully: ${assetId} (${file.originalname})`);
          } catch (dbError: any) {
            console.error(`Database error for file ${file.originalname}:`, dbError);
            // Clean up uploaded file on error
            if (fs.existsSync(filePath)) {
              fs.unlinkSync(filePath);
            }
            throw dbError;
          }
        }

        // Return summary
        res.status(201).json({
          status: 'success',
          message: `Successfully uploaded ${uploadedAssets.length} creative asset(s)`,
          assets: uploadedAssets,
          count: uploadedAssets.length,
          upload_summary: {
            total_files: files.length,
            total_size_bytes: files.reduce((sum, f) => sum + f.size, 0),
            total_size_mb: (files.reduce((sum, f) => sum + f.size, 0) / (1024 * 1024)).toFixed(2)
          }
        });

      } catch (error: any) {
        console.error('Error uploading creative assets:', error);

        // Clean up any uploaded files on error
        const files = req.files as Express.Multer.File[];
        if (files) {
          files.forEach(file => {
            if (fs.existsSync(file.path)) {
              try {
                fs.unlinkSync(file.path);
              } catch (cleanupError) {
                console.warn('Failed to cleanup file:', file.path);
              }
            }
          });
        }

        res.status(500).json({
          error: 'Failed to upload creative assets',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/creatives
   * List all creative assets with optional filters
   */
  router.get(
    '/',
    apiRateLimiter,
    validateInput({
      query: {
        campaign_id: { type: 'uuid', required: false },
        type: { type: 'string', required: false, enum: ['image', 'video', 'other'] },
        status: { type: 'string', required: false, enum: ['uploaded', 'processing', 'ready', 'failed'] },
        limit: { type: 'number', required: false, min: 1, max: 100 },
        offset: { type: 'number', required: false, min: 0 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { campaign_id, type, status, limit = 20, offset = 0 } = req.query;

        console.log(`Fetching creative assets: campaign_id=${campaign_id || 'all'}, type=${type || 'all'}`);

        let query = `
          SELECT *
          FROM creative_assets
          WHERE 1=1
        `;

        const values: any[] = [];
        let paramIndex = 1;

        if (campaign_id) {
          query += ` AND campaign_id = $${paramIndex}`;
          values.push(campaign_id);
          paramIndex++;
        }

        if (type) {
          query += ` AND type = $${paramIndex}`;
          values.push(type);
          paramIndex++;
        }

        if (status) {
          query += ` AND status = $${paramIndex}`;
          values.push(status);
          paramIndex++;
        }

        query += `
          ORDER BY created_at DESC
          LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
        `;

        values.push(parseInt(limit as string), parseInt(offset as string));

        const result = await pgPool.query(query, values);

        // Get total count
        let countQuery = 'SELECT COUNT(*) FROM creative_assets WHERE 1=1';
        const countValues: any[] = [];
        let countParamIndex = 1;

        if (campaign_id) {
          countQuery += ` AND campaign_id = $${countParamIndex}`;
          countValues.push(campaign_id);
          countParamIndex++;
        }

        if (type) {
          countQuery += ` AND type = $${countParamIndex}`;
          countValues.push(type);
          countParamIndex++;
        }

        if (status) {
          countQuery += ` AND status = $${countParamIndex}`;
          countValues.push(status);
          countParamIndex++;
        }

        const countResult = await pgPool.query(countQuery, countValues);
        const totalCount = parseInt(countResult.rows[0].count);

        res.json({
          status: 'success',
          assets: result.rows.map(row => ({
            id: row.id,
            campaign_id: row.campaign_id,
            type: row.type,
            title: row.title,
            description: row.description,
            file_url: row.file_url,
            file_size: parseInt(row.file_size),
            mime_type: row.mime_type,
            status: row.status,
            thumbnail_url: row.thumbnail_url,
            created_at: row.created_at,
            updated_at: row.updated_at
          })),
          pagination: {
            total: totalCount,
            limit: parseInt(limit as string),
            offset: parseInt(offset as string),
            has_more: parseInt(offset as string) + result.rows.length < totalCount
          }
        });

      } catch (error: any) {
        console.error('Error fetching creative assets:', error);
        res.status(500).json({
          error: 'Failed to fetch creative assets',
          message: error.message,
          assets: []
        });
      }
    }
  );

  /**
   * GET /api/creatives/:id
   * Get detailed information about a creative asset
   */
  router.get(
    '/:id',
    apiRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;

        console.log(`Fetching creative asset: ${id}`);

        const query = 'SELECT * FROM creative_assets WHERE id = $1';
        const result = await pgPool.query(query, [id]);

        if (result.rows.length === 0) {
          return res.status(404).json({
            error: 'Creative asset not found',
            message: `Creative asset with id ${id} does not exist`
          });
        }

        const asset = result.rows[0];

        res.json({
          status: 'success',
          asset: {
            id: asset.id,
            campaign_id: asset.campaign_id,
            type: asset.type,
            title: asset.title,
            description: asset.description,
            file_path: asset.file_path,
            file_url: asset.file_url,
            file_size: parseInt(asset.file_size),
            mime_type: asset.mime_type,
            metadata: asset.metadata,
            status: asset.status,
            thumbnail_url: asset.thumbnail_url,
            created_at: asset.created_at,
            updated_at: asset.updated_at
          }
        });

      } catch (error: any) {
        console.error('Error fetching creative asset:', error);
        res.status(500).json({
          error: 'Failed to fetch creative asset',
          message: error.message
        });
      }
    }
  );

  /**
   * DELETE /api/creatives/:id
   * Delete a creative asset
   */
  router.delete(
    '/:id',
    apiRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;

        console.log(`Deleting creative asset: ${id}`);

        // Get asset info first
        const selectQuery = 'SELECT * FROM creative_assets WHERE id = $1';
        const selectResult = await pgPool.query(selectQuery, [id]);

        if (selectResult.rows.length === 0) {
          return res.status(404).json({
            error: 'Creative asset not found',
            message: `Creative asset with id ${id} does not exist`
          });
        }

        const asset = selectResult.rows[0];

        // Delete from database
        const deleteQuery = 'DELETE FROM creative_assets WHERE id = $1';
        await pgPool.query(deleteQuery, [id]);

        // Delete physical file
        if (asset.file_path && fs.existsSync(asset.file_path)) {
          try {
            fs.unlinkSync(asset.file_path);
            console.log(`Deleted file: ${asset.file_path}`);
          } catch (fileError: any) {
            console.warn(`Failed to delete file: ${asset.file_path}`, fileError.message);
            // Non-fatal, continue
          }
        }

        // Delete thumbnail if exists
        if (asset.thumbnail_url) {
          const thumbnailPath = path.join(uploadDir, path.basename(asset.thumbnail_url));
          if (fs.existsSync(thumbnailPath)) {
            try {
              fs.unlinkSync(thumbnailPath);
            } catch (thumbError) {
              console.warn('Failed to delete thumbnail:', thumbnailPath);
            }
          }
        }

        console.log(`Creative asset deleted successfully: ${id}`);

        res.json({
          status: 'success',
          message: 'Creative asset deleted successfully',
          asset_id: id
        });

      } catch (error: any) {
        console.error('Error deleting creative asset:', error);
        res.status(500).json({
          error: 'Failed to delete creative asset',
          message: error.message
        });
      }
    }
  );

  return router;
}

export default createCreativesRouter;
