/**
 * Security Tests - Agent 98
 *
 * Comprehensive security testing suite
 */

import { describe, it, expect, beforeAll } from '@jest/globals';
import {
  hashPassword,
  verifyPassword,
  validatePasswordStrength,
  isCommonPassword,
  generateSecurePassword,
  needsRehash
} from '../utils/password';
import {
  sanitizeHTML,
  sanitizeSQL
} from '../middleware/security';
import {
  createCampaignSchema,
  emailSchema,
  uuidSchema,
  registerUserSchema
} from '../middleware/validation-schemas';

// ============================================================================
// PASSWORD SECURITY TESTS
// ============================================================================

describe('Password Security', () => {
  describe('hashPassword', () => {
    it('should hash passwords securely', async () => {
      const password = 'SecurePassword123!';
      const hash = await hashPassword(password);

      expect(hash).toBeDefined();
      expect(hash).not.toBe(password);
      expect(hash.length).toBeGreaterThan(50);
    });

    it('should produce different hashes for same password', async () => {
      const password = 'SecurePassword123!';
      const hash1 = await hashPassword(password);
      const hash2 = await hashPassword(password);

      expect(hash1).not.toBe(hash2);
    });

    it('should reject passwords that are too long', async () => {
      const longPassword = 'a'.repeat(200);

      await expect(hashPassword(longPassword)).rejects.toThrow();
    });
  });

  describe('verifyPassword', () => {
    it('should verify correct passwords', async () => {
      const password = 'SecurePassword123!';
      const hash = await hashPassword(password);
      const isValid = await verifyPassword(password, hash);

      expect(isValid).toBe(true);
    });

    it('should reject incorrect passwords', async () => {
      const password = 'SecurePassword123!';
      const hash = await hashPassword(password);
      const isValid = await verifyPassword('WrongPassword123!', hash);

      expect(isValid).toBe(false);
    });

    it('should reject empty passwords', async () => {
      const hash = await hashPassword('SecurePassword123!');
      const isValid = await verifyPassword('', hash);

      expect(isValid).toBe(false);
    });
  });

  describe('validatePasswordStrength', () => {
    it('should accept strong passwords', () => {
      const result = validatePasswordStrength('StrongPass123!');
      expect(result.valid).toBe(true);
    });

    it('should reject short passwords', () => {
      const result = validatePasswordStrength('Short1!');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('at least');
    });

    it('should reject passwords without uppercase', () => {
      const result = validatePasswordStrength('lowercase123!');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('uppercase');
    });

    it('should reject passwords without lowercase', () => {
      const result = validatePasswordStrength('UPPERCASE123!');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('lowercase');
    });

    it('should reject passwords without numbers', () => {
      const result = validatePasswordStrength('NoNumbers!');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('number');
    });
  });

  describe('isCommonPassword', () => {
    it('should detect common passwords', () => {
      expect(isCommonPassword('password')).toBe(true);
      expect(isCommonPassword('password123')).toBe(true);
      expect(isCommonPassword('12345678')).toBe(true);
      expect(isCommonPassword('qwerty')).toBe(true);
    });

    it('should accept uncommon passwords', () => {
      expect(isCommonPassword('UncommonPass123!')).toBe(false);
      expect(isCommonPassword('MyUniqueP@ssw0rd')).toBe(false);
    });
  });

  describe('generateSecurePassword', () => {
    it('should generate passwords of correct length', () => {
      const password = generateSecurePassword(16);
      expect(password.length).toBe(16);
    });

    it('should generate passwords with mixed case and numbers', () => {
      const password = generateSecurePassword(16);

      expect(/[A-Z]/.test(password)).toBe(true); // Has uppercase
      expect(/[a-z]/.test(password)).toBe(true); // Has lowercase
      expect(/\d/.test(password)).toBe(true);    // Has number
    });

    it('should generate different passwords each time', () => {
      const password1 = generateSecurePassword(16);
      const password2 = generateSecurePassword(16);

      expect(password1).not.toBe(password2);
    });
  });

  describe('needsRehash', () => {
    it('should detect hashes needing upgrade', async () => {
      const password = 'SecurePassword123!';
      const weakHash = await hashPassword(password, 4); // Low salt rounds
      const needsUpgrade = needsRehash(weakHash, 12);

      expect(needsUpgrade).toBe(true);
    });
  });
});

// ============================================================================
// INPUT SANITIZATION TESTS
// ============================================================================

describe('Input Sanitization', () => {
  describe('sanitizeHTML', () => {
    it('should escape HTML special characters', () => {
      const input = '<script>alert("XSS")</script>';
      const sanitized = sanitizeHTML(input);

      expect(sanitized).not.toContain('<script>');
      expect(sanitized).toContain('&lt;script&gt;');
    });

    it('should escape quotes', () => {
      const input = 'He said "hello"';
      const sanitized = sanitizeHTML(input);

      expect(sanitized).toContain('&quot;');
    });

    it('should handle multiple dangerous characters', () => {
      const input = '<img src="x" onerror="alert(\'XSS\')">';
      const sanitized = sanitizeHTML(input);

      expect(sanitized).not.toContain('<img');
      expect(sanitized).not.toContain('onerror');
      expect(sanitized).toContain('&lt;');
      expect(sanitized).toContain('&gt;');
    });

    it('should not affect safe text', () => {
      const input = 'This is safe text with numbers 123';
      const sanitized = sanitizeHTML(input);

      expect(sanitized).toBe('This is safe text with numbers 123');
    });
  });

  describe('sanitizeSQL', () => {
    it('should detect UNION SELECT attacks', () => {
      const input = "1' UNION SELECT * FROM users--";

      expect(() => sanitizeSQL(input)).toThrow('SQL injection');
    });

    it('should detect DROP TABLE attacks', () => {
      const input = "1'; DROP TABLE users;--";

      expect(() => sanitizeSQL(input)).toThrow('SQL injection');
    });

    it('should detect DELETE FROM attacks', () => {
      const input = "1' OR 1=1; DELETE FROM users;--";

      expect(() => sanitizeSQL(input)).toThrow('SQL injection');
    });

    it('should allow safe SQL-like text', () => {
      const input = 'This is a normal string with SELECT in it';

      expect(() => sanitizeSQL(input)).not.toThrow();
    });
  });
});

