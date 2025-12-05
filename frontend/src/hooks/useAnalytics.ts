/**
 * Analytics Hooks
 * React Query hooks for analytics and insights
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import apiClient, {
  AnalyticsOverview,
  CampaignAnalytics,
  TrendData,
  PredictionAccuracy,
} from '../lib/api';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const analyticsKeys = {
  all: ['analytics'] as const,
  overview: (timeRange?: string) => [...analyticsKeys.all, 'overview', timeRange] as const,
  campaign: (campaignId: string, timeRange?: string) =>
    [...analyticsKeys.all, 'campaign', campaignId, timeRange] as const,
  trends: (period?: string, timeRange?: string) =>
    [...analyticsKeys.all, 'trends', period, timeRange] as const,
  predictions: (timeRange?: string) => [...analyticsKeys.all, 'predictions', timeRange] as const,
  roi: (timeRange?: string) => [...analyticsKeys.all, 'roi', timeRange] as const,
  roiTrends: (period?: string) => [...analyticsKeys.all, 'roi', 'trends', period] as const,
};

// ============================================================================
// QUERIES
// ============================================================================

/**
 * Get analytics overview
 * @param timeRange - Time range for analytics (e.g., 'last_7d', 'last_30d', 'last_90d')
 */
export function useAnalyticsOverview(
  timeRange = 'last_30d',
  options?: UseQueryOptions<AnalyticsOverview>
) {
  return useQuery({
    queryKey: analyticsKeys.overview(timeRange),
    queryFn: () => apiClient.getAnalyticsOverview(timeRange),
    staleTime: 60000, // 1 minute
    refetchInterval: 300000, // 5 minutes
    ...options,
  });
}

/**
 * Get campaign-specific analytics
 * @param campaignId - Campaign ID
 * @param timeRange - Time range for analytics
 */
export function useCampaignAnalytics(
  campaignId: string,
  timeRange = 'last_30d',
  options?: UseQueryOptions<CampaignAnalytics>
) {
  return useQuery({
    queryKey: analyticsKeys.campaign(campaignId, timeRange),
    queryFn: () => apiClient.getCampaignAnalytics(campaignId, timeRange),
    enabled: !!campaignId,
    staleTime: 60000, // 1 minute
    refetchInterval: 300000, // 5 minutes
    ...options,
  });
}

/**
 * Get trend data for charts
 * @param period - Grouping period ('hourly', 'daily', 'weekly', 'monthly')
 * @param timeRange - Time range for trends
 */
export function useTrends(
  period = 'daily',
  timeRange = 'last_30d',
  options?: UseQueryOptions<TrendData[]>
) {
  return useQuery({
    queryKey: analyticsKeys.trends(period, timeRange),
    queryFn: () => apiClient.getTrends(period, timeRange),
    staleTime: 60000, // 1 minute
    refetchInterval: 300000, // 5 minutes
    ...options,
  });
}

/**
 * Get prediction accuracy metrics
 * @param timeRange - Time range for accuracy calculation
 */
export function usePredictionAccuracy(
  timeRange = 'last_30d',
  options?: UseQueryOptions<PredictionAccuracy[]>
) {
  return useQuery({
    queryKey: analyticsKeys.predictions(timeRange),
    queryFn: () => apiClient.getPredictionAccuracy(timeRange),
    staleTime: 300000, // 5 minutes
    refetchInterval: 600000, // 10 minutes
    ...options,
  });
}

/**
 * Get ROI performance metrics
 * @param timeRange - Time range for ROI calculation
 */
export function useROIPerformance(timeRange = 'last_30d', options?: UseQueryOptions<any>) {
  return useQuery({
    queryKey: analyticsKeys.roi(timeRange),
    queryFn: () => apiClient.getROIPerformance(timeRange),
    staleTime: 60000, // 1 minute
    refetchInterval: 300000, // 5 minutes
    ...options,
  });
}

/**
 * Get ROI trends over time
 * @param period - Grouping period ('daily', 'weekly', 'monthly')
 */
export function useROITrends(period = 'weekly', options?: UseQueryOptions<any>) {
  return useQuery({
    queryKey: analyticsKeys.roiTrends(period),
    queryFn: () => apiClient.getROITrends(period),
    staleTime: 60000, // 1 minute
    refetchInterval: 300000, // 5 minutes
    ...options,
  });
}

/**
 * Get Meta insights for a specific ad
 * @param adId - Meta Ad ID
 * @param datePreset - Date range preset ('today', 'yesterday', 'last_7d', 'last_30d', etc.)
 */
export function useMetaInsights(
  adId: string,
  datePreset = 'last_7d',
  options?: UseQueryOptions<any>
) {
  return useQuery({
    queryKey: [...analyticsKeys.all, 'meta-insights', adId, datePreset],
    queryFn: () => apiClient.getMetaInsights(adId, datePreset),
    enabled: !!adId,
    staleTime: 300000, // 5 minutes
    ...options,
  });
}

// ============================================================================
// HELPER HOOKS
// ============================================================================

/**
 * Combined analytics dashboard hook
 * Fetches all data needed for main analytics dashboard
 */
export function useAnalyticsDashboard(timeRange = 'last_30d') {
  const overview = useAnalyticsOverview(timeRange);
  const trends = useTrends('daily', timeRange);
  const roiPerformance = useROIPerformance(timeRange);
  const predictionAccuracy = usePredictionAccuracy(timeRange);

  return {
    overview: {
      data: overview.data,
      isLoading: overview.isLoading,
      isError: overview.isError,
      error: overview.error,
    },
    trends: {
      data: trends.data,
      isLoading: trends.isLoading,
      isError: trends.isError,
      error: trends.error,
    },
    roiPerformance: {
      data: roiPerformance.data,
      isLoading: roiPerformance.isLoading,
      isError: roiPerformance.isError,
      error: roiPerformance.error,
    },
    predictionAccuracy: {
      data: predictionAccuracy.data,
      isLoading: predictionAccuracy.isLoading,
      isError: predictionAccuracy.isError,
      error: predictionAccuracy.error,
    },
    isLoading:
      overview.isLoading ||
      trends.isLoading ||
      roiPerformance.isLoading ||
      predictionAccuracy.isLoading,
    isError:
      overview.isError || trends.isError || roiPerformance.isError || predictionAccuracy.isError,
    refetch: () => {
      overview.refetch();
      trends.refetch();
      roiPerformance.refetch();
      predictionAccuracy.refetch();
    },
  };
}

/**
 * Combined campaign detail analytics hook
 * Fetches all analytics for a specific campaign
 */
export function useCampaignDetailAnalytics(campaignId: string, timeRange = 'last_30d') {
  const analytics = useCampaignAnalytics(campaignId, timeRange);

  return {
    data: analytics.data,
    isLoading: analytics.isLoading,
    isError: analytics.isError,
    error: analytics.error,
    refetch: analytics.refetch,
  };
}
