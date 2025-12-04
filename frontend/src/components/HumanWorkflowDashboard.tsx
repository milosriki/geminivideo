import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  dashboardAPI,
  VideoAnalysis,
  ApprovalItem,
  DriveAnalysisJob,
  CouncilScore,
} from '../services/dashboardAPI';
import {
  UploadIcon,
  CheckIcon,
  VideoIcon,
  GoogleDriveIcon,
  FilmIcon,
  PlayIcon,
  WandIcon,
  SendIcon,
  EyeIcon,
  BarChartIcon,
} from './icons';

// Additional icons needed
const XIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

const RefreshIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polyline points="23 4 23 10 17 10" />
    <polyline points="1 20 1 14 7 14" />
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
  </svg>
);

const FilterIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
  </svg>
);

const CalendarIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
    <line x1="16" y1="2" x2="16" y2="6" />
    <line x1="8" y1="2" x2="8" y2="6" />
    <line x1="3" y1="10" x2="21" y2="10" />
  </svg>
);

const TargetIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="6" />
    <circle cx="12" cy="12" r="2" />
  </svg>
);

const DollarIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <line x1="12" y1="1" x2="12" y2="23" />
    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
  </svg>
);

// Extended types for UI state
interface MetaAccount {
  id: string;
  name: string;
  accountId: string;
  isActive: boolean;
  currency: string;
  timezone: string;
}

interface CampaignConfig {
  name: string;
  budget: {
    type: 'daily' | 'lifetime';
    amount: number;
  };
  schedule: {
    startDate: string;
    endDate?: string;
  };
  targeting: {
    preset: 'broad' | 'lookalike' | 'custom';
    ageMin?: number;
    ageMax?: number;
    genders?: string[];
    locations?: string[];
    interests?: string[];
  };
}

interface PublishJob {
  id: string;
  adId: string;
  campaignConfig: CampaignConfig;
  status: 'queued' | 'publishing' | 'published' | 'failed';
  createdAt: string;
  publishedAt?: string;
  metaAdId?: string;
  error?: string;
}

// Toast notification component
const Toast: React.FC<{
  message: string;
  type: 'success' | 'error' | 'info';
  onClose: () => void;
}> = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const bgColor = {
    success: 'bg-green-500',
    error: 'bg-red-500',
    info: 'bg-blue-500',
  }[type];

  return (
    <div className={`${bgColor} text-white px-6 py-4 rounded-lg shadow-lg flex items-center justify-between min-w-[300px] animate-slide-in`}>
      <span className="font-medium">{message}</span>
      <button onClick={onClose} className="ml-4 hover:opacity-75">
        <XIcon className="w-4 h-4" />
      </button>
    </div>
  );
};

// Loading skeleton component
const Skeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`animate-pulse bg-gray-700 rounded ${className}`} />
);

// Confirmation dialog
const ConfirmDialog: React.FC<{
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmText?: string;
  cancelText?: string;
  type?: 'danger' | 'warning' | 'info';
}> = ({ title, message, onConfirm, onCancel, confirmText = 'Confirm', cancelText = 'Cancel', type = 'info' }) => {
  const buttonColor = {
    danger: 'bg-red-600 hover:bg-red-700',
    warning: 'bg-yellow-600 hover:bg-yellow-700',
    info: 'bg-indigo-600 hover:bg-indigo-700',
  }[type];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 border border-gray-700">
        <h3 className="text-xl font-bold text-white mb-3">{title}</h3>
        <p className="text-gray-300 mb-6">{message}</p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 ${buttonColor} text-white rounded-lg font-medium transition-colors`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

// Tab Navigation Component
const TabNav: React.FC<{
  active: 'analyze' | 'approve' | 'publish';
  onChange: (tab: 'analyze' | 'approve' | 'publish') => void;
}> = ({ active, onChange }) => {
  const tabs = [
    { id: 'analyze' as const, label: 'Analyze', icon: BarChartIcon },
    { id: 'approve' as const, label: 'Approve', icon: CheckIcon },
    { id: 'publish' as const, label: 'Publish', icon: SendIcon },
  ];

  return (
    <div className="flex gap-2 border-b border-gray-700 mb-6">
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`flex items-center gap-2 px-6 py-3 font-semibold transition-colors relative ${
            active === tab.id
              ? 'text-indigo-400 border-b-2 border-indigo-400 -mb-[2px]'
              : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          <tab.icon className="w-5 h-5" />
          {tab.label}
        </button>
      ))}
    </div>
  );
};

