/**
 * Meta Ads Manager - Real Facebook SDK Integration
 * Agents 11-14: Campaign, AdSet, Ad creation, Video upload, and Insights
 * Agent 95: Enhanced with retry logic, CAPI integration, and error handling
 */
import {
  FacebookAdsApi,
  AdAccount,
  Campaign,
  AdSet,
  Ad,
  AdCreative,
  AdVideo
} from 'facebook-nodejs-business-sdk';
import * as fs from 'fs';
import * as path from 'path';
import axios from 'axios';
import crypto from 'crypto';

export interface MetaConfig {
  accessToken: string;
  adAccountId: string;
  pageId: string;
}

export interface CampaignParams {
  name: string;
  objective?: string;
  status?: string;
  specialAdCategories?: string[];
}

export interface AdSetParams {
  name: string;
  campaignId: string;
  bidAmount: number;
  dailyBudget: number;
  targeting: any;
  optimizationGoal?: string;
  billingEvent?: string;
  status?: string;
}

export interface AdCreativeParams {
  name: string;
  videoId: string;
  title: string;
  message: string;
  callToAction?: {
    type: string;
    value?: any;
  };
}

export interface AdParams {
  name: string;
  adSetId: string;
  creativeId: string;
  status?: string;
}

export interface ConversionEvent {
  eventName: string;
  eventTime: number;
  userData: {
    email?: string;
    phone?: string;
    externalId?: string;
    clientIpAddress?: string;
    clientUserAgent?: string;
    fbc?: string;
    fbp?: string;
  };
  customData?: Record<string, any>;
  eventSourceUrl?: string;
  actionSource: string;
}

export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
}

/**
 * Retry helper with exponential backoff
 */
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  config: RetryConfig = { maxRetries: 3, baseDelay: 1000, maxDelay: 10000 }
): Promise<T> {
  let lastError: Error;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      lastError = error;

      // Check if error is retryable
      const isRateLimitError = error.message?.includes('rate limit') ||
                                error.code === 4 ||
                                error.code === 17 ||
                                error.code === 32;

      const isServerError = error.code >= 500 || error.message?.includes('server error');

      const shouldRetry = isRateLimitError || isServerError;

      if (!shouldRetry || attempt === config.maxRetries) {
        throw error;
      }

      // Calculate exponential backoff delay
      const delay = Math.min(
        config.baseDelay * Math.pow(2, attempt),
        config.maxDelay
      );

      // Add jitter to prevent thundering herd
      const jitter = Math.random() * 0.3 * delay;
      const totalDelay = delay + jitter;

      console.log(`Retry attempt ${attempt + 1}/${config.maxRetries} after ${Math.round(totalDelay)}ms`);
      await new Promise(resolve => setTimeout(resolve, totalDelay));
    }
  }

  throw lastError!;
}

/**
 * Meta Ads Manager - Full Facebook Marketing API Integration
 */
export class MetaAdsManager {
  private api: typeof FacebookAdsApi;
  private adAccount: AdAccount;
  private config: MetaConfig;
  private eventDeduplicationCache: Set<string> = new Set();
  private readonly CACHE_TTL = 24 * 60 * 60 * 1000; // 24 hours

  constructor(config: MetaConfig) {
    this.config = config;

    // Initialize Facebook Ads API
    this.api = FacebookAdsApi.init(config.accessToken);
    this.adAccount = new AdAccount(`act_${config.adAccountId}`);

    console.log(`Meta Ads Manager initialized for account: act_${config.adAccountId}`);

    // Clean up deduplication cache periodically
    setInterval(() => {
      this.eventDeduplicationCache.clear();
      console.log('Event deduplication cache cleared');
    }, this.CACHE_TTL);
  }

  /**
   * Agent 12: Create Campaign
   * Agent 95: Enhanced with retry logic
   */
  async createCampaign(params: CampaignParams): Promise<string> {
    return retryWithBackoff(async () => {
      try {
        const campaign = await this.adAccount.createCampaign([], {
          name: params.name,
          objective: params.objective || 'OUTCOME_ENGAGEMENT',
          status: params.status || 'PAUSED',
          special_ad_categories: params.specialAdCategories || []
        });

        console.log(`Campaign created: ${campaign.id}`);
        return campaign.id;
      } catch (error: any) {
        console.error('Error creating campaign:', error);
        throw this.normalizeError(error, 'Failed to create campaign');
      }
    });
  }

