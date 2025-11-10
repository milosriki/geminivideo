export function DiversificationDashboard() {
  // Mock data for demonstration
  const triggerEntropy = 0.78;
  const personaCoverage = 0.65;
  const noveltyIndex = 0.82;

  return (
    <div className="panel">
      <h2>🎯 Diversification</h2>

      <div style={{ marginBottom: '20px' }}>
        <h3>Trigger Entropy</h3>
        <div className="meter">
          <div 
            className="meter-fill" 
            style={{ 
              width: `${triggerEntropy * 100}%`,
              background: '#007bff'
            }} 
          />
        </div>
        <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
          {(triggerEntropy * 100).toFixed(0)}% - Good variety of psychological triggers
        </div>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Persona Coverage</h3>
        <div className="meter">
          <div 
            className="meter-fill" 
            style={{ 
              width: `${personaCoverage * 100}%`,
              background: '#28a745'
            }} 
          />
        </div>
        <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
          {(personaCoverage * 100).toFixed(0)}% - Reaching 5 out of 8 personas
        </div>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Novelty Index</h3>
        <div className="meter">
          <div 
            className="meter-fill" 
            style={{ 
              width: `${noveltyIndex * 100}%`,
              background: '#ffc107'
            }} 
          />
        </div>
        <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
          {(noveltyIndex * 100).toFixed(0)}% - High content originality
        </div>
      </div>

      <div style={{ padding: '10px', background: '#e7f3ff', borderRadius: '4px', fontSize: '12px' }}>
        💡 <strong>Recommendation:</strong> Consider adding more clips targeting tech enthusiasts and parents
      </div>
    </div>
  );
}
