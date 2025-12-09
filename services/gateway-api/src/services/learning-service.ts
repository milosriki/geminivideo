/**
 * Learning Service - Automated weight updates based on performance data
 */
import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';

export class LearningService {
  private weightsConfig: any;
  private configPath: string;

  constructor(weightsConfig: any) {
    this.weightsConfig = weightsConfig;
    this.configPath = process.env.CONFIG_PATH || '../../shared/config';
  }

  async updateWeights(): Promise<any> {
    // Read predictions log
    const logFile = path.join(process.env.LOG_DIR || '/tmp/logs', 'predictions.jsonl');
    
    if (!fs.existsSync(logFile)) {
      return {
        status: 'no_data',
        message: 'No predictions log found'
      };
    }

    const predictions = this.loadPredictions(logFile);
    const withActuals = predictions.filter((p: any) => p.actual_ctr !== undefined);

    const minSamples = this.weightsConfig.learning?.min_samples_for_update || 50;

    if (withActuals.length < minSamples) {
      return {
        status: 'insufficient_data',
        message: `Need at least ${minSamples} samples with actuals, have ${withActuals.length}`,
        current_samples: withActuals.length,
        required_samples: minSamples
      };
    }

    // Calculate calibration
    const calibration = this.calculateCalibration(withActuals);

    // Adjust weights if needed
    const adjustments = this.calculateWeightAdjustments(calibration);

    if (Object.keys(adjustments).length > 0) {
      this.applyWeightAdjustments(adjustments);
      
      return {
        status: 'updated',
        message: 'Weights updated based on performance data',
        calibration,
        adjustments,
        samples_used: withActuals.length
      };
    }

    return {
      status: 'no_update',
      message: 'Weights are well-calibrated, no update needed',
      calibration,
      samples_used: withActuals.length
    };
  }

  private loadPredictions(logFile: string): any[] {
    try {
      if (!fs.existsSync(logFile)) {
        return [];
      }
      const content = fs.readFileSync(logFile, 'utf-8');
      return content.trim().split('\n')
        .filter(line => line.length > 0)
        .map(line => {
          try {
            return JSON.parse(line);
          } catch {
            return null;
          }
        })
        .filter(item => item !== null);
    } catch (error: any) {
      console.error(`Error loading predictions: ${error.message}`);
      return [];
    }
  }

  private calculateCalibration(predictions: any[]): any {
    let correct = 0;
    let overPredicted = 0;
    let underPredicted = 0;

    for (const pred of predictions) {
      const predictedBand = pred.scores?.predicted_band || 'mid';
      const actualCTR = pred.actual_ctr || 0;

      let actualBand = 'mid';
      if (actualCTR < 0.3) actualBand = 'low';
      else if (actualCTR >= 0.7) actualBand = 'high';

      if (predictedBand === actualBand) {
        correct++;
      } else if (
        (predictedBand === 'high' && actualBand !== 'high') ||
        (predictedBand === 'mid' && actualBand === 'low')
      ) {
        overPredicted++;
      } else {
        underPredicted++;
      }
    }

    return {
      accuracy: correct / predictions.length,
      over_predicted_rate: overPredicted / predictions.length,
      under_predicted_rate: underPredicted / predictions.length
    };
  }

  private calculateWeightAdjustments(calibration: any): Record<string, number> {
    const adjustments: Record<string, number> = {};
    const learningRate = this.weightsConfig.learning?.learning_rate || 0.01;
    const maxDelta = this.weightsConfig.learning?.max_weight_delta || 0.1;

    // If over-predicting, reduce optimistic weights
    if (calibration.over_predicted_rate > 0.3) {
      adjustments['psychology_weights.urgency'] = -Math.min(learningRate, maxDelta);
      adjustments['hook_weights.motion_spike'] = -Math.min(learningRate, maxDelta);
    }

    // If under-predicting, increase weights
    if (calibration.under_predicted_rate > 0.3) {
      adjustments['psychology_weights.transformation'] = Math.min(learningRate, maxDelta);
      adjustments['technical_weights.resolution_score'] = Math.min(learningRate, maxDelta);
    }

    return adjustments;
  }

  private applyWeightAdjustments(adjustments: Record<string, number>): void {
    const weightsPath = path.join(this.configPath, 'weights.yaml');
    const backupPath = `${weightsPath}.backup`;

    try {
      // Create backup before modifying
      if (fs.existsSync(weightsPath)) {
        fs.copyFileSync(weightsPath, backupPath);
      }

      // Update weights config
      for (const [path, delta] of Object.entries(adjustments)) {
        const parts = path.split('.');
        let obj: any = this.weightsConfig;

        for (let i = 0; i < parts.length - 1; i++) {
          obj = obj[parts[i]];
        }

        const key = parts[parts.length - 1];
        obj[key] = Math.max(0, Math.min(1, obj[key] + delta));
      }

      // Update version
      const currentVersion = this.weightsConfig.version || '1.0.0';
      const versionParts = currentVersion.split('.').map((n: string) => parseInt(n));
      versionParts[2]++; // Increment patch version
      this.weightsConfig.version = versionParts.join('.');
      this.weightsConfig.last_updated = new Date().toISOString().split('T')[0];

      // Write updated config
      fs.writeFileSync(weightsPath, yaml.dump(this.weightsConfig), 'utf8');

      console.log('Weight adjustments applied successfully');
    } catch (error: any) {
      console.error(`Error applying weight adjustments: ${error.message}`);
      // Attempt to restore from backup
      if (fs.existsSync(backupPath)) {
        fs.copyFileSync(backupPath, weightsPath);
        console.log('Restored from backup after error');
      }
      throw error;
    }
  }
}
