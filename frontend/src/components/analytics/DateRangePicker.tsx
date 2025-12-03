import React, { useState } from 'react';
import { useAnalyticsStore } from '../../stores/analyticsStore';

type PresetKey = 'today' | '7d' | '30d' | '90d';

interface DatePreset {
  key: PresetKey;
  label: string;
  getDates: () => { start: Date; end: Date };
}

const presets: DatePreset[] = [
  {
    key: 'today',
    label: 'Today',
    getDates: () => {
      const start = new Date();
      start.setHours(0, 0, 0, 0);
      const end = new Date();
      end.setHours(23, 59, 59, 999);
      return { start, end };
    },
  },
  {
    key: '7d',
    label: 'Last 7 Days',
    getDates: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(start.getDate() - 7);
      return { start, end };
    },
  },
  {
    key: '30d',
    label: 'Last 30 Days',
    getDates: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(start.getDate() - 30);
      return { start, end };
    },
  },
  {
    key: '90d',
    label: 'Last 90 Days',
    getDates: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(start.getDate() - 90);
      return { start, end };
    },
  },
];

export const DateRangePicker: React.FC = () => {
  const { dateRange, setDateRange } = useAnalyticsStore();
  const [activePreset, setActivePreset] = useState<PresetKey>('30d');
  const [compareEnabled, setCompareEnabled] = useState(false);

  const handlePresetClick = (preset: DatePreset) => {
    const dates = preset.getDates();
    setDateRange(dates);
    setActivePreset(preset.key);
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 shadow-lg">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        {/* Preset Buttons */}
        <div className="flex flex-wrap gap-2">
          {presets.map((preset) => (
            <button
              key={preset.key}
              onClick={() => handlePresetClick(preset)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                activePreset === preset.key
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                  : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>

        {/* Date Display & Compare Toggle */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          {/* Custom Range Display */}
          <div className="flex items-center gap-2 px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg">
            <svg
              className="w-4 h-4 text-zinc-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <span className="text-sm text-zinc-300">
              {formatDate(dateRange.start)} - {formatDate(dateRange.end)}
            </span>
          </div>

          {/* Compare Toggle */}
          <label className="flex items-center gap-2 cursor-pointer group">
            <div className="relative">
              <input
                type="checkbox"
                checked={compareEnabled}
                onChange={(e) => setCompareEnabled(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-zinc-700 rounded-full peer-checked:bg-indigo-600 transition-colors duration-200"></div>
              <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform duration-200 peer-checked:translate-x-5"></div>
            </div>
            <span className="text-sm text-zinc-400 group-hover:text-zinc-300 transition-colors">
              Compare to previous period
            </span>
          </label>
        </div>
      </div>

      {/* Previous Period Info */}
      {compareEnabled && (
        <div className="mt-4 pt-4 border-t border-zinc-800">
          <div className="flex items-center gap-2 text-sm text-zinc-500">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>
              Comparing to:{' '}
              {(() => {
                const daysDiff = Math.round(
                  (dateRange.end.getTime() - dateRange.start.getTime()) / (1000 * 60 * 60 * 24)
                );
                const prevEnd = new Date(dateRange.start);
                prevEnd.setDate(prevEnd.getDate() - 1);
                const prevStart = new Date(prevEnd);
                prevStart.setDate(prevStart.getDate() - daysDiff);
                return `${formatDate(prevStart)} - ${formatDate(prevEnd)}`;
              })()}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
