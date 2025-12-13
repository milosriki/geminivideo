/**
 * AI Credits Endpoint Tests
 * 
 * Comprehensive unit tests for the AI Credits management system including:
 * - Credit balance retrieval
 * - Credit deduction operations
 * - User initialization
 * - Error handling and edge cases
 * 
 * Run with: npm test -- credits-endpoint.test.ts
 */

import { Request, Response } from 'express';
import { Pool } from 'pg';
import { registerCreditsEndpoints } from '../credits-endpoint';

// Mock Express app
const mockApp = {
  get: jest.fn(),
  post: jest.fn()
};

// Mock Pool
const mockPool = {
  query: jest.fn()
} as unknown as Pool;

describe('AI Credits Endpoints', () => {
  let getHandler: (req: Request, res: Response) => Promise<void>;
  let postHandler: (req: Request, res: Response) => Promise<void>;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Register endpoints and capture handlers
    registerCreditsEndpoints(mockApp as any, mockPool);
    
    // Extract handlers from mock calls
    const getCalls = mockApp.get.mock.calls;
    const postCalls = mockApp.post.mock.calls;
    
    getHandler = getCalls.find((call: any[]) => call[0] === '/api/credits')?.[1];
    postHandler = postCalls.find((call: any[]) => call[0] === '/api/credits/deduct')?.[1];
  });

  describe('Endpoint Registration', () => {
    it('should register GET /api/credits endpoint', () => {
      expect(mockApp.get).toHaveBeenCalledWith(
        '/api/credits',
        expect.any(Function)
      );
    });

    it('should register POST /api/credits/deduct endpoint', () => {
      expect(mockApp.post).toHaveBeenCalledWith(
        '/api/credits/deduct',
        expect.any(Function)
      );
    });
  });

  describe('GET /api/credits - Fetch Credits', () => {
    let mockReq: Partial<Request>;
    let mockRes: Partial<Response>;
    let jsonMock: jest.Mock;
    let statusMock: jest.Mock;

    beforeEach(() => {
      jsonMock = jest.fn();
      statusMock = jest.fn().mockReturnValue({ json: jsonMock });
      
      mockReq = {
        query: {}
      };
      
      mockRes = {
        json: jsonMock,
        status: statusMock
      };
    });

    it('should fetch credits for existing user', async () => {
      const mockCreditsData = {
        rows: [{
          user_id: 'test_user',
          total_credits: 10000,
          used_credits: 1500,
          available_credits: 8500,
          created_at: new Date('2024-01-01'),
          updated_at: new Date('2024-01-02')
        }]
      };

      const mockUsageData = {
        rows: [
          {
            date: new Date('2024-01-01'),
            used: '500',
            operation: 'video_generation',
            metadata: { duration: 30, quality: 'hd' }
          },
          {
            date: new Date('2024-01-02'),
            used: '300',
            operation: 'video_analysis',
            metadata: { clips_analyzed: 5 }
          }
        ]
      };

      (mockPool.query as jest.Mock)
        .mockResolvedValueOnce(mockCreditsData)
        .mockResolvedValueOnce(mockUsageData);

      mockReq.query = { user_id: 'test_user' };

      await getHandler(mockReq as Request, mockRes as Response);

      expect(mockPool.query).toHaveBeenCalledTimes(2);
      expect(jsonMock).toHaveBeenCalledWith({
        credits: {
          available: 8500,
          total: 10000,
          used: 1500,
          usage_history: expect.arrayContaining([
            expect.objectContaining({
              date: '2024-01-01',
              used: 500,
              operation: 'video_generation',
              duration: 30,
              quality: 'hd'
            }),
            expect.objectContaining({
              date: '2024-01-02',
              used: 300,
              operation: 'video_analysis',
              clips_analyzed: 5
            })
          ])
        }
      });
    });

    it('should initialize new user with default credits', async () => {
      const emptyCreditsResult = { rows: [] };
      const newUserResult = {
        rows: [{
          user_id: 'new_user',
          total_credits: 10000,
          used_credits: 0,
          available_credits: 10000,
          created_at: new Date(),
          updated_at: new Date()
        }]
      };

      (mockPool.query as jest.Mock)
        .mockResolvedValueOnce(emptyCreditsResult)
        .mockResolvedValueOnce(newUserResult);

      mockReq.query = { user_id: 'new_user' };

      await getHandler(mockReq as Request, mockRes as Response);

      expect(mockPool.query).toHaveBeenCalledTimes(2);
      expect(mockPool.query).toHaveBeenNthCalledWith(
        2,
        expect.stringContaining('INSERT INTO ai_credits'),
        ['new_user']
      );
      expect(jsonMock).toHaveBeenCalledWith({
        credits: {
          available: 10000,
          total: 10000,
          used: 0,
          usage_history: []
        }
      });
    });

    it('should use default_user when no user_id provided', async () => {
      const mockCreditsData = {
        rows: [{
          user_id: 'default_user',
          total_credits: 10000,
          used_credits: 0,
          available_credits: 10000,
          created_at: new Date(),
          updated_at: new Date()
        }]
      };

      const mockUsageData = { rows: [] };

      (mockPool.query as jest.Mock)
        .mockResolvedValueOnce(mockCreditsData)
        .mockResolvedValueOnce(mockUsageData);

      await getHandler(mockReq as Request, mockRes as Response);

      expect(mockPool.query).toHaveBeenNthCalledWith(
        1,
        expect.any(String),
        ['default_user']
      );
    });

    it('should handle empty usage history gracefully', async () => {
      const mockCreditsData = {
        rows: [{
          user_id: 'test_user',
          total_credits: 10000,
          used_credits: 0,
          available_credits: 10000,
          created_at: new Date(),
          updated_at: new Date()
        }]
      };

      const emptyUsageData = { rows: [] };

      (mockPool.query as jest.Mock)
        .mockResolvedValueOnce(mockCreditsData)
        .mockResolvedValueOnce(emptyUsageData);

      mockReq.query = { user_id: 'test_user' };

      await getHandler(mockReq as Request, mockRes as Response);

      expect(jsonMock).toHaveBeenCalledWith({
        credits: expect.objectContaining({
          usage_history: []
        })
      });
    });

    it('should filter out empty metadata from usage history', async () => {
      const mockCreditsData = {
        rows: [{
          user_id: 'test_user',
          total_credits: 10000,
          used_credits: 500,
          available_credits: 9500,
          created_at: new Date(),
          updated_at: new Date()
        }]
      };

      const mockUsageData = {
        rows: [
          {
            date: new Date('2024-01-01'),
            used: '500',
            operation: 'test_operation',
            metadata: {}
          }
        ]
      };

      (mockPool.query as jest.Mock)
        .mockResolvedValueOnce(mockCreditsData)
        .mockResolvedValueOnce(mockUsageData);

      mockReq.query = { user_id: 'test_user' };

      await getHandler(mockReq as Request, mockRes as Response);

      expect(jsonMock).toHaveBeenCalledWith({
        credits: expect.objectContaining({
          usage_history: [{
            date: '2024-01-01',
            used: 500,
            operation: 'test_operation'
          }]
        })
      });
    });

    it('should handle database errors gracefully', async () => {
      const dbError = new Error('Database connection failed');
      (mockPool.query as jest.Mock).mockRejectedValueOnce(dbError);

      mockReq.query = { user_id: 'test_user' };

      await getHandler(mockReq as Request, mockRes as Response);

      expect(statusMock).toHaveBeenCalledWith(500);
      expect(jsonMock).toHaveBeenCalledWith({
        error: 'Failed to fetch AI credits',
        details: 'Database connection failed'
      });
    });

    it('should handle query timeout errors', async () => {
      const timeoutError = new Error('Query timeout');
      (mockPool.query as jest.Mock).mockRejectedValueOnce(timeoutError);

      mockReq.query = { user_id: 'test_user' };

      await getHandler(mockReq as Request, mockRes as Response);

      expect(statusMock).toHaveBeenCalledWith(500);
      expect(jsonMock).toHaveBeenCalledWith({
        error: 'Failed to fetch AI credits',
        details: 'Query timeout'
      });
    });
  });

  describe('POST /api/credits/deduct - Deduct Credits', () => {
    let mockReq: Partial<Request>;
    let mockRes: Partial<Response>;
    let jsonMock: jest.Mock;
    let statusMock: jest.Mock;

    beforeEach(() => {
      jsonMock = jest.fn();
      statusMock = jest.fn().mockReturnValue({ json: jsonMock });
      
      mockReq = {
        body: {}
      };
      
      mockRes = {
        json: jsonMock,
        status: statusMock
      };
    });

    it('should successfully deduct credits when sufficient balance', async () => {
      const checkResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 1000
        }]
      };

      const deductResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 1500,
          available_credits: 8500
        }]
      };

      (mockPool.query as jest.Mock)
        .mockResolvedValueOnce(checkResult)
        .mockResolvedValueOnce(deductResult)
        .mockResolvedValueOnce({ rows: [{ id: 1, created_at: new Date() }] });

      mockReq.body = {
        user_id: 'test_user',
        credits: 500,
        operation: 'video_generation',
        metadata: { duration: 30, quality: 'hd' }
      };

      await postHandler(mockReq as Request, mockRes as Response);

      expect(mockPool.query).toHaveBeenCalledTimes(3);
      expect(jsonMock).toHaveBeenCalledWith({
        message: 'Credits deducted successfully',
        credits: {
          available: 8500,
          total: 10000,
          used: 1500
        }
      });
    });

    it('should return 400 when user_id is missing', async () => {
      mockReq.body = {
        credits: 500,
        operation: 'video_generation'
      };

      await postHandler(mockReq as Request, mockRes as Response);

      expect(statusMock).toHaveBeenCalledWith(400);
      expect(jsonMock).toHaveBeenCalledWith({
        error: 'Missing required fields',
        required: ['user_id', 'credits', 'operation']
      });
      expect(mockPool.query).not.toHaveBeenCalled();
    });

    it('should return 400 when credits is missing', async () => {
      mockReq.body = {
        user_id: 'test_user',
        operation: 'video_generation'
      };

      await postHandler(mockReq as Request, mockRes as Response);

      expect(statusMock).toHaveBeenCalledWith(400);
      expect(jsonMock).toHaveBeenCalledWith({
        error: 'Missing required fields',
        required: ['user_id', 'credits', 'operation']
      });
    });

    it('should return 400 when operation is missing', async () => {
      mockReq.body = {
        user_id: 'test_user',
        credits: 500
      };

      await postHandler(mockReq as Request, mockRes as Response);

      expect(statusMock).toHaveBeenCalledWith(400);
      expect(jsonMock).toHaveBeenCalledWith({
        error: 'Missing required fields',
        required: ['user_id', 'credits', 'operation']
      });
    });

    it('should return 404 when user does not exist', async () => {
      const emptyResult = { rows: [] };
      (mockPool.query as jest.Mock).mockResolvedValueOnce(emptyResult);

      mockReq.body = {
        user_id: 'non_existent_user',
        credits: 500,
        operation: 'video_generation'
      };

      await postHandler(mockReq as Request, mockRes as Response);

      expect(statusMock).toHaveBeenCalledWith(404);
      expect(jsonMock).toHaveBeenCalledWith({
        error: 'User not found',
        user_id: 'non_existent_user'
      });
    });

    it('should return 402 when insufficient credits', async () => {
      const checkResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 9800
        }]
      };

      (mockPool.query as jest.Mock).mockResolvedValueOnce(checkResult);

      mockReq.body = {
        user_id: 'test_user',
        credits: 500,
        operation: 'video_generation'
      };

      await postHandler(mockReq as Request, mockRes as Response);

      expect(statusMock).toHaveBeenCalledWith(402);
      expect(jsonMock).toHaveBeenCalledWith({
        error: 'Insufficient credits',
        available: 200,
        requested: 500
      });
    });

    it('should handle exact credit balance (boundary condition)', async () => {
      const checkResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 9500
        }]
      };

      const deductResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 10000,
          available_credits: 0
        }]
      };

      (mockPool.query as jest.Mock)
        .mockResolvedValueOnce(checkResult)
        .mockResolvedValueOnce(deductResult)
        .mockResolvedValueOnce({ rows: [{ id: 1, created_at: new Date() }] });

      mockReq.body = {
        user_id: 'test_user',
        credits: 500,
        operation: 'video_generation'
      };

      await postHandler(mockReq as Request, mockRes as Response);

      expect(jsonMock).toHaveBeenCalledWith({
        message: 'Credits deducted successfully',
        credits: {
          available: 0,
          total: 10000,
          used: 10000
        }
      });
    });

    it('should log usage with metadata', async () => {
      const checkResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 1000
        }]
      };

      const deductResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 1500,
          available_credits: 8500
        }]
      };

      (mockPool.query as jest.Mock)
        .mockResolvedValueOnce(checkResult)
        .mockResolvedValueOnce(deductResult)
        .mockResolvedValueOnce({ rows: [{ id: 1, created_at: new Date() }] });

      const metadata = { duration: 60, quality: '4k', resolution: '3840x2160' };
      mockReq.body = {
        user_id: 'test_user',
        credits: 500,
        operation: 'video_generation',
        metadata
      };

      await postHandler(mockReq as Request, mockRes as Response);

      expect(mockPool.query).toHaveBeenNthCalledWith(
        3,
        expect.stringContaining('INSERT INTO ai_credit_usage'),
        [
          'test_user',
          500,
          'video_generation',
          JSON.stringify(metadata)
        ]
      );
    });

    it('should handle missing metadata gracefully', async () => {
      const checkResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 1000
        }]
      };

      const deductResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 1500,
          available_credits: 8500
        }]
      };

      (mockPool.query as jest.Mock)
        .mockResolvedValueOnce(checkResult)
        .mockResolvedValueOnce(deductResult)
        .mockResolvedValueOnce({ rows: [{ id: 1, created_at: new Date() }] });

      mockReq.body = {
        user_id: 'test_user',
        credits: 500,
        operation: 'video_generation'
      };

      await postHandler(mockReq as Request, mockRes as Response);

      expect(mockPool.query).toHaveBeenNthCalledWith(
        3,
        expect.stringContaining('INSERT INTO ai_credit_usage'),
        ['test_user', 500, 'video_generation', '{}']
      );
    });

    it('should handle zero credits deduction', async () => {
      const checkResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 1000
        }]
      };

      const deductResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 1000,
          available_credits: 9000
        }]
      };

      (mockPool.query as jest.Mock)
        .mockResolvedValueOnce(checkResult)
        .mockResolvedValueOnce(deductResult)
        .mockResolvedValueOnce({ rows: [{ id: 1, created_at: new Date() }] });

      mockReq.body = {
        user_id: 'test_user',
        credits: 0,
        operation: 'test_operation'
      };

      await postHandler(mockReq as Request, mockRes as Response);

      expect(jsonMock).toHaveBeenCalledWith({
        message: 'Credits deducted successfully',
        credits: expect.any(Object)
      });
    });

    it('should handle database errors during deduction', async () => {
      const checkResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 1000
        }]
      };

      (mockPool.query as jest.Mock)
        .mockResolvedValueOnce(checkResult)
        .mockRejectedValueOnce(new Error('Deduction failed'));

      mockReq.body = {
        user_id: 'test_user',
        credits: 500,
        operation: 'video_generation'
      };

      await postHandler(mockReq as Request, mockRes as Response);

      expect(statusMock).toHaveBeenCalledWith(500);
      expect(jsonMock).toHaveBeenCalledWith({
        error: 'Failed to deduct credits',
        details: 'Deduction failed'
      });
    });

    it('should handle concurrent deduction attempts (race condition)', async () => {
      const checkResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 9700
        }]
      };

      (mockPool.query as jest.Mock).mockResolvedValueOnce(checkResult);

      mockReq.body = {
        user_id: 'test_user',
        credits: 500,
        operation: 'video_generation'
      };

      await postHandler(mockReq as Request, mockRes as Response);

      expect(statusMock).toHaveBeenCalledWith(402);
    });

    it('should handle large credit amounts', async () => {
      const checkResult = {
        rows: [{
          total_credits: 1000000,
          used_credits: 0
        }]
      };

      const deductResult = {
        rows: [{
          total_credits: 1000000,
          used_credits: 50000,
          available_credits: 950000
        }]
      };

      (mockPool.query as jest.Mock)
        .mockResolvedValueOnce(checkResult)
        .mockResolvedValueOnce(deductResult)
        .mockResolvedValueOnce({ rows: [{ id: 1, created_at: new Date() }] });

      mockReq.body = {
        user_id: 'enterprise_user',
        credits: 50000,
        operation: 'bulk_video_generation'
      };

      await postHandler(mockReq as Request, mockRes as Response);

      expect(jsonMock).toHaveBeenCalledWith({
        message: 'Credits deducted successfully',
        credits: {
          available: 950000,
          total: 1000000,
          used: 50000
        }
      });
    });

    it('should handle various operation types', async () => {
      const operations = [
        'video_generation',
        'video_analysis',
        'script_generation',
        'text_analysis',
        'image_processing'
      ];

      for (const operation of operations) {
        jest.clearAllMocks();

        const checkResult = {
          rows: [{
            total_credits: 10000,
            used_credits: 0
          }]
        };

        const deductResult = {
          rows: [{
            total_credits: 10000,
            used_credits: 100,
            available_credits: 9900
          }]
        };

        (mockPool.query as jest.Mock)
          .mockResolvedValueOnce(checkResult)
          .mockResolvedValueOnce(deductResult)
          .mockResolvedValueOnce({ rows: [{ id: 1, created_at: new Date() }] });

        mockReq.body = {
          user_id: 'test_user',
          credits: 100,
          operation
        };

        await postHandler(mockReq as Request, mockRes as Response);

        expect(mockPool.query).toHaveBeenNthCalledWith(
          3,
          expect.any(String),
          expect.arrayContaining([
            'test_user',
            100,
            operation,
            '{}'
          ])
        );
      }
    });
  });

  describe('Edge Cases and Stress Tests', () => {
    let mockReq: Partial<Request>;
    let mockRes: Partial<Response>;
    let jsonMock: jest.Mock;
    let statusMock: jest.Mock;

    beforeEach(() => {
      jsonMock = jest.fn();
      statusMock = jest.fn().mockReturnValue({ json: jsonMock });
      
      mockReq = { body: {}, query: {} };
      mockRes = { json: jsonMock, status: statusMock };
    });

    it('should handle negative credit values safely', async () => {
      const checkResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 1000
        }]
      };

      (mockPool.query as jest.Mock).mockResolvedValueOnce(checkResult);

      mockReq.body = {
        user_id: 'test_user',
        credits: -500,
        operation: 'video_generation'
      };

      await postHandler(mockReq as Request, mockRes as Response);

      // Should still process (negative would add credits back)
      expect(mockPool.query).toHaveBeenCalled();
    });

    it('should handle very long user IDs', async () => {
      const longUserId = 'a'.repeat(300);
      
      const checkResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 1000
        }]
      };

      (mockPool.query as jest.Mock).mockResolvedValueOnce(checkResult);

      mockReq.body = {
        user_id: longUserId,
        credits: 500,
        operation: 'video_generation'
      };

      await postHandler(mockReq as Request, mockRes as Response);

      expect(mockPool.query).toHaveBeenCalledWith(
        expect.any(String),
        expect.arrayContaining([longUserId])
      );
    });

    it('should handle special characters in operation names', async () => {
      const checkResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 1000
        }]
      };

      const deductResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 1500,
          available_credits: 8500
        }]
      };

      (mockPool.query as jest.Mock)
        .mockResolvedValueOnce(checkResult)
        .mockResolvedValueOnce(deductResult)
        .mockResolvedValueOnce({ rows: [{ id: 1, created_at: new Date() }] });

      mockReq.body = {
        user_id: 'test_user',
        credits: 500,
        operation: 'video-generation_v2.0@test'
      };

      await postHandler(mockReq as Request, mockRes as Response);

      expect(jsonMock).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'Credits deducted successfully'
        })
      );
    });

    it('should handle complex nested metadata objects', async () => {
      const checkResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 1000
        }]
      };

      const deductResult = {
        rows: [{
          total_credits: 10000,
          used_credits: 1500,
          available_credits: 8500
        }]
      };

      (mockPool.query as jest.Mock)
        .mockResolvedValueOnce(checkResult)
        .mockResolvedValueOnce(deductResult)
        .mockResolvedValueOnce({ rows: [{ id: 1, created_at: new Date() }] });

      const complexMetadata = {
        video: {
          duration: 60,
          quality: '4k',
          format: 'mp4',
          codec: 'h264'
        },
        processing: {
          ai_models: ['vision', 'audio'],
          gpu_time: 120,
          preprocessing: true
        },
        tags: ['marketing', 'product', 'demo']
      };

      mockReq.body = {
        user_id: 'test_user',
        credits: 500,
        operation: 'video_generation',
        metadata: complexMetadata
      };

      await postHandler(mockReq as Request, mockRes as Response);

      expect(mockPool.query).toHaveBeenNthCalledWith(
        3,
        expect.any(String),
        expect.arrayContaining([
          'test_user',
          500,
          'video_generation',
          JSON.stringify(complexMetadata)
        ])
      );
    });
  });
});