  /**
   * Agent 12: Create AdSet
   */
  async createAdSet(params: AdSetParams): Promise<string> {
    try {
      const adSet = await this.adAccount.createAdSet([], {
        name: params.name,
        campaign_id: params.campaignId,
        billing_event: params.billingEvent || 'IMPRESSIONS',
        optimization_goal: params.optimizationGoal || 'REACH',
        bid_amount: params.bidAmount,
        daily_budget: params.dailyBudget,
        targeting: params.targeting,
        status: params.status || 'PAUSED'
      });

      console.log(`AdSet created: ${adSet.id}`);
      return adSet.id;
    } catch (error: any) {
      console.error('Error creating adset:', error);
      throw new Error(`Failed to create adset: ${error.message}`);
    }
  }

  /**
   * Agent 13: Upload Video
   */
  async uploadVideo(videoPath: string): Promise<string> {
    try {
      if (!fs.existsSync(videoPath)) {
        throw new Error(`Video file not found: ${videoPath}`);
      }

      const video = await this.adAccount.createAdVideo([], {
        source: videoPath
      });

      console.log(`Video uploaded: ${video.id}`);
      return video.id;
    } catch (error: any) {
      console.error('Error uploading video:', error);
      throw new Error(`Failed to upload video: ${error.message}`);
    }
  }

  /**
   * Agent 13: Create Ad Creative
   */
  async createAdCreative(params: AdCreativeParams): Promise<string> {
    try {
      const creativeData: any = {
        name: params.name,
        object_story_spec: {
          page_id: this.config.pageId,
          video_data: {
            video_id: params.videoId,
            title: params.title,
            message: params.message
          }
        }
      };

      // Add call to action if provided
      if (params.callToAction) {
        creativeData.object_story_spec.video_data.call_to_action = params.callToAction;
      }

      const creative = await this.adAccount.createAdCreative([], creativeData);

      console.log(`Ad Creative created: ${creative.id}`);
      return creative.id;
    } catch (error: any) {
      console.error('Error creating ad creative:', error);
      throw new Error(`Failed to create ad creative: ${error.message}`);
    }
  }

  /**
   * Agent 13: Create Ad
   */
  async createAd(params: AdParams): Promise<string> {
    try {
      const ad = await this.adAccount.createAd([], {
        name: params.name,
        adset_id: params.adSetId,
        creative: { creative_id: params.creativeId },
        status: params.status || 'PAUSED'
      });

      console.log(`Ad created: ${ad.id}`);
      return ad.id;
    } catch (error: any) {
      console.error('Error creating ad:', error);
      throw new Error(`Failed to create ad: ${error.message}`);
    }
  }

  /**
   * Agent 13: Complete workflow - Upload video and create ad
   */
  async createVideoAd(
    videoPath: string,
    campaignId: string,
    adSetId: string,
    creative: AdCreativeParams,
    adName: string
  ): Promise<{ adId: string; videoId: string; creativeId: string }> {
    try {
      // Step 1: Upload video
      const videoId = await this.uploadVideo(videoPath);

      // Step 2: Create ad creative
      const creativeParams = {
        ...creative,
        videoId
      };
      const creativeId = await this.createAdCreative(creativeParams);

      // Step 3: Create ad
      const adId = await this.createAd({
        name: adName,
        adSetId,
        creativeId,
        status: 'PAUSED'
      });

      console.log(`Video ad created successfully: ${adId}`);
      return { adId, videoId, creativeId };
    } catch (error: any) {
      console.error('Error in createVideoAd workflow:', error);
      throw error;
    }
  }

