import React from 'react';


/**
 * Full-page loading screen with animated spinner
 * Used as Suspense fallback during lazy component loading
 */
export function LoadingScreen() {
  return (
    <div className="min-h-screen bg-zinc-900 flex flex-col items-center justify-center">
      {/* Animated Spinner */}
      <div className="relative">
        {/* Outer ring */}
        <div className="w-16 h-16 border-4 border-zinc-700 rounded-full" />
        {/* Spinning gradient arc */}
        <div className="absolute top-0 left-0 w-16 h-16 border-4 border-transparent border-t-indigo-500 border-r-indigo-500 rounded-full animate-spin" />
        {/* Inner glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-indigo-500/20 rounded-full blur-md" />
      </div>

      {/* Loading text */}
      <div className="mt-6 text-zinc-400 text-sm font-medium tracking-wide">
        Loading...
      </div>

      {/* Subtle animated dots */}
      <div className="mt-2 flex gap-1">
        <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  );
}

export default LoadingScreen;

