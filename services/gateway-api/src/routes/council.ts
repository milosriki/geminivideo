/**
 * Council of Titans & Analysis API Routes
 *
 * Provides endpoints for:
 * - Council of Titans video scoring and review
 * - Analysis job status tracking and results
 */

import { Router, Request, Response } from 'express';
import axios from 'axios';

const router = Router();

// Titan Core service URL
const TITAN_CORE_URL = process.env.TITAN_CORE_URL || 'http://localhost:8004';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface CouncilScore {
  video_id: string;
  overall_score: number;
  titan_scores: Array<{
    titan_name: string;
    score: number;
    reasoning: string;
    confidence: number;
  }>;
  consensus: string;
  verdict: 'APPROVE' | 'REJECT';
}

interface AnalysisStatus {
  asset_id: string;
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  progress?: number;
  message?: string;
}

interface AnalysisResults {
  asset_id: string;
  status: 'COMPLETED' | 'FAILED';
  results?: {
    scenes?: any[];
    emotions?: any[];
    objects?: any[];
    transcription?: string;
    metadata?: any;
  };
  error?: string;
  completed_at?: string;
}

// In-memory analysis job tracking (replace with Redis/DB in production)
const analysisJobs = new Map<string, AnalysisStatus>();
const analysisResults = new Map<string, AnalysisResults>();

// ============================================================================
// COUNCIL OF TITANS ENDPOINTS
// ============================================================================

/**
 * GET /api/council/score/:videoId
 * Get Council of Titans score for a video
 */
router.get('/score/:videoId', async (req: Request, res: Response) => {
  try {
    const { videoId } = req.params;

    console.log(`Fetching Council score for video: ${videoId}`);

    // Proxy request to titan-core service
    const response = await axios.get<CouncilScore>(
      `${TITAN_CORE_URL}/api/council/score/${videoId}`,
      {
        timeout: 30000 // 30 second timeout
      }
    );

    console.log(`Council score retrieved for video ${videoId}: ${response.data.overall_score}`);

    res.json(response.data);

  } catch (error: any) {
    console.error('Error fetching Council score:', error.message);

    // Handle specific error cases
    if (error.response?.status === 404) {
      return res.status(404).json({
        error: 'Video not found',
        video_id: req.params.videoId
      });
    }

    if (error.code === 'ECONNREFUSED') {
      return res.status(503).json({
        error: 'Titan Core service unavailable',
        details: 'Unable to connect to Council of Titans service'
      });
    }

    res.status(error.response?.status || 500).json({
      error: error.message || 'Failed to fetch Council score',
      details: error.response?.data || {}
    });
  }
});

/**
 * POST /api/council/review
 * Submit a video for Council of Titans review
 *
 * Body:
 * {
 *   video_id: string;
 *   video_url?: string;
 *   asset_id?: string;
 *   metadata?: any;
 * }
 */
router.post('/review', async (req: Request, res: Response) => {
  try {
    const { video_id, video_url, asset_id, metadata } = req.body;

    // Validate required fields
    if (!video_id) {
      return res.status(400).json({
        error: 'Missing required field: video_id'
      });
    }

    console.log(`Submitting video ${video_id} for Council review`);

    // Proxy request to titan-core service
    const response = await axios.post<{
      job_id: string;
      video_id: string;
      status: string;
      message: string;
    }>(
      `${TITAN_CORE_URL}/api/council/review`,
      {
        video_id,
        video_url,
        asset_id,
        metadata
      },
      {
        timeout: 60000 // 60 second timeout for submission
      }
    );

    console.log(`Council review submitted for video ${video_id}: ${response.data.job_id}`);

    // Return 202 Accepted for async processing
    res.status(202).json(response.data);

  } catch (error: any) {
    console.error('Error submitting Council review:', error.message);

    if (error.code === 'ECONNREFUSED') {
      return res.status(503).json({
        error: 'Titan Core service unavailable',
        details: 'Unable to connect to Council of Titans service'
      });
    }

    res.status(error.response?.status || 500).json({
      error: error.message || 'Failed to submit Council review',
      details: error.response?.data || {}
    });
  }
});

// ============================================================================
// ANALYSIS STATUS & RESULTS ENDPOINTS
// ============================================================================

/**
 * GET /api/analysis/status/:analysisId
 * Get the status of an analysis job
 */
router.get('/status/:analysisId', async (req: Request, res: Response) => {
  try {
    const { analysisId } = req.params;

    console.log(`Checking analysis status for: ${analysisId}`);

    // Check in-memory cache first
    if (analysisJobs.has(analysisId)) {
      const status = analysisJobs.get(analysisId)!;
      console.log(`Analysis status found in cache: ${status.status}`);
      return res.json(status);
    }

    // If not in memory, try to get from database or titan-core
    try {
      const response = await axios.get<AnalysisStatus>(
        `${TITAN_CORE_URL}/api/analysis/status/${analysisId}`,
        {
          timeout: 10000
        }
      );

      // Cache the status
      analysisJobs.set(analysisId, response.data);

      console.log(`Analysis status retrieved from Titan Core: ${response.data.status}`);
      return res.json(response.data);

    } catch (proxyError: any) {
      // If titan-core doesn't have it either, check if it's a valid asset_id
      // and return a default QUEUED status
      if (proxyError.response?.status === 404) {
        const defaultStatus: AnalysisStatus = {
          asset_id: analysisId,
          status: 'QUEUED',
          progress: 0,
          message: 'Analysis job queued'
        };

        // Cache for future requests
        analysisJobs.set(analysisId, defaultStatus);

        console.log(`Analysis not found, returning default QUEUED status`);
        return res.json(defaultStatus);
      }

      throw proxyError;
    }

  } catch (error: any) {
    console.error('Error fetching analysis status:', error.message);

    res.status(error.response?.status || 500).json({
      error: error.message || 'Failed to fetch analysis status',
      asset_id: req.params.analysisId
    });
  }
});

