/**
 * API Versioning Middleware (Agent 24)
 * Provides version management for API endpoints
 */
import { Router, Request, Response, NextFunction } from 'express';

export const API_VERSION = 'v1';
export const API_PREFIX = `/api/${API_VERSION}`;

/**
 * Middleware to extract and set API version from headers or URL
 * Allows clients to specify version via 'api-version' header
 */
export function apiVersionMiddleware(req: Request, res: Response, next: NextFunction) {
  // Extract version from header or default to current version
  const version = req.headers['api-version'] || API_VERSION;

  // Attach version to request object for downstream use
  (req as any).apiVersion = version as string;

  next();
}

/**
 * Creates a versioned router with automatic version headers
 * Adds X-API-Version header to all responses
 */
export function createVersionedRouter(): Router {
  const router = Router();

  // Add version header to all responses from this router
  router.use((req: Request, res: Response, next: NextFunction) => {
    res.setHeader('X-API-Version', API_VERSION);
    next();
  });

  return router;
}

/**
 * Helper to create deprecation warning for old API versions
 */
export function deprecationWarning(deprecatedVersion: string, sunsetDate: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    res.setHeader('Deprecation', 'true');
    res.setHeader('Sunset', sunsetDate);
    res.setHeader('Link', `<${API_PREFIX}>; rel="successor-version"`);
    console.warn(`⚠️ Deprecated API version ${deprecatedVersion} accessed: ${req.method} ${req.path}`);
    next();
  };
}

/**
 * Middleware to validate API version
 * Returns 400 if unsupported version is requested
 */
export function validateApiVersion(supportedVersions: string[] = ['v1']) {
  return (req: Request, res: Response, next: NextFunction) => {
    const requestedVersion = req.headers['api-version'] as string;

    if (requestedVersion && !supportedVersions.includes(requestedVersion)) {
      return res.status(400).json({
        error: 'Unsupported API Version',
        message: `API version '${requestedVersion}' is not supported`,
        supportedVersions,
        currentVersion: API_VERSION
      });
    }

    next();
  };
}

/**
 * Version information endpoint handler
 */
export function versionInfoHandler(req: Request, res: Response) {
  res.json({
    currentVersion: API_VERSION,
    apiPrefix: API_PREFIX,
    supportedVersions: ['v1'],
    deprecatedVersions: [],
    endpoints: {
      campaigns: `${API_PREFIX}/campaigns`,
      analytics: `${API_PREFIX}/analytics`,
      abTests: `${API_PREFIX}/ab-tests`,
      ads: `${API_PREFIX}/ads`,
      predictions: `${API_PREFIX}/predictions`,
      onboarding: `${API_PREFIX}/onboarding`,
      demo: `${API_PREFIX}/demo`,
      alerts: `${API_PREFIX}/alerts`,
      reports: `${API_PREFIX}/reports`,
      streaming: `${API_PREFIX}/streaming`,
      imageGeneration: `${API_PREFIX}/image`,
      mlProxy: `${API_PREFIX}/ml`,
      roasDashboard: `${API_PREFIX}/roas-dashboard`
    }
  });
}
