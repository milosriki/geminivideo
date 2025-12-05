/**
 * ROAS Tracking Dashboard - Agent 14
 * Real-time ROAS tracking for elite marketers spending $20k/day
 * Investor-grade dashboard with comprehensive performance metrics
 */
import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CalendarIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  SparklesIcon,
  ChartPieIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { apiUrl } from '@/config/api';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface ROASMetrics {
  current_roas: number;
  predicted_roas: number;
  actual_roas: number;
  roas_change: number;
  total_spend: number;
  total_revenue: number;
  profit: number;
  roi_percentage: number;
}

interface CampaignROAS {
  campaign_id: string;
  campaign_name: string;
  predicted_roas: number;
  actual_roas: number;
  accuracy_score: number;
  spend: number;
  revenue: number;
  conversions: number;
  ctr: number;
  platform: string;
  status: string;
  hook_type?: string;
  created_at: string;
}

interface ROASTrendData {
  date: string;
  predicted_roas: number;
  actual_roas: number;
  spend: number;
  revenue: number;
  profit: number;
}

interface CreativePerformance {
  creative_id: string;
  creative_name: string;
  roas: number;
  spend: number;
  revenue: number;
  conversions: number;
  impressions: number;
  ctr: number;
  hook_type?: string;
  template_id?: string;
}

interface CostBreakdown {
  category: string;
  cost: number;
  conversions: number;
  cpa: number;
  percentage: number;
}

interface PlatformComparison {
  platform: string;
  spend: number;
  revenue: number;
  roas: number;
  conversions: number;
  campaigns: number;
}

interface DashboardData {
  metrics: ROASMetrics;
  campaigns: CampaignROAS[];
  trend_data: ROASTrendData[];
  top_creatives: CreativePerformance[];
  cost_breakdown: CostBreakdown[];
  platform_comparison: PlatformComparison[];
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

const formatPercentage = (value: number): string => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
};

const formatROAS = (value: number): string => {
  return `${value.toFixed(2)}x`;
};

const getROASColor = (roas: number): string => {
  if (roas >= 3) return '#10b981'; // Green
  if (roas >= 2) return '#f59e0b'; // Amber
  return '#ef4444'; // Red
};

const getTrendColor = (value: number): string => {
  return value >= 0 ? '#10b981' : '#ef4444';
};

// ============================================================================
// METRIC CARD COMPONENT
// ============================================================================

interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  change?: number;
  trend?: 'up' | 'down';
  icon?: React.ReactNode;
  color?: string;
  loading?: boolean;
}

function MetricCard({ title, value, subtitle, change, trend, icon, color = '#8b5cf6', loading }: MetricCardProps) {
  if (loading) {
    return (
      <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6 animate-pulse">
        <div className="h-4 bg-zinc-800 rounded w-24 mb-4"></div>
        <div className="h-10 bg-zinc-800 rounded w-32 mb-2"></div>
        <div className="h-4 bg-zinc-800 rounded w-20"></div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl bg-zinc-900 border border-zinc-800 p-6 hover:border-zinc-700 transition-colors"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {icon && (
            <div className="p-2 rounded-lg" style={{ backgroundColor: `${color}20` }}>
              <div style={{ color }}>{icon}</div>
            </div>
          )}
          <p className="text-zinc-400 text-sm font-medium">{title}</p>
        </div>
        {change !== undefined && (
          <div className={`flex items-center gap-1 text-xs font-medium px-2 py-1 rounded ${
            trend === 'up' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
          }`}>
            {trend === 'up' ? (
              <ArrowTrendingUpIcon className="h-3 w-3" />
            ) : (
              <ArrowTrendingDownIcon className="h-3 w-3" />
            )}
            {formatPercentage(Math.abs(change))}
          </div>
        )}
      </div>
      <p className="text-4xl font-bold text-white mb-1">{value}</p>
      {subtitle && <p className="text-sm text-zinc-500">{subtitle}</p>}
    </motion.div>
  );
}

