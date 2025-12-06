#!/usr/bin/env ts-node
/**
 * AGENT 90: API ROUTE FIXES
 * Adds missing API endpoints and fixes request/response schemas
 * This script is IDEMPOTENT - safe to run multiple times
 */

import * as fs from 'fs';
import * as path from 'path';

const PROJECT_ROOT = path.join(__dirname, '../..');
let fixesApplied = 0;
let fixesFailed = 0;

console.log('='.repeat(50));
console.log('AGENT 90: API ROUTE FIXES');
console.log('='.repeat(50));
console.log(`Working directory: ${PROJECT_ROOT}\n`);

/**
 * Add code to file if it doesn't exist
 */
function addCodeToFile(
  filePath: string,
  searchPattern: string | RegExp,
  codeToAdd: string,
  description: string,
  fixNum: number,
  total: number
): boolean {
  console.log(`[FIX ${fixNum}/${total}] ${description}...`);

  const fullPath = path.join(PROJECT_ROOT, filePath);

  if (!fs.existsSync(fullPath)) {
    console.log(`  ⊘ File not found: ${filePath}`);
    return false;
  }

  let content = fs.readFileSync(fullPath, 'utf-8');

  // Check if code already exists
  if (content.includes(codeToAdd)) {
    console.log(`  ⊘ Already added`);
    return true;
  }

  // Find insertion point
  const match = content.match(searchPattern);
  if (!match) {
    console.log(`  ⊘ Insertion point not found`);
    return false;
  }

  // Insert code
  const insertIndex = match.index! + match[0].length;
  content = content.slice(0, insertIndex) + '\n\n' + codeToAdd + content.slice(insertIndex);

  fs.writeFileSync(fullPath, content, 'utf-8');
  console.log(`  ✓ Added route`);
  fixesApplied++;
  return true;
}

