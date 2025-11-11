// Type definitions for Gateway API

export interface KnowledgeUploadRequest {
  category: 'brand_guidelines' | 'competitor_analysis' | 'industry_benchmarks' | 'templates';
  subcategory: string;
  metadata: {
    version: string;
    author: string;
    tags: string[];
  };
}

export interface KnowledgeUploadResponse {
  upload_id: string;
  gcs_path: string;
  status: 'uploaded' | 'failed';
  timestamp: string;
}

export interface KnowledgeActivateRequest {
  upload_id: string;
  category: string;
}

export interface KnowledgeActivateResponse {
  status: 'active' | 'failed';
  version: string;
  activated_at: string;
  affected_services: string[];
}

export interface KnowledgeStatusResponse {
  category: string;
  active_version: string;
  last_updated: string;
  files: KnowledgeFile[];
}

export interface KnowledgeFile {
  name: string;
  gcs_path: string;
  size_bytes: number;
  checksum: string;
}

export interface PredictionLogEntry {
  prediction_id: string;
  timestamp: string;
  asset_id: string;
  clip_id: string;
  scores: ScoreBundle;
  predicted_band: string;
  predicted_ctr: number;
  actual_ctr?: number;
  model_version: string;
}

export interface ScoreBundle {
  psychology: PsychologyScore;
  hook_strength: HookStrength;
  novelty: NoveltyScore;
  composite: number;
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
