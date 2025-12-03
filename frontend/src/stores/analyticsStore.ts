import { create } from 'zustand';

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

      // TODO: Replace with actual API call
      // Example API call structure:
      // const response = await fetch(`/api/analytics${campaignId ? `/${campaignId}` : ''}`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     startDate: dateRange.start.toISOString(),
      //     endDate: dateRange.end.toISOString(),
      //   }),
      // });
      // const data = await response.json();

      // Mock data for now
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const mockMetrics: Metrics = {
        roas: 3.42,
        spend: 12543.00,
        revenue: 42876.00,
        impressions: 1245678,
        clicks: 23456,
        conversions: 1234,
        ctr: 1.88,
        cpc: 0.54,
        cpa: 10.17,
      };

      set({ metrics: mockMetrics, isLoading: false });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch analytics';
      set({ error: errorMessage, isLoading: false });
    }
  },
}));
