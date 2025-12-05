/**
 * Multi-Platform Publisher - Orchestrates publishing to all platforms
 * Coordinates Meta, Google, and TikTok publishing in parallel
 * Agent 19: Multi-Platform Publishing Infrastructure
 */

import axios from 'axios';
import { FormatAdapter } from './format_adapter';
import { statusAggregator, MultiPlatformJob, PlatformStatus } from './status_aggregator';

export interface PublishRequest {
  creative_id: string;
  video_path: string;
  platforms: ('meta' | 'google' | 'tiktok')[];
  budget_allocation: Record<string, number>;
  campaign_name: string;
  campaign_config: {
    // Meta config
    meta?: {
      objective?: string;
      targeting?: any;
      placements?: string[];
      adSetName?: string;
    };
    // Google config
    google?: {
      biddingStrategy?: string;
      adGroupName?: string;
      cpcBidMicros?: number;
      headline?: string;
      description?: string;
      finalUrl?: string;
    };
    // TikTok config
    tiktok?: {
      objective?: string;
      targeting?: any;
      adGroupName?: string;
    };
  };
  creative_config?: {
    caption?: string;
    headline?: string;
    cta?: string;
  };
}

export interface PublishResponse {
  success: boolean;
  job_id: string;
  platforms: ('meta' | 'google' | 'tiktok')[];
  platform_statuses: PlatformStatus[];
  overall_status: string;
  message: string;
  errors?: Array<{
    platform: string;
    error: string;
  }>;
}

export class MultiPlatformPublisher {
  private formatAdapter: FormatAdapter;
  private metaPublisherUrl: string;
  private googleAdsUrl: string;
  private tiktokAdsUrl: string;

  constructor(config: {
    videoAgentUrl: string;
    metaPublisherUrl: string;
    googleAdsUrl: string;
    tiktokAdsUrl: string;
  }) {
    this.formatAdapter = new FormatAdapter(config.videoAgentUrl);
    this.metaPublisherUrl = config.metaPublisherUrl;
    this.googleAdsUrl = config.googleAdsUrl;
    this.tiktokAdsUrl = config.tiktokAdsUrl;
  }

  /**
   * Publish creative to multiple platforms simultaneously
   */
  async publishMultiPlatform(request: PublishRequest): Promise<PublishResponse> {
    console.log(`[Multi-Platform] Starting publish to ${request.platforms.join(', ')}`);
    console.log(`[Multi-Platform] Campaign: ${request.campaign_name}`);
    console.log(`[Multi-Platform] Budget allocation:`, request.budget_allocation);

    // Create job for tracking
    const job = statusAggregator.createJob(
      request.creative_id,
      request.platforms,
      request.campaign_name,
      request.budget_allocation,
      request.video_path
    );

    console.log(`[Multi-Platform] Created job: ${job.jobId}`);

    // Adapt creative to platform formats
    let adaptationJob;
    try {
      console.log(`[Multi-Platform] Adapting creative for platforms...`);
      adaptationJob = await this.formatAdapter.adaptCreative(
        request.video_path,
        request.platforms,
        {
          smartCrop: true,
          quality: 'high'
        }
      );

      if (adaptationJob.status === 'failed') {
        console.error(`[Multi-Platform] Format adaptation failed: ${adaptationJob.error}`);
        // Continue with original video for now
      } else {
        console.log(`[Multi-Platform] Adapted to ${adaptationJob.targetFormats.length} formats`);
      }
    } catch (error: any) {
      console.warn(`[Multi-Platform] Format adaptation error: ${error.message}`);
      // Continue without adaptation
    }

    // Publish to each platform in parallel
    const publishPromises: Promise<void>[] = [];
    const errors: Array<{ platform: string; error: string }> = [];

    for (const platform of request.platforms) {
      const budget = request.budget_allocation[platform] || 0;

      // Find adapted format for platform
      let videoPath = request.video_path;
      if (adaptationJob?.targetFormats) {
        const adaptedFormat = adaptationJob.targetFormats.find(
          f => f.platform === platform && f.placement === 'reels'
        );
        if (adaptedFormat) {
          videoPath = adaptedFormat.videoPath;
        }
      }

      const publishPromise = this._publishToPlatform(
        job.jobId,
        platform,
        {
          ...request,
          video_path: videoPath,
          budget: budget
        }
      ).catch(error => {
        console.error(`[Multi-Platform] ${platform} publish failed:`, error.message);
        errors.push({
          platform,
          error: error.message
        });

        // Update status to failed
        statusAggregator.updatePlatformStatus(job.jobId, platform, {
          status: 'failed',
          error: error.message
        });
      });

      publishPromises.push(publishPromise);
    }

    // Wait for all platforms to complete
    await Promise.all(publishPromises);

    // Get final job status
    const finalJob = statusAggregator.getJobStatus(job.jobId);

    console.log(`[Multi-Platform] Publish completed: ${finalJob?.overallStatus}`);
    console.log(`[Multi-Platform] Success: ${finalJob?.successCount}/${finalJob?.totalPlatforms}`);

    return {
      success: (finalJob?.successCount || 0) > 0,
      job_id: job.jobId,
      platforms: request.platforms,
      platform_statuses: finalJob?.platformStatuses || [],
      overall_status: finalJob?.overallStatus || 'unknown',
      message: this._generateStatusMessage(finalJob),
      errors: errors.length > 0 ? errors : undefined
    };
  }

