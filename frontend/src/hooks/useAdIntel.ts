/**
 * AdIntel Hook - React interface to AdIntel OS API
 *
 * Usage:
 *   const { searchAds, trackBrand, getWinners, trends } = useAdIntel();
 *   const results = await searchAds({ query: "fitness", winners_only: true });
 */

import { useState, useCallback } from 'react';
import { API_BASE_URL } from '../config/api';

// =============================================================================
// Types
// =============================================================================

export interface AdIntelAd {
  ad_id: string;
  brand_name: string;
  platform: 'meta' | 'tiktok' | 'google';
  format: 'video' | 'image' | 'carousel';
  headline?: string;
  body_text?: string;
  transcription?: string;
  thumbnail_url?: string;
  video_url?: string;
  landing_page_url?: string;
  industry?: string;
  primary_emotion?: string;
  emotional_drivers: string[];
  hook_type?: string;
  hook_text?: string;
  winning_patterns: string[];
  running_duration_days: number;
  is_winner: boolean;
  winner_score?: number;
  first_seen: string;
  last_seen: string;
}

export interface SearchFilters {
  query?: string;
  platform?: 'meta' | 'tiktok' | 'google' | 'all';
  format?: 'video' | 'image' | 'carousel' | 'all';
  industry?: string;
  emotion?: string;
  hook_type?: string;
  min_running_days?: number;
  winners_only?: boolean;
  brand_name?: string;
  sort_by?: 'running_duration_days:desc' | 'winner_score:desc' | 'created_at:desc';
  page?: number;
  per_page?: number;
}

export interface SearchResponse {
  hits: AdIntelAd[];
  total: number;
  page: number;
  per_page: number;
  facets: Record<string, Array<{ value: string; count: number }>>;
  credits_used: number;
  remaining_credits: number;
}

export interface TrackedBrand {
  brand_id: string;
  brand_name: string;
  status: string;
  ad_count: number;
  winner_count: number;
  last_checked?: string;
  next_check?: string;
}

export interface TrendData {
  total_winners: number;
  by_industry: Array<{ value: string; count: number }>;
  by_emotion: Array<{ value: string; count: number }>;
  by_hook_type: Array<{ value: string; count: number }>;
  top_patterns: Array<{ value: string; count: number }>;
}

// =============================================================================
// API Client
// =============================================================================

const API_KEY = localStorage.getItem('adintel_api_key') || 'demo-key';

async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/api/intel${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.detail || error.error || `API error: ${response.status}`);
  }

  return response.json();
}

// =============================================================================
// Hook
// =============================================================================

