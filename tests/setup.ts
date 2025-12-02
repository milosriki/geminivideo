/**
 * Jest Global Setup
 * Common test utilities and configuration
 * Agent 29 of 30
 */

import { jest } from '@jest/globals';

// Extend Jest timeout for integration tests
jest.setTimeout(30000);

// Mock environment variables
process.env.NODE_ENV = 'test';
process.env.DATABASE_URL = process.env.TEST_DATABASE_URL || 'postgresql://test:test@localhost:5432/test_db';
process.env.REDIS_URL = process.env.TEST_REDIS_URL || 'redis://localhost:6379';

// Suppress console logs during tests (optional)
if (process.env.SILENT_TESTS === 'true') {
  global.console = {
    ...console,
    log: jest.fn(),
    debug: jest.fn(),
    info: jest.fn(),
    warn: jest.fn(),
  };
}

// Global test utilities
declare global {
  var testUtils: {
    waitFor: (ms: number) => Promise<void>;
    mockResponse: (data: any, status?: number) => any;
  };
}

global.testUtils = {
  waitFor: (ms: number) => new Promise(resolve => setTimeout(resolve, ms)),

  mockResponse: (data: any, status: number = 200) => ({
    status,
    data,
    headers: {},
    config: {},
    statusText: 'OK'
  })
};
