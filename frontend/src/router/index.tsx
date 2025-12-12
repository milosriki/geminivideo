/**
 * Router Configuration - GeminiVideo
 * Centralized routing with lazy-loaded components
 * Exposes all 32 previously hidden components
 */

import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import { DashboardLayout } from '@/layouts/DashboardLayout'

// ============================================================================
// LOADING FALLBACK
// ============================================================================

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

// ============================================================================
// LAZY LOADED PAGES - DASHBOARD
// ============================================================================

const HomePage = lazy(() => import('@/pages/HomePage'))
const ProjectsPage = lazy(() => import('@/pages/ProjectsPage'))
const SettingsPage = lazy(() => import('@/pages/SettingsPage'))
const HelpPage = lazy(() => import('@/pages/HelpPage'))
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'))

// Creator Dashboard (Hidden Component #1)
const CreatorDashboard = lazy(() =>
  import('@/components/CreatorDashboard').then(m => ({ default: m.CreatorDashboard }))
)

// ============================================================================
// LAZY LOADED PAGES - CAMPAIGNS
// ============================================================================

const CreateCampaignPage = lazy(() => import('@/pages/campaigns/CreateCampaignPage'))
const CampaignsPage = lazy(() => import('@/pages/campaigns/CampaignsPage'))

// Campaign Builder (Hidden Component #2)
const CampaignBuilder = lazy(() => import('@/components/CampaignBuilder'))

// ============================================================================
// LAZY LOADED PAGES - ANALYTICS & REPORTING
// ============================================================================

const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage'))

// Hidden Analytics Components (#3-8)
const AnalyticsDashboard = lazy(() => import('@/components/AnalyticsDashboard'))
const PerformanceDashboard = lazy(() => import('@/components/PerformanceDashboard'))
const ReliabilityChart = lazy(() => import('@/components/ReliabilityChart'))
const DiversificationDashboard = lazy(() => import('@/components/DiversificationDashboard'))
const ROASDashboard = lazy(() => import('@/pages/ROASDashboard'))
const ReportsPage = lazy(() => import('@/pages/ReportsPage'))

// ============================================================================
// LAZY LOADED PAGES - STUDIO & CREATIVE
// ============================================================================

const StudioPage = lazy(() => import('@/pages/studio/StudioPage'))

// Hidden Studio Components (#9-13)
const ProVideoEditor = lazy(() => import('@/components/pro/ProVideoEditor'))
const StoryboardStudio = lazy(() => import('@/components/StoryboardStudio'))
const VideoStudio = lazy(() => import('@/components/VideoStudio'))
const VideoGenerator = lazy(() => import('@/components/VideoGenerator'))
const AICreativeStudio = lazy(() => import('@/components/AICreativeStudio'))

// Pro Editor Sub-components (#14-16)
const AudioMixerPanel = lazy(() => import('@/components/pro/AudioMixerPanel'))
const ColorGradingPanel = lazy(() => import('@/components/pro/ColorGradingPanel'))
const ColorGradingPanelDemo = lazy(() => import('@/components/pro/ColorGradingPanelDemo'))

// ============================================================================
// LAZY LOADED PAGES - ASSETS
// ============================================================================

const AssetsPage = lazy(() => import('@/pages/AssetsPage'))

// Hidden Asset Components (#17-19)
const AssetsPanel = lazy(() => import('@/components/AssetsPanel'))
const RankedClipsPanel = lazy(() => import('@/components/RankedClipsPanel'))
const SemanticSearchPanel = lazy(() => import('@/components/SemanticSearchPanel'))

// ============================================================================
// LAZY LOADED PAGES - TOOLS
// ============================================================================

const AdSpyPage = lazy(() => import('@/pages/AdSpyPage'))

// Hidden Tool Components (#20-27)
const AdSpyDashboard = lazy(() => import('@/components/AdSpyDashboard'))
const AnalysisPanel = lazy(() => import('@/components/AnalysisPanel'))
const CompliancePanel = lazy(() => import('@/components/CompliancePanel'))
const AudioSuite = lazy(() => import('@/components/AudioSuite'))
const AudioSuitePanel = lazy(() => import('@/components/AudioSuitePanel'))
const ImageSuite = lazy(() => import('@/components/ImageSuite'))
const Assistant = lazy(() => import('@/components/Assistant'))
const ResourcesPage = lazy(() => import('@/pages/ResourcesPage'))

