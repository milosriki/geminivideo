import React, { useState, useMemo } from 'react';
import { BarChartIcon, EyeIcon, TagIcon, SparklesIcon } from './icons';

interface MetricData {
  label: string;
  value: number;
  change: number;
  format: 'number' | 'currency' | 'percentage';
}

interface ChartDataPoint {
  date: string;
  impressions: number;
  clicks: number;
  conversions: number;
  spend: number;
  revenue: number;
}

interface CampaignPerformance {
  id: string;
  name: string;
  platform: string;
  status: 'active' | 'paused' | 'completed';
  impressions: number;
  clicks: number;
  conversions: number;
  spend: number;
  revenue: number;
  ctr: number;
  cvr: number;
  roas: number;
}

interface AnalyticsDashboardProps {
  dateRange?: { start: Date; end: Date };
  onDateRangeChange?: (range: { start: Date; end: Date }) => void;
}

const formatValue = (value: number, format: MetricData['format']): string => {
  switch (format) {
    case 'currency':
      return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    case 'percentage':
      return `${value.toFixed(2)}%`;
    default:
      return value.toLocaleString('en-US');
  }
};

const MOCK_METRICS: MetricData[] = [
  { label: 'Total Impressions', value: 2456789, change: 12.5, format: 'number' },
  { label: 'Total Clicks', value: 45678, change: 8.3, format: 'number' },
  { label: 'Total Conversions', value: 1234, change: 15.2, format: 'number' },
  { label: 'Total Spend', value: 12456.78, change: -3.4, format: 'currency' },
  { label: 'Total Revenue', value: 45678.90, change: 22.1, format: 'currency' },
  { label: 'Average ROAS', value: 3.67, change: 5.8, format: 'number' },
  { label: 'Average CTR', value: 1.86, change: 0.4, format: 'percentage' },
  { label: 'Average CVR', value: 2.70, change: 1.2, format: 'percentage' },
];

const MOCK_CAMPAIGNS: CampaignPerformance[] = [
  {
    id: '1',
    name: 'Summer Sale 2024',
    platform: 'Meta',
    status: 'active',
    impressions: 567890,
    clicks: 12345,
    conversions: 456,
    spend: 3456.78,
    revenue: 15678.90,
    ctr: 2.17,
    cvr: 3.69,
    roas: 4.54,
  },
  {
    id: '2',
    name: 'Brand Awareness Q4',
    platform: 'Google',
    status: 'active',
    impressions: 890123,
    clicks: 15678,
    conversions: 234,
    spend: 4567.89,
    revenue: 12345.67,
    ctr: 1.76,
    cvr: 1.49,
    roas: 2.70,
  },
  {
    id: '3',
    name: 'Product Launch - Fitness',
    platform: 'TikTok',
    status: 'paused',
    impressions: 345678,
    clicks: 8901,
    conversions: 189,
    spend: 2345.67,
    revenue: 8901.23,
    ctr: 2.58,
    cvr: 2.12,
    roas: 3.79,
  },
  {
    id: '4',
    name: 'Retargeting Campaign',
    platform: 'Meta',
    status: 'active',
    impressions: 234567,
    clicks: 5678,
    conversions: 234,
    spend: 1234.56,
    revenue: 6789.01,
    ctr: 2.42,
    cvr: 4.12,
    roas: 5.50,
  },
  {
    id: '5',
    name: 'Holiday Promo',
    platform: 'YouTube',
    status: 'completed',
    impressions: 418531,
    clicks: 3076,
    conversions: 121,
    spend: 851.88,
    revenue: 1964.09,
    ctr: 0.74,
    cvr: 3.93,
    roas: 2.31,
  },
];

const MOCK_CHART_DATA: ChartDataPoint[] = [
  { date: '2024-01-01', impressions: 45000, clicks: 1200, conversions: 45, spend: 450, revenue: 1800 },
  { date: '2024-01-02', impressions: 52000, clicks: 1400, conversions: 52, spend: 480, revenue: 2100 },
  { date: '2024-01-03', impressions: 48000, clicks: 1300, conversions: 48, spend: 460, revenue: 1950 },
  { date: '2024-01-04', impressions: 61000, clicks: 1600, conversions: 65, spend: 520, revenue: 2600 },
  { date: '2024-01-05', impressions: 55000, clicks: 1450, conversions: 58, spend: 490, revenue: 2350 },
  { date: '2024-01-06', impressions: 72000, clicks: 1850, conversions: 75, spend: 580, revenue: 3000 },
  { date: '2024-01-07', impressions: 68000, clicks: 1750, conversions: 70, spend: 550, revenue: 2800 },
];

