import * as admin from 'firebase-admin';
import { UserRecord } from 'firebase-admin/auth';

/**
 * Firebase Authentication Service
 *
 * Provides server-side authentication operations using Firebase Admin SDK
 * Handles token verification, user management, and custom claims
 */
export class FirebaseAuthService {
  private auth: admin.auth.Auth;
  private initialized: boolean = false;

  constructor() {
    this.initializeFirebase();
    this.auth = admin.auth();
  }

  /**
   * Initialize Firebase Admin SDK
   * Uses environment variables for configuration
   * Supports both service account file and individual credentials
   */
  private initializeFirebase(): void {
    if (this.initialized || admin.apps.length > 0) {
      console.log('🔥 Firebase Admin SDK already initialized');
      this.initialized = true;
      return;
    }

    try {
      // Method 1: Initialize with service account file path
      if (process.env.FIREBASE_SERVICE_ACCOUNT_PATH) {
        const serviceAccount = require(process.env.FIREBASE_SERVICE_ACCOUNT_PATH);

        admin.initializeApp({
          credential: admin.credential.cert(serviceAccount),
          projectId: process.env.FIREBASE_PROJECT_ID,
          storageBucket: process.env.FIREBASE_STORAGE_BUCKET
        });

        console.log('🔥 Firebase Admin initialized with service account file');
      }
      // Method 2: Initialize with individual environment variables
      else if (process.env.FIREBASE_PROJECT_ID && process.env.FIREBASE_CLIENT_EMAIL && process.env.FIREBASE_PRIVATE_KEY) {
        admin.initializeApp({
          credential: admin.credential.cert({
            projectId: process.env.FIREBASE_PROJECT_ID,
            clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
            privateKey: process.env.FIREBASE_PRIVATE_KEY.replace(/\\n/g, '\n')
          }),
          projectId: process.env.FIREBASE_PROJECT_ID,
          storageBucket: process.env.FIREBASE_STORAGE_BUCKET
        });

        console.log('🔥 Firebase Admin initialized with environment variables');
      }
      // Method 3: Initialize with Application Default Credentials (GCP environment)
      else if (process.env.GOOGLE_APPLICATION_CREDENTIALS || process.env.GCLOUD_PROJECT) {
        admin.initializeApp({
          projectId: process.env.FIREBASE_PROJECT_ID || process.env.GCLOUD_PROJECT
        });

        console.log('🔥 Firebase Admin initialized with Application Default Credentials');
      }
      else {
        throw new Error(
          'Firebase Admin SDK initialization failed: No valid credentials found. ' +
          'Please set FIREBASE_SERVICE_ACCOUNT_PATH or individual Firebase credentials.'
        );
      }

      this.initialized = true;
      console.log('✅ Firebase Admin SDK initialized successfully');
      console.log('📦 Project ID:', process.env.FIREBASE_PROJECT_ID);

    } catch (error: any) {
      console.error('❌ Firebase Admin SDK initialization error:', error.message);
      throw new Error(`Failed to initialize Firebase Admin SDK: ${error.message}`);
    }
  }

  /**
   * Verify a Firebase ID token
   *
   * @param idToken - The Firebase ID token to verify
   * @param checkRevoked - Whether to check if the token has been revoked (default: true)
   * @returns Decoded token containing user information
   * @throws Error if token is invalid or revoked
   */
  async verifyIdToken(idToken: string, checkRevoked: boolean = true): Promise<admin.auth.DecodedIdToken> {
    try {
      const decodedToken = await this.auth.verifyIdToken(idToken, checkRevoked);
      return decodedToken;
    } catch (error: any) {
      console.error('Token verification failed:', error.code, error.message);
      throw error;
    }
  }

  /**
   * Create a custom token for a user
   * Useful for server-side authentication flows
   *
   * @param uid - The user ID
   * @param additionalClaims - Optional custom claims to include in the token
   * @returns Custom token string
   */
  async createCustomToken(uid: string, additionalClaims?: object): Promise<string> {
    try {
      const customToken = await this.auth.createCustomToken(uid, additionalClaims);
      console.log(`✅ Custom token created for user: ${uid}`);
      return customToken;
    } catch (error: any) {
      console.error('Custom token creation failed:', error.message);
      throw new Error(`Failed to create custom token: ${error.message}`);
    }
  }

