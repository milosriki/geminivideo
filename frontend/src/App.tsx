import { Suspense } from 'react';
import { BrowserRouter, useRoutes } from 'react-router-dom';
import { routes } from './routes';
import { LoadingScreen } from './components/LoadingScreen';
import { ErrorBoundary } from './components/ErrorBoundary';
import './App.css';

/**
 * App Routes Component
 * Renders the route configuration using useRoutes hook
 */
function AppRoutes() {
  const element = useRoutes(routes);
  return element;
}

/**
 * Main Application Component
 *
 * Features:
 * - BrowserRouter for client-side routing
 * - ErrorBoundary for graceful error handling
 * - Suspense with LoadingScreen for lazy-loaded components
 * - All routes defined in ./routes.tsx
 *
 * Route Structure:
 * /              - CreatorDashboard (Home)
 * /login         - LoginPage
 * /campaigns     - CampaignBuilder
 * /analytics     - AnalyticsDashboard
 * /studio        - ProVideoEditor
 * /studio/ai     - AICreativeStudio
 * /spy           - AdSpyDashboard
 * /library       - AssetsPanel
 * /analysis      - AnalysisPanel
 * /compliance    - CompliancePanel
 * /testing       - ABTestingDashboard
 * /workflow      - HumanWorkflowDashboard
 * /batch         - BatchProcessingPanel
 * /render        - RenderJobPanel
 * /audio         - AudioSuite
 * /image         - ImageSuite
 * /settings      - Settings
 * *              - NotFound (404)
 */
export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Suspense fallback={<LoadingScreen />}>
          <AppRoutes />
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
