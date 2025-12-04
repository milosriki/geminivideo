/**
 * Dataset Loaders - Offline data sources
 *
 * Provides FREE, offline alternatives to paid APIs:
 * 1. KaggleLoader - Load ad datasets from Kaggle CSV/JSON files
 * 2. HuggingFaceLoader - Use HuggingFace models for ad generation & analysis
 *
 * ZERO COST - All data sources are free
 */

import * as fs from 'fs';
import * as path from 'path';
import * as csv from 'csv-parser';
import axios from 'axios';

// Types matching ad-intelligence.ts
interface AdPattern {
  source: 'kaggle' | 'huggingface';
  hook_type: string;
  emotional_triggers: string[];
  visual_style: string;
  pacing: string;
  cta_style: string;
  performance_tier: 'top_1_percent' | 'top_10_percent' | 'average' | 'unknown';
  transcript?: string;
  industry: string;
  raw_data: any;
}

interface KaggleDatasetRow {
  [key: string]: string | number;
}

/**
 * KaggleLoader - Load ad datasets from local Kaggle CSV/JSON files
 *
 * Supported datasets:
 * - advertising.csv (TV/Radio/Newspaper ad spend -> sales)
 * - facebook_ad_campaign.csv (Facebook ad performance data)
 */
export class KaggleLoader {
  private dataPath: string;

  constructor(dataPath?: string) {
    this.dataPath = dataPath || process.env.KAGGLE_DATA_PATH || '/data/kaggle';
  }

  /**
   * Load ad dataset from CSV file
   * @param filename - Name of the CSV file (e.g., 'advertising.csv')
   * @returns Promise<AdPattern[]>
   */
  async loadAdDataset(filename: string): Promise<AdPattern[]> {
    const filePath = path.join(this.dataPath, filename);

    if (!fs.existsSync(filePath)) {
      throw new Error(`KAGGLE_FILE_NOT_FOUND: ${filePath}. Run download_datasets.sh first.`);
    }

    const patterns: AdPattern[] = [];
    const stats = await this.parseAdPerformance(filePath);

    for (const row of stats) {
      const pattern = this.transformToPattern(row, filename);
      if (pattern) {
        patterns.push(pattern);
      }
    }

    console.log(`Loaded ${patterns.length} ad patterns from ${filename}`);
    return patterns;
  }

  /**
   * Parse CSV file and extract CTR, impressions, and performance metrics
   */
  private async parseAdPerformance(filePath: string): Promise<KaggleDatasetRow[]> {
    return new Promise((resolve, reject) => {
      const rows: KaggleDatasetRow[] = [];

      fs.createReadStream(filePath)
        .pipe(csv())
        .on('data', (data: KaggleDatasetRow) => {
          rows.push(data);
        })
        .on('end', () => {
          resolve(rows);
        })
        .on('error', (error) => {
          reject(new Error(`CSV_PARSE_ERROR: ${error.message}`));
        });
    });
  }

  /**
   * Transform Kaggle dataset row to AdPattern format
   */
  private transformToPattern(row: KaggleDatasetRow, source: string): AdPattern | null {
    // Handle different dataset formats
    if (source.includes('advertising')) {
      return this.transformAdvertisingDataset(row);
    } else if (source.includes('facebook')) {
      return this.transformFacebookDataset(row);
    }
    return null;
  }

  /**
   * Transform advertising.csv format
   * Columns: TV, Radio, Newspaper, Sales
   */
  private transformAdvertisingDataset(row: KaggleDatasetRow): AdPattern {
    const tv = parseFloat(row.TV as string) || 0;
    const radio = parseFloat(row.Radio as string) || 0;
    const newspaper = parseFloat(row.Newspaper as string) || 0;
    const sales = parseFloat(row.Sales as string) || 0;

    // Infer strategy from spend allocation
    let primaryChannel = 'unknown';
    let hookType = 'awareness';

    if (tv > radio && tv > newspaper) {
      primaryChannel = 'TV';
      hookType = 'visual_storytelling';
    } else if (radio > tv && radio > newspaper) {
      primaryChannel = 'Radio';
      hookType = 'audio_hook';
    } else if (newspaper > tv && newspaper > radio) {
      primaryChannel = 'Print';
      hookType = 'headline_driven';
    }

    // Calculate performance tier based on sales
    let performanceTier: AdPattern['performance_tier'] = 'average';
    if (sales > 20) performanceTier = 'top_1_percent';
    else if (sales > 15) performanceTier = 'top_10_percent';

    return {
      source: 'kaggle',
      hook_type: hookType,
      emotional_triggers: this.inferEmotionsFromChannel(primaryChannel),
      visual_style: primaryChannel === 'TV' ? 'broadcast' : 'minimal',
      pacing: primaryChannel === 'TV' ? 'medium' : 'slow',
      cta_style: 'traditional',
      performance_tier: performanceTier,
      transcript: `${primaryChannel} campaign with $${tv + radio + newspaper}k spend`,
      industry: 'retail',
      raw_data: { ...row, primaryChannel, totalSpend: tv + radio + newspaper }
    };
  }

