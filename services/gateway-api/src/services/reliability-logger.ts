/**
 * Reliability Logger - JSONL prediction logging and metrics
 */
import * as fs from 'fs';
import * as path from 'path';
import { v4 as uuidv4 } from 'uuid';

interface PredictionLog {
  prediction_id: string;
  timestamp: string;
  scenes: any[];
  scores: any;
  metadata: any;
  actual_ctr?: number;
  actual_clicks?: number;
  actual_impressions?: number;
  updated_at?: string;
  trigger?: string;
}

export class ReliabilityLogger {
  private logFile: string;
  private predictions: Map<string, PredictionLog>;

  constructor() {
    const logDir = process.env.LOG_DIR || '/tmp/logs';
    this.logFile = path.join(logDir, 'predictions.jsonl');
    this.predictions = new Map();
    
    // Ensure log directory exists
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }

    // Load existing predictions
    this.loadPredictions();
  }

  logPrediction(data: any): string {
    const predictionId = uuidv4();
    
    const logEntry: PredictionLog = {
      prediction_id: predictionId,
      timestamp: data.timestamp || new Date().toISOString(),
      scenes: data.scenes,
      scores: data.scores,
      metadata: data.metadata || {}
    };

    // Store in memory
    this.predictions.set(predictionId, logEntry);

    // Append to JSONL file
    try {
      fs.appendFileSync(
        this.logFile,
        JSON.stringify(logEntry) + '\n',
        'utf8'
      );
    } catch (error) {
      console.error('Error writing to prediction log:', error);
    }

    return predictionId;
  }

  updateActualCTR(predictionId: string, actualCTR: number, clicks: number, impressions: number): void {
    try {
      // Validate inputs
      if (actualCTR < 0 || actualCTR > 1) {
        console.error(`Invalid CTR value: ${actualCTR}. Must be between 0 and 1`);
        return;
      }
      if (clicks < 0 || impressions < 0) {
        console.error('Invalid clicks/impressions: must be non-negative');
        return;
      }

      const prediction = this.predictions.get(predictionId);
      if (!prediction) {
        console.warn(`Prediction ${predictionId} not found`);
        return;
      }

      prediction.actual_ctr = actualCTR;
      prediction.actual_clicks = clicks;
      prediction.actual_impressions = impressions;
      prediction.updated_at = new Date().toISOString();

      // Persist to file (append update record)
      const updateLine = JSON.stringify({
        type: 'update',
        prediction_id: predictionId,
        actual_ctr: actualCTR,
        actual_clicks: clicks,
        actual_impressions: impressions,
        updated_at: prediction.updated_at
      });
      fs.appendFileSync(this.logFile, updateLine + '\n');

      console.log(`Updated CTR for prediction ${predictionId}`);
    } catch (error: any) {
      console.error(`Error updating CTR: ${error.message}`);
    }
  }

  private loadPredictions(): void {
    if (!fs.existsSync(this.logFile)) {
      return;
    }

    try {
      const content = fs.readFileSync(this.logFile, 'utf8');
      const lines = content.trim().split('\n');

      for (const line of lines) {
        if (line.trim()) {
          const entry = JSON.parse(line) as PredictionLog;
          this.predictions.set(entry.prediction_id, entry);
        }
      }
    } catch (error) {
      console.error('Error loading predictions:', error);
    }
  }

  getReliabilityMetrics(): any {
    const predictions = Array.from(this.predictions.values());
    
    // Filter predictions with actual CTR
    const withActuals = predictions.filter(p => p.actual_ctr !== undefined);

    if (withActuals.length === 0) {
      return {
        total_predictions: predictions.length,
        with_actuals: 0,
        in_band_count: 0,
        above_high_count: 0,
        below_low_count: 0,
        calibration: {
          in_band_percentage: 0,
          above_high_percentage: 0,
          below_low_percentage: 0
        }
      };
    }

    let inBandCount = 0;
    let aboveHighCount = 0;
    let belowLowCount = 0;

    for (const pred of withActuals) {
      const predictedBand = pred.scores?.predicted_band || 'mid';
      const actualCTR = pred.actual_ctr || 0;

      // Band thresholds
      if (predictedBand === 'low' && actualCTR <= 0.3) {
        inBandCount++;
      } else if (predictedBand === 'mid' && actualCTR > 0.3 && actualCTR < 0.7) {
        inBandCount++;
      } else if (predictedBand === 'high' && actualCTR >= 0.7) {
        inBandCount++;
      } else if (actualCTR >= 0.7) {
        aboveHighCount++;
      } else if (actualCTR <= 0.3) {
        belowLowCount++;
      }
    }

    return {
      total_predictions: predictions.length,
      with_actuals: withActuals.length,
      in_band_count: inBandCount,
      above_high_count: aboveHighCount,
      below_low_count: belowLowCount,
      calibration: {
        in_band_percentage: (inBandCount / withActuals.length) * 100,
        above_high_percentage: (aboveHighCount / withActuals.length) * 100,
        below_low_percentage: (belowLowCount / withActuals.length) * 100
      }
    };
  }

  getDiversificationMetrics(): any {
    const predictions = Array.from(this.predictions.values());

    if (predictions.length === 0) {
      return {
        trigger_entropy: 0,
        persona_coverage: 0,
        novelty_index: 0
      };
    }

    // Calculate trigger diversity (simplified)
    const triggerCounts: Record<string, number> = {};
    
    for (const pred of predictions) {
      // Extract triggers from scores
      const triggers = pred.scores?.triggers || [];
      for (const trigger of triggers) {
        triggerCounts[trigger] = (triggerCounts[trigger] || 0) + 1;
      }
    }

    // Shannon entropy
    const total = Object.values(triggerCounts).reduce((a, b) => a + b, 0);
    let entropy = 0;
    
    if (total > 0) {
      for (const count of Object.values(triggerCounts)) {
        const p = count / total;
        entropy -= p * Math.log2(p);
      }
    }

    // Average novelty score
    let avgNovelty = 0;
    let noveltyCount = 0;

    for (const pred of predictions) {
      if (pred.scores?.novelty_score !== undefined) {
        avgNovelty += pred.scores.novelty_score;
        noveltyCount++;
      }
    }

    avgNovelty = noveltyCount > 0 ? avgNovelty / noveltyCount : 0;

    return {
      trigger_entropy: entropy,
      persona_coverage: Object.keys(triggerCounts).length,
      novelty_index: avgNovelty,
      total_predictions: predictions.length
    };
  }

  detectFatigue(): Array<{trigger: string, count: number, fatigue_score: number}> {
    try {
      const triggerCounts = new Map<string, number>();
      const recentPredictions = Array.from(this.predictions.values())
        .filter(p => {
          const timestamp = new Date(p.timestamp);
          const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
          return timestamp > dayAgo;
        });

      // Count trigger usage
      recentPredictions.forEach(p => {
        const trigger = p.trigger || p.metadata?.trigger || 'unknown';
        triggerCounts.set(trigger, (triggerCounts.get(trigger) || 0) + 1);
      });

      // Calculate fatigue scores (higher count = higher fatigue)
      const totalPredictions = recentPredictions.length || 1;
      const results: Array<{trigger: string, count: number, fatigue_score: number}> = [];

      triggerCounts.forEach((count, trigger) => {
        const fatigue_score = Math.min(1, count / (totalPredictions * 0.3)); // 30% threshold
        if (fatigue_score > 0.5) { // Only report high fatigue
          results.push({ trigger, count, fatigue_score });
        }
      });

      return results.sort((a, b) => b.fatigue_score - a.fatigue_score);
    } catch (error: any) {
      console.error(`Error detecting fatigue: ${error.message}`);
      return [];
    }
  }
}
