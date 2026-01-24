/**
 * useSSE Hook
 * React hook for Server-Sent Events (SSE) streaming
 */

import { useEffect, useRef, useState, useCallback } from 'react';

export interface SSEOptions {
  onMessage?: (event: any) => void;
  onError?: (error: Error) => void;
  onOpen?: () => void;
  onClose?: () => void;
  autoConnect?: boolean;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export interface SSEHookResult<T = any> {
  data: T | null;
  error: Error | null;
  isConnected: boolean;
  isLoading: boolean;
  connect: () => void;
  disconnect: () => void;
  reconnect: () => void;
}

/**
 * Hook for SSE streaming
 */
export function useSSE<T = any>(
  url: string | null,
  options: SSEOptions = {}
): SSEHookResult<T> {
  const {
    onMessage,
    onError,
    onOpen,
    onClose,
    autoConnect = true,
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
      setIsLoading(false);
      onClose?.();
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = undefined;
    }
  }, [onClose]);

  const connect = useCallback(() => {
    if (!url) return;

    // Close existing connection
    disconnect();

    setIsLoading(true);
    setError(null);

    try {
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setIsConnected(true);
        setIsLoading(false);
        reconnectAttemptsRef.current = 0;
        onOpen?.();
      };

      eventSource.onmessage = (event) => {
        try {
          const parsedData = JSON.parse(event.data);
          setData(parsedData);
          onMessage?.(parsedData);
        } catch (e) {
          console.error('Failed to parse SSE message:', e);
        }
      };

      eventSource.onerror = (e) => {
        const error = new Error('SSE connection error');
        setError(error);
        setIsConnected(false);
        setIsLoading(false);
        onError?.(error);

        // Attempt reconnection
        if (reconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(
            `SSE reconnecting... (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else {
          disconnect();
        }
      };

      // Handle custom event types
      eventSource.addEventListener('complete', (event: any) => {
        try {
          const parsedData = JSON.parse(event.data);
          setData(parsedData);
          onMessage?.(parsedData);
        } catch (e) {
          console.error('Failed to parse complete event:', e);
        }
        disconnect();
      });

      eventSource.addEventListener('error', (event: any) => {
        try {
          const parsedData = JSON.parse(event.data);
          setError(new Error(parsedData.error || 'Unknown error'));
          onError?.(new Error(parsedData.error));
        } catch (e) {
          console.error('Failed to parse error event:', e);
        }
        disconnect();
      });

    } catch (e) {
      const error = e instanceof Error ? e : new Error('Failed to connect to SSE');
      setError(error);
      setIsLoading(false);
      onError?.(error);
    }
  }, [url, disconnect, onMessage, onError, onOpen, reconnect, reconnectInterval, maxReconnectAttempts]);

  const manualReconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect]);

  // Auto-connect on mount or URL change
  useEffect(() => {
    if (autoConnect && url) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [url, autoConnect, connect, disconnect]);

  return {
    data,
    error,
    isConnected,
    isLoading,
    connect,
    disconnect,
    reconnect: manualReconnect
  };
}

/**
 * Hook for streaming AI Council scores
 */
export function useCouncilScoreStream(
  videoUrl: string | null,
  transcript: string | null,
  features?: any
) {
  const [stages, setStages] = useState<Record<string, any>>({});
  const [currentStage, setCurrentStage] = useState<string>('');
  const [finalScore, setFinalScore] = useState<any>(null);

  const url = videoUrl && transcript
    ? `/api/stream/council-score?videoUrl=${encodeURIComponent(videoUrl)}&transcript=${encodeURIComponent(transcript)}&features=${encodeURIComponent(JSON.stringify(features || {}))}`
    : null;

  const { isConnected, isLoading, error, connect, disconnect } = useSSE(url, {
    autoConnect: false,
    onMessage: (event) => {
      if (event.type === 'council_score_stream') {
        setCurrentStage(event.stage);

        if (event.stage === 'complete' && event.finalScore) {
          setFinalScore(event.finalScore);
        } else if (event.model) {
          setStages(prev => ({
            ...prev,
            [event.model]: {
              thinking: event.thinking || prev[event.model]?.thinking || '',
              score: event.score,
              reasoning: event.reasoning,
              isComplete: event.isComplete
            }
          }));
        }
      }
    }
  });

  return {
    stages,
    currentStage,
    finalScore,
    isConnected,
    isLoading,
    error,
    startStreaming: connect,
    stopStreaming: disconnect
  };
}

/**
 * Hook for streaming video render progress
 */
export function useRenderProgressStream(jobId: string | null) {
  const [progress, setProgress] = useState(0);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [totalFrames, setTotalFrames] = useState(0);
  const [stage, setStage] = useState('');
  const [fps, setFps] = useState(0);
  const [estimatedTime, setEstimatedTime] = useState(0);

  const url = jobId ? `/api/stream/render-progress/${jobId}` : null;

  const { isConnected, error, disconnect } = useSSE(url, {
    onMessage: (event) => {
      if (event.type === 'video_render_progress') {
        setProgress(event.progress || 0);
        setCurrentFrame(event.currentFrame || 0);
        setTotalFrames(event.totalFrames || 0);
        setStage(event.stage || '');
        setFps(event.fps || 0);
        setEstimatedTime(event.estimatedTimeRemaining || 0);
      }
    }
  });

  return {
    progress,
    currentFrame,
    totalFrames,
    stage,
    fps,
    estimatedTime,
    isConnected,
    error,
    disconnect
  };
}

export interface CampaignMetrics {
  impressions: number;
  clicks: number;
  ctr: number;
  spend: number;
  conversions: number;
  roas: number;
}

/**
 * Hook for streaming campaign metrics
 */
export function useCampaignMetricsStream(campaignId: string | null) {
  const [metrics, setMetrics] = useState<CampaignMetrics | null>(null);
  const [change, setChange] = useState<Partial<CampaignMetrics> | null>(null);

  const url = campaignId ? `/api/stream/campaign-metrics/${campaignId}` : null;

  const { isConnected, error, connect, disconnect } = useSSE(url, {
    autoConnect: false,
    onMessage: (event) => {
      if (event.type === 'campaign_metrics') {
        setMetrics(event.metrics);
        setChange(event.change);
      }
    }
  });

  return {
    metrics,
    change,
    isConnected,
    error,
    startStreaming: connect,
    stopStreaming: disconnect
  };
}
