import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { CheckIcon, SparklesIcon } from '../icons';

interface ReviewStepProps {
  setupData: {
    name: string;
    objective: string;
    budget: number;
    platforms: string[];
    targetAudience?: string;
  };
  creativeData: {
    uploadedFiles?: File[];
    style?: string;
    scriptTemplate?: string;
    hookStyle?: string;
    variants?: number;
    selectedAvatar?: string;
  };
  onEdit: (step: number) => void;
  onBack: () => void;
  onLaunch: () => void;
  isLaunching?: boolean;
}

const PLATFORM_NAMES: Record<string, string> = {
  meta: 'Meta',
  tiktok: 'TikTok',
  youtube: 'YouTube',
  google: 'Google',
};

const OBJECTIVE_LABELS: Record<string, string> = {
  conversions: 'Conversions',
  traffic: 'Traffic',
  awareness: 'Awareness',
  engagement: 'Engagement',
};

const STYLE_LABELS: Record<string, string> = {
  ugc: 'UGC',
  professional: 'Professional',
  mixed: 'Mixed',
};

export const ReviewStep: React.FC<ReviewStepProps> = ({
  setupData,
  creativeData,
  onEdit,
  onBack,
  onLaunch,
  isLaunching = false,
}) => {
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Campaign Setup Summary */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">Campaign Setup</h3>
          <button
            onClick={() => onEdit(1)}
            className="text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            Edit
          </button>
        </div>
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <dt className="text-sm text-zinc-400 mb-1">Campaign Name</dt>
            <dd className="font-medium text-white">{setupData.name || 'Untitled'}</dd>
          </div>
          <div>
            <dt className="text-sm text-zinc-400 mb-1">Objective</dt>
            <dd className="font-medium text-white">
              {OBJECTIVE_LABELS[setupData.objective] || setupData.objective}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-zinc-400 mb-1">Daily Budget</dt>
            <dd className="font-medium text-white">${setupData.budget.toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-sm text-zinc-400 mb-1">Platforms</dt>
            <dd className="flex flex-wrap gap-2">
              {setupData.platforms.map((platform) => (
                <span
                  key={platform}
                  className="px-2 py-1 bg-indigo-500/20 border border-indigo-500/50 text-indigo-300 rounded text-sm"
                >
                  {PLATFORM_NAMES[platform] || platform}
                </span>
              ))}
            </dd>
          </div>
          {setupData.targetAudience && (
            <div className="col-span-2">
              <dt className="text-sm text-zinc-400 mb-1">Target Audience</dt>
              <dd className="font-medium text-white capitalize">
                {setupData.targetAudience.replace('-', ' ')}
              </dd>
            </div>
          )}
        </dl>
      </div>

      {/* Creative Settings Summary */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">Creative Settings</h3>
          <button
            onClick={() => onEdit(2)}
            className="text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            Edit
          </button>
        </div>
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <dt className="text-sm text-zinc-400 mb-1">Uploaded Files</dt>
            <dd className="font-medium text-white">
              {creativeData.uploadedFiles?.length || 0} file(s)
            </dd>
          </div>
          <div>
            <dt className="text-sm text-zinc-400 mb-1">Style</dt>
            <dd className="font-medium text-white">
              {creativeData.style ? STYLE_LABELS[creativeData.style] : 'Not selected'}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-zinc-400 mb-1">Script Template</dt>
            <dd className="font-medium text-white capitalize">
              {creativeData.scriptTemplate?.replace('-', ' ') || 'Not selected'}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-zinc-400 mb-1">Hook Style</dt>
            <dd className="font-medium text-white capitalize">
              {creativeData.hookStyle || 'Not selected'}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-zinc-400 mb-1">Variants</dt>
            <dd className="font-medium text-white">{creativeData.variants || 1}</dd>
          </div>
          <div>
            <dt className="text-sm text-zinc-400 mb-1">AI Avatar</dt>
            <dd className="font-medium text-white">
              {creativeData.selectedAvatar ? 'Selected' : 'Not selected'}
            </dd>
          </div>
        </dl>
      </div>

      {/* Preview Placeholder */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">Preview</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: creativeData.variants || 1 }).map((_, index) => (
            <div
              key={index}
              className="aspect-video bg-zinc-800 rounded-lg flex items-center justify-center border border-zinc-700"
            >
              <div className="text-center">
                <SparklesIcon className="w-8 h-8 text-zinc-600 mx-auto mb-2" />
                <p className="text-sm text-zinc-500">Variant {index + 1}</p>
                <p className="text-xs text-zinc-600 mt-1">Preview after generation</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Schedule */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">Schedule Launch</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-zinc-400 mb-2">Start Date</label>
            <input
              type="date"
              value={scheduleDate}
              onChange={(e) => setScheduleDate(e.target.value)}
              className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-2">Start Time</label>
            <input
              type="time"
              value={scheduleTime}
              onChange={(e) => setScheduleTime(e.target.value)}
              className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
        </div>
        {!scheduleDate && (
          <p className="mt-3 text-sm text-zinc-500">
            Leave empty to launch immediately
          </p>
        )}
      </div>

      {/* Warning */}
      <div className="bg-yellow-900/20 border border-yellow-700/50 rounded-lg p-4">
        <div className="flex gap-3">
          <span className="text-yellow-500 text-xl">⚠️</span>
          <div>
            <p className="text-sm text-yellow-300 font-medium">
              Ready to launch?
            </p>
            <p className="text-sm text-yellow-200/80 mt-1">
              Your campaign will start running{' '}
              {scheduleDate ? 'at the scheduled time' : 'immediately'} after
              publishing. You can pause or edit it at any time from the dashboard.
            </p>
          </div>
        </div>
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between pt-4">
        <button
          onClick={onBack}
          className="px-6 py-3 border border-zinc-600 text-zinc-300 rounded-lg hover:bg-zinc-800 transition-colors"
          disabled={isLaunching}
        >
          Back
        </button>
        <button
          onClick={onLaunch}
          disabled={isLaunching}
          className="px-8 py-3 bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600 text-white font-bold rounded-lg transition-all shadow-lg shadow-green-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isLaunching ? (
            <>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
              />
              <span>Launching...</span>
            </>
          ) : (
            <>
              <CheckIcon className="w-5 h-5" />
              <span>Launch Campaign</span>
            </>
          )}
        </button>
      </div>
    </motion.div>
  );
};
