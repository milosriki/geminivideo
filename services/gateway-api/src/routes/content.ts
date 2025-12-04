/**
 * Content Routes - Avatars, Trending Ads, and AI Insights
 * Provides frontend with avatar library, competitor analysis, and AI recommendations
 */
import { Router, Request, Response } from 'express';

const router = Router();

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface Avatar {
  key: string;
  name: string;
  description: string;
  image_url: string;
  voice_style: string;
  best_for: string[];
}

interface TrendingAd {
  id: string;
  brand: string;
  title: string;
  views: string;
  engagement: string;
  platform: 'instagram' | 'tiktok' | 'youtube' | 'facebook';
  thumbnail_url: string;
  hook_type: string;
}

interface TopPerformer {
  id: string;
  title: string;
  brand: string;
  ctr: number;
  roas: number;
  spend: string;
  revenue: string;
  platform: 'instagram' | 'tiktok' | 'youtube' | 'facebook';
  thumbnail_url: string;
  duration: number;
  created_date: string;
}

interface AIInsight {
  id: string;
  category: 'hook' | 'pacing' | 'audience' | 'creative' | 'optimization';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  recommendation: string;
  confidence: number;
  data_points: number;
}

// ============================================================================
// MOCK DATA
// ============================================================================

const AVATARS: Avatar[] = [
  {
    key: 'sophia_professional',
    name: 'Sophia',
    description: 'Professional business presenter with warm, confident delivery',
    image_url: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&h=400&fit=crop',
    voice_style: 'Professional, warm, confident',
    best_for: ['B2B', 'SaaS', 'Professional Services', 'Finance']
  },
  {
    key: 'marcus_energetic',
    name: 'Marcus',
    description: 'High-energy fitness coach with motivational delivery',
    image_url: 'https://images.unsplash.com/photo-1566492031773-4f4e44671857?w=400&h=400&fit=crop',
    voice_style: 'Energetic, motivational, upbeat',
    best_for: ['Fitness', 'Wellness', 'Sports', 'Lifestyle']
  },
  {
    key: 'emma_friendly',
    name: 'Emma',
    description: 'Friendly lifestyle influencer with conversational tone',
    image_url: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400&h=400&fit=crop',
    voice_style: 'Friendly, conversational, relatable',
    best_for: ['E-commerce', 'Beauty', 'Fashion', 'Lifestyle']
  },
  {
    key: 'david_authoritative',
    name: 'David',
    description: 'Authoritative expert with educational delivery style',
    image_url: 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=400&h=400&fit=crop',
    voice_style: 'Authoritative, educational, trustworthy',
    best_for: ['Education', 'Healthcare', 'Legal', 'Consulting']
  },
  {
    key: 'aria_creative',
    name: 'Aria',
    description: 'Creative storyteller with engaging, artistic delivery',
    image_url: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&h=400&fit=crop',
    voice_style: 'Creative, engaging, artistic',
    best_for: ['Art', 'Design', 'Entertainment', 'Media']
  },
  {
    key: 'james_tech',
    name: 'James',
    description: 'Tech-savvy presenter with clear, concise explanations',
    image_url: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop',
    voice_style: 'Clear, concise, tech-savvy',
    best_for: ['Technology', 'Software', 'Startups', 'Innovation']
  },
  {
    key: 'nina_luxury',
    name: 'Nina',
    description: 'Elegant luxury brand ambassador with sophisticated tone',
    image_url: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400&h=400&fit=crop',
    voice_style: 'Sophisticated, elegant, refined',
    best_for: ['Luxury', 'Premium', 'Real Estate', 'High-end Fashion']
  },
  {
    key: 'tyler_casual',
    name: 'Tyler',
    description: 'Casual, down-to-earth presenter perfect for everyday products',
    image_url: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&h=400&fit=crop',
    voice_style: 'Casual, down-to-earth, approachable',
    best_for: ['Consumer Goods', 'Food & Beverage', 'Travel', 'Gaming']
  }
];

