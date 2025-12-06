/**
 * Admin Panel - Connection & Credential Management
 *
 * Manages all external service connections:
 * - Foreplay (winning ads)
 * - Creatify (URL-to-video)
 * - HubSpot (CRM)
 * - AnyTrack (conversions)
 * - Meta Marketing (FB/IG ads)
 * - AI Providers (OpenAI, Gemini, Together, Fireworks)
 */

import { useState, useEffect, useCallback } from "react";
import {
  ShieldCheckIcon,
  WifiIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  KeyIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon,
  CloudArrowDownIcon,
} from "@heroicons/react/24/outline";

// Types
type ServiceType =
  | "foreplay"
  | "creatify"
  | "hubspot"
  | "anytrack"
  | "meta"
  | "google_ads"
  | "together_ai"
  | "fireworks_ai"
  | "openai"
  | "gemini";

type ConnectionStatus = "connected" | "disconnected" | "error" | "not_configured" | "testing";

interface ServiceStatus {
  service: ServiceType;
  status: ConnectionStatus;
  last_tested?: string;
  error_message?: string;
  is_configured: boolean;
}

interface ConnectionTestResult {
  service: ServiceType;
  status: ConnectionStatus;
  message: string;
  response_time_ms?: number;
  account_info?: Record<string, unknown>;
}

interface ServiceConfig {
  name: string;
  description: string;
  icon: string;
  fields: {
    name: string;
    key: string;
    type: "text" | "password";
    required: boolean;
    placeholder: string;
  }[];
  category: "data_sources" | "ai_providers" | "marketing" | "analytics";
}

// Service configurations
const SERVICE_CONFIGS: Record<ServiceType, ServiceConfig> = {
  foreplay: {
    name: "Foreplay",
    description: "Winning ads database for pattern learning",
    icon: "🎯",
    category: "data_sources",
    fields: [
      {
        name: "API Key",
        key: "api_key",
        type: "password",
        required: true,
        placeholder: "fp_xxxxxxxxxxxxxx",
      },
    ],
  },
  creatify: {
    name: "Creatify",
    description: "AI video generation from URLs",
    icon: "🎬",
    category: "data_sources",
    fields: [
      {
        name: "API ID",
        key: "api_id",
        type: "text",
        required: true,
        placeholder: "Your Creatify API ID",
      },
      {
        name: "API Key",
        key: "api_key",
        type: "password",
        required: true,
        placeholder: "Your Creatify API Key",
      },
    ],
  },
  hubspot: {
    name: "HubSpot",
    description: "CRM integration for deal & contact sync",
    icon: "🔶",
    category: "marketing",
    fields: [
      {
        name: "Access Token",
        key: "access_token",
        type: "password",
        required: true,
        placeholder: "pat-xxxxxx-xxxxxx-xxxxxx",
      },
    ],
  },
  anytrack: {
    name: "AnyTrack",
    description: "Conversion tracking & attribution",
    icon: "📊",
    category: "analytics",
    fields: [
      {
        name: "API Key",
        key: "api_key",
        type: "password",
        required: true,
        placeholder: "Your AnyTrack API Key",
      },
      {
        name: "Account ID",
        key: "account_id",
        type: "text",
        required: true,
        placeholder: "Your Account ID",
      },
    ],
  },
  meta: {
    name: "Meta Marketing",
    description: "Facebook & Instagram ads management",
    icon: "📘",
    category: "marketing",
    fields: [
      {
        name: "Access Token",
        key: "access_token",
        type: "password",
        required: true,
        placeholder: "EAAxxxxxxx...",
      },
      {
        name: "Ad Account ID",
        key: "account_id",
        type: "text",
        required: false,
        placeholder: "act_xxxxxxxxxx",
      },
    ],
  },
  google_ads: {
    name: "Google Ads",
    description: "Google advertising platform",
    icon: "🔍",
    category: "marketing",
    fields: [
      {
        name: "Developer Token",
        key: "api_key",
        type: "password",
        required: true,
        placeholder: "Your Developer Token",
      },
    ],
  },
  together_ai: {
    name: "Together AI",
    description: "Llama 4 inference provider",
    icon: "🦙",
    category: "ai_providers",
    fields: [
      {
        name: "API Key",
        key: "api_key",
        type: "password",
        required: true,
        placeholder: "Your Together AI API Key",
      },
    ],
  },
  fireworks_ai: {
    name: "Fireworks AI",
    description: "Llama 4 inference provider (backup)",
    icon: "🔥",
    category: "ai_providers",
    fields: [
      {
        name: "API Key",
        key: "api_key",
        type: "password",
        required: true,
        placeholder: "Your Fireworks API Key",
      },
    ],
  },
  openai: {
    name: "OpenAI",
    description: "GPT-4 and ChatGPT models",
    icon: "🤖",
    category: "ai_providers",
    fields: [
      {
        name: "API Key",
        key: "api_key",
        type: "password",
        required: true,
        placeholder: "sk-xxxxxxxxxxxxxxxx",
      },
    ],
  },
  gemini: {
    name: "Google Gemini",
    description: "Google AI models",
    icon: "✨",
    category: "ai_providers",
    fields: [
      {
        name: "API Key",
        key: "api_key",
        type: "password",
        required: true,
        placeholder: "Your Gemini API Key",
      },
    ],
  },
};