  /**
   * Transform facebook_ad_campaign.csv format
   * Columns: ad_id, campaign_id, age, gender, interest, impressions, clicks, spent, total_conversion, approved_conversion
   */
  private transformFacebookDataset(row: KaggleDatasetRow): AdPattern {
    const impressions = parseInt(row.Impressions as string) || parseInt(row.impressions as string) || 0;
    const clicks = parseInt(row.Clicks as string) || parseInt(row.clicks as string) || 0;
    const spent = parseFloat(row.Spent as string) || parseFloat(row.spent as string) || 0;
    const conversions = parseInt(row['Total_Conversion'] as string) ||
                       parseInt(row.total_conversion as string) || 0;

    const ctr = impressions > 0 ? (clicks / impressions) * 100 : 0;
    const cpc = clicks > 0 ? spent / clicks : 0;
    const cvr = clicks > 0 ? (conversions / clicks) * 100 : 0;

    // Determine performance tier based on CTR and CVR
    let performanceTier: AdPattern['performance_tier'] = 'average';
    if (ctr > 2.0 && cvr > 5.0) performanceTier = 'top_1_percent';
    else if (ctr > 1.0 && cvr > 2.0) performanceTier = 'top_10_percent';

    // Infer targeting strategy
    const age = row.age || row.Age || 'unknown';
    const gender = row.gender || row.Gender || 'all';
    const interest = row.interest || row.Interest || 'general';

    return {
      source: 'kaggle',
      hook_type: this.inferHookFromInterest(interest as string),
      emotional_triggers: this.inferEmotionsFromInterest(interest as string),
      visual_style: 'social_media',
      pacing: 'fast',
      cta_style: this.inferCTAFromConversions(cvr),
      performance_tier: performanceTier,
      transcript: `Facebook ad targeting ${age}, ${gender}, interested in ${interest}`,
      industry: this.inferIndustryFromInterest(interest as string),
      raw_data: {
        ...row,
        metrics: { impressions, clicks, spent, conversions, ctr, cpc, cvr }
      }
    };
  }

  private inferEmotionsFromChannel(channel: string): string[] {
    const channelEmotions: Record<string, string[]> = {
      TV: ['trust', 'excitement', 'aspiration'],
      Radio: ['urgency', 'curiosity', 'trust'],
      Print: ['credibility', 'trust', 'authority']
    };
    return channelEmotions[channel] || ['neutral'];
  }

  private inferHookFromInterest(interest: string): string {
    const interestLower = interest.toLowerCase();
    if (interestLower.includes('fitness') || interestLower.includes('health')) return 'transformation';
    if (interestLower.includes('tech') || interestLower.includes('gadget')) return 'innovation';
    if (interestLower.includes('fashion') || interestLower.includes('beauty')) return 'aspiration';
    if (interestLower.includes('food') || interestLower.includes('cooking')) return 'sensory';
    return 'problem_solution';
  }

  private inferEmotionsFromInterest(interest: string): string[] {
    const interestLower = interest.toLowerCase();
    if (interestLower.includes('fitness')) return ['motivation', 'aspiration', 'urgency'];
    if (interestLower.includes('tech')) return ['curiosity', 'excitement', 'fomo'];
    if (interestLower.includes('fashion')) return ['desire', 'aspiration', 'belonging'];
    if (interestLower.includes('food')) return ['pleasure', 'comfort', 'indulgence'];
    return ['curiosity', 'trust'];
  }

  private inferIndustryFromInterest(interest: string): string {
    const interestLower = interest.toLowerCase();
    if (interestLower.includes('fitness') || interestLower.includes('health')) return 'fitness';
    if (interestLower.includes('tech')) return 'technology';
    if (interestLower.includes('fashion') || interestLower.includes('beauty')) return 'fashion';
    if (interestLower.includes('food')) return 'food_beverage';
    if (interestLower.includes('travel')) return 'travel';
    return 'general';
  }

