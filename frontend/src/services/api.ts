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

export const pauseCampaign = async (id: string) => {
  return api.post(`/campaigns/${id}/pause`);
};

export const getCampaignPerformance = async (id: string) => {
  return api.get(`/campaigns/${id}/performance`);
};

// Ad Management
export const getAds = async (params?: { campaign_id?: string; status?: string; approved?: boolean }) => {
  const queryParams = new URLSearchParams();
  if (params?.campaign_id) queryParams.append('campaign_id', params.campaign_id);
  if (params?.status) queryParams.append('status', params.status);
  if (params?.approved !== undefined) queryParams.append('approved', String(params.approved));
  const query = queryParams.toString();
  return api.get(`/ads${query ? `?${query}` : ''}`);
};

export const getAdById = async (id: string) => {
  return api.get(`/ads/${id}`);
};

export const createAd = async (data: {
  campaign_id: string;
  creative_url?: string;
  headline?: string;
  description?: string;
  call_to_action?: string;
}) => {
  return api.post('/ads', data);
};

export const updateAd = async (id: string, data: {
  headline?: string;
  description?: string;
  call_to_action?: string;
  status?: string;
}) => {
  return api.put(`/ads/${id}`, data);
};

export const deleteAd = async (id: string) => {
  return api.delete(`/ads/${id}`);
};

export const approveAd = async (id: string, notes?: string) => {
  return api.post(`/ads/${id}/approve`, { notes });
};

export const rejectAd = async (id: string, reason: string) => {
  return api.post(`/ads/${id}/reject`, { reason });
};

export const getAdPerformance = async (id: string) => {
  return api.get(`/ads/${id}/performance`);
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

// Additional Analytics Methods
export const getAnalyticsOverview = async (params?: {
  start_date?: string;
  end_date?: string;
  time_range?: 'today' | '7d' | '30d' | '90d' | 'all';
}) => {
  const queryParams = new URLSearchParams();
  if (params?.start_date) queryParams.append('start_date', params.start_date);
  if (params?.end_date) queryParams.append('end_date', params.end_date);
  if (params?.time_range) queryParams.append('time_range', params.time_range);
  const query = queryParams.toString();
  return api.get(`/analytics/overview${query ? `?${query}` : ''}`);
};

export const getCampaignAnalytics = async (campaignId: string, params?: {
  start_date?: string;
  end_date?: string;
}) => {
  const queryParams = new URLSearchParams();
  if (params?.start_date) queryParams.append('start_date', params.start_date);
  if (params?.end_date) queryParams.append('end_date', params.end_date);
  const query = queryParams.toString();
  return api.get(`/analytics/campaigns/${campaignId}${query ? `?${query}` : ''}`);
};

export const getPerformanceTrends = async (params?: {
  metric?: string;
  days?: number;
}) => {
  const queryParams = new URLSearchParams();
  if (params?.metric) queryParams.append('metric', params.metric);
  if (params?.days) queryParams.append('days', String(params.days));
  const query = queryParams.toString();
  return api.get(`/analytics/trends${query ? `?${query}` : ''}`);
};

export const getPredictionsVsActual = async (params?: {
  start_date?: string;
  end_date?: string;
  limit?: number;
}) => {
  const queryParams = new URLSearchParams();
  if (params?.start_date) queryParams.append('start_date', params.start_date);
  if (params?.end_date) queryParams.append('end_date', params.end_date);
  if (params?.limit) queryParams.append('limit', String(params.limit));
  const query = queryParams.toString();
  return api.get(`/analytics/predictions-vs-actual${query ? `?${query}` : ''}`);
};

export const getRealTimeAnalytics = async () => {
  return api.get('/analytics/real-time');
};

export default api;
