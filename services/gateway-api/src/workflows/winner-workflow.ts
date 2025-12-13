/**
 * Winner Workflow - Complete Pipeline from Detection to Publishing
 * Agent 04: Wire Winner Workflows
 *
 * This workflow orchestrates the complete winner lifecycle:
 * 1. Detect winners from running campaigns
 * 2. Index winners to RAG for learning
 * 3. Select top performers for replication
 * 4. Generate replica variations
 * 5. Queue for approval or auto-publish
 * 6. Publish approved replicas
 *
 * Created: 2025-12-13
 */

import axios from 'axios';
import { db } from '../services/database';
import { logger } from '../utils/logger';
import { MultiPlatformPublisher } from '../multi-platform/multi_publisher';
import type { Campaign, Experiment } from '@prisma/client';

// ============================================================================
// Types & Interfaces
// ============================================================================

export interface WorkflowConfig {
  autoPublish: boolean;           // Default: false (require approval)
  maxReplicasPerWinner: number;   // Default: 3
  budgetMultiplier: number;       // Default: 1.5x winner budget
  minRoas: number;                // Minimum ROAS to qualify as winner
  minConfidence: number;          // Minimum statistical confidence
  platforms: ('meta' | 'google' | 'tiktok')[];  // Target platforms
}

export const DEFAULT_CONFIG: WorkflowConfig = {
  autoPublish: false,
  maxReplicasPerWinner: 3,
  budgetMultiplier: 1.5,
  minRoas: 2.0,
  minConfidence: 0.85,
  platforms: ['meta']
};

export interface WorkflowResult {
  workflowId: string;
  campaignId?: string;
  winnersDetected: number;
  winnersIndexed: number;
  topWinnersSelected: number;
  replicasCreated: number;
  replicasQueued: number;
  replicasPublished: number;
  status: 'success' | 'partial' | 'failed';
  error?: string;
  startTime: Date;
  endTime: Date;
  duration: number;
  details: {
    winners: WinnerAd[];
    topWinners: WinnerAd[];
    replicas: ReplicaAd[];
  };
}

export interface WinnerAd {
  id: string;
  campaignId: string;
  adId: string;
  adSetId?: string;
  creativeId?: string;
  performance: {
    roas: number;
    ctr: number;
    cpc: number;
    spend: number;
    revenue: number;
    conversions: number;
    impressions: number;
    clicks: number;
  };
  confidence: number;
  detectedAt: Date;
  indexedAt?: Date;
  metadata: Record<string, any>;
}

export interface ReplicaAd {
  id: string;
  winnerId: string;
  variationType: 'audience' | 'hook' | 'budget' | 'placement' | 'creative';
  variation: Record<string, any>;
  status: 'pending_approval' | 'approved' | 'rejected' | 'published' | 'failed';
  approvedBy?: string;
  approvedAt?: Date;
  publishedAt?: Date;
  publishJobId?: string;
  metadata: Record<string, any>;
}

export interface ApprovalQueueEntry {
  id: string;
  replicaId: string;
  winnerId: string;
  status: 'pending' | 'approved' | 'rejected';
  queuedAt: Date;
  reviewedAt?: Date;
  reviewedBy?: string;
  notes?: string;
}

// ============================================================================
// Main Workflow Function
// ============================================================================

/**
 * Run the complete winner detection → replication → publishing workflow
 */
