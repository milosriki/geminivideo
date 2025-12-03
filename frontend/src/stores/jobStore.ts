import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';

export type JobType = 'video-generation' | 'video-edit' | 'render' | 'upload' | 'analysis';
export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

export interface Job {
  id: string;
  type: JobType;
  status: JobStatus;
  progress: number; // 0-100
  createdAt: Date;
  updatedAt: Date;
  completedAt?: Date;
  error?: string;
  metadata?: {
    title?: string;
    description?: string;
    duration?: number;
    fileSize?: number;
    outputUrl?: string;
    [key: string]: unknown;
  };
}

export interface JobState {
  jobs: Job[];

  addJob: (job: Job) => void;
  updateJob: (id: string, updates: Partial<Job>) => void;
  removeJob: (id: string) => void;
  clearCompleted: () => void;
  clearAll: () => void;
  getJobById: (id: string) => Job | undefined;
  getJobsByStatus: (status: JobStatus) => Job[];
  getJobsByType: (type: JobType) => Job[];
}

export const useJobStore = create<JobState>()(
  immer((set, get) => ({
    jobs: [],

    addJob: (job) => set((state) => {
      state.jobs.unshift(job); // Add to beginning of array
    }),

    updateJob: (id, updates) => set((state) => {
      const index = state.jobs.findIndex((j) => j.id === id);
      if (index !== -1) {
        state.jobs[index] = {
          ...state.jobs[index],
          ...updates,
          updatedAt: new Date(),
        };

        // Set completedAt if status is completed or failed
        if (updates.status === 'completed' || updates.status === 'failed') {
          state.jobs[index].completedAt = new Date();
        }
      }
    }),

    removeJob: (id) => set((state) => {
      state.jobs = state.jobs.filter((j) => j.id !== id);
    }),

    clearCompleted: () => set((state) => {
      state.jobs = state.jobs.filter(
        (j) => j.status !== 'completed' && j.status !== 'failed'
      );
    }),

    clearAll: () => set({ jobs: [] }),

    getJobById: (id) => {
      return get().jobs.find((j) => j.id === id);
    },

    getJobsByStatus: (status) => {
      return get().jobs.filter((j) => j.status === status);
    },

    getJobsByType: (type) => {
      return get().jobs.filter((j) => j.type === type);
    },
  }))
);