export function useAdIntel() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [trends, setTrends] = useState<TrendData | null>(null);
  const [trackedBrands, setTrackedBrands] = useState<TrackedBrand[]>([]);

  // Search ads with filters
  const searchAds = useCallback(async (filters: SearchFilters = {}): Promise<SearchResponse> => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiCall<SearchResponse>('/discovery/search', {
        method: 'POST',
        body: JSON.stringify({
          query: filters.query || '*',
          platform: filters.platform,
          format: filters.format,
          industry: filters.industry,
          emotion: filters.emotion,
          hook_type: filters.hook_type,
          min_running_days: filters.min_running_days || 0,
          winners_only: filters.winners_only || false,
          brand_name: filters.brand_name,
          sort_by: filters.sort_by || 'running_duration_days:desc',
          page: filters.page || 1,
          per_page: filters.per_page || 20,
        }),
      });

      setResults(response);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Search failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get winning ads
  const getWinners = useCallback(async (
    industry?: string,
    platform?: string,
    minDays: number = 30,
    page: number = 1,
    perPage: number = 20
  ) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (industry) params.set('industry', industry);
      if (platform) params.set('platform', platform);
      params.set('min_days', minDays.toString());
      params.set('page', page.toString());
      params.set('per_page', perPage.toString());

      const response = await apiCall<{ winners: AdIntelAd[]; total: number }>(
        `/discovery/winners?${params}`
      );
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get winners';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Find similar ads
  const findSimilar = useCallback(async (adId: string, limit: number = 10) => {
    setLoading(true);
    try {
      const response = await apiCall<{ similar_ads: AdIntelAd[] }>(
        `/discovery/similar/${adId}?limit=${limit}`
      );
      return response.similar_ads;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to find similar ads';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Track a brand (Spyder)
  const trackBrand = useCallback(async (
    brandName: string,
    domain?: string,
    platforms: string[] = ['meta']
  ): Promise<TrackedBrand> => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiCall<TrackedBrand>('/spyder/track', {
        method: 'POST',
        body: JSON.stringify({
          brand_name: brandName,
          domain,
          platforms,
          check_interval_hours: 24,
        }),
      });

      setTrackedBrands(prev => [...prev.filter(b => b.brand_id !== response.brand_id), response]);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to track brand';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get tracked brands
  const getTrackedBrands = useCallback(async (): Promise<TrackedBrand[]> => {
    setLoading(true);
    try {
      const response = await apiCall<{ brands: TrackedBrand[] }>('/spyder/brands');
      setTrackedBrands(response.brands);
      return response.brands;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get tracked brands';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get brand ads
  const getBrandAds = useCallback(async (brandId: string, page: number = 1, perPage: number = 20) => {
    setLoading(true);
    try {
      const response = await apiCall<{ ads: AdIntelAd[]; total: number }>(
        `/spyder/brand/${brandId}/ads?page=${page}&per_page=${perPage}`
      );
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get brand ads';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Untrack brand
  const untrackBrand = useCallback(async (brandId: string) => {
    setLoading(true);
    try {
      await apiCall(`/spyder/brand/${brandId}`, { method: 'DELETE' });
      setTrackedBrands(prev => prev.filter(b => b.brand_id !== brandId));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to untrack brand';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Enrich ad with AI
  const enrichAd = useCallback(async (adId: string, videoUrl?: string) => {
    setLoading(true);
    try {
      const response = await apiCall<{
        transcription?: string;
        hook_analysis?: any;
        emotional_drivers: string[];
        winning_patterns: string[];
        winner_score: number;
      }>('/enrich', {
        method: 'POST',
        body: JSON.stringify({ ad_id: adId, video_url: videoUrl }),
      });
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Enrichment failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get trends
  const getTrends = useCallback(async (): Promise<TrendData> => {
    setLoading(true);
    try {
      const response = await apiCall<TrendData>('/analytics/trends');
      setTrends(response);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get trends';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get emotion breakdown
  const getEmotionBreakdown = useCallback(async (industry?: string) => {
    try {
      const params = industry ? `?industry=${industry}` : '';
      return await apiCall<{
        primary_emotions: Array<{ value: string; count: number }>;
        emotional_drivers: Array<{ value: string; count: number }>;
      }>(`/analytics/emotions${params}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get emotions';
      setError(message);
      throw err;
    }
  }, []);

  // Get hook patterns
  const getHookPatterns = useCallback(async (industry?: string) => {
    try {
      const params = industry ? `?industry=${industry}` : '';
      return await apiCall<{
        hook_types: Array<{ value: string; count: number }>;
        winning_patterns: Array<{ value: string; count: number }>;
      }>(`/analytics/hooks${params}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get hooks';
      setError(message);
      throw err;
    }
  }, []);

  // Get brand analytics
  const getBrandAnalytics = useCallback(async (brandName: string) => {
    try {
      return await apiCall<{
        brand_name: string;
        total_ads: number;
        winner_count: number;
        winner_rate: number;
        avg_running_days: number;
        facets: Record<string, Array<{ value: string; count: number }>>;
      }>(`/analytics/brand/${encodeURIComponent(brandName)}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get brand analytics';
      setError(message);
      throw err;
    }
  }, []);

  // Get credit balance
  const getCredits = useCallback(async () => {
    try {
      return await apiCall<{
        total_credits: number;
        used_credits: number;
        remaining_credits: number;
        reset_date: string;
        plan: string;
      }>('/account/credits');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get credits';
      setError(message);
      throw err;
    }
  }, []);

  // Get suggestions (autocomplete)
  const getSuggestions = useCallback(async (query: string, limit: number = 10) => {
    try {
      const response = await apiCall<{ suggestions: string[] }>(
        `/discovery/suggestions?q=${encodeURIComponent(query)}&limit=${limit}`
      );
      return response.suggestions;
    } catch (err) {
      return []; // Fail silently for suggestions
    }
  }, []);

  return {
    // State
    loading,
    error,
    results,
    trends,
    trackedBrands,

    // Discovery
    searchAds,
    getWinners,
    findSimilar,
    getSuggestions,

    // Spyder (Brand Tracking)
    trackBrand,
    getTrackedBrands,
    getBrandAds,
    untrackBrand,

    // Enrichment
    enrichAd,

    // Analytics
    getTrends,
    getEmotionBreakdown,
    getHookPatterns,
    getBrandAnalytics,

    // Account
    getCredits,

    // Helpers
    clearError: () => setError(null),
  };
}

export default useAdIntel;
