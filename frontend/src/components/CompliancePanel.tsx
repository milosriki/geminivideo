import { useState } from 'react';

export default function CompliancePanel() {
  // Sample compliance data
  const [compliance] = useState({
    passed: false,
    checks: {
      resolution: { passed: true, actual: [1080, 1920], expected: [1080, 1920] },
      duration: { passed: true, duration: 15.5, min: 3, max: 90, warning: false },
      hook_text_length: { passed: false, length: 42, max: 38, text: 'Get fit in 30 days with our proven program' },
      contrast_ratio: { passed: true, ratio: 5.2, min: 4.5 },
      subtitles_present: true
    },
    failed: ['hook_text_length'],
    warnings: []
  });

  return (
    <div>
      <div className="card">
        <div className="panel-header">
          <h2>Compliance Checker</h2>
          <span className={`status-badge ${compliance.passed ? 'success' : 'error'}`}>
            {compliance.passed ? 'ALL CHECKS PASSED' : 'ISSUES DETECTED'}
          </span>
        </div>

        <p style={{ marginBottom: '20px', color: '#666' }}>
          Platform compliance checks for Instagram Reels, Facebook Reels, and Stories.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {/* Resolution Check */}
          <div className="card" style={{ border: '1px solid #e0e0e0' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <h3 style={{ marginBottom: '5px' }}>Resolution</h3>
                <p style={{ fontSize: '14px', color: '#666' }}>
                  Expected: {compliance.checks.resolution.expected.join('x')}, 
                  Actual: {compliance.checks.resolution.actual.join('x')}
                </p>
              </div>
              <span className={`status-badge ${compliance.checks.resolution.passed ? 'success' : 'error'}`}>
                {compliance.checks.resolution.passed ? '✓ PASS' : '✗ FAIL'}
              </span>
            </div>
          </div>

          {/* Duration Check */}
          <div className="card" style={{ border: '1px solid #e0e0e0' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <h3 style={{ marginBottom: '5px' }}>Duration</h3>
                <p style={{ fontSize: '14px', color: '#666' }}>
                  {compliance.checks.duration.duration}s (Range: {compliance.checks.duration.min}-{compliance.checks.duration.max}s)
                </p>
                {compliance.checks.duration.warning && (
                  <p style={{ fontSize: '12px', color: '#856404', marginTop: '5px' }}>
                    ⚠ Warning: Duration &gt; 60s may have lower completion rates
                  </p>
                )}
              </div>
              <span className={`status-badge ${compliance.checks.duration.passed ? 'success' : 'error'}`}>
                {compliance.checks.duration.passed ? '✓ PASS' : '✗ FAIL'}
              </span>
            </div>
          </div>

          {/* Hook Text Length Check */}
          <div className="card" style={{ border: '1px solid #e0e0e0' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ flex: 1 }}>
                <h3 style={{ marginBottom: '5px' }}>Hook Text Length (First 3s)</h3>
                <p style={{ fontSize: '14px', color: '#666' }}>
                  {compliance.checks.hook_text_length.length} chars (Max: {compliance.checks.hook_text_length.max})
                </p>
                <p style={{ fontSize: '12px', color: '#666', marginTop: '5px', fontStyle: 'italic' }}>
                  "{compliance.checks.hook_text_length.text}"
                </p>
                {!compliance.checks.hook_text_length.passed && (
                  <p style={{ fontSize: '12px', color: '#721c24', marginTop: '5px' }}>
                    ✗ Text exceeds Instagram's recommended 38 character limit
                  </p>
                )}
              </div>
              <span className={`status-badge ${compliance.checks.hook_text_length.passed ? 'success' : 'error'}`}>
                {compliance.checks.hook_text_length.passed ? '✓ PASS' : '✗ FAIL'}
              </span>
            </div>
          </div>

          {/* Contrast Ratio Check */}
          <div className="card" style={{ border: '1px solid #e0e0e0' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <h3 style={{ marginBottom: '5px' }}>Contrast Ratio</h3>
                <p style={{ fontSize: '14px', color: '#666' }}>
                  {compliance.checks.contrast_ratio.ratio.toFixed(1)}:1 (Min: {compliance.checks.contrast_ratio.min}:1)
                </p>
              </div>
              <span className={`status-badge ${compliance.checks.contrast_ratio.passed ? 'success' : 'error'}`}>
                {compliance.checks.contrast_ratio.passed ? '✓ PASS' : '✗ FAIL'}
              </span>
            </div>
          </div>

          {/* Subtitles Check */}
          <div className="card" style={{ border: '1px solid #e0e0e0' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <h3 style={{ marginBottom: '5px' }}>Subtitles Present</h3>
                <p style={{ fontSize: '14px', color: '#666' }}>
                  {compliance.checks.subtitles_present ? 'Subtitles included' : 'No subtitles found'}
                </p>
              </div>
              <span className={`status-badge ${compliance.checks.subtitles_present ? 'success' : 'error'}`}>
                {compliance.checks.subtitles_present ? '✓ PASS' : '✗ FAIL'}
              </span>
            </div>
          </div>
        </div>

        {compliance.failed.length > 0 && (
          <div className="error" style={{ marginTop: '20px' }}>
            <strong>Failed Checks:</strong> {compliance.failed.join(', ')}
          </div>
        )}
      </div>
    </div>
  );
}