  /**
   * Get user by UID
   *
   * @param uid - The user ID
   * @returns UserRecord or null if not found
   */
  async getUserById(uid: string): Promise<UserRecord | null> {
    try {
      const userRecord = await this.auth.getUser(uid);
      return userRecord;
    } catch (error: any) {
      if (error.code === 'auth/user-not-found') {
        console.warn(`User not found: ${uid}`);
        return null;
      }
      console.error('Error fetching user:', error.message);
      throw error;
    }
  }

  /**
   * Get user by email address
   *
   * @param email - The user's email address
   * @returns UserRecord or null if not found
   */
  async getUserByEmail(email: string): Promise<UserRecord | null> {
    try {
      const userRecord = await this.auth.getUserByEmail(email);
      return userRecord;
    } catch (error: any) {
      if (error.code === 'auth/user-not-found') {
        console.warn(`User not found with email: ${email}`);
        return null;
      }
      console.error('Error fetching user by email:', error.message);
      throw error;
    }
  }

  /**
   * Create a new user
   *
   * @param email - User's email address
   * @param password - User's password
   * @param displayName - Optional display name
   * @param photoURL - Optional photo URL
   * @returns Created UserRecord
   */
  async createUser(
    email: string,
    password: string,
    displayName?: string,
    photoURL?: string
  ): Promise<UserRecord> {
    try {
      const userRecord = await this.auth.createUser({
        email,
        password,
        displayName,
        photoURL,
        emailVerified: false
      });

      console.log(`✅ User created successfully: ${userRecord.uid}`);
      return userRecord;
    } catch (error: any) {
      console.error('User creation failed:', error.message);
      throw new Error(`Failed to create user: ${error.message}`);
    }
  }

  /**
   * Update user information
   *
   * @param uid - User ID
   * @param updates - Properties to update
   * @returns Updated UserRecord
   */
  async updateUser(uid: string, updates: admin.auth.UpdateRequest): Promise<UserRecord> {
    try {
      const userRecord = await this.auth.updateUser(uid, updates);
      console.log(`✅ User updated successfully: ${uid}`);
      return userRecord;
    } catch (error: any) {
      console.error('User update failed:', error.message);
      throw new Error(`Failed to update user: ${error.message}`);
    }
  }

  /**
   * Delete a user
   *
   * @param uid - User ID to delete
   */
  async deleteUser(uid: string): Promise<void> {
    try {
      await this.auth.deleteUser(uid);
      console.log(`✅ User deleted successfully: ${uid}`);
    } catch (error: any) {
      console.error('User deletion failed:', error.message);
      throw new Error(`Failed to delete user: ${error.message}`);
    }
  }

  /**
   * Set custom claims for a user (e.g., roles, permissions)
   *
   * @param uid - User ID
   * @param claims - Custom claims object (e.g., { role: 'admin', subscriptionTier: 'premium' })
   */
  async setCustomClaims(uid: string, claims: object): Promise<void> {
    try {
      await this.auth.setCustomUserClaims(uid, claims);
      console.log(`✅ Custom claims set for user ${uid}:`, claims);
    } catch (error: any) {
      console.error('Setting custom claims failed:', error.message);
      throw new Error(`Failed to set custom claims: ${error.message}`);
    }
  }

  /**
   * Get custom claims for a user
   *
   * @param uid - User ID
   * @returns Custom claims object or null
   */
  async getCustomClaims(uid: string): Promise<Record<string, any> | null> {
    try {
      const userRecord = await this.getUserById(uid);
      return userRecord?.customClaims || null;
    } catch (error: any) {
      console.error('Getting custom claims failed:', error.message);
      throw error;
    }
  }

  /**
   * Set user role (convenience method for setting role claim)
   *
   * @param uid - User ID
   * @param role - Role to set (admin, editor, viewer)
   */
  async setUserRole(uid: string, role: 'admin' | 'editor' | 'viewer'): Promise<void> {
    try {
      const existingClaims = await this.getCustomClaims(uid) || {};
      await this.setCustomClaims(uid, { ...existingClaims, role });
      console.log(`✅ Role '${role}' set for user: ${uid}`);
    } catch (error: any) {
      console.error('Setting user role failed:', error.message);
      throw error;
    }
  }

