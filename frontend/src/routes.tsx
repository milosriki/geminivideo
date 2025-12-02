import { lazy } from 'react';
import type { RouteObject } from 'react-router-dom';

// ============================================================================
// LAZY LOADED COMPONENTS
// All components are lazy-loaded for optimal code splitting
// ============================================================================

// Layout
const MainLayout = lazy(() => import('./components/MainLayout'));

// Core Pages
const CreatorDashboard = lazy(() =>
  import('./components/CreatorDashboard').then(m => ({ default: m.CreatorDashboard }))
);
const LoginPage = lazy(() => import('./components/LoginPage'));
const NotFound = lazy(() => import('./components/NotFound'));

// Campaign Management
const CampaignBuilder = lazy(() => import('./components/CampaignBuilder'));

// Analytics & Reporting
const AnalyticsDashboard = lazy(() => import('./components/AnalyticsDashboard'));
const PerformanceDashboard = lazy(() => import('./components/PerformanceDashboard'));
const ReliabilityChart = lazy(() => import('./components/ReliabilityChart'));
const DiversificationDashboard = lazy(() => import('./components/DiversificationDashboard'));

// Video Editing Suite
const ProVideoEditor = lazy(() => import('./components/pro/ProVideoEditor'));
const StoryboardStudio = lazy(() => import('./components/StoryboardStudio'));

// Pro Editor Sub-components
const AudioMixerPanel = lazy(() => import('./components/pro/AudioMixerPanel'));
const ColorGradingPanel = lazy(() => import('./components/pro/ColorGradingPanel'));
const ColorGradingPanelDemo = lazy(() => import('./components/pro/ColorGradingPanelDemo'));

// Competitor Intelligence
const AdSpyDashboard = lazy(() => import('./components/AdSpyDashboard'));

// Asset Management
const AssetsPanel = lazy(() => import('./components/AssetsPanel'));
const RankedClipsPanel = lazy(() => import('./components/RankedClipsPanel'));
const SemanticSearchPanel = lazy(() => import('./components/SemanticSearchPanel'));

// Analysis & Compliance
const AnalysisPanel = lazy(() => import('./components/AnalysisPanel'));
const CompliancePanel = lazy(() => import('./components/CompliancePanel'));

// Audio Tools
const AudioSuite = lazy(() => import('./components/AudioSuite'));
const AudioSuitePanel = lazy(() => import('./components/AudioSuitePanel'));

// Image Tools
const ImageSuite = lazy(() => import('./components/ImageSuite'));

// Workflow & Testing
const ABTestingDashboard = lazy(() => import('./components/ABTestingDashboard'));
const HumanWorkflowDashboard = lazy(() => import('./components/HumanWorkflowDashboard'));
const BatchProcessingPanel = lazy(() => import('./components/BatchProcessingPanel'));

// Render
const RenderJobPanel = lazy(() => import('./components/RenderJobPanel'));

// Assistant
const Assistant = lazy(() => import('./components/Assistant'));

// ============================================================================
// WRAPPER COMPONENTS FOR PROPS-REQUIRED COMPONENTS
// These provide default props for standalone route rendering
// ============================================================================

/**
 * CampaignBuilder Wrapper
 * Provides default onComplete callback for route-based rendering
 */
function CampaignBuilderPage() {
  return (
    <CampaignBuilder
      onComplete={(campaign) => {
        console.log('Campaign created:', campaign);
        // In production, navigate to campaign details or campaigns list
        window.location.href = '/analytics';
      }}
    />
  );
}

/**
 * AICreativeStudio Wrapper
 * Provides default callback for standalone rendering
 */
const AICreativeStudio = lazy(() => import('./components/AICreativeStudio'));
function AICreativeStudioPage() {
  return (
    <AICreativeStudio
      onCreativeGenerated={(creative) => {
        console.log('Creative generated:', creative);
      }}
    />
  );
}

/**
 * VideoStudio Wrapper
 */
const VideoStudio = lazy(() => import('./components/VideoStudio'));
function VideoStudioPage() {
  return (
    <VideoStudio
      onClose={() => {
        window.location.href = '/studio';
      }}
    />
  );
}

