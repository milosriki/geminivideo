/**
 * Cost Tracker Service
 *
 * Tracks and reports API costs for AI model usage.
 * Records all API calls to the database and provides cost analysis/projection.
 */

import { Pool } from 'pg';

interface CostRecord {
  model_name: string;
  operation_type: string;
  input_tokens?: number;
  output_tokens?: number;
  total_tokens: number;
  cost_usd: number;
  latency_ms: number;
  cache_hit?: boolean;
  early_exit?: boolean;
}

interface DailyCost {
  date: string;
  model_name: string;
  calls: number;
  total_cost: number;
  avg_latency: number;
  cache_hit_rate: number;
}

interface ModelCost {
  model_name: string;
  calls: number;
  total_cost: number;
  avg_cost_per_call: number;
  total_tokens: number;
  avg_latency: number;
}

interface CostProjection {
  current_daily_average: number;
  projected_weekly: number;
  projected_monthly: number;
  projected_annual: number;
  trend: 'increasing' | 'decreasing' | 'stable';
  trend_percentage: number;
}

// Model pricing per 1K tokens (input/output blended for simplicity)
const MODEL_PRICING: Record<string, number> = {
  'gemini-2.0-flash': 0.00075,
  'gemini-2.0-flash-exp': 0.00075, // Same as flash
  'gemini-3-pro': 0.00125,
  'gpt-4o-mini': 0.00015,
  'claude-3.5-sonnet': 0.003,
  'claude-3-5-sonnet-20241022': 0.003, // Same pricing
  'gpt-4o': 0.005,
};

export class CostTracker {
  private pgPool: Pool;

  constructor(pgPool: Pool) {
    this.pgPool = pgPool;
  }

  /**
   * Record a cost entry to the database
   */
  async recordCost(
    model: string,
    tokens: number,
    latency: number,
    operationType: string = 'generation',
    options?: {
      inputTokens?: number;
      outputTokens?: number;
      cacheHit?: boolean;
      earlyExit?: boolean;
    }
  ): Promise<void> {
    try {
      // Calculate cost based on model pricing
      const costPer1k = MODEL_PRICING[model] || 0.001; // Default fallback
      const costUsd = (tokens / 1000) * costPer1k;

      const query = `
        INSERT INTO api_costs (
          model_name,
          operation_type,
          input_tokens,
          output_tokens,
          total_tokens,
          cost_usd,
          latency_ms,
          cache_hit,
          early_exit
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
      `;

      await this.pgPool.query(query, [
        model,
        operationType,
        options?.inputTokens || null,
        options?.outputTokens || null,
        tokens,
        costUsd,
        latency,
        options?.cacheHit || false,
        options?.earlyExit || false,
      ]);

      console.log(`📊 Cost recorded: ${model} - ${tokens} tokens - $${costUsd.toFixed(6)} - ${latency}ms`);
    } catch (error) {
      console.error('Failed to record cost:', error);
      // Don't throw - cost tracking should not break the main flow
    }
  }

  /**
   * Get daily costs for the last N days
   */
  async getDailyCosts(days: number = 30): Promise<DailyCost[]> {
    const query = `
      SELECT
        date,
        model_name,
        calls,
        total_cost,
        avg_latency,
        cache_hit_rate
      FROM daily_costs
      WHERE date >= CURRENT_DATE - INTERVAL '1 day' * $1
      ORDER BY date DESC, total_cost DESC
    `;

    const result = await this.pgPool.query(query, [days]);
    return result.rows;
  }

  /**
   * Get cost breakdown by model for the last N days
   */
  async getModelCosts(model?: string, days: number = 30): Promise<ModelCost[]> {
    const conditions = [`created_at >= NOW() - INTERVAL '1 day' * $1`];
    const params: any[] = [days];

    if (model) {
      conditions.push('model_name = $2');
      params.push(model);
    }

    const query = `
      SELECT
        model_name,
        COUNT(*) as calls,
        SUM(cost_usd) as total_cost,
        AVG(cost_usd) as avg_cost_per_call,
        SUM(total_tokens) as total_tokens,
        AVG(latency_ms) as avg_latency
      FROM api_costs
      WHERE ${conditions.join(' AND ')}
      GROUP BY model_name
      ORDER BY total_cost DESC
    `;

    const result = await this.pgPool.query(query, params);
    return result.rows.map((row) => ({
      model_name: row.model_name,
      calls: parseInt(row.calls),
      total_cost: parseFloat(row.total_cost),
      avg_cost_per_call: parseFloat(row.avg_cost_per_call),
      total_tokens: parseInt(row.total_tokens),
      avg_latency: parseFloat(row.avg_latency),
    }));
  }

