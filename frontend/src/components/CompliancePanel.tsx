import { useState, useEffect } from 'react';

interface CompliancePanelProps {
  clips: any[];
}

export function CompliancePanel({ clips }: CompliancePanelProps) {
  const [compliance, setCompliance] = useState<any>(null);

  useEffect(() => {
    if (clips.length > 0) {
      // Simulate compliance check
      setCompliance({
        compliant: true,
        checks: {
          aspect_ratio: { passed: true, message: '9:16 (Reels/Stories)' },
          resolution: { passed: true, message: 'OK' },
          duration: { passed: true, message: 'OK' },
          first_3s_text_length: { passed: true, message: 'OK' },
          contrast_ratio: { passed: true, message: 'OK' },
          subtitles_present: { passed: false, message: 'No subtitles' },
          loudness_normalized: { passed: true, message: 'OK' }
        }
      });
    } else {
      setCompliance(null);
    }
  }, [clips]);

  return (
    <div className="panel">
      <h2>✅ Compliance</h2>

      {!compliance && (
        <div style={{ textAlign: 'center', color: '#666', padding: '20px' }}>
          Select clips to view compliance status
        </div>
      )}

      {compliance && (
        <>
          <div style={{ marginBottom: '15px' }}>
            <span className={`status ${compliance.compliant ? 'compliant' : 'non-compliant'}`}>
              {compliance.compliant ? 'COMPLIANT' : 'NON-COMPLIANT'}
            </span>
          </div>

          <h3>Checks</h3>
          
          {Object.entries(compliance.checks).map(([key, value]: [string, any]) => (
            <div 
              key={key} 
              style={{ 
                padding: '8px', 
                background: value.passed ? '#f8f9fa' : '#fff3cd',
                borderRadius: '4px',
                marginBottom: '8px',
                fontSize: '14px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 500 }}>
                  {value.passed ? '✓' : '⚠️'} {key.replace(/_/g, ' ')}
                </span>
                <span style={{ color: '#666', fontSize: '12px' }}>
                  {value.message}
                </span>
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