  /**
   * Agent 14: Get Ad Insights
   */
  async getAdInsights(
    adId: string,
    datePreset: string = 'last_7d',
    fields?: string[]
  ): Promise<any> {
    try {
      const defaultFields = [
        'impressions',
        'clicks',
        'spend',
        'ctr',
        'cpm',
        'cpp',
        'reach',
        'frequency',
        'conversions',
        'cost_per_conversion'
      ];

      const ad = new Ad(adId);
      const insights = await ad.getInsights(
        fields || defaultFields,
        {
          date_preset: datePreset
        }
      );

      if (insights && insights.length > 0) {
        return insights[0];
      }

      return null;
    } catch (error: any) {
      console.error('Error getting ad insights:', error);
      throw new Error(`Failed to get ad insights: ${error.message}`);
    }
  }

  /**
   * Agent 14: Get Campaign Insights
   */
  async getCampaignInsights(
    campaignId: string,
    datePreset: string = 'last_7d'
  ): Promise<any> {
    try {
      const campaign = new Campaign(campaignId);
      const insights = await campaign.getInsights(
        [
          'impressions',
          'clicks',
          'spend',
          'ctr',
          'reach',
          'frequency',
          'conversions',
          'cost_per_conversion',
          'actions',
          'action_values'
        ],
        {
          date_preset: datePreset
        }
      );

      if (insights && insights.length > 0) {
        return insights[0];
      }

      return null;
    } catch (error: any) {
      console.error('Error getting campaign insights:', error);
      throw new Error(`Failed to get campaign insights: ${error.message}`);
    }
  }

  /**
   * Agent 14: Get AdSet Insights
   */
  async getAdSetInsights(
    adSetId: string,
    datePreset: string = 'last_7d'
  ): Promise<any> {
    try {
      const adSet = new AdSet(adSetId);
      const insights = await adSet.getInsights(
        [
          'impressions',
          'clicks',
          'spend',
          'ctr',
          'cpm',
          'reach',
          'conversions'
        ],
        {
          date_preset: datePreset
        }
      );

      if (insights && insights.length > 0) {
        return insights[0];
      }

      return null;
    } catch (error: any) {
      console.error('Error getting adset insights:', error);
      throw new Error(`Failed to get adset insights: ${error.message}`);
    }
  }

  /**
   * Agent 14: Sync insights to database
   */
  async syncInsightsToDatabase(adId: string, insights: any): Promise<void> {
    try {
      console.log(`Syncing insights for ad ${adId}:`, {
        impressions: insights.impressions,
        clicks: insights.clicks,
        ctr: insights.ctr,
        spend: insights.spend
      });
    } catch (error: any) {
      console.error('Error syncing insights to database:', error);
      throw error;
    }
  }

  /**
   * Update ad status (activate/pause)
   */
  async updateAdStatus(adId: string, status: 'ACTIVE' | 'PAUSED'): Promise<void> {
    try {
      const ad = new Ad(adId);
      await ad.update([], { status });
      console.log(`Ad ${adId} status updated to ${status}`);
    } catch (error: any) {
      console.error('Error updating ad status:', error);
      throw new Error(`Failed to update ad status: ${error.message}`);
    }
  }

  /**
   * Update adset budget
   */
  async updateAdSetBudget(adSetId: string, dailyBudget: number): Promise<void> {
    try {
      const adSet = new AdSet(adSetId);
      await adSet.update([], { daily_budget: dailyBudget });
      console.log(`AdSet ${adSetId} budget updated to ${dailyBudget}`);
    } catch (error: any) {
      console.error('Error updating adset budget:', error);
      throw new Error(`Failed to update adset budget: ${error.message}`);
    }
  }

  /**
   * Get account info
   */
  async getAccountInfo(): Promise<any> {
    try {
      const fields = ['id', 'name', 'account_status', 'currency', 'timezone_name'];
      const accountInfo = await this.adAccount.read(fields);
      return accountInfo;
    } catch (error: any) {
      console.error('Error getting account info:', error);
      throw new Error(`Failed to get account info: ${error.message}`);
    }
  }

