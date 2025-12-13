import { logger } from '../utils/logger';

interface Winner {
  id: string;
  creative: {
    type: 'video' | 'image';
    hookType: string;
    visualStyle: string;
    duration?: number;
    cta: string;
  };
  targeting: {
    ageRange: string;
    interests: string[];
    lookalike?: boolean;
  };
  performance: {
    roas: number;
    ctr: number;
  };
}

interface Insights {
  topHooks: { hookType: string; avgROAS: number; count: number }[];
  topVisuals: { visualStyle: string; avgROAS: number; count: number }[];
  optimalDuration: { range: string; avgROAS: number }[];
  topAudiences: { targeting: string; avgROAS: number; count: number }[];
  topCTAs: { cta: string; avgCTR: number; count: number }[];
  recommendations: string[];
}

export class InsightsExtractor {

  /**
   * Main extraction logic - analyzes winning ads and extracts actionable insights
   */
  async extractInsights(winners: Winner[]): Promise<Insights> {
    logger.info(`Extracting insights from ${winners.length} winners`);

    if (winners.length === 0) {
      logger.warn('No winners provided for insight extraction');
      return {
        topHooks: [],
        topVisuals: [],
        optimalDuration: [],
        topAudiences: [],
        topCTAs: [],
        recommendations: ['No data available - need more winning ads to generate insights']
      };
    }

    const insights: Insights = {
      topHooks: await this.analyzeHookPatterns(winners),
      topVisuals: await this.analyzeVisualPatterns(winners),
      optimalDuration: await this.analyzeDuration(winners),
      topAudiences: await this.analyzeAudiencePatterns(winners),
      topCTAs: await this.analyzeCTAPatterns(winners),
      recommendations: []
    };

    // Generate recommendations based on insights
    insights.recommendations = this.generateRecommendations(insights);

    logger.info('Insights extraction complete', {
      hooksAnalyzed: insights.topHooks.length,
      visualsAnalyzed: insights.topVisuals.length,
      recommendationsGenerated: insights.recommendations.length
    });

    return insights;
  }

  /**
   * Analyzes what hook types work best
   */
  async analyzeHookPatterns(winners: Winner[]): Promise<{ hookType: string; avgROAS: number; count: number }[]> {
    logger.info('Analyzing hook patterns');

    const hookStats = new Map<string, { totalROAS: number; count: number }>();

    for (const winner of winners) {
      const hook = winner.creative.hookType;
      const stats = hookStats.get(hook) || { totalROAS: 0, count: 0 };
      stats.totalROAS += winner.performance.roas;
      stats.count += 1;
      hookStats.set(hook, stats);
    }

    const topHooks = Array.from(hookStats.entries())
      .map(([hookType, stats]) => ({
        hookType,
        avgROAS: stats.totalROAS / stats.count,
        count: stats.count
      }))
      .sort((a, b) => b.avgROAS - a.avgROAS)
      .slice(0, 5);

    logger.info(`Found ${topHooks.length} top-performing hook types`);

    return topHooks;
  }

  /**
   * Analyzes what visual styles work best
   */
  async analyzeVisualPatterns(winners: Winner[]): Promise<{ visualStyle: string; avgROAS: number; count: number }[]> {
    logger.info('Analyzing visual patterns');

    const visualStats = new Map<string, { totalROAS: number; count: number }>();

    for (const winner of winners) {
      const style = winner.creative.visualStyle;
      const stats = visualStats.get(style) || { totalROAS: 0, count: 0 };
      stats.totalROAS += winner.performance.roas;
      stats.count += 1;
      visualStats.set(style, stats);
    }

    const topVisuals = Array.from(visualStats.entries())
      .map(([visualStyle, stats]) => ({
        visualStyle,
        avgROAS: stats.totalROAS / stats.count,
        count: stats.count
      }))
      .sort((a, b) => b.avgROAS - a.avgROAS)
      .slice(0, 5);

    logger.info(`Found ${topVisuals.length} top-performing visual styles`);

    return topVisuals;
  }

