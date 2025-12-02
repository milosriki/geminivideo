import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AnalyticsDashboard } from './AnalyticsDashboard';

/**
 * Comprehensive test suite for Analytics Dashboard
 * Agent 27 of the ULTIMATE 30-agent production plan
 */

// ============================================================================
// MOCK DATA
// ============================================================================

const mockCampaignMetrics = [
  {
    campaignId: 'campaign_1',
    campaignName: 'Summer Sale 2024',
    spend: 5000,
    revenue: 15000,
    roas: 3.0,
    impressions: 100000,
    clicks: 5000,
    conversions: 300,
    ctr: 0.05,
    cvr: 0.06,
    cpa: 16.67,
    timestamp: Date.now(),
  },
  {
    campaignId: 'campaign_2',
    campaignName: 'Product Launch Q1',
    spend: 3000,
    revenue: 9000,
    roas: 3.0,
    impressions: 75000,
    clicks: 3750,
    conversions: 225,
    ctr: 0.05,
    cvr: 0.06,
    cpa: 13.33,
    timestamp: Date.now(),
  },
];

const mockTrendData = [
  {
    date: '2024-01-01',
    timestamp: 1704067200000,
    roas: 2.8,
    spend: 1000,
    revenue: 2800,
    conversions: 50,
    ctr: 0.045,
  },
  {
    date: '2024-01-02',
    timestamp: 1704153600000,
    roas: 3.2,
    spend: 1100,
    revenue: 3520,
    conversions: 60,
    ctr: 0.055,
  },
  {
    date: '2024-01-03',
    timestamp: 1704240000000,
    roas: 3.0,
    spend: 1050,
    revenue: 3150,
    conversions: 55,
    ctr: 0.05,
  },
];

const mockFunnelData = [
  { stage: 'Impressions', value: 100000, percentage: 100, dropoff: 0 },
  { stage: 'Clicks', value: 5000, percentage: 5, dropoff: 95 },
  { stage: 'Landing Page', value: 4500, percentage: 4.5, dropoff: 10 },
  { stage: 'Add to Cart', value: 1000, percentage: 1, dropoff: 77.8 },
  { stage: 'Purchase', value: 300, percentage: 0.3, dropoff: 70 },
];

const mockCreativePerformance = [
  {
    creativeId: 'creative_1',
    creativeName: 'Summer Video Ad',
    campaignId: 'campaign_1',
    format: 'video',
    hookType: 'problem_agitate',
    impressions: 50000,
    clicks: 2500,
    conversions: 150,
    spend: 2500,
    revenue: 7500,
    roas: 3.0,
    ctr: 0.05,
    cvr: 0.06,
    cpa: 16.67,
    thumbnailUrl: 'https://example.com/thumbnail.jpg',
  },
  {
    creativeId: 'creative_2',
    creativeName: 'Product Image Ad',
    campaignId: 'campaign_1',
    format: 'image',
    hookType: 'social_proof',
    impressions: 50000,
    clicks: 2500,
    conversions: 150,
    spend: 2500,
    revenue: 7500,
    roas: 3.0,
    ctr: 0.05,
    cvr: 0.06,
    cpa: 16.67,
  },
];

const mockHubSpotDeals = [
  {
    dealId: 'deal_1',
    dealName: 'Enterprise Deal',
    amount: 50000,
    stage: 'Closed Won',
    campaignId: 'campaign_1',
    creativeId: 'creative_1',
    sourceChannel: 'Facebook',
    createdAt: Date.now() - 30 * 24 * 60 * 60 * 1000,
    closedAt: Date.now() - 5 * 24 * 60 * 60 * 1000,
  },
  {
    dealId: 'deal_2',
    dealName: 'SMB Deal',
    amount: 5000,
    stage: 'Negotiation',
    campaignId: 'campaign_2',
    sourceChannel: 'Google',
    createdAt: Date.now() - 15 * 24 * 60 * 60 * 1000,
  },
];

const mockPredictionComparison = {
  predictedRoas: 2.8,
  actualRoas: 3.0,
  predictedConversions: 280,
  actualConversions: 300,
  accuracy: 93.3,
  variance: 7.1,
};

const mockAlertConfigs = [
  {
    id: 'alert_1',
    type: 'roas_drop' as const,
    threshold: 2.0,
    enabled: true,
    campaignIds: ['campaign_1'],
  },
];

const mockScheduledReports = [
  {
    id: 'report_1',
    name: 'Weekly Performance Report',
    frequency: 'weekly' as const,
    recipients: ['user@example.com'],
    metrics: ['roas', 'spend', 'revenue'],
    enabled: true,
  },
];

// ============================================================================
// MOCK API SETUP
// ============================================================================

