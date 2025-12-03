/**
 * Scoring Engine - Psychology, Hook, Technical, Demographic, Novelty scoring
 */

interface WeightsConfig {
  psychology_weights: Record<string, number>;
  hook_weights: Record<string, number>;
  technical_weights: Record<string, number>;
  demographic_weights: Record<string, number>;
  novelty_weights: Record<string, number>;
  probability_bands: any;
}

interface TriggersConfig {
  driver_keywords: Record<string, string[]>;
  fitness_triggers: Record<string, string[]>;
}

interface PersonasConfig {
  personas: Array<{
    id: string;
    name: string;
    keywords: string[];
    pain_points: string[];
    goals: string[];
  }>;
}

import { GeminiScoringService } from './gemini-scoring';

export class ScoringEngine {
  private weightsConfig: WeightsConfig;
  private triggersConfig: TriggersConfig;
  private personasConfig: PersonasConfig;
  private geminiService: GeminiScoringService;

  constructor(
    weightsConfig: WeightsConfig,
    triggersConfig: TriggersConfig,
    personasConfig: PersonasConfig
  ) {
    this.weightsConfig = weightsConfig;
    this.triggersConfig = triggersConfig;
    this.personasConfig = personasConfig;
    this.geminiService = new GeminiScoringService(process.env.GEMINI_API_KEY || '');
  }

  async scoreStoryboard(scenes: any[], metadata: any = {}): Promise<any> {
    // Parallelize AI calls for speed
    const [psychologyScore, hookScore] = await Promise.all([
      this.calculatePsychologyScore(scenes, metadata),
      this.calculateHookStrength(scenes)
    ]);

    const technicalScore = this.calculateTechnicalScore(scenes);
    const demographicScore = this.calculateDemographicMatch(scenes, metadata);
    const noveltyScore = this.calculateNoveltyScore(scenes);

    // Weighted composite score
    const compositeScore =
      psychologyScore * 0.3 +
      hookScore * 0.25 +
      technicalScore * 0.2 +
      demographicScore * 0.15 +
      noveltyScore * 0.1;

    const winProbability = this.calculateWinProbability(compositeScore);

    return {
      psychology_score: psychologyScore,
      hook_strength: hookScore,
      technical_score: technicalScore,
      demographic_match: demographicScore,
      novelty_score: noveltyScore,
      composite_score: compositeScore,
      win_probability: winProbability,
      predicted_band: winProbability.band,
      confidence: winProbability.confidence
    };
  }

  private async calculatePsychologyScore(scenes: any[], metadata: any): Promise<number> {
    const weights = this.weightsConfig.psychology_weights;

    // Extract text from scenes
    const allText = this.extractAllText(scenes);

    // Call Gemini for deep analysis
    const analysis = await this.geminiService.analyzeScene(allText, "Psychological Impact Analysis");

    // Map AI scores (0-10) to normalized (0-1)
    const painScore = (analysis.pain_point_score || 0) / 10;

    // Fallback to keyword matching if AI fails or returns 0 (unlikely with fallback)
    // But we trust the AI now.

    // We still use some heuristics for other parts if AI doesn't cover them explicitly yet
    // Or we could expand the AI prompt. For speedrun, we map what we have.

    const scores = {
      pain_point: painScore,
      transformation: painScore * 0.8, // inferred
      urgency: painScore * 0.7, // inferred
      authority: 0.5, // placeholder
      social_proof: 0.5 // placeholder
    };

    // Weighted sum
    const totalScore =
      scores.pain_point * weights.pain_point +
      scores.transformation * weights.transformation +
      scores.urgency * weights.urgency +
      scores.authority * weights.authority +
      scores.social_proof * weights.social_proof;

    return totalScore;
  }

  private async calculateHookStrength(scenes: any[]): Promise<number> {
    const weights = this.weightsConfig.hook_weights;

    // Check first scene/clip for hook characteristics
    if (!scenes.length) return 0;

    const firstScene = scenes[0];
    const text = this.extractSceneText(firstScene);

    // Call Gemini for Hook Analysis
    const analysis = await this.geminiService.analyzeScene(text, "Hook Strength Analysis");
    const aiHookScore = (analysis.hook_score || 0) / 10;

    // Hybrid: AI Score + Technical Signals (Motion)
    let motionSpike = firstScene.features?.motion_score || 0;

    // Blend AI judgment with raw signal
    const finalHook = (aiHookScore * 0.7) + (Math.min(motionSpike * 2, 1) * 0.3);

    return Math.min(finalHook, 1.0);
  }

  private calculateTechnicalScore(scenes: any[]): number {
    if (!scenes.length) return 0;

    const weights = this.weightsConfig.technical_weights;

    // Average technical quality from scenes
    let avgQuality = 0;
    let count = 0;

    for (const scene of scenes) {
      if (scene.features?.technical_quality !== undefined) {
        avgQuality += scene.features.technical_quality;
        count++;
      }
    }

    avgQuality = count > 0 ? avgQuality / count : 0.5;

    // For MVP, use technical_quality as proxy for all technical aspects
    const score =
      avgQuality * weights.resolution_score +
      avgQuality * weights.audio_quality +
      avgQuality * weights.lighting +
      avgQuality * weights.stabilization;

    return Math.min(score, 1.0);
  }

  private calculateDemographicMatch(scenes: any[], metadata: any): number {
    const weights = this.weightsConfig.demographic_weights;
    const personas = this.personasConfig.personas;

    // Extract text from scenes
    const allText = this.extractAllText(scenes).toLowerCase();

    // Find best matching persona
    let bestMatch = 0;

    for (const persona of personas) {
      const keywordMatches = persona.keywords.filter(kw =>
        allText.includes(kw.toLowerCase())
      ).length;

      const matchScore = Math.min(keywordMatches / persona.keywords.length, 1.0);

      if (matchScore > bestMatch) {
        bestMatch = matchScore;
      }
    }

    // Demographic score (simplified for MVP)
    const score =
      bestMatch * weights.persona_match +
      0.7 * weights.age_range + // Placeholder
      0.7 * weights.fitness_level + // Placeholder
      0.7 * weights.trigger_alignment; // Placeholder

    return Math.min(score, 1.0);
  }

  private calculateNoveltyScore(scenes: any[]): number {
    if (!scenes.length) return 0.5;

    // Use novelty scores from scenes if available
    let avgNovelty = 0;
    let count = 0;

    for (const scene of scenes) {
      if (scene.novelty_score !== undefined) {
        avgNovelty += scene.novelty_score;
        count++;
      }
    }

    return count > 0 ? avgNovelty / count : 0.5;
  }

  private calculateWinProbability(compositeScore: number): any {
    const bands = this.weightsConfig.probability_bands;

    // Determine band
    let band: string;
    let confidence: number;

    if (compositeScore < bands.low.max) {
      band = 'low';
      confidence = bands.low.confidence_threshold;
    } else if (compositeScore >= bands.high.min) {
      band = 'high';
      confidence = bands.high.confidence_threshold;
    } else {
      band = 'mid';
      confidence = bands.mid.confidence_threshold;
    }

    return {
      probability: compositeScore,
      band,
      confidence
    };
  }

  private extractAllText(scenes: any[]): string {
    return scenes
      .map(scene => this.extractSceneText(scene))
      .join(' ');
  }

  private extractSceneText(scene: any): string {
    const texts: string[] = [];

    if (scene.features?.text_detected) {
      texts.push(...scene.features.text_detected);
    }

    if (scene.features?.transcript) {
      texts.push(scene.features.transcript);
    }

    if (scene.text) {
      texts.push(scene.text);
    }

    return texts.join(' ');
  }
}
