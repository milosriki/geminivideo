import { useState, useEffect } from 'react';
import { getDiversificationMetrics } from '../services/api';

export default function DiversificationDashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    setLoading(true);
    try {
      const data = await getDiversificationMetrics();
      setMetrics(data);
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
          <h2>Diversification Dashboard</h2>
          <button className="button" onClick={loadMetrics} disabled={loading}>
            Refresh
          </button>
        </div>

        <p style={{ marginBottom: '20px', color: '#666' }}>
          Track content diversity to avoid ad fatigue and maintain audience engagement.
        </p>

        {loading ? (
          <div className="loading">Loading metrics...</div>
        ) : metrics ? (
          <div className="grid grid-3">
            <div className="metric-card">
              <h3>Trigger Entropy</h3>
              <div className="value">{metrics.trigger_entropy.toFixed(2)}</div>
              <div className="label">
                Shannon entropy of driver triggers<br/>
                Higher = more diverse content
              </div>
            </div>

            <div className="metric-card">
              <h3>Persona Coverage</h3>
              <div className="value">{metrics.persona_coverage}</div>
              <div className="label">
                Unique personas targeted<br/>
                Broader coverage reduces fatigue
              </div>
            </div>

            <div className="metric-card">
              <h3>Novelty Index</h3>
              <div className="value">{(metrics.novelty_index * 100).toFixed(0)}%</div>
              <div className="label">
                Average semantic uniqueness<br/>
                Higher = more unique content
              </div>
            </div>
          </div>
        ) : (
          <p style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
            No metrics available yet. Generate some predictions first.
          </p>
        )}

        {metrics && (
          <div className="card" style={{ marginTop: '20px', border: '1px solid #e0e0e0' }}>
            <h3 style={{ marginBottom: '10px' }}>Interpretation Guide</h3>
            <ul style={{ fontSize: '14px', color: '#666', lineHeight: '1.8' }}>
              <li><strong>Trigger Entropy:</strong> Target &gt; 2.0 for good diversity. Below 1.5 suggests repetitive messaging.</li>
              <li><strong>Persona Coverage:</strong> Aim to target 3-5 personas regularly to maximize reach.</li>
              <li><strong>Novelty Index:</strong> Target 60-80%. Too high may confuse audience; too low causes fatigue.</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
