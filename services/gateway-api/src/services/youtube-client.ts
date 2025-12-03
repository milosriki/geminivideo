/**
 * YouTube API Client
 * Fetches trending videos and transforms them to AdPattern format
 * Requires: YOUTUBE_API_KEY (free from console.cloud.google.com)
 *
 * API Documentation: https://developers.google.com/youtube/v3/docs
 */

import axios, { AxiosError } from 'axios';

// Import AdPattern type from ad-intelligence
interface AdPattern {
  source: 'foreplay' | 'meta_library' | 'tiktok' | 'google' | 'youtube';
  hook_type: string;
  emotional_triggers: string[];
  visual_style: string;
  pacing: string;
  cta_style: string;
  performance_tier: 'top_1_percent' | 'top_10_percent' | 'average' | 'unknown';
  transcript?: string;
  industry: string;
  raw_data: any;
}

interface YouTubeVideo {
  id: string;
  title: string;
  description: string;
  channel: string;
  viewCount: string;
  likeCount: string;
  commentCount: string;
  publishedAt: string;
  thumbnails: any;
  tags?: string[];
  categoryId: string;
}

/**
 * YouTube Data API Client
 * Free API with 10,000 quota units per day
 */
export class YouTubeClient {
  private apiKey: string | null;
  private baseUrl = 'https://www.googleapis.com/youtube/v3';

  // Category mapping (YouTube category IDs)
  private categoryMap: Record<string, string> = {
    'all': '',
    'film': '1',
    'autos': '2',
    'music': '10',
    'pets': '15',
    'sports': '17',
    'gaming': '20',
    'people': '22',
    'comedy': '23',
    'entertainment': '24',
    'news': '25',
    'howto': '26',
    'education': '27',
    'science': '28',
    'nonprofits': '29'
  };

  constructor() {
    this.apiKey = process.env.YOUTUBE_API_KEY || null;
  }

  isConfigured(): boolean {
    return this.apiKey !== null;
  }

  /**
   * Get trending videos by category and region
   */
  async getTrendingVideos(params: {
    category?: string;
    region?: string;
    limit?: number;
  }): Promise<AdPattern[]> {
    if (!this.apiKey) {
      throw new Error('YOUTUBE_NOT_CONFIGURED: Set YOUTUBE_API_KEY (free from console.cloud.google.com)');
    }

    try {
      const categoryId = params.category ? this.categoryMap[params.category.toLowerCase()] || '' : '';

      const response = await axios.get(`${this.baseUrl}/videos`, {
        params: {
          part: 'snippet,statistics,contentDetails',
          chart: 'mostPopular',
          regionCode: params.region || 'US',
          videoCategoryId: categoryId || undefined,
          maxResults: Math.min(params.limit || 20, 50), // YouTube max is 50
          key: this.apiKey
        },
        timeout: 30000
      });

      if (!response.data.items || response.data.items.length === 0) {
        throw new Error('YOUTUBE_NO_DATA: No trending videos found');
      }

      return response.data.items.map((video: any) => this.transformToPattern(video));
    } catch (error) {
      const axiosError = error as AxiosError;
      if (axiosError.response?.status === 400) {
        throw new Error('YOUTUBE_BAD_REQUEST: Invalid parameters. Check category and region codes.');
      }
      if (axiosError.response?.status === 403) {
        throw new Error('YOUTUBE_AUTH_FAILED: Invalid API key or quota exceeded');
      }
      throw new Error(`YOUTUBE_ERROR: ${axiosError.message}`);
    }
  }

  /**
   * Search videos by keyword
   */
  async searchVideos(params: {
    query: string;
    limit?: number;
    order?: 'date' | 'rating' | 'relevance' | 'viewCount';
  }): Promise<AdPattern[]> {
    if (!this.apiKey) {
      throw new Error('YOUTUBE_NOT_CONFIGURED: Set YOUTUBE_API_KEY');
    }

    try {
      // First, search for video IDs
      const searchResponse = await axios.get(`${this.baseUrl}/search`, {
        params: {
          part: 'id',
          q: params.query,
          type: 'video',
          maxResults: Math.min(params.limit || 20, 50),
          order: params.order || 'viewCount',
          key: this.apiKey
        },
        timeout: 30000
      });

      if (!searchResponse.data.items || searchResponse.data.items.length === 0) {
        throw new Error('YOUTUBE_NO_RESULTS: No videos found for query');
      }

      // Extract video IDs
      const videoIds = searchResponse.data.items
        .map((item: any) => item.id.videoId)
        .filter(Boolean)
        .join(',');

      // Get full video details
      return await this.getVideoDetails(videoIds);
    } catch (error) {
      const axiosError = error as AxiosError;
      if (axiosError.response?.status === 403) {
        throw new Error('YOUTUBE_AUTH_FAILED: Invalid API key or quota exceeded');
      }
      throw new Error(`YOUTUBE_SEARCH_ERROR: ${axiosError.message}`);
    }
  }

