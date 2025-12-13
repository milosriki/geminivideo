/**
 * Winner Replicator Service
 * Automatically replicates winning ads with strategic variations
 *
 * Variation Types:
 * 1. Audience: Same creative, different targeting (lookalikes, expanded demographics)
 * 2. Hook: Same creative, different hooks (3 AI-generated variations)
 * 3. Placement: Same creative, different placements (Feed, Stories, Reels)
 * 4. Budget: Scaled budget based on winner performance
 */

import axios, { AxiosError } from 'axios';
import { logger } from '../utils/logger';

// Types
interface Winner {
  id: string;
  adId: string;
  campaignId?: string;
  adSetId?: string;
  creative: {
    videoUrl?: string;
    imageUrl?: string;
    headline: string;
    primaryText: string;
    description?: string;
    callToAction: string;
  };
  targeting: {
    ageMin: number;
    ageMax: number;
    genders: number[]; // 1: male, 2: female
    locations: string[];
    interests?: string[];
    lookalike?: {
      sourceAudienceId: string;
      ratio: number; // 1-10
    };
  };
  placements?: string[];
  performance: {
    roas: number;
    ctr: number;
    spend: number;
    conversions: number;
    cpc: number;
    cpm: number;
  };
  budget: {
    dailyBudget: number;
    lifetimeBudget?: number;
  };
}

interface ReplicaConfig {
  variationType: 'audience' | 'hook' | 'placement' | 'budget';
  budgetMultiplier?: number;
  hookVariationCount?: number;
}

interface Replica {
  originalWinnerId: string;
  variationType: string;
  creative: any;
  targeting: any;
  placements?: string[];
  budget: any;
  metadata: {
    createdAt: string;
    parentAdId: string;
    variationDetails: string;
  };
}

interface HookVariation {
  originalHook: string;
  newHook: string;
  strategy: string;
  reasoning: string;
}

/**
 * Winner Replicator Class
 * Creates and publishes variations of winning ads
 */
export class WinnerReplicator {
  private metaPublisherUrl: string;
  private geminiUrl: string;

  constructor() {
    this.metaPublisherUrl = process.env.META_PUBLISHER_URL || 'http://localhost:8003';
    this.geminiUrl = process.env.GEMINI_SERVICE_URL || 'http://localhost:8001';

    logger.info('WinnerReplicator initialized', {
      metaPublisherUrl: this.metaPublisherUrl,
      geminiUrl: this.geminiUrl,
    });
  }

  /**
   * Main replication function
   * Creates multiple replicas of a winning ad with different variations
   */
  async replicateWinner(winner: Winner, configs: ReplicaConfig[]): Promise<any[]> {
    logger.info('Starting winner replication', {
      winnerId: winner.id,
      adId: winner.adId,
      configCount: configs.length,
      roas: winner.performance.roas,
    });

    const replicas: any[] = [];
    const errors: string[] = [];

    for (const config of configs) {
      try {
        const replica = await this.createReplica(winner, config);
        const publishedAdId = await this.publishReplica(replica);

        replicas.push({
          ...replica,
          publishedAdId,
          status: 'published',
        });

        logger.info('Replica created and published', {
          winnerId: winner.id,
          variationType: config.variationType,
          publishedAdId,
        });
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Unknown error';
        errors.push(`${config.variationType}: ${errorMsg}`);

        logger.error('Failed to create/publish replica', {
          winnerId: winner.id,
          variationType: config.variationType,
          error: errorMsg,
        });
      }
    }

    logger.info('Winner replication completed', {
      winnerId: winner.id,
      successCount: replicas.length,
      errorCount: errors.length,
    });

    return replicas;
  }

  /**
   * Generate variations of a winning ad
   * Returns multiple replica configurations based on variation strategies
   */
  async generateVariations(winner: Winner): Promise<Replica[]> {
    logger.info('Generating variations for winner', {
      winnerId: winner.id,
      roas: winner.performance.roas,
    });

    const variations: Replica[] = [];

    // Strategy 1: Audience variations (2 replicas)
    const audienceReplicas = await this.createAudienceVariations(winner, 2);
    variations.push(...audienceReplicas);

    // Strategy 2: Hook variations (3 replicas)
    const hookReplicas = await this.createHookVariations(winner, 3);
    variations.push(...hookReplicas);

    // Strategy 3: Placement variations (1 replica with all placements)
    const placementReplica = await this.createPlacementVariation(winner);
    variations.push(placementReplica);

    // Strategy 4: Budget scaling (1 replica with 2x budget if ROAS > 3)
    if (winner.performance.roas >= 3) {
      const budgetReplica = await this.createBudgetScaledReplica(winner, 2);
      variations.push(budgetReplica);
    }

    logger.info('Variations generated', {
      winnerId: winner.id,
      totalVariations: variations.length,
      audienceCount: audienceReplicas.length,
      hookCount: hookReplicas.length,
      placementCount: 1,
      budgetScaling: winner.performance.roas >= 3,
    });

    return variations;
  }

