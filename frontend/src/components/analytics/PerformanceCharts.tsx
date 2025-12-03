import React, { useState, useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  TooltipProps,
} from 'recharts';
import { motion } from 'framer-motion';

type MetricKey = 'spend' | 'revenue' | 'roas' | 'conversions';

interface ChartDataPoint {
  date: string;
  spend: number;
  revenue: number;
  roas: number;
  conversions: number;
}

interface MetricConfig {
  key: MetricKey;
  label: string;
  color: string;
  gradient: string;
  prefix?: string;
  suffix?: string;
  decimals?: number;
}

const metrics: MetricConfig[] = [
  {
    key: 'spend',
    label: 'Spend',
    color: '#ef4444',
    gradient: 'spend-gradient',
    prefix: '$',
    decimals: 2,
  },
  {
    key: 'revenue',
    label: 'Revenue',
    color: '#10b981',
    gradient: 'revenue-gradient',
    prefix: '$',
    decimals: 2,
  },
  {
    key: 'roas',
    label: 'ROAS',
    color: '#8b5cf6',
    gradient: 'roas-gradient',
    suffix: 'x',
    decimals: 2,
  },
  {
    key: 'conversions',
    label: 'Conversions',
    color: '#3b82f6',
    gradient: 'conversions-gradient',
    decimals: 0,
  },
];

// Generate realistic mock data for the past 30 days
const generateChartData = (): ChartDataPoint[] => {
  const data: ChartDataPoint[] = [];
  const today = new Date();

  for (let i = 29; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);

    const baseSpend = 800 + Math.random() * 400;
    const baseRoas = 3.2 + Math.random() * 1.5;
    const baseConversions = 30 + Math.random() * 40;

    data.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      spend: Math.round(baseSpend * 100) / 100,
      revenue: Math.round(baseSpend * baseRoas * 100) / 100,
      roas: Math.round(baseRoas * 100) / 100,
      conversions: Math.round(baseConversions),
    });
  }

  return data;
};

const CustomTooltip: React.FC<
  TooltipProps<number, string> & { selectedMetric: MetricConfig }
> = ({ active, payload, selectedMetric }) => {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const data = payload[0].payload as ChartDataPoint;

  return (
    <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-4 shadow-xl">
      <p className="text-sm font-medium text-zinc-400 mb-3">{data.date}</p>

      <div className="space-y-2">
        {metrics.map((metric) => (
          <div key={metric.key} className="flex items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: metric.color }}
              />
              <span className="text-xs text-zinc-500">{metric.label}</span>
            </div>
            <span
              className={`text-sm font-semibold ${
                selectedMetric.key === metric.key ? 'text-white' : 'text-zinc-400'
              }`}
            >
              {metric.prefix}
              {typeof data[metric.key] === 'number'
                ? data[metric.key].toLocaleString('en-US', {
                    minimumFractionDigits: metric.decimals ?? 0,
                    maximumFractionDigits: metric.decimals ?? 0,
                  })
                : data[metric.key]}
              {metric.suffix}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export const PerformanceCharts: React.FC = () => {
  const [selectedMetric, setSelectedMetric] = useState<MetricKey>('revenue');
  const chartData = useMemo(() => generateChartData(), []);

  const activeMetric = metrics.find((m) => m.key === selectedMetric) || metrics[0];

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 shadow-lg">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-zinc-800 rounded-lg">
            <svg
              className="w-5 h-5 text-indigo-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Performance Over Time</h2>
            <p className="text-xs text-zinc-500">Last 30 days</p>
          </div>
        </div>

        {/* Metric Toggle Buttons */}
        <div className="flex flex-wrap gap-2">
          {metrics.map((metric) => (
            <motion.button
              key={metric.key}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setSelectedMetric(metric.key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                selectedMetric === metric.key
                  ? 'text-white shadow-lg'
                  : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200'
              }`}
              style={{
                backgroundColor:
                  selectedMetric === metric.key ? metric.color : undefined,
              }}
            >
              {metric.label}
            </motion.button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={chartData}
            margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id={activeMetric.gradient} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={activeMetric.color} stopOpacity={0.3} />
                <stop offset="95%" stopColor={activeMetric.color} stopOpacity={0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />

            <XAxis
              dataKey="date"
              stroke="#52525b"
              tick={{ fill: '#71717a', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#27272a' }}
            />

            <YAxis
              stroke="#52525b"
              tick={{ fill: '#71717a', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#27272a' }}
              tickFormatter={(value) => {
                if (activeMetric.prefix === '$') {
                  return `$${(value / 1000).toFixed(0)}k`;
                }
                if (value >= 1000) {
                  return `${(value / 1000).toFixed(0)}k`;
                }
                return value.toString();
              }}
            />

            <Tooltip
              content={<CustomTooltip selectedMetric={activeMetric} />}
              cursor={{ stroke: activeMetric.color, strokeWidth: 1, strokeDasharray: '5 5' }}
            />

            <Area
              type="monotone"
              dataKey={selectedMetric}
              stroke={activeMetric.color}
              strokeWidth={3}
              fill={`url(#${activeMetric.gradient})`}
              animationDuration={500}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-zinc-800">
        {metrics.map((metric) => {
          const values = chartData.map((d) => d[metric.key]);
          const total = values.reduce((sum, val) => sum + val, 0);
          const avg = total / values.length;

          return (
            <div key={metric.key} className="text-center">
              <div className="text-xs text-zinc-500 mb-1">{metric.label} Avg</div>
              <div className="text-lg font-semibold" style={{ color: metric.color }}>
                {metric.prefix}
                {avg.toLocaleString('en-US', {
                  minimumFractionDigits: metric.decimals ?? 0,
                  maximumFractionDigits: metric.decimals ?? 0,
                })}
                {metric.suffix}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
