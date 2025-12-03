import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface SetupStepProps {
  data: {
    name: string;
    objective: string;
    budget: number;
    platforms: string[];
    targetAudience?: string;
  };
  onUpdate: (data: Partial<SetupStepProps['data']>) => void;
  onNext: () => void;
}

const OBJECTIVES = [
  { value: 'conversions', label: 'Conversions', description: 'Drive sales and actions' },
  { value: 'traffic', label: 'Traffic', description: 'Increase website visits' },
  { value: 'awareness', label: 'Awareness', description: 'Build brand recognition' },
  { value: 'engagement', label: 'Engagement', description: 'Get likes, shares, comments' },
];

const PLATFORMS = [
  { id: 'meta', name: 'Meta', color: 'bg-blue-600' },
  { id: 'tiktok', name: 'TikTok', color: 'bg-pink-500' },
  { id: 'youtube', name: 'YouTube', color: 'bg-red-600' },
  { id: 'google', name: 'Google', color: 'bg-green-600' },
];

const AUDIENCES = [
  { value: 'young-adults', label: 'Young Adults (18-34)' },
  { value: 'professionals', label: 'Professionals (25-54)' },
  { value: 'seniors', label: 'Seniors (55+)' },
  { value: 'custom', label: 'Custom Audience' },
];

export const SetupStep: React.FC<SetupStepProps> = ({ data, onUpdate, onNext }) => {
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handlePlatformToggle = (platformId: string) => {
    const newPlatforms = data.platforms.includes(platformId)
      ? data.platforms.filter((p) => p !== platformId)
      : [...data.platforms, platformId];
    onUpdate({ platforms: newPlatforms });
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!data.name.trim()) {
      newErrors.name = 'Campaign name is required';
    }

    if (!data.objective) {
      newErrors.objective = 'Please select an objective';
    }

    if (data.budget <= 0) {
      newErrors.budget = 'Budget must be greater than 0';
    }

    if (data.platforms.length === 0) {
      newErrors.platforms = 'Select at least one platform';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateForm()) {
      onNext();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Campaign Name */}
      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-2">
          Campaign Name <span className="text-red-400">*</span>
        </label>
        <input
          type="text"
          value={data.name}
          onChange={(e) => onUpdate({ name: e.target.value })}
          placeholder="e.g., Summer Sale 2024"
          className={`w-full px-4 py-3 bg-zinc-800 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all ${
            errors.name ? 'border-red-500' : 'border-zinc-700'
          }`}
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-400">{errors.name}</p>
        )}
      </div>

      {/* Objective */}
      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-3">
          Campaign Objective <span className="text-red-400">*</span>
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {OBJECTIVES.map((obj) => (
            <button
              key={obj.value}
              onClick={() => onUpdate({ objective: obj.value })}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                data.objective === obj.value
                  ? 'border-indigo-500 bg-indigo-500/10'
                  : 'border-zinc-700 bg-zinc-800/60 hover:border-zinc-600'
              }`}
            >
              <div className="font-medium text-white">{obj.label}</div>
              <div className="text-sm text-zinc-400 mt-1">{obj.description}</div>
            </button>
          ))}
        </div>
        {errors.objective && (
          <p className="mt-1 text-sm text-red-400">{errors.objective}</p>
        )}
      </div>

      {/* Budget */}
      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-2">
          Daily Budget <span className="text-red-400">*</span>
        </label>
        <div className="relative">
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400">
            $
          </span>
          <input
            type="number"
            value={data.budget || ''}
            onChange={(e) => onUpdate({ budget: Number(e.target.value) })}
            placeholder="0"
            min="1"
            className={`w-full pl-8 pr-4 py-3 bg-zinc-800 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all ${
              errors.budget ? 'border-red-500' : 'border-zinc-700'
            }`}
          />
        </div>
        {errors.budget && (
          <p className="mt-1 text-sm text-red-400">{errors.budget}</p>
        )}
        <p className="mt-1 text-sm text-zinc-500">
          Recommended minimum: $50/day for optimal results
        </p>
      </div>

      {/* Platforms */}
      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-3">
          Select Platforms <span className="text-red-400">*</span>
        </label>
        <div className="grid grid-cols-2 gap-3">
          {PLATFORMS.map((platform) => (
            <button
              key={platform.id}
              onClick={() => handlePlatformToggle(platform.id)}
              className={`p-4 rounded-lg border-2 transition-all ${
                data.platforms.includes(platform.id)
                  ? 'border-indigo-500 bg-indigo-500/10'
                  : 'border-zinc-700 bg-zinc-800/60 hover:border-zinc-600'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className={`w-4 h-4 rounded ${platform.color}`} />
                <span className="font-medium text-white">{platform.name}</span>
              </div>
            </button>
          ))}
        </div>
        {errors.platforms && (
          <p className="mt-1 text-sm text-red-400">{errors.platforms}</p>
        )}
      </div>

      {/* Target Audience */}
      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-2">
          Target Audience
        </label>
        <select
          value={data.targetAudience || ''}
          onChange={(e) => onUpdate({ targetAudience: e.target.value })}
          className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        >
          <option value="">Select an audience</option>
          {AUDIENCES.map((audience) => (
            <option key={audience.value} value={audience.value}>
              {audience.label}
            </option>
          ))}
        </select>
      </div>

      {/* Next Button */}
      <div className="flex justify-end pt-4">
        <button
          onClick={handleNext}
          className="px-8 py-3 bg-indigo-500 hover:bg-indigo-600 text-white font-medium rounded-lg transition-colors shadow-lg shadow-indigo-500/30"
        >
          Next Step
        </button>
      </div>
    </motion.div>
  );
};
