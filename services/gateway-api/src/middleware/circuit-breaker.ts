/**
 * Circuit Breaker Middleware - Agent 25
 *
 * Provides circuit breaker protection for external API calls to prevent
 * cascading failures when external services are degraded or unavailable.
 *
 * Protected Services:
 * - Meta API (Facebook Marketing API via meta-publisher)
 * - HubSpot API (CRM webhooks and data sync)
 * - Google APIs (Cloud Storage, Ads, Generative AI)
 *
 * Circuit Breaker States:
 * - CLOSED: Normal operation, requests pass through
 * - OPEN: Service is failing, requests fail fast
 * - HALF_OPEN: Testing if service has recovered
 *
 * Configuration:
 * - timeout: Maximum time to wait for function execution (ms)
 * - errorThresholdPercentage: Error rate to trigger circuit open (%)
 * - resetTimeout: Time to wait before testing recovery (ms)
 * - volumeThreshold: Minimum requests before circuit can open
 *
 * Created: 2025-12-13
 * Agent: 25 - Add Circuit Breakers
 */

import CircuitBreaker from 'opossum';
import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';
import { monitoring } from '../services/monitoring';

/**
 * Circuit breaker configuration interface
 */
export interface CircuitBreakerConfig {
  timeout: number;                    // How long to wait for function execution (ms)
  errorThresholdPercentage: number;   // Error percentage to trip breaker (0-100)
  resetTimeout: number;               // Time to wait before testing again (ms)
  volumeThreshold: number;            // Minimum calls before tripping
  name?: string;                      // Circuit breaker name for monitoring
}

/**
 * Default circuit breaker configuration
 * Conservative settings suitable for most external APIs
 */
const DEFAULT_CONFIG: CircuitBreakerConfig = {
  timeout: 10000,              // 10 seconds
  errorThresholdPercentage: 50, // Trip at 50% error rate
  resetTimeout: 30000,          // Wait 30s before retry
  volumeThreshold: 5,           // Need 5+ requests before tripping
};

/**
 * Meta API specific configuration
 * Meta API can be slower, so we give it more time
 */
const META_API_CONFIG: CircuitBreakerConfig = {
  timeout: 15000,              // 15 seconds for Meta API
  errorThresholdPercentage: 50,
  resetTimeout: 60000,          // Wait 1 minute before retry
  volumeThreshold: 3,           // Trip faster for critical service
  name: 'meta-api',
};

/**
 * HubSpot API specific configuration
 * HubSpot is critical for revenue tracking
 */
const HUBSPOT_API_CONFIG: CircuitBreakerConfig = {
  timeout: 10000,
  errorThresholdPercentage: 40, // More sensitive to errors
  resetTimeout: 45000,           // Wait 45s before retry
  volumeThreshold: 5,
  name: 'hubspot-api',
};

/**
 * Google APIs specific configuration
 * Google services are generally reliable
 */
const GOOGLE_API_CONFIG: CircuitBreakerConfig = {
  timeout: 12000,               // 12 seconds
  errorThresholdPercentage: 50,
  resetTimeout: 30000,
  volumeThreshold: 5,
  name: 'google-api',
};

// ============================================================================
// Meta API Circuit Breaker
// ============================================================================

/**
 * Meta API call wrapper function
 * Handles requests to Meta Marketing API via meta-publisher service
 */
