# 🚀 API MISMATCH QUICK FIX GUIDE
**Copy-paste code snippets to fix all 11 API contract mismatches**

---

## 1️⃣ Add Campaign Resume Endpoint
**File:** `/home/user/geminivideo/services/gateway-api/src/routes/campaigns.ts`
**Location:** After line 656 (after pause endpoint)

```typescript
  /**
   * POST /api/campaigns/:id/resume
   * Resume a paused campaign
   */
  router.post(
    '/:id/resume',
    apiRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;

        console.log(`Resuming campaign: ${id}`);

        // Update campaign status to active
        const updateQuery = `
          UPDATE campaigns
          SET status = 'active', updated_at = NOW()
          WHERE id = $1 AND status = 'paused'
          RETURNING *
        `;

        const result = await pgPool.query(updateQuery, [id]);

        if (result.rows.length === 0) {
          return res.status(404).json({
            error: 'Campaign not found or not paused',
            message: `Campaign with id ${id} does not exist or is not paused`
          });
        }

        const campaign = result.rows[0];

        console.log(`Campaign resumed successfully: ${id}`);

        res.json({
          status: 'success',
          message: 'Campaign resumed successfully',
          campaign: {
            id: campaign.id,
            name: campaign.name,
            status: campaign.status
          }
        });

      } catch (error: any) {
        console.error('Error resuming campaign:', error);
        res.status(500).json({
          error: 'Failed to resume campaign',
          message: error.message
        });
      }
    }
  );
```

---

## 2️⃣ Add Analytics ROI Endpoints
**File:** `/home/user/geminivideo/services/gateway-api/src/routes/analytics.ts`
**Location:** After line 651 (after real-time endpoint)

```typescript
  /**
   * GET /api/analytics/roi/performance
   * Get ROI/ROAS performance metrics
   */
  router.get(
    '/roi/performance',
    apiRateLimiter,
    validateInput({
      query: {
        timeRange: { type: 'string', required: false, enum: ['7d', '30d', '90d'] }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { timeRange = '30d' } = req.query;
        const days = parseInt(timeRange.replace('d', ''));

        console.log(`Fetching ROI performance: timeRange=${timeRange}`);

        const query = `
          SELECT
            COALESCE(SUM(pm.spend), 0) as total_spend,
            COALESCE(SUM(pm.conversions), 0) as total_conversions,
            COALESCE(SUM(pm.conversions * 50), 0) as total_revenue,
            CASE
              WHEN SUM(pm.spend) > 0
              THEN (SUM(pm.conversions * 50) / SUM(pm.spend))
              ELSE 0
            END as roas,
            COALESCE(AVG(pm.ctr), 0) as avg_ctr,
            COUNT(DISTINCT pm.video_id) as ad_count
          FROM performance_metrics pm
          WHERE pm.date >= CURRENT_DATE - INTERVAL '${days} days'
        `;

        const result = await pgPool.query(query);
        const metrics = result.rows[0];

        res.json({
          status: 'success',
          time_range: timeRange,
          performance: {
            total_spend: parseFloat(metrics.total_spend),
            total_conversions: parseInt(metrics.total_conversions),
            total_revenue: parseFloat(metrics.total_revenue),
            roas: parseFloat(metrics.roas),
            avg_ctr: parseFloat(metrics.avg_ctr),
            ad_count: parseInt(metrics.ad_count)
          }
        });

      } catch (error: any) {
        console.error('Error fetching ROI performance:', error);
        res.status(500).json({
          error: 'Failed to fetch ROI performance',
          message: error.message
        });
      }
    }
  );

  /**
   * GET /api/analytics/roi/trends
   * Get ROI trends over time
   */
  router.get(
    '/roi/trends',
    apiRateLimiter,
    validateInput({
      query: {
        period: { type: 'string', required: false, enum: ['daily', 'weekly', 'monthly'] }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { period = 'weekly' } = req.query;

        console.log(`Fetching ROI trends: period=${period}`);

        const query = `
          SELECT
            DATE_TRUNC('${period}', pm.date) as period,
            COALESCE(SUM(pm.spend), 0) as spend,
            COALESCE(SUM(pm.conversions), 0) as conversions,
            COALESCE(SUM(pm.conversions * 50), 0) as revenue,
            CASE
              WHEN SUM(pm.spend) > 0
              THEN (SUM(pm.conversions * 50) / SUM(pm.spend))
              ELSE 0
            END as roas
          FROM performance_metrics pm
          WHERE pm.date >= CURRENT_DATE - INTERVAL '90 days'
          GROUP BY DATE_TRUNC('${period}', pm.date)
          ORDER BY period ASC
        `;

        const result = await pgPool.query(query);

        const trends = result.rows.map(row => ({
          period: row.period,
          spend: parseFloat(row.spend),
          conversions: parseInt(row.conversions),
          revenue: parseFloat(row.revenue),
          roas: parseFloat(row.roas)
        }));

        res.json({
          status: 'success',
          period,
          trends
        });

      } catch (error: any) {
        console.error('Error fetching ROI trends:', error);
        res.status(500).json({
          error: 'Failed to fetch ROI trends',
          message: error.message
        });
      }
    }
  );
```