/**
 * VideoGenerator - No wrapper needed (no required props)
 */
const VideoGenerator = lazy(() => import('./components/VideoGenerator'));

// ============================================================================
// ROUTE CONFIGURATION
// Organized by feature area with nested routes
// ============================================================================

export const routes: RouteObject[] = [
  // Public Routes (no auth required)
  {
    path: '/login',
    element: <LoginPage />,
  },

  // Protected Routes (wrapped in MainLayout)
  {
    path: '/',
    element: <MainLayout />,
    children: [
      // Dashboard (Home)
      {
        index: true,
        element: <CreatorDashboard />,
      },

      // Campaign Management
      {
        path: 'campaigns',
        children: [
          { index: true, element: <CampaignBuilderPage /> },
          { path: 'new', element: <CampaignBuilderPage /> },
          { path: ':id', element: <CampaignBuilderPage /> },
          { path: ':id/edit', element: <CampaignBuilderPage /> },
        ],
      },

      // Analytics & Reporting
      {
        path: 'analytics',
        children: [
          { index: true, element: <AnalyticsDashboard /> },
          { path: 'performance', element: <PerformanceDashboard /> },
          { path: 'reliability', element: <ReliabilityChart /> },
          { path: 'diversification', element: <DiversificationDashboard /> },
        ],
      },

      // Video Studio (Pro Editor)
      {
        path: 'studio',
        children: [
          { index: true, element: <ProVideoEditor /> },
          { path: 'pro', element: <ProVideoEditor /> },
          { path: 'pro/:projectId', element: <ProVideoEditor /> },
          { path: 'storyboard', element: <StoryboardStudio /> },
          { path: 'video', element: <VideoStudioPage /> },
          { path: 'ai', element: <AICreativeStudioPage /> },
          { path: 'generate', element: <VideoGenerator /> },
          // Pro editor sub-tools (accessible as standalone for demos)
          { path: 'audio-mixer', element: <AudioMixerPanel /> },
          { path: 'color-grading', element: <ColorGradingPanel /> },
          { path: 'color-grading-demo', element: <ColorGradingPanelDemo /> },
        ],
      },

      // Ad Spy & Competitor Intelligence
      {
        path: 'spy',
        element: <AdSpyDashboard />,
      },

      // Asset Library
      {
        path: 'library',
        children: [
          { index: true, element: <AssetsPanel /> },
          { path: 'assets', element: <AssetsPanel /> },
          { path: 'clips', element: <RankedClipsPanel /> },
          { path: 'search', element: <SemanticSearchPanel /> },
        ],
      },

      // Analysis & Compliance
      {
        path: 'analysis',
        element: <AnalysisPanel />,
      },
      {
        path: 'compliance',
        element: <CompliancePanel />,
      },

      // Audio Tools
      {
        path: 'audio',
        children: [
          { index: true, element: <AudioSuite /> },
          { path: 'suite', element: <AudioSuitePanel /> },
        ],
      },

      // Image Tools
      {
        path: 'image',
        element: <ImageSuite />,
      },

      // Workflow & Testing
      {
        path: 'testing',
        element: <ABTestingDashboard />,
      },
      {
        path: 'workflow',
        children: [
          { index: true, element: <HumanWorkflowDashboard /> },
          { path: 'approvals', element: <HumanWorkflowDashboard /> },
        ],
      },
      {
        path: 'batch',
        element: <BatchProcessingPanel />,
      },

      // Render Jobs
      {
        path: 'render',
        element: <RenderJobPanel />,
      },

      // AI Assistant
      {
        path: 'assistant',
        element: <Assistant />,
      },

      // Settings (placeholder - can be expanded)
      {
        path: 'settings',
        element: (
          <div className="text-white p-6">
            <h1 className="text-2xl font-bold mb-4">Settings</h1>
            <p className="text-zinc-400">Settings page coming soon...</p>
          </div>
        ),
      },
    ],
  },

  // Catch-all 404
  {
    path: '*',
    element: <NotFound />,
  },
];

export default routes;
