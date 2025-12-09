import { useState, useEffect, useCallback } from 'react';
import {
  getAnalyticsOverview,
  getDashboardMetrics,
  getReliabilityMetrics,
  getDiversificationMetrics,
  getCampaignPerformance
} from '../services/api';

interface DashboardData {
  overview: any;
  metrics: any;
  reliability: any;
  diversification: any;
  loading: boolean;
  error: Error | null;
}

export function useDashboard(refreshInterval: number = 60000) {
  const [data, setData] = useState<DashboardData>({
    overview: null,
    metrics: null,
    reliability: null,
    diversification: null,
    loading: true,
    error: null
  });

  const fetchDashboardData = useCallback(async () => {
    try {
      setData(prev => ({ ...prev, loading: true, error: null }));

      const [overview, metrics, reliability, diversification] = await Promise.all([
        getAnalyticsOverview({ time_range: '7d' }).catch(() => null),
        getDashboardMetrics().catch(() => null),
        getReliabilityMetrics().catch(() => null),
        getDiversificationMetrics().catch(() => null)
      ]);

      setData({
        overview: overview?.data,
        metrics: metrics?.data,
        reliability: reliability?.data,
        diversification: diversification?.data,
        loading: false,
        error: null
      });
    } catch (error: any) {
      setData(prev => ({
        ...prev,
        loading: false,
        error: error
      }));
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();

    if (refreshInterval > 0) {
      const interval = setInterval(fetchDashboardData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchDashboardData, refreshInterval]);

  return { ...data, refresh: fetchDashboardData };
}

export function useCampaignDashboard(campaignId: string) {
  const [performance, setPerformance] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchPerformance = useCallback(async () => {
    if (!campaignId) return;

    try {
      setLoading(true);
      const response = await getCampaignPerformance(campaignId);
      setPerformance(response.data?.data);
      setError(null);
    } catch (e: any) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, [campaignId]);

  useEffect(() => {
    fetchPerformance();
  }, [fetchPerformance]);

  return { performance, loading, error, refresh: fetchPerformance };
}
