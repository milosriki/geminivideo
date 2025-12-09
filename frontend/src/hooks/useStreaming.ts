import { useState, useEffect, useCallback, useRef } from 'react';

interface StreamingOptions {
  onMessage?: (data: any) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

export function useStreaming(url: string, options: StreamingOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [data, setData] = useState<any[]>([]);
  const [error, setError] = useState<Error | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
      reconnectAttemptsRef.current = 0;
    };

    eventSource.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        setData(prev => [...prev, parsedData]);
        options.onMessage?.(parsedData);
      } catch (e) {
        console.error('Failed to parse SSE data:', e);
      }
    };

    eventSource.onerror = (e) => {
      setIsConnected(false);
      const err = new Error('SSE connection error');
      setError(err);
      options.onError?.(err);

      eventSource.close();

      // Attempt reconnect
      const maxAttempts = options.reconnectAttempts ?? 3;
      if (reconnectAttemptsRef.current < maxAttempts) {
        reconnectAttemptsRef.current++;
        const delay = options.reconnectDelay ?? 2000;
        setTimeout(connect, delay * reconnectAttemptsRef.current);
      }
    };

    return () => {
      eventSource.close();
    };
  }, [url, options]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
  }, []);

  const clearData = useCallback(() => {
    setData([]);
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connect,
    disconnect,
    isConnected,
    data,
    error,
    clearData
  };
}

// Specific hook for campaign metrics streaming
export function useCampaignMetricsStream(campaignId: string) {
  const baseUrl = process.env.REACT_APP_API_URL || '';
  return useStreaming(`${baseUrl}/api/stream/campaign-metrics/${campaignId}`);
}

// Specific hook for A/B test results streaming
export function useABTestResultsStream(testId: string) {
  const baseUrl = process.env.REACT_APP_API_URL || '';
  return useStreaming(`${baseUrl}/api/stream/ab-test-results/${testId}`);
}

// Specific hook for render progress streaming
export function useRenderProgressStream(jobId: string) {
  const baseUrl = process.env.REACT_APP_API_URL || '';
  return useStreaming(`${baseUrl}/api/stream/render-progress/${jobId}`);
}
