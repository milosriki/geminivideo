/**
 * Prediction service - AI scoring and win probability
 */
import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';
import { logger } from '../logger';

interface Clip {
  objects?: string[];
  ocr_tokens?: string[];
  motion_score?: number;
  transcript_excerpt?: string;
  duration?: number;
  rankScore?: number;
}

interface PredictionResult {
  scores: {
    psychology: number;
    technical: number;
    hookStrength: number;
    demographicMatch: number;
  };
  predictedCTR: {
    band: 'low' | 'mid' | 'high';
    confidence: number;
    probability: number;
  };
  triggerStack: string[];
  personaCandidates: string[];
}

export class PredictionService {
  private triggers: any;
  private personas: any;
  private weights: any;

  constructor() {
    this.loadConfigs();
  }

  private loadConfigs() {
    try {
      // Load triggers config
      const triggersPath = '/app/shared/config/triggers_config.json';
      this.triggers = JSON.parse(fs.readFileSync(triggersPath, 'utf-8'));

      // Load personas
      const personasPath = '/app/shared/config/personas.json';
      this.personas = JSON.parse(fs.readFileSync(personasPath, 'utf-8'));

      // Load weights
      const weightsPath = '/app/shared/config/weights.yaml';
      this.weights = yaml.load(fs.readFileSync(weightsPath, 'utf-8')) as any;

      logger.info('Prediction configs loaded');
    } catch (error: any) {
      logger.error('Failed to load prediction configs', { error: error.message });
      // Set defaults
      this.triggers = { psychological_triggers: {} };
      this.personas = { personas: [] };
      this.weights = { prediction_weights: {}, ctr_bands: {} };
    }
  }

  async predict(clips: Clip[], context: any): Promise<PredictionResult> {
    try {
      // Calculate component scores
      const psychologyScore = this.calculatePsychologyScore(clips);
      const technicalScore = this.calculateTechnicalScore(clips);
      const hookStrength = this.calculateHookStrength(clips);
      const demographicMatch = this.calculateDemographicMatch(clips, context);

      // Detect triggers
      const triggerStack = this.detectTriggers(clips);

      // Find matching personas
      const personaCandidates = this.matchPersonas(clips);

      // Calculate overall prediction
      const weights = this.weights.prediction_weights || {};
      const overallScore = 
        psychologyScore * (weights.psychology_score || 0.3) +
        technicalScore * (weights.technical_score || 0.25) +
        hookStrength * (weights.hook_strength || 0.25) +
        demographicMatch * (weights.demographic_match || 0.2);

      // Determine CTR band
      const ctrBands = this.weights.ctr_bands || {};
      let band: 'low' | 'mid' | 'high' = 'mid';
      let probability = overallScore;

      if (overallScore < (ctrBands.low?.max || 0.02)) {
        band = 'low';
      } else if (overallScore >= (ctrBands.high?.min || 0.05)) {
        band = 'high';
      }

      // Calculate confidence (simplified)
      const confidence = Math.min(0.95, 0.5 + (triggerStack.length * 0.1));

      return {
        scores: {
          psychology: psychologyScore,
          technical: technicalScore,
          hookStrength: hookStrength,
          demographicMatch: demographicMatch
        },
        predictedCTR: {
          band,
          confidence,
          probability
        },
        triggerStack,
        personaCandidates
      };
    } catch (error: any) {
      logger.error('Prediction calculation failed', { error: error.message });
      throw error;
    }
  }

  private calculatePsychologyScore(clips: Clip[]): number {
    // Driver stack detection using triggers
    const triggers = this.detectTriggers(clips);
    
    // More triggers = higher psychology score
    const triggerScore = Math.min(1.0, triggers.length / 5.0);
    
    return triggerScore;
  }

  private calculateTechnicalScore(clips: Clip[]): number {
    // Simplified technical score based on clip quality
    let score = 0.5; // Base score
    
    // Check motion
    const avgMotion = clips.reduce((sum, c) => sum + (c.motion_score || 0), 0) / clips.length;
    score += avgMotion * 0.3;
    
    // Check if clips have good rank scores
    const avgRank = clips.reduce((sum, c) => sum + (c.rankScore || 0), 0) / clips.length;
    score += avgRank * 0.2;
    
    return Math.min(1.0, score);
  }

  private calculateHookStrength(clips: Clip[]): number {
    if (clips.length === 0) return 0;
    
    const firstClip = clips[0];
    let score = 0.3; // Base score
    
    // Check for brevity (short first clip is good)
    const duration = firstClip.duration || 10;
    if (duration <= 3) score += 0.3;
    else if (duration <= 5) score += 0.2;
    
    // Check for numbers in OCR
    const hasNumbers = (firstClip.ocr_tokens || []).some(token => 
      /\d+/.test(token)
    );
    if (hasNumbers) score += 0.2;
    
    // Check for questions
    const hasQuestion = (firstClip.ocr_tokens || []).some(token =>
      token.includes('?') || /^(how|why|what|when|where|who)/i.test(token)
    );
    if (hasQuestion) score += 0.2;
    
    return Math.min(1.0, score);
  }

  private calculateDemographicMatch(clips: Clip[], context: any): number {
    const personas = this.matchPersonas(clips);
    
    // More matching personas = higher score
    const score = Math.min(1.0, personas.length / 3.0);
    
    return score;
  }

  private detectTriggers(clips: Clip[]): string[] {
    const triggers: string[] = [];
    const triggerConfig = this.triggers.psychological_triggers || {};
    
    // Collect all text from clips
    const allText = clips.flatMap(c => [
      ...(c.ocr_tokens || []),
      c.transcript_excerpt || ''
    ]).join(' ').toLowerCase();
    
    // Check each trigger
    for (const [triggerName, config] of Object.entries(triggerConfig)) {
      const triggerData = config as any;
      const keywords = triggerData.keywords || [];
      const patterns = triggerData.patterns || [];
      
      // Check keywords
      const hasKeyword = keywords.some((kw: string) => allText.includes(kw.toLowerCase()));
      
      // Check patterns
      const hasPattern = patterns.some((pattern: string) => {
        try {
          return new RegExp(pattern, 'i').test(allText);
        } catch {
          return false;
        }
      });
      
      if (hasKeyword || hasPattern) {
        triggers.push(triggerName);
      }
    }
    
    return triggers;
  }

  private matchPersonas(clips: Clip[]): string[] {
    const matches: string[] = [];
    const personasList = this.personas.personas || [];
    
    // Collect all text and objects
    const allTokens = clips.flatMap(c => [
      ...(c.ocr_tokens || []),
      ...(c.objects || [])
    ]).map(t => t.toLowerCase());
    
    // Match against each persona
    for (const persona of personasList) {
      const keywords = persona.keywords || [];
      const matchCount = keywords.filter((kw: string) => 
        allTokens.some(token => token.includes(kw.toLowerCase()))
      ).length;
      
      if (matchCount >= 2) {
        matches.push(persona.name || persona.id);
      }
    }
    
    return matches;
  }
}
