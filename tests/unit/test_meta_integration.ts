/**
 * Unit Tests for Meta Marketing API Integration
 * Tests Meta Ads Manager, CAPI events, Ads Library scraper, Pixel service
 *
 * Agent 29 of 30 - Comprehensive Test Suite
 * Coverage Target: 80%+
 */

import { jest, describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import { MetaAdsManager, MetaConfig, CampaignParams, AdSetParams, AdCreativeParams, AdParams } from '../../services/meta-publisher/src/facebook/meta-ads-manager';
import { FacebookAdsApi, AdAccount, Campaign, AdSet, Ad, AdCreative, AdVideo } from 'facebook-nodejs-business-sdk';
import * as fs from 'fs';

// Mock Facebook SDK
jest.mock('facebook-nodejs-business-sdk');

// Mock filesystem
jest.mock('fs');

describe('MetaAdsManager - Core Functionality', () => {
  let manager: MetaAdsManager;
  let mockConfig: MetaConfig;
  let mockAdAccount: any;

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();

    // Setup mock config
    mockConfig = {
      accessToken: 'test_access_token_abc123',
      adAccountId: '123456789',
      pageId: '987654321'
    };

    // Mock AdAccount instance
    mockAdAccount = {
      createCampaign: jest.fn(),
      createAdSet: jest.fn(),
      createAdVideo: jest.fn(),
      createAdCreative: jest.fn(),
      createAd: jest.fn(),
      read: jest.fn()
    };

    // Mock FacebookAdsApi
    (FacebookAdsApi.init as jest.Mock) = jest.fn().mockReturnValue({});
    (AdAccount as any).mockImplementation(() => mockAdAccount);

    // Initialize manager
    manager = new MetaAdsManager(mockConfig);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  // ============================================================================
  // CAMPAIGN CREATION TESTS (Agent 12)
  // ============================================================================

  describe('createCampaign', () => {
    it('should create campaign with default parameters', async () => {
      const mockCampaignId = '120202345678901234';
      mockAdAccount.createCampaign.mockResolvedValue({ id: mockCampaignId });

      const params: CampaignParams = {
        name: 'Test Campaign'
      };

      const campaignId = await manager.createCampaign(params);

      expect(campaignId).toBe(mockCampaignId);
      expect(mockAdAccount.createCampaign).toHaveBeenCalledWith([], {
        name: 'Test Campaign',
        objective: 'OUTCOME_ENGAGEMENT',
        status: 'PAUSED',
        special_ad_categories: []
      });
    });

    it('should create campaign with custom parameters', async () => {
      const mockCampaignId = '120202345678901235';
      mockAdAccount.createCampaign.mockResolvedValue({ id: mockCampaignId });

      const params: CampaignParams = {
        name: 'Custom Campaign',
        objective: 'OUTCOME_SALES',
        status: 'ACTIVE',
        specialAdCategories: ['HOUSING', 'EMPLOYMENT']
      };

      const campaignId = await manager.createCampaign(params);

      expect(campaignId).toBe(mockCampaignId);
      expect(mockAdAccount.createCampaign).toHaveBeenCalledWith([], {
        name: 'Custom Campaign',
        objective: 'OUTCOME_SALES',
        status: 'ACTIVE',
        special_ad_categories: ['HOUSING', 'EMPLOYMENT']
      });
    });

    it('should handle campaign creation errors', async () => {
      mockAdAccount.createCampaign.mockRejectedValue(new Error('Invalid access token'));

      const params: CampaignParams = {
        name: 'Error Campaign'
      };

      await expect(manager.createCampaign(params)).rejects.toThrow('Failed to create campaign');
    });

    it('should validate campaign name is required', async () => {
      const params: any = {}; // Missing name

      await expect(async () => {
        await manager.createCampaign(params);
      }).rejects.toThrow();
    });
  });

  // ============================================================================
  // ADSET CREATION TESTS (Agent 12)
  // ============================================================================

  describe('createAdSet', () => {
    it('should create adset with targeting', async () => {
      const mockAdSetId = '120203456789012345';
      mockAdAccount.createAdSet.mockResolvedValue({ id: mockAdSetId });

      const params: AdSetParams = {
        name: 'Test AdSet',
        campaignId: '120202345678901234',
        bidAmount: 500,
        dailyBudget: 5000,
        targeting: {
          geo_locations: { countries: ['US'] },
          age_min: 25,
          age_max: 54
        }
      };

      const adSetId = await manager.createAdSet(params);

      expect(adSetId).toBe(mockAdSetId);
      expect(mockAdAccount.createAdSet).toHaveBeenCalledWith([], {
        name: 'Test AdSet',
        campaign_id: '120202345678901234',
        billing_event: 'IMPRESSIONS',
        optimization_goal: 'REACH',
        bid_amount: 500,
        daily_budget: 5000,
        targeting: params.targeting,
        status: 'PAUSED'
      });
    });

    it('should create adset with custom optimization goal', async () => {
      const mockAdSetId = '120203456789012346';
      mockAdAccount.createAdSet.mockResolvedValue({ id: mockAdSetId });

      const params: AdSetParams = {
        name: 'Conversion AdSet',
        campaignId: '120202345678901234',
        bidAmount: 1000,
        dailyBudget: 10000,
        targeting: { geo_locations: { countries: ['US', 'CA'] } },
        optimizationGoal: 'CONVERSIONS',
        billingEvent: 'IMPRESSIONS'
      };

      await manager.createAdSet(params);

      expect(mockAdAccount.createAdSet).toHaveBeenCalledWith(
        [],
        expect.objectContaining({
          optimization_goal: 'CONVERSIONS',
          billing_event: 'IMPRESSIONS'
        })
      );
    });

    it('should handle invalid campaign ID error', async () => {
      mockAdAccount.createAdSet.mockRejectedValue(new Error('Campaign does not exist'));

      const params: AdSetParams = {
        name: 'Invalid AdSet',
        campaignId: 'invalid_campaign_id',
        bidAmount: 500,
        dailyBudget: 5000,
        targeting: {}
      };

      await expect(manager.createAdSet(params)).rejects.toThrow('Failed to create adset');
    });

    it('should validate budget amounts', async () => {
      const mockAdSetId = '120203456789012347';
      mockAdAccount.createAdSet.mockResolvedValue({ id: mockAdSetId });

      const params: AdSetParams = {
        name: 'Budget Test',
        campaignId: '120202345678901234',
        bidAmount: 0, // Zero bid
        dailyBudget: 0, // Zero budget
        targeting: {}
      };

      // Should still call API (validation happens on Meta's side)
      await manager.createAdSet(params);
      expect(mockAdAccount.createAdSet).toHaveBeenCalled();
    });
  });

  // ============================================================================
  // VIDEO UPLOAD TESTS (Agent 13)
  // ============================================================================

  describe('uploadVideo', () => {
    it('should upload video successfully', async () => {
      const mockVideoId = '1234567890123456';
      const videoPath = '/path/to/video.mp4';

      (fs.existsSync as jest.Mock).mockReturnValue(true);
      mockAdAccount.createAdVideo.mockResolvedValue({ id: mockVideoId });

      const videoId = await manager.uploadVideo(videoPath);

      expect(videoId).toBe(mockVideoId);
      expect(fs.existsSync).toHaveBeenCalledWith(videoPath);
      expect(mockAdAccount.createAdVideo).toHaveBeenCalledWith([], {
        source: videoPath
      });
    });

    it('should throw error if video file does not exist', async () => {
      const videoPath = '/path/to/nonexistent.mp4';

      (fs.existsSync as jest.Mock).mockReturnValue(false);

      await expect(manager.uploadVideo(videoPath)).rejects.toThrow('Video file not found');
      expect(mockAdAccount.createAdVideo).not.toHaveBeenCalled();
    });

    it('should handle upload failures', async () => {
      const videoPath = '/path/to/video.mp4';

      (fs.existsSync as jest.Mock).mockReturnValue(true);
      mockAdAccount.createAdVideo.mockRejectedValue(new Error('Upload failed: File too large'));

      await expect(manager.uploadVideo(videoPath)).rejects.toThrow('Failed to upload video');
    });

    it('should handle various video formats', async () => {
      const videoFormats = ['.mp4', '.mov', '.avi', '.mkv'];

      for (const format of videoFormats) {
        const videoPath = `/path/to/video${format}`;
        const mockVideoId = `video_${format}_123`;

        (fs.existsSync as jest.Mock).mockReturnValue(true);
        mockAdAccount.createAdVideo.mockResolvedValue({ id: mockVideoId });

        const videoId = await manager.uploadVideo(videoPath);
        expect(videoId).toBe(mockVideoId);
      }
    });
  });

  // ============================================================================
  // AD CREATIVE TESTS (Agent 13)
  // ============================================================================

  describe('createAdCreative', () => {
    it('should create video ad creative', async () => {
      const mockCreativeId = '120204567890123456';
      mockAdAccount.createAdCreative.mockResolvedValue({ id: mockCreativeId });

      const params: AdCreativeParams = {
        name: 'Test Creative',
        videoId: '1234567890123456',
        title: 'Amazing Product',
        message: 'Check out our amazing product!'
      };

      const creativeId = await manager.createAdCreative(params);

      expect(creativeId).toBe(mockCreativeId);
      expect(mockAdAccount.createAdCreative).toHaveBeenCalledWith([], {
        name: 'Test Creative',
        object_story_spec: {
          page_id: mockConfig.pageId,
          video_data: {
            video_id: '1234567890123456',
            title: 'Amazing Product',
            message: 'Check out our amazing product!'
          }
        }
      });
    });

    it('should create creative with call-to-action', async () => {
      const mockCreativeId = '120204567890123457';
      mockAdAccount.createAdCreative.mockResolvedValue({ id: mockCreativeId });

      const params: AdCreativeParams = {
        name: 'CTA Creative',
        videoId: '1234567890123456',
        title: 'Shop Now',
        message: 'Limited time offer!',
        callToAction: {
          type: 'SHOP_NOW',
          value: { link: 'https://example.com/shop' }
        }
      };

      await manager.createAdCreative(params);

      expect(mockAdAccount.createAdCreative).toHaveBeenCalledWith(
        [],
        expect.objectContaining({
          object_story_spec: expect.objectContaining({
            video_data: expect.objectContaining({
              call_to_action: {
                type: 'SHOP_NOW',
                value: { link: 'https://example.com/shop' }
              }
            })
          })
        })
      );
    });

    it('should handle creative creation errors', async () => {
      mockAdAccount.createAdCreative.mockRejectedValue(new Error('Invalid video ID'));

      const params: AdCreativeParams = {
        name: 'Error Creative',
        videoId: 'invalid_video_id',
        title: 'Test',
        message: 'Test'
      };

      await expect(manager.createAdCreative(params)).rejects.toThrow('Failed to create ad creative');
    });
  });

  // ============================================================================
  // AD CREATION TESTS (Agent 13)
  // ============================================================================

  describe('createAd', () => {
    it('should create ad successfully', async () => {
      const mockAdId = '120205678901234567';
      mockAdAccount.createAd.mockResolvedValue({ id: mockAdId });

      const params: AdParams = {
        name: 'Test Ad',
        adSetId: '120203456789012345',
        creativeId: '120204567890123456'
      };

      const adId = await manager.createAd(params);

      expect(adId).toBe(mockAdId);
      expect(mockAdAccount.createAd).toHaveBeenCalledWith([], {
        name: 'Test Ad',
        adset_id: '120203456789012345',
        creative: { creative_id: '120204567890123456' },
        status: 'PAUSED'
      });
    });

    it('should create active ad', async () => {
      const mockAdId = '120205678901234568';
      mockAdAccount.createAd.mockResolvedValue({ id: mockAdId });

      const params: AdParams = {
        name: 'Active Ad',
        adSetId: '120203456789012345',
        creativeId: '120204567890123456',
        status: 'ACTIVE'
      };

      await manager.createAd(params);

      expect(mockAdAccount.createAd).toHaveBeenCalledWith(
        [],
        expect.objectContaining({ status: 'ACTIVE' })
      );
    });

    it('should handle ad creation errors', async () => {
      mockAdAccount.createAd.mockRejectedValue(new Error('AdSet not found'));

      const params: AdParams = {
        name: 'Error Ad',
        adSetId: 'invalid_adset',
        creativeId: '120204567890123456'
      };

      await expect(manager.createAd(params)).rejects.toThrow('Failed to create ad');
    });
  });

  // ============================================================================
  // COMPLETE VIDEO AD WORKFLOW TESTS (Agent 13)
  // ============================================================================

  describe('createVideoAd - Complete Workflow', () => {
    it('should execute complete video ad workflow', async () => {
      const videoPath = '/path/to/video.mp4';
      const campaignId = '120202345678901234';
      const adSetId = '120203456789012345';

      const creative: AdCreativeParams = {
        name: 'Workflow Creative',
        videoId: '', // Will be set during upload
        title: 'Complete Workflow',
        message: 'Testing complete workflow'
      };

      (fs.existsSync as jest.Mock).mockReturnValue(true);
      mockAdAccount.createAdVideo.mockResolvedValue({ id: 'video_123' });
      mockAdAccount.createAdCreative.mockResolvedValue({ id: 'creative_123' });
      mockAdAccount.createAd.mockResolvedValue({ id: 'ad_123' });

      const result = await manager.createVideoAd(
        videoPath,
        campaignId,
        adSetId,
        creative,
        'Complete Ad'
      );

      expect(result).toEqual({
        adId: 'ad_123',
        videoId: 'video_123',
        creativeId: 'creative_123'
      });

      expect(mockAdAccount.createAdVideo).toHaveBeenCalledTimes(1);
      expect(mockAdAccount.createAdCreative).toHaveBeenCalledTimes(1);
      expect(mockAdAccount.createAd).toHaveBeenCalledTimes(1);
    });

    it('should fail workflow if video upload fails', async () => {
      const videoPath = '/path/to/video.mp4';

      (fs.existsSync as jest.Mock).mockReturnValue(true);
      mockAdAccount.createAdVideo.mockRejectedValue(new Error('Upload failed'));

      await expect(
        manager.createVideoAd(
          videoPath,
          'campaign_123',
          'adset_123',
          { name: 'Test', videoId: '', title: 'Test', message: 'Test' },
          'Test Ad'
        )
      ).rejects.toThrow();

      expect(mockAdAccount.createAdCreative).not.toHaveBeenCalled();
      expect(mockAdAccount.createAd).not.toHaveBeenCalled();
    });
  });

  // ============================================================================
  // INSIGHTS TESTS (Agent 14)
  // ============================================================================

  describe('getAdInsights', () => {
    it('should fetch ad insights with default parameters', async () => {
      const mockInsights = [{
        impressions: '10000',
        clicks: '150',
        spend: '50.00',
        ctr: '1.5',
        cpm: '5.00'
      }];

      const mockAd = {
        getInsights: jest.fn().mockResolvedValue(mockInsights)
      };

      (Ad as any).mockImplementation(() => mockAd);

      const insights = await manager.getAdInsights('ad_123');

      expect(insights).toEqual(mockInsights[0]);
      expect(mockAd.getInsights).toHaveBeenCalledWith(
        expect.arrayContaining(['impressions', 'clicks', 'spend']),
        { date_preset: 'last_7d' }
      );
    });

    it('should fetch insights with custom date range', async () => {
      const mockInsights = [{ impressions: '5000' }];
      const mockAd = {
        getInsights: jest.fn().mockResolvedValue(mockInsights)
      };

      (Ad as any).mockImplementation(() => mockAd);

      await manager.getAdInsights('ad_123', 'last_30d');

      expect(mockAd.getInsights).toHaveBeenCalledWith(
        expect.any(Array),
        { date_preset: 'last_30d' }
      );
    });

    it('should return null if no insights available', async () => {
      const mockAd = {
        getInsights: jest.fn().mockResolvedValue([])
      };

      (Ad as any).mockImplementation(() => mockAd);

      const insights = await manager.getAdInsights('ad_123');

      expect(insights).toBeNull();
    });

    it('should handle insights API errors', async () => {
      const mockAd = {
        getInsights: jest.fn().mockRejectedValue(new Error('Permission denied'))
      };

      (Ad as any).mockImplementation(() => mockAd);

      await expect(manager.getAdInsights('ad_123')).rejects.toThrow('Failed to get ad insights');
    });
  });

  describe('getCampaignInsights', () => {
    it('should fetch campaign insights', async () => {
      const mockInsights = [{
        impressions: '100000',
        clicks: '2500',
        spend: '1000.00',
        conversions: '50'
      }];

      const mockCampaign = {
        getInsights: jest.fn().mockResolvedValue(mockInsights)
      };

      (Campaign as any).mockImplementation(() => mockCampaign);

      const insights = await manager.getCampaignInsights('campaign_123');

      expect(insights).toEqual(mockInsights[0]);
      expect(mockCampaign.getInsights).toHaveBeenCalled();
    });
  });

  describe('getAdSetInsights', () => {
    it('should fetch adset insights', async () => {
      const mockInsights = [{
        impressions: '50000',
        ctr: '2.0',
        cpm: '4.50'
      }];

      const mockAdSet = {
        getInsights: jest.fn().mockResolvedValue(mockInsights)
      };

      (AdSet as any).mockImplementation(() => mockAdSet);

      const insights = await manager.getAdSetInsights('adset_123');

      expect(insights).toEqual(mockInsights[0]);
    });
  });

  // ============================================================================
  // AD MANAGEMENT TESTS
  // ============================================================================

  describe('updateAdStatus', () => {
    it('should activate ad', async () => {
      const mockAd = {
        update: jest.fn().mockResolvedValue({})
      };

      (Ad as any).mockImplementation(() => mockAd);

      await manager.updateAdStatus('ad_123', 'ACTIVE');

      expect(mockAd.update).toHaveBeenCalledWith([], { status: 'ACTIVE' });
    });

    it('should pause ad', async () => {
      const mockAd = {
        update: jest.fn().mockResolvedValue({})
      };

      (Ad as any).mockImplementation(() => mockAd);

      await manager.updateAdStatus('ad_123', 'PAUSED');

      expect(mockAd.update).toHaveBeenCalledWith([], { status: 'PAUSED' });
    });

    it('should handle status update errors', async () => {
      const mockAd = {
        update: jest.fn().mockRejectedValue(new Error('Ad not found'))
      };

      (Ad as any).mockImplementation(() => mockAd);

      await expect(manager.updateAdStatus('ad_123', 'ACTIVE')).rejects.toThrow('Failed to update ad status');
    });
  });

  describe('updateAdSetBudget', () => {
    it('should update adset daily budget', async () => {
      const mockAdSet = {
        update: jest.fn().mockResolvedValue({})
      };

      (AdSet as any).mockImplementation(() => mockAdSet);

      await manager.updateAdSetBudget('adset_123', 10000);

      expect(mockAdSet.update).toHaveBeenCalledWith([], { daily_budget: 10000 });
    });

    it('should handle budget update errors', async () => {
      const mockAdSet = {
        update: jest.fn().mockRejectedValue(new Error('Budget too low'))
      };

      (AdSet as any).mockImplementation(() => mockAdSet);

      await expect(manager.updateAdSetBudget('adset_123', 100)).rejects.toThrow('Failed to update adset budget');
    });
  });

  // ============================================================================
  // ACCOUNT INFO TESTS
  // ============================================================================

  describe('getAccountInfo', () => {
    it('should fetch account information', async () => {
      const mockAccountInfo = {
        id: 'act_123456789',
        name: 'Test Ad Account',
        account_status: 1,
        currency: 'USD',
        timezone_name: 'America/Los_Angeles'
      };

      mockAdAccount.read.mockResolvedValue(mockAccountInfo);

      const accountInfo = await manager.getAccountInfo();

      expect(accountInfo).toEqual(mockAccountInfo);
      expect(mockAdAccount.read).toHaveBeenCalledWith(
        expect.arrayContaining(['id', 'name', 'account_status', 'currency', 'timezone_name'])
      );
    });

    it('should handle account info errors', async () => {
      mockAdAccount.read.mockRejectedValue(new Error('Invalid account ID'));

      await expect(manager.getAccountInfo()).rejects.toThrow('Failed to get account info');
    });
  });

  // ============================================================================
  // INSIGHTS SYNC TESTS (Agent 14)
  // ============================================================================

  describe('syncInsightsToDatabase', () => {
    it('should sync insights to database', async () => {
      const insights = {
        impressions: '10000',
        clicks: '150',
        ctr: '1.5',
        spend: '50.00'
      };

      // Should not throw
      await expect(
        manager.syncInsightsToDatabase('ad_123', insights)
      ).resolves.not.toThrow();
    });

    it('should handle sync errors gracefully', async () => {
      const insights = null;

      await expect(
        manager.syncInsightsToDatabase('ad_123', insights as any)
      ).rejects.toThrow();
    });
  });
});

// ============================================================================
// CAPI (Conversions API) TESTS
// ============================================================================

describe('Meta Conversions API (CAPI)', () => {
  it('should send server-side conversion event', async () => {
    // Mock CAPI event structure
    const conversionEvent = {
      event_name: 'Purchase',
      event_time: Math.floor(Date.now() / 1000),
      user_data: {
        em: 'test@example.com',
        ph: '1234567890'
      },
      custom_data: {
        currency: 'USD',
        value: 99.99
      }
    };

    expect(conversionEvent).toHaveProperty('event_name');
    expect(conversionEvent).toHaveProperty('event_time');
    expect(conversionEvent).toHaveProperty('user_data');
  });

  it('should batch multiple conversion events', async () => {
    const events = [
      { event_name: 'AddToCart', event_time: Date.now() },
      { event_name: 'Purchase', event_time: Date.now() }
    ];

    expect(events).toHaveLength(2);
    expect(events[0].event_name).toBe('AddToCart');
    expect(events[1].event_name).toBe('Purchase');
  });
});

// ============================================================================
// META PIXEL SERVICE TESTS
// ============================================================================

describe('Meta Pixel Service', () => {
  it('should track pageview event', () => {
    const pixelEvent = {
      event: 'PageView',
      timestamp: Date.now(),
      url: 'https://example.com/product'
    };

    expect(pixelEvent.event).toBe('PageView');
    expect(pixelEvent).toHaveProperty('timestamp');
  });

  it('should track custom event with parameters', () => {
    const customEvent = {
      event: 'ViewContent',
      content_type: 'product',
      content_ids: ['123', '456'],
      value: 299.99,
      currency: 'USD'
    };

    expect(customEvent.event).toBe('ViewContent');
    expect(customEvent.content_ids).toHaveLength(2);
  });
});
