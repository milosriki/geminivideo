import React from 'react';
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

interface PerformanceDataPoint {
  day: string;
  roas: number;
  spend?: number;
  revenue?: number;
}

interface PerformanceChartProps {
  data?: PerformanceDataPoint[];
  title?: string;
}

const mockPerformanceData: PerformanceDataPoint[] = [
  { day: 'Mon', roas: 3.2, spend: 1200, revenue: 3840 },
  { day: 'Tue', roas: 3.8, spend: 1400, revenue: 5320 },
  { day: 'Wed', roas: 3.5, spend: 1100, revenue: 3850 },
  { day: 'Thu', roas: 4.1, spend: 1600, revenue: 6560 },
  { day: 'Fri', roas: 4.5, spend: 1800, revenue: 8100 },
  { day: 'Sat', roas: 4.8, spend: 2000, revenue: 9600 },
  { day: 'Sun', roas: 4.2, spend: 1500, revenue: 6300 },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-3 shadow-xl">
        <p className="text-zinc-400 text-sm mb-1">{label}</p>
        <p className="text-white font-semibold text-lg">
          ROAS: {payload[0].value.toFixed(1)}x
        </p>
        {payload[0].payload.spend && (
          <p className="text-zinc-400 text-sm mt-1">
            Spend: ${payload[0].payload.spend.toLocaleString()}
          </p>
        )}
        {payload[0].payload.revenue && (
          <p className="text-emerald-400 text-sm">
            Revenue: ${payload[0].payload.revenue.toLocaleString()}
          </p>
        )}
      </div>
    );
  }
  return null;
};

export const PerformanceChart: React.FC<PerformanceChartProps> = ({
  data = mockPerformanceData,
  title = 'Performance (7 Days)',
}) => {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-lg shadow-black/20 h-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white font-semibold text-lg">{title}</h3>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-indigo-500" />
            <span className="text-zinc-400 text-sm">ROAS</span>
          </div>
        </div>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="roasGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
            <XAxis
              dataKey="day"
              stroke="#71717a"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#71717a"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value}x`}
              domain={[0, 'auto']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="roas"
              stroke="#6366f1"
              strokeWidth={3}
              fill="url(#roasGradient)"
              dot={{ fill: '#6366f1', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: '#6366f1', strokeWidth: 2, fill: '#fff' }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between mt-4 pt-4 border-t border-zinc-800">
        <div>
          <span className="text-zinc-500 text-sm">Avg ROAS</span>
          <p className="text-white font-semibold">4.0x</p>
        </div>
        <div>
          <span className="text-zinc-500 text-sm">Best Day</span>
          <p className="text-emerald-400 font-semibold">Sat (4.8x)</p>
        </div>
        <div>
          <span className="text-zinc-500 text-sm">Total Spend</span>
          <p className="text-white font-semibold">$10,600</p>
        </div>
      </div>
    </div>
  );
};

export default PerformanceChart;
