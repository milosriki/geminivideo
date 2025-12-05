/**
 * Demo Data Generator for Investor Presentations
 *
 * Generates realistic, impressive demo data for showcasing platform capabilities.
 * Designed to "wow" investors with €5M investment on the line.
 */

export interface DemoCampaign {
  id: string;
  name: string;
  status: 'active' | 'paused' | 'completed';
  platform: 'meta' | 'google' | 'tiktok';
  objective: 'conversions' | 'traffic' | 'awareness';

  // Impressive metrics
  impressions: number;
  clicks: number;
  conversions: number;
  spend: number;
  revenue: number;
  roas: number;
  ctr: number;
  cpc: number;
  cpa: number;

  // Time series data for charts
  daily_metrics: DailyMetric[];

  // AI Council scores
  ai_scores: {
    visual_appeal: number;
    message_clarity: number;
    engagement_potential: number;
    conversion_probability: number;
    overall_score: number;
  };

  // Meta data
  created_at: string;
  updated_at: string;
  scenario?: DemoScenario;
}

export interface DailyMetric {
  date: string;
  impressions: number;
  clicks: number;
  conversions: number;
  spend: number;
  revenue: number;
  roas: number;
  ctr: number;
}

export type DemoScenario =
  | 'successful_campaign'
  | 'optimizing_campaign'
  | 'ab_test_winner'
  | 'scaling_success';

export interface DemoABTest {
  id: string;
  name: string;
  status: 'running' | 'completed';
  variants: DemoVariant[];
  winner?: string;
  confidence: number;
  sample_size: number;
  created_at: string;
}

export interface DemoVariant {
  id: string;
  name: string;
  impressions: number;
  clicks: number;
  conversions: number;
  spend: number;
  revenue: number;
  ctr: number;
  cvr: number;
  roas: number;
  alpha: number; // Thompson Sampling
  beta: number;  // Thompson Sampling
  win_probability: number;
}

export interface DemoAICouncilScore {
  creative_id: string;
  timestamp: string;
  scores: {
    director: {
      visual_composition: number;
      storytelling: number;
      brand_alignment: number;
      overall: number;
    };
    oracle: {
      predicted_ctr: number;
      predicted_cvr: number;
      predicted_roas: number;
      confidence: number;
    };
    strategist: {
      audience_fit: number;
      timing: number;
      competitive_edge: number;
      overall: number;
    };
    overall_score: number;
    recommendation: 'approved' | 'needs_work' | 'rejected';
  };
}

export class DemoDataGenerator {
  private randomSeed: number = Date.now();

  /**
   * Seeded random number generator for consistent demo data
   */
  private seededRandom(seed?: number): number {
    if (seed !== undefined) this.randomSeed = seed;
    const x = Math.sin(this.randomSeed++) * 10000;
    return x - Math.floor(x);
  }

  /**
   * Generate random number in range with optional seed
   */
  private random(min: number, max: number, seed?: number): number {
    const rand = seed !== undefined ? this.seededRandom(seed) : Math.random();
    return min + rand * (max - min);
  }

  /**
   * Generate random integer in range
   */
  private randomInt(min: number, max: number, seed?: number): number {
    return Math.floor(this.random(min, max, seed));
  }

  /**
   * Generate realistic time series data with trends
   */
  private generateTimeSeries(
    days: number,
    baseValue: number,
    trend: 'up' | 'down' | 'stable' | 'volatile',
    volatility: number = 0.1
  ): number[] {
    const data: number[] = [];
    let value = baseValue;

    for (let i = 0; i < days; i++) {
      // Apply trend
      if (trend === 'up') {
        value *= 1 + this.random(0.01, 0.05);
      } else if (trend === 'down') {
        value *= 1 - this.random(0.01, 0.03);
      } else if (trend === 'volatile') {
        value *= 1 + this.random(-0.1, 0.15);
      }

      // Add noise
      const noise = 1 + this.random(-volatility, volatility);
      data.push(Math.max(0, value * noise));
    }

    return data;
  }

