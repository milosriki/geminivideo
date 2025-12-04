import { useState, useEffect } from 'react';
import { ArrowPathIcon, InformationCircleIcon } from '@heroicons/react/24/outline';

interface CorrelationData {
  metrics: string[];
  matrix: number[][];
}

function getCorrelationColor(value: number): string {
  // Strong positive: purple, neutral: zinc, strong negative: orange
  if (value >= 0.7) return 'bg-purple-500';
  if (value >= 0.5) return 'bg-purple-400/70';
  if (value >= 0.3) return 'bg-purple-300/50';
  if (value >= 0.1) return 'bg-zinc-600';
  if (value >= -0.1) return 'bg-zinc-700';
  if (value >= -0.3) return 'bg-orange-300/50';
  if (value >= -0.5) return 'bg-orange-400/70';
  return 'bg-orange-500';
}

export function CorrelationHeatmap() {
  const [data, setData] = useState<CorrelationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [hoveredCell, setHoveredCell] = useState<{ row: number; col: number } | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Simulated data - replace with actual API call
        await new Promise(resolve => setTimeout(resolve, 400));

        const metrics = ['CTR', 'ROAS', 'CPC', 'Impressions', 'Conversions', 'Engagement'];
        const n = metrics.length;
        const matrix: number[][] = [];

        for (let i = 0; i < n; i++) {
          matrix[i] = [];
          for (let j = 0; j < n; j++) {
            if (i === j) {
              matrix[i][j] = 1;
            } else if (j > i) {
              matrix[i][j] = (Math.random() * 2 - 1) * 0.9;
            } else {
              matrix[i][j] = matrix[j][i];
            }
          }
        }

        setData({ metrics, matrix });
      } catch (err) {
        console.error('Failed to fetch correlation data:', err);
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

  if (!data) {
    return (
      <div className="rounded-xl bg-zinc-900/50 p-6 ring-1 ring-white/10">
        <p className="text-zinc-400">No correlation data available</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-zinc-900/50 p-6 ring-1 ring-white/10">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h4 className="text-lg font-semibold text-white">Metric Correlations</h4>
          <p className="text-sm text-zinc-400 mt-1">How metrics relate to each other</p>
        </div>
        <div className="group relative">
          <InformationCircleIcon className="h-5 w-5 text-zinc-500 cursor-help" />
          <div className="absolute right-0 top-6 w-64 p-3 bg-zinc-800 rounded-lg text-xs text-zinc-300 opacity-0 group-hover:opacity-100 transition-opacity z-10 ring-1 ring-white/10">
            Values range from -1 (negative correlation) to +1 (positive correlation).
            Purple = positive, Orange = negative.
          </div>
        </div>
      </div>

      {/* Heatmap */}
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full">
          {/* Header row */}
          <div className="flex">
            <div className="w-24 h-10 flex-shrink-0" />
            {data.metrics.map((metric, i) => (
              <div
                key={i}
                className="w-16 h-10 flex items-center justify-center text-xs text-zinc-400 font-medium"
              >
                {metric}
              </div>
            ))}
          </div>

          {/* Data rows */}
          {data.matrix.map((row, i) => (
            <div key={i} className="flex">
              <div className="w-24 h-16 flex items-center text-xs text-zinc-400 font-medium flex-shrink-0">
                {data.metrics[i]}
              </div>
              {row.map((value, j) => (
                <div
                  key={j}
                  className={`w-16 h-16 flex items-center justify-center text-xs font-medium rounded-md m-0.5 cursor-pointer transition-transform hover:scale-105 ${getCorrelationColor(value)} ${
                    hoveredCell?.row === i && hoveredCell?.col === j ? 'ring-2 ring-white' : ''
                  }`}
                  onMouseEnter={() => setHoveredCell({ row: i, col: j })}
                  onMouseLeave={() => setHoveredCell(null)}
                >
                  <span className={value > 0.3 || value < -0.3 ? 'text-white' : 'text-zinc-300'}>
                    {value.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-6 pt-4 border-t border-zinc-800">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-orange-500" />
          <span className="text-xs text-zinc-400">Strong Negative</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-zinc-600" />
          <span className="text-xs text-zinc-400">Neutral</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-purple-500" />
          <span className="text-xs text-zinc-400">Strong Positive</span>
        </div>
      </div>

      {/* Hovered cell info */}
      {hoveredCell && (
        <div className="mt-4 p-3 bg-zinc-800 rounded-lg">
          <p className="text-sm text-white">
            <span className="text-zinc-400">Correlation:</span>{' '}
            <span className="font-semibold">{data.metrics[hoveredCell.row]}</span>
            {' ↔ '}
            <span className="font-semibold">{data.metrics[hoveredCell.col]}</span>
            {' = '}
            <span className={data.matrix[hoveredCell.row][hoveredCell.col] > 0 ? 'text-purple-400' : 'text-orange-400'}>
              {data.matrix[hoveredCell.row][hoveredCell.col].toFixed(3)}
            </span>
          </p>
        </div>
      )}
    </div>
  );
}

export default CorrelationHeatmap;
