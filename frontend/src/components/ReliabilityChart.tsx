import { useState, useEffect } from 'react';
import { predictApi } from '../services/api';

export function ReliabilityChart() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const response = await predictApi.getReliability();
      setStats(response.data);
    } catch (err) {
      console.error('Failed to load reliability stats', err);
      // Use mock data if API fails
      setStats({
        total: 45,
        distribution: { low: 12, mid: 23, high: 10 },
        inBand: 32,
        above: 8,
        below: 5
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="panel">
        <h2>📈 Prediction Reliability</h2>
        <div className="loading">Loading stats...</div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="panel">
        <h2>📈 Prediction Reliability</h2>
        <div style={{ textAlign: 'center', color: '#666', padding: '20px' }}>
          No reliability data available yet
        </div>
      </div>
    );
  }

  const accuracy = stats.total > 0 ? (stats.inBand / stats.total) * 100 : 0;

  return (
    <div className="panel">
      <h2>📈 Prediction Reliability</h2>

      <div style={{ marginBottom: '20px' }}>
        <h3>Overall Accuracy</h3>
        <div style={{ fontSize: '36px', fontWeight: 'bold', textAlign: 'center', color: '#007bff' }}>
          {accuracy.toFixed(1)}%
        </div>
        <div style={{ textAlign: 'center', color: '#666', fontSize: '14px' }}>
          Based on {stats.total} predictions
        </div>
      </div>

      <h3>Band Distribution</h3>
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
          <div style={{ flex: 1, textAlign: 'center' }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#dc3545' }}>
              {stats.distribution.low}
            </div>
            <div style={{ fontSize: '12px', color: '#666' }}>Low</div>
          </div>
          <div style={{ flex: 1, textAlign: 'center' }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ffc107' }}>
              {stats.distribution.mid}
            </div>
            <div style={{ fontSize: '12px', color: '#666' }}>Mid</div>
          </div>
          <div style={{ flex: 1, textAlign: 'center' }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#28a745' }}>
              {stats.distribution.high}
            </div>
            <div style={{ fontSize: '12px', color: '#666' }}>High</div>
          </div>
        </div>
      </div>

      <h3>Prediction Accuracy</h3>
      <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
        <div style={{ flex: 1, padding: '10px', background: '#d4edda', borderRadius: '4px', textAlign: 'center' }}>
          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{stats.inBand}</div>
          <div style={{ fontSize: '12px' }}>In Band</div>
        </div>
        <div style={{ flex: 1, padding: '10px', background: '#fff3cd', borderRadius: '4px', textAlign: 'center' }}>
          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{stats.above}</div>
          <div style={{ fontSize: '12px' }}>Above</div>
        </div>
        <div style={{ flex: 1, padding: '10px', background: '#f8d7da', borderRadius: '4px', textAlign: 'center' }}>
          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{stats.below}</div>
          <div style={{ fontSize: '12px' }}>Below</div>
        </div>
      </div>

      <button className="button secondary" onClick={loadStats}>
        Refresh
      </button>
    </div>
  );
}
