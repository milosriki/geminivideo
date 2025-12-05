/**
 * Edge Worker: Prediction Cache
 * Caches ML predictions at the edge for ultra-low latency
 * Deployed to Cloudflare Workers for global distribution
 */

import { CloudflareEnv, PredictionCache, CacheOptions } from '../types/env';

// Default cache TTL: 5 minutes
const DEFAULT_TTL = 300;
const STALE_WHILE_REVALIDATE = 600; // 10 minutes

export default {
  async fetch(request: Request, env: CloudflareEnv, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS headers for all responses
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    };

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // Route: GET /api/predict-quick/:creative_id
      if (path.match(/^\/api\/predict-quick\/(.+)$/) && request.method === 'GET') {
        const creativeId = path.split('/').pop()!;
        return await handlePredictionRequest(creativeId, env, ctx, corsHeaders);
      }

      // Route: POST /api/predict-quick (batch)
      if (path === '/api/predict-quick' && request.method === 'POST') {
        return await handleBatchPrediction(request, env, ctx, corsHeaders);
      }

      // Route: DELETE /api/predict-quick/:creative_id (cache invalidation)
      if (path.match(/^\/api\/predict-quick\/(.+)$/) && request.method === 'DELETE') {
        const creativeId = path.split('/').pop()!;
        return await handleCacheInvalidation(creativeId, env, corsHeaders);
      }

      // Route: GET /api/predict-quick/stats (cache statistics)
      if (path === '/api/predict-quick/stats' && request.method === 'GET') {
        return await handleCacheStats(env, corsHeaders);
      }

      // 404 for unknown routes
      return new Response('Not Found', {
        status: 404,
        headers: corsHeaders,
      });
    } catch (error: any) {
      console.error('Edge Worker Error:', error);
      return new Response(
        JSON.stringify({
          error: 'Internal Server Error',
          message: error.message,
          timestamp: new Date().toISOString(),
        }),
        {
          status: 500,
          headers: {
            ...corsHeaders,
            'Content-Type': 'application/json',
          },
        }
      );
    }
  },
};

async function handlePredictionRequest(
  creativeId: string,
  env: CloudflareEnv,
  ctx: ExecutionContext,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const cacheKey = `prediction:${creativeId}`;

  console.log(`[Edge] Checking cache for: ${cacheKey}`);

  // 1. Check KV cache
  const cached = await env.PREDICTIONS.get(cacheKey, 'json') as PredictionCache | null;

  if (cached) {
    const expiresAt = new Date(cached.expires_at);
    const now = new Date();

    // Check if cache is still valid
    if (expiresAt > now) {
      console.log(`[Edge] Cache HIT: ${cacheKey}`);

      // Track cache hit
      ctx.waitUntil(trackAnalytics(env, {
        event_type: 'impression',
        creative_id: creativeId,
        timestamp: new Date().toISOString(),
        metadata: { cache_hit: true },
      }));

      return new Response(JSON.stringify(cached), {
        status: 200,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
          'Cache-Control': `public, max-age=${Math.floor((expiresAt.getTime() - now.getTime()) / 1000)}`,
          'X-Cache': 'HIT',
          'X-Cache-Expires': cached.expires_at,
        },
      });
    }
  }

  console.log(`[Edge] Cache MISS: ${cacheKey}`);

  // 2. Forward to origin (ML service)
  const originUrl = `${env.ML_SERVICE_URL}/api/ml/predict-ctr/${creativeId}`;

  try {
    const originResponse = await fetch(originUrl, {
      headers: {
        'Authorization': `Bearer ${env.API_SECRET}`,
      },
    });

    if (!originResponse.ok) {
      throw new Error(`Origin returned ${originResponse.status}`);
    }

    const prediction = await originResponse.json();

    // 3. Cache the prediction
    const cacheTTL = parseInt(env.CACHE_TTL_SECONDS || String(DEFAULT_TTL));
    const expiresAt = new Date(Date.now() + cacheTTL * 1000);

    const cacheData: PredictionCache = {
      creative_id: creativeId,
      predicted_ctr: prediction.predicted_ctr,
      predicted_roas: prediction.predicted_roas,
      confidence: prediction.confidence,
      cached_at: new Date().toISOString(),
      expires_at: expiresAt.toISOString(),
    };

    // Store in KV (fire and forget)
    ctx.waitUntil(
      env.PREDICTIONS.put(cacheKey, JSON.stringify(cacheData), {
        expirationTtl: cacheTTL + STALE_WHILE_REVALIDATE,
      })
    );

    // Track cache miss
    ctx.waitUntil(trackAnalytics(env, {
      event_type: 'impression',
      creative_id: creativeId,
      timestamp: new Date().toISOString(),
      metadata: { cache_hit: false },
    }));

    return new Response(JSON.stringify(cacheData), {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
        'Cache-Control': `public, max-age=${cacheTTL}, stale-while-revalidate=${STALE_WHILE_REVALIDATE}`,
        'X-Cache': 'MISS',
      },
    });
  } catch (error: any) {
    console.error(`[Edge] Origin fetch failed: ${error.message}`);

    // Return stale cache if available
    if (cached) {
      console.log(`[Edge] Returning STALE cache: ${cacheKey}`);
      return new Response(JSON.stringify(cached), {
        status: 200,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
          'X-Cache': 'STALE',
          'Warning': '110 - "Response is stale"',
        },
      });
    }

    // No cache available, return error
    return new Response(
      JSON.stringify({
        error: 'Service Unavailable',
        message: 'ML service is unavailable and no cache exists',
      }),
      {
        status: 503,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
          'Retry-After': '60',
        },
      }
    );
  }
}

