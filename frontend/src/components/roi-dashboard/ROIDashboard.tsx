import { useState, useEffect } from 'react';
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  BoltIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';

interface ROIData {
  date: string;
  roi: number;
  spend: number;
  revenue: number;
  roas: number;
}

interface ROIMetrics {
  currentROI: number;
  roiChange: number;
  totalSpend: number;
  totalRevenue: number;
  avgROAS: number;
  predictedROI: number;
}

function MetricCard({
  icon: Icon,
  label,
  value,
  change,
  format = 'number'
}: {
  icon: React.ElementType;
  label: string;
  value: number;
  change?: number;
  format?: 'number' | 'currency' | 'percent';
}) {
  const formatValue = (val: number) => {
    switch (format) {
      case 'currency': return `$${val.toLocaleString()}`;
      case 'percent': return `${val.toFixed(1)}%`;
      default: return val.toLocaleString();
    }
  };

  return (
    <div className="rounded-xl bg-zinc-900/50 p-6 ring-1 ring-white/10 hover:ring-purple-500/30 transition-all group">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-zinc-400">{label}</p>
          <p className="text-2xl font-bold text-white mt-1">{formatValue(value)}</p>
          {change !== undefined && (
            <div className={`flex items-center gap-1 mt-2 text-sm ${change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {change >= 0 ? <ArrowTrendingUpIcon className="h-4 w-4" /> : <ArrowTrendingDownIcon className="h-4 w-4" />}
              <span>{Math.abs(change).toFixed(1)}%</span>
            </div>
          )}
        </div>
        <div className="rounded-lg bg-purple-500/10 p-3 ring-1 ring-purple-500/20 group-hover:bg-purple-500/20 transition-colors">
          <Icon className="h-6 w-6 text-purple-400" />
        </div>
      </div>
    </div>
  );
}

export function ROIDashboard() {
  const [metrics, setMetrics] = useState<ROIMetrics | null>(null);
  const [chartData, setChartData] = useState<ROIData[]>([]);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Simulated data - replace with actual API calls
        await new Promise(resolve => setTimeout(resolve, 500));

        setMetrics({
          currentROI: 324.5,
          roiChange: 12.3,
          totalSpend: 45680,
          totalRevenue: 193200,
          avgROAS: 4.23,
          predictedROI: 356.8,
        });

        const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90;
        setChartData(
          Array.from({ length: days }, (_, i) => ({
            date: new Date(Date.now() - (days - i - 1) * 86400000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
            roi: 280 + Math.random() * 100,
            spend: 1000 + Math.random() * 500,
            revenue: 4000 + Math.random() * 2000,
            roas: 3.5 + Math.random() * 1.5,
          }))
        );
      } catch (err) {
        console.error('Failed to fetch ROI data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [timeRange]);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-zinc-900/50 rounded-xl" />
          ))}
        </div>
        <div className="h-80 bg-zinc-900/50 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with time range selector */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">ROI Performance</h3>
        <div className="flex gap-2">
          {(['7d', '30d', '90d'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 text-sm rounded-lg transition-all ${
                timeRange === range
                  ? 'bg-purple-500 text-white'
                  : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
              }`}
            >
              {range === '7d' ? '7 Days' : range === '30d' ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>
      </div>

      {/* Metric cards */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={ChartBarIcon}
            label="Current ROI"
            value={metrics.currentROI}
            change={metrics.roiChange}
            format="percent"
          />
          <MetricCard
            icon={CurrencyDollarIcon}
            label="Total Revenue"
            value={metrics.totalRevenue}
            format="currency"
          />
          <MetricCard
            icon={BoltIcon}
            label="Avg ROAS"
            value={metrics.avgROAS}
          />
          <MetricCard
            icon={SparklesIcon}
            label="Predicted ROI"
            value={metrics.predictedROI}
            format="percent"
          />
        </div>
      )}

      {/* ROI Trend Chart */}
      <div className="rounded-xl bg-zinc-900/50 p-6 ring-1 ring-white/10">
        <h4 className="text-sm font-medium text-zinc-400 mb-4">ROI Trend</h4>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="roiGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="date" tick={{ fill: '#71717a', fontSize: 12 }} />
              <YAxis tick={{ fill: '#71717a', fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#18181b',
                  border: '1px solid #3f3f46',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#fff' }}
              />
              <Area
                type="monotone"
                dataKey="roi"
                stroke="#a855f7"
                strokeWidth={2}
                fill="url(#roiGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Revenue vs Spend Chart */}
      <div className="rounded-xl bg-zinc-900/50 p-6 ring-1 ring-white/10">
        <h4 className="text-sm font-medium text-zinc-400 mb-4">Revenue vs Spend</h4>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="date" tick={{ fill: '#71717a', fontSize: 12 }} />
              <YAxis tick={{ fill: '#71717a', fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#18181b',
                  border: '1px solid #3f3f46',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#fff' }}
              />
              <Line type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="spend" stroke="#f59e0b" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center justify-center gap-6 mt-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-emerald-500" />
            <span className="text-sm text-zinc-400">Revenue</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-amber-500" />
            <span className="text-sm text-zinc-400">Spend</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ROIDashboard;
