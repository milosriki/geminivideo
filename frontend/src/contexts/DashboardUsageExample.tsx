/**
 * Dashboard API and Context Usage Examples
 * Agent 11: Frontend Dashboard Integration Engineer
 *
 * This file demonstrates how to use the Dashboard API client
 * and React context in your components.
 */

import React, { useEffect, useState } from 'react';
import { useDashboard } from './DashboardContext';
import type { ApprovalItem, MetaInsights } from '../services/dashboardAPI';

// ============================================================================
// EXAMPLE 1: Using the Context Hook in a Component
// ============================================================================

export const ApprovalQueueComponent: React.FC = () => {
  const {
    getApprovalQueue,
    approveAd,
    rejectAd,
    isLoading,
    getError,
  } = useDashboard();

  const [approvalItems, setApprovalItems] = useState<ApprovalItem[]>([]);

  useEffect(() => {
    loadApprovalQueue();
  }, []);

  const loadApprovalQueue = async () => {
    const items = await getApprovalQueue(false); // Don't use cache
    if (items) {
      setApprovalItems(items);
    }
  };

  const handleApprove = async (adId: string) => {
    const success = await approveAd(adId, 'Looks great!');
    if (success) {
      await loadApprovalQueue(); // Refresh the queue
    }
  };

  const handleReject = async (adId: string) => {
    const success = await rejectAd(adId, 'Needs improvement');
    if (success) {
      await loadApprovalQueue(); // Refresh the queue
    }
  };

  const loading = isLoading('approvalQueue');
  const error = getError('approvalQueue');

  if (loading) {
    return <div>Loading approval queue...</div>;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  return (
    <div>
      <h2>Approval Queue ({approvalItems.length} items)</h2>
      {approvalItems.map((item) => (
        <div key={item.ad_id} style={{ border: '1px solid #ccc', padding: '10px', margin: '10px 0' }}>
          <h3>Ad: {item.ad_id}</h3>
          <p>CTR Prediction: {(item.predicted_ctr * 100).toFixed(2)}%</p>
          <p>ROAS Prediction: {item.predicted_roas.toFixed(2)}</p>
          <p>Status: {item.status}</p>
          <button onClick={() => handleApprove(item.ad_id)}>Approve</button>
          <button onClick={() => handleReject(item.ad_id)}>Reject</button>
        </div>
      ))}
    </div>
  );
};

// ============================================================================
// EXAMPLE 2: Video Analysis Component
// ============================================================================

export const VideoAnalysisComponent: React.FC = () => {
  const { analyzeVideo, getAnalysisStatus, isLoading, getError } = useDashboard();
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('');

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const result = await analyzeVideo(file);
    if (result) {
      setAnalysisId(result.asset_id);
      pollAnalysisStatus(result.asset_id);
    }
  };

  const pollAnalysisStatus = async (id: string) => {
    const interval = setInterval(async () => {
      const statusResult = await getAnalysisStatus(id);
      if (statusResult) {
        setStatus(statusResult.status);
        if (statusResult.status === 'COMPLETED' || statusResult.status === 'FAILED') {
          clearInterval(interval);
        }
      }
    }, 2000); // Poll every 2 seconds
  };

  const loading = isLoading(`analyzeVideo_*`);
  const error = getError(`analyzeVideo_*`);

  return (
    <div>
      <h2>Video Analysis</h2>
      <input type="file" accept="video/*" onChange={handleFileUpload} disabled={loading} />
      {loading && <p>Analyzing video...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error.message}</p>}
      {analysisId && <p>Analysis ID: {analysisId}</p>}
      {status && <p>Status: {status}</p>}
    </div>
  );
};

// ============================================================================
// EXAMPLE 3: Meta Insights Dashboard
// ============================================================================

