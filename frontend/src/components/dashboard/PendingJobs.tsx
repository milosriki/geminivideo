import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon } from '@heroicons/react/24/outline';
import {
  VideoCameraIcon,
  PhotoIcon,
  DocumentTextIcon,
  SparklesIcon,
} from '@heroicons/react/24/solid';

interface Job {
  id: string;
  type: 'video' | 'image' | 'script' | 'analysis';
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  createdAt: string;
}

const mockJobs: Job[] = [
  {
    id: '1',
    type: 'video',
    name: 'Product Demo - Summer Collection',
    status: 'processing',
    progress: 65,
    createdAt: '2 min ago',
  },
  {
    id: '2',
    type: 'image',
    name: 'Hero Banner Variations (x5)',
    status: 'processing',
    progress: 40,
    createdAt: '5 min ago',
  },
  {
    id: '3',
    type: 'script',
    name: 'Ad Script - Black Friday',
    status: 'pending',
    progress: 0,
    createdAt: '8 min ago',
  },
  {
    id: '4',
    type: 'analysis',
    name: 'Competitor Analysis - Nike',
    status: 'completed',
    progress: 100,
    createdAt: '15 min ago',
  },
];

const typeConfig = {
  video: {
    icon: VideoCameraIcon,
    color: 'text-purple-400',
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/20',
  },
  image: {
    icon: PhotoIcon,
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
  },
  script: {
    icon: DocumentTextIcon,
    color: 'text-green-400',
    bg: 'bg-green-500/10',
    border: 'border-green-500/20',
  },
  analysis: {
    icon: SparklesIcon,
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/20',
  },
};

const statusConfig = {
  pending: {
    label: 'Pending',
    color: 'text-zinc-400',
    bg: 'bg-zinc-500/10',
    dot: 'bg-zinc-400',
  },
  processing: {
    label: 'Processing',
    color: 'text-indigo-400',
    bg: 'bg-indigo-500/10',
    dot: 'bg-indigo-400',
  },
  completed: {
    label: 'Completed',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
    dot: 'bg-emerald-400',
  },
  failed: {
    label: 'Failed',
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    dot: 'bg-red-400',
  },
};

export const PendingJobs: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>(mockJobs);

  const handleCancel = (jobId: string) => {
    setJobs(jobs.filter(job => job.id !== jobId));
  };

  const activeJobs = jobs.filter(job => job.status !== 'completed' && job.status !== 'failed');
  const canCancel = (status: Job['status']) => status === 'pending' || status === 'processing';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 sm:p-5 shadow-lg shadow-black/20 h-full"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h3 className="text-white font-semibold text-base sm:text-lg">Pending Jobs</h3>
          {activeJobs.length > 0 && (
            <span className="px-2 py-0.5 bg-indigo-500/10 text-indigo-400 text-xs font-medium rounded-full">
              {activeJobs.length}
            </span>
          )}
        </div>
        <a
          href="/jobs"
          className="text-indigo-400 hover:text-indigo-300 text-xs sm:text-sm font-medium transition-colors"
        >
          View All
        </a>
      </div>

      {/* Jobs List */}
      <div className="space-y-3">
        <AnimatePresence mode="popLayout">
          {jobs.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-8"
            >
              <div className="inline-flex items-center justify-center w-16 h-16 bg-zinc-800 rounded-full mb-3">
                <SparklesIcon className="w-8 h-8 text-zinc-600" />
              </div>
              <p className="text-zinc-500 text-sm">No active jobs</p>
            </motion.div>
          ) : (
            jobs.map((job, index) => {
              const typeStyles = typeConfig[job.type];
              const statusStyles = statusConfig[job.status];
              const TypeIcon = typeStyles.icon;

              return (
                <motion.div
                  key={job.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20, height: 0, marginBottom: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  className={`bg-zinc-800/50 border ${typeStyles.border} rounded-lg p-2 sm:p-3 hover:bg-zinc-800 transition-colors group`}
                >
                  <div className="flex items-start gap-2 sm:gap-3">
                    {/* Type Icon */}
                    <div className={`${typeStyles.bg} ${typeStyles.color} p-2 rounded-lg shrink-0`}>
                      <TypeIcon className="w-4 h-4" />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      {/* Title and Status */}
                      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-1 sm:gap-2 mb-1">
                        <h4 className="text-white text-xs sm:text-sm font-medium truncate">
                          {job.name}
                        </h4>
                        <span
                          className={`px-2 py-0.5 ${statusStyles.bg} ${statusStyles.color} text-xs font-medium rounded shrink-0 self-start`}
                        >
                          {statusStyles.label}
                        </span>
                      </div>

                      {/* Progress Bar */}
                      {job.status === 'processing' && (
                        <div className="mb-2">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-zinc-500 text-xs">
                              {job.progress}%
                            </span>
                          </div>
                          <div className="h-1.5 bg-zinc-700 rounded-full overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${job.progress}%` }}
                              transition={{ duration: 0.5, ease: 'easeOut' }}
                              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                            />
                          </div>
                        </div>
                      )}

                      {/* Footer */}
                      <div className="flex items-center justify-between">
                        <span className="text-zinc-500 text-xs">
                          {job.createdAt}
                        </span>

                        {/* Cancel Button */}
                        {canCancel(job.status) && (
                          <button
                            onClick={() => handleCancel(job.id)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-zinc-700 rounded"
                            title="Cancel job"
                          >
                            <XMarkIcon className="w-4 h-4 text-zinc-400 hover:text-red-400 transition-colors" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })
          )}
        </AnimatePresence>
      </div>

      {/* Summary Footer */}
      {jobs.length > 0 && (
        <div className="mt-4 pt-4 border-t border-zinc-800">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5">
                <div className={`w-2 h-2 rounded-full ${statusConfig.processing.dot} animate-pulse`} />
                <span className="text-zinc-400">
                  {jobs.filter(j => j.status === 'processing').length} processing
                </span>
              </div>
              <span className="text-zinc-700">•</span>
              <div className="flex items-center gap-1.5">
                <div className={`w-2 h-2 rounded-full ${statusConfig.pending.dot}`} />
                <span className="text-zinc-400">
                  {jobs.filter(j => j.status === 'pending').length} queued
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default PendingJobs;