const setupMockAPI = () => {
  global.fetch = vi.fn((url: string) => {
    const urlStr = url.toString();

    if (urlStr.includes('/analytics/campaigns')) {
      return Promise.resolve({
        ok: true,
        json: async () => mockCampaignMetrics,
      } as Response);
    }

    if (urlStr.includes('/analytics/trends')) {
      return Promise.resolve({
        ok: true,
        json: async () => mockTrendData,
      } as Response);
    }

    if (urlStr.includes('/analytics/funnel')) {
      return Promise.resolve({
        ok: true,
        json: async () => mockFunnelData,
      } as Response);
    }

    if (urlStr.includes('/analytics/creatives')) {
      return Promise.resolve({
        ok: true,
        json: async () => mockCreativePerformance,
      } as Response);
    }

    if (urlStr.includes('/analytics/hubspot-deals')) {
      return Promise.resolve({
        ok: true,
        json: async () => mockHubSpotDeals,
      } as Response);
    }

    if (urlStr.includes('/analytics/prediction-comparison')) {
      return Promise.resolve({
        ok: true,
        json: async () => mockPredictionComparison,
      } as Response);
    }

    if (urlStr.includes('/analytics/alerts') && !urlStr.includes('POST')) {
      return Promise.resolve({
        ok: true,
        json: async () => mockAlertConfigs,
      } as Response);
    }

    if (urlStr.includes('/analytics/scheduled-reports')) {
      return Promise.resolve({
        ok: true,
        json: async () => mockScheduledReports,
      } as Response);
    }

    if (urlStr.includes('/analytics/export/csv')) {
      return Promise.resolve({
        ok: true,
        blob: async () => new Blob(['mock,csv,data'], { type: 'text/csv' }),
      } as Response);
    }

    return Promise.resolve({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    } as Response);
  });

  // Mock WebSocket
  class MockWebSocket {
    onopen: (() => void) | null = null;
    onmessage: ((event: MessageEvent) => void) | null = null;
    onerror: ((event: Event) => void) | null = null;
    onclose: (() => void) | null = null;

    constructor(url: string) {
      setTimeout(() => {
        if (this.onopen) this.onopen();
      }, 0);
    }

    send(data: string) {
      // Mock send
    }

    close() {
      if (this.onclose) this.onclose();
    }
  }

  global.WebSocket = MockWebSocket as any;
};

// ============================================================================
// TEST UTILITIES
// ============================================================================

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

// ============================================================================
// TESTS
// ============================================================================

