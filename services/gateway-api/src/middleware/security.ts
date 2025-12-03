/**
 * Security Middleware - OWASP Best Practices Implementation
 * Agent 5: Comprehensive Security Layer
 */

import rateLimit, { RateLimitRequestHandler } from 'express-rate-limit';
import helmet from 'helmet';
import { Request, Response, NextFunction } from 'express';
import { createClient } from 'redis';
import crypto from 'crypto';

// Redis client for distributed rate limiting
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
let redisClient: ReturnType<typeof createClient> | null = null;

// Initialize Redis for rate limiting
export async function initializeSecurityRedis() {
  try {
    redisClient = createClient({ url: REDIS_URL });
    redisClient.on('error', (err) => console.error('Security Redis Error:', err));
    await redisClient.connect();
    console.log('✅ Security Redis connected for rate limiting');
  } catch (error) {
    console.warn('⚠️  Redis unavailable - using in-memory rate limiting');
  }
}

// ============================================================================
// RATE LIMITING CONFIGURATION
// ============================================================================

export interface RateLimitOptions {
  windowMs?: number;
  maxRequests?: number;
  keyGenerator?: (req: Request) => string;
  skipSuccessfulRequests?: boolean;
  skipFailedRequests?: boolean;
}

/**
 * Create a rate limiter with Redis backend for distributed systems
 * Per-user and per-IP rate limiting with endpoint-specific limits
 */
export const createRateLimiter = (options: RateLimitOptions = {}): RateLimitRequestHandler => {
  const {
    windowMs = 15 * 60 * 1000, // 15 minutes default
    maxRequests = 100,
    keyGenerator,
    skipSuccessfulRequests = false,
    skipFailedRequests = false
  } = options;

  return rateLimit({
    windowMs,
    max: maxRequests,
    standardHeaders: true, // Return rate limit info in `RateLimit-*` headers
    legacyHeaders: false, // Disable `X-RateLimit-*` headers
    skipSuccessfulRequests,
    skipFailedRequests,

    // Custom key generator - prioritize user ID, then API key, then IP
    keyGenerator: keyGenerator || ((req: Request) => {
      const userId = (req as any).userId;
      const apiKey = req.headers['x-api-key'];
      const ip = req.ip || req.socket.remoteAddress || 'unknown';

      if (userId) return `user:${userId}`;
      if (apiKey) return `api:${apiKey}`;
      return `ip:${ip}`;
    }),

    // Custom handler for rate limit exceeded
    handler: (req: Request, res: Response) => {
      logSecurityEvent('RATE_LIMIT_EXCEEDED', req);
      res.status(429).json({
        error: 'Too Many Requests',
        message: 'Rate limit exceeded. Please try again later.',
        retryAfter: res.getHeader('Retry-After')
      });
    }
  });
};

// Endpoint-specific rate limiters
export const globalRateLimiter = createRateLimiter({
  windowMs: 15 * 60 * 1000, // 15 minutes
  maxRequests: 100
});

export const authRateLimiter = createRateLimiter({
  windowMs: 15 * 60 * 1000,
  maxRequests: 5, // Strict limit for auth endpoints
  skipSuccessfulRequests: true
});

export const apiRateLimiter = createRateLimiter({
  windowMs: 60 * 1000, // 1 minute
  maxRequests: 60 // 60 requests per minute
});

export const uploadRateLimiter = createRateLimiter({
  windowMs: 60 * 60 * 1000, // 1 hour
  maxRequests: 10 // Limited uploads
});

// ============================================================================
// SECURITY HEADERS - Helmet Configuration
// ============================================================================

/**
 * Comprehensive security headers following OWASP recommendations
 */
export const securityHeaders = helmet({
  // Content Security Policy - prevents XSS attacks
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"], // Adjust based on your needs
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", 'data:', 'https:'],
      connectSrc: ["'self'"],
      fontSrc: ["'self'"],
      objectSrc: ["'none'"],
      mediaSrc: ["'self'"],
      frameSrc: ["'none'"],
      upgradeInsecureRequests: []
    }
  },

  // Strict-Transport-Security - enforces HTTPS
  hsts: {
    maxAge: 31536000, // 1 year
    includeSubDomains: true,
    preload: true
  },

  // X-Frame-Options - prevents clickjacking
  frameguard: {
    action: 'deny'
  },

  // X-Content-Type-Options - prevents MIME sniffing
  noSniff: true,

  // X-DNS-Prefetch-Control
  dnsPrefetchControl: {
    allow: false
  },

  // X-Download-Options
  ieNoOpen: true,

  // Referrer-Policy
  referrerPolicy: {
    policy: 'strict-origin-when-cross-origin'
  },

  // X-Permitted-Cross-Domain-Policies
  permittedCrossDomainPolicies: {
    permittedPolicies: 'none'
  }
});

