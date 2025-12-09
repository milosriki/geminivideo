import { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth, UserRole } from '@/contexts/AuthContext';

/**
 * Protected Route Component Props
 */
interface ProtectedRouteProps {
  children: ReactNode;
  redirectTo?: string;
  requiredRoles?: UserRole[];
}

/**
 * Protected Route Component
 * Renders children only if user is authenticated
 * Redirects to login page otherwise
 *
 * @example
 * ```tsx
 * <ProtectedRoute>
 *   <Dashboard />
 * </ProtectedRoute>
 * ```
 *
 * @example With role-based access
 * ```tsx
 * <ProtectedRoute requiredRoles={[UserRole.ADMIN]}>
 *   <AdminPanel />
 * </ProtectedRoute>
 * ```
 */
export function ProtectedRoute({
  children,
  redirectTo = '/login',
  requiredRoles
}: ProtectedRouteProps) {
  const { currentUser, loading, hasRole } = useAuth();

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="h-12 w-12 rounded-full border-4 border-zinc-800 border-t-violet-500 animate-spin" />
          </div>
          <p className="text-zinc-400 text-sm">Authenticating...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!currentUser) {
    return <Navigate to={redirectTo} replace />;
  }

  // Check role requirements if specified
  if (requiredRoles && requiredRoles.length > 0) {
    if (!hasRole(...requiredRoles)) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="max-w-md p-8 text-center">
            <div className="mb-4">
              <svg
                className="mx-auto h-12 w-12 text-red-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Access Denied</h2>
            <p className="text-zinc-400 mb-4">
              You don't have permission to view this page.
            </p>
            <p className="text-sm text-zinc-500">
              Required roles: {requiredRoles.join(', ')}
            </p>
          </div>
        </div>
      );
    }
  }

  // User is authenticated and has required roles
  return <>{children}</>;
}
