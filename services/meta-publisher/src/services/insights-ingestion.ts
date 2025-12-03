import cron from 'node-cron';
import { Pool } from 'pg';
import { MetaAdsManager } from '../facebook/meta-ads-manager';

export class InsightsIngestionService {
    private pool: Pool;
    private metaAdsManager: MetaAdsManager;
    private isRunning: boolean = false;

    constructor(metaAdsManager: MetaAdsManager, databaseUrl: string) {
        this.metaAdsManager = metaAdsManager;
        this.pool = new Pool({
            connectionString: databaseUrl,
            ssl: databaseUrl.includes('localhost') ? false : { rejectUnauthorized: false }
        });
    }

    public startCronJob() {
        // Run every hour at minute 0
        cron.schedule('0 * * * *', async () => {
            console.log('🕒 Starting hourly insights ingestion...');
            await this.ingestInsights();
        });
        console.log('✅ Insights ingestion cron job scheduled (Hourly)');
    }

    public async ingestInsights() {
        if (this.isRunning) {
            console.log('⚠️ Ingestion already running, skipping...');
            return;
        }

        this.isRunning = true;
        try {
            // 1. Get all active ads from DB that have a platform ID
            // We assume 'storage_url' or a new column 'platform_ad_id' holds the Meta Ad ID.
            // For now, let's assume we store Meta Ad ID in 'storage_url' or similar for simplicity,
            // OR we fetch all ads from Meta and match by name/metadata.

            // Better approach: Fetch all ads from Meta Account directly
            const accountInsights = await this.metaAdsManager.getAccountInsights();

            console.log(`📊 Fetched ${accountInsights.length} insight records from Meta`);

            for (const insight of accountInsights) {
                // Update DB based on ad_id (assuming we stored it)
                // If we don't have ad_id in DB, we can't link.
                // For this MVP, we'll try to match by Ad Name if ID fails, or just log.

                await this.updateVideoMetrics(insight);
            }

        } catch (error) {
            console.error('❌ Error during insights ingestion:', error);
        } finally {
            this.isRunning = false;
        }
    }

    private async updateVideoMetrics(insight: any) {
        try {
            // Calculate ROAS
            const spend = parseFloat(insight.spend || '0');
            const revenue = parseFloat(insight.action_values?.[0]?.value || '0'); // Simplified revenue check
            const roas = spend > 0 ? revenue / spend : 0;

            const query = `
        UPDATE videos 
        SET 
          impressions = $1,
          clicks = $2,
          conversions = $3,
          actual_roas = $4,
          updated_at = NOW()
        WHERE 
          platform_ad_id = $5 
          OR storage_url LIKE $6 -- Fallback if we stored ID in URL
      `;

            // We need to ensure 'platform_ad_id' exists in schema or we use a workaround.
            // The schema has 'storage_url', let's assume we might have put the ID there or we need to add a column.
            // For Day 8, let's add the column if missing, or use a flexible match.
            // Let's assume we match by some identifier.

            // WAIT: The schema in database_schema.sql DOES NOT have platform_ad_id.
            // We should add it. For now, I will try to match by name or assume we added it.
            // Let's assume we add it in a migration or use a workaround.

            // Workaround: We'll just log for now if we can't find the video.
            // But to be "Pro Grade", we should add the column.

            // For this step, I will write the code assuming the column exists, 
            // and then I will add a migration file to add the column.

            await this.pool.query(query, [
                insight.impressions,
                insight.clicks,
                insight.actions?.length || 0, // Simplified conversions
                roas,
                insight.ad_id,
                `%${insight.ad_id}%`
            ]);

        } catch (err) {
            console.error(`Failed to update metrics for ad ${insight.ad_id}`, err);
        }
    }
}
