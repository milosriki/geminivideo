import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AnalyticsDashboard } from './AnalyticsDashboard';

/**
 * Example usage of the Analytics Dashboard component
 *
 * This file demonstrates various ways to integrate and use the Analytics Dashboard
 * in your application.
 */

// Create a query client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: true,
      retry: 3,
    },
  },
});

// ============================================================================
// EXAMPLE 1: Basic Usage
// ============================================================================

export function BasicAnalyticsDashboard() {
  return (
    <QueryClientProvider client={queryClient}>
      <AnalyticsDashboard />
    </QueryClientProvider>
  );
}

// ============================================================================
// EXAMPLE 2: With Pre-selected Campaigns
// ============================================================================

export function CampaignSpecificDashboard() {
  const campaignIds = ['campaign_123', 'campaign_456', 'campaign_789'];

  return (
    <QueryClientProvider client={queryClient}>
      <AnalyticsDashboard campaignIds={campaignIds} />
    </QueryClientProvider>
  );
}

// ============================================================================
// EXAMPLE 3: Embedded in Application with Navigation
// ============================================================================

export function AppWithAnalytics() {
  const [currentView, setCurrentView] = React.useState<'campaigns' | 'analytics' | 'settings'>('analytics');
  const [selectedCampaigns, setSelectedCampaigns] = React.useState<string[]>([]);

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-900">
        {/* Navigation Bar */}
        <nav className="bg-gray-800 border-b border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-4">
                <span className="text-xl font-bold text-white">GeminiVideo</span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setCurrentView('campaigns')}
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      currentView === 'campaigns'
                        ? 'bg-gray-900 text-white'
                        : 'text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    Campaigns
                  </button>
                  <button
                    onClick={() => setCurrentView('analytics')}
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      currentView === 'analytics'
                        ? 'bg-gray-900 text-white'
                        : 'text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    Analytics
                  </button>
                  <button
                    onClick={() => setCurrentView('settings')}
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      currentView === 'settings'
                        ? 'bg-gray-900 text-white'
                        : 'text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    Settings
                  </button>
                </div>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto">
          {currentView === 'analytics' && (
            <AnalyticsDashboard campaignIds={selectedCampaigns} />
          )}
          {currentView === 'campaigns' && (
            <div className="p-6">
              <h2 className="text-2xl font-bold text-white mb-4">Campaigns</h2>
              <p className="text-gray-400">Campaign management view...</p>
            </div>
          )}
          {currentView === 'settings' && (
            <div className="p-6">
              <h2 className="text-2xl font-bold text-white mb-4">Settings</h2>
              <p className="text-gray-400">Application settings...</p>
            </div>
          )}
        </main>
      </div>
    </QueryClientProvider>
  );
}

// ============================================================================
// EXAMPLE 4: With Campaign Selector
// ============================================================================

export function AnalyticsWithCampaignSelector() {
  const [selectedCampaigns, setSelectedCampaigns] = React.useState<string[]>([]);
  const [availableCampaigns] = React.useState([
    { id: 'campaign_1', name: 'Summer Sale 2024' },
    { id: 'campaign_2', name: 'Product Launch Q1' },
    { id: 'campaign_3', name: 'Holiday Campaign' },
    { id: 'campaign_4', name: 'Brand Awareness' },
  ]);

  const toggleCampaign = (campaignId: string) => {
    setSelectedCampaigns((prev) =>
      prev.includes(campaignId)
        ? prev.filter((id) => id !== campaignId)
        : [...prev, campaignId]
    );
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto p-6 space-y-6">
          {/* Campaign Selector */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-4">Select Campaigns</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {availableCampaigns.map((campaign) => (
                <button
                  key={campaign.id}
                  onClick={() => toggleCampaign(campaign.id)}
                  className={`px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                    selectedCampaigns.includes(campaign.id)
                      ? 'bg-indigo-600 text-white ring-2 ring-indigo-400'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {selectedCampaigns.includes(campaign.id) && (
                    <span className="mr-2">✓</span>
                  )}
                  {campaign.name}
                </button>
              ))}
            </div>
            {selectedCampaigns.length > 0 && (
              <div className="mt-4 flex items-center justify-between">
                <span className="text-sm text-gray-400">
                  {selectedCampaigns.length} campaign{selectedCampaigns.length !== 1 ? 's' : ''} selected
                </span>
                <button
                  onClick={() => setSelectedCampaigns([])}
                  className="text-sm text-red-400 hover:text-red-300 underline"
                >
                  Clear all
                </button>
              </div>
            )}
          </div>

          {/* Analytics Dashboard */}
          {selectedCampaigns.length > 0 ? (
            <AnalyticsDashboard campaignIds={selectedCampaigns} />
          ) : (
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-12 text-center">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-xl font-semibold mb-2">No Campaigns Selected</h3>
              <p className="text-gray-400">
                Select one or more campaigns above to view analytics
              </p>
            </div>
          )}
        </div>
      </div>
    </QueryClientProvider>
  );
}

// ============================================================================
// EXAMPLE 5: Multiple Dashboards in Tabs
// ============================================================================

export function MultiDashboardView() {
  const [activeTab, setActiveTab] = React.useState<'all' | 'facebook' | 'google'>('all');

  const campaignGroups = {
    all: ['campaign_1', 'campaign_2', 'campaign_3', 'campaign_4'],
    facebook: ['campaign_1', 'campaign_2'],
    google: ['campaign_3', 'campaign_4'],
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-900 text-white p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold">Performance Analytics</h1>
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab('all')}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  activeTab === 'all'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-800 text-gray-400'
                }`}
              >
                All Platforms
              </button>
              <button
                onClick={() => setActiveTab('facebook')}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  activeTab === 'facebook'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-800 text-gray-400'
                }`}
              >
                Facebook
              </button>
              <button
                onClick={() => setActiveTab('google')}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  activeTab === 'google'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-800 text-gray-400'
                }`}
              >
                Google
              </button>
            </div>
          </div>

          <AnalyticsDashboard campaignIds={campaignGroups[activeTab]} />
        </div>
      </div>
    </QueryClientProvider>
  );
}

