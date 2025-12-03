import React, { Suspense } from 'react';
import { ErrorBoundary } from '../layout/ErrorBoundary';
import LoginPage from '../LoginPage';

const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen bg-gray-950">
    <div className="text-center">
      <svg className="animate-spin h-10 w-10 text-indigo-500 mx-auto mb-4" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <p className="text-gray-400">Loading...</p>
    </div>
  </div>
);

interface LoginPageWrapperProps {
  onLoginSuccess?: () => void;
}

export const LoginPageWrapper: React.FC<LoginPageWrapperProps> = ({ onLoginSuccess }) => {
  const handleLogin = async (credentials: { email: string; password: string }) => {
    // TODO: Implement actual login logic with Firebase/Auth service
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    onLoginSuccess?.();
  };

  const handleSignup = async (data: { email: string; password: string; name: string }) => {
    // TODO: Implement actual signup logic with Firebase/Auth service
    await new Promise(resolve => setTimeout(resolve, 1000));
    onLoginSuccess?.();
  };

  const handleForgotPassword = async (email: string) => {
    // TODO: Implement actual password reset logic
    await new Promise(resolve => setTimeout(resolve, 1000));
  };

  const handleGoogleLogin = async () => {
    // TODO: Implement Google OAuth login
    await new Promise(resolve => setTimeout(resolve, 1000));
    onLoginSuccess?.();
  };

  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingFallback />}>
        <LoginPage
          onLogin={handleLogin}
          onSignup={handleSignup}
          onForgotPassword={handleForgotPassword}
          onGoogleLogin={handleGoogleLogin}
        />
      </Suspense>
    </ErrorBoundary>
  );
};

export default LoginPageWrapper;
