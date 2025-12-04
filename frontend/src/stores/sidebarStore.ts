import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SidebarState {
  isOpen: boolean;
  isMobileOpen: boolean;
  activeSection: string | null;
  expandedSections: string[];
  toggle: () => void;
  setMobileOpen: (open: boolean) => void;
  setActiveSection: (section: string | null) => void;
  toggleSection: (section: string) => void;
  isExpanded: (section: string) => boolean;
}

export const useSidebarStore = create<SidebarState>()(
  persist(
    (set, get) => ({
      isOpen: true,
      isMobileOpen: false,
      activeSection: null,
      expandedSections: ['Create', 'Studio'], // Default expanded sections

      toggle: () => set((state) => ({ isOpen: !state.isOpen })),

      setMobileOpen: (open) => set({ isMobileOpen: open }),

      setActiveSection: (section) => set({ activeSection: section }),

      toggleSection: (section) => set((state) => ({
        expandedSections: state.expandedSections.includes(section)
          ? state.expandedSections.filter((s) => s !== section)
          : [...state.expandedSections, section]
      })),

      isExpanded: (section) => get().expandedSections.includes(section),
    }),
    {
      name: 'sidebar-storage',
      partialize: (state) => ({
        isOpen: state.isOpen,
        expandedSections: state.expandedSections
      })
    }
  )
);
