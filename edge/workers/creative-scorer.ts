/**
 * Edge Worker: Creative Scorer
 * Quick creative scoring at the edge using lightweight algorithms
 * Falls back to origin for complex ML scoring
 */

import { CloudflareEnv, CreativeScore } from '../types/env';

const SCORE_CACHE_TTL = 300; // 5 minutes

export default {
  async fetch(request: Request, env: CloudflareEnv, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // Route: POST /api/score-cached
      if (path === '/api/score-cached' && request.method === 'POST') {
        return await handleQuickScore(request, env, ctx, corsHeaders);
      }

      // Route: GET /api/score-cached/:creative_id
      if (path.match(/^\/api\/score-cached\/(.+)$/) && request.method === 'GET') {
        const creativeId = path.split('/').pop()!;
        return await getCachedScore(creativeId, env, corsHeaders);
      }

      return new Response('Not Found', { status: 404, headers: corsHeaders });
    } catch (error: any) {
      console.error('[Creative Scorer] Error:', error);
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

async function handleQuickScore(
  request: Request,
  env: CloudflareEnv,
  ctx: ExecutionContext,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const body = await request.json() as {
    creative_id: string;
    video_duration?: number;
    hook_duration?: number;
    has_cta?: boolean;
    has_text_overlay?: boolean;
    audio_type?: 'music' | 'voiceover' | 'silent';
  };

  const { creative_id, video_duration, hook_duration, has_cta, has_text_overlay, audio_type } = body;

  if (!creative_id) {
    return new Response(
      JSON.stringify({ error: 'creative_id is required' }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }

  const cacheKey = `score:${creative_id}`;

  // Check cache first
  const cached = await env.CREATIVE_SCORES.get(cacheKey, 'json') as CreativeScore | null;
  if (cached) {
    console.log(`[Edge] Score cache HIT: ${creative_id}`);
    return new Response(JSON.stringify(cached), {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
        'X-Cache': 'HIT',
      },
    });
  }

  console.log(`[Edge] Score cache MISS: ${creative_id}`);

  // Quick lightweight scoring (no ML)
  const score = calculateQuickScore({
    video_duration: video_duration || 30,
    hook_duration: hook_duration || 3,
    has_cta: has_cta || false,
    has_text_overlay: has_text_overlay || false,
    audio_type: audio_type || 'music',
  });

  const result: CreativeScore = {
    creative_id,
    hook_score: score.hook,
    retention_score: score.retention,
    cta_score: score.cta,
    overall_score: score.overall,
    timestamp: new Date().toISOString(),
  };

  // Cache the score
  ctx.waitUntil(
    env.CREATIVE_SCORES.put(cacheKey, JSON.stringify(result), {
      expirationTtl: SCORE_CACHE_TTL,
    })
  );

  return new Response(JSON.stringify(result), {
    status: 200,
    headers: {
      ...corsHeaders,
      'Content-Type': 'application/json',
      'Cache-Control': `public, max-age=${SCORE_CACHE_TTL}`,
      'X-Cache': 'MISS',
      'X-Score-Type': 'quick',
    },
  });
}

async function getCachedScore(
  creativeId: string,
  env: CloudflareEnv,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const cacheKey = `score:${creativeId}`;
  const cached = await env.CREATIVE_SCORES.get(cacheKey, 'json') as CreativeScore | null;

  if (cached) {
    return new Response(JSON.stringify(cached), {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
        'X-Cache': 'HIT',
      },
    });
  }

  return new Response(
    JSON.stringify({
      error: 'Not Found',
      message: 'No cached score for this creative. Use POST /api/score-cached to generate.',
    }),
    {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    }
  );
}

// Lightweight scoring algorithm (runs at edge)
function calculateQuickScore(params: {
  video_duration: number;
  hook_duration: number;
  has_cta: boolean;
  has_text_overlay: boolean;
  audio_type: string;
}): { hook: number; retention: number; cta: number; overall: number } {
  let hookScore = 50; // Base score
  let retentionScore = 50;
  let ctaScore = 50;

  // Hook scoring (first 3 seconds)
  if (params.hook_duration <= 3) {
    hookScore += 30; // Strong hook
  } else if (params.hook_duration <= 5) {
    hookScore += 20; // Good hook
  } else {
    hookScore += 10; // Slow hook
  }

  // Retention scoring (video length)
  if (params.video_duration >= 15 && params.video_duration <= 30) {
    retentionScore += 30; // Ideal length for ads
  } else if (params.video_duration < 15) {
    retentionScore += 20; // Short but watchable
  } else if (params.video_duration <= 60) {
    retentionScore += 10; // Might lose attention
  }

  // Text overlay bonus
  if (params.has_text_overlay) {
    retentionScore += 10;
    hookScore += 10;
  }

  // Audio type bonus
  if (params.audio_type === 'voiceover') {
    retentionScore += 15;
  } else if (params.audio_type === 'music') {
    retentionScore += 10;
  }

  // CTA scoring
  if (params.has_cta) {
    ctaScore += 40; // Strong CTA present
  } else {
    ctaScore += 5; // Weak or missing CTA
  }

  // Normalize scores to 0-100
  hookScore = Math.min(100, Math.max(0, hookScore));
  retentionScore = Math.min(100, Math.max(0, retentionScore));
  ctaScore = Math.min(100, Math.max(0, ctaScore));

  // Overall weighted average
  const overall = hookScore * 0.4 + retentionScore * 0.35 + ctaScore * 0.25;

  return {
    hook: Math.round(hookScore),
    retention: Math.round(retentionScore),
    cta: Math.round(ctaScore),
    overall: Math.round(overall),
  };
}
