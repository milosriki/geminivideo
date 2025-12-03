import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './components/layout/MainLayout';
import {
  LoginPageWrapper,
  CampaignBuilderWrapper,
  AnalyticsDashboardWrapper,
  ProVideoEditorWrapper,
  AICreativeStudioWrapper,
  AdSpyDashboardWrapper
} from './components/wrappers';
import HomeDashboard from './components/dashboard/HomeDashboard';
import { ToastContainer, FadeIn } from './components/ui';
import { EmptyState } from './components/ui/EmptyState';

// Loading fallback
const PageLoader = () => (
  <div className="flex items-center justify-center h-screen bg-zinc-950 text-white">
    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
  </div>
);

// Placeholder pages for new routes
const AssetsPage = () => (
  <FadeIn>
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-6">Assets Library</h1>
      <EmptyState.Assets onAction={() => {/* TODO: Implement upload */}} />
    </div>
  </FadeIn>
);

const SettingsPage = () => (
  <FadeIn>
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-6">Settings</h1>
      <p className="text-zinc-400">Settings page coming soon...</p>
    </div>
  </FadeIn>
);

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPageWrapper />} />

          {/* Protected Routes (wrapped in MainLayout) */}
          <Route element={<MainLayout />}>
            <Route index element={<HomeDashboard />} />

            {/* Campaign Routes */}
            <Route path="campaigns" element={<CampaignBuilderWrapper />} />
            <Route path="campaigns/:id" element={<CampaignBuilderWrapper />} />

            {/* Analytics & Spy */}
            <Route path="analytics" element={<AnalyticsDashboardWrapper />} />
            <Route path="spy" element={<AdSpyDashboardWrapper />} />

            {/* Studio Tools */}
            <Route path="studio" element={<ProVideoEditorWrapper />} />
            <Route path="studio/ai" element={<AICreativeStudioWrapper />} />

            {/* Assets & Settings */}
            <Route path="assets" element={<AssetsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>

      {/* Global Toast Notifications */}
      <ToastContainer />
    </BrowserRouter>
  );
}

export default App;
