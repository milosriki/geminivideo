const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8080';

export interface Asset {
  id: string;
  filename: string;
  duration: number;
  resolution: string;
  aspectRatio: string;
  fileSize: number;
  path: string;
  thumbnail?: string;
  tags: string[];
}

export interface Clip {
  id: string;
  assetId: string;
  startTime: number;
  endTime: number;
  duration: number;
  tags: string[];
  sceneType?: string;
  objects?: string[];
  transcript?: string;
}

export interface StoryboardClip {
  clipId: string;
  duration: number;
  transition?: string;
  effects?: string[];
}

export interface RemixRequest {
  storyboard: StoryboardClip[];
  assetMap: Record<string, string>;
  outputFormat?: string;
  overlays?: {
    cta?: string;
    logo?: string;
  };
}

export interface RenderJob {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  outputUrl?: string;
  error?: string;
  createdAt: string;
  completedAt?: string;
}

export const api = {
  // Ingest
  async syncDrive(source: 'local' | 'drive' = 'local', folderId?: string) {
    const response = await fetch(`${GATEWAY_URL}/ingest/drive/sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source, folderId })
    });
    return response.json();
  },

  // Assets
  async getAssets(): Promise<Asset[]> {
    const response = await fetch(`${GATEWAY_URL}/assets`);
    return response.json();
  },

  async getAssetClips(assetId: string): Promise<Clip[]> {
    const response = await fetch(`${GATEWAY_URL}/assets/${assetId}/clips`);
    return response.json();
  },

  // Render
  async createRemix(request: RemixRequest): Promise<{ jobId: string; status: string }> {
    const response = await fetch(`${GATEWAY_URL}/render/remix`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    return response.json();
  },

  async getJobStatus(jobId: string): Promise<RenderJob> {
    const response = await fetch(`${GATEWAY_URL}/render/jobs/${jobId}`);
    return response.json();
  },

  // Publishing
  async publishToMeta(videoUrl: string, caption: string, platform: string) {
    const response = await fetch(`${GATEWAY_URL}/publish/meta`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ videoUrl, caption, platform })
    });
    return response.json();
  },

  async getMetrics(creativeId?: string, days: number = 7) {
    const params = new URLSearchParams();
    if (creativeId) params.append('creativeId', creativeId);
    params.append('days', days.toString());
    
    const response = await fetch(`${GATEWAY_URL}/performance/metrics?${params}`);
    return response.json();
  }
};
