import React, { useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';

/**
 * Main Application Layout
 * Provides navigation sidebar and renders child routes via Outlet
 */

interface NavItem {
  path: string;
  label: string;
  icon: string;
  badge?: string;
}

const mainNavItems: NavItem[] = [
  { path: '/', label: 'Dashboard', icon: '🏠' },
  { path: '/campaigns', label: 'Campaigns', icon: '🚀' },
  { path: '/analytics', label: 'Analytics', icon: '📊' },
  { path: '/studio', label: 'Video Studio', icon: '🎬' },
  { path: '/studio/ai', label: 'AI Creative', icon: '✨' },
  { path: '/spy', label: 'Ad Spy', icon: '🔍' },
];

const toolNavItems: NavItem[] = [
  { path: '/library', label: 'Asset Library', icon: '📁' },
  { path: '/analysis', label: 'Analysis', icon: '🔬' },
  { path: '/compliance', label: 'Compliance', icon: '✅' },
  { path: '/render', label: 'Render Jobs', icon: '🎞️' },
];

const workflowNavItems: NavItem[] = [
  { path: '/testing', label: 'A/B Testing', icon: '🧪' },
  { path: '/workflow', label: 'Approvals', icon: '👥' },
  { path: '/batch', label: 'Batch Process', icon: '⚡' },
];

export function MainLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const location = useLocation();

  const NavSection = ({ title, items }: { title?: string; items: NavItem[] }) => (
    <div className="mb-6">
      {title && !sidebarCollapsed && (
        <h3 className="px-4 mb-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
          {title}
        </h3>
      )}
      <nav className="space-y-1">
        {items.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all ${
                isActive
                  ? 'bg-indigo-600 text-white'
                  : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
              } ${sidebarCollapsed ? 'justify-center' : ''}`
            }
          >
            <span className="text-lg">{item.icon}</span>
            {!sidebarCollapsed && (
              <>
                <span className="font-medium">{item.label}</span>
                {item.badge && (
                  <span className="ml-auto px-2 py-0.5 text-xs bg-indigo-500 rounded-full">
                    {item.badge}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </div>
  );

  return (
    <div className="min-h-screen bg-zinc-900 flex">
      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-full bg-zinc-950 border-r border-zinc-800 transition-all duration-300 z-50 ${
          sidebarCollapsed ? 'w-16' : 'w-64'
        }`}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-zinc-800">
          {!sidebarCollapsed && (
            <div className="flex items-center gap-2">
              <span className="text-2xl">🎬</span>
              <span className="font-bold text-white">GeminiVideo</span>
            </div>
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
          >
            {sidebarCollapsed ? '→' : '←'}
          </button>
        </div>

        {/* Navigation */}
        <div className="p-3 overflow-y-auto h-[calc(100vh-4rem)]">
          <NavSection items={mainNavItems} />
          <NavSection title="Tools" items={toolNavItems} />
          <NavSection title="Workflow" items={workflowNavItems} />

          {/* User/Settings at bottom */}
          <div className="absolute bottom-4 left-0 right-0 px-3">
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white'
                    : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
                } ${sidebarCollapsed ? 'justify-center' : ''}`
              }
            >
              <span className="text-lg">⚙️</span>
              {!sidebarCollapsed && <span className="font-medium">Settings</span>}
            </NavLink>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main
        className={`flex-1 transition-all duration-300 ${
          sidebarCollapsed ? 'ml-16' : 'ml-64'
        }`}
      >
        {/* Top Bar */}
        <header className="h-16 bg-zinc-950/50 border-b border-zinc-800 flex items-center justify-between px-6 sticky top-0 z-40 backdrop-blur-sm">
          <div className="flex items-center gap-4">
            {/* Breadcrumb based on current path */}
            <span className="text-zinc-400 text-sm">
              {location.pathname === '/'
                ? 'Dashboard'
                : location.pathname.split('/').filter(Boolean).join(' / ')}
            </span>
          </div>

          <div className="flex items-center gap-4">
            {/* Quick Actions */}
            <button className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors">
              + New Campaign
            </button>
            {/* User Avatar */}
            <div className="w-8 h-8 bg-zinc-700 rounded-full flex items-center justify-center text-sm">
              👤
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

export default MainLayout;
