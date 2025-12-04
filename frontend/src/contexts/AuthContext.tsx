import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
  User,
  UserCredential,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
  sendPasswordResetEmail,
  sendEmailVerification,
  updateProfile,
  GoogleAuthProvider,
  updatePassword,
  reauthenticateWithCredential,
  EmailAuthProvider
} from 'firebase/auth';
import { auth } from '../firebaseConfig';

/**
 * User role types matching backend RBAC
 */
export enum UserRole {
  ADMIN = 'admin',
  EDITOR = 'editor',
  VIEWER = 'viewer'
}

/**
 * Extended user information with custom claims
 */
export interface AuthUser extends User {
  role?: UserRole;
  customClaims?: Record<string, any>;
}

/**
 * Authentication context state
 */
interface AuthContextType {
  currentUser: AuthUser | null;
  loading: boolean;
  error: string | null;

  // Email/Password Authentication
  login: (email: string, password: string) => Promise<UserCredential>;
  signup: (email: string, password: string, displayName?: string) => Promise<UserCredential>;
  logout: () => Promise<void>;

  // Google OAuth
  loginWithGoogle: () => Promise<UserCredential>;

  // Password Management
  resetPassword: (email: string) => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;

  // Profile Management
  updateUserProfile: (displayName?: string, photoURL?: string) => Promise<void>;
  sendVerificationEmail: () => Promise<void>;

  // Token Management
  getIdToken: (forceRefresh?: boolean) => Promise<string | null>;
  refreshToken: () => Promise<string | null>;

  // Role Helpers
  hasRole: (...roles: UserRole[]) => boolean;
  isAdmin: () => boolean;
  canEdit: () => boolean;

  // Clear error
  clearError: () => void;
}

/**
 * Create Authentication Context
 */