// ============================================
// FIX 1: Add POST /api/campaigns/:id/resume endpoint
// ============================================
addCodeToFile(
  'services/gateway-api/src/routes/campaigns.ts',
  /router\.post\(['"]\/\:id\/pause['"]/,
  `// ADDED BY AGENT 90: Resume campaign endpoint
router.post('/:id/resume', validateAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const userId = (req as any).user.uid;

    // Update campaign status to active
    const campaign = await prisma.campaign.update({
      where: { id, user_id: userId },
      data: { status: 'active' }
    });

    res.json({
      success: true,
      campaign,
      message: 'Campaign resumed successfully'
    });
  } catch (error: any) {
    console.error('Resume campaign error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to resume campaign'
    });
  }
});`,
  'Add POST /api/campaigns/:id/resume',
  1,
  9
);

// ============================================
// FIX 2: Add GET /api/analytics/roi/performance endpoint
// ============================================
addCodeToFile(
  'services/gateway-api/src/routes/analytics.ts',
  /export default router;/,
  `// ADDED BY AGENT 90: ROI performance endpoint
router.get('/roi/performance', validateAuth, async (req, res) => {
  try {
    const { timeRange = '7d' } = req.query;
    const userId = (req as any).user.uid;

    // Calculate ROI metrics from campaigns
    const campaigns = await prisma.campaign.findMany({
      where: { user_id: userId },
      include: { videos: true }
    });

    const totalSpend = campaigns.reduce((sum, c) => sum + (c.total_spend || 0), 0);
    const totalRevenue = campaigns.reduce((sum, c) => sum + (c.total_revenue || 0), 0);
    const roi = totalSpend > 0 ? ((totalRevenue - totalSpend) / totalSpend) * 100 : 0;
    const roas = totalSpend > 0 ? totalRevenue / totalSpend : 0;

    res.json({
      success: true,
      data: {
        roi,
        roas,
        totalSpend,
        totalRevenue,
        profit: totalRevenue - totalSpend,
        campaignCount: campaigns.length,
        timeRange
      }
    });
  } catch (error: any) {
    console.error('ROI performance error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to fetch ROI performance'
    });
  }
});`,
  'Add GET /api/analytics/roi/performance',
  2,
  9
);

// ============================================
// FIX 3: Add GET /api/analytics/roi/trends endpoint
// ============================================
addCodeToFile(
  'services/gateway-api/src/routes/analytics.ts',
  /export default router;/,
  `// ADDED BY AGENT 90: ROI trends endpoint
router.get('/roi/trends', validateAuth, async (req, res) => {
  try {
    const { period = 'daily' } = req.query;
    const userId = (req as any).user.uid;

    // Fetch performance metrics grouped by date
    const metrics = await prisma.performanceMetric.findMany({
      where: {
        campaign: { user_id: userId }
      },
      orderBy: { timestamp: 'asc' }
    });

    // Group by period and calculate ROI/ROAS
    const trends = metrics.reduce((acc: any[], metric) => {
      const spend = metric.spend || 0;
      const revenue = metric.revenue || 0;
      const roas = spend > 0 ? revenue / spend : 0;
      const roi = spend > 0 ? ((revenue - spend) / spend) * 100 : 0;

      acc.push({
        date: metric.timestamp,
        roi,
        roas,
        spend,
        revenue
      });
      return acc;
    }, []);

    res.json({
      success: true,
      data: trends,
      period
    });
  } catch (error: any) {
    console.error('ROI trends error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to fetch ROI trends'
    });
  }
});`,
  'Add GET /api/analytics/roi/trends',
  3,
  9
);

// ============================================
// FIX 4: Add POST /api/ab-tests/:id/start endpoint
// ============================================
addCodeToFile(
  'services/gateway-api/src/routes/ab-tests.ts',
  /router\.post\(['"]\/\:id\/pause['"]/,
  `// ADDED BY AGENT 90: Start A/B test endpoint
router.post('/:id/start', validateAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const userId = (req as any).user.uid;

    const experiment = await prisma.experiment.update({
      where: { id, user_id: userId },
      data: {
        status: 'active',
        started_at: new Date()
      }
    });

    res.json({
      success: true,
      experiment,
      message: 'A/B test started successfully'
    });
  } catch (error: any) {
    console.error('Start A/B test error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to start A/B test'
    });
  }
});`,
  'Add POST /api/ab-tests/:id/start',
  4,
  9
);

// ============================================
// FIX 5: Add POST /api/ab-tests/:id/stop endpoint
// ============================================
addCodeToFile(
  'services/gateway-api/src/routes/ab-tests.ts',
  /router\.post\(['"]\/\:id\/start['"]/,
  `// ADDED BY AGENT 90: Stop A/B test endpoint
router.post('/:id/stop', validateAuth, async (req, res) => {
  try {
    const { id } = req.params;
    const userId = (req as any).user.uid;

    const experiment = await prisma.experiment.update({
      where: { id, user_id: userId },
      data: {
        status: 'completed',
        ended_at: new Date()
      }
    });

    res.json({
      success: true,
      experiment,
      message: 'A/B test stopped successfully'
    });
  } catch (error: any) {
    console.error('Stop A/B test error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to stop A/B test'
    });
  }
});`,
  'Add POST /api/ab-tests/:id/stop',
  5,
  9
);

// ============================================
// FIX 6: Add POST /api/publish/google endpoint
// ============================================
addCodeToFile(
  'services/gateway-api/src/index.ts',
  /app\.post\(['"]\/api\/publish\/meta['"]/,
  `// ADDED BY AGENT 90: Google Ads publishing endpoint
app.post('/api/publish/google', validateAuth, async (req, res) => {
  try {
    // Proxy to google-ads service
    const response = await fetch(\`\${process.env.GOOGLE_ADS_URL}/publish\`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();
    res.json(data);
  } catch (error: any) {
    console.error('Google publish error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to publish to Google Ads'
    });
  }
});`,
  'Add POST /api/publish/google',
  6,
  9
);

// ============================================
// FIX 7: Add POST /api/publish/tiktok endpoint
// ============================================
addCodeToFile(
  'services/gateway-api/src/index.ts',
  /app\.post\(['"]\/api\/publish\/google['"]/,
  `// ADDED BY AGENT 90: TikTok Ads publishing endpoint
app.post('/api/publish/tiktok', validateAuth, async (req, res) => {
  try {
    // Proxy to tiktok-ads service
    const response = await fetch(\`\${process.env.TIKTOK_ADS_URL}/publish\`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();
    res.json(data);
  } catch (error: any) {
    console.error('TikTok publish error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to publish to TikTok Ads'
    });
  }
});`,
  'Add POST /api/publish/tiktok',
  7,
  9
);

// ============================================
// FIX 8: Add GET /api/publish/campaigns/:campaignId endpoint
// ============================================
addCodeToFile(
  'services/gateway-api/src/index.ts',
  /app\.get\(['"]\/api\/publish\/jobs['"]/,
  `// ADDED BY AGENT 90: Get publish jobs for campaign
app.get('/api/publish/campaigns/:campaignId', validateAuth, async (req, res) => {
  try {
    const { campaignId } = req.params;
    const userId = (req as any).user.uid;

    // Verify campaign ownership
    const campaign = await prisma.campaign.findFirst({
      where: { id: campaignId, user_id: userId }
    });

    if (!campaign) {
      return res.status(404).json({
        success: false,
        error: 'Campaign not found'
      });
    }

    // Fetch publish jobs for this campaign
    const jobs = await prisma.publishJob.findMany({
      where: { campaign_id: campaignId },
      orderBy: { created_at: 'desc' }
    });

    res.json({
      success: true,
      jobs
    });
  } catch (error: any) {
    console.error('Get campaign publish jobs error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to fetch campaign publish jobs'
    });
  }
});`,
  'Add GET /api/publish/campaigns/:campaignId',
  8,
  9
);

// ============================================
// FIX 9: Fix promoteWinner schema in frontend
// ============================================
console.log('[FIX 9/9] Fix promoteWinner API contract...');
const apiFilePath = path.join(PROJECT_ROOT, 'frontend/src/lib/api.ts');

if (fs.existsSync(apiFilePath)) {
  let content = fs.readFileSync(apiFilePath, 'utf-8');

  const oldCode = `promoteWinner(testId: string, winner: 'A' | 'B')`;
  const newCode = `promoteWinner(testId: string, variantId: string, newBudget: number)`;

  if (content.includes(oldCode)) {
    // Update function signature and request body
    content = content.replace(
      /promoteWinner\(testId: string, winner: ['"]A['"] \| ['"]B['"]\)\s*{[\s\S]*?return this\.request/,
      `promoteWinner(testId: string, variantId: string, newBudget: number) {
    // FIXED BY AGENT 90: Backend expects variant_id and new_budget, not winner
    return this.request`
    );

    content = content.replace(
      /method: ['"]POST['"]\s*,\s*body:\s*{\s*winner\s*}/,
      `method: 'POST',
      body: { variant_id: variantId, new_budget: newBudget }`
    );

    fs.writeFileSync(apiFilePath, content, 'utf-8');
    console.log('  ✓ Fixed promoteWinner schema');
    fixesApplied++;
  } else {
    console.log('  ⊘ Already fixed or pattern not found');
  }
} else {
  console.log('  ⊘ File not found');
}

// ============================================
// SUMMARY
// ============================================
console.log('\n' + '='.repeat(50));
console.log('API ROUTE FIXES SUMMARY');
console.log('='.repeat(50));
console.log(`Fixes applied: ${fixesApplied}`);
console.log(`Fixes requiring manual attention: ${fixesFailed}`);
console.log();

if (fixesApplied > 0) {
  console.log('✓ API route fixes have been applied!');
  console.log();
  console.log('NEXT STEPS:');
  console.log('1. Rebuild gateway-api: cd services/gateway-api && npm run build');
  console.log('2. Rebuild frontend: cd frontend && npm run build');
  console.log('3. Test endpoints with: curl -X POST http://localhost:8080/api/campaigns/:id/resume');
  console.log('4. Run: ./scripts/fixes/verify-fixes.sh');
}

process.exit(0);