export async function runFullWinnerWorkflow(
  config: Partial<WorkflowConfig> = {},
  campaignId?: string
): Promise<WorkflowResult> {
  const finalConfig = { ...DEFAULT_CONFIG, ...config };
  const workflowId = `workflow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const startTime = new Date();

  logger.info(`[Winner Workflow ${workflowId}] Starting workflow`, {
    config: finalConfig,
    campaignId
  });

  const result: WorkflowResult = {
    workflowId,
    campaignId,
    winnersDetected: 0,
    winnersIndexed: 0,
    topWinnersSelected: 0,
    replicasCreated: 0,
    replicasQueued: 0,
    replicasPublished: 0,
    status: 'success',
    startTime,
    endTime: new Date(),
    duration: 0,
    details: {
      winners: [],
      topWinners: [],
      replicas: []
    }
  };

  try {
    // ========================================================================
    // STEP 1: Detect Winners
    // ========================================================================
    logger.info(`[Winner Workflow ${workflowId}] Step 1: Detecting winners...`);
    const winners = await detectWinners(finalConfig, campaignId);
    result.winnersDetected = winners.length;
    result.details.winners = winners;

    logger.info(`[Winner Workflow ${workflowId}] Detected ${winners.length} winners`, {
      minRoas: finalConfig.minRoas,
      minConfidence: finalConfig.minConfidence
    });

    if (winners.length === 0) {
      logger.warn(`[Winner Workflow ${workflowId}] No winners detected. Ending workflow.`);
      result.status = 'partial';
      result.endTime = new Date();
      result.duration = result.endTime.getTime() - startTime.getTime();
      return result;
    }

    // ========================================================================
    // STEP 2: Index Winners to RAG
    // ========================================================================
    logger.info(`[Winner Workflow ${workflowId}] Step 2: Indexing winners to RAG...`);
    for (const winner of winners) {
      try {
        await indexWinnerToRAG(winner);
        winner.indexedAt = new Date();
        result.winnersIndexed++;
        logger.info(`[Winner Workflow ${workflowId}] Indexed winner ${winner.id} to RAG`);
      } catch (error: any) {
        logger.error(`[Winner Workflow ${workflowId}] Failed to index winner ${winner.id}:`, error);
        // Continue with other winners
      }
    }

    logger.info(`[Winner Workflow ${workflowId}] Indexed ${result.winnersIndexed}/${winners.length} winners`);

    // ========================================================================
    // STEP 3: Select Top Winners for Replication
    // ========================================================================
    logger.info(`[Winner Workflow ${workflowId}] Step 3: Selecting top winners...`);
    const topWinners = winners
      .filter(w => w.indexedAt) // Only replicate successfully indexed winners
      .sort((a, b) => {
        // Sort by ROAS * confidence (weighted score)
        const scoreA = a.performance.roas * a.confidence;
        const scoreB = b.performance.roas * b.confidence;
        return scoreB - scoreA;
      })
      .slice(0, Math.min(5, winners.length)); // Top 5 winners max

    result.topWinnersSelected = topWinners.length;
    result.details.topWinners = topWinners;

    logger.info(`[Winner Workflow ${workflowId}] Selected ${topWinners.length} top winners for replication`);

    if (topWinners.length === 0) {
      logger.warn(`[Winner Workflow ${workflowId}] No top winners selected. Ending workflow.`);
      result.status = 'partial';
      result.endTime = new Date();
      result.duration = result.endTime.getTime() - startTime.getTime();
      return result;
    }

    // ========================================================================
    // STEP 4: Generate Replicas
    // ========================================================================
    logger.info(`[Winner Workflow ${workflowId}] Step 4: Generating replicas...`);
    const allReplicas: ReplicaAd[] = [];

    for (const winner of topWinners) {
      try {
        logger.info(`[Winner Workflow ${workflowId}] Generating ${finalConfig.maxReplicasPerWinner} replicas for winner ${winner.id}`);

        const replicas = await generateReplicas(winner, finalConfig);
        allReplicas.push(...replicas);
        result.replicasCreated += replicas.length;

        logger.info(`[Winner Workflow ${workflowId}] Generated ${replicas.length} replicas for winner ${winner.id}`);
      } catch (error: any) {
        logger.error(`[Winner Workflow ${workflowId}] Failed to generate replicas for winner ${winner.id}:`, error);
        // Continue with other winners
      }
    }

    result.details.replicas = allReplicas;

    logger.info(`[Winner Workflow ${workflowId}] Generated ${result.replicasCreated} total replicas`);

    if (allReplicas.length === 0) {
      logger.warn(`[Winner Workflow ${workflowId}] No replicas generated. Ending workflow.`);
      result.status = 'partial';
      result.endTime = new Date();
      result.duration = result.endTime.getTime() - startTime.getTime();
      return result;
    }

    // ========================================================================
    // STEP 5 & 6: Publish or Queue for Approval
    // ========================================================================
    if (finalConfig.autoPublish) {
      logger.info(`[Winner Workflow ${workflowId}] Step 5/6: Auto-publishing replicas...`);

      for (const replica of allReplicas) {
        try {
          await publishReplica(replica, finalConfig.platforms);
          replica.status = 'published';
          replica.publishedAt = new Date();
          result.replicasPublished++;

          logger.info(`[Winner Workflow ${workflowId}] Published replica ${replica.id}`);
        } catch (error: any) {
          logger.error(`[Winner Workflow ${workflowId}] Failed to publish replica ${replica.id}:`, error);
          replica.status = 'failed';
          replica.metadata.publishError = error.message;
        }
      }

      logger.info(`[Winner Workflow ${workflowId}] Published ${result.replicasPublished}/${allReplicas.length} replicas`);
    } else {
      logger.info(`[Winner Workflow ${workflowId}] Step 5: Queueing replicas for approval...`);

      for (const replica of allReplicas) {
        try {
          await queueForApproval(replica);
          replica.status = 'pending_approval';
          result.replicasQueued++;

          logger.info(`[Winner Workflow ${workflowId}] Queued replica ${replica.id} for approval`);
        } catch (error: any) {
          logger.error(`[Winner Workflow ${workflowId}] Failed to queue replica ${replica.id}:`, error);
          replica.status = 'failed';
          replica.metadata.queueError = error.message;
        }
      }

      logger.info(`[Winner Workflow ${workflowId}] Queued ${result.replicasQueued}/${allReplicas.length} replicas for approval`);
    }

    // ========================================================================
    // Workflow Complete
    // ========================================================================
    result.endTime = new Date();
    result.duration = result.endTime.getTime() - startTime.getTime();

    // Determine final status
    if (result.winnersDetected === 0) {
      result.status = 'failed';
    } else if (result.replicasCreated === 0) {
      result.status = 'partial';
    } else {
      result.status = 'success';
    }

    logger.info(`[Winner Workflow ${workflowId}] Workflow completed`, {
      status: result.status,
      duration: `${(result.duration / 1000).toFixed(2)}s`,
      winnersDetected: result.winnersDetected,
      replicasCreated: result.replicasCreated,
      replicasPublished: result.replicasPublished,
      replicasQueued: result.replicasQueued
    });

    return result;

  } catch (error: any) {
    logger.error(`[Winner Workflow ${workflowId}] Workflow failed:`, error);
    result.status = 'failed';
    result.error = error.message;
    result.endTime = new Date();
    result.duration = result.endTime.getTime() - startTime.getTime();
    return result;
  }
}

// ============================================================================
// Step 1: Detect Winners
// ============================================================================

/**
 * Detect winning ads based on performance metrics
 */
async function detectWinners(
  config: WorkflowConfig,
  campaignId?: string
): Promise<WinnerAd[]> {
  const winners: WinnerAd[] = [];

  try {
    // Get ML service URL
    const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8003';

    // Call ML service to detect winners
    const response = await axios.post(
      `${ML_SERVICE_URL}/api/ml/detect-winners`,
      {
        campaignId,
        minRoas: config.minRoas,
        minConfidence: config.minConfidence,
        lookbackDays: 7
      },
      { timeout: 30000 }
    );

    const detectedWinners = response.data.winners || [];

    // Convert to WinnerAd format
    for (const winner of detectedWinners) {
      winners.push({
        id: `winner_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        campaignId: winner.campaign_id,
        adId: winner.ad_id,
        adSetId: winner.ad_set_id,
        creativeId: winner.creative_id,
        performance: {
          roas: winner.roas,
          ctr: winner.ctr,
          cpc: winner.cpc,
          spend: winner.spend,
          revenue: winner.revenue,
          conversions: winner.conversions,
          impressions: winner.impressions,
          clicks: winner.clicks
        },
        confidence: winner.confidence,
        detectedAt: new Date(),
        metadata: winner.metadata || {}
      });
    }

    return winners;

  } catch (error: any) {
    logger.error('Failed to detect winners:', error);

    // Fallback: Query database for high-performing experiments
    if (campaignId) {
      const experiments = await db.getClient().experiment.findMany({
        where: {
          campaignId,
          status: 'COMPLETED',
          confidence: { gte: config.minConfidence }
        },
        include: {
          campaign: true
        },
        orderBy: {
          confidence: 'desc'
        },
        take: 10
      });

      // Convert experiments to winners (simplified)
      for (const exp of experiments) {
        const metadata = exp.metadata as any;
        const metrics = exp.metrics as any;

        if (metrics?.roas && metrics.roas >= config.minRoas) {
          winners.push({
            id: `winner_exp_${exp.id}`,
            campaignId: exp.campaignId,
            adId: exp.winnerVariantId || exp.id,
            performance: {
              roas: metrics.roas || 0,
              ctr: metrics.ctr || 0,
              cpc: metrics.cpc || 0,
              spend: metrics.spend || 0,
              revenue: metrics.revenue || 0,
              conversions: metrics.conversions || 0,
              impressions: metrics.impressions || 0,
              clicks: metrics.clicks || 0
            },
            confidence: exp.confidence || 0,
            detectedAt: new Date(),
            metadata: metadata || {}
          });
        }
      }
    }

    return winners;
  }
}

