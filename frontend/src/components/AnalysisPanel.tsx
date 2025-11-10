import { useState, useEffect } from 'react';
import { predictApi, renderApi } from '../services/api';

interface AnalysisPanelProps {
  clips: any[];
}

export function AnalysisPanel({ clips }: AnalysisPanelProps) {
  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<any>(null);

  useEffect(() => {
    if (clips.length > 0) {
      analyzeclips();
    } else {
      setPrediction(null);
    }
  }, [clips]);

  useEffect(() => {
    if (jobId) {
      const interval = setInterval(pollJob, 3000);
      return () => clearInterval(interval);
    }
  }, [jobId]);

  const analyzeclips = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await predictApi.score(clips);
      setPrediction(response.data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRender = async () => {
    if (clips.length === 0) return;

    try {
      setLoading(true);
      setError(null);
      const response = await renderApi.createJob(clips, 'reels');
      setJobId(response.data.jobId);
      setJobStatus(response.data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const pollJob = async () => {
    if (!jobId) return;

    try {
      const response = await renderApi.getJob(jobId);
      setJobStatus(response.data);
      
      if (response.data.status === 'completed' || response.data.status === 'failed') {
        setJobId(null);
      }
    } catch (err: any) {
      console.error('Job poll error:', err);
    }
  };

  return (
    <div className="panel">
      <h2>📊 Analysis</h2>

      {clips.length === 0 && (
        <div style={{ textAlign: 'center', color: '#666', padding: '20px' }}>
          Select clips to view analysis
        </div>
      )}

      {error && <div className="error">{error}</div>}

      {clips.length > 0 && (
        <>
          <button className="button" onClick={handleRender} disabled={loading || !!jobId}>
            {loading ? 'Processing...' : jobId ? 'Rendering...' : 'Render Storyboard'}
          </button>

          {jobStatus && (
            <div style={{ marginTop: '10px', padding: '10px', background: '#f8f9fa', borderRadius: '4px' }}>
              <div>Status: {jobStatus.status}</div>
              <div>Progress: {(jobStatus.progress * 100).toFixed(0)}%</div>
              {jobStatus.outputUrl && <div>✓ Output: {jobStatus.outputUrl}</div>}
            </div>
          )}

          <h3>Prediction Scores</h3>
          {loading && <div className="loading">Analyzing...</div>}
          
          {prediction && (
            <>
              <div style={{ marginBottom: '15px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                  <span>Psychology Score</span>
                  <span style={{ fontWeight: 'bold' }}>{(prediction.scores.psychology * 100).toFixed(0)}%</span>
                </div>
                <div className="meter">
                  <div className="meter-fill" style={{ width: `${prediction.scores.psychology * 100}%` }} />
                </div>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                  <span>Technical Score</span>
                  <span style={{ fontWeight: 'bold' }}>{(prediction.scores.technical * 100).toFixed(0)}%</span>
                </div>
                <div className="meter">
                  <div className="meter-fill" style={{ width: `${prediction.scores.technical * 100}%` }} />
                </div>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                  <span>Hook Strength</span>
                  <span style={{ fontWeight: 'bold' }}>{(prediction.scores.hookStrength * 100).toFixed(0)}%</span>
                </div>
                <div className="meter">
                  <div className="meter-fill" style={{ width: `${prediction.scores.hookStrength * 100}%` }} />
                </div>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                  <span>Demographic Match</span>
                  <span style={{ fontWeight: 'bold' }}>{(prediction.scores.demographicMatch * 100).toFixed(0)}%</span>
                </div>
                <div className="meter">
                  <div className="meter-fill" style={{ width: `${prediction.scores.demographicMatch * 100}%` }} />
                </div>
              </div>

              <h3>Predicted CTR</h3>
              <div style={{ 
                padding: '15px', 
                background: prediction.predictedCTR.band === 'high' ? '#d4edda' : prediction.predictedCTR.band === 'mid' ? '#fff3cd' : '#f8d7da',
                borderRadius: '4px',
                marginBottom: '15px'
              }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', textAlign: 'center' }}>
                  {prediction.predictedCTR.band.toUpperCase()}
                </div>
                <div style={{ textAlign: 'center', color: '#666', fontSize: '14px' }}>
                  Confidence: {(prediction.predictedCTR.confidence * 100).toFixed(0)}%
                </div>
              </div>

              {prediction.triggerStack.length > 0 && (
                <>
                  <h3>Triggers Detected</h3>
                  <div className="tags">
                    {prediction.triggerStack.map((trigger: string, i: number) => (
                      <span key={i} className="tag">{trigger}</span>
                    ))}
                  </div>
                </>
              )}

              {prediction.personaCandidates.length > 0 && (
                <>
                  <h3>Persona Matches</h3>
                  <div className="tags">
                    {prediction.personaCandidates.map((persona: string, i: number) => (
                      <span key={i} className="tag">{persona}</span>
                    ))}
                  </div>
                </>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