const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Hook to use authentication context
 * @throws Error if used outside AuthProvider
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * Authentication Provider Props
 */
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Authentication Provider Component
 * Wraps the application to provide authentication state and methods
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch and attach custom claims (including role) to user
   */
  const fetchCustomClaims = async (user: User): Promise<AuthUser> => {
    try {
      const idTokenResult = await user.getIdTokenResult();
      const customClaims = idTokenResult.claims;

      // Extract role from custom claims
      const role = customClaims.role as UserRole || UserRole.VIEWER;

      return {
        ...user,
        role,
        customClaims
      } as AuthUser;
    } catch (error) {
      console.error('Error fetching custom claims:', error);
      return {
        ...user,
        role: UserRole.VIEWER
      } as AuthUser;
    }
  };

  /**
   * Sign up with email and password
   */
  const signup = async (
    email: string,
    password: string,
    displayName?: string
  ): Promise<UserCredential> => {
    try {
      setError(null);
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);

      // Update display name if provided
      if (displayName && userCredential.user) {
        await updateProfile(userCredential.user, { displayName });
      }

      // Send verification email
      if (userCredential.user) {
        await sendEmailVerification(userCredential.user);
      }

      return userCredential;
    } catch (error: any) {
      const errorMessage = getAuthErrorMessage(error.code);
      setError(errorMessage);
      throw error;
    }
  };

  /**
   * Login with email and password
   */
  const login = async (email: string, password: string): Promise<UserCredential> => {
    try {
      setError(null);
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      return userCredential;
    } catch (error: any) {
      const errorMessage = getAuthErrorMessage(error.code);
      setError(errorMessage);
      throw error;
    }
  };

  /**
   * Login with Google OAuth
   */
  const loginWithGoogle = async (): Promise<UserCredential> => {
    try {
      setError(null);
      const provider = new GoogleAuthProvider();
      provider.addScope('profile');
      provider.addScope('email');

      const userCredential = await signInWithPopup(auth, provider);
      return userCredential;
    } catch (error: any) {
      const errorMessage = getAuthErrorMessage(error.code);
      setError(errorMessage);
      throw error;
    }
  };

  /**
   * Logout current user
   */
  const logout = async (): Promise<void> => {
    try {
      setError(null);
      await signOut(auth);
    } catch (error: any) {
      const errorMessage = getAuthErrorMessage(error.code);
      setError(errorMessage);
      throw error;
    }
  };

  /**
   * Send password reset email
   */
  const resetPassword = async (email: string): Promise<void> => {
    try {
      setError(null);
      await sendPasswordResetEmail(auth, email);
    } catch (error: any) {
      const errorMessage = getAuthErrorMessage(error.code);
      setError(errorMessage);
      throw error;
    }
  };

  /**
   * Change user password (requires re-authentication)
   */
  const changePassword = async (currentPassword: string, newPassword: string): Promise<void> => {
    try {
      setError(null);

      if (!currentUser || !currentUser.email) {
        throw new Error('No authenticated user found');
      }

      // Re-authenticate user
      const credential = EmailAuthProvider.credential(currentUser.email, currentPassword);
      await reauthenticateWithCredential(currentUser, credential);

      // Update password
      await updatePassword(currentUser, newPassword);
    } catch (error: any) {
      const errorMessage = getAuthErrorMessage(error.code);
      setError(errorMessage);
      throw error;
    }
  };

  /**
   * Update user profile
   */
  const updateUserProfile = async (displayName?: string, photoURL?: string): Promise<void> => {
    try {
      setError(null);

      if (!currentUser) {
        throw new Error('No authenticated user found');
      }

      const updates: { displayName?: string; photoURL?: string } = {};
      if (displayName !== undefined) updates.displayName = displayName;
      if (photoURL !== undefined) updates.photoURL = photoURL;

      await updateProfile(currentUser, updates);

      // Refresh user to get updated profile
      await currentUser.reload();
      const updatedUser = await fetchCustomClaims(auth.currentUser!);
      setCurrentUser(updatedUser);
    } catch (error: any) {
      const errorMessage = getAuthErrorMessage(error.code);
      setError(errorMessage);
      throw error;
    }
  };

  /**
   * Send email verification
   */
  const sendVerificationEmail = async (): Promise<void> => {
    try {
      setError(null);

      if (!currentUser) {
        throw new Error('No authenticated user found');
      }

      await sendEmailVerification(currentUser);
    } catch (error: any) {
      const errorMessage = getAuthErrorMessage(error.code);
      setError(errorMessage);
      throw error;
    }
  };

  /**
   * Get ID token for API requests
   */
  const getIdToken = async (forceRefresh: boolean = false): Promise<string | null> => {
    try {
      if (!currentUser) {
        return null;
      }

      const token = await currentUser.getIdToken(forceRefresh);
      return token;
    } catch (error) {
      console.error('Error getting ID token:', error);
      return null;
    }
  };

  /**
   * Force refresh ID token
   */
  const refreshToken = async (): Promise<string | null> => {
    try {
      if (!currentUser) {
        return null;
      }

      const token = await currentUser.getIdToken(true);

      // Refresh custom claims
      const updatedUser = await fetchCustomClaims(currentUser);
      setCurrentUser(updatedUser);

      return token;
    } catch (error) {
      console.error('Error refreshing token:', error);
      return null;
    }
  };

  /**
   * Check if current user has any of the specified roles
   */
  const hasRole = (...roles: UserRole[]): boolean => {
    if (!currentUser || !currentUser.role) {
      return false;
    }
    return roles.includes(currentUser.role);
  };

  /**
   * Check if current user is admin
   */
  const isAdmin = (): boolean => {
    return hasRole(UserRole.ADMIN);
  };

  /**
   * Check if current user can edit
   */
  const canEdit = (): boolean => {
    return hasRole(UserRole.ADMIN, UserRole.EDITOR);
  };

  /**
   * Clear error state
   */
  const clearError = (): void => {
    setError(null);
  };

  /**
   * Listen to authentication state changes
   */
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (user) {
        // User is signed in
        const authUser = await fetchCustomClaims(user);
        setCurrentUser(authUser);
      } else {
        // User is signed out
        setCurrentUser(null);
      }
      setLoading(false);
    });

    // Cleanup subscription
    return unsubscribe;
  }, []);

  /**
   * Refresh token periodically (every 55 minutes)
   * Firebase tokens expire after 1 hour
   */
  useEffect(() => {
    if (!currentUser) return;

    const refreshInterval = setInterval(async () => {
      try {
        await refreshToken();
        // console.log('🔄 Token refreshed successfully');
      } catch (error) {
        console.error('Token refresh failed:', error);
      }
    }, 55 * 60 * 1000); // 55 minutes

    return () => clearInterval(refreshInterval);
  }, [currentUser]);

  const value: AuthContextType = {
    currentUser,
    loading,
    error,
    login,
    signup,
    logout,
    loginWithGoogle,
    resetPassword,
    changePassword,
    updateUserProfile,
    sendVerificationEmail,
    getIdToken,
    refreshToken,
    hasRole,
    isAdmin,
    canEdit,
    clearError
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Protected Route Component
 * Renders children only if user is authenticated
 * Redirects to login page otherwise
 */
interface ProtectedRouteProps {
  children: ReactNode;
  redirectTo?: string;
  requiredRoles?: UserRole[];
  fallback?: ReactNode;
}

export function ProtectedRoute({
  children,
  redirectTo = '/login',
  requiredRoles,
  fallback
}: ProtectedRouteProps) {
  const { currentUser, loading, hasRole } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div>Loading...</div>
      </div>
    );
  }

  if (!currentUser) {
    // Redirect to login (in a real app, use react-router)
    if (typeof window !== 'undefined') {
      window.location.href = redirectTo;
    }
    return fallback || null;
  }

  // Check role requirements
  if (requiredRoles && requiredRoles.length > 0) {
    if (!hasRole(...requiredRoles)) {
      return (
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <h2>Access Denied</h2>
          <p>You don't have permission to view this page.</p>
          <p>Required roles: {requiredRoles.join(', ')}</p>
        </div>
      );
    }
  }

  return <>{children}</>;
}

/**
 * Convert Firebase auth error codes to user-friendly messages
 */
function getAuthErrorMessage(errorCode: string): string {
  const errorMessages: Record<string, string> = {
    'auth/email-already-in-use': 'This email address is already registered.',
    'auth/invalid-email': 'Invalid email address format.',
    'auth/operation-not-allowed': 'This operation is not allowed.',
    'auth/weak-password': 'Password is too weak. Please use a stronger password.',
    'auth/user-disabled': 'This account has been disabled.',
    'auth/user-not-found': 'No account found with this email address.',
    'auth/wrong-password': 'Incorrect password.',
    'auth/invalid-credential': 'Invalid credentials provided.',
    'auth/too-many-requests': 'Too many failed attempts. Please try again later.',
    'auth/network-request-failed': 'Network error. Please check your connection.',
    'auth/requires-recent-login': 'This operation requires recent authentication. Please login again.',
    'auth/popup-closed-by-user': 'Sign-in popup was closed before completing.',
    'auth/cancelled-popup-request': 'Only one popup request is allowed at a time.',
    'auth/popup-blocked': 'Sign-in popup was blocked by the browser.'
  };

  return errorMessages[errorCode] || 'An unexpected error occurred. Please try again.';
}