---

## 3️⃣ Add A/B Test Start/Stop Endpoints
**File:** `/home/user/geminivideo/services/gateway-api/src/routes/ab-tests.ts`
**Location:** After line 541 (after pause endpoint)

```typescript
  /**
   * POST /api/ab-tests/:id/start
   * Start an A/B test experiment
   */
  router.post(
    '/:id/start',
    apiRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;

        console.log(`Starting A/B test: ${id}`);

        // Update campaign status to active
        const updateQuery = `
          UPDATE campaigns
          SET status = 'active', updated_at = NOW()
          WHERE id = $1 AND status IN ('draft', 'paused')
          RETURNING *
        `;

        const result = await pgPool.query(updateQuery, [id]);

        if (result.rows.length === 0) {
          return res.status(404).json({
            error: 'Experiment not found or already active',
            message: `Experiment with id ${id} does not exist or is already active`
          });
        }

        // Notify ML service
        try {
          await axios.post(
            `${ML_SERVICE_URL}/api/ml/ab/experiments/${id}/start`,
            {},
            { timeout: 5000 }
          );
        } catch (mlError: any) {
          console.warn('ML service notification failed:', mlError.message);
        }

        res.json({
          status: 'success',
          message: 'A/B test started successfully',
          experiment_id: id
        });

      } catch (error: any) {
        console.error('Error starting A/B test:', error);
        res.status(500).json({
          error: 'Failed to start A/B test',
          message: error.message
        });
      }
    }
  );

  /**
   * POST /api/ab-tests/:id/stop
   * Stop an A/B test experiment
   */
  router.post(
    '/:id/stop',
    apiRateLimiter,
    validateInput({
      params: {
        id: { type: 'uuid', required: true }
      }
    }),
    async (req: Request, res: Response) => {
      try {
        const { id } = req.params;

        console.log(`Stopping A/B test: ${id}`);

        // Update campaign status to completed
        const updateQuery = `
          UPDATE campaigns
          SET status = 'completed', updated_at = NOW()
          WHERE id = $1 AND status = 'active'
          RETURNING *
        `;

        const result = await pgPool.query(updateQuery, [id]);

        if (result.rows.length === 0) {
          return res.status(404).json({
            error: 'Experiment not found or not active',
            message: `Experiment with id ${id} does not exist or is not active`
          });
        }

        // Notify ML service
        try {
          await axios.post(
            `${ML_SERVICE_URL}/api/ml/ab/experiments/${id}/stop`,
            {},
            { timeout: 5000 }
          );
        } catch (mlError: any) {
          console.warn('ML service notification failed:', mlError.message);
        }

        res.json({
          status: 'success',
          message: 'A/B test stopped successfully',
          experiment_id: id
        });

      } catch (error: any) {
        console.error('Error stopping A/B test:', error);
        res.status(500).json({
          error: 'Failed to stop A/B test',
          message: error.message
        });
      }
    }
  );
```

---

## 4️⃣ Add Publishing Proxy Endpoints
**File:** `/home/user/geminivideo/services/gateway-api/src/index.ts`
**Location:** After line 651 (after /api/insights endpoint)