// ============================================================================
// Step 2: Index to RAG
// ============================================================================

/**
 * Index winner to RAG system for learning
 */
async function indexWinnerToRAG(winner: WinnerAd): Promise<void> {
  try {
    const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8003';

    // Call ML service to index winner
    await axios.post(
      `${ML_SERVICE_URL}/api/ml/rag/index-winner`,
      {
        ad_id: winner.adId,
        campaign_id: winner.campaignId,
        performance: winner.performance,
        confidence: winner.confidence,
        metadata: winner.metadata
      },
      { timeout: 15000 }
    );

    logger.info(`Indexed winner ${winner.id} to RAG`);

  } catch (error: any) {
    logger.error(`Failed to index winner ${winner.id} to RAG:`, error);
    throw error;
  }
}

// ============================================================================
// Step 4: Generate Replicas
// ============================================================================

/**
 * Generate replica variations of a winning ad
 */
async function generateReplicas(
  winner: WinnerAd,
  config: WorkflowConfig
): Promise<ReplicaAd[]> {
  const replicas: ReplicaAd[] = [];

  const variationTypes: Array<ReplicaAd['variationType']> = [
    'audience',
    'hook',
    'budget'
  ];

  // Generate replicas based on configuration
  const numReplicas = Math.min(config.maxReplicasPerWinner, variationTypes.length);

  for (let i = 0; i < numReplicas; i++) {
    const variationType = variationTypes[i];

    const replica: ReplicaAd = {
      id: `replica_${winner.id}_${variationType}_${Date.now()}_${i}`,
      winnerId: winner.id,
      variationType,
      variation: generateVariation(winner, variationType, config),
      status: 'pending_approval',
      metadata: {
        sourceWinner: winner.id,
        sourcePerformance: winner.performance,
        createdAt: new Date().toISOString()
      }
    };

    replicas.push(replica);
  }

  return replicas;
}