  private inferCTAFromConversions(cvr: number): string {
    if (cvr > 5.0) return 'direct_purchase';
    if (cvr > 2.0) return 'sign_up';
    if (cvr > 1.0) return 'learn_more';
    return 'soft_engagement';
  }

  /**
   * Get available datasets in the Kaggle data directory
   */
  getAvailableDatasets(): string[] {
    if (!fs.existsSync(this.dataPath)) {
      return [];
    }

    return fs.readdirSync(this.dataPath)
      .filter(file => file.endsWith('.csv') || file.endsWith('.json'))
      .map(file => path.join(this.dataPath, file));
  }

  /**
   * Get statistics about loaded datasets
   */
  async getDatasetStats(filename: string): Promise<{
    total_rows: number;
    file_size: number;
    last_modified: Date;
  }> {
    const filePath = path.join(this.dataPath, filename);

    if (!fs.existsSync(filePath)) {
      throw new Error(`KAGGLE_FILE_NOT_FOUND: ${filePath}`);
    }

    const stats = fs.statSync(filePath);
    const rows = await this.parseAdPerformance(filePath);

    return {
      total_rows: rows.length,
      file_size: stats.size,
      last_modified: stats.mtime
    };
  }
}

/**
 * HuggingFaceLoader - Use HuggingFace models for ad generation & analysis
 *
 * Features:
 * - Load pre-trained ad generation models (GPT-2 fine-tuned on ads)
 * - Generate ad copy variants
 * - Classify ad types and sentiment
 * - FREE using HuggingFace Inference API
 */
export class HuggingFaceLoader {
  private apiToken: string | null;
  private baseUrl = 'https://api-inference.huggingface.co/models';

  constructor() {
    this.apiToken = process.env.HUGGINGFACE_API_TOKEN || null;
  }

  isConfigured(): boolean {
    return this.apiToken !== null;
  }

  /**
   * Load GPT-2 model fine-tuned for ad generation
   * Model: "mrm8488/t5-base-finetuned-ad-generation"
   */
  async loadAdsGPT2(): Promise<string> {
    if (!this.apiToken) {
      throw new Error('HUGGINGFACE_NOT_CONFIGURED: Set HUGGINGFACE_API_TOKEN (free from huggingface.co)');
    }

    return 'mrm8488/t5-base-finetuned-ad-generation';
  }

  /**
   * Generate ad variant using HuggingFace Inference API
   * @param prompt - Product/service description
   * @param options - Generation parameters
   */
  async generateAdVariant(
    prompt: string,
    options?: {
      max_length?: number;
      temperature?: number;
      top_p?: number;
    }
  ): Promise<string> {
    if (!this.apiToken) {
      throw new Error('HUGGINGFACE_NOT_CONFIGURED: Set HUGGINGFACE_API_TOKEN');
    }

    try {
      const model = 'mrm8488/t5-base-finetuned-ad-generation';
      const response = await axios.post(
        `${this.baseUrl}/${model}`,
        {
          inputs: prompt,
          parameters: {
            max_length: options?.max_length || 100,
            temperature: options?.temperature || 0.7,
            top_p: options?.top_p || 0.9,
            do_sample: true
          }
        },
        {
          headers: {
            'Authorization': `Bearer ${this.apiToken}`,
            'Content-Type': 'application/json'
          },
          timeout: 30000
        }
      );

      if (Array.isArray(response.data) && response.data.length > 0) {
        return response.data[0].generated_text || response.data[0].translation_text || '';
      }

      throw new Error('HUGGINGFACE_EMPTY_RESPONSE: No text generated');
    } catch (error: any) {
      if (error.response?.status === 503) {
        throw new Error('HUGGINGFACE_MODEL_LOADING: Model is loading, try again in 20 seconds');
      }
      throw new Error(`HUGGINGFACE_ERROR: ${error.message}`);
    }
  }

