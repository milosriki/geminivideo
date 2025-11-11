import { useState, useEffect } from 'react';

interface StoryboardScene {
  clip_id: string;
  asset_id: string;
  start_time: number;
  end_time: number;
  transition?: string;
}

interface RenderJob {
  job_id: string;
  status: string;
  output_path?: string;
  created_at: string;
  completed_at?: string;
  error?: string;
}

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8082';

export default function RenderJob() {
  const [storyboard, setStoryboard] = useState<StoryboardScene[]>([]);
  const [job, setJob] = useState<RenderJob | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load storyboard from localStorage
    const saved = localStorage.getItem('storyboard');
    if (saved) {
      setStoryboard(JSON.parse(saved));
    }
  }, []);

  const startRender = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${GATEWAY_URL}/render/remix`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          storyboard,
          output_format: 'mp4',
          resolution: '1920x1080',
          fps: 30,
          compliance_check: true
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Render failed');
      }

      const jobData = await response.json();
      setJob(jobData);
      
      // Poll for job status
      pollJobStatus(jobData.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${GATEWAY_URL}/render/status/${jobId}`);
        const jobData = await response.json();
        setJob(jobData);

        if (jobData.status === 'completed' || jobData.status === 'failed') {
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Failed to poll job status:', err);
        clearInterval(interval);
      }
    }, 2000);
  };

  return (
    <div className="render-job-page">
      <h1>Render Video Ad</h1>
      
      <div className="storyboard-preview">
        <h2>Storyboard ({storyboard.length} clips)</h2>
        <div className="clips-sequence">
          {storyboard.map((scene, idx) => (
            <div key={scene.clip_id} className="sequence-item">
              <span className="sequence-number">{idx + 1}</span>
              <div className="sequence-info">
                <p>Clip: {scene.start_time}s - {scene.end_time}s</p>
                <p>Transition: {scene.transition || 'none'}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="render-controls">
        <button 
          onClick={startRender} 
          disabled={loading || storyboard.length === 0 || (job?.status === 'processing')}
        >
          {loading ? 'Starting...' : 'Start Render'}
        </button>
      </div>

      {error && <div className="error">Error: {error}</div>}

      {job && (
        <div className="render-status">
          <h2>Render Status</h2>
          <div className={`status-badge status-${job.status}`}>
            {job.status.toUpperCase()}
          </div>
          <div className="job-details">
            <p><strong>Job ID:</strong> {job.job_id}</p>
            <p><strong>Created:</strong> {new Date(job.created_at).toLocaleString()}</p>
            {job.completed_at && (
              <p><strong>Completed:</strong> {new Date(job.completed_at).toLocaleString()}</p>
            )}
            {job.output_path && (
              <p><strong>Output:</strong> <a href={job.output_path}>{job.output_path}</a></p>
            )}
            {job.error && (
              <p className="error"><strong>Error:</strong> {job.error}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
