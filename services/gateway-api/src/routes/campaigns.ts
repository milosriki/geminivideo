/**
 * Campaigns API Routes
 * Handles campaign management, predictions, drafts, launches, and creative uploads
 */
import { Router, Request, Response } from 'express';
import { v4 as uuidv4 } from 'uuid';

const router = Router();

// ============================================================================
// TYPES
// ============================================================================

interface Campaign {
  id: string;
  name: string;
  status: 'draft' | 'active' | 'paused' | 'completed';
  budget: number;
  spend: number;
  revenue: number;
  roas: number;
  conversions: number;
  impressions: number;
  clicks: number;
  ctr: number;
  createdAt: string;
  updatedAt?: string;
  description?: string;
  targetAudience?: string;
  startDate?: string;
  endDate?: string;
}

interface CampaignCreateRequest {
  name: string;
  budget: number;
  description?: string;
  targetAudience?: string;
  startDate?: string;
  endDate?: string;
}

interface CampaignUpdateRequest {
  name?: string;
  status?: 'draft' | 'active' | 'paused' | 'completed';
  budget?: number;
  description?: string;
  targetAudience?: string;
  startDate?: string;
  endDate?: string;
}

interface PredictionRequest {
  campaignId?: string;
  budget?: number;
  targetAudience?: string;
  creativeCount?: number;
}

interface PredictionResponse {
  predictedRoas: number;
  predictedConversions: number;
  predictedImpressions: number;
  predictedClicks: number;
  predictedCtr: number;
  confidence: number;
  recommendations: string[];
}

interface DraftRequest {
  name: string;
  budget?: number;
  description?: string;
  targetAudience?: string;
}

interface LaunchRequest {
  campaignId: string;
  confirmedBudget: number;
}

interface Creative {
  id: string;
  campaignId?: string;
  filename: string;
  url: string;
  type: string;
  size: number;
  uploadedAt: string;
}

// ============================================================================
// IN-MEMORY STORAGE
// TODO: Replace with real database (PostgreSQL via Prisma)
// ============================================================================

const campaigns = new Map<string, Campaign>();
const creatives = new Map<string, Creative>();

// Initialize with some mock data
const mockCampaigns: Campaign[] = [
  {
    id: '1',
    name: 'Summer Sale 2024',
    status: 'active',
    budget: 50000,
    spend: 32450,
    revenue: 145800,
    roas: 4.49,
    conversions: 1284,
    impressions: 2450000,
    clicks: 48920,
    ctr: 2.0,
    createdAt: new Date('2024-06-01').toISOString(),
    updatedAt: new Date('2024-12-04').toISOString(),
    description: 'Summer promotional campaign for new product line',
    targetAudience: 'Ages 25-45, Fashion enthusiasts',
    startDate: '2024-06-01',
    endDate: '2024-08-31'
  },
  {
    id: '2',
    name: 'Black Friday Deals',
    status: 'completed',
    budget: 75000,
    spend: 74850,
    revenue: 298750,
    roas: 3.99,
    conversions: 2156,
    impressions: 3890000,
    clicks: 89320,
    ctr: 2.3,
    createdAt: new Date('2024-11-15').toISOString(),
    updatedAt: new Date('2024-12-01').toISOString(),
    description: 'Black Friday and Cyber Monday promotion',
    targetAudience: 'All segments, Deal seekers',
    startDate: '2024-11-20',
    endDate: '2024-11-30'
  },
  {
    id: '3',
    name: 'Holiday Gift Guide',
    status: 'active',
    budget: 60000,
    spend: 18920,
    revenue: 65450,
    roas: 3.46,
    conversions: 582,
    impressions: 1240000,
    clicks: 28450,
    ctr: 2.29,
    createdAt: new Date('2024-12-01').toISOString(),
    updatedAt: new Date('2024-12-04').toISOString(),
    description: 'Holiday season gift recommendations',
    targetAudience: 'Ages 30-55, Gift shoppers',
    startDate: '2024-12-01',
    endDate: '2024-12-24'
  },
  {
    id: '4',
    name: 'New Year Fitness',
    status: 'draft',
    budget: 45000,
    spend: 0,
    revenue: 0,
    roas: 0,
    conversions: 0,
    impressions: 0,
    clicks: 0,
    ctr: 0,
    createdAt: new Date('2024-12-03').toISOString(),
    description: 'New Year resolution fitness campaign',
    targetAudience: 'Ages 20-50, Health conscious',
    startDate: '2025-01-01',
    endDate: '2025-02-28'
  },
  {
    id: '5',
    name: 'Spring Collection Launch',
    status: 'paused',
    budget: 55000,
    spend: 12340,
    revenue: 38920,
    roas: 3.15,
    conversions: 298,
    impressions: 890000,
    clicks: 18450,
    ctr: 2.07,
    createdAt: new Date('2024-11-28').toISOString(),
    updatedAt: new Date('2024-12-02').toISOString(),
    description: 'Pre-launch campaign for spring fashion line',
    targetAudience: 'Ages 18-35, Fashion forward',
    startDate: '2025-02-15',
    endDate: '2025-04-30'
  }
];