  /**
   * Get total spend for the last N days
   */
  async getTotalSpend(days: number = 30): Promise<{
    total_cost: number;
    total_calls: number;
    total_tokens: number;
    avg_cost_per_call: number;
    models_used: number;
    date_range: { start: string; end: string };
  }> {
    const query = `
      SELECT
        SUM(cost_usd) as total_cost,
        COUNT(*) as total_calls,
        SUM(total_tokens) as total_tokens,
        AVG(cost_usd) as avg_cost_per_call,
        COUNT(DISTINCT model_name) as models_used,
        MIN(created_at) as earliest,
        MAX(created_at) as latest
      FROM api_costs
      WHERE created_at >= NOW() - INTERVAL '1 day' * $1
    `;

    const result = await this.pgPool.query(query, [days]);
    const row = result.rows[0];

    return {
      total_cost: parseFloat(row.total_cost) || 0,
      total_calls: parseInt(row.total_calls) || 0,
      total_tokens: parseInt(row.total_tokens) || 0,
      avg_cost_per_call: parseFloat(row.avg_cost_per_call) || 0,
      models_used: parseInt(row.models_used) || 0,
      date_range: {
        start: row.earliest || new Date().toISOString(),
        end: row.latest || new Date().toISOString(),
      },
    };
  }

  /**
   * Project future costs based on historical data
   */
  async getCostProjection(days: number = 30): Promise<CostProjection> {
    // Get daily averages for trend analysis
    const query = `
      SELECT
        DATE(created_at) as date,
        SUM(cost_usd) as daily_cost
      FROM api_costs
      WHERE created_at >= NOW() - INTERVAL '1 day' * $1
      GROUP BY DATE(created_at)
      ORDER BY date DESC
    `;

    const result = await this.pgPool.query(query, [days]);
    const dailyCosts = result.rows.map((row) => parseFloat(row.daily_cost));

    if (dailyCosts.length === 0) {
      return {
        current_daily_average: 0,
        projected_weekly: 0,
        projected_monthly: 0,
        projected_annual: 0,
        trend: 'stable',
        trend_percentage: 0,
      };
    }

    // Calculate daily average
    const avgDailyCost = dailyCosts.reduce((a, b) => a + b, 0) / dailyCosts.length;

    // Calculate trend (compare first half vs second half)
    const midpoint = Math.floor(dailyCosts.length / 2);
    const recentAvg = dailyCosts.slice(0, midpoint).reduce((a, b) => a + b, 0) / midpoint;
    const olderAvg = dailyCosts.slice(midpoint).reduce((a, b) => a + b, 0) / (dailyCosts.length - midpoint);

    let trend: 'increasing' | 'decreasing' | 'stable' = 'stable';
    let trendPercentage = 0;

    if (olderAvg > 0) {
      trendPercentage = ((recentAvg - olderAvg) / olderAvg) * 100;
      if (Math.abs(trendPercentage) > 10) {
        trend = trendPercentage > 0 ? 'increasing' : 'decreasing';
      }
    }

    // Project using recent average for more accurate near-term predictions
    const projectionBase = recentAvg > 0 ? recentAvg : avgDailyCost;

    return {
      current_daily_average: avgDailyCost,
      projected_weekly: projectionBase * 7,
      projected_monthly: projectionBase * 30,
      projected_annual: projectionBase * 365,
      trend,
      trend_percentage: Math.round(trendPercentage * 10) / 10,
    };
  }

  /**
   * Get available model pricing information
   */
  getModelPricing(): Record<string, number> {
    return { ...MODEL_PRICING };
  }

  /**
   * Estimate cost for a given model and token count
   */
  estimateCost(model: string, tokens: number): number {
    const costPer1k = MODEL_PRICING[model] || 0.001;
    return (tokens / 1000) * costPer1k;
  }
}