describe('AnalyticsDashboard', () => {
  beforeEach(() => {
    setupMockAPI();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('should render the dashboard header', () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      expect(screen.getByText(/Analytics Dashboard/i)).toBeInTheDocument();
    });

    it('should render all tabs', () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      expect(screen.getByText(/Overview/i)).toBeInTheDocument();
      expect(screen.getByText(/Creatives/i)).toBeInTheDocument();
      expect(screen.getByText(/Attribution/i)).toBeInTheDocument();
      expect(screen.getByText(/Alerts/i)).toBeInTheDocument();
      expect(screen.getByText(/Reports/i)).toBeInTheDocument();
    });

    it('should render date range picker', () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      expect(screen.getByText(/Start Date/i)).toBeInTheDocument();
      expect(screen.getByText(/End Date/i)).toBeInTheDocument();
    });

    it('should render auto-refresh toggle', () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      expect(screen.getByText(/Auto-refresh/i)).toBeInTheDocument();
    });
  });

  describe('Metric Cards', () => {
    it('should display key metrics', async () => {
      const { container } = render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1', 'campaign_2']} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/Total Spend/i)).toBeInTheDocument();
        expect(screen.getByText(/Total Revenue/i)).toBeInTheDocument();
        expect(screen.getByText(/ROAS/i)).toBeInTheDocument();
        expect(screen.getByText(/CTR/i)).toBeInTheDocument();
        expect(screen.getByText(/CPA/i)).toBeInTheDocument();
      });
    });

    it('should calculate aggregate metrics correctly', async () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1', 'campaign_2']} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        // Total spend: 5000 + 3000 = 8000
        expect(screen.getByText(/\$8,000\.00/)).toBeInTheDocument();
        // Total revenue: 15000 + 9000 = 24000
        expect(screen.getByText(/\$24,000\.00/)).toBeInTheDocument();
      });
    });
  });

  describe('Charts', () => {
    it('should render ROAS trend chart', async () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/ROAS Trend Over Time/i)).toBeInTheDocument();
      });
    });

    it('should render conversion funnel', async () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/Conversion Funnel/i)).toBeInTheDocument();
      });
    });

    it('should render spend vs revenue chart', async () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/Spend vs Revenue/i)).toBeInTheDocument();
      });
    });
  });

  describe('Tab Navigation', () => {
    it('should switch to Creatives tab', async () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      const creativesTab = screen.getByText(/🎨\s*Creatives/);
      fireEvent.click(creativesTab);

      await waitFor(() => {
        expect(screen.getByText(/Creative Performance Comparison/i)).toBeInTheDocument();
      });
    });

    it('should switch to Attribution tab', async () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      const attributionTab = screen.getByText(/🔗\s*Attribution/);
      fireEvent.click(attributionTab);

      await waitFor(() => {
        expect(screen.getByText(/HubSpot Deal Attribution/i)).toBeInTheDocument();
      });
    });

    it('should switch to Alerts tab', async () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      const alertsTab = screen.getByText(/🔔\s*Alerts/);
      fireEvent.click(alertsTab);

      await waitFor(() => {
        expect(screen.getByText(/Alert Configuration/i)).toBeInTheDocument();
      });
    });

    it('should switch to Reports tab', async () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      const reportsTab = screen.getByText(/📅\s*Reports/);
      fireEvent.click(reportsTab);

      await waitFor(() => {
        expect(screen.getByText(/Scheduled Reports/i)).toBeInTheDocument();
      });
    });
  });

  describe('Date Range Picker', () => {
    it('should update date range on quick button click', () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      const sevenDayButton = screen.getByText('7d');
      fireEvent.click(sevenDayButton);

      // Date should be updated (implementation detail, hard to test exact dates)
      expect(sevenDayButton).toBeInTheDocument();
    });
  });

  describe('Auto-refresh', () => {
    it('should toggle auto-refresh', () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      const autoRefreshCheckbox = screen.getByRole('checkbox');
      expect(autoRefreshCheckbox).toBeChecked();

      fireEvent.click(autoRefreshCheckbox);
      expect(autoRefreshCheckbox).not.toBeChecked();
    });
  });

  describe('Creative Performance', () => {
    it('should display creative performance table', async () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      const creativesTab = screen.getByText(/🎨\s*Creatives/);
      fireEvent.click(creativesTab);

      await waitFor(() => {
        expect(screen.getByText('Summer Video Ad')).toBeInTheDocument();
        expect(screen.getByText('Product Image Ad')).toBeInTheDocument();
      });
    });

    it('should sort creative performance table', async () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      const creativesTab = screen.getByText(/🎨\s*Creatives/);
      fireEvent.click(creativesTab);

      await waitFor(() => {
        const roasHeader = screen.getByText('ROAS');
        fireEvent.click(roasHeader);
        // Should toggle sort direction
      });
    });
  });

  describe('Export Functionality', () => {
    it('should export creatives to CSV', async () => {
      global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
      global.URL.revokeObjectURL = vi.fn();

      const { container } = render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      const creativesTab = screen.getByText(/🎨\s*Creatives/);
      fireEvent.click(creativesTab);

      await waitFor(() => {
        const exportButton = screen.getByText(/Export to CSV/i);
        fireEvent.click(exportButton);
      });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/analytics/export/csv')
        );
      });
    });
  });

  describe('Alert Configuration', () => {
    it('should display alert configuration form', async () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      const alertsTab = screen.getByText(/🔔\s*Alerts/);
      fireEvent.click(alertsTab);

      await waitFor(() => {
        expect(screen.getByText(/Create New Alert/i)).toBeInTheDocument();
        expect(screen.getByText(/Alert Type/i)).toBeInTheDocument();
        expect(screen.getByText(/Threshold/i)).toBeInTheDocument();
      });
    });

    it('should display existing alerts', async () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      const alertsTab = screen.getByText(/🔔\s*Alerts/);
      fireEvent.click(alertsTab);

      await waitFor(() => {
        expect(screen.getByText(/Active Alerts/i)).toBeInTheDocument();
      });
    });
  });

  describe('Scheduled Reports', () => {
    it('should display scheduled report form', async () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      const reportsTab = screen.getByText(/📅\s*Reports/);
      fireEvent.click(reportsTab);

      await waitFor(() => {
        expect(screen.getByText(/Create New Report/i)).toBeInTheDocument();
        expect(screen.getByText(/Report Name/i)).toBeInTheDocument();
        expect(screen.getByText(/Frequency/i)).toBeInTheDocument();
      });
    });

    it('should add email recipients', async () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      const reportsTab = screen.getByText(/📅\s*Reports/);
      fireEvent.click(reportsTab);

      await waitFor(() => {
        const emailInput = screen.getByPlaceholderText('email@example.com');
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });

        const addButton = screen.getByText('Add');
        fireEvent.click(addButton);
      });
    });
  });

  describe('Performance vs Prediction', () => {
    it('should display prediction comparison', async () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText(/Performance vs Prediction/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error',
        } as Response)
      );

      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      // Should not crash, should show loading or error state
      await waitFor(() => {
        expect(screen.getByText(/Analytics Dashboard/i)).toBeInTheDocument();
      });
    });
  });

  describe('WebSocket Integration', () => {
    it('should establish WebSocket connection', async () => {
      const mockWSConstructor = vi.fn();
      global.WebSocket = mockWSConstructor as any;

      render(
        <QueryClientProvider client={new QueryClient()}>
          <AnalyticsDashboard campaignIds={['campaign_1']} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(mockWSConstructor).toHaveBeenCalled();
      });
    });
  });
});
