import React, { Suspense } from 'react';
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

// Loading fallback
const PageLoader = () => (
  <div className="flex items-center justify-center h-screen bg-gray-900 text-white">
    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
  </div>
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
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
