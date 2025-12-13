import { useState, useEffect, useRef } from 'react';
import { titanAPI } from '../services/api';

interface JobProgress {
  jobId: string;
  status: string;
  progress: number;
  stage: string;
  outputUrl?: string;
  videoUrl?: string;
  error?: string;
  metadata?: Record<string, unknown>;
}

export function useJobProgress(jobId: string | null) {
  const [progress, setProgress] = useState<JobProgress | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const isPollingRef = useRef(false);
  const timeoutIdRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!jobId) {
      return;
    }

    // Prevent starting multiple polling instances
    if (isPollingRef.current) {
      return;
    }

    setIsPolling(true);
    isPollingRef.current = true;

    const poll = async () => {
      if (!isPollingRef.current) return;

      try {
        const status = await titanAPI.getJobStatus(jobId);
        
        if (!isPollingRef.current) return;
        
        setProgress({
          jobId,
          status: status.status,
          progress: status.progress,
          stage: status.stage,
          outputUrl: status.output_url,
          videoUrl: status.video_url,
          error: status.error,
          metadata: status.metadata
        });

        // Stop polling if completed or failed
        if (status.status === 'completed' || status.status === 'error' || status.status === 'failed') {
          setIsPolling(false);
          isPollingRef.current = false;
          return;
        }

        // Continue polling
        if (isPollingRef.current) {
          timeoutIdRef.current = setTimeout(poll, 3000); // Poll every 3 seconds
        }

      } catch (error) {
        console.error('Failed to get job status:', error);
        if (isPollingRef.current) {
          timeoutIdRef.current = setTimeout(poll, 5000); // Retry after 5 seconds on error
        }
      }
    };

    poll();

    return () => {
      setIsPolling(false);
      isPollingRef.current = false;
      if (timeoutIdRef.current) {
        clearTimeout(timeoutIdRef.current);
        timeoutIdRef.current = null;
      }
    };
  }, [jobId]);

  return { progress, isPolling };
}