const MetricCard: React.FC<{ metric: MetricData }> = ({ metric }) => (
  <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg p-4">
    <div className="text-gray-400 text-xs uppercase tracking-wider mb-1">{metric.label}</div>
    <div className="text-2xl font-bold">{formatValue(metric.value, metric.format)}</div>
    <div className={`text-sm mt-1 ${metric.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
      {metric.change >= 0 ? '+' : ''}{metric.change}% vs last period
    </div>
  </div>
);

const MiniChart: React.FC<{ data: number[]; color: string }> = ({ data, color }) => {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const width = 100;
  const height = 30;
  const points = data.map((v, i) =>
    `${(i / (data.length - 1)) * width},${height - ((v - min) / range) * height}`
  ).join(' ');

  return (
    <svg width={width} height={height} className="inline-block">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="2"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
};

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  dateRange,
  onDateRangeChange,
}) => {
  const [selectedMetric, setSelectedMetric] = useState<'impressions' | 'clicks' | 'conversions' | 'spend' | 'revenue'>('impressions');
  const [selectedPeriod, setSelectedPeriod] = useState<'7d' | '30d' | '90d' | 'custom'>('7d');

  const chartData = useMemo(() => {
    return MOCK_CHART_DATA.map(d => d[selectedMetric]);
  }, [selectedMetric]);

  const maxChartValue = Math.max(...chartData);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Analytics Dashboard</h1>
            <p className="text-gray-400 text-sm mt-1">Track your campaign performance</p>
          </div>
          <div className="flex gap-2">
            {(['7d', '30d', '90d'] as const).map(period => (
              <button
                key={period}
                onClick={() => setSelectedPeriod(period)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedPeriod === period
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                {period === '7d' ? 'Last 7 Days' : period === '30d' ? 'Last 30 Days' : 'Last 90 Days'}
              </button>
            ))}
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {MOCK_METRICS.slice(0, 8).map((metric, i) => (
            <MetricCard key={i} metric={metric} />
          ))}
        </div>

        {/* Main Chart */}
        <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <BarChartIcon className="w-5 h-5 text-indigo-400" />
              <h2 className="text-lg font-semibold">Performance Over Time</h2>
            </div>
            <div className="flex gap-2">
              {(['impressions', 'clicks', 'conversions', 'spend', 'revenue'] as const).map(metric => (
                <button
                  key={metric}
                  onClick={() => setSelectedMetric(metric)}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    selectedMetric === metric
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                  }`}
                >
                  {metric.charAt(0).toUpperCase() + metric.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Simple Bar Chart */}
          <div className="h-64 flex items-end justify-between gap-2">
            {chartData.map((value, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-2">
                <div
                  className="w-full bg-indigo-600/80 rounded-t transition-all hover:bg-indigo-500"
                  style={{ height: `${(value / maxChartValue) * 100}%`, minHeight: '4px' }}
                />
                <span className="text-xs text-gray-500">
                  {new Date(MOCK_CHART_DATA[i].date).toLocaleDateString('en-US', { weekday: 'short' })}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Campaigns Table */}
        <div className="bg-gray-800/60 border border-gray-700/60 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-gray-700">
            <h2 className="text-lg font-semibold">Campaign Performance</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-800/80">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Campaign</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Platform</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">Impressions</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">Clicks</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">CTR</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">Spend</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">Revenue</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">ROAS</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-400 uppercase tracking-wider">Trend</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {MOCK_CAMPAIGNS.map(campaign => (
                  <tr key={campaign.id} className="hover:bg-gray-800/40 transition-colors">
                    <td className="px-4 py-4 font-medium">{campaign.name}</td>
                    <td className="px-4 py-4 text-gray-400">{campaign.platform}</td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        campaign.status === 'active' ? 'bg-green-900/50 text-green-400' :
                        campaign.status === 'paused' ? 'bg-yellow-900/50 text-yellow-400' :
                        'bg-gray-700 text-gray-400'
                      }`}>
                        {campaign.status}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-right">{campaign.impressions.toLocaleString()}</td>
                    <td className="px-4 py-4 text-right">{campaign.clicks.toLocaleString()}</td>
                    <td className="px-4 py-4 text-right">{campaign.ctr.toFixed(2)}%</td>
                    <td className="px-4 py-4 text-right">${campaign.spend.toLocaleString()}</td>
                    <td className="px-4 py-4 text-right text-green-400">${campaign.revenue.toLocaleString()}</td>
                    <td className="px-4 py-4 text-right font-semibold">{campaign.roas.toFixed(2)}x</td>
                    <td className="px-4 py-4 text-center">
                      <MiniChart
                        data={[45, 52, 48, 61, 55, 72, 68].map(v => v * (1 + Math.random() * 0.2))}
                        color="#818cf8"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* AI Insights */}
        <div className="bg-gradient-to-r from-indigo-900/40 to-purple-900/40 border border-indigo-700/50 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <SparklesIcon className="w-6 h-6 text-indigo-400" />
            <h2 className="text-lg font-semibold">AI Insights</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-black/20 rounded-lg p-4">
              <h3 className="font-medium text-indigo-300 mb-2">Top Performer</h3>
              <p className="text-sm text-gray-300">
                "Summer Sale 2024" has the highest ROAS at 4.54x. Consider increasing budget by 20%.
              </p>
            </div>
            <div className="bg-black/20 rounded-lg p-4">
              <h3 className="font-medium text-yellow-300 mb-2">Needs Attention</h3>
              <p className="text-sm text-gray-300">
                "Brand Awareness Q4" CVR is below average. Try refreshing creative assets.
              </p>
            </div>
            <div className="bg-black/20 rounded-lg p-4">
              <h3 className="font-medium text-green-300 mb-2">Opportunity</h3>
              <p className="text-sm text-gray-300">
                TikTok campaigns show 35% higher engagement. Expand audience targeting.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
