/**
 * Real-time Event Types
 * Defines all event types for WebSocket and SSE streaming
 */

// Base event structure
export interface BaseEvent {
  type: string;
  timestamp: string;
  id?: string;
}

// ============================================================================
// JOB PROGRESS EVENTS
// ============================================================================

export interface JobProgressEvent extends BaseEvent {
  type: 'job_progress';
  jobId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  stage: string;
  progress: number; // 0-1
  message: string;
  metadata?: Record<string, any>;
}

export interface VideoRenderProgressEvent extends BaseEvent {
  type: 'video_render_progress';
  jobId: string;
  currentFrame: number;
  totalFrames: number;
  progress: number; // 0-1
  fps: number;
  estimatedTimeRemaining: number; // seconds
  stage: 'preparing' | 'rendering' | 'encoding' | 'uploading' | 'complete';
}

// ============================================================================
// AI STREAMING EVENTS
// ============================================================================

export interface AIStreamChunk extends BaseEvent {
  type: 'ai_stream_chunk';
  model: 'gemini' | 'claude' | 'gpt4' | 'perplexity';
  chunk: string;
  isComplete: boolean;
  metadata?: {
    tokensUsed?: number;
    thinkingTime?: number;
  };
}

export interface CouncilScoreStreamEvent extends BaseEvent {
  type: 'council_score_stream';
  stage: 'gemini' | 'claude' | 'gpt4' | 'perplexity' | 'aggregating' | 'complete';
  model?: string;
  thinking?: string;
  score?: number;
  reasoning?: string;
  isComplete: boolean;
  finalScore?: {
    composite: number;
    psychology: any;
    hookStrength: any;
    novelty: any;
  };
}

export interface AIEvaluationStreamEvent extends BaseEvent {
  type: 'ai_evaluation_stream';
  evaluationType: 'creative' | 'technical' | 'performance';
  model: string;
  chunk: string;
  isComplete: boolean;
}

// ============================================================================
// CAMPAIGN & A/B TEST EVENTS
// ============================================================================

export interface CampaignMetricsEvent extends BaseEvent {
  type: 'campaign_metrics';
  campaignId: string;
  metrics: {
    impressions: number;
    clicks: number;
    ctr: number;
    spend: number;
    conversions: number;
    roas: number;
  };
  change: {
    impressions: number;
    clicks: number;
    ctr: number;
    spend: number;
  };
}

export interface ABTestResultEvent extends BaseEvent {
  type: 'ab_test_result';
  testId: string;
  variantId: string;
  metrics: {
    impressions: number;
    clicks: number;
    ctr: number;
    conversions: number;
    confidence: number;
  };
  isWinner: boolean;
  statisticalSignificance: number;
}

export interface LiveMetricUpdateEvent extends BaseEvent {
  type: 'live_metric_update';
  entityId: string;
  entityType: 'campaign' | 'ad' | 'variant' | 'creative';
  metric: string;
  value: number;
  delta: number;
  deltaPercent: number;
}

// ============================================================================
// ALERT EVENTS
// ============================================================================

export interface AlertEvent extends BaseEvent {
  type: 'alert';
  alertId: string;
  severity: 'info' | 'warning' | 'critical';
  category: 'performance' | 'budget' | 'technical' | 'policy';
  title: string;
  message: string;
  entityId?: string;
  entityType?: string;
  actionRequired: boolean;
  actions?: Array<{
    label: string;
    action: string;
    url?: string;
  }>;
}

// ============================================================================
// SYSTEM EVENTS
// ============================================================================

export interface ConnectionEvent extends BaseEvent {
  type: 'connected' | 'disconnected' | 'error';
  message: string;
  clientId?: string;
}

export interface HeartbeatEvent extends BaseEvent {
  type: 'heartbeat';
  serverTime: string;
}

export interface SubscriptionEvent extends BaseEvent {
  type: 'subscribed' | 'unsubscribed';
  channel: string;
  success: boolean;
}

// ============================================================================
// CHANNEL TYPES
// ============================================================================

export type ChannelType =
  | 'job_progress'
  | 'video_render'
  | 'ai_stream'
  | 'campaign_metrics'
  | 'ab_test_results'
  | 'alerts'
  | 'live_metrics';

export interface Channel {
  type: ChannelType;
  id?: string; // For specific entity channels
  userId?: string; // For user-specific channels
}

export function getChannelName(channel: Channel): string {
  const parts = [channel.type];
  if (channel.id) parts.push(channel.id);
  if (channel.userId) parts.push(channel.userId);
  return parts.join(':');
}

// ============================================================================
// EVENT UNION TYPE
// ============================================================================

export type RealtimeEvent =
  | JobProgressEvent
  | VideoRenderProgressEvent
  | AIStreamChunk
  | CouncilScoreStreamEvent
  | AIEvaluationStreamEvent
  | CampaignMetricsEvent
  | ABTestResultEvent
  | LiveMetricUpdateEvent
  | AlertEvent
  | ConnectionEvent
  | HeartbeatEvent
  | SubscriptionEvent;

// ============================================================================
// EVENT FACTORIES
// ============================================================================

export function createJobProgressEvent(
  jobId: string,
  status: JobProgressEvent['status'],
  stage: string,
  progress: number,
  message: string,
  metadata?: Record<string, any>
): JobProgressEvent {
  return {
    type: 'job_progress',
    jobId,
    status,
    stage,
    progress,
    message,
    metadata,
    timestamp: new Date().toISOString(),
    id: `job_${jobId}_${Date.now()}`
  };
}

export function createAIStreamChunk(
  model: AIStreamChunk['model'],
  chunk: string,
  isComplete: boolean,
  metadata?: AIStreamChunk['metadata']
): AIStreamChunk {
  return {
    type: 'ai_stream_chunk',
    model,
    chunk,
    isComplete,
    metadata,
    timestamp: new Date().toISOString(),
    id: `ai_${model}_${Date.now()}`
  };
}

export function createAlertEvent(
  severity: AlertEvent['severity'],
  category: AlertEvent['category'],
  title: string,
  message: string,
  options?: Partial<AlertEvent>
): AlertEvent {
  return {
    type: 'alert',
    alertId: options?.alertId || `alert_${Date.now()}`,
    severity,
    category,
    title,
    message,
    actionRequired: options?.actionRequired || false,
    timestamp: new Date().toISOString(),
    ...options
  };
}

export function createHeartbeat(): HeartbeatEvent {
  return {
    type: 'heartbeat',
    serverTime: new Date().toISOString(),
    timestamp: new Date().toISOString()
  };
}
