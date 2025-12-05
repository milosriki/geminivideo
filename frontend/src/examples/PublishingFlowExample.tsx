/**
 * Publishing Flow Example
 * Demonstrates multi-platform publishing with status tracking
 */

import React, { useState } from 'react';
import {
  useMultiPlatformPublish,
  usePublishingProgress,
  usePublishStatus,
} from '../hooks/usePublishing';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { useToastStore } from '../stores/toastStore';

interface PublishingFlowExampleProps {
  campaignId: string;
}

export const PublishingFlowExample: React.FC<PublishingFlowExampleProps> = ({ campaignId }) => {
  const [selectedPlatforms, setSelectedPlatforms] = useState<Array<'meta' | 'google' | 'tiktok'>>(
    []
  );

  const { publishToMeta, publishToGoogle, publishToTikTok, isLoading } =
    useMultiPlatformPublish();
  const { jobs, hasActiveJobs, completedJobs, failedJobs } = usePublishingProgress(campaignId);
  const { addToast } = useToastStore();

  const platforms = [
    { id: 'meta', name: 'Meta (Facebook/Instagram)', icon: '📱', color: 'blue' },
    { id: 'google', name: 'Google Ads', icon: '🔍', color: 'green' },
    { id: 'tiktok', name: 'TikTok Ads', icon: '🎵', color: 'pink' },
  ];

  const togglePlatform = (platform: 'meta' | 'google' | 'tiktok') => {
    setSelectedPlatforms((prev) =>
      prev.includes(platform) ? prev.filter((p) => p !== platform) : [...prev, platform]
    );
  };

  const handlePublish = async () => {
    if (selectedPlatforms.length === 0) {
      addToast({
        title: 'No Platforms Selected',
        message: 'Please select at least one platform to publish to',
        variant: 'warning',
      });
      return;
    }

    try {
      for (const platform of selectedPlatforms) {
        const request = {
          campaignId,
          platform,
          adAccountId: `act_${Math.random().toString(36).substr(2, 9)}`, // Demo ID
        };

        if (platform === 'meta') {
          await publishToMeta(request);
        } else if (platform === 'google') {
          await publishToGoogle(request);
        } else if (platform === 'tiktok') {
          await publishToTikTok(request);
        }

        addToast({
          title: `Publishing to ${platform}`,
          message: 'Your campaign is being published',
          variant: 'info',
        });
      }

      addToast({
        title: 'Publishing Started',
        message: `Publishing to ${selectedPlatforms.length} platform(s)`,
        variant: 'success',
      });
    } catch (error: any) {
      addToast({
        title: 'Publishing Failed',
        message: error.message || 'Failed to start publishing',
        variant: 'error',
      });
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Multi-Platform Publishing</h1>
          <p className="text-gray-400">Publish your campaign to multiple ad platforms</p>
        </div>

        {/* Platform Selection */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold text-white mb-4">Select Platforms</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {platforms.map((platform) => {
              const isSelected = selectedPlatforms.includes(platform.id as any);
              return (
                <button
                  key={platform.id}
                  onClick={() => togglePlatform(platform.id as any)}
                  className={`p-6 rounded-lg border-2 transition-all ${
                    isSelected
                      ? 'border-indigo-500 bg-indigo-900/30'
                      : 'border-gray-700 bg-gray-900/50 hover:border-gray-600'
                  }`}
                >
                  <div className="text-4xl mb-2">{platform.icon}</div>
                  <h3 className="font-semibold text-white mb-1">{platform.name}</h3>
                  <p className="text-xs text-gray-400">
                    {isSelected ? 'Selected' : 'Click to select'}
                  </p>
                </button>
              );
            })}
          </div>

          <button
            onClick={handlePublish}
            disabled={isLoading || selectedPlatforms.length === 0}
            className="mt-6 w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg font-semibold text-white transition-colors"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <LoadingSpinner size="sm" />
                Publishing...
              </span>
            ) : (
              `Publish to ${selectedPlatforms.length} Platform${selectedPlatforms.length !== 1 ? 's' : ''}`
            )}
          </button>
        </div>

        {/* Publishing Status */}
        {jobs && jobs.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">Publishing Status</h2>

            {hasActiveJobs && (
              <div className="mb-6 p-4 bg-blue-900/20 border border-blue-500/50 rounded-lg">
                <div className="flex items-center gap-2">
                  <LoadingSpinner size="sm" />
                  <p className="text-blue-300 font-medium">Publishing in progress...</p>
                </div>
              </div>
            )}

            <div className="space-y-4">
              {jobs.map((job) => (
                <PublishJobCard key={job.jobId} jobId={job.jobId} />
              ))}
            </div>

            {/* Summary */}
            <div className="mt-6 pt-6 border-t border-gray-700 grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-white">{jobs.length}</p>
                <p className="text-sm text-gray-400">Total Jobs</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-400">{completedJobs.length}</p>
                <p className="text-sm text-gray-400">Completed</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-red-400">{failedJobs.length}</p>
                <p className="text-sm text-gray-400">Failed</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const PublishJobCard: React.FC<{ jobId: string }> = ({ jobId }) => {
  const { data: status, isLoading } = usePublishStatus(jobId);

  if (isLoading) {
    return (
      <div className="p-4 bg-gray-900/50 rounded-lg">
        <div className="flex items-center gap-3">
          <LoadingSpinner size="sm" />
          <p className="text-gray-400">Loading job status...</p>
        </div>
      </div>
    );
  }

  if (!status) return null;

  const statusColors = {
    pending: 'bg-yellow-900/20 border-yellow-500/50 text-yellow-400',
    processing: 'bg-blue-900/20 border-blue-500/50 text-blue-400',
    completed: 'bg-green-900/20 border-green-500/50 text-green-400',
    failed: 'bg-red-900/20 border-red-500/50 text-red-400',
  };

  const statusIcons = {
    pending: '⏳',
    processing: '⚙️',
    completed: '✅',
    failed: '❌',
  };

  return (
    <div className={`p-4 rounded-lg border ${statusColors[status.status]}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{statusIcons[status.status]}</span>
          <div>
            <p className="font-semibold text-white capitalize">{status.platform}</p>
            <p className="text-sm text-gray-400">Job ID: {status.jobId}</p>
          </div>
        </div>
        <div className="text-right">
          <p className={`font-semibold capitalize ${statusColors[status.status]}`}>
            {status.status}
          </p>
          {status.progress > 0 && (
            <p className="text-sm text-gray-400">{status.progress}% complete</p>
          )}
        </div>
      </div>

      {status.message && (
        <p className="mt-2 text-sm text-gray-300">{status.message}</p>
      )}

      {status.status === 'completed' && status.externalId && (
        <p className="mt-2 text-sm text-green-400">
          External ID: {status.externalId}
        </p>
      )}

      {status.status === 'failed' && status.error && (
        <p className="mt-2 text-sm text-red-400">
          Error: {status.error}
        </p>
      )}

      {/* Progress Bar */}
      {status.status === 'processing' && (
        <div className="mt-3 w-full bg-gray-700 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${status.progress}%` }}
          />
        </div>
      )}
    </div>
  );
};

export default PublishingFlowExample;
