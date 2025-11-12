import { useState } from 'react';
import { searchClips } from '../services/api';

export default function SemanticSearchPanel() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    try {
      const data = await searchClips(query);
      setResults(data.results || []);
    } catch (err) {
      console.error(err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="card">
        <div className="panel-header">
          <h2>Semantic Search</h2>
        </div>

        <p style={{ marginBottom: '15px', color: '#666' }}>
          Search for video clips using natural language. The system uses sentence embeddings to find semantically similar content.
        </p>

        <div style={{ display: 'flex', gap: '10px', marginBottom: '30px' }}>
          <input
            type="text"
            className="input"
            placeholder="e.g., 'person doing squats', 'weight loss transformation', 'workout motivation'"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button className="button" onClick={handleSearch} disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        {loading && <div className="loading">Searching clips...</div>}

        {!loading && searched && results.length === 0 && (
          <p style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
            No results found for "{query}"
          </p>
        )}

        {!loading && results.length > 0 && (
          <div>
            <h3 style={{ marginBottom: '15px' }}>Results ({results.length})</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {results.map((result, idx) => (
                <div key={result.clip_id} className="card" style={{ border: '1px solid #e0e0e0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span className="status-badge info">#{idx + 1}</span>
                      <span style={{ marginLeft: '10px', fontWeight: 'bold' }}>
                        Similarity: {(result.similarity * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      Clip ID: {result.clip_id}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
