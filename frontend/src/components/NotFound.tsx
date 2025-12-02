import React from 'react';
import { Link } from 'react-router-dom';

/**
 * 404 Not Found Page
 * Displayed when a route doesn't match any defined paths
 */
export function NotFound() {
  return (
    <div className="min-h-screen bg-zinc-900 flex flex-col items-center justify-center p-6">
      {/* Large 404 text */}
      <div className="relative">
        <h1 className="text-[150px] font-bold text-zinc-800 select-none">
          404
        </h1>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-6xl">🎬</span>
        </div>
      </div>

      {/* Message */}
      <h2 className="text-2xl font-semibold text-white mt-4">
        Page Not Found
      </h2>
      <p className="text-zinc-400 mt-2 text-center max-w-md">
        The page you're looking for doesn't exist or has been moved.
        Let's get you back on track.
      </p>

      {/* Action buttons */}
      <div className="mt-8 flex gap-4">
        <Link
          to="/"
          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors"
        >
          Go to Dashboard
        </Link>
        <button
          onClick={() => window.history.back()}
          className="px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-white font-medium rounded-lg border border-zinc-700 transition-colors"
        >
          Go Back
        </button>
      </div>

      {/* Quick links */}
      <div className="mt-12 text-center">
        <p className="text-zinc-500 text-sm mb-4">Quick Links</p>
        <div className="flex flex-wrap justify-center gap-4">
          <Link to="/campaigns" className="text-indigo-400 hover:text-indigo-300 text-sm">
            Campaigns
          </Link>
          <Link to="/analytics" className="text-indigo-400 hover:text-indigo-300 text-sm">
            Analytics
          </Link>
          <Link to="/studio" className="text-indigo-400 hover:text-indigo-300 text-sm">
            Video Studio
          </Link>
          <Link to="/spy" className="text-indigo-400 hover:text-indigo-300 text-sm">
            Ad Spy
          </Link>
          <Link to="/library" className="text-indigo-400 hover:text-indigo-300 text-sm">
            Asset Library
          </Link>
        </div>
      </div>
    </div>
  );
}

export default NotFound;
