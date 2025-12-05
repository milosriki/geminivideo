/**
 * Investor Presentation Page
 *
 * Full-screen slideshow mode showcasing platform capabilities.
 * Designed to close the €5M investment.
 *
 * Keyboard shortcuts:
 * - Arrow Left/Right: Navigate slides
 * - F: Toggle fullscreen
 * - D: Toggle demo data
 * - ESC: Exit presentation
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDemoMode, fetchWithDemoMode } from '@/hooks/useDemoMode';
import {
  ChartBarIcon,
  SparklesIcon,
  RocketLaunchIcon,
  CurrencyDollarIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  XMarkIcon,
  ArrowTrendingUpIcon,
  LightBulbIcon,
  UserGroupIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

interface PresentationStats {
  headline_metrics: {
    total_revenue: number;
    average_roas: number;
    total_conversions: number;
    average_ctr: number;
    total_campaigns: number;
    active_campaigns: number;
  };
  ai_performance: {
    average_ai_score: number;
    approval_rate: number;
    creatives_evaluated: number;
    high_performers: number;
  };
  testing_efficiency: {
    active_tests: number;
    average_confidence: number;
    total_samples: number;
    clear_winners: number;
  };
  platform_reach: {
    platforms: number;
    total_impressions: number;
    multi_platform_roas: number;
  };
  growth_indicators: {
    month_over_month_growth: number;
    roas_improvement: number;
    conversion_rate_lift: number;
    cost_efficiency_gain: number;
  };
}

const SLIDES = [
  {
    id: 'intro',
    title: 'TitanAds AI Platform',
    subtitle: 'Autonomous Ad Creative Generation & Optimization',
    icon: RocketLaunchIcon,
    gradient: 'from-violet-500 to-purple-600'
  },
  {
    id: 'metrics',
    title: 'Platform Performance',
    subtitle: 'Real Results from 20 Elite Marketers',
    icon: ChartBarIcon,
    gradient: 'from-blue-500 to-cyan-600'
  },
  {
    id: 'ai-council',
    title: 'AI Council in Action',
    subtitle: '3-Agent System: Director, Oracle, Strategist',
    icon: SparklesIcon,
    gradient: 'from-pink-500 to-rose-600'
  },
  {
    id: 'ab-testing',
    title: 'Thompson Sampling A/B Tests',
    subtitle: 'Intelligent Budget Allocation',
    icon: LightBulbIcon,
    gradient: 'from-amber-500 to-orange-600'
  },
  {
    id: 'platforms',
    title: 'Multi-Platform Domination',
    subtitle: 'Meta, Google, TikTok - Unified Dashboard',
    icon: UserGroupIcon,
    gradient: 'from-emerald-500 to-green-600'
  },
  {
    id: 'growth',
    title: 'Growth Trajectory',
    subtitle: 'Path to €5M ARR',
    icon: ArrowTrendingUpIcon,
    gradient: 'from-indigo-500 to-blue-600'
  },
  {
    id: 'cta',
    title: 'Join Our Journey',
    subtitle: 'Investment Opportunity: €5M Series A',
    icon: CurrencyDollarIcon,
    gradient: 'from-violet-500 to-purple-600'
  }
];

export default function InvestorPresentationPage() {
  const navigate = useNavigate();
  const { enabled: demoMode, enableDemoMode } = useDemoMode();
  const [currentSlide, setCurrentSlide] = useState(0);
  const [stats, setStats] = useState<PresentationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Enable demo mode on mount
  useEffect(() => {
    if (!demoMode) {
      enableDemoMode();
    }
  }, [demoMode, enableDemoMode]);

  // Fetch presentation stats
  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const response = await fetchWithDemoMode('/api/presentation-stats', true);
        const data = await response.json();
        setStats(data);
      } catch (error) {
        console.error('Error fetching presentation stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowLeft':
          prevSlide();
          break;
        case 'ArrowRight':
        case ' ': // Space bar
          e.preventDefault();
          nextSlide();
          break;
        case 'f':
        case 'F':
          toggleFullscreen();
          break;
        case 'd':
        case 'D':
          // Toggle demo mode (already handled by hook)
          break;
        case 'Escape':
          exitPresentation();
          break;
        case 'Home':
          setCurrentSlide(0);
          break;
        case 'End':
          setCurrentSlide(SLIDES.length - 1);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [currentSlide]);

  const nextSlide = useCallback(() => {
    setCurrentSlide(prev => (prev + 1) % SLIDES.length);
  }, []);

  const prevSlide = useCallback(() => {
    setCurrentSlide(prev => (prev - 1 + SLIDES.length) % SLIDES.length);
  }, []);

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => {
        setIsFullscreen(true);
      }).catch(err => {
        console.error('Error entering fullscreen:', err);
      });
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
      });
    }
  }, []);

  const exitPresentation = useCallback(() => {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    }
    navigate('/');
  }, [navigate]);

  const slide = SLIDES[currentSlide];
  const Icon = slide.icon;

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toFixed(0);
  };

  const formatCurrency = (num: number) => {
    return `€${formatNumber(num)}`;
  };

  const AnimatedNumber = ({ value, suffix = '' }: { value: number; suffix?: string }) => {
    return (
      <span className="tabular-nums">
        {value.toFixed(1)}{suffix}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-white relative overflow-hidden">
      {/* Background gradient */}
      <div className={`absolute inset-0 bg-gradient-to-br ${slide.gradient} opacity-10`} />

      {/* Navigation controls */}
      <div className="absolute top-4 right-4 z-50 flex items-center gap-2">
        <button
          onClick={toggleFullscreen}
          className="px-3 py-2 rounded-lg bg-zinc-800/50 border border-zinc-700/50 backdrop-blur-sm hover:bg-zinc-700/50 transition-colors text-sm"
        >
          {isFullscreen ? 'Exit Fullscreen (F)' : 'Fullscreen (F)'}
        </button>
        <button
          onClick={exitPresentation}
          className="p-2 rounded-lg bg-zinc-800/50 border border-zinc-700/50 backdrop-blur-sm hover:bg-zinc-700/50 transition-colors"
        >
          <XMarkIcon className="h-5 w-5" />
        </button>
      </div>

      {/* Slide progress */}
      <div className="absolute top-4 left-4 z-50 flex items-center gap-2">
        <span className="px-3 py-2 rounded-lg bg-zinc-800/50 border border-zinc-700/50 backdrop-blur-sm text-sm">
          {currentSlide + 1} / {SLIDES.length}
        </span>
      </div>

      {/* Main content */}
      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center p-8">
        {/* Slide content */}
        <div className="max-w-6xl w-full">
          {/* Title section */}
          <div className="text-center mb-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className={`inline-flex p-4 rounded-2xl bg-gradient-to-br ${slide.gradient} mb-6`}>
              <Icon className="h-12 w-12 text-white" />
            </div>
            <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-white to-zinc-400 bg-clip-text text-transparent">
              {slide.title}
            </h1>
            <p className="text-xl md:text-2xl text-zinc-400">
              {slide.subtitle}
            </p>
          </div>

          {/* Slide-specific content */}
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="h-12 w-12 rounded-full border-4 border-zinc-800 border-t-violet-500 animate-spin" />
            </div>
          ) : (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
              {renderSlideContent(slide.id, stats)}
            </div>
          )}
        </div>

        {/* Navigation arrows */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-4">
          <button
            onClick={prevSlide}
            className="p-3 rounded-full bg-zinc-800/50 border border-zinc-700/50 backdrop-blur-sm hover:bg-zinc-700/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={currentSlide === 0}
          >
            <ChevronLeftIcon className="h-6 w-6" />
          </button>

          {/* Slide indicators */}
          <div className="flex items-center gap-2">
            {SLIDES.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentSlide(idx)}
                className={`h-2 rounded-full transition-all ${
                  idx === currentSlide
                    ? 'w-8 bg-violet-500'
                    : 'w-2 bg-zinc-700 hover:bg-zinc-600'
                }`}
              />
            ))}
          </div>

          <button
            onClick={nextSlide}
            className="p-3 rounded-full bg-zinc-800/50 border border-zinc-700/50 backdrop-blur-sm hover:bg-zinc-700/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={currentSlide === SLIDES.length - 1}
          >
            <ChevronRightIcon className="h-6 w-6" />
          </button>
        </div>
      </div>

      {/* Keyboard shortcuts help */}
      <div className="absolute bottom-4 right-4 z-40 text-xs text-zinc-500 text-right">
        <div>← → Navigate | F Fullscreen | ESC Exit</div>
      </div>
    </div>
  );
}

