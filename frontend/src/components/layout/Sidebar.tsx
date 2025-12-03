import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  HomeIcon,
  RocketLaunchIcon,
  FilmIcon,
  SparklesIcon,
  ChartBarIcon,
  MagnifyingGlassIcon,
  FolderIcon,
  Cog6ToothIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ArrowRightOnRectangleIcon,
  UserCircleIcon,
} from '@heroicons/react/24/outline';
import { useSidebarStore } from '../../stores/sidebarStore';
import { useIsMobile } from '../../hooks';
import clsx from 'clsx';
import { useState, useEffect } from 'react';

interface NavItem {
  name: string;
  path: string;
  icon: typeof HomeIcon;
}

const navItems: NavItem[] = [
  { name: 'Home', path: '/', icon: HomeIcon },
  { name: 'Campaigns', path: '/campaigns', icon: RocketLaunchIcon },
  { name: 'Studio', path: '/studio', icon: FilmIcon },
  { name: 'AI Studio', path: '/studio/ai', icon: SparklesIcon },
  { name: 'Analytics', path: '/analytics', icon: ChartBarIcon },
  { name: 'Ad Spy', path: '/spy', icon: MagnifyingGlassIcon },
  { name: 'Assets', path: '/assets', icon: FolderIcon },
  { name: 'Settings', path: '/settings', icon: Cog6ToothIcon },
];

export function Sidebar() {
  const { isOpen, toggle, close } = useSidebarStore();
  const location = useLocation();
  const navigate = useNavigate();
  const isMobile = useIsMobile();
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  // Close sidebar on mobile when route changes
  useEffect(() => {
    if (isMobile) {
      close();
    }
  }, [location.pathname, isMobile, close]);

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const handleLogout = () => {
    // TODO: Implement logout logic
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    // Close sidebar on mobile after navigation
    if (isMobile) {
      close();
    }
  };

  // On mobile, sidebar width is always full (256px) when open
  // On desktop, it can be collapsed to 64px
  const sidebarWidth = isMobile ? 256 : (isOpen ? 256 : 64);

  return (
    <>
      {/* Backdrop for mobile - only show when sidebar is open on mobile */}
      <AnimatePresence>
        {isMobile && isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/50 z-30 md:hidden"
            onClick={close}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{
          width: sidebarWidth,
          x: isMobile && !isOpen ? -256 : 0,
        }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className={clsx(
          'fixed left-0 top-0 h-full bg-zinc-900 border-r border-zinc-800 flex flex-col',
          isMobile ? 'z-40' : 'z-40'
        )}
      >
        {/* Logo Section */}
        <div className="h-16 flex items-center justify-center border-b border-zinc-800 relative px-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-emerald-500 to-emerald-700 rounded-lg flex items-center justify-center shrink-0">
              <svg
                className="w-5 h-5 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
            </div>
            <AnimatePresence>
              {(isOpen || isMobile) && (
                <motion.span
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: 'auto' }}
                  exit={{ opacity: 0, width: 0 }}
                  transition={{ duration: 0.2 }}
                  className="text-lg font-bold text-white whitespace-nowrap overflow-hidden"
                >
                  GeminiVideo
                </motion.span>
              )}
            </AnimatePresence>
          </div>

          {/* Toggle Button - Hidden on mobile */}
          {!isMobile && (
            <motion.button
              onClick={toggle}
              className={clsx(
                'absolute -right-3 top-1/2 -translate-y-1/2',
                'w-6 h-6 rounded-full bg-zinc-800 border border-zinc-700',
                'flex items-center justify-center',
                'hover:bg-zinc-700 transition-colors',
                'text-zinc-400 hover:text-white'
              )}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              {isOpen ? (
                <ChevronLeftIcon className="w-4 h-4" />
              ) : (
                <ChevronRightIcon className="w-4 h-4" />
              )}
            </motion.button>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4 px-2">
          <div className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              const showLabel = isOpen || isMobile;

              return (
                <div
                  key={item.path}
                  className="relative"
                  onMouseEnter={() => setHoveredItem(item.path)}
                  onMouseLeave={() => setHoveredItem(null)}
                >
                  <motion.button
                    onClick={() => handleNavigation(item.path)}
                    className={clsx(
                      'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg',
                      'transition-colors duration-200 relative overflow-hidden',
                      // Touch-friendly tap target on mobile (min 44px)
                      'min-h-[44px]',
                      active
                        ? 'bg-zinc-800 text-white'
                        : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200'
                    )}
                    whileHover={{ x: 2 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {/* Active indicator */}
                    {active && (
                      <motion.div
                        layoutId="activeIndicator"
                        className="absolute left-0 top-0 bottom-0 w-1 bg-indigo-500"
                        initial={false}
                        transition={{ duration: 0.3, ease: 'easeInOut' }}
                      />
                    )}

                    <Icon className={clsx('w-5 h-5 shrink-0', active && 'text-white')} />

                    <AnimatePresence>
                      {showLabel && (
                        <motion.span
                          initial={{ opacity: 0, width: 0 }}
                          animate={{ opacity: 1, width: 'auto' }}
                          exit={{ opacity: 0, width: 0 }}
                          transition={{ duration: 0.2 }}
                          className="text-sm font-medium whitespace-nowrap overflow-hidden"
                        >
                          {item.name}
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </motion.button>

                  {/* Tooltip when collapsed - only show on desktop */}
                  <AnimatePresence>
                    {!isMobile && !isOpen && hoveredItem === item.path && (
                      <motion.div
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -10 }}
                        transition={{ duration: 0.15 }}
                        className="absolute left-full top-1/2 -translate-y-1/2 ml-2 px-2 py-1 bg-zinc-800 border border-zinc-700 rounded-md shadow-lg z-50 whitespace-nowrap pointer-events-none"
                      >
                        <span className="text-xs font-medium text-white">
                          {item.name}
                        </span>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        </nav>

        {/* User Section */}
        <div className="border-t border-zinc-800 p-2">
          <div
            className={clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg',
              'hover:bg-zinc-800/50 transition-colors cursor-pointer',
              // Touch-friendly on mobile
              'min-h-[44px]'
            )}
          >
            <UserCircleIcon className="w-8 h-8 text-zinc-400 shrink-0" />
            <AnimatePresence>
              {(isOpen || isMobile) && (
                <motion.div
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: 'auto' }}
                  exit={{ opacity: 0, width: 0 }}
                  transition={{ duration: 0.2 }}
                  className="flex-1 min-w-0 overflow-hidden"
                >
                  <p className="text-sm font-medium text-zinc-300 truncate">
                    John Doe
                  </p>
                  <p className="text-xs text-zinc-500 truncate">john@example.com</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Logout Button */}
          <motion.button
            onClick={handleLogout}
            className={clsx(
              'w-full flex items-center gap-3 px-3 py-2.5 mt-1 rounded-lg',
              'text-zinc-400 hover:bg-red-500/10 hover:text-red-400',
              'transition-colors duration-200',
              // Touch-friendly on mobile
              'min-h-[44px]'
            )}
            whileHover={{ x: 2 }}
            whileTap={{ scale: 0.98 }}
          >
            <ArrowRightOnRectangleIcon className="w-5 h-5 shrink-0" />
            <AnimatePresence>
              {(isOpen || isMobile) && (
                <motion.span
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: 'auto' }}
                  exit={{ opacity: 0, width: 0 }}
                  transition={{ duration: 0.2 }}
                  className="text-sm font-medium whitespace-nowrap overflow-hidden"
                >
                  Logout
                </motion.span>
              )}
            </AnimatePresence>
          </motion.button>
        </div>
      </motion.aside>
    </>
  );
}