  /**
   * Get detailed information for specific video IDs
   */
  async getVideoDetails(videoIds: string | string[]): Promise<AdPattern[]> {
    if (!this.apiKey) {
      throw new Error('YOUTUBE_NOT_CONFIGURED: Set YOUTUBE_API_KEY');
    }

    try {
      const ids = Array.isArray(videoIds) ? videoIds.join(',') : videoIds;

      const response = await axios.get(`${this.baseUrl}/videos`, {
        params: {
          part: 'snippet,statistics,contentDetails',
          id: ids,
          key: this.apiKey
        },
        timeout: 10000
      });

      if (!response.data.items || response.data.items.length === 0) {
        throw new Error('YOUTUBE_VIDEO_NOT_FOUND: No videos found with provided IDs');
      }

      return response.data.items.map((video: any) => this.transformToPattern(video));
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(`YOUTUBE_DETAILS_ERROR: ${axiosError.message}`);
    }
  }

  /**
   * Transform YouTube video to AdPattern format
   */
  private transformToPattern(video: any): AdPattern {
    const snippet = video.snippet || {};
    const statistics = video.statistics || {};
    const contentDetails = video.contentDetails || {};

    const title = snippet.title || '';
    const description = snippet.description || '';
    const tags = snippet.tags || [];

    // Extract view count for performance tier
    const viewCount = parseInt(statistics.viewCount || '0');
    const likeCount = parseInt(statistics.likeCount || '0');

    return {
      source: 'youtube' as any, // Will need to update AdPattern type
      hook_type: this.inferHookType(title, description, tags),
      emotional_triggers: this.extractEmotions(title, description, tags),
      visual_style: this.inferVisualStyle(snippet.categoryId, tags),
      pacing: this.inferPacing(contentDetails.duration),
      cta_style: this.extractCTA(description),
      performance_tier: this.inferPerformanceTier(viewCount, likeCount),
      transcript: `${title}\n\n${description}`,
      industry: this.inferIndustry(snippet.categoryId, tags),
      raw_data: {
        video_id: video.id,
        title: snippet.title,
        description: snippet.description,
        channel: snippet.channelTitle,
        published_at: snippet.publishedAt,
        view_count: viewCount,
        like_count: likeCount,
        comment_count: parseInt(statistics.commentCount || '0'),
        duration: contentDetails.duration,
        tags: tags,
        category_id: snippet.categoryId,
        thumbnails: snippet.thumbnails,
        url: `https://www.youtube.com/watch?v=${video.id}`
      }
    };
  }

  /**
   * Infer hook type from title and description
   */
  private inferHookType(title: string, description: string, tags: string[]): string {
    const text = `${title} ${description}`.toLowerCase();
    const tagText = tags.join(' ').toLowerCase();

    if (text.match(/\?$/) || text.includes('how to')) return 'question';
    if (text.match(/!$|amazing|shocking|unbelievable/)) return 'exclamation';
    if (text.match(/\d+%|\d+ (ways|tips|secrets)/)) return 'listicle';
    if (text.includes('before') && text.includes('after')) return 'transformation';
    if (text.match(/review|test|vs|comparison/)) return 'comparison';
    if (tagText.includes('tutorial') || text.includes('tutorial')) return 'educational';
    if (text.match(/free|discount|deal|sale/)) return 'offer';

    return 'statement';
  }