  /**
   * Create a replica based on variation type
   */
  private async createReplica(winner: Winner, config: ReplicaConfig): Promise<Replica> {
    switch (config.variationType) {
      case 'audience':
        return this.replicateWithNewAudience(winner);

      case 'hook':
        return this.replicateWithNewHook(winner);

      case 'placement':
        return this.replicateWithNewPlacement(winner);

      case 'budget':
        const multiplier = config.budgetMultiplier || 2;
        return this.scaleWinnerBudget(winner, multiplier);

      default:
        throw new Error(`Unknown variation type: ${config.variationType}`);
    }
  }

  /**
   * Create multiple audience variations
   */
  private async createAudienceVariations(winner: Winner, count: number): Promise<Replica[]> {
    const replicas: Replica[] = [];

    for (let i = 0; i < count; i++) {
      const replica = await this.replicateWithNewAudience(winner, i);
      replicas.push(replica);
    }

    return replicas;
  }

  /**
   * Create replica with new audience targeting
   * Strategies:
   * - Lookalike audiences (1%, 2%, 5%)
   * - Expanded age ranges
   * - Different locations
   * - Broader interests
   */
  private async replicateWithNewAudience(winner: Winner, variation: number = 0): Promise<Replica> {
    const newTargeting = { ...winner.targeting };

    // Variation 0: Create lookalike audience
    if (variation === 0) {
      newTargeting.lookalike = {
        sourceAudienceId: winner.adSetId || 'best_customers',
        ratio: 1, // 1% lookalike
      };
      newTargeting.interests = undefined; // Remove interests for LAL
    }
    // Variation 1: Expand age range
    else if (variation === 1) {
      newTargeting.ageMin = Math.max(18, winner.targeting.ageMin - 5);
      newTargeting.ageMax = Math.min(65, winner.targeting.ageMax + 10);
    }
    // Variation 2+: Broader interests
    else {
      // Keep same targeting but remove specific interest restrictions
      if (newTargeting.interests && newTargeting.interests.length > 0) {
        newTargeting.interests = newTargeting.interests.slice(0, Math.ceil(newTargeting.interests.length / 2));
      }
    }

    const replica: Replica = {
      originalWinnerId: winner.id,
      variationType: 'audience',
      creative: { ...winner.creative },
      targeting: newTargeting,
      placements: winner.placements,
      budget: { ...winner.budget },
      metadata: {
        createdAt: new Date().toISOString(),
        parentAdId: winner.adId,
        variationDetails: `Audience variation ${variation}: ${
          variation === 0 ? 'Lookalike 1%' :
          variation === 1 ? 'Expanded age range' :
          'Broader interests'
        }`,
      },
    };

    logger.debug('Created audience variation replica', {
      winnerId: winner.id,
      variation,
      strategy: replica.metadata.variationDetails,
    });

    return replica;
  }

  /**
   * Create multiple hook variations using AI
   */
  private async createHookVariations(winner: Winner, count: number): Promise<Replica[]> {
    const hookVariations = await this.generateHookVariations(
      winner.creative.primaryText,
      winner.creative.headline,
      count
    );

    const replicas: Replica[] = hookVariations.map((hookVar, index) => ({
      originalWinnerId: winner.id,
      variationType: 'hook',
      creative: {
        ...winner.creative,
        headline: hookVar.newHook,
        primaryText: `${hookVar.newHook}\n\n${winner.creative.primaryText.split('\n\n').slice(1).join('\n\n')}`,
      },
      targeting: { ...winner.targeting },
      placements: winner.placements,
      budget: { ...winner.budget },
      metadata: {
        createdAt: new Date().toISOString(),
        parentAdId: winner.adId,
        variationDetails: `Hook variation ${index + 1}: ${hookVar.strategy} - ${hookVar.reasoning}`,
      },
    }));

    return replicas;
  }

