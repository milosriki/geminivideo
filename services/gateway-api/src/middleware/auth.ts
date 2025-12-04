import { Request, Response, NextFunction } from 'express';
import { FirebaseAuthService } from '../services/firebase-auth';

/**
 * User role types for role-based access control (RBAC)
 */
export enum UserRole {
  ADMIN = 'admin',
  EDITOR = 'editor',
  VIEWER = 'viewer'
}

/**
 * Extended Express Request interface with authenticated user information
 */
export interface AuthenticatedRequest extends Request {
  user?: {
    uid: string;
    email: string | null;
    emailVerified: boolean;
    displayName: string | null;
    photoURL: string | null;
    role: UserRole;
    customClaims?: Record<string, any>;
  };
}

/**
 * Authentication error class for better error handling
 */
export class AuthenticationError extends Error {
  constructor(
    message: string,
    public statusCode: number = 401,
    public code: string = 'AUTH_ERROR'
  ) {
    super(message);
    this.name = 'AuthenticationError';
    Object.setPrototypeOf(this, AuthenticationError.prototype);
  }
}

/**
 * Firebase Authentication Service instance
 */
const authService = new FirebaseAuthService();

/**
 * Extract Bearer token from Authorization header
 * @param authHeader - The Authorization header value
 * @returns The extracted token or null
 */
function extractToken(authHeader: string | undefined): string | null {
  if (!authHeader) {
    return null;
  }

  const parts = authHeader.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Bearer') {
    return null;
  }

  return parts[1];
}

/**
 * Get user role from custom claims with fallback to viewer
 * @param customClaims - Firebase custom claims object
 * @returns UserRole
 */
function getUserRole(customClaims?: Record<string, any>): UserRole {
  if (!customClaims || !customClaims.role) {
    return UserRole.VIEWER; // Default role
  }

  const role = customClaims.role.toLowerCase();

  if (Object.values(UserRole).includes(role as UserRole)) {
    return role as UserRole;
  }

  return UserRole.VIEWER;
}

/**
 * Middleware to verify Firebase JWT token and attach user to request
 *
 * This middleware:
 * 1. Extracts the Bearer token from Authorization header
 * 2. Verifies the token with Firebase Admin SDK
 * 3. Attaches user information to the request object
 * 4. Handles token expiration and validation errors
 *
 * @param req - Express request object
 * @param res - Express response object
 * @param next - Express next function
 */
export async function authenticateUser(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  try {
    const token = extractToken(req.headers.authorization);

    if (!token) {
      throw new AuthenticationError(
        'No authentication token provided',
        401,
        'NO_TOKEN'
      );
    }

    // Verify the token with Firebase
    const decodedToken = await authService.verifyIdToken(token);

    // Get user details from Firebase
    const userRecord = await authService.getUserById(decodedToken.uid);

    if (!userRecord) {
      throw new AuthenticationError(
        'User not found',
        404,
        'USER_NOT_FOUND'
      );
    }

    // Extract role from custom claims
    const role = getUserRole(decodedToken);

    // Attach user information to request
    (req as AuthenticatedRequest).user = {
      uid: userRecord.uid,
      email: userRecord.email || null,
      emailVerified: userRecord.emailVerified,
      displayName: userRecord.displayName || null,
      photoURL: userRecord.photoURL || null,
      role: role,
      customClaims: decodedToken
    };

    next();
  } catch (error: any) {
    // Handle Firebase-specific errors
    if (error.code === 'auth/id-token-expired') {
      res.status(401).json({
        error: 'Token expired',
        code: 'TOKEN_EXPIRED',
        message: 'Your session has expired. Please login again.'
      });
      return;
    }

    if (error.code === 'auth/argument-error') {
      res.status(401).json({
        error: 'Invalid token format',
        code: 'INVALID_TOKEN',
        message: 'The authentication token is malformed.'
      });
      return;
    }

    if (error instanceof AuthenticationError) {
      res.status(error.statusCode).json({
        error: error.message,
        code: error.code
      });
      return;
    }

    // Log unexpected errors
    console.error('Authentication error:', error);

    res.status(401).json({
      error: 'Authentication failed',
      code: 'AUTH_FAILED',
      message: error.message || 'Unable to authenticate request'
    });
  }
}

