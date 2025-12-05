/**
 * Download & Render Job Management API Routes
 *
 * Provides endpoints for:
 * - Downloading rendered video files
 * - Listing all render jobs
 * - Getting job metadata
 */

import { Router, Request, Response } from 'express';
import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';

const router = Router();

// Video Agent service URL
const VIDEO_AGENT_URL = process.env.VIDEO_AGENT_URL || 'http://localhost:8002';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface RenderJob {
  id: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  progress?: number;
  output_path?: string;
  error?: string;
  created_at?: string;
  updated_at?: string;
  request?: any;
}

interface JobMetadata {
  job_id: string;
  status: string;
  output_path?: string;
  file_size?: number;
  duration?: number;
  format?: string;
  created_at?: string;
  updated_at?: string;
}

// ============================================================================
// DOWNLOAD ENDPOINT
// ============================================================================

/**
 * GET /api/render/download/:jobId
 * Download rendered video file
 *
 * Returns the rendered video file as a stream with proper headers
 */
router.get('/api/render/download/:jobId', async (req: Request, res: Response) => {
  try {
    const { jobId } = req.params;

    console.log(`📥 Download request for job: ${jobId}`);

    // First, check job status to verify it's completed
    let jobStatus: RenderJob;
    try {
      const statusResponse = await axios.get<RenderJob>(
        `${VIDEO_AGENT_URL}/render/status/${jobId}`,
        {
          timeout: 10000
        }
      );
      jobStatus = statusResponse.data;
    } catch (statusError: any) {
      if (statusError.response?.status === 404) {
        return res.status(404).json({
          error: 'Render job not found',
          job_id: jobId,
          message: 'No render job exists with this ID'
        });
      }
      throw statusError;
    }

    // Check if job is completed
    if (jobStatus.status !== 'COMPLETED') {
      return res.status(400).json({
        error: 'Video not ready',
        job_id: jobId,
        status: jobStatus.status,
        progress: jobStatus.progress || 0,
        message: jobStatus.status === 'FAILED'
          ? 'Render job failed'
          : 'Video is still being rendered. Please try again later.'
      });
    }

    // Check if output_path exists
    if (!jobStatus.output_path) {
      return res.status(500).json({
        error: 'Output path not found',
        job_id: jobId,
        message: 'Render completed but output path is missing'
      });
    }

    // Try to stream the file from video-agent's download endpoint first
    try {
      console.log(`🎬 Proxying download to video-agent for job: ${jobId}`);

      const videoResponse = await axios.get(
        `${VIDEO_AGENT_URL}/render/${jobId}/download`,
        {
          responseType: 'stream',
          timeout: 30000
        }
      );

      // Forward headers from video-agent
      if (videoResponse.headers['content-type']) {
        res.setHeader('Content-Type', videoResponse.headers['content-type']);
      } else {
        res.setHeader('Content-Type', 'video/mp4');
      }

      if (videoResponse.headers['content-length']) {
        res.setHeader('Content-Length', videoResponse.headers['content-length']);
      }

      res.setHeader('Content-Disposition', `attachment; filename="video_${jobId}.mp4"`);
      res.setHeader('Cache-Control', 'public, max-age=86400'); // Cache for 24 hours

      // Pipe the video stream to response
      videoResponse.data.pipe(res);

      console.log(`✅ Download started for job: ${jobId}`);

    } catch (proxyError: any) {
      // If video-agent doesn't have download endpoint, fall back to direct file access
      if (proxyError.response?.status === 404 || proxyError.code === 'ECONNREFUSED') {
        console.log(`⚠️ Video-agent download endpoint not available, trying direct file access`);

        // Try to access file directly (for local development)
        const outputPath = jobStatus.output_path;

        if (!fs.existsSync(outputPath)) {
          return res.status(404).json({
            error: 'Video file not found',
            job_id: jobId,
            output_path: outputPath,
            message: 'Render completed but video file is missing from filesystem'
          });
        }

        // Get file stats
        const stats = fs.statSync(outputPath);
        const fileSize = stats.size;

        // Set headers
        res.setHeader('Content-Type', 'video/mp4');
        res.setHeader('Content-Length', fileSize);
        res.setHeader('Content-Disposition', `attachment; filename="video_${jobId}.mp4"`);
        res.setHeader('Cache-Control', 'public, max-age=86400');

        // Stream file
        const fileStream = fs.createReadStream(outputPath);
        fileStream.pipe(res);

        console.log(`✅ Download started (direct file access) for job: ${jobId}`);

        fileStream.on('error', (error) => {
          console.error(`Error streaming file for job ${jobId}:`, error);
          if (!res.headersSent) {
            res.status(500).json({
              error: 'Error streaming video file',
              job_id: jobId
            });
          }
        });
      } else {
        throw proxyError;
      }
    }

  } catch (error: any) {
    console.error('Error handling download request:', error.message);

    if (error.code === 'ECONNREFUSED') {
      return res.status(503).json({
        error: 'Video Agent service unavailable',
        details: 'Unable to connect to video rendering service'
      });
    }

    // Only send error response if headers haven't been sent yet
    if (!res.headersSent) {
      res.status(error.response?.status || 500).json({
        error: error.message || 'Failed to download video',
        job_id: req.params.jobId,
        details: error.response?.data || {}
      });
    }
  }
});

