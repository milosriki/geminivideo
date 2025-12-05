/**
 * Multi-Platform Publisher Component
 * Unified interface for publishing to Meta, Google, and TikTok
 * Agent 19: Multi-Platform Publishing Infrastructure
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './MultiPlatformPublisher.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Platform {
  id: 'meta' | 'google' | 'tiktok';
  name: string;
  icon: string;
  enabled: boolean;
  budget: number;
  percentage: number;
}

interface PlatformStatus {
  platform: 'meta' | 'google' | 'tiktok';
  status: 'pending' | 'uploading' | 'processing' | 'live' | 'failed' | 'paused';
  campaignId?: string;
  adId?: string;
  error?: string;
  metrics?: {
    impressions?: number;
    clicks?: number;
    spend?: number;
    ctr?: number;
    roas?: number;
  };
}

interface PublishingJob {
  jobId: string;
  overallStatus: 'pending' | 'in_progress' | 'completed' | 'partial_success' | 'failed';
  platformStatuses: PlatformStatus[];
  successCount: number;
  failureCount: number;
  totalPlatforms: number;
}

interface MultiPlatformPublisherProps {
  creativeId?: string;
  videoPath?: string;
  onPublishSuccess?: (jobId: string) => void;
  onPublishError?: (error: string) => void;
}

const MultiPlatformPublisher: React.FC<MultiPlatformPublisherProps> = ({
  creativeId: initialCreativeId,
  videoPath: initialVideoPath,
  onPublishSuccess,
  onPublishError
}) => {
  const [platforms, setPlatforms] = useState<Platform[]>([
    { id: 'meta', name: 'Meta (Facebook & Instagram)', icon: '📱', enabled: true, budget: 0, percentage: 50 },
    { id: 'google', name: 'Google Ads (YouTube)', icon: '🎥', enabled: true, budget: 0, percentage: 30 },
    { id: 'tiktok', name: 'TikTok', icon: '🎵', enabled: true, budget: 0, percentage: 20 }
  ]);

  const [totalBudget, setTotalBudget] = useState<number>(1000);
  const [campaignName, setCampaignName] = useState<string>('');
  const [creativeId, setCreativeId] = useState<string>(initialCreativeId || '');
  const [videoPath, setVideoPath] = useState<string>(initialVideoPath || '');
  const [caption, setCaption] = useState<string>('');
  const [headline, setHeadline] = useState<string>('');
  const [cta, setCta] = useState<string>('Learn More');

  const [isPublishing, setIsPublishing] = useState<boolean>(false);
  const [publishingJob, setPublishingJob] = useState<PublishingJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState<boolean>(false);
  const [platformSpecs, setPlatformSpecs] = useState<any>(null);

  // Load platform specs on mount
  useEffect(() => {
    loadPlatformSpecs();
  }, []);

  // Calculate budget allocation when total budget or percentages change
  useEffect(() => {
    const updatedPlatforms = platforms.map(platform => ({
      ...platform,
      budget: (totalBudget * platform.percentage) / 100
    }));
    setPlatforms(updatedPlatforms);
  }, [totalBudget]);

  const loadPlatformSpecs = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/platforms/specs`);
      setPlatformSpecs(response.data);
    } catch (error: any) {
      console.error('Error loading platform specs:', error);
    }
  };

  const togglePlatform = (platformId: 'meta' | 'google' | 'tiktok') => {
    setPlatforms(platforms.map(p =>
      p.id === platformId ? { ...p, enabled: !p.enabled } : p
    ));
  };

  const updateBudgetPercentage = (platformId: 'meta' | 'google' | 'tiktok', percentage: number) => {
    // Ensure total percentage is 100%
    const otherPlatforms = platforms.filter(p => p.id !== platformId && p.enabled);
    const remainingPercentage = 100 - percentage;

    if (otherPlatforms.length === 0) {
      // Only one platform enabled, use 100%
      setPlatforms(platforms.map(p =>
        p.id === platformId ? { ...p, percentage: 100, budget: totalBudget } : p
      ));
      return;
    }

    // Distribute remaining percentage among other enabled platforms
    const perPlatform = remainingPercentage / otherPlatforms.length;

    const updatedPlatforms = platforms.map(p => {
      if (p.id === platformId) {
        return { ...p, percentage, budget: (totalBudget * percentage) / 100 };
      } else if (p.enabled) {
        return { ...p, percentage: perPlatform, budget: (totalBudget * perPlatform) / 100 };
      }
      return p;
    });

    setPlatforms(updatedPlatforms);
  };

  const calculateRecommendedAllocation = async () => {
    try {
      const enabledPlatforms = platforms.filter(p => p.enabled).map(p => p.id);

      const response = await axios.post(`${API_BASE}/api/platforms/budget-allocation`, {
        platforms: enabledPlatforms,
        total_budget: totalBudget
      });

      const allocation = response.data.allocation;

      const updatedPlatforms = platforms.map(p => {
        if (p.enabled && allocation[p.id]) {
          const percentage = (allocation[p.id] / totalBudget) * 100;
          return { ...p, percentage, budget: allocation[p.id] };
        }
        return p;
      });

      setPlatforms(updatedPlatforms);
    } catch (error: any) {
      console.error('Error calculating allocation:', error);
    }
  };

  const publishToAllPlatforms = async () => {
    if (!campaignName.trim()) {
      setError('Campaign name is required');
      return;
    }

    if (!videoPath.trim()) {
      setError('Video path is required');
      return;
    }

    const enabledPlatforms = platforms.filter(p => p.enabled);

    if (enabledPlatforms.length === 0) {
      setError('Please select at least one platform');
      return;
    }

    setError(null);
    setIsPublishing(true);

    try {
      // Prepare budget allocation
      const budgetAllocation: Record<string, number> = {};
      enabledPlatforms.forEach(p => {
        budgetAllocation[p.id] = p.budget;
      });

      // Publish to all platforms
      const response = await axios.post(`${API_BASE}/api/publish/multi`, {
        creative_id: creativeId || `creative_${Date.now()}`,
        video_path: videoPath,
        platforms: enabledPlatforms.map(p => p.id),
        budget_allocation: budgetAllocation,
        campaign_name: campaignName,
        creative_config: {
          caption,
          headline,
          cta
        },
        campaign_config: {
          meta: {
            objective: 'OUTCOME_ENGAGEMENT',
            placements: ['instagram_reels', 'facebook_reels']
          },
          google: {
            headline,
            description: caption,
            finalUrl: 'https://example.com'
          },
          tiktok: {
            objective: 'TRAFFIC'
          }
        }
      });

      console.log('Publish response:', response.data);

      setPublishingJob({
        jobId: response.data.job_id,
        overallStatus: response.data.overall_status,
        platformStatuses: response.data.platform_statuses,
        successCount: response.data.platform_statuses.filter((s: PlatformStatus) => s.status === 'live').length,
        failureCount: response.data.platform_statuses.filter((s: PlatformStatus) => s.status === 'failed').length,
        totalPlatforms: enabledPlatforms.length
      });

      // Start polling for status updates
      pollJobStatus(response.data.job_id);

      if (onPublishSuccess) {
        onPublishSuccess(response.data.job_id);
      }

    } catch (error: any) {
      console.error('Publishing error:', error);
      const errorMessage = error.response?.data?.message || error.message;
      setError(errorMessage);

      if (onPublishError) {
        onPublishError(errorMessage);
      }
    } finally {
      setIsPublishing(false);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE}/api/publish/status/${jobId}`);

        const job = response.data.job;
        const platformStatuses = response.data.platformStatuses;

        setPublishingJob({
          jobId: job.jobId,
          overallStatus: job.overallStatus,
          platformStatuses,
          successCount: job.successCount,
          failureCount: job.failureCount,
          totalPlatforms: job.totalPlatforms
        });

        // Stop polling if job is complete
        if (['completed', 'partial_success', 'failed'].includes(job.overallStatus)) {
          clearInterval(pollInterval);
        }

      } catch (error: any) {
        console.error('Error polling job status:', error);
        clearInterval(pollInterval);
      }
    }, 3000); // Poll every 3 seconds

    // Stop polling after 5 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
    }, 300000);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'live':
      case 'completed':
        return '#22c55e';
      case 'processing':
      case 'uploading':
      case 'in_progress':
        return '#f59e0b';
      case 'failed':
        return '#ef4444';
      case 'paused':
        return '#6b7280';
      default:
        return '#9ca3af';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'live':
      case 'completed':
        return '✓';
      case 'processing':
      case 'uploading':
      case 'in_progress':
        return '⟳';
      case 'failed':
        return '✗';
      case 'paused':
        return '❚❚';
      default:
        return '○';
    }
  };

  const renderPlatformSelector = () => (
    <div className="platform-selector">
      <h3>Select Platforms</h3>
      <div className="platforms-grid">
        {platforms.map(platform => (
          <div
            key={platform.id}
            className={`platform-card ${platform.enabled ? 'enabled' : 'disabled'}`}
            onClick={() => togglePlatform(platform.id)}
          >
            <div className="platform-icon">{platform.icon}</div>
            <div className="platform-name">{platform.name}</div>
            <div className="platform-toggle">
              <input
                type="checkbox"
                checked={platform.enabled}
                onChange={() => {}}
                onClick={(e) => e.stopPropagation()}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderBudgetAllocation = () => (
    <div className="budget-allocation">
      <div className="budget-header">
        <h3>Budget Allocation</h3>
        <button
          className="btn-secondary"
          onClick={calculateRecommendedAllocation}
          disabled={isPublishing}
        >
          Auto-Optimize
        </button>
      </div>

      <div className="total-budget">
        <label>Total Budget ($)</label>
        <input
          type="number"
          value={totalBudget}
          onChange={(e) => setTotalBudget(parseFloat(e.target.value) || 0)}
          min="1"
          step="100"
          disabled={isPublishing}
        />
      </div>

      <div className="platform-budgets">
        {platforms.filter(p => p.enabled).map(platform => (
          <div key={platform.id} className="platform-budget">
            <div className="platform-budget-header">
              <span>{platform.icon} {platform.name}</span>
              <span className="budget-amount">${platform.budget.toFixed(2)}</span>
            </div>
            <div className="budget-slider-container">
              <input
                type="range"
                min="0"
                max="100"
                value={platform.percentage}
                onChange={(e) => updateBudgetPercentage(platform.id, parseFloat(e.target.value))}
                className="budget-slider"
                disabled={isPublishing}
              />
              <span className="percentage-label">{platform.percentage.toFixed(0)}%</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderCampaignDetails = () => (
    <div className="campaign-details">
      <h3>Campaign Details</h3>

      <div className="form-group">
        <label>Campaign Name *</label>
        <input
          type="text"
          value={campaignName}
          onChange={(e) => setCampaignName(e.target.value)}
          placeholder="Summer Sale 2024"
          disabled={isPublishing}
        />
      </div>

      <div className="form-group">
        <label>Video Path *</label>
        <input
          type="text"
          value={videoPath}
          onChange={(e) => setVideoPath(e.target.value)}
          placeholder="/path/to/video.mp4"
          disabled={isPublishing}
        />
      </div>

      <div className="form-group">
        <label>Creative ID (Optional)</label>
        <input
          type="text"
          value={creativeId}
          onChange={(e) => setCreativeId(e.target.value)}
          placeholder="creative_123"
          disabled={isPublishing}
        />
      </div>

      <div className="form-group">
        <label>Headline</label>
        <input
          type="text"
          value={headline}
          onChange={(e) => setHeadline(e.target.value)}
          placeholder="Your Amazing Product"
          maxLength={100}
          disabled={isPublishing}
        />
      </div>

      <div className="form-group">
        <label>Caption / Description</label>
        <textarea
          value={caption}
          onChange={(e) => setCaption(e.target.value)}
          placeholder="Tell your story..."
          rows={4}
          maxLength={500}
          disabled={isPublishing}
        />
      </div>

      <div className="form-group">
        <label>Call to Action</label>
        <select
          value={cta}
          onChange={(e) => setCta(e.target.value)}
          disabled={isPublishing}
        >
          <option value="Learn More">Learn More</option>
          <option value="Shop Now">Shop Now</option>
          <option value="Sign Up">Sign Up</option>
          <option value="Watch More">Watch More</option>
          <option value="Download">Download</option>
        </select>
      </div>
    </div>
  );

  const renderPublishingProgress = () => {
    if (!publishingJob) return null;

    return (
      <div className="publishing-progress">
        <h3>Publishing Status</h3>

        <div className="overall-status">
          <div
            className="status-badge"
            style={{ backgroundColor: getStatusColor(publishingJob.overallStatus) }}
          >
            {getStatusIcon(publishingJob.overallStatus)} {publishingJob.overallStatus.toUpperCase().replace('_', ' ')}
          </div>
          <div className="status-summary">
            {publishingJob.successCount}/{publishingJob.totalPlatforms} platforms live
          </div>
        </div>

        <div className="platform-statuses">
          {publishingJob.platformStatuses.map((status, index) => (
            <div key={index} className="platform-status-card">
              <div className="platform-status-header">
                <span className="platform-name">
                  {platforms.find(p => p.id === status.platform)?.icon}{' '}
                  {platforms.find(p => p.id === status.platform)?.name}
                </span>
                <span
                  className="status-indicator"
                  style={{ color: getStatusColor(status.status) }}
                >
                  {getStatusIcon(status.status)} {status.status}
                </span>
              </div>

              {status.campaignId && (
                <div className="platform-details">
                  <div><strong>Campaign:</strong> {status.campaignId}</div>
                  {status.adId && <div><strong>Ad:</strong> {status.adId}</div>}
                </div>
              )}

              {status.error && (
                <div className="platform-error">
                  <strong>Error:</strong> {status.error}
                </div>
              )}

              {status.metrics && (
                <div className="platform-metrics">
                  <div><strong>Impressions:</strong> {status.metrics.impressions?.toLocaleString()}</div>
                  <div><strong>Clicks:</strong> {status.metrics.clicks?.toLocaleString()}</div>
                  <div><strong>CTR:</strong> {((status.metrics.ctr || 0) * 100).toFixed(2)}%</div>
                  <div><strong>Spend:</strong> ${status.metrics.spend?.toFixed(2)}</div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderPlatformSpecs = () => {
    if (!showPreview || !platformSpecs) return null;

    return (
      <div className="platform-specs-modal" onClick={() => setShowPreview(false)}>
        <div className="specs-content" onClick={(e) => e.stopPropagation()}>
          <div className="specs-header">
            <h3>Platform Creative Specifications</h3>
            <button onClick={() => setShowPreview(false)}>✕</button>
          </div>

          <div className="specs-grid">
            {platformSpecs.specs?.map((spec: any, index: number) => (
              <div key={index} className="spec-card">
                <h4>{spec.platform.toUpperCase()}</h4>
                <div className="spec-details">
                  <div><strong>Placement:</strong> {spec.placement}</div>
                  <div><strong>Aspect Ratio:</strong> {spec.aspectRatio}</div>
                  <div><strong>Dimensions:</strong> {spec.width}x{spec.height}</div>
                  <div><strong>Duration:</strong> {spec.minDuration}-{spec.maxDuration}s</div>
                  <div><strong>Max Size:</strong> {spec.maxFileSize}MB</div>
                  <div><strong>Formats:</strong> {spec.formats.join(', ')}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="multi-platform-publisher">
      <div className="publisher-header">
        <h2>Multi-Platform Publishing</h2>
        <p>Publish to Meta, Google, and TikTok simultaneously</p>
      </div>

      {error && (
        <div className="error-banner">
          <strong>Error:</strong> {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {renderPlatformSelector()}
      {renderBudgetAllocation()}
      {renderCampaignDetails()}

      <div className="action-buttons">
        <button
          className="btn-secondary"
          onClick={() => setShowPreview(true)}
          disabled={isPublishing}
        >
          View Platform Specs
        </button>

        <button
          className="btn-primary"
          onClick={publishToAllPlatforms}
          disabled={isPublishing || platforms.filter(p => p.enabled).length === 0}
        >
          {isPublishing ? (
            <>
              <span className="spinner"></span> Publishing...
            </>
          ) : (
            <>Publish to {platforms.filter(p => p.enabled).length} Platform(s)</>
          )}
        </button>
      </div>

      {renderPublishingProgress()}
      {renderPlatformSpecs()}
    </div>
  );
};

export default MultiPlatformPublisher;
