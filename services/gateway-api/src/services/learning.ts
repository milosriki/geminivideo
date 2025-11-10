/**
 * Learning service - Weight updates
 */
import fs from 'fs';
import yaml from 'js-yaml';
import { logger } from '../logger';

export class LearningService {
  private weightsPath: string;

  constructor() {
    this.weightsPath = '/app/shared/config/weights.yaml';
  }

  async getCurrentWeights(): Promise<any> {
    try {
      const content = fs.readFileSync(this.weightsPath, 'utf-8');
      return yaml.load(content);
    } catch (error: any) {
      logger.error('Failed to read weights', { error: error.message });
      throw error;
    }
  }

  async updateWeights(predictions: any[], actuals: any[]): Promise<any> {
    try {
      // Load current weights
      const weights = await this.getCurrentWeights();
      
      // Calculate errors and adjustments
      const adjustments = this.calculateAdjustments(predictions, actuals);
      
      // Apply conservative updates
      const maxDelta = weights.learning?.max_delta_per_update || 0.05;
      const smoothingFactor = weights.learning?.smoothing_factor || 0.8;
      
      const predWeights = weights.prediction_weights || {};
      
      for (const [key, delta] of Object.entries(adjustments)) {
        const currentWeight = predWeights[key] || 0;
        const clampedDelta = Math.max(-maxDelta, Math.min(maxDelta, delta as number));
        const newWeight = currentWeight + clampedDelta * smoothingFactor;
        predWeights[key] = Math.max(0, Math.min(1, newWeight));
      }
      
      // Normalize weights to sum to 1
      const sum = Object.values(predWeights).reduce((a: any, b: any) => a + b, 0);
      if (sum > 0) {
        for (const key of Object.keys(predWeights)) {
          predWeights[key] /= sum;
        }
      }
      
      // Update version and timestamp
      weights.version = (parseFloat(weights.version || '1.0') + 0.1).toFixed(1);
      weights.last_updated = new Date().toISOString();
      weights.prediction_weights = predWeights;
      
      // Write back to file
      const yamlStr = yaml.dump(weights);
      fs.writeFileSync(this.weightsPath, yamlStr, 'utf-8');
      
      logger.info('Weights updated', { version: weights.version });
      
      return {
        version: weights.version,
        weights: predWeights,
        adjustments
      };
    } catch (error: any) {
      logger.error('Failed to update weights', { error: error.message });
      throw error;
    }
  }

  private calculateAdjustments(predictions: any[], actuals: any[]): Record<string, number> {
    // Simplified adjustment calculation
    // In production, this would use gradient descent or similar
    
    const adjustments: Record<string, number> = {
      psychology_score: 0,
      technical_score: 0,
      hook_strength: 0,
      demographic_match: 0
    };
    
    if (predictions.length !== actuals.length) {
      logger.warn('Prediction and actual arrays length mismatch');
      return adjustments;
    }
    
    // Calculate average error for each component
    for (let i = 0; i < predictions.length; i++) {
      const pred = predictions[i];
      const actual = actuals[i];
      
      const error = (actual.ctr || 0) - (pred.predictedCTR?.probability || 0);
      
      // Distribute error to components based on correlation
      // This is a simplified heuristic
      if (error > 0) {
        // Underestimated - increase weights for components that were high
        const scores = pred.scores || {};
        if (scores.psychology > 0.6) adjustments.psychology_score += 0.01;
        if (scores.technical > 0.6) adjustments.technical_score += 0.01;
        if (scores.hookStrength > 0.6) adjustments.hook_strength += 0.01;
        if (scores.demographicMatch > 0.6) adjustments.demographic_match += 0.01;
      } else {
        // Overestimated - decrease weights for components that were high
        const scores = pred.scores || {};
        if (scores.psychology > 0.6) adjustments.psychology_score -= 0.01;
        if (scores.technical > 0.6) adjustments.technical_score -= 0.01;
        if (scores.hookStrength > 0.6) adjustments.hook_strength -= 0.01;
        if (scores.demographicMatch > 0.6) adjustments.demographic_match -= 0.01;
      }
    }
    
    // Average adjustments
    const count = predictions.length;
    for (const key of Object.keys(adjustments)) {
      adjustments[key] /= count;
    }
    
    return adjustments;
  }
}
