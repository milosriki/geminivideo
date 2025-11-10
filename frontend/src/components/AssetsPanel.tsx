import { useState, useEffect } from 'react';
import { assetsApi } from '../services/api';

interface AssetsPanelProps {
  onSelectAsset: (id: string) => void;
  selectedAssetId: string | null;
}

export function AssetsPanel({ onSelectAsset, selectedAssetId }: AssetsPanelProps) {
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [localPath, setLocalPath] = useState('/app/data/cache');

  const loadAssets = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await assetsApi.getAll();
      setAssets(response.data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleScanLocal = async () => {
    try {
      setLoading(true);
      setError(null);
      await assetsApi.ingestLocal(localPath);
      await loadAssets();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssets();
  }, []);

  return (
    <div className="panel">
      <h2>📁 Assets Library</h2>
      
      <div style={{ marginBottom: '15px' }}>
        <input
          type="text"
          className="input"
          placeholder="Local folder path"
          value={localPath}
          onChange={(e) => setLocalPath(e.target.value)}
        />
        <button className="button" onClick={handleScanLocal} disabled={loading}>
          {loading ? 'Scanning...' : 'Scan Library'}
        </button>
        <button className="button secondary" onClick={loadAssets} disabled={loading}>
          Refresh
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="asset-list">
        {loading && <div className="loading">Loading assets...</div>}
        
        {!loading && assets.length === 0 && (
          <div style={{ textAlign: 'center', color: '#666', padding: '20px' }}>
            No assets found. Click "Scan Library" to import videos.
          </div>
        )}

        {assets.map((asset) => (
          <div
            key={asset.id}
            className={`asset-item ${selectedAssetId === asset.id ? 'selected' : ''}`}
            onClick={() => onSelectAsset(asset.id)}
          >
            <div style={{ fontWeight: 'bold' }}>{asset.name}</div>
            <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
              {asset.driveFileId ? '☁️ Drive' : '💾 Local'} • {asset.id.substring(0, 8)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
