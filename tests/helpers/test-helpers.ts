/**
 * Test Helper Functions
 * Agent 29 of 30
 */

import axios, { AxiosInstance } from 'axios';

/**
 * Create a test API client
 */
export function createTestApiClient(baseURL: string, apiKey?: string): AxiosInstance {
  const headers: any = {
    'Content-Type': 'application/json'
  };

  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  return axios.create({
    baseURL,
    timeout: 10000,
    headers,
    validateStatus: () => true // Don't throw on any status
  });
}

/**
 * Wait for a condition to be true
 */
export async function waitForCondition(
  condition: () => boolean | Promise<boolean>,
  timeout: number = 5000,
  interval: number = 100
): Promise<void> {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    const result = await condition();
    if (result) {
      return;
    }
    await new Promise(resolve => setTimeout(resolve, interval));
  }

  throw new Error(`Condition not met within ${timeout}ms`);
}

/**
 * Retry an operation
 */
export async function retry<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error | undefined;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError || new Error('Retry failed');
}

/**
 * Generate random test data
 */
export function generateRandomString(length: number = 10): string {
  return Math.random().toString(36).substring(2, 2 + length);
}

export function generateRandomEmail(): string {
  return `test-${generateRandomString()}@example.com`;
}

export function generateRandomCampaignName(): string {
  return `Test Campaign ${generateRandomString()}`;
}

/**
 * Mock delay
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Create mock campaign data
 */
export function createMockCampaign(overrides: any = {}) {
  return {
    name: generateRandomCampaignName(),
    objective: 'OUTCOME_ENGAGEMENT',
    status: 'PAUSED',
    special_ad_categories: [],
    ...overrides
  };
}

/**
 * Create mock adset data
 */
export function createMockAdSet(campaignId: string, overrides: any = {}) {
  return {
    name: `Test AdSet ${generateRandomString()}`,
    campaign_id: campaignId,
    bid_amount: 500,
    daily_budget: 5000,
    targeting: {
      geo_locations: { countries: ['US'] },
      age_min: 25,
      age_max: 54
    },
    ...overrides
  };
}

/**
 * Validate API response structure
 */
export function validateApiResponse(response: any, expectedFields: string[]): void {
  for (const field of expectedFields) {
    if (!(field in response.data)) {
      throw new Error(`Missing expected field: ${field}`);
    }
  }
}
