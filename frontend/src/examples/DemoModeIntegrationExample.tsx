/**
 * Demo Mode Integration Examples
 *
 * Shows how to integrate demo mode into existing pages and components.
 */

import { useEffect, useState } from 'react';
import { useDemoMode, fetchWithDemoMode } from '@/hooks/useDemoMode';
import { DemoModeBadge } from '@/components/DemoModeIndicator';

// ============================================================================
// EXAMPLE 1: Analytics Dashboard with Demo Data
// ============================================================================

interface AnalyticsData {
  overview: {
    total_revenue: number;
    roas: number;
    conversions: number;
  };
  daily_breakdown: any[];
}

export function AnalyticsDashboardExample() {
  const { enabled: demoMode } = useDemoMode();
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);

        // Automatically fetches from /api/demo/analytics if demo mode is on
        const response = await fetchWithDemoMode('/api/analytics', demoMode);
        const data = await response.json();

        setAnalytics(data);
      } catch (error) {
        console.error('Error fetching analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, [demoMode]);

  if (loading) return <div>Loading...</div>;
  if (!analytics) return <div>No data</div>;

  return (
    <div className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-2xl font-bold">Analytics Dashboard</h1>
        {demoMode && <DemoModeBadge />}
      </div>

      <div className="grid grid-cols-3 gap-6">
        <MetricCard
          label="Total Revenue"
          value={`€${analytics.overview.total_revenue.toLocaleString()}`}
        />
        <MetricCard
          label="ROAS"
          value={`${analytics.overview.roas.toFixed(2)}x`}
        />
        <MetricCard
          label="Conversions"
          value={analytics.overview.conversions.toLocaleString()}
        />
      </div>

      {/* Show demo indicator */}
      {demoMode && (
        <div className="mt-4 p-4 rounded-lg bg-violet-500/10 border border-violet-500/30">
          <p className="text-sm text-violet-300">
            📊 Showing demo data for presentation purposes
          </p>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// EXAMPLE 2: Campaign List with Demo Toggle
// ============================================================================

export function CampaignListExample() {
  const {
    enabled: demoMode,
    toggleDemoMode,
    resetDemoData
  } = useDemoMode();

  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCampaigns = async () => {
      try {
        setLoading(true);

        // Fetch from demo or real API based on mode
        const response = await fetchWithDemoMode('/api/campaigns', demoMode);
        const data = await response.json();

        setCampaigns(data.campaigns || []);
      } catch (error) {
        console.error('Error fetching campaigns:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCampaigns();
  }, [demoMode]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold">Campaigns</h1>
          {demoMode && <DemoModeBadge />}
        </div>

        {/* Demo controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={toggleDemoMode}
            className="px-4 py-2 rounded-lg bg-zinc-800 border border-zinc-700 hover:bg-zinc-700 transition-colors text-sm"
          >
            {demoMode ? 'Exit Demo Mode' : 'Enable Demo Mode'}
          </button>

          {demoMode && (
            <button
              onClick={resetDemoData}
              className="px-4 py-2 rounded-lg bg-zinc-800 border border-zinc-700 hover:bg-zinc-700 transition-colors text-sm"
            >
              Reset Data
            </button>
          )}
        </div>
      </div>

      {/* Campaign list */}
      <div className="space-y-4">
        {loading ? (
          <div>Loading campaigns...</div>
        ) : campaigns.length === 0 ? (
          <div>No campaigns found</div>
        ) : (
          campaigns.map((campaign: any) => (
            <CampaignCard key={campaign.id} campaign={campaign} />
          ))
        )}
      </div>
    </div>
  );
}

// ============================================================================
// EXAMPLE 3: AI Council Score with Demo Data
// ============================================================================

export function AICouncilScoreExample({ creativeId }: { creativeId: string }) {
  const { enabled: demoMode } = useDemoMode();
  const [score, setScore] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchScore = async () => {
      try {
        setLoading(true);

        let response;
        if (demoMode) {
          // Fetch demo AI Council score
          response = await fetch(
            `${import.meta.env.VITE_API_URL}/api/demo/ai-council?performance=high`
          );
        } else {
          // Fetch real AI Council score
          response = await fetch(
            `${import.meta.env.VITE_API_URL}/api/council/evaluate`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ creative_id: creativeId })
            }
          );
        }

        const data = await response.json();
        setScore(data);
      } catch (error) {
        console.error('Error fetching AI score:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchScore();
  }, [demoMode, creativeId]);

  if (loading) return <div>Evaluating...</div>;
  if (!score) return <div>No score available</div>;

  return (
    <div className="p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/30">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold">AI Council Score</h3>
        {demoMode && <DemoModeBadge />}
      </div>

      <div className="space-y-4">
        {/* Overall score */}
        <div>
          <div className="text-sm text-zinc-500 mb-2">Overall Score</div>
          <div className="text-4xl font-bold text-violet-400">
            {score.scores?.overall_score?.toFixed(1) || 'N/A'}
          </div>
        </div>

        {/* Individual scores */}
        <div className="grid grid-cols-3 gap-4">
          <AgentScore
            name="Director"
            score={score.scores?.director?.overall || 0}
          />
          <AgentScore
            name="Oracle"
            score={score.scores?.oracle?.confidence || 0}
          />
          <AgentScore
            name="Strategist"
            score={score.scores?.strategist?.overall || 0}
          />
        </div>

        {/* Recommendation */}
        <div className={`p-3 rounded-lg ${
          score.scores?.recommendation === 'approved'
            ? 'bg-emerald-500/10 border border-emerald-500/30'
            : 'bg-amber-500/10 border border-amber-500/30'
        }`}>
          <div className="text-sm font-medium">
            {score.scores?.recommendation === 'approved'
              ? '✅ Approved for Publishing'
              : '⚠️ Needs Optimization'}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// EXAMPLE 4: URL Parameter Detection
// ============================================================================

export function DemoModeUrlExample() {
  const { enabled, enableDemoMode, disableDemoMode } = useDemoMode();

  useEffect(() => {
    // Check URL parameter on mount
    const urlParams = new URLSearchParams(window.location.search);
    const demoParam = urlParams.get('demo');

    if (demoParam === 'true' && !enabled) {
      enableDemoMode();
      console.log('Demo mode activated via URL parameter');
    } else if (demoParam === 'false' && enabled) {
      disableDemoMode();
      console.log('Demo mode deactivated via URL parameter');
    }
  }, [enabled, enableDemoMode, disableDemoMode]);

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Demo Mode URL Control</h2>

      <div className="space-y-3 text-sm">
        <p className="text-zinc-400">
          Demo mode can be controlled via URL parameters:
        </p>

        <div className="p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50 font-mono">
          <div className="text-emerald-400">
            ?demo=true  → Enable demo mode
          </div>
          <div className="text-red-400">
            ?demo=false → Disable demo mode
          </div>
        </div>

        <p className="text-zinc-400">
          Current status: {enabled ? '✅ Demo mode active' : '⏸️ Demo mode inactive'}
        </p>

        {/* Demo links */}
        <div className="flex gap-2 mt-4">
          <a
            href="/?demo=true"
            className="px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-700 transition-colors text-sm"
          >
            Enable Demo Mode
          </a>
          <a
            href="/?demo=false"
            className="px-4 py-2 rounded-lg bg-zinc-700 hover:bg-zinc-600 transition-colors text-sm"
          >
            Disable Demo Mode
          </a>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// EXAMPLE 5: Presentation Link Component
// ============================================================================

export function PresentationLinkExample() {
  const { enableDemoMode } = useDemoMode();

  const handleStartPresentation = () => {
    // Enable demo mode
    enableDemoMode();

    // Navigate to presentation
    window.location.href = '/demo/presentation';
  };

  return (
    <div className="p-6">
      <div className="text-center space-y-4">
        <h2 className="text-2xl font-bold">Investor Presentation</h2>
        <p className="text-zinc-400 max-w-md mx-auto">
          Launch the full-screen investor presentation with impressive demo data
        </p>

        <button
          onClick={handleStartPresentation}
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 transition-all transform hover:scale-105 text-lg font-semibold"
        >
          Start Presentation →
        </button>

        <p className="text-xs text-zinc-500">
          Keyboard shortcuts: ← → to navigate | F for fullscreen | ESC to exit
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// Helper Components
// ============================================================================

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/30">
      <div className="text-sm text-zinc-500 mb-1">{label}</div>
      <div className="text-3xl font-bold">{value}</div>
    </div>
  );
}

function CampaignCard({ campaign }: { campaign: any }) {
  return (
    <div className="p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/30 hover:border-zinc-600/50 transition-colors">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold mb-1">{campaign.name}</h3>
          <p className="text-sm text-zinc-500">
            {campaign.platform} • {campaign.status}
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-violet-400">
            {campaign.roas?.toFixed(2)}x
          </div>
          <div className="text-sm text-zinc-500">ROAS</div>
        </div>
      </div>
    </div>
  );
}

function AgentScore({ name, score }: { name: string; score: number }) {
  return (
    <div className="text-center">
      <div className="text-xs text-zinc-500 mb-1">{name}</div>
      <div className="text-xl font-bold">{score.toFixed(0)}</div>
    </div>
  );
}

// ============================================================================
// USAGE GUIDE
// ============================================================================

/**
 * HOW TO USE DEMO MODE IN YOUR COMPONENTS:
 *
 * 1. Import the hook:
 *    import { useDemoMode } from '@/hooks/useDemoMode';
 *
 * 2. Use the hook in your component:
 *    const { enabled, toggleDemoMode } = useDemoMode();
 *
 * 3. Fetch data conditionally:
 *    const response = await fetchWithDemoMode('/api/campaigns', enabled);
 *
 * 4. Show demo indicator:
 *    {enabled && <DemoModeBadge />}
 *
 * 5. Add toggle button (optional):
 *    <button onClick={toggleDemoMode}>Toggle Demo</button>
 *
 * THAT'S IT! The hook handles all the complexity.
 */

export default {
  AnalyticsDashboardExample,
  CampaignListExample,
  AICouncilScoreExample,
  DemoModeUrlExample,
  PresentationLinkExample
};