  /**
   * Create replica with new hook using Gemini AI
   */
  private async replicateWithNewHook(winner: Winner): Promise<Replica> {
    const hookVariations = await this.generateHookVariations(
      winner.creative.primaryText,
      winner.creative.headline,
      1
    );

    const newHook = hookVariations[0];

    const replica: Replica = {
      originalWinnerId: winner.id,
      variationType: 'hook',
      creative: {
        ...winner.creative,
        headline: newHook.newHook,
        primaryText: `${newHook.newHook}\n\n${winner.creative.primaryText.split('\n\n').slice(1).join('\n\n')}`,
      },
      targeting: { ...winner.targeting },
      placements: winner.placements,
      budget: { ...winner.budget },
      metadata: {
        createdAt: new Date().toISOString(),
        parentAdId: winner.adId,
        variationDetails: `Hook variation: ${newHook.strategy} - ${newHook.reasoning}`,
      },
    };

    logger.debug('Created hook variation replica', {
      winnerId: winner.id,
      originalHook: newHook.originalHook,
      newHook: newHook.newHook,
      strategy: newHook.strategy,
    });

    return replica;
  }

  /**
   * Generate hook variations using Gemini AI
   * Creates 3 different hooks using proven psychological triggers
   */
  private async generateHookVariations(
    primaryText: string,
    headline: string,
    count: number = 3
  ): Promise<HookVariation[]> {
    try {
      const prompt = `You are an expert ad copywriter. Generate ${count} alternative hooks for this winning ad.

Original Headline: ${headline}
Original Primary Text: ${primaryText}

Generate ${count} new hooks using these strategies:
1. Curiosity gap (make them wonder)
2. Social proof (authority/popularity)
3. Urgency/scarcity (FOMO)

For each hook, provide:
- newHook: The new headline (max 40 chars)
- strategy: Which strategy was used
- reasoning: Why this will work

Return JSON array of objects with: originalHook, newHook, strategy, reasoning`;

      const response = await axios.post(
        `${this.geminiUrl}/api/generate`,
        {
          prompt,
          responseFormat: 'json',
        },
        {
          timeout: 30000,
        }
      );

      if (response.data && Array.isArray(response.data.variations)) {
        return response.data.variations.slice(0, count);
      }

      // Fallback if Gemini response is unexpected
      return this.generateFallbackHooks(headline, count);

    } catch (error) {
      logger.error('Failed to generate hook variations with Gemini', {
        error: error instanceof Error ? error.message : 'Unknown error',
      });

      // Return fallback hooks
      return this.generateFallbackHooks(headline, count);
    }
  }

  /**
   * Generate fallback hooks if AI generation fails
   */
  private generateFallbackHooks(originalHook: string, count: number): HookVariation[] {
    const strategies = [
      {
        prefix: '🔥 Limited Time:',
        strategy: 'urgency',
        reasoning: 'Creates FOMO with scarcity',
      },
      {
        prefix: '✨ Thousands are using:',
        strategy: 'social_proof',
        reasoning: 'Leverages bandwagon effect',
      },
      {
        prefix: '🎯 The secret to:',
        strategy: 'curiosity',
        reasoning: 'Opens curiosity gap',
      },
    ];

    return strategies.slice(0, count).map(s => ({
      originalHook,
      newHook: `${s.prefix} ${originalHook}`,
      strategy: s.strategy,
      reasoning: s.reasoning,
    }));
  }

  /**
   * Create replica with new placement strategy
   */
  private async replicateWithNewPlacement(winner: Winner): Promise<Replica> {
    // Expand to all automatic placements for maximum reach
    const newPlacements = [
      'feed',
      'story',
      'reels',
      'instagram_explore',
      'marketplace',
      'video_feeds',
      'right_column',
      'instant_article',
    ];

    const replica: Replica = {
      originalWinnerId: winner.id,
      variationType: 'placement',
      creative: { ...winner.creative },
      targeting: { ...winner.targeting },
      placements: newPlacements,
      budget: { ...winner.budget },
      metadata: {
        createdAt: new Date().toISOString(),
        parentAdId: winner.adId,
        variationDetails: 'Automatic placements across all Meta platforms',
      },
    };

    logger.debug('Created placement variation replica', {
      winnerId: winner.id,
      originalPlacements: winner.placements?.length || 0,
      newPlacements: newPlacements.length,
    });

    return replica;
  }