// Load mock campaigns into storage
mockCampaigns.forEach(campaign => {
  campaigns.set(campaign.id, campaign);
});

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function generateMockMetrics(): Partial<Campaign> {
  const impressions = Math.floor(Math.random() * 1000000) + 500000;
  const clicks = Math.floor(impressions * (Math.random() * 0.03 + 0.015)); // CTR 1.5-4.5%
  const conversions = Math.floor(clicks * (Math.random() * 0.05 + 0.02)); // CVR 2-7%
  const spend = Math.floor(Math.random() * 30000) + 10000;
  const revenue = spend * (Math.random() * 2 + 2.5); // ROAS 2.5-4.5

  return {
    spend,
    revenue: Math.floor(revenue),
    roas: parseFloat((revenue / spend).toFixed(2)),
    conversions,
    impressions,
    clicks,
    ctr: parseFloat(((clicks / impressions) * 100).toFixed(2))
  };
}

function predictCampaignPerformance(params: PredictionRequest): PredictionResponse {
  const budget = params.budget || 50000;
  const creativeCount = params.creativeCount || 5;

  // Simple prediction model (TODO: Replace with ML model)
  const baseRoas = 3.2 + (Math.random() * 1.5);
  const roasBonus = (creativeCount / 10) * 0.3; // More creatives = better ROAS
  const predictedRoas = parseFloat((baseRoas + roasBonus).toFixed(2));

  const predictedRevenue = budget * predictedRoas;
  const predictedConversions = Math.floor(predictedRevenue / 120); // Avg order value $120
  const predictedImpressions = Math.floor(budget * 100); // $0.01 CPM estimate
  const predictedClicks = Math.floor(predictedImpressions * 0.025); // 2.5% CTR
  const predictedCtr = 2.5;

  const recommendations = [
    predictedRoas > 3.5 ? 'Strong expected performance - proceed with launch' : 'Consider increasing creative quality or refining targeting',
    creativeCount < 5 ? 'Add more creative variations to improve performance' : 'Good creative diversity',
    budget > 75000 ? 'Large budget detected - consider A/B testing' : 'Budget is optimal for testing',
    'Monitor performance closely in first 48 hours',
    'Set up automated rules for budget pacing'
  ];

  return {
    predictedRoas,
    predictedConversions,
    predictedImpressions,
    predictedClicks,
    predictedCtr,
    confidence: parseFloat((0.7 + Math.random() * 0.2).toFixed(2)), // 70-90% confidence
    recommendations: recommendations.filter((_, i) => i < 3) // Top 3 recommendations
  };
}

// ============================================================================
// ROUTES
// ============================================================================

/**
 * GET /api/campaigns
 * List all campaigns with optional filtering
 */
