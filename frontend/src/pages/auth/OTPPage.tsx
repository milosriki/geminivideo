import { useState, useRef, useEffect, KeyboardEvent, ChangeEvent, ClipboardEvent } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import { useAuth } from '@/contexts/AuthContext';
import { apiUrl } from '@/config/api';

interface OTPInputProps {
  length?: number;
  onComplete?: (otp: string) => void;
}

function OTPInput({ length = 6, onComplete }: OTPInputProps) {
  const [otp, setOtp] = useState<string[]>(new Array(length).fill(''));
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    // Auto-focus first input on mount
    if (inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, []);

  useEffect(() => {
    // Check if OTP is complete
    if (otp.every(digit => digit !== '') && onComplete) {
      onComplete(otp.join(''));
    }
  }, [otp, onComplete]);

  const handleChange = (index: number, e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;

    // Only allow single digit numbers
    if (value && !/^\d$/.test(value)) {
      return;
    }

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < length - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace') {
      e.preventDefault();

      const newOtp = [...otp];

      if (otp[index]) {
        // Clear current field
        newOtp[index] = '';
        setOtp(newOtp);
      } else if (index > 0) {
        // Move to previous field and clear it
        newOtp[index - 1] = '';
        setOtp(newOtp);
        inputRefs.current[index - 1]?.focus();
      }
    } else if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1]?.focus();
    } else if (e.key === 'ArrowRight' && index < length - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text/plain').trim();

    // Only allow digits
    const digits = pastedData.replace(/\D/g, '').slice(0, length);

    if (digits) {
      const newOtp = [...otp];
      digits.split('').forEach((digit, i) => {
        if (i < length) {
          newOtp[i] = digit;
        }
      });
      setOtp(newOtp);

      // Focus the next empty field or last field
      const nextIndex = Math.min(digits.length, length - 1);
      inputRefs.current[nextIndex]?.focus();
    }
  };

  const handleFocus = (index: number) => {
    inputRefs.current[index]?.select();
  };

  return (
    <div className="flex justify-center gap-2 sm:gap-3">
      {otp.map((digit, index) => (
        <input
          key={index}
          ref={el => inputRefs.current[index] = el}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={digit}
          onChange={(e) => handleChange(index, e)}
          onKeyDown={(e) => handleKeyDown(index, e)}
          onPaste={handlePaste}
          onFocus={() => handleFocus(index)}
          className={clsx(
            'relative flex h-14 w-11 sm:h-16 sm:w-14 items-center justify-center',
            'text-center text-2xl font-semibold',
            'bg-zinc-900 text-white',
            'border border-zinc-700 rounded-lg',
            'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'transition-all duration-200',
            'hover:border-zinc-600',
            digit && 'border-zinc-600'
          )}
          aria-label={`Digit ${index + 1}`}
        />
      ))}
    </div>
  );
}

export default function OTPPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentUser, getIdToken } = useAuth();
  const [isResending, setIsResending] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const email = location.state?.email || currentUser?.email || 'your email';

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleResendCode = async () => {
    if (countdown > 0) return;

    setIsResending(true);
    setError(null);

    try {
      const token = await getIdToken();
      const response = await fetch(apiUrl('/auth/otp/resend'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({ email })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to resend verification code');
      }

      setCountdown(60); // Start 60 second countdown
    } catch (error) {
      console.error('Failed to resend code:', error);
      setError(error instanceof Error ? error.message : 'Failed to resend verification code. Please try again.');
    } finally {
      setIsResending(false);
    }
  };

  const handleOTPComplete = async (otp: string) => {
    setIsVerifying(true);
    setError(null);

    try {
      const token = await getIdToken();
      const response = await fetch(apiUrl('/auth/otp/verify'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({ email, otp })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Invalid verification code');
      }

      const data = await response.json();

      // Navigate to onboarding or dashboard based on user status
      if (data.isNewUser) {
        navigate('/onboarding/welcome');
      } else {
        navigate('/');
      }
    } catch (error) {
      console.error('Failed to verify OTP:', error);
      setError(error instanceof Error ? error.message : 'Invalid verification code. Please try again.');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // OTP completion is handled by the OTPInput component
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Verify your email
          </h1>
          <p className="mt-3 text-sm leading-6 text-zinc-400">
            A 6-digit verification code has been sent to{' '}
            <span className="font-semibold text-white">{email}</span>
          </p>
        </div>

        {/* OTP Form */}
        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div>
            <label htmlFor="otp" className="sr-only">
              Enter one-time password
            </label>
            <OTPInput length={6} onComplete={handleOTPComplete} />
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-lg bg-red-900/20 border border-red-800 p-4">
              <div className="flex gap-3">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-red-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth="1.5"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                    />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Resend Code */}
          <div className="text-center">
            <p className="text-sm leading-6 text-zinc-400">
              Didn't receive a code?{' '}
              <button
                type="button"
                onClick={handleResendCode}
                disabled={countdown > 0 || isResending}
                className={clsx(
                  'font-semibold transition-colors',
                  countdown > 0 || isResending
                    ? 'text-zinc-600 cursor-not-allowed'
                    : 'text-white underline decoration-white/25 underline-offset-2 hover:decoration-white/50'
                )}
              >
                {isResending ? (
                  'Sending...'
                ) : countdown > 0 ? (
                  `Resend in ${countdown}s`
                ) : (
                  'Request new code'
                )}
              </button>
            </p>
          </div>

          {/* Verify Button */}
          <button
            type="submit"
            disabled={isVerifying}
            className={clsx(
              'flex w-full justify-center rounded-full px-3.5 py-2.5',
              'text-sm font-semibold text-white shadow-sm',
              'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
              'transition-all duration-200',
              isVerifying
                ? 'bg-zinc-700 cursor-not-allowed'
                : 'bg-zinc-800 hover:bg-zinc-700 focus-visible:outline-blue-500'
            )}
          >
            {isVerifying ? (
              <span className="flex items-center gap-2">
                <svg
                  className="animate-spin h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Verifying...
              </span>
            ) : (
              'Verify'
            )}
          </button>
        </form>

        {/* Back to Login */}
        <div className="text-center">
          <Link
            to="/login"
            className="text-sm font-semibold text-white hover:text-zinc-300 transition-colors"
          >
            Use a different email
          </Link>
        </div>

        {/* Additional Info */}
        <div className="mt-8 rounded-lg bg-zinc-900/50 border border-zinc-800 p-4">
          <div className="flex gap-3">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-blue-400"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
                />
              </svg>
            </div>
            <div className="flex-1">
              <p className="text-sm text-zinc-400">
                The verification code will expire in 10 minutes. Make sure to check your spam folder if you don't see it.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
