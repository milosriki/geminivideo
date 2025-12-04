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

// Prediction & ROI Analytics
export const getPredictionAccuracy = async (predictionId?: string) => {
  const url = predictionId
    ? `/api/predictions/correlation/${predictionId}`
    : '/api/analytics/prediction-accuracy';
  const response = await api.get(url);
  return response.data;
};

export const getValidationStatus = async () => {
  const response = await api.get('/api/predictions/validation-status');
  return response.data;
};

export const getROIPerformance = async () => {
  const response = await api.get('/api/analytics/roi-performance');
  return response.data;
};

export const getCorrelationReport = async () => {
  const response = await api.get('/api/analytics/correlation-report');
  return response.data;
};

export default api;
