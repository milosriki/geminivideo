import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { ChevronDownIcon } from '@heroicons/react/24/outline';

interface PerformanceDataPoint {
  day: string;
  roas: number;
  spend: number;
  revenue: number;
  clicks: number;
}

interface PerformanceChartProps {
  data?: PerformanceDataPoint[];
  title?: string;
}

type MetricType = 'roas' | 'revenue' | 'spend' | 'clicks';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

const metricConfig = {
  roas: {
    label: 'ROAS',
    color: '#6366f1',
    gradient: 'roasGradient',
    formatter: (value: number) => `${value.toFixed(1)}x`,
    domain: [0, 'auto'],
  },
  revenue: {
    label: 'Revenue',
    color: '#10b981',
    gradient: 'revenueGradient',
    formatter: (value: number) => `$${value.toLocaleString()}`,
    domain: [0, 'auto'],
  },
  spend: {
    label: 'Spend',
    color: '#f59e0b',
    gradient: 'spendGradient',
    formatter: (value: number) => `$${value.toLocaleString()}`,
    domain: [0, 'auto'],
  },
  clicks: {
    label: 'Clicks',
    color: '#8b5cf6',
    gradient: 'clicksGradient',
    formatter: (value: number) => value.toLocaleString(),
    domain: [0, 'auto'],
  },
};

const CustomTooltip = ({ active, payload, label, selectedMetric }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const config = metricConfig[selectedMetric as MetricType];

    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-zinc-900 border border-zinc-700 rounded-lg p-4 shadow-2xl"
      >
        <p className="text-zinc-400 text-xs font-medium uppercase tracking-wide mb-2">
          {label}
        </p>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: config.color }}
            />
            <span className="text-white font-semibold text-base">
              {config.formatter(payload[0].value)}
            </span>
          </div>
          {selectedMetric === 'roas' && (
            <>
              <p className="text-zinc-400 text-sm">
                Spend: <span className="text-white font-medium">${data.spend.toLocaleString()}</span>
              </p>
              <p className="text-emerald-400 text-sm">
                Revenue: <span className="text-white font-medium">${data.revenue.toLocaleString()}</span>
              </p>
            </>
          )}
          {selectedMetric === 'revenue' && (
            <p className="text-zinc-400 text-sm">
              Clicks: <span className="text-white font-medium">{data.clicks.toLocaleString()}</span>
            </p>
          )}
          {selectedMetric === 'spend' && (
            <p className="text-zinc-400 text-sm">
              ROAS: <span className="text-white font-medium">{data.roas.toFixed(1)}x</span>
            </p>
          )}
          {selectedMetric === 'clicks' && (
            <p className="text-zinc-400 text-sm">
              Revenue: <span className="text-white font-medium">${data.revenue.toLocaleString()}</span>
            </p>
          )}
        </div>
      </motion.div>
    );
  }
  return null;
};

export const PerformanceChart: React.FC<PerformanceChartProps> = ({
  data: propsData,
  title = 'Performance (7 Days)',
}) => {
  const [selectedMetric, setSelectedMetric] = useState<MetricType>('roas');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [fetchedData, setFetchedData] = useState<PerformanceDataPoint[]>([]);

  useEffect(() => {
    if (!propsData) {
      const fetchPerformance = async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/api/analytics/performance?days=7`);
          if (response.ok) {
            const result = await response.json();
            setFetchedData(result.data || []);
          }
        } catch (err) {
          console.error('Failed to fetch performance data:', err);
        }
      };
      fetchPerformance();
    }
  }, [propsData]);

  const data = propsData || fetchedData;
  const config = metricConfig[selectedMetric];

  const calculateStats = () => {
    const values = data.map(d => d[selectedMetric]);
    const total = values.reduce((a, b) => a + b, 0);
    const avg = total / values.length;
    const max = Math.max(...values);
    const maxDay = data.find(d => d[selectedMetric] === max)?.day || '';

    return {
      avg: config.formatter(avg),
      max: config.formatter(max),
      maxDay,
      total: selectedMetric === 'spend' || selectedMetric === 'revenue'
        ? config.formatter(total)
        : null,
    };
  };

  const stats = calculateStats();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.2 }}
      className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 sm:p-5 shadow-lg shadow-black/20 h-full"
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-0 mb-4">
        <h3 className="text-white font-semibold text-base sm:text-lg">{title}</h3>

        {/* Metric Selector Dropdown */}
        <div className="relative w-full sm:w-auto">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center justify-center sm:justify-start gap-2 px-3 py-2 sm:py-1.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium transition-colors border border-zinc-700 w-full sm:w-auto min-h-[44px] sm:min-h-0"
          >
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: config.color }}
            />
            {config.label}
            <ChevronDownIcon
              className={`w-4 h-4 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`}
            />
          </button>

          {isDropdownOpen && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setIsDropdownOpen(false)}
              />
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute right-0 mt-2 w-full sm:w-40 bg-zinc-800 border border-zinc-700 rounded-lg shadow-xl z-20 overflow-hidden"
              >
                {(Object.keys(metricConfig) as MetricType[]).map((metric) => {
                  const metricConf = metricConfig[metric];
                  return (
                    <button
                      key={metric}
                      onClick={() => {
                        setSelectedMetric(metric);
                        setIsDropdownOpen(false);
                      }}
                      className={`w-full px-3 py-2.5 text-left text-sm flex items-center gap-2 transition-colors ${selectedMetric === metric
                          ? 'bg-zinc-700 text-white'
                          : 'text-zinc-300 hover:bg-zinc-700/50'
                        }`}
                    >
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: metricConf.color }}
                      />
                      {metricConf.label}
                    </button>
                  );
                })}
              </motion.div>
            </>
          )}
        </div>
      </div>

      <motion.div
        key={selectedMetric}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="h-48 sm:h-64"
      >
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 5, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="spendGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="clicksGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#3f3f46" opacity={0.2} />
            <XAxis
              dataKey="name"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#71717a', fontSize: 12 }}
              dy={10}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#71717a', fontSize: 12 }}
              tickFormatter={config.formatter}
              domain={config.domain as any}
            />
            <Tooltip content={<CustomTooltip selectedMetric={selectedMetric} />} />
            <Area
              type="monotone"
              dataKey={selectedMetric}
              stroke={config.color}
              strokeWidth={3}
              fill={`url(#${config.gradient})`}
              dot={{ fill: config.color, strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: config.color, strokeWidth: 2, fill: '#fff' }}
              animationDuration={500}
            />
          </AreaChart>
        </ResponsiveContainer>
      </motion.div>

      <div className="grid grid-cols-2 sm:flex sm:items-center sm:justify-between gap-4 mt-4 pt-4 border-t border-zinc-800">
        <div>
          <span className="text-zinc-500 text-xs sm:text-sm">Average</span>
          <p className="text-white font-semibold text-sm sm:text-base">{stats.avg}</p>
        </div>
        <div>
          <span className="text-zinc-500 text-xs sm:text-sm">Best Day</span>
          <p className="text-emerald-400 font-semibold text-sm sm:text-base">
            {stats.maxDay} ({stats.max})
          </p>
        </div>
        {stats.total && (
          <div>
            <span className="text-zinc-500 text-xs sm:text-sm">Total</span>
            <p className="text-white font-semibold text-sm sm:text-base">{stats.total}</p>
          </div>
        )}
        {!stats.total && (
          <div>
            <span className="text-zinc-500 text-xs sm:text-sm">Peak</span>
            <p className="text-white font-semibold text-sm sm:text-base">{stats.max}</p>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default PerformanceChart;