```typescript
// POST /api/publish/google - Proxy to Google Ads publishing
app.post('/api/publish/google',
  uploadRateLimiter,
  validateInput({
    body: {
      campaignId: { type: 'string', required: true },
      adAccountId: { type: 'string', required: true },
      config: { type: 'object', required: false }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const { campaignId, adAccountId, config } = req.body;

      console.log(`Publishing to Google Ads: campaign=${campaignId}`);

      // Forward to multi-platform publisher or Google Ads service
      const response = await axios.post(
        `${GOOGLE_ADS_URL}/api/publish`,
        {
          campaign_id: campaignId,
          ad_account_id: adAccountId,
          ...config
        },
        { timeout: 30000 }
      );

      res.status(202).json({
        status: 'accepted',
        platform: 'google',
        campaign_id: campaignId,
        job_id: response.data.job_id || uuidv4(),
        message: 'Google Ads publishing initiated',
        data: response.data
      });

    } catch (error: any) {
      console.error('Google Ads publishing error:', error.message);
      res.status(error.response?.status || 500).json({
        error: 'Publishing failed',
        message: error.message,
        details: error.response?.data
      });
    }
  });

// POST /api/publish/tiktok - Proxy to TikTok Ads publishing
app.post('/api/publish/tiktok',
  uploadRateLimiter,
  validateInput({
    body: {
      campaignId: { type: 'string', required: true },
      adAccountId: { type: 'string', required: true },
      config: { type: 'object', required: false }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const { campaignId, adAccountId, config } = req.body;

      console.log(`Publishing to TikTok Ads: campaign=${campaignId}`);

      // Forward to TikTok Ads service
      const response = await axios.post(
        `${TIKTOK_ADS_URL}/api/publish`,
        {
          campaign_id: campaignId,
          ad_account_id: adAccountId,
          ...config
        },
        { timeout: 30000 }
      );

      res.status(202).json({
        status: 'accepted',
        platform: 'tiktok',
        campaign_id: campaignId,
        job_id: response.data.job_id || uuidv4(),
        message: 'TikTok Ads publishing initiated',
        data: response.data
      });

    } catch (error: any) {
      console.error('TikTok Ads publishing error:', error.message);
      res.status(error.response?.status || 500).json({
        error: 'Publishing failed',
        message: error.message,
        details: error.response?.data
      });
    }
  });

// GET /api/publish/campaigns/:campaignId - Get all publish jobs for a campaign
app.get('/api/publish/campaigns/:campaignId',
  apiRateLimiter,
  validateInput({
    params: {
      campaignId: { type: 'uuid', required: true }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const { campaignId } = req.params;

      console.log(`Fetching publish jobs for campaign: ${campaignId}`);

      // Get all jobs for this campaign from status aggregator
      const allJobs = statusAggregator.getRecentJobs(100);
      const campaignJobs = allJobs.filter(job => job.campaignId === campaignId);

      res.json({
        status: 'success',
        campaign_id: campaignId,
        jobs: campaignJobs,
        count: campaignJobs.length
      });

    } catch (error: any) {
      console.error('Error fetching campaign publish jobs:', error.message);
      res.status(500).json({
        error: 'Failed to fetch publish jobs',
        message: error.message
      });
    }
  });
```

---

## 5️⃣ Fix Frontend promoteWinner Call
**File:** `/home/user/geminivideo/frontend/src/lib/api.ts`
**Location:** Replace line 531-533

```typescript
  /**
   * Promote winner
   */
  async promoteWinner(testId: string, winner: 'A' | 'B'): Promise<ABTest> {
    // First, get test details to get variant IDs
    const test = await this.get<ABTest>(`/api/ab-tests/${testId}`);

    if (!test.variantA || !test.variantB) {
      throw new Error('Test variants not found');
    }

    // Map winner letter to variant_id
    const variantId = winner === 'A' ? test.variantA.id : test.variantB.id;

    // Backend expects { variant_id, new_budget }
    // Calculate new budget (e.g., full campaign budget)
    const newBudget = test.budget?.amount || 1000; // Default or from test config

    return this.post(`/api/ab-tests/${testId}/promote`, {
      variant_id: variantId,
      new_budget: newBudget
    });
  }
```

**OR Update TypeScript Types:**
```typescript
// frontend/src/lib/api.ts - Update ABTestVariant interface
export interface ABTestVariant {
  id?: string;  // ADD THIS
  name: string;
  creative: CampaignCreative;
  targeting?: Partial<TargetingConfig>;
  budget?: Partial<BudgetConfig>;
}
```

---

