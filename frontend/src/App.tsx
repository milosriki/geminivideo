import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { DashboardLayout } from '@/layouts/DashboardLayout'
import { useToastStore } from '@/stores/toastStore'
import { CheckCircleIcon, ExclamationCircleIcon, ExclamationTriangleIcon, InformationCircleIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { ErrorBoundary } from '@/components/ErrorBoundary';

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
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'))

// Auth Pages (standalone, no dashboard layout)
const LoginPage = lazy(() => import('@/pages/auth/LoginPage'))
const RegisterPage = lazy(() => import('@/pages/auth/RegisterPage'))
const OTPPage = lazy(() => import('@/pages/auth/OTPPage'))

// Onboarding Pages (standalone, no dashboard layout)
const WelcomePage = lazy(() => import('@/pages/onboarding/WelcomePage'))
const ConnectMetaPage = lazy(() => import('@/pages/onboarding/ConnectMetaPage'))
const ConnectGooglePage = lazy(() => import('@/pages/onboarding/ConnectGooglePage'))
const ConfigurePage = lazy(() => import('@/pages/onboarding/ConfigurePage'))
const FirstCampaignPage = lazy(() => import('@/pages/onboarding/FirstCampaignPage'))
const CompletePage = lazy(() => import('@/pages/onboarding/CompletePage'))

// Marketing Pages (standalone with Radiant layout)
const BlogPage = lazy(() => import('@/pages/BlogPage'))
const CompanyPage = lazy(() => import('@/pages/CompanyPage'))
const PricingPage = lazy(() => import('@/pages/PricingPage'))

// Demo Pages (standalone for investor presentations)
const InvestorPresentationPage = lazy(() => import('@/pages/demo/InvestorPresentationPage'))

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
  const { toasts, removeToast } = useToastStore()

  const iconMap = {
    success: CheckCircleIcon,
    error: ExclamationCircleIcon,
    warning: ExclamationTriangleIcon,
    info: InformationCircleIcon,
  }

  const colorMap = {
    success: 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400',
    error: 'bg-red-500/10 border-red-500/50 text-red-400',
    warning: 'bg-amber-500/10 border-amber-500/50 text-amber-400',
    info: 'bg-blue-500/10 border-blue-500/50 text-blue-400',
  }

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map((toast) => {
        const Icon = iconMap[toast.variant]
        return (
          <div
            key={toast.id}
            className={`flex items-start gap-3 p-4 rounded-lg border backdrop-blur-sm animate-in slide-in-from-right-5 ${colorMap[toast.variant]}`}
          >
            <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="font-medium text-white">{toast.title}</p>
              {toast.message && (
                <p className="text-sm opacity-80 mt-0.5">{toast.message}</p>
              )}
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="flex-shrink-0 hover:opacity-70 transition-opacity"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          </div>
        )
      })}
    </div>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="min-h-screen bg-zinc-950 text-white font-sans antialiased selection:bg-violet-500/30">
          <Routes>
            {/* Auth Routes (standalone - no dashboard) */}
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

            {/* Onboarding Routes (standalone - no dashboard) */}
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

            {/* Marketing Pages (standalone with Radiant layout) */}
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

            {/* Demo Pages (standalone for investor presentations) */}
            <Route
              path="/demo/presentation"
              element={
                <Suspense fallback={<PageLoader />}>
                  <InvestorPresentationPage />
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

              {/* Help / Support */}
              <Route
                path="help"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <HelpPage />
                  </Suspense>
                }
              />

              {/* 404 Not Found - Catch all */}
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

          {/* Global Toast Notifications */}
          <ToastContainer />
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