  /**
   * Analyzes optimal video lengths
   */
  private async analyzeDuration(winners: Winner[]): Promise<{ range: string; avgROAS: number }[]> {
    logger.info('Analyzing video duration patterns');

    const videoWinners = winners.filter(w => w.creative.type === 'video' && w.creative.duration);

    if (videoWinners.length === 0) {
      logger.warn('No video winners with duration data found');
      return [];
    }

    const ranges = [
      { range: '0-15s', min: 0, max: 15 },
      { range: '15-30s', min: 15, max: 30 },
      { range: '30-60s', min: 30, max: 60 },
      { range: '60+s', min: 60, max: Infinity }
    ];

    const durationInsights = ranges.map(r => {
      const inRange = videoWinners.filter(w =>
        w.creative.duration! >= r.min && w.creative.duration! < r.max
      );
      return {
        range: r.range,
        avgROAS: inRange.length > 0
          ? inRange.reduce((sum, w) => sum + w.performance.roas, 0) / inRange.length
          : 0,
        count: inRange.length
      };
    }).filter(d => d.count > 0);

    logger.info(`Analyzed ${videoWinners.length} video winners across ${durationInsights.length} duration ranges`);

    return durationInsights;
  }

  /**
   * Analyzes what audience targeting works best
   */
  async analyzeAudiencePatterns(winners: Winner[]): Promise<{ targeting: string; avgROAS: number; count: number }[]> {
    logger.info('Analyzing audience patterns');

    const audienceStats = new Map<string, { totalROAS: number; count: number }>();

    for (const winner of winners) {
      const key = winner.targeting.lookalike
        ? 'Lookalike'
        : `${winner.targeting.ageRange} (${winner.targeting.interests.slice(0, 2).join(', ')})`;

      const stats = audienceStats.get(key) || { totalROAS: 0, count: 0 };
      stats.totalROAS += winner.performance.roas;
      stats.count += 1;
      audienceStats.set(key, stats);
    }

    const topAudiences = Array.from(audienceStats.entries())
      .map(([targeting, stats]) => ({
        targeting,
        avgROAS: stats.totalROAS / stats.count,
        count: stats.count
      }))
      .sort((a, b) => b.avgROAS - a.avgROAS);

    logger.info(`Found ${topAudiences.length} audience segments`);

    return topAudiences;
  }

  /**
   * Analyzes CTA performance patterns
   */
  private async analyzeCTAPatterns(winners: Winner[]): Promise<{ cta: string; avgCTR: number; count: number }[]> {
    logger.info('Analyzing CTA patterns');

    const ctaStats = new Map<string, { totalCTR: number; count: number }>();

    for (const winner of winners) {
      const cta = winner.creative.cta;
      const stats = ctaStats.get(cta) || { totalCTR: 0, count: 0 };
      stats.totalCTR += winner.performance.ctr;
      stats.count += 1;
      ctaStats.set(cta, stats);
    }

    const topCTAs = Array.from(ctaStats.entries())
      .map(([cta, stats]) => ({
        cta,
        avgCTR: stats.totalCTR / stats.count,
        count: stats.count
      }))
      .sort((a, b) => b.avgCTR - a.avgCTR)
      .slice(0, 5);

    logger.info(`Found ${topCTAs.length} top-performing CTAs`);

    return topCTAs;
  }

