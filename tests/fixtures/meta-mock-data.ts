/**
 * Mock Data for Meta API Tests
 * Agent 29 of 30
 */

export const mockCampaign = {
  id: '120202345678901234',
  name: 'Test Campaign',
  objective: 'OUTCOME_ENGAGEMENT',
  status: 'PAUSED',
  created_time: '2024-01-01T00:00:00Z',
  updated_time: '2024-01-01T00:00:00Z'
};

export const mockAdSet = {
  id: '120203456789012345',
  name: 'Test AdSet',
  campaign_id: '120202345678901234',
  status: 'PAUSED',
  daily_budget: 5000,
  bid_amount: 500,
  targeting: {
    geo_locations: { countries: ['US'] },
    age_min: 25,
    age_max: 54
  }
};

export const mockAd = {
  id: '120205678901234567',
  name: 'Test Ad',
  adset_id: '120203456789012345',
  status: 'PAUSED',
  creative: {
    id: '120204567890123456'
  }
};

export const mockVideo = {
  id: '1234567890123456',
  title: 'Test Video',
  source: '/path/to/video.mp4',
  length: 15.0,
  created_time: '2024-01-01T00:00:00Z'
};

export const mockCreative = {
  id: '120204567890123456',
  name: 'Test Creative',
  object_story_spec: {
    page_id: '987654321',
    video_data: {
      video_id: '1234567890123456',
      title: 'Amazing Product',
      message: 'Check it out!'
    }
  }
};

export const mockInsights = {
  impressions: '10000',
  clicks: '150',
  spend: '50.00',
  ctr: '1.5',
  cpm: '5.00',
  cpp: '0.33',
  reach: '8500',
  frequency: '1.18',
  conversions: '25',
  cost_per_conversion: '2.00'
};

export const mockAccountInfo = {
  id: 'act_123456789',
  name: 'Test Ad Account',
  account_status: 1,
  currency: 'USD',
  timezone_name: 'America/Los_Angeles'
};
