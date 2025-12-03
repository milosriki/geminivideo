import React, { useState, useCallback } from 'react';
import { KeyIcon, SparklesIcon } from './icons';
import { Link } from '@/components/catalyst/link';
import { Divider } from '@/components/catalyst/divider';
import { AuthLayout } from '@/components/catalyst/auth-layout';
import { SlimLayout } from '@/components/salient/SlimLayout';
import { TextField } from '@/components/salient/Fields';
import { Button as SalientButton } from '@/components/salient/Button';

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
                <SalientButton
                  outline
                  className="w-full gap-3"
                  onClick={handleGoogleLogin}
                  disabled={isLoading}
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
                </SalientButton>

                <div className="relative my-6">
                  <Divider />
                  <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-zinc-900 px-4 text-zinc-500 text-sm">
                    or continue with email
                  </span>
                </div>
              </>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'signup' && (
                <TextField
                  label="Full Name"
                  name="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="John Doe"
                  required
                />
              )}

              <TextField
                label="Email Address"
                name="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
              />

              {mode !== 'forgot' && (
                <TextField
                  label="Password"
                  name="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  minLength={8}
                />
              )}

              {mode === 'signup' && (
                <TextField
                  label="Confirm Password"
                  name="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm your password"
                  required
                />
              )}

              {mode === 'login' && (
                <div className="flex items-center justify-between text-sm">
                  <label className="flex items-center gap-2 text-gray-400">
                    <input type="checkbox" className="rounded bg-gray-800 border-gray-700" />
                    Remember me
                  </label>
                  <Link
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      setMode('forgot');
                    }}
                    className="text-indigo-400"
                  >
                    Forgot password?
                  </Link>
                </div>
              )}

              <SalientButton
                color="blue"
                type="submit"
                className="w-full"
                disabled={isLoading}
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
              </SalientButton>
            </form>

            {/* Mode Toggle */}
            <div className="mt-6 text-center text-sm text-gray-400">
              {mode === 'login' && (
                <>
                  Don't have an account?{' '}
                  <Link
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      setMode('signup');
                    }}
                    className="text-indigo-400 font-medium"
                  >
                    Sign up
                  </Link>
                </>
              )}
              {mode === 'signup' && (
                <>
                  Already have an account?{' '}
                  <Link
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      setMode('login');
                    }}
                    className="text-indigo-400 font-medium"
                  >
                    Sign in
                  </Link>
                </>
              )}
              {mode === 'forgot' && (
                <Link
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setMode('login');
                  }}
                  className="text-indigo-400 font-medium"
                >
                  Back to login
                </Link>
              )}
            </div>
          </div>

          {/* Terms */}
          {mode === 'signup' && (
            <p className="mt-6 text-center text-xs text-gray-500">
              By creating an account, you agree to our{' '}
              <Link href="#" className="text-indigo-400">Terms of Service</Link>
              {' '}and{' '}
              <Link href="#" className="text-indigo-400">Privacy Policy</Link>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