/**
 * Generate specific variation based on type
 */
function generateVariation(
  winner: WinnerAd,
  variationType: ReplicaAd['variationType'],
  config: WorkflowConfig
): Record<string, any> {
  switch (variationType) {
    case 'audience':
      return {
        type: 'lookalike',
        sourceAudience: winner.metadata.targetAudience,
        expansionPercent: 10
      };

    case 'hook':
      return {
        type: 'alternative_hook',
        originalHook: winner.metadata.hook,
        newHookStyle: 'question' // Could use AI to generate
      };

    case 'budget':
      return {
        type: 'budget_increase',
        originalBudget: winner.performance.spend / 7, // Daily budget estimate
        newBudget: (winner.performance.spend / 7) * config.budgetMultiplier,
        multiplier: config.budgetMultiplier
      };

    case 'placement':
      return {
        type: 'placement_expansion',
        originalPlacements: winner.metadata.placements || ['feed'],
        newPlacements: ['feed', 'stories', 'reels']
      };

    case 'creative':
      return {
        type: 'creative_remix',
        originalCreative: winner.creativeId,
        remixType: 'color_grade' // Could be: format, aspect_ratio, caption_style
      };

    default:
      return {};
  }
}

// ============================================================================
// Step 5: Queue for Approval
// ============================================================================

