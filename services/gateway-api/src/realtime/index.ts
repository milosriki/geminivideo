/**
 * Real-time Streaming Module
 * Exports all real-time functionality for SSE, WebSocket, and Channels
 */

export * from './events';
export * from './channels';
export * from './websocket-manager';
export * from './sse-manager';

// Re-export convenience functions
export {
  getChannelManager,
  initializeChannelManager,
  shutdownChannelManager
} from './channels';

export {
  initializeWebSocketManager,
  getWebSocketManager,
  shutdownWebSocketManager
} from './websocket-manager';

export {
  getSSEManager,
  shutdownSSEManager,
  streamAIResponse
} from './sse-manager';