  /**
   * Generate daily metrics with realistic patterns
   */
  private generateDailyMetrics(
    days: number,
    scenario: DemoScenario,
    budget: number
  ): DailyMetric[] {
    const metrics: DailyMetric[] = [];
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    // Define patterns based on scenario
    let impressionsTrend: 'up' | 'down' | 'stable' | 'volatile' = 'stable';
    let roasTrend: 'up' | 'down' | 'stable' | 'volatile' = 'stable';
    let baseCTR = 0.02;
    let baseCVR = 0.03;

    switch (scenario) {
      case 'successful_campaign':
        impressionsTrend = 'up';
        roasTrend = 'stable';
        baseCTR = 0.04; // High CTR
        baseCVR = 0.05; // High CVR
        break;
      case 'optimizing_campaign':
        impressionsTrend = 'stable';
        roasTrend = 'up';
        baseCTR = 0.025;
        baseCVR = 0.035;
        break;
      case 'ab_test_winner':
        impressionsTrend = 'stable';
        roasTrend = 'up';
        baseCTR = 0.038;
        baseCVR = 0.045;
        break;
      case 'scaling_success':
        impressionsTrend = 'up';
        roasTrend = 'stable';
        baseCTR = 0.035;
        baseCVR = 0.042;
        break;
    }

    // Generate time series
    const dailySpend = budget / days;
    const impressionsSeries = this.generateTimeSeries(days, 50000, impressionsTrend, 0.15);
    const ctrSeries = this.generateTimeSeries(days, baseCTR, roasTrend === 'up' ? 'up' : 'stable', 0.05);
    const cvrSeries = this.generateTimeSeries(days, baseCVR, roasTrend === 'up' ? 'up' : 'stable', 0.05);

    for (let i = 0; i < days; i++) {
      const date = new Date(startDate);
      date.setDate(date.getDate() + i);

      const impressions = Math.round(impressionsSeries[i]);
      const ctr = Math.min(0.1, Math.max(0.01, ctrSeries[i]));
      const cvr = Math.min(0.15, Math.max(0.01, cvrSeries[i]));
      const clicks = Math.round(impressions * ctr);
      const conversions = Math.round(clicks * cvr);
      const spend = dailySpend * (1 + this.random(-0.1, 0.1));
      const aov = 150 + this.random(-20, 50); // Average Order Value
      const revenue = conversions * aov;
      const roas = revenue / spend;

      metrics.push({
        date: date.toISOString().split('T')[0],
        impressions,
        clicks,
        conversions,
        spend: parseFloat(spend.toFixed(2)),
        revenue: parseFloat(revenue.toFixed(2)),
        roas: parseFloat(roas.toFixed(2)),
        ctr: parseFloat((ctr * 100).toFixed(2))
      });
    }

    return metrics;
  }

  /**
   * Generate a demo campaign with specified scenario
   */
  generateCampaign(scenario: DemoScenario, days: number = 30): DemoCampaign {
    const id = `demo-campaign-${this.randomInt(1000, 9999)}`;
    const budget = this.random(5000, 25000);
    const dailyMetrics = this.generateDailyMetrics(days, scenario, budget);

    // Aggregate metrics
    const totals = dailyMetrics.reduce(
      (acc, day) => ({
        impressions: acc.impressions + day.impressions,
        clicks: acc.clicks + day.clicks,
        conversions: acc.conversions + day.conversions,
        spend: acc.spend + day.spend,
        revenue: acc.revenue + day.revenue
      }),
      { impressions: 0, clicks: 0, conversions: 0, spend: 0, revenue: 0 }
    );

    const avgCTR = (totals.clicks / totals.impressions) * 100;
    const roas = totals.revenue / totals.spend;
    const cpc = totals.spend / totals.clicks;
    const cpa = totals.spend / totals.conversions;

    // Generate AI Council scores based on performance
    const baseScore = scenario === 'successful_campaign' ? 85 :
                     scenario === 'ab_test_winner' ? 90 :
                     scenario === 'scaling_success' ? 88 : 75;

    const ai_scores = {
      visual_appeal: baseScore + this.random(-5, 5),
      message_clarity: baseScore + this.random(-5, 5),
      engagement_potential: baseScore + this.random(-5, 5),
      conversion_probability: baseScore + this.random(-5, 5),
      overall_score: 0
    };
    ai_scores.overall_score = (
      ai_scores.visual_appeal +
      ai_scores.message_clarity +
      ai_scores.engagement_potential +
      ai_scores.conversion_probability
    ) / 4;

    const names = {
      successful_campaign: 'Summer Sale Blowout 🔥',
      optimizing_campaign: 'Q4 Product Launch',
      ab_test_winner: 'Black Friday Winner',
      scaling_success: 'New Customer Acquisition'
    };

    return {
      id,
      name: names[scenario],
      status: 'active',
      platform: ['meta', 'google', 'tiktok'][this.randomInt(0, 3)] as any,
      objective: 'conversions',
      impressions: totals.impressions,
      clicks: totals.clicks,
      conversions: totals.conversions,
      spend: parseFloat(totals.spend.toFixed(2)),
      revenue: parseFloat(totals.revenue.toFixed(2)),
      roas: parseFloat(roas.toFixed(2)),
      ctr: parseFloat(avgCTR.toFixed(2)),
      cpc: parseFloat(cpc.toFixed(2)),
      cpa: parseFloat(cpa.toFixed(2)),
      daily_metrics: dailyMetrics,
      ai_scores,
      created_at: new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date().toISOString(),
      scenario
    };
  }