/**
 * GET /api/analysis/results/:analysisId
 * Get the results of a completed analysis
 */
router.get('/results/:analysisId', async (req: Request, res: Response) => {
  try {
    const { analysisId } = req.params;

    console.log(`Fetching analysis results for: ${analysisId}`);

    // Check in-memory cache first
    if (analysisResults.has(analysisId)) {
      const results = analysisResults.get(analysisId)!;

      if (results.status === 'COMPLETED') {
        console.log(`Analysis results found in cache`);
        return res.json(results);
      } else if (results.status === 'FAILED') {
        return res.status(400).json(results);
      }
    }

    // Check if analysis is still in progress
    const status = analysisJobs.get(analysisId);
    if (status && (status.status === 'QUEUED' || status.status === 'PROCESSING')) {
      return res.status(202).json({
        error: 'Analysis not yet completed',
        asset_id: analysisId,
        status: status.status,
        progress: status.progress,
        message: 'Analysis is still in progress. Please check status endpoint.'
      });
    }

    // Try to fetch from titan-core or database
    try {
      const response = await axios.get<AnalysisResults>(
        `${TITAN_CORE_URL}/api/analysis/results/${analysisId}`,
        {
          timeout: 30000
        }
      );

      // Cache the results
      analysisResults.set(analysisId, response.data);

      console.log(`Analysis results retrieved from Titan Core`);
      return res.json(response.data);

    } catch (proxyError: any) {
      if (proxyError.response?.status === 404) {
        return res.status(404).json({
          error: 'Analysis results not found',
          asset_id: analysisId,
          message: 'No results available for this analysis ID'
        });
      }

      if (proxyError.response?.status === 202) {
        // Analysis still in progress on titan-core
        return res.status(202).json({
          error: 'Analysis not yet completed',
          asset_id: analysisId,
          message: 'Analysis is still in progress'
        });
      }

      throw proxyError;
    }

  } catch (error: any) {
    console.error('Error fetching analysis results:', error.message);

    res.status(error.response?.status || 500).json({
      error: error.message || 'Failed to fetch analysis results',
      asset_id: req.params.analysisId
    });
  }
});

// ============================================================================
// INTERNAL HELPER ENDPOINTS (Optional - for testing)
// ============================================================================

/**
 * POST /api/analysis/update-status (Internal)
 * Update analysis job status (for internal use by analysis workers)
 */
router.post('/update-status', async (req: Request, res: Response) => {
  try {
    const { asset_id, status, progress, message } = req.body;

    if (!asset_id || !status) {
      return res.status(400).json({
        error: 'Missing required fields: asset_id, status'
      });
    }

    const statusUpdate: AnalysisStatus = {
      asset_id,
      status,
      progress: progress || 0,
      message: message || ''
    };

    // Update in-memory cache
    analysisJobs.set(asset_id, statusUpdate);

    console.log(`Analysis status updated for ${asset_id}: ${status}`);

    res.json({
      message: 'Status updated successfully',
      status: statusUpdate
    });

  } catch (error: any) {
    console.error('Error updating analysis status:', error.message);
    res.status(500).json({
      error: error.message || 'Failed to update analysis status'
    });
  }
});

/**
 * POST /api/analysis/update-results (Internal)
 * Update analysis results (for internal use by analysis workers)
 */
router.post('/update-results', async (req: Request, res: Response) => {
  try {
    const { asset_id, status, results, error } = req.body;

    if (!asset_id) {
      return res.status(400).json({
        error: 'Missing required field: asset_id'
      });
    }

    const resultsUpdate: AnalysisResults = {
      asset_id,
      status: status || 'COMPLETED',
      results: results || {},
      error: error || undefined,
      completed_at: new Date().toISOString()
    };

    // Update in-memory cache
    analysisResults.set(asset_id, resultsUpdate);

    // Update status to COMPLETED or FAILED
    analysisJobs.set(asset_id, {
      asset_id,
      status: resultsUpdate.status,
      progress: 100,
      message: resultsUpdate.status === 'COMPLETED'
        ? 'Analysis completed successfully'
        : 'Analysis failed'
    });

    console.log(`Analysis results updated for ${asset_id}: ${resultsUpdate.status}`);

    res.json({
      message: 'Results updated successfully',
      results: resultsUpdate
    });

  } catch (error: any) {
    console.error('Error updating analysis results:', error.message);
    res.status(500).json({
      error: error.message || 'Failed to update analysis results'
    });
  }
});

/**
 * DELETE /api/analysis/clear-cache (Internal)
 * Clear in-memory cache (for testing)
 */
router.delete('/clear-cache', (req: Request, res: Response) => {
  const jobCount = analysisJobs.size;
  const resultsCount = analysisResults.size;

  analysisJobs.clear();
  analysisResults.clear();

  console.log(`Cache cleared: ${jobCount} jobs, ${resultsCount} results`);

  res.json({
    message: 'Cache cleared successfully',
    cleared: {
      jobs: jobCount,
      results: resultsCount
    }
  });
});

// ============================================================================
// EXPORT
// ============================================================================

export default router;
