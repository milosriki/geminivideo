/**
 * Zod Validation Schemas - Agent 98: Security & Validation
 *
 * Comprehensive type-safe validation schemas using Zod
 * Provides strong input validation for all API endpoints
 */

import { z } from 'zod';
import { Request, Response, NextFunction } from 'express';

// ============================================================================
// COMMON VALIDATION SCHEMAS
// ============================================================================

/**
 * UUID validation schema
 */
export const uuidSchema = z.string().uuid('Invalid UUID format');

/**
 * Email validation schema
 */
export const emailSchema = z.string().email('Invalid email format').max(255);

/**
 * URL validation schema
 */
export const urlSchema = z.string().url('Invalid URL format').max(2000);

/**
 * Date string validation
 */
export const dateSchema = z.string().datetime('Invalid date format').or(z.date());

/**
 * Pagination schema
 */
export const paginationSchema = z.object({
  limit: z.coerce.number().int().min(1).max(100).default(20),
  offset: z.coerce.number().int().min(0).default(0)
});

// ============================================================================
// CAMPAIGN VALIDATION SCHEMAS
// ============================================================================

/**
 * Campaign creation schema
 */
export const createCampaignSchema = z.object({
  name: z.string().min(1, 'Campaign name is required').max(255).trim(),
  budget_daily: z.number().positive('Budget must be positive').max(1000000),
  target_audience: z.object({
    age_min: z.number().int().min(13).max(65).optional(),
    age_max: z.number().int().min(13).max(65).optional(),
    genders: z.array(z.enum(['male', 'female', 'all'])).optional(),
    interests: z.array(z.string()).optional(),
    locations: z.array(z.string()).optional()
  }).optional(),
  objective: z.enum(['conversions', 'traffic', 'awareness', 'engagement']).default('conversions'),
  status: z.enum(['draft', 'active', 'paused']).default('draft'),
  start_date: dateSchema.optional(),
  end_date: dateSchema.optional()
});

/**
 * Campaign update schema
 */
export const updateCampaignSchema = z.object({
  name: z.string().min(1).max(255).trim().optional(),
  budget_daily: z.number().positive().max(1000000).optional(),
  target_audience: z.object({
    age_min: z.number().int().min(13).max(65).optional(),
    age_max: z.number().int().min(13).max(65).optional(),
    genders: z.array(z.enum(['male', 'female', 'all'])).optional(),
    interests: z.array(z.string()).optional(),
    locations: z.array(z.string()).optional()
  }).optional(),
  status: z.enum(['draft', 'active', 'paused', 'completed']).optional()
});

/**
 * Campaign query schema
 */
export const queryCampaignsSchema = z.object({
  status: z.enum(['draft', 'active', 'paused', 'completed']).optional(),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  offset: z.coerce.number().int().min(0).default(0),
  sort_by: z.enum(['created_at', 'budget_daily', 'name']).default('created_at'),
  sort_order: z.enum(['asc', 'desc']).default('desc')
});

// ============================================================================
// AD VALIDATION SCHEMAS
// ============================================================================

/**
 * Ad creation schema
 */
export const createAdSchema = z.object({
  campaign_id: uuidSchema.optional(),
  video_id: uuidSchema.optional(),
  asset_id: uuidSchema.optional(),
  arc_name: z.string().max(100).trim().optional(),
  clip_ids: z.array(uuidSchema).max(50).optional(),
  caption: z.string().max(2200, 'Caption too long').trim().optional(),
  predicted_ctr: z.number().min(0).max(1).optional(),
  predicted_roas: z.number().min(0).max(100).optional(),
  status: z.enum(['pending_approval', 'approved', 'rejected', 'published']).default('pending_approval')
});

/**
 * Ad approval schema
 */
export const approveAdSchema = z.object({
  approved: z.boolean(),
  notes: z.string().max(1000).trim().optional()
});

// ============================================================================
// A/B TEST VALIDATION SCHEMAS
// ============================================================================

/**
 * Create A/B test schema
 */
export const createABTestSchema = z.object({
  name: z.string().min(1, 'Test name is required').max(255).trim(),
  campaign_id: uuidSchema,
  variants: z.array(z.object({
    name: z.string().min(1).max(100).trim(),
    video_id: uuidSchema,
    traffic_allocation: z.number().min(0).max(100)
  })).min(2, 'At least 2 variants required').max(10),
  objective: z.enum(['ctr', 'conversions', 'roas', 'engagement']).default('conversions'),
  duration_days: z.number().int().min(1).max(90).default(7)
});

