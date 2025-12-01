/**
 * Dashboard Context Provider
 * Agent 11: Frontend Dashboard Integration Engineer
 *
 * Provides unified API access, loading states, error management,
 * and caching for all dashboard components.
 */

import React, { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react';
import { dashboardAPI } from '../services/dashboardAPI';
import type {
  VideoAnalysis,
  AnalysisStatus,
  AnalysisResults,
  CouncilScore,
  ReviewStatus,
  MetaInsights,
  RefreshStatus,
  TopPerformersList,
  RenderConfig,
  RenderJob,
  RenderStatus,
  ApprovalItem,
  ApprovalStatus,
  DiversificationMetrics,
  ReliabilityMetrics,
  AccuracyMetrics,
  DriveAnalysisJob,
  DriveAnalysisStatus,
  DashboardAPIError,
} from '../services/dashboardAPI';

// ============================================================================
// TYPES
// ============================================================================

interface LoadingState {
  [key: string]: boolean;
}

interface ErrorState {
  [key: string]: DashboardAPIError | null;
}

interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

interface Cache {
  [key: string]: CacheEntry<any>;
}

interface DashboardContextValue {
  // Loading states
  loading: LoadingState;
  isLoading: (key: string) => boolean;
  setLoading: (key: string, value: boolean) => void;

  // Error states
  errors: ErrorState;
  getError: (key: string) => DashboardAPIError | null;
  setError: (key: string, error: DashboardAPIError | null) => void;
  clearError: (key: string) => void;
  clearAllErrors: () => void;

  // Cache management
  getFromCache: <T>(key: string) => T | null;
  setCache: <T>(key: string, data: T, ttl?: number) => void;
  clearCache: (key?: string) => void;

  // Video Analysis Methods
  analyzeVideo: (file: File) => Promise<VideoAnalysis | null>;
  getAnalysisStatus: (analysisId: string) => Promise<AnalysisStatus | null>;
  getAnalysisResults: (analysisId: string) => Promise<AnalysisResults | null>;

  // Council of Titans Methods
  getCouncilScore: (videoId: string, useCache?: boolean) => Promise<CouncilScore | null>;
  submitForCouncilReview: (videoId: string) => Promise<ReviewStatus | null>;

  // Meta Learning Methods
  getMetaInsights: (useCache?: boolean) => Promise<MetaInsights | null>;
  triggerMetaRefresh: () => Promise<RefreshStatus | null>;
  getTopPerformers: (limit?: number, useCache?: boolean) => Promise<TopPerformersList | null>;

  // Render Job Methods
  createRenderJob: (config: RenderConfig) => Promise<RenderJob | null>;
  getRenderStatus: (jobId: string) => Promise<RenderStatus | null>;
  cancelRenderJob: (jobId: string) => Promise<boolean>;
  downloadRenderedVideo: (jobId: string) => Promise<Blob | null>;

  // Approval Workflow Methods
  getApprovalQueue: (useCache?: boolean) => Promise<ApprovalItem[]>;
  submitForApproval: (adId: string) => Promise<ApprovalStatus | null>;
  approveAd: (adId: string, notes?: string) => Promise<boolean>;
  rejectAd: (adId: string, reason: string) => Promise<boolean>;

  // Metrics Methods
  getDiversificationMetrics: (useCache?: boolean) => Promise<DiversificationMetrics | null>;
  getReliabilityMetrics: (useCache?: boolean) => Promise<ReliabilityMetrics | null>;
  getPredictionAccuracy: (useCache?: boolean) => Promise<AccuracyMetrics | null>;

  // Drive Integration Methods
  analyzeDriveFolder: (folderId: string, maxVideos?: number) => Promise<DriveAnalysisJob | null>;
  getDriveAnalysisStatus: (jobId: string) => Promise<DriveAnalysisStatus | null>;

  // Authentication
  setAuthToken: (token: string) => void;
  clearAuthToken: () => void;
}

// ============================================================================
// CONTEXT
// ============================================================================

const DashboardContext = createContext<DashboardContextValue | undefined>(undefined);

// ============================================================================
// PROVIDER
// ============================================================================

interface DashboardProviderProps {
  children: ReactNode;
  cacheTTL?: number; // Default cache TTL in milliseconds
}

export const DashboardProvider: React.FC<DashboardProviderProps> = ({
  children,
  cacheFFTL = 5 * 60 * 1000 // 5 minutes default
}) => {
  const [loading, setLoadingState] = useState<LoadingState>({});
  const [errors, setErrorsState] = useState<ErrorState>({});
  const [cache, setCacheState] = useState<Cache>({});

  // ============================================================================
  // LOADING STATE MANAGEMENT
  // ============================================================================

  const setLoading = useCallback((key: string, value: boolean) => {
    setLoadingState((prev) => ({ ...prev, [key]: value }));
  }, []);

  const isLoading = useCallback((key: string): boolean => {
    return loading[key] || false;
  }, [loading]);

  // ============================================================================
  // ERROR STATE MANAGEMENT
  // ============================================================================

  const setError = useCallback((key: string, error: DashboardAPIError | null) => {
    setErrorsState((prev) => ({ ...prev, [key]: error }));
  }, []);

  const getError = useCallback((key: string): DashboardAPIError | null => {
    return errors[key] || null;
  }, [errors]);

  const clearError = useCallback((key: string) => {
    setErrorsState((prev) => {
      const newErrors = { ...prev };
      delete newErrors[key];
      return newErrors;
    });
  }, []);

  const clearAllErrors = useCallback(() => {
    setErrorsState({});
  }, []);

  // ============================================================================
  // CACHE MANAGEMENT
  // ============================================================================

  const getFromCache = useCallback(<T,>(key: string): T | null => {
    const entry = cache[key];
    if (!entry) return null;

    // Check if cache is expired
    const now = Date.now();
    if (now - entry.timestamp > cacheFFTL) {
      // Cache expired, remove it
      setCacheState((prev) => {
        const newCache = { ...prev };
        delete newCache[key];
        return newCache;
      });
      return null;
    }

    return entry.data as T;
  }, [cache, cacheFFTL]);

  const setCache = useCallback(<T,>(key: string, data: T, ttl?: number) => {
    setCacheState((prev) => ({
      ...prev,
      [key]: {
        data,
        timestamp: Date.now(),
      },
    }));
  }, []);

  const clearCache = useCallback((key?: string) => {
    if (key) {
      setCacheState((prev) => {
        const newCache = { ...prev };
        delete newCache[key];
        return newCache;
      });
    } else {
      setCacheState({});
    }
  }, []);

  // ============================================================================
  // API WRAPPER HELPER
  // ============================================================================

  const withErrorHandling = useCallback(
    async <T,>(
      key: string,
      apiCall: () => Promise<T>,
      useCache: boolean = false
    ): Promise<T | null> => {
      try {
        // Check cache first if enabled
        if (useCache) {
          const cached = getFromCache<T>(key);
          if (cached) {
            return cached;
          }
        }

        setLoading(key, true);
        clearError(key);

        const result = await apiCall();

        // Store in cache if successful
        if (useCache && result) {
          setCache(key, result);
        }

        return result;
      } catch (err) {
        const error = err as DashboardAPIError;
        setError(key, error);
        console.error(`API Error [${key}]:`, error);
        return null;
      } finally {
        setLoading(key, false);
      }
    },
    [setLoading, clearError, setError, getFromCache, setCache]
  );

  // ============================================================================
  // VIDEO ANALYSIS METHODS
  // ============================================================================

  const analyzeVideo = useCallback(
    async (file: File): Promise<VideoAnalysis | null> => {
      return withErrorHandling(
        `analyzeVideo_${file.name}`,
        () => dashboardAPI.analyzeVideo(file)
      );
    },
    [withErrorHandling]
  );

  const getAnalysisStatus = useCallback(
    async (analysisId: string): Promise<AnalysisStatus | null> => {
      return withErrorHandling(
        `analysisStatus_${analysisId}`,
        () => dashboardAPI.getAnalysisStatus(analysisId)
      );
    },
    [withErrorHandling]
  );

  const getAnalysisResults = useCallback(
    async (analysisId: string): Promise<AnalysisResults | null> => {
      return withErrorHandling(
        `analysisResults_${analysisId}`,
        () => dashboardAPI.getAnalysisResults(analysisId),
        true // Cache results
      );
    },
    [withErrorHandling]
  );

  // ============================================================================
  // COUNCIL OF TITANS METHODS
  // ============================================================================

  const getCouncilScore = useCallback(
    async (videoId: string, useCache: boolean = true): Promise<CouncilScore | null> => {
      return withErrorHandling(
        `councilScore_${videoId}`,
        () => dashboardAPI.getCouncilScore(videoId),
        useCache
      );
    },
    [withErrorHandling]
  );

  const submitForCouncilReview = useCallback(
    async (videoId: string): Promise<ReviewStatus | null> => {
      const result = await withErrorHandling(
        `submitCouncilReview_${videoId}`,
        () => dashboardAPI.submitForCouncilReview(videoId)
      );
      // Invalidate cache after submission
      if (result) {
        clearCache(`councilScore_${videoId}`);
      }
      return result;
    },
    [withErrorHandling, clearCache]
  );

  // ============================================================================
  // META LEARNING METHODS
  // ============================================================================

  const getMetaInsights = useCallback(
    async (useCache: boolean = true): Promise<MetaInsights | null> => {
      return withErrorHandling(
        'metaInsights',
        () => dashboardAPI.getMetaInsights(),
        useCache
      );
    },
    [withErrorHandling]
  );

  const triggerMetaRefresh = useCallback(
    async (): Promise<RefreshStatus | null> => {
      const result = await withErrorHandling(
        'triggerMetaRefresh',
        () => dashboardAPI.triggerMetaRefresh()
      );
      // Clear meta insights cache after refresh
      if (result) {
        clearCache('metaInsights');
        clearCache('topPerformers');
      }
      return result;
    },
    [withErrorHandling, clearCache]
  );

  const getTopPerformers = useCallback(
    async (limit: number = 10, useCache: boolean = true): Promise<TopPerformersList | null> => {
      return withErrorHandling(
        `topPerformers_${limit}`,
        () => dashboardAPI.getTopPerformers(limit),
        useCache
      );
    },
    [withErrorHandling]
  );

  // ============================================================================
  // RENDER JOB METHODS
  // ============================================================================

  const createRenderJob = useCallback(
    async (config: RenderConfig): Promise<RenderJob | null> => {
      return withErrorHandling(
        'createRenderJob',
        () => dashboardAPI.createRenderJob(config)
      );
    },
    [withErrorHandling]
  );

  const getRenderStatus = useCallback(
    async (jobId: string): Promise<RenderStatus | null> => {
      return withErrorHandling(
        `renderStatus_${jobId}`,
        () => dashboardAPI.getRenderStatus(jobId)
      );
    },
    [withErrorHandling]
  );

  const cancelRenderJob = useCallback(
    async (jobId: string): Promise<boolean> => {
      const result = await withErrorHandling(
        `cancelRenderJob_${jobId}`,
        () => dashboardAPI.cancelRenderJob(jobId)
      );
      return result || false;
    },
    [withErrorHandling]
  );

  const downloadRenderedVideo = useCallback(
    async (jobId: string): Promise<Blob | null> => {
      return withErrorHandling(
        `downloadVideo_${jobId}`,
        () => dashboardAPI.downloadRenderedVideo(jobId)
      );
    },
    [withErrorHandling]
  );

  // ============================================================================
  // APPROVAL WORKFLOW METHODS
  // ============================================================================

  const getApprovalQueue = useCallback(
    async (useCache: boolean = false): Promise<ApprovalItem[]> => {
      const result = await withErrorHandling(
        'approvalQueue',
        () => dashboardAPI.getApprovalQueue(),
        useCache
      );
      return result || [];
    },
    [withErrorHandling]
  );

  const submitForApproval = useCallback(
    async (adId: string): Promise<ApprovalStatus | null> => {
      const result = await withErrorHandling(
        `submitApproval_${adId}`,
        () => dashboardAPI.submitForApproval(adId)
      );
      // Invalidate approval queue cache
      if (result) {
        clearCache('approvalQueue');
      }
      return result;
    },
    [withErrorHandling, clearCache]
  );

  const approveAd = useCallback(
    async (adId: string, notes?: string): Promise<boolean> => {
      const result = await withErrorHandling(
        `approveAd_${adId}`,
        () => dashboardAPI.approveAd(adId, notes)
      );
      // Invalidate approval queue cache
      if (result) {
        clearCache('approvalQueue');
      }
      return result || false;
    },
    [withErrorHandling, clearCache]
  );

  const rejectAd = useCallback(
    async (adId: string, reason: string): Promise<boolean> => {
      const result = await withErrorHandling(
        `rejectAd_${adId}`,
        () => dashboardAPI.rejectAd(adId, reason)
      );
      // Invalidate approval queue cache
      if (result) {
        clearCache('approvalQueue');
      }
      return result || false;
    },
    [withErrorHandling, clearCache]
  );

  // ============================================================================
  // METRICS METHODS
  // ============================================================================

  const getDiversificationMetrics = useCallback(
    async (useCache: boolean = true): Promise<DiversificationMetrics | null> => {
      return withErrorHandling(
        'diversificationMetrics',
        () => dashboardAPI.getDiversificationMetrics(),
        useCache
      );
    },
    [withErrorHandling]
  );

  const getReliabilityMetrics = useCallback(
    async (useCache: boolean = true): Promise<ReliabilityMetrics | null> => {
      return withErrorHandling(
        'reliabilityMetrics',
        () => dashboardAPI.getReliabilityMetrics(),
        useCache
      );
    },
    [withErrorHandling]
  );

  const getPredictionAccuracy = useCallback(
    async (useCache: boolean = true): Promise<AccuracyMetrics | null> => {
      return withErrorHandling(
        'predictionAccuracy',
        () => dashboardAPI.getPredictionAccuracy(),
        useCache
      );
    },
    [withErrorHandling]
  );

  // ============================================================================
  // DRIVE INTEGRATION METHODS
  // ============================================================================

  const analyzeDriveFolder = useCallback(
    async (folderId: string, maxVideos: number = 10): Promise<DriveAnalysisJob | null> => {
      return withErrorHandling(
        `analyzeDriveFolder_${folderId}`,
        () => dashboardAPI.analyzeDriveFolder(folderId, maxVideos)
      );
    },
    [withErrorHandling]
  );

  const getDriveAnalysisStatus = useCallback(
    async (jobId: string): Promise<DriveAnalysisStatus | null> => {
      return withErrorHandling(
        `driveAnalysisStatus_${jobId}`,
        () => dashboardAPI.getDriveAnalysisStatus(jobId)
      );
    },
    [withErrorHandling]
  );

  // ============================================================================
  // AUTHENTICATION METHODS
  // ============================================================================

  const setAuthToken = useCallback((token: string) => {
    dashboardAPI.setAuthToken(token);
  }, []);

  const clearAuthToken = useCallback(() => {
    dashboardAPI.clearAuthToken();
    clearCache(); // Clear all cached data on logout
    clearAllErrors();
  }, [clearCache, clearAllErrors]);

  // ============================================================================
  // CACHE CLEANUP ON UNMOUNT
  // ============================================================================

  useEffect(() => {
    // Cleanup interval to remove expired cache entries
    const cleanupInterval = setInterval(() => {
      const now = Date.now();
      setCacheState((prev) => {
        const newCache = { ...prev };
        let hasChanges = false;

        Object.keys(newCache).forEach((key) => {
          if (now - newCache[key].timestamp > cacheFFTL) {
            delete newCache[key];
            hasChanges = true;
          }
        });

        return hasChanges ? newCache : prev;
      });
    }, 60000); // Run cleanup every minute

    return () => clearInterval(cleanupInterval);
  }, [cacheFFTL]);

  // ============================================================================
  // CONTEXT VALUE
  // ============================================================================

  const value: DashboardContextValue = {
    // Loading states
    loading,
    isLoading,
    setLoading,

    // Error states
    errors,
    getError,
    setError,
    clearError,
    clearAllErrors,

    // Cache management
    getFromCache,
    setCache,
    clearCache,

    // Video Analysis
    analyzeVideo,
    getAnalysisStatus,
    getAnalysisResults,

    // Council of Titans
    getCouncilScore,
    submitForCouncilReview,

    // Meta Learning
    getMetaInsights,
    triggerMetaRefresh,
    getTopPerformers,

    // Render Jobs
    createRenderJob,
    getRenderStatus,
    cancelRenderJob,
    downloadRenderedVideo,

    // Approval Workflow
    getApprovalQueue,
    submitForApproval,
    approveAd,
    rejectAd,

    // Metrics
    getDiversificationMetrics,
    getReliabilityMetrics,
    getPredictionAccuracy,

    // Drive Integration
    analyzeDriveFolder,
    getDriveAnalysisStatus,

    // Authentication
    setAuthToken,
    clearAuthToken,
  };

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
};

// ============================================================================
// HOOK
// ============================================================================

/**
 * Custom hook to access the Dashboard context
 * @throws Error if used outside of DashboardProvider
 */
export const useDashboard = (): DashboardContextValue => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used within a DashboardProvider');
  }
  return context;
};

// Export context for advanced use cases
export { DashboardContext };
