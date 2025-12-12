import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { API_BASE_URL as API_BASE } from '../config/api';
import { ValidationStatusPanel, PredictionAccuracyChart, CorrelationHeatmap } from './predictions';
import { ROIDashboard } from './roi-dashboard';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';
import { useQuery, useQueryClient } from '@tanstack/react-query';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface AnalyticsDashboardProps {
  campaignIds?: string[];
}

interface CampaignMetrics {
  campaignId: string;
  campaignName: string;
  spend: number;
  revenue: number;
  roas: number;
  impressions: number;
  clicks: number;
  conversions: number;
  ctr: number;
  cvr: number;
  cpa: number;
  timestamp: number;
}

interface TrendDataPoint {
  date: string;
  timestamp: number;
  roas: number;
  spend: number;
  revenue: number;
  conversions: number;
  ctr: number;
}

interface FunnelStage {
  stage: string;
  value: number;
  percentage: number;
  dropoff?: number;
}

interface CreativePerformance {
  creativeId: string;
  creativeName: string;
  campaignId: string;
  format: string;
  hookType: string;
  impressions: number;
  clicks: number;
  conversions: number;
  spend: number;
  revenue: number;
  roas: number;
  ctr: number;
  cvr: number;
  cpa: number;
  thumbnailUrl?: string;
}

interface HubSpotDeal {
  dealId: string;
  dealName: string;
  amount: number;
  stage: string;
  campaignId?: string;
  creativeId?: string;
  sourceChannel: string;
  createdAt: number;
  closedAt?: number;
}

interface PerformancePrediction {
  predictedRoas: number;
  actualRoas: number;
  predictedConversions: number;
  actualConversions: number;
  accuracy: number;
  variance: number;
}

interface AlertConfig {
  id: string;
  type: 'roas_drop' | 'spend_limit' | 'conversion_drop' | 'ctr_drop';
  threshold: number;
  enabled: boolean;
  campaignIds: string[];
}

interface ScheduledReport {
  id: string;
  name: string;
  frequency: 'daily' | 'weekly' | 'monthly';
  recipients: string[];
  metrics: string[];
  enabled: boolean;
}

interface DateRange {
  startDate: Date;
  endDate: Date;
}

// ============================================================================
// API CLIENT
// ============================================================================