  /**
   * Generates actionable recommendations based on insights
   */
  private generateRecommendations(insights: Insights): string[] {
    logger.info('Generating recommendations');

    const recommendations: string[] = [];

    // Hook recommendations
    if (insights.topHooks.length > 0) {
      const topHook = insights.topHooks[0];
      recommendations.push(
        `Use "${topHook.hookType}" hooks - ${topHook.avgROAS.toFixed(1)}x avg ROAS (${topHook.count} winners)`
      );

      if (insights.topHooks.length > 1) {
        recommendations.push(
          `Alternative: "${insights.topHooks[1].hookType}" hooks - ${insights.topHooks[1].avgROAS.toFixed(1)}x avg ROAS`
        );
      }
    }

    // Visual style recommendations
    if (insights.topVisuals.length > 0) {
      const topVisual = insights.topVisuals[0];
      recommendations.push(
        `Focus on "${topVisual.visualStyle}" visual style - ${topVisual.avgROAS.toFixed(1)}x avg ROAS`
      );
    }

    // Duration recommendations
    if (insights.optimalDuration.length > 0) {
      const bestDuration = [...insights.optimalDuration].sort((a, b) => b.avgROAS - a.avgROAS)[0];
      if (bestDuration && bestDuration.avgROAS > 0) {
        recommendations.push(
          `Keep videos ${bestDuration.range} for best ROAS (${bestDuration.avgROAS.toFixed(1)}x avg)`
        );
      }
    }

    // Audience recommendations
    if (insights.topAudiences.length > 0) {
      const topAudience = insights.topAudiences[0];
      recommendations.push(
        `Target "${topAudience.targeting}" audience - ${topAudience.avgROAS.toFixed(1)}x avg ROAS`
      );
    }

    // CTA recommendations
    if (insights.topCTAs.length > 0) {
      const topCTA = insights.topCTAs[0];
      recommendations.push(
        `Use "${topCTA.cta}" CTA - ${(topCTA.avgCTR * 100).toFixed(2)}% avg CTR`
      );
    }

    // Meta recommendation based on sample size
    if (insights.topHooks.length > 0 && insights.topHooks[0].count < 5) {
      recommendations.push(
        'Note: Small sample size - continue testing to validate patterns'
      );
    }

    logger.info(`Generated ${recommendations.length} recommendations`);

    return recommendations;
  }

  /**
   * Generates a formatted markdown report of insights
   */
  async generateReport(insights: Insights): Promise<string> {
    logger.info('Generating insights report');

    let report = '# Winner Insights Report\n\n';
    report += `Generated: ${new Date().toISOString()}\n\n`;

    // Top Hooks Section
    report += '## Top Performing Hooks\n\n';
    if (insights.topHooks.length > 0) {
      for (const hook of insights.topHooks) {
        report += `- **${hook.hookType}**: ${hook.avgROAS.toFixed(2)}x ROAS (${hook.count} winners)\n`;
      }
    } else {
      report += 'No hook data available\n';
    }

    // Top Visual Styles Section
    report += '\n## Top Performing Visual Styles\n\n';
    if (insights.topVisuals.length > 0) {
      for (const visual of insights.topVisuals) {
        report += `- **${visual.visualStyle}**: ${visual.avgROAS.toFixed(2)}x ROAS (${visual.count} winners)\n`;
      }
    } else {
      report += 'No visual style data available\n';
    }

    // Optimal Duration Section
    report += '\n## Optimal Video Duration\n\n';
    if (insights.optimalDuration.length > 0) {
      const sorted = [...insights.optimalDuration].sort((a, b) => b.avgROAS - a.avgROAS);
      for (const duration of sorted) {
        report += `- **${duration.range}**: ${duration.avgROAS.toFixed(2)}x ROAS\n`;
      }
    } else {
      report += 'No duration data available\n';
    }

    // Top Audiences Section
    report += '\n## Top Performing Audiences\n\n';
    if (insights.topAudiences.length > 0) {
      for (const audience of insights.topAudiences.slice(0, 5)) {
        report += `- **${audience.targeting}**: ${audience.avgROAS.toFixed(2)}x ROAS (${audience.count} winners)\n`;
      }
    } else {
      report += 'No audience data available\n';
    }

    // Top CTAs Section
    report += '\n## Top Performing CTAs\n\n';
    if (insights.topCTAs.length > 0) {
      for (const cta of insights.topCTAs) {
        report += `- **${cta.cta}**: ${(cta.avgCTR * 100).toFixed(2)}% CTR (${cta.count} winners)\n`;
      }
    } else {
      report += 'No CTA data available\n';
    }

    // Recommendations Section
    report += '\n## Actionable Recommendations\n\n';
    if (insights.recommendations.length > 0) {
      for (const rec of insights.recommendations) {
        report += `- ${rec}\n`;
      }
    } else {
      report += 'No recommendations available\n';
    }

    report += '\n---\n\n';
    report += '*This report is generated from winning ad performance data. Continue testing to validate and refine these insights.*\n';

    logger.info('Report generation complete');

    return report;
  }
}

// Export singleton instance
export const insightsExtractor = new InsightsExtractor();
