import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role?: string;
  createdAt?: Date;
}

export interface UserState {
  user: User | null;
  isAuthenticated: boolean;
  credits: number;

  setUser: (user: User | null) => void;
  logout: () => void;
  updateCredits: (credits: number) => void;
  decrementCredits: (amount: number) => void;
  incrementCredits: (amount: number) => void;
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      credits: 0,

      setUser: (user) => set({
        user,
        isAuthenticated: user !== null,
      }),

      logout: () => set({
        user: null,
        isAuthenticated: false,
        credits: 0,
      }),

      updateCredits: (credits) => set({ credits }),

      decrementCredits: (amount) => set((state) => ({
        credits: Math.max(0, state.credits - amount),
      })),

      incrementCredits: (amount) => set((state) => ({
        credits: state.credits + amount,
      })),
    }),
    {
      name: 'user-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        credits: state.credits,
      }),
    }
  )
);
