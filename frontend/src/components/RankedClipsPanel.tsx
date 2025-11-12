import { useState, useEffect } from 'react';
import { getAssets, getAssetClips } from '../services/api';

export default function RankedClipsPanel() {
  const [assets, setAssets] = useState<any[]>([]);
  const [selectedAsset, setSelectedAsset] = useState('');
  const [clips, setClips] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [topN, setTopN] = useState(10);

  useEffect(() => {
    loadAssets();
  }, []);

  const loadAssets = async () => {
    try {
      const data = await getAssets();
      setAssets(data.assets || []);
      if (data.assets?.length > 0) {
        setSelectedAsset(data.assets[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadClips = async () => {
    if (!selectedAsset) return;

    setLoading(true);
    try {
      const data = await getAssetClips(selectedAsset, true, topN);
      setClips(data.clips || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedAsset) {
      loadClips();
    }
  }, [selectedAsset, topN]);

  return (
    <div>
      <div className="card">
        <div className="panel-header">
          <h2>Ranked Clips</h2>
        </div>

        <div style={{ marginBottom: '20px', display: 'flex', gap: '10px', alignItems: 'center' }}>
          <label className="label" style={{ marginBottom: 0 }}>Asset:</label>
          <select
            className="input"
            value={selectedAsset}
            onChange={(e) => setSelectedAsset(e.target.value)}
            style={{ flex: 1 }}
          >
            <option value="">Select an asset</option>
            {assets.map((asset) => (
              <option key={asset.id} value={asset.id}>
                {asset.filename}
              </option>
            ))}
          </select>

          <label className="label" style={{ marginBottom: 0 }}>Top N:</label>
          <input
            type="number"
            className="input"
            value={topN}
            onChange={(e) => setTopN(parseInt(e.target.value))}
            min="1"
            max="50"
            style={{ width: '100px' }}
          />
        </div>

        {loading ? (
          <div className="loading">Loading ranked clips...</div>
        ) : clips.length === 0 ? (
          <p style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
            No clips available. Select an asset with clips.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            {clips.map((clip, idx) => (
              <div key={clip.id} className="card" style={{ border: '1px solid #e0e0e0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                      <span className="status-badge info">Rank #{clip.rank || idx + 1}</span>
                      <span style={{ fontWeight: 'bold', fontSize: '18px' }}>
                        Score: {clip.score.toFixed(3)}
                      </span>
                    </div>
                    <p style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>
                      Time: {clip.start_time.toFixed(1)}s - {clip.end_time.toFixed(1)}s
                      ({clip.duration.toFixed(1)}s)
                    </p>
                  </div>
                </div>

                <div style={{ marginTop: '15px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '13px' }}>
                  <div>
                    <strong>Motion Score:</strong> {clip.features.motion_score.toFixed(3)}
                  </div>
                  <div>
                    <strong>Technical Quality:</strong> {clip.features.technical_quality.toFixed(3)}
                  </div>
                  <div>
                    <strong>Objects:</strong> {clip.features.objects.length}
                    {clip.features.objects.length > 0 && (
                      <span style={{ color: '#666' }}> ({clip.features.objects.slice(0, 3).join(', ')})</span>
                    )}
                  </div>
                  <div>
                    <strong>Text Detected:</strong> {clip.features.text_detected.length}
                  </div>
                </div>

                {clip.features.text_detected.length > 0 && (
                  <div style={{ marginTop: '10px', padding: '10px', background: '#f8f9fa', borderRadius: '4px' }}>
                    <strong style={{ fontSize: '12px' }}>Detected Text:</strong>
                    <p style={{ fontSize: '12px', marginTop: '5px', color: '#666' }}>
                      {clip.features.text_detected.join(' • ')}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
