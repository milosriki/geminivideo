/**
 * AI Insights Component
 *
 * ============================================================================
 * 🔴 CRITICAL ANALYSIS FINDINGS (December 2024)
 * ============================================================================
 *
 * STATUS: 100% FAKE INSIGHTS - Not powered by AI at all!
 *
 * WHAT'S FAKE:
 * - mockInsights array (lines 17-39): ALL hardcoded text
 *   "23% better than average" - made up percentage
 *   "2.1x higher engagement" - fabricated multiplier
 *   "40% better on Instagram" - invented statistic
 * - "Powered by Gemini AI" (line 150): FALSE - no AI is called
 * - "Updated 5 min ago" (line 150): FALSE - data never updates
 * - Refresh button: Just does setTimeout, no real refresh
 *
 * WHAT IT SHOULD DO:
 * 1. Call Gemini API to analyze user's actual ad performance
 * 2. Compare against industry benchmarks (from real data)
 * 3. Generate personalized insights based on user's content
 *
 * FAST FIX:
 * const insights = await fetch('/api/insights/ai').then(r => r.json());
 * Where /api/insights/ai calls Gemini with user's performance data
 * ============================================================================
 */

import React, { useState, useEffect } from 'react';


interface Insight {
  id: number;
  type: 'tip' | 'warning' | 'success' | 'trend';
  title: string;
  description: string;
  action?: string;
}

interface AIInsightsProps {
  insights?: Insight[];
  onRefresh?: () => void;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

const getInsightIcon = (type: Insight['type']) => {
  switch (type) {
    case 'success':
      return (
        <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
          <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      );
    case 'warning':
      return (
        <div className="w-8 h-8 rounded-full bg-amber-500/20 flex items-center justify-center flex-shrink-0">
          <svg className="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
      );
    case 'trend':
      return (
        <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0">
          <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        </div>
      );
    case 'tip':
    default:
      return (
        <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center flex-shrink-0">
          <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
      );
  }
};

export const AIInsights: React.FC<AIInsightsProps> = ({
  insights: propsInsights,
  onRefresh,
}) => {
  const [insights, setInsights] = useState<Insight[]>(propsInsights || []);
  const [loading, setLoading] = useState(!propsInsights);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchInsights = async () => {
    try {
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/insights/ai`);
      if (response.ok) {
        const data = await response.json();
        setInsights(data.insights || []);
        setLastUpdated(new Date());
      } else {
        throw new Error(`API returned ${response.status}`);
      }
    } catch (err) {
      console.error('Failed to fetch insights:', err);
      setError('Unable to load AI insights. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!propsInsights) {
      fetchInsights();
    }
  }, [propsInsights]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    if (onRefresh) {
      await onRefresh();
    } else {
      await fetchInsights();
    }
    setIsRefreshing(false);
  };

  const getTimeSinceUpdate = () => {
    const seconds = Math.floor((new Date().getTime() - lastUpdated.getTime()) / 1000);
    if (seconds < 60) return 'Just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} min ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 sm:p-5 shadow-lg shadow-black/20">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
            </svg>
          </div>
          <h3 className="text-white font-semibold text-base sm:text-lg">AI Insights</h3>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="p-2 rounded-lg hover:bg-zinc-800 transition-colors disabled:opacity-50 min-h-[44px] min-w-[44px] flex items-center justify-center sm:min-h-0 sm:min-w-0"
        >
          <svg
            className={`w-4 h-4 text-zinc-400 ${isRefreshing ? 'animate-spin' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      <div className="space-y-4">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-lg bg-red-900/20 border border-red-800/50">
            <p className="text-red-400 text-sm">{error}</p>
            <button
              onClick={handleRefresh}
              className="mt-2 text-red-300 hover:text-red-200 text-sm font-medium underline"
            >
              Try again
            </button>
          </div>
        )}

        {!loading && !error && insights.length === 0 && (
          <div className="p-8 text-center">
            <p className="text-zinc-400 text-sm">No insights available yet.</p>
            <p className="text-zinc-500 text-xs mt-1">Generate some ads to get AI-powered insights.</p>
          </div>
        )}

        {!loading && !error && insights.slice(0, 3).map((insight) => (
          <div
            key={insight.id}
            className="p-3 sm:p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50 hover:bg-zinc-800 transition-colors"
          >
            <div className="flex items-start gap-3">
              {getInsightIcon(insight.type)}
              <div className="flex-1 min-w-0">
                <p className="text-white font-medium text-sm">{insight.title}</p>
                <p className="text-zinc-400 text-sm mt-1 leading-relaxed">
                  {insight.description}
                </p>
                {insight.action && (
                  <button className="mt-2 text-indigo-400 hover:text-indigo-300 text-sm font-medium transition-colors flex items-center gap-1">
                    {insight.action}
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-zinc-800">
        <p className="text-zinc-500 text-xs text-center">
          Powered by Gemini AI • Updated {getTimeSinceUpdate()}
        </p>
      </div>
    </div>
  )
}
