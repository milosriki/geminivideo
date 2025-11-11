import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

interface Clip {
  clip_id: string;
  asset_id: string;
  start_time: number;
  end_time: number;
  duration: number;
  scene_score: number;
  features: {
    motion_energy: number;
    face_detected: boolean;
    text_overlay: boolean;
    [key: string]: any;
  };
}

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8081';

export default function RankedClips() {
  const { assetId } = useParams<{ assetId: string }>();
  const [clips, setClips] = useState<Clip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedClips, setSelectedClips] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (assetId) fetchClips();
  }, [assetId]);

  const fetchClips = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${GATEWAY_URL}/assets/${assetId}/clips?ranked=true&top=10`);
      if (!response.ok) throw new Error('Failed to fetch clips');
      const data = await response.json();
      setClips(data.clips || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const toggleClipSelection = (clipId: string) => {
    const newSelection = new Set(selectedClips);
    if (newSelection.has(clipId)) {
      newSelection.delete(clipId);
    } else {
      newSelection.add(clipId);
    }
    setSelectedClips(newSelection);
  };

  const createStoryboard = () => {
    const selectedClipData = clips.filter(c => selectedClips.has(c.clip_id));
    const storyboard = selectedClipData.map(clip => ({
      clip_id: clip.clip_id,
      asset_id: clip.asset_id,
      start_time: clip.start_time,
      end_time: clip.end_time,
      transition: 'fade'
    }));

    // Navigate to render page with storyboard
    localStorage.setItem('storyboard', JSON.stringify(storyboard));
    window.location.href = '/render';
  };

  if (loading) return <div className="loading">Loading clips...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="ranked-clips-page">
      <h1>Ranked Clips</h1>
      <div className="actions">
        <button onClick={createStoryboard} disabled={selectedClips.size === 0}>
          Create Ad from {selectedClips.size} Selected Clips
        </button>
      </div>
      <div className="clips-list">
        {clips.length === 0 ? (
          <div className="no-clips">No clips available for this asset.</div>
        ) : (
          clips.map(clip => (
            <div 
              key={clip.clip_id} 
              className={`clip-card ${selectedClips.has(clip.clip_id) ? 'selected' : ''}`}
              onClick={() => toggleClipSelection(clip.clip_id)}
            >
              <div className="clip-thumbnail">
                {clip.features.thumbnail_url ? (
                  <img src={clip.features.thumbnail_url} alt="Clip thumbnail" />
                ) : (
                  <div className="thumbnail-placeholder">No preview</div>
                )}
              </div>
              <div className="clip-info">
                <h3>Clip {clip.start_time.toFixed(1)}s - {clip.end_time.toFixed(1)}s</h3>
                <div className="score">
                  <span className="score-label">Scene Score:</span>
                  <span className="score-value">{(clip.scene_score * 100).toFixed(0)}%</span>
                </div>
                <div className="features">
                  <span className={clip.features.face_detected ? 'feature-active' : 'feature-inactive'}>
                    👤 Face
                  </span>
                  <span className={clip.features.text_overlay ? 'feature-active' : 'feature-inactive'}>
                    📝 Text
                  </span>
                  <span className="feature-active">
                    ⚡ Motion: {(clip.features.motion_energy * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
