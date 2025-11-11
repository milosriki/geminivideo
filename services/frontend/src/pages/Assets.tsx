import { useState, useEffect } from 'react';

interface Asset {
  asset_id: string;
  filename: string;
  duration_seconds: number;
  resolution: string;
  status: string;
  ingested_at: string;
}

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8081';

export default function Assets() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAssets();
  }, []);

  const fetchAssets = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${GATEWAY_URL}/assets`);
      if (!response.ok) throw new Error('Failed to fetch assets');
      const data = await response.json();
      setAssets(data.assets || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading assets...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="assets-page">
      <h1>Video Assets</h1>
      <div className="assets-grid">
        {assets.length === 0 ? (
          <div className="no-assets">No assets found. Upload videos to get started.</div>
        ) : (
          assets.map(asset => (
            <div key={asset.asset_id} className="asset-card">
              <div className="asset-header">
                <h3>{asset.filename}</h3>
                <span className={`status status-${asset.status}`}>{asset.status}</span>
              </div>
              <div className="asset-info">
                <p><strong>Duration:</strong> {asset.duration_seconds}s</p>
                <p><strong>Resolution:</strong> {asset.resolution}</p>
                <p><strong>Ingested:</strong> {new Date(asset.ingested_at).toLocaleString()}</p>
              </div>
              <button onClick={() => window.location.href = `/clips/${asset.asset_id}`}>
                View Clips
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
