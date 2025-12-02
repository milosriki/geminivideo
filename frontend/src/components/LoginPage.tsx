import React, { useState, useCallback } from 'react';
import { KeyIcon, SparklesIcon } from './icons';

interface LoginPageProps {
  onLogin?: (credentials: { email: string; password: string }) => Promise<void>;
  onSignup?: (data: { email: string; password: string; name: string }) => Promise<void>;
  onForgotPassword?: (email: string) => Promise<void>;
  onGoogleLogin?: () => Promise<void>;
}

export const LoginPage: React.FC<LoginPageProps> = ({
  onLogin,
  onSignup,
  onForgotPassword,
  onGoogleLogin,
}) => {
  const [mode, setMode] = useState<'login' | 'signup' | 'forgot'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);
    setIsLoading(true);

    try {
      if (mode === 'login') {
        await onLogin?.({ email, password });
      } else if (mode === 'signup') {
        if (password !== confirmPassword) {
          throw new Error('Passwords do not match');
        }
        await onSignup?.({ email, password, name });
      } else if (mode === 'forgot') {
        await onForgotPassword?.(email);
        setSuccessMessage('Password reset instructions sent to your email');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [mode, email, password, confirmPassword, name, onLogin, onSignup, onForgotPassword]);

  const handleGoogleLogin = useCallback(async () => {
    setError(null);
    setIsLoading(true);
    try {
      await onGoogleLogin?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Google login failed');
    } finally {
      setIsLoading(false);
    }
  }, [onGoogleLogin]);

  return (
    <div className="min-h-screen bg-gray-950 flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:flex-1 bg-gradient-to-br from-indigo-900 via-purple-900 to-gray-900 p-12 flex-col justify-between">
        <div>
          <div className="flex items-center gap-3 mb-12">
            <div className="w-10 h-10 bg-white/10 backdrop-blur rounded-lg flex items-center justify-center">
              <SparklesIcon className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-white">GeminiVideo</span>
          </div>

          <div className="max-w-md">
            <h1 className="text-4xl font-bold text-white mb-4">
              AI-Powered Video Ads That Convert
            </h1>
            <p className="text-lg text-gray-300">
              Create, analyze, and optimize your video ad campaigns with the power of AI.
              Join thousands of marketers who have transformed their ad performance.
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="flex items-center gap-4 text-gray-300">
            <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center text-xl">
              1
            </div>
            <span>AI-powered creative generation</span>
          </div>
          <div className="flex items-center gap-4 text-gray-300">
            <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center text-xl">
              2
            </div>
            <span>Real-time performance analytics</span>
          </div>
          <div className="flex items-center gap-4 text-gray-300">
            <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center text-xl">
              3
            </div>
            <span>Competitor ad intelligence</span>
          </div>
        </div>

        <p className="text-gray-500 text-sm">
          Trusted by 10,000+ marketers worldwide
        </p>
      </div>

      {/* Right Panel - Auth Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-12">
            <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
              <SparklesIcon className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-white">GeminiVideo</span>
          </div>

          <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-8">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-white">
                {mode === 'login' && 'Welcome back'}
                {mode === 'signup' && 'Create an account'}
                {mode === 'forgot' && 'Reset password'}
              </h2>
              <p className="text-gray-400 mt-2">
                {mode === 'login' && 'Sign in to continue to your dashboard'}
                {mode === 'signup' && 'Start your free 14-day trial'}
                {mode === 'forgot' && 'Enter your email to reset your password'}
              </p>
            </div>

            {/* Error/Success Messages */}
            {error && (
              <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}
            {successMessage && (
              <div className="mb-4 p-3 bg-green-900/30 border border-green-700 rounded-lg text-green-400 text-sm">
                {successMessage}
              </div>
            )}

            {/* Google Login */}
            {mode !== 'forgot' && (
              <>
                <button
                  onClick={handleGoogleLogin}
                  disabled={isLoading}
                  className="w-full py-3 px-4 bg-white text-gray-900 rounded-lg font-medium flex items-center justify-center gap-3 hover:bg-gray-100 transition-colors disabled:opacity-50"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path
                      fill="currentColor"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="currentColor"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                  Continue with Google
                </button>

                <div className="relative my-6">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-700" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-4 bg-gray-900/50 text-gray-500">or continue with email</span>
                  </div>
                </div>
              </>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'signup' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={e => setName(e.target.value)}
                    placeholder="John Doe"
                    required
                    className="w-full px-4 py-3 bg-gray-800/60 border border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className="w-full px-4 py-3 bg-gray-800/60 border border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>

              {mode !== 'forgot' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    required
                    minLength={8}
                    className="w-full px-4 py-3 bg-gray-800/60 border border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
              )}

              {mode === 'signup' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)}
                    placeholder="Confirm your password"
                    required
                    className="w-full px-4 py-3 bg-gray-800/60 border border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
              )}

              {mode === 'login' && (
                <div className="flex items-center justify-between text-sm">
                  <label className="flex items-center gap-2 text-gray-400">
                    <input type="checkbox" className="rounded bg-gray-800 border-gray-700" />
                    Remember me
                  </label>
                  <button
                    type="button"
                    onClick={() => setMode('forgot')}
                    className="text-indigo-400 hover:text-indigo-300"
                  >
                    Forgot password?
                  </button>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Processing...
                  </>
                ) : (
                  <>
                    <KeyIcon className="w-5 h-5" />
                    {mode === 'login' && 'Sign In'}
                    {mode === 'signup' && 'Create Account'}
                    {mode === 'forgot' && 'Send Reset Link'}
                  </>
                )}
              </button>
            </form>

            {/* Mode Toggle */}
            <div className="mt-6 text-center text-sm text-gray-400">
              {mode === 'login' && (
                <>
                  Don't have an account?{' '}
                  <button
                    onClick={() => setMode('signup')}
                    className="text-indigo-400 hover:text-indigo-300 font-medium"
                  >
                    Sign up
                  </button>
                </>
              )}
              {mode === 'signup' && (
                <>
                  Already have an account?{' '}
                  <button
                    onClick={() => setMode('login')}
                    className="text-indigo-400 hover:text-indigo-300 font-medium"
                  >
                    Sign in
                  </button>
                </>
              )}
              {mode === 'forgot' && (
                <button
                  onClick={() => setMode('login')}
                  className="text-indigo-400 hover:text-indigo-300 font-medium"
                >
                  Back to login
                </button>
              )}
            </div>
          </div>

          {/* Terms */}
          {mode === 'signup' && (
            <p className="mt-6 text-center text-xs text-gray-500">
              By creating an account, you agree to our{' '}
              <a href="#" className="text-indigo-400 hover:underline">Terms of Service</a>
              {' '}and{' '}
              <a href="#" className="text-indigo-400 hover:underline">Privacy Policy</a>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
