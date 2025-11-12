import { useState, useEffect } from 'react';
import { getAssets, ingestLocalFolder } from '../services/api';

export default function AssetsPanel() {
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [folderPath, setFolderPath] = useState('');
  const [ingesting, setIngesting] = useState(false);

  useEffect(() => {
    loadAssets();
  }, []);

  const loadAssets = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getAssets();
      setAssets(data.assets || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async () => {
    if (!folderPath.trim()) {
      setError('Please enter a folder path');
      return;
    }

    setIngesting(true);
    setError('');
    try {
      const result = await ingestLocalFolder(folderPath);
      alert(`Ingested ${result.successful} videos successfully`);
      loadAssets();
      setFolderPath('');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div>
      <div className="card">
        <div className="panel-header">
          <h2>Assets & Ingest</h2>
          <button className="button" onClick={loadAssets} disabled={loading}>
            Refresh
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        <div style={{ marginBottom: '30px' }}>
          <h3 style={{ marginBottom: '15px' }}>Ingest Videos</h3>
          <div style={{ display: 'flex', gap: '10px' }}>
            <input
              type="text"
              className="input"
              placeholder="/path/to/video/folder"
              value={folderPath}
              onChange={(e) => setFolderPath(e.target.value)}
              disabled={ingesting}
            />
            <button
              className="button"
              onClick={handleIngest}
              disabled={ingesting}
            >
              {ingesting ? 'Ingesting...' : 'Ingest Folder'}
            </button>
          </div>
          <p style={{ marginTop: '10px', fontSize: '12px', color: '#666' }}>
            Provide absolute path to folder containing video files (MP4, AVI, MOV, etc.)
          </p>
        </div>

        <h3 style={{ marginBottom: '15px' }}>Assets ({assets.length})</h3>
        
        {loading ? (
          <div className="loading">Loading assets...</div>
        ) : assets.length === 0 ? (
          <p style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
            No assets found. Ingest some videos to get started.
          </p>
        ) : (
          <div className="grid grid-2">
            {assets.map((asset) => (
              <div key={asset.id} className="card" style={{ border: '1px solid #e0e0e0' }}>
                <h4 style={{ marginBottom: '10px' }}>{asset.filename}</h4>
                <div style={{ fontSize: '14px', color: '#666' }}>
                  <p>Duration: {asset.duration.toFixed(1)}s</p>
                  <p>Resolution: {asset.resolution[0]}x{asset.resolution[1]}</p>
                  <p>Clips: {asset.clips?.length || 0}</p>
                  <p>Size: {(asset.file_size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