export const MetaInsightsDashboard: React.FC = () => {
  const {
    getMetaInsights,
    triggerMetaRefresh,
    getTopPerformers,
    isLoading,
    getError,
  } = useDashboard();

  const [insights, setInsights] = useState<MetaInsights | null>(null);

  useEffect(() => {
    loadInsights();
  }, []);

  const loadInsights = async () => {
    const data = await getMetaInsights(true); // Use cache
    if (data) {
      setInsights(data);
    }
  };

  const handleRefresh = async () => {
    const result = await triggerMetaRefresh();
    if (result && result.status === 'accepted') {
      // Wait a bit then reload
      setTimeout(loadInsights, 3000);
    }
  };

  const loading = isLoading('metaInsights');
  const error = getError('metaInsights');

  if (loading) {
    return <div>Loading insights...</div>;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  return (
    <div>
      <h2>Meta Learning Insights</h2>
      <button onClick={handleRefresh}>Refresh Data</button>
      {insights && (
        <div>
          <p>Campaigns Analyzed: {insights.campaigns_analyzed}</p>
          <p>Average CTR: {(insights.avg_ctr * 100).toFixed(2)}%</p>
          <p>Average ROAS: {insights.avg_roas.toFixed(2)}</p>
          <h3>Top Performers</h3>
          <ul>
            {insights.top_performers.map((performer) => (
              <li key={performer.ad_id}>
                {performer.ad_id}: CTR {(performer.ctr * 100).toFixed(2)}%, ROAS {performer.roas.toFixed(2)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// EXAMPLE 4: Render Job Monitor
// ============================================================================

export const RenderJobMonitor: React.FC<{ jobId: string }> = ({ jobId }) => {
  const { getRenderStatus, cancelRenderJob, downloadRenderedVideo } = useDashboard();
  const [status, setStatus] = useState<string>('');
  const [progress, setProgress] = useState<number>(0);

  useEffect(() => {
    const interval = setInterval(async () => {
      const result = await getRenderStatus(jobId);
      if (result) {
        setStatus(result.status);
        setProgress(result.progress);

        if (result.status === 'COMPLETED' || result.status === 'FAILED') {
          clearInterval(interval);
        }
      }
    }, 1000); // Poll every second

    return () => clearInterval(interval);
  }, [jobId, getRenderStatus]);

  const handleCancel = async () => {
    await cancelRenderJob(jobId);
  };

  const handleDownload = async () => {
    const blob = await downloadRenderedVideo(jobId);
    if (blob) {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `render_${jobId}.mp4`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div>
      <h3>Render Job: {jobId}</h3>
      <p>Status: {status}</p>
      <p>Progress: {progress}%</p>
      <div style={{ width: '100%', height: '20px', backgroundColor: '#eee' }}>
        <div style={{ width: `${progress}%`, height: '100%', backgroundColor: '#4caf50' }} />
      </div>
      {status === 'PROCESSING' && <button onClick={handleCancel}>Cancel</button>}
      {status === 'COMPLETED' && <button onClick={handleDownload}>Download Video</button>}
    </div>
  );
};

// ============================================================================
// EXAMPLE 5: Metrics Dashboard
// ============================================================================

export const MetricsDashboard: React.FC = () => {
  const {
    getDiversificationMetrics,
    getReliabilityMetrics,
    getPredictionAccuracy,
    isLoading,
  } = useDashboard();

  const [diversification, setDiversification] = useState<any>(null);
  const [reliability, setReliability] = useState<any>(null);
  const [accuracy, setAccuracy] = useState<any>(null);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    const [div, rel, acc] = await Promise.all([
      getDiversificationMetrics(true),
      getReliabilityMetrics(true),
      getPredictionAccuracy(true),
    ]);

    setDiversification(div);
    setReliability(rel);
    setAccuracy(acc);
  };

  const loading = isLoading('diversificationMetrics') ||
    isLoading('reliabilityMetrics') ||
    isLoading('predictionAccuracy');

  if (loading) {
    return <div>Loading metrics...</div>;
  }

  return (
    <div>
      <h2>System Metrics</h2>

      {diversification && (
        <div>
          <h3>Diversification</h3>
          <p>Total Predictions: {diversification.total_predictions}</p>
          <p>Unique Patterns: {diversification.unique_patterns}</p>
          <p>Diversity Score: {diversification.diversity_score.toFixed(2)}</p>
        </div>
      )}

      {reliability && (
        <div>
          <h3>Reliability</h3>
          <p>Total Predictions: {reliability.total_predictions}</p>
          <p>Correct Predictions: {reliability.correct_predictions}</p>
          <p>Accuracy: {(reliability.accuracy * 100).toFixed(2)}%</p>
        </div>
      )}

      {accuracy && (
        <div>
          <h3>Prediction Accuracy</h3>
          <p>Overall Accuracy: {(accuracy.overall_accuracy * 100).toFixed(2)}%</p>
          <p>CTR MAE: {accuracy.ctr_mae.toFixed(4)}</p>
          <p>ROAS MAE: {accuracy.roas_mae.toFixed(2)}</p>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// EXAMPLE 6: Drive Folder Analysis
// ============================================================================

export const DriveFolderAnalysis: React.FC = () => {
  const { analyzeDriveFolder, getDriveAnalysisStatus, isLoading, getError } = useDashboard();
  const [folderId, setFolderId] = useState<string>('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);

  const handleAnalyze = async () => {
    const result = await analyzeDriveFolder(folderId, 10);
    if (result) {
      setJobId(result.job_id);
      pollJobStatus(result.job_id);
    }
  };

  const pollJobStatus = async (id: string) => {
    const interval = setInterval(async () => {
      const status = await getDriveAnalysisStatus(id);
      if (status) {
        setProgress((status.videos_analyzed / status.total_videos) * 100);

        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(interval);
        }
      }
    }, 2000);
  };

  const loading = isLoading(`analyzeDriveFolder_${folderId}`);
  const error = getError(`analyzeDriveFolder_${folderId}`);

  return (
    <div>
      <h2>Google Drive Folder Analysis</h2>
      <input
        type="text"
        placeholder="Enter Google Drive Folder ID"
        value={folderId}
        onChange={(e) => setFolderId(e.target.value)}
      />
      <button onClick={handleAnalyze} disabled={loading || !folderId}>
        Analyze Folder
      </button>
      {loading && <p>Starting analysis...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error.message}</p>}
      {jobId && (
        <div>
          <p>Job ID: {jobId}</p>
          <p>Progress: {progress.toFixed(0)}%</p>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// EXAMPLE 7: App Setup with Provider
// ============================================================================

/*
// In your App.tsx or main.tsx:

import { DashboardProvider } from './contexts/DashboardContext';
import { ApprovalQueueComponent } from './contexts/DashboardUsageExample';

function App() {
  return (
    <DashboardProvider cacheTTL={5 * 60 * 1000}> {/* 5 minutes cache * /}
      <div className="App">
        <ApprovalQueueComponent />
        <VideoAnalysisComponent />
        <MetaInsightsDashboard />
        {/* ... other components * /}
      </div>
    </DashboardProvider>
  );
}

export default App;
*/

// ============================================================================
// EXAMPLE 8: Direct API Usage (without Context)
// ============================================================================

/*
// If you need to use the API directly without the context:

import { dashboardAPI } from '../services/dashboardAPI';

// Set auth token
dashboardAPI.setAuthToken('your-jwt-token-here');

// Make API calls directly
const analyzeVideoDirectly = async (file: File) => {
  try {
    const result = await dashboardAPI.analyzeVideo(file);
    // console.log('Analysis result:', result);
  } catch (error) {
    console.error('Analysis failed:', error);
  }
};

// Get approval queue
const getQueue = async () => {
  try {
    const items = await dashboardAPI.getApprovalQueue();
    // console.log('Approval queue:', items);
  } catch (error) {
    console.error('Failed to get queue:', error);
  }
};
*/

export default {
  ApprovalQueueComponent,
  VideoAnalysisComponent,
  MetaInsightsDashboard,
  RenderJobMonitor,
  MetricsDashboard,
  DriveFolderAnalysis,
};
