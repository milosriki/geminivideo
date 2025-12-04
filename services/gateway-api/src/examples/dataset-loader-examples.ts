/**
 * Dataset Loaders Usage Examples
 *
 * This file demonstrates how to use KaggleLoader and HuggingFaceLoader
 * to import ad patterns from offline and free data sources.
 */

import { kaggleLoader, huggingfaceLoader } from '../services/dataset-loaders';
import { adIntelligence } from '../services/ad-intelligence';

/**
 * Example 1: Load ad patterns from Kaggle datasets (100% OFFLINE)
 */
async function example1_LoadKaggleDatasets() {
  console.log('Example 1: Loading Kaggle datasets...\n');

  // Check available datasets
  const datasets = kaggleLoader.getAvailableDatasets();
  console.log(`Available datasets: ${datasets.length}`);
  datasets.forEach(ds => console.log(`  - ${ds}`));

  if (datasets.length === 0) {
    console.log('\n⚠️  No datasets found!');
    console.log('Run: ./scripts/download_datasets.sh');
    return;
  }

  // Load advertising.csv
  try {
    console.log('\nLoading advertising.csv...');
    const patterns = await kaggleLoader.loadAdDataset('advertising.csv');
    console.log(`✓ Loaded ${patterns.length} ad patterns`);

    // Show sample pattern
    console.log('\nSample pattern:');
    console.log(JSON.stringify(patterns[0], null, 2));

    // Get dataset stats
    const stats = await kaggleLoader.getDatasetStats('advertising.csv');
    console.log('\nDataset stats:');
    console.log(`  Total rows: ${stats.total_rows}`);
    console.log(`  File size: ${(stats.file_size / 1024).toFixed(2)} KB`);
    console.log(`  Last modified: ${stats.last_modified}`);

  } catch (error: any) {
    console.error('Error:', error.message);
  }
}

/**
 * Example 2: Generate ad variants with HuggingFace AI
 */
async function example2_GenerateHuggingFaceAds() {
  console.log('\nExample 2: Generating ads with HuggingFace...\n');

  if (!huggingfaceLoader.isConfigured()) {
    console.log('⚠️  HuggingFace not configured');
    console.log('Set HUGGINGFACE_API_TOKEN environment variable');
    console.log('Get free token at: https://huggingface.co/settings/tokens');
    return;
  }

  try {
    // Generate 3 ad variants
    const prompt = 'fitness tracker that monitors heart rate and sleep quality';
    console.log(`Prompt: "${prompt}"\n`);

    const variants = await huggingfaceLoader.generateAdVariants(prompt, 3);

    console.log(`✓ Generated ${variants.length} ad variants:\n`);
    variants.forEach((variant, i) => {
      console.log(`Variant ${i + 1}:`);
      console.log(variant);
      console.log('---');
    });

    // Analyze sentiment of first variant
    if (variants.length > 0) {
      console.log('\nAnalyzing first variant...');
      const analysis = await huggingfaceLoader.analyzeAdText(variants[0]);
      console.log('Analysis:');
      console.log(`  Sentiment: ${analysis.sentiment}`);
      console.log(`  Confidence: ${(analysis.confidence * 100).toFixed(1)}%`);
      console.log(`  Emotions: ${analysis.emotions.join(', ')}`);
    }

  } catch (error: any) {
    console.error('Error:', error.message);
  }
}

/**
 * Example 3: Import Kaggle patterns into knowledge base
 */
