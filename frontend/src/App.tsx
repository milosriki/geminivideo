<<<<<<< HEAD
import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { DashboardLayout } from '@/layouts/DashboardLayout'
import { ErrorBoundary } from '@/components/ErrorBoundary'

// Lazy load all pages for code splitting
const HomePage = lazy(() => import('@/pages/HomePage'))
const CreateCampaignPage = lazy(() => import('@/pages/campaigns/CreateCampaignPage'))
const CampaignsPage = lazy(() => import('@/pages/campaigns/CampaignsPage'))
const ProjectsPage = lazy(() => import('@/pages/ProjectsPage'))
const AssetsPage = lazy(() => import('@/pages/AssetsPage'))
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage'))
const AdSpyPage = lazy(() => import('@/pages/AdSpyPage'))
const StudioPage = lazy(() => import('@/pages/studio/StudioPage'))
const SettingsPage = lazy(() => import('@/pages/SettingsPage'))
const HelpPage = lazy(() => import('@/pages/HelpPage'))
const ResourcesPage = lazy(() => import('@/pages/ResourcesPage'))
const LandingPage = lazy(() => import('@/pages/LandingPage'))

// Loading fallback component
function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          <div className="h-12 w-12 rounded-full border-4 border-zinc-800 border-t-violet-500 animate-spin" />
        </div>
        <p className="text-zinc-400 text-sm">Loading...</p>
      </div>
    </div>
  )
}

// Toast Provider Component
function ToastContainer() {
  // Will be implemented with useToastStore
  return null
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="min-h-screen bg-zinc-950 text-white">
          <Routes>
          {/* Marketing Routes */}
          <Route
            path="/marketing"
            element={
              <Suspense fallback={<PageLoader />}>
                <LandingPage />
              </Suspense>
            }
          />

          {/* Dashboard Routes */}
          <Route path="/" element={<DashboardLayout />}>
            <Route
              index
              element={
                <Suspense fallback={<PageLoader />}>
                  <HomePage />
                </Suspense>
              }
            />

            {/* Campaign Routes */}
            <Route
              path="create"
              element={
                <Suspense fallback={<PageLoader />}>
                  <CreateCampaignPage />
                </Suspense>
              }
            />
            <Route
              path="campaigns"
              element={
                <Suspense fallback={<PageLoader />}>
                  <CampaignsPage />
                </Suspense>
              }
            />
            <Route
              path="campaigns/:id"
              element={
                <Suspense fallback={<PageLoader />}>
                  <CampaignsPage />
                </Suspense>
              }
            />

            {/* Projects */}
            <Route
              path="projects"
              element={
                <Suspense fallback={<PageLoader />}>
                  <ProjectsPage />
                </Suspense>
              }
            />

            {/* Assets / Library */}
            <Route
              path="assets"
              element={
                <Suspense fallback={<PageLoader />}>
                  <AssetsPage />
                </Suspense>
              }
            />

            {/* Analytics */}
            <Route
              path="analytics"
              element={
                <Suspense fallback={<PageLoader />}>
                  <AnalyticsPage />
                </Suspense>
              }
            />

            {/* Ad Spy */}
            <Route
              path="spy"
              element={
                <Suspense fallback={<PageLoader />}>
                  <AdSpyPage />
                </Suspense>
              }
            />

            {/* Studio */}
            <Route
              path="studio"
              element={
                <Suspense fallback={<PageLoader />}>
                  <StudioPage />
                </Suspense>
              }
            />
            <Route
              path="studio/:projectId"
              element={
                <Suspense fallback={<PageLoader />}>
                  <StudioPage />
                </Suspense>
              }
            />

            {/* Settings */}
            <Route
              path="settings"
              element={
                <Suspense fallback={<PageLoader />}>
                  <SettingsPage />
                </Suspense>
              }
            />

            {/* Help */}
            <Route
              path="help"
              element={
                <Suspense fallback={<PageLoader />}>
                  <HelpPage />
                </Suspense>
              }
            />

            {/* Resources */}
            <Route
              path="resources"
              element={
                <Suspense fallback={<PageLoader />}>
                  <ResourcesPage />
                </Suspense>
              }
            />

            {/* Catch all - redirect to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>

        {/* Global Toast Notifications */}
        <ToastContainer />
      </div>
    </BrowserRouter>
  </ErrorBoundary>
  )
}

export default App
=======
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
>>>>>>> origin/claude/plan-video-editing-solution-01K1NVwMYwFHsZECx5H2RVTT
