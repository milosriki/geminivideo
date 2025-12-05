/**
 * WebSocket Manager
 * Handles WebSocket connections and real-time event streaming
 */

import { Server as HTTPServer } from 'http';
import { WebSocketServer, WebSocket } from 'ws';
import { parse as parseUrl } from 'url';
import { parse as parseQuery } from 'querystring';
import { getChannelManager } from './channels';
import {
  RealtimeEvent,
  Channel,
  ConnectionEvent,
  HeartbeatEvent,
  createHeartbeat
} from './events';

export interface WebSocketClient {
  id: string;
  ws: WebSocket;
  userId?: string;
  subscribedChannels: Set<string>;
  connectedAt: Date;
  lastHeartbeat: Date;
  metadata?: Record<string, any>;
}

export class WebSocketManager {
  private wss: WebSocketServer | null = null;
  private clients: Map<string, WebSocketClient> = new Map();
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private cleanupInterval: NodeJS.Timeout | null = null;

  private readonly HEARTBEAT_INTERVAL = 30000; // 30 seconds
  private readonly CLIENT_TIMEOUT = 60000; // 60 seconds
  private readonly CLEANUP_INTERVAL = 120000; // 2 minutes

  constructor(private server: HTTPServer) {}

  /**
   * Initialize WebSocket server
   */
  initialize(): void {
    this.wss = new WebSocketServer({
      server: this.server,
      path: '/ws',
      clientTracking: true
    });

    this.wss.on('connection', (ws: WebSocket, req) => {
      this.handleConnection(ws, req);
    });

    // Start heartbeat
    this.startHeartbeat();

    // Start cleanup of dead connections
    this.startCleanup();

    console.log('✅ WebSocket server initialized on /ws');
  }

