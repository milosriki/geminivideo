/**
 * Image Generation API Routes
 * Agent 37: AI Image Generation (FLUX/SDXL/DALL-E 3/Imagen 3)
 *
 * Endpoints for generating AI images for ad creatives using:
 * - FLUX.1 Pro/Dev/Schnell
 * - DALL-E 3
 * - Imagen 3
 * - SDXL Turbo
 */

import { Router, Request, Response } from 'express';
import { httpClient } from "../index";
import { Pool } from 'pg';
import { v4 as uuidv4 } from 'uuid';

// Import security middleware
import {
  apiRateLimiter,
  uploadRateLimiter,
  validateInput
} from '../middleware/security';

export function createImageGenerationRouter(pgPool: Pool): Router {
  const router = Router();

  // Service URL for Python image generator
  const VIDEO_AGENT_URL = process.env.VIDEO_AGENT_URL || 'http://localhost:8002';

  /**
   * POST /api/image/generate
   * Generate image from text prompt
   */
  router.post('/generate',
    uploadRateLimiter,
    validateInput({
      body: {
        prompt: { type: 'string', required: true, min: 10, max: 2000, sanitize: true },
        provider: {
          type: 'string',
          required: false,
          enum: ['flux_pro', 'flux_dev', 'flux_schnell', 'dalle3', 'imagen3', 'sdxl_turbo']
        },
        aspect_ratio: {
          type: 'string',
          required: false,
          enum: ['1:1', '4:5', '9:16', '16:9', '4:3']
        },
        style: {
          type: 'string',
          required: false,
          enum: ['photorealistic', 'cinematic', 'minimal', 'vibrant', 'lifestyle', 'product', 'dramatic', 'natural']
        },
        quality: { type: 'string', required: false, enum: ['low', 'medium', 'high'] },
        num_images: { type: 'number', required: false, min: 1, max: 4 },
        negative_prompt: { type: 'string', required: false, max: 1000, sanitize: true }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const {
          prompt,
          provider = 'flux_dev',
          aspect_ratio = '1:1',
          style = 'photorealistic',
          quality = 'high',
          num_images = 1,
          negative_prompt
        } = req.body;

        console.log(`[Image Gen] Generating image: provider=${provider}, aspect=${aspect_ratio}`);

        // Forward to Python image generator service
        const response = await axios.post(`${VIDEO_AGENT_URL}/api/image/generate`, {
          prompt,
          config: {
            provider,
            aspect_ratio,
            style,
            quality,
            num_images,
            negative_prompt
          }
        }, {
          timeout: 120000 // 2 minute timeout for image generation
        });

        // Log generation to database
        const generationId = uuidv4();
        await pgPool.query(`
          INSERT INTO image_generations (
            generation_id, prompt, provider, aspect_ratio,
            style, quality, image_path, cost_estimate, generation_time
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        `, [
          generationId,
          prompt,
          provider,
          aspect_ratio,
          style,
          quality,
          response.data.image_path,
          response.data.cost_estimate || 0.0,
          response.data.generation_time || 0.0
        ]).catch(err => {
          console.warn('[Image Gen] Failed to log generation:', err.message);
        });

        res.status(201).json({
          status: 'success',
          generation_id: generationId,
          image_path: response.data.image_path,
          provider,
          cost_estimate: response.data.cost_estimate,
          generation_time: response.data.generation_time,
          metadata: response.data.metadata
        });

      } catch (error: any) {
        console.error('[Image Gen] Generation error:', error.message);
        res.status(error.response?.status || 500).json({
          error: 'Image generation failed',
          message: error.message,
          details: error.response?.data
        });
      }
    }
  );

  /**
   * POST /api/image/product-shot
   * Generate professional product photography
   */
  router.post('/product-shot',
    uploadRateLimiter,
    validateInput({
      body: {
        product_desc: { type: 'string', required: true, min: 10, max: 500, sanitize: true },
        style: { type: 'string', required: false, max: 200, sanitize: true },
        background: { type: 'string', required: false, max: 100, sanitize: true },
        provider: { type: 'string', required: false },
        aspect_ratio: { type: 'string', required: false }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const {
          product_desc,
          style = 'clean product photography',
          background = 'white',
          provider = 'flux_pro',
          aspect_ratio = '1:1'
        } = req.body;

        console.log(`[Product Shot] Generating: ${product_desc.substring(0, 50)}...`);

        const response = await axios.post(`${VIDEO_AGENT_URL}/api/image/product-shot`, {
          product_desc,
          style,
          background,
          config: {
            provider,
            aspect_ratio,
            style: 'product',
            quality: 'high'
          }
        }, {
          timeout: 120000
        });

        // Log to database
        const generationId = uuidv4();
        await pgPool.query(`
          INSERT INTO image_generations (
            generation_id, prompt, provider, aspect_ratio,
            style, quality, image_path, cost_estimate, generation_time,
            generation_type
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        `, [
          generationId,
          `Product: ${product_desc}`,
          provider,
          aspect_ratio,
          'product',
          'high',
          response.data.image_path,
          response.data.cost_estimate || 0.0,
          response.data.generation_time || 0.0,
          'product_shot'
        ]).catch(err => console.warn('DB log failed:', err.message));

        res.status(201).json({
          status: 'success',
          generation_id: generationId,
          image_path: response.data.image_path,
          product_desc,
          cost_estimate: response.data.cost_estimate,
          generation_time: response.data.generation_time
        });

      } catch (error: any) {
        console.error('[Product Shot] Error:', error.message);
        res.status(error.response?.status || 500).json({
          error: 'Product shot generation failed',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/image/lifestyle
   * Generate lifestyle/context scenes
   */
  router.post('/lifestyle',
    uploadRateLimiter,
    validateInput({
      body: {
        scene_desc: { type: 'string', required: true, min: 10, max: 500, sanitize: true },
        brand_style: { type: 'string', required: false, max: 200, sanitize: true },
        provider: { type: 'string', required: false },
        aspect_ratio: { type: 'string', required: false }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const {
          scene_desc,
          brand_style = 'modern and aspirational',
          provider = 'flux_dev',
          aspect_ratio = '4:5'
        } = req.body;

        console.log(`[Lifestyle] Generating: ${scene_desc.substring(0, 50)}...`);

        const response = await axios.post(`${VIDEO_AGENT_URL}/api/image/lifestyle`, {
          scene_desc,
          brand_style,
          config: {
            provider,
            aspect_ratio,
            style: 'lifestyle',
            quality: 'high'
          }
        }, {
          timeout: 120000
        });

        const generationId = uuidv4();
        await pgPool.query(`
          INSERT INTO image_generations (
            generation_id, prompt, provider, aspect_ratio,
            style, quality, image_path, cost_estimate, generation_time,
            generation_type
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        `, [
          generationId,
          `Lifestyle: ${scene_desc}`,
          provider,
          aspect_ratio,
          'lifestyle',
          'high',
          response.data.image_path,
          response.data.cost_estimate || 0.0,
          response.data.generation_time || 0.0,
          'lifestyle'
        ]).catch(err => console.warn('DB log failed:', err.message));

        res.status(201).json({
          status: 'success',
          generation_id: generationId,
          image_path: response.data.image_path,
          scene_desc,
          cost_estimate: response.data.cost_estimate,
          generation_time: response.data.generation_time
        });

      } catch (error: any) {
        console.error('[Lifestyle] Error:', error.message);
        res.status(error.response?.status || 500).json({
          error: 'Lifestyle image generation failed',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/image/thumbnail
   * Generate video thumbnail optimized for platform
   */
  router.post('/thumbnail',
    uploadRateLimiter,
    validateInput({
      body: {
        video_summary: { type: 'string', required: true, min: 10, max: 500, sanitize: true },
        style: { type: 'string', required: false, max: 100, sanitize: true },
        platform: {
          type: 'string',
          required: false,
          enum: ['instagram', 'youtube', 'tiktok', 'facebook']
        }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const {
          video_summary,
          style = 'attention-grabbing',
          platform = 'instagram'
        } = req.body;

        console.log(`[Thumbnail] Generating for ${platform}: ${video_summary.substring(0, 50)}...`);

        const response = await axios.post(`${VIDEO_AGENT_URL}/api/image/thumbnail`, {
          video_summary,
          style,
          platform
        }, {
          timeout: 60000 // Faster for thumbnails
        });

        const generationId = uuidv4();
        await pgPool.query(`
          INSERT INTO image_generations (
            generation_id, prompt, provider, aspect_ratio,
            style, quality, image_path, cost_estimate, generation_time,
            generation_type, platform
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        `, [
          generationId,
          `Thumbnail: ${video_summary}`,
          'flux_schnell',
          response.data.aspect_ratio || '1:1',
          'vibrant',
          'medium',
          response.data.image_path,
          response.data.cost_estimate || 0.0,
          response.data.generation_time || 0.0,
          'thumbnail',
          platform
        ]).catch(err => console.warn('DB log failed:', err.message));

        res.status(201).json({
          status: 'success',
          generation_id: generationId,
          image_path: response.data.image_path,
          platform,
          cost_estimate: response.data.cost_estimate,
          generation_time: response.data.generation_time
        });

      } catch (error: any) {
        console.error('[Thumbnail] Error:', error.message);
        res.status(error.response?.status || 500).json({
          error: 'Thumbnail generation failed',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/image/extend
   * Outpaint/extend image for different aspect ratios
   */
  router.post('/extend',
    uploadRateLimiter,
    validateInput({
      body: {
        image_path: { type: 'string', required: true, min: 1, max: 1000 },
        direction: {
          type: 'string',
          required: true,
          enum: ['up', 'down', 'left', 'right', 'all']
        },
        target_aspect_ratio: {
          type: 'string',
          required: true,
          enum: ['1:1', '4:5', '9:16', '16:9', '4:3']
        }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { image_path, direction, target_aspect_ratio } = req.body;

        console.log(`[Extend] Extending ${image_path} to ${target_aspect_ratio}`);

        const response = await axios.post(`${VIDEO_AGENT_URL}/api/image/extend`, {
          image_path,
          direction,
          target_aspect_ratio
        }, {
          timeout: 180000 // 3 minutes for outpainting
        });

        res.status(201).json({
          status: 'success',
          original_path: image_path,
          extended_path: response.data.image_path,
          direction,
          target_aspect_ratio,
          cost_estimate: response.data.cost_estimate,
          generation_time: response.data.generation_time
        });

      } catch (error: any) {
        console.error('[Extend] Error:', error.message);
        res.status(error.response?.status || 500).json({
          error: 'Image extension failed',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/image/batch-variants
   * Generate multiple variants for A/B testing
   */
  router.post('/batch-variants',
    uploadRateLimiter,
    validateInput({
      body: {
        base_prompt: { type: 'string', required: true, min: 10, max: 2000, sanitize: true },
        num_variants: { type: 'number', required: false, min: 2, max: 10 },
        provider: { type: 'string', required: false },
        aspect_ratio: { type: 'string', required: false }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const {
          base_prompt,
          num_variants = 5,
          provider = 'flux_dev',
          aspect_ratio = '1:1'
        } = req.body;

        console.log(`[Batch Variants] Generating ${num_variants} variants`);

        const response = await axios.post(`${VIDEO_AGENT_URL}/api/image/batch-variants`, {
          base_prompt,
          num_variants,
          config: {
            provider,
            aspect_ratio,
            quality: 'high'
          }
        }, {
          timeout: 300000 // 5 minutes for batch generation
        });

        res.status(202).json({
          status: 'accepted',
          message: `Generating ${num_variants} variants`,
          variants: response.data.variants,
          total_cost_estimate: response.data.total_cost_estimate,
          estimated_time: response.data.estimated_time
        });

      } catch (error: any) {
        console.error('[Batch Variants] Error:', error.message);
        res.status(error.response?.status || 500).json({
          error: 'Batch variant generation failed',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/image/platform-batch
   * Generate platform-specific creatives in one call
   */
  router.post('/platform-batch',
    uploadRateLimiter,
    validateInput({
      body: {
        prompt: { type: 'string', required: true, min: 10, max: 2000, sanitize: true },
        platforms: {
          type: 'array',
          required: true,
          min: 1,
          max: 5
        }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { prompt, platforms } = req.body;

        console.log(`[Platform Batch] Generating for: ${platforms.join(', ')}`);

        const response = await axios.post(`${VIDEO_AGENT_URL}/api/image/platform-batch`, {
          prompt,
          platforms
        }, {
          timeout: 300000
        });

        res.status(202).json({
          status: 'accepted',
          message: `Generating images for ${platforms.length} platforms`,
          platforms,
          results: response.data.results,
          total_cost_estimate: response.data.total_cost_estimate
        });

      } catch (error: any) {
        console.error('[Platform Batch] Error:', error.message);
        res.status(error.response?.status || 500).json({
          error: 'Platform batch generation failed',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/image/providers
   * Get available image generation providers
   */
  router.get('/providers',
    apiRateLimiter,
    async (req: Request, res: Response) => {
      try {
        const response = await axios.get(`${VIDEO_AGENT_URL}/api/image/providers`, {
          timeout: 10000
        });

        res.json({
          status: 'success',
          providers: response.data.providers,
          pricing: {
            flux_pro: '$0.055 per image',
            flux_dev: '$0.025 per image',
            flux_schnell: '$0.003 per image',
            dalle3: '$0.040 per image',
            imagen3: '$0.020 per image',
            sdxl_turbo: '$0.002 per image'
          },
          recommendations: {
            product_shots: 'flux_pro',
            lifestyle: 'flux_dev',
            thumbnails: 'flux_schnell',
            creative_concepts: 'dalle3',
            fast_previews: 'sdxl_turbo'
          }
        });

      } catch (error: any) {
        console.error('[Providers] Error:', error.message);
        res.status(500).json({
          error: 'Failed to get providers',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/image/stats
   * Get image generation statistics
   */
  router.get('/stats',
    apiRateLimiter,
    async (req: Request, res: Response) => {
      try {
        // Get stats from database
        const statsQuery = `
          SELECT
            COUNT(*) as total_generations,
            SUM(cost_estimate) as total_cost,
            AVG(generation_time) as avg_generation_time,
            COUNT(DISTINCT provider) as providers_used,
            generation_type,
            COUNT(*) as count_by_type
          FROM image_generations
          WHERE created_at > NOW() - INTERVAL '30 days'
          GROUP BY generation_type
        `;

        const result = await pgPool.query(statsQuery);

        const providerStats = await pgPool.query(`
          SELECT
            provider,
            COUNT(*) as count,
            AVG(generation_time) as avg_time,
            SUM(cost_estimate) as total_cost
          FROM image_generations
          WHERE created_at > NOW() - INTERVAL '30 days'
          GROUP BY provider
          ORDER BY count DESC
        `);

        res.json({
          status: 'success',
          period: 'Last 30 days',
          overall: result.rows[0] || {},
          by_type: result.rows,
          by_provider: providerStats.rows,
          timestamp: new Date().toISOString()
        });

      } catch (error: any) {
        console.error('[Stats] Error:', error.message);
        res.status(500).json({
          error: 'Failed to get stats',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/image/history
   * Get recent image generations
   */
  router.get('/history',
    apiRateLimiter,
    validateInput({
      query: {
        limit: { type: 'number', required: false, min: 1, max: 100 },
        provider: { type: 'string', required: false },
        generation_type: { type: 'string', required: false }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { limit = 20, provider, generation_type } = req.query;

        let query = `
          SELECT
            generation_id,
            prompt,
            provider,
            aspect_ratio,
            style,
            quality,
            image_path,
            cost_estimate,
            generation_time,
            generation_type,
            platform,
            created_at
          FROM image_generations
          WHERE 1=1
        `;

        const params: any[] = [];
        let paramIndex = 1;

        if (provider) {
          query += ` AND provider = $${paramIndex}`;
          params.push(provider);
          paramIndex++;
        }

        if (generation_type) {
          query += ` AND generation_type = $${paramIndex}`;
          params.push(generation_type);
          paramIndex++;
        }

        query += ` ORDER BY created_at DESC LIMIT $${paramIndex}`;
        params.push(limit);

        const result = await pgPool.query(query, params);

        res.json({
          status: 'success',
          count: result.rows.length,
          generations: result.rows
        });

      } catch (error: any) {
        console.error('[History] Error:', error.message);
        res.status(500).json({
          error: 'Failed to get history',
          message: error.message
        });
      }
    }
  );

  return router;
}

export default createImageGenerationRouter;