  /**
   * Extract emotional triggers from content
   */
  private extractEmotions(title: string, description: string, tags: string[]): string[] {
    const emotions: string[] = [];
    const text = `${title} ${description} ${tags.join(' ')}`.toLowerCase();

    if (text.match(/excit|amaz|wow|incredible|awesome/)) emotions.push('excitement');
    if (text.match(/fear|miss|urgent|limited|now|today only/)) emotions.push('urgency');
    if (text.match(/trust|proven|guarantee|expert|professional/)) emotions.push('trust');
    if (text.match(/save|free|discount|bonus|gift/)) emotions.push('greed');
    if (text.match(/join|community|together|family/)) emotions.push('belonging');
    if (text.match(/shock|surpris|never expected/)) emotions.push('curiosity');
    if (text.match(/inspire|motivat|achiev|success/)) emotions.push('aspiration');
    if (text.match(/fun|laugh|humor|funny|comedy/)) emotions.push('joy');

    return emotions.length > 0 ? emotions : ['neutral'];
  }

  /**
   * Infer visual style from category and tags
   */
  private inferVisualStyle(categoryId: string, tags: string[]): string {
    const tagText = tags.join(' ').toLowerCase();

    // Category-based inference
    switch (categoryId) {
      case '10': return 'music_video'; // Music
      case '20': return 'gameplay'; // Gaming
      case '17': return 'sports_footage'; // Sports
      case '23':
      case '24': return 'entertainment'; // Comedy/Entertainment
      case '26':
      case '27': return 'educational'; // Howto/Education
      default:
        // Tag-based inference
        if (tagText.includes('vlog')) return 'vlog';
        if (tagText.includes('cinematic')) return 'cinematic';
        if (tagText.includes('animation')) return 'animated';
        if (tagText.includes('unboxing')) return 'product_showcase';
        return 'standard';
    }
  }

  /**
   * Infer pacing from video duration
   * YouTube duration format: PT#M#S (e.g., PT15M30S)
   */
  private inferPacing(duration: string): string {
    if (!duration) return 'unknown';

    // Parse ISO 8601 duration
    const match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
    if (!match) return 'unknown';

    const hours = parseInt(match[1] || '0');
    const minutes = parseInt(match[2] || '0');
    const seconds = parseInt(match[3] || '0');
    const totalSeconds = hours * 3600 + minutes * 60 + seconds;

    if (totalSeconds < 60) return 'fast'; // Under 1 minute
    if (totalSeconds < 300) return 'medium'; // 1-5 minutes
    return 'slow'; // Over 5 minutes
  }

  /**
   * Extract CTA from description
   */
  private extractCTA(description: string): string {
    const descLower = description.toLowerCase();

    if (descLower.includes('subscribe')) return 'subscribe';
    if (descLower.includes('click the link')) return 'click_link';
    if (descLower.includes('shop now') || descLower.includes('buy now')) return 'shop_now';
    if (descLower.includes('learn more')) return 'learn_more';
    if (descLower.includes('download')) return 'download';
    if (descLower.includes('sign up') || descLower.includes('join')) return 'sign_up';
    if (descLower.includes('follow')) return 'follow';

    return 'watch';
  }

  /**
   * Infer performance tier from view count and engagement
   */
  private inferPerformanceTier(viewCount: number, likeCount: number): AdPattern['performance_tier'] {
    const engagementRate = viewCount > 0 ? (likeCount / viewCount) : 0;

    // High view count + good engagement
    if (viewCount > 1000000 && engagementRate > 0.03) return 'top_1_percent';
    if (viewCount > 100000 && engagementRate > 0.02) return 'top_10_percent';
    if (viewCount > 10000) return 'average';

    return 'unknown';
  }

  /**
   * Infer industry from category and tags
   */
  private inferIndustry(categoryId: string, tags: string[]): string {
    const tagText = tags.join(' ').toLowerCase();

    // Category-based inference
    switch (categoryId) {
      case '17': return 'fitness'; // Sports
      case '26': return 'education'; // Howto
      case '28': return 'technology'; // Science & Tech
      case '10': return 'entertainment'; // Music
      case '20': return 'gaming';
      case '15': return 'lifestyle'; // Pets
      case '2': return 'automotive';
      default:
        // Tag-based inference
        if (tagText.includes('fitness') || tagText.includes('workout')) return 'fitness';
        if (tagText.includes('beauty') || tagText.includes('makeup')) return 'beauty';
        if (tagText.includes('tech') || tagText.includes('gadget')) return 'technology';
        if (tagText.includes('food') || tagText.includes('cooking')) return 'food';
        if (tagText.includes('fashion') || tagText.includes('style')) return 'fashion';
        if (tagText.includes('business') || tagText.includes('entrepreneur')) return 'business';
        return 'general';
    }
  }
}

// Singleton export
export const youtubeClient = new YouTubeClient();
