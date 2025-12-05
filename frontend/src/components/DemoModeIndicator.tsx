/**
 * Demo Mode Indicator Component
 *
 * Subtle badge shown in the UI when demo mode is active.
 * Designed for investor presentations.
 */

import { useDemoMode } from '@/hooks/useDemoMode';
import { BeakerIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface DemoModeIndicatorProps {
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
  showControls?: boolean;
}

export function DemoModeIndicator({
  position = 'bottom-right',
  showControls = true
}: DemoModeIndicatorProps) {
  const { enabled, showIndicator, toggleDemoMode, resetDemoData } = useDemoMode();

  if (!enabled || !showIndicator) {
    return null;
  }

  const positionClasses = {
    'top-left': 'top-4 left-4',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-right': 'bottom-4 right-4'
  };

  return (
    <div
      className={`fixed ${positionClasses[position]} z-50 flex items-center gap-2 group`}
    >
      {/* Main Badge */}
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-violet-500/10 border border-violet-500/30 backdrop-blur-sm">
        <BeakerIcon className="h-4 w-4 text-violet-400" />
        <span className="text-sm font-medium text-violet-300">Demo Mode</span>

        {showControls && (
          <button
            onClick={toggleDemoMode}
            className="ml-1 p-0.5 rounded hover:bg-violet-500/20 transition-colors"
            title="Exit demo mode"
          >
            <XMarkIcon className="h-3.5 w-3.5 text-violet-400" />
          </button>
        )}
      </div>

      {/* Extended Controls (shown on hover) */}
      {showControls && (
        <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <button
            onClick={resetDemoData}
            className="px-3 py-2 rounded-lg bg-zinc-800/80 border border-zinc-700 backdrop-blur-sm hover:bg-zinc-700/80 transition-colors"
            title="Reset demo data"
          >
            <span className="text-sm text-zinc-300">Reset Data</span>
          </button>
        </div>
      )}
    </div>
  );
}

/**
 * Inline Demo Badge (for use in page headers)
 */
export function DemoModeBadge() {
  const { enabled } = useDemoMode();

  if (!enabled) {
    return null;
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium bg-violet-500/10 border border-violet-500/30 text-violet-300">
      <BeakerIcon className="h-3 w-3" />
      Demo
    </span>
  );
}