class AnalyticsAPI {
  static async getCampaignMetrics(
    campaignIds: string[],
    dateRange: DateRange
  ): Promise<CampaignMetrics[]> {
    const params = new URLSearchParams({
      campaignIds: campaignIds.join(','),
      startDate: dateRange.startDate.toISOString(),
      endDate: dateRange.endDate.toISOString(),
    });

    let response;
    try {
      response = await fetch(`${API_BASE}/analytics/campaigns?${params}`);
    } catch (error) {
      console.error('Error fetching campaign metrics:', error);
      throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    if (!response.ok) throw new Error('Failed to fetch campaign metrics');
    return response.json();
  }

  static async getTrendData(
    campaignIds: string[],
    dateRange: DateRange,
    granularity: 'hour' | 'day' | 'week' = 'day'
  ): Promise<TrendDataPoint[]> {
    const params = new URLSearchParams({
      campaignIds: campaignIds.join(','),
      startDate: dateRange.startDate.toISOString(),
      endDate: dateRange.endDate.toISOString(),
      granularity,
    });

    let response;
    try {
      response = await fetch(`${API_BASE}/analytics/trends?${params}`);
    } catch (error) {
      console.error('Error fetching trend data:', error);
      throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    if (!response.ok) throw new Error('Failed to fetch trend data');
    return response.json();
  }

  static async getFunnelData(
    campaignIds: string[],
    dateRange: DateRange
  ): Promise<FunnelStage[]> {
    const params = new URLSearchParams({
      campaignIds: campaignIds.join(','),
      startDate: dateRange.startDate.toISOString(),
      endDate: dateRange.endDate.toISOString(),
    });

    let response;
    try {
      response = await fetch(`${API_BASE}/analytics/funnel?${params}`);
    } catch (error) {
      console.error('Error fetching funnel data:', error);
      throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    if (!response.ok) throw new Error('Failed to fetch funnel data');
    return response.json();
  }

  static async getCreativePerformance(
    campaignIds: string[],
    dateRange: DateRange
  ): Promise<CreativePerformance[]> {
    const params = new URLSearchParams({
      campaignIds: campaignIds.join(','),
      startDate: dateRange.startDate.toISOString(),
      endDate: dateRange.endDate.toISOString(),
    });

    let response;
    try {
      response = await fetch(`${API_BASE}/analytics/creatives?${params}`);
    } catch (error) {
      console.error('Error fetching creative performance:', error);
      throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    if (!response.ok) throw new Error('Failed to fetch creative performance');
    return response.json();
  }

  static async getHubSpotAttribution(
    campaignIds: string[],
    dateRange: DateRange
  ): Promise<HubSpotDeal[]> {
    const params = new URLSearchParams({
      campaignIds: campaignIds.join(','),
      startDate: dateRange.startDate.toISOString(),
      endDate: dateRange.endDate.toISOString(),
    });

    let response;
    try {
      response = await fetch(`${API_BASE}/analytics/hubspot-deals?${params}`);
    } catch (error) {
      console.error('Error fetching HubSpot attribution:', error);
      throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    if (!response.ok) throw new Error('Failed to fetch HubSpot attribution');
    return response.json();
  }

  static async getPerformancePrediction(
    campaignIds: string[],
    dateRange: DateRange
  ): Promise<PerformancePrediction> {
    const params = new URLSearchParams({
      campaignIds: campaignIds.join(','),
      startDate: dateRange.startDate.toISOString(),
      endDate: dateRange.endDate.toISOString(),
    });

    let response;
    try {
      response = await fetch(`${API_BASE}/analytics/prediction-comparison?${params}`);
    } catch (error) {
      console.error('Error fetching performance prediction:', error);
      throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    if (!response.ok) throw new Error('Failed to fetch predictions');
    return response.json();
  }

  static async exportToCSV(
    campaignIds: string[],
    dateRange: DateRange,
    dataType: 'campaigns' | 'creatives' | 'funnel' | 'hubspot'
  ): Promise<Blob> {
    const params = new URLSearchParams({
      campaignIds: campaignIds.join(','),
      startDate: dateRange.startDate.toISOString(),
      endDate: dateRange.endDate.toISOString(),
      dataType,
    });

    let response;
    try {
      response = await fetch(`${API_BASE}/analytics/export/csv?${params}`);
    } catch (error) {
      console.error('Error exporting to CSV:', error);
      throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    if (!response.ok) throw new Error('Failed to export data');
    return response.blob();
  }

  static async saveAlertConfig(config: AlertConfig): Promise<void> {
    let response;
    try {
      response = await fetch(`${API_BASE}/analytics/alerts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
    } catch (error) {
      console.error('Error saving alert config:', error);
      throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    if (!response.ok) throw new Error('Failed to save alert config');
  }

  static async getAlertConfigs(campaignIds: string[]): Promise<AlertConfig[]> {
    const params = new URLSearchParams({
      campaignIds: campaignIds.join(','),
    });

    let response;
    try {
      response = await fetch(`${API_BASE}/analytics/alerts?${params}`);
    } catch (error) {
      console.error('Error fetching alert configs:', error);
      throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    if (!response.ok) throw new Error('Failed to fetch alert configs');
    return response.json();
  }

  static async saveScheduledReport(report: ScheduledReport): Promise<void> {
    let response;
    try {
      response = await fetch(`${API_BASE}/analytics/scheduled-reports`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(report),
      });
    } catch (error) {
      console.error('Error saving scheduled report:', error);
      throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    if (!response.ok) throw new Error('Failed to save scheduled report');
  }

  static async getScheduledReports(): Promise<ScheduledReport[]> {
    const response = await fetch(`${API_BASE}/analytics/scheduled-reports`);
    if (!response.ok) throw new Error('Failed to fetch scheduled reports');
    return response.json();
  }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

const formatNumber = (value: number): string => {
  return new Intl.NumberFormat('en-US').format(Math.round(value));
};

const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(2)}%`;
};

const formatDate = (timestamp: number): string => {
  return new Date(timestamp).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
};

const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

// ============================================================================
// METRIC CARD COMPONENT
// ============================================================================

interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  trend?: number;
  icon?: React.ReactNode;
  color?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  icon,
  color = 'indigo',
}) => {
  const trendColor = trend && trend > 0 ? 'text-green-400' : trend && trend < 0 ? 'text-red-400' : 'text-gray-400';
  const bgColor = `bg-${color}-500/10`;
  const borderColor = `border-${color}-500/30`;

  return (
    <div className={`${bgColor} border ${borderColor} rounded-lg p-4 space-y-2`}>
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider text-gray-400">{title}</span>
        {icon && <span className={`text-${color}-400`}>{icon}</span>}
      </div>
      <div className="text-2xl font-bold">{value}</div>
      {subtitle && <div className="text-xs text-gray-500">{subtitle}</div>}
      {trend !== undefined && (
        <div className={`text-xs ${trendColor} flex items-center gap-1`}>
          {trend > 0 ? '↑' : trend < 0 ? '↓' : '→'} {Math.abs(trend).toFixed(1)}% vs previous period
        </div>
      )}
    </div>
  );
};

// ============================================================================
// MAIN ANALYTICS DASHBOARD COMPONENT
// ============================================================================

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  campaignIds: propCampaignIds,
}) => {
  const queryClient = useQueryClient();

  // State Management
  const [selectedCampaigns, setSelectedCampaigns] = useState<string[]>(propCampaignIds || []);
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
    endDate: new Date(),
  });
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds
  const [activeTab, setActiveTab] = useState<'overview' | 'creatives' | 'attribution' | 'alerts' | 'reports' | 'roi'>('overview');
  const [sortColumn, setSortColumn] = useState<keyof CreativePerformance>('roas');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  // Quick date range presets
  const setQuickRange = (days: number) => {
    setDateRange({
      startDate: new Date(Date.now() - days * 24 * 60 * 60 * 1000),
      endDate: new Date(),
    });
  };

  // Data Fetching with React Query
  const { data: campaignMetrics, isLoading: loadingMetrics } = useQuery({
    queryKey: ['campaignMetrics', selectedCampaigns, dateRange],
    queryFn: () => AnalyticsAPI.getCampaignMetrics(selectedCampaigns, dateRange),
    enabled: selectedCampaigns.length > 0,
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  const { data: trendData, isLoading: loadingTrends } = useQuery({
    queryKey: ['trendData', selectedCampaigns, dateRange],
    queryFn: () => AnalyticsAPI.getTrendData(selectedCampaigns, dateRange),
    enabled: selectedCampaigns.length > 0,
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  const { data: funnelData, isLoading: loadingFunnel } = useQuery({
    queryKey: ['funnelData', selectedCampaigns, dateRange],
    queryFn: () => AnalyticsAPI.getFunnelData(selectedCampaigns, dateRange),
    enabled: selectedCampaigns.length > 0,
  });

  const { data: creativePerformance, isLoading: loadingCreatives } = useQuery({
    queryKey: ['creativePerformance', selectedCampaigns, dateRange],
    queryFn: () => AnalyticsAPI.getCreativePerformance(selectedCampaigns, dateRange),
    enabled: selectedCampaigns.length > 0,
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  const { data: hubspotDeals, isLoading: loadingHubSpot } = useQuery({
    queryKey: ['hubspotDeals', selectedCampaigns, dateRange],
    queryFn: () => AnalyticsAPI.getHubSpotAttribution(selectedCampaigns, dateRange),
    enabled: selectedCampaigns.length > 0,
  });

  const { data: predictionComparison, isLoading: loadingPrediction } = useQuery({
    queryKey: ['predictionComparison', selectedCampaigns, dateRange],
    queryFn: () => AnalyticsAPI.getPerformancePrediction(selectedCampaigns, dateRange),
    enabled: selectedCampaigns.length > 0,
  });

  const { data: alertConfigs } = useQuery({
    queryKey: ['alertConfigs', selectedCampaigns],
    queryFn: () => AnalyticsAPI.getAlertConfigs(selectedCampaigns),
    enabled: selectedCampaigns.length > 0,
  });

  const { data: scheduledReports } = useQuery({
    queryKey: ['scheduledReports'],
    queryFn: () => AnalyticsAPI.getScheduledReports(),
  });

  // WebSocket for real-time updates
  useEffect(() => {
    if (!autoRefresh || selectedCampaigns.length === 0) return;

    const ws = new WebSocket(`${API_BASE.replace('http', 'ws')}/analytics/stream`);

    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'subscribe',
        campaignIds: selectedCampaigns
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'metrics_update') {
        // Invalidate queries to trigger refetch
        queryClient.invalidateQueries({ queryKey: ['campaignMetrics'] });
        queryClient.invalidateQueries({ queryKey: ['trendData'] });
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      ws.close();
    };
  }, [autoRefresh, selectedCampaigns, queryClient]);

  // Calculate aggregate metrics
  const aggregateMetrics = useMemo(() => {
    if (!campaignMetrics || campaignMetrics.length === 0) {
      return {
        totalSpend: 0,
        totalRevenue: 0,
        avgRoas: 0,
        totalImpressions: 0,
        totalClicks: 0,
        totalConversions: 0,
        avgCtr: 0,
        avgCvr: 0,
        avgCpa: 0,
      };
    }

    const totals = campaignMetrics.reduce(
      (acc, metric) => ({
        spend: acc.spend + metric.spend,
        revenue: acc.revenue + metric.revenue,
        impressions: acc.impressions + metric.impressions,
        clicks: acc.clicks + metric.clicks,
        conversions: acc.conversions + metric.conversions,
      }),
      { spend: 0, revenue: 0, impressions: 0, clicks: 0, conversions: 0 }
    );

    return {
      totalSpend: totals.spend,
      totalRevenue: totals.revenue,
      avgRoas: totals.spend > 0 ? totals.revenue / totals.spend : 0,
      totalImpressions: totals.impressions,
      totalClicks: totals.clicks,
      totalConversions: totals.conversions,
      avgCtr: totals.impressions > 0 ? totals.clicks / totals.impressions : 0,
      avgCvr: totals.clicks > 0 ? totals.conversions / totals.clicks : 0,
      avgCpa: totals.conversions > 0 ? totals.spend / totals.conversions : 0,
    };
  }, [campaignMetrics]);

  // Export to CSV handler
  const handleExport = useCallback(
    async (dataType: 'campaigns' | 'creatives' | 'funnel' | 'hubspot') => {
      try {
        const blob = await AnalyticsAPI.exportToCSV(selectedCampaigns, dateRange, dataType);
        const filename = `analytics_${dataType}_${Date.now()}.csv`;
        downloadBlob(blob, filename);
      } catch (error) {
        console.error('Export failed:', error);
        alert('Failed to export data. Please try again.');
      }
    },
    [selectedCampaigns, dateRange]
  );

  // Sorted creative performance
  const sortedCreatives = useMemo(() => {
    if (!creativePerformance) return [];

    return [...creativePerformance].sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];
      const multiplier = sortDirection === 'asc' ? 1 : -1;

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return (aVal - bVal) * multiplier;
      }
      return 0;
    });
  }, [creativePerformance, sortColumn, sortDirection]);

  const handleSort = (column: keyof CreativePerformance) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('desc');
    }
  };

  // Chart colors
  const COLORS = {
    primary: '#6366f1',
    secondary: '#8b5cf6',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',
  };

  const FUNNEL_COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe'];

  // ============================================================================
  // RENDER SECTIONS
  // ============================================================================

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Total Spend"
          value={formatCurrency(aggregateMetrics.totalSpend)}
          color="red"
          icon={<span>💰</span>}
        />
        <MetricCard
          title="Total Revenue"
          value={formatCurrency(aggregateMetrics.totalRevenue)}
          color="green"
          icon={<span>💵</span>}
        />
        <MetricCard
          title="ROAS"
          value={`${aggregateMetrics.avgRoas.toFixed(2)}x`}
          subtitle={`${formatPercentage(aggregateMetrics.avgRoas - 1)} profit margin`}
          color="indigo"
          icon={<span>📈</span>}
        />
        <MetricCard
          title="CTR"
          value={formatPercentage(aggregateMetrics.avgCtr)}
          subtitle={`${formatNumber(aggregateMetrics.totalClicks)} clicks`}
          color="blue"
          icon={<span>👆</span>}
        />
        <MetricCard
          title="CPA"
          value={formatCurrency(aggregateMetrics.avgCpa)}
          subtitle={`${formatNumber(aggregateMetrics.totalConversions)} conversions`}
          color="purple"
          icon={<span>🎯</span>}
        />
      </div>

      {/* ROAS Trend Chart */}
      <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span>📊</span> ROAS Trend Over Time
        </h3>
        {loadingTrends ? (
          <div className="h-64 flex items-center justify-center text-gray-400">
            Loading trend data...
          </div>
        ) : trendData && trendData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={trendData}>
              <defs>
                <linearGradient id="colorRoas" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.8} />
                  <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="date"
                stroke="#9ca3af"
                style={{ fontSize: '12px' }}
              />
              <YAxis
                stroke="#9ca3af"
                style={{ fontSize: '12px' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#f3f4f6' }}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="roas"
                stroke={COLORS.primary}
                fillOpacity={1}
                fill="url(#colorRoas)"
                name="ROAS"
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-64 flex items-center justify-center text-gray-400">
            No trend data available
          </div>
        )}
      </div>

      {/* Performance Metrics Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Spend vs Revenue Chart */}
        <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span>💸</span> Spend vs Revenue
          </h3>
          {loadingTrends ? (
            <div className="h-64 flex items-center justify-center text-gray-400">
              Loading data...
            </div>
          ) : trendData && trendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="date"
                  stroke="#9ca3af"
                  style={{ fontSize: '12px' }}
                />
                <YAxis
                  stroke="#9ca3af"
                  style={{ fontSize: '12px' }}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                  formatter={(value: number) => formatCurrency(value)}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="spend"
                  stroke={COLORS.danger}
                  strokeWidth={2}
                  name="Spend"
                  dot={{ r: 3 }}
                />
                <Line
                  type="monotone"
                  dataKey="revenue"
                  stroke={COLORS.success}
                  strokeWidth={2}
                  name="Revenue"
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              No data available
            </div>
          )}
        </div>

        {/* CTR Trend Chart */}
        <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span>👆</span> Click-Through Rate Trend
          </h3>
          {loadingTrends ? (
            <div className="h-64 flex items-center justify-center text-gray-400">
              Loading data...
            </div>
          ) : trendData && trendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="date"
                  stroke="#9ca3af"
                  style={{ fontSize: '12px' }}
                />
                <YAxis
                  stroke="#9ca3af"
                  style={{ fontSize: '12px' }}
                  tickFormatter={(value) => `${(value * 100).toFixed(1)}%`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                  formatter={(value: number) => formatPercentage(value)}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="ctr"
                  stroke={COLORS.info}
                  strokeWidth={2}
                  name="CTR"
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              No data available
            </div>
          )}
        </div>
      </div>

      {/* Conversion Funnel */}
      <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span>🎯</span> Conversion Funnel
        </h3>
        {loadingFunnel ? (
          <div className="h-64 flex items-center justify-center text-gray-400">
            Loading funnel data...
          </div>
        ) : funnelData && funnelData.length > 0 ? (
          <div className="space-y-4">
            {funnelData.map((stage, index) => (
              <div key={stage.stage}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">{stage.stage}</span>
                  <span className="text-sm text-gray-400">
                    {formatNumber(stage.value)} ({stage.percentage.toFixed(1)}%)
                  </span>
                </div>
                <div className="relative h-8 bg-gray-700/50 rounded-lg overflow-hidden">
                  <div
                    className="absolute top-0 left-0 h-full rounded-lg transition-all duration-300"
                    style={{
                      width: `${stage.percentage}%`,
                      backgroundColor: FUNNEL_COLORS[index % FUNNEL_COLORS.length],
                    }}
                  />
                </div>
                {stage.dropoff !== undefined && (
                  <div className="text-xs text-red-400 mt-1">
                    ↓ {stage.dropoff.toFixed(1)}% drop-off
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="h-64 flex items-center justify-center text-gray-400">
            No funnel data available
          </div>
        )}
      </div>

      {/* Performance vs Prediction */}
      {predictionComparison && (
        <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span>🔮</span> Performance vs Prediction
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <div className="text-sm text-gray-400">ROAS</div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold">{predictionComparison.actualRoas.toFixed(2)}x</span>
                <span className="text-sm text-gray-500">
                  vs {predictionComparison.predictedRoas.toFixed(2)}x predicted
                </span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="text-sm text-gray-400">Conversions</div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold">{formatNumber(predictionComparison.actualConversions)}</span>
                <span className="text-sm text-gray-500">
                  vs {formatNumber(predictionComparison.predictedConversions)} predicted
                </span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="text-sm text-gray-400">Prediction Accuracy</div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold">{predictionComparison.accuracy.toFixed(1)}%</span>
                <span className="text-sm text-gray-500">
                  ({predictionComparison.variance > 0 ? '+' : ''}{predictionComparison.variance.toFixed(1)}% variance)
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderCreativesTab = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <span>🎨</span> Creative Performance Comparison
        </h3>
        <button
          onClick={() => handleExport('creatives')}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-sm font-medium transition-colors"
        >
          Export to CSV
        </button>
      </div>

      {loadingCreatives ? (
        <div className="h-64 flex items-center justify-center text-gray-400">
          Loading creative performance data...
        </div>
      ) : sortedCreatives && sortedCreatives.length > 0 ? (
        <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-900/50">
                <tr>
                  {[
                    { key: 'creativeName', label: 'Creative' },
                    { key: 'format', label: 'Format' },
                    { key: 'hookType', label: 'Hook Type' },
                    { key: 'impressions', label: 'Impressions' },
                    { key: 'clicks', label: 'Clicks' },
                    { key: 'conversions', label: 'Conv.' },
                    { key: 'ctr', label: 'CTR' },
                    { key: 'cvr', label: 'CVR' },
                    { key: 'cpa', label: 'CPA' },
                    { key: 'roas', label: 'ROAS' },
                    { key: 'spend', label: 'Spend' },
                    { key: 'revenue', label: 'Revenue' },
                  ].map((col) => (
                    <th
                      key={col.key}
                      onClick={() => handleSort(col.key as keyof CreativePerformance)}
                      className="px-4 py-3 text-left text-xs font-semibold text-gray-300 cursor-pointer hover:bg-gray-800/50 transition-colors"
                    >
                      <div className="flex items-center gap-1">
                        {col.label}
                        {sortColumn === col.key && (
                          <span className="text-indigo-400">
                            {sortDirection === 'asc' ? '↑' : '↓'}
                          </span>
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sortedCreatives.map((creative) => (
                  <tr
                    key={creative.creativeId}
                    className="border-t border-gray-700/50 hover:bg-gray-800/30 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        {creative.thumbnailUrl && (
                          <img
                            src={creative.thumbnailUrl}
                            alt={creative.creativeName}
                            className="w-12 h-12 rounded object-cover"
                          />
                        )}
                        <span className="font-medium">{creative.creativeName}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-300">{creative.format}</td>
                    <td className="px-4 py-3 text-gray-300">{creative.hookType}</td>
                    <td className="px-4 py-3">{formatNumber(creative.impressions)}</td>
                    <td className="px-4 py-3">{formatNumber(creative.clicks)}</td>
                    <td className="px-4 py-3">{formatNumber(creative.conversions)}</td>
                    <td className="px-4 py-3">{formatPercentage(creative.ctr)}</td>
                    <td className="px-4 py-3">{formatPercentage(creative.cvr)}</td>
                    <td className="px-4 py-3">{formatCurrency(creative.cpa)}</td>
                    <td className="px-4 py-3">
                      <span className={creative.roas >= 2 ? 'text-green-400 font-semibold' : creative.roas >= 1 ? 'text-yellow-400' : 'text-red-400'}>
                        {creative.roas.toFixed(2)}x
                      </span>
                    </td>
                    <td className="px-4 py-3">{formatCurrency(creative.spend)}</td>
                    <td className="px-4 py-3">{formatCurrency(creative.revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="h-64 flex items-center justify-center text-gray-400 bg-gray-800/60 border border-gray-700/60 rounded-lg">
          No creative performance data available
        </div>
      )}
    </div>
  );

  const renderAttributionTab = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <span>🔗</span> HubSpot Deal Attribution
        </h3>
        <button
          onClick={() => handleExport('hubspot')}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-sm font-medium transition-colors"
        >
          Export to CSV
        </button>
      </div>

      {loadingHubSpot ? (
        <div className="h-64 flex items-center justify-center text-gray-400">
          Loading HubSpot attribution data...
        </div>
      ) : hubspotDeals && hubspotDeals.length > 0 ? (
        <>
          {/* Attribution Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <MetricCard
              title="Total Deals"
              value={formatNumber(hubspotDeals.length)}
              color="purple"
              icon={<span>🤝</span>}
            />
            <MetricCard
              title="Total Deal Value"
              value={formatCurrency(
                hubspotDeals.reduce((sum, deal) => sum + deal.amount, 0)
              )}
              color="green"
              icon={<span>💰</span>}
            />
            <MetricCard
              title="Closed Deals"
              value={formatNumber(
                hubspotDeals.filter((d) => d.closedAt).length
              )}
              color="blue"
              icon={<span>✅</span>}
            />
            <MetricCard
              title="Avg Deal Size"
              value={formatCurrency(
                hubspotDeals.reduce((sum, deal) => sum + deal.amount, 0) /
                hubspotDeals.length
              )}
              color="indigo"
              icon={<span>📊</span>}
            />
          </div>

          {/* Deals by Source Channel */}
          <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg p-6">
            <h4 className="text-md font-semibold mb-4">Deals by Source Channel</h4>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={Object.entries(
                    hubspotDeals.reduce((acc, deal) => {
                      acc[deal.sourceChannel] = (acc[deal.sourceChannel] || 0) + 1;
                      return acc;
                    }, {} as Record<string, number>)
                  ).map(([name, value]) => ({ name, value }))}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) =>
                    `${name}: ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {Object.keys(
                    hubspotDeals.reduce((acc, deal) => {
                      acc[deal.sourceChannel] = true;
                      return acc;
                    }, {} as Record<string, boolean>)
                  ).map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={Object.values(COLORS)[index % Object.values(COLORS).length]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Deals Table */}
          <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-900/50">
                  <tr>
                    {['Deal Name', 'Amount', 'Stage', 'Source', 'Campaign', 'Created', 'Closed'].map((header) => (
                      <th key={header} className="px-4 py-3 text-left text-xs font-semibold text-gray-300">
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {hubspotDeals.map((deal) => (
                    <tr
                      key={deal.dealId}
                      className="border-t border-gray-700/50 hover:bg-gray-800/30 transition-colors"
                    >
                      <td className="px-4 py-3 font-medium">{deal.dealName}</td>
                      <td className="px-4 py-3">{formatCurrency(deal.amount)}</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 bg-indigo-500/20 text-indigo-300 rounded text-xs">
                          {deal.stage}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-300">{deal.sourceChannel}</td>
                      <td className="px-4 py-3 text-gray-300">
                        {deal.campaignId || '—'}
                      </td>
                      <td className="px-4 py-3 text-gray-400">
                        {formatDate(deal.createdAt)}
                      </td>
                      <td className="px-4 py-3 text-gray-400">
                        {deal.closedAt ? formatDate(deal.closedAt) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        <div className="h-64 flex items-center justify-center text-gray-400 bg-gray-800/60 border border-gray-700/60 rounded-lg">
          No HubSpot attribution data available
        </div>
      )}
    </div>
  );

  const RenderAlertsTab = () => {
    const [newAlert, setNewAlert] = useState<Partial<AlertConfig>>({
      type: 'roas_drop',
      threshold: 1.5,
      enabled: true,
      campaignIds: selectedCampaigns,
    });

    const handleSaveAlert = async () => {
      try {
        await AnalyticsAPI.saveAlertConfig(newAlert as AlertConfig);
        queryClient.invalidateQueries({ queryKey: ['alertConfigs'] });
        alert('Alert configuration saved successfully!');
      } catch (error) {
        console.error('Failed to save alert:', error);
        alert('Failed to save alert configuration. Please try again.');
      }
    };

    return (
      <div className="space-y-6">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <span>🔔</span> Alert Configuration
        </h3>

        {/* Create New Alert */}
        <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg p-6 space-y-4">
          <h4 className="text-md font-semibold">Create New Alert</h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Alert Type</label>
              <select
                value={newAlert.type}
                onChange={(e) => setNewAlert({ ...newAlert, type: e.target.value as AlertConfig['type'] })}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="roas_drop">ROAS Drop</option>
                <option value="spend_limit">Spend Limit</option>
                <option value="conversion_drop">Conversion Drop</option>
                <option value="ctr_drop">CTR Drop</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Threshold</label>
              <input
                type="number"
                step="0.1"
                value={newAlert.threshold}
                onChange={(e) => setNewAlert({ ...newAlert, threshold: parseFloat(e.target.value) })}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={newAlert.enabled}
              onChange={(e) => setNewAlert({ ...newAlert, enabled: e.target.checked })}
              className="rounded"
            />
            <label className="text-sm text-gray-400">Enable this alert</label>
          </div>

          <button
            onClick={handleSaveAlert}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-sm font-medium transition-colors"
          >
            Save Alert
          </button>
        </div>

        {/* Existing Alerts */}
        {alertConfigs && alertConfigs.length > 0 && (
          <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg overflow-hidden">
            <div className="px-4 py-3 bg-gray-900/50">
              <h4 className="text-md font-semibold">Active Alerts</h4>
            </div>
            <div className="divide-y divide-gray-700/50">
              {alertConfigs.map((alert) => (
                <div key={alert.id} className="px-4 py-3 flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="font-medium">{alert.type.replace('_', ' ').toUpperCase()}</div>
                    <div className="text-sm text-gray-400">
                      Threshold: {alert.threshold} • {alert.campaignIds.length} campaigns
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 rounded text-xs ${alert.enabled ? 'bg-green-500/20 text-green-300' : 'bg-gray-500/20 text-gray-400'}`}>
                      {alert.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const RenderReportsTab = () => {
    const [newReport, setNewReport] = useState<Partial<ScheduledReport>>({
      name: '',
      frequency: 'weekly',
      recipients: [],
      metrics: ['roas', 'spend', 'revenue', 'conversions'],
      enabled: true,
    });

    const [recipientInput, setRecipientInput] = useState('');

    const handleAddRecipient = () => {
      if (recipientInput && !newReport.recipients?.includes(recipientInput)) {
        setNewReport({
          ...newReport,
          recipients: [...(newReport.recipients || []), recipientInput],
        });
        setRecipientInput('');
      }
    };

    const handleSaveReport = async () => {
      try {
        await AnalyticsAPI.saveScheduledReport(newReport as ScheduledReport);
        queryClient.invalidateQueries({ queryKey: ['scheduledReports'] });
        alert('Scheduled report saved successfully!');
        setNewReport({
          name: '',
          frequency: 'weekly',
          recipients: [],
          metrics: ['roas', 'spend', 'revenue', 'conversions'],
          enabled: true,
        });
      } catch (error) {
        console.error('Failed to save report:', error);
        alert('Failed to save scheduled report. Please try again.');
      }
    };

    return (
      <div className="space-y-6">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <span>📅</span> Scheduled Reports
        </h3>

        {/* Create New Report */}
        <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg p-6 space-y-4">
          <h4 className="text-md font-semibold">Create New Report</h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Report Name</label>
              <input
                type="text"
                value={newReport.name}
                onChange={(e) => setNewReport({ ...newReport, name: e.target.value })}
                placeholder="Weekly Performance Report"
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Frequency</label>
              <select
                value={newReport.frequency}
                onChange={(e) => setNewReport({ ...newReport, frequency: e.target.value as ScheduledReport['frequency'] })}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Recipients</label>
            <div className="flex gap-2 mb-2">
              <input
                type="email"
                value={recipientInput}
                onChange={(e) => setRecipientInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddRecipient()}
                placeholder="email@example.com"
                className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <button
                onClick={handleAddRecipient}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {newReport.recipients?.map((email) => (
                <span
                  key={email}
                  className="px-3 py-1 bg-indigo-500/20 text-indigo-300 rounded-full text-xs flex items-center gap-2"
                >
                  {email}
                  <button
                    onClick={() =>
                      setNewReport({
                        ...newReport,
                        recipients: newReport.recipients?.filter((e) => e !== email),
                      })
                    }
                    className="hover:text-red-400"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          <button
            onClick={handleSaveReport}
            disabled={!newReport.name || !newReport.recipients?.length}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors"
          >
            Save Report
          </button>
        </div>

        {/* Existing Reports */}
        {scheduledReports && scheduledReports.length > 0 && (
          <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg overflow-hidden">
            <div className="px-4 py-3 bg-gray-900/50">
              <h4 className="text-md font-semibold">Active Reports</h4>
            </div>
            <div className="divide-y divide-gray-700/50">
              {scheduledReports.map((report) => (
                <div key={report.id} className="px-4 py-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium">{report.name}</div>
                    <span className={`px-2 py-1 rounded text-xs ${report.enabled ? 'bg-green-500/20 text-green-300' : 'bg-gray-500/20 text-gray-400'}`}>
                      {report.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                  <div className="text-sm text-gray-400">
                    {report.frequency.charAt(0).toUpperCase() + report.frequency.slice(1)} • {report.recipients.length} recipients
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // ============================================================================
  // MAIN RENDER
  // ============================================================================

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <span>📊</span> Analytics Dashboard
            </h1>
            <p className="text-gray-400 mt-1">Real-time campaign performance tracking</p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-2 bg-gray-800/60 border border-gray-700/60 rounded-lg">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm">Auto-refresh</span>
              {autoRefresh && (
                <span className="animate-pulse text-green-400 text-xs">●</span>
              )}
            </div>
          </div>
        </div>

        {/* Date Range Picker */}
        <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg p-4">
          <div className="flex flex-col lg:flex-row lg:items-center gap-4">
            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Start Date</label>
                <input
                  type="date"
                  value={dateRange.startDate.toISOString().split('T')[0]}
                  onChange={(e) =>
                    setDateRange({ ...dateRange, startDate: new Date(e.target.value) })
                  }
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">End Date</label>
                <input
                  type="date"
                  value={dateRange.endDate.toISOString().split('T')[0]}
                  onChange={(e) =>
                    setDateRange({ ...dateRange, endDate: new Date(e.target.value) })
                  }
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setQuickRange(7)}
                className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
              >
                7d
              </button>
              <button
                onClick={() => setQuickRange(30)}
                className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
              >
                30d
              </button>
              <button
                onClick={() => setQuickRange(90)}
                className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
              >
                90d
              </button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto">
          {[
            { id: 'overview', label: 'Overview', icon: '📈' },
            { id: 'creatives', label: 'Creatives', icon: '🎨' },
            { id: 'attribution', label: 'Attribution', icon: '🔗' },
            { id: 'roi', label: 'ROI & Predictions', icon: '🎯' },
            { id: 'alerts', label: 'Alerts', icon: '🔔' },
            { id: 'reports', label: 'Reports', icon: '📅' },

          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${activeTab === tab.id
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-800/60 text-gray-400 hover:bg-gray-700/60'
                }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'creatives' && renderCreativesTab()}
        {activeTab === 'attribution' && renderAttributionTab()}
        {activeTab === 'alerts' && <RenderAlertsTab />}
        {activeTab === 'reports' && <RenderReportsTab />}
        {activeTab === 'roi' && (
          <div className="space-y-8 mt-6">
            <ROIDashboard />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <PredictionAccuracyChart />
              <CorrelationHeatmap />
            </div>
            <ValidationStatusPanel />
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
