/**
 * ABTestingDashboard Integration Examples
 *
 * This file shows various ways to integrate the A/B Testing Dashboard
 * into your application.
 */

import React from 'react';
import ABTestingDashboard from './ABTestingDashboard';

// ============================================================================
// EXAMPLE 1: Basic Usage
// ============================================================================

export const BasicExample: React.FC = () => {
  return (
    <div className="app">
      <ABTestingDashboard />
    </div>
  );
};

// ============================================================================
// EXAMPLE 2: With Router Integration
// ============================================================================

import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';

export const RouterExample: React.FC = () => {
  return (
    <Router>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/ab-testing">A/B Testing</Link>
      </nav>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/ab-testing" element={<ABTestingDashboard />} />
      </Routes>
    </Router>
  );
};

const Home: React.FC = () => <div>Home Page</div>;

// ============================================================================
// EXAMPLE 3: With API Integration
// ============================================================================

export const APIIntegrationExample: React.FC = () => {
  // In the real component, you would modify the useEffect to fetch from API
  // Here's the pattern:

  /*
  useEffect(() => {
    // Fetch experiments from API
    const fetchExperiments = async () => {
      try {
        const response = await fetch('/api/v1/experiments');
        const data = await response.json();
        setExperiments(data.experiments);
      } catch (error) {
        console.error('Failed to fetch experiments:', error);
      }
    };

    fetchExperiments();

    // Set up WebSocket for real-time updates
    const ws = new WebSocket('wss://api.example.com/experiments/stream');

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setExperiments(prev =>
        prev.map(exp => exp.id === update.id ? { ...exp, ...update } : exp)
      );
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      ws.close();
    };
  }, []);
  */

  return <ABTestingDashboard />;
};

// ============================================================================
// EXAMPLE 4: Custom Event Handlers
// ============================================================================

export const CustomHandlersExample: React.FC = () => {
  // You can wrap the dashboard and add custom event handlers

  const handleExperimentCreated = (experiment: any) => {
    console.log('New experiment created:', experiment);
    // Send to analytics
    // Update global state
  };

  const handleExperimentPaused = (experimentId: string) => {
    console.log('Experiment paused:', experimentId);
    // Send notification
    // Log to audit trail
  };

  const handleBudgetChanged = (experimentId: string, newAllocation: any) => {
    console.log('Budget changed:', { experimentId, newAllocation });
    // Update backend
    // Send alert to team
  };

  // In production, you'd modify the component to accept these as props
  return <ABTestingDashboard />;
};

// ============================================================================
// EXAMPLE 5: With State Management (Redux/Zustand)
// ============================================================================

import { useSelector, useDispatch } from 'react-redux';

export const ReduxExample: React.FC = () => {
  // const experiments = useSelector((state: any) => state.experiments.list);
  // const dispatch = useDispatch();

  // useEffect(() => {
  //   dispatch(fetchExperiments());
  // }, [dispatch]);

  return <ABTestingDashboard />;
};

// ============================================================================
// EXAMPLE 6: Embedded in Larger Dashboard
// ============================================================================

export const EmbeddedExample: React.FC = () => {
  return (
    <div className="main-dashboard">
      <header className="main-header">
        <h1>Video Analytics Platform</h1>
      </header>

      <div className="dashboard-layout">
        <aside className="sidebar">
          <nav>
            <ul>
              <li>Overview</li>
              <li>Performance</li>
              <li>A/B Testing</li>
              <li>Settings</li>
            </ul>
          </nav>
        </aside>

        <main className="main-content">
          <ABTestingDashboard />
        </main>
      </div>
    </div>
  );
};

// ============================================================================
// EXAMPLE 7: With Authentication Guard
// ============================================================================

import { useAuth } from '../hooks/useAuth';

export const AuthenticatedExample: React.FC = () => {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <div>Please log in to view A/B testing dashboard</div>;
  }

  if (!user.permissions.includes('ab_testing')) {
    return <div>You don't have permission to access this feature</div>;
  }

  return <ABTestingDashboard />;
};

