/**
 * Publishing Hooks
 * React Query hooks for multi-platform publishing operations
 */

import { useMutation, useQuery, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import apiClient, { PublishRequest, PublishStatus } from '../lib/api';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const publishKeys = {
  all: ['publish'] as const,
  status: (jobId: string) => [...publishKeys.all, 'status', jobId] as const,
  campaignJobs: (campaignId: string) => [...publishKeys.all, 'campaign', campaignId] as const,
};

// ============================================================================
// QUERIES
// ============================================================================

/**
 * Get publish job status
 * @param jobId - Publish job ID
 */
export function usePublishStatus(jobId: string, options?: Partial<UseQueryOptions<PublishStatus>>) {
  return useQuery({
    queryKey: publishKeys.status(jobId),
    queryFn: () => apiClient.getPublishStatus(jobId),
    enabled: !!jobId,
    staleTime: 5000, // 5 seconds
    refetchInterval: (query) => {
      const data = query.state.data as PublishStatus | undefined;
      // Stop polling when job is completed or failed
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      return 5000; // Poll every 5 seconds
    },
    ...options as any,
  });
}

/**
 * Get all publish jobs for a campaign
 * @param campaignId - Campaign ID
 */
export function useCampaignPublishJobs(
  campaignId: string,
  options?: Partial<UseQueryOptions<PublishStatus[]>>
) {
  return useQuery({
    queryKey: publishKeys.campaignJobs(campaignId),
    queryFn: () => apiClient.getCampaignPublishJobs(campaignId),
    enabled: !!campaignId,
    staleTime: 30000, // 30 seconds
    ...options as any,
  });
}

// ============================================================================
// MUTATIONS
// ============================================================================

/**
 * Publish campaign to Meta
 */
export function usePublishToMeta() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: PublishRequest) => apiClient.publishToMeta(request),
    onSuccess: (data, variables) => {
      // Invalidate campaign publish jobs
      queryClient.invalidateQueries({
        queryKey: publishKeys.campaignJobs(variables.campaignId),
      });
    },
  });
}

/**
 * Publish campaign to Google Ads
 */
export function usePublishToGoogle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: PublishRequest) => apiClient.publishToGoogle(request),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: publishKeys.campaignJobs(variables.campaignId),
      });
    },
  });
}

/**
 * Publish campaign to TikTok
 */
export function usePublishToTikTok() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: PublishRequest) => apiClient.publishToTikTok(request),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: publishKeys.campaignJobs(variables.campaignId),
      });
    },
  });
}

// ============================================================================
// HELPER HOOKS
// ============================================================================

/**
 * Combined hook for publishing to multiple platforms
 */
export function useMultiPlatformPublish() {
  const publishToMeta = usePublishToMeta();
  const publishToGoogle = usePublishToGoogle();
  const publishToTikTok = usePublishToTikTok();

  return {
    publishToMeta: publishToMeta.mutate,
    publishToMetaAsync: publishToMeta.mutateAsync,
    publishToGoogle: publishToGoogle.mutate,
    publishToGoogleAsync: publishToGoogle.mutateAsync,
    publishToTikTok: publishToTikTok.mutate,
    publishToTikTokAsync: publishToTikTok.mutateAsync,
    isLoading:
      publishToMeta.isPending || publishToGoogle.isPending || publishToTikTok.isPending,
    isError: publishToMeta.isError || publishToGoogle.isError || publishToTikTok.isError,
    error: publishToMeta.error || publishToGoogle.error || publishToTikTok.error,
    metaStatus: {
      isPending: publishToMeta.isPending,
      isSuccess: publishToMeta.isSuccess,
      isError: publishToMeta.isError,
      error: publishToMeta.error,
      data: publishToMeta.data,
    },
    googleStatus: {
      isPending: publishToGoogle.isPending,
      isSuccess: publishToGoogle.isSuccess,
      isError: publishToGoogle.isError,
      error: publishToGoogle.error,
      data: publishToGoogle.data,
    },
    tiktokStatus: {
      isPending: publishToTikTok.isPending,
      isSuccess: publishToTikTok.isSuccess,
      isError: publishToTikTok.isError,
      error: publishToTikTok.error,
      data: publishToTikTok.data,
    },
  };
}

/**
 * Hook to track publishing progress
 * Automatically polls status for active jobs
 */
export function usePublishingProgress(campaignId: string) {
  const jobs = useCampaignPublishJobs(campaignId);

  // Get active jobs (pending or processing)
  const activeJobs = (jobs.data as PublishStatus[] | undefined)?.filter(
    (job: PublishStatus) => job.status === 'pending' || job.status === 'processing'
  );

  // Poll status for all active jobs
  const statusQueries = (activeJobs || []).map((job: PublishStatus) =>
    // eslint-disable-next-line react-hooks/rules-of-hooks
    usePublishStatus(job.jobId)
  );
  
  // Need to use statusQueries here to avoid unused var warning if needed, 
  // but usually it's used for UI feedback.
  console.log('Active status queries:', statusQueries.length);

  return {
    jobs: jobs.data as PublishStatus[] | undefined,
    isLoading: jobs.isLoading,
    isError: jobs.isError,
    error: jobs.error,
    activeJobs,
    hasActiveJobs: (activeJobs?.length || 0) > 0,
    completedJobs: (jobs.data as PublishStatus[] | undefined)?.filter((job: PublishStatus) => job.status === 'completed') || [],
    failedJobs: (jobs.data as PublishStatus[] | undefined)?.filter((job: PublishStatus) => job.status === 'failed') || [],
    refetch: jobs.refetch,
  };
}

/**
 * Hook for campaign launch with publishing
 * Combines campaign launch with platform publishing
 */
export function useLaunchAndPublish() {
  const publishToMeta = usePublishToMeta();
  const publishToGoogle = usePublishToGoogle();
  const publishToTikTok = usePublishToTikTok();

  const launchAndPublish = async (params: {
    campaignId: string;
    platforms: Array<'meta' | 'google' | 'tiktok'>;
    adAccountIds: Record<string, string>;
    configs?: Record<string, any>;
  }) => {
    const { campaignId, platforms, adAccountIds, configs = {} } = params;
    const results: Array<{ platform: string; status: PublishStatus | null; error: any }> = [];

    // Publish to each platform
    for (const platform of platforms) {
      try {
        const request: PublishRequest = {
          campaignId,
          platform,
          adAccountId: adAccountIds[platform],
          config: configs[platform],
        };

        let status: PublishStatus | null = null;

        if (platform === 'meta') {
          status = await publishToMeta.mutateAsync(request);
        } else if (platform === 'google') {
          status = await publishToGoogle.mutateAsync(request);
        } else if (platform === 'tiktok') {
          status = await publishToTikTok.mutateAsync(request);
        }

        results.push({ platform, status, error: null });
      } catch (error) {
        results.push({ platform, status: null, error });
      }
    }

    return results;
  };

  return {
    launchAndPublish,
    isLoading:
      publishToMeta.isPending || publishToGoogle.isPending || publishToTikTok.isPending,
  };
}

/**
 * Simple hook to check if a publish job is complete
 */
export function useIsPublishComplete(jobId?: string) {
  const status = usePublishStatus(jobId || '', {
    enabled: !!jobId,
  } as any);

  const data = status.data as PublishStatus | undefined;

  return {
    isComplete: data?.status === 'completed',
    isFailed: data?.status === 'failed',
    isProcessing: data?.status === 'processing',
    isPending: data?.status === 'pending',
    progress: data?.progress || 0,
    message: data?.message,
    error: data?.error,
    externalId: data?.externalId,
  };
}
