# Agent 6: UX Enhancement Specialist

## Your Mission
Polish the UI with loading states, error handling, animations, and metrics dashboard.

## Priority: LOW (Wait for Agent 5 base UI)

## Tasks

### 1. Loading States Component
Create `services/frontend/src/components/LoadingSpinner.tsx`:
```typescript
export function LoadingSpinner({ text = 'Loading...' }) {
  return (
    <div className="loading-container">
      <div className="spinner"></div>
      <p>{text}</p>
    </div>
  );
}

export function ProgressBar({ progress = 0, text = '' }) {
  return (
    <div className="progress-container">
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress}%` }}></div>
      </div>
      <p>{text} {progress}%</p>
    </div>
  );
}
```

### 2. Error Boundary
Create `services/frontend/src/components/ErrorBoundary.tsx`:
```typescript
import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h1>Something went wrong</h1>
          <p>{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### 3. Metrics Dashboard
Create `services/frontend/src/pages/Dashboard.tsx`:
```typescript
import { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function Dashboard() {
  const [metrics, setMetrics] = useState({
    totalAssets: 0,
    totalClips: 0,
    avgCTR: 0,
    topPerforming: []
  });

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      const assets = await api.getAssets();
      // Aggregate metrics
      setMetrics({
        totalAssets: assets.count,
        totalClips: assets.assets.reduce((sum, a) => sum + (a.clips_count || 0), 0),
        avgCTR: 0.045,  // Would calculate from predictions
        topPerforming: []  // Would load from DB
      });
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="dashboard">
      <h1>Performance Dashboard</h1>

      <div className="metrics-grid">
        <div className="metric-card">
          <h3>Total Assets</h3>
          <p className="metric-value">{metrics.totalAssets}</p>
        </div>
        <div className="metric-card">
          <h3>Total Clips</h3>
          <p className="metric-value">{metrics.totalClips}</p>
        </div>
        <div className="metric-card">
          <h3>Average CTR</h3>
          <p className="metric-value">{(metrics.avgCTR * 100).toFixed(2)}%</p>
        </div>
      </div>

      <div className="chart-section">
        <h2>Performance Over Time</h2>
        {/* Add chart library integration */}
      </div>
    </div>
  );
}
```

### 4. Enhanced CSS
Create `services/frontend/src/styles/enhanced.css`:
```css
/* Loading animations */
.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-top-color: #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Progress bar */
.progress-bar {
  width: 100%;
  height: 20px;
  background: #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3498db, #2ecc71);
  transition: width 0.3s ease;
}

/* Card hover effects */
.asset-card, .clip-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.asset-card:hover, .clip-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.15);
}

/* Clip selection */
.clip-card.selected {
  border: 3px solid #2ecc71;
  box-shadow: 0 0 15px rgba(46, 204, 113, 0.5);
}

/* Toast notifications */
.toast {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: #2c3e50;
  color: white;
  padding: 15px 20px;
  border-radius: 5px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.3);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { transform: translateX(400px); }
  to { transform: translateX(0); }
}

/* Status badges */
.status-processing {
  color: #f39c12;
  font-weight: bold;
}

.status-completed {
  color: #2ecc71;
  font-weight: bold;
}

.status-failed {
  color: #e74c3c;
  font-weight: bold;
}

/* Emotion indicators */
.emotion-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 3px;
  font-size: 0.85em;
  margin: 2px;
}

.emotion-happy { background: #2ecc71; color: white; }
.emotion-surprise { background: #f39c12; color: white; }
.emotion-neutral { background: #95a5a6; color: white; }

/* Responsive grid */
@media (max-width: 768px) {
  .assets-grid, .clips-grid {
    grid-template-columns: 1fr;
  }

  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
```

### 5. Toast Notifications
Create `services/frontend/src/components/Toast.tsx`:
```typescript
import { useState, useEffect } from 'react';

interface ToastProps {
  message: string;
  type?: 'success' | 'error' | 'info';
  duration?: number;
}

export function useToast() {
  const [toast, setToast] = useState<ToastProps | null>(null);

  const showToast = (message: string, type: ToastProps['type'] = 'info', duration = 3000) => {
    setToast({ message, type, duration });
    setTimeout(() => setToast(null), duration);
  };

  const ToastComponent = toast ? (
    <div className={`toast toast-${toast.type}`}>
      {toast.message}
    </div>
  ) : null;

  return { showToast, ToastComponent };
}
```

### 6. Keyboard Shortcuts
Create `services/frontend/src/hooks/useKeyboardShortcuts.ts`:
```typescript
import { useEffect } from 'react';

export function useKeyboardShortcuts(shortcuts: Record<string, () => void>) {
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      const key = e.key.toLowerCase();
      const withMod = e.ctrlKey || e.metaKey;

      for (const [combo, handler] of Object.entries(shortcuts)) {
        const [modifier, ...keys] = combo.split('+');
        const shortcutKey = keys.join('+') || modifier;

        if (modifier === 'ctrl' && withMod && key === shortcutKey) {
          e.preventDefault();
          handler();
        } else if (key === combo) {
          handler();
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [shortcuts]);
}
```

## Deliverables
- [ ] Loading spinner component
- [ ] Progress bar component
- [ ] Error boundary
- [ ] Toast notifications
- [ ] Enhanced CSS with animations
- [ ] Metrics dashboard
- [ ] Keyboard shortcuts
- [ ] Responsive design
- [ ] Status badges

## Branch
`agent-6-ux-enhancements`

## Blockers
- **Agent 5** (needs base UI first)

## Who Depends On You
Nobody (polish layer)
