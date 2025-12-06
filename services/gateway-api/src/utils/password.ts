/**
 * Password Hashing Utilities - Agent 98: Security & Validation
 *
 * Provides secure password hashing and verification using bcrypt
 * Industry-standard password security with configurable salt rounds
 */

import bcrypt from 'bcrypt';

// ============================================================================
// CONFIGURATION
// ============================================================================

/**
 * Salt rounds for bcrypt hashing
 * Higher = more secure but slower
 * Recommended: 10-12 for production
 */
const SALT_ROUNDS = parseInt(process.env.BCRYPT_SALT_ROUNDS || '12', 10);

/**
 * Minimum password length
 */
const MIN_PASSWORD_LENGTH = 8;

/**
 * Maximum password length (prevent DoS attacks)
 */
const MAX_PASSWORD_LENGTH = 128;

// ============================================================================
// PASSWORD VALIDATION
// ============================================================================

/**
 * Password strength requirements
 */
export interface PasswordRequirements {
  minLength: number;
  maxLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireNumber: boolean;
  requireSpecialChar: boolean;
}

/**
 * Default password requirements
 */
const DEFAULT_REQUIREMENTS: PasswordRequirements = {
  minLength: MIN_PASSWORD_LENGTH,
  maxLength: MAX_PASSWORD_LENGTH,
  requireUppercase: true,
  requireLowercase: true,
  requireNumber: true,
  requireSpecialChar: false
};

/**
 * Validate password strength
 *
 * @param password - Password to validate
 * @param requirements - Custom requirements (optional)
 * @returns Object with validation result and error message
 */
export function validatePasswordStrength(
  password: string,
  requirements: Partial<PasswordRequirements> = {}
): { valid: boolean; error?: string } {
  const reqs = { ...DEFAULT_REQUIREMENTS, ...requirements };

  // Check length
  if (password.length < reqs.minLength) {
    return {
      valid: false,
      error: `Password must be at least ${reqs.minLength} characters long`
    };
  }

  if (password.length > reqs.maxLength) {
    return {
      valid: false,
      error: `Password must be at most ${reqs.maxLength} characters long`
    };
  }

  // Check uppercase
  if (reqs.requireUppercase && !/[A-Z]/.test(password)) {
    return {
      valid: false,
      error: 'Password must contain at least one uppercase letter'
    };
  }

  // Check lowercase
  if (reqs.requireLowercase && !/[a-z]/.test(password)) {
    return {
      valid: false,
      error: 'Password must contain at least one lowercase letter'
    };
  }

  // Check number
  if (reqs.requireNumber && !/\d/.test(password)) {
    return {
      valid: false,
      error: 'Password must contain at least one number'
    };
  }

  // Check special character
  if (reqs.requireSpecialChar && !/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    return {
      valid: false,
      error: 'Password must contain at least one special character'
    };
  }

  return { valid: true };
}

/**
 * Check if password contains common patterns (basic check)
 *
 * @param password - Password to check
 * @returns true if password is too common/weak
 */
export function isCommonPassword(password: string): boolean {
  const commonPasswords = [
    'password',
    '12345678',
    'qwerty',
    'abc123',
    'password123',
    'admin',
    'letmein',
    'welcome',
    'monkey',
    '1234567890'
  ];

  const lowerPassword = password.toLowerCase();

  return commonPasswords.some(common => lowerPassword.includes(common));
}

// ============================================================================
// PASSWORD HASHING
// ============================================================================

/**
 * Hash a password using bcrypt
 *
 * @param password - Plain text password
 * @param saltRounds - Number of salt rounds (default: from env or 12)
 * @returns Hashed password
 * @throws Error if hashing fails
 */
export async function hashPassword(
  password: string,
  saltRounds: number = SALT_ROUNDS
): Promise<string> {
  try {
    // Validate password length to prevent DoS
    if (password.length > MAX_PASSWORD_LENGTH) {
      throw new Error(`Password too long (max ${MAX_PASSWORD_LENGTH} characters)`);
    }

    // Generate salt and hash
    const salt = await bcrypt.genSalt(saltRounds);
    const hash = await bcrypt.hash(password, salt);

    return hash;
  } catch (error: any) {
    console.error('Password hashing error:', error.message);
    throw new Error(`Failed to hash password: ${error.message}`);
  }
}

/**
 * Hash a password synchronously (use sparingly - blocks event loop)
 *
 * @param password - Plain text password
 * @param saltRounds - Number of salt rounds (default: from env or 12)
 * @returns Hashed password
 * @throws Error if hashing fails
 */
export function hashPasswordSync(
  password: string,
  saltRounds: number = SALT_ROUNDS
): string {
  try {
    if (password.length > MAX_PASSWORD_LENGTH) {
      throw new Error(`Password too long (max ${MAX_PASSWORD_LENGTH} characters)`);
    }

    const salt = bcrypt.genSaltSync(saltRounds);
    const hash = bcrypt.hashSync(password, salt);

    return hash;
  } catch (error: any) {
    console.error('Password hashing error:', error.message);
    throw new Error(`Failed to hash password: ${error.message}`);
  }
}