  /**
   * Create placement variation
   */
  private async createPlacementVariation(winner: Winner): Promise<Replica> {
    return this.replicateWithNewPlacement(winner);
  }

  /**
   * Scale winner budget based on performance
   */
  private async scaleWinnerBudget(winner: Winner, multiplier: number): Promise<Replica> {
    const newBudget = {
      dailyBudget: winner.budget.dailyBudget * multiplier,
      lifetimeBudget: winner.budget.lifetimeBudget
        ? winner.budget.lifetimeBudget * multiplier
        : undefined,
    };

    const replica: Replica = {
      originalWinnerId: winner.id,
      variationType: 'budget',
      creative: { ...winner.creative },
      targeting: { ...winner.targeting },
      placements: winner.placements,
      budget: newBudget,
      metadata: {
        createdAt: new Date().toISOString(),
        parentAdId: winner.adId,
        variationDetails: `Budget scaled ${multiplier}x (ROAS: ${winner.performance.roas.toFixed(2)})`,
      },
    };

    logger.debug('Created budget scaled replica', {
      winnerId: winner.id,
      originalBudget: winner.budget.dailyBudget,
      newBudget: newBudget.dailyBudget,
      multiplier,
      roas: winner.performance.roas,
    });

    return replica;
  }

  /**
   * Create budget-scaled replica
   */
  private async createBudgetScaledReplica(winner: Winner, multiplier: number): Promise<Replica> {
    return this.scaleWinnerBudget(winner, multiplier);
  }

  /**
   * Publish replica to Meta via Meta Publisher service
   */
  async publishReplica(replica: Replica): Promise<string> {
    try {
      logger.info('Publishing replica to Meta', {
        originalWinnerId: replica.originalWinnerId,
        variationType: replica.variationType,
      });

      const payload = {
        name: `Winner Replica - ${replica.variationType} - ${replica.metadata.parentAdId}`,
        creative: replica.creative,
        targeting: replica.targeting,
        placements: replica.placements,
        budget: replica.budget,
        optimization_goal: 'OFFSITE_CONVERSIONS',
        bid_strategy: 'LOWEST_COST_WITH_BID_CAP',
        status: 'PAUSED', // Start paused for review
        metadata: {
          ...replica.metadata,
          isReplica: true,
        },
      };

      const response = await axios.post(
        `${this.metaPublisherUrl}/api/ads`,
        payload,
        {
          timeout: 30000,
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      const adId = response.data.adId || response.data.id;

      logger.info('Replica published successfully', {
        originalWinnerId: replica.originalWinnerId,
        variationType: replica.variationType,
        publishedAdId: adId,
      });

      return adId;

    } catch (error) {
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError;
        logger.error('Failed to publish replica - Meta API error', {
          originalWinnerId: replica.originalWinnerId,
          variationType: replica.variationType,
          status: axiosError.response?.status,
          error: axiosError.response?.data || axiosError.message,
        });
        throw new Error(`Meta API error: ${axiosError.response?.status} - ${JSON.stringify(axiosError.response?.data)}`);
      }

      logger.error('Failed to publish replica - Unknown error', {
        originalWinnerId: replica.originalWinnerId,
        variationType: replica.variationType,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      throw error;
    }
  }

  /**
   * Batch publish multiple replicas
   */
  async publishReplicas(replicas: Replica[]): Promise<{ adId: string; replica: Replica }[]> {
    logger.info('Batch publishing replicas', {
      count: replicas.length,
    });

    const results: { adId: string; replica: Replica }[] = [];
    const errors: string[] = [];

    for (const replica of replicas) {
      try {
        const adId = await this.publishReplica(replica);
        results.push({ adId, replica });
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Unknown error';
        errors.push(`${replica.variationType}: ${errorMsg}`);
      }
    }

    logger.info('Batch publishing completed', {
      total: replicas.length,
      successful: results.length,
      failed: errors.length,
    });

    if (errors.length > 0) {
      logger.warn('Some replicas failed to publish', { errors });
    }

    return results;
  }
}

// Export singleton instance
export const winnerReplicator = new WinnerReplicator();

// Export types for use in other modules
export type { Winner, ReplicaConfig, Replica, HookVariation };