  /**
   * Generate impressive A/B test with clear winner
   */
  generateABTest(): DemoABTest {
    const id = `demo-ab-${this.randomInt(1000, 9999)}`;
    const sampleSize = this.randomInt(50000, 150000);

    // Variant A (Control) - Good performance
    const variantA: DemoVariant = {
      id: `${id}-a`,
      name: 'Control: Original Creative',
      impressions: Math.round(sampleSize * 0.5),
      clicks: 0,
      conversions: 0,
      spend: 0,
      revenue: 0,
      ctr: 2.8,
      cvr: 3.2,
      roas: 2.5,
      alpha: 0,
      beta: 0,
      win_probability: 0.15
    };
    variantA.clicks = Math.round(variantA.impressions * (variantA.ctr / 100));
    variantA.conversions = Math.round(variantA.clicks * (variantA.cvr / 100));
    variantA.spend = variantA.clicks * 0.5;
    variantA.revenue = variantA.conversions * 150;
    variantA.roas = variantA.revenue / variantA.spend;
    variantA.alpha = variantA.clicks + 1;
    variantA.beta = (variantA.impressions - variantA.clicks) + 1;

    // Variant B (Winner) - Significantly better
    const variantB: DemoVariant = {
      id: `${id}-b`,
      name: 'Variant B: AI-Optimized Hook',
      impressions: Math.round(sampleSize * 0.5),
      clicks: 0,
      conversions: 0,
      spend: 0,
      revenue: 0,
      ctr: 4.2, // 50% better CTR
      cvr: 4.8, // 50% better CVR
      roas: 3.8, // 52% better ROAS
      alpha: 0,
      beta: 0,
      win_probability: 0.85
    };
    variantB.clicks = Math.round(variantB.impressions * (variantB.ctr / 100));
    variantB.conversions = Math.round(variantB.clicks * (variantB.cvr / 100));
    variantB.spend = variantB.clicks * 0.5;
    variantB.revenue = variantB.conversions * 150;
    variantB.roas = variantB.revenue / variantB.spend;
    variantB.alpha = variantB.clicks + 1;
    variantB.beta = (variantB.impressions - variantB.clicks) + 1;

    return {
      id,
      name: 'Creative Hook Test - Nov 2024',
      status: 'running',
      variants: [variantA, variantB],
      winner: variantB.id,
      confidence: 95.3,
      sample_size: sampleSize,
      created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
    };
  }

  /**
   * Generate AI Council evaluation score
   */
  generateAICouncilScore(predictedPerformance: 'high' | 'medium' | 'low' = 'high'): DemoAICouncilScore {
    const baseScores = {
      high: { min: 85, max: 95 },
      medium: { min: 70, max: 84 },
      low: { min: 50, max: 69 }
    };

    const range = baseScores[predictedPerformance];

    const directorScores = {
      visual_composition: this.random(range.min, range.max),
      storytelling: this.random(range.min, range.max),
      brand_alignment: this.random(range.min, range.max),
      overall: 0
    };
    directorScores.overall = (
      directorScores.visual_composition +
      directorScores.storytelling +
      directorScores.brand_alignment
    ) / 3;

    const oracleScores = {
      predicted_ctr: predictedPerformance === 'high' ? this.random(3.5, 5.5) :
                     predictedPerformance === 'medium' ? this.random(2.0, 3.4) :
                     this.random(1.0, 1.9),
      predicted_cvr: predictedPerformance === 'high' ? this.random(4.0, 6.0) :
                     predictedPerformance === 'medium' ? this.random(2.5, 3.9) :
                     this.random(1.5, 2.4),
      predicted_roas: predictedPerformance === 'high' ? this.random(3.0, 4.5) :
                      predictedPerformance === 'medium' ? this.random(2.0, 2.9) :
                      this.random(1.0, 1.9),
      confidence: this.random(range.min - 5, range.max)
    };

    const strategistScores = {
      audience_fit: this.random(range.min, range.max),
      timing: this.random(range.min, range.max),
      competitive_edge: this.random(range.min, range.max),
      overall: 0
    };
    strategistScores.overall = (
      strategistScores.audience_fit +
      strategistScores.timing +
      strategistScores.competitive_edge
    ) / 3;

    const overall_score = (
      directorScores.overall +
      strategistScores.overall +
      oracleScores.confidence
    ) / 3;

    return {
      creative_id: `demo-creative-${this.randomInt(1000, 9999)}`,
      timestamp: new Date().toISOString(),
      scores: {
        director: directorScores,
        oracle: oracleScores,
        strategist: strategistScores,
        overall_score,
        recommendation: overall_score >= 85 ? 'approved' :
                       overall_score >= 70 ? 'needs_work' : 'rejected'
      }
    };
  }

