/**
 * Unit tests for scoring engine
 */

import { ScoringEngine } from '../services/scoring-engine';

// Mock configurations
const mockWeightsConfig = {
  psychology_weights: {
    pain_point: 0.30,
    transformation: 0.25,
    urgency: 0.20,
    authority: 0.15,
    social_proof: 0.10
  },
  hook_weights: {
    has_number: 0.35,
    has_question: 0.25,
    motion_spike: 0.20,
    first_3s_text: 0.20
  },
  technical_weights: {
    resolution_score: 0.30,
    audio_quality: 0.25,
    lighting: 0.20,
    stabilization: 0.25
  },
  demographic_weights: {
    persona_match: 0.40,
    age_range: 0.25,
    fitness_level: 0.20,
    trigger_alignment: 0.15
  },
  novelty_weights: {
    semantic_uniqueness: 0.60,
    visual_diversity: 0.40
  },
  probability_bands: {
    low: { min: 0.0, max: 0.3, confidence_threshold: 0.6 },
    mid: { min: 0.3, max: 0.7, confidence_threshold: 0.7 },
    high: { min: 0.7, max: 1.0, confidence_threshold: 0.8 }
  }
};

const mockTriggersConfig = {
  driver_keywords: {
    pain_points: ['struggling', 'tired', 'stuck'],
    transformations: ['transform', 'change', 'achieve'],
    urgency: ['now', 'today', 'limited'],
    authority: ['certified', 'expert', 'proven'],
    social_proof: ['clients', 'results', 'success']
  },
  fitness_triggers: {}
};

const mockPersonasConfig = {
  personas: [
    {
      id: 'weight_loss',
      name: 'Weight Loss Seeker',
      keywords: ['lose weight', 'fat loss', 'slim'],
      pain_points: ['tried everything'],
      goals: ['lose weight']
    }
  ]
};

describe('ScoringEngine', () => {
  let engine: ScoringEngine;

  beforeEach(() => {
    engine = new ScoringEngine(mockWeightsConfig, mockTriggersConfig, mockPersonasConfig);
  });

  test('should calculate hook strength with number', async () => {
    const scenes = [
      {
        features: {
          text_detected: ['Lose 10 pounds in 30 days'],
          motion_score: 0.5
        }
      }
    ];

    const scores = await engine.scoreStoryboard(scenes);

    expect(scores.hook_strength).toBeGreaterThan(0);
    expect(scores.hook_strength).toBeLessThanOrEqual(1);
  });

  test('should calculate psychology score with keywords', async () => {
    const scenes = [
      {
        features: {
          text_detected: ['Transform your body now with proven methods'],
          transcript: 'Are you struggling? Get results today!'
        }
      }
    ];

    const scores = await engine.scoreStoryboard(scenes);

    expect(scores.psychology_score).toBeGreaterThan(0);
  });

  test('should assign correct probability band', async () => {
    const scenes = [
      {
        features: {
          text_detected: ['Transform now'],
          motion_score: 0.8,
          technical_quality: 0.9
        },
        novelty_score: 0.7
      }
    ];

    const scores = await engine.scoreStoryboard(scenes);

    expect(scores.predicted_band).toMatch(/low|mid|high/);
    expect(scores.confidence).toBeGreaterThan(0);
    expect(scores.confidence).toBeLessThanOrEqual(1);
  });

  test('should calculate composite score', async () => {
    const scenes = [
      {
        features: {
          motion_score: 0.5,
          technical_quality: 0.7
        }
      }
    ];

    const scores = await engine.scoreStoryboard(scenes);

    expect(scores.composite_score).toBeGreaterThanOrEqual(0);
    expect(scores.composite_score).toBeLessThanOrEqual(1);
  });
});

// Run tests if this file is executed directly
if (require.main === module) {
  console.log('Run tests with: npm test');
}
