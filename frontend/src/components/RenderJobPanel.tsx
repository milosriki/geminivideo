import { useState } from 'react';
import { createRenderJob, getRenderJobStatus } from '../services/api';
import { API_BASE_URL } from '../config/api';

export default function RenderJobPanel() {
  const [jobId, setJobId] = useState('');
  const [jobStatus, setJobStatus] = useState<any>(null);
  const [creating, setCreating] = useState(false);
  const [checking, setChecking] = useState(false);
  
  // Story arc state
  const [assetId, setAssetId] = useState('');
  const [arcName, setArcName] = useState('fitness_transformation');
  const [creatingStoryArc, setCreatingStoryArc] = useState(false);

  const handleCreateJob = async () => {
    setCreating(true);
    try {
      // Sample scenes for demonstration
      const sampleScenes = [
        {
          clip_id: 'sample_1',
          asset_id: 'sample_asset',
          start_time: 0,
          end_time: 5,
          video_path: '/data/inputs/sample.mp4'
        }
      ];

      const result = await createRenderJob(sampleScenes, 'reels', {
        enable_transitions: true,
        enable_subtitles: true,
        enable_overlays: true,
        driver_signals: {
          hook_text: 'Transform in 30 days',
          cta_text: 'Start today'
        }
      });

      setJobId(result.job_id);
      alert(`Render job created: ${result.job_id}`);
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setCreating(false);
    }
  };

  const handleCreateStoryArc = async () => {
    if (!assetId) {
      alert('Please enter an asset ID');
      return;
    }

    setCreatingStoryArc(true);
    try {
      const response = await fetch(`${API_BASE_URL}/render/story_arc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          asset_id: assetId,
          arc_name: arcName
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setJobId(result.job_id);
      alert(`Story arc render job created: ${result.job_id}\nSelected ${result.selected_clips.length} clips`);
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setCreatingStoryArc(false);
    }
  };

  const handleCheckStatus = async () => {
    if (!jobId) {
      alert('Please enter a job ID');
      return;
    }

    setChecking(true);
    try {
      const status = await getRenderJobStatus(jobId);
      setJobStatus(status);
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setChecking(false);
    }
  };

  return (
    <div>
      <div className="card">
        <div className="panel-header">
          <h2>Render Job</h2>
        </div>

        <p style={{ marginBottom: '20px', color: '#666' }}>
          Create and monitor video rendering jobs with overlays, subtitles, and compliance checks.
        </p>

        <div className="card" style={{ border: '1px solid #e0e0e0', marginBottom: '20px' }}>
          <h3 style={{ marginBottom: '15px' }}>Create New Render Job</h3>
          <p style={{ fontSize: '14px', color: '#666', marginBottom: '15px' }}>
            This will create a sample render job with demo scenes. In production, you would select
            specific clips from your assets.
          </p>
          <button className="button" onClick={handleCreateJob} disabled={creating}>
            {creating ? 'Creating Job...' : 'Create Sample Render Job'}
          </button>
        </div>

        <div className="card" style={{ border: '1px solid #007bff', marginBottom: '20px' }}>
          <h3 style={{ marginBottom: '15px', color: '#007bff' }}>🎬 Create Story Arc Ad</h3>
          <p style={{ fontSize: '14px', color: '#666', marginBottom: '15px' }}>
            Generate a transformation ad using emotion-based story arcs. Clips are automatically 
            selected based on emotional progression (sad → neutral → happy).
          </p>
          
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', fontWeight: 'bold' }}>
              Asset ID:
            </label>
            <input
              type="text"
              className="input"
              placeholder="Enter asset ID with analyzed clips"
              value={assetId}
              onChange={(e) => setAssetId(e.target.value)}
              style={{ marginBottom: '15px' }}
            />
          </div>
          
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', fontWeight: 'bold' }}>
              Story Arc Template:
            </label>
            <select 
              className="input" 
              value={arcName}
              onChange={(e) => setArcName(e.target.value)}
              style={{ marginBottom: '15px' }}
            >
              <option value="fitness_transformation">Fitness Transformation (30s)</option>
              <option value="motivation_arc">Motivation Arc (20s)</option>
              <option value="quick_win">Quick Win (15s)</option>
            </select>
          </div>
          
          <button 
            className="button" 
            onClick={handleCreateStoryArc} 
            disabled={creatingStoryArc || !assetId}
            style={{ background: '#007bff' }}
          >
            {creatingStoryArc ? 'Creating Transformation Ad...' : '🎥 Render Transformation Ad'}
          </button>
        </div>

        <div className="card" style={{ border: '1px solid #e0e0e0' }}>
          <h3 style={{ marginBottom: '15px' }}>Check Job Status</h3>
          <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
            <input
              type="text"
              className="input"
              placeholder="Enter job ID"
              value={jobId}
              onChange={(e) => setJobId(e.target.value)}
            />
            <button className="button" onClick={handleCheckStatus} disabled={checking}>
              {checking ? 'Checking...' : 'Check Status'}
            </button>
          </div>

          {jobStatus && (
            <div>
              <div style={{ display: 'flex', gap: '15px', marginBottom: '20px' }}>
                <div className="metric-card" style={{ flex: 1 }}>
                  <h3>Status</h3>
                  <span className={`status-badge ${
                    jobStatus.status === 'completed' ? 'success' :
                    jobStatus.status === 'failed' ? 'error' :
                    jobStatus.status === 'processing' ? 'warning' : 'info'
                  }`}>
                    {jobStatus.status.toUpperCase()}
                  </span>
                </div>

                <div className="metric-card" style={{ flex: 1 }}>
                  <h3>Progress</h3>
                  <div className="value">{(jobStatus.progress * 100).toFixed(0)}%</div>
                </div>
              </div>

              {jobStatus.status === 'completed' && jobStatus.output_path && (
                <div className="card" style={{ border: '1px solid #28a745', background: '#d4edda' }}>
                  <h3 style={{ color: '#155724', marginBottom: '10px' }}>✓ Render Complete</h3>
                  <p style={{ fontSize: '14px', color: '#155724', marginBottom: '10px' }}>
                    <strong>Output:</strong> {jobStatus.output_path}
                  </p>

                  {jobStatus.compliance && (
                    <div style={{ marginTop: '15px' }}>
                      <h4 style={{ color: '#155724', marginBottom: '10px' }}>Compliance Status</h4>
                      <p style={{ fontSize: '14px', color: '#155724' }}>
                        Overall: {jobStatus.compliance.passed ? '✓ Passed' : '✗ Failed'}
                      </p>
                      {jobStatus.compliance.failed && jobStatus.compliance.failed.length > 0 && (
                        <p style={{ fontSize: '12px', color: '#721c24', marginTop: '5px' }}>
                          Failed checks: {jobStatus.compliance.failed.join(', ')}
                        </p>
                      )}
                      {jobStatus.compliance.warnings && jobStatus.compliance.warnings.length > 0 && (
                        <p style={{ fontSize: '12px', color: '#856404', marginTop: '5px' }}>
                          Warnings: {jobStatus.compliance.warnings.join(', ')}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}

              {jobStatus.status === 'failed' && jobStatus.error && (
                <div className="error">
                  <strong>Error:</strong> {jobStatus.error}
                </div>
              )}

              {jobStatus.status === 'processing' && (
                <div className="card" style={{ border: '1px solid #ffc107', background: '#fff3cd' }}>
                  <p style={{ color: '#856404' }}>
                    Job is currently processing. Check back in a few moments...
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