  /**
   * Generate a complete demo dataset
   */
  generateDemoDataset() {
    return {
      campaigns: [
        this.generateCampaign('successful_campaign', 30),
        this.generateCampaign('optimizing_campaign', 21),
        this.generateCampaign('ab_test_winner', 14),
        this.generateCampaign('scaling_success', 45)
      ],
      ab_tests: [
        this.generateABTest(),
        this.generateABTest(),
        this.generateABTest()
      ],
      ai_council_scores: [
        this.generateAICouncilScore('high'),
        this.generateAICouncilScore('high'),
        this.generateAICouncilScore('medium'),
        this.generateAICouncilScore('high')
      ],
      summary: {
        total_campaigns: 4,
        total_spend: 0,
        total_revenue: 0,
        avg_roas: 0,
        total_conversions: 0,
        platform_distribution: {
          meta: 0,
          google: 0,
          tiktok: 0
        }
      }
    };
  }

  /**
   * Generate analytics data for dashboard
   */
  generateAnalytics(days: number = 30) {
    const dailyData = this.generateDailyMetrics(days, 'successful_campaign', 20000);

    const totals = dailyData.reduce(
      (acc, day) => ({
        impressions: acc.impressions + day.impressions,
        clicks: acc.clicks + day.clicks,
        conversions: acc.conversions + day.conversions,
        spend: acc.spend + day.spend,
        revenue: acc.revenue + day.revenue
      }),
      { impressions: 0, clicks: 0, conversions: 0, spend: 0, revenue: 0 }
    );

    return {
      overview: {
        total_impressions: totals.impressions,
        total_clicks: totals.clicks,
        total_conversions: totals.conversions,
        total_spend: parseFloat(totals.spend.toFixed(2)),
        total_revenue: parseFloat(totals.revenue.toFixed(2)),
        roas: parseFloat((totals.revenue / totals.spend).toFixed(2)),
        avg_ctr: parseFloat(((totals.clicks / totals.impressions) * 100).toFixed(2)),
        avg_cpc: parseFloat((totals.spend / totals.clicks).toFixed(2)),
        avg_cpa: parseFloat((totals.spend / totals.conversions).toFixed(2))
      },
      daily_breakdown: dailyData,
      platform_performance: [
        {
          platform: 'Meta',
          impressions: Math.round(totals.impressions * 0.45),
          clicks: Math.round(totals.clicks * 0.48),
          conversions: Math.round(totals.conversions * 0.52),
          spend: parseFloat((totals.spend * 0.45).toFixed(2)),
          revenue: parseFloat((totals.revenue * 0.52).toFixed(2)),
          roas: parseFloat(((totals.revenue * 0.52) / (totals.spend * 0.45)).toFixed(2))
        },
        {
          platform: 'Google',
          impressions: Math.round(totals.impressions * 0.35),
          clicks: Math.round(totals.clicks * 0.32),
          conversions: Math.round(totals.conversions * 0.30),
          spend: parseFloat((totals.spend * 0.35).toFixed(2)),
          revenue: parseFloat((totals.revenue * 0.30).toFixed(2)),
          roas: parseFloat(((totals.revenue * 0.30) / (totals.spend * 0.35)).toFixed(2))
        },
        {
          platform: 'TikTok',
          impressions: Math.round(totals.impressions * 0.20),
          clicks: Math.round(totals.clicks * 0.20),
          conversions: Math.round(totals.conversions * 0.18),
          spend: parseFloat((totals.spend * 0.20).toFixed(2)),
          revenue: parseFloat((totals.revenue * 0.18).toFixed(2)),
          roas: parseFloat(((totals.revenue * 0.18) / (totals.spend * 0.20)).toFixed(2))
        }
      ]
    };
  }
}

// Export singleton instance
export const demoDataGenerator = new DemoDataGenerator();
