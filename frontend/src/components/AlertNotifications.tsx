/**
 * Alert Notifications Component
 * Agent 16 - Real-Time Performance Alerts
 *
 * Features:
 * - Bell icon with badge count
 * - Dropdown list of recent alerts
 * - Alert detail modal
 * - Sound notification option
 * - WebSocket real-time updates
 */

import React, { useState, useEffect, useRef } from 'react';
import { Bell, X, CheckCircle, AlertTriangle, AlertCircle, Info, Volume2, VolumeX } from 'lucide-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

interface Alert {
  alert_id: string;
  rule_id: string;
  alert_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  message: string;
  campaign_id: string;
  campaign_name: string;
  ad_id?: string;
  metric_name: string;
  metric_value: number;
  threshold_value: number;
  details: Record<string, any>;
  timestamp: string;
  acknowledged: boolean;
  acknowledged_at?: string;
  acknowledged_by?: string;
  resolved: boolean;
  resolved_at?: string;
  notification_status: Record<string, boolean>;
}

interface AlertNotificationsProps {
  userId?: string;
  soundEnabled?: boolean;
  autoConnect?: boolean;
}

export const AlertNotifications: React.FC<AlertNotificationsProps> = ({
  userId = 'current_user',
  soundEnabled: initialSoundEnabled = true,
  autoConnect = true
}) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [soundEnabled, setSoundEnabled] = useState(initialSoundEnabled);
  const [wsConnected, setWsConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  // Initialize audio for notifications
  useEffect(() => {
    // Create audio element for alert sound
    audioRef.current = new Audio('/notification.mp3'); // Add a notification sound file
  }, []);

  // WebSocket connection for real-time alerts
  useEffect(() => {
    if (!autoConnect) return;

    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(`${WS_URL}/ws/alerts`);

        ws.onopen = () => {
          console.log('Alert WebSocket connected');
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === 'alert') {
              // New alert received
              const newAlert = data.data as Alert;
              setAlerts((prev) => [newAlert, ...prev]);
              setUnreadCount((prev) => prev + 1);

              // Play sound if enabled and critical/high severity
              if (soundEnabled && ['critical', 'high'].includes(newAlert.severity)) {
                audioRef.current?.play().catch(err => console.error('Audio play failed:', err));
              }

              // Show browser notification
              if ('Notification' in window && Notification.permission === 'granted') {
                new Notification(newAlert.title, {
                  body: newAlert.message,
                  icon: '/logo.png',
                  tag: newAlert.alert_id
                });
              }
            } else if (data.type === 'alert_acknowledged' || data.type === 'alert_resolved') {
              // Update alert status
              setAlerts((prev) =>
                prev.map((alert) =>
                  alert.alert_id === data.alert_id
                    ? {
                        ...alert,
                        acknowledged: data.type === 'alert_acknowledged',
                        resolved: data.type === 'alert_resolved'
                      }
                    : alert
                )
              );
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.onclose = () => {
          console.log('Alert WebSocket disconnected');
          setWsConnected(false);

          // Attempt to reconnect after 5 seconds
          setTimeout(connectWebSocket, 5000);
        };

        ws.onerror = (error) => {
          console.error('Alert WebSocket error:', error);
        };

        wsRef.current = ws;
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [autoConnect, soundEnabled]);

  // Fetch initial alerts
  useEffect(() => {
    fetchAlerts();

    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/alerts`, {
        params: { limit: 50 }
      });

      const fetchedAlerts = response.data.alerts || [];
      setAlerts(fetchedAlerts);
      setUnreadCount(fetchedAlerts.filter((a: Alert) => !a.acknowledged).length);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    }
  };

  const acknowledgeAlert = async (alertId: string) => {
    try {
      await axios.put(`${API_URL}/api/alerts/${alertId}/acknowledge`, {
        user_id: userId
      });

      setAlerts((prev) =>
        prev.map((alert) =>
          alert.alert_id === alertId ? { ...alert, acknowledged: true } : alert
        )
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const resolveAlert = async (alertId: string) => {
    try {
      await axios.put(`${API_URL}/api/alerts/${alertId}/resolve`);

      setAlerts((prev) => prev.filter((alert) => alert.alert_id !== alertId));
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'high':
        return <AlertCircle className="w-5 h-5 text-orange-500" />;
      case 'medium':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'low':
        return <Info className="w-5 h-5 text-blue-500" />;
      default:
        return <Info className="w-5 h-5 text-gray-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 border-red-500 text-red-800';
      case 'high':
        return 'bg-orange-100 border-orange-500 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 border-yellow-500 text-yellow-800';
      case 'low':
        return 'bg-blue-100 border-blue-500 text-blue-800';
      default:
        return 'bg-gray-100 border-gray-500 text-gray-800';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <>
      {/* Bell Icon with Badge */}
      <div className="relative" ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="relative p-2 rounded-full hover:bg-gray-100 transition-colors"
          aria-label="Notifications"
        >
          <Bell className="w-6 h-6 text-gray-700" />
          {unreadCount > 0 && (
            <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-500 rounded-full">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
          {wsConnected && (
            <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></span>
          )}
        </button>

        {/* Dropdown */}
        {isOpen && (
          <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-[600px] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between bg-gray-50">
              <h3 className="text-lg font-semibold text-gray-800">Alerts</h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSoundEnabled(!soundEnabled)}
                  className="p-1 hover:bg-gray-200 rounded"
                  title={soundEnabled ? 'Mute notifications' : 'Enable sound'}
                >
                  {soundEnabled ? (
                    <Volume2 className="w-4 h-4 text-gray-600" />
                  ) : (
                    <VolumeX className="w-4 h-4 text-gray-400" />
                  )}
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-gray-200 rounded"
                >
                  <X className="w-4 h-4 text-gray-600" />
                </button>
              </div>
            </div>

            {/* Alert List */}
            <div className="overflow-y-auto flex-1">
              {alerts.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <Bell className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>No alerts</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-100">
                  {alerts.map((alert) => (
                    <div
                      key={alert.alert_id}
                      className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                        !alert.acknowledged ? 'bg-blue-50' : ''
                      }`}
                      onClick={() => setSelectedAlert(alert)}
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 mt-1">
                          {getSeverityIcon(alert.severity)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <p className="text-sm font-semibold text-gray-900 truncate">
                              {alert.title}
                            </p>
                            <span className="text-xs text-gray-500 ml-2 flex-shrink-0">
                              {formatTimestamp(alert.timestamp)}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 line-clamp-2">
                            {alert.message}
                          </p>
                          <div className="flex items-center gap-2 mt-2">
                            <span
                              className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getSeverityColor(
                                alert.severity
                              )}`}
                            >
                              {alert.severity.toUpperCase()}
                            </span>
                            {!alert.acknowledged && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  acknowledgeAlert(alert.alert_id);
                                }}
                                className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                              >
                                Acknowledge
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
              <button
                onClick={() => {
                  setIsOpen(false);
                  // Navigate to alerts page
                  window.location.href = '/alerts';
                }}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                View all alerts →
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Alert Detail Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className={`px-6 py-4 border-l-4 ${getSeverityColor(selectedAlert.severity)}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {getSeverityIcon(selectedAlert.severity)}
                  <h2 className="text-xl font-bold text-gray-900">
                    {selectedAlert.title}
                  </h2>
                </div>
                <button
                  onClick={() => setSelectedAlert(null)}
                  className="p-1 hover:bg-gray-200 rounded"
                >
                  <X className="w-5 h-5 text-gray-600" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-1">Message</h3>
                  <p className="text-gray-900">{selectedAlert.message}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-1">Campaign</h3>
                    <p className="text-gray-900">{selectedAlert.campaign_name}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-1">Metric</h3>
                    <p className="text-gray-900">{selectedAlert.metric_name}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-1">Current Value</h3>
                    <p className="text-gray-900">{selectedAlert.metric_value.toFixed(2)}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-1">Threshold</h3>
                    <p className="text-gray-900">{selectedAlert.threshold_value.toFixed(2)}</p>
                  </div>
                </div>

                {selectedAlert.details.action && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="text-sm font-semibold text-blue-900 mb-1">
                      Recommended Action
                    </h3>
                    <p className="text-blue-800">{selectedAlert.details.action}</p>
                  </div>
                )}

                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-1">Timestamp</h3>
                  <p className="text-gray-900">
                    {new Date(selectedAlert.timestamp).toLocaleString()}
                  </p>
                </div>

                {selectedAlert.acknowledged && (
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="w-4 h-4" />
                    <span className="text-sm">
                      Acknowledged by {selectedAlert.acknowledged_by || 'user'}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex gap-3 justify-end">
              {!selectedAlert.acknowledged && (
                <button
                  onClick={() => {
                    acknowledgeAlert(selectedAlert.alert_id);
                    setSelectedAlert(null);
                  }}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Acknowledge
                </button>
              )}
              <button
                onClick={() => {
                  resolveAlert(selectedAlert.alert_id);
                  setSelectedAlert(null);
                }}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
              >
                Resolve
              </button>
              <button
                onClick={() => setSelectedAlert(null)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default AlertNotifications;
