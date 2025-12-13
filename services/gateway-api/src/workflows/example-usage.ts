/**
 * Winner Workflow - Usage Examples
 * Demonstrates how to use the winner workflow in different scenarios
 */

import {
  runFullWinnerWorkflow,
  approveReplica,
  rejectReplica,
  getPendingApprovals,
  DEFAULT_CONFIG,
  type WorkflowConfig
} from './winner-workflow';

// ============================================================================
// Example 1: Run workflow with default config (requires approval)
// ============================================================================

async function example1_DefaultWorkflow() {
  console.log('Example 1: Running workflow with default config...');

  const result = await runFullWinnerWorkflow();

  console.log('Workflow Result:');
  console.log(`  Status: ${result.status}`);
  console.log(`  Winners Detected: ${result.winnersDetected}`);
  console.log(`  Replicas Created: ${result.replicasCreated}`);
  console.log(`  Replicas Queued: ${result.replicasQueued}`);
  console.log(`  Duration: ${(result.duration / 1000).toFixed(2)}s`);
}

// ============================================================================
// Example 2: Run workflow with auto-publish enabled
// ============================================================================

async function example2_AutoPublish() {
  console.log('Example 2: Running workflow with auto-publish...');

  const config: Partial<WorkflowConfig> = {
    autoPublish: true,           // Auto-publish without approval
    maxReplicasPerWinner: 5,     // Generate 5 replicas per winner
    budgetMultiplier: 2.0,       // 2x budget for replicas
    minRoas: 3.0,                // Only ads with 3x+ ROAS
    platforms: ['meta', 'google'] // Publish to Meta and Google
  };

  const result = await runFullWinnerWorkflow(config);

  console.log('Workflow Result:');
  console.log(`  Winners Detected: ${result.winnersDetected}`);
  console.log(`  Replicas Published: ${result.replicasPublished}`);

  // Show details of published replicas
  const publishedReplicas = result.details.replicas.filter(r => r.status === 'published');
  console.log(`\nPublished Replicas:`);
  publishedReplicas.forEach(replica => {
    console.log(`  - ${replica.id} (${replica.variationType})`);
  });
}

// ============================================================================
// Example 3: Run workflow for specific campaign
// ============================================================================

async function example3_SpecificCampaign() {
  console.log('Example 3: Running workflow for specific campaign...');

  const campaignId = 'campaign_123';

  const config: Partial<WorkflowConfig> = {
    autoPublish: false,
    maxReplicasPerWinner: 3,
    minRoas: 2.5,
    minConfidence: 0.9
  };

  const result = await runFullWinnerWorkflow(config, campaignId);

  console.log(`Campaign ${campaignId} Workflow Result:`);
  console.log(`  Top Winners: ${result.topWinnersSelected}`);
  console.log(`  Replicas Awaiting Approval: ${result.replicasQueued}`);

  // Show top winners
  console.log(`\nTop Winners:`);
  result.details.topWinners.forEach((winner, idx) => {
    console.log(`  ${idx + 1}. Winner ${winner.id}`);
    console.log(`     ROAS: ${winner.performance.roas.toFixed(2)}x`);
    console.log(`     Confidence: ${(winner.confidence * 100).toFixed(1)}%`);
    console.log(`     Revenue: $${winner.performance.revenue.toFixed(2)}`);
  });
}

// ============================================================================
// Example 4: Approval workflow
// ============================================================================

async function example4_ApprovalWorkflow() {
  console.log('Example 4: Managing approval queue...');

  // First, run workflow to generate replicas
  const result = await runFullWinnerWorkflow({
    autoPublish: false,
    maxReplicasPerWinner: 3
  });

  console.log(`Generated ${result.replicasQueued} replicas for approval`);

  // Get pending approvals
  const pendingApprovals = await getPendingApprovals();
  console.log(`\nPending Approvals: ${pendingApprovals.length}`);

  // Review and approve/reject each replica
  for (const { replica } of pendingApprovals) {
    console.log(`\nReviewing replica: ${replica.id}`);
    console.log(`  Winner: ${replica.winnerId}`);
    console.log(`  Variation: ${replica.variationType}`);
    console.log(`  Details: ${JSON.stringify(replica.variation, null, 2)}`);

    // Example: Auto-approve budget variations, review others
    if (replica.variationType === 'budget') {
      await approveReplica(replica.id, 'system_auto_approver', ['meta']);
      console.log(`  ✅ Auto-approved`);
    } else {
      // In a real app, this would wait for human review
      console.log(`  ⏳ Awaiting human review`);
    }
  }
}

// ============================================================================
// Example 5: Manual approval/rejection
// ============================================================================