const ADMIN_API_URL = import.meta.env.VITE_ADMIN_API_URL || "http://localhost:8010";

// Status badge component
function StatusBadge({ status }: { status: ConnectionStatus }) {
  const config = {
    connected: {
      color: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
      icon: CheckCircleIcon,
      label: "Connected",
    },
    disconnected: {
      color: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400",
      icon: XCircleIcon,
      label: "Disconnected",
    },
    error: {
      color: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
      icon: ExclamationTriangleIcon,
      label: "Error",
    },
    not_configured: {
      color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
      icon: KeyIcon,
      label: "Not Configured",
    },
    testing: {
      color: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
      icon: ArrowPathIcon,
      label: "Testing...",
    },
  };

  const { color, icon: Icon, label } = config[status];

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${color}`}>
      <Icon className={`w-3.5 h-3.5 ${status === "testing" ? "animate-spin" : ""}`} />
      {label}
    </span>
  );
}

// Service card component
function ServiceCard({
  service,
  status,
  onConfigure,
  onTest,
  onDelete,
  onSync,
}: {
  service: ServiceType;
  status: ServiceStatus;
  onConfigure: (service: ServiceType) => void;
  onTest: (service: ServiceType) => void;
  onDelete: (service: ServiceType) => void;
  onSync?: (service: ServiceType) => void;
}) {
  const config = SERVICE_CONFIGS[service];
  const hasSyncFeature = ["foreplay", "creatify", "meta"].includes(service);

  return (
    <div className="bg-white dark:bg-zinc-800 rounded-xl border border-zinc-200 dark:border-zinc-700 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{config.icon}</span>
          <div>
            <h3 className="font-semibold text-zinc-900 dark:text-white">{config.name}</h3>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">{config.description}</p>
          </div>
        </div>
        <StatusBadge status={status.status} />
      </div>

      {status.error_message && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg text-sm text-red-700 dark:text-red-400">
          {status.error_message}
        </div>
      )}

      {status.last_tested && (
        <p className="text-xs text-zinc-400 mb-4">
          Last tested: {new Date(status.last_tested).toLocaleString()}
        </p>
      )}

      <div className="flex items-center gap-2">
        <button
          onClick={() => onConfigure(service)}
          className="flex-1 px-3 py-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 bg-zinc-100 dark:bg-zinc-700 rounded-lg hover:bg-zinc-200 dark:hover:bg-zinc-600 transition-colors"
        >
          <KeyIcon className="w-4 h-4 inline mr-1.5" />
          Configure
        </button>

        <button
          onClick={() => onTest(service)}
          disabled={!status.is_configured}
          className="px-3 py-2 text-sm font-medium text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <WifiIcon className="w-4 h-4 inline mr-1.5" />
          Test
        </button>

        {hasSyncFeature && onSync && (
          <button
            onClick={() => onSync(service)}
            disabled={status.status !== "connected"}
            className="px-3 py-2 text-sm font-medium text-purple-700 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/30 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <CloudArrowDownIcon className="w-4 h-4 inline mr-1.5" />
            Sync
          </button>
        )}

        {status.is_configured && (
          <button
            onClick={() => onDelete(service)}
            className="px-3 py-2 text-sm font-medium text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/30 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors"
          >
            <TrashIcon className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}

// Configuration modal
function ConfigureModal({
  service,
  onClose,
  onSave,
}: {
  service: ServiceType | null;
  onClose: () => void;
  onSave: (service: ServiceType, credentials: Record<string, string>) => void;
}) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState(false);

  if (!service) return null;

  const config = SERVICE_CONFIGS[service];

  const handleSave = async () => {
    setSaving(true);
    await onSave(service, values);
    setSaving(false);
    onClose();
  };

  const allRequiredFilled = config.fields
    .filter((f) => f.required)
    .every((f) => values[f.key]?.trim());

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-zinc-800 rounded-2xl shadow-xl w-full max-w-md mx-4">
        <div className="p-6 border-b border-zinc-200 dark:border-zinc-700">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{config.icon}</span>
            <div>
              <h2 className="text-lg font-semibold text-zinc-900 dark:text-white">
                Configure {config.name}
              </h2>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">{config.description}</p>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {config.fields.map((field) => (
            <div key={field.key}>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                {field.name}
                {field.required && <span className="text-red-500 ml-1">*</span>}
              </label>
              <div className="relative">
                <input
                  type={field.type === "password" && !showPasswords[field.key] ? "password" : "text"}
                  value={values[field.key] || ""}
                  onChange={(e) => setValues({ ...values, [field.key]: e.target.value })}
                  placeholder={field.placeholder}
                  className="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {field.type === "password" && (
                  <button
                    type="button"
                    onClick={() =>
                      setShowPasswords({ ...showPasswords, [field.key]: !showPasswords[field.key] })
                    }
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
                  >
                    {showPasswords[field.key] ? (
                      <EyeSlashIcon className="w-5 h-5" />
                    ) : (
                      <EyeIcon className="w-5 h-5" />
                    )}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="p-6 border-t border-zinc-200 dark:border-zinc-700 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-700 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!allRequiredFilled || saving}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? "Saving..." : "Save Credentials"}
          </button>
        </div>
      </div>
    </div>
  );
}

// Main Admin Panel component
export default function AdminPanel() {
  const [statuses, setStatuses] = useState<ServiceStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [testingAll, setTestingAll] = useState(false);
  const [configureService, setConfigureService] = useState<ServiceType | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });

  // Fetch status on mount
  const fetchStatuses = useCallback(async () => {
    if (!authToken) return;

    try {
      const response = await fetch(`${ADMIN_API_URL}/services/status`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });

      if (response.ok) {
        const data = await response.json();
        setStatuses(data);
      }
    } catch (error) {
      console.error("Failed to fetch statuses:", error);
    } finally {
      setLoading(false);
    }
  }, [authToken]);

  useEffect(() => {
    if (authToken) {
      fetchStatuses();
    } else {
      setLoading(false);
    }
  }, [authToken, fetchStatuses]);

  // Login handler
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);

    try {
      const response = await fetch(`${ADMIN_API_URL}/auth/login`, {
        method: "POST",
        headers: {
          Authorization: `Basic ${btoa(`${loginForm.username}:${loginForm.password}`)}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAuthToken(data.token);
        localStorage.setItem("admin_token", data.token);
      } else {
        setLoginError("Invalid credentials");
      }
    } catch {
      setLoginError("Connection failed");
    }
  };

  // Check for stored token
  useEffect(() => {
    const storedToken = localStorage.getItem("admin_token");
    if (storedToken) {
      setAuthToken(storedToken);
    }
  }, []);

  // Test connection
  const testConnection = async (service: ServiceType) => {
    if (!authToken) return;

    // Update local status to testing
    setStatuses((prev) =>
      prev.map((s) => (s.service === service ? { ...s, status: "testing" } : s))
    );

    try {
      const response = await fetch(`${ADMIN_API_URL}/services/${service}/test`, {
        method: "POST",
        headers: { Authorization: `Bearer ${authToken}` },
      });

      if (response.ok) {
        const result: ConnectionTestResult = await response.json();
        setStatuses((prev) =>
          prev.map((s) =>
            s.service === service
              ? {
                  ...s,
                  status: result.status,
                  error_message: result.status === "error" ? result.message : undefined,
                  last_tested: new Date().toISOString(),
                }
              : s
          )
        );
      }
    } catch (error) {
      console.error("Test failed:", error);
    }
  };

  // Test all connections
  const testAllConnections = async () => {
    if (!authToken) return;

    setTestingAll(true);

    try {
      const response = await fetch(`${ADMIN_API_URL}/services/test-all`, {
        method: "POST",
        headers: { Authorization: `Bearer ${authToken}` },
      });

      if (response.ok) {
        await fetchStatuses();
      }
    } catch (error) {
      console.error("Test all failed:", error);
    } finally {
      setTestingAll(false);
    }
  };

  // Save credentials
  const saveCredentials = async (service: ServiceType, credentials: Record<string, string>) => {
    if (!authToken) return;

    try {
      const response = await fetch(`${ADMIN_API_URL}/services/${service}/credentials`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${authToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          service,
          ...credentials,
        }),
      });

      if (response.ok) {
        await fetchStatuses();
      }
    } catch (error) {
      console.error("Save failed:", error);
    }
  };

  // Delete credentials
  const deleteCredentials = async (service: ServiceType) => {
    if (!authToken) return;

    if (!confirm(`Delete credentials for ${SERVICE_CONFIGS[service].name}?`)) return;

    try {
      const response = await fetch(`${ADMIN_API_URL}/services/${service}/credentials`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${authToken}` },
      });

      if (response.ok) {
        await fetchStatuses();
      }
    } catch (error) {
      console.error("Delete failed:", error);
    }
  };

  // Sync data
  const syncData = async (service: ServiceType) => {
    if (!authToken) return;

    try {
      const endpoint =
        service === "foreplay"
          ? "/sync/foreplay"
          : service === "creatify"
            ? "/sync/creatify"
            : "/sync/meta-historical";

      const response = await fetch(`${ADMIN_API_URL}${endpoint}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${authToken}` },
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Sync completed: ${JSON.stringify(result)}`);
      }
    } catch (error) {
      console.error("Sync failed:", error);
      alert("Sync failed");
    }
  };

  // Logout
  const logout = () => {
    setAuthToken(null);
    localStorage.removeItem("admin_token");
  };

  // Login form
  if (!authToken) {
    return (
      <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-zinc-800 rounded-2xl shadow-xl w-full max-w-md p-8">
          <div className="text-center mb-8">
            <ShieldCheckIcon className="w-12 h-12 mx-auto text-blue-600 mb-4" />
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">Admin Panel</h1>
            <p className="text-zinc-500 dark:text-zinc-400 mt-2">
              Sign in to manage service connections
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            {loginError && (
              <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg text-sm text-red-700 dark:text-red-400">
                {loginError}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                Username
              </label>
              <input
                type="text"
                value={loginForm.username}
                onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                className="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="admin"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                Password
              </label>
              <input
                type="password"
                value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                className="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-lg text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter password"
              />
            </div>

            <button
              type="submit"
              className="w-full px-4 py-2.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              Sign In
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900 flex items-center justify-center">
        <ArrowPathIcon className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  // Group services by category
  const categories = {
    data_sources: { title: "Data Sources", services: [] as ServiceType[] },
    ai_providers: { title: "AI Providers", services: [] as ServiceType[] },
    marketing: { title: "Marketing Platforms", services: [] as ServiceType[] },
    analytics: { title: "Analytics & Tracking", services: [] as ServiceType[] },
  };

  Object.entries(SERVICE_CONFIGS).forEach(([service, config]) => {
    categories[config.category].services.push(service as ServiceType);
  });

  // Calculate stats
  const connectedCount = statuses.filter((s) => s.status === "connected").length;
  const configuredCount = statuses.filter((s) => s.is_configured).length;
  const errorCount = statuses.filter((s) => s.status === "error").length;

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-white flex items-center gap-3">
              <ShieldCheckIcon className="w-8 h-8 text-blue-600" />
              Admin Panel
            </h1>
            <p className="text-zinc-500 dark:text-zinc-400 mt-1">
              Manage external service connections and credentials
            </p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={testAllConnections}
              disabled={testingAll}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              <ArrowPathIcon className={`w-4 h-4 ${testingAll ? "animate-spin" : ""}`} />
              {testingAll ? "Testing..." : "Test All Connections"}
            </button>
            <button
              onClick={logout}
              className="px-4 py-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors"
            >
              Logout
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mt-6">
          <div className="bg-white dark:bg-zinc-800 rounded-xl p-4 border border-zinc-200 dark:border-zinc-700">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Total Services</p>
            <p className="text-2xl font-bold text-zinc-900 dark:text-white">
              {Object.keys(SERVICE_CONFIGS).length}
            </p>
          </div>
          <div className="bg-white dark:bg-zinc-800 rounded-xl p-4 border border-zinc-200 dark:border-zinc-700">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Configured</p>
            <p className="text-2xl font-bold text-blue-600">{configuredCount}</p>
          </div>
          <div className="bg-white dark:bg-zinc-800 rounded-xl p-4 border border-zinc-200 dark:border-zinc-700">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Connected</p>
            <p className="text-2xl font-bold text-green-600">{connectedCount}</p>
          </div>
          <div className="bg-white dark:bg-zinc-800 rounded-xl p-4 border border-zinc-200 dark:border-zinc-700">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Errors</p>
            <p className="text-2xl font-bold text-red-600">{errorCount}</p>
          </div>
        </div>
      </div>

      {/* Service Categories */}
      <div className="max-w-7xl mx-auto space-y-8">
        {Object.entries(categories).map(([key, category]) => (
          <div key={key}>
            <h2 className="text-lg font-semibold text-zinc-900 dark:text-white mb-4">
              {category.title}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {category.services.map((service) => {
                const status = statuses.find((s) => s.service === service) || {
                  service,
                  status: "not_configured" as ConnectionStatus,
                  is_configured: false,
                };

                return (
                  <ServiceCard
                    key={service}
                    service={service}
                    status={status}
                    onConfigure={setConfigureService}
                    onTest={testConnection}
                    onDelete={deleteCredentials}
                    onSync={syncData}
                  />
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Configure Modal */}
      <ConfigureModal
        service={configureService}
        onClose={() => setConfigureService(null)}
        onSave={saveCredentials}
      />
    </div>
  );
}