/**
 * Add replica to approval queue in database
 */
async function queueForApproval(replica: ReplicaAd): Promise<void> {
  try {
    // Store in database using Campaign metadata field for now
    // In production, this would be a dedicated ApprovalQueue table
    const queueEntry: ApprovalQueueEntry = {
      id: `approval_${replica.id}`,
      replicaId: replica.id,
      winnerId: replica.winnerId,
      status: 'pending',
      queuedAt: new Date()
    };

    // Store in database - using KnowledgeDocument as temporary storage
    await db.createKnowledgeDocument({
      name: `Replica Approval: ${replica.id}`,
      description: `Replica of winner ${replica.winnerId} - ${replica.variationType} variation`,
      content: JSON.stringify({
        queueEntry,
        replica
      }),
      embedding: [], // Empty embedding for approval queue entries
      category: 'approval_queue',
      tags: ['replica', 'pending_approval', replica.variationType],
      metadata: {
        replicaId: replica.id,
        winnerId: replica.winnerId,
        variationType: replica.variationType,
        status: 'pending'
      }
    });

    logger.info(`Queued replica ${replica.id} for approval`);

  } catch (error: any) {
    logger.error(`Failed to queue replica ${replica.id}:`, error);
    throw error;
  }
}

// ============================================================================
// Step 6: Publish Replica
// ============================================================================

/**
 * Publish approved replica to advertising platforms
 */
async function publishReplica(
  replica: ReplicaAd,
  platforms: ('meta' | 'google' | 'tiktok')[]
): Promise<void> {
  try {
    // Get Meta publisher URL
    const META_PUBLISHER_URL = process.env.META_PUBLISHER_URL || 'http://localhost:8001';
    const GOOGLE_ADS_URL = process.env.GOOGLE_ADS_URL || 'http://localhost:8004';
    const TIKTOK_ADS_URL = process.env.TIKTOK_ADS_URL || 'http://localhost:8005';

    // Initialize multi-platform publisher
    const publisher = new MultiPlatformPublisher({
      videoAgentUrl: process.env.VIDEO_AGENT_URL || 'http://localhost:8002',
      metaPublisherUrl: META_PUBLISHER_URL,
      googleAdsUrl: GOOGLE_ADS_URL,
      tiktokAdsUrl: TIKTOK_ADS_URL
    });

    // Prepare publish request
    const publishRequest = {
      creative_id: replica.id,
      video_path: replica.metadata.videoPath || '/tmp/placeholder.mp4',
      platforms,
      budget_allocation: calculateBudgetAllocation(platforms, replica.variation),
      campaign_name: `Winner Replica: ${replica.winnerId}`,
      campaign_config: {
        meta: {
          objective: 'OUTCOME_ENGAGEMENT',
          targeting: replica.variation.sourceAudience || {},
          placements: replica.variation.newPlacements || ['feed', 'reels']
        }
      },
      creative_config: {
        caption: replica.metadata.caption,
        headline: replica.metadata.headline,
        cta: 'LEARN_MORE'
      }
    };

    // Publish to platforms
    const publishResult = await publisher.publishMultiPlatform(publishRequest);

    replica.publishJobId = publishResult.job_id;
    replica.metadata.publishResult = publishResult;

    logger.info(`Published replica ${replica.id} to ${platforms.join(', ')}`);

  } catch (error: any) {
    logger.error(`Failed to publish replica ${replica.id}:`, error);
    throw error;
  }
}

/**
 * Calculate budget allocation across platforms
 */
