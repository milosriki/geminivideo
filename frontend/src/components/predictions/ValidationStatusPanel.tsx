import { useState, useEffect } from 'react';
import { CheckCircleIcon, ClockIcon, ExclamationTriangleIcon, ChartBarIcon } from '@heroicons/react/24/outline';

interface ValidationStats {
  totalPredictions: number;
  validatedPredictions: number;
  pendingValidation: number;
  avgValidationTime: string;
  accuracyRate: number;
  lastUpdated: string;
}

function StatusCard({
  icon: Icon,
  label,
  value,
  subValue,
  color
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  subValue?: string;
  color: 'green' | 'yellow' | 'blue' | 'purple';
}) {
  const colorClasses = {
    green: 'bg-emerald-500/10 text-emerald-400 ring-emerald-500/20',
    yellow: 'bg-amber-500/10 text-amber-400 ring-amber-500/20',
    blue: 'bg-blue-500/10 text-blue-400 ring-blue-500/20',
    purple: 'bg-purple-500/10 text-purple-400 ring-purple-500/20',
  };

  return (
    <div className="rounded-xl bg-zinc-900/50 p-6 ring-1 ring-white/10 hover:ring-white/20 transition-all">
      <div className="flex items-center gap-4">
        <div className={`rounded-lg p-3 ring-1 ${colorClasses[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
        <div>
          <p className="text-sm text-zinc-400">{label}</p>
          <p className="text-2xl font-semibold text-white">{value}</p>
          {subValue && <p className="text-xs text-zinc-500 mt-1">{subValue}</p>}
        </div>
      </div>
    </div>
  );
}

export function ValidationStatusPanel() {
  const [stats, setStats] = useState<ValidationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Simulated data - replace with actual API call
        await new Promise(resolve => setTimeout(resolve, 500));
        setStats({
          totalPredictions: 1247,
          validatedPredictions: 1089,
          pendingValidation: 158,
          avgValidationTime: '2.4 hours',
          accuracyRate: 87.3,
          lastUpdated: new Date().toISOString(),
        });
      } catch (err) {
        setError('Failed to fetch validation stats');
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="rounded-xl bg-zinc-900/50 p-6 animate-pulse">
            <div className="h-16 bg-zinc-800 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="rounded-xl bg-red-500/10 p-6 text-red-400 ring-1 ring-red-500/20">
        {error || 'No data available'}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Prediction Validation Status</h3>
        <span className="text-xs text-zinc-500">
          Updated {new Date(stats.lastUpdated).toLocaleTimeString()}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatusCard
          icon={ChartBarIcon}
          label="Total Predictions"
          value={stats.totalPredictions.toLocaleString()}
          subValue="All time"
          color="purple"
        />
        <StatusCard
          icon={CheckCircleIcon}
          label="Validated"
          value={stats.validatedPredictions.toLocaleString()}
          subValue={`${stats.accuracyRate}% accuracy`}
          color="green"
        />
        <StatusCard
          icon={ClockIcon}
          label="Pending"
          value={stats.pendingValidation.toLocaleString()}
          subValue="Awaiting results"
          color="yellow"
        />
        <StatusCard
          icon={ExclamationTriangleIcon}
          label="Avg Validation Time"
          value={stats.avgValidationTime}
          subValue="Time to confirm"
          color="blue"
        />
      </div>

      {/* Progress bar showing validation rate */}
      <div className="rounded-xl bg-zinc-900/50 p-6 ring-1 ring-white/10">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-zinc-400">Validation Progress</span>
          <span className="text-sm font-medium text-white">
            {((stats.validatedPredictions / stats.totalPredictions) * 100).toFixed(1)}%
          </span>
        </div>
        <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full transition-all duration-500"
            style={{ width: `${(stats.validatedPredictions / stats.totalPredictions) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export default ValidationStatusPanel;
