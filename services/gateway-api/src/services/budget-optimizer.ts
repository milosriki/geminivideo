/**
 * Budget Optimizer Service
 * Agent 05 - Wire Budget Reallocation
 *
 * Automatically reallocates budget from underperforming ads to high-performing ones
 * based on ROAS (Return on Ad Spend) metrics.
 *
 * Budget Rules:
 * - Winners (ROAS >= 2x): Increase budget by 50%
 * - Average (ROAS 1-2x): Keep budget unchanged
 * - Losers (ROAS < 1x, spend > $50): Decrease budget by 50%
 * - Very Losers (ROAS < 0.5x): Pause ad
 */

import axios from 'axios';
import { logger } from '../utils/logger';
import { db } from './database';

/**
 * Campaign performance metrics used for budget optimization
 */
export interface CampaignMetrics {
  campaignId: string;
  adId: string;
  roas: number;
  spend: number;
  revenue: number;
  currentBudget: number;
  impressions: number;
  clicks: number;
  conversions: number;
  status: string;
}

/**
 * Budget change recommendation
 */
export interface BudgetChange {
  adId: string;
  campaignId: string;
  currentBudget: number;
  newBudget: number;
  reason: string;
  action: 'increase' | 'decrease' | 'pause' | 'keep';
  roasCategory: 'winner' | 'average' | 'loser' | 'very-loser';
  metrics: {
    roas: number;
    spend: number;
    revenue: number;
  };
}

/**
 * Budget reallocation summary
 */
export interface ReallocationSummary {
  accountId: string;
  timestamp: Date;
  totalCampaigns: number;
  changes: BudgetChange[];
  summary: {
    winners: number;
    average: number;
    losers: number;
    veryLosers: number;
    totalBudgetBefore: number;
    totalBudgetAfter: number;
    budgetShift: number;
  };
}

/**
 * Budget Optimizer - Automatic budget reallocation engine
 */
export class BudgetOptimizer {
  private metaApiUrl = process.env.META_PUBLISHER_URL || 'http://localhost:8003';
  private minSpendThreshold = 50; // Minimum spend to consider for budget changes
  private winnerRoasThreshold = 2.0; // ROAS >= 2x
  private averageRoasThreshold = 1.0; // ROAS >= 1x
  private loserRoasThreshold = 0.5; // ROAS < 0.5x for very losers