async function example5_ManualApproval() {
  console.log('Example 5: Manual approval/rejection...');

  const replicaId = 'replica_winner_123_audience_1234567890_0';
  const reviewerId = 'user_jane_doe';

  // Get pending approvals
  const pending = await getPendingApprovals();
  const replicaToReview = pending.find(p => p.replica.id === replicaId);

  if (!replicaToReview) {
    console.log(`Replica ${replicaId} not found in approval queue`);
    return;
  }

  const { replica } = replicaToReview;

  console.log(`\nReviewing Replica:`);
  console.log(`  ID: ${replica.id}`);
  console.log(`  Variation Type: ${replica.variationType}`);
  console.log(`  Variation: ${JSON.stringify(replica.variation, null, 2)}`);

  // Example decision logic
  const shouldApprove = replica.variation.expansionPercent <= 15;

  if (shouldApprove) {
    await approveReplica(replica.id, reviewerId, ['meta', 'google']);
    console.log('✅ Replica approved and published to Meta and Google');
  } else {
    await rejectReplica(
      replica.id,
      reviewerId,
      'Audience expansion too aggressive - would increase CPA'
    );
    console.log('❌ Replica rejected');
  }
}

// ============================================================================
// Example 6: Conservative workflow (high-quality winners only)
// ============================================================================

async function example6_ConservativeWorkflow() {
  console.log('Example 6: Conservative workflow (high-quality only)...');

  const config: Partial<WorkflowConfig> = {
    autoPublish: false,
    maxReplicasPerWinner: 2,     // Only 2 replicas per winner
    budgetMultiplier: 1.2,        // Conservative 20% budget increase
    minRoas: 5.0,                 // Very high ROAS requirement (5x)
    minConfidence: 0.95,          // 95% confidence
    platforms: ['meta']           // Single platform initially
  };

  const result = await runFullWinnerWorkflow(config);

  console.log('Conservative Workflow Result:');
  console.log(`  Winners Detected: ${result.winnersDetected}`);
  console.log(`  Top Winners Selected: ${result.topWinnersSelected}`);
  console.log(`  Replicas Created: ${result.replicasCreated}`);

  if (result.topWinnersSelected === 0) {
    console.log('\n⚠️  No winners met the strict criteria');
    console.log('   Consider lowering minRoas or minConfidence');
  }
}

// ============================================================================
// Example 7: Aggressive scaling workflow
// ============================================================================

async function example7_AggressiveScaling() {
  console.log('Example 7: Aggressive scaling workflow...');

  const config: Partial<WorkflowConfig> = {
    autoPublish: true,            // Auto-publish immediately
    maxReplicasPerWinner: 5,      // More variations
    budgetMultiplier: 3.0,        // Triple the budget
    minRoas: 1.5,                 // Lower threshold to scale faster
    minConfidence: 0.75,          // Lower confidence acceptable
    platforms: ['meta', 'google', 'tiktok'] // All platforms
  };

  const result = await runFullWinnerWorkflow(config);

  console.log('Aggressive Scaling Result:');
  console.log(`  Winners Detected: ${result.winnersDetected}`);
  console.log(`  Replicas Published: ${result.replicasPublished}`);
  console.log(`  Total Platforms: 3`);

  // Calculate total budget deployed
  const totalBudget = result.details.replicas
    .filter(r => r.status === 'published')
    .reduce((sum, r) => sum + (r.variation.newBudget || 0), 0);

  console.log(`  Total Budget Deployed: $${totalBudget.toFixed(2)}/day`);
}

// ============================================================================
// Main: Run all examples
// ============================================================================

async function runAllExamples() {
  console.log('='.repeat(70));
  console.log('WINNER WORKFLOW - USAGE EXAMPLES');
  console.log('='.repeat(70));

  // Uncomment the examples you want to run:

  // await example1_DefaultWorkflow();
  // await example2_AutoPublish();
  // await example3_SpecificCampaign();
  // await example4_ApprovalWorkflow();
  // await example5_ManualApproval();
  // await example6_ConservativeWorkflow();
  // await example7_AggressiveScaling();

  console.log('\n' + '='.repeat(70));
  console.log('Examples completed!');
  console.log('='.repeat(70));
}

// Export for use in other files
export {
  example1_DefaultWorkflow,
  example2_AutoPublish,
  example3_SpecificCampaign,
  example4_ApprovalWorkflow,
  example5_ManualApproval,
  example6_ConservativeWorkflow,
  example7_AggressiveScaling,
  runAllExamples
};

// Run if executed directly
if (require.main === module) {
  runAllExamples().catch(console.error);
}
