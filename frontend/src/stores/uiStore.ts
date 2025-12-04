import { create } from 'zustand';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

export interface UIState {
  theme: 'dark' | 'light';
  isMobileMenuOpen: boolean;
  activeModal: string | null;
  toasts: Toast[];
  setTheme: (theme: 'dark' | 'light') => void;
  toggleMobileMenu: () => void;
  openModal: (modalId: string) => void;
  closeModal: () => void;
  addToast: (message: string, type: ToastType) => void;
  removeToast: (id: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  theme: 'dark',
  isMobileMenuOpen: false,
  activeModal: null,
  toasts: [],

  setTheme: (theme) => set({ theme }),

  toggleMobileMenu: () => set((state) => ({
    isMobileMenuOpen: !state.isMobileMenuOpen
  })),

  openModal: (modalId) => set({ activeModal: modalId }),

  closeModal: () => set({ activeModal: null }),

  addToast: (message, type) => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    set((state) => ({
      toasts: [...state.toasts, { id, message, type }]
    }));

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((toast) => toast.id !== id)
      }));
    }, 5000);
  },

  removeToast: (id) => set((state) => ({
    toasts: state.toasts.filter((toast) => toast.id !== id)
  })),
}));
