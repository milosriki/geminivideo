/**
 * HubSpot Webhook Handler - Artery #1 (HubSpot → ML-Service)
 *
 * Purpose:
 *   Receives HubSpot deal stage changes and routes them to ML-Service for:
 *   - Synthetic revenue calculation
 *   - Attribution to ad clicks
 *   - Budget optimization triggers
 *
 * Flow:
 *   1. Verify HubSpot signature
 *   2. Parse deal stage change
 *   3. Calculate synthetic revenue
 *   4. Attribute to ad click (3-layer attribution)
 *   5. Queue ad change job if needed
 *
 * Created: 2025-12-07
 */

import { Router, Request, Response } from 'express';
import crypto from 'crypto';
import axios from 'axios';

const router = Router();

// Environment variables
const HUBSPOT_CLIENT_SECRET = process.env.HUBSPOT_CLIENT_SECRET || '';
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8003';

interface HubSpotEvent {
  objectId: number;
  propertyName: string;
  propertyValue: string;
  changeSource: string;
  eventId: number;
  subscriptionId: number;
  portalId: number;
  appId: number;
  occurredAt: number;
  eventType: string;
  attemptNumber: number;
}

interface DealStageChange {
  dealId: string;
  tenantId: string;
  stageFrom: string | null;
  stageTo: string;
  dealValue?: number;
  contactEmail?: string;
  contactId?: string;
  occurredAt: Date;
}

interface SyntheticRevenueResult {
  stage_from: string | null;
  stage_to: string;
  synthetic_value: number;
  calculated_value: number;
  confidence: number;
  reason: string;
  timestamp: string;
}

/**
 * Verify HubSpot webhook signature
 */
function verifyHubSpotSignature(req: Request, clientSecret: string): boolean {
  const signature = req.headers['x-hubspot-signature'] as string;
  const requestBody = JSON.stringify(req.body);

  if (!signature || !clientSecret) {
    return false;
  }

  const hash = crypto
    .createHmac('sha256', clientSecret)
    .update(requestBody)
    .digest('hex');

  return signature === hash;
}

/**
 * Parse HubSpot event to deal stage change
 */
function parseDealStageChange(events: HubSpotEvent[]): DealStageChange | null {
  // Find deal stage change event
  const stageEvent = events.find(e =>
    e.eventType === 'deal.propertyChange' &&
    e.propertyName === 'dealstage'
  );

  if (!stageEvent) {
    return null;
  }

  // Extract tenant ID from portal ID (you may need to map this)
  const tenantId = `hubspot_${stageEvent.portalId}`;

  // TODO: Fetch previous stage from HubSpot API or database
  // For now, we'll set it to null (new deal)
  const stageFrom = null;

  return {
    dealId: stageEvent.objectId.toString(),
    tenantId,
    stageFrom,
    stageTo: stageEvent.propertyValue,
    occurredAt: new Date(stageEvent.occurredAt),
  };
}

/**
 * Calculate synthetic revenue via ML-Service
 */
async function calculateSyntheticRevenue(
  tenantId: string,
  stageFrom: string | null,
  stageTo: string,
  dealValue?: number
): Promise<SyntheticRevenueResult> {
  const response = await axios.post(
    `${ML_SERVICE_URL}/api/ml/synthetic-revenue/calculate`,
    {
      tenant_id: tenantId,
      stage_from: stageFrom,
      stage_to: stageTo,
      deal_value: dealValue,
    },
    { timeout: 10000 }
  );

  return response.data;
}

/**
 * Attribute conversion to ad click via ML-Service
 */
async function attributeConversion(
  tenantId: string,
  dealId: string,
  syntheticValue: number,
  stageTo: string,
  occurredAt: Date,
  contactEmail?: string
): Promise<any> {
  // Generate conversion fingerprint (would come from contact tracking in real implementation)
  const fingerprint = contactEmail
    ? crypto.createHash('sha256').update(contactEmail).digest('hex')
    : undefined;

  const response = await axios.post(
    `${ML_SERVICE_URL}/api/ml/attribution/attribute-conversion`,
    {
      tenant_id: tenantId,
      conversion_id: dealId,
      conversion_type: `deal_${stageTo}`,
      conversion_value: syntheticValue,
      conversion_timestamp: occurredAt.toISOString(),
      fingerprint_hash: fingerprint,
      // IP and user agent would come from click tracking
    },
    { timeout: 10000 }
  );

  return response.data;
}

