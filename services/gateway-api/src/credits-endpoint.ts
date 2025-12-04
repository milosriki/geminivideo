/**
 * AI Credits Endpoint Code
 *
 * ADD THIS TO index.ts after the job endpoints (around line 962)
 * AND add the table initialization code to the pgPool.query().then() block
 */

import { Request, Response } from 'express';
import { Pool } from 'pg';

// ============================================================================
// TABLE INITIALIZATION CODE - Add this inside pgPool.query().then() block
// ============================================================================
/*

// Create AI credits tables if they don't exist
const createCreditsTablesQuery = `
  CREATE TABLE IF NOT EXISTS ai_credits (
    user_id VARCHAR(255) PRIMARY KEY,
    total_credits INTEGER NOT NULL DEFAULT 10000,
    used_credits INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
  );

  CREATE TABLE IF NOT EXISTS ai_credit_usage (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    credits_used INTEGER NOT NULL,
    operation VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
  );

  CREATE INDEX IF NOT EXISTS idx_credit_usage_user ON ai_credit_usage(user_id);
  CREATE INDEX IF NOT EXISTS idx_credit_usage_created ON ai_credit_usage(created_at DESC);
`;

await pgPool.query(createCreditsTablesQuery);
console.log('✅ AI credits tables initialized');

// Initialize default user with credits if not exists
const initDefaultUserQuery = `
  INSERT INTO ai_credits (user_id, total_credits, used_credits)
  VALUES ('default_user', 10000, 1500)
  ON CONFLICT (user_id) DO NOTHING;
`;

await pgPool.query(initDefaultUserQuery);

// Seed some sample usage history for the default user (only if no records exist)
const checkUsageQuery = 'SELECT COUNT(*) as count FROM ai_credit_usage WHERE user_id = $1';
const usageCount = await pgPool.query(checkUsageQuery, ['default_user']);

if (parseInt(usageCount.rows[0].count) === 0) {
  const seedUsageQuery = `
    INSERT INTO ai_credit_usage (user_id, credits_used, operation, metadata, created_at)
    VALUES
      ('default_user', 500, 'video_generation', '{"duration": 30, "quality": "hd"}', NOW() - INTERVAL '2 days'),
      ('default_user', 300, 'video_analysis', '{"clips_analyzed": 5}', NOW() - INTERVAL '1 day'),
      ('default_user', 200, 'script_generation', '{"variants": 3}', NOW() - INTERVAL '1 day'),
      ('default_user', 400, 'video_generation', '{"duration": 60, "quality": "4k"}', NOW() - INTERVAL '12 hours'),
      ('default_user', 100, 'text_analysis', '{"words": 500}', NOW() - INTERVAL '6 hours');
  `;

  await pgPool.query(seedUsageQuery);
  console.log('✅ AI credits initialized with sample data');
} else {
  console.log('✅ AI credits tables ready (existing data found)');
}

*/

// ============================================================================
// ENDPOINT CODE - Add this after the job endpoints section
// ============================================================================