const TRENDING_ADS: TrendingAd[] = [
  {
    id: 'trend_001',
    brand: 'Gymshark',
    title: 'Summer Shred Challenge - 30 Days',
    views: '2.4M',
    engagement: '18.5%',
    platform: 'tiktok',
    thumbnail_url: 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=600&fit=crop',
    hook_type: 'Transformation Story'
  },
  {
    id: 'trend_002',
    brand: 'Shopify',
    title: 'From Side Hustle to $100K/Month',
    views: '1.8M',
    engagement: '15.2%',
    platform: 'instagram',
    thumbnail_url: 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=400&h=600&fit=crop',
    hook_type: 'Success Story'
  },
  {
    id: 'trend_003',
    brand: 'HelloFresh',
    title: '5-Minute Gourmet Meals At Home',
    views: '3.1M',
    engagement: '22.3%',
    platform: 'youtube',
    thumbnail_url: 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=600&fit=crop',
    hook_type: 'Problem-Solution'
  },
  {
    id: 'trend_004',
    brand: 'Duolingo',
    title: 'Speak Spanish in 30 Days (Without Classes)',
    views: '4.2M',
    engagement: '25.7%',
    platform: 'tiktok',
    thumbnail_url: 'https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=400&h=600&fit=crop',
    hook_type: 'Bold Promise'
  },
  {
    id: 'trend_005',
    brand: 'Glossier',
    title: 'No-Makeup Makeup in Under 2 Minutes',
    views: '2.9M',
    engagement: '20.1%',
    platform: 'instagram',
    thumbnail_url: 'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=400&h=600&fit=crop',
    hook_type: 'Time-Saving Hack'
  },
  {
    id: 'trend_006',
    brand: 'Peloton',
    title: 'Transform Your Home Into a Gym',
    views: '1.6M',
    engagement: '14.8%',
    platform: 'facebook',
    thumbnail_url: 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400&h=600&fit=crop',
    hook_type: 'Lifestyle Upgrade'
  },
  {
    id: 'trend_007',
    brand: 'Warby Parker',
    title: 'Designer Glasses for $95 (Try 5 Free)',
    views: '2.2M',
    engagement: '17.9%',
    platform: 'youtube',
    thumbnail_url: 'https://images.unsplash.com/photo-1574258495973-f010dfbb5371?w=400&h=600&fit=crop',
    hook_type: 'Value Proposition'
  },
  {
    id: 'trend_008',
    brand: 'Calm',
    title: 'Fall Asleep in 60 Seconds (Science-Backed)',
    views: '5.3M',
    engagement: '28.4%',
    platform: 'tiktok',
    thumbnail_url: 'https://images.unsplash.com/photo-1511988617509-a57c8a288659?w=400&h=600&fit=crop',
    hook_type: 'Curiosity Gap'
  },
  {
    id: 'trend_009',
    brand: 'Dollar Shave Club',
    title: 'Why Are Razors So Expensive? (We Fixed It)',
    views: '1.9M',
    engagement: '16.3%',
    platform: 'facebook',
    thumbnail_url: 'https://images.unsplash.com/photo-1493106641515-6b5631de4bb9?w=400&h=600&fit=crop',
    hook_type: 'Question Hook'
  },
  {
    id: 'trend_010',
    brand: 'Notion',
    title: 'One App to Replace Them All',
    views: '3.7M',
    engagement: '23.5%',
    platform: 'youtube',
    thumbnail_url: 'https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?w=400&h=600&fit=crop',
    hook_type: 'Simplification'
  }
];

