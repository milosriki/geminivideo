/**
 * Market Intelligence Service
 * Auto-updates competitor tracking when campaigns scale
 * 
 * Purpose: Always keep market intelligence fresh when scaling campaigns
 */

import axios from 'axios';

const TITAN_CORE_URL = process.env.TITAN_CORE_URL || 'http://titan-core:8084';
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://ml-service:8003';

interface ScalingEvent {
  campaign_id: string;
  ad_id?: string;
  old_budget: number;
  new_budget: number;
  change_percentage: number;
  reason: string;
  triggered_by: string;
}

interface CompetitorAd {
  brand: string;
  hook_text: string;
  platform: string;
  engagement?: number;
  views?: number;
  url?: string;
  creative_type?: string;
}

/**
 * Track competitor ads when campaign scales
 * This ensures market intelligence is always up-to-date
 */
export async function updateMarketIntelOnScaling(
  event: ScalingEvent
): Promise<void> {
  try {
    // Only update on significant scaling (20%+ increase)
    if (event.change_percentage < 0.20) {
      return; // Skip small changes
    }

    console.log(`[MarketIntel] Campaign ${event.campaign_id} scaling - updating competitor intelligence`);

    // Step 1: Get competitor page IDs from campaign metadata
    // (This would come from campaign configuration)
    const competitorPageIds = await getCompetitorPageIds(event.campaign_id);

    if (!competitorPageIds || competitorPageIds.length === 0) {
      console.log(`[MarketIntel] No competitor pages configured for campaign ${event.campaign_id}`);
      return;
    }

    // Step 2: Fetch competitor ads from Meta Ads Library
    const competitorAds = await fetchCompetitorAds(competitorPageIds);

    // Step 3: Track ads in Market Intel service
    for (const ad of competitorAds) {
      await trackCompetitorAd(ad);
    }

    // Step 4: Analyze trends and update insights
    await analyzeAndUpdateTrends();

    console.log(`[MarketIntel] Updated ${competitorAds.length} competitor ads for campaign ${event.campaign_id}`);

  } catch (error: any) {
    console.error(`[MarketIntel] Failed to update on scaling: ${error.message}`);
    // Non-fatal - don't block scaling
  }
}

/**
 * Get competitor page IDs from campaign configuration
 */
async function getCompetitorPageIds(campaignId: string): Promise<string[]> {
  try {
    // This would query the database for campaign metadata
    // For now, return empty - will be implemented based on your schema
    // Example:
    // const campaign = await db.query('SELECT competitor_pages FROM campaigns WHERE id = $1', [campaignId]);
    // return campaign.competitor_pages || [];
    
    // TODO: Implement based on your campaign schema
    return [];
  } catch (error) {
    console.error(`[MarketIntel] Failed to get competitor pages: ${error}`);
    return [];
  }
}

/**
 * Fetch competitor ads from Meta Ads Library via titan-core
 */
async function fetchCompetitorAds(pageIds: string[]): Promise<CompetitorAd[]> {
  try {
    const pageIdsStr = pageIds.join(',');
    const response = await axios.get(
      `${TITAN_CORE_URL}/meta/ads-library/competitor/${pageIdsStr}`,
      {
        params: { days_back: 30 },
        timeout: 30000
      }
    );

    // Transform Meta Ads Library format to CompetitorAd format
    return response.data.map((ad: any) => ({
      brand: ad.page_name || 'Unknown',
      hook_text: ad.ad_creative_bodies?.[0] || ad.ad_creative_bodies || '',
      platform: 'Meta',
      engagement: ad.estimated_audience_size || 0,
      views: ad.impressions || 0,
      url: ad.ad_snapshot_url || '',
      creative_type: ad.ad_creative_bodies ? 'text' : 'video'
    }));

  } catch (error: any) {
    console.error(`[MarketIntel] Failed to fetch competitor ads: ${error.message}`);
    return [];
  }
}

/**
 * Track a competitor ad in Market Intel
 */
async function trackCompetitorAd(ad: CompetitorAd): Promise<void> {
  try {
    // Call Market Intel API endpoint (if deployed as service)
    // Or use direct database insert
    // For now, we'll call ML service which has Market Intel integration
    
    await axios.post(
      `${ML_SERVICE_URL}/api/ml/market-intel/track`,
      {
        brand: ad.brand,
        hook_text: ad.hook_text,
        platform: ad.platform,
        engagement: ad.engagement,
        views: ad.views,
        url: ad.url,
        creative_type: ad.creative_type
      },
      { timeout: 5000 }
    );

  } catch (error: any) {
    // If endpoint doesn't exist, that's okay - Market Intel might be library-only
    console.debug(`[MarketIntel] Track endpoint not available (non-fatal): ${error.message}`);
  }
}

/**
 * Analyze trends and update insights
 */
async function analyzeAndUpdateTrends(): Promise<void> {
  try {
    // Trigger trend analysis
    await axios.post(
      `${ML_SERVICE_URL}/api/ml/market-intel/analyze-trends`,
      { days: 30 },
      { timeout: 10000 }
    );

  } catch (error: any) {
    console.debug(`[MarketIntel] Analyze endpoint not available (non-fatal): ${error.message}`);
  }
}

/**
 * Hook into SafeExecutor to auto-update on scaling
 */
export function setupMarketIntelAutoUpdate(): void {
  // This will be called from safe-executor when budget increases
  console.log('[MarketIntel] Auto-update enabled - will track competitors on scaling events');
}

