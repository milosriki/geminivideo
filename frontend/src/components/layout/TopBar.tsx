import { useState } from 'react';
import { Bars3Icon } from '@heroicons/react/24/outline';
import { useSidebarStore } from '../../stores/sidebarStore';
import { useIsMobile } from '../../hooks';
import clsx from 'clsx';

export function TopBar() {
  const { toggle } = useSidebarStore();
  const isMobile = useIsMobile();
  const [searchQuery, setSearchQuery] = useState('');
  const [showUserMenu, setShowUserMenu] = useState(false);

  return (
    <header className={clsx(
      'h-16 bg-zinc-900 border-b border-zinc-800 flex items-center justify-between',
      // Responsive padding
      'px-3 sm:px-4 md:px-6'
    )}>
      {/* Left: Menu Toggle + Breadcrumbs */}
      <div className="flex items-center gap-2 sm:gap-4">
        {/* Hamburger Button - Always visible, especially on mobile */}
        <button
          onClick={toggle}
          className={clsx(
            'p-2 rounded-lg hover:bg-zinc-800 transition-colors text-zinc-400 hover:text-white',
            // Touch-friendly on mobile (min 44px)
            'min-h-[44px] min-w-[44px] flex items-center justify-center'
          )}
          aria-label="Toggle sidebar"
        >
          <Bars3Icon className="w-6 h-6" />
        </button>

        {/* Breadcrumbs - Hidden on mobile */}
        <nav className="hidden md:flex items-center gap-2 text-sm">
          <span className="text-zinc-500">Dashboard</span>
          <svg
            className="w-4 h-4 text-zinc-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
          <span className="text-zinc-300">Overview</span>
        </nav>
      </div>

      {/* Center: Search - Hidden on small mobile, visible on tablet+ */}
      <div className="flex-1 max-w-xl mx-4 hidden sm:block lg:mx-8">
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            placeholder="Search videos, projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={clsx(
              'w-full bg-zinc-800 border border-zinc-700 rounded-lg pl-10 pr-4',
              'text-sm text-white placeholder-zinc-500',
              'focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
              'transition-all',
              // Smaller padding on mobile
              'py-2 sm:py-2.5'
            )}
          />
          <kbd className="absolute right-3 top-1/2 -translate-y-1/2 hidden lg:inline-flex items-center gap-1 px-2 py-0.5 text-xs text-zinc-500 bg-zinc-700 rounded">
            <span>⌘</span>K
          </kbd>
        </div>
      </div>

      {/* Right: Notifications + User Menu */}
      <div className="flex items-center gap-1 sm:gap-2 md:gap-3">
        {/* Notifications */}
        <button className={clsx(
          'relative p-2 rounded-lg hover:bg-zinc-800 transition-colors text-zinc-400 hover:text-white',
          // Touch-friendly on mobile
          'min-h-[44px] min-w-[44px] flex items-center justify-center'
        )}>
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-emerald-500 rounded-full"></span>
        </button>

        {/* User Menu */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className={clsx(
              'flex items-center gap-2 sm:gap-3 p-1 sm:p-1.5 rounded-lg hover:bg-zinc-800 transition-colors',
              // Touch-friendly on mobile
              'min-h-[44px]'
            )}
          >
            <div className={clsx(
              'bg-gradient-to-br from-emerald-500 to-emerald-700 rounded-full',
              'flex items-center justify-center text-white font-medium',
              // Responsive avatar size
              'w-8 h-8 text-sm sm:w-9 sm:h-9'
            )}>
              U
            </div>
            <div className="hidden sm:block text-left">
              <p className="text-sm font-medium text-white">User</p>
              <p className="text-xs text-zinc-500">Pro Plan</p>
            </div>
            <svg
              className="w-4 h-4 text-zinc-500 hidden sm:block"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>

          {/* Dropdown */}
          {showUserMenu && (
            <>
              {/* Backdrop for mobile */}
              <div
                className="fixed inset-0 z-40 sm:hidden"
                onClick={() => setShowUserMenu(false)}
              />

              <div className={clsx(
                'absolute right-0 mt-2 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl py-1 z-50',
                // Full width on mobile, fixed width on desktop
                'w-screen sm:w-56',
                'max-w-xs'
              )}>
                <a
                  href="#"
                  className={clsx(
                    'flex items-center gap-3 px-4 py-3 sm:py-2 text-sm text-zinc-300',
                    'hover:bg-zinc-800 transition-colors',
                    // Touch-friendly on mobile
                    'min-h-[44px] sm:min-h-0'
                  )}
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>
                  Profile
                </a>
                <a
                  href="#"
                  className={clsx(
                    'flex items-center gap-3 px-4 py-3 sm:py-2 text-sm text-zinc-300',
                    'hover:bg-zinc-800 transition-colors',
                    // Touch-friendly on mobile
                    'min-h-[44px] sm:min-h-0'
                  )}
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  Settings
                </a>
                <hr className="my-1 border-zinc-800" />
                <a
                  href="#"
                  className={clsx(
                    'flex items-center gap-3 px-4 py-3 sm:py-2 text-sm text-red-400',
                    'hover:bg-zinc-800 transition-colors',
                    // Touch-friendly on mobile
                    'min-h-[44px] sm:min-h-0'
                  )}
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                    />
                  </svg>
                  Sign out
                </a>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