async function handleBatchPrediction(
  request: Request,
  env: CloudflareEnv,
  ctx: ExecutionContext,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const body = await request.json() as { creative_ids: string[] };
  const creativeIds = body.creative_ids;

  if (!creativeIds || !Array.isArray(creativeIds) || creativeIds.length === 0) {
    return new Response(
      JSON.stringify({ error: 'creative_ids array is required' }),
      {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }

  // Limit batch size
  if (creativeIds.length > 50) {
    return new Response(
      JSON.stringify({ error: 'Batch size limited to 50 creatives' }),
      {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }

  // Fetch all predictions in parallel
  const results = await Promise.all(
    creativeIds.map(async (id) => {
      const cacheKey = `prediction:${id}`;
      const cached = await env.PREDICTIONS.get(cacheKey, 'json') as PredictionCache | null;

      if (cached) {
        const expiresAt = new Date(cached.expires_at);
        if (expiresAt > new Date()) {
          return { creative_id: id, ...cached, cache_hit: true };
        }
      }

      // Cache miss - mark for background fetch
      return {
        creative_id: id,
        cache_hit: false,
        message: 'Use individual endpoint for uncached predictions',
      };
    })
  );

  return new Response(JSON.stringify({ predictions: results }), {
    status: 200,
    headers: {
      ...corsHeaders,
      'Content-Type': 'application/json',
    },
  });
}

async function handleCacheInvalidation(
  creativeId: string,
  env: CloudflareEnv,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const cacheKey = `prediction:${creativeId}`;

  await env.PREDICTIONS.delete(cacheKey);

  return new Response(
    JSON.stringify({
      message: 'Cache invalidated',
      creative_id: creativeId,
      cache_key: cacheKey,
    }),
    {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
      },
    }
  );
}

async function handleCacheStats(
  env: CloudflareEnv,
  corsHeaders: Record<string, string>
): Promise<Response> {
  // Note: KV doesn't provide built-in stats, so we'd need to track this separately
  // This is a placeholder for edge analytics integration
  return new Response(
    JSON.stringify({
      message: 'Cache statistics endpoint',
      note: 'Implement with Durable Objects for real-time stats',
    }),
    {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
      },
    }
  );
}

async function trackAnalytics(
  env: CloudflareEnv,
  event: any
): Promise<void> {
  if (env.ENABLE_EDGE_ANALYTICS !== 'true') {
    return;
  }

  try {
    // Store in KV for batch processing
    const analyticsKey = `analytics:${Date.now()}:${Math.random()}`;
    await env.ANALYTICS.put(analyticsKey, JSON.stringify(event), {
      expirationTtl: 86400, // 24 hours
    });
  } catch (error) {
    console.error('Analytics tracking failed:', error);
    // Don't throw - analytics failures shouldn't break requests
  }
}
