/**
 * Onboarding API Routes
 * Elite marketer onboarding flow for $20k/day ad spenders
 */
import { Router, Request, Response } from 'express';
import { Pool } from 'pg';

export function createOnboardingRouter(db: Pool) {
  const router = Router();

  /**
   * POST /api/onboarding/start
   * Initialize onboarding session for new user
   */
  router.post('/start', async (req: Request, res: Response) => {
    try {
      const { userId, email } = req.body;

      if (!userId) {
        return res.status(400).json({ error: 'userId is required' });
      }

      // Check if onboarding already exists
      const existingResult = await db.query(
        'SELECT * FROM onboarding_progress WHERE user_id = $1',
        [userId]
      );

      if (existingResult.rows.length > 0) {
        return res.json({
          success: true,
          message: 'Onboarding session already exists',
          data: existingResult.rows[0]
        });
      }

      // Create new onboarding record
      const result = await db.query(
        `INSERT INTO onboarding_progress (
          user_id,
          current_step,
          started_at
        ) VALUES ($1, 1, NOW())
        RETURNING *`,
        [userId]
      );

      res.json({
        success: true,
        message: 'Onboarding session initialized',
        data: result.rows[0]
      });
    } catch (error: any) {
      console.error('Error starting onboarding:', error);
      res.status(500).json({
        error: 'Failed to start onboarding',
        details: error.message
      });
    }
  });

  /**
   * GET /api/onboarding/status
   * Get current onboarding progress
   */
  router.get('/status', async (req: Request, res: Response) => {
    try {
      const { userId } = req.query;

      if (!userId) {
        return res.status(400).json({ error: 'userId is required' });
      }

      const result = await db.query(
        'SELECT * FROM onboarding_progress WHERE user_id = $1',
        [userId]
      );

      if (result.rows.length === 0) {
        return res.status(404).json({
          error: 'Onboarding not found',
          message: 'User has not started onboarding'
        });
      }

      const progress = result.rows[0];

      // Calculate completion percentage
      const steps = [
        progress.step_welcome,
        progress.step_connect_meta,
        progress.step_connect_google,
        progress.step_configure,
        progress.step_first_campaign
      ];
      const completedCount = steps.filter(Boolean).length;
      const completionPercentage = Math.round((completedCount / steps.length) * 100);

      res.json({
        success: true,
        data: {
          ...progress,
          completionPercentage,
          completedSteps: completedCount,
          totalSteps: steps.length
        }
      });
    } catch (error: any) {
      console.error('Error getting onboarding status:', error);
      res.status(500).json({
        error: 'Failed to get onboarding status',
        details: error.message
      });
    }
  });

  /**
   * PUT /api/onboarding/step/:step
   * Complete a specific onboarding step
   */
  router.put('/step/:step', async (req: Request, res: Response) => {
    try {
      const { step } = req.params;
      const { userId, data } = req.body;

      if (!userId) {
        return res.status(400).json({ error: 'userId is required' });
      }

      const validSteps = ['welcome', 'connect-meta', 'connect-google', 'configure', 'first-campaign', 'complete'];
      if (!validSteps.includes(step)) {
        return res.status(400).json({ error: 'Invalid step name' });
      }

      // Map URL step names to database column names
      const stepMapping: Record<string, string> = {
        'welcome': 'step_welcome',
        'connect-meta': 'step_connect_meta',
        'connect-google': 'step_connect_google',
        'configure': 'step_configure',
        'first-campaign': 'step_first_campaign',
        'complete': 'step_complete'
      };

      const stepColumn = stepMapping[step];

      // Build dynamic update query based on step
      let updateQuery = `UPDATE onboarding_progress SET ${stepColumn} = true`;
      const queryParams: any[] = [];
      let paramIndex = 1;

      // Handle step-specific data
      if (step === 'connect-meta' && data?.meta_business_id) {
        updateQuery += `, meta_business_id = $${paramIndex}, meta_ad_account_id = $${paramIndex + 1}, meta_connected_at = NOW()`;
        queryParams.push(data.meta_business_id, data.meta_ad_account_id || null);
        paramIndex += 2;
      }

      if (step === 'connect-google' && data?.google_customer_id) {
        updateQuery += `, google_customer_id = $${paramIndex}, google_connected_at = NOW()`;
        queryParams.push(data.google_customer_id);
        paramIndex += 1;
      }

      if (step === 'configure' && data) {
        const updates: string[] = [];
        if (data.default_currency) {
          updates.push(`default_currency = $${paramIndex}`);
          queryParams.push(data.default_currency);
          paramIndex++;
        }
        if (data.default_timezone) {
          updates.push(`default_timezone = $${paramIndex}`);
          queryParams.push(data.default_timezone);
          paramIndex++;
        }
        if (data.daily_budget_limit !== undefined) {
          updates.push(`daily_budget_limit = $${paramIndex}`);
          queryParams.push(data.daily_budget_limit);
          paramIndex++;
        }
        if (data.email_notifications !== undefined) {
          updates.push(`email_notifications = $${paramIndex}`);
          queryParams.push(data.email_notifications);
          paramIndex++;
        }
        if (data.slack_notifications !== undefined) {
          updates.push(`slack_notifications = $${paramIndex}`);
          queryParams.push(data.slack_notifications);
          paramIndex++;
        }
        if (data.push_notifications !== undefined) {
          updates.push(`push_notifications = $${paramIndex}`);
          queryParams.push(data.push_notifications);
          paramIndex++;
        }
        if (updates.length > 0) {
          updateQuery += `, ${updates.join(', ')}`;
        }
      }

      if (step === 'first-campaign' && data?.campaign_id) {
        updateQuery += `, first_campaign_id = $${paramIndex}, first_campaign_created_at = NOW()`;
        queryParams.push(data.campaign_id);
        paramIndex += 1;
      }

      // Update current step number
      const stepNumbers: Record<string, number> = {
        'welcome': 2,
        'connect-meta': 3,
        'connect-google': 4,
        'configure': 5,
        'first-campaign': 6,
        'complete': 6
      };
      updateQuery += `, current_step = $${paramIndex}`;
      queryParams.push(stepNumbers[step]);
      paramIndex++;

      // Add WHERE clause
      updateQuery += ` WHERE user_id = $${paramIndex} RETURNING *`;
      queryParams.push(userId);

      const result = await db.query(updateQuery, queryParams);

      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Onboarding not found' });
      }

      res.json({
        success: true,
        message: `Step '${step}' completed`,
        data: result.rows[0]
      });
    } catch (error: any) {
      console.error(`Error completing step ${req.params.step}:`, error);
      res.status(500).json({
        error: 'Failed to complete step',
        details: error.message
      });
    }
  });

  /**
   * POST /api/onboarding/skip
   * Skip optional onboarding steps
   */
  router.post('/skip', async (req: Request, res: Response) => {
    try {
      const { userId, step, reason } = req.body;

      if (!userId || !step) {
        return res.status(400).json({ error: 'userId and step are required' });
      }

      // Get current skipped steps
      const currentResult = await db.query(
        'SELECT skipped_steps FROM onboarding_progress WHERE user_id = $1',
        [userId]
      );

      if (currentResult.rows.length === 0) {
        return res.status(404).json({ error: 'Onboarding not found' });
      }

      const skippedSteps = currentResult.rows[0].skipped_steps || [];
      skippedSteps.push({
        step,
        reason: reason || 'User skipped',
        skippedAt: new Date().toISOString()
      });

      // Update skipped steps
      const result = await db.query(
        `UPDATE onboarding_progress
         SET skipped_steps = $1
         WHERE user_id = $2
         RETURNING *`,
        [JSON.stringify(skippedSteps), userId]
      );

      res.json({
        success: true,
        message: `Step '${step}' skipped`,
        data: result.rows[0]
      });
    } catch (error: any) {
      console.error('Error skipping step:', error);
      res.status(500).json({
        error: 'Failed to skip step',
        details: error.message
      });
    }
  });

  /**
   * DELETE /api/onboarding/reset
   * Reset onboarding progress (admin only)
   */
  router.delete('/reset', async (req: Request, res: Response) => {
    try {
      const { userId } = req.body;

      if (!userId) {
        return res.status(400).json({ error: 'userId is required' });
      }

      const result = await db.query(
        'DELETE FROM onboarding_progress WHERE user_id = $1 RETURNING *',
        [userId]
      );

      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Onboarding not found' });
      }

      res.json({
        success: true,
        message: 'Onboarding reset successfully',
        data: result.rows[0]
      });
    } catch (error: any) {
      console.error('Error resetting onboarding:', error);
      res.status(500).json({
        error: 'Failed to reset onboarding',
        details: error.message
      });
    }
  });

  return router;
}
