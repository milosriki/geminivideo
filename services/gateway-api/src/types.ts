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

export interface VideoAdConcept {
  conceptId: string;
  storyboard: StoryboardClip[];
  hook: string;
  persona: string;
  triggers: string[];
  scores: {
    psychology: number;
    compliance: number;
    diversification: number;
    novelty: number;
    overall: number;
  };
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

export interface Weights {
  psychology_weight: number;
  compliance_weight: number;
  diversification_weight: number;
  novelty_weight: number;
  thresholds: {
    minimum_score: number;
    excellent_score: number;
  };
  psychology_factors: Record<string, number>;
  compliance_factors: Record<string, number>;
  diversification_factors: Record<string, number>;
  novelty_factors: Record<string, number>;
  platform_specs: Record<string, any>;
  learning: {
    adjustment_rate: number;
    min_samples_for_update: number;
    lookback_days: number;
  };
}
