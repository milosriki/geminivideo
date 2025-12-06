/**
 * useWebSocket Hook
 * React hook for WebSocket connections with channel subscriptions
 */

import { useEffect, useRef, useState, useCallback } from 'react';

export interface WebSocketOptions {
  onMessage?: (event: any) => void;
  onError?: (error: Error) => void;
  onOpen?: () => void;
  onClose?: () => void;
  autoConnect?: boolean;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

export interface WebSocketHookResult {
  isConnected: boolean;
  error: Error | null;
  send: (data: any) => void;
  subscribe: (channel: string, id?: string) => void;
  unsubscribe: (channel: string) => void;
  connect: () => void;
  disconnect: () => void;
}

/**
 * Hook for WebSocket connections
 */
export function useWebSocket(
  url: string | null,
  options: WebSocketOptions = {}
): WebSocketHookResult {
  const {
    onMessage,
    onError,
    onOpen,
    onClose,
    autoConnect = true,
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    heartbeatInterval = 30000
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const heartbeatIntervalRef = useRef<NodeJS.Timeout>();

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setIsConnected(false);
      onClose?.();
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = undefined;
    }

    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = undefined;
    }
  }, [onClose]);

  const send = useCallback((data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  const subscribe = useCallback((channel: string, id?: string) => {
    send({
      type: 'subscribe',
      channel: {
        type: channel,
        id
      }
    });
  }, [send]);

  const unsubscribe = useCallback((channel: string) => {
    send({
      type: 'unsubscribe',
      channel: {
        type: channel
      }
    });
  }, [send]);

  const connect = useCallback(() => {
    if (!url) return;

    // Close existing connection
    disconnect();

    setError(null);

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        onOpen?.();

        // Start heartbeat
        heartbeatIntervalRef.current = setInterval(() => {
          send({ type: 'ping' });
        }, heartbeatInterval);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage?.(data);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = (e) => {
        const error = new Error('WebSocket connection error');
        setError(error);
        onError?.(error);
      };

      ws.onclose = () => {
        setIsConnected(false);
        onClose?.();

        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = undefined;
        }

        // Attempt reconnection
        if (reconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

    } catch (e) {
      const error = e instanceof Error ? e : new Error('Failed to connect to WebSocket');
      setError(error);
      onError?.(error);
    }
  }, [url, disconnect, onMessage, onError, onOpen, onClose, send, reconnect, reconnectInterval, maxReconnectAttempts, heartbeatInterval]);

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
    isConnected,
    error,
    send,
    subscribe,
    unsubscribe,
    connect,
    disconnect
  };
}

/**
 * Hook for subscribing to real-time job progress
 */
export function useJobProgress(jobId: string | null) {
  const [progress, setProgress] = useState<any>(null);
  const [status, setStatus] = useState<string>('');

  const wsUrl = jobId ? `ws://localhost:8000/ws?userId=demo` : null;

  const { isConnected, error, subscribe, unsubscribe } = useWebSocket(wsUrl, {
    onMessage: (event) => {
      if (event.type === 'job_progress' && event.jobId === jobId) {
        setProgress(event);
        setStatus(event.status);
      }
    }
  });

  useEffect(() => {
    if (isConnected && jobId) {
      subscribe('job_progress', jobId);
    }

    return () => {
      if (jobId) {
        unsubscribe('job_progress');
      }
    };
  }, [isConnected, jobId, subscribe, unsubscribe]);

  return {
    progress,
    status,
    isConnected,
    error
  };
}

/**
 * Hook for subscribing to real-time alerts
 */
export function useRealtimeAlerts(userId?: string) {
  const [alerts, setAlerts] = useState<any[]>([]);

  const wsUrl = userId ? `ws://localhost:8000/ws?userId=${userId}` : null;

  const { isConnected, error, subscribe, unsubscribe } = useWebSocket(wsUrl, {
    onMessage: (event) => {
      if (event.type === 'alert') {
        setAlerts(prev => [event, ...prev].slice(0, 50)); // Keep last 50 alerts
      }
    }
  });

  useEffect(() => {
    if (isConnected) {
      subscribe('alerts');
    }

    return () => {
      unsubscribe('alerts');
    };
  }, [isConnected, subscribe, unsubscribe]);

  const clearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  const dismissAlert = useCallback((alertId: string) => {
    setAlerts(prev => prev.filter(a => a.alertId !== alertId));
  }, []);

  return {
    alerts,
    isConnected,
    error,
    clearAlerts,
    dismissAlert
  };
}

/**
 * Hook for subscribing to live metrics
 */
export function useLiveMetrics(entityId: string | null, entityType: string) {
  const [metrics, setMetrics] = useState<Record<string, any>>({});

  const wsUrl = entityId ? `ws://localhost:8000/ws?userId=demo` : null;

  const { isConnected, error, subscribe, unsubscribe } = useWebSocket(wsUrl, {
    onMessage: (event) => {
      if (event.type === 'live_metric_update' && event.entityId === entityId) {
        setMetrics(prev => ({
          ...prev,
          [event.metric]: {
            value: event.value,
            delta: event.delta,
            deltaPercent: event.deltaPercent,
            timestamp: event.timestamp
          }
        }));
      }
    }
  });

  useEffect(() => {
    if (isConnected && entityId) {
      subscribe('live_metrics', entityId);
    }

    return () => {
      if (entityId) {
        unsubscribe('live_metrics');
      }
    };
  }, [isConnected, entityId, subscribe, unsubscribe]);

  return {
    metrics,
    isConnected,
    error
  };
}
