import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAnalyticsStore } from '../stores/analyticsStore';
import { FadeIn, StaggerContainer } from './ui';
import {
  DateRangePicker,
  KPIGrid,
  CampaignTable,
  PerformanceCharts,
} from './analytics';

interface AnalyticsDashboardProps {
  dateRange?: { start: Date; end: Date };
  onDateRangeChange?: (range: { start: Date; end: Date }) => void;
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = () => {
  const { fetchAnalytics } = useAnalyticsStore();

  useEffect(() => {
    // Fetch analytics data on component mount
    fetchAnalytics();
  }, [fetchAnalytics]);

  return (
    <div className="min-h-screen bg-zinc-950 text-white p-6">
      <div className="max-w-[1600px] mx-auto space-y-8">
        {/* Page Header */}
        <FadeIn direction="down" className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Analytics Dashboard</h1>
          <p className="text-zinc-500">
            Track performance metrics and optimize your campaigns in real-time
          </p>
        </FadeIn>

        {/* Stagger the main content sections */}
        <StaggerContainer staggerDelay={0.1} initialDelay={0.1}>
          {/* Date Range Picker */}
          <div>
            <DateRangePicker />
          </div>

          {/* KPI Grid */}
          <div>
            <KPIGrid />
          </div>

          {/* Performance Charts */}
          <div>
            <PerformanceCharts />
          </div>

          {/* Campaign Table */}
          <div>
            <CampaignTable />
          </div>
        </StaggerContainer>

        {/* AI Insights Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.5 }}
          className="bg-gradient-to-r from-indigo-900/40 to-purple-900/40 border border-indigo-700/50 rounded-xl p-6 shadow-lg"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-indigo-800/50 rounded-lg">
              <svg
                className="w-6 h-6 text-indigo-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">AI-Powered Insights</h2>
              <p className="text-xs text-indigo-300">
                Recommendations based on your campaign performance
              </p>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <motion.div
              whileHover={{ scale: 1.02 }}
              className="bg-black/20 backdrop-blur-sm rounded-xl p-5 border border-indigo-800/30"
            >
              <div className="flex items-center gap-2 mb-3">
                <svg
                  className="w-5 h-5 text-green-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <h3 className="font-semibold text-green-400">Top Performer</h3>
              </div>
              <p className="text-sm text-zinc-300 leading-relaxed">
                "Black Friday Promotion" achieved 4.76x ROAS with strong conversion rates.
                Consider allocating 25% more budget to scale performance.
              </p>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.02 }}
              className="bg-black/20 backdrop-blur-sm rounded-xl p-5 border border-yellow-800/30"
            >
              <div className="flex items-center gap-2 mb-3">
                <svg
                  className="w-5 h-5 text-yellow-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                <h3 className="font-semibold text-yellow-400">Needs Attention</h3>
              </div>
              <p className="text-sm text-zinc-300 leading-relaxed">
                "Brand Awareness Q4" shows declining ROAS at 2.57x. Test new creative
                variations and consider audience refinement.
              </p>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.02 }}
              className="bg-black/20 backdrop-blur-sm rounded-xl p-5 border border-blue-800/30"
            >
              <div className="flex items-center gap-2 mb-3">
                <svg
                  className="w-5 h-5 text-blue-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                <h3 className="font-semibold text-blue-400">Opportunity</h3>
              </div>
              <p className="text-sm text-zinc-300 leading-relaxed">
                Retargeting campaigns show 5.13x ROAS - 33% above average. Expand
                retargeting audiences to capture more high-intent users.
              </p>
            </motion.div>
          </div>
        </motion.div>

        {/* Footer Spacer */}
        <div className="h-8"></div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