async function metaApiCall(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse> {
  const META_PUBLISHER_URL = process.env.META_PUBLISHER_URL || 'http://localhost:8083';

  const fullUrl = url.startsWith('http') ? url : `${META_PUBLISHER_URL}${url}`;

  monitoring.log('debug', `[Circuit Breaker] Meta API call: ${fullUrl}`);

  return axios(fullUrl, {
    ...config,
    timeout: META_API_CONFIG.timeout,
  });
}

/**
 * Meta API Circuit Breaker instance
 */
export const metaApiBreaker = new CircuitBreaker(metaApiCall, {
  timeout: META_API_CONFIG.timeout,
  errorThresholdPercentage: META_API_CONFIG.errorThresholdPercentage,
  resetTimeout: META_API_CONFIG.resetTimeout,
  volumeThreshold: META_API_CONFIG.volumeThreshold,
  name: META_API_CONFIG.name,
});

// Event handlers for Meta API circuit breaker
metaApiBreaker.on('open', () => {
  monitoring.log('error', '[Circuit Breaker] Meta API circuit breaker OPENED - failing fast');
  monitoring.recordError('circuit_breaker_open', 'meta-api');
});

metaApiBreaker.on('halfOpen', () => {
  monitoring.log('warn', '[Circuit Breaker] Meta API circuit breaker HALF-OPEN - testing recovery');
});

metaApiBreaker.on('close', () => {
  monitoring.log('info', '[Circuit Breaker] Meta API circuit breaker CLOSED - service recovered');
});

metaApiBreaker.on('failure', (error) => {
  monitoring.log('warn', `[Circuit Breaker] Meta API call failed: ${error.message}`);
});

metaApiBreaker.on('timeout', () => {
  monitoring.log('error', `[Circuit Breaker] Meta API call timed out after ${META_API_CONFIG.timeout}ms`);
  monitoring.recordError('circuit_breaker_timeout', 'meta-api');
});

// ============================================================================
// HubSpot API Circuit Breaker
// ============================================================================

/**
 * HubSpot API call wrapper function
 * Handles requests to HubSpot CRM API
 */
async function hubspotApiCall(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse> {
  const HUBSPOT_API_BASE_URL = 'https://api.hubapi.com';
  const HUBSPOT_ACCESS_TOKEN = process.env.HUBSPOT_ACCESS_TOKEN || '';

  const fullUrl = url.startsWith('http') ? url : `${HUBSPOT_API_BASE_URL}${url}`;

  monitoring.log('debug', `[Circuit Breaker] HubSpot API call: ${fullUrl}`);

  return axios(fullUrl, {
    ...config,
    headers: {
      'Authorization': `Bearer ${HUBSPOT_ACCESS_TOKEN}`,
      'Content-Type': 'application/json',
      ...config?.headers,
    },
    timeout: HUBSPOT_API_CONFIG.timeout,
  });
}

/**
 * HubSpot API Circuit Breaker instance
 */
export const hubspotBreaker = new CircuitBreaker(hubspotApiCall, {
  timeout: HUBSPOT_API_CONFIG.timeout,
  errorThresholdPercentage: HUBSPOT_API_CONFIG.errorThresholdPercentage,
  resetTimeout: HUBSPOT_API_CONFIG.resetTimeout,
  volumeThreshold: HUBSPOT_API_CONFIG.volumeThreshold,
  name: HUBSPOT_API_CONFIG.name,
});

// Event handlers for HubSpot circuit breaker
hubspotBreaker.on('open', () => {
  monitoring.log('error', '[Circuit Breaker] HubSpot API circuit breaker OPENED - failing fast');
  monitoring.recordError('circuit_breaker_open', 'hubspot-api');
});

hubspotBreaker.on('halfOpen', () => {
  monitoring.log('warn', '[Circuit Breaker] HubSpot API circuit breaker HALF-OPEN - testing recovery');
});

hubspotBreaker.on('close', () => {
  monitoring.log('info', '[Circuit Breaker] HubSpot API circuit breaker CLOSED - service recovered');
});

hubspotBreaker.on('failure', (error) => {
  monitoring.log('warn', `[Circuit Breaker] HubSpot API call failed: ${error.message}`);
});

hubspotBreaker.on('timeout', () => {
  monitoring.log('error', `[Circuit Breaker] HubSpot API call timed out after ${HUBSPOT_API_CONFIG.timeout}ms`);
  monitoring.recordError('circuit_breaker_timeout', 'hubspot-api');
});

// ============================================================================
// Google APIs Circuit Breaker
// ============================================================================

/**
 * Google API call wrapper function
 * Handles requests to various Google services (Cloud Storage, Ads, AI)
 */
async function googleApiCall(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse> {
  monitoring.log('debug', `[Circuit Breaker] Google API call: ${url}`);

  return axios(url, {
    ...config,
    timeout: GOOGLE_API_CONFIG.timeout,
  });
}

/**
 * Google API Circuit Breaker instance
 */
export const googleBreaker = new CircuitBreaker(googleApiCall, {
  timeout: GOOGLE_API_CONFIG.timeout,
  errorThresholdPercentage: GOOGLE_API_CONFIG.errorThresholdPercentage,
  resetTimeout: GOOGLE_API_CONFIG.resetTimeout,
  volumeThreshold: GOOGLE_API_CONFIG.volumeThreshold,
  name: GOOGLE_API_CONFIG.name,
});

// Event handlers for Google API circuit breaker
googleBreaker.on('open', () => {
  monitoring.log('error', '[Circuit Breaker] Google API circuit breaker OPENED - failing fast');
  monitoring.recordError('circuit_breaker_open', 'google-api');
});

googleBreaker.on('halfOpen', () => {
  monitoring.log('warn', '[Circuit Breaker] Google API circuit breaker HALF-OPEN - testing recovery');
});

googleBreaker.on('close', () => {
  monitoring.log('info', '[Circuit Breaker] Google API circuit breaker CLOSED - service recovered');
});

googleBreaker.on('failure', (error) => {
  monitoring.log('warn', `[Circuit Breaker] Google API call failed: ${error.message}`);
});

googleBreaker.on('timeout', () => {
  monitoring.log('error', `[Circuit Breaker] Google API call timed out after ${GOOGLE_API_CONFIG.timeout}ms`);
  monitoring.recordError('circuit_breaker_timeout', 'google-api');
});

// ============================================================================
// Generic Wrapper Functions
// ============================================================================

/**
 * Execute a function with circuit breaker protection
 *
 * @param breaker - Circuit breaker instance to use
 * @param fn - Async function to execute
 * @returns Promise with the function result
 *
 * @example
 * ```typescript
 * const result = await withCircuitBreaker(
 *   metaApiBreaker,
 *   () => axios.post('/api/meta/ads', adData)
 * );
 * ```
 */
export async function withCircuitBreaker<T>(
  breaker: CircuitBreaker,
  fn: () => Promise<T>
): Promise<T> {
  return breaker.fire(fn);
}

/**
 * Execute a Meta API call with circuit breaker protection
 *
 * @param url - API endpoint (relative or absolute)
 * @param config - Axios request configuration
 * @returns Promise with the API response
 *
 * @example
 * ```typescript
 * const response = await callMetaApi('/publish/meta', {
 *   method: 'POST',
 *   data: { ad_id: '123', creative_id: '456' }
 * });
 * ```
 */
export async function callMetaApi(
  url: string,
  config?: AxiosRequestConfig
): Promise<AxiosResponse> {
  return metaApiBreaker.fire(url, config);
}

/**
 * Execute a HubSpot API call with circuit breaker protection
 *
 * @param url - API endpoint (relative or absolute)
 * @param config - Axios request configuration
 * @returns Promise with the API response
 *
 * @example
 * ```typescript
 * const response = await callHubSpotApi('/crm/v3/objects/deals/123', {
 *   method: 'GET'
 * });
 * ```
 */
export async function callHubSpotApi(
  url: string,
  config?: AxiosRequestConfig
): Promise<AxiosResponse> {
  return hubspotBreaker.fire(url, config);
}

/**
 * Execute a Google API call with circuit breaker protection
 *
 * @param url - Full API endpoint URL
 * @param config - Axios request configuration
 * @returns Promise with the API response
 *
 * @example
 * ```typescript
 * const response = await callGoogleApi(
 *   'https://ads.googleapis.com/v14/customers/123/campaigns',
 *   {
 *     method: 'GET',
 *     headers: { Authorization: `Bearer ${token}` }
 *   }
 * );
 * ```
 */
export async function callGoogleApi(
  url: string,
  config?: AxiosRequestConfig
): Promise<AxiosResponse> {
  return googleBreaker.fire(url, config);
}

// ============================================================================
// Advanced Helper Functions
// ============================================================================

/**
 * Execute multiple API calls with circuit breaker protection in parallel
 * Fails fast if any circuit breaker is open
 *
 * @param calls - Array of circuit breaker call tuples [breaker, fn]
 * @returns Promise with array of results
 *
 * @example
 * ```typescript
 * const [metaResult, hubspotResult] = await executeParallel([
 *   [metaApiBreaker, () => axios.get('/api/meta/insights')],
 *   [hubspotBreaker, () => axios.get('/crm/v3/objects/deals')]
 * ]);
 * ```
 */
export async function executeParallel<T>(
  calls: Array<[CircuitBreaker, () => Promise<T>]>
): Promise<T[]> {
  return Promise.all(
    calls.map(([breaker, fn]) => breaker.fire(fn))
  );
}

/**
 * Execute API calls with fallback if circuit breaker is open
 *
 * @param breaker - Circuit breaker instance
 * @param fn - Primary function to execute
 * @param fallbackFn - Fallback function if circuit is open
 * @returns Promise with result from primary or fallback function
 *
 * @example
 * ```typescript
 * const result = await executeWithFallback(
 *   metaApiBreaker,
 *   () => axios.get('/api/meta/insights'),
 *   () => getCachedInsights() // Use cached data if Meta API is down
 * );
 * ```
 */
export async function executeWithFallback<T>(
  breaker: CircuitBreaker,
  fn: () => Promise<T>,
  fallbackFn: () => Promise<T>
): Promise<T> {
  try {
    return await breaker.fire(fn);
  } catch (error: any) {
    // If circuit is open, use fallback
    if (error.message && error.message.includes('circuit')) {
      monitoring.log('warn', `[Circuit Breaker] Using fallback due to open circuit`);
      return fallbackFn();
    }
    // Otherwise, rethrow the original error
    throw error;
  }
}

/**
 * Get circuit breaker statistics for monitoring
 *
 * @param breaker - Circuit breaker instance
 * @returns Statistics object
 */
export function getCircuitBreakerStats(breaker: CircuitBreaker): {
  state: string;
  stats: any;
} {
  return {
    state: breaker.opened ? 'open' : breaker.halfOpen ? 'half-open' : 'closed',
    stats: breaker.stats,
  };
}

/**
 * Get all circuit breaker statuses for health checks
 *
 * @returns Object with all circuit breaker states
 */
export function getAllCircuitBreakerStatuses(): {
  meta: any;
  hubspot: any;
  google: any;
} {
  return {
    meta: getCircuitBreakerStats(metaApiBreaker),
    hubspot: getCircuitBreakerStats(hubspotBreaker),
    google: getCircuitBreakerStats(googleBreaker),
  };
}

/**
 * Reset all circuit breakers (use with caution)
 * Useful for manual intervention or testing
 */
export function resetAllCircuitBreakers(): void {
  monitoring.log('warn', '[Circuit Breaker] Manually resetting all circuit breakers');

  metaApiBreaker.close();
  hubspotBreaker.close();
  googleBreaker.close();
}

// ============================================================================
// Exports
// ============================================================================

export default {
  // Circuit breaker instances
  metaApiBreaker,
  hubspotBreaker,
  googleBreaker,

  // Wrapper functions
  withCircuitBreaker,
  callMetaApi,
  callHubSpotApi,
  callGoogleApi,

  // Advanced helpers
  executeParallel,
  executeWithFallback,

  // Monitoring
  getCircuitBreakerStats,
  getAllCircuitBreakerStatuses,
  resetAllCircuitBreakers,
};