router.get('/api/campaigns', (req: Request, res: Response) => {
  try {
    const { status, limit, offset } = req.query;

    let campaignList = Array.from(campaigns.values());

    // Filter by status if provided
    if (status && typeof status === 'string') {
      campaignList = campaignList.filter(c => c.status === status);
    }

    // Sort by creation date (newest first)
    campaignList.sort((a, b) =>
      new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );

    // Pagination
    const offsetNum = parseInt(offset as string) || 0;
    const limitNum = parseInt(limit as string) || 100;
    const paginatedList = campaignList.slice(offsetNum, offsetNum + limitNum);

    res.json({
      campaigns: paginatedList,
      total: campaignList.length,
      limit: limitNum,
      offset: offsetNum
    });
  } catch (error) {
    console.error('Error fetching campaigns:', error);
    res.status(500).json({
      error: 'Failed to fetch campaigns',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * GET /api/campaigns/:id
 * Get a single campaign by ID
 */
router.get('/api/campaigns/:id', (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const campaign = campaigns.get(id);

    if (!campaign) {
      return res.status(404).json({
        error: 'Campaign not found',
        campaignId: id
      });
    }

    res.json(campaign);
  } catch (error) {
    console.error('Error fetching campaign:', error);
    res.status(500).json({
      error: 'Failed to fetch campaign',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/campaigns
 * Create a new campaign
 */
router.post('/api/campaigns', (req: Request, res: Response) => {
  try {
    const data: CampaignCreateRequest = req.body;

    // Validation
    if (!data.name || !data.budget) {
      return res.status(400).json({
        error: 'Missing required fields',
        required: ['name', 'budget']
      });
    }

    if (data.budget <= 0) {
      return res.status(400).json({
        error: 'Budget must be greater than 0'
      });
    }

    const newCampaign: Campaign = {
      id: uuidv4(),
      name: data.name,
      status: 'draft',
      budget: data.budget,
      spend: 0,
      revenue: 0,
      roas: 0,
      conversions: 0,
      impressions: 0,
      clicks: 0,
      ctr: 0,
      createdAt: new Date().toISOString(),
      description: data.description,
      targetAudience: data.targetAudience,
      startDate: data.startDate,
      endDate: data.endDate
    };

    campaigns.set(newCampaign.id, newCampaign);

    res.status(201).json(newCampaign);
  } catch (error) {
    console.error('Error creating campaign:', error);
    res.status(500).json({
      error: 'Failed to create campaign',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * PUT /api/campaigns/:id
 * Update an existing campaign
 */
router.put('/api/campaigns/:id', (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const updates: CampaignUpdateRequest = req.body;

    const campaign = campaigns.get(id);
    if (!campaign) {
      return res.status(404).json({
        error: 'Campaign not found',
        campaignId: id
      });
    }

    // Validation
    if (updates.budget !== undefined && updates.budget <= 0) {
      return res.status(400).json({
        error: 'Budget must be greater than 0'
      });
    }

    if (updates.status && !['draft', 'active', 'paused', 'completed'].includes(updates.status)) {
      return res.status(400).json({
        error: 'Invalid status',
        validStatuses: ['draft', 'active', 'paused', 'completed']
      });
    }

    // Update campaign
    const updatedCampaign: Campaign = {
      ...campaign,
      ...updates,
      updatedAt: new Date().toISOString()
    };

    campaigns.set(id, updatedCampaign);

    res.json(updatedCampaign);
  } catch (error) {
    console.error('Error updating campaign:', error);
    res.status(500).json({
      error: 'Failed to update campaign',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * DELETE /api/campaigns/:id
 * Delete a campaign
 */
router.delete('/api/campaigns/:id', (req: Request, res: Response) => {
  try {
    const { id } = req.params;

    const campaign = campaigns.get(id);
    if (!campaign) {
      return res.status(404).json({
        error: 'Campaign not found',
        campaignId: id
      });
    }

    // Prevent deletion of active campaigns
    if (campaign.status === 'active') {
      return res.status(400).json({
        error: 'Cannot delete active campaign',
        message: 'Pause or complete the campaign before deleting'
      });
    }

    campaigns.delete(id);

    res.json({
      success: true,
      message: 'Campaign deleted successfully',
      deletedCampaignId: id
    });
  } catch (error) {
    console.error('Error deleting campaign:', error);
    res.status(500).json({
      error: 'Failed to delete campaign',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/campaigns/predict
 * Predict campaign performance using ML models
 */
router.post('/api/campaigns/predict', (req: Request, res: Response) => {
  try {
    const params: PredictionRequest = req.body;

    // Validate input
    if (params.budget !== undefined && params.budget <= 0) {
      return res.status(400).json({
        error: 'Budget must be greater than 0'
      });
    }

    const prediction = predictCampaignPerformance(params);

    res.json({
      success: true,
      prediction,
      modelVersion: 'v1.0.0-mock',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error predicting campaign performance:', error);
    res.status(500).json({
      error: 'Failed to predict campaign performance',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/campaigns/draft
 * Save campaign as draft
 */
router.post('/api/campaigns/draft', (req: Request, res: Response) => {
  try {
    const data: DraftRequest = req.body;

    // Validation
    if (!data.name) {
      return res.status(400).json({
        error: 'Missing required field: name'
      });
    }

    const draftCampaign: Campaign = {
      id: uuidv4(),
      name: data.name,
      status: 'draft',
      budget: data.budget || 0,
      spend: 0,
      revenue: 0,
      roas: 0,
      conversions: 0,
      impressions: 0,
      clicks: 0,
      ctr: 0,
      createdAt: new Date().toISOString(),
      description: data.description,
      targetAudience: data.targetAudience
    };

    campaigns.set(draftCampaign.id, draftCampaign);

    res.status(201).json({
      success: true,
      message: 'Draft saved successfully',
      campaign: draftCampaign
    });
  } catch (error) {
    console.error('Error saving draft:', error);
    res.status(500).json({
      error: 'Failed to save draft',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/campaigns/launch
 * Launch a campaign (change status from draft to active)
 */
router.post('/api/campaigns/launch', (req: Request, res: Response) => {
  try {
    const data: LaunchRequest = req.body;

    // Validation
    if (!data.campaignId || !data.confirmedBudget) {
      return res.status(400).json({
        error: 'Missing required fields',
        required: ['campaignId', 'confirmedBudget']
      });
    }

    const campaign = campaigns.get(data.campaignId);
    if (!campaign) {
      return res.status(404).json({
        error: 'Campaign not found',
        campaignId: data.campaignId
      });
    }

    // Validate campaign state
    if (campaign.status !== 'draft') {
      return res.status(400).json({
        error: 'Only draft campaigns can be launched',
        currentStatus: campaign.status
      });
    }

    if (data.confirmedBudget <= 0) {
      return res.status(400).json({
        error: 'Confirmed budget must be greater than 0'
      });
    }

    // Launch campaign
    const launchedCampaign: Campaign = {
      ...campaign,
      status: 'active',
      budget: data.confirmedBudget,
      updatedAt: new Date().toISOString()
    };

    campaigns.set(data.campaignId, launchedCampaign);

    res.json({
      success: true,
      message: 'Campaign launched successfully',
      campaign: launchedCampaign,
      launchedAt: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error launching campaign:', error);
    res.status(500).json({
      error: 'Failed to launch campaign',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /api/creatives/upload
 * Upload creative assets for campaigns
 *
 * TODO: Install and configure multer for multipart/form-data handling
 * npm install multer @types/multer
 *
 * Example implementation:
 * import multer from 'multer';
 * const upload = multer({ dest: 'uploads/' });
 * router.post('/api/creatives/upload', upload.single('file'), ...)
 */
router.post('/api/creatives/upload', (req: Request, res: Response) => {
  try {
    // TODO: Implement actual file upload with multer
    // This is a mock implementation for now

    const { campaignId, filename, fileType } = req.body;

    if (!filename) {
      return res.status(400).json({
        error: 'Missing required field: filename'
      });
    }

    // Mock creative upload
    const creative: Creative = {
      id: uuidv4(),
      campaignId,
      filename,
      url: `https://storage.googleapis.com/creatives/${uuidv4()}/${filename}`,
      type: fileType || 'image/jpeg',
      size: Math.floor(Math.random() * 5000000) + 100000, // Mock size 100KB-5MB
      uploadedAt: new Date().toISOString()
    };

    creatives.set(creative.id, creative);

    res.status(201).json({
      success: true,
      message: 'Creative uploaded successfully (mock)',
      creative,
      note: 'This is a mock upload. Install multer for real multipart/form-data handling.'
    });
  } catch (error) {
    console.error('Error uploading creative:', error);
    res.status(500).json({
      error: 'Failed to upload creative',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// ============================================================================
// EXPORT
// ============================================================================

export default router;
