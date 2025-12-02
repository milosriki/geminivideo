/**
 * Mock Facebook SDK for Testing
 * Agent 29 of 30
 */

export class MockFacebookAdsApi {
  static init(accessToken: string) {
    return new MockFacebookAdsApi();
  }
}

export class MockAdAccount {
  private id: string;

  constructor(id: string) {
    this.id = id;
  }

  async createCampaign(fields: any[], params: any) {
    return {
      id: '120202345678901234',
      ...params
    };
  }

  async createAdSet(fields: any[], params: any) {
    return {
      id: '120203456789012345',
      ...params
    };
  }

  async createAdVideo(fields: any[], params: any) {
    return {
      id: '1234567890123456',
      source: params.source
    };
  }

  async createAdCreative(fields: any[], params: any) {
    return {
      id: '120204567890123456',
      ...params
    };
  }

  async createAd(fields: any[], params: any) {
    return {
      id: '120205678901234567',
      ...params
    };
  }

  async read(fields: string[]) {
    return {
      id: this.id,
      name: 'Test Ad Account',
      account_status: 1,
      currency: 'USD',
      timezone_name: 'America/Los_Angeles'
    };
  }
}

export class MockCampaign {
  private id: string;

  constructor(id: string) {
    this.id = id;
  }

  async getInsights(fields: string[], params: any) {
    return [{
      impressions: '100000',
      clicks: '2500',
      spend: '1000.00',
      ctr: '2.5',
      reach: '85000',
      conversions: '50'
    }];
  }
}

export class MockAdSet {
  private id: string;

  constructor(id: string) {
    this.id = id;
  }

  async getInsights(fields: string[], params: any) {
    return [{
      impressions: '50000',
      clicks: '1000',
      spend: '500.00',
      ctr: '2.0',
      cpm: '10.00'
    }];
  }

  async update(fields: any[], params: any) {
    return { success: true };
  }
}

export class MockAd {
  private id: string;

  constructor(id: string) {
    this.id = id;
  }

  async getInsights(fields: string[], params: any) {
    return [{
      impressions: '10000',
      clicks: '150',
      spend: '50.00',
      ctr: '1.5',
      cpm: '5.00'
    }];
  }

  async update(fields: any[], params: any) {
    return { success: true };
  }
}
