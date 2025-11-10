import { useState, useEffect } from 'react';
import { assetsApi } from '../services/api';

interface RankedClipsPanelProps {
  assetId: string | null;
  onSelectClips: (clips: any[]) => void;
}

export function RankedClipsPanel({ assetId, onSelectClips }: RankedClipsPanelProps) {
  const [clips, setClips] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedClipIds, setSelectedClipIds] = useState<Set<string>>(new Set());
  const [topN, setTopN] = useState(5);

  useEffect(() => {
    if (assetId) {
      loadClips();
    } else {
      setClips([]);
    }
  }, [assetId, topN]);

  const loadClips = async () => {
    if (!assetId) return;

    try {
      setLoading(true);
      setError(null);
      const response = await assetsApi.getClips(assetId, true, topN);
      setClips(response.data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleClipSelection = (clipId: string) => {
    const newSelection = new Set(selectedClipIds);
    if (newSelection.has(clipId)) {
      newSelection.delete(clipId);
    } else {
      newSelection.add(clipId);
    }
    setSelectedClipIds(newSelection);
    
    // Update parent with selected clips
    const selected = clips.filter(c => newSelection.has(c.id));
    onSelectClips(selected);
  };

  return (
    <div className="panel">
      <h2>⭐ Ranked Clips</h2>

      <div style={{ marginBottom: '15px' }}>
        <label style={{ fontSize: '14px', display: 'block', marginBottom: '5px' }}>
          Show top:
        </label>
        <select 
          className="input" 
          value={topN} 
          onChange={(e) => setTopN(Number(e.target.value))}
          style={{ width: 'auto', padding: '5px' }}
        >
          <option value={3}>3</option>
          <option value={5}>5</option>
          <option value={10}>10</option>
          <option value={20}>20</option>
        </select>
      </div>

      {error && <div className="error">{error}</div>}

      {!assetId && (
        <div style={{ textAlign: 'center', color: '#666', padding: '20px' }}>
          Select an asset to view ranked clips
        </div>
      )}

      {loading && <div className="loading">Analyzing clips...</div>}

      {!loading && clips.map((clip, index) => (
        <div 
          key={clip.id} 
          className="clip-card"
          style={{ cursor: 'pointer', border: selectedClipIds.has(clip.id) ? '2px solid #007bff' : undefined }}
          onClick={() => toggleClipSelection(clip.id)}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontWeight: 'bold', color: '#999' }}>#{index + 1}</span>
              <span className="score" style={{ marginLeft: '10px' }}>
                Score: {clip.rankScore.toFixed(2)}
              </span>
            </div>
            {selectedClipIds.has(clip.id) && <span>✓</span>}
          </div>
          
          <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
            {clip.start.toFixed(1)}s - {clip.end.toFixed(1)}s ({clip.duration.toFixed(1)}s)
          </div>

          {clip.objects.length > 0 && (
            <div className="tags">
              {clip.objects.slice(0, 5).map((obj: string, i: number) => (
                <span key={i} className="tag">{obj}</span>
              ))}
            </div>
          )}

          {clip.ocr_tokens.length > 0 && (
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              💬 {clip.ocr_tokens.slice(0, 3).join(', ')}
            </div>
          )}

          <div style={{ fontSize: '12px', marginTop: '8px' }}>
            🏃 Motion: {(clip.motion_score * 100).toFixed(0)}%
          </div>
        </div>
      ))}
    </div>
  );
}
