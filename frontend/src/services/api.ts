import axios, { AxiosError } from 'axios';
import { API_BASE_URL } from '../config/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000, // 30 second timeout
});

// Global error interceptor for consistent error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const message = error.response?.data
      ? (typeof error.response.data === 'string' ? error.response.data : JSON.stringify(error.response.data))
      : error.message || 'Network error';

    console.error(`API Error [${error.config?.method?.toUpperCase()} ${error.config?.url}]:`, message);

    // Re-throw with a more informative error
    return Promise.reject(new Error(`API Error: ${message}`));
  }
);

// Assets
export const getAssets = async (skip = 0, limit = 100) => {
  const response = await api.get('/assets', { params: { skip, limit } });
  return response.data;
};

export const getAssetClips = async (assetId: string, ranked = true, top?: number, signal?: AbortSignal) => {
  const response = await api.get(`/assets/${assetId}/clips`, {
    params: { ranked, top },
    signal
  });
  return response.data;
};

export const ingestLocalFolder = async (folderPath: string) => {
  const response = await api.post('/ingest/local/folder', { folder_path: folderPath });
  return response.data;
};

// Search - supports AbortController signal for cancellation
export const searchClips = async (query: string, topK = 10, signal?: AbortSignal) => {
  const response = await api.post('/search/clips', { query, top_k: topK }, { signal });
  return response.data;
};

// Scoring
export const scoreStoryboard = async (scenes: any[], metadata: any = {}) => {
  const response = await api.post('/score/storyboard', { scenes, metadata });
  return response.data;
};

// Rendering
export const createRenderJob = async (scenes: any[], variant: string, options: any = {}) => {
  const response = await api.post('/render/remix', {
    scenes,
    variant,
    ...options
  });
  return response.data;
};

export const getRenderJobStatus = async (jobId: string) => {
  const response = await api.get(`/render/status/${jobId}`);
  return response.data;
};

// Meta Publishing
export const publishToMeta = async (data: any) => {
  const response = await api.post('/publish/meta', data);
  return response.data;
};

export const getInsights = async (adId: string, datePreset = 'last_7d') => {
  const response = await api.get('/insights', { params: { adId, datePreset } });
  return response.data;
};

// Metrics
export const getDiversificationMetrics = async () => {
  const response = await api.get('/metrics/diversification');
  return response.data;
};

export const getDashboardMetrics = async () => {
  const response = await api.get('/metrics');
  return response.data;
};

export const getReliabilityMetrics = async () => {
  const response = await api.get('/metrics/reliability');
  return response.data;
};

// Learning
export const triggerLearningUpdate = async () => {
  const response = await api.post('/internal/learning/update');
  return response.data;
};


// Credits
export const getCredits = async () => {
  const response = await api.get('/credits');
  return response.data;
};

// Campaign Builder
export const predictCampaign = async (campaignData: any) => {
  const response = await api.post('/campaigns/predict', campaignData);
  return response.data;
};

export const saveCampaignDraft = async (campaign: any) => {
  const response = await api.post('/campaigns/draft', campaign);
  return response.data;
};

export const launchCampaign = async (campaign: any) => {
  const response = await api.post('/campaigns/launch', campaign);
  return response.data;
};

