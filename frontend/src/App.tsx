import { useState, useEffect } from 'react';
import { api, Asset, Clip, RenderJob } from './services/api';
import './App.css';

function App() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [clips, setClips] = useState<Clip[]>([]);
  const [activeTab, setActiveTab] = useState<string>('assets');
  const [renderJob, setRenderJob] = useState<RenderJob | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAssets();
  }, []);

  const loadAssets = async () => {
    try {
      setLoading(true);
      const data = await api.getAssets();
      setAssets(data);
    } catch (error) {
      console.error('Failed to load assets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSyncDrive = async () => {
    try {
      setLoading(true);
      await api.syncDrive('local');
      await loadAssets();
      alert('Assets synced successfully');
    } catch (error) {
      console.error('Failed to sync:', error);
      alert('Failed to sync assets');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAsset = async (asset: Asset) => {
    setSelectedAsset(asset);
    try {
      const assetClips = await api.getAssetClips(asset.id);
      setClips(assetClips);
    } catch (error) {
      console.error('Failed to load clips:', error);
    }
  };

  const handleCreateRemix = async () => {
    if (clips.length === 0) {
      alert('No clips available to remix');
      return;
    }

    try {
      setLoading(true);
      const storyboard = clips.map(clip => ({
        clipId: clip.id,
        duration: clip.duration
      }));
      
      const assetMap: Record<string, string> = {};
      clips.forEach(clip => {
        assetMap[clip.id] = clip.assetId;
      });

      const result = await api.createRemix({
        storyboard,
        assetMap,
        overlays: { cta: 'Join Now!' }
      });

      setRenderJob(await api.getJobStatus(result.jobId));
      alert(`Remix job created: ${result.jobId}`);
      
      // Poll for status
      const interval = setInterval(async () => {
        const job = await api.getJobStatus(result.jobId);
        setRenderJob(job);
        if (job.status === 'completed' || job.status === 'failed') {
          clearInterval(interval);
        }
      }, 2000);
    } catch (error) {
      console.error('Failed to create remix:', error);
      alert('Failed to create remix');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎬 AI Ad Intelligence & Creation Suite</h1>
        <p>Gemini Creative Suite - Dubai Fitness Edition</p>
      </header>

      <nav className="app-nav">
        <button 
          className={activeTab === 'assets' ? 'active' : ''} 
          onClick={() => setActiveTab('assets')}
        >
          📁 Assets
        </button>
        <button 
          className={activeTab === 'psychology' ? 'active' : ''} 
          onClick={() => setActiveTab('psychology')}
        >
          🧠 Psychology Analysis
        </button>
        <button 
          className={activeTab === 'compliance' ? 'active' : ''} 
          onClick={() => setActiveTab('compliance')}
        >
          ✓ Compliance
        </button>
        <button 
          className={activeTab === 'diversification' ? 'active' : ''} 
          onClick={() => setActiveTab('diversification')}
        >
          🎨 Diversification
        </button>
        <button 
          className={activeTab === 'editor' ? 'active' : ''} 
          onClick={() => setActiveTab('editor')}
        >
          ✂️ Editor
        </button>
        <button 
          className={activeTab === 'player' ? 'active' : ''} 
          onClick={() => setActiveTab('player')}
        >
          ▶️ Player
        </button>
      </nav>

      <main className="app-content">
        {activeTab === 'assets' && (
          <div className="panel assets-panel">
            <div className="panel-header">
              <h2>Assets Library</h2>
              <button onClick={handleSyncDrive} disabled={loading}>
                {loading ? 'Syncing...' : '🔄 Sync Local Folder'}
              </button>
            </div>
            
            <div className="assets-grid">
              {assets.length === 0 ? (
                <div className="empty-state">
                  <p>No assets found. Click "Sync Local Folder" to import videos from data/input/</p>
                </div>
              ) : (
                assets.map(asset => (
                  <div 
                    key={asset.id} 
                    className={`asset-card ${selectedAsset?.id === asset.id ? 'selected' : ''}`}
                    onClick={() => handleSelectAsset(asset)}
                  >
                    <div className="asset-thumbnail">
                      {asset.thumbnail ? (
                        <img src={asset.thumbnail} alt={asset.filename} />
                      ) : (
                        <div className="placeholder-thumbnail">🎥</div>
                      )}
                    </div>
                    <div className="asset-info">
                      <h3>{asset.filename}</h3>
                      <p>Duration: {asset.duration.toFixed(1)}s</p>
                      <p>Resolution: {asset.resolution}</p>
                      <p>Aspect: {asset.aspectRatio}</p>
                    </div>
                  </div>
                ))
              )}
            </div>

            {selectedAsset && clips.length > 0 && (
              <div className="clips-section">
                <h3>Clips from {selectedAsset.filename}</h3>
                <div className="clips-list">
                  {clips.map(clip => (
                    <div key={clip.id} className="clip-item">
                      <span>Clip {clip.id.slice(0, 8)}</span>
                      <span>{clip.startTime.toFixed(1)}s - {clip.endTime.toFixed(1)}s</span>
                      <span>({clip.duration.toFixed(1)}s)</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'psychology' && (
          <div className="panel psychology-panel">
            <h2>🧠 Psychology Analysis</h2>
            <div className="placeholder-content">
              <p>TODO: Implement psychology analysis panel</p>
              <ul>
                <li>Hook relevance scoring</li>
                <li>Trigger alignment analysis</li>
                <li>Persona match evaluation</li>
                <li>Emotional appeal metrics</li>
              </ul>
            </div>
          </div>
        )}

        {activeTab === 'compliance' && (
          <div className="panel compliance-panel">
            <h2>✓ Compliance Check</h2>
            <div className="placeholder-content">
              <p>TODO: Implement compliance checking panel</p>
              <ul>
                <li>Aspect ratio validation</li>
                <li>Resolution requirements</li>
                <li>Duration constraints</li>
                <li>File size limits</li>
                <li>Platform-specific rules (Meta Feed/Story/Reel)</li>
              </ul>
            </div>
          </div>
        )}

        {activeTab === 'diversification' && (
          <div className="panel diversification-panel">
            <h2>🎨 Diversification Dashboard</h2>
            <div className="placeholder-content">
              <p>TODO: Implement diversification analysis</p>
              <ul>
                <li>Hook variety scoring</li>
                <li>Visual diversity metrics</li>
                <li>Persona coverage analysis</li>
                <li>Entropy calculations</li>
              </ul>
            </div>
          </div>
        )}

        {activeTab === 'editor' && (
          <div className="panel editor-panel">
            <h2>✂️ Video Editor</h2>
            <div className="editor-controls">
              <button onClick={handleCreateRemix} disabled={loading || clips.length === 0}>
                {loading ? 'Creating...' : '🎬 Create Remix'}
              </button>
            </div>
            
            {renderJob && (
              <div className="render-status">
                <h3>Render Job: {renderJob.jobId.slice(0, 8)}</h3>
                <p>Status: <strong>{renderJob.status}</strong></p>
                <p>Progress: {renderJob.progress}%</p>
                {renderJob.outputUrl && (
                  <p>Output: <a href={renderJob.outputUrl} target="_blank" rel="noopener noreferrer">
                    {renderJob.outputUrl}
                  </a></p>
                )}
                {renderJob.error && <p className="error">Error: {renderJob.error}</p>}
              </div>
            )}
            
            <div className="placeholder-content">
              <p>TODO: Implement visual editor</p>
              <ul>
                <li>Timeline view with clips</li>
                <li>Drag and drop storyboard</li>
                <li>Transition controls</li>
                <li>Text overlay editor</li>
                <li>CTA placement</li>
              </ul>
            </div>
          </div>
        )}

        {activeTab === 'player' && (
          <div className="panel player-panel">
            <h2>▶️ Video Player</h2>
            <div className="placeholder-content">
              <p>TODO: Implement video player</p>
              <ul>
                <li>Preview rendered videos</li>
                <li>Compare variations side-by-side</li>
                <li>Performance metrics overlay</li>
              </ul>
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>AI Ad Intelligence & Creation Suite v1.0 | Powered by Gemini</p>
      </footer>
    </div>
  );
}

export default App;
