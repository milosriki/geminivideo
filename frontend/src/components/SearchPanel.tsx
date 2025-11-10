import { useState } from 'react';
import { assetsApi } from '../services/api';

export function SearchPanel() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;

    try {
      setLoading(true);
      setError(null);
      const response = await assetsApi.searchClips(query, 10);
      setResults(response.data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel">
      <h2>🔍 Search Clips</h2>

      <input
        type="text"
        className="input"
        placeholder="Enter search query (semantic search)"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
      />
      
      <button className="button" onClick={handleSearch} disabled={loading}>
        {loading ? 'Searching...' : 'Search'}
      </button>

      {error && <div className="error">{error}</div>}

      {results.length > 0 && (
        <div style={{ marginTop: '15px' }}>
          <h3>{results.length} Results</h3>
          
          {results.map((clip, index) => (
            <div key={clip.id} className="clip-card">
              <div>
                <span style={{ fontWeight: 'bold', color: '#999' }}>#{index + 1}</span>
                <span className="score" style={{ marginLeft: '10px' }}>
                  Score: {clip.rankScore.toFixed(2)}
                </span>
              </div>
              
              <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                Video: {clip.videoId.substring(0, 8)}... • 
                {clip.start.toFixed(1)}s - {clip.end.toFixed(1)}s
              </div>

              {clip.ocr_tokens.length > 0 && (
                <div className="tags">
                  {clip.ocr_tokens.slice(0, 5).map((token: string, i: number) => (
                    <span key={i} className="tag">{token}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {!loading && results.length === 0 && query && (
        <div style={{ textAlign: 'center', color: '#666', padding: '20px' }}>
          No results found for "{query}"
        </div>
      )}
    </div>
  );
}
