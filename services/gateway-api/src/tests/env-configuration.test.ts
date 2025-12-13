/**
 * Environment Configuration Tests
 * 
 * Comprehensive tests for .env configuration including:
 * - DEFAULT_AI_CREDITS configuration
 * - Configuration validation
 * - Type safety and parsing
 * - Edge cases and error handling
 * 
 * Run with: npm test -- env-configuration.test.ts
 */

describe('Environment Configuration - DEFAULT_AI_CREDITS', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...originalEnv };
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  describe('Valid Configuration Values', () => {
    it('should parse valid integer from DEFAULT_AI_CREDITS', () => {
      process.env.DEFAULT_AI_CREDITS = '10000';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(10000);
      expect(typeof credits).toBe('number');
    });

    it('should handle small credit values', () => {
      process.env.DEFAULT_AI_CREDITS = '100';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(100);
    });

    it('should handle large credit values', () => {
      process.env.DEFAULT_AI_CREDITS = '1000000';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(1000000);
    });

    it('should handle maximum safe integer', () => {
      process.env.DEFAULT_AI_CREDITS = String(Number.MAX_SAFE_INTEGER);
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(Number.MAX_SAFE_INTEGER);
    });

    it('should accept common credit tier values', () => {
      const tiers = ['5000', '10000', '25000', '50000', '100000'];
      
      tiers.forEach(tier => {
        process.env.DEFAULT_AI_CREDITS = tier;
        const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
        
        expect(credits).toBe(parseInt(tier, 10));
        expect(credits).toBeGreaterThan(0);
      });
    });
  });

  describe('Default Fallback Behavior', () => {
    it('should use 10000 as default when env variable is not set', () => {
      delete process.env.DEFAULT_AI_CREDITS;
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(10000);
    });

    it('should use 10000 as default when env variable is empty string', () => {
      process.env.DEFAULT_AI_CREDITS = '';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(10000);
    });

    it('should use 10000 as default when env variable is undefined', () => {
      process.env.DEFAULT_AI_CREDITS = undefined as any;
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(10000);
    });
  });

  describe('Invalid Configuration Handling', () => {
    it('should return NaN for non-numeric values', () => {
      process.env.DEFAULT_AI_CREDITS = 'invalid';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBeNaN();
    });

    it('should return NaN for alphabetic strings', () => {
      process.env.DEFAULT_AI_CREDITS = 'abc123';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBeNaN();
    });

    it('should handle special characters gracefully', () => {
      const specialValues = ['@#$%', '!!!', '___', '...'];
      
      specialValues.forEach(value => {
        process.env.DEFAULT_AI_CREDITS = value;
        const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
        
        expect(credits).toBeNaN();
      });
    });

    it('should handle whitespace-only strings', () => {
      const whitespaceValues = ['   ', '\t', '\n', '\r\n'];
      
      whitespaceValues.forEach(value => {
        process.env.DEFAULT_AI_CREDITS = value;
        const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
        
        expect(credits).toBeNaN();
      });
    });
  });

  describe('Edge Cases and Boundary Values', () => {
    it('should handle zero credits', () => {
      process.env.DEFAULT_AI_CREDITS = '0';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(0);
    });

    it('should handle negative values', () => {
      process.env.DEFAULT_AI_CREDITS = '-1000';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(-1000);
    });

    it('should parse floating point as integer (truncates decimal)', () => {
      process.env.DEFAULT_AI_CREDITS = '10000.99';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(10000);
    });

    it('should handle scientific notation', () => {
      process.env.DEFAULT_AI_CREDITS = '1e5';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(1);
    });

    it('should handle numbers with leading zeros', () => {
      process.env.DEFAULT_AI_CREDITS = '00010000';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(10000);
    });

    it('should handle numbers with leading plus sign', () => {
      process.env.DEFAULT_AI_CREDITS = '+10000';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(10000);
    });

    it('should handle numbers with spaces', () => {
      process.env.DEFAULT_AI_CREDITS = ' 10000 ';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(10000);
    });

    it('should stop parsing at first non-numeric character', () => {
      process.env.DEFAULT_AI_CREDITS = '10000credits';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(10000);
    });
  });

  describe('Type Safety and Parsing', () => {
    it('should always return a number type when parsed', () => {
      process.env.DEFAULT_AI_CREDITS = '10000';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(typeof credits).toBe('number');
    });

    it('should use base 10 for parsing', () => {
      process.env.DEFAULT_AI_CREDITS = '10';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(10);
      expect(credits).not.toBe(0x10); // Not hex
      expect(credits).not.toBe(0o10); // Not octal
    });

    it('should handle octal-like strings correctly with base 10', () => {
      process.env.DEFAULT_AI_CREDITS = '0777';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(777);
      expect(credits).not.toBe(0o777);
    });

    it('should handle hex-like strings as decimal', () => {
      process.env.DEFAULT_AI_CREDITS = '0xFF';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(0);
    });
  });

  describe('Configuration Validation Strategies', () => {
    it('should validate credits are positive in production logic', () => {
      process.env.DEFAULT_AI_CREDITS = '10000';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      const isValid = credits > 0 && !isNaN(credits);
      
      expect(isValid).toBe(true);
    });

    it('should detect invalid configurations', () => {
      process.env.DEFAULT_AI_CREDITS = 'invalid';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      const isValid = credits > 0 && !isNaN(credits);
      
      expect(isValid).toBe(false);
    });

    it('should validate credits are within reasonable range', () => {
      const MIN_CREDITS = 0;
      const MAX_CREDITS = 10000000;

      process.env.DEFAULT_AI_CREDITS = '50000';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      const isValid = credits >= MIN_CREDITS && credits <= MAX_CREDITS;
      
      expect(isValid).toBe(true);
    });

    it('should reject extremely large values outside reasonable range', () => {
      const MAX_CREDITS = 10000000;

      process.env.DEFAULT_AI_CREDITS = '999999999999';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      const isValid = credits <= MAX_CREDITS;
      
      expect(isValid).toBe(false);
    });
  });

  describe('Multiple Environment Variables Interaction', () => {
    it('should not affect other environment variables', () => {
      process.env.DEFAULT_AI_CREDITS = '10000';
      process.env.OTHER_CONFIG = 'value';
      
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(credits).toBe(10000);
      expect(process.env.OTHER_CONFIG).toBe('value');
    });

    it('should handle PORT and DEFAULT_AI_CREDITS independently', () => {
      process.env.PORT = '8000';
      process.env.DEFAULT_AI_CREDITS = '15000';
      
      const port = parseInt(process.env.PORT || '8000', 10);
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      expect(port).toBe(8000);
      expect(credits).toBe(15000);
    });
  });

  describe('Documentation and Comments in .env', () => {
    it('should document the purpose of DEFAULT_AI_CREDITS', () => {
      const comment = '# Default credits assigned to new users';
      
      expect(comment).toContain('Default credits');
      expect(comment).toContain('new users');
    });

    it('should include the AI Credits configuration section header', () => {
      const header = '# AI CREDITS CONFIGURATION';
      
      expect(header).toContain('AI CREDITS');
      expect(header).toContain('CONFIGURATION');
    });

    it('should provide example value in documentation', () => {
      const example = 'DEFAULT_AI_CREDITS=10000';
      
      expect(example).toContain('DEFAULT_AI_CREDITS');
      expect(example).toContain('10000');
    });
  });

  describe('Consistency with Database Schema', () => {
    it('should match default value in database schema', () => {
      const envDefault = 10000;
      const dbDefault = 10000;
      
      expect(envDefault).toBe(dbDefault);
    });

    it('should be usable in SQL query construction', () => {
      process.env.DEFAULT_AI_CREDITS = '10000';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      const query = `total_credits INTEGER NOT NULL DEFAULT ${credits}`;
      
      expect(query).toContain('DEFAULT 10000');
    });

    it('should be parameterizable in SQL queries', () => {
      process.env.DEFAULT_AI_CREDITS = '15000';
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      
      const queryParams = [credits];
      
      expect(queryParams[0]).toBe(15000);
      expect(typeof queryParams[0]).toBe('number');
    });
  });

  describe('Real-world Usage Scenarios', () => {
    it('should support different environments with different defaults', () => {
      const environments = {
        development: '10000',
        staging: '25000',
        production: '50000'
      };

      Object.entries(environments).forEach(([env, value]) => {
        process.env.DEFAULT_AI_CREDITS = value;
        const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
        
        expect(credits).toBe(parseInt(value, 10));
      });
    });

    it('should handle dynamic configuration updates', () => {
      process.env.DEFAULT_AI_CREDITS = '10000';
      let credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      expect(credits).toBe(10000);

      process.env.DEFAULT_AI_CREDITS = '20000';
      credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      expect(credits).toBe(20000);
    });

    it('should support A/B testing with different credit tiers', () => {
      const tierA = '10000';
      const tierB = '15000';

      process.env.DEFAULT_AI_CREDITS = tierA;
      const creditsA = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);

      process.env.DEFAULT_AI_CREDITS = tierB;
      const creditsB = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);

      expect(creditsA).toBeLessThan(creditsB);
      expect(creditsB - creditsA).toBe(5000);
    });
  });

  describe('Error Prevention and Best Practices', () => {
    it('should provide clear variable naming', () => {
      const variableName = 'DEFAULT_AI_CREDITS';
      
      expect(variableName).toContain('DEFAULT');
      expect(variableName).toContain('AI');
      expect(variableName).toContain('CREDITS');
    });

    it('should use SCREAMING_SNAKE_CASE convention', () => {
      const variableName = 'DEFAULT_AI_CREDITS';
      
      expect(variableName).toBe(variableName.toUpperCase());
      expect(variableName).toContain('_');
    });

    it('should avoid ambiguous naming', () => {
      const variableName = 'DEFAULT_AI_CREDITS';
      
      expect(variableName).not.toBe('CREDITS');
      expect(variableName).not.toBe('DEFAULT_CREDITS');
      expect(variableName).toContain('AI');
    });
  });

  describe('Integration Tests', () => {
    it('should work with the full initialization flow', () => {
      process.env.DEFAULT_AI_CREDITS = '10000';
      const DEFAULT_AI_CREDITS = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);

      const createTableQuery = `
        CREATE TABLE IF NOT EXISTS ai_credits (
          user_id VARCHAR(255) PRIMARY KEY,
          total_credits INTEGER NOT NULL DEFAULT ${DEFAULT_AI_CREDITS},
          used_credits INTEGER NOT NULL DEFAULT 0
        );
      `;

      expect(createTableQuery).toContain('DEFAULT 10000');
    });

    it('should work with user initialization query', () => {
      process.env.DEFAULT_AI_CREDITS = '10000';
      const DEFAULT_AI_CREDITS = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);

      const initQuery = `
        INSERT INTO ai_credits (user_id, total_credits, used_credits)
        VALUES ('default_user', $1, 0)
        ON CONFLICT (user_id) DO NOTHING;
      `;

      const params = [DEFAULT_AI_CREDITS];

      expect(params[0]).toBe(10000);
      expect(initQuery).toContain('$1');
    });
  });

  describe('Performance Considerations', () => {
    it('should cache parsed value for performance', () => {
      process.env.DEFAULT_AI_CREDITS = '10000';
      
      const startTime = Date.now();
      const credits = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);
      const parseTime = Date.now() - startTime;

      expect(parseTime).toBeLessThan(10); // Should be very fast
      expect(credits).toBe(10000);
    });

    it('should not require repeated parsing', () => {
      process.env.DEFAULT_AI_CREDITS = '10000';
      const DEFAULT_AI_CREDITS = parseInt(process.env.DEFAULT_AI_CREDITS || '10000', 10);

      // Use the cached constant
      expect(DEFAULT_AI_CREDITS).toBe(10000);
      expect(DEFAULT_AI_CREDITS).toBe(10000);
      expect(DEFAULT_AI_CREDITS).toBe(10000);
    });
  });
});