// ============================================================================
// PASSWORD VERIFICATION
// ============================================================================

/**
 * Verify a password against a hash
 *
 * @param password - Plain text password to verify
 * @param hash - Hashed password to compare against
 * @returns true if password matches hash, false otherwise
 * @throws Error if verification fails
 */
export async function verifyPassword(
  password: string,
  hash: string
): Promise<boolean> {
  try {
    // Validate inputs
    if (!password || !hash) {
      return false;
    }

    // Verify password length to prevent DoS
    if (password.length > MAX_PASSWORD_LENGTH) {
      return false;
    }

    // Compare password with hash
    const isMatch = await bcrypt.compare(password, hash);

    return isMatch;
  } catch (error: any) {
    console.error('Password verification error:', error.message);
    throw new Error(`Failed to verify password: ${error.message}`);
  }
}

/**
 * Verify a password synchronously (use sparingly - blocks event loop)
 *
 * @param password - Plain text password to verify
 * @param hash - Hashed password to compare against
 * @returns true if password matches hash, false otherwise
 */
export function verifyPasswordSync(
  password: string,
  hash: string
): boolean {
  try {
    if (!password || !hash || password.length > MAX_PASSWORD_LENGTH) {
      return false;
    }

    return bcrypt.compareSync(password, hash);
  } catch (error: any) {
    console.error('Password verification error:', error.message);
    return false;
  }
}

// ============================================================================
// PASSWORD REHASHING
// ============================================================================

/**
 * Check if a password hash needs to be rehashed
 * (if salt rounds have changed)
 *
 * @param hash - Current password hash
 * @param targetSaltRounds - Desired salt rounds
 * @returns true if rehashing is needed
 */
export function needsRehash(
  hash: string,
  targetSaltRounds: number = SALT_ROUNDS
): boolean {
  try {
    const currentRounds = bcrypt.getRounds(hash);
    return currentRounds < targetSaltRounds;
  } catch (error) {
    // If we can't determine rounds, assume rehashing is needed
    return true;
  }
}

/**
 * Rehash a password if needed (on successful login)
 *
 * @param password - Plain text password
 * @param currentHash - Current password hash
 * @param targetSaltRounds - Desired salt rounds
 * @returns New hash if rehashing was needed, null otherwise
 */
export async function rehashIfNeeded(
  password: string,
  currentHash: string,
  targetSaltRounds: number = SALT_ROUNDS
): Promise<string | null> {
  try {
    // First verify the password
    const isValid = await verifyPassword(password, currentHash);

    if (!isValid) {
      return null;
    }

    // Check if rehashing is needed
    if (needsRehash(currentHash, targetSaltRounds)) {
      console.log('Password hash outdated, rehashing with new salt rounds');
      return await hashPassword(password, targetSaltRounds);
    }

    return null;
  } catch (error: any) {
    console.error('Password rehashing error:', error.message);
    return null;
  }
}

// ============================================================================
// PASSWORD GENERATION
// ============================================================================

/**
 * Generate a secure random password
 *
 * @param length - Password length (default: 16)
 * @param includeSpecialChars - Include special characters (default: true)
 * @returns Generated password
 */
export function generateSecurePassword(
  length: number = 16,
  includeSpecialChars: boolean = true
): string {
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const lowercase = 'abcdefghijklmnopqrstuvwxyz';
  const numbers = '0123456789';
  const specialChars = '!@#$%^&*()_+-=[]{}|;:,.<>?';

  let chars = uppercase + lowercase + numbers;
  if (includeSpecialChars) {
    chars += specialChars;
  }

  let password = '';

  // Ensure at least one of each required type
  password += uppercase[Math.floor(Math.random() * uppercase.length)];
  password += lowercase[Math.floor(Math.random() * lowercase.length)];
  password += numbers[Math.floor(Math.random() * numbers.length)];

  if (includeSpecialChars) {
    password += specialChars[Math.floor(Math.random() * specialChars.length)];
  }

  // Fill the rest randomly
  for (let i = password.length; i < length; i++) {
    password += chars[Math.floor(Math.random() * chars.length)];
  }

  // Shuffle the password
  return password
    .split('')
    .sort(() => Math.random() - 0.5)
    .join('');
}

// ============================================================================
// TIMING-SAFE COMPARISON
// ============================================================================

/**
 * Timing-safe string comparison to prevent timing attacks
 *
 * @param a - First string
 * @param b - Second string
 * @returns true if strings are equal
 */
export function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) {
    return false;
  }

  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }

  return result === 0;
}

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  // Validation
  validatePasswordStrength,
  isCommonPassword,

  // Hashing
  hashPassword,
  hashPasswordSync,

  // Verification
  verifyPassword,
  verifyPasswordSync,

  // Rehashing
  needsRehash,
  rehashIfNeeded,

  // Generation
  generateSecurePassword,

  // Security
  timingSafeEqual,

  // Constants
  SALT_ROUNDS,
  MIN_PASSWORD_LENGTH,
  MAX_PASSWORD_LENGTH
};
