/**
 * Analytics Dashboard Example
 * Demonstrates usage of analytics hooks
 */

import React from 'react';
import { useAnalyticsDashboard } from '../hooks/useAnalytics';
import { LoadingSpinner, Skeleton } from '../components/ui/LoadingSpinner';

export const AnalyticsDashboardExample: React.FC = () => {
  const { overview, trends, roiPerformance, predictionAccuracy, isLoading, isError, refetch } =
    useAnalyticsDashboard('last_30d');

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <LoadingSpinner size="xl" text="Loading analytics..." />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-6">
            <h2 className="text-xl font-bold text-red-400 mb-2">Failed to Load Analytics</h2>
            <p className="text-gray-300 mb-4">
              There was an error loading your analytics data.
            </p>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Analytics Dashboard</h1>
            <p className="text-gray-400">Last 30 days performance overview</p>
          </div>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
          >
            Refresh Data
          </button>
        </div>

        {/* Overview Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Total Spend"
            value={`$${overview.data?.totalSpend.toLocaleString() || 0}`}
            change="+12%"
            trend="up"
          />
          <MetricCard
            title="Total Revenue"
            value={`$${overview.data?.totalRevenue.toLocaleString() || 0}`}
            change="+18%"
            trend="up"
          />
          <MetricCard
            title="ROAS"
            value={`${overview.data?.roas.toFixed(2) || 0}x`}
            change="+5%"
            trend="up"
          />
          <MetricCard
            title="Active Campaigns"
            value={overview.data?.activeCampaigns || 0}
            change="+2"
            trend="up"
          />
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <MetricCard
            title="Impressions"
            value={overview.data?.impressions.toLocaleString() || 0}
            subtitle="Total ad views"
          />
          <MetricCard
            title="Clicks"
            value={overview.data?.clicks.toLocaleString() || 0}
            subtitle={`${((overview.data?.ctr || 0) * 100).toFixed(2)}% CTR`}
          />
          <MetricCard
            title="Conversions"
            value={overview.data?.conversions.toLocaleString() || 0}
            subtitle={`$${(overview.data?.cpa || 0).toFixed(2)} CPA`}
          />
        </div>

        {/* Trends Chart Placeholder */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold text-white mb-4">Performance Trends</h2>
          {trends.isLoading ? (
            <Skeleton className="h-64" />
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              <div>
                <p className="mb-2">Trends chart would go here</p>
                <p className="text-sm">Data points: {trends.data?.length || 0}</p>
              </div>
            </div>
          )}
        </div>

        {/* ROI Performance */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold text-white mb-4">ROI Performance</h2>
          {roiPerformance.isLoading ? (
            <div className="grid grid-cols-3 gap-4">
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
            </div>
          ) : (
            <div className="text-gray-300">
              <p>ROI data available: {roiPerformance.data ? 'Yes' : 'No'}</p>
            </div>
          )}
        </div>

        {/* Prediction Accuracy */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold text-white mb-4">AI Prediction Accuracy</h2>
          {predictionAccuracy.isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-16" />
              <Skeleton className="h-16" />
              <Skeleton className="h-16" />
            </div>
          ) : predictionAccuracy.data && predictionAccuracy.data.length > 0 ? (
            <div className="space-y-4">
              {predictionAccuracy.data.map((metric: any, index: number) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg">
                  <div>
                    <p className="font-semibold text-white">{metric.metric}</p>
                    <p className="text-sm text-gray-400">
                      Predicted: {metric.predicted} | Actual: {metric.actual}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-green-400">{metric.accuracy}%</p>
                    <p className="text-xs text-gray-400">Accuracy</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400">No prediction data available</p>
          )}
        </div>
      </div>
    </div>
  );
};

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: string;
  trend?: 'up' | 'down';
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, subtitle, change, trend }) => {
  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-400">{title}</h3>
        {change && (
          <span
            className={`text-xs font-semibold ${
              trend === 'up' ? 'text-green-400' : 'text-red-400'
            }`}
          >
            {change}
          </span>
        )}
      </div>
      <p className="text-3xl font-bold text-white mb-1">{value}</p>
      {subtitle && <p className="text-sm text-gray-400">{subtitle}</p>}
    </div>
  );
};

export default AnalyticsDashboardExample;
