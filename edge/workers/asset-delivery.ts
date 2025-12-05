/**
 * Edge Worker: Global Asset Delivery
 * Handles video and image assets using Cloudflare R2, Stream, and Images
 */

import { CloudflareEnv } from '../types/env';

export default {
  async fetch(request: Request, env: CloudflareEnv, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
      'Access-Control-Allow-Headers': 'Range, Content-Type',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // Route: GET /assets/videos/:video_id - Serve video from R2 or Stream
      if (path.match(/^\/assets\/videos\/(.+)$/)) {
        return await handleVideoAsset(path, request, env, ctx, corsHeaders);
      }

      // Route: GET /assets/images/:image_id - Serve image from R2 or Images
      if (path.match(/^\/assets\/images\/(.+)$/)) {
        return await handleImageAsset(path, request, env, ctx, corsHeaders);
      }

      // Route: GET /assets/thumbnails/:video_id - Generate/serve thumbnail
      if (path.match(/^\/assets\/thumbnails\/(.+)$/)) {
        return await handleThumbnail(path, request, env, ctx, corsHeaders);
      }

      return new Response('Not Found', { status: 404, headers: corsHeaders });
    } catch (error: any) {
      console.error('[Asset Delivery] Error:', error);
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

async function handleVideoAsset(
  path: string,
  request: Request,
  env: CloudflareEnv,
  ctx: ExecutionContext,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const videoId = path.split('/').pop()!;

  console.log(`[Asset Delivery] Video request: ${videoId}`);

  // Option 1: Use Cloudflare Stream (recommended for videos)
  if (env.STREAM_ACCOUNT_ID && env.STREAM_API_TOKEN) {
    const streamUrl = `https://customer-${env.STREAM_ACCOUNT_ID}.cloudflarestream.com/${videoId}/manifest/video.m3u8`;

    // Return HLS manifest URL
    return new Response(
      JSON.stringify({
        video_id: videoId,
        stream_url: streamUrl,
        thumbnail_url: `https://customer-${env.STREAM_ACCOUNT_ID}.cloudflarestream.com/${videoId}/thumbnails/thumbnail.jpg`,
        delivery_method: 'cloudflare_stream',
      }),
      {
        status: 200,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
          'Cache-Control': 'public, max-age=3600',
        },
      }
    );
  }

  // Option 2: Serve from R2 bucket
  try {
    const object = await env.VIDEO_CACHE.get(videoId);

    if (!object) {
      return new Response('Video not found', {
        status: 404,
        headers: corsHeaders,
      });
    }

    // Handle range requests for video streaming
    const rangeHeader = request.headers.get('Range');
    if (rangeHeader) {
      return handleRangeRequest(object, rangeHeader, corsHeaders);
    }

    // Serve full video
    const headers = new Headers(corsHeaders);
    headers.set('Content-Type', object.httpMetadata?.contentType || 'video/mp4');
    headers.set('Content-Length', String(object.size));
    headers.set('Cache-Control', 'public, max-age=31536000'); // 1 year
    headers.set('ETag', object.httpEtag || '');
    headers.set('Accept-Ranges', 'bytes');

    return new Response(object.body, {
      status: 200,
      headers,
    });
  } catch (error: any) {
    console.error(`[Asset Delivery] R2 fetch failed: ${error.message}`);
    return new Response('Service Unavailable', {
      status: 503,
      headers: corsHeaders,
    });
  }
}

async function handleImageAsset(
  path: string,
  request: Request,
  env: CloudflareEnv,
  ctx: ExecutionContext,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const imageId = path.split('/').pop()!;
  const url = new URL(request.url);

  // Parse image transformation params
  const width = url.searchParams.get('w') || url.searchParams.get('width');
  const height = url.searchParams.get('h') || url.searchParams.get('height');
  const quality = url.searchParams.get('q') || url.searchParams.get('quality') || '85';
  const format = url.searchParams.get('f') || url.searchParams.get('format') || 'auto';

  console.log(`[Asset Delivery] Image request: ${imageId} (${width}x${height}, q=${quality}, f=${format})`);

  // Option 1: Use Cloudflare Images (with transformations)
  if (env.CLOUDFLARE_ACCOUNT_ID) {
    const transformParams = [];
    if (width) transformParams.push(`width=${width}`);
    if (height) transformParams.push(`height=${height}`);
    if (quality) transformParams.push(`quality=${quality}`);
    if (format && format !== 'auto') transformParams.push(`format=${format}`);

    const variantPath = transformParams.length > 0 ? transformParams.join(',') : 'public';
    const imageUrl = `https://imagedelivery.net/${env.CLOUDFLARE_ACCOUNT_ID}/${imageId}/${variantPath}`;

    // Redirect to Cloudflare Images
    return Response.redirect(imageUrl, 302);
  }

  // Option 2: Serve from R2 bucket
  try {
    const object = await env.ASSETS.get(imageId);

    if (!object) {
      return new Response('Image not found', {
        status: 404,
        headers: corsHeaders,
      });
    }

    const headers = new Headers(corsHeaders);
    headers.set('Content-Type', object.httpMetadata?.contentType || 'image/jpeg');
    headers.set('Content-Length', String(object.size));
    headers.set('Cache-Control', 'public, max-age=31536000'); // 1 year
    headers.set('ETag', object.httpEtag || '');

    return new Response(object.body, {
      status: 200,
      headers,
    });
  } catch (error: any) {
    console.error(`[Asset Delivery] R2 fetch failed: ${error.message}`);
    return new Response('Service Unavailable', {
      status: 503,
      headers: corsHeaders,
    });
  }
}

async function handleThumbnail(
  path: string,
  request: Request,
  env: CloudflareEnv,
  ctx: ExecutionContext,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const videoId = path.split('/').pop()!;

  console.log(`[Asset Delivery] Thumbnail request: ${videoId}`);

  // Use Cloudflare Stream thumbnail
  if (env.STREAM_ACCOUNT_ID) {
    const url = new URL(request.url);
    const time = url.searchParams.get('time') || '0s';
    const width = url.searchParams.get('width') || '640';
    const height = url.searchParams.get('height') || '360';

    const thumbnailUrl = `https://customer-${env.STREAM_ACCOUNT_ID}.cloudflarestream.com/${videoId}/thumbnails/thumbnail.jpg?time=${time}&width=${width}&height=${height}`;

    return Response.redirect(thumbnailUrl, 302);
  }

  // Fallback: serve from R2 if exists
  try {
    const thumbnailKey = `thumbnails/${videoId}.jpg`;
    const object = await env.ASSETS.get(thumbnailKey);

    if (!object) {
      return new Response('Thumbnail not found', {
        status: 404,
        headers: corsHeaders,
      });
    }

    const headers = new Headers(corsHeaders);
    headers.set('Content-Type', 'image/jpeg');
    headers.set('Content-Length', String(object.size));
    headers.set('Cache-Control', 'public, max-age=86400'); // 1 day

    return new Response(object.body, {
      status: 200,
      headers,
    });
  } catch (error: any) {
    console.error(`[Asset Delivery] Thumbnail fetch failed: ${error.message}`);
    return new Response('Service Unavailable', {
      status: 503,
      headers: corsHeaders,
    });
  }
}

function handleRangeRequest(
  object: any,
  rangeHeader: string,
  corsHeaders: Record<string, string>
): Response {
  // Parse range header (e.g., "bytes=0-1023")
  const match = rangeHeader.match(/bytes=(\d+)-(\d*)/);
  if (!match) {
    return new Response('Invalid Range Header', {
      status: 416,
      headers: corsHeaders,
    });
  }

  const start = parseInt(match[1]);
  const end = match[2] ? parseInt(match[2]) : object.size - 1;
  const chunkSize = end - start + 1;

  if (start >= object.size || end >= object.size) {
    return new Response('Range Not Satisfiable', {
      status: 416,
      headers: {
        ...corsHeaders,
        'Content-Range': `bytes */${object.size}`,
      },
    });
  }

  const headers = new Headers(corsHeaders);
  headers.set('Content-Type', object.httpMetadata?.contentType || 'video/mp4');
  headers.set('Content-Length', String(chunkSize));
  headers.set('Content-Range', `bytes ${start}-${end}/${object.size}`);
  headers.set('Accept-Ranges', 'bytes');
  headers.set('Cache-Control', 'public, max-age=31536000');

  // Note: Actual range slicing would require the full R2 API
  // This is a simplified version
  return new Response(object.body, {
    status: 206, // Partial Content
    headers,
  });
}
