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

export const LoginPageWrapper: React.FC<LoginPageWrapperProps> = () => {
  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingFallback />}>
        <LoginPage />
      </Suspense>
    </ErrorBoundary>
  );
};

export default LoginPageWrapper;