// ============================================================================
// CUSTOM TOOLTIP COMPONENTS
// ============================================================================

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className="bg-zinc-800/95 backdrop-blur-sm border border-zinc-700 rounded-lg p-3 shadow-xl">
      <p className="text-zinc-300 text-xs font-medium mb-2">{label}</p>
      {payload.map((item: any, index: number) => (
        <div key={index} className="flex items-center justify-between gap-4 text-sm">
          <span style={{ color: item.color }}>{item.name}:</span>
          <span className="font-bold" style={{ color: item.color }}>
            {item.name.includes('ROAS') ? formatROAS(item.value) :
             item.name.includes('$') || item.dataKey.includes('spend') || item.dataKey.includes('revenue') || item.dataKey.includes('profit') ? formatCurrency(item.value) :
             item.value.toLocaleString()}
          </span>
        </div>
      ))}
    </div>
  );
}

// ============================================================================
// MAIN DASHBOARD COMPONENT
// ============================================================================

export function ROASDashboard() {
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d' | '90d'>('7d');
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Fetch dashboard data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(apiUrl(`/api/roas/dashboard?range=${timeRange}`));

      if (!response.ok) {
        throw new Error(`Failed to fetch data: ${response.statusText}`);
      }

      const result = await response.json();
      setData(result);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching ROAS data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchData();
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, fetchData]);

  // Platform colors
  const PLATFORM_COLORS: { [key: string]: string } = {
    Meta: '#1877f2',
    Google: '#4285f4',
    TikTok: '#000000',
    LinkedIn: '#0a66c2',
    Twitter: '#1da1f2',
  };

  if (error) {
    return (
      <div className="min-h-screen bg-zinc-950 p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          <div className="rounded-xl bg-red-500/10 border border-red-500/20 p-8 text-center">
            <h2 className="text-2xl font-bold text-red-400 mb-2">Error Loading Dashboard</h2>
            <p className="text-red-300/80 mb-4">{error}</p>
            <button
              onClick={fetchData}
              className="px-6 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">ROAS Tracking Dashboard</h1>
          <p className="text-zinc-400">Real-time return on ad spend analytics</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Time Range Selector */}
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>

          {/* Auto-refresh Toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`p-2 rounded-lg border transition-colors ${
              autoRefresh
                ? 'bg-purple-500/20 border-purple-500/50 text-purple-400'
                : 'bg-zinc-900 border-zinc-800 text-zinc-400'
            }`}
            title={autoRefresh ? 'Auto-refresh enabled' : 'Auto-refresh disabled'}
          >
            <ArrowPathIcon className={`h-5 w-5 ${autoRefresh ? 'animate-spin-slow' : ''}`} />
          </button>

          {/* Manual Refresh */}
          <button
            onClick={fetchData}
            disabled={loading}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-zinc-800 disabled:text-zinc-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            <CalendarIcon className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Last Updated */}
      {lastUpdated && (
        <p className="text-xs text-zinc-500">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </p>
      )}

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Current ROAS"
          value={data?.metrics ? formatROAS(data.metrics.current_roas) : '--'}
          subtitle="Overall return on ad spend"
          change={data?.metrics?.roas_change}
          trend={data?.metrics?.roas_change && data.metrics.roas_change >= 0 ? 'up' : 'down'}
          icon={<ChartBarIcon className="h-5 w-5" />}
          color="#f59e0b"
          loading={loading}
        />
        <MetricCard
          title="Total Revenue"
          value={data?.metrics ? formatCurrency(data.metrics.total_revenue) : '--'}
          subtitle={data?.metrics ? `from ${formatCurrency(data.metrics.total_spend)} spend` : ''}
          icon={<CurrencyDollarIcon className="h-5 w-5" />}
          color="#10b981"
          loading={loading}
        />
        <MetricCard
          title="Total Profit"
          value={data?.metrics ? formatCurrency(data.metrics.profit) : '--'}
          subtitle={data?.metrics ? `${data.metrics.roi_percentage.toFixed(1)}% ROI` : ''}
          change={data?.metrics ? (data.metrics.profit / data.metrics.total_spend * 100) : undefined}
          trend="up"
          icon={<SparklesIcon className="h-5 w-5" />}
          color="#8b5cf6"
          loading={loading}
        />
        <MetricCard
          title="ML Accuracy"
          value={data?.metrics ? `${((data.metrics.actual_roas / data.metrics.predicted_roas) * 100).toFixed(1)}%` : '--'}
          subtitle="Predicted vs Actual ROAS"
          icon={<ChartPieIcon className="h-5 w-5" />}
          color="#3b82f6"
          loading={loading}
        />
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ROAS Trend - Predicted vs Actual */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="rounded-xl bg-zinc-900 border border-zinc-800 p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold text-white">ROAS Trend</h3>
              <p className="text-sm text-zinc-400 mt-1">Predicted vs Actual Performance</p>
            </div>
          </div>
          <div className="h-[350px]">
            {loading ? (
              <div className="h-full flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data?.trend_data || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="date" stroke="#71717a" fontSize={12} />
                  <YAxis stroke="#71717a" fontSize={12} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="predicted_roas"
                    name="Predicted ROAS"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    dot={{ fill: '#8b5cf6', strokeWidth: 2, r: 4 }}
                    strokeDasharray="5 5"
                  />
                  <Line
                    type="monotone"
                    dataKey="actual_roas"
                    name="Actual ROAS"
                    stroke="#f59e0b"
                    strokeWidth={3}
                    dot={{ fill: '#f59e0b', strokeWidth: 2, r: 5 }}
                    activeDot={{ r: 8 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </motion.div>

        {/* Revenue, Spend & Profit */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="rounded-xl bg-zinc-900 border border-zinc-800 p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold text-white">Financial Performance</h3>
              <p className="text-sm text-zinc-400 mt-1">Revenue, Spend & Profit Trends</p>
            </div>
          </div>
          <div className="h-[350px]">
            {loading ? (
              <div className="h-full flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data?.trend_data || []}>
                  <defs>
                    <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorSpend" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="date" stroke="#71717a" fontSize={12} />
                  <YAxis stroke="#71717a" fontSize={12} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="revenue"
                    name="Revenue ($)"
                    stroke="#10b981"
                    fill="url(#colorRevenue)"
                    strokeWidth={2}
                  />
                  <Area
                    type="monotone"
                    dataKey="spend"
                    name="Spend ($)"
                    stroke="#ef4444"
                    fill="url(#colorSpend)"
                    strokeWidth={2}
                  />
                  <Area
                    type="monotone"
                    dataKey="profit"
                    name="Profit ($)"
                    stroke="#8b5cf6"
                    fill="url(#colorProfit)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </motion.div>
      </div>

      {/* Campaign Performance & Platform Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Campaigns by ROAS */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="lg:col-span-2 rounded-xl bg-zinc-900 border border-zinc-800 p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold text-white">Campaign Performance</h3>
              <p className="text-sm text-zinc-400 mt-1">Top campaigns by ROAS</p>
            </div>
          </div>
          <div className="overflow-x-auto">
            {loading ? (
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-12 bg-zinc-800 rounded animate-pulse"></div>
                ))}
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-zinc-800 text-zinc-400 text-left">
                    <th className="pb-3 font-medium">Campaign</th>
                    <th className="pb-3 font-medium">Platform</th>
                    <th className="pb-3 font-medium text-right">Predicted</th>
                    <th className="pb-3 font-medium text-right">Actual</th>
                    <th className="pb-3 font-medium text-right">Accuracy</th>
                    <th className="pb-3 font-medium text-right">Spend</th>
                    <th className="pb-3 font-medium text-right">Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.campaigns || []).slice(0, 10).map((campaign, index) => (
                    <tr key={campaign.campaign_id} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                      <td className="py-3 text-white font-medium">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-zinc-500">#{index + 1}</span>
                          <span className="truncate max-w-xs">{campaign.campaign_name}</span>
                        </div>
                      </td>
                      <td className="py-3">
                        <span className="px-2 py-1 rounded text-xs font-medium"
                          style={{
                            backgroundColor: `${PLATFORM_COLORS[campaign.platform] || '#71717a'}20`,
                            color: PLATFORM_COLORS[campaign.platform] || '#a1a1aa'
                          }}>
                          {campaign.platform}
                        </span>
                      </td>
                      <td className="py-3 text-right text-purple-400">{formatROAS(campaign.predicted_roas)}</td>
                      <td className="py-3 text-right font-bold" style={{ color: getROASColor(campaign.actual_roas) }}>
                        {formatROAS(campaign.actual_roas)}
                      </td>
                      <td className="py-3 text-right">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          campaign.accuracy_score >= 85 ? 'bg-emerald-500/20 text-emerald-400' :
                          campaign.accuracy_score >= 70 ? 'bg-amber-500/20 text-amber-400' :
                          'bg-red-500/20 text-red-400'
                        }`}>
                          {campaign.accuracy_score.toFixed(0)}%
                        </span>
                      </td>
                      <td className="py-3 text-right text-zinc-300">{formatCurrency(campaign.spend)}</td>
                      <td className="py-3 text-right text-emerald-400 font-medium">{formatCurrency(campaign.revenue)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </motion.div>

        {/* Platform Comparison */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl bg-zinc-900 border border-zinc-800 p-6"
        >
          <div className="mb-6">
            <h3 className="text-xl font-bold text-white">Platform ROAS</h3>
            <p className="text-sm text-zinc-400 mt-1">Performance by platform</p>
          </div>
          <div className="space-y-4">
            {loading ? (
              [...Array(4)].map((_, i) => (
                <div key={i} className="h-16 bg-zinc-800 rounded animate-pulse"></div>
              ))
            ) : (
              (data?.platform_comparison || []).map((platform) => (
                <div key={platform.platform} className="p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-white">{platform.platform}</span>
                    <span className="text-lg font-bold" style={{ color: getROASColor(platform.roas) }}>
                      {formatROAS(platform.roas)}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs text-zinc-400">
                    <div>
                      <p>Spend</p>
                      <p className="text-white font-medium">{formatCurrency(platform.spend)}</p>
                    </div>
                    <div>
                      <p>Revenue</p>
                      <p className="text-emerald-400 font-medium">{formatCurrency(platform.revenue)}</p>
                    </div>
                  </div>
                  <div className="mt-2 pt-2 border-t border-zinc-700 text-xs text-zinc-500">
                    {platform.campaigns} campaigns • {platform.conversions} conversions
                  </div>
                </div>
              ))
            )}
          </div>
        </motion.div>
      </div>

      {/* Top Performing Creatives & Cost Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Performing Creatives */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl bg-zinc-900 border border-zinc-800 p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold text-white">Top Performing Creatives</h3>
              <p className="text-sm text-zinc-400 mt-1">Best ROAS by creative</p>
            </div>
          </div>
          <div className="h-[300px]">
            {loading ? (
              <div className="h-full flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={(data?.top_creatives || []).slice(0, 8)} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis type="number" stroke="#71717a" fontSize={12} />
                  <YAxis type="category" dataKey="creative_name" stroke="#71717a" fontSize={11} width={120} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="roas" name="ROAS" radius={[0, 8, 8, 0]}>
                    {(data?.top_creatives || []).slice(0, 8).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getROASColor(entry.roas)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </motion.div>

        {/* Cost Breakdown */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl bg-zinc-900 border border-zinc-800 p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold text-white">Cost Per Conversion</h3>
              <p className="text-sm text-zinc-400 mt-1">Breakdown by category</p>
            </div>
          </div>
          <div className="space-y-3">
            {loading ? (
              [...Array(5)].map((_, i) => (
                <div key={i} className="h-12 bg-zinc-800 rounded animate-pulse"></div>
              ))
            ) : (
              (data?.cost_breakdown || []).map((item, index) => {
                const colors = ['#8b5cf6', '#f59e0b', '#10b981', '#3b82f6', '#ef4444'];
                const color = colors[index % colors.length];

                return (
                  <div key={item.category} className="p-3 rounded-lg bg-zinc-800/50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-white">{item.category}</span>
                      <span className="text-sm font-bold" style={{ color }}>
                        {formatCurrency(item.cpa)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 bg-zinc-700 rounded-full overflow-hidden">
                        <div
                          className="h-full transition-all duration-500"
                          style={{
                            width: `${item.percentage}%`,
                            backgroundColor: color
                          }}
                        />
                      </div>
                      <span className="text-xs text-zinc-400 w-12 text-right">{item.percentage.toFixed(0)}%</span>
                    </div>
                    <div className="mt-1 text-xs text-zinc-500">
                      {formatCurrency(item.cost)} • {item.conversions} conversions
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}

export default ROASDashboard;