async function example3_ImportToKnowledgeBase() {
  console.log('\nExample 3: Importing patterns to knowledge base...\n');

  try {
    // Load patterns from Facebook ad campaign dataset
    const patterns = await kaggleLoader.loadAdDataset('facebook_ad_campaign.csv');
    console.log(`Loaded ${patterns.length} patterns from Facebook dataset`);

    // Filter for high-performers only
    const topPerformers = patterns.filter(
      p => p.performance_tier === 'top_1_percent' || p.performance_tier === 'top_10_percent'
    );
    console.log(`Found ${topPerformers.length} top-performing ads`);

    // Inject into knowledge base
    const result = await adIntelligence.injectToKnowledgeBase(topPerformers);
    console.log(`✓ Injected ${result.injected} patterns to ${result.file_path}`);

    // Extract winning patterns
    console.log('\nExtracting winning patterns...');
    const winning = await adIntelligence.extractWinningPatterns();

    console.log('\nTop hooks:');
    winning.hooks.slice(0, 5).forEach(h => {
      console.log(`  ${h.type}: ${h.count} occurrences`);
    });

    console.log('\nTop emotions:');
    winning.emotions.slice(0, 5).forEach(e => {
      console.log(`  ${e.trigger}: ${e.frequency} occurrences`);
    });

  } catch (error: any) {
    console.error('Error:', error.message);
  }
}

/**
 * Example 4: Search across all data sources (including Kaggle & HuggingFace)
 */
async function example4_SearchAllSources() {
  console.log('\nExample 4: Searching across all data sources...\n');

  try {
    // Check status of all sources
    const status = adIntelligence.getStatus();
    console.log('Data source status:');
    Object.entries(status).forEach(([source, info]) => {
      const icon = info.configured ? '✓' : '✗';
      console.log(`  ${icon} ${source}: ${info.note}`);
    });

    // Search for fitness ads across all sources
    console.log('\nSearching for "fitness" ads...');
    const result = await adIntelligence.searchAll({
      query: 'fitness',
      industry: 'fitness',
      limit: 20
    });

    console.log(`\n✓ Found ${result.patterns.length} total patterns`);
    console.log('\nSource breakdown:');
    Object.entries(result.source_counts).forEach(([source, count]) => {
      console.log(`  ${source}: ${count} patterns`);
    });

    if (result.errors.length > 0) {
      console.log('\nErrors encountered:');
      result.errors.forEach(err => console.log(`  - ${err}`));
    }

  } catch (error: any) {
    console.error('Error:', error.message);
  }
}

/**
 * Example 5: Use API endpoints directly
 */
function example5_APIUsage() {
  console.log('\nExample 5: API Endpoint Usage\n');

  console.log('Check dataset status:');
  console.log('  GET /api/datasets/status\n');

  console.log('Import Kaggle dataset:');
  console.log('  POST /api/datasets/import');
  console.log('  Body: {');
  console.log('    "source": "kaggle",');
  console.log('    "dataset": "facebook_ad_campaign.csv",');
  console.log('    "industry": "fitness",');
  console.log('    "limit": 100');
  console.log('  }\n');

  console.log('Generate HuggingFace variants:');
  console.log('  POST /api/datasets/generate-variants');
  console.log('  Body: {');
  console.log('    "prompt": "fitness app for busy professionals",');
  console.log('    "count": 5,');
  console.log('    "analyze": true');
  console.log('  }\n');

  console.log('Check intelligence status (includes Kaggle & HF):');
  console.log('  GET /api/intelligence/status\n');
}

// Run examples
async function runAllExamples() {
  console.log('═══════════════════════════════════════════════════════');
  console.log('  Dataset Loaders Usage Examples');
  console.log('═══════════════════════════════════════════════════════\n');

  await example1_LoadKaggleDatasets();
  await example2_GenerateHuggingFaceAds();
  await example3_ImportToKnowledgeBase();
  await example4_SearchAllSources();
  example5_APIUsage();

  console.log('\n═══════════════════════════════════════════════════════');
  console.log('  Examples Complete!');
  console.log('═══════════════════════════════════════════════════════\n');
}

// Export for use in other modules
export {
  example1_LoadKaggleDatasets,
  example2_GenerateHuggingFaceAds,
  example3_ImportToKnowledgeBase,
  example4_SearchAllSources,
  example5_APIUsage
};

// Run if executed directly
if (require.main === module) {
  runAllExamples().catch(console.error);
}
