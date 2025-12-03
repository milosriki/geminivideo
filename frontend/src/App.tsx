import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { DashboardLayout } from '@/layouts/DashboardLayout'
import { motion, AnimatePresence } from 'framer-motion'
import { useUIStore } from '@/stores/uiStore'
import { cn } from '@/lib/utils'

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
  const toasts = useUIStore((state) => state.toasts)
  const removeToast = useUIStore((state) => state.removeToast)

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            className={cn(
              'px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 min-w-[300px]',
              toast.type === 'success' && 'bg-green-900 text-green-100 border border-green-700',
              toast.type === 'error' && 'bg-red-900 text-red-100 border border-red-700',
              toast.type === 'warning' && 'bg-amber-900 text-amber-100 border border-amber-700',
              toast.type === 'info' && 'bg-blue-900 text-blue-100 border border-blue-700'
            )}
          >
            <span className="flex-1">{toast.message}</span>
            <button onClick={() => removeToast(toast.id)} className="opacity-70 hover:opacity-100">
              ✕
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}

function App() {
  return (
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
  )
}

export default App
