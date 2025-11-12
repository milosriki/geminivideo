# Agent 5: Frontend UI Developer

## Your Mission
Wire up React frontend with real API calls to all backend services.

## Priority: HIGH

## Tasks

### 1. API Client Setup
Create `services/frontend/src/api/client.ts`:
```typescript
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8080';

export class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  async request(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  // Assets
  async getAssets(status?: string) {
    return this.request(`/assets${status ? `?status=${status}` : ''}`);
  }

  async ingestVideo(path: string) {
    return this.request('/ingest/local/folder', {
      method: 'POST',
      body: JSON.stringify({ path, recursive: true }),
    });
  }

  // Clips
  async getClips(assetId: string, ranked: boolean = true) {
    return this.request(`/assets/${assetId}/clips?ranked=${ranked}&top=10`);
  }

  async getEmotionalClips(assetId: string, minScore: number = 0.5) {
    return this.request(`/assets/${assetId}/clips/emotional?min_emotion_score=${minScore}`);
  }

  // Prediction
  async predictCTR(clipId: string) {
    return this.request('/predict/ctr', {
      method: 'POST',
      body: JSON.stringify({ clip_id: clipId }),
    });
  }

  async trainModel() {
    return this.request('/train/ctr-model', { method: 'POST' });
  }

  // Rendering
  async createRenderJob(storyboard: any, previewOnly: boolean = false) {
    return this.request('/render/remix', {
      method: 'POST',
      body: JSON.stringify({ storyboard, preview_only: previewOnly }),
    });
  }

  async getRenderStatus(jobId: string) {
    return this.request(`/render/status/${jobId}`);
  }

  // Publishing
  async publishAd(adData: any) {
    return this.request('/publish/meta', {
      method: 'POST',
      body: JSON.stringify(adData),
    });
  }

  async getInsights(adId: string, predictionId: string) {
    return this.request(`/insights?ad_id=${adId}&prediction_id=${predictionId}`);
  }
}

export const api = new APIClient();
```

### 2. Update Assets Page
Update `services/frontend/src/pages/Assets.tsx`:
```typescript
import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Link } from 'react-router-dom';

export default function Assets() {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploadPath, setUploadPath] = useState('');
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadAssets();
  }, []);

  const loadAssets = async () => {
    try {
      setLoading(true);
      const data = await api.getAssets();
      setAssets(data.assets);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    try {
      setUploading(true);
      await api.ingestVideo(uploadPath);
      setUploadPath('');
      // Reload assets after upload
      setTimeout(loadAssets, 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  if (loading) return <div className="loading">Loading assets...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="assets-page">
      <h1>Video Assets</h1>

      <div className="upload-section">
        <input
          type="text"
          value={uploadPath}
          onChange={(e) => setUploadPath(e.target.value)}
          placeholder="/path/to/video.mp4"
        />
        <button onClick={handleUpload} disabled={uploading || !uploadPath}>
          {uploading ? 'Uploading...' : 'Ingest Video'}
        </button>
      </div>

      <div className="assets-grid">
        {assets.map((asset) => (
          <div key={asset.asset_id} className="asset-card">
            <h3>{asset.filename}</h3>
            <p>Duration: {asset.duration_seconds}s</p>
            <p>Status: <span className={`status-${asset.status}`}>{asset.status}</span></p>
            {asset.status === 'completed' && (
              <Link to={`/clips/${asset.asset_id}`}>
                <button>View Clips</button>
              </Link>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 3. Update Ranked Clips Page
Update `services/frontend/src/pages/RankedClips.tsx`:
```typescript
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client';

