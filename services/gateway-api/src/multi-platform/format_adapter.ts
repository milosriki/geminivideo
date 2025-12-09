/**
 * Format Adapter - Adapts creatives for each platform's specifications
 * Handles video format conversion, aspect ratios, and platform-specific requirements
 * Agent 19: Multi-Platform Publishing Infrastructure
 */

export interface PlatformSpec {
  platform: 'meta' | 'google' | 'tiktok';
  aspectRatio: string;
  width: number;
  height: number;
  maxDuration: number; // seconds
  minDuration: number; // seconds
  maxFileSize: number; // MB
  formats: string[];
  placement?: string;
}

export interface CreativeFormat {
  platform: 'meta' | 'google' | 'tiktok';
  format: string;
  videoPath: string;
  thumbnailPath?: string;
  width: number;
  height: number;
  duration: number;
  fileSize: number;
  aspectRatio: string;
  placement?: string;
}

export interface AdaptationJob {
  jobId: string;
  sourceVideoPath: string;
  platforms: ('meta' | 'google' | 'tiktok')[];
  targetFormats: CreativeFormat[];
  status: 'pending' | 'processing' | 'completed' | 'failed';
  createdAt: Date;
  completedAt?: Date;
  error?: string;
}

/**
 * Platform Creative Specifications
 * These are production-grade specs validated against platform documentation
 */
export const PLATFORM_SPECS: Record<string, PlatformSpec[]> = {
  meta: [
    {
      platform: 'meta',
      aspectRatio: '1:1',
      width: 1080,
      height: 1080,
      maxDuration: 240,
      minDuration: 1,
      maxFileSize: 4000,
      formats: ['mp4', 'mov'],
      placement: 'feed'
    },
    {
      platform: 'meta',
      aspectRatio: '9:16',
      width: 1080,
      height: 1920,
      maxDuration: 60,
      minDuration: 1,
      maxFileSize: 4000,
      formats: ['mp4', 'mov'],
      placement: 'reels'
    },
    {
      platform: 'meta',
      aspectRatio: '9:16',
      width: 1080,
      height: 1920,
      maxDuration: 15,
      minDuration: 1,
      maxFileSize: 4000,
      formats: ['mp4', 'mov'],
      placement: 'story'
    },
    {
      platform: 'meta',
      aspectRatio: '16:9',
      width: 1920,
      height: 1080,
      maxDuration: 240,
      minDuration: 1,
      maxFileSize: 4000,
      formats: ['mp4', 'mov'],
      placement: 'in_stream'
    }
  ],
  google: [
    {
      platform: 'google',
      aspectRatio: '16:9',
      width: 1920,
      height: 1080,
      maxDuration: 360,
      minDuration: 6,
      maxFileSize: 1024,
      formats: ['mp4', 'mov', 'avi'],
      placement: 'youtube_in_stream'
    },
    {
      platform: 'google',
      aspectRatio: '9:16',
      width: 1080,
      height: 1920,
      maxDuration: 60,
      minDuration: 6,
      maxFileSize: 1024,
      formats: ['mp4', 'mov'],
      placement: 'youtube_shorts'
    },
    {
      platform: 'google',
      aspectRatio: '1:1',
      width: 1200,
      height: 1200,
      maxDuration: 30,
      minDuration: 6,
      maxFileSize: 150,
      formats: ['mp4', 'gif'],
      placement: 'display'
    }
  ],
  tiktok: [
    {
      platform: 'tiktok',
      aspectRatio: '9:16',
      width: 1080,
      height: 1920,
      maxDuration: 60,
      minDuration: 5,
      maxFileSize: 500,
      formats: ['mp4', 'mov'],
      placement: 'in_feed'
    },
    {
      platform: 'tiktok',
      aspectRatio: '9:16',
      width: 720,
      height: 1280,
      maxDuration: 60,
      minDuration: 5,
      maxFileSize: 500,
      formats: ['mp4', 'mov'],
      placement: 'in_feed_mobile'
    }
  ]
};

export class FormatAdapter {
  private videoAgentUrl: string;

  constructor(videoAgentUrl: string) {
    this.videoAgentUrl = videoAgentUrl;
  }

  /**
   * Get platform specifications for selected platforms
   */
  getPlatformSpecs(platforms: ('meta' | 'google' | 'tiktok')[]): PlatformSpec[] {
    const specs: PlatformSpec[] = [];

    for (const platform of platforms) {
      if (PLATFORM_SPECS[platform]) {
        specs.push(...PLATFORM_SPECS[platform]);
      }
    }

    return specs;
  }

  /**
   * Get recommended specs based on platforms
   * Returns the most common/versatile specs for each platform
   */
  getRecommendedSpecs(platforms: ('meta' | 'google' | 'tiktok')[]): PlatformSpec[] {
    const recommended: PlatformSpec[] = [];

    for (const platform of platforms) {
      switch (platform) {
        case 'meta':
          // Reels is most popular for Meta
          recommended.push(PLATFORM_SPECS.meta[1]); // 9:16 Reels
          recommended.push(PLATFORM_SPECS.meta[0]); // 1:1 Feed
          break;
        case 'google':
          // YouTube is primary for Google Ads
          recommended.push(PLATFORM_SPECS.google[0]); // 16:9 YouTube
          break;
        case 'tiktok':
          // TikTok only supports 9:16
          recommended.push(PLATFORM_SPECS.tiktok[0]); // 9:16 In-feed
          break;
      }
    }

    return recommended;
  }

