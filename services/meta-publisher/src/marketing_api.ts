import axios, { AxiosError, AxiosInstance } from 'axios';

/**
 * Meta Marketing API v19.0 Implementation
 *
 * This module provides a comprehensive interface to Meta's Marketing API v19.0
 * for managing ads, campaigns, ad sets, and creative content.
 *
 * @see https://developers.facebook.com/docs/marketing-api
 */

const API_VERSION = 'v19.0';
const BASE_URL = `https://graph.facebook.com/${API_VERSION}`;
const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1000;

// ==================== Interfaces ====================

export interface MetaApiConfig {
  accessToken: string;
  adAccountId: string;
  maxRetries?: number;
  retryDelay?: number;
}

export interface CreateAdParams {
  name: string;
  adset_id: string;
  creative: {
    creative_id: string;
  } | AdCreative;
  status?: 'ACTIVE' | 'PAUSED' | 'DELETED' | 'ARCHIVED';
  tracking_specs?: any[];
  conversion_specs?: any[];
}

export interface UpdateAdParams {
  name?: string;
  status?: 'ACTIVE' | 'PAUSED' | 'DELETED' | 'ARCHIVED';
  adset_id?: string;
  creative?: {
    creative_id: string;
  };
  tracking_specs?: any[];
}

export interface AdResponse {
  id: string;
  name?: string;
  status?: string;
  adset_id?: string;
  campaign_id?: string;
  created_time?: string;
  updated_time?: string;
}

export interface CreateCampaignParams {
  name: string;
  objective: CampaignObjective;
  status?: 'ACTIVE' | 'PAUSED' | 'DELETED' | 'ARCHIVED';
  special_ad_categories?: SpecialAdCategory[];
  buying_type?: 'AUCTION' | 'RESERVED';
  daily_budget?: number;
  lifetime_budget?: number;
  bid_strategy?: string;
  promoted_object?: any;
}

export interface UpdateCampaignParams {
  name?: string;
  status?: 'ACTIVE' | 'PAUSED' | 'DELETED' | 'ARCHIVED';
  daily_budget?: number;
  lifetime_budget?: number;
  bid_strategy?: string;
}

export interface CampaignResponse {
  id: string;
  name?: string;
  objective?: string;
  status?: string;
  created_time?: string;
  updated_time?: string;
  daily_budget?: string;
  lifetime_budget?: string;
}

export interface CreateAdSetParams {
  name: string;
  campaign_id: string;
  status?: 'ACTIVE' | 'PAUSED' | 'DELETED' | 'ARCHIVED';
  billing_event?: string;
  optimization_goal?: string;
  bid_amount?: number;
  daily_budget?: number;
  lifetime_budget?: number;
  targeting?: AdTargeting;
  start_time?: string;
  end_time?: string;
}

export interface UpdateAdSetParams {
  name?: string;
  status?: 'ACTIVE' | 'PAUSED' | 'DELETED' | 'ARCHIVED';
  bid_amount?: number;
  daily_budget?: number;
  lifetime_budget?: number;
  targeting?: AdTargeting;
}

export interface AdSetResponse {
  id: string;
  name?: string;
  campaign_id?: string;
  status?: string;
  billing_event?: string;
  optimization_goal?: string;
  created_time?: string;
  updated_time?: string;
}

export interface AdTargeting {
  geo_locations?: {
    countries?: string[];
    regions?: any[];
    cities?: any[];
  };
  age_min?: number;
  age_max?: number;
  genders?: number[];
  interests?: any[];
  behaviors?: any[];
  custom_audiences?: any[];
  excluded_custom_audiences?: any[];
}

export interface AdCreative {
  name?: string;
  object_story_spec?: any;
  asset_feed_spec?: any;
  degrees_of_freedom_spec?: any;
}

