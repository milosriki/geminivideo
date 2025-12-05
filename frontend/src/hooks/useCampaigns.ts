/**
 * Campaign Hooks
 * React Query hooks for campaign CRUD operations
 */

import { useMutation, useQuery, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import apiClient, { Campaign, CampaignPredictions } from '../lib/api';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const campaignKeys = {
  all: ['campaigns'] as const,
  lists: () => [...campaignKeys.all, 'list'] as const,
  list: (filters?: any) => [...campaignKeys.lists(), filters] as const,
  details: () => [...campaignKeys.all, 'detail'] as const,
  detail: (id: string) => [...campaignKeys.details(), id] as const,
  predictions: (data: any) => [...campaignKeys.all, 'predictions', data] as const,
};

// ============================================================================
// QUERIES
// ============================================================================

/**
 * Fetch all campaigns
 */
export function useCampaignsList(filters?: any, options?: UseQueryOptions<Campaign[]>) {
  return useQuery({
    queryKey: campaignKeys.list(filters),
    queryFn: () => apiClient.getCampaigns(filters),
    staleTime: 30000, // 30 seconds
    ...options,
  });
}

/**
 * Fetch single campaign by ID
 */
export function useCampaign(campaignId: string, options?: UseQueryOptions<Campaign>) {
  return useQuery({
    queryKey: campaignKeys.detail(campaignId),
    queryFn: () => apiClient.getCampaignById(campaignId),
    enabled: !!campaignId,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Get campaign predictions
 */
export function useCampaignPredictions(
  campaignData: Partial<Campaign>,
  options?: UseQueryOptions<CampaignPredictions>
) {
  return useQuery({
    queryKey: campaignKeys.predictions(campaignData),
    queryFn: () => apiClient.predictCampaign(campaignData),
    enabled: false, // Manual trigger only
    staleTime: 60000, // 1 minute
    ...options,
  });
}

// ============================================================================
// MUTATIONS
// ============================================================================

/**
 * Create new campaign
 */
export function useCreateCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (campaign: Partial<Campaign>) => apiClient.createCampaign(campaign),
    onSuccess: () => {
      // Invalidate campaigns list to refetch
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
    },
  });
}

/**
 * Update existing campaign
 */
export function useUpdateCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<Campaign> }) =>
      apiClient.updateCampaign(id, updates),
    onSuccess: (data, variables) => {
      // Update the specific campaign in cache
      queryClient.setQueryData(campaignKeys.detail(variables.id), data);
      // Invalidate lists to refetch
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
    },
  });
}

/**
 * Delete campaign
 */
export function useDeleteCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (campaignId: string) => apiClient.deleteCampaign(campaignId),
    onSuccess: (_, campaignId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: campaignKeys.detail(campaignId) });
      // Invalidate lists to refetch
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
    },
  });
}

/**
 * Save campaign as draft
 */
export function useSaveCampaignDraft() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (campaign: Partial<Campaign>) => apiClient.saveCampaignDraft(campaign),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
    },
  });
}

/**
 * Launch campaign
 */
export function useLaunchCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (campaignId: string) => apiClient.launchCampaign(campaignId),
    onSuccess: (data, campaignId) => {
      // Update the specific campaign in cache
      queryClient.setQueryData(campaignKeys.detail(campaignId), data);
      // Invalidate lists to refetch
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
    },
  });
}

/**
 * Pause campaign
 */
export function usePauseCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (campaignId: string) => apiClient.pauseCampaign(campaignId),
    onSuccess: (data, campaignId) => {
      queryClient.setQueryData(campaignKeys.detail(campaignId), data);
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
    },
  });
}

/**
 * Resume campaign
 */
export function useResumeCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (campaignId: string) => apiClient.resumeCampaign(campaignId),
    onSuccess: (data, campaignId) => {
      queryClient.setQueryData(campaignKeys.detail(campaignId), data);
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
    },
  });
}

/**
 * Upload creative
 */
export function useUploadCreative() {
  return useMutation({
    mutationFn: (formData: FormData) => apiClient.uploadCreative(formData),
  });
}

// ============================================================================
// HELPER HOOKS
// ============================================================================

/**
 * Combined hook for campaign actions
 */
export function useCampaignActions(campaignId?: string) {
  const createCampaign = useCreateCampaign();
  const updateCampaign = useUpdateCampaign();
  const deleteCampaign = useDeleteCampaign();
  const saveDraft = useSaveCampaignDraft();
  const launchCampaign = useLaunchCampaign();
  const pauseCampaign = usePauseCampaign();
  const resumeCampaign = useResumeCampaign();

  return {
    create: createCampaign.mutate,
    createAsync: createCampaign.mutateAsync,
    update: (updates: Partial<Campaign>) =>
      campaignId ? updateCampaign.mutate({ id: campaignId, updates }) : null,
    updateAsync: (updates: Partial<Campaign>) =>
      campaignId ? updateCampaign.mutateAsync({ id: campaignId, updates }) : null,
    delete: () => (campaignId ? deleteCampaign.mutate(campaignId) : null),
    deleteAsync: () => (campaignId ? deleteCampaign.mutateAsync(campaignId) : null),
    saveDraft: saveDraft.mutate,
    saveDraftAsync: saveDraft.mutateAsync,
    launch: () => (campaignId ? launchCampaign.mutate(campaignId) : null),
    launchAsync: () => (campaignId ? launchCampaign.mutateAsync(campaignId) : null),
    pause: () => (campaignId ? pauseCampaign.mutate(campaignId) : null),
    pauseAsync: () => (campaignId ? pauseCampaign.mutateAsync(campaignId) : null),
    resume: () => (campaignId ? resumeCampaign.mutate(campaignId) : null),
    resumeAsync: () => (campaignId ? resumeCampaign.mutateAsync(campaignId) : null),
    isLoading:
      createCampaign.isPending ||
      updateCampaign.isPending ||
      deleteCampaign.isPending ||
      saveDraft.isPending ||
      launchCampaign.isPending ||
      pauseCampaign.isPending ||
      resumeCampaign.isPending,
    isError:
      createCampaign.isError ||
      updateCampaign.isError ||
      deleteCampaign.isError ||
      saveDraft.isError ||
      launchCampaign.isError ||
      pauseCampaign.isError ||
      resumeCampaign.isError,
    error:
      createCampaign.error ||
      updateCampaign.error ||
      deleteCampaign.error ||
      saveDraft.error ||
      launchCampaign.error ||
      pauseCampaign.error ||
      resumeCampaign.error,
  };
}
