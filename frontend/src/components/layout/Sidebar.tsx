import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { ChevronDown, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { useSidebarStore } from '../../stores/sidebarStore';
import { navigation, NavItem } from '../../config/navigation';

// Logo component
const Logo: React.FC<{ collapsed: boolean }> = ({ collapsed }) => (
  <div className="flex items-center h-16 px-4 border-b border-zinc-800">
    <div className="flex items-center gap-3">
      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center">
        <span className="text-white font-bold text-sm">G</span>
      </div>
      {!collapsed && (
        <span className="text-white font-semibold text-lg whitespace-nowrap">
          GeminiVideo
        </span>
      )}
    </div>
  </div>
);

// Navigation item component
const NavItemComponent: React.FC<{
  item: NavItem;
  collapsed: boolean;
  depth?: number;
}> = ({ item, collapsed, depth = 0 }) => {
  const location = useLocation();
  const { toggleSection, isExpanded } = useSidebarStore();
  const hasChildren = item.children && item.children.length > 0;
  const expanded = isExpanded(item.label);

  // Check if this item or any child is active
  const isActive = item.href === location.pathname;
  const isChildActive = item.children?.some(
    (child) => child.href === location.pathname ||
    child.children?.some((grandchild) => grandchild.href === location.pathname)
  );

  const Icon = item.icon;
  const paddingLeft = collapsed ? 'px-4' : depth === 0 ? 'px-4' : 'pl-12 pr-4';

  // Parent item with children
  if (hasChildren) {
    return (
      <div>
        <button
          onClick={() => toggleSection(item.label)}
          className={`
            w-full flex items-center gap-3 py-3 ${paddingLeft}
            text-zinc-300 hover:text-white hover:bg-zinc-800
            transition-all duration-200 group
            ${isChildActive ? 'text-white bg-zinc-800/50' : ''}
            ${collapsed ? 'justify-center' : 'justify-between'}
          `}
          title={collapsed ? item.label : undefined}
        >
          <div className="flex items-center gap-3">
            {Icon && (
              <Icon
                size={20}
                className={`flex-shrink-0 ${isChildActive ? 'text-emerald-500' : ''}`}
              />
            )}
            {!collapsed && (
              <span className="font-medium whitespace-nowrap">{item.label}</span>
            )}
          </div>
          {!collapsed && (
            <ChevronDown
              size={16}
              className={`
                transition-transform duration-200
                ${expanded ? 'rotate-180' : ''}
              `}
            />
          )}
        </button>

        {/* Nested children */}
        {!collapsed && expanded && (
          <div className="overflow-hidden">
            {item.children!.map((child) => (
              <NavItemComponent
                key={child.label}
                item={child}
                collapsed={collapsed}
                depth={depth + 1}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  // Leaf item with href
  if (item.href) {
    return (
      <NavLink
        to={item.href}
        className={({ isActive: linkActive }) => `
          flex items-center gap-3 py-2.5 ${paddingLeft}
          transition-all duration-200 group
          ${collapsed ? 'justify-center' : ''}
          ${linkActive
            ? 'text-white bg-emerald-500/20 border-r-2 border-emerald-500'
            : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
          }
        `}
        title={collapsed ? item.label : undefined}
      >
        {Icon && (
          <Icon
            size={depth > 0 ? 16 : 20}
            className={`flex-shrink-0 ${isActive ? 'text-emerald-500' : ''}`}
          />
        )}
        {!collapsed && (
          <span className={`whitespace-nowrap ${depth > 0 ? 'text-sm' : 'font-medium'}`}>
            {item.label}
          </span>
        )}
      </NavLink>
    );
  }

  return null;
};

// Collapse toggle button
const CollapseButton: React.FC<{ isOpen: boolean; onToggle: () => void }> = ({
  isOpen,
  onToggle
}) => (
  <button
    onClick={onToggle}
    className="
      w-full flex items-center justify-center gap-2 py-4
      text-zinc-400 hover:text-white hover:bg-zinc-800
      transition-all duration-200 border-t border-zinc-800
    "
    title={isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
  >
    {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
    {isOpen && <span className="text-sm">Collapse</span>}
  </button>
);

// Mobile overlay backdrop
const MobileBackdrop: React.FC<{ onClick: () => void }> = ({ onClick }) => (
  <div
    className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
    onClick={onClick}
  />
);

// Mobile close button
const MobileCloseButton: React.FC<{ onClick: () => void }> = ({ onClick }) => (
  <button
    onClick={onClick}
    className="
      absolute top-4 right-4 p-2
      text-zinc-400 hover:text-white hover:bg-zinc-800
      rounded-lg transition-all duration-200 lg:hidden
    "
  >
    <X size={20} />
  </button>
);

// Main Sidebar component
export const Sidebar: React.FC = () => {
  const { isOpen, isMobileOpen, toggle, setMobileOpen } = useSidebarStore();

  return (
    <>
      {/* Mobile backdrop */}
      {isMobileOpen && <MobileBackdrop onClick={() => setMobileOpen(false)} />}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 h-full z-50
          bg-zinc-900 border-r border-zinc-800
          flex flex-col
          transition-all duration-200 ease-in-out

          /* Mobile: full overlay */
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0

          /* Width based on state */
          ${isOpen ? 'w-64' : 'w-16'}
        `}
      >
        {/* Mobile close button */}
        {isMobileOpen && <MobileCloseButton onClick={() => setMobileOpen(false)} />}

        {/* Logo */}
        <Logo collapsed={!isOpen} />

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4 scrollbar-thin scrollbar-thumb-zinc-700">
          {navigation.map((item) => (
            <NavItemComponent
              key={item.label}
              item={item}
              collapsed={!isOpen}
            />
          ))}
        </nav>

        {/* Collapse toggle - desktop only */}
        <div className="hidden lg:block">
          <CollapseButton isOpen={isOpen} onToggle={toggle} />
        </div>
      </aside>

      {/* Spacer to push content - matches sidebar width */}
      <div
        className={`
          hidden lg:block flex-shrink-0
          transition-all duration-200
          ${isOpen ? 'w-64' : 'w-16'}
        `}
      />
    </>
  );
};

// Mobile menu trigger button (to be used in header)
export const MobileMenuButton: React.FC = () => {
  const { setMobileOpen } = useSidebarStore();

  return (
    <button
      onClick={() => setMobileOpen(true)}
      className="
        p-2 text-zinc-400 hover:text-white hover:bg-zinc-800
        rounded-lg transition-all duration-200 lg:hidden
      "
    >
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <line x1="3" y1="12" x2="21" y2="12" />
        <line x1="3" y1="6" x2="21" y2="6" />
        <line x1="3" y1="18" x2="21" y2="18" />
      </svg>
    </button>
  );
};

export default Sidebar;
