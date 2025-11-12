import { useState, useEffect } from 'react';
import { getReliabilityMetrics } from '../services/api';

export default function ReliabilityChart() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    setLoading(true);
    try {
      const data = await getReliabilityMetrics();
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
          <h2>Reliability & Calibration</h2>
          <button className="button" onClick={loadMetrics} disabled={loading}>
            Refresh
          </button>
        </div>

        <p style={{ marginBottom: '20px', color: '#666' }}>
          Track prediction accuracy and model calibration over time.
        </p>

        {loading ? (
          <div className="loading">Loading metrics...</div>
        ) : metrics ? (
          <div>
            <div className="grid grid-3">
              <div className="metric-card">
                <h3>Total Predictions</h3>
                <div className="value">{metrics.total_predictions}</div>
                <div className="label">All predictions logged</div>
              </div>

              <div className="metric-card">
                <h3>With Actuals</h3>
                <div className="value">{metrics.with_actuals}</div>
                <div className="label">
                  {metrics.total_predictions > 0 
                    ? `${((metrics.with_actuals / metrics.total_predictions) * 100).toFixed(0)}% coverage`
                    : '0% coverage'}
                </div>
              </div>

              <div className="metric-card">
                <h3>In-Band Accuracy</h3>
                <div className="value" style={{ color: '#28a745' }}>
                  {metrics.in_band_count}
                </div>
                <div className="label">
                  {metrics.with_actuals > 0
                    ? `${metrics.calibration.in_band_percentage.toFixed(1)}% calibrated`
                    : 'N/A'}
                </div>
              </div>
            </div>

            {metrics.with_actuals > 0 && (
              <div className="card" style={{ marginTop: '20px', border: '1px solid #e0e0e0' }}>
                <h3 style={{ marginBottom: '15px' }}>Calibration Breakdown</h3>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                      <strong>In-Band Predictions</strong>
                      <p style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                        Predictions within expected probability band
                      </p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#28a745' }}>
                        {metrics.in_band_count}
                      </div>
                      <div style={{ fontSize: '14px', color: '#666' }}>
                        {metrics.calibration.in_band_percentage.toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                      <strong>Above High Band</strong>
                      <p style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                        Actual performance exceeded prediction
                      </p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ffc107' }}>
                        {metrics.above_high_count}
                      </div>
                      <div style={{ fontSize: '14px', color: '#666' }}>
                        {metrics.calibration.above_high_percentage.toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                      <strong>Below Low Band</strong>
                      <p style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                        Actual performance below prediction
                      </p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#dc3545' }}>
                        {metrics.below_low_count}
                      </div>
                      <div style={{ fontSize: '14px', color: '#666' }}>
                        {metrics.calibration.below_low_percentage.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: '20px', padding: '15px', background: '#f8f9fa', borderRadius: '4px' }}>
                  <strong style={{ fontSize: '14px' }}>Calibration Status:</strong>
                  <p style={{ fontSize: '14px', color: '#666', marginTop: '5px' }}>
                    {metrics.calibration.in_band_percentage >= 70
                      ? '✓ Model is well-calibrated (≥70% in-band accuracy)'
                      : metrics.calibration.in_band_percentage >= 50
                      ? '⚠ Model needs tuning (50-70% in-band accuracy)'
                      : '✗ Model requires recalibration (<50% in-band accuracy)'}
                  </p>
                </div>
              </div>
            )}

            {metrics.with_actuals === 0 && (
              <div className="card" style={{ marginTop: '20px', border: '1px solid #ffc107', background: '#fff3cd' }}>
                <p style={{ color: '#856404' }}>
                  <strong>No actual performance data available yet.</strong><br/>
                  Link ad insights to predictions to enable calibration tracking.
                </p>
              </div>
            )}
          </div>
        ) : (
          <p style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
            No metrics available yet.
          </p>
        )}
      </div>
    </div>
  );
}