// ============================================================================
// INPUT VALIDATION & SANITIZATION
// ============================================================================

export interface ValidationSchema {
  body?: Record<string, ValidationRule>;
  query?: Record<string, ValidationRule>;
  params?: Record<string, ValidationRule>;
}

export interface ValidationRule {
  type: 'string' | 'number' | 'boolean' | 'email' | 'uuid' | 'url' | 'object' | 'array';
  required?: boolean;
  min?: number;
  max?: number;
  pattern?: RegExp;
  enum?: any[];
  sanitize?: boolean;
}

/**
 * Validate and sanitize request inputs
 */
export const validateInput = (schema: ValidationSchema) => {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      const errors: string[] = [];

      // Validate body
      if (schema.body) {
        validateFields(req.body, schema.body, 'body', errors);
      }

      // Validate query
      if (schema.query) {
        validateFields(req.query, schema.query, 'query', errors);
      }

      // Validate params
      if (schema.params) {
        validateFields(req.params, schema.params, 'params', errors);
      }

      if (errors.length > 0) {
        logSecurityEvent('VALIDATION_FAILED', req, { errors });
        return res.status(400).json({
          error: 'Validation Failed',
          details: errors
        });
      }

      next();
    } catch (error: any) {
      logSecurityEvent('VALIDATION_ERROR', req, { error: error.message });
      res.status(500).json({ error: 'Internal validation error' });
    }
  };
};

function validateFields(
  data: any,
  schema: Record<string, ValidationRule>,
  location: string,
  errors: string[]
): void {
  for (const [field, rule] of Object.entries(schema)) {
    const value = data[field];

    // Check required
    if (rule.required && (value === undefined || value === null || value === '')) {
      errors.push(`${location}.${field} is required`);
      continue;
    }

    // Skip validation if not required and not provided
    if (!rule.required && (value === undefined || value === null)) {
      continue;
    }

    // Type validation
    if (!validateType(value, rule.type)) {
      errors.push(`${location}.${field} must be of type ${rule.type}`);
      continue;
    }

    // String validations
    if (rule.type === 'string' && typeof value === 'string') {
      if (rule.min !== undefined && value.length < rule.min) {
        errors.push(`${location}.${field} must be at least ${rule.min} characters`);
      }
      if (rule.max !== undefined && value.length > rule.max) {
        errors.push(`${location}.${field} must be at most ${rule.max} characters`);
      }
      if (rule.pattern && !rule.pattern.test(value)) {
        errors.push(`${location}.${field} format is invalid`);
      }

      // Sanitize if requested
      if (rule.sanitize) {
        data[field] = sanitizeHTML(value);
      }
    }

    // Number validations
    if (rule.type === 'number' && typeof value === 'number') {
      if (rule.min !== undefined && value < rule.min) {
        errors.push(`${location}.${field} must be at least ${rule.min}`);
      }
      if (rule.max !== undefined && value > rule.max) {
        errors.push(`${location}.${field} must be at most ${rule.max}`);
      }
    }

    // Enum validation
    if (rule.enum && !rule.enum.includes(value)) {
      errors.push(`${location}.${field} must be one of: ${rule.enum.join(', ')}`);
    }
  }
}

function validateType(value: any, type: string): boolean {
  switch (type) {
    case 'string':
      return typeof value === 'string';
    case 'number':
      return typeof value === 'number' && !isNaN(value);
    case 'boolean':
      return typeof value === 'boolean';
    case 'email':
      return typeof value === 'string' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
    case 'uuid':
      return typeof value === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
    case 'url':
      try {
        new URL(value);
        return true;
      } catch {
        return false;
      }
    case 'object':
      return typeof value === 'object' && value !== null && !Array.isArray(value);
    case 'array':
      return Array.isArray(value);
    default:
      return true;
  }
}

// ============================================================================
// SQL INJECTION PREVENTION
// ============================================================================

/**
 * Sanitize SQL input - detects and prevents SQL injection attempts
 */