/**
 * Middleware to require specific roles for route access
 *
 * Usage: requireRole(UserRole.ADMIN, UserRole.EDITOR)
 *
 * @param allowedRoles - Array of roles that can access the route
 * @returns Express middleware function
 */
export function requireRole(...allowedRoles: UserRole[]) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const user = (req as AuthenticatedRequest).user;

    if (!user) {
      res.status(401).json({
        error: 'Unauthorized',
        code: 'NO_USER',
        message: 'User not authenticated. Please use authenticateUser middleware first.'
      });
      return;
    }

    if (!allowedRoles.includes(user.role)) {
      res.status(403).json({
        error: 'Forbidden',
        code: 'INSUFFICIENT_PERMISSIONS',
        message: `This action requires one of the following roles: ${allowedRoles.join(', ')}`,
        requiredRoles: allowedRoles,
        currentRole: user.role
      });
      return;
    }

    next();
  };
}

/**
 * Optional authentication middleware
 * Attaches user if token is valid but doesn't require authentication
 * Useful for routes that have different behavior for authenticated vs unauthenticated users
 *
 * @param req - Express request object
 * @param res - Express response object
 * @param next - Express next function
 */
export async function optionalAuth(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  try {
    const token = extractToken(req.headers.authorization);

    if (!token) {
      // No token provided, continue without user
      return next();
    }

    // Try to verify token
    const decodedToken = await authService.verifyIdToken(token);
    const userRecord = await authService.getUserById(decodedToken.uid);

    if (userRecord) {
      const role = getUserRole(decodedToken);

      (req as AuthenticatedRequest).user = {
        uid: userRecord.uid,
        email: userRecord.email || null,
        emailVerified: userRecord.emailVerified,
        displayName: userRecord.displayName || null,
        photoURL: userRecord.photoURL || null,
        role: role,
        customClaims: decodedToken
      };
    }
  } catch (error) {
    // Silently fail for optional auth
    console.warn('Optional auth failed:', error);
  }

  next();
}

/**
 * Middleware to require email verification
 * Must be used after authenticateUser middleware
 *
 * @param req - Express request object
 * @param res - Express response object
 * @param next - Express next function
 */
export function requireEmailVerification(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const user = (req as AuthenticatedRequest).user;

  if (!user) {
    res.status(401).json({
      error: 'Unauthorized',
      code: 'NO_USER',
      message: 'User not authenticated'
    });
    return;
  }

  if (!user.emailVerified) {
    res.status(403).json({
      error: 'Email not verified',
      code: 'EMAIL_NOT_VERIFIED',
      message: 'Please verify your email address to access this resource'
    });
    return;
  }

  next();
}

/**
 * Helper function to check if user has any of the specified roles
 * @param user - The authenticated user
 * @param roles - Roles to check
 * @returns true if user has any of the roles
 */
export function hasRole(user: AuthenticatedRequest['user'], ...roles: UserRole[]): boolean {
  if (!user) return false;
  return roles.includes(user.role);
}

/**
 * Helper function to check if user is admin
 * @param user - The authenticated user
 * @returns true if user is admin
 */
export function isAdmin(user: AuthenticatedRequest['user']): boolean {
  return hasRole(user, UserRole.ADMIN);
}

/**
 * Helper function to check if user can edit
 * @param user - The authenticated user
 * @returns true if user is admin or editor
 */
export function canEdit(user: AuthenticatedRequest['user']): boolean {
  return hasRole(user, UserRole.ADMIN, UserRole.EDITOR);
}