// ============================================================================
// ZOD VALIDATION TESTS
// ============================================================================

describe('Zod Schema Validation', () => {
  describe('emailSchema', () => {
    it('should accept valid emails', () => {
      expect(() => emailSchema.parse('user@example.com')).not.toThrow();
      expect(() => emailSchema.parse('test.user+tag@domain.co.uk')).not.toThrow();
    });

    it('should reject invalid emails', () => {
      expect(() => emailSchema.parse('invalid-email')).toThrow();
      expect(() => emailSchema.parse('@example.com')).toThrow();
      expect(() => emailSchema.parse('user@')).toThrow();
    });
  });

  describe('uuidSchema', () => {
    it('should accept valid UUIDs', () => {
      const validUUID = '123e4567-e89b-12d3-a456-426614174000';
      expect(() => uuidSchema.parse(validUUID)).not.toThrow();
    });

    it('should reject invalid UUIDs', () => {
      expect(() => uuidSchema.parse('not-a-uuid')).toThrow();
      expect(() => uuidSchema.parse('12345678')).toThrow();
    });
  });

  describe('createCampaignSchema', () => {
    it('should accept valid campaign data', () => {
      const validCampaign = {
        name: 'Test Campaign',
        budget_daily: 100,
        objective: 'conversions',
        status: 'draft'
      };

      expect(() => createCampaignSchema.parse(validCampaign)).not.toThrow();
    });

    it('should reject campaign with negative budget', () => {
      const invalidCampaign = {
        name: 'Test Campaign',
        budget_daily: -100,
        objective: 'conversions'
      };

      expect(() => createCampaignSchema.parse(invalidCampaign)).toThrow();
    });

    it('should reject campaign without name', () => {
      const invalidCampaign = {
        budget_daily: 100,
        objective: 'conversions'
      };

      expect(() => createCampaignSchema.parse(invalidCampaign)).toThrow();
    });

    it('should reject invalid objective', () => {
      const invalidCampaign = {
        name: 'Test Campaign',
        budget_daily: 100,
        objective: 'invalid_objective'
      };

      expect(() => createCampaignSchema.parse(invalidCampaign)).toThrow();
    });
  });

  describe('registerUserSchema', () => {
    it('should accept valid user registration', () => {
      const validUser = {
        email: 'user@example.com',
        password: 'SecurePass123!',
        displayName: 'John Doe'
      };

      expect(() => registerUserSchema.parse(validUser)).not.toThrow();
    });

    it('should reject weak passwords', () => {
      const invalidUser = {
        email: 'user@example.com',
        password: 'weak',
        displayName: 'John Doe'
      };

      expect(() => registerUserSchema.parse(invalidUser)).toThrow();
    });

    it('should reject passwords without uppercase', () => {
      const invalidUser = {
        email: 'user@example.com',
        password: 'lowercase123',
        displayName: 'John Doe'
      };

      expect(() => registerUserSchema.parse(invalidUser)).toThrow();
    });

    it('should reject invalid email format', () => {
      const invalidUser = {
        email: 'not-an-email',
        password: 'SecurePass123!',
        displayName: 'John Doe'
      };

      expect(() => registerUserSchema.parse(invalidUser)).toThrow();
    });
  });
});

// ============================================================================
// SECURITY BEST PRACTICES TESTS
// ============================================================================

describe('Security Best Practices', () => {
  it('password hashes should be timing-safe', async () => {
    const password = 'SecurePassword123!';
    const hash = await hashPassword(password);

    const startCorrect = Date.now();
    await verifyPassword(password, hash);
    const timeCorrect = Date.now() - startCorrect;

    const startWrong = Date.now();
    await verifyPassword('WrongPassword123!', hash);
    const timeWrong = Date.now() - startWrong;

    // Timing should be similar (within 50ms) to prevent timing attacks
    const timeDiff = Math.abs(timeCorrect - timeWrong);
    expect(timeDiff).toBeLessThan(50);
  });

  it('should not expose sensitive error details', () => {
    try {
      uuidSchema.parse('invalid-uuid');
    } catch (error: any) {
      // Error should not contain internal implementation details
      expect(error.message).not.toContain('node_modules');
      expect(error.message).not.toContain('stack');
    }
  });
});

// ============================================================================
// INTEGRATION TESTS (if needed)
// ============================================================================

describe('Security Integration', () => {
  it('should validate and sanitize user input in one flow', () => {
    const userInput = {
      name: '<script>alert("XSS")</script>',
      email: 'user@example.com',
      budget_daily: 100
    };

    // Validation should pass
    const result = createCampaignSchema.safeParse(userInput);
    expect(result.success).toBe(true);

    // HTML should be sanitized
    if (result.success) {
      const sanitizedName = sanitizeHTML(result.data.name);
      expect(sanitizedName).not.toContain('<script>');
      expect(sanitizedName).toContain('&lt;script&gt;');
    }
  });
});
