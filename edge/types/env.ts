/**
 * Cloudflare Workers Environment Types
 * Type definitions for Workers bindings and environment variables
 */

export interface CloudflareEnv {
  // KV Namespaces for caching
  PREDICTIONS: KVNamespace;
  CREATIVE_SCORES: KVNamespace;
  AB_TESTS: KVNamespace;
  ANALYTICS: KVNamespace;

  // D1 Database (SQLite at edge)
  DB: D1Database;

  // R2 Storage buckets
  ASSETS: R2Bucket;
  VIDEO_CACHE: R2Bucket;

  // Durable Objects
  ANALYTICS_AGGREGATOR: DurableObjectNamespace;
  RATE_LIMITER: DurableObjectNamespace;

  // Environment variables
  ORIGIN_URL: string;
  GATEWAY_API_URL: string;
  TITAN_CORE_URL: string;
  ML_SERVICE_URL: string;

  // Secrets
  API_SECRET: string;
  CLOUDFLARE_ACCOUNT_ID: string;
  CLOUDFLARE_API_TOKEN: string;

  // Stream API
  STREAM_ACCOUNT_ID?: string;
  STREAM_API_TOKEN?: string;

  // Feature flags
  ENABLE_EDGE_ANALYTICS: string;
  ENABLE_SMART_ROUTING: string;
  CACHE_TTL_SECONDS: string;
}

export interface EdgeRequestContext {
  request: Request;
  env: CloudflareEnv;
  ctx: ExecutionContext;
}

export interface CacheOptions {
  ttl: number;
  staleWhileRevalidate?: number;
  cacheKey?: string;
  tags?: string[];
}

export interface PredictionCache {
  creative_id: string;
  predicted_ctr: number;
  predicted_roas: number;
  confidence: number;
  cached_at: string;
  expires_at: string;
}

export interface CreativeScore {
  creative_id: string;
  hook_score: number;
  retention_score: number;
  cta_score: number;
  overall_score: number;
  timestamp: string;
}

export interface ABTestVariant {
  variant_id: string;
  experiment_id: string;
  allocation_percent: number;
  is_control: boolean;
  metadata: Record<string, any>;
}

export interface EdgeAnalyticsEvent {
  event_type: 'impression' | 'click' | 'conversion' | 'error';
  creative_id?: string;
  variant_id?: string;
  timestamp: string;
  country?: string;
  city?: string;
  user_agent?: string;
  referer?: string;
  metadata?: Record<string, any>;
}

export interface RegionPerformance {
  region: string;
  avg_latency_ms: number;
  request_count: number;
  error_rate: number;
  cache_hit_rate: number;
}