export type CampaignObjective =
  | 'APP_INSTALLS'
  | 'BRAND_AWARENESS'
  | 'EVENT_RESPONSES'
  | 'LEAD_GENERATION'
  | 'LINK_CLICKS'
  | 'LOCAL_AWARENESS'
  | 'MESSAGES'
  | 'OFFER_CLAIMS'
  | 'OUTCOME_APP_PROMOTION'
  | 'OUTCOME_AWARENESS'
  | 'OUTCOME_ENGAGEMENT'
  | 'OUTCOME_LEADS'
  | 'OUTCOME_SALES'
  | 'OUTCOME_TRAFFIC'
  | 'PAGE_LIKES'
  | 'POST_ENGAGEMENT'
  | 'PRODUCT_CATALOG_SALES'
  | 'REACH'
  | 'STORE_VISITS'
  | 'VIDEO_VIEWS';

export type SpecialAdCategory = 'CREDIT' | 'EMPLOYMENT' | 'HOUSING' | 'ISSUES_ELECTIONS_POLITICS' | 'ONLINE_GAMBLING_AND_GAMING' | 'NONE';

export interface MetaApiError {
  message: string;
  type: string;
  code: number;
  error_subcode?: number;
  error_user_title?: string;
  error_user_msg?: string;
  fbtrace_id?: string;
}

export interface AdInsightsParams {
  fields?: string[];
  time_range?: {
    since: string;
    until: string;
  };
  level?: 'ad' | 'adset' | 'campaign' | 'account';
  breakdowns?: string[];
}

// ==================== Meta Marketing API Class ====================

export class MetaMarketingAPI {
  private accessToken: string;
  private adAccountId: string;
  private maxRetries: number;
  private retryDelay: number;
  private axiosInstance: AxiosInstance;

