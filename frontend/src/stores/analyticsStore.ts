import { create } from 'zustand';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export interface DateRange {
  start: Date;
  end: Date;
}

export interface Metrics {
  roas: number;
  spend: number;
  revenue: number;
  impressions: number;
  clicks: number;
  conversions: number;
  ctr?: number;
  cpc?: number;
  cpa?: number;
}

export interface AnalyticsState {
  dateRange: DateRange;
  metrics: Metrics;
  isLoading: boolean;
  error: string | null;

  setDateRange: (dateRange: DateRange) => void;
  setMetrics: (metrics: Metrics) => void;
  fetchAnalytics: (campaignId?: string) => Promise<void>;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
}

// Default date range: last 30 days
const getDefaultDateRange = (): DateRange => {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 30);
  return { start, end };
};

const initialMetrics: Metrics = {
  roas: 0,
  spend: 0,
  revenue: 0,
  impressions: 0,
  clicks: 0,
  conversions: 0,
  ctr: 0,
  cpc: 0,
  cpa: 0,
};

export const useAnalyticsStore = create<AnalyticsState>((set, get) => ({
  dateRange: getDefaultDateRange(),
  metrics: initialMetrics,
  isLoading: false,
  error: null,

  setDateRange: (dateRange) => set({ dateRange }),

  setMetrics: (metrics) => set({ metrics }),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  fetchAnalytics: async (campaignId) => {
    set({ isLoading: true, error: null });

    try {
      const { dateRange } = get();

      const endpoint = campaignId
        ? `${API_BASE_URL}/analytics/${campaignId}`
        : `${API_BASE_URL}/analytics`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          startDate: dateRange.start.toISOString(),
          endDate: dateRange.end.toISOString(),
        }),
      });

      if (!response.ok) {
        throw new Error('Data source not configured. Please configure analytics in the backend.');
      }

      const data = await response.json();
      set({ metrics: data, isLoading: false });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Data source not configured. Please configure analytics in the backend.';
      set({ error: errorMessage, isLoading: false, metrics: initialMetrics });
    }
  },
}));