// ============================================================================
// EXAMPLE 8: With Loading and Error States
// ============================================================================

export const LoadingExample: React.FC = () => {
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    // Simulate loading
    setTimeout(() => setLoading(false), 2000);
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        <p>Loading A/B testing dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error Loading Dashboard</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  return <ABTestingDashboard />;
};

// ============================================================================
// EXAMPLE 9: With Analytics Tracking
// ============================================================================

export const AnalyticsExample: React.FC = () => {
  React.useEffect(() => {
    // Track page view
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'page_view', {
        page_title: 'A/B Testing Dashboard',
        page_location: window.location.href,
        page_path: '/ab-testing',
      });
    }
  }, []);

  return <ABTestingDashboard />;
};

// ============================================================================
// EXAMPLE 10: Responsive Mobile Version
// ============================================================================

export const ResponsiveExample: React.FC = () => {
  const [isMobile, setIsMobile] = React.useState(false);

  React.useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);

    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  return (
    <div className={isMobile ? 'mobile-layout' : 'desktop-layout'}>
      <ABTestingDashboard />
    </div>
  );
};

// ============================================================================
// API Service Layer Example
// ============================================================================

export class ABTestingService {
  private baseURL = '/api/v1';

  async getExperiments() {
    const response = await fetch(`${this.baseURL}/experiments`);
    if (!response.ok) throw new Error('Failed to fetch experiments');
    return response.json();
  }

  async getExperiment(id: string) {
    const response = await fetch(`${this.baseURL}/experiments/${id}`);
    if (!response.ok) throw new Error('Failed to fetch experiment');
    return response.json();
  }

  async createExperiment(data: any) {
    const response = await fetch(`${this.baseURL}/experiments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create experiment');
    return response.json();
  }

  async updateExperiment(id: string, data: any) {
    const response = await fetch(`${this.baseURL}/experiments/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update experiment');
    return response.json();
  }

  async deleteExperiment(id: string) {
    const response = await fetch(`${this.baseURL}/experiments/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete experiment');
    return response.json();
  }

  async pauseExperiment(id: string) {
    return this.updateExperiment(id, { status: 'paused' });
  }

  async resumeExperiment(id: string) {
    return this.updateExperiment(id, { status: 'running' });
  }

  async updateBudgetAllocation(id: string, allocation: any) {
    const response = await fetch(`${this.baseURL}/experiments/${id}/budget`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(allocation),
    });
    if (!response.ok) throw new Error('Failed to update budget');
    return response.json();
  }

  async getVariantPerformance(experimentId: string, variantId: string, timeRange: string = '7d') {
    const response = await fetch(
      `${this.baseURL}/experiments/${experimentId}/variants/${variantId}/performance?range=${timeRange}`
    );
    if (!response.ok) throw new Error('Failed to fetch variant performance');
    return response.json();
  }

  subscribeToUpdates(experimentId: string, callback: (data: any) => void) {
    const ws = new WebSocket(`wss://api.example.com/experiments/${experimentId}/stream`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      callback(data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => ws.close();
  }
}

// ============================================================================
// Usage with Service Layer
// ============================================================================

export const ServiceLayerExample: React.FC = () => {
  const [experiments, setExperiments] = React.useState([]);
  const service = new ABTestingService();

  React.useEffect(() => {
    service.getExperiments()
      .then(data => setExperiments(data))
      .catch(error => console.error(error));
  }, []);

  return <ABTestingDashboard />;
};

// ============================================================================
// Export all examples
// ============================================================================

export default {
  BasicExample,
  RouterExample,
  APIIntegrationExample,
  CustomHandlersExample,
  ReduxExample,
  EmbeddedExample,
  AuthenticatedExample,
  LoadingExample,
  AnalyticsExample,
  ResponsiveExample,
  ServiceLayerExample,
};
