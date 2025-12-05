/**
 * A/B Testing Hooks
 * React Query hooks for A/B test operations
 */

import { useMutation, useQuery, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import apiClient, { ABTest, ABTestResults } from '../lib/api';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const abTestKeys = {
  all: ['ab-tests'] as const,
  lists: () => [...abTestKeys.all, 'list'] as const,
  list: (filters?: any) => [...abTestKeys.lists(), filters] as const,
  details: () => [...abTestKeys.all, 'detail'] as const,
  detail: (id: string) => [...abTestKeys.details(), id] as const,
  results: (id: string) => [...abTestKeys.all, 'results', id] as const,
};

// ============================================================================
// QUERIES
// ============================================================================

/**
 * Fetch all A/B tests
 */
export function useABTestsList(filters?: any, options?: UseQueryOptions<ABTest[]>) {
  return useQuery({
    queryKey: abTestKeys.list(filters),
    queryFn: () => apiClient.getABTests(filters),
    staleTime: 30000, // 30 seconds
    ...options,
  });
}

/**
 * Fetch single A/B test by ID
 */
export function useABTest(testId: string, options?: UseQueryOptions<ABTest>) {
  return useQuery({
    queryKey: abTestKeys.detail(testId),
    queryFn: () => apiClient.getABTestById(testId),
    enabled: !!testId,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Fetch A/B test results
 */
export function useABTestResults(testId: string, options?: UseQueryOptions<ABTestResults>) {
  return useQuery({
    queryKey: abTestKeys.results(testId),
    queryFn: () => apiClient.getABTestResults(testId),
    enabled: !!testId,
    staleTime: 60000, // 1 minute
    refetchInterval: 300000, // 5 minutes for active tests
    ...options,
  });
}

// ============================================================================
// MUTATIONS
// ============================================================================

/**
 * Create new A/B test
 */
export function useCreateABTest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (test: Partial<ABTest>) => apiClient.createABTest(test),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: abTestKeys.lists() });
    },
  });
}

/**
 * Update existing A/B test
 */
export function useUpdateABTest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<ABTest> }) =>
      apiClient.updateABTest(id, updates),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(abTestKeys.detail(variables.id), data);
      queryClient.invalidateQueries({ queryKey: abTestKeys.lists() });
    },
  });
}

/**
 * Delete A/B test
 */
export function useDeleteABTest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (testId: string) => apiClient.deleteABTest(testId),
    onSuccess: (_, testId) => {
      queryClient.removeQueries({ queryKey: abTestKeys.detail(testId) });
      queryClient.removeQueries({ queryKey: abTestKeys.results(testId) });
      queryClient.invalidateQueries({ queryKey: abTestKeys.lists() });
    },
  });
}

/**
 * Start A/B test
 */
export function useStartABTest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (testId: string) => apiClient.startABTest(testId),
    onSuccess: (data, testId) => {
      queryClient.setQueryData(abTestKeys.detail(testId), data);
      queryClient.invalidateQueries({ queryKey: abTestKeys.lists() });
    },
  });
}

/**
 * Stop A/B test
 */
export function useStopABTest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (testId: string) => apiClient.stopABTest(testId),
    onSuccess: (data, testId) => {
      queryClient.setQueryData(abTestKeys.detail(testId), data);
      queryClient.invalidateQueries({ queryKey: abTestKeys.lists() });
      // Also invalidate results when stopping
      queryClient.invalidateQueries({ queryKey: abTestKeys.results(testId) });
    },
  });
}

/**
 * Promote winner
 */
export function usePromoteWinner() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ testId, winner }: { testId: string; winner: 'A' | 'B' }) =>
      apiClient.promoteWinner(testId, winner),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(abTestKeys.detail(variables.testId), data);
      queryClient.invalidateQueries({ queryKey: abTestKeys.lists() });
    },
  });
}

// ============================================================================
// HELPER HOOKS
// ============================================================================

/**
 * Combined hook for A/B test actions
 */
export function useABTestActions(testId?: string) {
  const createTest = useCreateABTest();
  const updateTest = useUpdateABTest();
  const deleteTest = useDeleteABTest();
  const startTest = useStartABTest();
  const stopTest = useStopABTest();
  const promoteWinner = usePromoteWinner();

  return {
    create: createTest.mutate,
    createAsync: createTest.mutateAsync,
    update: (updates: Partial<ABTest>) =>
      testId ? updateTest.mutate({ id: testId, updates }) : null,
    updateAsync: (updates: Partial<ABTest>) =>
      testId ? updateTest.mutateAsync({ id: testId, updates }) : null,
    delete: () => (testId ? deleteTest.mutate(testId) : null),
    deleteAsync: () => (testId ? deleteTest.mutateAsync(testId) : null),
    start: () => (testId ? startTest.mutate(testId) : null),
    startAsync: () => (testId ? startTest.mutateAsync(testId) : null),
    stop: () => (testId ? stopTest.mutate(testId) : null),
    stopAsync: () => (testId ? stopTest.mutateAsync(testId) : null),
    promote: (winner: 'A' | 'B') =>
      testId ? promoteWinner.mutate({ testId, winner }) : null,
    promoteAsync: (winner: 'A' | 'B') =>
      testId ? promoteWinner.mutateAsync({ testId, winner }) : null,
    isLoading:
      createTest.isPending ||
      updateTest.isPending ||
      deleteTest.isPending ||
      startTest.isPending ||
      stopTest.isPending ||
      promoteWinner.isPending,
    isError:
      createTest.isError ||
      updateTest.isError ||
      deleteTest.isError ||
      startTest.isError ||
      stopTest.isError ||
      promoteWinner.isError,
    error:
      createTest.error ||
      updateTest.error ||
      deleteTest.error ||
      startTest.error ||
      stopTest.error ||
      promoteWinner.error,
  };
}

/**
 * Combined hook for A/B test detail page
 * Fetches test details and results together
 */
export function useABTestDetail(testId: string) {
  const test = useABTest(testId);
  const results = useABTestResults(testId);

  return {
    test: {
      data: test.data,
      isLoading: test.isLoading,
      isError: test.isError,
      error: test.error,
    },
    results: {
      data: results.data,
      isLoading: results.isLoading,
      isError: results.isError,
      error: results.error,
    },
    isLoading: test.isLoading || results.isLoading,
    isError: test.isError || results.isError,
    refetch: () => {
      test.refetch();
      results.refetch();
    },
  };
}

/**
 * Hook to get active A/B tests for a campaign
 */
export function useCampaignABTests(campaignId: string) {
  return useABTestsList({ campaignId, status: 'running' });
}