const TOP_PERFORMERS: TopPerformer[] = [
  {
    id: 'perf_001',
    title: 'Lose 10 Pounds in 30 Days - Here\'s How',
    brand: 'Noom',
    ctr: 8.7,
    roas: 4.2,
    spend: '$12,400',
    revenue: '$52,080',
    platform: 'facebook',
    thumbnail_url: 'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=400&h=600&fit=crop',
    duration: 15,
    created_date: '2024-11-15'
  },
  {
    id: 'perf_002',
    title: 'This Skincare Routine Changed My Life',
    brand: 'The Ordinary',
    ctr: 9.2,
    roas: 5.8,
    spend: '$8,200',
    revenue: '$47,560',
    platform: 'instagram',
    thumbnail_url: 'https://images.unsplash.com/photo-1556228720-195a672e8a03?w=400&h=600&fit=crop',
    duration: 12,
    created_date: '2024-11-18'
  },
  {
    id: 'perf_003',
    title: 'I Quit My Job to Build This App',
    brand: 'Indie Maker',
    ctr: 7.3,
    roas: 6.5,
    spend: '$5,600',
    revenue: '$36,400',
    platform: 'tiktok',
    thumbnail_url: 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=400&h=600&fit=crop',
    duration: 20,
    created_date: '2024-11-20'
  },
  {
    id: 'perf_004',
    title: 'Cook Restaurant-Quality Meals at Home',
    brand: 'MasterClass',
    ctr: 6.8,
    roas: 3.9,
    spend: '$15,300',
    revenue: '$59,670',
    platform: 'youtube',
    thumbnail_url: 'https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=400&h=600&fit=crop',
    duration: 30,
    created_date: '2024-11-12'
  },
  {
    id: 'perf_005',
    title: 'Learn to Code in 6 Months (No Degree)',
    brand: 'Codecademy',
    ctr: 8.1,
    roas: 4.7,
    spend: '$9,800',
    revenue: '$46,060',
    platform: 'facebook',
    thumbnail_url: 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=400&h=600&fit=crop',
    duration: 25,
    created_date: '2024-11-10'
  },
  {
    id: 'perf_006',
    title: 'Morning Routine of Successful People',
    brand: 'Headspace',
    ctr: 7.9,
    roas: 5.2,
    spend: '$7,100',
    revenue: '$36,920',
    platform: 'instagram',
    thumbnail_url: 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=400&h=600&fit=crop',
    duration: 18,
    created_date: '2024-11-22'
  },
  {
    id: 'perf_007',
    title: 'Budget Travel Hacks That Actually Work',
    brand: 'Skyscanner',
    ctr: 6.5,
    roas: 3.4,
    spend: '$11,200',
    revenue: '$38,080',
    platform: 'tiktok',
    thumbnail_url: 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=400&h=600&fit=crop',
    duration: 22,
    created_date: '2024-11-08'
  },
  {
    id: 'perf_008',
    title: 'Invest Like the Top 1% (Beginner Guide)',
    brand: 'Robinhood',
    ctr: 8.9,
    roas: 7.1,
    spend: '$14,500',
    revenue: '$102,950',
    platform: 'youtube',
    thumbnail_url: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400&h=600&fit=crop',
    duration: 35,
    created_date: '2024-11-05'
  }
];

const AI_INSIGHTS: AIInsight[] = [
  {
    id: 'insight_001',
    category: 'hook',
    title: 'Problem-First Hooks Outperform by 45%',
    description: 'Ads that start with a relatable problem in the first 3 seconds have 45% higher engagement than benefit-first hooks.',
    impact: 'high',
    recommendation: 'Lead with "Tired of X?" or "Struggling with Y?" before presenting your solution. Test problem-focused hooks in your next 3 ad variants.',
    confidence: 92,
    data_points: 1247
  },
  {
    id: 'insight_002',
    category: 'pacing',
    title: 'Optimal Video Length: 15-20 Seconds',
    description: 'Videos between 15-20 seconds achieve the best balance of completion rate (78%) and conversion rate (6.2%).',
    impact: 'high',
    recommendation: 'Trim videos longer than 25 seconds. Focus on one core message. Use text overlays to accelerate information delivery.',
    confidence: 88,
    data_points: 3456
  },
  {
    id: 'insight_003',
    category: 'audience',
    title: 'Female 25-34 Segment Shows 3.2x ROAS',
    description: 'Your highest-performing audience segment is females aged 25-34 with interests in wellness and productivity.',
    impact: 'high',
    recommendation: 'Allocate 40% more budget to this segment. Create lookalike audiences. Use wellness-focused messaging and female presenters.',
    confidence: 95,
    data_points: 892
  },
  {
    id: 'insight_004',
    category: 'creative',
    title: 'Face-to-Camera Shots Increase Trust by 34%',
    description: 'Ads featuring direct face-to-camera shots in the first 5 seconds show 34% higher click-through rates.',
    impact: 'medium',
    recommendation: 'Start videos with a talking head or presenter looking directly at camera. Avoid B-roll openings. Test avatar-based videos.',
    confidence: 85,
    data_points: 2134
  },
  {
    id: 'insight_005',
    category: 'optimization',
    title: 'Peak Performance Hours: 7-9 PM',
    description: 'Your ads perform 52% better when shown between 7-9 PM in the user\'s timezone.',
    impact: 'medium',
    recommendation: 'Use dayparting to concentrate 60% of daily budget in evening hours. Test weekend morning slots (9-11 AM) as secondary peak.',
    confidence: 90,
    data_points: 4521
  },
  {
    id: 'insight_006',
    category: 'hook',
    title: 'Numbers in Hooks Drive 28% More Clicks',
    description: 'Hooks containing specific numbers ("30 days", "$100K", "5 minutes") outperform vague claims significantly.',
    impact: 'medium',
    recommendation: 'Replace vague claims with specific numbers. Use timeframes, dollar amounts, or percentages. Test "$X in Y days" format.',
    confidence: 87,
    data_points: 1876
  },
  {
    id: 'insight_007',
    category: 'creative',
    title: 'Caption Overlays Boost Completion by 41%',
    description: 'Videos with on-screen captions show 41% higher completion rates, especially on mobile with sound off.',
    impact: 'high',
    recommendation: 'Add captions to all video ads. Use large, bold fonts. Highlight key words in different colors. Consider emoji accents.',
    confidence: 93,
    data_points: 5234
  },
  {
    id: 'insight_008',
    category: 'audience',
    title: 'Lookalike Audiences at 1% Perform Best',
    description: 'Your 1% lookalike audiences show 2.8x ROAS compared to 5% lookalikes or interest-based targeting.',
    impact: 'high',
    recommendation: 'Focus budget on 1% lookalikes from purchasers list. Avoid broad 5-10% lookalikes. Refresh seed audience monthly.',
    confidence: 91,
    data_points: 678
  },
  {
    id: 'insight_009',
    category: 'pacing',
    title: 'Scene Changes Every 3-4 Seconds Optimal',
    description: 'Videos with scene changes every 3-4 seconds maintain attention 2.3x better than static shots.',
    impact: 'medium',
    recommendation: 'Edit videos with rapid cuts. Mix close-ups, wide shots, and product shots. Use transitions to maintain visual interest.',
    confidence: 84,
    data_points: 2987
  },
  {
    id: 'insight_010',
    category: 'optimization',
    title: 'Retargeting at 7-Day Window Converts Best',
    description: 'Retargeting users who engaged 7 days ago shows 58% higher conversion than immediate retargeting.',
    impact: 'medium',
    recommendation: 'Set retargeting campaigns to 7-14 day window. Use different creative for retargeting. Offer time-limited discounts.',
    confidence: 89,
    data_points: 1543
  }
];