// ============================================================================
// LAZY LOADED PAGES - WORKFLOW & TESTING
// ============================================================================

// Hidden Workflow Components (#28-31)
const ABTestingDashboard = lazy(() => import('@/components/ABTestingDashboard'))
const HumanWorkflowDashboard = lazy(() => import('@/components/HumanWorkflowDashboard'))
const BatchProcessingPanel = lazy(() => import('@/components/BatchProcessingPanel'))
const RenderJobPanel = lazy(() => import('@/components/RenderJobPanel'))

// ============================================================================
// LAZY LOADED PAGES - AUTH (Standalone)
// ============================================================================

const LoginPage = lazy(() => import('@/pages/auth/LoginPage'))
const RegisterPage = lazy(() => import('@/pages/auth/RegisterPage'))
const OTPPage = lazy(() => import('@/pages/auth/OTPPage'))

// ============================================================================
// LAZY LOADED PAGES - ONBOARDING (Standalone)
// ============================================================================

const WelcomePage = lazy(() => import('@/pages/onboarding/WelcomePage'))
const ConnectMetaPage = lazy(() => import('@/pages/onboarding/ConnectMetaPage'))
const ConnectGooglePage = lazy(() => import('@/pages/onboarding/ConnectGooglePage'))
const ConfigurePage = lazy(() => import('@/pages/onboarding/ConfigurePage'))
const FirstCampaignPage = lazy(() => import('@/pages/onboarding/FirstCampaignPage'))
const CompletePage = lazy(() => import('@/pages/onboarding/CompletePage'))

// ============================================================================
// LAZY LOADED PAGES - MARKETING (Standalone)
// ============================================================================

// Hidden Component #32
const LandingPage = lazy(() => import('@/pages/LandingPage'))
const BlogPage = lazy(() => import('@/pages/BlogPage'))
const CompanyPage = lazy(() => import('@/pages/CompanyPage'))
const PricingPage = lazy(() => import('@/pages/PricingPage'))

// ============================================================================
// LAZY LOADED PAGES - DEMO (Standalone)
// ============================================================================

const InvestorPresentationPage = lazy(() => import('@/pages/demo/InvestorPresentationPage'))

// ============================================================================
// WRAPPER COMPONENTS FOR PROPS-REQUIRED COMPONENTS
// ============================================================================

/**
 * CampaignBuilder requires onComplete callback
 */
function CampaignBuilderPage() {
  return (
    <Suspense fallback={<PageLoader />}>
      <CampaignBuilder
        onComplete={(campaign) => {
          console.log('Campaign created:', campaign)
          window.location.href = '/campaigns'
        }}
      />
    </Suspense>
  )
}

/**
 * AICreativeStudio requires onCreativeGenerated callback
 */
function AICreativeStudioPage() {
  return (
    <Suspense fallback={<PageLoader />}>
      <AICreativeStudio
        onCreativeGenerated={(creative) => {
          console.log('Creative generated:', creative)
        }}
      />
    </Suspense>
  )
}

/**
 * VideoStudio requires onClose callback
 */
function VideoStudioPage() {
  return (
    <Suspense fallback={<PageLoader />}>
      <VideoStudio
        onClose={() => {
          window.location.href = '/studio'
        }}
      />
    </Suspense>
  )
}

// ============================================================================
// MAIN ROUTER COMPONENT
// ============================================================================

