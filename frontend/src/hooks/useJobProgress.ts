/**
 * useJobProgress Hook
 * 
 * Polls for job status from the gateway API and provides real-time progress updates.
 * Supports render jobs, pipeline jobs, and any async processing with status tracking.
 */

import { useState, useEffect, useCallback, useRef } from 'react';

interface JobProgress {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'error';
  progress: number;
  stage?: string;
  outputUrl?: string;
  videoUrl?: string;
  error?: string;
  metadata?: Record<string, unknown>;
  createdAt?: string;
  completedAt?: string;
}

interface UseJobProgressOptions {
  /** Polling interval in milliseconds (default: 3000ms) */
  pollingInterval?: number;
  /** Maximum number of poll attempts before giving up (default: 200 = ~10 minutes) */
  maxPolls?: number;
  /** Auto-start polling when jobId is provided (default: true) */
  autoStart?: boolean;
  /** Callback when job completes successfully */
  onComplete?: (progress: JobProgress) => void;
  /** Callback when job fails */
  onError?: (error: string) => void;
}

interface UseJobProgressReturn {
  /** Current job progress state */
  progress: JobProgress | null;
  /** Whether polling is currently active */
  isPolling: boolean;
  /** Whether the job is loading (first poll hasn't completed) */
  isLoading: boolean;
  /** Any error that occurred during polling */
  error: string | null;
  /** Start polling for a job */
  startPolling: (jobId: string) => void;
  /** Stop polling */
  stopPolling: () => void;
  /** Reset state and stop polling */
  reset: () => void;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useJobProgress(
  initialJobId: string | null = null,
  options: UseJobProgressOptions = {}
): UseJobProgressReturn {
  const {
    pollingInterval = 3000,
    maxPolls = 200,
    autoStart = true,
    onComplete,
    onError,
  } = options;

  const [progress, setProgress] = useState<JobProgress | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pollCountRef = useRef(0);
  const pollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const currentJobIdRef = useRef<string | null>(null);
  const isPollingRef = useRef(false);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (pollTimeoutRef.current) {
      clearTimeout(pollTimeoutRef.current);
      pollTimeoutRef.current = null;
    }
    isPollingRef.current = false;
  }, []);

  // Fetch job status from API
  const fetchJobStatus = useCallback(async (jobId: string): Promise<JobProgress | null> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/pipeline/job/${jobId}/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`Job ${jobId} not found`);
        }
        throw new Error(`Failed to fetch job status: ${response.statusText}`);
      }

      const data = await response.json();
      
      return {
        jobId: data.job_id || jobId,
        status: data.status,
        progress: data.progress || 0,
        stage: data.stage,
        outputUrl: data.output_url,
        videoUrl: data.video_url,
        error: data.error,
        metadata: data.metadata,
        createdAt: data.created_at,
        completedAt: data.completed_at,
      };
    } catch (err) {
      console.error('Failed to fetch job status:', err);
      throw err;
    }
  }, []);

  // Poll function
  const poll = useCallback(async (jobId: string) => {
    if (!isPollingRef.current || currentJobIdRef.current !== jobId) {
      return;
    }

    pollCountRef.current += 1;

    try {
      const status = await fetchJobStatus(jobId);
      
      if (!status || currentJobIdRef.current !== jobId) {
        return;
      }

      setProgress(status);
      setIsLoading(false);

      // Check if job is complete or failed
      if (status.status === 'completed') {
        cleanup();
        setIsPolling(false);
        onComplete?.(status);
        return;
      }

      if (status.status === 'failed' || status.status === 'error') {
        cleanup();
        setIsPolling(false);
        const errorMessage = status.error || 'Job failed';
        setError(errorMessage);
        onError?.(errorMessage);
        return;
      }

      // Check if max polls exceeded
      if (pollCountRef.current >= maxPolls) {
        cleanup();
        setIsPolling(false);
        const timeoutError = `Job timed out after ${Math.round((maxPolls * pollingInterval) / 60000)} minutes`;
        setError(timeoutError);
        onError?.(timeoutError);
        return;
      }

      // Continue polling
      pollTimeoutRef.current = setTimeout(() => poll(jobId), pollingInterval);
    } catch (err) {
      console.error('Polling error:', err);
      
      // Retry on network errors, but not on 404
      if (pollCountRef.current < 3) {
        pollTimeoutRef.current = setTimeout(() => poll(jobId), pollingInterval * 2);
      } else {
        cleanup();
        setIsPolling(false);
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        onError?.(errorMessage);
      }
    }
  }, [fetchJobStatus, cleanup, maxPolls, pollingInterval, onComplete, onError]);

  // Start polling
  const startPolling = useCallback((jobId: string) => {
    cleanup();
    
    currentJobIdRef.current = jobId;
    pollCountRef.current = 0;
    isPollingRef.current = true;
    
    setProgress(null);
    setError(null);
    setIsPolling(true);
    setIsLoading(true);

    // Start polling
    poll(jobId);
  }, [cleanup, poll]);

  // Stop polling
  const stopPolling = useCallback(() => {
    cleanup();
    setIsPolling(false);
  }, [cleanup]);

  // Reset state
  const reset = useCallback(() => {
    cleanup();
    currentJobIdRef.current = null;
    pollCountRef.current = 0;
    setProgress(null);
    setError(null);
    setIsPolling(false);
    setIsLoading(false);
  }, [cleanup]);

  // Auto-start polling when initialJobId changes
  useEffect(() => {
    if (initialJobId && autoStart) {
      startPolling(initialJobId);
    }

    return () => {
      cleanup();
    };
  }, [initialJobId, autoStart, startPolling, cleanup]);

  return {
    progress,
    isPolling,
    isLoading,
    error,
    startPolling,
    stopPolling,
    reset,
  };
}

export default useJobProgress;
