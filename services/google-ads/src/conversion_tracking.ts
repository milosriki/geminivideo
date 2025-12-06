/**
 * Google Conversion Tracking
 *
 * Wire real Google conversion data for accurate ROAS measurement.
 * This is critical - without accurate tracking, optimization is blind.
 */

import { GoogleAdsApi } from 'google-ads-api';

export interface ConversionEvent {
  conversionId: string;
  conversionName: string;
  conversionTime: Date;
  conversionValue: number;
  currencyCode: string;
  gclid: string;  // Google Click ID
  orderId?: string;
  customerId: string;
}

export interface ConversionAction {
  id: string;
  name: string;
  category: 'PURCHASE' | 'LEAD' | 'SIGNUP' | 'PAGE_VIEW' | 'OTHER';
  countingType: 'ONE_PER_CLICK' | 'MANY_PER_CLICK';
  valueSettings: {
    defaultValue: number;
    alwaysUseDefaultValue: boolean;
  };
}

export interface ConversionStats {
  totalConversions: number;
  totalValue: number;
  averageValue: number;
  conversionRate: number;
  costPerConversion: number;
  roas: number;
}

export class GoogleConversionTracker {
  private client: GoogleAdsApi;
  private customerId: string;

  constructor(customerId: string) {
    this.customerId = customerId;

    // Initialize Google Ads API client
    this.client = new GoogleAdsApi({
      client_id: process.env.GOOGLE_CLIENT_ID || '',
      client_secret: process.env.GOOGLE_CLIENT_SECRET || '',
      developer_token: process.env.GOOGLE_DEVELOPER_TOKEN || '',
    });
  }

