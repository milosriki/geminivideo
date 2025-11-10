import axios from 'axios';

const API_URL = import.meta.env.VITE_GATEWAY_API_URL || 'http://localhost:8080';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const assetsApi = {
  getAll: () => api.get('/assets'),
  getClips: (id: string, ranked = true, top = 10) =>
    api.get(`/assets/${id}/clips`, { params: { ranked, top } }),
  ingestLocal: (folderPath: string) =>
    api.post('/assets/ingest/local', { folderPath }),
  ingestDrive: (folderId?: string, maxFiles?: number) =>
    api.post('/assets/ingest/drive', { folderId, maxFiles }),
  searchClips: (query: string, topK = 10) =>
    api.post('/assets/search/clips', { q: query, topK })
};

export const renderApi = {
  createJob: (clips: any[], variant = 'reels') =>
    api.post('/render/remix', { clips, variant, enableSubtitles: true, enableOverlays: true }),
  getJob: (jobId: string) => api.get(`/render/jobs/${jobId}`),
  listJobs: () => api.get('/render/jobs')
};

export const predictApi = {
  score: (clips: any[], context?: any) =>
    api.post('/predict/score', { clips, context }),
  getReliability: () => api.get('/predict/reliability')
};

export default api;
