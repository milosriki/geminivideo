/**
 * Status Aggregator - Aggregates status across multiple platforms
 * Provides unified view of multi-platform publishing status
 * Agent 19: Multi-Platform Publishing Infrastructure
 */

export interface PlatformStatus {
  platform: 'meta' | 'google' | 'tiktok';
  status: 'pending' | 'uploading' | 'processing' | 'live' | 'failed' | 'paused';
  campaignId?: string;
  adId?: string;
  adSetId?: string;
  adGroupId?: string;
  videoId?: string;
  creativeId?: string;
  error?: string;
  metrics?: {
    impressions?: number;
    clicks?: number;
    spend?: number;
    conversions?: number;
    ctr?: number;
    cpa?: number;
    roas?: number;
  };
  lastUpdated: Date;
}

export interface MultiPlatformJob {
  jobId: string;
  creativeId: string;
  platforms: ('meta' | 'google' | 'tiktok')[];
  platformStatuses: PlatformStatus[];
  overallStatus: 'pending' | 'in_progress' | 'completed' | 'partial_success' | 'failed';
  successCount: number;
  failureCount: number;
  totalPlatforms: number;
  campaignName: string;
  budgetAllocation: Record<string, number>;
  createdAt: Date;
  completedAt?: Date;
  videoPath: string;
}

export interface AggregatedMetrics {
  totalImpressions: number;
  totalClicks: number;
  totalSpend: number;
  totalConversions: number;
  averageCtr: number;
  averageCpa: number;
  overallRoas: number;
  platformBreakdown: Record<string, {
    impressions: number;
    clicks: number;
    spend: number;
    conversions: number;
    ctr: number;
    cpa: number;
    roas: number;
    percentage: number;
  }>;
}

export class StatusAggregator {
  private jobs: Map<string, MultiPlatformJob> = new Map();

  /**
   * Create a new multi-platform publishing job
   */
  createJob(
    creativeId: string,
    platforms: ('meta' | 'google' | 'tiktok')[],
    campaignName: string,
    budgetAllocation: Record<string, number>,
    videoPath: string
  ): MultiPlatformJob {
    const jobId = `multi_${Date.now()}_${Math.random().toString(36).substring(7)}`;

    const job: MultiPlatformJob = {
      jobId,
      creativeId,
      platforms,
      platformStatuses: platforms.map(platform => ({
        platform,
        status: 'pending',
        lastUpdated: new Date()
      })),
      overallStatus: 'pending',
      successCount: 0,
      failureCount: 0,
      totalPlatforms: platforms.length,
      campaignName,
      budgetAllocation,
      createdAt: new Date(),
      videoPath
    };

    this.jobs.set(jobId, job);
    return job;
  }

  /**
   * Update status for a specific platform
   */
  updatePlatformStatus(
    jobId: string,
    platform: 'meta' | 'google' | 'tiktok',
    update: Partial<PlatformStatus>
  ): MultiPlatformJob | null {
    const job = this.jobs.get(jobId);
    if (!job) {
      console.error(`Job ${jobId} not found`);
      return null;
    }

    // Find and update platform status
    const platformStatus = job.platformStatuses.find(ps => ps.platform === platform);
    if (!platformStatus) {
      console.error(`Platform ${platform} not found in job ${jobId}`);
      return null;
    }

    Object.assign(platformStatus, {
      ...update,
      lastUpdated: new Date()
    });

    // Recalculate job status
    this._updateJobStatus(job);

    return job;
  }

  /**
   * Get job status
   */
  getJobStatus(jobId: string): MultiPlatformJob | null {
    return this.jobs.get(jobId) || null;
  }

  /**
   * Get all jobs
   */
  getAllJobs(): MultiPlatformJob[] {
    return Array.from(this.jobs.values());
  }

  /**
   * Update overall job status based on platform statuses
   */
  private _updateJobStatus(job: MultiPlatformJob): void {
    const statuses = job.platformStatuses.map(ps => ps.status);

    job.successCount = statuses.filter(s => s === 'live').length;
    job.failureCount = statuses.filter(s => s === 'failed').length;

    // Determine overall status
    if (job.successCount === job.totalPlatforms) {
      job.overallStatus = 'completed';
      job.completedAt = new Date();
    } else if (job.failureCount === job.totalPlatforms) {
      job.overallStatus = 'failed';
      job.completedAt = new Date();
    } else if (job.successCount > 0 && (job.successCount + job.failureCount) === job.totalPlatforms) {
      job.overallStatus = 'partial_success';
      job.completedAt = new Date();
    } else if (statuses.some(s => s === 'uploading' || s === 'processing')) {
      job.overallStatus = 'in_progress';
    } else {
      job.overallStatus = 'pending';
    }
  }

