/**
 * Centralized API Configuration
 * All API base URLs should be imported from this file to ensure consistency.
 */

// Gateway API (port 8000) - Main API gateway
// Production Cloud Run URL as fallback
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://gateway-api-489769736562.us-central1.run.app';

// Individual service URLs (for direct access if needed)
export const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || API_BASE_URL;
export const DRIVE_INTEL_URL = import.meta.env.VITE_DRIVE_INTEL_URL || `${API_BASE_URL}/drive-intel`;
export const VIDEO_AGENT_URL = import.meta.env.VITE_VIDEO_AGENT_URL || `${API_BASE_URL}/video-agent`;
export const META_PUBLISHER_URL = import.meta.env.VITE_META_PUBLISHER_URL || `${API_BASE_URL}/meta-publisher`;

// Helper to construct full API URLs
export const apiUrl = (path: string): string => {
  const base = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${cleanPath}`;
};