  /**
   * Publish to a specific platform
   */
  private async _publishToPlatform(
    jobId: string,
    platform: 'meta' | 'google' | 'tiktok',
    request: PublishRequest & { budget: number }
  ): Promise<void> {
    console.log(`[${platform.toUpperCase()}] Starting publish...`);

    // Update status to uploading
    statusAggregator.updatePlatformStatus(jobId, platform, {
      status: 'uploading'
    });

    try {
      switch (platform) {
        case 'meta':
          await this._publishToMeta(jobId, request);
          break;
        case 'google':
          await this._publishToGoogle(jobId, request);
          break;
        case 'tiktok':
          await this._publishToTikTok(jobId, request);
          break;
      }

      console.log(`[${platform.toUpperCase()}] Publish successful`);

    } catch (error: any) {
      console.error(`[${platform.toUpperCase()}] Publish failed:`, error.message);
      throw error;
    }
  }

  /**
   * Publish to Meta (Facebook/Instagram)
   */
  private async _publishToMeta(
    jobId: string,
    request: PublishRequest & { budget: number }
  ): Promise<void> {
    statusAggregator.updatePlatformStatus(jobId, 'meta', {
      status: 'processing'
    });

    const metaConfig = request.campaign_config.meta || {};

    // Step 1: Create campaign
    const campaignResponse = await axios.post(
      `${this.metaPublisherUrl}/api/campaigns`,
      {
        name: request.campaign_name,
        objective: metaConfig.objective || 'OUTCOME_ENGAGEMENT',
        status: 'PAUSED'
      },
      { timeout: 30000 }
    );

    const campaignId = campaignResponse.data.campaign_id;
    console.log(`[META] Campaign created: ${campaignId}`);

    // Step 2: Create ad set
    const adSetResponse = await axios.post(
      `${this.metaPublisherUrl}/api/adsets`,
      {
        name: metaConfig.adSetName || `${request.campaign_name} - AdSet`,
        campaignId,
        bidAmount: 1000, // $10 CPM
        dailyBudget: Math.round(request.budget * 100), // Convert to cents
        targeting: metaConfig.targeting || {
          geo_locations: { countries: ['US'] },
          age_min: 18,
          age_max: 65
        },
        optimizationGoal: 'REACH',
        billingEvent: 'IMPRESSIONS',
        status: 'PAUSED'
      },
      { timeout: 30000 }
    );

    const adSetId = adSetResponse.data.adset_id;
    console.log(`[META] AdSet created: ${adSetId}`);

    // Step 3: Upload video and create ad
    const videoAdResponse = await axios.post(
      `${this.metaPublisherUrl}/api/video-ads`,
      {
        videoPath: request.video_path,
        campaignId,
        adSetId,
        creative: {
          title: request.creative_config?.headline || request.campaign_name,
          message: request.creative_config?.caption || 'Check this out!',
          callToAction: {
            type: 'LEARN_MORE',
            value: { link: 'https://example.com' }
          }
        },
        adName: `${request.campaign_name} - Video Ad`
      },
      { timeout: 60000 }
    );

    const adId = videoAdResponse.data.ad_id;
    const videoId = videoAdResponse.data.video_id;
    console.log(`[META] Video ad created: ${adId}`);

    // Update status to live
    statusAggregator.updatePlatformStatus(jobId, 'meta', {
      status: 'live',
      campaignId,
      adSetId,
      adId,
      videoId
    });
  }

