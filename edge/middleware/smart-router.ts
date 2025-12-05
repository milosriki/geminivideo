/**
 * Edge Middleware: Smart Router
 * Intelligent request routing based on location, load, and performance
 */

import { CloudflareEnv } from '../types/env';

interface RoutingDecision {
  destination: 'edge' | 'origin' | 'cached';
  endpoint: string;
  reason: string;
}

export class SmartRouter {
  constructor(private env: CloudflareEnv) {}

  /**
   * Decide where to route the request
   * @param request - Incoming request
   * @returns Routing decision
   */
  async route(request: Request): Promise<RoutingDecision> {
    const url = new URL(request.url);
    const path = url.pathname;
    const cf = (request as any).cf;

    // Get client location
    const country = cf?.country || 'US';
    const colo = cf?.colo || 'unknown'; // Cloudflare data center

    console.log(`[Smart Router] Request from ${country} (${colo}): ${path}`);

    // Route to edge for latency-critical endpoints
    if (this.isEdgeCacheable(path)) {
      return {
        destination: 'edge',
        endpoint: this.getEdgeEndpoint(path),
        reason: 'Edge-cacheable endpoint',
      };
    }

    // Route to origin for complex operations
    if (this.requiresOrigin(path)) {
      return {
        destination: 'origin',
        endpoint: this.env.ORIGIN_URL + path,
        reason: 'Requires origin processing',
      };
    }

    // Default: try cache, fallback to origin
    return {
      destination: 'cached',
      endpoint: this.env.ORIGIN_URL + path,
      reason: 'Default routing with cache fallback',
    };
  }

  /**
   * Check if endpoint should be handled at edge
   */
  private isEdgeCacheable(path: string): boolean {
    const edgePaths = [
      '/api/predict-quick',
      '/api/score-cached',
      '/api/hooks/trending',
      '/api/ab/assign',
      '/api/assets', // Static assets
      '/avatars',
    ];

    return edgePaths.some((p) => path.startsWith(p));
  }

  /**
   * Check if endpoint requires origin processing
   */
  private requiresOrigin(path: string): boolean {
    const originPaths = [
      '/api/generate', // Video generation
      '/api/render', // Rendering
      '/api/publish', // Publishing
      '/api/pipeline', // Full pipeline
      '/api/council', // AI Council
      '/api/oracle', // Oracle predictions
    ];

    return originPaths.some((p) => path.startsWith(p));
  }

  /**
   * Get edge endpoint URL
   */
  private getEdgeEndpoint(path: string): string {
    // Map to appropriate edge worker
    if (path.startsWith('/api/predict-quick')) {
      return 'https://prediction-cache.workers.dev' + path;
    }
    if (path.startsWith('/api/score-cached')) {
      return 'https://creative-scorer.workers.dev' + path;
    }
    if (path.startsWith('/api/hooks/trending')) {
      return 'https://trending-hooks.workers.dev' + path;
    }
    if (path.startsWith('/api/ab')) {
      return 'https://ab-router.workers.dev' + path;
    }

    // Fallback to origin
    return this.env.ORIGIN_URL + path;
  }

  /**
   * Select best origin based on load and latency
   */
  async selectOrigin(preferredRegion?: string): Promise<string> {
    // In production, this would check health and latency
    // For now, return configured origin
    return this.env.ORIGIN_URL;
  }

  /**
   * Get region-specific configuration
   */
  getRegionConfig(country: string): {
    preferredCDN: string;
    cacheTTL: number;
    originRegion: string;
  } {
    const regionMap: Record<string, any> = {
      US: {
        preferredCDN: 'cloudflare-us-east',
        cacheTTL: 300,
        originRegion: 'us-central1',
      },
      EU: {
        preferredCDN: 'cloudflare-eu-west',
        cacheTTL: 300,
        originRegion: 'europe-west1',
      },
      ASIA: {
        preferredCDN: 'cloudflare-asia-east',
        cacheTTL: 600, // Longer TTL for distant regions
        originRegion: 'asia-east1',
      },
    };

    // Map country to region
    const region = this.getRegion(country);
    return regionMap[region] || regionMap.US;
  }

  private getRegion(country: string): string {
    const euCountries = ['DE', 'FR', 'IT', 'ES', 'GB', 'NL', 'BE', 'SE', 'NO', 'DK'];
    const asiaCountries = ['CN', 'JP', 'KR', 'IN', 'SG', 'TH', 'VN', 'MY'];

    if (euCountries.includes(country)) return 'EU';
    if (asiaCountries.includes(country)) return 'ASIA';
    return 'US';
  }
}
