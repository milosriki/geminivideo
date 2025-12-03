import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Assets
export const getAssets = async (skip = 0, limit = 100) => {
  const response = await api.get('/assets', { params: { skip, limit } });
  return response.data;
};

export const getAssetClips = async (assetId: string, ranked = true, top?: number) => {
  const response = await api.get(`/assets/${assetId}/clips`, {
    params: { ranked, top }
  });
  return response.data;
};

export const ingestLocalFolder = async (folderPath: string) => {
  const response = await api.post('/ingest/local/folder', { folder_path: folderPath });
  return response.data;
};

// Search
export const searchClips = async (query: string, topK = 10) => {
  const response = await api.post('/search/clips', { query, top_k: topK });
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

export default api;
