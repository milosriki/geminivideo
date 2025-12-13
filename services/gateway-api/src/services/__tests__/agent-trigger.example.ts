/**
 * Agent Trigger Service - Usage Examples
 * Demonstrates how to use the AgentTrigger service to analyze winning ads
 */

import { agentTrigger, Winner, AgentAnalysis, BatchAnalysisResult } from '../agent-trigger';

/**
 * Example 1: Analyze a single winner ad
 */
async function analyzeSingleWinner() {
  const winner: Winner = {
    id: 'winner_123',
    adId: 'ad_456',
    campaignId: 'campaign_789',
    creative: {
      videoUrl: 'https://example.com/video.mp4',
      thumbnailUrl: 'https://example.com/thumb.jpg',
      headline: 'Transform Your Business in 30 Days',
      description: 'Learn the secrets of successful entrepreneurs',
      duration: 30,
      format: 'video',
    },
    performance: {
      roas: 4.5,
      ctr: 0.08,
      conversionRate: 0.12,
      impressions: 100000,
      clicks: 8000,
      conversions: 960,
      spend: 5000,
      revenue: 22500,
    },
    targeting: {
      demographics: { age: '25-45', gender: 'all' },
      interests: ['business', 'entrepreneurship', 'marketing'],
      locations: ['US', 'UK', 'CA'],
      platforms: ['facebook', 'instagram'],
    },
    copy: 'Ready to transform your business? Join 10,000+ entrepreneurs who increased their revenue by 300% in just 30 days. Click now!',
    timestamp: new Date().toISOString(),
  };

  try {
    console.log('🔍 Analyzing winner ad...');
    const analysis: AgentAnalysis = await agentTrigger.triggerAgentOnWinner(winner, 'deep');

    console.log('✅ Analysis completed!');
    console.log('Winning Factors:', analysis.winningFactors);
    console.log('Patterns Found:', analysis.patterns.length);
    console.log('New Concepts:', analysis.newConcepts.length);
    console.log('Confidence:', analysis.confidence);

    return analysis;
  } catch (error) {
    console.error('❌ Analysis failed:', error);
    throw error;
  }
}

/**
 * Example 2: Batch analyze multiple winners
 */
async function analyzeBatchWinners() {
  const winners: Winner[] = [
    {
      id: 'winner_001',
      adId: 'ad_001',
      creative: {
        videoUrl: 'https://example.com/video1.mp4',
        headline: 'Winner Ad 1',
      },
      performance: { roas: 5.2, ctr: 0.09, conversionRate: 0.15 },
      targeting: {},
      copy: 'Amazing product that delivers results!',
      timestamp: new Date().toISOString(),
    },
    {
      id: 'winner_002',
      adId: 'ad_002',
      creative: {
        videoUrl: 'https://example.com/video2.mp4',
        headline: 'Winner Ad 2',
      },
      performance: { roas: 4.8, ctr: 0.085, conversionRate: 0.13 },
      targeting: {},
      copy: 'Transform your life today!',
      timestamp: new Date().toISOString(),
    },
  ];

  try {
    console.log(`🔍 Analyzing ${winners.length} winners in batch...`);
    const result: BatchAnalysisResult = await agentTrigger.triggerBatchAnalysis(winners, 2);

    console.log('✅ Batch analysis completed!');
    console.log(`Total: ${result.total}`);
    console.log(`Successful: ${result.successful}`);
    console.log(`Failed: ${result.failed}`);
    console.log(`Duration: ${result.duration}ms`);

    // Access individual results
    result.results.forEach((analysis, winnerId) => {
      console.log(`\nWinner ${winnerId}:`);
      console.log(`  - Patterns: ${analysis.patterns.length}`);
      console.log(`  - Concepts: ${analysis.newConcepts.length}`);
    });

    return result;
  } catch (error) {
    console.error('❌ Batch analysis failed:', error);
    throw error;
  }
}

/**
 * Example 3: Retrieve historical analysis
 */