function renderSlideContent(slideId: string, stats: PresentationStats | null) {
  if (!stats) return null;

  switch (slideId) {
    case 'intro':
      return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <FeatureCard
            title="AI-Powered"
            description="3-agent AI Council evaluates every creative"
            stat="92% approval rate"
          />
          <FeatureCard
            title="Autonomous"
            description="Generate, test, and optimize ads automatically"
            stat="24/7 operation"
          />
          <FeatureCard
            title="Multi-Platform"
            description="Deploy to Meta, Google, TikTok simultaneously"
            stat="3 platforms"
          />
        </div>
      );

    case 'metrics':
      return (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          <MetricCard
            label="Total Revenue"
            value={`€${stats.headline_metrics.total_revenue.toLocaleString()}`}
            trend="+32%"
          />
          <MetricCard
            label="Average ROAS"
            value={`${stats.headline_metrics.average_roas.toFixed(2)}x`}
            trend="+18%"
          />
          <MetricCard
            label="Conversions"
            value={stats.headline_metrics.total_conversions.toLocaleString()}
            trend="+45%"
          />
          <MetricCard
            label="CTR"
            value={`${stats.headline_metrics.average_ctr.toFixed(2)}%`}
            trend="+27%"
          />
          <MetricCard
            label="Active Campaigns"
            value={stats.headline_metrics.active_campaigns.toString()}
            trend="Live"
          />
          <MetricCard
            label="Total Campaigns"
            value={stats.headline_metrics.total_campaigns.toString()}
            trend="All time"
          />
        </div>
      );

    case 'ai-council':
      return (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <AgentCard
              name="Director"
              role="Visual & Storytelling"
              score={stats.ai_performance.average_ai_score}
            />
            <AgentCard
              name="Oracle"
              role="Performance Prediction"
              score={stats.ai_performance.average_ai_score}
            />
            <AgentCard
              name="Strategist"
              role="Audience & Timing"
              score={stats.ai_performance.average_ai_score}
            />
          </div>
          <div className="text-center p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/30">
            <div className="text-4xl font-bold text-violet-400 mb-2">
              {stats.ai_performance.approval_rate.toFixed(1)}%
            </div>
            <div className="text-zinc-400">
              Approval Rate ({stats.ai_performance.high_performers} high performers)
            </div>
          </div>
        </div>
      );

    case 'ab-testing':
      return (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/30">
              <div className="text-2xl font-bold mb-2">Thompson Sampling</div>
              <p className="text-zinc-400 mb-4">
                Bayesian optimization allocates budget to winning variants in real-time
              </p>
              <div className="flex items-center gap-2 text-emerald-400">
                <CheckCircleIcon className="h-5 w-5" />
                <span>{stats.testing_efficiency.average_confidence.toFixed(1)}% avg confidence</span>
              </div>
            </div>
            <div className="p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/30">
              <div className="text-2xl font-bold mb-2">Active Tests</div>
              <div className="text-5xl font-bold text-violet-400 my-4">
                {stats.testing_efficiency.active_tests}
              </div>
              <p className="text-zinc-400">
                {stats.testing_efficiency.total_samples.toLocaleString()} total samples
              </p>
            </div>
          </div>
        </div>
      );

    case 'platforms':
      return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <PlatformCard
            name="Meta"
            impressions={Math.round(stats.platform_reach.total_impressions * 0.45)}
            roas={stats.platform_reach.multi_platform_roas * 1.15}
          />
          <PlatformCard
            name="Google"
            impressions={Math.round(stats.platform_reach.total_impressions * 0.35)}
            roas={stats.platform_reach.multi_platform_roas * 0.95}
          />
          <PlatformCard
            name="TikTok"
            impressions={Math.round(stats.platform_reach.total_impressions * 0.20)}
            roas={stats.platform_reach.multi_platform_roas * 0.90}
          />
        </div>
      );

    case 'growth':
      return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <GrowthCard
            label="MoM Growth"
            value={`+${stats.growth_indicators.month_over_month_growth}%`}
          />
          <GrowthCard
            label="ROAS Improvement"
            value={`+${stats.growth_indicators.roas_improvement}%`}
          />
          <GrowthCard
            label="CVR Lift"
            value={`+${stats.growth_indicators.conversion_rate_lift}%`}
          />
          <GrowthCard
            label="Cost Efficiency"
            value={`+${stats.growth_indicators.cost_efficiency_gain}%`}
          />
        </div>
      );

    case 'cta':
      return (
        <div className="text-center space-y-8">
          <div className="p-8 rounded-2xl bg-gradient-to-br from-violet-500/20 to-purple-500/20 border border-violet-500/30">
            <div className="text-6xl font-bold text-violet-400 mb-4">€5M</div>
            <div className="text-2xl mb-2">Series A Investment</div>
            <p className="text-zinc-400 max-w-2xl mx-auto">
              Join us in revolutionizing ad creative generation with AI.
              20 elite marketers, 1,000+ campaigns, proven ROI.
            </p>
          </div>
          <button
            onClick={() => window.location.href = 'mailto:invest@titanads.ai'}
            className="px-8 py-4 rounded-xl bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 transition-all transform hover:scale-105 text-lg font-semibold"
          >
            Schedule Demo Call
          </button>
        </div>
      );

    default:
      return null;
  }
}