  constructor(config: MetaApiConfig) {
    this.accessToken = config.accessToken;
    this.adAccountId = config.adAccountId;
    this.maxRetries = config.maxRetries || MAX_RETRIES;
    this.retryDelay = config.retryDelay || RETRY_DELAY_MS;

    // Create axios instance with default config
    this.axiosInstance = axios.create({
      baseURL: BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      (error) => this.handleAxiosError(error)
    );
  }

  // ==================== Private Helper Methods ====================

  /**
   * Handles axios errors and transforms them to MetaApiError
   */
  private handleAxiosError(error: AxiosError): never {
    if (error.response?.data) {
      const data = error.response.data as any;
      if (data.error) {
        const metaError: MetaApiError = {
          message: data.error.message || 'Unknown Meta API error',
          type: data.error.type || 'UnknownError',
          code: data.error.code || 0,
          error_subcode: data.error.error_subcode,
          error_user_title: data.error.error_user_title,
          error_user_msg: data.error.error_user_msg,
          fbtrace_id: data.error.fbtrace_id,
        };
        throw new Error(
          `Meta API Error [${metaError.code}]: ${metaError.message}${
            metaError.fbtrace_id ? ` (fbtrace_id: ${metaError.fbtrace_id})` : ''
          }`
        );
      }
    }
    throw error;
  }

  /**
   * Checks if an error is retryable based on error code
   */
  private isRetryableError(error: any): boolean {
    // Retryable error codes from Meta API
    const retryableCodes = [
      1, // API Unknown error
      2, // API Service error
      4, // API Too Many Calls
      17, // API User Too Many Calls
      32, // API Page Too Many Calls
      80000, // There was an error performing this operation
      190, // Access token has expired (if using token refresh)
    ];

    if (axios.isAxiosError(error) && error.response?.data) {
      const data = error.response.data as any;
      if (data.error && retryableCodes.includes(data.error.code)) {
        return true;
      }
    }

    // Also retry on network errors
    if (error.code === 'ECONNRESET' || error.code === 'ETIMEDOUT' || error.code === 'ENOTFOUND') {
      return true;
    }

    return false;
  }

  /**
   * Executes a request with retry logic
   */
  private async executeWithRetry<T>(
    operation: () => Promise<T>,
    retryCount: number = 0
  ): Promise<T> {
    try {
      return await operation();
    } catch (error) {
      if (retryCount < this.maxRetries && this.isRetryableError(error)) {
        const delay = this.retryDelay * Math.pow(2, retryCount); // Exponential backoff
        console.warn(
          `Meta API request failed, retrying in ${delay}ms... (attempt ${retryCount + 1}/${this.maxRetries})`
        );
        await this.sleep(delay);
        return this.executeWithRetry(operation, retryCount + 1);
      }
      throw error;
    }
  }

  /**
   * Sleep helper for retries
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Builds query parameters including access token
   */
  private buildParams(additionalParams: Record<string, any> = {}): Record<string, any> {
    return {
      access_token: this.accessToken,
      ...additionalParams,
    };
  }

  /**
   * Formats ad account ID with 'act_' prefix if needed
   */
  private formatAdAccountId(adAccountId?: string): string {
    const accountId = adAccountId || this.adAccountId;
    return accountId.startsWith('act_') ? accountId : `act_${accountId}`;
  }

  // ==================== Campaign Methods ====================

  /**
   * Creates a new campaign
   * @see https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group
   */
  async createCampaign(params: CreateCampaignParams): Promise<CampaignResponse> {
    return this.executeWithRetry(async () => {
      const accountId = this.formatAdAccountId();
      const response = await this.axiosInstance.post(
        `/${accountId}/campaigns`,
        params,
        {
          params: this.buildParams(),
        }
      );
      return response.data;
    });
  }

  /**
   * Updates an existing campaign
   * @see https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group
   */
  async updateCampaign(campaignId: string, params: UpdateCampaignParams): Promise<CampaignResponse> {
    return this.executeWithRetry(async () => {
      const response = await this.axiosInstance.post(
        `/${campaignId}`,
        params,
        {
          params: this.buildParams(),
        }
      );
      return response.data;
    });
  }

  /**
   * Deletes a campaign
   * @see https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group
   */
  async deleteCampaign(campaignId: string): Promise<{ success: boolean }> {
    return this.executeWithRetry(async () => {
      const response = await this.axiosInstance.delete(`/${campaignId}`, {
        params: this.buildParams(),
      });
      return response.data;
    });
  }

  /**
   * Gets campaign details
   * @see https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group
   */
  async getCampaign(campaignId: string, fields?: string[]): Promise<CampaignResponse> {
    return this.executeWithRetry(async () => {
      const params = this.buildParams();
      if (fields && fields.length > 0) {
        params.fields = fields.join(',');
      }
      const response = await this.axiosInstance.get(`/${campaignId}`, { params });
      return response.data;
    });
  }

  /**
   * Lists campaigns for the ad account
   * @see https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group
   */
  async listCampaigns(fields?: string[], limit?: number): Promise<{ data: CampaignResponse[] }> {
    return this.executeWithRetry(async () => {
      const accountId = this.formatAdAccountId();
      const params = this.buildParams();
      if (fields && fields.length > 0) {
        params.fields = fields.join(',');
      }
      if (limit) {
        params.limit = limit;
      }
      const response = await this.axiosInstance.get(`/${accountId}/campaigns`, { params });
      return response.data;
    });
  }

  // ==================== Ad Set Methods ====================

  /**
   * Creates a new ad set
   * @see https://developers.facebook.com/docs/marketing-api/reference/ad-campaign
   */
  async createAdSet(params: CreateAdSetParams): Promise<AdSetResponse> {
    return this.executeWithRetry(async () => {
      const accountId = this.formatAdAccountId();
      const response = await this.axiosInstance.post(
        `/${accountId}/adsets`,
        params,
        {
          params: this.buildParams(),
        }
      );
      return response.data;
    });
  }

  /**
   * Updates an existing ad set
   * @see https://developers.facebook.com/docs/marketing-api/reference/ad-campaign
   */
  async updateAdSet(adSetId: string, params: UpdateAdSetParams): Promise<AdSetResponse> {
    return this.executeWithRetry(async () => {
      const response = await this.axiosInstance.post(
        `/${adSetId}`,
        params,
        {
          params: this.buildParams(),
        }
      );
      return response.data;
    });
  }

  /**
   * Deletes an ad set
   * @see https://developers.facebook.com/docs/marketing-api/reference/ad-campaign
   */
  async deleteAdSet(adSetId: string): Promise<{ success: boolean }> {
    return this.executeWithRetry(async () => {
      const response = await this.axiosInstance.delete(`/${adSetId}`, {
        params: this.buildParams(),
      });
      return response.data;
    });
  }

  /**
   * Gets ad set details
   * @see https://developers.facebook.com/docs/marketing-api/reference/ad-campaign
   */
  async getAdSet(adSetId: string, fields?: string[]): Promise<AdSetResponse> {
    return this.executeWithRetry(async () => {
      const params = this.buildParams();
      if (fields && fields.length > 0) {
        params.fields = fields.join(',');
      }
      const response = await this.axiosInstance.get(`/${adSetId}`, { params });
      return response.data;
    });
  }

  // ==================== Ad Methods ====================

  /**
   * Creates a new ad
   * @see https://developers.facebook.com/docs/marketing-api/reference/adgroup
   */
  async createAd(params: CreateAdParams): Promise<AdResponse> {
    return this.executeWithRetry(async () => {
      const accountId = this.formatAdAccountId();
      const response = await this.axiosInstance.post(
        `/${accountId}/ads`,
        params,
        {
          params: this.buildParams(),
        }
      );
      return response.data;
    });
  }

  /**
   * Updates an existing ad
   * @see https://developers.facebook.com/docs/marketing-api/reference/adgroup
   */
  async updateAd(adId: string, params: UpdateAdParams): Promise<AdResponse> {
    return this.executeWithRetry(async () => {
      const response = await this.axiosInstance.post(
        `/${adId}`,
        params,
        {
          params: this.buildParams(),
        }
      );
      return response.data;
    });
  }

  /**
   * Deletes an ad
   * @see https://developers.facebook.com/docs/marketing-api/reference/adgroup
   */
  async deleteAd(adId: string): Promise<{ success: boolean }> {
    return this.executeWithRetry(async () => {
      const response = await this.axiosInstance.delete(`/${adId}`, {
        params: this.buildParams(),
      });
      return response.data;
    });
  }

  /**
   * Gets ad details
   * @see https://developers.facebook.com/docs/marketing-api/reference/adgroup
   */
  async getAd(adId: string, fields?: string[]): Promise<AdResponse> {
    return this.executeWithRetry(async () => {
      const params = this.buildParams();
      if (fields && fields.length > 0) {
        params.fields = fields.join(',');
      }
      const response = await this.axiosInstance.get(`/${adId}`, { params });
      return response.data;
    });
  }

  /**
   * Lists ads for the ad account
   * @see https://developers.facebook.com/docs/marketing-api/reference/adgroup
   */
  async listAds(fields?: string[], limit?: number): Promise<{ data: AdResponse[] }> {
    return this.executeWithRetry(async () => {
      const accountId = this.formatAdAccountId();
      const params = this.buildParams();
      if (fields && fields.length > 0) {
        params.fields = fields.join(',');
      }
      if (limit) {
        params.limit = limit;
      }
      const response = await this.axiosInstance.get(`/${accountId}/ads`, { params });
      return response.data;
    });
  }

  // ==================== Ad Creative Methods ====================

  /**
   * Creates a new ad creative
   * @see https://developers.facebook.com/docs/marketing-api/reference/ad-creative
   */
  async createAdCreative(creative: AdCreative): Promise<{ id: string }> {
    return this.executeWithRetry(async () => {
      const accountId = this.formatAdAccountId();
      const response = await this.axiosInstance.post(
        `/${accountId}/adcreatives`,
        creative,
        {
          params: this.buildParams(),
        }
      );
      return response.data;
    });
  }

  /**
   * Gets ad creative details
   * @see https://developers.facebook.com/docs/marketing-api/reference/ad-creative
   */
  async getAdCreative(creativeId: string, fields?: string[]): Promise<any> {
    return this.executeWithRetry(async () => {
      const params = this.buildParams();
      if (fields && fields.length > 0) {
        params.fields = fields.join(',');
      }
      const response = await this.axiosInstance.get(`/${creativeId}`, { params });
      return response.data;
    });
  }

  // ==================== Insights Methods ====================

  /**
   * Gets insights for an ad
   * @see https://developers.facebook.com/docs/marketing-api/insights
   */
  async getAdInsights(adId: string, params?: AdInsightsParams): Promise<any> {
    return this.executeWithRetry(async () => {
      const queryParams = this.buildParams();
      if (params?.fields && params.fields.length > 0) {
        queryParams.fields = params.fields.join(',');
      }
      if (params?.time_range) {
        queryParams.time_range = JSON.stringify(params.time_range);
      }
      if (params?.level) {
        queryParams.level = params.level;
      }
      if (params?.breakdowns && params.breakdowns.length > 0) {
        queryParams.breakdowns = params.breakdowns.join(',');
      }
      const response = await this.axiosInstance.get(`/${adId}/insights`, {
        params: queryParams,
      });
      return response.data;
    });
  }

  /**
   * Gets insights for a campaign
   * @see https://developers.facebook.com/docs/marketing-api/insights
   */
  async getCampaignInsights(campaignId: string, params?: AdInsightsParams): Promise<any> {
    return this.executeWithRetry(async () => {
      const queryParams = this.buildParams();
      if (params?.fields && params.fields.length > 0) {
        queryParams.fields = params.fields.join(',');
      }
      if (params?.time_range) {
        queryParams.time_range = JSON.stringify(params.time_range);
      }
      if (params?.level) {
        queryParams.level = params.level;
      }
      if (params?.breakdowns && params.breakdowns.length > 0) {
        queryParams.breakdowns = params.breakdowns.join(',');
      }
      const response = await this.axiosInstance.get(`/${campaignId}/insights`, {
        params: queryParams,
      });
      return response.data;
    });
  }

  /**
   * Gets insights for an ad account
   * @see https://developers.facebook.com/docs/marketing-api/insights
   */
  async getAccountInsights(params?: AdInsightsParams, adAccountId?: string): Promise<any> {
    return this.executeWithRetry(async () => {
      const accountId = this.formatAdAccountId(adAccountId);
      const queryParams = this.buildParams();
      if (params?.fields && params.fields.length > 0) {
        queryParams.fields = params.fields.join(',');
      }
      if (params?.time_range) {
        queryParams.time_range = JSON.stringify(params.time_range);
      }
      if (params?.level) {
        queryParams.level = params.level;
      }
      if (params?.breakdowns && params.breakdowns.length > 0) {
        queryParams.breakdowns = params.breakdowns.join(',');
      }
      const response = await this.axiosInstance.get(`/${accountId}/insights`, {
        params: queryParams,
      });
      return response.data;
    });
  }

  // ==================== Batch Operations ====================

  /**
   * Performs batch operations for multiple requests
   * @see https://developers.facebook.com/docs/graph-api/making-multiple-requests
   */
  async batchRequest(requests: Array<{ method: string; relative_url: string; body?: any }>): Promise<any> {
    return this.executeWithRetry(async () => {
      const response = await this.axiosInstance.post(
        '/',
        {
          batch: JSON.stringify(requests),
        },
        {
          params: this.buildParams(),
        }
      );
      return response.data;
    });
  }

  // ==================== Utility Methods ====================

  /**
   * Validates the access token
   * @see https://developers.facebook.com/docs/facebook-login/guides/access-tokens/debugging-and-error-handling
   */
  async debugToken(): Promise<any> {
    return this.executeWithRetry(async () => {
      const response = await this.axiosInstance.get('/debug_token', {
        params: {
          input_token: this.accessToken,
          access_token: this.accessToken,
        },
      });
      return response.data;
    });
  }

  /**
   * Gets ad account details
   * @see https://developers.facebook.com/docs/marketing-api/reference/ad-account
   */
  async getAdAccount(fields?: string[], adAccountId?: string): Promise<any> {
    return this.executeWithRetry(async () => {
      const accountId = this.formatAdAccountId(adAccountId);
      const params = this.buildParams();
      if (fields && fields.length > 0) {
        params.fields = fields.join(',');
      }
      const response = await this.axiosInstance.get(`/${accountId}`, { params });
      return response.data;
    });
  }
}

// ==================== Factory Function ====================

/**
 * Creates a new instance of MetaMarketingAPI
 */
export function createMetaMarketingAPI(config: MetaApiConfig): MetaMarketingAPI {
  return new MetaMarketingAPI(config);
}

// ==================== Default Export ====================

export default MetaMarketingAPI;