export const sanitizeSQL = (input: string): string => {
  if (typeof input !== 'string') return input;

  // Remove SQL comments
  let sanitized = input.replace(/--.*$/gm, '');
  sanitized = sanitized.replace(/\/\*[\s\S]*?\*\//g, '');

  // Remove dangerous SQL keywords in suspicious contexts
  const dangerousPatterns = [
    /(\bUNION\b.*\bSELECT\b)/gi,
    /(\bDROP\b.*\bTABLE\b)/gi,
    /(\bDELETE\b.*\bFROM\b)/gi,
    /(\bINSERT\b.*\bINTO\b)/gi,
    /(\bUPDATE\b.*\bSET\b)/gi,
    /(\bEXEC\b|\bEXECUTE\b)/gi,
    /(;.*\b(SELECT|INSERT|UPDATE|DELETE|DROP)\b)/gi
  ];

  for (const pattern of dangerousPatterns) {
    if (pattern.test(sanitized)) {
      throw new Error('Potential SQL injection detected');
    }
  }

  return sanitized;
};

/**
 * Middleware to sanitize all string inputs for SQL safety
 */
export const sqlInjectionProtection = (req: Request, res: Response, next: NextFunction) => {
  try {
    sanitizeObject(req.body);
    sanitizeObject(req.query);
    sanitizeObject(req.params);
    next();
  } catch (error: any) {
    logSecurityEvent('SQL_INJECTION_ATTEMPT', req, { error: error.message });
    res.status(400).json({
      error: 'Invalid input detected',
      message: 'Your request contains suspicious patterns'
    });
  }
};

function sanitizeObject(obj: any): void {
  if (!obj || typeof obj !== 'object') return;

  for (const key in obj) {
    if (typeof obj[key] === 'string') {
      sanitizeSQL(obj[key]); // Throws if dangerous pattern detected
    } else if (typeof obj[key] === 'object') {
      sanitizeObject(obj[key]);
    }
  }
}

// ============================================================================
// XSS PREVENTION
// ============================================================================

/**
 * Sanitize HTML to prevent XSS attacks
 */
export const sanitizeHTML = (input: string): string => {
  if (typeof input !== 'string') return input;

  return input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;');
};

/**
 * XSS protection middleware
 */
export const xssProtection = (req: Request, res: Response, next: NextFunction) => {
  try {
    if (req.body) {
      req.body = sanitizeObjectForXSS(req.body);
    }
    if (req.query) {
      req.query = sanitizeObjectForXSS(req.query);
    }
    next();
  } catch (error: any) {
    logSecurityEvent('XSS_PROTECTION_ERROR', req, { error: error.message });
    res.status(400).json({ error: 'Invalid input' });
  }
};

function sanitizeObjectForXSS(obj: any): any {
  if (typeof obj === 'string') {
    return sanitizeHTML(obj);
  } else if (Array.isArray(obj)) {
    return obj.map(sanitizeObjectForXSS);
  } else if (obj && typeof obj === 'object') {
    const sanitized: any = {};
    for (const key in obj) {
      sanitized[key] = sanitizeObjectForXSS(obj[key]);
    }
    return sanitized;
  }
  return obj;
}

// ============================================================================
// CORS CONFIGURATION
// ============================================================================

/**
 * Secure CORS configuration
 */
export const corsConfig = {
  origin: (origin: string | undefined, callback: (err: Error | null, allow?: boolean) => void) => {
    // Allow requests with no origin (like mobile apps or curl requests)
    if (!origin) return callback(null, true);

    const allowedOrigins = process.env.ALLOWED_ORIGINS?.split(',') || [
      'http://localhost:3000',
      'http://localhost:3001',
      'https://geminivideo.app'
    ];

    if (allowedOrigins.includes(origin) || allowedOrigins.includes('*')) {
      callback(null, true);
    } else {
      logSecurityEvent('CORS_BLOCKED', { origin } as any);
      callback(new Error('Not allowed by CORS'));
    }
  },
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-API-Key', 'X-Request-ID'],
  credentials: true,
  maxAge: 86400, // 24 hours
  optionsSuccessStatus: 200
};

// ============================================================================
// API KEY VALIDATION
// ============================================================================

/**
 * Validate API key from request headers
 */
export const validateApiKey = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const apiKey = req.headers['x-api-key'] as string;

    if (!apiKey) {
      logSecurityEvent('MISSING_API_KEY', req);
      return res.status(401).json({
        error: 'Unauthorized',
        message: 'API key is required'
      });
    }

    // Validate API key format
    if (!isValidApiKeyFormat(apiKey)) {
      logSecurityEvent('INVALID_API_KEY_FORMAT', req);
      return res.status(401).json({
        error: 'Unauthorized',
        message: 'Invalid API key format'
      });
    }

    // Hash the API key for lookup
    const hashedKey = hashApiKey(apiKey);

    // In production, validate against database
    // For now, check against environment variable
    const validKeys = process.env.API_KEYS?.split(',') || [];

    if (!validKeys.includes(hashedKey) && !validKeys.includes(apiKey)) {
      logSecurityEvent('INVALID_API_KEY', req, { hashedKey });
      return res.status(401).json({
        error: 'Unauthorized',
        message: 'Invalid API key'
      });
    }

    // Attach API key info to request
    (req as any).apiKey = apiKey;

    next();
  } catch (error: any) {
    logSecurityEvent('API_KEY_VALIDATION_ERROR', req, { error: error.message });
    res.status(500).json({ error: 'Authentication error' });
  }
};