async function getHistoricalAnalysis(winnerId: string) {
  try {
    console.log(`📊 Retrieving analysis for winner ${winnerId}...`);
    const analysis = await agentTrigger.getAnalysis(winnerId);

    if (analysis) {
      console.log('✅ Analysis found!');
      console.log('Timestamp:', analysis.timestamp);
      console.log('Confidence:', analysis.confidence);
      return analysis;
    } else {
      console.log('⚠️ No analysis found for this winner');
      return null;
    }
  } catch (error) {
    console.error('❌ Failed to retrieve analysis:', error);
    throw error;
  }
}

/**
 * Example 4: Search for similar patterns
 */
async function findSimilarPatterns(patternDescription: string) {
  try {
    console.log(`🔎 Searching for patterns similar to: "${patternDescription}"...`);
    const patterns = await agentTrigger.searchSimilarPatterns(patternDescription, 5);

    console.log(`✅ Found ${patterns.length} similar patterns`);
    patterns.forEach((pattern, idx) => {
      console.log(`\n${idx + 1}. ${pattern.category}: ${pattern.pattern}`);
      console.log(`   Strength: ${pattern.strength}`);
      console.log(`   Applicability: ${pattern.applicability}`);
    });

    return patterns;
  } catch (error) {
    console.error('❌ Pattern search failed:', error);
    throw error;
  }
}

/**
 * Example 5: Health check
 */
async function checkServiceHealth() {
  try {
    console.log('🏥 Checking service health...');
    const health = await agentTrigger.healthCheck();

    console.log('✅ Health check completed');
    console.log('LangGraph:', health.langgraph ? '✅' : '❌');
    console.log('RAG:', health.rag ? '✅' : '❌');
    console.log('Database:', health.database ? '✅' : '❌');

    return health;
  } catch (error) {
    console.error('❌ Health check failed:', error);
    throw error;
  }
}

/**
 * Example 6: Process winner in a webhook/event handler
 */
async function processWinnerEvent(winnerData: any) {
  console.log('📥 Received winner event:', winnerData.id);

  try {
    // Trigger analysis
    const analysis = await agentTrigger.triggerAgentOnWinner(winnerData, 'standard');

    // Log insights
    console.log('🎯 Key winning factors:');
    analysis.winningFactors.forEach((factor, idx) => {
      console.log(`  ${idx + 1}. ${factor}`);
    });

    // Generate new concepts based on winner
    if (analysis.newConcepts.length > 0) {
      console.log('\n💡 Generated new ad concepts:');
      analysis.newConcepts.forEach((concept, idx) => {
        console.log(`  ${idx + 1}. ${concept.title}`);
        console.log(`     Hook: ${concept.hook}`);
        console.log(`     Estimated ROAS: ${concept.estimatedPerformance.roas}`);
      });
    }

    // Apply improvements
    if (analysis.improvements.length > 0) {
      console.log('\n🔧 Suggested improvements:');
      analysis.improvements.forEach((improvement, idx) => {
        console.log(`  ${idx + 1}. ${improvement}`);
      });
    }

    return analysis;
  } catch (error) {
    console.error('❌ Failed to process winner event:', error);
    // Handle error appropriately (retry, alert, etc.)
    throw error;
  }
}

// Export examples for testing
export {
  analyzeSingleWinner,
  analyzeBatchWinners,
  getHistoricalAnalysis,
  findSimilarPatterns,
  checkServiceHealth,
  processWinnerEvent,
};

/**
 * Main execution (for testing)
 */
if (require.main === module) {
  (async () => {
    console.log('🚀 Running Agent Trigger Examples...\n');

    // Run health check first
    await checkServiceHealth();

    // Then run other examples
    // Uncomment to test:
    // await analyzeSingleWinner();
    // await analyzeBatchWinners();
    // await getHistoricalAnalysis('winner_123');
    // await findSimilarPatterns('emotional hook with urgency');
  })();
}
