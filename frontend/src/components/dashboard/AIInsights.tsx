<<<<<<< HEAD
import { Heading } from '@/components/catalyst/heading'
import { Text } from '@/components/catalyst/text'
import { SparklesIcon } from '@heroicons/react/20/solid'
=======
import React, { useState } from 'react';
import { StaggerContainer } from '../ui/StaggerContainer';

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

const mockInsights: Insight[] = [
  {
    id: 1,
    type: 'success',
    title: 'Top performing hook',
    description: '"Did you know..." style hooks are converting 23% better than average this week.',
    action: 'Generate similar',
  },
  {
    id: 2,
    type: 'trend',
    title: 'Trending format',
    description: 'Split-screen before/after videos are seeing 2.1x higher engagement.',
    action: 'Try this format',
  },
  {
    id: 3,
    type: 'tip',
    title: 'Optimization tip',
    description: 'Videos under 15 seconds perform 40% better on Instagram Reels.',
    action: 'Optimize videos',
  },
];

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
  insights = mockInsights,
  onRefresh,
}) => {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    if (onRefresh) {
      await onRefresh();
    } else {
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    setIsRefreshing(false);
  };
>>>>>>> 6f56b443fc530e149eac70a51a1753661922ccf6

export function AIInsights() {
  return (
<<<<<<< HEAD
    <div className="p-6 rounded-lg border border-zinc-950/5 bg-gradient-to-br from-indigo-50 to-white dark:from-indigo-950/30 dark:to-zinc-900 shadow-sm dark:border-white/5">
      <div className="flex items-center gap-2 mb-4 text-indigo-600 dark:text-indigo-400">
        <SparklesIcon className="size-5" />
        <Heading level={2}>AI Insights</Heading>
      </div>
      <div className="space-y-4">
        <div className="p-3 rounded-md bg-white/50 dark:bg-white/5 border border-indigo-100 dark:border-white/5">
          <Text className="font-medium text-zinc-900 dark:text-white">Opportunity Detected</Text>
          <Text className="mt-1 text-sm">Your "Tech Gadget" video has a 25% higher CTR than average. Consider increasing budget.</Text>
        </div>
        <div className="p-3 rounded-md bg-white/50 dark:bg-white/5 border border-indigo-100 dark:border-white/5">
          <Text className="font-medium text-zinc-900 dark:text-white">Trend Alert</Text>
          <Text className="mt-1 text-sm">UGC-style videos are trending in your niche. Generate 3 new variations?</Text>
        </div>
=======
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

      <StaggerContainer staggerDelay={0.1} className="space-y-4">
        {insights.slice(0, 3).map((insight) => (
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
      </StaggerContainer>

      <div className="mt-4 pt-4 border-t border-zinc-800">
        <p className="text-zinc-500 text-xs text-center">
          Powered by Gemini AI • Updated 5 min ago
        </p>
>>>>>>> 6f56b443fc530e149eac70a51a1753661922ccf6
      </div>
    </div>
  )
}