export function registerCreditsEndpoints(app: any, pgPool: Pool) {
  // GET /api/credits - Get user's AI credit balance and usage history
  app.get('/api/credits', async (req: Request, res: Response) => {
    try {
      // Use default user since auth isn't implemented
      const userId = req.query.user_id as string || 'default_user';

      console.log(`Fetching AI credits for user: ${userId}`);

      // Get user's credit balance
      const creditsQuery = `
        SELECT
          user_id,
          total_credits,
          used_credits,
          (total_credits - used_credits) as available_credits,
          created_at,
          updated_at
        FROM ai_credits
        WHERE user_id = $1
      `;

      const creditsResult = await pgPool.query(creditsQuery, [userId]);

      if (creditsResult.rows.length === 0) {
        // Initialize new user with default credits
        const initQuery = `
          INSERT INTO ai_credits (user_id, total_credits, used_credits)
          VALUES ($1, 10000, 0)
          RETURNING user_id, total_credits, used_credits, (total_credits - used_credits) as available_credits, created_at, updated_at
        `;

        const initResult = await pgPool.query(initQuery, [userId]);
        const newUser = initResult.rows[0];

        return res.json({
          credits: {
            available: newUser.available_credits,
            total: newUser.total_credits,
            used: newUser.used_credits,
            usage_history: []
          }
        });
      }

      const credits = creditsResult.rows[0];

      // Get usage history (last 30 days)
      const usageQuery = `
        SELECT
          DATE(created_at) as date,
          SUM(credits_used) as used,
          operation,
          metadata
        FROM ai_credit_usage
        WHERE user_id = $1
          AND created_at >= NOW() - INTERVAL '30 days'
        GROUP BY DATE(created_at), operation, metadata, created_at
        ORDER BY created_at DESC
        LIMIT 50
      `;

      const usageResult = await pgPool.query(usageQuery, [userId]);

      // Format usage history
      const usageHistory = usageResult.rows.map(row => ({
        date: row.date.toISOString().split('T')[0],
        used: parseInt(row.used),
        operation: row.operation,
        ...(row.metadata && Object.keys(row.metadata).length > 0 ? row.metadata : {})
      }));

      res.json({
        credits: {
          available: parseInt(credits.available_credits),
          total: parseInt(credits.total_credits),
          used: parseInt(credits.used_credits),
          usage_history: usageHistory
        }
      });

      console.log(`Credits fetched successfully for user: ${userId}`);

    } catch (error: any) {
      console.error('Error fetching AI credits:', error.message);
      res.status(500).json({
        error: 'Failed to fetch AI credits',
        details: error.message
      });
    }
  });

  // POST /api/credits/deduct - Deduct credits for an operation (internal use)
  app.post('/api/credits/deduct', async (req: Request, res: Response) => {
    try {
      const { user_id, credits, operation, metadata } = req.body;

      // Validate required fields
      if (!user_id || !credits || !operation) {
        return res.status(400).json({
          error: 'Missing required fields',
          required: ['user_id', 'credits', 'operation']
        });
      }

      console.log(`Deducting ${credits} credits for user ${user_id} (${operation})`);

      // Check if user has enough credits
      const checkQuery = `
        SELECT total_credits, used_credits
        FROM ai_credits
        WHERE user_id = $1
      `;

      const checkResult = await pgPool.query(checkQuery, [user_id]);

      if (checkResult.rows.length === 0) {
        return res.status(404).json({
          error: 'User not found',
          user_id
        });
      }

      const currentCredits = checkResult.rows[0];
      const available = currentCredits.total_credits - currentCredits.used_credits;

      if (available < credits) {
        return res.status(402).json({
          error: 'Insufficient credits',
          available,
          requested: credits
        });
      }

      // Deduct credits
      const deductQuery = `
        UPDATE ai_credits
        SET used_credits = used_credits + $1,
            updated_at = NOW()
        WHERE user_id = $2
        RETURNING total_credits, used_credits, (total_credits - used_credits) as available_credits
      `;

      const deductResult = await pgPool.query(deductQuery, [credits, user_id]);

      // Log usage
      const logQuery = `
        INSERT INTO ai_credit_usage (user_id, credits_used, operation, metadata, created_at)
        VALUES ($1, $2, $3, $4, NOW())
        RETURNING id, created_at
      `;

      await pgPool.query(logQuery, [
        user_id,
        credits,
        operation,
        metadata ? JSON.stringify(metadata) : '{}'
      ]);

      const updatedCredits = deductResult.rows[0];

      res.json({
        message: 'Credits deducted successfully',
        credits: {
          available: parseInt(updatedCredits.available_credits),
          total: parseInt(updatedCredits.total_credits),
          used: parseInt(updatedCredits.used_credits)
        }
      });

      console.log(`Credits deducted: ${credits} from user ${user_id}. New balance: ${updatedCredits.available_credits}`);

    } catch (error: any) {
      console.error('Error deducting credits:', error.message);
      res.status(500).json({
        error: 'Failed to deduct credits',
        details: error.message
      });
    }
  });
}

// ============================================================================
// INLINE VERSION - Copy this directly into index.ts after job endpoints
// ============================================================================

