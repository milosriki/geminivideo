import { AdCreative, AdvancedEdit } from '../types';
import { processVideoWithCreative, processVideoWithAdvancedEdits } from './videoProcessor';

// Define EditTemplate as a union type supporting both creative and advanced editing modes
export type EditTemplate =
  | { mode: 'creative'; creative: AdCreative; sourceVideos: File[] }
  | { mode: 'advanced'; edits: AdvancedEdit[] };

export interface BatchJob {
  id: string;
  sourceVideo: File;
  template: EditTemplate;
  status: 'pending' | 'processing' | 'complete' | 'error' | 'cancelled';
  progress: number;
  outputUrl?: string;
  error?: string;
  startedAt?: Date;
  completedAt?: Date;
}

export interface BatchQueueState {
  jobs: BatchJob[];
  isProcessing: boolean;
  concurrentLimit: number;
  completedCount: number;
  errorCount: number;
}

type JobCallback = (job: BatchJob) => void;
type QueueCallback = () => void;

export class BatchProcessor {
  private jobs: Map<string, BatchJob> = new Map();
  private isProcessing: boolean = false;
  private concurrentLimit: number = 2;
  private activeJobs: Set<string> = new Set();
  private storageKey: string = 'batchProcessor_queue';

  // Callbacks
  private onJobCompleteCallback?: JobCallback;
  private onJobErrorCallback?: JobCallback;
  private onQueueCompleteCallback?: QueueCallback;

  constructor() {
    this.loadFromStorage();
  }

  /**
   * Add multiple videos to the batch queue with the same template
   */
  addToQueue(videos: File[], template: EditTemplate): string[] {
    const jobIds: string[] = [];

    videos.forEach(video => {
      const job: BatchJob = {
        id: this.generateJobId(),
        sourceVideo: video,
        template: template,
        status: 'pending',
        progress: 0,
      };

      this.jobs.set(job.id, job);
      jobIds.push(job.id);
    });

    this.saveToStorage();

    // Auto-start processing if not already running
    if (!this.isProcessing) {
      this.processQueue();
    }

    return jobIds;
  }

  /**
   * Remove a job from the queue (only if pending or complete)
   */
  removeFromQueue(jobId: string): boolean {
    const job = this.jobs.get(jobId);
    if (!job) return false;

    // Can't remove jobs that are currently processing
    if (job.status === 'processing') {
      return false;
    }

    // Cleanup output URL if exists
    if (job.outputUrl) {
      URL.revokeObjectURL(job.outputUrl);
    }

    this.jobs.delete(jobId);
    this.saveToStorage();
    return true;
  }

  /**
   * Cancel a job (marks it as cancelled, stops if processing)
   */
  cancelJob(jobId: string): boolean {
    const job = this.jobs.get(jobId);
    if (!job) return false;

    if (job.status === 'pending' || job.status === 'processing') {
      job.status = 'cancelled';
      job.completedAt = new Date();
      this.activeJobs.delete(jobId);
      this.saveToStorage();

      // Continue processing next jobs
      if (this.isProcessing) {
        this.processNextJobs();
      }

      return true;
    }

    return false;
  }

  /**
   * Pause the queue (stops processing new jobs)
   */
  pauseQueue(): void {
    this.isProcessing = false;
    this.saveToStorage();
  }

  /**
   * Resume the queue (starts processing again)
   */
  resumeQueue(): void {
    if (!this.isProcessing) {
      this.processQueue();
    }
  }

  /**
   * Clear all completed jobs from the queue
   */
  clearCompleted(): void {
    const completedJobs = Array.from(this.jobs.values())
      .filter(job => job.status === 'complete');

    completedJobs.forEach(job => {
      if (job.outputUrl) {
        URL.revokeObjectURL(job.outputUrl);
      }
      this.jobs.delete(job.id);
    });

    this.saveToStorage();
  }

  /**
   * Clear all jobs from the queue
   */
  clearAll(): void {
    // Revoke all output URLs
    this.jobs.forEach(job => {
      if (job.outputUrl) {
        URL.revokeObjectURL(job.outputUrl);
      }
    });

    this.jobs.clear();
    this.activeJobs.clear();
    this.isProcessing = false;
    this.saveToStorage();
  }

  /**
   * Get current queue state
   */
  getQueueState(): BatchQueueState {
    const jobsArray = Array.from(this.jobs.values());

    return {
      jobs: jobsArray,
      isProcessing: this.isProcessing,
      concurrentLimit: this.concurrentLimit,
      completedCount: jobsArray.filter(j => j.status === 'complete').length,
      errorCount: jobsArray.filter(j => j.status === 'error').length,
    };
  }

  /**
   * Get a specific job by ID
   */
  getJob(jobId: string): BatchJob | null {
    return this.jobs.get(jobId) || null;
  }

  /**
   * Set the concurrent processing limit
   */
  setConcurrentLimit(limit: number): void {
    this.concurrentLimit = Math.max(1, Math.min(limit, 5)); // Limit between 1-5
    this.saveToStorage();
  }

  /**
   * Set callback for job completion
   */
  onJobComplete(callback: JobCallback): void {
    this.onJobCompleteCallback = callback;
  }

  /**
   * Set callback for job error
   */
  onJobError(callback: JobCallback): void {
    this.onJobErrorCallback = callback;
  }

  /**
   * Set callback for queue completion
   */
  onQueueComplete(callback: QueueCallback): void {
    this.onQueueCompleteCallback = callback;
  }