// ============================================================================
// EXAMPLE 6: With Custom Styling
// ============================================================================

export function CustomStyledDashboard() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <div className="max-w-7xl mx-auto p-6">
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 shadow-2xl">
            <AnalyticsDashboard campaignIds={['campaign_1']} />
          </div>
        </div>
      </div>
    </QueryClientProvider>
  );
}

// ============================================================================
// EXAMPLE 7: Integration with Authentication
// ============================================================================

export function AuthenticatedDashboard() {
  const [isAuthenticated, setIsAuthenticated] = React.useState(false);
  const [user, setUser] = React.useState<{ name: string; campaigns: string[] } | null>(null);

  React.useEffect(() => {
    // Simulate authentication check
    const checkAuth = async () => {
      // In real app, check with your auth provider
      const mockUser = {
        name: 'John Doe',
        campaigns: ['campaign_1', 'campaign_2', 'campaign_3'],
      };
      setUser(mockUser);
      setIsAuthenticated(true);
    };

    checkAuth();
  }, []);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-900">
        <header className="bg-gray-800 border-b border-gray-700">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <h1 className="text-xl font-bold text-white">Analytics Dashboard</h1>
            <div className="flex items-center gap-4">
              <span className="text-gray-400">Welcome, {user?.name}</span>
              <button
                onClick={() => setIsAuthenticated(false)}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm"
              >
                Logout
              </button>
            </div>
          </div>
        </header>
        <main>
          <AnalyticsDashboard campaignIds={user?.campaigns || []} />
        </main>
      </div>
    </QueryClientProvider>
  );
}

// ============================================================================
// EXAMPLE 8: With Error Boundary
// ============================================================================

class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Dashboard error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center p-6">
          <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-8 max-w-lg">
            <h2 className="text-2xl font-bold text-red-400 mb-4">Something went wrong</h2>
            <p className="text-gray-300 mb-4">
              The analytics dashboard encountered an error. Please try refreshing the page.
            </p>
            <details className="text-sm text-gray-400">
              <summary className="cursor-pointer mb-2">Error details</summary>
              <pre className="bg-gray-800 p-4 rounded overflow-x-auto">
                {this.state.error?.toString()}
              </pre>
            </details>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export function SafeAnalyticsDashboard() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AnalyticsDashboard />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

// ============================================================================
// EXPORT DEFAULT FOR TESTING
// ============================================================================

export default function AnalyticsDashboardExamples() {
  const [example, setExample] = React.useState<number>(1);

  const examples = [
    { id: 1, name: 'Basic', component: <BasicAnalyticsDashboard /> },
    { id: 2, name: 'Campaign Specific', component: <CampaignSpecificDashboard /> },
    { id: 3, name: 'With Navigation', component: <AppWithAnalytics /> },
    { id: 4, name: 'With Selector', component: <AnalyticsWithCampaignSelector /> },
    { id: 5, name: 'Multi Dashboard', component: <MultiDashboardView /> },
    { id: 6, name: 'Custom Styled', component: <CustomStyledDashboard /> },
    { id: 7, name: 'Authenticated', component: <AuthenticatedDashboard /> },
    { id: 8, name: 'With Error Boundary', component: <SafeAnalyticsDashboard /> },
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold mb-4">Analytics Dashboard Examples</h1>
          <div className="flex flex-wrap gap-2">
            {examples.map((ex) => (
              <button
                key={ex.id}
                onClick={() => setExample(ex.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  example === ex.id
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {ex.id}. {ex.name}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div>{examples.find((ex) => ex.id === example)?.component}</div>
    </div>
  );
}
