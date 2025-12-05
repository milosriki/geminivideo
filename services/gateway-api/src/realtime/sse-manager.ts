/**
 * Server-Sent Events (SSE) Manager
 * Handles streaming AI responses and real-time updates via SSE
 */

import { Response } from 'express';
import { RealtimeEvent } from './events';

export interface SSEClient {
  id: string;
  response: Response;
  userId?: string;
  connectedAt: Date;
  lastEventTime: Date;
  eventCount: number;
}

export class SSEManager {
  private clients: Map<string, SSEClient> = new Map();
  private keepAliveInterval: NodeJS.Timeout | null = null;
  private readonly KEEP_ALIVE_INTERVAL = 15000; // 15 seconds

  constructor() {
    this.startKeepAlive();
  }

  /**
   * Initialize SSE connection
   */
  initializeConnection(
    res: Response,
    userId?: string,
    metadata?: Record<string, any>
  ): SSEClient {
    // Set SSE headers
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('X-Accel-Buffering', 'no'); // Disable nginx buffering

    // CORS headers for SSE
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    const clientId = `sse_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const client: SSEClient = {
      id: clientId,
      response: res,
      userId,
      connectedAt: new Date(),
      lastEventTime: new Date(),
      eventCount: 0
    };

    this.clients.set(clientId, client);

    // Send initial connection event
    this.sendEvent(client, {
      type: 'connected',
      message: 'SSE connection established',
      clientId,
      timestamp: new Date().toISOString()
    } as any);

    // Handle client disconnect
    res.on('close', () => {
      this.handleDisconnect(clientId);
    });

    console.log(`📡 SSE client connected: ${clientId} (${this.clients.size} total)`);

    return client;
  }

  /**
   * Send event to specific client
   */
  sendEvent(client: SSEClient, event: RealtimeEvent | any, eventType?: string): boolean {
    try {
      const data = JSON.stringify(event);
      let message = '';

      // Add event ID for tracking
      if (event.id) {
        message += `id: ${event.id}\n`;
      }

      // Add event type if specified
      if (eventType) {
        message += `event: ${eventType}\n`;
      }

      // Add data
      message += `data: ${data}\n\n`;

      // Write to response
      client.response.write(message);

      // Update stats
      client.lastEventTime = new Date();
      client.eventCount++;

      return true;
    } catch (error) {
      console.error(`Failed to send SSE event to client ${client.id}:`, error);
      this.handleDisconnect(client.id);
      return false;
    }
  }

  /**
   * Send event to specific client by ID
   */
  sendEventById(clientId: string, event: RealtimeEvent | any, eventType?: string): boolean {
    const client = this.clients.get(clientId);
    if (client) {
      return this.sendEvent(client, event, eventType);
    }
    return false;
  }

  /**
   * Send event to all clients for a specific user
   */
  sendToUser(userId: string, event: RealtimeEvent | any, eventType?: string): number {
    let sent = 0;
    for (const client of this.clients.values()) {
      if (client.userId === userId) {
        if (this.sendEvent(client, event, eventType)) {
          sent++;
        }
      }
    }
    return sent;
  }

  /**
   * Broadcast event to all connected clients
   */
  broadcast(event: RealtimeEvent | any, eventType?: string): number {
    let sent = 0;
    for (const client of this.clients.values()) {
      if (this.sendEvent(client, event, eventType)) {
        sent++;
      }
    }
    return sent;
  }

  /**
   * Send a simple text chunk (for AI streaming)
   */
  sendChunk(client: SSEClient, chunk: string): boolean {
    try {
      client.response.write(`data: ${JSON.stringify({ chunk })}\n\n`);
      client.lastEventTime = new Date();
      client.eventCount++;
      return true;
    } catch (error) {
      console.error(`Failed to send chunk to client ${client.id}:`, error);
      this.handleDisconnect(client.id);
      return false;
    }
  }

  /**
   * Send completion signal
   */
  sendComplete(client: SSEClient, data?: any): void {
    this.sendEvent(client, {
      type: 'complete',
      data,
      timestamp: new Date().toISOString()
    } as any, 'complete');

    // End the connection
    client.response.end();
    this.handleDisconnect(client.id);
  }

  /**
   * Send error to client
   */
  sendError(client: SSEClient, error: string): void {
    this.sendEvent(client, {
      type: 'error',
      error,
      timestamp: new Date().toISOString()
    } as any, 'error');

    // End the connection
    client.response.end();
    this.handleDisconnect(client.id);
  }

  /**
   * Handle client disconnect
   */
  private handleDisconnect(clientId: string): void {
    const client = this.clients.get(clientId);
    if (client) {
      console.log(
        `👋 SSE client disconnected: ${clientId} ` +
        `(sent ${client.eventCount} events, ` +
        `duration: ${Date.now() - client.connectedAt.getTime()}ms)`
      );
      this.clients.delete(clientId);
    }
  }

  /**
   * Start keep-alive mechanism
   */
  private startKeepAlive(): void {
    this.keepAliveInterval = setInterval(() => {
      const comment = `: keep-alive ${new Date().toISOString()}\n\n`;

      for (const client of this.clients.values()) {
        try {
          client.response.write(comment);
        } catch (error) {
          console.error(`Keep-alive failed for client ${client.id}:`, error);
          this.handleDisconnect(client.id);
        }
      }
    }, this.KEEP_ALIVE_INTERVAL);
  }

  /**
   * Get statistics
   */
  getStats() {
    const totalEvents = Array.from(this.clients.values()).reduce(
      (sum, client) => sum + client.eventCount,
      0
    );

    return {
      totalConnections: this.clients.size,
      totalEvents,
      clients: Array.from(this.clients.values()).map(c => ({
        id: c.id,
        userId: c.userId,
        connectedAt: c.connectedAt,
        eventCount: c.eventCount,
        lastEventTime: c.lastEventTime
      }))
    };
  }

  /**
   * Shutdown SSE manager
   */
  shutdown(): void {
    console.log('🛑 Shutting down SSE manager...');

    // Stop keep-alive
    if (this.keepAliveInterval) {
      clearInterval(this.keepAliveInterval);
      this.keepAliveInterval = null;
    }

    // Close all connections
    for (const client of this.clients.values()) {
      try {
        this.sendEvent(client, {
          type: 'server_shutdown',
          message: 'Server is shutting down',
          timestamp: new Date().toISOString()
        } as any);
        client.response.end();
      } catch (error) {
        console.error(`Error closing SSE client ${client.id}:`, error);
      }
    }

    this.clients.clear();

    console.log('✅ SSE manager shutdown complete');
  }
}

// Singleton instance
let sseManager: SSEManager | null = null;

export function getSSEManager(): SSEManager {
  if (!sseManager) {
    sseManager = new SSEManager();
  }
  return sseManager;
}

export function shutdownSSEManager(): void {
  if (sseManager) {
    sseManager.shutdown();
    sseManager = null;
  }
}

/**
 * Helper function to create SSE stream for AI responses
 */
export async function* streamAIResponse(
  model: string,
  prompt: string,
  apiFunction: (prompt: string) => AsyncIterable<string>
): AsyncGenerator<{ model: string; chunk: string; isComplete: boolean }> {
  try {
    for await (const chunk of apiFunction(prompt)) {
      yield {
        model,
        chunk,
        isComplete: false
      };
    }

    yield {
      model,
      chunk: '',
      isComplete: true
    };
  } catch (error) {
    console.error(`AI streaming error for ${model}:`, error);
    throw error;
  }
}
