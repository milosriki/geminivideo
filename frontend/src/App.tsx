import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { DashboardLayout } from '@/layouts/DashboardLayout'
import { useToastStore } from '@/stores/toastStore'
import { CheckCircleIcon, ExclamationCircleIcon, ExclamationTriangleIcon, InformationCircleIcon, XMarkIcon } from '@heroicons/react/24/outline'

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
    <BrowserRouter>
      <div className="min-h-screen bg-zinc-950 text-white">
        <Routes>
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