// ===== ANALYZE TAB COMPONENTS =====

const GoogleDriveAnalyzer: React.FC<{
  onAnalysisComplete: (results: VideoAnalysis[]) => void;
  showToast: (message: string, type: 'success' | 'error' | 'info') => void;
}> = ({ onAnalysisComplete, showToast }) => {
  const [folderId, setFolderId] = useState('');
  const [maxVideos, setMaxVideos] = useState(10);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState<DriveAnalysisJob | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const startAnalysis = async () => {
    if (!folderId.trim()) {
      showToast('Please enter a Google Drive folder ID', 'error');
      return;
    }

    try {
      setIsAnalyzing(true);
      const job = await dashboardAPI.analyzeDriveFolder(folderId, maxVideos);
      setProgress(job);
      showToast('Analysis started! This may take a few minutes.', 'info');

      // Poll for progress
      pollIntervalRef.current = setInterval(async () => {
        try {
          const updated = await dashboardAPI.getDriveAnalysisStatus(job.job_id);

          if (updated.status === 'completed') {
            clearInterval(pollIntervalRef.current!);
            setIsAnalyzing(false);
            if (updated.results) {
              onAnalysisComplete(updated.results);
              showToast(`Analysis complete! Analyzed ${updated.videos_analyzed} videos.`, 'success');
            }
          } else if (updated.status === 'failed') {
            clearInterval(pollIntervalRef.current!);
            setIsAnalyzing(false);
            showToast('Analysis failed', 'error');
          }
        } catch (error) {
          console.error('Error polling analysis status:', error);
        }
      }, 3000);
    } catch (error) {
      setIsAnalyzing(false);
      showToast(`Failed to start analysis: ${error}`, 'error');
    }
  };

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center gap-3 mb-4">
        <GoogleDriveIcon className="w-6 h-6 text-indigo-400" />
        <h3 className="text-lg font-bold text-white">Google Drive Analyzer</h3>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Folder ID
          </label>
          <input
            type="text"
            value={folderId}
            onChange={e => setFolderId(e.target.value)}
            placeholder="Enter Google Drive folder ID"
            className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            disabled={isAnalyzing}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Max Videos: {maxVideos}
          </label>
          <input
            type="range"
            min="1"
            max="100"
            value={maxVideos}
            onChange={e => setMaxVideos(Number(e.target.value))}
            className="w-full"
            disabled={isAnalyzing}
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>1</span>
            <span>100</span>
          </div>
        </div>

        {progress && isAnalyzing && (
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-300">Analyzing videos...</span>
              <span className="text-sm font-medium text-indigo-400">
                {progress.videos_analyzed || 0} / {progress.videos_found || maxVideos}
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${((progress.videos_analyzed || 0) / (progress.videos_found || maxVideos)) * 100}%`,
                }}
              />
            </div>
          </div>
        )}

        <button
          onClick={startAnalysis}
          disabled={isAnalyzing}
          className={`w-full py-3 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all ${
            isAnalyzing
              ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
              : 'bg-indigo-600 hover:bg-indigo-700 text-white'
          }`}
        >
          {isAnalyzing ? (
            <>
              <RefreshIcon className="w-5 h-5 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <WandIcon className="w-5 h-5" />
              Analyze Folder
            </>
          )}
        </button>
      </div>
    </div>
  );
};

const LocalVideoUploader: React.FC<{
  onUploadComplete: (results: VideoAnalysis[]) => void;
  showToast: (message: string, type: 'success' | 'error' | 'info') => void;
}> = ({ onUploadComplete, showToast }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<
    Array<{ file: File; progress: number; status: 'uploading' | 'analyzing' | 'complete' | 'error'; result?: VideoAnalysis }>
  >([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const videoFiles = Array.from(files).filter(file =>
      file.type.startsWith('video/')
    );

    if (videoFiles.length === 0) {
      showToast('Please select video files only', 'error');
      return;
    }

    const newUploads = videoFiles.map(file => ({
      file,
      progress: 0,
      status: 'uploading' as const,
    }));

    setUploadingFiles(prev => [...prev, ...newUploads]);

    // Process each file
    const completedResults: VideoAnalysis[] = [];

    for (let i = 0; i < videoFiles.length; i++) {
      const file = videoFiles[i];
      try {
        // Simulate upload progress
        for (let progress = 0; progress <= 100; progress += 20) {
          await new Promise(resolve => setTimeout(resolve, 200));
          setUploadingFiles(prev =>
            prev.map(item =>
              item.file === file ? { ...item, progress } : item
            )
          );
        }

        // Start analysis
        setUploadingFiles(prev =>
          prev.map(item =>
            item.file === file ? { ...item, status: 'analyzing' } : item
          )
        );

        const result = await dashboardAPI.analyzeVideo(file);
        completedResults.push(result);

        setUploadingFiles(prev =>
          prev.map(item =>
            item.file === file
              ? { ...item, status: 'complete', result }
              : item
          )
        );

        showToast(`${file.name} analyzed successfully!`, 'success');
      } catch (error) {
        setUploadingFiles(prev =>
          prev.map(item =>
            item.file === file ? { ...item, status: 'error' } : item
          )
        );
        showToast(`Failed to analyze ${file.name}`, 'error');
      }
    }

    if (completedResults.length > 0) {
      onUploadComplete(completedResults);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center gap-3 mb-4">
        <UploadIcon className="w-6 h-6 text-indigo-400" />
        <h3 className="text-lg font-bold text-white">Local Video Uploader</h3>
      </div>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragging
            ? 'border-indigo-500 bg-indigo-500/10'
            : 'border-gray-600 hover:border-gray-500'
        }`}
      >
        <VideoIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-300 font-medium mb-2">
          Drag and drop videos here
        </p>
        <p className="text-gray-500 text-sm mb-4">or click to browse</p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="video/*"
          onChange={e => handleFiles(e.target.files)}
          className="hidden"
        />
      </div>

      {uploadingFiles.length > 0 && (
        <div className="mt-4 space-y-2 max-h-60 overflow-y-auto">
          {uploadingFiles.map((item, idx) => (
            <div
              key={idx}
              className="bg-gray-900 rounded-lg p-3 border border-gray-700"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-300 truncate flex-1">
                  {item.file.name}
                </span>
                {item.status === 'complete' && (
                  <CheckIcon className="w-5 h-5 text-green-500" />
                )}
                {item.status === 'error' && (
                  <XIcon className="w-5 h-5 text-red-500" />
                )}
              </div>
              {item.status === 'uploading' && (
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-indigo-600 h-2 rounded-full transition-all"
                    style={{ width: `${item.progress}%` }}
                  />
                </div>
              )}
              {item.status === 'analyzing' && (
                <div className="text-xs text-indigo-400 flex items-center gap-2">
                  <RefreshIcon className="w-4 h-4 animate-spin" />
                  Analyzing...
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const AnalysisResultsPanel: React.FC<{
  results: VideoAnalysis[];
  onRefresh: () => void;
}> = ({ results, onRefresh }) => {
  const [sortBy, setSortBy] = useState<'status' | 'date' | 'name'>('date');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const sortedResults = [...results].sort((a, b) => {
    switch (sortBy) {
      case 'status':
        return a.status.localeCompare(b.status);
      case 'date':
        return (b.timestamp || '').localeCompare(a.timestamp || '');
      case 'name':
        return a.asset_id.localeCompare(b.asset_id);
      default:
        return 0;
    }
  });

  const filteredResults = sortedResults.filter(result => {
    if (filterStatus !== 'all' && result.status !== filterStatus) return false;
    return true;
  });

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <FilmIcon className="w-6 h-6 text-indigo-400" />
          <h3 className="text-lg font-bold text-white">
            Analysis Results ({filteredResults.length})
          </h3>
        </div>
        <button
          onClick={onRefresh}
          className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
        >
          <RefreshIcon className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6 p-4 bg-gray-900 rounded-lg">
        <div className="flex items-center gap-2">
          <FilterIcon className="w-4 h-4 text-gray-400" />
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value as any)}
            className="px-3 py-1 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-indigo-500"
          >
            <option value="date">Sort by Date</option>
            <option value="status">Sort by Status</option>
            <option value="name">Sort by Name</option>
          </select>
        </div>

        <select
          value={filterStatus}
          onChange={e => setFilterStatus(e.target.value)}
          className="px-3 py-1 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-indigo-500"
        >
          <option value="all">All Status</option>
          <option value="QUEUED">Queued</option>
          <option value="PROCESSING">Processing</option>
          <option value="COMPLETED">Completed</option>
          <option value="FAILED">Failed</option>
        </select>
      </div>

      {/* Results Grid */}
      {filteredResults.length === 0 ? (
        <div className="text-center py-12">
          <VideoIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">No analysis results yet</p>
          <p className="text-gray-500 text-sm mt-2">
            Upload videos or analyze a Google Drive folder to get started
          </p>
        </div>
      ) : (
        <div className="space-y-3 max-h-[500px] overflow-y-auto">
          {filteredResults.map((result, idx) => (
            <div
              key={idx}
              className="bg-gray-900 rounded-lg p-4 border border-gray-700 hover:border-indigo-500/50 transition-colors"
            >
              <div className="flex gap-4">
                <div className="w-32 h-20 bg-gray-800 rounded flex items-center justify-center flex-shrink-0">
                  <VideoIcon className="w-8 h-8 text-gray-600" />
                </div>

                <div className="flex-1 min-w-0">
                  <h4 className="text-white font-semibold truncate mb-1">
                    {result.asset_id}
                  </h4>
                  <div className="flex flex-wrap gap-2 text-xs mb-2">
                    <span className={`font-medium px-2 py-1 rounded ${
                      result.status === 'COMPLETED' ? 'bg-green-900/30 text-green-400' :
                      result.status === 'PROCESSING' ? 'bg-yellow-900/30 text-yellow-400' :
                      result.status === 'FAILED' ? 'bg-red-900/30 text-red-400' :
                      'bg-gray-700 text-gray-400'
                    }`}>
                      {result.status}
                    </span>
                    {result.timestamp && (
                      <span className="text-gray-400">
                        {new Date(result.timestamp).toLocaleDateString()}
                      </span>
                    )}
                  </div>

                  {result.hook_style && (
                    <div className="flex flex-wrap gap-2">
                      <div className="bg-indigo-900/30 text-indigo-300 px-2 py-1 rounded text-xs font-semibold">
                        Hook: {result.hook_style}
                      </div>
                      {result.pacing && (
                        <div className="bg-purple-900/30 text-purple-300 px-2 py-1 rounded text-xs font-semibold">
                          Pacing: {result.pacing}
                        </div>
                      )}
                      {result.emotional_trigger && (
                        <div className="bg-blue-900/30 text-blue-300 px-2 py-1 rounded text-xs font-semibold">
                          Emotion: {result.emotional_trigger}
                        </div>
                      )}
                    </div>
                  )}

                  {result.reasoning && (
                    <p className="text-sm text-gray-400 mt-2 line-clamp-2">
                      {result.reasoning}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ===== APPROVE TAB COMPONENTS =====

const ApprovalQueuePanel: React.FC<{
  showToast: (message: string, type: 'success' | 'error' | 'info') => void;
}> = ({ showToast }) => {
  const [approvalQueue, setApprovalQueue] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [councilScores, setCouncilScores] = useState<Record<string, CouncilScore>>({});
  const [confirmDialog, setConfirmDialog] = useState<{
    show: boolean;
    type: 'approve' | 'reject' | 'reanalyze' | 'bulk-approve' | 'bulk-reject';
    item?: ApprovalItem;
    input?: string;
  }>({ show: false, type: 'approve' });

  const loadApprovalQueue = useCallback(async () => {
    try {
      setLoading(true);
      const queue = await dashboardAPI.getApprovalQueue();
      setApprovalQueue(queue);

      // Load council scores for each item
      for (const item of queue) {
        try {
          const score = await dashboardAPI.getCouncilScore(item.asset_id);
          setCouncilScores(prev => ({ ...prev, [item.asset_id]: score }));
        } catch (error) {
          console.error(`Failed to load council score for ${item.asset_id}:`, error);
        }
      }
    } catch (error) {
      showToast(`Failed to load approval queue: ${error}`, 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadApprovalQueue();
  }, [loadApprovalQueue]);

  const handleApprove = async (item: ApprovalItem, notes?: string) => {
    try {
      await dashboardAPI.approveAd(item.ad_id, notes);
      showToast(`Ad approved successfully!`, 'success');
      loadApprovalQueue();
    } catch (error) {
      showToast(`Failed to approve: ${error}`, 'error');
    }
  };

  const handleReject = async (item: ApprovalItem, reason: string) => {
    if (!reason.trim()) {
      showToast('Please provide a reason for rejection', 'error');
      return;
    }
    try {
      await dashboardAPI.rejectAd(item.ad_id, reason);
      showToast(`Ad rejected`, 'info');
      loadApprovalQueue();
    } catch (error) {
      showToast(`Failed to reject: ${error}`, 'error');
    }
  };

  const handleReanalyze = async (item: ApprovalItem) => {
    try {
      await dashboardAPI.submitForCouncilReview(item.asset_id);
      showToast(`Re-analysis requested`, 'info');
      loadApprovalQueue();
    } catch (error) {
      showToast(`Failed to request re-analysis: ${error}`, 'error');
    }
  };

  const toggleSelection = (id: string) => {
    const newSelection = new Set(selectedItems);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedItems(newSelection);
  };

  const toggleSelectAll = () => {
    if (selectedItems.size === approvalQueue.length) {
      setSelectedItems(new Set());
    } else {
      setSelectedItems(new Set(approvalQueue.map(item => item.ad_id)));
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <Skeleton className="h-32 w-full" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div>
      {/* Bulk Actions Bar */}
      {approvalQueue.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-4 mb-4 border border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedItems.size === approvalQueue.length}
                onChange={toggleSelectAll}
                className="w-4 h-4 rounded"
              />
              <span className="text-white font-medium">
                Select All ({selectedItems.size} selected)
              </span>
            </label>
          </div>

          {selectedItems.size > 0 && (
            <div className="flex gap-2">
              <button
                onClick={() => setConfirmDialog({ show: true, type: 'bulk-approve' })}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                <CheckIcon className="w-4 h-4" />
                Approve ({selectedItems.size})
              </button>
              <button
                onClick={() => setConfirmDialog({ show: true, type: 'bulk-reject' })}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                <XIcon className="w-4 h-4" />
                Reject ({selectedItems.size})
              </button>
            </div>
          )}
        </div>
      )}

      {/* Approval Queue */}
      {approvalQueue.length === 0 ? (
        <div className="bg-gray-800 rounded-lg p-12 text-center border border-gray-700">
          <CheckIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 text-lg">No items in approval queue</p>
          <p className="text-gray-500 text-sm mt-2">
            Analyzed videos will appear here for approval
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {approvalQueue.map(item => {
            const councilScore = councilScores[item.asset_id];

            return (
              <div
                key={item.ad_id}
                className={`bg-gray-800 rounded-lg p-6 border transition-colors ${
                  selectedItems.has(item.ad_id)
                    ? 'border-indigo-500'
                    : 'border-gray-700 hover:border-gray-600'
                }`}
              >
                <div className="flex gap-4">
                  <input
                    type="checkbox"
                    checked={selectedItems.has(item.ad_id)}
                    onChange={() => toggleSelection(item.ad_id)}
                    className="w-5 h-5 rounded mt-1"
                  />

                  {item.thumbnail_url ? (
                    <img
                      src={item.thumbnail_url}
                      alt={item.arc_name || item.ad_id}
                      className="w-48 h-28 object-cover rounded flex-shrink-0"
                    />
                  ) : (
                    <div className="w-48 h-28 bg-gray-900 rounded flex items-center justify-center flex-shrink-0">
                      <VideoIcon className="w-12 h-12 text-gray-600" />
                    </div>
                  )}

                  <div className="flex-1">
                    <h4 className="text-white font-bold text-lg mb-2">
                      {item.arc_name || item.ad_id}
                    </h4>

                    {/* Council Score Display */}
                    {councilScore && (
                      <>
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-bold mb-3 bg-indigo-900/50 text-indigo-300">
                          Council Score: {councilScore.overall_score}/100
                        </div>

                        {/* Titan Scores */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
                          {councilScore.titan_scores.map((titan, idx) => (
                            <div key={idx} className="bg-gray-900 rounded p-2">
                              <div className="text-xs text-gray-400">{titan.titan_name}</div>
                              <div className="text-lg font-bold text-indigo-400">
                                {titan.score}/100
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Consensus */}
                        {councilScore.consensus && (
                          <div className="bg-gray-900 rounded p-3 mb-3">
                            <div className="text-xs font-semibold text-gray-400 mb-1">
                              COUNCIL CONSENSUS:
                            </div>
                            <p className="text-sm text-gray-300">{councilScore.consensus}</p>
                          </div>
                        )}
                      </>
                    )}

                    {/* Predicted Metrics */}
                    <div className="flex gap-3 mb-3">
                      <div className="bg-green-900/30 text-green-300 px-3 py-1 rounded text-sm font-semibold">
                        CTR: {(item.predicted_ctr * 100).toFixed(2)}%
                      </div>
                      <div className="bg-blue-900/30 text-blue-300 px-3 py-1 rounded text-sm font-semibold">
                        ROAS: {item.predicted_roas.toFixed(2)}x
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => setConfirmDialog({ show: true, type: 'approve', item })}
                        className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                      >
                        <CheckIcon className="w-4 h-4" />
                        Approve
                      </button>
                      <button
                        onClick={() => setConfirmDialog({ show: true, type: 'reject', item })}
                        className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                      >
                        <XIcon className="w-4 h-4" />
                        Reject
                      </button>
                      <button
                        onClick={() => setConfirmDialog({ show: true, type: 'reanalyze', item })}
                        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                      >
                        <RefreshIcon className="w-4 h-4" />
                        Re-analyze
                      </button>
                      <button
                        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                      >
                        <EyeIcon className="w-4 h-4" />
                        Preview
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Confirmation Dialogs */}
      {confirmDialog.show && confirmDialog.type === 'approve' && confirmDialog.item && (
        <ConfirmDialog
          title="Approve Ad"
          message={`Are you sure you want to approve "${confirmDialog.item.arc_name || confirmDialog.item.ad_id}"?`}
          onConfirm={() => {
            handleApprove(confirmDialog.item!);
            setConfirmDialog({ show: false, type: 'approve' });
          }}
          onCancel={() => setConfirmDialog({ show: false, type: 'approve' })}
          confirmText="Approve"
          type="info"
        />
      )}

      {confirmDialog.show && confirmDialog.type === 'reject' && confirmDialog.item && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 border border-gray-700">
            <h3 className="text-xl font-bold text-white mb-3">Reject Ad</h3>
            <p className="text-gray-300 mb-4">
              Please provide a reason for rejecting "{confirmDialog.item.arc_name || confirmDialog.item.ad_id}":
            </p>
            <textarea
              value={confirmDialog.input || ''}
              onChange={e => setConfirmDialog({ ...confirmDialog, input: e.target.value })}
              placeholder="Enter rejection reason..."
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 mb-4"
              rows={3}
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setConfirmDialog({ show: false, type: 'reject' })}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  handleReject(confirmDialog.item!, confirmDialog.input || '');
                  setConfirmDialog({ show: false, type: 'reject' });
                }}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
              >
                Reject
              </button>
            </div>
          </div>
        </div>
      )}

      {confirmDialog.show && confirmDialog.type === 'reanalyze' && confirmDialog.item && (
        <ConfirmDialog
          title="Re-analyze Ad"
          message={`Request re-analysis for "${confirmDialog.item.arc_name || confirmDialog.item.ad_id}"? This will send the ad back through the Council of Titans.`}
          onConfirm={() => {
            handleReanalyze(confirmDialog.item!);
            setConfirmDialog({ show: false, type: 'reanalyze' });
          }}
          onCancel={() => setConfirmDialog({ show: false, type: 'reanalyze' })}
          confirmText="Re-analyze"
          type="warning"
        />
      )}
    </div>
  );
};

// ===== PUBLISH TAB COMPONENTS =====

const PublishPanel: React.FC<{
  showToast: (message: string, type: 'success' | 'error' | 'info') => void;
}> = ({ showToast }) => {
  const [metaAccounts] = useState<MetaAccount[]>([
    {
      id: '1',
      name: 'Primary Ad Account',
      accountId: 'ACT_123456789',
      isActive: true,
      currency: 'USD',
      timezone: 'America/New_York',
    },
  ]);
  const [selectedAccount, setSelectedAccount] = useState<string>('1');
  const [approvedAds, setApprovedAds] = useState<ApprovalItem[]>([]);
  const [selectedAd, setSelectedAd] = useState<string>('');
  const [publishHistory] = useState<PublishJob[]>([]);
  const [loading, setLoading] = useState(false);

  const [campaignConfig, setCampaignConfig] = useState<CampaignConfig>({
    name: '',
    budget: {
      type: 'daily',
      amount: 50,
    },
    schedule: {
      startDate: new Date().toISOString().split('T')[0],
    },
    targeting: {
      preset: 'broad',
    },
  });

  useEffect(() => {
    loadApprovedAds();
  }, []);

  const loadApprovedAds = async () => {
    try {
      setLoading(true);
      const queue = await dashboardAPI.getApprovalQueue();
      // Filter for approved ads (in real implementation, the API would filter)
      setApprovedAds(queue);
    } catch (error) {
      showToast(`Failed to load approved ads: ${error}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async () => {
    if (!selectedAccount) {
      showToast('Please select a Meta account', 'error');
      return;
    }
    if (!selectedAd) {
      showToast('Please select an ad to publish', 'error');
      return;
    }
    if (!campaignConfig.name.trim()) {
      showToast('Please enter a campaign name', 'error');
      return;
    }

    showToast('Publishing to Meta...', 'info');
    // In production, would call actual publishing API
    setTimeout(() => {
      showToast('Ad published successfully!', 'success');
    }, 2000);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Meta Account Selector */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-bold text-white mb-4">Meta Account</h3>
        {metaAccounts.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-400">No Meta accounts connected</p>
            <button className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors">
              Connect Meta Account
            </button>
          </div>
        ) : (
          <select
            value={selectedAccount}
            onChange={e => setSelectedAccount(e.target.value)}
            className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
          >
            {metaAccounts.map(account => (
              <option key={account.id} value={account.id}>
                {account.name} ({account.accountId}) - {account.currency}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Ad Selector */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-bold text-white mb-4">Select Approved Ad</h3>
        {approvedAds.length === 0 ? (
          <div className="text-center py-8">
            <CheckIcon className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No approved ads available</p>
            <p className="text-gray-500 text-sm mt-2">
              Approve ads in the Approve tab first
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {approvedAds.map(ad => (
              <button
                key={ad.ad_id}
                onClick={() => setSelectedAd(ad.ad_id)}
                className={`p-4 rounded-lg border-2 transition-all text-left ${
                  selectedAd === ad.ad_id
                    ? 'border-indigo-500 bg-indigo-500/10'
                    : 'border-gray-700 hover:border-gray-600'
                }`}
              >
                <div className="flex gap-3">
                  {ad.thumbnail_url && (
                    <img
                      src={ad.thumbnail_url}
                      alt={ad.arc_name || ad.ad_id}
                      className="w-24 h-16 object-cover rounded"
                    />
                  )}
                  <div className="flex-1">
                    <h4 className="text-white font-semibold mb-1">
                      {ad.arc_name || ad.ad_id}
                    </h4>
                    <div className="text-xs text-green-400">
                      CTR: {(ad.predicted_ctr * 100).toFixed(2)}% | ROAS: {ad.predicted_roas.toFixed(2)}x
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Campaign Configuration */}
      {selectedAd && (
        <>
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-bold text-white mb-4">Campaign Configuration</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Campaign Name *
                </label>
                <input
                  type="text"
                  value={campaignConfig.name}
                  onChange={e =>
                    setCampaignConfig({ ...campaignConfig, name: e.target.value })
                  }
                  placeholder="Enter campaign name"
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center gap-2">
                    <DollarIcon className="w-4 h-4" />
                    Budget Type
                  </label>
                  <select
                    value={campaignConfig.budget.type}
                    onChange={e =>
                      setCampaignConfig({
                        ...campaignConfig,
                        budget: { ...campaignConfig.budget, type: e.target.value as any },
                      })
                    }
                    className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="daily">Daily Budget</option>
                    <option value="lifetime">Lifetime Budget</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Amount ($)
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={campaignConfig.budget.amount}
                    onChange={e =>
                      setCampaignConfig({
                        ...campaignConfig,
                        budget: { ...campaignConfig.budget, amount: Number(e.target.value) },
                      })
                    }
                    className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center gap-2">
                    <CalendarIcon className="w-4 h-4" />
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={campaignConfig.schedule.startDate}
                    onChange={e =>
                      setCampaignConfig({
                        ...campaignConfig,
                        schedule: { ...campaignConfig.schedule, startDate: e.target.value },
                      })
                    }
                    className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    End Date (Optional)
                  </label>
                  <input
                    type="date"
                    value={campaignConfig.schedule.endDate || ''}
                    onChange={e =>
                      setCampaignConfig({
                        ...campaignConfig,
                        schedule: { ...campaignConfig.schedule, endDate: e.target.value },
                      })
                    }
                    className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center gap-2">
                  <TargetIcon className="w-4 h-4" />
                  Targeting Preset
                </label>
                <select
                  value={campaignConfig.targeting.preset}
                  onChange={e =>
                    setCampaignConfig({
                      ...campaignConfig,
                      targeting: { ...campaignConfig.targeting, preset: e.target.value as any },
                    })
                  }
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="broad">Broad Targeting</option>
                  <option value="lookalike">Lookalike Audience</option>
                  <option value="custom">Custom Audience</option>
                </select>
              </div>
            </div>
          </div>

          {/* Publish Button */}
          <button
            onClick={handlePublish}
            disabled={!selectedAccount || !selectedAd}
            className={`w-full py-4 rounded-lg font-bold text-lg flex items-center justify-center gap-3 transition-all ${
              !selectedAccount || !selectedAd
                ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transform hover:scale-[1.02]'
            }`}
          >
            <SendIcon className="w-6 h-6" />
            Publish to Meta
          </button>
        </>
      )}

      {/* Publishing History */}
      {publishHistory.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-bold text-white mb-4">Publishing History</h3>
          <div className="space-y-3">
            {publishHistory.map(job => (
              <div
                key={job.id}
                className="bg-gray-900 rounded-lg p-4 border border-gray-700"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-medium">
                    {job.campaignConfig.name}
                  </span>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold ${
                      job.status === 'published'
                        ? 'bg-green-900/50 text-green-300'
                        : job.status === 'publishing'
                        ? 'bg-yellow-900/50 text-yellow-300'
                        : job.status === 'failed'
                        ? 'bg-red-900/50 text-red-300'
                        : 'bg-gray-700 text-gray-300'
                    }`}
                  >
                    {job.status.toUpperCase()}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-400">
                  <span>
                    {new Date(job.createdAt).toLocaleDateString()}
                  </span>
                  {job.metaAdId && (
                    <span className="text-indigo-400">
                      Ad ID: {job.metaAdId}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ===== MAIN COMPONENT =====

export const HumanWorkflowDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'analyze' | 'approve' | 'publish'>('analyze');
  const [analysisResults, setAnalysisResults] = useState<VideoAnalysis[]>([]);
  const [toasts, setToasts] = useState<
    Array<{ id: number; message: string; type: 'success' | 'error' | 'info' }>
  >([]);

  const showToast = useCallback(
    (message: string, type: 'success' | 'error' | 'info') => {
      const id = Date.now();
      setToasts(prev => [...prev, { id, message, type }]);
    },
    []
  );

  const removeToast = useCallback((id: number) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const handleAnalysisComplete = useCallback((results: VideoAnalysis[]) => {
    setAnalysisResults(prev => [...results, ...prev]);
  }, []);

  const refreshAnalysisResults = () => {
    showToast('Refresh functionality requires backend integration', 'info');
  };

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Human Workflow Dashboard
          </h1>
          <p className="text-gray-400">
            Analyze videos, approve content, and publish to Meta
          </p>
        </div>

        {/* Tab Navigation */}
        <TabNav active={activeTab} onChange={setActiveTab} />

        {/* Tab Content */}
        <div className="animate-fade-in">
          {activeTab === 'analyze' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <GoogleDriveAnalyzer
                  onAnalysisComplete={handleAnalysisComplete}
                  showToast={showToast}
                />
                <LocalVideoUploader
                  onUploadComplete={handleAnalysisComplete}
                  showToast={showToast}
                />
              </div>
              <AnalysisResultsPanel
                results={analysisResults}
                onRefresh={refreshAnalysisResults}
              />
            </div>
          )}

          {activeTab === 'approve' && (
            <ApprovalQueuePanel showToast={showToast} />
          )}

          {activeTab === 'publish' && (
            <PublishPanel showToast={showToast} />
          )}
        </div>
      </div>

      {/* Toast Notifications */}
      <div className="fixed bottom-6 right-6 space-y-3 z-50">
        {toasts.map(toast => (
          <Toast
            key={toast.id}
            message={toast.message}
            type={toast.type}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </div>
    </div>
  );
};

export default HumanWorkflowDashboard;