/**
 * Update A/B test schema
 */
export const updateABTestSchema = z.object({
  status: z.enum(['running', 'paused', 'completed']).optional(),
  winner_variant_id: uuidSchema.optional()
});

// ============================================================================
// PUBLISHING VALIDATION SCHEMAS
// ============================================================================

/**
 * Meta publishing schema
 */
export const publishMetaSchema = z.object({
  ad_id: uuidSchema,
  video_path: z.string().min(1).max(1000),
  caption: z.string().max(2200).trim().optional(),
  scheduled_time: dateSchema.optional()
});

/**
 * Multi-platform publishing schema
 */
export const publishMultiPlatformSchema = z.object({
  creative_id: z.string().min(1).max(100),
  video_path: z.string().min(1).max(1000),
  platforms: z.array(z.enum(['meta', 'google', 'tiktok'])).min(1).max(3),
  budget_allocation: z.object({
    meta: z.number().positive().optional(),
    google: z.number().positive().optional(),
    tiktok: z.number().positive().optional()
  }),
  campaign_name: z.string().min(1).max(255).trim(),
  campaign_config: z.object({
    objective: z.enum(['conversions', 'traffic', 'awareness', 'engagement']).optional(),
    start_date: dateSchema.optional(),
    end_date: dateSchema.optional()
  }).optional()
});

// ============================================================================
// GOOGLE ADS VALIDATION SCHEMAS
// ============================================================================

/**
 * Google Ads campaign creation schema
 */
export const createGoogleCampaignSchema = z.object({
  name: z.string().min(1).max(255).trim(),
  budget: z.number().positive().max(1000000),
  biddingStrategy: z.string().max(50).optional(),
  startDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be YYYY-MM-DD format').optional(),
  endDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be YYYY-MM-DD format').optional(),
  status: z.enum(['ACTIVE', 'PAUSED']).default('ACTIVE')
});

/**
 * Google Ads video ad creation schema
 */
export const createGoogleVideoAdSchema = z.object({
  videoPath: z.string().min(1).max(1000),
  campaignId: z.string().min(1),
  adGroupId: z.string().min(1),
  headline: z.string().min(1).max(100).trim(),
  description: z.string().max(1000).trim().optional(),
  finalUrl: urlSchema
});

// ============================================================================
// IMAGE GENERATION VALIDATION SCHEMAS
// ============================================================================

/**
 * Image generation schema
 */
export const generateImageSchema = z.object({
  prompt: z.string().min(10, 'Prompt must be at least 10 characters').max(2000),
  style: z.enum(['realistic', 'artistic', 'cartoon', 'abstract', 'photographic']).default('realistic'),
  aspect_ratio: z.enum(['1:1', '16:9', '9:16', '4:3', '3:4']).default('1:1'),
  num_images: z.number().int().min(1).max(4).default(1),
  negative_prompt: z.string().max(1000).optional()
});

// ============================================================================
// ANALYTICS VALIDATION SCHEMAS
// ============================================================================

/**
 * Analytics query schema
 */
export const analyticsQuerySchema = z.object({
  campaign_id: uuidSchema.optional(),
  start_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  end_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  metric: z.enum(['impressions', 'clicks', 'conversions', 'spend', 'roas', 'ctr']).optional(),
  group_by: z.enum(['day', 'week', 'month', 'platform', 'campaign']).default('day')
});

// ============================================================================
// FILE UPLOAD VALIDATION SCHEMAS
// ============================================================================

/**
 * Video upload metadata schema
 */
export const videoUploadSchema = z.object({
  filename: z.string().min(1).max(255).regex(/\.(mp4|mov|avi|webm)$/i, 'Invalid video format'),
  size_bytes: z.number().int().positive().max(500 * 1024 * 1024), // Max 500MB
  duration_seconds: z.number().positive().max(600).optional(), // Max 10 minutes
  folder_id: z.string().max(200).optional()
});

/**
 * Folder analysis schema
 */
export const analyzeFolderSchema = z.object({
  folder_id: z.string().min(1).max(200),
  max_videos: z.number().int().min(1).max(1000).default(10)
});

// ============================================================================
// USER AUTHENTICATION SCHEMAS
// ============================================================================

/**
 * User registration schema
 */
export const registerUserSchema = z.object({
  email: emailSchema,
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .max(128)
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'Password must contain uppercase, lowercase, and number'),
  displayName: z.string().min(1).max(100).trim(),
  photoURL: urlSchema.optional()
});

