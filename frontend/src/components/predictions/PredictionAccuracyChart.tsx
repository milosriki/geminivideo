import { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { ArrowPathIcon } from '@heroicons/react/24/outline';

interface AccuracyPoint {
  date: string;
  accuracy: number;
  predictions: number;
  validated: number;
}

export function PredictionAccuracyChart() {
  const [data, setData] = useState<AccuracyPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [avgAccuracy, setAvgAccuracy] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Simulated data - replace with actual API call
        await new Promise(resolve => setTimeout(resolve, 400));

        const chartData = Array.from({ length: 14 }, (_, i) => ({
          date: new Date(Date.now() - (13 - i) * 86400000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          accuracy: 75 + Math.random() * 20,
          predictions: Math.floor(50 + Math.random() * 100),
          validated: Math.floor(40 + Math.random() * 80),
        }));

        setData(chartData);
        setAvgAccuracy(chartData.reduce((sum, d) => sum + d.accuracy, 0) / chartData.length);
      } catch (err) {
        console.error('Failed to fetch accuracy data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="rounded-xl bg-zinc-900/50 p-6 ring-1 ring-white/10 h-96 flex items-center justify-center">
        <ArrowPathIcon className="h-8 w-8 text-zinc-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-zinc-900/50 p-6 ring-1 ring-white/10">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h4 className="text-lg font-semibold text-white">Prediction Accuracy</h4>
          <p className="text-sm text-zinc-400 mt-1">Last 14 days performance</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-white">{avgAccuracy.toFixed(1)}%</p>
          <p className="text-xs text-zinc-500">Average accuracy</p>
        </div>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <defs>
              <linearGradient id="accuracyGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis
              dataKey="date"
              tick={{ fill: '#71717a', fontSize: 12 }}
              axisLine={{ stroke: '#3f3f46' }}
            />
            <YAxis
              domain={[60, 100]}
              tick={{ fill: '#71717a', fontSize: 12 }}
              axisLine={{ stroke: '#3f3f46' }}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#18181b',
                border: '1px solid #3f3f46',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#fff' }}
              formatter={(value: number, name: string) => {
                if (name === 'accuracy') return [`${value.toFixed(1)}%`, 'Accuracy'];
                return [value, name];
              }}
            />
            <ReferenceLine
              y={85}
              stroke="#a855f7"
              strokeDasharray="5 5"
              label={{ value: 'Target 85%', fill: '#a855f7', fontSize: 11 }}
            />
            <Line
              type="monotone"
              dataKey="accuracy"
              stroke="#22c55e"
              strokeWidth={2}
              dot={{ fill: '#22c55e', strokeWidth: 0, r: 4 }}
              activeDot={{ r: 6, fill: '#22c55e' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-zinc-800">
        <div className="text-center">
          <p className="text-xl font-semibold text-white">
            {data.reduce((sum, d) => sum + d.predictions, 0).toLocaleString()}
          </p>
          <p className="text-xs text-zinc-500">Total Predictions</p>
        </div>
        <div className="text-center">
          <p className="text-xl font-semibold text-emerald-400">
            {data.reduce((sum, d) => sum + d.validated, 0).toLocaleString()}
          </p>
          <p className="text-xs text-zinc-500">Validated</p>
        </div>
        <div className="text-center">
          <p className="text-xl font-semibold text-purple-400">
            {Math.max(...data.map(d => d.accuracy)).toFixed(1)}%
          </p>
          <p className="text-xs text-zinc-500">Peak Accuracy</p>
        </div>
      </div>
    </div>
  );
}

export default PredictionAccuracyChart;