function calculateBudgetAllocation(
  platforms: string[],
  variation: Record<string, any>
): Record<string, number> {
  const allocation: Record<string, number> = {};
  const budgetPerPlatform = variation.newBudget || 100;

  for (const platform of platforms) {
    allocation[platform] = budgetPerPlatform / platforms.length;
  }

  return allocation;
}

// ============================================================================
// Approval Management Functions
// ============================================================================

/**
 * Approve a replica and publish it
 */
export async function approveReplica(
  replicaId: string,
  approvedBy: string,
  platforms: ('meta' | 'google' | 'tiktok')[] = ['meta']
): Promise<void> {
  logger.info(`Approving replica ${replicaId} by ${approvedBy}`);

  // Get replica from database
  const docs = await db.searchKnowledgeDocuments({
    category: 'approval_queue',
    tags: ['replica', replicaId]
  });

  if (docs.length === 0) {
    throw new Error(`Replica ${replicaId} not found in approval queue`);
  }

  const doc = docs[0];
  const data = JSON.parse(doc.content);
  const replica: ReplicaAd = data.replica;

  // Update status
  replica.status = 'approved';
  replica.approvedBy = approvedBy;
  replica.approvedAt = new Date();

  // Publish replica
  await publishReplica(replica, platforms);

  // Update database
  await db.updateKnowledgeDocument(doc.id, {
    content: JSON.stringify({
      ...data,
      replica
    }),
    tags: ['replica', 'approved', replica.variationType],
    metadata: {
      ...(doc.metadata as Record<string, any> || {}),
      status: 'approved',
      approvedBy,
      approvedAt: replica.approvedAt.toISOString()
    }
  });

  logger.info(`Replica ${replicaId} approved and published`);
}

/**
 * Reject a replica
 */
export async function rejectReplica(
  replicaId: string,
  rejectedBy: string,
  reason: string
): Promise<void> {
  logger.info(`Rejecting replica ${replicaId} by ${rejectedBy}: ${reason}`);

  // Get replica from database
  const docs = await db.searchKnowledgeDocuments({
    category: 'approval_queue',
    tags: ['replica', replicaId]
  });

  if (docs.length === 0) {
    throw new Error(`Replica ${replicaId} not found in approval queue`);
  }

  const doc = docs[0];
  const data = JSON.parse(doc.content);
  const replica: ReplicaAd = data.replica;

  // Update status
  replica.status = 'rejected';
  replica.metadata.rejectedBy = rejectedBy;
  replica.metadata.rejectedAt = new Date().toISOString();
  replica.metadata.rejectionReason = reason;

  // Update database
  await db.updateKnowledgeDocument(doc.id, {
    content: JSON.stringify({
      ...data,
      replica
    }),
    tags: ['replica', 'rejected', replica.variationType],
    metadata: {
      ...(doc.metadata as Record<string, any> || {}),
      status: 'rejected',
      rejectedBy,
      rejectionReason: reason
    }
  });

  logger.info(`Replica ${replicaId} rejected`);
}

/**
 * Get all pending approvals
 */
export async function getPendingApprovals(): Promise<Array<{
  queueEntry: ApprovalQueueEntry;
  replica: ReplicaAd;
}>> {
  const docs = await db.searchKnowledgeDocuments({
    category: 'approval_queue',
    tags: ['replica', 'pending_approval']
  });

  return docs.map(doc => {
    const data = JSON.parse(doc.content);
    return {
      queueEntry: data.queueEntry,
      replica: data.replica
    };
  });
}

// ============================================================================
// Workflow Status Tracking
// ============================================================================

/**
 * Get workflow status by ID
 */
export async function getWorkflowStatus(workflowId: string): Promise<any> {
  // In production, this would query a WorkflowRuns table
  // For now, return a placeholder
  logger.info(`Getting status for workflow ${workflowId}`);

  return {
    workflowId,
    status: 'completed',
    message: 'Workflow status tracking not yet implemented'
  };
}

// ============================================================================
// Exports
// ============================================================================

export {
  runFullWinnerWorkflow as default,
  detectWinners,
  indexWinnerToRAG,
  generateReplicas,
  publishReplica,
  queueForApproval
};