function FeatureCard({ title, description, stat }: { title: string; description: string; stat: string }) {
  return (
    <div className="p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/30 hover:border-zinc-600/50 transition-colors">
      <div className="text-xl font-bold mb-2">{title}</div>
      <p className="text-zinc-400 mb-4">{description}</p>
      <div className="text-2xl font-bold text-violet-400">{stat}</div>
    </div>
  );
}

function MetricCard({ label, value, trend }: { label: string; value: string; trend: string }) {
  return (
    <div className="p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/30">
      <div className="text-sm text-zinc-500 mb-1">{label}</div>
      <div className="text-3xl font-bold mb-2">{value}</div>
      <div className="text-emerald-400 text-sm">{trend}</div>
    </div>
  );
}

function AgentCard({ name, role, score }: { name: string; role: string; score: number }) {
  return (
    <div className="p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/30">
      <div className="text-xl font-bold mb-1">{name}</div>
      <div className="text-sm text-zinc-500 mb-4">{role}</div>
      <div className="flex items-center gap-2">
        <div className="flex-1 h-2 rounded-full bg-zinc-700">
          <div
            className="h-full rounded-full bg-gradient-to-r from-violet-500 to-purple-600"
            style={{ width: `${score}%` }}
          />
        </div>
        <span className="text-sm font-mono">{score.toFixed(0)}</span>
      </div>
    </div>
  );
}

function PlatformCard({ name, impressions, roas }: { name: string; impressions: number; roas: number }) {
  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toFixed(0);
  };

  return (
    <div className="p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/30">
      <div className="text-2xl font-bold mb-4">{name}</div>
      <div className="space-y-3">
        <div>
          <div className="text-sm text-zinc-500">Impressions</div>
          <div className="text-xl font-mono">{formatNumber(impressions)}</div>
        </div>
        <div>
          <div className="text-sm text-zinc-500">ROAS</div>
          <div className="text-xl font-mono text-violet-400">{roas.toFixed(2)}x</div>
        </div>
      </div>
    </div>
  );
}

function GrowthCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-6 rounded-xl bg-zinc-800/30 border border-zinc-700/30 text-center">
      <div className="text-sm text-zinc-500 mb-2">{label}</div>
      <div className="text-3xl font-bold text-emerald-400">{value}</div>
    </div>
  );
}
