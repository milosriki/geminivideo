/**
 * Configuration management
 */
import dotenv from 'dotenv';

dotenv.config();

export const config = {
  driveIntelUrl: process.env.DRIVE_INTEL_URL || 'http://localhost:8001',
  videoAgentUrl: process.env.VIDEO_AGENT_URL || 'http://localhost:8002',
  metaPublisherUrl: process.env.META_PUBLISHER_URL || 'http://localhost:8003',
  enableLlmFallback: process.env.ENABLE_LLM_FALLBACK === 'true',
  logLevel: process.env.LOG_LEVEL || 'info',
  nodeEnv: process.env.NODE_ENV || 'development'
};
