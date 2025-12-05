/**
 * Demo Mode Hook
 *
 * Manages demo mode state, detects ?demo=true parameter, and stores preference in localStorage.
 * Used for investor presentations with impressive real-looking data.
 */

import { useState, useEffect, useCallback } from 'react';

const DEMO_MODE_KEY = 'demo_mode_enabled';
const DEMO_SESSION_KEY = 'demo_session_id';

export interface DemoModeConfig {
  enabled: boolean;
  sessionId: string | null;
  autoUpdate: boolean; // Enable live-updating charts
  showIndicator: boolean; // Show demo badge in UI
}

export function useDemoMode() {
  const [config, setConfig] = useState<DemoModeConfig>(() => {
    // Check URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const demoParam = urlParams.get('demo');

    // Check localStorage
    const stored = localStorage.getItem(DEMO_MODE_KEY);
    const sessionId = localStorage.getItem(DEMO_SESSION_KEY);

    const enabled = demoParam === 'true' || stored === 'true';

    return {
      enabled,
      sessionId: sessionId || null,
      autoUpdate: enabled,
      showIndicator: enabled
    };
  });

  // Toggle demo mode
  const toggleDemoMode = useCallback(() => {
    setConfig(prev => {
      const newEnabled = !prev.enabled;

      // Store preference
      localStorage.setItem(DEMO_MODE_KEY, String(newEnabled));

      // Generate session ID if enabling
      if (newEnabled && !prev.sessionId) {
        const sessionId = `demo-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        localStorage.setItem(DEMO_SESSION_KEY, sessionId);
        return {
          ...prev,
          enabled: newEnabled,
          sessionId,
          autoUpdate: newEnabled,
          showIndicator: newEnabled
        };
      }

      return {
        ...prev,
        enabled: newEnabled,
        autoUpdate: newEnabled,
        showIndicator: newEnabled
      };
    });
  }, []);

  // Enable demo mode
  const enableDemoMode = useCallback(() => {
    const sessionId = `demo-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem(DEMO_MODE_KEY, 'true');
    localStorage.setItem(DEMO_SESSION_KEY, sessionId);

    setConfig({
      enabled: true,
      sessionId,
      autoUpdate: true,
      showIndicator: true
    });
  }, []);

  // Disable demo mode
  const disableDemoMode = useCallback(() => {
    localStorage.removeItem(DEMO_MODE_KEY);
    localStorage.removeItem(DEMO_SESSION_KEY);

    setConfig({
      enabled: false,
      sessionId: null,
      autoUpdate: false,
      showIndicator: false
    });
  }, []);

  // Update config
  const updateConfig = useCallback((updates: Partial<DemoModeConfig>) => {
    setConfig(prev => ({ ...prev, ...updates }));
  }, []);

  // Reset demo data on server
  const resetDemoData = useCallback(async () => {
    if (!config.enabled) return;

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/demo/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error('Failed to reset demo data');
      }

      const data = await response.json();
      console.log('Demo data reset:', data);

      // Reload page to fetch fresh data
      window.location.reload();
    } catch (error) {
      console.error('Error resetting demo data:', error);
    }
  }, [config.enabled]);

  // Listen for URL parameter changes
  useEffect(() => {
    const handleUrlChange = () => {
      const urlParams = new URLSearchParams(window.location.search);
      const demoParam = urlParams.get('demo');

      if (demoParam === 'true' && !config.enabled) {
        enableDemoMode();
      } else if (demoParam === 'false' && config.enabled) {
        disableDemoMode();
      }
    };

    window.addEventListener('popstate', handleUrlChange);
    return () => window.removeEventListener('popstate', handleUrlChange);
  }, [config.enabled, enableDemoMode, disableDemoMode]);

  return {
    ...config,
    toggleDemoMode,
    enableDemoMode,
    disableDemoMode,
    updateConfig,
    resetDemoData
  };
}

/**
 * Get demo API URL with demo mode parameter
 */
export function getDemoApiUrl(endpoint: string, demoMode: boolean): string {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  if (!demoMode) {
    return `${apiUrl}${endpoint}`;
  }

  // Replace /api/ with /api/demo/ for demo endpoints
  const demoEndpoint = endpoint.replace('/api/', '/api/demo/');
  return `${apiUrl}${demoEndpoint}`;
}

/**
 * Fetch data with automatic demo mode switching
 */
export async function fetchWithDemoMode(
  endpoint: string,
  demoMode: boolean,
  options?: RequestInit
): Promise<Response> {
  const url = getDemoApiUrl(endpoint, demoMode);

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {})
    }
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.statusText}`);
  }

  return response;
}