export default function RankedClips() {
  const { assetId } = useParams();
  const [clips, setClips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEmotional, setShowEmotional] = useState(false);
  const [selectedClips, setSelectedClips] = useState([]);

  useEffect(() => {
    loadClips();
  }, [assetId, showEmotional]);

  const loadClips = async () => {
    try {
      setLoading(true);
      const data = showEmotional
        ? await api.getEmotionalClips(assetId)
        : await api.getClips(assetId, true);
      setClips(data.clips);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleClipSelection = (clipId: string) => {
    setSelectedClips(prev =>
      prev.includes(clipId)
        ? prev.filter(id => id !== clipId)
        : [...prev, clipId]
    );
  };

  const handlePredictCTR = async (clipId: string) => {
    try {
      const result = await api.predictCTR(clipId);
      alert(`Predicted CTR: ${(result.predicted_ctr * 100).toFixed(2)}%\nBand: ${result.predicted_band}`);
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const handleCreateAd = () => {
    if (selectedClips.length === 0) {
      alert('Select at least one clip');
      return;
    }
    // Navigate to render page with selected clips
    window.location.href = `/render?clips=${selectedClips.join(',')}`;
  };

  if (loading) return <div className="loading">Loading clips...</div>;

  return (
    <div className="clips-page">
      <h1>Ranked Clips</h1>

      <div className="controls">
        <label>
          <input
            type="checkbox"
            checked={showEmotional}
            onChange={(e) => setShowEmotional(e.target.checked)}
          />
          Show only emotional clips
        </label>
        <button onClick={handleCreateAd} disabled={selectedClips.length === 0}>
          Create Ad from Selected ({selectedClips.length})
        </button>
      </div>

      <div className="clips-grid">
        {clips.map((clip) => (
          <div
            key={clip.clip_id}
            className={`clip-card ${selectedClips.includes(clip.clip_id) ? 'selected' : ''}`}
            onClick={() => toggleClipSelection(clip.clip_id)}
          >
            <img src={clip.thumbnail_url || '/placeholder.jpg'} alt="Clip thumbnail" />
            <div className="clip-info">
              <p>Duration: {clip.duration.toFixed(1)}s</p>
              <p>Score: {(clip.scene_score * 100).toFixed(0)}%</p>
              {clip.emotion_data && (
                <p>Emotion: {clip.emotion_data.dominant} ({(clip.emotion_data.priority_score * 100).toFixed(0)}%)</p>
              )}
              <button onClick={(e) => {
                e.stopPropagation();
                handlePredictCTR(clip.clip_id);
              }}>
                Predict CTR
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 4. Update Render Job Page
Update `services/frontend/src/pages/RenderJob.tsx`:
```typescript
import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api/client';

export default function RenderJob() {
  const [searchParams] = useSearchParams();
  const clipIds = searchParams.get('clips')?.split(',') || [];

  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [outputUrl, setOutputUrl] = useState(null);
  const [isPreview, setIsPreview] = useState(true);

  const startRender = async () => {
    try {
      setStatus('queued');

      // Create storyboard from selected clips
      const storyboard = {
        clips: clipIds.map(id => ({ clip_id: id, transition: 'fade' })),
        resolution: '1920x1080',
        fps: 30
      };

      const result = await api.createRenderJob(storyboard, isPreview);
      setJobId(result.job_id);

      // Poll for status
      pollStatus(result.job_id);
    } catch (err) {
      alert(`Error: ${err.message}`);
      setStatus('failed');
    }
  };

  const pollStatus = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const result = await api.getRenderStatus(id);
        setStatus(result.status);

        if (result.status === 'completed') {
          setOutputUrl(result.output_url);
          clearInterval(interval);
        } else if (result.status === 'failed') {
          clearInterval(interval);
          alert(`Render failed: ${result.error}`);
        }
      } catch (err) {
        console.error(err);
      }
    }, 2000);
  };

  const handlePublish = async () => {
    if (!outputUrl) return;

    try {
      const result = await api.publishAd({
        video_url: outputUrl,
        caption: 'AI-generated ad',
        targeting: { age_range: [25, 45] },
        budget: { daily_budget: 100, currency: 'USD' }
      });

      alert(`Ad published! Ad ID: ${result.ad_id}`);
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  return (
    <div className="render-page">
      <h1>Create Ad</h1>

      <div className="render-controls">
        <p>Selected clips: {clipIds.length}</p>
        <label>
          <input
            type="checkbox"
            checked={isPreview}
            onChange={(e) => setIsPreview(e.target.checked)}
          />
          Preview only (fast)
        </label>
        <button onClick={startRender} disabled={status !== 'idle'}>
          {isPreview ? 'Generate Preview' : 'Render Full Ad'}
        </button>
      </div>

      {status !== 'idle' && (
        <div className="render-status">
          <h2>Status: {status}</h2>
          {status === 'processing' && <div className="spinner">Rendering...</div>}
          {status === 'completed' && outputUrl && (
            <div>
              <video controls src={outputUrl} style={{maxWidth: '100%'}} />
              <button onClick={handlePublish}>Publish to Meta</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

### 5. Environment Configuration
Create `services/frontend/.env.example`:
```
VITE_API_URL=http://localhost:8080
```

## Deliverables
- [ ] API client implemented
- [ ] Assets page with upload
- [ ] Ranked clips page with selection
- [ ] Render page with preview
- [ ] Emotion filtering toggle
- [ ] CTR prediction button
- [ ] Publish to Meta button
- [ ] Loading states everywhere
- [ ] Error handling

## Branch
`agent-5-frontend-integration`

## Blockers
None (can work with stub responses initially)

## Who Depends On You
- Agent 6 (needs base UI for enhancement)
