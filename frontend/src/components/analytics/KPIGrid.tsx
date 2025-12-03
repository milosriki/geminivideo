import React from 'react';
import { motion } from 'framer-motion';

interface KPIData {
  id: string;
  name: string;
  value: string;
  change: number;
  sparklineData: number[];
  prefix?: string;
  suffix?: string;
}

const Sparkline: React.FC<{ data: number[]; color: string; positive: boolean }> = ({
  data,
  color,
  positive,
}) => {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const width = 80;
  const height = 24;

  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((v - min) / range) * height;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <svg width={width} height={height} className="opacity-80">
      <defs>
        <linearGradient id={`gradient-${color}`} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.4" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline
        points={`0,${height} ${points} ${width},${height}`}
        fill={`url(#gradient-${color})`}
        stroke="none"
      />
      <polyline points={points} fill="none" stroke={color} strokeWidth="2" />
    </svg>
  );
};

const KPICard: React.FC<{ kpi: KPIData; index: number }> = ({ kpi, index }) => {
  const isPositive = kpi.change >= 0;
  const sparklineColor = isPositive ? '#10b981' : '#ef4444';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
      className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 sm:p-5 md:p-6 hover:border-zinc-700 transition-colors duration-200 shadow-lg"
    >
      {/* Metric Name */}
      <div className="text-zinc-500 text-xs font-medium uppercase tracking-wider mb-3">
        {kpi.name}
      </div>

      {/* Value */}
      <div className="flex items-baseline gap-1 mb-3">
        {kpi.prefix && <span className="text-lg sm:text-xl font-semibold text-zinc-300">{kpi.prefix}</span>}
        <span className="text-2xl sm:text-3xl font-bold text-white">{kpi.value}</span>
        {kpi.suffix && <span className="text-lg sm:text-xl font-semibold text-zinc-400">{kpi.suffix}</span>}
      </div>

      {/* Change & Sparkline */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          {isPositive ? (
            <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z"
                clipRule="evenodd"
              />
            </svg>
          ) : (
            <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
          )}
          <span
            className={`text-sm font-semibold ${
              isPositive ? 'text-green-500' : 'text-red-500'
            }`}
          >
            {isPositive ? '+' : ''}
            {kpi.change.toFixed(1)}%
          </span>
        </div>

        <Sparkline data={kpi.sparklineData} color={sparklineColor} positive={isPositive} />
      </div>
    </motion.div>
  );
};

export const KPIGrid: React.FC = () => {
  // Generate realistic sparkline data
  const generateSparkline = (base: number, trend: 'up' | 'down') => {
    const data: number[] = [];
    let value = base;
    for (let i = 0; i < 12; i++) {
      const variance = (Math.random() - 0.5) * base * 0.15;
      const trendAdjust = trend === 'up' ? base * 0.02 : -base * 0.015;
      value = Math.max(0, value + variance + trendAdjust);
      data.push(value);
    }
    return data;
  };

  const kpis: KPIData[] = [
    {
      id: 'roas',
      name: 'ROAS',
      value: '3.42',
      change: 12.3,
      sparklineData: generateSparkline(3.4, 'up'),
      suffix: 'x',
    },
    {
      id: 'revenue',
      name: 'Revenue',
      value: '42,876',
      change: 18.7,
      sparklineData: generateSparkline(42000, 'up'),
      prefix: '$',
    },
    {
      id: 'spend',
      name: 'Spend',
      value: '12,543',
      change: 5.2,
      sparklineData: generateSparkline(12000, 'up'),
      prefix: '$',
    },
    {
      id: 'impressions',
      name: 'Impressions',
      value: '1.25M',
      change: 24.1,
      sparklineData: generateSparkline(1200000, 'up'),
    },
    {
      id: 'clicks',
      name: 'Clicks',
      value: '23,456',
      change: 15.8,
      sparklineData: generateSparkline(23000, 'up'),
    },
    {
      id: 'conversions',
      name: 'Conversions',
      value: '1,234',
      change: 8.4,
      sparklineData: generateSparkline(1200, 'up'),
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
      {kpis.map((kpi, index) => (
        <KPICard key={kpi.id} kpi={kpi} index={index} />
      ))}
    </div>
  );
};
