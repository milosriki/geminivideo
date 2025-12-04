/**
 * Unified Dashboard API Client
 * Agent 11: Frontend Dashboard Integration Engineer
 *
 * Connects all backend services through a single, type-safe interface
 * with comprehensive error handling, retry logic, and request interceptors.
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios';

import { API_BASE_URL } from '../config/api';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface VideoAnalysis {
  asset_id: string;
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  hook_style?: string;
  pacing?: string;
  emotional_trigger?: string;
  visual_elements?: string[];
  reasoning?: string;
  timestamp?: string;
}

export interface AnalysisStatus {
  asset_id: string;
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  progress?: number;
  message?: string;
  error?: string;
}

export interface AnalysisResults {
  asset_id: string;
  scenes: SceneAnalysis[];
  scores: ScoreBundle;
  predicted_ctr: number;
  predicted_roas: number;
  timestamp: string;
}

export interface SceneAnalysis {
  timestamp: string;
  description: string;
  emotion?: string;
  objects?: string[];
  confidence?: number;
}

export interface ScoreBundle {
  psychology: PsychologyScore;
  hook_strength: HookStrength;
  novelty: NoveltyScore;
  composite: number;
  win_probability?: { value: number; band: string };
}

export interface PsychologyScore {
  curiosity: number;
  urgency: number;
  social_proof: number;
  surprise: number;
  empathy: number;
  composite: number;
}

export interface HookStrength {
  hook_type: string;
  strength: number;
  confidence: number;
}

export interface NoveltyScore {
  embedding_distance: number;
  temporal_decay: number;
  diversity_bonus: number;
  composite: number;
}

export interface CouncilScore {
  video_id: string;
  overall_score: number;
  titan_scores: TitanScore[];
  consensus: string;
  timestamp: string;
}

export interface TitanScore {
  titan_name: string;
  score: number;
  reasoning: string;
  confidence: number;
}

export interface ReviewStatus {
  video_id: string;
  status: 'pending' | 'in_review' | 'completed';
  submitted_at: string;
}

export interface MetaInsights {
  campaigns_analyzed: number;
  avg_ctr: number;
  avg_roas: number;
  top_performers: TopPerformer[];
  winning_patterns: WinningPattern[];
  timestamp: string;
}

export interface TopPerformer {
  ad_id: string;
  ctr: number;
  roas: number;
  spend: number;
  impressions: number;
  creative_summary: string;
}

export interface WinningPattern {
  pattern_type: string;
  frequency: number;
  avg_ctr: number;
  confidence: number;
}

export interface RefreshStatus {
  status: 'accepted' | 'processing' | 'completed';
  message: string;
  results?: {
    campaigns_analyzed: number;
    avg_ctr: number;
    avg_roas: number;
  };
}

export interface TopPerformersList {
  performers: TopPerformer[];
  total_count: number;
  timestamp: string;
}

export interface RenderConfig {
  scenes: RenderScene[];
  variant: string;
  output_format?: string;
  resolution?: string;
  transitions?: boolean;
}

export interface RenderScene {
  clip_id: string;
  start_time?: number;
  duration?: number;
  effects?: string[];
}

export interface RenderJob {
  job_id: string;
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  progress?: number;
  output_path?: string;
  created_at: string;
  estimated_completion?: string;
}

export interface RenderStatus {
  job_id: string;
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  progress: number;
  message?: string;
  output_url?: string;
  error?: string;
}

export interface ApprovalItem {
  ad_id: string;
  asset_id: string;
  clip_ids: string[];
  arc_name?: string;
  predicted_ctr: number;
  predicted_roas: number;
  status: string;
  created_at: string;
  notes?: string;
  thumbnail_url?: string;
}

export interface ApprovalStatus {
  ad_id: string;
  status: 'pending_approval' | 'approved' | 'rejected';
  submitted_at: string;
}

export interface DiversificationMetrics {
  total_predictions: number;
  unique_patterns: number;
  diversity_score: number;
  pattern_distribution: Record<string, number>;
  timestamp: string;
}

export interface ReliabilityMetrics {
  total_predictions: number;
  correct_predictions: number;
  accuracy: number;
  avg_confidence: number;
  calibration_score: number;
  timestamp: string;
}

export interface AccuracyMetrics {
  overall_accuracy: number;
  ctr_mae: number;  // Mean Absolute Error
  ctr_rmse: number; // Root Mean Square Error
  roas_mae: number;
  roas_rmse: number;
  sample_size: number;
  timestamp: string;
}

export interface DriveAnalysisJob {
  job_id: string;
  folder_id: string;
  status: 'accepted' | 'processing' | 'completed' | 'failed';
  videos_found?: number;
  videos_analyzed?: number;
  message: string;
}

export interface DriveAnalysisStatus {
  job_id: string;
  status: 'accepted' | 'processing' | 'completed' | 'failed';
  progress: number;
  videos_analyzed: number;
  total_videos: number;
  results?: VideoAnalysis[];
}

export interface DashboardAPIError {
  message: string;
  code?: string;
  status?: number;
  details?: any;
}

// ============================================================================
// API CLIENT CONFIGURATION
// ============================================================================

const DEFAULT_TIMEOUT = 30000; // 30 seconds
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

class DashboardAPIClass {
  private client: AxiosInstance;
  private authToken: string | null = null;

  constructor() {
    const baseURL = API_BASE_URL;

    this.client = axios.create({
      baseURL,
      timeout: DEFAULT_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * Setup request/response interceptors for authentication and error handling
   */
  private setupInterceptors(): void {
    // Request interceptor - Add auth token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        if (this.authToken && config.headers) {
          config.headers.Authorization = `Bearer ${this.authToken}`;
        }
        return config;
      },
      (error: AxiosError) => {
        return Promise.reject(this.transformError(error));
      }
    );

    // Response interceptor - Handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean; _retryCount?: number };

        // Retry logic for network errors and 5xx errors
        if (
          originalRequest &&
          !originalRequest._retry &&
          this.shouldRetry(error)
        ) {
          originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;

          if (originalRequest._retryCount <= MAX_RETRIES) {
            originalRequest._retry = true;
            await this.delay(RETRY_DELAY * originalRequest._retryCount);
            return this.client(originalRequest);
          }
        }

        return Promise.reject(this.transformError(error));
      }
    );
  }

  /**
   * Determine if request should be retried
   */
  private shouldRetry(error: AxiosError): boolean {
    if (!error.response) {
      // Network error - retry
      return true;
    }

    const status = error.response.status;
    // Retry on 5xx errors and 429 (rate limit)
    return status >= 500 || status === 429;
  }

  /**
   * Transform axios error to custom error format
   */
  private transformError(error: AxiosError): DashboardAPIError {
    if (error.response) {
      // Server responded with error
      return {
        message: (error.response.data as any)?.error || error.message,
        status: error.response.status,
        code: (error.response.data as any)?.code,
        details: error.response.data,
      };
    } else if (error.request) {
      // Request made but no response
      return {
        message: 'No response from server. Please check your connection.',
        code: 'NETWORK_ERROR',
      };
    } else {
      // Error setting up request
      return {
        message: error.message,
        code: 'REQUEST_ERROR',
      };
    }
  }

  /**
   * Utility function to delay execution
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Set authentication token
   */
  public setAuthToken(token: string): void {
    this.authToken = token;
  }

  /**
   * Clear authentication token
   */
  public clearAuthToken(): void {
    this.authToken = null;
  }

  /**
   * Update base URL (useful for environment switching)
   */
  public setBaseURL(url: string): void {
    this.client.defaults.baseURL = url;
  }

  // ============================================================================
  // VIDEO ANALYSIS METHODS
  // ============================================================================

  /**
   * Analyze a video file
   * @param file Video file to analyze
   * @returns Analysis result with asset_id
   */
  async analyzeVideo(file: File): Promise<VideoAnalysis> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<VideoAnalysis>('/api/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * Get analysis status for a video
   * @param analysisId Asset ID or analysis ID
   */
  async getAnalysisStatus(analysisId: string): Promise<AnalysisStatus> {
    const response = await this.client.get<AnalysisStatus>(`/api/analysis/status/${analysisId}`);
    return response.data;
  }

  /**
   * Get complete analysis results
   * @param analysisId Asset ID
   */
  async getAnalysisResults(analysisId: string): Promise<AnalysisResults> {
    const response = await this.client.get<AnalysisResults>(`/api/analysis/results/${analysisId}`);
    return response.data;
  }

  // ============================================================================
  // COUNCIL OF TITANS METHODS
  // ============================================================================

  /**
   * Get Council of Titans score for a video
   * @param videoId Video asset ID
   */
  async getCouncilScore(videoId: string): Promise<CouncilScore> {
    const response = await this.client.get<CouncilScore>(`/api/council/score/${videoId}`);
    return response.data;
  }

  /**
   * Submit video for Council review
   * @param videoId Video asset ID
   */
  async submitForCouncilReview(videoId: string): Promise<ReviewStatus> {
    const response = await this.client.post<ReviewStatus>('/api/council/review', {
      video_id: videoId,
    });
    return response.data;
  }

  // ============================================================================
  // META LEARNING METHODS
  // ============================================================================

  /**
   * Get meta learning insights
   */
  async getMetaInsights(): Promise<MetaInsights> {
    const response = await this.client.get<MetaInsights>('/api/insights');
    return response.data;
  }

  /**
   * Trigger meta learning data refresh
   */
  async triggerMetaRefresh(): Promise<RefreshStatus> {
    const response = await this.client.post<RefreshStatus>('/api/trigger/refresh-meta-metrics', {
      days_back: 7,
    });
    return response.data;
  }

  /**
   * Get top performing ads
   * @param limit Number of top performers to return
   */
  async getTopPerformers(limit: number = 10): Promise<TopPerformersList> {
    const response = await this.client.get<TopPerformersList>('/api/top-performers', {
      params: { limit },
    });
    return response.data;
  }

  // ============================================================================
  // RENDER JOB METHODS
  // ============================================================================

  /**
   * Create a new render job
   * @param config Render configuration
   */
  async createRenderJob(config: RenderConfig): Promise<RenderJob> {
    const response = await this.client.post<RenderJob>('/api/render/remix', config);
    return response.data;
  }

  /**
   * Get render job status
   * @param jobId Render job ID
   */
  async getRenderStatus(jobId: string): Promise<RenderStatus> {
    const response = await this.client.get<RenderStatus>(`/api/render/status/${jobId}`);
    return response.data;
  }

  /**
   * Cancel a render job
   * @param jobId Render job ID
   */
  async cancelRenderJob(jobId: string): Promise<boolean> {
    const response = await this.client.delete(`/api/render/job/${jobId}`);
    return response.data.success || true;
  }

  /**
   * Download rendered video
   * @param jobId Render job ID
   */
  async downloadRenderedVideo(jobId: string): Promise<Blob> {
    const response = await this.client.get(`/api/render/download/${jobId}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // ============================================================================
  // APPROVAL WORKFLOW METHODS
  // ============================================================================

  /**
   * Get approval queue
   */
  async getApprovalQueue(): Promise<ApprovalItem[]> {
    const response = await this.client.get<{ count: number; ads: ApprovalItem[] }>('/api/approval/queue');
    return response.data.ads;
  }

  /**
   * Submit ad for approval
   * @param adId Ad ID
   */
  async submitForApproval(adId: string): Promise<ApprovalStatus> {
    const response = await this.client.post<ApprovalStatus>('/api/approval/submit', {
      ad_id: adId,
    });
    return response.data;
  }

  /**
   * Approve an ad
   * @param adId Ad ID
   * @param notes Optional approval notes
   */
  async approveAd(adId: string, notes?: string): Promise<boolean> {
    const response = await this.client.post(`/api/approval/approve/${adId}`, {
      approved: true,
      notes: notes || '',
    });
    return response.data.message.includes('approved');
  }

  /**
   * Reject an ad
   * @param adId Ad ID
   * @param reason Rejection reason
   */
  async rejectAd(adId: string, reason: string): Promise<boolean> {
    const response = await this.client.post(`/api/approval/approve/${adId}`, {
      approved: false,
      notes: reason,
    });
    return response.data.message.includes('rejected');
  }

  // ============================================================================
  // METRICS METHODS
  // ============================================================================

  /**
   * Get diversification metrics
   */
  async getDiversificationMetrics(): Promise<DiversificationMetrics> {
    const response = await this.client.get<DiversificationMetrics>('/api/metrics/diversification');
    return response.data;
  }

  /**
   * Get reliability metrics
   */
  async getReliabilityMetrics(): Promise<ReliabilityMetrics> {
    const response = await this.client.get<ReliabilityMetrics>('/api/metrics/reliability');
    return response.data;
  }

  /**
   * Get prediction accuracy metrics
   */
  async getPredictionAccuracy(): Promise<AccuracyMetrics> {
    const response = await this.client.get<AccuracyMetrics>('/api/metrics/accuracy');
    return response.data;
  }

  // ============================================================================
  // DRIVE INTEGRATION METHODS
  // ============================================================================

  /**
   * Analyze Google Drive folder
   * @param folderId Google Drive folder ID
   * @param maxVideos Maximum number of videos to analyze
   */
  async analyzeDriveFolder(folderId: string, maxVideos: number = 10): Promise<DriveAnalysisJob> {
    const response = await this.client.post<DriveAnalysisJob>('/api/trigger/analyze-drive-folder', {
      folder_id: folderId,
      max_videos: maxVideos,
    });
    return response.data;
  }

  /**
   * Get Drive analysis status
   * @param jobId Analysis job ID
   */
  async getDriveAnalysisStatus(jobId: string): Promise<DriveAnalysisStatus> {
    const response = await this.client.get<DriveAnalysisStatus>(`/api/drive/analysis/${jobId}`);
    return response.data;
  }

  // ============================================================================
  // SCORING METHODS
  // ============================================================================

  /**
   * Score a storyboard/scene composition
   * @param scenes Array of scenes to score
   * @param metadata Additional metadata
   */
  async scoreStoryboard(scenes: any[], metadata: any = {}): Promise<ScoreBundle> {
    const response = await this.client.post<{ scores: ScoreBundle }>('/api/score/storyboard', {
      scenes,
      metadata,
    });
    return response.data.scores;
  }

  // ============================================================================
  // ASSET MANAGEMENT METHODS
  // ============================================================================

  /**
   * Get assets with pagination
   * @param skip Number of assets to skip
   * @param limit Number of assets to return
   */
  async getAssets(skip: number = 0, limit: number = 100): Promise<any[]> {
    const response = await this.client.get('/api/assets', {
      params: { skip, limit },
    });
    return response.data;
  }

  /**
   * Get clips for an asset
   * @param assetId Asset ID
   * @param ranked Whether to return ranked clips
   * @param top Number of top clips to return
   */
  async getAssetClips(assetId: string, ranked: boolean = true, top?: number): Promise<any[]> {
    const response = await this.client.get(`/api/assets/${assetId}/clips`, {
      params: { ranked, top },
    });
    return response.data;
  }

  /**
   * Search clips by query
   * @param query Search query
   * @param topK Number of results to return
   */
  async searchClips(query: string, topK: number = 10): Promise<any[]> {
    const response = await this.client.post('/api/search/clips', {
      query,
      top_k: topK,
    });
    return response.data;
  }
}

// Export singleton instance
export const dashboardAPI = new DashboardAPIClass();

// Export class for testing or creating custom instances
export { DashboardAPIClass };
