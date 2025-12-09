import { Pool } from 'pg';
import axios from 'axios';

const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8004';

interface BatchJob {
  id: string;
  type: 'campaign_launch' | 'ad_approval' | 'performance_update' | 'prediction_batch';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  data: any;
  created_at: Date;
  completed_at?: Date;
  error?: string;
}

export class BatchExecutor {
  private pgPool: Pool;
  private isRunning: boolean = false;
  private batchSize: number = 50;

  constructor(pgPool: Pool) {
    this.pgPool = pgPool;
  }

  async processPendingJobs(): Promise<void> {
    if (this.isRunning) {
      console.log('Batch executor already running, skipping');
      return;
    }

    this.isRunning = true;
    try {
      const jobs = await this.fetchPendingJobs();
      console.log(`Processing ${jobs.length} pending batch jobs`);

      for (const job of jobs) {
        try {
          await this.processJob(job);
        } catch (error: any) {
          console.error(`Error processing job ${job.id}: ${error.message}`);
          await this.markJobFailed(job.id, error.message);
        }
      }
    } finally {
      this.isRunning = false;
    }
  }

  private async fetchPendingJobs(): Promise<BatchJob[]> {
    const result = await this.pgPool.query(
      `SELECT * FROM batch_jobs
       WHERE status = 'pending'
       ORDER BY created_at ASC
       LIMIT $1`,
      [this.batchSize]
    );
    return result.rows;
  }

  private async processJob(job: BatchJob): Promise<void> {
    await this.markJobProcessing(job.id);

    switch (job.type) {
      case 'prediction_batch':
        await this.processPredictionBatch(job);
        break;
      case 'performance_update':
        await this.processPerformanceUpdate(job);
        break;
      case 'campaign_launch':
        await this.processCampaignLaunch(job);
        break;
      default:
        throw new Error(`Unknown job type: ${job.type}`);
    }

    await this.markJobCompleted(job.id);
  }

  private async processPredictionBatch(job: BatchJob): Promise<void> {
    const { ad_ids } = job.data;
    const response = await axios.post(`${ML_SERVICE_URL}/api/ml/predict/batch`, {
      ad_ids
    }, { timeout: 120000 });
    console.log(`Batch prediction completed: ${response.data.results?.length} predictions`);
  }

  private async processPerformanceUpdate(job: BatchJob): Promise<void> {
    const { campaign_ids } = job.data;
    const response = await axios.post(`${ML_SERVICE_URL}/api/ml/actuals/batch`, {
      campaign_ids
    }, { timeout: 120000 });
    console.log(`Performance update completed: ${response.data.updated} campaigns`);
  }

  private async processCampaignLaunch(job: BatchJob): Promise<void> {
    const { campaign_id, platforms } = job.data;
    // Launch to each platform
    for (const platform of platforms) {
      await axios.post(`${ML_SERVICE_URL}/api/publish/${platform}`, {
        campaign_id
      }, { timeout: 60000 });
    }
    console.log(`Campaign ${campaign_id} launched to ${platforms.join(', ')}`);
  }

  private async markJobProcessing(jobId: string): Promise<void> {
    await this.pgPool.query(
      `UPDATE batch_jobs SET status = 'processing', started_at = NOW() WHERE id = $1`,
      [jobId]
    );
  }

  private async markJobCompleted(jobId: string): Promise<void> {
    await this.pgPool.query(
      `UPDATE batch_jobs SET status = 'completed', completed_at = NOW() WHERE id = $1`,
      [jobId]
    );
  }

  private async markJobFailed(jobId: string, error: string): Promise<void> {
    await this.pgPool.query(
      `UPDATE batch_jobs SET status = 'failed', error = $1, completed_at = NOW() WHERE id = $2`,
      [error, jobId]
    );
  }
}

export function startBatchExecutorWorker(pgPool: Pool, intervalMs: number = 60000): void {
  const executor = new BatchExecutor(pgPool);

  // Run immediately
  executor.processPendingJobs();

  // Then run on interval
  setInterval(() => {
    executor.processPendingJobs();
  }, intervalMs);

  console.log(`Batch executor worker started, running every ${intervalMs}ms`);
}