  /**
   * Aggregate metrics across all platforms for a job
   */
  aggregateMetrics(jobId: string): AggregatedMetrics | null {
    const job = this.jobs.get(jobId);
    if (!job) {
      console.error(`Job ${jobId} not found`);
      return null;
    }

    const aggregated: AggregatedMetrics = {
      totalImpressions: 0,
      totalClicks: 0,
      totalSpend: 0,
      totalConversions: 0,
      averageCtr: 0,
      averageCpa: 0,
      overallRoas: 0,
      platformBreakdown: {}
    };

    // Aggregate totals
    for (const platformStatus of job.platformStatuses) {
      const metrics = platformStatus.metrics;
      if (!metrics) continue;

      aggregated.totalImpressions += metrics.impressions || 0;
      aggregated.totalClicks += metrics.clicks || 0;
      aggregated.totalSpend += metrics.spend || 0;
      aggregated.totalConversions += metrics.conversions || 0;

      // Calculate platform breakdown
      const platformBreakdown = {
        impressions: metrics.impressions || 0,
        clicks: metrics.clicks || 0,
        spend: metrics.spend || 0,
        conversions: metrics.conversions || 0,
        ctr: metrics.ctr || 0,
        cpa: metrics.cpa || 0,
        roas: metrics.roas || 0,
        percentage: 0 // Will calculate after totals
      };

      aggregated.platformBreakdown[platformStatus.platform] = platformBreakdown;
    }

    // Calculate averages and percentages
    if (aggregated.totalImpressions > 0) {
      aggregated.averageCtr = aggregated.totalClicks / aggregated.totalImpressions;
    }

    if (aggregated.totalConversions > 0 && aggregated.totalSpend > 0) {
      aggregated.averageCpa = aggregated.totalSpend / aggregated.totalConversions;
    }

    if (aggregated.totalSpend > 0) {
      // Calculate revenue (approximate from conversions)
      const revenue = aggregated.totalConversions * 100; // Assume $100 per conversion
      aggregated.overallRoas = revenue / aggregated.totalSpend;
    }

    // Calculate platform percentages based on spend
    if (aggregated.totalSpend > 0) {
      for (const platform in aggregated.platformBreakdown) {
        const breakdown = aggregated.platformBreakdown[platform];
        breakdown.percentage = (breakdown.spend / aggregated.totalSpend) * 100;
      }
    }

    return aggregated;
  }

  /**
   * Get summary of all active jobs
   */
  getSummary(): {
    totalJobs: number;
    pendingJobs: number;
    inProgressJobs: number;
    completedJobs: number;
    failedJobs: number;
    partialSuccessJobs: number;
  } {
    const jobs = Array.from(this.jobs.values());

    return {
      totalJobs: jobs.length,
      pendingJobs: jobs.filter(j => j.overallStatus === 'pending').length,
      inProgressJobs: jobs.filter(j => j.overallStatus === 'in_progress').length,
      completedJobs: jobs.filter(j => j.overallStatus === 'completed').length,
      failedJobs: jobs.filter(j => j.overallStatus === 'failed').length,
      partialSuccessJobs: jobs.filter(j => j.overallStatus === 'partial_success').length
    };
  }

  /**
   * Get recent jobs (last N jobs)
   */
  getRecentJobs(limit: number = 10): MultiPlatformJob[] {
    const jobs = Array.from(this.jobs.values());
    jobs.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
    return jobs.slice(0, limit);
  }

  /**
   * Clean up old completed jobs (older than 30 days)
   */
  cleanupOldJobs(daysToKeep: number = 30): number {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);

    let deletedCount = 0;

    for (const [jobId, job] of this.jobs.entries()) {
      if (
        (job.overallStatus === 'completed' || job.overallStatus === 'failed') &&
        job.completedAt &&
        job.completedAt < cutoffDate
      ) {
        this.jobs.delete(jobId);
        deletedCount++;
      }
    }

    console.log(`Cleaned up ${deletedCount} old jobs`);
    return deletedCount;
  }

  /**
   * Get platform performance comparison
   */
  getPlatformComparison(jobId: string): Array<{
    platform: string;
    status: string;
    performance: 'excellent' | 'good' | 'average' | 'poor' | 'unknown';
    metrics?: {
      impressions?: number;
      clicks?: number;
      ctr?: number;
      roas?: number;
    };
  }> | null {
    const job = this.jobs.get(jobId);
    if (!job) return null;

    return job.platformStatuses.map(ps => {
      let performance: 'excellent' | 'good' | 'average' | 'poor' | 'unknown' = 'unknown';

      if (ps.metrics) {
        const ctr = ps.metrics.ctr || 0;
        const roas = ps.metrics.roas || 0;

        // Performance benchmarks
        if (ctr > 0.05 && roas > 3) {
          performance = 'excellent';
        } else if (ctr > 0.03 && roas > 2) {
          performance = 'good';
        } else if (ctr > 0.01 && roas > 1) {
          performance = 'average';
        } else if (ps.status === 'live') {
          performance = 'poor';
        }
      }

      return {
        platform: ps.platform,
        status: ps.status,
        performance,
        metrics: ps.metrics
      };
    });
  }

  /**
   * Export job data for reporting
   */
  exportJobData(jobId: string): any {
    const job = this.jobs.get(jobId);
    if (!job) return null;

    const metrics = this.aggregateMetrics(jobId);
    const comparison = this.getPlatformComparison(jobId);

    return {
      job,
      aggregatedMetrics: metrics,
      platformComparison: comparison,
      exportedAt: new Date().toISOString()
    };
  }
}

// Singleton instance
export const statusAggregator = new StatusAggregator();
