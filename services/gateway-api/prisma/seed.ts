/**
 * Database Seed Script
 * Populates the database with initial development/test data
 */

import { PrismaClient, UserRole, AssetStatus, ClipStatus, CampaignStatus, CampaignObjective } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Starting database seed...');

  // Clear existing data (development only!)
  if (process.env.NODE_ENV === 'development') {
    console.log('🧹 Clearing existing data...');
    await prisma.conversion.deleteMany();
    await prisma.prediction.deleteMany();
    await prisma.experiment.deleteMany();
    await prisma.campaign.deleteMany();
    await prisma.clip.deleteMany();
    await prisma.asset.deleteMany();
    await prisma.knowledgeDocument.deleteMany();
    await prisma.user.deleteMany();
  }

  // ============================================================================
  // Users
  // ============================================================================

  console.log('👤 Creating users...');

  const adminUser = await prisma.user.create({
    data: {
      email: 'admin@geminivideo.ai',
      name: 'Admin User',
      role: UserRole.ADMIN,
      apiKey: 'dev_admin_key_12345',
      settings: {
        notifications: true,
        theme: 'dark',
        language: 'en',
      },
    },
  });

  const demoUser = await prisma.user.create({
    data: {
      email: 'demo@geminivideo.ai',
      name: 'Demo User',
      role: UserRole.USER,
      apiKey: 'dev_demo_key_67890',
      settings: {
        notifications: true,
        theme: 'light',
        language: 'en',
      },
    },
  });

  const enterpriseUser = await prisma.user.create({
    data: {
      email: 'enterprise@geminivideo.ai',
      name: 'Enterprise User',
      role: UserRole.ENTERPRISE,
      apiKey: 'dev_enterprise_key_abcde',
      settings: {
        notifications: true,
        theme: 'dark',
        language: 'en',
        features: {
          advancedAnalytics: true,
          customBranding: true,
          prioritySupport: true,
        },
      },
    },
  });

  console.log(`✅ Created ${3} users`);

  // ============================================================================
  // Assets
  // ============================================================================

  console.log('📹 Creating assets...');

  const asset1 = await prisma.asset.create({
    data: {
      userId: demoUser.id,
      filename: 'demo-video-1.mp4',
      originalName: 'Product Launch Video.mp4',
      mimeType: 'video/mp4',
      fileSize: BigInt(52428800), // 50MB
      gcsUrl: 'gs://geminivideo-dev/assets/demo-video-1.mp4',
      gcsBucket: 'geminivideo-dev',
      gcsPath: 'assets/demo-video-1.mp4',
      thumbnailUrl: 'https://storage.googleapis.com/geminivideo-dev/thumbnails/demo-video-1.jpg',
      duration: 120.5,
      width: 1920,
      height: 1080,
      fps: 30,
      bitrate: 5000000,
      codec: 'h264',
      status: AssetStatus.READY,
      metadata: {
        uploadedFrom: 'web',
        originalFormat: 'mp4',
      },
    },
  });

  const asset2 = await prisma.asset.create({
    data: {
      userId: demoUser.id,
      filename: 'demo-video-2.mp4',
      originalName: 'Customer Testimonials.mp4',
      mimeType: 'video/mp4',
      fileSize: BigInt(73400320), // 70MB
      gcsUrl: 'gs://geminivideo-dev/assets/demo-video-2.mp4',
      gcsBucket: 'geminivideo-dev',
      gcsPath: 'assets/demo-video-2.mp4',
      thumbnailUrl: 'https://storage.googleapis.com/geminivideo-dev/thumbnails/demo-video-2.jpg',
      duration: 180.0,
      width: 1920,
      height: 1080,
      fps: 30,
      bitrate: 4000000,
      codec: 'h264',
      status: AssetStatus.READY,
      metadata: {
        uploadedFrom: 'api',
        originalFormat: 'mp4',
      },
    },
  });

  console.log(`✅ Created ${2} assets`);

  // ============================================================================
  // Clips
  // ============================================================================

  console.log('✂️ Creating clips...');

  const clips = [];

  // Clips for asset 1
  for (let i = 0; i < 5; i++) {
    const clip = await prisma.clip.create({
      data: {
        assetId: asset1.id,
        startTime: i * 20,
        endTime: (i * 20) + 15,
        duration: 15,
        clipUrl: `gs://geminivideo-dev/clips/${asset1.filename}-clip-${i}.mp4`,
        thumbnailUrl: `https://storage.googleapis.com/geminivideo-dev/thumbnails/${asset1.filename}-clip-${i}.jpg`,
        features: {
          hasLogo: i % 2 === 0,
          hasCall ToAction: i > 2,
          emotion: ['happy', 'excited', 'surprised'][i % 3],
          dominantColors: ['#FF0000', '#00FF00', '#0000FF'],
        },
        faceCount: Math.floor(Math.random() * 3),
        hasText: i > 1,
        hasSpeech: true,
        hasMusic: i % 2 === 0,
        score: 0.7 + (Math.random() * 0.3),
        viralScore: 0.6 + (Math.random() * 0.4),
        engagementScore: 0.75 + (Math.random() * 0.25),
        brandSafetyScore: 0.95 + (Math.random() * 0.05),
        rank: i + 1,
        status: ClipStatus.SCORED,
        metadata: {
          extracted: new Date().toISOString(),
        },
      },
    });
    clips.push(clip);
  }

  // Clips for asset 2
  for (let i = 0; i < 6; i++) {
    const clip = await prisma.clip.create({
      data: {
        assetId: asset2.id,
        startTime: i * 25,
        endTime: (i * 25) + 15,
        duration: 15,
        clipUrl: `gs://geminivideo-dev/clips/${asset2.filename}-clip-${i}.mp4`,
        thumbnailUrl: `https://storage.googleapis.com/geminivideo-dev/thumbnails/${asset2.filename}-clip-${i}.jpg`,
        features: {
          hasLogo: i % 3 === 0,
          hasCallToAction: i > 3,
          emotion: ['calm', 'happy', 'professional'][i % 3],
          dominantColors: ['#0066CC', '#FFFFFF', '#000000'],
        },
        faceCount: 1 + Math.floor(Math.random() * 2),
        hasText: i > 2,
        hasSpeech: true,
        hasMusic: false,
        score: 0.65 + (Math.random() * 0.35),
        viralScore: 0.5 + (Math.random() * 0.5),
        engagementScore: 0.7 + (Math.random() * 0.3),
        brandSafetyScore: 0.98,
        rank: i + 1,
        status: ClipStatus.SCORED,
        metadata: {
          extracted: new Date().toISOString(),
        },
      },
    });
    clips.push(clip);
  }

  console.log(`✅ Created ${clips.length} clips`);

  // ============================================================================
  // Predictions
  // ============================================================================

  console.log('🔮 Creating predictions...');

  let predictionCount = 0;
  for (const clip of clips.slice(0, 5)) {
    await prisma.prediction.create({
      data: {
        clipId: clip.id,
        modelVersion: 'v1.2.3',
        modelType: 'roas',
        predictedRoas: 2.5 + (Math.random() * 2.5),
        predictedCtr: 0.02 + (Math.random() * 0.03),
        predictedCpc: 0.5 + (Math.random() * 1.5),
        predictedCpa: 10 + (Math.random() * 20),
        predictedEngagement: 0.05 + (Math.random() * 0.1),
        confidence: 0.8 + (Math.random() * 0.2),
        features: {
          clipScore: clip.score,
          duration: clip.duration,
          faceCount: clip.faceCount,
          hasText: clip.hasText,
          hasSpeech: clip.hasSpeech,
        },
      },
    });
    predictionCount++;
  }

  console.log(`✅ Created ${predictionCount} predictions`);

  // ============================================================================
  // Campaigns
  // ============================================================================

  console.log('📢 Creating campaigns...');

  const campaign1 = await prisma.campaign.create({
    data: {
      userId: demoUser.id,
      name: 'Summer Product Launch',
      description: 'Q3 product launch campaign targeting young professionals',
      objective: CampaignObjective.CONVERSIONS,
      budget: 5000,
      dailyBudget: 200,
      currency: 'USD',
      status: CampaignStatus.ACTIVE,
      metaCampaignId: 'meta_camp_123456',
      metaAdSetId: 'meta_adset_789012',
      metaAccountId: 'act_345678',
      targetAudience: {
        age: [25, 45],
        gender: 'all',
        interests: ['technology', 'business', 'innovation'],
      },
      targetLocations: ['US', 'CA', 'UK', 'AU'],
      targetAgeRange: { min: 25, max: 45 },
      startDate: new Date('2025-06-01'),
      endDate: new Date('2025-08-31'),
      totalSpend: 1250.50,
      totalImpressions: BigInt(125000),
      totalClicks: BigInt(3500),
      totalConversions: BigInt(175),
      metadata: {
        platform: 'meta',
        createdBy: 'api',
      },
    },
  });

  const campaign2 = await prisma.campaign.create({
    data: {
      userId: enterpriseUser.id,
      name: 'Brand Awareness Campaign',
      description: 'Building brand awareness in new markets',
      objective: CampaignObjective.AWARENESS,
      budget: 10000,
      dailyBudget: 500,
      currency: 'USD',
      status: CampaignStatus.ACTIVE,
      metaCampaignId: 'meta_camp_234567',
      targetAudience: {
        age: [18, 65],
        gender: 'all',
        interests: ['lifestyle', 'entertainment'],
      },
      targetLocations: ['US', 'UK', 'DE', 'FR'],
      targetAgeRange: { min: 18, max: 65 },
      startDate: new Date('2025-07-01'),
      endDate: new Date('2025-09-30'),
      totalSpend: 2500.00,
      totalImpressions: BigInt(500000),
      totalClicks: BigInt(10000),
      totalConversions: BigInt(250),
      metadata: {
        platform: 'meta',
        createdBy: 'dashboard',
      },
    },
  });

  console.log(`✅ Created ${2} campaigns`);

  // ============================================================================
  // Experiments
  // ============================================================================

  console.log('🧪 Creating experiments...');

  const experiment1 = await prisma.experiment.create({
    data: {
      campaignId: campaign1.id,
      name: 'Headline A/B Test',
      description: 'Testing different headlines for engagement',
      status: 'RUNNING',
      variants: [
        {
          id: 'variant-a',
          name: 'Variant A - Direct',
          headline: 'Transform Your Business Today',
          impressions: 50000,
          clicks: 1500,
          conversions: 75,
        },
        {
          id: 'variant-b',
          name: 'Variant B - Question',
          headline: 'Ready to Transform Your Business?',
          impressions: 50000,
          clicks: 1750,
          conversions: 95,
        },
      ],
      metrics: {
        'variant-a': { ctr: 0.03, cvr: 0.05 },
        'variant-b': { ctr: 0.035, cvr: 0.054 },
      },
      confidence: 0.85,
      startDate: new Date('2025-06-01'),
    },
  });

  console.log(`✅ Created ${1} experiment`);

  // ============================================================================
  // Conversions
  // ============================================================================

  console.log('💰 Creating conversions...');

  const conversions = [];
  for (let i = 0; i < 10; i++) {
    const conversion = await prisma.conversion.create({
      data: {
        campaignId: i % 2 === 0 ? campaign1.id : campaign2.id,
        source: 'META',
        externalId: `meta_conv_${1000 + i}`,
        value: 50 + (Math.random() * 150),
        currency: 'USD',
        attributedClipId: clips[i % clips.length].id,
        timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000),
        metadata: {
          conversionType: 'purchase',
          source: 'facebook',
        },
      },
    });
    conversions.push(conversion);
  }

  console.log(`✅ Created ${conversions.length} conversions`);

  // ============================================================================
  // Knowledge Documents
  // ============================================================================

  console.log('📚 Creating knowledge documents...');

  const knowledgeDocs = [
    {
      name: 'Video Ad Best Practices',
      description: 'Best practices for creating engaging video ads',
      content: `
# Video Ad Best Practices

## Key Principles
1. Hook viewers in the first 3 seconds
2. Keep videos under 15 seconds for social media
3. Include clear call-to-action
4. Test multiple variants
5. Optimize for mobile viewing

## Performance Tips
- Use subtitles for accessibility
- Include brand logo early
- Focus on one key message
- Use high-quality visuals
- Test different aspect ratios
      `.trim(),
      category: 'best-practices',
      tags: ['video', 'ads', 'marketing'],
      source: 'internal',
      author: 'Marketing Team',
    },
    {
      name: 'Meta Ads Optimization Guide',
      description: 'Guide for optimizing Meta advertising campaigns',
      content: `
# Meta Ads Optimization Guide

## Campaign Structure
- Organize campaigns by objective
- Use campaign budget optimization
- Test different placements
- Leverage lookalike audiences

## Creative Strategy
- Use video ads for engagement
- Test multiple creative variants
- Refresh creative every 2-3 weeks
- Monitor creative fatigue

## Targeting
- Start broad, then narrow
- Use detailed targeting expansion
- Leverage Meta Pixel data
- Create custom audiences
      `.trim(),
      category: 'platform-guides',
      tags: ['meta', 'facebook', 'advertising'],
      source: 'internal',
      author: 'Ads Team',
    },
    {
      name: 'ROAS Calculation Methods',
      description: 'Different methods for calculating Return on Ad Spend',
      content: `
# ROAS Calculation Methods

## Basic ROAS
ROAS = Revenue / Ad Spend

## Blended ROAS
Includes all marketing channels

## Incremental ROAS
Measures additional revenue from ads

## Time-Window Attribution
- 1-day click
- 7-day click
- 28-day click/view

## Best Practices
- Use consistent attribution windows
- Account for customer lifetime value
- Consider cross-channel attribution
- Track both online and offline conversions
      `.trim(),
      category: 'analytics',
      tags: ['roas', 'analytics', 'metrics'],
      source: 'internal',
      author: 'Analytics Team',
    },
  ];

  for (const doc of knowledgeDocs) {
    // Generate a simple embedding (in production, use actual embedding model)
    const embedding = Array.from({ length: 1536 }, () => Math.random());

    await prisma.knowledgeDocument.create({
      data: {
        ...doc,
        embedding,
        embeddingModel: 'text-embedding-3-small',
        version: 1,
      },
    });
  }

  console.log(`✅ Created ${knowledgeDocs.length} knowledge documents`);

  // ============================================================================
  // Summary
  // ============================================================================

  console.log('\n✅ Database seeded successfully!');
  console.log('\n📊 Summary:');
  console.log(`   - Users: 3`);
  console.log(`   - Assets: 2`);
  console.log(`   - Clips: ${clips.length}`);
  console.log(`   - Predictions: ${predictionCount}`);
  console.log(`   - Campaigns: 2`);
  console.log(`   - Experiments: 1`);
  console.log(`   - Conversions: ${conversions.length}`);
  console.log(`   - Knowledge Documents: ${knowledgeDocs.length}`);
  console.log('\n🔑 API Keys for testing:');
  console.log(`   - Admin: dev_admin_key_12345`);
  console.log(`   - Demo: dev_demo_key_67890`);
  console.log(`   - Enterprise: dev_enterprise_key_abcde`);
}

main()
  .catch((error) => {
    console.error('❌ Seed failed:', error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
