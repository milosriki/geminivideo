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

export default api;