export const uploadCreative = async (formData: FormData) => {
  const response = await api.post('/creatives/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const getCampaigns = async (filters?: any) => {
  const response = await api.get('/campaigns', { params: filters });
  return response.data;
};

export const getCampaignById = async (campaignId: string) => {
  const response = await api.get(`/campaigns/${campaignId}`);
  return response.data;
};

export const updateCampaign = async (campaignId: string, updates: any) => {
  const response = await api.put(`/campaigns/${campaignId}`, updates);
  return response.data;
};

export const deleteCampaign = async (campaignId: string) => {
  const response = await api.delete(`/campaigns/${campaignId}`);

  return response.data;
};

// Predictions & ROI Analytics
export const getPredictionAccuracy = async (timeRange = 'last_30d') => {
  const response = await api.get('/analytics/predictions/accuracy', { params: { timeRange } });
  return response.data;
};

export const getValidationStatus = async () => {
  const response = await api.get('/analytics/predictions/validation');
  return response.data;
};

export const getROIPerformance = async (timeRange = 'last_30d') => {
  const response = await api.get('/analytics/roi/performance', { params: { timeRange } });
  return response.data;
};

export const getCorrelationReport = async () => {
  const response = await api.get('/analytics/correlation');
  return response.data;
};

export const getROITrends = async (period = 'weekly') => {
  const response = await api.get('/analytics/roi/trends', { params: { period } });
  return response.data;
};

export const getPredictionHistory = async (limit = 50) => {
  const response = await api.get('/analytics/predictions/history', { params: { limit } });
  return response.data;
};

// Titan Core - AI Intelligence API
export const titanAPI = {
  // Council of Titans - Multi-model evaluation
  evaluateWithCouncil: async (data: {
    video_url?: string;
    script?: string;
    niche: string;
    target_audience?: string;
  }): Promise<{
    council_score: number;
    breakdown: Record<string, number>;
    recommendations: string[];
    confidence: number;
  }> => {
    const response = await api.post('/api/council/evaluate', data);
    return response.data;
  },

  // Oracle - Performance prediction
  predictPerformance: async (data: {
    creative_features: {
      hook_type: string;
      duration: number;
      has_captions: boolean;
      music_tempo: string;
      color_scheme: string;
    };
    historical_data?: unknown[];
  }): Promise<{
    predicted_ctr: number;
    predicted_cpa: number;
    predicted_roas: number;
    confidence: number;
    confidence_breakdown: Record<string, number>;
  }> => {
    const response = await api.post('/api/oracle/predict', data);
    return response.data;
  },

  // Director - Script generation
  generateScript: async (data: {
    niche: string;
    style: string;
    duration: number;
    hooks?: string[];
    target_emotion?: string;
  }): Promise<{
    script: string;
    hooks: string[];
    call_to_action: string;
    estimated_impact: number;
  }> => {
    const response = await api.post('/api/director/generate', data);
    return response.data;
  },

  // Full Pipeline - Generate winning ad
  generateWinningAd: async (data: {
    niche: string;
    style: string;
    duration?: number;
    music_style?: string;
    caption_style?: string;
    target_audience?: string;
  }): Promise<{
    job_id: string;
    status: string;
    message: string;
  }> => {
    const response = await api.post('/api/pipeline/generate-campaign', data);
    return response.data;
  },

  // Get job status with progress
  getJobStatus: async (jobId: string): Promise<{
    job_id: string;
    status: string;
    progress: number;
    stage: string;
    output_url?: string;
    video_url?: string;
    error?: string;
    metadata?: Record<string, unknown>;
  }> => {
    const response = await api.get(`/api/pipeline/job/${jobId}/status`);
    return response.data;
  },

  // Download generated video
  getVideoDownloadUrl: async (videoId: string): Promise<string> => {
    const response = await api.get(`/api/videos/${videoId}/download`);
    return response.data.url;
  }
};

// Pro Video API
export const proVideoAPI = {
  // Generate captions
  generateCaptions: async (data: {
    video_path: string;
    style: 'instagram' | 'tiktok' | 'karaoke' | 'youtube' | 'hormozi';
    language?: string;
    word_level?: boolean;
  }) => {
    const response = await api.post('/api/pro/caption', data);
    return response.data;
  },

  // Color grading
  applyColorGrade: async (data: {
    video_path: string;
    preset: string;
    intensity?: number;
  }) => {
    const response = await api.post('/api/pro/color-grade', data);
    return response.data;
  },

  // Render with all pro features
  renderProVideo: async (data: {
    job_id?: string;
    video_path: string;
    captions?: boolean;
    color_grade?: string;
    music_path?: string;
    transitions?: string[];
  }) => {
    const response = await api.post('/api/pro/render', data);
    return response.data;
  }
};

export default api;