  /**
   * Upload offline conversion for a click
   */
  async uploadConversion(event: ConversionEvent): Promise<{ success: boolean; error?: string }> {
    try {
      const customer = this.client.Customer({
        customer_id: this.customerId,
        refresh_token: process.env.GOOGLE_REFRESH_TOKEN || '',
      });

      // Build conversion adjustment
      const conversionAdjustment = {
        conversion_action: `customers/${this.customerId}/conversionActions/${event.conversionId}`,
        gclid_date_time_pair: {
          gclid: event.gclid,
          conversion_date_time: event.conversionTime.toISOString().replace('T', ' ').split('.')[0] + '+00:00',
        },
        conversion_value: event.conversionValue,
        currency_code: event.currencyCode,
        order_id: event.orderId,
      };

      // Upload the conversion
      await customer.conversionAdjustmentUploads.uploadConversionAdjustments({
        customer_id: this.customerId,
        conversion_adjustments: [conversionAdjustment],
        partial_failure: true,
      });

      console.log(`Conversion uploaded: ${event.conversionId} - $${event.conversionValue}`);
      return { success: true };
    } catch (error: any) {
      console.error('Failed to upload conversion:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Get all conversion actions for the account
   */
  async getConversionActions(): Promise<ConversionAction[]> {
    try {
      const customer = this.client.Customer({
        customer_id: this.customerId,
        refresh_token: process.env.GOOGLE_REFRESH_TOKEN || '',
      });

      const response = await customer.query(`
        SELECT
          conversion_action.id,
          conversion_action.name,
          conversion_action.category,
          conversion_action.counting_type,
          conversion_action.value_settings.default_value,
          conversion_action.value_settings.always_use_default_value
        FROM conversion_action
        WHERE conversion_action.status = 'ENABLED'
      `);

      return response.map((row: any) => ({
        id: row.conversion_action.id,
        name: row.conversion_action.name,
        category: row.conversion_action.category,
        countingType: row.conversion_action.counting_type,
        valueSettings: {
          defaultValue: row.conversion_action.value_settings.default_value,
          alwaysUseDefaultValue: row.conversion_action.value_settings.always_use_default_value,
        },
      }));
    } catch (error) {
      console.error('Failed to get conversion actions:', error);
      return [];
    }
  }

  /**
   * Get conversion stats for a campaign
   */
  async getCampaignConversionStats(
    campaignId: string,
    startDate: Date,
    endDate: Date
  ): Promise<ConversionStats> {
    try {
      const customer = this.client.Customer({
        customer_id: this.customerId,
        refresh_token: process.env.GOOGLE_REFRESH_TOKEN || '',
      });

      const dateRange = `segments.date BETWEEN '${this.formatDate(startDate)}' AND '${this.formatDate(endDate)}'`;

      const response = await customer.query(`
        SELECT
          campaign.id,
          campaign.name,
          metrics.conversions,
          metrics.conversions_value,
          metrics.cost_micros,
          metrics.clicks,
          metrics.impressions
        FROM campaign
        WHERE campaign.id = ${campaignId}
        AND ${dateRange}
      `);

      if (response.length === 0) {
        return {
          totalConversions: 0,
          totalValue: 0,
          averageValue: 0,
          conversionRate: 0,
          costPerConversion: 0,
          roas: 0,
        };
      }

      const data = response[0];
      const conversions = data.metrics.conversions || 0;
      const value = data.metrics.conversions_value || 0;
      const cost = (data.metrics.cost_micros || 0) / 1000000;
      const clicks = data.metrics.clicks || 0;

      return {
        totalConversions: conversions,
        totalValue: value,
        averageValue: conversions > 0 ? value / conversions : 0,
        conversionRate: clicks > 0 ? (conversions / clicks) * 100 : 0,
        costPerConversion: conversions > 0 ? cost / conversions : 0,
        roas: cost > 0 ? value / cost : 0,
      };
    } catch (error) {
      console.error('Failed to get conversion stats:', error);
      return {
        totalConversions: 0,
        totalValue: 0,
        averageValue: 0,
        conversionRate: 0,
        costPerConversion: 0,
        roas: 0,
      };
    }
  }

  /**
   * Get all conversions in a date range
   */
  async getConversions(startDate: Date, endDate: Date): Promise<any[]> {
    try {
      const customer = this.client.Customer({
        customer_id: this.customerId,
        refresh_token: process.env.GOOGLE_REFRESH_TOKEN || '',
      });

      const dateRange = `segments.date BETWEEN '${this.formatDate(startDate)}' AND '${this.formatDate(endDate)}'`;

      const response = await customer.query(`
        SELECT
          segments.date,
          segments.conversion_action,
          segments.conversion_action_name,
          metrics.conversions,
          metrics.conversions_value,
          campaign.id,
          campaign.name,
          ad_group.id,
          ad_group.name
        FROM campaign
        WHERE ${dateRange}
        AND metrics.conversions > 0
        ORDER BY segments.date DESC
      `);

      return response.map((row: any) => ({
        date: row.segments.date,
        conversionAction: row.segments.conversion_action,
        conversionActionName: row.segments.conversion_action_name,
        conversions: row.metrics.conversions,
        value: row.metrics.conversions_value,
        campaignId: row.campaign.id,
        campaignName: row.campaign.name,
        adGroupId: row.ad_group.id,
        adGroupName: row.ad_group.name,
      }));
    } catch (error) {
      console.error('Failed to get conversions:', error);
      return [];
    }
  }

  /**
   * Create a new conversion action
   */
  async createConversionAction(
    name: string,
    category: 'PURCHASE' | 'LEAD' | 'SIGNUP',
    defaultValue: number
  ): Promise<string | null> {
    try {
      const customer = this.client.Customer({
        customer_id: this.customerId,
        refresh_token: process.env.GOOGLE_REFRESH_TOKEN || '',
      });

      const operation = {
        create: {
          name,
          category,
          counting_type: 'MANY_PER_CLICK',
          type: 'UPLOAD',
          value_settings: {
            default_value: defaultValue,
            always_use_default_value: false,
          },
          attribution_model_settings: {
            attribution_model: 'GOOGLE_ADS_LAST_CLICK',
          },
        },
      };

      const response = await customer.conversionActions.create([operation]);

      console.log(`Created conversion action: ${name}`);
      return response.results[0].resource_name;
    } catch (error) {
      console.error('Failed to create conversion action:', error);
      return null;
    }
  }

  /**
   * Sync conversions from external source (e.g., your database)
   */
  async syncConversionsFromDatabase(
    conversions: Array<{
      gclid: string;
      conversionTime: Date;
      value: number;
      orderId?: string;
    }>,
    conversionActionId: string
  ): Promise<{ successful: number; failed: number }> {
    let successful = 0;
    let failed = 0;

    for (const conv of conversions) {
      const result = await this.uploadConversion({
        conversionId: conversionActionId,
        conversionName: 'synced_conversion',
        conversionTime: conv.conversionTime,
        conversionValue: conv.value,
        currencyCode: 'USD',
        gclid: conv.gclid,
        orderId: conv.orderId,
        customerId: this.customerId,
      });

      if (result.success) {
        successful++;
      } else {
        failed++;
      }
    }

    console.log(`Sync complete: ${successful} successful, ${failed} failed`);
    return { successful, failed };
  }

  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }
}

/**
 * Express routes for conversion tracking
 */
import { Router, Request, Response } from 'express';

export function createConversionRouter(): Router {
  const router = Router();

  // Upload a single conversion
  router.post('/conversions/upload', async (req: Request, res: Response) => {
    try {
      const { customerId, conversion } = req.body;

      if (!customerId || !conversion) {
        return res.status(400).json({ error: 'Missing customerId or conversion data' });
      }

      const tracker = new GoogleConversionTracker(customerId);
      const result = await tracker.uploadConversion(conversion);

      return res.json(result);
    } catch (error: any) {
      return res.status(500).json({ error: error.message });
    }
  });

  // Get conversion stats for a campaign
  router.get('/conversions/stats/:campaignId', async (req: Request, res: Response) => {
    try {
      const { campaignId } = req.params;
      const { customerId, startDate, endDate } = req.query;

      if (!customerId) {
        return res.status(400).json({ error: 'Missing customerId' });
      }

      const tracker = new GoogleConversionTracker(customerId as string);
      const stats = await tracker.getCampaignConversionStats(
        campaignId,
        new Date(startDate as string || Date.now() - 7 * 24 * 60 * 60 * 1000),
        new Date(endDate as string || Date.now())
      );

      return res.json(stats);
    } catch (error: any) {
      return res.status(500).json({ error: error.message });
    }
  });

  // Get all conversions
  router.get('/conversions', async (req: Request, res: Response) => {
    try {
      const { customerId, startDate, endDate } = req.query;

      if (!customerId) {
        return res.status(400).json({ error: 'Missing customerId' });
      }

      const tracker = new GoogleConversionTracker(customerId as string);
      const conversions = await tracker.getConversions(
        new Date(startDate as string || Date.now() - 30 * 24 * 60 * 60 * 1000),
        new Date(endDate as string || Date.now())
      );

      return res.json({ conversions });
    } catch (error: any) {
      return res.status(500).json({ error: error.message });
    }
  });

  // Get conversion actions
  router.get('/conversion-actions', async (req: Request, res: Response) => {
    try {
      const { customerId } = req.query;

      if (!customerId) {
        return res.status(400).json({ error: 'Missing customerId' });
      }

      const tracker = new GoogleConversionTracker(customerId as string);
      const actions = await tracker.getConversionActions();

      return res.json({ actions });
    } catch (error: any) {
      return res.status(500).json({ error: error.message });
    }
  });

  return router;
}
