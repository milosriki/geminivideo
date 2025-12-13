/**
 * Pro Video Module Proxy Routes
 * Proxy routes to access all 13 pro video processing modules
 *
 * Provides access to professional video editing features:
 * - Auto Captions
 * - Audio Mixer
 * - Color Grading
 * - Image Generator
 * - Keyframe Engine
 * - Motion Graphics
 * - Preview Generator
 * - Pro Renderer
 * - Smart Crop
 * - Timeline Engine
 * - Transitions Library
 * - Voice Generator
 * - Asset Library
 */

import { Router, Request, Response } from 'express';
import { Pool } from 'pg';
import axios from 'axios';
import { apiRateLimiter, uploadRateLimiter, validateInput } from '../middleware/security';

const router = Router();

// Service URLs
const VIDEO_AGENT_URL = process.env.VIDEO_AGENT_URL || 'http://localhost:8002';

/**
 * Create video proxy router with database connection
 */
export function createVideoProxyRouter(pgPool: Pool): Router {
  
  // ============================================================================
  // AUTO CAPTIONS MODULE
  // ============================================================================
  
  /**
   * POST /api/video-pro/auto-captions/generate
   * Generate auto captions for a video
   */
  router.post(
    '/auto-captions/generate',
    uploadRateLimiter,
    validateInput({
      body: {
        video_url: { type: 'string', required: true, max: 500 },
        language: { type: 'string', required: false, max: 10 },
        style: { type: 'string', required: false, max: 50 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const response = await axios.post(
          `${VIDEO_AGENT_URL}/pro/auto-captions/generate`,
          req.body,
          { timeout: 60000 }
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Auto captions error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  // ============================================================================
  // AUDIO MIXER MODULE
  // ============================================================================
  
  /**
   * POST /api/video-pro/audio-mixer/mix
   * Mix multiple audio tracks
   */
  router.post(
    '/audio-mixer/mix',
    uploadRateLimiter,
    validateInput({
      body: {
        tracks: { type: 'array', required: true },
        output_format: { type: 'string', required: false, max: 10 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const response = await axios.post(
          `${VIDEO_AGENT_URL}/pro/audio-mixer/mix`,
          req.body,
          { timeout: 60000 }
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Audio mixer error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  // ============================================================================
  // COLOR GRADING MODULE
  // ============================================================================
  
  /**
   * POST /api/video-pro/color-grading/apply
   * Apply color grading to video
   */
  router.post(
    '/color-grading/apply',
    uploadRateLimiter,
    validateInput({
      body: {
        video_url: { type: 'string', required: true, max: 500 },
        preset: { type: 'string', required: false, max: 50 },
        lut_url: { type: 'string', required: false, max: 500 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const response = await axios.post(
          `${VIDEO_AGENT_URL}/pro/color-grading/apply`,
          req.body,
          { timeout: 90000 }
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Color grading error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  // ============================================================================
  // IMAGE GENERATOR MODULE
  // ============================================================================
  
  /**
   * POST /api/video-pro/image-generator/generate
   * Generate images for video overlays
   */
  router.post(
    '/image-generator/generate',
    uploadRateLimiter,
    validateInput({
      body: {
        prompt: { type: 'string', required: true, max: 1000, sanitize: true },
        width: { type: 'number', required: false, min: 64, max: 2048 },
        height: { type: 'number', required: false, min: 64, max: 2048 },
        style: { type: 'string', required: false, max: 50 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const response = await axios.post(
          `${VIDEO_AGENT_URL}/pro/image-generator/generate`,
          req.body,
          { timeout: 30000 }
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Image generator error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  // ============================================================================
  // KEYFRAME ENGINE MODULE
  // ============================================================================
  
  /**
   * POST /api/video-pro/keyframe-engine/apply
   * Apply keyframe animations
   */
  router.post(
    '/keyframe-engine/apply',
    uploadRateLimiter,
    validateInput({
      body: {
        video_url: { type: 'string', required: true, max: 500 },
        keyframes: { type: 'array', required: true }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const response = await axios.post(
          `${VIDEO_AGENT_URL}/pro/keyframe-engine/apply`,
          req.body,
          { timeout: 60000 }
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Keyframe engine error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  // ============================================================================
  // MOTION GRAPHICS MODULE
  // ============================================================================
  
  /**
   * POST /api/video-pro/motion-graphics/add
   * Add motion graphics elements
   */
  router.post(
    '/motion-graphics/add',
    uploadRateLimiter,
    validateInput({
      body: {
        video_url: { type: 'string', required: true, max: 500 },
        graphics: { type: 'array', required: true },
        timing: { type: 'object', required: false }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const response = await axios.post(
          `${VIDEO_AGENT_URL}/pro/motion-graphics/add`,
          req.body,
          { timeout: 60000 }
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Motion graphics error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  // ============================================================================
  // PREVIEW GENERATOR MODULE
  // ============================================================================
  
  /**
   * POST /api/video-pro/preview-generator/generate
   * Generate video preview/proxy
   */
  router.post(
    '/preview-generator/generate',
    apiRateLimiter,
    validateInput({
      body: {
        video_url: { type: 'string', required: true, max: 500 },
        quality: { type: 'string', required: false, enum: ['low', 'medium', 'high'] }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const response = await axios.post(
          `${VIDEO_AGENT_URL}/pro/preview-generator/generate`,
          req.body,
          { timeout: 45000 }
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Preview generator error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  // ============================================================================
  // PRO RENDERER MODULE
  // ============================================================================
  
  /**
   * POST /api/video-pro/pro-renderer/render
   * Render final video with all effects
   */
  router.post(
    '/pro-renderer/render',
    uploadRateLimiter,
    validateInput({
      body: {
        timeline: { type: 'object', required: true },
        quality: { type: 'string', required: false, enum: ['draft', 'standard', 'high', 'ultra'] },
        output_format: { type: 'string', required: false, max: 10 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const response = await axios.post(
          `${VIDEO_AGENT_URL}/pro/pro-renderer/render`,
          req.body,
          { timeout: 300000 } // 5 minutes for rendering
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Pro renderer error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  // ============================================================================
  // SMART CROP MODULE
  // ============================================================================
  
  /**
   * POST /api/video-pro/smart-crop/crop
   * Apply AI-powered smart crop for different aspect ratios
   */
  router.post(
    '/smart-crop/crop',
    uploadRateLimiter,
    validateInput({
      body: {
        video_url: { type: 'string', required: true, max: 500 },
        aspect_ratio: { type: 'string', required: true, max: 10 },
        focus_area: { type: 'string', required: false, max: 50 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const response = await axios.post(
          `${VIDEO_AGENT_URL}/pro/smart-crop/crop`,
          req.body,
          { timeout: 60000 }
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Smart crop error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  // ============================================================================
  // TIMELINE ENGINE MODULE
  // ============================================================================
  
  /**
   * POST /api/video-pro/timeline-engine/create
   * Create or update video timeline
   */
  router.post(
    '/timeline-engine/create',
    uploadRateLimiter,
    validateInput({
      body: {
        clips: { type: 'array', required: true },
        transitions: { type: 'array', required: false },
        audio_tracks: { type: 'array', required: false }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const response = await axios.post(
          `${VIDEO_AGENT_URL}/pro/timeline-engine/create`,
          req.body,
          { timeout: 30000 }
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Timeline engine error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  // ============================================================================
  // TRANSITIONS LIBRARY MODULE
  // ============================================================================
  
  /**
   * GET /api/video-pro/transitions-library/list
   * List available transitions
   */
  router.get(
    '/transitions-library/list',
    apiRateLimiter,
    async (req: Request, res: Response) => {
      try {
        const response = await axios.get(
          `${VIDEO_AGENT_URL}/pro/transitions-library/list`,
          { timeout: 10000 }
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Transitions library error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/video-pro/transitions-library/apply
   * Apply transition between clips
   */
  router.post(
    '/transitions-library/apply',
    uploadRateLimiter,
    validateInput({
      body: {
        clip1_url: { type: 'string', required: true, max: 500 },
        clip2_url: { type: 'string', required: true, max: 500 },
        transition_type: { type: 'string', required: true, max: 50 },
        duration: { type: 'number', required: false, min: 0.1, max: 5.0 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const response = await axios.post(
          `${VIDEO_AGENT_URL}/pro/transitions-library/apply`,
          req.body,
          { timeout: 60000 }
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Transitions apply error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  // ============================================================================
  // VOICE GENERATOR MODULE
  // ============================================================================
  
  /**
   * POST /api/video-pro/voice-generator/generate
   * Generate AI voice for video
   */
  router.post(
    '/voice-generator/generate',
    uploadRateLimiter,
    validateInput({
      body: {
        text: { type: 'string', required: true, min: 1, max: 5000, sanitize: true },
        voice_id: { type: 'string', required: false, max: 100 },
        provider: { type: 'string', required: false, enum: ['elevenlabs', 'openai', 'google'] },
        settings: { type: 'object', required: false }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        // Additional validation for text content
        const { text } = req.body;
        
        // Check text length for rate limiting purposes
        if (text.length > 3000) {
          console.warn(`Long text request: ${text.length} characters`);
        }

        const response = await axios.post(
          `${VIDEO_AGENT_URL}/pro/voice-generator/generate`,
          req.body,
          { timeout: 30000 }
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Voice generator error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/video-pro/voice-generator/voices
   * List available voices
   */
  router.get(
    '/voice-generator/voices',
    apiRateLimiter,
    validateInput({
      query: {
        provider: { type: 'string', required: false, enum: ['elevenlabs', 'openai', 'google'] }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const response = await axios.get(
          `${VIDEO_AGENT_URL}/pro/voice-generator/voices`,
          { 
            params: req.query,
            timeout: 10000 
          }
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Voice list error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  // ============================================================================
  // ASSET LIBRARY MODULE
  // ============================================================================
  
  /**
   * GET /api/video-pro/asset-library/search
   * Search for assets (stock footage, music, images)
   */
  router.get(
    '/asset-library/search',
    apiRateLimiter,
    validateInput({
      query: {
        query: { type: 'string', required: false, max: 200, sanitize: true },
        asset_type: { type: 'string', required: false, enum: ['video', 'audio', 'image', 'all'] },
        category: { type: 'string', required: false, max: 50 },
        limit: { type: 'number', required: false, min: 1, max: 100 }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const response = await axios.get(
          `${VIDEO_AGENT_URL}/pro/asset-library/search`,
          { 
            params: req.query,
            timeout: 15000 
          }
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Asset library search error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/video-pro/asset-library/download
   * Download asset from library
   */
  router.post(
    '/asset-library/download',
    uploadRateLimiter,
    validateInput({
      body: {
        asset_id: { type: 'string', required: true, max: 200 },
        asset_type: { type: 'string', required: true, enum: ['video', 'audio', 'image'] }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const response = await axios.post(
          `${VIDEO_AGENT_URL}/pro/asset-library/download`,
          req.body,
          { timeout: 60000 }
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Asset download error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  // ============================================================================
  // GENERAL MODULE STATUS
  // ============================================================================
  
  /**
   * GET /api/video-pro/status
   * Get status of all pro video modules
   */
  router.get(
    '/status',
    apiRateLimiter,
    async (req: Request, res: Response) => {
      try {
        const response = await axios.get(
          `${VIDEO_AGENT_URL}/pro/status`,
          { timeout: 5000 }
        );
        res.json(response.data);
      } catch (error: any) {
        console.error('Pro modules status error:', error.message);
        res.status(error.response?.status || 500).json({
          status: 'error',
          message: 'Pro video modules unavailable',
          details: error.message
        });
      }
    }
  );

  return router;
}

export default createVideoProxyRouter;
