import React, { useState, useEffect } from 'react';
import { ArrowDownTrayIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

interface ExportSettings {
  resolution: '720p' | '1080p' | '4K';
  format: 'MP4' | 'MOV' | 'WebM';
  quality: 'low' | 'medium' | 'high' | 'ultra';
}

interface ExportPanelProps {
  duration?: number;
  onExport?: (settings: ExportSettings) => void;
}

const RESOLUTION_OPTIONS = [
  { value: '720p', label: '720p (HD)', width: 1280, height: 720 },
  { value: '1080p', label: '1080p (Full HD)', width: 1920, height: 1080 },
  { value: '4K', label: '4K (Ultra HD)', width: 3840, height: 2160 },
] as const;

const FORMAT_OPTIONS = [
  { value: 'MP4', label: 'MP4 (H.264)', description: 'Best compatibility' },
  { value: 'MOV', label: 'MOV (ProRes)', description: 'High quality, large file' },
  { value: 'WebM', label: 'WebM (VP9)', description: 'Web optimized' },
] as const;

const QUALITY_LEVELS = [
  { value: 'low', label: 'Low', bitrate: 2 },
  { value: 'medium', label: 'Medium', bitrate: 5 },
  { value: 'high', label: 'High', bitrate: 10 },
  { value: 'ultra', label: 'Ultra', bitrate: 20 },
] as const;

export const ExportPanel: React.FC<ExportPanelProps> = ({ duration = 25, onExport }) => {
  const [settings, setSettings] = useState<ExportSettings>({
    resolution: '1080p',
    format: 'MP4',
    quality: 'high',
  });
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [estimatedSize, setEstimatedSize] = useState(0);

  useEffect(() => {
    calculateEstimatedSize();
  }, [settings, duration]);

  const calculateEstimatedSize = () => {
    const resolutionMultiplier = {
      '720p': 1,
      '1080p': 2.25,
      '4K': 9,
    }[settings.resolution];

    const qualityBitrate = QUALITY_LEVELS.find(q => q.value === settings.quality)?.bitrate || 5;

    const formatMultiplier = {
      'MP4': 1,
      'MOV': 2.5,
      'WebM': 0.8,
    }[settings.format];

    // Estimate: (bitrate in Mbps * duration in seconds * resolution multiplier * format multiplier) / 8
    const sizeInMB = (qualityBitrate * duration * resolutionMultiplier * formatMultiplier) / 8;
    setEstimatedSize(Math.round(sizeInMB));
  };

  const handleExport = async () => {
    setIsExporting(true);
    setExportProgress(0);

    // Track interval for cleanup
    let interval: ReturnType<typeof setInterval> | null = null;
    let completionTimeout: ReturnType<typeof setTimeout> | null = null;

    const cleanup = () => {
      if (interval) clearInterval(interval);
      if (completionTimeout) clearTimeout(completionTimeout);
    };

    // Simulate export progress
    interval = setInterval(() => {
      setExportProgress(prev => {
        if (prev >= 100) {
          cleanup();
          completionTimeout = setTimeout(() => {
            setIsExporting(false);
            setExportProgress(0);
            onExport?.(settings);
          }, 500);
          return 100;
        }
        return prev + 5;
      });
    }, 200);
  };

  const formatFileSize = (mb: number): string => {
    if (mb < 1024) {
      return `${mb} MB`;
    }
    return `${(mb / 1024).toFixed(2)} GB`;
  };

  return (
    <div className="h-full flex flex-col bg-zinc-900">
      {/* Header */}
      <div className="h-12 bg-zinc-800 border-b border-zinc-700 flex items-center px-4">
        <ArrowDownTrayIcon className="w-5 h-5 text-zinc-400 mr-2" />
        <span className="text-sm font-medium text-zinc-300">Export Settings</span>
      </div>

      {/* Settings */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Resolution */}
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-3">Resolution</label>
          <div className="space-y-2">
            {RESOLUTION_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => setSettings(prev => ({ ...prev, resolution: option.value }))}
                className={`w-full px-4 py-3 rounded-lg border-2 transition-all text-left ${
                  settings.resolution === option.value
                    ? 'border-indigo-500 bg-indigo-500/10 text-white'
                    : 'border-zinc-700 bg-zinc-800 text-zinc-400 hover:border-zinc-600'
                }`}
              >
                <div className="font-medium text-sm">{option.label}</div>
                <div className="text-xs text-zinc-500 mt-0.5">
                  {option.width} × {option.height}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Format */}
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-3">Format</label>
          <div className="space-y-2">
            {FORMAT_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => setSettings(prev => ({ ...prev, format: option.value }))}
                className={`w-full px-4 py-3 rounded-lg border-2 transition-all text-left ${
                  settings.format === option.value
                    ? 'border-indigo-500 bg-indigo-500/10 text-white'
                    : 'border-zinc-700 bg-zinc-800 text-zinc-400 hover:border-zinc-600'
                }`}
              >
                <div className="font-medium text-sm">{option.label}</div>
                <div className="text-xs text-zinc-500 mt-0.5">{option.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Quality */}
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-3">Quality</label>
          <div className="relative">
            <input
              type="range"
              min="0"
              max="3"
              value={QUALITY_LEVELS.findIndex(q => q.value === settings.quality)}
              onChange={(e) => {
                const level = QUALITY_LEVELS[Number(e.target.value)];
                setSettings(prev => ({ ...prev, quality: level.value }));
              }}
              className="w-full accent-indigo-500"
            />
            <div className="flex justify-between mt-2">
              {QUALITY_LEVELS.map((level) => (
                <button
                  key={level.value}
                  onClick={() => setSettings(prev => ({ ...prev, quality: level.value }))}
                  className={`text-xs transition-colors ${
                    settings.quality === level.value ? 'text-indigo-400 font-medium' : 'text-zinc-500'
                  }`}
                >
                  {level.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Estimated File Size */}
        <div className="p-4 bg-zinc-800 rounded-lg border border-zinc-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-zinc-400">Estimated File Size</span>
            <span className="text-lg font-bold text-white">{formatFileSize(estimatedSize)}</span>
          </div>
          <div className="flex items-center justify-between text-xs text-zinc-500">
            <span>Duration: {Math.floor(duration / 60)}:{(duration % 60).toString().padStart(2, '0')}</span>
            <span>
              {QUALITY_LEVELS.find(q => q.value === settings.quality)?.bitrate} Mbps
            </span>
          </div>
        </div>

        {/* Additional Options */}
        <div className="space-y-3">
          <label className="flex items-center gap-3 cursor-pointer group">
            <input
              type="checkbox"
              className="w-4 h-4 rounded border-zinc-600 bg-zinc-800 text-indigo-600
                focus:ring-2 focus:ring-indigo-500 focus:ring-offset-0"
              defaultChecked
            />
            <span className="text-sm text-zinc-400 group-hover:text-zinc-300 transition-colors">
              Include audio
            </span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer group">
            <input
              type="checkbox"
              className="w-4 h-4 rounded border-zinc-600 bg-zinc-800 text-indigo-600
                focus:ring-2 focus:ring-indigo-500 focus:ring-offset-0"
            />
            <span className="text-sm text-zinc-400 group-hover:text-zinc-300 transition-colors">
              Embed subtitles
            </span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer group">
            <input
              type="checkbox"
              className="w-4 h-4 rounded border-zinc-600 bg-zinc-800 text-indigo-600
                focus:ring-2 focus:ring-indigo-500 focus:ring-offset-0"
            />
            <span className="text-sm text-zinc-400 group-hover:text-zinc-300 transition-colors">
              Optimize for web
            </span>
          </label>
        </div>
      </div>

      {/* Export Button */}
      <div className="p-4 border-t border-zinc-700">
        {isExporting ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-zinc-400">Exporting...</span>
              <span className="text-white font-medium">{exportProgress}%</span>
            </div>
            <div className="w-full h-2 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-300 ease-out"
                style={{ width: `${exportProgress}%` }}
              />
            </div>
            {exportProgress === 100 && (
              <div className="flex items-center gap-2 text-green-500 text-sm animate-fade-in">
                <CheckCircleIcon className="w-4 h-4" />
                Export complete!
              </div>
            )}
          </div>
        ) : (
          <button
            onClick={handleExport}
            className="w-full px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500
              hover:to-purple-500 rounded-lg font-medium transition-all shadow-lg hover:shadow-xl
              hover:scale-[1.02] flex items-center justify-center gap-2"
          >
            <ArrowDownTrayIcon className="w-5 h-5" />
            Export Video
          </button>
        )}
      </div>
    </div>
  );
};

export default ExportPanel;
