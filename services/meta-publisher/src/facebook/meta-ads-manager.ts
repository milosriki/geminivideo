/**
 * Meta Ads Manager - Real Facebook SDK Integration
 * Agents 11-14: Campaign, AdSet, Ad creation, Video upload, and Insights
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

/**
 * Meta Ads Manager - Full Facebook Marketing API Integration
 */
export class MetaAdsManager {
  private api: typeof FacebookAdsApi;
  private adAccount: AdAccount;
  private config: MetaConfig;

  constructor(config: MetaConfig) {
    this.config = config;

    // Initialize Facebook Ads API
    this.api = FacebookAdsApi.init(config.accessToken);
    this.adAccount = new AdAccount(`act_${config.adAccountId}`);

    console.log(`Meta Ads Manager initialized for account: act_${config.adAccountId}`);
  }

  /**
   * Agent 12: Create Campaign
   */
  async createCampaign(params: CampaignParams): Promise<string> {
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
      throw new Error(`Failed to create campaign: ${error.message}`);
    }
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
   * Get all campaigns for the account
   */
  async getCampaigns(limit: number = 20): Promise<any[]> {
    try {
      const fields = ['id', 'name', 'status', 'objective', 'start_time', 'stop_time'];
      const campaigns = await this.adAccount.getCampaigns(fields, { limit });
      return campaigns;
    } catch (error: any) {
      console.error('Error getting campaigns:', error);
      throw new Error(`Failed to get campaigns: ${error.message}`);
    }
  }
}

export default MetaAdsManager;
