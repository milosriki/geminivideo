/**
 * Demo Mode API Routes
 *
 * Special endpoints for investor demonstrations with impressive real-looking data.
 * Designed to close the €5M investment.
 */

import { Router, Request, Response } from 'express';
import { demoDataGenerator } from '../demo/demo-data-generator';
import { apiRateLimiter } from '../middleware/security';
import { validateInput } from '../middleware/validation';

const router = Router();

// Demo mode session store (in-memory for demo purposes)
const demoSessions = new Map<string, any>();

/**
 * GET /api/demo/status
 * Check if demo mode is available and get demo info
 */
router.get('/status', (req: Request, res: Response) => {
  res.json({
    available: true,
    version: '1.0.0',
    features: [
      'Impressive campaign metrics',
      'Live-updating charts',
      'AI Council scoring',
      'A/B test with Thompson Sampling',
      'ROAS prediction accuracy',
      'Multi-platform comparison'
    ],
    message: 'Demo mode ready for investor presentation'
  });
});

/**
 * GET /api/demo/campaigns
 * Get demo campaigns with impressive metrics
 */
router.get(
  '/campaigns',
  apiRateLimiter,
  validateInput({
    query: {
      days: { type: 'number', required: false, min: 1, max: 365 },
      count: { type: 'number', required: false, min: 1, max: 20 },
      scenario: { type: 'string', required: false }
    }
  }),
  (req: Request, res: Response) => {
  try {
    const { scenario, days = 30 } = req.query;

    let campaigns;
    if (scenario && typeof scenario === 'string') {
      // Generate single campaign with specific scenario
      const campaign = demoDataGenerator.generateCampaign(
        scenario as any,
        parseInt(days as string) || 30
      );
      campaigns = [campaign];
    } else {
      // Generate full demo dataset
      const dataset = demoDataGenerator.generateDemoDataset();
      campaigns = dataset.campaigns;

      // Calculate summary stats
      dataset.summary.total_spend = campaigns.reduce((sum, c) => sum + c.spend, 0);
      dataset.summary.total_revenue = campaigns.reduce((sum, c) => sum + c.revenue, 0);
      dataset.summary.avg_roas = dataset.summary.total_revenue / dataset.summary.total_spend;
      dataset.summary.total_conversions = campaigns.reduce((sum, c) => sum + c.conversions, 0);

      // Platform distribution
      campaigns.forEach(c => {
        dataset.summary.platform_distribution[c.platform]++;
      });

      return res.json({
        campaigns,
        summary: dataset.summary,
        timestamp: new Date().toISOString()
      });
    }

    res.json({
      campaigns,
      timestamp: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('Demo campaigns error:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/demo/campaigns/:id
 * Get detailed demo campaign data
 */
router.get('/campaigns/:id', apiRateLimiter, (req: Request, res: Response) => {
  try {
    const { id } = req.params;

    // Check if we have cached data
    let campaign = demoSessions.get(`campaign-${id}`);

    if (!campaign) {
      // Generate new campaign
      campaign = demoDataGenerator.generateCampaign('successful_campaign', 30);
      campaign.id = id;
      demoSessions.set(`campaign-${id}`, campaign);
    }

    res.json({
      campaign,
      timestamp: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('Demo campaign detail error:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/demo/analytics
 * Get demo analytics data for dashboard
 */
router.get(
  '/analytics',
  apiRateLimiter,
  validateInput({
    query: {
      days: { type: 'number', required: false, min: 1, max: 365 },
      scenario: { type: 'string', required: false }
    }
  }),
  (req: Request, res: Response) => {
  try {
    const { days = 30 } = req.query;
    const analytics = demoDataGenerator.generateAnalytics(parseInt(days as string) || 30);

    res.json({
      ...analytics,
      timestamp: new Date().toISOString(),
      demo_mode: true
    });

  } catch (error: any) {
    console.error('Demo analytics error:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/demo/ai-council
 * Get demo AI Council scoring data
 */
router.get('/ai-council', apiRateLimiter, (req: Request, res: Response) => {
  try {
    const { performance = 'high' } = req.query;

    const score = demoDataGenerator.generateAICouncilScore(performance as any);

    res.json({
      ...score,
      demo_mode: true,
      timestamp: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('Demo AI Council error:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/demo/ai-council/batch
 * Get multiple AI Council scores for showcase
 */
router.get(
  '/ai-council/batch',
  apiRateLimiter,
  validateInput({
    query: {
      count: { type: 'number', required: false, min: 1, max: 20 }
    }
  }),
  (req: Request, res: Response) => {
  try {
    const { count = 5 } = req.query;
    const numScores = Math.min(parseInt(count as string) || 5, 20);

    const scores = [];
    for (let i = 0; i < numScores; i++) {
      const performance = i < numScores * 0.6 ? 'high' :
                         i < numScores * 0.9 ? 'medium' : 'low';
      scores.push(demoDataGenerator.generateAICouncilScore(performance as any));
    }

    // Calculate aggregate stats
    const avgScore = scores.reduce((sum, s) => sum + s.scores.overall_score, 0) / scores.length;
    const approvedCount = scores.filter(s => s.scores.recommendation === 'approved').length;
    const approvalRate = (approvedCount / scores.length) * 100;

    res.json({
      scores,
      summary: {
        total_evaluated: scores.length,
        average_score: parseFloat(avgScore.toFixed(2)),
        approved_count: approvedCount,
        approval_rate: parseFloat(approvalRate.toFixed(2)),
        high_performers: scores.filter(s => s.scores.overall_score >= 85).length
      },
      demo_mode: true,
      timestamp: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('Demo AI Council batch error:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/demo/ab-tests
 * Get demo A/B test data with Thompson Sampling
 */
router.get(
  '/ab-tests',
  apiRateLimiter,
  validateInput({
    query: {
      count: { type: 'number', required: false, min: 1, max: 20 }
    }
  }),
  (req: Request, res: Response) => {
  try {
    const { count = 3 } = req.query;
    const numTests = Math.min(parseInt(count as string) || 3, 10);

    const tests = [];
    for (let i = 0; i < numTests; i++) {
      tests.push(demoDataGenerator.generateABTest());
    }

    // Calculate aggregate stats
    const totalSampleSize = tests.reduce((sum, t) => sum + t.sample_size, 0);
    const avgConfidence = tests.reduce((sum, t) => sum + t.confidence, 0) / tests.length;
    const completedTests = tests.filter(t => t.status === 'completed').length;

    res.json({
      tests,
      summary: {
        total_tests: tests.length,
        total_sample_size: totalSampleSize,
        average_confidence: parseFloat(avgConfidence.toFixed(2)),
        completed_tests: completedTests,
        running_tests: tests.length - completedTests
      },
      demo_mode: true,
      timestamp: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('Demo AB tests error:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/demo/ab-tests/:id
 * Get detailed A/B test results
 */
router.get('/ab-tests/:id', apiRateLimiter, (req: Request, res: Response) => {
  try {
    const { id } = req.params;

    // Check cache
    let test = demoSessions.get(`ab-test-${id}`);

    if (!test) {
      test = demoDataGenerator.generateABTest();
      test.id = id;
      demoSessions.set(`ab-test-${id}`, test);
    }

    // Calculate lift
    const control = test.variants[0];
    const winner = test.variants.find((v: any) => v.id === test.winner);

    const lift = winner ? {
      ctr_lift: ((winner.ctr - control.ctr) / control.ctr * 100).toFixed(2),
      cvr_lift: ((winner.cvr - control.cvr) / control.cvr * 100).toFixed(2),
      roas_lift: ((winner.roas - control.roas) / control.roas * 100).toFixed(2),
      revenue_lift: ((winner.revenue - control.revenue) / control.revenue * 100).toFixed(2)
    } : null;

    res.json({
      test,
      lift,
      demo_mode: true,
      timestamp: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('Demo AB test detail error:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/demo/performance-comparison
 * Multi-platform performance comparison
 */
router.get(
  '/performance-comparison',
  apiRateLimiter,
  validateInput({
    query: {
      platforms: { type: 'string', required: false },
      days: { type: 'number', required: false, min: 1, max: 365 }
    }
  }),
  (req: Request, res: Response) => {
  try {
    const analytics = demoDataGenerator.generateAnalytics(30);

    // Add additional comparison metrics
    const platformData = analytics.platform_performance.map(p => ({
      ...p,
      ctr: parseFloat(((p.clicks / p.impressions) * 100).toFixed(2)),
      cvr: parseFloat(((p.conversions / p.clicks) * 100).toFixed(2)),
      cpc: parseFloat((p.spend / p.clicks).toFixed(2)),
      cpa: parseFloat((p.spend / p.conversions).toFixed(2)),
      efficiency_score: parseFloat((p.roas * 100 / (p.spend / 1000)).toFixed(2))
    }));

    // Rank platforms
    platformData.sort((a, b) => b.roas - a.roas);
    const ranked = platformData.map((p, idx) => ({
      ...p,
      rank: idx + 1,
      badge: idx === 0 ? 'Best ROAS' : idx === 1 ? 'Best Volume' : 'Growth Potential'
    }));

    res.json({
      platforms: ranked,
      insights: [
        {
          type: 'success',
          message: `${ranked[0].platform} is your top performer with ${ranked[0].roas}x ROAS`,
          priority: 'high'
        },
        {
          type: 'info',
          message: `${ranked[2].platform} shows 35% growth opportunity with optimization`,
          priority: 'medium'
        },
        {
          type: 'success',
          message: 'Overall account ROAS increased 24% this month',
          priority: 'high'
        }
      ],
      demo_mode: true,
      timestamp: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('Demo performance comparison error:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/demo/live-metrics
 * Simulated live-updating metrics for presentation
 */
router.get(
  '/live-metrics',
  apiRateLimiter,
  validateInput({
    query: {
      count: { type: 'number', required: false, min: 1, max: 20 }
    }
  }),
  (req: Request, res: Response) => {
  try {
    const now = new Date();
    const campaign = demoDataGenerator.generateCampaign('successful_campaign', 1);
    const dailyMetric = campaign.daily_metrics[0];

    // Simulate "live" hour-by-hour breakdown
    const hourlyData = [];
    for (let hour = 0; hour < 24; hour++) {
      const fraction = 1 / 24;
      hourlyData.push({
        hour: `${hour.toString().padStart(2, '0')}:00`,
        impressions: Math.round(dailyMetric.impressions * fraction * (0.8 + Math.random() * 0.4)),
        clicks: Math.round(dailyMetric.clicks * fraction * (0.8 + Math.random() * 0.4)),
        conversions: Math.round(dailyMetric.conversions * fraction * (0.8 + Math.random() * 0.4)),
        spend: parseFloat((dailyMetric.spend * fraction * (0.8 + Math.random() * 0.4)).toFixed(2))
      });
    }

    res.json({
      current_hour: now.getHours(),
      hourly_breakdown: hourlyData,
      current_totals: {
        impressions: hourlyData.slice(0, now.getHours() + 1).reduce((sum, h) => sum + h.impressions, 0),
        clicks: hourlyData.slice(0, now.getHours() + 1).reduce((sum, h) => sum + h.clicks, 0),
        conversions: hourlyData.slice(0, now.getHours() + 1).reduce((sum, h) => sum + h.conversions, 0),
        spend: parseFloat(hourlyData.slice(0, now.getHours() + 1).reduce((sum, h) => sum + h.spend, 0).toFixed(2))
      },
      projected_daily: {
        impressions: dailyMetric.impressions,
        clicks: dailyMetric.clicks,
        conversions: dailyMetric.conversions,
        spend: dailyMetric.spend
      },
      demo_mode: true,
      timestamp: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('Demo live metrics error:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/demo/reset
 * Reset demo data (clear cache)
 */
router.post('/reset', apiRateLimiter, (req: Request, res: Response) => {
  try {
    demoSessions.clear();

    res.json({
      message: 'Demo data reset successfully',
      timestamp: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('Demo reset error:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/demo/presentation-stats
 * Key stats for investor presentation slides
 */
router.get('/presentation-stats', apiRateLimiter, (req: Request, res: Response) => {
  try {
    const dataset = demoDataGenerator.generateDemoDataset();
    const analytics = demoDataGenerator.generateAnalytics(30);

    // Calculate impressive headline numbers
    const totalSpend = dataset.campaigns.reduce((sum, c) => sum + c.spend, 0);
    const totalRevenue = dataset.campaigns.reduce((sum, c) => sum + c.revenue, 0);
    const avgROAS = totalRevenue / totalSpend;
    const totalConversions = dataset.campaigns.reduce((sum, c) => sum + c.conversions, 0);
    const avgCTR = dataset.campaigns.reduce((sum, c) => sum + c.ctr, 0) / dataset.campaigns.length;

    // AI Council stats
    const avgAIScore = dataset.ai_council_scores.reduce((sum, s) => sum + s.scores.overall_score, 0) / dataset.ai_council_scores.length;
    const approvalRate = (dataset.ai_council_scores.filter(s => s.scores.recommendation === 'approved').length / dataset.ai_council_scores.length) * 100;

    // A/B test stats
    const avgConfidence = dataset.ab_tests.reduce((sum, t) => sum + t.confidence, 0) / dataset.ab_tests.length;
    const totalTestSamples = dataset.ab_tests.reduce((sum, t) => sum + t.sample_size, 0);

    res.json({
      headline_metrics: {
        total_revenue: parseFloat(totalRevenue.toFixed(2)),
        average_roas: parseFloat(avgROAS.toFixed(2)),
        total_conversions: totalConversions,
        average_ctr: parseFloat(avgCTR.toFixed(2)),
        total_campaigns: dataset.campaigns.length,
        active_campaigns: dataset.campaigns.filter(c => c.status === 'active').length
      },
      ai_performance: {
        average_ai_score: parseFloat(avgAIScore.toFixed(2)),
        approval_rate: parseFloat(approvalRate.toFixed(2)),
        creatives_evaluated: dataset.ai_council_scores.length,
        high_performers: dataset.ai_council_scores.filter(s => s.scores.overall_score >= 85).length
      },
      testing_efficiency: {
        active_tests: dataset.ab_tests.length,
        average_confidence: parseFloat(avgConfidence.toFixed(2)),
        total_samples: totalTestSamples,
        clear_winners: dataset.ab_tests.filter(t => t.confidence >= 95).length
      },
      platform_reach: {
        platforms: Object.keys(analytics.platform_performance).length,
        total_impressions: analytics.overview.total_impressions,
        multi_platform_roas: analytics.overview.roas
      },
      growth_indicators: {
        month_over_month_growth: 24.5,
        roas_improvement: 18.3,
        conversion_rate_lift: 32.7,
        cost_efficiency_gain: 15.8
      },
      demo_mode: true,
      timestamp: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('Demo presentation stats error:', error);
    res.status(500).json({ error: error.message });
  }
});

export default router;
