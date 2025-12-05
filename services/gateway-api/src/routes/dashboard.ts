import express, { Request, Response } from 'express';
import axios from 'axios';

const router = express.Router();

// GET /api/dashboard/summary
router.get('/summary', async (req: Request, res: Response) => {
    try {
        const META_PUBLISHER_URL = process.env.META_PUBLISHER_URL || 'http://localhost:8083';

        // Fetch campaigns from meta-publisher
        let campaigns = [];
        let activeCampaignsCount = 0;

        try {
            console.log(`[Dashboard] Fetching campaigns from ${META_PUBLISHER_URL}/api/campaigns`);
            const response = await axios.get(`${META_PUBLISHER_URL}/api/campaigns`);
            if (response.data.status === 'success') {
                campaigns = response.data.campaigns;
                activeCampaignsCount = campaigns.filter((c: any) => c.status === 'ACTIVE').length;
            }
        } catch (error: any) {
            console.warn('[Dashboard] Failed to fetch campaigns:', error.message);
            // Don't fail the whole request, just return empty campaigns
        }

        // Fetch account info for total spend (if available)
        let totalSpend = 0;
        let currency = 'USD';

        try {
            const accountResponse = await axios.get(`${META_PUBLISHER_URL}/api/account/info`);
            // Note: Account info usually doesn't have total spend directly, 
            // we might need to fetch insights for "lifetime" to get spend.
            // For now, we'll use a placeholder or try to fetch insights if possible.
            currency = accountResponse.data.currency;
        } catch (error) {
            console.warn('[Dashboard] Failed to fetch account info');
        }

        // Construct response matching HomePage.tsx expectations
        res.json({
            metrics: {
                activeCampaigns: activeCampaignsCount,
                totalSpend: totalSpend, // This would ideally come from an insights call
                currency: currency,
                videosGenerated: 156, // Placeholder or fetch from DB
                roas: 4.2 // Placeholder or fetch from insights
            },
            campaigns: campaigns.map((c: any) => ({
                id: c.id,
                name: c.name,
                status: c.status,
                objective: c.objective
            }))
        });

    } catch (error: any) {
        console.error('Error fetching dashboard summary:', error);
        res.status(500).json({ error: error.message });
    }
});

export default router;