  /**
   * Validate if a video meets platform specifications
   */
  validateVideoForPlatform(
    videoMetadata: {
      width: number;
      height: number;
      duration: number;
      fileSize: number; // in MB
      format: string;
    },
    spec: PlatformSpec
  ): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Check aspect ratio (with 5% tolerance)
    const videoAspectRatio = videoMetadata.width / videoMetadata.height;
    const [specWidth, specHeight] = spec.aspectRatio.split(':').map(Number);
    const specAspectRatio = specWidth / specHeight;
    const aspectRatioTolerance = 0.05;

    if (Math.abs(videoAspectRatio - specAspectRatio) > aspectRatioTolerance) {
      errors.push(
        `Aspect ratio mismatch: video is ${videoMetadata.width}x${videoMetadata.height}, ` +
        `expected ${spec.aspectRatio}`
      );
    }

    // Check duration
    if (videoMetadata.duration < spec.minDuration) {
      errors.push(`Duration too short: ${videoMetadata.duration}s (min: ${spec.minDuration}s)`);
    }
    if (videoMetadata.duration > spec.maxDuration) {
      errors.push(`Duration too long: ${videoMetadata.duration}s (max: ${spec.maxDuration}s)`);
    }

    // Check file size
    if (videoMetadata.fileSize > spec.maxFileSize) {
      errors.push(
        `File size too large: ${videoMetadata.fileSize}MB (max: ${spec.maxFileSize}MB)`
      );
    }

    // Check format
    if (!spec.formats.includes(videoMetadata.format.toLowerCase())) {
      errors.push(
        `Format not supported: ${videoMetadata.format} ` +
        `(supported: ${spec.formats.join(', ')})`
      );
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Adapt a creative to multiple platform formats
   * This will call video-agent to perform actual video processing
   */
  async adaptCreative(
    sourceVideoPath: string,
    platforms: ('meta' | 'google' | 'tiktok')[],
    options: {
      smartCrop?: boolean;
      quality?: 'high' | 'medium' | 'low';
      outputDir?: string;
    } = {}
  ): Promise<AdaptationJob> {
    const jobId = `adapt_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    const targetSpecs = this.getRecommendedSpecs(platforms);

    const job: AdaptationJob = {
      jobId,
      sourceVideoPath,
      platforms,
      targetFormats: [],
      status: 'pending',
      createdAt: new Date()
    };

    try {
      job.status = 'processing';

      // Call video-agent to perform format conversions
      const axios = require('axios');

      const response = await httpClient.post(
        `${this.videoAgentUrl}/api/format/adapt`,
        {
          jobId,
          sourceVideoPath,
          targetSpecs,
          options: {
            smartCrop: options.smartCrop ?? true,
            quality: options.quality ?? 'high',
            outputDir: options.outputDir ?? `/tmp/adapted/${jobId}`
          }
        },
        {
          timeout: 300000 // 5 minute timeout for video processing
        }
      );

      job.targetFormats = response.data.formats || [];
      job.status = 'completed';
      job.completedAt = new Date();

    } catch (error: any) {
      console.error('Format adaptation error:', error.message);
      job.status = 'failed';
      job.error = error.message;

      // Generate mock formats for development/testing
      job.targetFormats = this._generateMockFormats(targetSpecs, sourceVideoPath);
    }

    return job;
  }

  /**
   * Generate mock formats for development/testing
   * Used when video-agent is not available
   */
  private _generateMockFormats(
    specs: PlatformSpec[],
    sourceVideoPath: string
  ): CreativeFormat[] {
    return specs.map(spec => ({
      platform: spec.platform,
      format: spec.formats[0],
      videoPath: `/tmp/mock_${spec.platform}_${spec.placement}_${Date.now()}.${spec.formats[0]}`,
      width: spec.width,
      height: spec.height,
      duration: 30, // Mock duration
      fileSize: 50, // Mock file size
      aspectRatio: spec.aspectRatio,
      placement: spec.placement
    }));
  }

  /**
   * Get optimal format for a platform placement
   */
  getOptimalFormat(
    platform: 'meta' | 'google' | 'tiktok',
    placement?: string
  ): PlatformSpec | null {
    const platformSpecs = PLATFORM_SPECS[platform];

    if (!platformSpecs || platformSpecs.length === 0) {
      return null;
    }

    // If placement specified, find exact match
    if (placement) {
      const spec = platformSpecs.find(s => s.placement === placement);
      if (spec) return spec;
    }

    // Otherwise return first (most common) format
    return platformSpecs[0];
  }

  /**
   * Calculate budget allocation for multi-platform publishing
   * Based on platform performance and reach
   */
  calculateBudgetAllocation(
    platforms: ('meta' | 'google' | 'tiktok')[],
    totalBudget: number,
    customWeights?: Record<string, number>
  ): Record<string, number> {
    // Default platform weights based on typical performance
    const defaultWeights = {
      meta: 0.50,   // 50% - Largest reach, best targeting
      google: 0.30, // 30% - High intent, YouTube dominance
      tiktok: 0.20  // 20% - Growing platform, younger audience
    };

    const weights = customWeights || defaultWeights;
    const allocation: Record<string, number> = {};

    // Calculate total weight for selected platforms
    let totalWeight = 0;
    for (const platform of platforms) {
      totalWeight += weights[platform] || 0;
    }

    // Normalize and allocate budget
    for (const platform of platforms) {
      const weight = weights[platform] || 0;
      allocation[platform] = (weight / totalWeight) * totalBudget;
    }

    return allocation;
  }
}
