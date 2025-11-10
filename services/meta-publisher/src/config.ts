/**
 * Configuration management
 */
import dotenv from 'dotenv';

dotenv.config();

export const config = {
  metaAccessToken: process.env.META_ACCESS_TOKEN || '',
  metaAppId: process.env.META_APP_ID || '',
  metaAppSecret: process.env.META_APP_SECRET || '',
  metaAdAccountId: process.env.META_AD_ACCOUNT_ID || '',
  dryRun: process.env.META_DRY_RUN !== 'false', // Default to true
  logLevel: process.env.LOG_LEVEL || 'info',
  nodeEnv: process.env.NODE_ENV || 'development'
};