## 6️⃣ Fix Prediction Accuracy Path
**File:** `/home/user/geminivideo/frontend/src/lib/api.ts`
**Location:** Line 458

```typescript
  /**
   * Get prediction accuracy
   */
  async getPredictionAccuracy(timeRange = 'last_30d'): Promise<PredictionAccuracy[]> {
    // CHANGE PATH FROM /api/analytics/predictions/accuracy
    // TO /api/predictions/accuracy
    return this.get('/api/predictions/accuracy', { params: { timeRange } });
  }
```

---

## 7️⃣ Update Campaign Type Handling (Optional)
**File:** `/home/user/geminivideo/frontend/src/lib/api.ts`
**Add response transformer helper:**

```typescript
/**
 * Transform backend response to frontend Campaign type
 */
function transformCampaignResponse(backendData: any): Campaign {
  return {
    id: backendData.id,
    name: backendData.name,
    status: backendData.status,
    // Map budget_daily (number) to BudgetConfig object
    budget: {
      type: 'daily',
      amount: parseFloat(backendData.budget_daily || 0),
      bidStrategy: 'lowest_cost'
    },
    // Map target_audience (json) to TargetingConfig object
    targeting: {
      locations: backendData.target_audience?.locations || [],
      ageMin: backendData.target_audience?.age_min || 18,
      ageMax: backendData.target_audience?.age_max || 65,
      genders: backendData.target_audience?.genders || ['all'],
      interests: backendData.target_audience?.interests || [],
      behaviors: backendData.target_audience?.behaviors || [],
      customAudiences: backendData.target_audience?.custom_audiences || [],
      lookalikes: backendData.target_audience?.lookalikes || [],
      detailedTargeting: backendData.target_audience?.detailed_targeting || {}
    },
    // Provide defaults for missing fields
    objective: backendData.objective || 'conversions',
    creatives: backendData.creatives || [],
    schedule: backendData.schedule || {
      startDate: new Date().toISOString(),
      timeZone: 'America/Los_Angeles'
    },
    predictions: backendData.predictions,
    abTestConfig: backendData.ab_test_config,
    createdAt: new Date(backendData.created_at),
    updatedAt: new Date(backendData.updated_at)
  };
}

// Use in getCampaigns and getCampaignById:
async getCampaigns(filters?: any): Promise<Campaign[]> {
  const response = await this.get('/api/campaigns', { params: filters });
  return response.campaigns.map(transformCampaignResponse);
}

async getCampaignById(campaignId: string): Promise<Campaign> {
  const response = await this.get(`/api/campaigns/${campaignId}`);
  return transformCampaignResponse(response.campaign);
}
```

---

## ✅ Quick Verification
After applying fixes, test with:

```bash
# 1. Campaign resume
curl -X POST http://localhost:8000/api/campaigns/YOUR_ID/resume
# Should return 200 with campaign data

# 2. ROI endpoints
curl "http://localhost:8000/api/analytics/roi/performance?timeRange=30d"
curl "http://localhost:8000/api/analytics/roi/trends?period=weekly"
# Should return 200 with metrics

# 3. A/B test lifecycle
curl -X POST http://localhost:8000/api/ab-tests/YOUR_ID/start
curl -X POST http://localhost:8000/api/ab-tests/YOUR_ID/stop
# Should return 200 success messages

# 4. Publishing
curl -X POST http://localhost:8000/api/publish/google \
  -H "Content-Type: application/json" \
  -d '{"campaignId":"123","adAccountId":"456"}'

curl -X POST http://localhost:8000/api/publish/tiktok \
  -H "Content-Type: application/json" \
  -d '{"campaignId":"123","adAccountId":"456"}'

curl http://localhost:8000/api/publish/campaigns/YOUR_ID
# All should return 200/202 responses

# 5. Prediction accuracy
curl http://localhost:8000/api/predictions/accuracy?timeRange=30d
# Should return 200 with accuracy data
```

---

## 📋 Deployment Checklist
- [ ] Apply all 7 fixes above
- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Test all frontend hooks
- [ ] Verify TypeScript compilation
- [ ] Check browser console for errors
- [ ] Test E2E user workflows
- [ ] Deploy to staging first
- [ ] Smoke test all endpoints
- [ ] Monitor error logs

---

**All fixes estimated: 2-4 hours implementation + 2 hours testing = 4-6 hours total**
