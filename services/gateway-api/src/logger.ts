import * as fs from 'fs';
import * as path from 'path';
import { PredictionLogEntry } from './types';

const LOGS_DIR = path.join(__dirname, '../../../logs');
const PREDICTIONS_LOG = path.join(LOGS_DIR, 'predictions.jsonl');

// Ensure logs directory exists
if (!fs.existsSync(LOGS_DIR)) {
  fs.mkdirSync(LOGS_DIR, { recursive: true });
}

/**
 * Log prediction to JSONL file for reliability tracking and nightly learning
 */
export function logPrediction(entry: PredictionLogEntry): void {
  try {
    const logLine = JSON.stringify(entry) + '\n';
    fs.appendFileSync(PREDICTIONS_LOG, logLine, 'utf8');
  } catch (error) {
    console.error('Failed to log prediction:', error);
  }
}

/**
 * Read all prediction logs (for analysis and learning)
 */
export function readPredictionLogs(): PredictionLogEntry[] {
  try {
    if (!fs.existsSync(PREDICTIONS_LOG)) {
      return [];
    }

    const content = fs.readFileSync(PREDICTIONS_LOG, 'utf8');
    const lines = content.split('\n').filter(line => line.trim());
    
    return lines.map(line => {
      try {
        return JSON.parse(line) as PredictionLogEntry;
      } catch {
        return null;
      }
    }).filter(entry => entry !== null) as PredictionLogEntry[];
  } catch (error) {
    console.error('Failed to read prediction logs:', error);
    return [];
  }
}

/**
 * Update actual CTR for a prediction (called when insights are available)
 */
export function updateActualCTR(predictionId: string, actualCTR: number): boolean {
  try {
    const logs = readPredictionLogs();
    const updatedLogs = logs.map(entry => {
      if (entry.prediction_id === predictionId) {
        return { ...entry, actual_ctr: actualCTR };
      }
      return entry;
    });

    // Rewrite log file with updated entries
    const content = updatedLogs.map(entry => JSON.stringify(entry)).join('\n') + '\n';
    fs.writeFileSync(PREDICTIONS_LOG, content, 'utf8');
    
    return true;
  } catch (error) {
    console.error('Failed to update actual CTR:', error);
    return false;
  }
}