// ============================================================================
// ENDPOINTS
// ============================================================================

/**
 * GET /avatars
 * List available AI avatars for video generation
 * Returns array of avatar profiles with images, voice styles, and best use cases
 */
router.get('/avatars', (req: Request, res: Response) => {
  try {
    const { category, voice_style } = req.query;

    let filteredAvatars = [...AVATARS];

    // Filter by category if provided
    if (category && typeof category === 'string') {
      filteredAvatars = filteredAvatars.filter(avatar =>
        avatar.best_for.some(useCase =>
          useCase.toLowerCase().includes(category.toLowerCase())
        )
      );
    }

    // Filter by voice style if provided
    if (voice_style && typeof voice_style === 'string') {
      filteredAvatars = filteredAvatars.filter(avatar =>
        avatar.voice_style.toLowerCase().includes(voice_style.toLowerCase())
      );
    }

    res.json({
      count: filteredAvatars.length,
      avatars: filteredAvatars
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/ads/trending
 * Get trending competitor ads from major platforms
 * Returns ads with high engagement and view counts for competitive analysis
 */
router.get('/api/ads/trending', (req: Request, res: Response) => {
  try {
    const { platform, limit } = req.query;

    let filteredAds = [...TRENDING_ADS];

    // Filter by platform if provided
    if (platform && typeof platform === 'string') {
      filteredAds = filteredAds.filter(ad =>
        ad.platform.toLowerCase() === platform.toLowerCase()
      );
    }

    // Apply limit if provided
    if (limit && typeof limit === 'string') {
      const limitNum = parseInt(limit, 10);
      if (!isNaN(limitNum) && limitNum > 0) {
        filteredAds = filteredAds.slice(0, limitNum);
      }
    }

    // Sort by engagement (parse percentage and sort)
    filteredAds.sort((a, b) => {
      const engagementA = parseFloat(a.engagement.replace('%', ''));
      const engagementB = parseFloat(b.engagement.replace('%', ''));
      return engagementB - engagementA;
    });

    res.json({
      count: filteredAds.length,
      trending_ads: filteredAds,
      platforms: ['instagram', 'tiktok', 'youtube', 'facebook'],
      updated_at: new Date().toISOString()
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/top-performers
 * Get top performing ads based on CTR and ROAS metrics
 * Returns ads with best performance metrics for learning and optimization
 */
router.get('/api/top-performers', (req: Request, res: Response) => {
  try {
    const { platform, min_roas, sort_by, limit } = req.query;

    let filteredPerformers = [...TOP_PERFORMERS];

    // Filter by platform if provided
    if (platform && typeof platform === 'string') {
      filteredPerformers = filteredPerformers.filter(ad =>
        ad.platform.toLowerCase() === platform.toLowerCase()
      );
    }

    // Filter by minimum ROAS if provided
    if (min_roas && typeof min_roas === 'string') {
      const minRoasNum = parseFloat(min_roas);
      if (!isNaN(minRoasNum)) {
        filteredPerformers = filteredPerformers.filter(ad =>
          ad.roas >= minRoasNum
        );
      }
    }

    // Sort by specified metric
    const sortMetric = (sort_by as string) || 'roas';
    if (sortMetric === 'roas') {
      filteredPerformers.sort((a, b) => b.roas - a.roas);
    } else if (sortMetric === 'ctr') {
      filteredPerformers.sort((a, b) => b.ctr - a.ctr);
    } else if (sortMetric === 'revenue') {
      filteredPerformers.sort((a, b) => {
        const revenueA = parseFloat(a.revenue.replace(/[$,]/g, ''));
        const revenueB = parseFloat(b.revenue.replace(/[$,]/g, ''));
        return revenueB - revenueA;
      });
    }

    // Apply limit if provided
    if (limit && typeof limit === 'string') {
      const limitNum = parseInt(limit, 10);
      if (!isNaN(limitNum) && limitNum > 0) {
        filteredPerformers = filteredPerformers.slice(0, limitNum);
      }
    }

    // Calculate aggregate metrics
    const avgCtr = filteredPerformers.reduce((sum, ad) => sum + ad.ctr, 0) / filteredPerformers.length;
    const avgRoas = filteredPerformers.reduce((sum, ad) => sum + ad.roas, 0) / filteredPerformers.length;

    res.json({
      count: filteredPerformers.length,
      top_performers: filteredPerformers,
      metrics: {
        avg_ctr: parseFloat(avgCtr.toFixed(2)),
        avg_roas: parseFloat(avgRoas.toFixed(2))
      },
      updated_at: new Date().toISOString()
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/insights/ai
 * Get AI-generated insights and recommendations
 * Returns actionable insights based on performance data analysis
 */
router.get('/api/insights/ai', (req: Request, res: Response) => {
  try {
    const { category, impact, min_confidence, limit } = req.query;

    let filteredInsights = [...AI_INSIGHTS];

    // Filter by category if provided
    if (category && typeof category === 'string') {
      filteredInsights = filteredInsights.filter(insight =>
        insight.category.toLowerCase() === category.toLowerCase()
      );
    }

    // Filter by impact level if provided
    if (impact && typeof impact === 'string') {
      filteredInsights = filteredInsights.filter(insight =>
        insight.impact.toLowerCase() === impact.toLowerCase()
      );
    }

    // Filter by minimum confidence if provided
    if (min_confidence && typeof min_confidence === 'string') {
      const minConfNum = parseFloat(min_confidence);
      if (!isNaN(minConfNum)) {
        filteredInsights = filteredInsights.filter(insight =>
          insight.confidence >= minConfNum
        );
      }
    }

    // Sort by impact (high > medium > low) and then by confidence
    const impactWeight = { high: 3, medium: 2, low: 1 };
    filteredInsights.sort((a, b) => {
      const impactDiff = impactWeight[b.impact] - impactWeight[a.impact];
      if (impactDiff !== 0) return impactDiff;
      return b.confidence - a.confidence;
    });

    // Apply limit if provided
    if (limit && typeof limit === 'string') {
      const limitNum = parseInt(limit, 10);
      if (!isNaN(limitNum) && limitNum > 0) {
        filteredInsights = filteredInsights.slice(0, limitNum);
      }
    }

    // Calculate aggregate stats
    const avgConfidence = filteredInsights.reduce((sum, insight) => sum + insight.confidence, 0) / filteredInsights.length;
    const totalDataPoints = filteredInsights.reduce((sum, insight) => sum + insight.data_points, 0);

    res.json({
      count: filteredInsights.length,
      insights: filteredInsights,
      categories: ['hook', 'pacing', 'audience', 'creative', 'optimization'],
      stats: {
        avg_confidence: parseFloat(avgConfidence.toFixed(1)),
        total_data_points: totalDataPoints,
        high_impact_count: filteredInsights.filter(i => i.impact === 'high').length
      },
      generated_at: new Date().toISOString()
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
