/**
 * Edge Worker: Trending Hooks
 * Serves trending creative hooks with edge caching
 * Updated every 5 minutes from origin
 */

import { CloudflareEnv } from '../types/env';

const TRENDING_CACHE_TTL = 300; // 5 minutes
const STALE_WHILE_REVALIDATE = 600; // 10 minutes

interface TrendingHook {
  hook_id: string;
  hook_text: string;
  category: string;
  trend_score: number;
  usage_count: number;
  avg_ctr: number;
  examples: string[];
}

export default {
  async fetch(request: Request, env: CloudflareEnv, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // Route: GET /api/hooks/trending
      if (path === '/api/hooks/trending' && request.method === 'GET') {
        const category = url.searchParams.get('category') || 'all';
        const limit = parseInt(url.searchParams.get('limit') || '10');
        return await handleTrendingHooks(category, limit, env, ctx, corsHeaders);
      }

      // Route: GET /api/hooks/trending/:category
      if (path.match(/^\/api\/hooks\/trending\/(.+)$/) && request.method === 'GET') {
        const category = path.split('/').pop()!;
        const limit = parseInt(url.searchParams.get('limit') || '10');
        return await handleTrendingHooks(category, limit, env, ctx, corsHeaders);
      }

      return new Response('Not Found', { status: 404, headers: corsHeaders });
    } catch (error: any) {
      console.error('[Trending Hooks] Error:', error);
      return new Response(
        JSON.stringify({ error: 'Internal Server Error', message: error.message }),
        {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        }
      );
    }
  },
};

async function handleTrendingHooks(
  category: string,
  limit: number,
  env: CloudflareEnv,
  ctx: ExecutionContext,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const cacheKey = `trending_hooks:${category}:${limit}`;

  console.log(`[Edge] Checking trending hooks cache: ${cacheKey}`);

  // Check KV cache
  const cached = await env.PREDICTIONS.get(cacheKey, 'json') as {
    hooks: TrendingHook[];
    cached_at: string;
    expires_at: string;
  } | null;

  if (cached) {
    const expiresAt = new Date(cached.expires_at);
    const now = new Date();

    if (expiresAt > now) {
      console.log(`[Edge] Trending hooks cache HIT: ${cacheKey}`);
      return new Response(JSON.stringify(cached.hooks), {
        status: 200,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
          'Cache-Control': `public, max-age=${Math.floor((expiresAt.getTime() - now.getTime()) / 1000)}`,
          'X-Cache': 'HIT',
          'X-Cached-At': cached.cached_at,
        },
      });
    }
  }

  console.log(`[Edge] Trending hooks cache MISS: ${cacheKey}`);

  // Fetch from origin
  try {
    const originUrl = `${env.GATEWAY_API_URL}/api/hooks/trending?category=${category}&limit=${limit}`;
    const originResponse = await fetch(originUrl, {
      headers: { 'Authorization': `Bearer ${env.API_SECRET}` },
    });

    if (!originResponse.ok) {
      throw new Error(`Origin returned ${originResponse.status}`);
    }

    const hooks = await originResponse.json();

    // Cache the results
    const expiresAt = new Date(Date.now() + TRENDING_CACHE_TTL * 1000);
    const cacheData = {
      hooks,
      cached_at: new Date().toISOString(),
      expires_at: expiresAt.toISOString(),
    };

    ctx.waitUntil(
      env.PREDICTIONS.put(cacheKey, JSON.stringify(cacheData), {
        expirationTtl: TRENDING_CACHE_TTL + STALE_WHILE_REVALIDATE,
      })
    );

    return new Response(JSON.stringify(hooks), {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
        'Cache-Control': `public, max-age=${TRENDING_CACHE_TTL}, stale-while-revalidate=${STALE_WHILE_REVALIDATE}`,
        'X-Cache': 'MISS',
      },
    });
  } catch (error: any) {
    console.error(`[Edge] Origin fetch failed: ${error.message}`);

    // Return stale cache if available
    if (cached) {
      console.log(`[Edge] Returning STALE trending hooks: ${cacheKey}`);
      return new Response(JSON.stringify(cached.hooks), {
        status: 200,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
          'X-Cache': 'STALE',
          'Warning': '110 - "Response is stale"',
        },
      });
    }

    // No cache, return fallback
    return new Response(
      JSON.stringify({
        error: 'Service Unavailable',
        message: 'Origin unavailable and no cache exists',
        fallback: getFallbackHooks(category),
      }),
      {
        status: 503,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
          'X-Fallback': 'true',
        },
      }
    );
  }
}

// Fallback trending hooks (hardcoded for resilience)
function getFallbackHooks(category: string): TrendingHook[] {
  const fallbackHooks: Record<string, TrendingHook[]> = {
    fitness: [
      {
        hook_id: 'fallback-1',
        hook_text: 'You\'re doing it wrong...',
        category: 'fitness',
        trend_score: 85,
        usage_count: 500,
        avg_ctr: 0.045,
        examples: ['gym form corrections', 'workout tips'],
      },
      {
        hook_id: 'fallback-2',
        hook_text: 'This one simple trick...',
        category: 'fitness',
        trend_score: 80,
        usage_count: 450,
        avg_ctr: 0.042,
        examples: ['fat loss', 'muscle gain'],
      },
    ],
    ecommerce: [
      {
        hook_id: 'fallback-3',
        hook_text: 'I was skeptical until...',
        category: 'ecommerce',
        trend_score: 90,
        usage_count: 600,
        avg_ctr: 0.048,
        examples: ['product reviews', 'testimonials'],
      },
    ],
    all: [
      {
        hook_id: 'fallback-4',
        hook_text: 'Watch what happens when...',
        category: 'general',
        trend_score: 88,
        usage_count: 550,
        avg_ctr: 0.046,
        examples: ['demonstrations', 'reveals'],
      },
    ],
  };

  return fallbackHooks[category] || fallbackHooks.all;
}