// ============================================================================
// JOB LISTING ENDPOINT
// ============================================================================

/**
 * GET /api/render/jobs
 * List all render jobs
 *
 * Query parameters:
 * - status: Filter by status (PENDING, PROCESSING, COMPLETED, FAILED)
 * - limit: Maximum number of jobs to return (default: 50)
 * - offset: Pagination offset (default: 0)
 */
router.get('/api/render/jobs', async (req: Request, res: Response) => {
  try {
    const { status, limit = '50', offset = '0' } = req.query;

    console.log(`📋 Listing render jobs (status: ${status || 'all'}, limit: ${limit}, offset: ${offset})`);

    // Try to proxy to video-agent jobs endpoint
    try {
      const response = await axios.get(
        `${VIDEO_AGENT_URL}/render/jobs`,
        {
          params: { status, limit, offset },
          timeout: 15000
        }
      );

      console.log(`✅ Retrieved ${response.data.jobs?.length || 0} render jobs`);

      res.json(response.data);

    } catch (proxyError: any) {
      // If endpoint doesn't exist on video-agent, return empty list
      if (proxyError.response?.status === 404 || proxyError.code === 'ECONNREFUSED') {
        console.log(`⚠️ Video-agent jobs endpoint not available, returning empty list`);

        return res.json({
          jobs: [],
          total: 0,
          limit: parseInt(limit as string),
          offset: parseInt(offset as string),
          message: 'Video Agent jobs endpoint not available'
        });
      }

      throw proxyError;
    }

  } catch (error: any) {
    console.error('Error listing render jobs:', error.message);

    if (error.code === 'ECONNREFUSED') {
      return res.status(503).json({
        error: 'Video Agent service unavailable',
        details: 'Unable to connect to video rendering service'
      });
    }

    res.status(error.response?.status || 500).json({
      error: error.message || 'Failed to list render jobs',
      details: error.response?.data || {}
    });
  }
});

// ============================================================================
// JOB METADATA ENDPOINT
// ============================================================================

/**
 * GET /api/render/job/:jobId/metadata
 * Get job metadata without downloading the video
 *
 * Returns job status, file size, duration, and other metadata
 */
router.get('/api/render/job/:jobId/metadata', async (req: Request, res: Response) => {
  try {
    const { jobId } = req.params;

    console.log(`📊 Fetching metadata for job: ${jobId}`);

    // Get job status from video-agent
    let jobStatus: RenderJob;
    try {
      const statusResponse = await axios.get<RenderJob>(
        `${VIDEO_AGENT_URL}/render/status/${jobId}`,
        {
          timeout: 10000
        }
      );
      jobStatus = statusResponse.data;
    } catch (statusError: any) {
      if (statusError.response?.status === 404) {
        return res.status(404).json({
          error: 'Render job not found',
          job_id: jobId,
          message: 'No render job exists with this ID'
        });
      }
      throw statusError;
    }

    // Build metadata response
    const metadata: JobMetadata = {
      job_id: jobId,
      status: jobStatus.status,
      output_path: jobStatus.output_path,
      created_at: jobStatus.created_at,
      updated_at: jobStatus.updated_at
    };

    // If job is completed and output path exists, get file metadata
    if (jobStatus.status === 'COMPLETED' && jobStatus.output_path) {
      try {
        // Try to get file stats if file is accessible
        if (fs.existsSync(jobStatus.output_path)) {
          const stats = fs.statSync(jobStatus.output_path);
          metadata.file_size = stats.size;

          // Try to get video duration using ffprobe (if available)
          // This is optional and can be added later
          metadata.format = 'mp4';
        }
      } catch (fileError) {
        console.warn(`Could not access file for job ${jobId}:`, fileError);
        // Continue without file metadata
      }
    }

    console.log(`✅ Metadata retrieved for job: ${jobId} (status: ${metadata.status})`);

    res.json(metadata);

  } catch (error: any) {
    console.error('Error fetching job metadata:', error.message);

    if (error.code === 'ECONNREFUSED') {
      return res.status(503).json({
        error: 'Video Agent service unavailable',
        details: 'Unable to connect to video rendering service'
      });
    }

    res.status(error.response?.status || 500).json({
      error: error.message || 'Failed to fetch job metadata',
      job_id: req.params.jobId,
      details: error.response?.data || {}
    });
  }
});

// ============================================================================
// EXPORT
// ============================================================================

export default router;
