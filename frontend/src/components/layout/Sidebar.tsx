// Placeholder Sidebar component - to be implemented by Agent 3
// This minimal version prevents build errors until the full Sidebar is ready

import { useSidebarStore } from '../../stores/sidebarStore';

export function Sidebar() {
  const { isOpen } = useSidebarStore();

  return (
    <aside
      className={`fixed left-0 top-0 h-full bg-zinc-900 border-r border-zinc-800 transition-all duration-300 z-40 ${isOpen ? 'w-56' : 'w-16'
        }`}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-center border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-emerald-500 to-emerald-700 rounded-lg flex items-center justify-center">
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
          {isOpen && (
            <span className="text-lg font-bold text-white">GeminiVideo</span>
          )}
        </div>
      </div>

      {/* Placeholder content - Agent 3 will add navigation */}
      <nav className="p-4">
        {isOpen ? (
          <p className="text-xs text-zinc-500">Navigation loading...</p>
        ) : null}
      </nav>
    </aside>
  );
}