  /**
   * Main budget reallocation function
   * Analyzes all campaigns for an account and reallocates budget
   */
  async reallocateBudget(accountId: string): Promise<ReallocationSummary> {
    logger.info(`Starting budget reallocation for account ${accountId}`);

    try {
      // Get all active campaigns with metrics
      const campaigns = await this.getActiveCampaigns(accountId);

      if (campaigns.length === 0) {
        logger.warn(`No active campaigns found for account ${accountId}`);
        return this.createEmptySummary(accountId);
      }

      logger.info(`Found ${campaigns.length} active campaigns for analysis`);

      // Categorize campaigns by performance
      const winners: CampaignMetrics[] = [];
      const average: CampaignMetrics[] = [];
      const losers: CampaignMetrics[] = [];
      const veryLosers: CampaignMetrics[] = [];

      for (const campaign of campaigns) {
        if (campaign.roas >= this.winnerRoasThreshold) {
          winners.push(campaign);
        } else if (campaign.roas >= this.averageRoasThreshold) {
          average.push(campaign);
        } else if (campaign.roas >= this.loserRoasThreshold && campaign.spend > this.minSpendThreshold) {
          losers.push(campaign);
        } else if (campaign.roas < this.loserRoasThreshold && campaign.spend > this.minSpendThreshold) {
          veryLosers.push(campaign);
        } else {
          // Low spend campaigns that don't meet threshold - keep as average
          average.push(campaign);
        }
      }

      logger.info(`Campaign categorization: Winners=${winners.length}, Average=${average.length}, Losers=${losers.length}, VeryLosers=${veryLosers.length}`);

      // Calculate budget changes
      const changes = this.calculateBudgetChanges(winners, average, losers, veryLosers);

      // Calculate totals
      const totalBudgetBefore = campaigns.reduce((sum, c) => sum + c.currentBudget, 0);
      const totalBudgetAfter = changes.reduce((sum, c) => sum + c.newBudget, 0);

      // Create summary
      const summary: ReallocationSummary = {
        accountId,
        timestamp: new Date(),
        totalCampaigns: campaigns.length,
        changes,
        summary: {
          winners: winners.length,
          average: average.length,
          losers: losers.length,
          veryLosers: veryLosers.length,
          totalBudgetBefore,
          totalBudgetAfter,
          budgetShift: totalBudgetAfter - totalBudgetBefore
        }
      };

      logger.info(`Budget reallocation complete: ${changes.length} changes recommended`, {
        totalBudgetBefore,
        totalBudgetAfter,
        budgetShift: summary.summary.budgetShift
      });

      return summary;

    } catch (error) {
      logger.error('Error during budget reallocation', {
        accountId,
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  /**
   * Calculate budget changes for all campaigns
   */
  private calculateBudgetChanges(
    winners: CampaignMetrics[],
    average: CampaignMetrics[],
    losers: CampaignMetrics[],
    veryLosers: CampaignMetrics[]
  ): BudgetChange[] {
    const changes: BudgetChange[] = [];

    // Winners: Increase budget by 50%
    for (const winner of winners) {
      changes.push({
        adId: winner.adId,
        campaignId: winner.campaignId,
        currentBudget: winner.currentBudget,
        newBudget: winner.currentBudget * 1.5,
        reason: `High performer - ROAS ${winner.roas.toFixed(2)}x exceeds 2x threshold`,
        action: 'increase',
        roasCategory: 'winner',
        metrics: {
          roas: winner.roas,
          spend: winner.spend,
          revenue: winner.revenue
        }
      });
    }

    // Average: Keep budget unchanged
    for (const avg of average) {
      changes.push({
        adId: avg.adId,
        campaignId: avg.campaignId,
        currentBudget: avg.currentBudget,
        newBudget: avg.currentBudget,
        reason: `Average performer - ROAS ${avg.roas.toFixed(2)}x is acceptable`,
        action: 'keep',
        roasCategory: 'average',
        metrics: {
          roas: avg.roas,
          spend: avg.spend,
          revenue: avg.revenue
        }
      });
    }

    // Losers: Decrease budget by 50%
    for (const loser of losers) {
      changes.push({
        adId: loser.adId,
        campaignId: loser.campaignId,
        currentBudget: loser.currentBudget,
        newBudget: loser.currentBudget * 0.5,
        reason: `Underperforming - ROAS ${loser.roas.toFixed(2)}x below 1x threshold, spent $${loser.spend.toFixed(2)}`,
        action: 'decrease',
        roasCategory: 'loser',
        metrics: {
          roas: loser.roas,
          spend: loser.spend,
          revenue: loser.revenue
        }
      });
    }

    // Very Losers: Pause ad
    for (const veryLoser of veryLosers) {
      changes.push({
        adId: veryLoser.adId,
        campaignId: veryLoser.campaignId,
        currentBudget: veryLoser.currentBudget,
        newBudget: 0,
        reason: `Critical underperformance - ROAS ${veryLoser.roas.toFixed(2)}x below 0.5x threshold, spent $${veryLoser.spend.toFixed(2)}. Pausing to prevent further losses.`,
        action: 'pause',
        roasCategory: 'very-loser',
        metrics: {
          roas: veryLoser.roas,
          spend: veryLoser.spend,
          revenue: veryLoser.revenue
        }
      });
    }

    return changes;
  }

  /**
   * Identify underperforming campaigns (losers)
   */
  identifyLosers(campaigns: CampaignMetrics[]): CampaignMetrics[] {
    return campaigns.filter(campaign => {
      // Losers: ROAS < 1x and spend > threshold
      const isLoser = campaign.roas < this.averageRoasThreshold && campaign.spend > this.minSpendThreshold;

      if (isLoser) {
        logger.info(`Identified loser campaign`, {
          campaignId: campaign.campaignId,
          adId: campaign.adId,
          roas: campaign.roas,
          spend: campaign.spend
        });
      }

      return isLoser;
    });
  }

  /**
   * Calculate optimal budget distribution for winners
   * Distributes total budget proportionally based on ROAS performance
   */
  calculateOptimalBudget(winners: CampaignMetrics[], totalBudget: number): Map<string, number> {
    const budgetMap = new Map<string, number>();

    if (winners.length === 0) {
      logger.warn('No winner campaigns to allocate budget to');
      return budgetMap;
    }

    // Calculate total weighted ROAS
    const totalWeightedRoas = winners.reduce((sum, w) => sum + w.roas, 0);

    // Distribute budget proportionally to ROAS
    for (const winner of winners) {
      const proportion = winner.roas / totalWeightedRoas;
      const allocatedBudget = totalBudget * proportion;
      budgetMap.set(winner.adId, allocatedBudget);

      logger.info(`Optimal budget allocation`, {
        adId: winner.adId,
        roas: winner.roas,
        proportion: (proportion * 100).toFixed(2) + '%',
        allocatedBudget: allocatedBudget.toFixed(2)
      });
    }

    return budgetMap;
  }

  /**
   * Apply budget changes via Meta API
   */
  async applyBudgetChanges(changes: BudgetChange[]): Promise<{
    success: number;
    failed: number;
    errors: Array<{ adId: string; error: string }>;
  }> {
    logger.info(`Applying ${changes.length} budget changes`);

    let success = 0;
    let failed = 0;
    const errors: Array<{ adId: string; error: string }> = [];

    for (const change of changes) {
      try {
        if (change.action === 'pause') {
          await this.pauseAd(change.adId);
          logger.info(`Successfully paused ad ${change.adId}`);
        } else if (change.action === 'increase' || change.action === 'decrease') {
          await this.updateBudget(change.adId, change.newBudget);
          logger.info(`Successfully updated budget for ad ${change.adId}: $${change.currentBudget} -> $${change.newBudget}`);
        }
        // 'keep' action requires no API call

        success++;

      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logger.error(`Failed to apply budget change for ad ${change.adId}`, {
          error: errorMessage,
          change
        });
        failed++;
        errors.push({
          adId: change.adId,
          error: errorMessage
        });
      }
    }

    logger.info(`Budget changes applied: ${success} successful, ${failed} failed`);

    return { success, failed, errors };
  }

  /**
   * Get all active campaigns with performance metrics
   */
  private async getActiveCampaigns(accountId: string): Promise<CampaignMetrics[]> {
    try {
      // Query campaigns with conversions and spend data
      const campaigns = await db.listCampaigns({
        where: {
          metaAccountId: accountId,
          status: 'ACTIVE',
          deletedAt: null
        }
      });

      const metricsPromises = campaigns.map(async (campaign) => {
        try {
          // Get conversions for revenue calculation
          const conversions = await db.listConversions({
            campaignId: campaign.id,
            take: 1000 // Get recent conversions
          });

          const revenue = conversions.reduce((sum, conv) => {
            return sum + Number(conv.value);
          }, 0);

          const spend = Number(campaign.totalSpend || 0);
          const roas = spend > 0 ? revenue / spend : 0;

          return {
            campaignId: campaign.id,
            adId: campaign.metaCampaignId || campaign.id,
            roas,
            spend,
            revenue,
            currentBudget: Number(campaign.dailyBudget || campaign.budget),
            impressions: Number(campaign.totalImpressions || 0),
            clicks: Number(campaign.totalClicks || 0),
            conversions: Number(campaign.totalConversions || 0),
            status: campaign.status
          } as CampaignMetrics;

        } catch (error) {
          logger.error(`Error calculating metrics for campaign ${campaign.id}`, {
            error: error instanceof Error ? error.message : String(error)
          });
          // Return campaign with zero metrics on error
          return {
            campaignId: campaign.id,
            adId: campaign.metaCampaignId || campaign.id,
            roas: 0,
            spend: 0,
            revenue: 0,
            currentBudget: Number(campaign.dailyBudget || campaign.budget),
            impressions: 0,
            clicks: 0,
            conversions: 0,
            status: campaign.status
          } as CampaignMetrics;
        }
      });

      const metrics = await Promise.all(metricsPromises);

      logger.info(`Retrieved ${metrics.length} campaigns with metrics for account ${accountId}`);

      return metrics;

    } catch (error) {
      logger.error('Error fetching active campaigns', {
        accountId,
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    }
  }

  /**
   * Update ad budget via Meta API
   */
  private async updateBudget(adId: string, newBudget: number): Promise<void> {
    try {
      const response = await axios.put(
        `${this.metaApiUrl}/api/ads/${adId}/budget`,
        {
          daily_budget: newBudget * 100 // Meta API expects budget in cents
        },
        {
          timeout: 10000,
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.status !== 200) {
        throw new Error(`Meta API returned status ${response.status}`);
      }

      logger.info(`Budget updated successfully via Meta API`, {
        adId,
        newBudget
      });

    } catch (error) {
      if (axios.isAxiosError(error)) {
        logger.error('Meta API budget update failed', {
          adId,
          newBudget,
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data
        });
        throw new Error(`Meta API error: ${error.response?.data?.message || error.message}`);
      }
      throw error;
    }
  }

  /**
   * Pause an ad via Meta API
   */
  private async pauseAd(adId: string): Promise<void> {
    try {
      const response = await axios.post(
        `${this.metaApiUrl}/api/ads/${adId}/pause`,
        {},
        {
          timeout: 10000,
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.status !== 200) {
        throw new Error(`Meta API returned status ${response.status}`);
      }

      logger.info(`Ad paused successfully via Meta API`, { adId });

    } catch (error) {
      if (axios.isAxiosError(error)) {
        logger.error('Meta API ad pause failed', {
          adId,
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data
        });
        throw new Error(`Meta API error: ${error.response?.data?.message || error.message}`);
      }
      throw error;
    }
  }

  /**
   * Create empty summary when no campaigns found
   */
  private createEmptySummary(accountId: string): ReallocationSummary {
    return {
      accountId,
      timestamp: new Date(),
      totalCampaigns: 0,
      changes: [],
      summary: {
        winners: 0,
        average: 0,
        losers: 0,
        veryLosers: 0,
        totalBudgetBefore: 0,
        totalBudgetAfter: 0,
        budgetShift: 0
      }
    };
  }
}

// Export singleton instance
export const budgetOptimizer = new BudgetOptimizer();

// Export for testing
export default budgetOptimizer;