export function AppRouter() {
  return (
    <Routes>
      {/* ====================================================================
          AUTH ROUTES (Standalone - No Dashboard Layout)
          ==================================================================== */}
      <Route
        path="/login"
        element={
          <Suspense fallback={<PageLoader />}>
            <LoginPage />
          </Suspense>
        }
      />
      <Route
        path="/register"
        element={
          <Suspense fallback={<PageLoader />}>
            <RegisterPage />
          </Suspense>
        }
      />
      <Route
        path="/verify"
        element={
          <Suspense fallback={<PageLoader />}>
            <OTPPage />
          </Suspense>
        }
      />

      {/* ====================================================================
          ONBOARDING ROUTES (Standalone - No Dashboard Layout)
          ==================================================================== */}
      <Route
        path="/onboarding/welcome"
        element={
          <Suspense fallback={<PageLoader />}>
            <WelcomePage />
          </Suspense>
        }
      />
      <Route
        path="/onboarding/connect-meta"
        element={
          <Suspense fallback={<PageLoader />}>
            <ConnectMetaPage />
          </Suspense>
        }
      />
      <Route
        path="/onboarding/connect-google"
        element={
          <Suspense fallback={<PageLoader />}>
            <ConnectGooglePage />
          </Suspense>
        }
      />
      <Route
        path="/onboarding/configure"
        element={
          <Suspense fallback={<PageLoader />}>
            <ConfigurePage />
          </Suspense>
        }
      />
      <Route
        path="/onboarding/first-campaign"
        element={
          <Suspense fallback={<PageLoader />}>
            <FirstCampaignPage />
          </Suspense>
        }
      />
      <Route
        path="/onboarding/complete"
        element={
          <Suspense fallback={<PageLoader />}>
            <CompletePage />
          </Suspense>
        }
      />

      {/* ====================================================================
          MARKETING ROUTES (Standalone)
          ==================================================================== */}
      <Route
        path="/landing"
        element={
          <Suspense fallback={<PageLoader />}>
            <LandingPage />
          </Suspense>
        }
      />
      <Route
        path="/blog"
        element={
          <Suspense fallback={<PageLoader />}>
            <BlogPage />
          </Suspense>
        }
      />
      <Route
        path="/company"
        element={
          <Suspense fallback={<PageLoader />}>
            <CompanyPage />
          </Suspense>
        }
      />
      <Route
        path="/pricing"
        element={
          <Suspense fallback={<PageLoader />}>
            <PricingPage />
          </Suspense>
        }
      />

      {/* ====================================================================
          DEMO ROUTES (Standalone)
          ==================================================================== */}
      <Route
        path="/demo/presentation"
        element={
          <Suspense fallback={<PageLoader />}>
            <InvestorPresentationPage />
          </Suspense>
        }
      />

      {/* ====================================================================
          DASHBOARD ROUTES (With DashboardLayout)
          ==================================================================== */}
      <Route path="/" element={<DashboardLayout />}>
        {/* Home / Dashboard */}
        <Route
          index
          element={
            <Suspense fallback={<PageLoader />}>
              <HomePage />
            </Suspense>
          }
        />
        <Route
          path="dashboard/creator"
          element={
            <Suspense fallback={<PageLoader />}>
              <CreatorDashboard />
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
        <Route path="campaigns/builder" element={<CampaignBuilderPage />} />
        <Route path="campaigns/new" element={<CampaignBuilderPage />} />

        {/* Analytics & Reporting Routes */}
        <Route
          path="analytics"
          element={
            <Suspense fallback={<PageLoader />}>
              <AnalyticsPage />
            </Suspense>
          }
        />
        <Route
          path="analytics/dashboard"
          element={
            <Suspense fallback={<PageLoader />}>
              <AnalyticsDashboard />
            </Suspense>
          }
        />
        <Route
          path="analytics/performance"
          element={
            <Suspense fallback={<PageLoader />}>
              <PerformanceDashboard />
            </Suspense>
          }
        />
        <Route
          path="analytics/reliability"
          element={
            <Suspense fallback={<PageLoader />}>
              <ReliabilityChart />
            </Suspense>
          }
        />
        <Route
          path="analytics/diversification"
          element={
            <Suspense fallback={<PageLoader />}>
              <DiversificationDashboard />
            </Suspense>
          }
        />
        <Route
          path="analytics/roas"
          element={
            <Suspense fallback={<PageLoader />}>
              <ROASDashboard />
            </Suspense>
          }
        />
        <Route
          path="reports"
          element={
            <Suspense fallback={<PageLoader />}>
              <ReportsPage />
            </Suspense>
          }
        />

        {/* Studio & Creative Routes */}
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
        <Route
          path="studio/pro"
          element={
            <Suspense fallback={<PageLoader />}>
              <ProVideoEditor />
            </Suspense>
          }
        />
        <Route
          path="studio/pro/:projectId"
          element={
            <Suspense fallback={<PageLoader />}>
              <ProVideoEditor />
            </Suspense>
          }
        />
        <Route
          path="studio/storyboard"
          element={
            <Suspense fallback={<PageLoader />}>
              <StoryboardStudio />
            </Suspense>
          }
        />
        <Route path="studio/video" element={<VideoStudioPage />} />
        <Route path="studio/ai" element={<AICreativeStudioPage />} />
        <Route
          path="studio/generate"
          element={
            <Suspense fallback={<PageLoader />}>
              <VideoGenerator />
            </Suspense>
          }
        />
        <Route
          path="studio/audio-mixer"
          element={
            <Suspense fallback={<PageLoader />}>
              <AudioMixerPanel />
            </Suspense>
          }
        />
        <Route
          path="studio/color-grading"
          element={
            <Suspense fallback={<PageLoader />}>
              <ColorGradingPanel />
            </Suspense>
          }
        />
        <Route
          path="studio/color-grading-demo"
          element={
            <Suspense fallback={<PageLoader />}>
              <ColorGradingPanelDemo />
            </Suspense>
          }
        />

        {/* Assets & Library Routes */}
        <Route
          path="assets"
          element={
            <Suspense fallback={<PageLoader />}>
              <AssetsPage />
            </Suspense>
          }
        />
        <Route
          path="library"
          element={
            <Suspense fallback={<PageLoader />}>
              <AssetsPanel />
            </Suspense>
          }
        />
        <Route
          path="library/assets"
          element={
            <Suspense fallback={<PageLoader />}>
              <AssetsPanel />
            </Suspense>
          }
        />
        <Route
          path="library/clips"
          element={
            <Suspense fallback={<PageLoader />}>
              <RankedClipsPanel />
            </Suspense>
          }
        />
        <Route
          path="library/search"
          element={
            <Suspense fallback={<PageLoader />}>
              <SemanticSearchPanel />
            </Suspense>
          }
        />

        {/* Tools Routes */}
        <Route
          path="spy"
          element={
            <Suspense fallback={<PageLoader />}>
              <AdSpyPage />
            </Suspense>
          }
        />
        <Route
          path="spy/dashboard"
          element={
            <Suspense fallback={<PageLoader />}>
              <AdSpyDashboard />
            </Suspense>
          }
        />
        <Route
          path="analysis"
          element={
            <Suspense fallback={<PageLoader />}>
              <AnalysisPanel />
            </Suspense>
          }
        />
        <Route
          path="compliance"
          element={
            <Suspense fallback={<PageLoader />}>
              <CompliancePanel />
            </Suspense>
          }
        />
        <Route
          path="audio"
          element={
            <Suspense fallback={<PageLoader />}>
              <AudioSuite />
            </Suspense>
          }
        />
        <Route
          path="audio/suite"
          element={
            <Suspense fallback={<PageLoader />}>
              <AudioSuitePanel />
            </Suspense>
          }
        />
        <Route
          path="image"
          element={
            <Suspense fallback={<PageLoader />}>
              <ImageSuite />
            </Suspense>
          }
        />
        <Route
          path="assistant"
          element={
            <Suspense fallback={<PageLoader />}>
              <Assistant />
            </Suspense>
          }
        />
        <Route
          path="resources"
          element={
            <Suspense fallback={<PageLoader />}>
              <ResourcesPage />
            </Suspense>
          }
        />

        {/* Workflow & Testing Routes */}
        <Route
          path="testing"
          element={
            <Suspense fallback={<PageLoader />}>
              <ABTestingDashboard />
            </Suspense>
          }
        />
        <Route
          path="workflow"
          element={
            <Suspense fallback={<PageLoader />}>
              <HumanWorkflowDashboard />
            </Suspense>
          }
        />
        <Route
          path="workflow/approvals"
          element={
            <Suspense fallback={<PageLoader />}>
              <HumanWorkflowDashboard />
            </Suspense>
          }
        />
        <Route
          path="batch"
          element={
            <Suspense fallback={<PageLoader />}>
              <BatchProcessingPanel />
            </Suspense>
          }
        />
        <Route
          path="render"
          element={
            <Suspense fallback={<PageLoader />}>
              <RenderJobPanel />
            </Suspense>
          }
        />

        {/* Other Routes */}
        <Route
          path="projects"
          element={
            <Suspense fallback={<PageLoader />}>
              <ProjectsPage />
            </Suspense>
          }
        />
        <Route
          path="settings"
          element={
            <Suspense fallback={<PageLoader />}>
              <SettingsPage />
            </Suspense>
          }
        />
        <Route
          path="help"
          element={
            <Suspense fallback={<PageLoader />}>
              <HelpPage />
            </Suspense>
          }
        />

        {/* 404 Not Found - Catch all within dashboard */}
        <Route
          path="*"
          element={
            <Suspense fallback={<PageLoader />}>
              <NotFoundPage />
            </Suspense>
          }
        />
      </Route>
    </Routes>
  )
}

export default AppRouter
