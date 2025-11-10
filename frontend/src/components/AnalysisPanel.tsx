import { useState } from 'react';
import { scoreStoryboard } from '../services/api';

export default function AnalysisPanel() {
  const [scores, setScores] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      // Sample scenes for demonstration
      const sampleScenes = [
        {
          features: {
            text_detected: ['Transform your body', 'Get results'],
            transcript: 'Are you tired of not seeing results?',
            motion_score: 0.7,
            technical_quality: 0.8
          }
        }
      ];

      const data = await scoreStoryboard(sampleScenes, {
        target_persona: 'weight_loss_seeker'
      });
      setScores(data.scores);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="card">
        <div className="panel-header">
          <h2>Analysis Dashboard</h2>
          <button className="button" onClick={handleAnalyze} disabled={loading}>
            {loading ? 'Analyzing...' : 'Analyze Sample'}
          </button>
        </div>

        <p style={{ marginBottom: '20px', color: '#666' }}>
          Comprehensive scoring analysis including psychology drivers, hook strength, technical quality, and demographic matching.
        </p>

        {scores && (
          <div className="grid grid-3">
            <div className="metric-card">
              <h3>Psychology Score</h3>
              <div className="value">{(scores.psychology_score * 100).toFixed(0)}%</div>
              <div className="label">Driver-based content analysis</div>
            </div>

            <div className="metric-card">
              <h3>Hook Strength</h3>
              <div className="value">{(scores.hook_strength * 100).toFixed(0)}%</div>
              <div className="label">First 3s engagement potential</div>
            </div>

            <div className="metric-card">
              <h3>Technical Score</h3>
              <div className="value">{(scores.technical_score * 100).toFixed(0)}%</div>
              <div className="label">Video quality & production</div>
            </div>

            <div className="metric-card">
              <h3>Demographic Match</h3>
              <div className="value">{(scores.demographic_match * 100).toFixed(0)}%</div>
              <div className="label">Persona fit score</div>
            </div>

            <div className="metric-card">
              <h3>Novelty Score</h3>
              <div className="value">{(scores.novelty_score * 100).toFixed(0)}%</div>
              <div className="label">Semantic uniqueness</div>
            </div>

            <div className="metric-card">
              <h3>Composite Score</h3>
              <div className="value" style={{ color: '#667eea' }}>
                {(scores.composite_score * 100).toFixed(0)}%
              </div>
              <div className="label">Overall weighted score</div>
            </div>
          </div>
        )}

        {scores?.win_probability && (
          <div className="card" style={{ marginTop: '20px', border: '2px solid #667eea' }}>
            <h3 style={{ marginBottom: '15px' }}>Win Probability Prediction</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
              <div>
                <span className={`status-badge ${
                  scores.predicted_band === 'high' ? 'success' :
                  scores.predicted_band === 'mid' ? 'warning' : 'error'
                }`}>
                  {scores.predicted_band.toUpperCase()} BAND
                </span>
              </div>
              <div>
                <div style={{ fontSize: '14px', color: '#666' }}>Probability</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                  {(scores.win_probability.probability * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div style={{ fontSize: '14px', color: '#666' }}>Confidence</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                  {(scores.confidence * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