  /**
   * Handle new WebSocket connection
   */
  private handleConnection(ws: WebSocket, req: any): void {
    const url = parseUrl(req.url || '', true);
    const query = url.query;

    // Generate client ID
    const clientId = `ws_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const client: WebSocketClient = {
      id: clientId,
      ws,
      userId: query.userId as string,
      subscribedChannels: new Set(),
      connectedAt: new Date(),
      lastHeartbeat: new Date(),
      metadata: {
        userAgent: req.headers['user-agent'],
        ip: req.socket.remoteAddress
      }
    };

    this.clients.set(clientId, client);

    // Send connection confirmation
    this.sendToClient(client, {
      type: 'connected',
      message: 'Connected to real-time service',
      clientId,
      timestamp: new Date().toISOString()
    } as ConnectionEvent);

    console.log(`📱 Client connected: ${clientId} (${this.clients.size} total)`);

    // Handle messages from client
    ws.on('message', (data: Buffer) => {
      this.handleMessage(client, data);
    });

    // Handle client disconnect
    ws.on('close', () => {
      this.handleDisconnect(client);
    });

    // Handle errors
    ws.on('error', (error) => {
      console.error(`WebSocket error for client ${clientId}:`, error);
      this.handleDisconnect(client);
    });

    // Update last heartbeat on pong
    ws.on('pong', () => {
      client.lastHeartbeat = new Date();
    });
  }

  /**
   * Handle incoming message from client
   */
  private handleMessage(client: WebSocketClient, data: Buffer): void {
    try {
      const message = JSON.parse(data.toString());

      switch (message.type) {
        case 'subscribe':
          this.handleSubscribe(client, message.channel);
          break;

        case 'unsubscribe':
          this.handleUnsubscribe(client, message.channel);
          break;

        case 'ping':
          this.sendToClient(client, {
            type: 'pong',
            timestamp: new Date().toISOString()
          } as any);
          break;

        default:
          console.warn(`Unknown message type from client ${client.id}:`, message.type);
      }
    } catch (error) {
      console.error(`Failed to parse message from client ${client.id}:`, error);
    }
  }

  /**
   * Handle channel subscription
   */
  private handleSubscribe(client: WebSocketClient, channelData: Channel): void {
    const channelManager = getChannelManager();

    // Subscribe to channel
    const subscription = channelManager.subscribe(channelData, (event: RealtimeEvent) => {
      this.sendToClient(client, event);
    });

    client.subscribedChannels.add(subscription.subscriptionId);

    // Send confirmation
    this.sendToClient(client, {
      type: 'subscribed',
      channel: channelData.type,
      success: true,
      timestamp: new Date().toISOString()
    } as any);

    console.log(`📡 Client ${client.id} subscribed to ${channelData.type}`);
  }

  /**
   * Handle channel unsubscription
   */
  private handleUnsubscribe(client: WebSocketClient, channelData: Channel): void {
    // Implementation would need to track subscriptions to properly unsubscribe
    // For now, just remove from client's tracked channels
    client.subscribedChannels.clear();

    this.sendToClient(client, {
      type: 'unsubscribed',
      channel: channelData.type,
      success: true,
      timestamp: new Date().toISOString()
    } as any);
  }

  /**
   * Handle client disconnect
   */
  private handleDisconnect(client: WebSocketClient): void {
    console.log(`👋 Client disconnected: ${client.id}`);

    // Clean up subscriptions
    client.subscribedChannels.clear();

    // Remove from clients map
    this.clients.delete(client.id);
  }

  /**
   * Send event to specific client
   */
  private sendToClient(client: WebSocketClient, event: RealtimeEvent | any): void {
    if (client.ws.readyState === WebSocket.OPEN) {
      try {
        client.ws.send(JSON.stringify(event));
      } catch (error) {
        console.error(`Failed to send to client ${client.id}:`, error);
      }
    }
  }

  /**
   * Broadcast event to all clients subscribed to a channel
   */
  broadcast(channel: Channel, event: RealtimeEvent): void {
    const channelManager = getChannelManager();
    channelManager.publish(channel, event);
  }

  /**
   * Send event to specific user
   */
  sendToUser(userId: string, event: RealtimeEvent): void {
    for (const client of this.clients.values()) {
      if (client.userId === userId) {
        this.sendToClient(client, event);
      }
    }
  }

  /**
   * Start heartbeat to keep connections alive
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      const heartbeat = createHeartbeat();

      for (const client of this.clients.values()) {
        if (client.ws.readyState === WebSocket.OPEN) {
          try {
            client.ws.ping();
            // Also send heartbeat event
            this.sendToClient(client, heartbeat);
          } catch (error) {
            console.error(`Failed to ping client ${client.id}:`, error);
          }
        }
      }
    }, this.HEARTBEAT_INTERVAL);
  }

  /**
   * Start cleanup of dead connections
   */
  private startCleanup(): void {
    this.cleanupInterval = setInterval(() => {
      const now = Date.now();
      const deadClients: string[] = [];

      for (const [clientId, client] of this.clients.entries()) {
        const timeSinceHeartbeat = now - client.lastHeartbeat.getTime();

        if (timeSinceHeartbeat > this.CLIENT_TIMEOUT) {
          deadClients.push(clientId);
        }
      }

      // Remove dead clients
      for (const clientId of deadClients) {
        const client = this.clients.get(clientId);
        if (client) {
          console.log(`🧹 Cleaning up dead client: ${clientId}`);
          client.ws.terminate();
          this.handleDisconnect(client);
        }
      }
    }, this.CLEANUP_INTERVAL);
  }

  /**
   * Get connection statistics
   */
  getStats() {
    const channelManager = getChannelManager();

    return {
      totalConnections: this.clients.size,
      channels: channelManager.getStats(),
      clients: Array.from(this.clients.values()).map(c => ({
        id: c.id,
        userId: c.userId,
        connectedAt: c.connectedAt,
        subscribedChannels: c.subscribedChannels.size,
        isAlive: c.ws.readyState === WebSocket.OPEN
      }))
    };
  }

  /**
   * Shutdown WebSocket server
   */
  async shutdown(): Promise<void> {
    console.log('🛑 Shutting down WebSocket manager...');

    // Clear intervals
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }

    // Close all client connections
    for (const client of this.clients.values()) {
      try {
        this.sendToClient(client, {
          type: 'disconnected',
          message: 'Server shutting down',
          timestamp: new Date().toISOString()
        } as ConnectionEvent);

        client.ws.close();
      } catch (error) {
        console.error(`Error closing client ${client.id}:`, error);
      }
    }

    this.clients.clear();

    // Close WebSocket server
    if (this.wss) {
      await new Promise<void>((resolve) => {
        this.wss!.close(() => {
          console.log('✅ WebSocket server closed');
          resolve();
        });
      });
    }

    console.log('✅ WebSocket manager shutdown complete');
  }
}

// Singleton instance
let wsManager: WebSocketManager | null = null;

export function initializeWebSocketManager(server: HTTPServer): WebSocketManager {
  if (!wsManager) {
    wsManager = new WebSocketManager(server);
    wsManager.initialize();
  }
  return wsManager;
}

export function getWebSocketManager(): WebSocketManager | null {
  return wsManager;
}

export async function shutdownWebSocketManager(): Promise<void> {
  if (wsManager) {
    await wsManager.shutdown();
    wsManager = null;
  }
}