  /**
   * Analyze ad text and classify its type
   * Uses: "distilbert-base-uncased-finetuned-sst-2-english" for sentiment
   */
  async analyzeAdText(text: string): Promise<{
    sentiment: 'positive' | 'negative' | 'neutral';
    confidence: number;
    emotions: string[];
  }> {
    if (!this.apiToken) {
      throw new Error('HUGGINGFACE_NOT_CONFIGURED: Set HUGGINGFACE_API_TOKEN');
    }

    try {
      const model = 'distilbert-base-uncased-finetuned-sst-2-english';
      const response = await axios.post(
        `${this.baseUrl}/${model}`,
        { inputs: text },
        {
          headers: {
            'Authorization': `Bearer ${this.apiToken}`,
            'Content-Type': 'application/json'
          },
          timeout: 30000
        }
      );

      const results = response.data[0];
      const topResult = results[0];

      // Map sentiment labels
      let sentiment: 'positive' | 'negative' | 'neutral' = 'neutral';
      if (topResult.label === 'POSITIVE') sentiment = 'positive';
      if (topResult.label === 'NEGATIVE') sentiment = 'negative';

      // Infer emotions from text
      const emotions = this.extractEmotionsFromText(text, sentiment);

      return {
        sentiment,
        confidence: topResult.score,
        emotions
      };
    } catch (error: any) {
      throw new Error(`HUGGINGFACE_ANALYSIS_ERROR: ${error.message}`);
    }
  }

  /**
   * Generate multiple ad variants in parallel
   */
  async generateAdVariants(
    prompt: string,
    count: number = 3
  ): Promise<string[]> {
    const variants: string[] = [];

    for (let i = 0; i < count; i++) {
      try {
        const variant = await this.generateAdVariant(prompt, {
          temperature: 0.7 + (i * 0.1), // Increase temperature for diversity
          max_length: 100
        });
        variants.push(variant);
      } catch (error: any) {
        console.warn(`Failed to generate variant ${i + 1}:`, error.message);
      }
    }

    return variants;
  }

  /**
   * Transform HuggingFace generated text to AdPattern
   */
  transformToPattern(generatedText: string, prompt: string): AdPattern {
    const analysis = this.quickAnalyze(generatedText);

    return {
      source: 'huggingface',
      hook_type: analysis.hook_type,
      emotional_triggers: analysis.emotions,
      visual_style: 'text_based',
      pacing: 'medium',
      cta_style: analysis.cta_style,
      performance_tier: 'unknown',
      transcript: generatedText,
      industry: 'general',
      raw_data: {
        prompt,
        generated_text: generatedText,
        model: 'mrm8488/t5-base-finetuned-ad-generation'
      }
    };
  }

  /**
   * Quick text analysis without API call (for offline use)
   */
  private quickAnalyze(text: string): {
    hook_type: string;
    emotions: string[];
    cta_style: string;
  } {
    const textLower = text.toLowerCase();

    let hook_type = 'statement';
    if (textLower.includes('?')) hook_type = 'question';
    if (textLower.match(/\d+%/)) hook_type = 'statistic';
    if (textLower.includes('!')) hook_type = 'exclamation';

    const emotions = this.extractEmotionsFromText(text, 'neutral');

    let cta_style = 'soft';
    if (textLower.includes('buy now') || textLower.includes('shop now')) cta_style = 'direct_purchase';
    if (textLower.includes('sign up') || textLower.includes('register')) cta_style = 'sign_up';
    if (textLower.includes('learn more') || textLower.includes('discover')) cta_style = 'learn_more';

    return { hook_type, emotions, cta_style };
  }

  private extractEmotionsFromText(text: string, sentiment: string): string[] {
    const emotions: string[] = [];
    const textLower = text.toLowerCase();

    if (textLower.match(/excit|amaz|wow|incredible/)) emotions.push('excitement');
    if (textLower.match(/save|discount|deal|offer/)) emotions.push('greed');
    if (textLower.match(/limited|hurry|now|today/)) emotions.push('urgency');
    if (textLower.match(/trust|proven|guarantee|certified/)) emotions.push('trust');
    if (textLower.match(/join|community|together|belong/)) emotions.push('belonging');
    if (textLower.match(/new|innovative|revolutionary/)) emotions.push('curiosity');
    if (textLower.match(/transform|change|improve/)) emotions.push('aspiration');

    if (sentiment === 'positive' && emotions.length === 0) emotions.push('positive');
    if (sentiment === 'negative' && emotions.length === 0) emotions.push('concern');

    return emotions.length > 0 ? emotions : ['neutral'];
  }

  /**
   * Batch process multiple texts
   */
  async batchAnalyze(texts: string[]): Promise<AdPattern[]> {
    const patterns: AdPattern[] = [];

    for (const text of texts) {
      try {
        const pattern = this.transformToPattern(text, 'batch_analysis');
        patterns.push(pattern);
      } catch (error: any) {
        console.warn(`Failed to analyze text:`, error.message);
      }
    }

    return patterns;
  }
}

// Singleton exports
export const kaggleLoader = new KaggleLoader();
export const huggingfaceLoader = new HuggingFaceLoader();
