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

  updateActualCTR(predictionId: string, actualCTR: number, clicks: number, impressions: number): boolean {
    const prediction = this.predictions.get(predictionId);
    
    if (!prediction) {
      return false;
    }

    prediction.actual_ctr = actualCTR;
    prediction.actual_clicks = clicks;
    prediction.actual_impressions = impressions;

    // Note: In a full implementation, would update the JSONL file or use a database
    return true;
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

  detectFatigue(): any[] {
    // Stub for fatigue detection
    // Would track creatives exceeding predicted upper band then decaying below lower band
    return [];
  }
}
