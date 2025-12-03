/**
 * Scoring Engine - Psychology, Hook, Technical, Demographic, Novelty scoring
 *
 * ============================================================================
 * 🔴 CRITICAL ANALYSIS FINDINGS (December 2024)
 * ============================================================================
 *
 * STATUS: HARDCODED RULES - NOT AI-POWERED DECISIONS
 *
 * WHAT'S BROKEN:
 * - Decision logic is 100% KEYWORD MATCHING (lines 91-93)
 * - allText.includes(kw.toLowerCase()) - just string contains!
 * - Fixed weights from weights.yaml, never learns
 * - Psychology scores from counting word matches, not AI analysis
 * - Win probability is formula-based, not ML-predicted
 *
 * WHAT IT SHOULD DO:
 * 1. Use Gemini/Claude to analyze content psychology
 * 2. Train ML model on actual performance data
 * 3. Update weights based on real CTR feedback
 * 4. A/B test different scoring approaches
 *
 * CURRENT WEIGHTS (hardcoded):
 * - Psychology: 30%
 * - Hook: 25%
 * - Technical: 20%
 * - Demographic: 15%
 * - Novelty: 10%
 *
 * FAST FIX:
 * Replace calculatePsychologyScore() with Gemini API call:
 *   const result = await gemini.analyze(content, "Rate psychology 0-100")
 *
 * IMPACT: System makes decisions based on word matching, not intelligence
 * ============================================================================
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

export class ScoringEngine {
  private weightsConfig: WeightsConfig;
  private triggersConfig: TriggersConfig;
  private personasConfig: PersonasConfig;

  constructor(
    weightsConfig: WeightsConfig,
    triggersConfig: TriggersConfig,
    personasConfig: PersonasConfig
  ) {
    this.weightsConfig = weightsConfig;
    this.triggersConfig = triggersConfig;
    this.personasConfig = personasConfig;
  }

  scoreStoryboard(scenes: any[], metadata: any = {}): any {
    const psychologyScore = this.calculatePsychologyScore(scenes, metadata);
    const hookScore = this.calculateHookStrength(scenes);
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

  private calculatePsychologyScore(scenes: any[], metadata: any): number {
    // ⚠️ FAKE PSYCHOLOGY SCORING ⚠️
    // This is NOT AI-powered - it's just counting keyword matches!
    // A video saying "pain pain pain" would score high on pain_point
    //
    // TODO: Replace with actual AI analysis:
    // const analysis = await gemini.analyze(scenes, "Evaluate psychological triggers");
    // return analysis.score;

    const weights = this.weightsConfig.psychology_weights;
    const keywords = this.triggersConfig.driver_keywords;

    let scores = {
      pain_point: 0,
      transformation: 0,
      urgency: 0,
      authority: 0,
      social_proof: 0
    };

    // Extract text from scenes
    const allText = this.extractAllText(scenes).toLowerCase();

    // ⚠️ THIS IS THE PROBLEM - Just string matching, not understanding!
    // Count keyword matches
    for (const [category, keywordList] of Object.entries(keywords)) {
      const matches = keywordList.filter(kw =>
        allText.includes(kw.toLowerCase())  // FAKE: Just contains() check
      ).length;
      const categoryScore = Math.min(matches / 3, 1.0); // FAKE: Arbitrary normalization

      if (category === 'pain_points') scores.pain_point = categoryScore;
      else if (category === 'transformations') scores.transformation = categoryScore;
      else if (category === 'urgency') scores.urgency = categoryScore;
      else if (category === 'authority') scores.authority = categoryScore;
      else if (category === 'social_proof') scores.social_proof = categoryScore;
    }

    // Weighted sum
    const totalScore =
      scores.pain_point * weights.pain_point +
      scores.transformation * weights.transformation +
      scores.urgency * weights.urgency +
      scores.authority * weights.authority +
      scores.social_proof * weights.social_proof;

    return totalScore;
  }

  private calculateHookStrength(scenes: any[]): number {
    const weights = this.weightsConfig.hook_weights;

    // Check first scene/clip for hook characteristics
    if (!scenes.length) return 0;

    const firstScene = scenes[0];
    const text = this.extractSceneText(firstScene).toLowerCase();

    let hasNumber = /\d+/.test(text) ? 1 : 0;
    let hasQuestion = /\?/.test(text) ? 1 : 0;
    let motionSpike = firstScene.features?.motion_score || 0;
    let first3sText = text.length > 0 && text.length <= 38 ? 1 : 0.5;

    const hookScore =
      hasNumber * weights.has_number +
      hasQuestion * weights.has_question +
      Math.min(motionSpike * 2, 1) * weights.motion_spike +
      first3sText * weights.first_3s_text;

    return Math.min(hookScore, 1.0);
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
    // ⚠️ DEMOGRAPHIC MATCHING IS MOSTLY HARDCODED ⚠️
    // - age_range: hardcoded 0.7 (line 190)
    // - fitness_level: hardcoded 0.7 (line 191)
    // - trigger_alignment: hardcoded 0.7 (line 192)
    // Only persona_match uses actual content analysis (but still just keyword matching)

    const weights = this.weightsConfig.demographic_weights;
    const personas = this.personasConfig.personas;

    // Extract text from scenes
    const allText = this.extractAllText(scenes).toLowerCase();

    // Find best matching persona (still just keyword matching, not AI)
    let bestMatch = 0;

    for (const persona of personas) {
      const keywordMatches = persona.keywords.filter(kw =>
        allText.includes(kw.toLowerCase())  // FAKE: Just string matching
      ).length;

      const matchScore = Math.min(keywordMatches / persona.keywords.length, 1.0);

      if (matchScore > bestMatch) {
        bestMatch = matchScore;
      }
    }

    // ⚠️ THREE HARDCODED VALUES BELOW - NOT REAL ANALYSIS
    // Demographic score (simplified for MVP)
    const score =
      bestMatch * weights.persona_match +
      0.7 * weights.age_range + // HARDCODED: Always 0.7, no real age detection
      0.7 * weights.fitness_level + // HARDCODED: Always 0.7, no real fitness analysis
      0.7 * weights.trigger_alignment; // HARDCODED: Always 0.7, no real trigger analysis

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
