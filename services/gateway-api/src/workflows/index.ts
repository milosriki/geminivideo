/**
 * Workflows Index
 * Centralized exports for all workflow modules
 */

export {
  runFullWinnerWorkflow,
  approveReplica,
  rejectReplica,
  getPendingApprovals,
  getWorkflowStatus,
  detectWinners,
  indexWinnerToRAG,
  generateReplicas,
  publishReplica,
  queueForApproval,
  DEFAULT_CONFIG,
  type WorkflowConfig,
  type WorkflowResult,
  type WinnerAd,
  type ReplicaAd,
  type ApprovalQueueEntry
} from './winner-workflow';