/**
 * User login schema
 */
export const loginUserSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'Password is required')
});

/**
 * Password reset schema
 */
export const resetPasswordSchema = z.object({
  email: emailSchema
});

/**
 * Update password schema
 */
export const updatePasswordSchema = z.object({
  current_password: z.string().min(1),
  new_password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .max(128)
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'Password must contain uppercase, lowercase, and number')
});

// ============================================================================
// WEBHOOK VALIDATION SCHEMAS
// ============================================================================

/**
 * Meta webhook validation schema
 */
export const metaWebhookSchema = z.object({
  entry: z.array(z.object({
    id: z.string(),
    time: z.number(),
    changes: z.array(z.object({
      field: z.string(),
      value: z.unknown()
    }))
  })),
  object: z.string()
});

// ============================================================================
// ZOD VALIDATION MIDDLEWARE
// ============================================================================

/**
 * Generic Zod validation middleware factory
 *
 * @param schema - Zod schema to validate against
 * @param location - Where to validate (body, query, params)
 * @returns Express middleware function
 */
export function validateZod<T extends z.ZodType>(
  schema: T,
  location: 'body' | 'query' | 'params' = 'body'
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const data = req[location];
      const validated = await schema.parseAsync(data);

      // Replace request data with validated and sanitized data
      req[location] = validated;

      next();
    } catch (error) {
      if (error instanceof z.ZodError) {
        const errors = error.issues.map(err => ({
          field: err.path.join('.'),
          message: err.message,
          code: err.code
        }));

        console.warn('[Validation] Request validation failed:', {
          location,
          errors,
          path: req.path,
          method: req.method
        });

        return res.status(400).json({
          error: 'Validation failed',
          details: errors,
          message: 'Invalid request data'
        });
      }

      // Unexpected validation error
      console.error('[Validation] Unexpected error:', error);
      return res.status(500).json({
        error: 'Validation error',
        message: 'An unexpected validation error occurred'
      });
    }
  };
}

/**
 * Validate request body with Zod schema
 */
export const validateBody = <T extends z.ZodType>(schema: T) =>
  validateZod(schema, 'body');

/**
 * Validate query parameters with Zod schema
 */
export const validateQuery = <T extends z.ZodType>(schema: T) =>
  validateZod(schema, 'query');

/**
 * Validate route parameters with Zod schema
 */
export const validateParams = <T extends z.ZodType>(schema: T) =>
  validateZod(schema, 'params');

// ============================================================================
// COMBINED VALIDATION MIDDLEWARE
// ============================================================================

/**
 * Validate multiple locations at once
 */
export function validateRequest(schemas: {
  body?: z.ZodType;
  query?: z.ZodType;
  params?: z.ZodType;
}) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      if (schemas.body) {
        req.body = await schemas.body.parseAsync(req.body) as any;
      }
      if (schemas.query) {
        req.query = await schemas.query.parseAsync(req.query) as any;
      }
      if (schemas.params) {
        req.params = await schemas.params.parseAsync(req.params) as any;
      }

      next();
    } catch (error) {
      if (error instanceof z.ZodError) {
        const errors = error.issues.map(err => ({
          field: err.path.join('.'),
          message: err.message,
          code: err.code
        }));

        return res.status(400).json({
          error: 'Validation failed',
          details: errors
        });
      }

      return res.status(500).json({
        error: 'Validation error'
      });
    }
  };
}

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  // Schemas
  uuidSchema,
  emailSchema,
  urlSchema,
  dateSchema,
  paginationSchema,

  // Campaign schemas
  createCampaignSchema,
  updateCampaignSchema,
  queryCampaignsSchema,

  // Ad schemas
  createAdSchema,
  approveAdSchema,

  // A/B test schemas
  createABTestSchema,
  updateABTestSchema,

  // Publishing schemas
  publishMetaSchema,
  publishMultiPlatformSchema,

  // Google Ads schemas
  createGoogleCampaignSchema,
  createGoogleVideoAdSchema,

  // Image generation schemas
  generateImageSchema,

  // Analytics schemas
  analyticsQuerySchema,

  // File upload schemas
  videoUploadSchema,
  analyzeFolderSchema,

  // Auth schemas
  registerUserSchema,
  loginUserSchema,
  resetPasswordSchema,
  updatePasswordSchema,

  // Webhook schemas
  metaWebhookSchema,

  // Middleware
  validateZod,
  validateBody,
  validateQuery,
  validateParams,
  validateRequest
};
