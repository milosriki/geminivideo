import React, { useState } from 'react';
import { BentoCard } from '@/components/radiant/bento-card';
import { AnimatedNumber } from '@/components/radiant/animated-number';
import { PerformanceChart } from './PerformanceChart';
import { RecentActivity } from './RecentActivity';
import { QuickActions } from './QuickActions';
import { AIInsights } from './AIInsights';

// Mock data for the dashboard
const mockMetrics = {
  activeCampaigns: 12,
  videosGenerated: 1847,
  roasAverage: 4.2,
  aiCredits: 8500,
  aiCreditsTotal: 10000,
};

const mockChanges = {
  activeCampaigns: 23,
  videosGenerated: 156,
  roasAverage: 0.3,
  aiCreditsPercentage: 85,
};

interface HomeDashboardProps {
  userName?: string;
}

export const HomeDashboard: React.FC<HomeDashboardProps> = ({
  userName = 'Creator',
}) => {
  const [showQuickActionsDropdown, setShowQuickActionsDropdown] = useState(false);

  return (
    <div className="min-h-screen bg-zinc-950 p-4 lg:p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-white">
            Welcome back, {userName}! <span className="inline-block animate-wave">👋</span>
          </h1>
          <p className="text-zinc-400 mt-1">
            Here's what's happening with your campaigns today.
          </p>
        </div>

        {/* Quick Actions Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowQuickActionsDropdown(!showQuickActionsDropdown)}
            className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium transition-colors shadow-lg shadow-indigo-500/25"
          >
            Quick Actions
            <svg
              className={`w-4 h-4 transition-transform ${showQuickActionsDropdown ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showQuickActionsDropdown && (
            <div className="absolute right-0 mt-2 w-56 bg-zinc-800 border border-zinc-700 rounded-lg shadow-xl z-50">
              <div className="py-1">
                {[
                  { label: 'New Campaign', icon: '➕' },
                  { label: 'Generate Video', icon: '🎬' },
                  { label: 'Analyze Competitor', icon: '🔍' },
                  { label: 'View Analytics', icon: '📊' },
                ].map((item, idx) => (
                  <button
                    key={idx}
                    className="w-full px-4 py-2.5 text-left text-white hover:bg-zinc-700 transition-colors flex items-center gap-3"
                    onClick={() => setShowQuickActionsDropdown(false)}
                  >
                    <span>{item.icon}</span>
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <BentoCard
          dark
          eyebrow="Active Campaigns"
          title={<AnimatedNumber value={mockMetrics.activeCampaigns} />}
          description={`+${mockChanges.activeCampaigns}% from last month`}
          graphic={
            <div className="absolute inset-0 flex items-center justify-center opacity-20">
              <svg className="w-32 h-32 text-violet-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          }
          fade={['bottom']}
        />
        <BentoCard
          dark
          eyebrow="Videos Generated"
          title={<AnimatedNumber value={mockMetrics.videosGenerated} />}
          description={`+${mockChanges.videosGenerated} this week`}
          graphic={
            <div className="absolute inset-0 flex items-center justify-center opacity-20">
              <svg className="w-32 h-32 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="m22 8-6 4 6 4V8Z" />
                <rect x="2" y="6" width="14" height="12" rx="2" strokeWidth={1} />
              </svg>
            </div>
          }
          fade={['bottom']}
        />
        <BentoCard
          dark
          eyebrow="ROAS Average"
          title={<><AnimatedNumber value={mockMetrics.roasAverage} decimals={1} />x</>}
          description={`+${mockChanges.roasAverage} improvement`}
          graphic={
            <div className="absolute inset-0 flex items-center justify-center opacity-20">
              <svg className="w-32 h-32 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
          }
          fade={['bottom']}
        />
        <BentoCard
          dark
          eyebrow="AI Credits"
          title={<AnimatedNumber value={mockMetrics.aiCredits} />}
          description={`${mockChanges.aiCreditsPercentage}% remaining`}
          graphic={
            <div className="absolute inset-0 flex items-center justify-center opacity-20">
              <svg className="w-32 h-32 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
              </svg>
            </div>
          }
          fade={['bottom']}
        />
      </div>

      {/* Charts and Activity Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <PerformanceChart />
        <RecentActivity />
      </div>

      {/* Quick Actions and AI Insights Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <QuickActions />
        <AIInsights />
      </div>

      {/* Credits Progress Bar */}
      <div className="mt-8 bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-lg shadow-black/20">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span className="text-white font-medium">AI Credits Usage</span>
          </div>
          <span className="text-zinc-400 text-sm">
            {mockMetrics.aiCredits.toLocaleString()} / {mockMetrics.aiCreditsTotal.toLocaleString()} credits
          </span>
        </div>
        <div className="h-3 bg-zinc-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-1000"
            style={{ width: `${(mockMetrics.aiCredits / mockMetrics.aiCreditsTotal) * 100}%` }}
          />
        </div>
        <p className="text-zinc-500 text-sm mt-2">
          {mockChanges.aiCreditsPercentage}% of your monthly credits remaining. Resets in 12 days.
        </p>
      </div>

      {/* Animate wave emoji */}
      <style>{`
        @keyframes wave {
          0%, 100% { transform: rotate(0deg); }
          25% { transform: rotate(20deg); }
          75% { transform: rotate(-10deg); }
        }
        .animate-wave {
          animation: wave 1.5s ease-in-out infinite;
          display: inline-block;
          transform-origin: 70% 70%;
        }
      `}</style>
    </div>
  );
};

export default HomeDashboard;
