import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';
import { PsychologyScore, HookStrength, NoveltyScore, ScoreBundle } from './types';

// Load weights configuration
let weights: any = {};
const weightsPath = path.join(__dirname, '../../../shared/config/weights.yaml');

try {
  if (fs.existsSync(weightsPath)) {
    const weightsContent = fs.readFileSync(weightsPath, 'utf8');
    weights = yaml.load(weightsContent) as any;
  }
} catch (error) {
  console.warn('Failed to load weights.yaml, using defaults:', error);
  weights = {
    psychology: {
      curiosity: 0.85,
      urgency: 0.78,
      social_proof: 0.72,
      surprise: 0.68,
      empathy: 0.75
    },
    hooks: {
      curiosity_gap: 0.85,
      urgency_scarcity: 0.78,
      social_proof: 0.72,
      pattern_interrupt: 0.68,
      emotional_story: 0.75
    },
    novelty: {
      embedding_threshold: 0.85,
      temporal_decay: 0.95,
      diversity_bonus: 0.10
    }
  };
}

/**
 * Calculate psychology score for a clip
 * Based on detected psychological triggers and weighted factors
 */
export function calculatePsychologyScore(features: any): PsychologyScore {
  const psychWeights = weights.psychology || {};
  
  // Extract or infer psychology factors from features
  const curiosity = features.has_question || features.incomplete_narrative ? 0.8 : 0.4;
  const urgency = features.has_countdown || features.limited_time ? 0.85 : 0.3;
  const socialProof = features.has_testimonial || features.crowd_reaction ? 0.75 : 0.35;
  const surprise = features.pattern_break || features.unexpected_element ? 0.7 : 0.3;
  const empathy = features.emotional_face || features.story_arc ? 0.8 : 0.4;

  // Calculate weighted composite
  const composite = (
    curiosity * psychWeights.curiosity +
    urgency * psychWeights.urgency +
    socialProof * psychWeights.social_proof +
    surprise * psychWeights.surprise +
    empathy * psychWeights.empathy
  ) / 5.0;

  return {
    curiosity,
    urgency,
    social_proof: socialProof,
    surprise,
    empathy,
    composite
  };
}

/**
 * Calculate hook strength based on detected hook type
 */
export function calculateHookStrength(features: any): HookStrength {
  const hookWeights = weights.hooks || {};
  
  // Detect most likely hook type
  let hookType = 'pattern_interrupt';
  let strength = 0.5;
  
  if (features.has_question || features.incomplete_narrative) {
    hookType = 'curiosity_gap';
    strength = 0.85;
  } else if (features.has_countdown || features.limited_time) {
    hookType = 'urgency_scarcity';
    strength = 0.78;
  } else if (features.has_testimonial || features.crowd_reaction) {
    hookType = 'social_proof';
    strength = 0.72;
  } else if (features.emotional_face || features.story_arc) {
    hookType = 'emotional_story';
    strength = 0.75;
  }

  // Apply weight from config
  const weightedStrength = strength * (hookWeights[hookType] || 1.0);
  
  return {
    hook_type: hookType,
    strength: weightedStrength,
    confidence: 0.75 // Placeholder - would come from ML model
  };
}

/**
 * Calculate novelty score using embedding distance and temporal factors
 */
export function calculateNoveltyScore(features: any, history: any[] = []): NoveltyScore {
  const noveltyConfig = weights.novelty || {};
  
  // Embedding distance from recent content (placeholder - would use FAISS)
  const embeddingDistance = history.length > 0 ? 0.72 : 0.90;
  
  // Temporal decay - newer content gets higher novelty
  const hoursSinceLastSimilar = features.hours_since_similar || 24;
  const temporalDecay = Math.pow(noveltyConfig.temporal_decay || 0.95, hoursSinceLastSimilar);
  
  // Diversity bonus for unique features
  const uniqueFeatureCount = features.unique_features || 2;
  const diversityBonus = Math.min(uniqueFeatureCount * (noveltyConfig.diversity_bonus || 0.10), 0.30);
  
  // Composite novelty score
  const composite = (embeddingDistance * temporalDecay) + diversityBonus;
  
  return {
    embedding_distance: embeddingDistance,
    temporal_decay: temporalDecay,
    diversity_bonus: diversityBonus,
    composite: Math.min(composite, 1.0)
  };
}

/**
 * Calculate complete score bundle for a clip
 */
export function calculateScoreBundle(features: any, history: any[] = []): ScoreBundle {
  const psychology = calculatePsychologyScore(features);
  const hookStrength = calculateHookStrength(features);
  const novelty = calculateNoveltyScore(features, history);
  
  // Calculate composite score (weighted average)
  const composite = (
    psychology.composite * 0.4 +
    hookStrength.strength * 0.35 +
    novelty.composite * 0.25
  );
  
  return {
    psychology,
    hook_strength: hookStrength,
    novelty,
    composite
  };
}

/**
 * Predict performance band based on composite score
 */
export function predictPerformanceBand(compositeScore: number): { band: string; predicted_ctr: number } {
  const bands = weights.performance_bands || {
    viral: { min_score: 0.85, expected_ctr: 0.08 },
    high: { min_score: 0.70, expected_ctr: 0.05 },
    medium: { min_score: 0.50, expected_ctr: 0.03 },
    low: { min_score: 0.00, expected_ctr: 0.01 }
  };

  if (compositeScore >= bands.viral.min_score) {
    return { band: 'viral', predicted_ctr: bands.viral.expected_ctr };
  } else if (compositeScore >= bands.high.min_score) {
    return { band: 'high', predicted_ctr: bands.high.expected_ctr };
  } else if (compositeScore >= bands.medium.min_score) {
    return { band: 'medium', predicted_ctr: bands.medium.expected_ctr };
  } else {
    return { band: 'low', predicted_ctr: bands.low.expected_ctr };
  }
}
