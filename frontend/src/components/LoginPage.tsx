import React, { useState, FormEvent } from 'react';
import { useAuth } from '../contexts/AuthContext';
import '../App.css';

/**
 * Login Page Component
 *
 * Provides UI for:
 * - Email/password login
 * - Google OAuth login
 * - Sign up
 * - Password reset
 * - Error handling and loading states
 */
export function LoginPage() {
  const {
    login,
    signup,
    loginWithGoogle,
    resetPassword,
    error,
    clearError
  } = useAuth();

  const [isSignUp, setIsSignUp] = useState(false);
  const [showResetPassword, setShowResetPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [displayName, setDisplayName] = useState('');

  // Validation errors
  const [validationError, setValidationError] = useState<string | null>(null);

  /**
   * Validate form inputs
   */
  const validateForm = (): boolean => {
    setValidationError(null);

    if (!email || !email.includes('@')) {
      setValidationError('Please enter a valid email address');
      return false;
    }

    if (!showResetPassword && !password) {
      setValidationError('Password is required');
      return false;
    }

    if (isSignUp) {
      if (password.length < 6) {
        setValidationError('Password must be at least 6 characters');
        return false;
      }

      if (password !== confirmPassword) {
        setValidationError('Passwords do not match');
        return false;
      }

      if (!displayName.trim()) {
        setValidationError('Display name is required');
        return false;
      }
    }

    return true;
  };

  /**
   * Handle email/password form submission
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setSuccessMessage(null);
    clearError();

    try {
      if (showResetPassword) {
        // Password reset
        await resetPassword(email);
        setSuccessMessage('Password reset email sent! Check your inbox.');
        setShowResetPassword(false);
        setEmail('');
      } else if (isSignUp) {
        // Sign up
        await signup(email, password, displayName);
        setSuccessMessage('Account created! Please check your email to verify your account.');

        // Redirect to dashboard after 2 seconds
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
      } else {
        // Login
        await login(email, password);

        // Redirect to dashboard
        window.location.href = '/';
      }
    } catch (err: any) {
      console.error('Authentication error:', err);
      // Error is handled by AuthContext
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle Google OAuth login
   */
  const handleGoogleLogin = async () => {
    setLoading(true);
    setSuccessMessage(null);
    clearError();

    try {
      await loginWithGoogle();

      // Redirect to dashboard
      window.location.href = '/';
    } catch (err: any) {
      console.error('Google login error:', err);
      // Error is handled by AuthContext
    } finally {
      setLoading(false);
    }
  };

  /**
   * Toggle between login and sign up
   */
  const toggleMode = () => {
    setIsSignUp(!isSignUp);
    setShowResetPassword(false);
    setValidationError(null);
    setSuccessMessage(null);
    clearError();

    // Clear form
    setEmail('');
    setPassword('');
    setConfirmPassword('');
    setDisplayName('');
  };

  /**
   * Toggle password reset view
   */
  const toggleResetPassword = () => {
    setShowResetPassword(!showResetPassword);
    setIsSignUp(false);
    setValidationError(null);
    setSuccessMessage(null);
    clearError();

    // Clear form
    setPassword('');
    setConfirmPassword('');
    setDisplayName('');
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        {/* Logo/Header */}
        <div style={styles.header}>
          <h1 style={styles.title}>
            {showResetPassword ? 'Reset Password' : isSignUp ? 'Create Account' : 'Welcome Back'}
          </h1>
          <p style={styles.subtitle}>
            {showResetPassword
              ? 'Enter your email to receive a password reset link'
              : isSignUp
              ? 'Sign up to start creating amazing videos'
              : 'Sign in to continue to GeminiVideo'}
          </p>
        </div>

        {/* Error Message */}
        {(error || validationError) && (
          <div style={styles.errorBox}>
            <span style={styles.errorIcon}>⚠️</span>
            <span>{error || validationError}</span>
          </div>
        )}

        {/* Success Message */}
        {successMessage && (
          <div style={styles.successBox}>
            <span style={styles.successIcon}>✅</span>
            <span>{successMessage}</span>
          </div>
        )}

        {/* Google Sign In Button */}
        {!showResetPassword && (
          <button
            onClick={handleGoogleLogin}
            disabled={loading}
            style={styles.googleButton}
            type="button"
          >
            <svg style={styles.googleIcon} viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            {loading ? 'Processing...' : 'Continue with Google'}
          </button>
        )}

        {/* Divider */}
        {!showResetPassword && (
          <div style={styles.divider}>
            <span style={styles.dividerLine}></span>
            <span style={styles.dividerText}>OR</span>
            <span style={styles.dividerLine}></span>
          </div>
        )}

        {/* Email/Password Form */}
        <form onSubmit={handleSubmit} style={styles.form}>
          {/* Email Input */}
          <div style={styles.inputGroup}>
            <label htmlFor="email" style={styles.label}>
              Email Address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              style={styles.input}
              disabled={loading}
              required
            />
          </div>

          {/* Display Name Input (Sign Up Only) */}
          {isSignUp && !showResetPassword && (
            <div style={styles.inputGroup}>
              <label htmlFor="displayName" style={styles.label}>
                Display Name
              </label>
              <input
                id="displayName"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="John Doe"
                style={styles.input}
                disabled={loading}
                required
              />
            </div>
          )}

          {/* Password Input */}
          {!showResetPassword && (
            <div style={styles.inputGroup}>
              <label htmlFor="password" style={styles.label}>
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                style={styles.input}
                disabled={loading}
                required
                minLength={6}
              />
            </div>
          )}

          {/* Confirm Password Input (Sign Up Only) */}
          {isSignUp && !showResetPassword && (
            <div style={styles.inputGroup}>
              <label htmlFor="confirmPassword" style={styles.label}>
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                style={styles.input}
                disabled={loading}
                required
                minLength={6}
              />
            </div>
          )}

          {/* Forgot Password Link */}
          {!isSignUp && !showResetPassword && (
            <div style={styles.forgotPassword}>
              <button
                type="button"
                onClick={toggleResetPassword}
                style={styles.linkButton}
                disabled={loading}
              >
                Forgot password?
              </button>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            style={{
              ...styles.submitButton,
              ...(loading ? styles.submitButtonDisabled : {})
            }}
          >
            {loading
              ? 'Processing...'
              : showResetPassword
              ? 'Send Reset Link'
              : isSignUp
              ? 'Create Account'
              : 'Sign In'}
          </button>
        </form>

        {/* Toggle Mode */}
        <div style={styles.footer}>
          {showResetPassword ? (
            <button
              type="button"
              onClick={toggleResetPassword}
              style={styles.linkButton}
              disabled={loading}
            >
              ← Back to Sign In
            </button>
          ) : (
            <>
              <span style={styles.footerText}>
                {isSignUp ? 'Already have an account?' : "Don't have an account?"}
              </span>
              <button
                type="button"
                onClick={toggleMode}
                style={styles.linkButton}
                disabled={loading}
              >
                {isSignUp ? 'Sign In' : 'Sign Up'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Inline styles for the component
 * In production, consider moving to CSS modules or styled-components
 */
const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    padding: '1rem'
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: '12px',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.1)',
    padding: '2.5rem',
    width: '100%',
    maxWidth: '440px'
  },
  header: {
    textAlign: 'center',
    marginBottom: '2rem'
  },
  title: {
    fontSize: '1.875rem',
    fontWeight: 'bold',
    color: '#1a202c',
    marginBottom: '0.5rem'
  },
  subtitle: {
    fontSize: '0.875rem',
    color: '#718096',
    marginTop: '0.5rem'
  },
  errorBox: {
    backgroundColor: '#fed7d7',
    border: '1px solid #fc8181',
    borderRadius: '6px',
    padding: '0.75rem',
    marginBottom: '1rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    color: '#c53030',
    fontSize: '0.875rem'
  },
  errorIcon: {
    fontSize: '1.125rem'
  },
  successBox: {
    backgroundColor: '#c6f6d5',
    border: '1px solid #68d391',
    borderRadius: '6px',
    padding: '0.75rem',
    marginBottom: '1rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    color: '#22543d',
    fontSize: '0.875rem'
  },
  successIcon: {
    fontSize: '1.125rem'
  },
  googleButton: {
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.75rem',
    padding: '0.75rem 1rem',
    backgroundColor: '#ffffff',
    border: '1px solid #e2e8f0',
    borderRadius: '6px',
    fontSize: '0.9375rem',
    fontWeight: '500',
    color: '#4a5568',
    cursor: 'pointer',
    transition: 'all 0.2s',
    marginBottom: '1rem'
  },
  googleIcon: {
    width: '20px',
    height: '20px'
  },
  divider: {
    display: 'flex',
    alignItems: 'center',
    margin: '1.5rem 0',
    gap: '0.75rem'
  },
  dividerLine: {
    flex: 1,
    height: '1px',
    backgroundColor: '#e2e8f0'
  },
  dividerText: {
    fontSize: '0.75rem',
    color: '#a0aec0',
    fontWeight: '500'
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem'
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem'
  },
  label: {
    fontSize: '0.875rem',
    fontWeight: '500',
    color: '#4a5568'
  },
  input: {
    padding: '0.75rem',
    border: '1px solid #e2e8f0',
    borderRadius: '6px',
    fontSize: '0.9375rem',
    transition: 'border-color 0.2s',
    outline: 'none'
  },
  forgotPassword: {
    textAlign: 'right',
    marginTop: '-0.5rem'
  },
  submitButton: {
    width: '100%',
    padding: '0.75rem 1rem',
    backgroundColor: '#667eea',
    color: '#ffffff',
    border: 'none',
    borderRadius: '6px',
    fontSize: '0.9375rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
    marginTop: '0.5rem'
  },
  submitButtonDisabled: {
    backgroundColor: '#a0aec0',
    cursor: 'not-allowed'
  },
  footer: {
    marginTop: '1.5rem',
    textAlign: 'center',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem'
  },
  footerText: {
    fontSize: '0.875rem',
    color: '#718096'
  },
  linkButton: {
    background: 'none',
    border: 'none',
    color: '#667eea',
    fontSize: '0.875rem',
    fontWeight: '500',
    cursor: 'pointer',
    textDecoration: 'none',
    padding: 0
  }
};

export default LoginPage;