  /**
   * Revoke all refresh tokens for a user
   * Forces user to re-authenticate
   *
   * @param uid - User ID
   */
  async revokeRefreshTokens(uid: string): Promise<void> {
    try {
      await this.auth.revokeRefreshTokens(uid);
      console.log(`✅ Refresh tokens revoked for user: ${uid}`);
    } catch (error: any) {
      console.error('Revoking refresh tokens failed:', error.message);
      throw new Error(`Failed to revoke refresh tokens: ${error.message}`);
    }
  }

  /**
   * Generate email verification link
   *
   * @param email - User's email address
   * @returns Email verification link
   */
  async generateEmailVerificationLink(email: string): Promise<string> {
    try {
      const actionCodeSettings = {
        url: process.env.EMAIL_VERIFICATION_REDIRECT_URL || `${process.env.FRONTEND_URL}/verify-email`,
        handleCodeInApp: false
      };

      const link = await this.auth.generateEmailVerificationLink(email, actionCodeSettings);
      console.log(`✅ Email verification link generated for: ${email}`);
      return link;
    } catch (error: any) {
      console.error('Generating email verification link failed:', error.message);
      throw new Error(`Failed to generate verification link: ${error.message}`);
    }
  }

  /**
   * Generate password reset link
   *
   * @param email - User's email address
   * @returns Password reset link
   */
  async generatePasswordResetLink(email: string): Promise<string> {
    try {
      const actionCodeSettings = {
        url: process.env.PASSWORD_RESET_REDIRECT_URL || `${process.env.FRONTEND_URL}/reset-password`,
        handleCodeInApp: false
      };

      const link = await this.auth.generatePasswordResetLink(email, actionCodeSettings);
      console.log(`✅ Password reset link generated for: ${email}`);
      return link;
    } catch (error: any) {
      console.error('Generating password reset link failed:', error.message);
      throw new Error(`Failed to generate reset link: ${error.message}`);
    }
  }

  /**
   * List all users (paginated)
   *
   * @param maxResults - Maximum number of users to return (default: 1000)
   * @param pageToken - Token for pagination
   * @returns List of users and next page token
   */
  async listUsers(maxResults: number = 1000, pageToken?: string): Promise<{
    users: UserRecord[];
    pageToken?: string;
  }> {
    try {
      const listUsersResult = await this.auth.listUsers(maxResults, pageToken);

      return {
        users: listUsersResult.users,
        pageToken: listUsersResult.pageToken
      };
    } catch (error: any) {
      console.error('Listing users failed:', error.message);
      throw new Error(`Failed to list users: ${error.message}`);
    }
  }

  /**
   * Verify session cookie
   * Alternative to ID tokens for session management
   *
   * @param sessionCookie - The session cookie to verify
   * @param checkRevoked - Whether to check if the session has been revoked
   * @returns Decoded session cookie
   */
  async verifySessionCookie(sessionCookie: string, checkRevoked: boolean = true): Promise<admin.auth.DecodedIdToken> {
    try {
      const decodedClaims = await this.auth.verifySessionCookie(sessionCookie, checkRevoked);
      return decodedClaims;
    } catch (error: any) {
      console.error('Session cookie verification failed:', error.message);
      throw error;
    }
  }

  /**
   * Create session cookie from ID token
   *
   * @param idToken - Firebase ID token
   * @param expiresIn - Session duration in milliseconds (max: 14 days)
   * @returns Session cookie string
   */
  async createSessionCookie(idToken: string, expiresIn: number): Promise<string> {
    try {
      // Max expiration is 14 days
      const maxExpiration = 14 * 24 * 60 * 60 * 1000; // 14 days in milliseconds
      const sessionDuration = Math.min(expiresIn, maxExpiration);

      const sessionCookie = await this.auth.createSessionCookie(idToken, { expiresIn: sessionDuration });
      console.log('✅ Session cookie created');
      return sessionCookie;
    } catch (error: any) {
      console.error('Session cookie creation failed:', error.message);
      throw new Error(`Failed to create session cookie: ${error.message}`);
    }
  }

  /**
   * Check if Firebase Admin SDK is initialized
   * @returns true if initialized
   */
  isInitialized(): boolean {
    return this.initialized;
  }
}

// Export singleton instance
export default new FirebaseAuthService();
