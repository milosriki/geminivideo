import { Link } from 'react-router-dom'
import { Button } from '../components/salient/Button'
import { Logo } from '../components/salient/Logo'
import { SlimLayout } from '../components/salient/SlimLayout'

export default function NotFoundPage() {
  return (
    <SlimLayout>
      <div className="flex">
        <Link to="/" aria-label="Home">
          <Logo className="h-10 w-auto" />
        </Link>
      </div>

      {/* 404 Text with Gradient */}
      <div className="mt-20">
        <h1 className="text-8xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-purple-600 bg-clip-text text-transparent animate-pulse">
          404
        </h1>
      </div>

      {/* Error Title */}
      <h2 className="mt-6 text-3xl font-bold text-zinc-900">
        Page not found
      </h2>

      {/* Friendly Error Message */}
      <p className="mt-4 text-base text-zinc-600 leading-relaxed">
        Sorry, we couldn't find the page you're looking for. The page may have been moved,
        deleted, or never existed in the first place.
      </p>

      {/* Action Buttons */}
      <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:gap-6">
        <Button
          href="/"
          variant="solid"
          color="blue"
          className="shadow-lg hover:shadow-xl transition-shadow duration-300"
        >
          Go back home
        </Button>
        <Button
          href="/help"
          variant="outline"
          color="slate"
          className="transition-all duration-300"
        >
          Contact support
        </Button>
      </div>

      {/* Popular Links / Suggestions */}
      <div className="mt-12 pt-8 border-t border-zinc-200">
        <h3 className="text-sm font-semibold text-zinc-900 mb-4">
          Popular pages you might be looking for:
        </h3>
        <ul className="space-y-3">
          <li>
            <Link
              to="/projects"
              className="text-sm text-blue-600 hover:text-blue-700 hover:underline transition-colors duration-200 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              Projects Dashboard
            </Link>
          </li>
          <li>
            <Link
              to="/campaigns"
              className="text-sm text-blue-600 hover:text-blue-700 hover:underline transition-colors duration-200 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              Campaigns
            </Link>
          </li>
          <li>
            <Link
              to="/studio"
              className="text-sm text-blue-600 hover:text-blue-700 hover:underline transition-colors duration-200 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              Video Studio
            </Link>
          </li>
          <li>
            <Link
              to="/analytics"
              className="text-sm text-blue-600 hover:text-blue-700 hover:underline transition-colors duration-200 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              Analytics
            </Link>
          </li>
          <li>
            <Link
              to="/settings"
              className="text-sm text-blue-600 hover:text-blue-700 hover:underline transition-colors duration-200 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              Settings
            </Link>
          </li>
        </ul>
      </div>

      {/* Decorative Illustration - Animated Icons */}
      <div className="mt-12 flex justify-center gap-6 opacity-20">
        <div className="animate-bounce" style={{ animationDelay: '0s', animationDuration: '3s' }}>
          <svg className="w-8 h-8 text-purple-600" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth={2} fill="none" />
          </svg>
        </div>
        <div className="animate-bounce" style={{ animationDelay: '0.5s', animationDuration: '3s' }}>
          <svg className="w-8 h-8 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
            <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" />
          </svg>
        </div>
        <div className="animate-bounce" style={{ animationDelay: '1s', animationDuration: '3s' }}>
          <svg className="w-8 h-8 text-purple-600" fill="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth={2} fill="none" />
            <path d="M12 6v6l4 2" stroke="currentColor" strokeWidth={2} fill="none" />
          </svg>
        </div>
      </div>
    </SlimLayout>
  )
}