/**
 * Queue ad change job if optimization is needed
 * (This would trigger budget reallocation based on performance)
 */
async function queueAdChangeIfNeeded(
  attribution: any,
  syntheticRevenue: SyntheticRevenueResult,
  tenantId: string
): Promise<void> {
  // Only queue if attribution was successful
  if (!attribution.success) {
    return;
  }

  // Check if this conversion should trigger optimization
  // (e.g., significant value, high confidence)
  if (syntheticRevenue.calculated_value > 1000 && syntheticRevenue.confidence > 0.7) {
    // TODO: Queue pg-boss job for budget optimization
    // This would be handled by SafeExecutor worker
    console.log(`[HubSpot Webhook] Queuing optimization for ad ${attribution.ad_id}`);

    // Example (requires pg-boss setup):
    // await pgBoss.send('budget-optimization', {
    //   tenant_id: tenantId,
    //   ad_id: attribution.ad_id,
    //   campaign_id: attribution.campaign_id,
    //   trigger: 'high_value_conversion',
    //   conversion_value: syntheticRevenue.calculated_value,
    // });
  }
}

/**
 * Main webhook endpoint
 */
router.post('/webhook/hubspot', async (req: Request, res: Response) => {
  try {
    // Step 1: Verify signature
    if (!verifyHubSpotSignature(req, HUBSPOT_CLIENT_SECRET)) {
      console.error('[HubSpot Webhook] Invalid signature');
      return res.status(403).json({ error: 'Invalid signature' });
    }

    // Step 2: Parse events
    const events: HubSpotEvent[] = req.body;

    if (!Array.isArray(events) || events.length === 0) {
      return res.status(400).json({ error: 'No events in webhook' });
    }

    // Step 3: Extract deal stage change
    const stageChange = parseDealStageChange(events);

    if (!stageChange) {
      // Not a deal stage change, ignore
      return res.status(200).json({ status: 'ignored', reason: 'Not a deal stage change' });
    }

    console.log(`[HubSpot Webhook] Deal ${stageChange.dealId} moved to ${stageChange.stageTo}`);

    // Step 4: Calculate synthetic revenue
    const syntheticRevenue = await calculateSyntheticRevenue(
      stageChange.tenantId,
      stageChange.stageFrom,
      stageChange.stageTo,
      stageChange.dealValue
    );

    console.log(
      `[HubSpot Webhook] Synthetic revenue: $${syntheticRevenue.synthetic_value} ` +
      `(+$${syntheticRevenue.calculated_value}, ${syntheticRevenue.confidence * 100}% confidence)`
    );

    // Step 5: Attribute to ad click
    const attribution = await attributeConversion(
      stageChange.tenantId,
      stageChange.dealId,
      syntheticRevenue.calculated_value,
      stageChange.stageTo,
      stageChange.occurredAt,
      stageChange.contactEmail
    );

    console.log(
      `[HubSpot Webhook] Attribution: ${attribution.success ? 'SUCCESS' : 'FAILED'} ` +
      `(method: ${attribution.attribution_method}, confidence: ${attribution.attribution_confidence})`
    );

    // Step 6: Queue optimization if needed
    if (attribution.success) {
      await queueAdChangeIfNeeded(attribution, syntheticRevenue, stageChange.tenantId);
    }

    // Return success
    return res.status(200).json({
      status: 'processed',
      deal_id: stageChange.dealId,
      stage_to: stageChange.stageTo,
      synthetic_revenue: {
        value: syntheticRevenue.synthetic_value,
        incremental: syntheticRevenue.calculated_value,
        confidence: syntheticRevenue.confidence,
      },
      attribution: {
        success: attribution.success,
        method: attribution.attribution_method,
        confidence: attribution.attribution_confidence,
        ad_id: attribution.ad_id,
        campaign_id: attribution.campaign_id,
      },
    });

  } catch (error: any) {
    console.error('[HubSpot Webhook] Error processing webhook:', error.message);

    // Return 200 to prevent HubSpot retries for application errors
    // (HubSpot will retry on 5xx errors)
    return res.status(200).json({
      status: 'error',
      error: error.message,
      note: 'Logged for investigation',
    });
  }
});

/**
 * Healthcheck endpoint
 */
router.get('/webhook/hubspot/health', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    service: 'hubspot-webhook',
    ml_service_url: ML_SERVICE_URL,
    signature_verification: !!HUBSPOT_CLIENT_SECRET,
  });
});

export default router;
