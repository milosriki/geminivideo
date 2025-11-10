/**
 * Reliability logging service
 */
import fs from 'fs';
import path from 'path';
import { logger } from '../logger';

interface PredictionLog {
  creativeId: string;
  prediction: any;
  timestamp: string;
  features: any;
  actuals?: any;
}

export class ReliabilityLogger {
  private logPath: string;

  constructor() {
    this.logPath = '/app/logs/predictions.jsonl';
    this.ensureLogFile();
  }

  private ensureLogFile() {
    try {
      const dir = path.dirname(this.logPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      if (!fs.existsSync(this.logPath)) {
        fs.writeFileSync(this.logPath, '');
      }
    } catch (error: any) {
      logger.error('Failed to ensure log file', { error: error.message });
    }
  }

  async log(entry: PredictionLog): Promise<void> {
    try {
      const line = JSON.stringify(entry) + '\n';
      fs.appendFileSync(this.logPath, line, 'utf-8');
      logger.debug('Logged prediction', { creativeId: entry.creativeId });
    } catch (error: any) {
      logger.error('Failed to log prediction', { error: error.message });
    }
  }

  async getStats(): Promise<any> {
    try {
      // Read all logs
      if (!fs.existsSync(this.logPath)) {
        return {
          total: 0,
          distribution: { low: 0, mid: 0, high: 0 },
          inBand: 0,
          above: 0,
          below: 0
        };
      }

      const content = fs.readFileSync(this.logPath, 'utf-8');
      const lines = content.split('\n').filter(l => l.trim());
      
      const distribution = { low: 0, mid: 0, high: 0 };
      let inBand = 0;
      let above = 0;
      let below = 0;
      
      for (const line of lines) {
        try {
          const entry = JSON.parse(line);
          const band = entry.prediction?.predictedCTR?.band || 'mid';
          distribution[band as keyof typeof distribution]++;
          
          // If we have actuals, calculate accuracy
          if (entry.actuals) {
            const predicted = entry.prediction?.predictedCTR?.probability || 0;
            const actual = entry.actuals?.ctr || 0;
            
            if (Math.abs(predicted - actual) < 0.01) {
              inBand++;
            } else if (actual > predicted) {
              above++;
            } else {
              below++;
            }
          }
        } catch {
          continue;
        }
      }
      
      return {
        total: lines.length,
        distribution,
        inBand,
        above,
        below
      };
    } catch (error: any) {
      logger.error('Failed to get stats', { error: error.message });
      return { total: 0, distribution: { low: 0, mid: 0, high: 0 } };
    }
  }
}
