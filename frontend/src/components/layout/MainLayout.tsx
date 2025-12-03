import { Outlet, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { useSidebarStore } from '../../stores/sidebarStore';
import { useIsMobile } from '../../hooks';
import { PageTransition } from '../ui/PageTransition';
import clsx from 'clsx';

export function MainLayout() {
  const { isOpen } = useSidebarStore();
  const isMobile = useIsMobile();
  const location = useLocation();

  // On mobile, no margin (sidebar is overlay)
  // On desktop, margin based on sidebar state
  const mainMargin = isMobile ? 'ml-0' : (isOpen ? 'ml-64' : 'ml-16');

  return (
    <div className="flex h-screen bg-zinc-950 overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div
        className={clsx(
          'flex-1 flex flex-col transition-all duration-300',
          mainMargin
        )}
      >
        <TopBar />
        <main className={clsx(
          'flex-1 overflow-auto',
          // Responsive padding
          'p-3 sm:p-4 md:p-6'
        )}>
          <AnimatePresence mode="wait">
            <PageTransition key={location.pathname}>
              <Outlet />
            </PageTransition>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
