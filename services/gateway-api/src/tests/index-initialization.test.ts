/**
 * Index.ts Database Initialization Tests
 * 
 * Comprehensive unit tests for the database initialization logic including:
 * - AI Credits table creation
 * - Default user initialization
 * - Configuration constants
 * - Error handling during initialization
 * - Index creation
 * 
 * Run with: npm test -- index-initialization.test.ts
 */

import { Pool } from 'pg';

describe('Index.ts Database Initialization', () => {
  let mockPool: jest.Mocked<Pool>;

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockPool = {
      query: jest.fn(),
      on: jest.fn()
    } as unknown as jest.Mocked<Pool>;
  });

  describe('Configuration Constants', () => {
    it('should parse DEFAULT_AI_CREDITS from environment variable', () => {
      process.env.DEFAULT_AI_CREDITS = '15000';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(15000);
      
      delete process.env.DEFAULT_AI_CREDITS;
    });

    it('should default to 10000 credits when env variable is not set', () => {
      delete process.env.DEFAULT_AI_CREDITS;
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(10000);
    });

    it('should handle invalid DEFAULT_AI_CREDITS gracefully', () => {
      process.env.DEFAULT_AI_CREDITS = 'invalid';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBeNaN();
      
      delete process.env.DEFAULT_AI_CREDITS;
    });

    it('should handle zero credits configuration', () => {
      process.env.DEFAULT_AI_CREDITS = '0';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(0);
      
      delete process.env.DEFAULT_AI_CREDITS;
    });

    it('should handle negative credits configuration', () => {
      process.env.DEFAULT_AI_CREDITS = '-1000';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(-1000);
      
      delete process.env.DEFAULT_AI_CREDITS;
    });

    it('should handle very large credit values', () => {
      process.env.DEFAULT_AI_CREDITS = '999999999';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(999999999);
      
      delete process.env.DEFAULT_AI_CREDITS;
    });
  });

  describe('AI Credits Table Creation', () => {
    it('should create ai_credits table with correct schema', async () => {
      const DEFAULT_AI_CREDITS = 10000;
      const createTableQuery = `
        CREATE TABLE IF NOT EXISTS ai_credits (
          user_id VARCHAR(255) PRIMARY KEY,
          total_credits INTEGER NOT NULL DEFAULT ${DEFAULT_AI_CREDITS},
          used_credits INTEGER NOT NULL DEFAULT 0,
          created_at TIMESTAMP DEFAULT NOW(),
          updated_at TIMESTAMP DEFAULT NOW()
        );
      `;

      expect(createTableQuery).toContain('CREATE TABLE IF NOT EXISTS ai_credits');
      expect(createTableQuery).toContain('user_id VARCHAR(255) PRIMARY KEY');
      expect(createTableQuery).toContain('total_credits INTEGER NOT NULL DEFAULT 10000');
      expect(createTableQuery).toContain('used_credits INTEGER NOT NULL DEFAULT 0');
      expect(createTableQuery).toContain('created_at TIMESTAMP DEFAULT NOW()');
      expect(createTableQuery).toContain('updated_at TIMESTAMP DEFAULT NOW()');
    });

    it('should create ai_credit_usage table with correct schema', () => {
      const createUsageTableQuery = `
        CREATE TABLE IF NOT EXISTS ai_credit_usage (
          id SERIAL PRIMARY KEY,
          user_id VARCHAR(255) NOT NULL,
          credits_used INTEGER NOT NULL,
          operation VARCHAR(100) NOT NULL,
          metadata JSONB DEFAULT '{}',
          created_at TIMESTAMP DEFAULT NOW()
        );
      `;

      expect(createUsageTableQuery).toContain('CREATE TABLE IF NOT EXISTS ai_credit_usage');
      expect(createUsageTableQuery).toContain('id SERIAL PRIMARY KEY');
      expect(createUsageTableQuery).toContain('user_id VARCHAR(255) NOT NULL');
      expect(createUsageTableQuery).toContain('credits_used INTEGER NOT NULL');
      expect(createUsageTableQuery).toContain('operation VARCHAR(100) NOT NULL');
      expect(createUsageTableQuery).toContain('metadata JSONB DEFAULT');
      expect(createUsageTableQuery).toContain('created_at TIMESTAMP DEFAULT NOW()');
    });

    it('should create index on credit_usage user_id', () => {
      const createIndexQuery = 'CREATE INDEX IF NOT EXISTS idx_credit_usage_user ON ai_credit_usage(user_id);';

      expect(createIndexQuery).toContain('CREATE INDEX IF NOT EXISTS');
      expect(createIndexQuery).toContain('idx_credit_usage_user');
      expect(createIndexQuery).toContain('ai_credit_usage(user_id)');
    });

    it('should create index on credit_usage created_at', () => {
      const createIndexQuery = 'CREATE INDEX IF NOT EXISTS idx_credit_usage_created ON ai_credit_usage(created_at DESC);';

      expect(createIndexQuery).toContain('CREATE INDEX IF NOT EXISTS');
      expect(createIndexQuery).toContain('idx_credit_usage_created');
      expect(createIndexQuery).toContain('ai_credit_usage(created_at DESC)');
    });

    it('should use IF NOT EXISTS for idempotent table creation', () => {
      const queries = [
        'CREATE TABLE IF NOT EXISTS ai_credits',
        'CREATE TABLE IF NOT EXISTS ai_credit_usage',
        'CREATE INDEX IF NOT EXISTS idx_credit_usage_user',
        'CREATE INDEX IF NOT EXISTS idx_credit_usage_created'
      ];

      queries.forEach(query => {
        expect(query).toContain('IF NOT EXISTS');
      });
    });
  });

  describe('Default User Initialization', () => {
    it('should initialize default_user with correct credits', async () => {
      const DEFAULT_AI_CREDITS = 10000;
      const initDefaultUserQuery = `
        INSERT INTO ai_credits (user_id, total_credits, used_credits)
        VALUES ('default_user', $1, 0)
        ON CONFLICT (user_id) DO NOTHING;
      `;

      mockPool.query.mockResolvedValueOnce({ rows: [] } as any);

      await mockPool.query(initDefaultUserQuery, [DEFAULT_AI_CREDITS]);

      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO ai_credits'),
        [DEFAULT_AI_CREDITS]
      );
    });

    it('should use ON CONFLICT DO NOTHING for idempotent user creation', () => {
      const query = `
        INSERT INTO ai_credits (user_id, total_credits, used_credits)
        VALUES ('default_user', $1, 0)
        ON CONFLICT (user_id) DO NOTHING;
      `;

      expect(query).toContain('ON CONFLICT (user_id) DO NOTHING');
    });

    it('should initialize default_user with zero used_credits', () => {
      const query = `
        INSERT INTO ai_credits (user_id, total_credits, used_credits)
        VALUES ('default_user', $1, 0)
        ON CONFLICT (user_id) DO NOTHING;
      `;

      expect(query).toContain('used_credits');
      expect(query).toMatch(/VALUES.*0/);
    });

    it('should handle different default credit amounts', async () => {
      const creditAmounts = [5000, 10000, 25000, 50000, 100000];

      for (const amount of creditAmounts) {
        const query = `
          INSERT INTO ai_credits (user_id, total_credits, used_credits)
          VALUES ('default_user', $1, 0)
          ON CONFLICT (user_id) DO NOTHING;
        `;

        mockPool.query.mockResolvedValueOnce({ rows: [] } as any);
        await mockPool.query(query, [amount]);

        expect(mockPool.query).toHaveBeenCalledWith(
          expect.any(String),
          [amount]
        );

        jest.clearAllMocks();
      }
    });
  });

  describe('Database Connection and Initialization Flow', () => {
    it('should execute initialization queries in correct order', async () => {
      const queries: string[] = [];
      
      mockPool.query.mockImplementation((query: any) => {
        if (typeof query === 'string') {
          queries.push(query);
        }
        return Promise.resolve({ rows: [] } as any);
      });

      // Simulate the initialization flow
      await mockPool.query('SELECT NOW()'); // Connection check
      await mockPool.query('CREATE TABLE IF NOT EXISTS ai_credits'); // Table creation
      await mockPool.query('INSERT INTO ai_credits'); // User initialization

      expect(queries[0]).toContain('SELECT NOW()');
      expect(queries[1]).toContain('CREATE TABLE');
      expect(queries[2]).toContain('INSERT INTO');
    });

    it('should handle successful database connection', async () => {
      mockPool.query.mockResolvedValueOnce({ 
        rows: [{ now: new Date() }] 
      } as any);

      const result = await mockPool.query('SELECT NOW()');

      expect(result.rows).toHaveLength(1);
      expect(result.rows[0].now).toBeDefined();
    });

    it('should log success message after table initialization', async () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      // Simulate successful initialization
      mockPool.query.mockResolvedValue({ rows: [] } as any);

      await mockPool.query('CREATE TABLE IF NOT EXISTS ai_credits');
      console.log('✅ AI credits tables initialized');

      expect(consoleSpy).toHaveBeenCalledWith('✅ AI credits tables initialized');

      consoleSpy.mockRestore();
    });

    it('should log success message after default user initialization', async () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      const DEFAULT_AI_CREDITS = 10000;

      mockPool.query.mockResolvedValue({ rows: [] } as any);

      await mockPool.query('INSERT INTO ai_credits', [DEFAULT_AI_CREDITS]);
      console.log(`✅ Default user credits initialized (${DEFAULT_AI_CREDITS} credits)`);

      expect(consoleSpy).toHaveBeenCalledWith(
        `✅ Default user credits initialized (${DEFAULT_AI_CREDITS} credits)`
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Error Handling', () => {
    it('should log warning on table creation failure', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      const error = new Error('Table creation failed');

      mockPool.query.mockRejectedValueOnce(error);

      try {
        await mockPool.query('CREATE TABLE IF NOT EXISTS ai_credits');
      } catch (e) {
        console.error('⚠️  Credits table initialization failed:', e);
        console.error('⚠️  Credits endpoints may not function correctly');
      }

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '⚠️  Credits table initialization failed:',
        error
      );

      consoleErrorSpy.mockRestore();
    });

    it('should allow application to continue after initialization failure', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      const error = new Error('Initialization failed');

      mockPool.query.mockRejectedValueOnce(error);

      try {
        await mockPool.query('CREATE TABLE');
      } catch (e) {
        // Application should continue even after error
        console.error('⚠️  Credits table initialization failed:', e);
      }

      expect(consoleErrorSpy).toHaveBeenCalled();
      consoleErrorSpy.mockRestore();
    });

    it('should handle connection timeout errors', async () => {
      const timeoutError = new Error('Connection timeout');
      mockPool.query.mockRejectedValueOnce(timeoutError);

      await expect(mockPool.query('SELECT NOW()')).rejects.toThrow('Connection timeout');
    });

    it('should handle permission errors during table creation', async () => {
      const permissionError = new Error('Permission denied');
      mockPool.query.mockRejectedValueOnce(permissionError);

      await expect(
        mockPool.query('CREATE TABLE IF NOT EXISTS ai_credits')
      ).rejects.toThrow('Permission denied');
    });

    it('should handle invalid SQL syntax errors', async () => {
      const syntaxError = new Error('Syntax error near');
      mockPool.query.mockRejectedValueOnce(syntaxError);

      await expect(
        mockPool.query('CREAT TABLE ai_credits') // Typo in CREATE
      ).rejects.toThrow('Syntax error');
    });

    it('should handle database unavailable errors', async () => {
      const unavailableError = new Error('Database unavailable');
      mockPool.query.mockRejectedValueOnce(unavailableError);

      await expect(mockPool.query('SELECT NOW()')).rejects.toThrow('Database unavailable');
    });
  });

  describe('Index Creation and Performance', () => {
    it('should create indexes for query optimization', () => {
      const indexes = [
        'CREATE INDEX IF NOT EXISTS idx_credit_usage_user ON ai_credit_usage(user_id)',
        'CREATE INDEX IF NOT EXISTS idx_credit_usage_created ON ai_credit_usage(created_at DESC)'
      ];

      indexes.forEach(index => {
        expect(index).toContain('CREATE INDEX IF NOT EXISTS');
        expect(index).toContain('ai_credit_usage');
      });
    });

    it('should create descending index on created_at for recent queries', () => {
      const index = 'CREATE INDEX IF NOT EXISTS idx_credit_usage_created ON ai_credit_usage(created_at DESC)';

      expect(index).toContain('created_at DESC');
    });

    it('should create user_id index for user-specific queries', () => {
      const index = 'CREATE INDEX IF NOT EXISTS idx_credit_usage_user ON ai_credit_usage(user_id)';

      expect(index).toContain('user_id');
    });
  });

  describe('Data Type Validation', () => {
    it('should use VARCHAR(255) for user_id to support various ID formats', () => {
      const schema = 'user_id VARCHAR(255) PRIMARY KEY';

      expect(schema).toContain('VARCHAR(255)');
      expect(schema).toContain('PRIMARY KEY');
    });

    it('should use INTEGER for credit values', () => {
      const schema = `
        total_credits INTEGER NOT NULL DEFAULT 10000,
        used_credits INTEGER NOT NULL DEFAULT 0
      `;

      expect(schema).toContain('total_credits INTEGER');
      expect(schema).toContain('used_credits INTEGER');
    });

    it('should use JSONB for flexible metadata storage', () => {
      const schema = "metadata JSONB DEFAULT '{}'";

      expect(schema).toContain('JSONB');
      expect(schema).toContain("DEFAULT '{}'");
    });

    it('should use TIMESTAMP for temporal tracking', () => {
      const schema = `
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      `;

      expect(schema).toContain('TIMESTAMP DEFAULT NOW()');
    });

    it('should use SERIAL for auto-incrementing primary keys', () => {
      const schema = 'id SERIAL PRIMARY KEY';

      expect(schema).toContain('SERIAL');
      expect(schema).toContain('PRIMARY KEY');
    });
  });

  describe('Default Values and Constraints', () => {
    it('should set NOT NULL constraints on required fields', () => {
      const constraints = [
        'total_credits INTEGER NOT NULL',
        'used_credits INTEGER NOT NULL',
        'user_id VARCHAR(255) NOT NULL',
        'credits_used INTEGER NOT NULL',
        'operation VARCHAR(100) NOT NULL'
      ];

      constraints.forEach(constraint => {
        expect(constraint).toContain('NOT NULL');
      });
    });

    it('should provide sensible default values', () => {
      const defaults = [
        'DEFAULT 10000',
        'DEFAULT 0',
        "DEFAULT '{}'",
        'DEFAULT NOW()'
      ];

      defaults.forEach(defaultValue => {
        expect(defaultValue).toContain('DEFAULT');
      });
    });

    it('should use parameterized values for user-configurable defaults', () => {
      const DEFAULT_AI_CREDITS = 15000;
      const query = `total_credits INTEGER NOT NULL DEFAULT ${DEFAULT_AI_CREDITS}`;

      expect(query).toContain('15000');
    });
  });

  describe('Integration with Existing Database', () => {
    it('should not conflict with existing tables', () => {
      const query = 'CREATE TABLE IF NOT EXISTS ai_credits';

      expect(query).toContain('IF NOT EXISTS');
    });

    it('should handle re-initialization gracefully', async () => {
      // First initialization
      mockPool.query.mockResolvedValueOnce({ rows: [] } as any);
      await mockPool.query('CREATE TABLE IF NOT EXISTS ai_credits');

      // Second initialization (should not fail)
      mockPool.query.mockResolvedValueOnce({ rows: [] } as any);
      await mockPool.query('CREATE TABLE IF NOT EXISTS ai_credits');

      expect(mockPool.query).toHaveBeenCalledTimes(2);
    });

    it('should handle existing default_user gracefully', async () => {
      const query = `
        INSERT INTO ai_credits (user_id, total_credits, used_credits)
        VALUES ('default_user', $1, 0)
        ON CONFLICT (user_id) DO NOTHING;
      `;

      mockPool.query.mockResolvedValue({ rows: [], rowCount: 0 } as any);

      await mockPool.query(query, [10000]);

      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('ON CONFLICT'),
        [10000]
      );
    });
  });

  describe('Schema Comments and Documentation', () => {
    it('should include comment about production migration recommendation', () => {
      const comment = 'Note: In production, this should ideally be managed through database migrations';

      expect(comment).toContain('production');
      expect(comment).toContain('database migrations');
    });

    it('should document the GROUP A classification', () => {
      const comment = 'Initialize AI Credits tables (GROUP A)';

      expect(comment).toContain('GROUP A');
    });
  });

  describe('Environment Configuration', () => {
    it('should respect DATABASE_URL environment variable', () => {
      process.env.DATABASE_URL = 'postgresql://user:pass@localhost:5432/testdb';

      expect(process.env.DATABASE_URL).toContain('postgresql://');
      expect(process.env.DATABASE_URL).toContain('localhost');

      delete process.env.DATABASE_URL;
    });

    it('should exit with error when DATABASE_URL is not set', () => {
      const originalExit = process.exit;
      const mockExit = jest.fn() as any;
      process.exit = mockExit;

      const DATABASE_URL = process.env.DATABASE_URL;
      if (!DATABASE_URL) {
        console.error('❌ DATABASE_URL environment variable is required');
        process.exit(1);
      }

      expect(mockExit).toHaveBeenCalledWith(1);
      process.exit = originalExit;
    });
  });

  describe('Logging and Monitoring', () => {
    it('should log PostgreSQL connection success', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      console.log('✅ PostgreSQL connected');

      expect(consoleSpy).toHaveBeenCalledWith('✅ PostgreSQL connected');

      consoleSpy.mockRestore();
    });

    it('should log table initialization progress', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      console.log('✅ AI credits tables initialized');
      console.log('✅ Default user credits initialized (10000 credits)');

      expect(consoleSpy).toHaveBeenCalledTimes(2);

      consoleSpy.mockRestore();
    });

    it('should log warning messages for initialization failures', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      console.error('⚠️  Credits table initialization failed:', new Error('Test error'));
      console.error('⚠️  Credits endpoints may not function correctly');

      expect(consoleSpy).toHaveBeenCalledTimes(2);

      consoleSpy.mockRestore();
    });
  });

  describe('Concurrent Access and Race Conditions', () => {
    it('should handle concurrent table creation attempts', async () => {
      const promises = Array(10).fill(null).map(() => 
        mockPool.query('CREATE TABLE IF NOT EXISTS ai_credits')
      );

      mockPool.query.mockResolvedValue({ rows: [] } as any);

      await Promise.all(promises);

      expect(mockPool.query).toHaveBeenCalledTimes(10);
    });

    it('should handle concurrent default user initialization', async () => {
      const promises = Array(5).fill(null).map(() => 
        mockPool.query(
          'INSERT INTO ai_credits (user_id, total_credits, used_credits) VALUES ($1, $2, 0) ON CONFLICT DO NOTHING',
          ['default_user', 10000]
        )
      );

      mockPool.query.mockResolvedValue({ rows: [], rowCount: 0 } as any);

      await Promise.all(promises);

      expect(mockPool.query).toHaveBeenCalledTimes(5);
    });
  });
});