/*

// ============================================================================
// AI CREDITS ENDPOINTS - Track and manage AI credit usage
// ============================================================================

// GET /api/credits - Get user's AI credit balance and usage history
app.get('/api/credits', async (req: Request, res: Response) => {
  try {
    // Use default user since auth isn't implemented
    const userId = req.query.user_id as string || 'default_user';

    console.log(`Fetching AI credits for user: ${userId}`);

    // Get user's credit balance
    const creditsQuery = `
      SELECT
        user_id,
        total_credits,
        used_credits,
        (total_credits - used_credits) as available_credits,
        created_at,
        updated_at
      FROM ai_credits
      WHERE user_id = $1
    `;

    const creditsResult = await pgPool.query(creditsQuery, [userId]);

    if (creditsResult.rows.length === 0) {
      // Initialize new user with default credits
      const initQuery = `
        INSERT INTO ai_credits (user_id, total_credits, used_credits)
        VALUES ($1, 10000, 0)
        RETURNING user_id, total_credits, used_credits, (total_credits - used_credits) as available_credits, created_at, updated_at
      `;

      const initResult = await pgPool.query(initQuery, [userId]);
      const newUser = initResult.rows[0];

      return res.json({
        credits: {
          available: newUser.available_credits,
          total: newUser.total_credits,
          used: newUser.used_credits,
          usage_history: []
        }
      });
    }

    const credits = creditsResult.rows[0];

    // Get usage history (last 30 days)
    const usageQuery = `
      SELECT
        DATE(created_at) as date,
        SUM(credits_used) as used,
        operation,
        metadata
      FROM ai_credit_usage
      WHERE user_id = $1
        AND created_at >= NOW() - INTERVAL '30 days'
      GROUP BY DATE(created_at), operation, metadata, created_at
      ORDER BY created_at DESC
      LIMIT 50
    `;

    const usageResult = await pgPool.query(usageQuery, [userId]);

    // Format usage history
    const usageHistory = usageResult.rows.map(row => ({
      date: row.date.toISOString().split('T')[0],
      used: parseInt(row.used),
      operation: row.operation,
      ...(row.metadata && Object.keys(row.metadata).length > 0 ? row.metadata : {})
    }));

    res.json({
      credits: {
        available: parseInt(credits.available_credits),
        total: parseInt(credits.total_credits),
        used: parseInt(credits.used_credits),
        usage_history: usageHistory
      }
    });

    console.log(`Credits fetched successfully for user: ${userId}`);

  } catch (error: any) {
    console.error('Error fetching AI credits:', error.message);
    res.status(500).json({
      error: 'Failed to fetch AI credits',
      details: error.message
    });
  }
});

// POST /api/credits/deduct - Deduct credits for an operation (internal use)
app.post('/api/credits/deduct', async (req: Request, res: Response) => {
  try {
    const { user_id, credits, operation, metadata } = req.body;

    // Validate required fields
    if (!user_id || !credits || !operation) {
      return res.status(400).json({
        error: 'Missing required fields',
        required: ['user_id', 'credits', 'operation']
      });
    }

    console.log(`Deducting ${credits} credits for user ${user_id} (${operation})`);

    // Check if user has enough credits
    const checkQuery = `
      SELECT total_credits, used_credits
      FROM ai_credits
      WHERE user_id = $1
    `;

    const checkResult = await pgPool.query(checkQuery, [user_id]);

    if (checkResult.rows.length === 0) {
      return res.status(404).json({
        error: 'User not found',
        user_id
      });
    }

    const currentCredits = checkResult.rows[0];
    const available = currentCredits.total_credits - currentCredits.used_credits;

    if (available < credits) {
      return res.status(402).json({
        error: 'Insufficient credits',
        available,
        requested: credits
      });
    }

    // Deduct credits
    const deductQuery = `
      UPDATE ai_credits
      SET used_credits = used_credits + $1,
          updated_at = NOW()
      WHERE user_id = $2
      RETURNING total_credits, used_credits, (total_credits - used_credits) as available_credits
    `;

    const deductResult = await pgPool.query(deductQuery, [credits, user_id]);

    // Log usage
    const logQuery = `
      INSERT INTO ai_credit_usage (user_id, credits_used, operation, metadata, created_at)
      VALUES ($1, $2, $3, $4, NOW())
      RETURNING id, created_at
    `;

    await pgPool.query(logQuery, [
      user_id,
      credits,
      operation,
      metadata ? JSON.stringify(metadata) : '{}'
    ]);

    const updatedCredits = deductResult.rows[0];

    res.json({
      message: 'Credits deducted successfully',
      credits: {
        available: parseInt(updatedCredits.available_credits),
        total: parseInt(updatedCredits.total_credits),
        used: parseInt(updatedCredits.used_credits)
      }
    });

    console.log(`Credits deducted: ${credits} from user ${user_id}. New balance: ${updatedCredits.available_credits}`);

  } catch (error: any) {
    console.error('Error deducting credits:', error.message);
    res.status(500).json({
      error: 'Failed to deduct credits',
      details: error.message
    });
  }
});

*/