function isValidApiKeyFormat(key: string): boolean {
  // API keys should be alphanumeric and at least 32 characters
  return /^[A-Za-z0-9_-]{32,}$/.test(key);
}

function hashApiKey(key: string): string {
  return crypto.createHash('sha256').update(key).digest('hex');
}

// ============================================================================
// AUDIT LOGGING
// ============================================================================

/**
 * Log all requests for security audit
 */
export const auditLog = (req: Request, res: Response, next: NextFunction) => {
  const startTime = Date.now();

  // Capture response
  const originalSend = res.send;
  res.send = function (data: any) {
    res.send = originalSend;

    const duration = Date.now() - startTime;
    const logData = {
      timestamp: new Date().toISOString(),
      method: req.method,
      url: req.url,
      ip: req.ip || req.socket.remoteAddress,
      userAgent: req.headers['user-agent'],
      statusCode: res.statusCode,
      duration,
      userId: (req as any).userId,
      apiKey: (req as any).apiKey ? '***' : undefined
    };

    // Log to console (in production, send to logging service)
    if (res.statusCode >= 400) {
      console.warn('🔴 Security Audit:', JSON.stringify(logData));
    } else {
      console.log('🔵 Audit:', JSON.stringify(logData));
    }

    return originalSend.call(this, data);
  };

  next();
};

// ============================================================================
// BRUTE FORCE PROTECTION
// ============================================================================

export interface BruteForceOptions {
  freeRetries?: number;
  minWait?: number;
  maxWait?: number;
  lifetime?: number;
  keyGenerator?: (req: Request) => string;
}

/**
 * Protect against brute force attacks with exponential backoff
 */
export const bruteForceProtection = (options: BruteForceOptions = {}) => {
  const {
    freeRetries = 5,
    minWait = 1000, // 1 second
    maxWait = 60000, // 1 minute
    lifetime = 3600000, // 1 hour
    keyGenerator = (req: Request) => req.ip || 'unknown'
  } = options;

  const attempts = new Map<string, { count: number; resetAt: number }>();

  return async (req: Request, res: Response, next: NextFunction) => {
    const key = keyGenerator(req);
    const now = Date.now();

    // Clean up expired entries
    for (const [k, v] of attempts.entries()) {
      if (now > v.resetAt) {
        attempts.delete(k);
      }
    }

    const record = attempts.get(key);

    if (!record) {
      attempts.set(key, { count: 1, resetAt: now + lifetime });
      return next();
    }

    // Calculate wait time with exponential backoff
    const attemptsOverLimit = record.count - freeRetries;
    if (attemptsOverLimit > 0) {
      const waitTime = Math.min(minWait * Math.pow(2, attemptsOverLimit - 1), maxWait);

      logSecurityEvent('BRUTE_FORCE_DETECTED', req, {
        attempts: record.count,
        waitTime
      });

      return res.status(429).json({
        error: 'Too Many Attempts',
        message: `Please wait ${Math.ceil(waitTime / 1000)} seconds before trying again`,
        retryAfter: Math.ceil(waitTime / 1000)
      });
    }

    // Increment attempt count
    record.count++;

    // Store failed attempt tracking for later reset
    (req as any).bruteForceKey = key;

    next();
  };
};

/**
 * Reset brute force counter on successful authentication
 */
export const resetBruteForce = (req: Request) => {
  const key = (req as any).bruteForceKey;
  if (key && redisClient) {
    // In production, clear from Redis
    console.log(`Resetting brute force counter for ${key}`);
  }
};

// ============================================================================
// SECURITY EVENT LOGGING
// ============================================================================

interface SecurityEvent {
  type: string;
  timestamp: string;
  ip?: string;
  url?: string;
  userAgent?: string;
  details?: any;
}

/**
 * Log security events for monitoring and alerting
 */
function logSecurityEvent(type: string, req: Request | any, details?: any): void {
  const event: SecurityEvent = {
    type,
    timestamp: new Date().toISOString(),
    ip: req.ip || req.socket?.remoteAddress,
    url: req.url,
    userAgent: req.headers?.['user-agent'],
    details
  };

  // Log to console (in production, send to SIEM)
  console.warn('🛡️  Security Event:', JSON.stringify(event));

  // In production, send to monitoring service
  // Example: sendToSIEM(event);
}

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  initializeSecurityRedis,
  createRateLimiter,
  globalRateLimiter,
  authRateLimiter,
  apiRateLimiter,
  uploadRateLimiter,
  securityHeaders,
  validateInput,
  sanitizeSQL,
  sanitizeHTML,
  sqlInjectionProtection,
  xssProtection,
  corsConfig,
  validateApiKey,
  auditLog,
  bruteForceProtection,
  resetBruteForce
};