  /**
   * Publish to Google Ads (YouTube)
   */
  private async _publishToGoogle(
    jobId: string,
    request: PublishRequest & { budget: number }
  ): Promise<void> {
    statusAggregator.updatePlatformStatus(jobId, 'google', {
      status: 'processing'
    });

    const googleConfig = request.campaign_config.google || {};

    // Step 1: Create campaign
    const campaignResponse = await axios.post(
      `${this.googleAdsUrl}/api/campaigns`,
      {
        name: request.campaign_name,
        budget: Math.round(request.budget * 1000000), // Convert to micros
        biddingStrategy: googleConfig.biddingStrategy || 'MAXIMIZE_CONVERSIONS',
        status: 'PAUSED'
      },
      { timeout: 30000 }
    );

    const campaignId = campaignResponse.data.campaign_id;
    console.log(`[GOOGLE] Campaign created: ${campaignId}`);

    // Step 2: Create ad group
    const adGroupResponse = await axios.post(
      `${this.googleAdsUrl}/api/ad-groups`,
      {
        name: googleConfig.adGroupName || `${request.campaign_name} - AdGroup`,
        campaignId,
        cpcBidMicros: googleConfig.cpcBidMicros || 1000000, // $1 CPC
        status: 'PAUSED'
      },
      { timeout: 30000 }
    );

    const adGroupId = adGroupResponse.data.ad_group_id;
    console.log(`[GOOGLE] AdGroup created: ${adGroupId}`);

    // Step 3: Upload video and create ad
    const videoAdResponse = await axios.post(
      `${this.googleAdsUrl}/api/video-ads`,
      {
        videoPath: request.video_path,
        campaignId,
        adGroupId,
        headline: googleConfig.headline || request.creative_config?.headline || request.campaign_name,
        description: googleConfig.description || request.creative_config?.caption || 'Watch now',
        finalUrl: googleConfig.finalUrl || 'https://example.com'
      },
      { timeout: 90000 }
    );

    const adId = videoAdResponse.data.ad_id;
    const videoId = videoAdResponse.data.video_id;
    console.log(`[GOOGLE] Video ad created: ${adId}`);

    // Update status to live
    statusAggregator.updatePlatformStatus(jobId, 'google', {
      status: 'live',
      campaignId,
      adGroupId,
      adId,
      videoId
    });
  }

  /**
   * Publish to TikTok
   */
  private async _publishToTikTok(
    jobId: string,
    request: PublishRequest & { budget: number }
  ): Promise<void> {
    statusAggregator.updatePlatformStatus(jobId, 'tiktok', {
      status: 'processing'
    });

    const tiktokConfig = request.campaign_config.tiktok || {};

    // Call TikTok service (placeholder implementation)
    const response = await axios.post(
      `${this.tiktokAdsUrl}/api/publish`,
      {
        campaignName: request.campaign_name,
        videoPath: request.video_path,
        budget: request.budget,
        objective: tiktokConfig.objective || 'TRAFFIC',
        targeting: tiktokConfig.targeting || {},
        adGroupName: tiktokConfig.adGroupName || `${request.campaign_name} - AdGroup`
      },
      { timeout: 60000 }
    );

    const campaignId = response.data.campaign_id;
    const adId = response.data.ad_id;

    console.log(`[TIKTOK] Campaign created: ${campaignId}`);

    // Update status to live
    statusAggregator.updatePlatformStatus(jobId, 'tiktok', {
      status: 'live',
      campaignId,
      adId
    });
  }

  /**
   * Generate status message based on job results
   */
  private _generateStatusMessage(job: MultiPlatformJob | null): string {
    if (!job) {
      return 'Unknown status';
    }

    const { successCount, failureCount, totalPlatforms, overallStatus } = job;

    if (overallStatus === 'completed') {
      return `Successfully published to all ${totalPlatforms} platform(s)`;
    } else if (overallStatus === 'failed') {
      return `Failed to publish to all ${totalPlatforms} platform(s)`;
    } else if (overallStatus === 'partial_success') {
      return `Published to ${successCount}/${totalPlatforms} platform(s). ${failureCount} failed.`;
    } else if (overallStatus === 'in_progress') {
      return `Publishing in progress... (${successCount}/${totalPlatforms} completed)`;
    } else {
      return 'Waiting to start publishing';
    }
  }

  /**
   * Get platform specifications for frontend
   */
  getPlatformSpecs(platforms: ('meta' | 'google' | 'tiktok')[] = ['meta', 'google', 'tiktok']) {
    return this.formatAdapter.getPlatformSpecs(platforms);
  }

  /**
   * Calculate recommended budget allocation
   */
  calculateBudgetAllocation(
    platforms: ('meta' | 'google' | 'tiktok')[],
    totalBudget: number,
    customWeights?: Record<string, number>
  ) {
    return this.formatAdapter.calculateBudgetAllocation(platforms, totalBudget, customWeights);
  }
}
