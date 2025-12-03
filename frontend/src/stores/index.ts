// ==========================================
// UI Store - Sidebar, Theme, Modals
// ==========================================
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UIState {
  sidebarOpen: boolean
  sidebarCollapsed: boolean
  theme: 'dark' | 'light'
  activeModal: string | null
  
  // Actions
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setTheme: (theme: 'dark' | 'light') => void
  openModal: (modalId: string) => void
  closeModal: () => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      sidebarCollapsed: false,
      theme: 'dark',
      activeModal: null,

      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      setTheme: (theme) => set({ theme }),
      openModal: (modalId) => set({ activeModal: modalId }),
      closeModal: () => set({ activeModal: null }),
    }),
    {
      name: 'geminivideo-ui',
    }
  )
)

// ==========================================
// Campaign Store - Campaign Builder State
// ==========================================
export interface Campaign {
  id: string
  name: string
  objective: 'conversions' | 'traffic' | 'awareness'
  budget: number
  platforms: string[]
  status: 'draft' | 'active' | 'paused' | 'completed'
  createdAt: string
  metrics?: {
    spend: number
    impressions: number
    clicks: number
    conversions: number
    roas: number
  }
}

interface CampaignWizardState {
  step: number
  name: string
  objective: string
  budget: number
  platforms: string[]
  targetAudience: string
  creativeStyle: string
  scriptTemplate: string
  hookStyle: string
  variants: number
  avatar: string | null
  schedule: Date | null
}

interface CampaignState {
  campaigns: Campaign[]
  activeCampaign: Campaign | null
  wizard: CampaignWizardState
  isLoading: boolean
  
  // Actions
  setCampaigns: (campaigns: Campaign[]) => void
  setActiveCampaign: (campaign: Campaign | null) => void
  updateWizard: (data: Partial<CampaignWizardState>) => void
  nextStep: () => void
  prevStep: () => void
  resetWizard: () => void
  setLoading: (loading: boolean) => void
}

const initialWizardState: CampaignWizardState = {
  step: 1,
  name: '',
  objective: '',
  budget: 1000,
  platforms: [],
  targetAudience: '',
  creativeStyle: 'ugc',
  scriptTemplate: '',
  hookStyle: '',
  variants: 3,
  avatar: null,
  schedule: null,
}

export const useCampaignStore = create<CampaignState>((set) => ({
  campaigns: [],
  activeCampaign: null,
  wizard: initialWizardState,
  isLoading: false,

  setCampaigns: (campaigns) => set({ campaigns }),
  setActiveCampaign: (campaign) => set({ activeCampaign: campaign }),
  updateWizard: (data) => set((state) => ({ wizard: { ...state.wizard, ...data } })),
  nextStep: () => set((state) => ({ wizard: { ...state.wizard, step: state.wizard.step + 1 } })),
  prevStep: () => set((state) => ({ wizard: { ...state.wizard, step: Math.max(1, state.wizard.step - 1) } })),
  resetWizard: () => set({ wizard: initialWizardState }),
  setLoading: (loading) => set({ isLoading: loading }),
}))

// ==========================================
// Job Store - Generation Queue & Progress
// ==========================================
export interface Job {
  id: string
  type: 'generate' | 'analyze' | 'render' | 'publish'
  name: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  progress: number
  currentStep?: string
  error?: string
  result?: any
  createdAt: string
  completedAt?: string
}

interface JobState {
  jobs: Job[]
  activeJob: Job | null
  
  // Actions
  addJob: (job: Job) => void
  updateJob: (id: string, updates: Partial<Job>) => void
  removeJob: (id: string) => void
  setActiveJob: (job: Job | null) => void
  clearCompleted: () => void
}

export const useJobStore = create<JobState>((set) => ({
  jobs: [],
  activeJob: null,

  addJob: (job) => set((state) => ({ jobs: [job, ...state.jobs] })),
  updateJob: (id, updates) => set((state) => ({
    jobs: state.jobs.map((j) => (j.id === id ? { ...j, ...updates } : j)),
  })),
  removeJob: (id) => set((state) => ({ jobs: state.jobs.filter((j) => j.id !== id) })),
  setActiveJob: (job) => set({ activeJob: job }),
  clearCompleted: () => set((state) => ({ jobs: state.jobs.filter((j) => j.status !== 'completed') })),
}))

// ==========================================
// Toast Store - Notifications
// ==========================================
export interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
}

interface ToastState {
  toasts: Toast[]
  
  // Actions
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
  clearToasts: () => void
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],

  addToast: (toast) => {
    const id = Math.random().toString(36).substr(2, 9)
    set((state) => ({ toasts: [...state.toasts, { ...toast, id }] }))
    
    // Auto remove after duration
    const duration = toast.duration ?? 5000
    if (duration > 0) {
      setTimeout(() => {
        set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }))
      }, duration)
    }
  },
  removeToast: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
  clearToasts: () => set({ toasts: [] }),
}))

// ==========================================
// User Store - Auth & Preferences
// ==========================================
export interface User {
  id: string
  name: string
  email: string
  avatar?: string
  role: 'admin' | 'user'
  preferences: {
    defaultPlatforms: string[]
    defaultBudget: number
    timezone: string
  }
}

interface UserState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  
  // Actions
  setUser: (user: User | null) => void
  updatePreferences: (preferences: Partial<User['preferences']>) => void
  logout: () => void
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,

      setUser: (user) => set({ user, isAuthenticated: !!user, isLoading: false }),
      updatePreferences: (preferences) => set((state) => ({
        user: state.user ? { ...state.user, preferences: { ...state.user.preferences, ...preferences } } : null,
      })),
      logout: () => set({ user: null, isAuthenticated: false }),
    }),
    {
      name: 'geminivideo-user',
    }
  )
)

// ==========================================
// Analytics Store - Metrics & Charts
// ==========================================
export interface AnalyticsData {
  date: string
  spend: number
  revenue: number
  impressions: number
  clicks: number
  conversions: number
  roas: number
}

interface AnalyticsState {
  dateRange: { start: Date; end: Date }
  data: AnalyticsData[]
  comparison: AnalyticsData[]
  isLoading: boolean
  
  // Actions
  setDateRange: (range: { start: Date; end: Date }) => void
  setData: (data: AnalyticsData[]) => void
  setComparison: (data: AnalyticsData[]) => void
  setLoading: (loading: boolean) => void
}

export const useAnalyticsStore = create<AnalyticsState>((set) => ({
  dateRange: {
    start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    end: new Date(),
  },
  data: [],
  comparison: [],
  isLoading: false,

  setDateRange: (range) => set({ dateRange: range }),
  setData: (data) => set({ data }),
  setComparison: (comparison) => set({ comparison }),
  setLoading: (loading) => set({ isLoading: loading }),
}))