  /**
   * Main queue processing loop
   */
  async processQueue(): Promise<void> {
    this.isProcessing = true;
    this.saveToStorage();

    await this.processNextJobs();
  }

  /**
   * Process next batch of jobs up to concurrent limit
   */
  private async processNextJobs(): Promise<void> {
    if (!this.isProcessing) return;

    const pendingJobs = Array.from(this.jobs.values())
      .filter(job => job.status === 'pending');

    // Check if we can process more jobs
    while (this.activeJobs.size < this.concurrentLimit && pendingJobs.length > 0) {
      const job = pendingJobs.shift();
      if (job) {
        this.activeJobs.add(job.id);
        this.processJob(job).catch(err => {
          console.error(`Unexpected error processing job ${job.id}:`, err);
        });
      }
    }

    // Check if queue is complete
    if (this.activeJobs.size === 0 && pendingJobs.length === 0) {
      this.isProcessing = false;
      this.saveToStorage();

      if (this.onQueueCompleteCallback) {
        this.onQueueCompleteCallback();
      }
    }
  }

  /**
   * Process a single job
   */
  async processJob(job: BatchJob): Promise<void> {
    try {
      job.status = 'processing';
      job.startedAt = new Date();
      job.progress = 0;
      this.saveToStorage();

      let outputBlob: Blob;

      // Process based on template mode
      if (job.template.mode === 'creative') {
        const { creative, sourceVideos } = job.template;

        outputBlob = await processVideoWithCreative(
          sourceVideos,
          creative,
          (progressData) => {
            job.progress = progressData.progress;
            this.saveToStorage();
          },
          (logMessage) => {
            console.log(`[Job ${job.id}] ${logMessage}`);
          }
        );
      } else {
        // Advanced mode
        const { edits } = job.template;

        outputBlob = await processVideoWithAdvancedEdits(
          job.sourceVideo,
          edits,
          (progressData) => {
            job.progress = progressData.progress;
            this.saveToStorage();
          },
          (logMessage) => {
            console.log(`[Job ${job.id}] ${logMessage}`);
          }
        );
      }

      // Create object URL for download
      job.outputUrl = URL.createObjectURL(outputBlob);
      job.status = 'complete';
      job.progress = 1;
      job.completedAt = new Date();

      this.saveToStorage();
      this.activeJobs.delete(job.id);

      if (this.onJobCompleteCallback) {
        this.onJobCompleteCallback(job);
      }

      // Process next jobs
      await this.processNextJobs();

    } catch (error: any) {
      job.status = 'error';
      job.error = error.message || 'Unknown error occurred';
      job.completedAt = new Date();

      this.saveToStorage();
      this.activeJobs.delete(job.id);

      if (this.onJobErrorCallback) {
        this.onJobErrorCallback(job);
      }

      // Process next jobs even after error
      await this.processNextJobs();
    }
  }

  /**
   * Retry a failed job
   */
  retryJob(jobId: string): boolean {
    const job = this.jobs.get(jobId);
    if (!job || job.status !== 'error') return false;

    job.status = 'pending';
    job.progress = 0;
    job.error = undefined;
    job.startedAt = undefined;
    job.completedAt = undefined;

    this.saveToStorage();

    // Auto-start processing if not already running
    if (!this.isProcessing) {
      this.processQueue();
    }

    return true;
  }

  /**
   * Generate a unique job ID
   */
  private generateJobId(): string {
    return `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Save queue state to localStorage (without File objects)
   */
  private saveToStorage(): void {
    try {
      const state = {
        concurrentLimit: this.concurrentLimit,
        isProcessing: this.isProcessing,
        jobs: Array.from(this.jobs.values()).map(job => ({
          id: job.id,
          fileName: job.sourceVideo.name,
          fileSize: job.sourceVideo.size,
          fileType: job.sourceVideo.type,
          status: job.status,
          progress: job.progress,
          error: job.error,
          startedAt: job.startedAt?.toISOString(),
          completedAt: job.completedAt?.toISOString(),
          // Note: We don't persist outputUrl or template as they contain non-serializable data
        }))
      };

      localStorage.setItem(this.storageKey, JSON.stringify(state));
    } catch (error) {
      console.error('Failed to save queue to storage:', error);
    }
  }

  /**
   * Load queue state from localStorage
   */
  private loadFromStorage(): void {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (!stored) return;

      const state = JSON.parse(stored);

      if (state.concurrentLimit) {
        this.concurrentLimit = state.concurrentLimit;
      }

      // Note: We only restore metadata, not actual jobs with files
      // Jobs with files must be added fresh in each session

    } catch (error) {
      console.error('Failed to load queue from storage:', error);
    }
  }

  /**
   * Get all completed jobs with output URLs
   */
  getCompletedJobs(): BatchJob[] {
    return Array.from(this.jobs.values())
      .filter(job => job.status === 'complete' && job.outputUrl);
  }

  /**
   * Download all completed videos as a zip (simplified version)
   */
  async downloadAll(): Promise<void> {
    const completedJobs = this.getCompletedJobs();

    if (completedJobs.length === 0) {
      throw new Error('No completed jobs to download');
    }

    // Download each file individually
    // In a production app, you might want to use JSZip to create a zip file
    completedJobs.forEach((job, index) => {
      if (job.outputUrl) {
        const link = document.createElement('a');
        link.href = job.outputUrl;
        link.download = `${job.sourceVideo.name.replace(/\.[^/.]+$/, '')}_processed_${index + 1}.mp4`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    });
  }
}

// Export singleton instance
export const batchProcessor = new BatchProcessor();