  /**
   * Get Account Level Insights (for Ingestion)
   */
  async getAccountInsights(datePreset: string = 'last_7d'): Promise<any[]> {
    try {
      const fields = [
        'ad_id',
        'ad_name',
        'impressions',
        'clicks',
        'spend',
        'actions',
        'action_values',
        'ctr'
      ];

      // Using the ad account object to fetch insights at 'ad' level
      const insights = await this.adAccount.getInsights(
        fields,
        {
          level: 'ad',
          date_preset: datePreset,
          time_increment: 'all_days'
        }
      );

      return insights;
    } catch (error: any) {
      console.error('Meta API Error (getAccountInsights):', error);
      throw new Error(`Failed to fetch account insights: ${error.message}`);
    }
  }

  /**
   * Agent 95: Send Conversion API Event
   * Implements event deduplication using event_id
   */
  async sendConversionEvent(event: ConversionEvent, pixelId?: string): Promise<void> {
    return retryWithBackoff(async () => {
      try {
        // Generate event ID for deduplication
        const eventId = this.generateEventId(event);

        // Check if event already sent (deduplication)
        if (this.eventDeduplicationCache.has(eventId)) {
          console.log(`Event ${eventId} already sent, skipping (deduplication)`);
          return;
        }

        // Hash user data for privacy
        const hashedUserData = this.hashUserData(event.userData);

        const eventData = {
          event_name: event.eventName,
          event_time: event.eventTime,
          event_id: eventId,
          action_source: event.actionSource,
          user_data: hashedUserData,
          custom_data: event.customData || {},
          event_source_url: event.eventSourceUrl || ''
        };

        // Use pixel ID from config if not provided
        const targetPixelId = pixelId || this.config.pageId;

        // Send to Meta Conversion API
        const META_API_VERSION = 'v18.0';
        const url = `https://graph.facebook.com/${META_API_VERSION}/${targetPixelId}/events`;

        await axios.post(url, {
          data: [eventData],
          access_token: this.config.accessToken
        });

        // Add to deduplication cache
        this.eventDeduplicationCache.add(eventId);

        console.log(`Conversion event sent successfully: ${event.eventName} (${eventId})`);
      } catch (error: any) {
        console.error('Error sending conversion event:', error);
        throw this.normalizeError(error, 'Failed to send conversion event');
      }
    });
  }

  /**
   * Agent 95: Generate unique event ID for deduplication
   */
  private generateEventId(event: ConversionEvent): string {
    const data = JSON.stringify({
      eventName: event.eventName,
      eventTime: event.eventTime,
      externalId: event.userData.externalId,
      email: event.userData.email
    });

    return crypto.createHash('sha256').update(data).digest('hex').substring(0, 16);
  }

  /**
   * Agent 95: Hash user data for privacy compliance
   */
  private hashUserData(userData: ConversionEvent['userData']): any {
    const hashed: any = {};

    if (userData.email) {
      hashed.em = crypto.createHash('sha256')
        .update(userData.email.toLowerCase().trim())
        .digest('hex');
    }

    if (userData.phone) {
      hashed.ph = crypto.createHash('sha256')
        .update(userData.phone.replace(/\D/g, ''))
        .digest('hex');
    }

    if (userData.externalId) {
      hashed.external_id = userData.externalId;
    }

    // Non-PII fields don't need hashing
    if (userData.clientIpAddress) hashed.client_ip_address = userData.clientIpAddress;
    if (userData.clientUserAgent) hashed.client_user_agent = userData.clientUserAgent;
    if (userData.fbc) hashed.fbc = userData.fbc;
    if (userData.fbp) hashed.fbp = userData.fbp;

    return hashed;
  }

  /**
   * Agent 95: Normalize error responses for consistent error handling
   */
  private normalizeError(error: any, defaultMessage: string): Error {
    const errorObj = new Error(defaultMessage);

    if (error.response?.data?.error) {
      const fbError = error.response.data.error;
      (errorObj as any).code = fbError.code;
      (errorObj as any).type = fbError.type;
      (errorObj as any).message = fbError.message || defaultMessage;
      (errorObj as any).fbtrace_id = fbError.fbtrace_id;
    } else if (error.message) {
      (errorObj as any).message = error.message;
    }

    return errorObj;
  }
}

export default MetaAdsManager;
