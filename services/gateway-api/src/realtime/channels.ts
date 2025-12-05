/**
 * Channel Management System
 * Handles pub/sub channel subscriptions for real-time events
 */

import { EventEmitter } from 'events';
import { createClient, RedisClientType } from 'redis';
import { RealtimeEvent, Channel, getChannelName } from './events';

export interface ChannelSubscription {
  channel: Channel;
  callback: (event: RealtimeEvent) => void;
  subscriptionId: string;
}

export class ChannelManager extends EventEmitter {
  private redisClient: RedisClientType | null = null;
  private redisPubClient: RedisClientType | null = null;
  private subscriptions: Map<string, Set<ChannelSubscription>> = new Map();
  private redisSubscriptions: Set<string> = new Set();
  private isConnected = false;

  constructor(private redisUrl?: string) {
    super();
    this.setMaxListeners(100); // Support many subscriptions
  }

  /**
   * Initialize Redis connections for pub/sub
   */
  async initialize(): Promise<void> {
    if (!this.redisUrl) {
      console.warn('⚠️  No Redis URL provided, using in-memory channels only');
      return;
    }

    try {
      // Create subscriber client
      this.redisClient = createClient({ url: this.redisUrl });
      this.redisClient.on('error', (err) => {
        console.error('Redis subscriber error:', err);
        this.emit('error', err);
      });

      // Create publisher client
      this.redisPubClient = createClient({ url: this.redisUrl });
      this.redisPubClient.on('error', (err) => {
        console.error('Redis publisher error:', err);
      });

      await this.redisClient.connect();
      await this.redisPubClient.connect();

      this.isConnected = true;
      console.log('✅ Redis channel manager connected');

      // Handle incoming messages
      this.setupRedisListeners();
    } catch (error) {
      console.error('Failed to connect Redis channel manager:', error);
      this.isConnected = false;
      // Continue without Redis - local only mode
    }
  }

  /**
   * Setup Redis message listeners
   */
  private setupRedisListeners(): void {
    if (!this.redisClient) return;

    // Handle pattern messages
    this.redisClient.on('message', (channel: string, message: string) => {
      try {
        const event = JSON.parse(message) as RealtimeEvent;
        this.emit(`channel:${channel}`, event);
      } catch (error) {
        console.error('Failed to parse Redis message:', error);
      }
    });
  }

  /**
   * Subscribe to a channel
   */
  subscribe(
    channel: Channel,
    callback: (event: RealtimeEvent) => void
  ): ChannelSubscription {
    const channelName = getChannelName(channel);
    const subscriptionId = `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const subscription: ChannelSubscription = {
      channel,
      callback,
      subscriptionId
    };

    // Add to local subscriptions
    if (!this.subscriptions.has(channelName)) {
      this.subscriptions.set(channelName, new Set());
    }
    this.subscriptions.get(channelName)!.add(subscription);

    // Setup local event listener
    this.on(`channel:${channelName}`, callback);

    // Subscribe to Redis channel if not already subscribed
    if (this.isConnected && this.redisClient && !this.redisSubscriptions.has(channelName)) {
      this.redisClient.subscribe(channelName, (err) => {
        if (err) {
          console.error(`Failed to subscribe to Redis channel ${channelName}:`, err);
        } else {
          this.redisSubscriptions.add(channelName);
          console.log(`📡 Subscribed to channel: ${channelName}`);
        }
      });
    }

    return subscription;
  }

  /**
   * Unsubscribe from a channel
   */
  unsubscribe(subscription: ChannelSubscription): void {
    const channelName = getChannelName(subscription.channel);
    const subs = this.subscriptions.get(channelName);

    if (subs) {
      subs.delete(subscription);
      this.off(`channel:${channelName}`, subscription.callback);

      // If no more subscriptions for this channel, unsubscribe from Redis
      if (subs.size === 0) {
        this.subscriptions.delete(channelName);

        if (this.isConnected && this.redisClient && this.redisSubscriptions.has(channelName)) {
          this.redisClient.unsubscribe(channelName);
          this.redisSubscriptions.delete(channelName);
          console.log(`📡 Unsubscribed from channel: ${channelName}`);
        }
      }
    }
  }

  /**
   * Publish an event to a channel
   */
  async publish(channel: Channel, event: RealtimeEvent): Promise<void> {
    const channelName = getChannelName(channel);

    // Always emit locally first for immediate delivery to local subscribers
    this.emit(`channel:${channelName}`, event);

    // Publish to Redis for distributed subscribers
    if (this.isConnected && this.redisPubClient) {
      try {
        await this.redisPubClient.publish(channelName, JSON.stringify(event));
      } catch (error) {
        console.error(`Failed to publish to Redis channel ${channelName}:`, error);
      }
    }
  }

  /**
   * Get all active channel names
   */
  getActiveChannels(): string[] {
    return Array.from(this.subscriptions.keys());
  }

  /**
   * Get subscription count for a channel
   */
  getSubscriptionCount(channel: Channel): number {
    const channelName = getChannelName(channel);
    return this.subscriptions.get(channelName)?.size || 0;
  }

  /**
   * Get total subscription count
   */
  getTotalSubscriptions(): number {
    let total = 0;
    for (const subs of this.subscriptions.values()) {
      total += subs.size;
    }
    return total;
  }

  /**
   * Cleanup all subscriptions and close connections
   */
  async shutdown(): Promise<void> {
    console.log('🛑 Shutting down channel manager...');

    // Clear all local subscriptions
    for (const [channelName, subs] of this.subscriptions.entries()) {
      for (const sub of subs) {
        this.off(`channel:${channelName}`, sub.callback);
      }
    }
    this.subscriptions.clear();
    this.redisSubscriptions.clear();

    // Close Redis connections
    if (this.redisClient) {
      await this.redisClient.quit();
      this.redisClient = null;
    }

    if (this.redisPubClient) {
      await this.redisPubClient.quit();
      this.redisPubClient = null;
    }

    this.isConnected = false;
    this.removeAllListeners();

    console.log('✅ Channel manager shutdown complete');
  }

  /**
   * Get stats
   */
  getStats() {
    return {
      isConnected: this.isConnected,
      activeChannels: this.subscriptions.size,
      totalSubscriptions: this.getTotalSubscriptions(),
      redisSubscriptions: this.redisSubscriptions.size,
      channels: this.getActiveChannels()
    };
  }
}

// Singleton instance
let channelManager: ChannelManager | null = null;

export function getChannelManager(): ChannelManager {
  if (!channelManager) {
    const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
    channelManager = new ChannelManager(redisUrl);
  }
  return channelManager;
}

export async function initializeChannelManager(): Promise<ChannelManager> {
  const manager = getChannelManager();
  await manager.initialize();
  return manager;
}

export async function shutdownChannelManager(): Promise<void> {
  if (channelManager) {
    await channelManager.shutdown();
    channelManager = null;
  }
}
